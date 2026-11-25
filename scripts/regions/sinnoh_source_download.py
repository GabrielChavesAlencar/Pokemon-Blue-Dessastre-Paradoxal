"""Download the two pinned Sinnoh resources from the authors' public links.

Windows only for MEGA AES via the system CNG provider. No external executables,
pip installs, accounts, mirrors, archive extraction or uploads. SHA-256 of
the exact user-reviewed ZIP is authoritative; a changed source fails closed.
"""
from __future__ import annotations

import base64
import ctypes
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, build_opener, HTTPRedirectHandler

from sinnoh_private_visual import PACKS, discover, fail, verified_archive

PAGES = {
    "maps": "https://eeveeexpo.com/resources/1661/download",
    "overworlds": "https://eeveeexpo.com/resources/609/download",
}
SIZES = {"maps": 89235961, "overworlds": 2158072}
MEGA_ID = "PMZxiYhI"
MEDIAFIRE_ID = "vmrjeckhz5dclzr"
CHUNK = 1024 * 1024
TRANSIENT_HTTP = (408,429,500,502,503,504)
RETRY_DELAYS = (1,8,24,45)


def host(url):
    p = urlsplit(url)
    if p.scheme != "https" or not p.hostname or p.username or p.password or p.port not in (None,443):
        fail("DOWNLOAD_UNSAFE_URL")
    return p.hostname.lower()


def provider_host(url, kind):
    h = host(url)
    if kind == "maps":
        return h in ("mega.nz","mega.co.nz") or h.endswith((".mega.nz",".mega.co.nz"))
    return h == "mediafire.com" or h.endswith(".mediafire.com")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class ProviderRedirect(HTTPRedirectHandler):
    def __init__(self, kind):
        self.kind = kind

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not provider_host(newurl,self.kind):
            fail("DOWNLOAD_UNSAFE_REDIRECT")
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def source_redirect(kind):
    # Preserve the fragment containing the MEGA public file's decryption key.
    # Never send the key to a third-party service.
    req = Request(PAGES[kind], headers={"User-Agent":"Mozilla/5.0"})
    try:
        with build_opener(NoRedirect()).open(req,timeout=45):
            fail("DOWNLOAD_SOURCE_DID_NOT_REDIRECT:"+kind)
    except HTTPError as exc:
        try:
            if exc.code in TRANSIENT_HTTP:
                raise
            if exc.code not in (301,302,303,307,308):
                fail("DOWNLOAD_SOURCE_HTTP_%d:%s"%(exc.code,kind))
            location = exc.headers.get("Location","")
        finally:
            exc.close()
    if not provider_host(location,kind):
        fail("DOWNLOAD_SOURCE_PROVIDER_CHANGED:"+kind)
    return location


def provider_open(url, kind, body=None):
    if not provider_host(url,kind):
        fail("DOWNLOAD_UNSAFE_PROVIDER")
    headers={"User-Agent":"Mozilla/5.0","Accept-Encoding":"identity"}
    if body is not None:
        headers["Content-Type"]="application/json"
    return build_opener(ProviderRedirect(kind)).open(
        Request(url,data=body,headers=headers),timeout=60)


def bounded_read(response,limit):
    blob=response.read(limit+1)
    if len(blob)>limit:
        fail("DOWNLOAD_RESPONSE_TOO_LARGE")
    return blob


class DownloadLink(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[]

    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="a" and a.get("id")=="downloadButton":
            self.links.append(a.get("href",""))


def mediafire_url(location):
    p=urlsplit(location)
    if not provider_host(location,"overworlds") or not p.path.startswith("/file/"+MEDIAFIRE_ID+"/"):
        fail("DOWNLOAD_MEDIAFIRE_FILE_CHANGED")
    with provider_open(location,"overworlds") as response:
        page=bounded_read(response,2_000_000).decode("utf-8",errors="replace")
    parser=DownloadLink()
    parser.feed(page)
    if len(parser.links)!=1:
        fail("DOWNLOAD_MEDIAFIRE_LINK_MISSING")
    link=parser.links[0]
    if not re.fullmatch(r"download[0-9]+\.mediafire\.com",host(link)):
        fail("DOWNLOAD_MEDIAFIRE_HOST_CHANGED")
    return link


def mega_key(location):
    p=urlsplit(location)
    if not provider_host(location,"maps") or p.path!="/file/"+MEGA_ID:
        fail("DOWNLOAD_MEGA_FILE_CHANGED")
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}",p.fragment):
        fail("DOWNLOAD_MEGA_PUBLIC_KEY_MISSING")
    raw=base64.urlsafe_b64decode(p.fragment+"=")
    return bytes(a^b for a,b in zip(raw[:16],raw[16:])),raw[16:24]


