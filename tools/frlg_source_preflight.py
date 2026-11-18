#!/usr/bin/env python3
"""Fail-closed FRLG source-only verifier. No extract, run, store or artifact."""
import argparse
import hashlib
import hmac
import ipaddress
import json
import os
from pathlib import Path
import sys
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data/regions/kanto-source.json"
PIN = "48883c8217bcd9e7fa1b9446bddaa9db5f9715a7ba73ac02785b6660769e2683"
MAX_SIZE = 700 * 1024 * 1024
RAR4 = b"Rar!\x1a\x07\x00"
RAR5 = b"Rar!\x1a\x07\x01\x00"

class SourceRejected(ValueError):
    pass

def validate_manifest(path=MANIFEST):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("region") != "KANTO":
        raise SourceRejected("Wrong source/region")
    if data.get("sha256") != PIN:
        raise SourceRejected("Pinned SHA-256 changed")
    if data.get("source") != "https://eeveeexpo.com/resources/1797/":
        raise SourceRejected("Original source URL changed")
    if data.get("author") != "TheTinfoilTemplar":
        raise SourceRejected("Original author changed")
    if "do not redistribute the archive" not in data.get("policy", ""):
        raise SourceRejected("Rights restriction missing")
    return PIN

def verify_stream(stream, expected=PIN, limit=MAX_SIZE):
    if not isinstance(expected,str) or len(expected)!=64 or any(c not in "0123456789abcdef" for c in expected):
        raise SourceRejected("Malformed expected SHA-256")
    sha = hashlib.sha256()
    n = 0
    prefix = b""
    while True:
        chunk = stream.read(1024 * 1024)
        if not chunk:
            break
        n += len(chunk)
        if n > limit:
            raise SourceRejected("Too large")
        if len(prefix) < len(RAR5):
            prefix = (prefix + chunk)[:len(RAR5)]
        sha.update(chunk)
    if n < len(RAR4) or not (prefix.startswith(RAR4) or prefix.startswith(RAR5)):
        raise SourceRejected("Not an original RAR (ZIP/HTML/quota?)")
    if not hmac.compare_digest(sha.hexdigest(),expected):
        raise SourceRejected("SHA-256 mismatch")
    return n

def verify_file(path):
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_SIZE:
        raise SourceRejected("Invalid local source")
    with path.open("rb") as f:
        return verify_stream(f)

def require_https(url):
    try:
        p = urllib.parse.urlsplit(url)
        if p.scheme!="https" or not p.hostname or p.username or p.password or p.fragment:
            raise SourceRejected("HTTPS public host required")
        host=p.hostname.lower()
        if host in ("localhost","localhost.localdomain") or host.endswith(".local"):
            raise SourceRejected("Local host prohibited")
        try:
            addr=ipaddress.ip_address(host)
        except ValueError:
            return
        if not addr.is_global:
            raise SourceRejected("Private/nonpublic host prohibited")
    except ValueError:
        raise SourceRejected("Invalid HTTPS URL") from None

class HTTPSRedirectsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        require_https(newurl)
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def verify_secret_url(var="FRLG_SOURCE_URL"):
    url=os.environ.get(var,"")
    if not url:
        raise SourceRejected("No authorized secret source URL")
    require_https(url)
    opener=urllib.request.build_opener(HTTPSRedirectsOnly())
    req=urllib.request.Request(url, headers={"User-Agent":"frlg-preflight/1"})
    try:
        with opener.open(req,timeout=90) as res:
            length=res.headers.get("Content-Length")
            if length and int(length)>MAX_SIZE:
                raise SourceRejected("Too large")
            return verify_stream(res)
    except SourceRejected:
        raise
    except Exception:
        # Do not expose signed URLs embedded in network exceptions.
        raise SourceRejected("Remote download failed (URL redacted)") from None

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    opts=p.add_mutually_exclusive_group(required=True)
    opts.add_argument("--check-config",action="store_true")
    opts.add_argument("--file",type=Path)
    opts.add_argument("--from-secret-env",action="store_true")
    a=p.parse_args(argv)
    try:
        validate_manifest()
        if a.check_config:
            print("FRLG_SOURCE_PIN_VALID; no archive accessed")
        else:
            size=verify_file(a.file) if a.file is not None else verify_secret_url()
            print("FRLG_SOURCE_SHA256_MATCH; bytes=%d; no extraction/execution" % size)
        return 0
    except (SourceRejected,OSError,ValueError) as e:
        print("FRLG_SOURCE_REJECTED: %s" % e,file=sys.stderr)
        return 1

if __name__=="__main__":
    sys.exit(main())