def mega_url():
    body=json.dumps([{"a":"g","g":1,"p":MEGA_ID,"ssl":2}]).encode()
    with provider_open("https://g.api.mega.co.nz/cs?id=1","maps",body) as response:
        reply=json.loads(bounded_read(response,1_000_000))
    if (not isinstance(reply,list) or len(reply)!=1 or not isinstance(reply[0],dict)
            or reply[0].get("s")!=SIZES["maps"] or not isinstance(reply[0].get("g"),str)):
        fail("DOWNLOAD_MEGA_API_UNAVAILABLE_OR_FILE_CHANGED")
    url=reply[0]["g"]
    if not provider_host(url,"maps"):
        fail("DOWNLOAD_MEGA_HOST_CHANGED")
    return url


class WindowsAES:
    """AES ECB of counter blocks via Windows CNG, no padding."""
    def __init__(self,key):
        if os.name!="nt":
            fail("DOWNLOAD_MEGA_REQUIRES_WINDOWS")
        self.dll=ctypes.WinDLL("bcrypt.dll")
        self.alg=ctypes.c_void_p()
        self.key=ctypes.c_void_p()
        self.obj=None
        self.dll.BCryptOpenAlgorithmProvider.argtypes=[ctypes.POINTER(ctypes.c_void_p),ctypes.c_wchar_p,ctypes.c_wchar_p,ctypes.c_ulong]
        self.dll.BCryptSetProperty.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_ulong]
        self.dll.BCryptGetProperty.argtypes=[ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(ctypes.c_ulong),ctypes.c_ulong]
        self.dll.BCryptGenerateSymmetricKey.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_void_p),ctypes.c_void_p,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_ulong]
        self.dll.BCryptEncrypt.argtypes=[ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_ulong,ctypes.c_void_p,ctypes.c_ulong,ctypes.POINTER(ctypes.c_ulong),ctypes.c_ulong]
        self.dll.BCryptDestroyKey.argtypes=[ctypes.c_void_p]
        self.dll.BCryptCloseAlgorithmProvider.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
        try:
            self.check(self.dll.BCryptOpenAlgorithmProvider(ctypes.byref(self.alg),"AES",None,0))
            mode=ctypes.create_unicode_buffer("ChainingModeECB")
            self.check(self.dll.BCryptSetProperty(self.alg,"ChainingMode",mode,ctypes.sizeof(mode),0))
            size=ctypes.c_ulong();used=ctypes.c_ulong()
            self.check(self.dll.BCryptGetProperty(self.alg,"ObjectLength",ctypes.byref(size),ctypes.sizeof(size),ctypes.byref(used),0))
            if not 0<size.value<=1_000_000:
                fail("DOWNLOAD_CNG_OBJECT_LENGTH")
            self.obj=ctypes.create_string_buffer(size.value)
            secret=ctypes.create_string_buffer(key)
            self.check(self.dll.BCryptGenerateSymmetricKey(self.alg,ctypes.byref(self.key),self.obj,size.value,secret,len(key),0))
        except BaseException:
            self.close()
            raise

    @staticmethod
    def check(status):
        if status!=0:
            fail("DOWNLOAD_WINDOWS_AES_ERROR")

    def encrypt(self,data):
        inp=ctypes.create_string_buffer(data)
        out=ctypes.create_string_buffer(len(data))
        used=ctypes.c_ulong()
        self.check(self.dll.BCryptEncrypt(self.key,inp,len(data),None,None,0,out,len(data),ctypes.byref(used),0))
        if used.value!=len(data):
            fail("DOWNLOAD_WINDOWS_AES_SIZE")
        return out.raw

    def close(self):
        if self.key.value:
            self.dll.BCryptDestroyKey(self.key);self.key=ctypes.c_void_p()
        if self.alg.value:
            self.dll.BCryptCloseAlgorithmProvider(self.alg,0);self.alg=ctypes.c_void_p()

    def __enter__(self):
        return self

    def __exit__(self,*exc):
        self.close()


def decrypt_ctr(encrypt,nonce,offset,blob):
    if len(nonce)!=8 or offset%16:
        fail("DOWNLOAD_MEGA_COUNTER_ALIGNMENT")
    start=offset//16
    count=(len(blob)+15)//16
    counters=b"".join(nonce+i.to_bytes(8,"big") for i in range(start,start+count))
    stream=encrypt(counters)[:len(blob)]
    if len(stream)!=len(blob):
        fail("DOWNLOAD_MEGA_COUNTER_SIZE")
    return (int.from_bytes(blob,"little")^int.from_bytes(stream,"little")).to_bytes(len(blob),"little")


def stream_to_file(response,output,kind,transform=None):
    expected=SIZES[kind]
    digest=hashlib.sha256()
    total=0
    next_report=0
    while total<expected:
        n=min(CHUNK,expected-total)
        raw=response.read(n)
        if len(raw)!=n:
            fail("DOWNLOAD_TRUNCATED:"+kind)
        if transform:
            raw=transform(total,raw)
        if len(raw)!=n:
            fail("DOWNLOAD_TRANSFORM_SIZE")
        digest.update(raw);output.write(raw);total+=n
        if total>=next_report or total==expected:
            print("SINNOH QA: %s %d%%"%(kind,total*100//expected),flush=True)
            next_report=total+8*CHUNK
    if response.read(1):
        fail("DOWNLOAD_SIZE_MISMATCH:"+kind)
    if digest.hexdigest()!=PACKS[kind][1]:
        fail("DOWNLOAD_SHA256_MISMATCH:"+kind)


def download(kind,output):
    # Record only the stage and resource name, never the URL/key.
    print("SINNOH QA: consultando redirecionamento original "+kind,flush=True)
    location=source_redirect(kind)
    print("SINNOH QA: redirecionamento original confirmado "+kind,flush=True)
    if kind=="maps":
        key,nonce=mega_key(location)
        url=mega_url()
        with WindowsAES(key) as aes, provider_open(url,kind) as response:
            stream_to_file(response,output,kind,lambda offset,data:decrypt_ctr(aes.encrypt,nonce,offset,data))
    else:
        url=mediafire_url(location)
        with provider_open(url,kind) as response:
            stream_to_file(response,output,kind)


def retry_download(kind,output,fetch=download,pause=time.sleep):
    """Retry transient provider failures only; never retry integrity errors."""
    attempts=len(RETRY_DELAYS)+1
    for attempt in range(attempts):
        try:
            return fetch(kind,output)
        except (URLError,TimeoutError,ConnectionError) as exc:
            if isinstance(exc,HTTPError) and exc.code not in TRANSIENT_HTTP:
                raise
            if attempt==attempts-1:raise
            output.seek(0);output.truncate(0)
            delay=RETRY_DELAYS[attempt]
            print("SINNOH QA: falha transitoria na fonte %s; tentativa %d/%d apos %ds"%(kind,attempt+2,attempts,delay),flush=True)
            pause(delay)

def ensure_sources(project,fetch=retry_download):
    # Explicit Sinnoh click only. Existing valid local archives take precedence.
    from install_sinnoh_experimental_windows import safe_path
    project=safe_path(Path(project).absolute())
    found=discover(project)
    if len(found)==len(PACKS):
        return found
    cache=safe_path(project/".blue-work"/"sinnoh-private-input")
    cache.mkdir(parents=True,exist_ok=True)
    safe_path(cache)
    for kind,(name,_) in PACKS.items():
        if kind in found:
            continue
        target=safe_path(cache/name)
        temp=None
        print("SINNOH QA: baixando %s da fonte original..."%name,flush=True)
        try:
            with tempfile.NamedTemporaryFile(dir=cache,prefix=".sinnoh-",suffix=".part",delete=False) as output:
                temp=Path(output.name)
                fetch(kind,output)
                output.flush();os.fsync(output.fileno())
            with verified_archive(temp,kind):
                pass
            if target.exists():
                with verified_archive(target,kind):
                    pass
            else:
                # Same-directory rename. No source is extracted or published.
                os.replace(temp,target)
            found[kind]=target
        except (OSError,ValueError,TypeError,KeyError) as exc:
            # No signed URLs or MEGA public-key fragments in the visible log.
            fail("DOWNLOAD_FAILED:"+kind+":"+type(exc).__name__)
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
    return found
