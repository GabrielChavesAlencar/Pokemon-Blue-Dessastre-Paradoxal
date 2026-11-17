#!/usr/bin/env python3
"""E04 public MediaFire origin probe, ephemeral and fail-closed.

Queries the two FIXED files linked by the original project's author. When
--download is given, optionally downloads to .blue-work ONLY and validates
ZIP metadata; never extracts, executes, publishes, installs or changes game/.
The report always distinguishes file-provider metadata from rights and origin
attestation. Copyrighted source bytes must NEVER enter Git/artifacts.
"""
from __future__ import annotations

import argparse
import hashlib
import html
from html.parser import HTMLParser
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import (
    HTTPRedirectHandler, Request, build_opener,
)

from audit_unova_u02 import audit_zip

ROOT = Path(__file__).resolve().parents[2]
POST = "https://www.reddit.com/r/PokemonRMXP/comments/wsiyyr/"
MEDIAFIRE = "https://www.mediafire.com"
FIXED = {
    "zip": ("tq5w0in2xt2peb1", "Pokemon_World_V18.zip"),
    "credits": ("gdtsjg5lbnstzo1", "Credits.txt"),
}
MAX_JSON = 512 * 1024
MAX_HTML = 2 * 1024 * 1024
MAX_SOURCE = 2_000_000_000
MAX_CREDITS = 512_000
CHUNK = 1024 * 1024
UA = "Mozilla/5.0 (compatible; UnovaMetadataAudit/1.0; source-verification)"
DOWNLOAD_RX = re.compile(r"https://download\d+\.mediafire\.com/[^\s\"'<>]+", re.I)


class SourceBlocked(Exception):
    pass


def block(reason):
    raise SourceBlocked(reason)


def is_mediafire_url(url: str) -> bool:
    if not isinstance(url, str):
        return False
    obj = urlparse(url)
    host = (obj.hostname or "").lower()
    return (
        obj.scheme == "https" and
        (host == "mediafire.com" or host.endswith(".mediafire.com")) and
        obj.username is None and obj.password is None and
        (obj.port in (None, 443))
    )


class SafeRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not is_mediafire_url(newurl):
            block("REDIRECT_FORA_MEDIAFIRE")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


OPENER = build_opener(SafeRedirect)


def request_bounded(url: str, *, post: dict | None = None, limit: int = MAX_JSON) -> bytes:
    if not is_mediafire_url(url):
        block("URL_FORA_DOMINIO_PERMITIDO")
    payload = urlencode(post).encode("ascii") if post else None
    req = Request(url, data=payload, headers={
        "User-Agent": UA, "Accept": "application/json" if post else "text/html",
    })
    with OPENER.open(req, timeout=30) as response:
        if not is_mediafire_url(response.url):
            block("URL_FINAL_FORA_DOMINIO")
        body = response.read(limit + 1)
    if len(body) > limit:
        block("RESPOSTA_REMOTA_GRANDE_DEMAIS")
    return body


def get_api_file_info(key: str) -> dict:
    if key not in (x[0] for x in FIXED.values()):
        block("CHAVE_FORA_DA_FONTE_ORIGINAL")
    url = MEDIAFIRE + "/api/1.5/file/get_info.php"
    data = request_bounded(url, post={"quick_key": key, "response_format": "json"})
    try:
        obj = json.loads(data.decode("utf-8-sig"))
        response = obj["response"]
        if response.get("result") != "Success":
            block("API: " + str(response.get("message", "indisponivel"))[:120])
        info = response["file_info"]
        if not isinstance(info, dict) or info.get("quickkey", info.get("quick_key")) not in (key, None):
            block("INFO_DIVERGENTE")
        return info
    except (TypeError, ValueError, KeyError, UnicodeError) as exc:
        block("RESPOSTA_API_INESPERADA: " + exc.__class__.__name__)


class DownloadButton(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        data = dict(attrs)
        if data.get("id") == "downloadButton":
            self.href = data.get("href")


def get_direct_link(quickkey: str, filename: str, info: dict) -> str:
    links = info.get("links", {})
    if isinstance(links, dict):
        for field in ("direct_download",):
            url = links.get(field)
            if isinstance(url, str) and DOWNLOAD_RX.fullmatch(url) and is_mediafire_url(url):
                return url
    page = f"{MEDIAFIRE}/file/{quickkey}/{filename}/file"
    body = request_bounded(page, limit=MAX_HTML).decode("utf-8", errors="replace")
    parser = DownloadButton()
    parser.feed(body)
    values = [parser.href, *(DOWNLOAD_RX.findall(html.unescape(body))[:8])]
    for value in values:
        if not value:
            continue
        url = html.unescape(value)
        if DOWNLOAD_RX.fullmatch(url) and is_mediafire_url(url):
            return url
    block("LINK_DIRETO_NAO_ENCONTRADO_NA_PAGINA_PUBLICA")


def verify_workspace(root: Path) -> tuple[Path, Path]:
    root = root.absolute()
    if not root.is_dir() or root.is_symlink():
        block("RAIZ_INVALIDA")
    local = root / ".blue-work/unova"
    sources = local / "sources"
    audit = local / "audit"
    for folder in (root / ".blue-work", local, sources, audit):
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            block("PASTA_PRIVADA_INSEGURA")
    sources.mkdir(parents=True, exist_ok=True)
    audit.mkdir(parents=True, exist_ok=True)
    return sources, audit


def download_private(root: Path, url: str, filename: str, claimed_size: int, limit: int) -> dict:
    if not is_mediafire_url(url) or not DOWNLOAD_RX.fullmatch(url):
        block("URL_BINARIA_NAO_PERMITIDA")
    sources, _ = verify_workspace(root)
    target = sources / filename
    if target.is_symlink() or target.exists():
        block("ARQUIVO_LOCAL_EXISTENTE_NAO_SUBSTITUIR")
    if claimed_size < 1 or claimed_size > limit:
        block("TAMANHO_DA_FONTE_FORA_LIMITE")
    temp = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=sources, prefix=".remote-unova-", delete=False) as dst:
            temp = Path(dst.name)
            req = Request(url, headers={"User-Agent": UA, "Accept": "application/octet-stream"})
            with OPENER.open(req, timeout=80) as src:
                if not is_mediafire_url(src.url):
                    block("BINARIO_REDIRIGIDO_PARA_FORA_DO_PROVIDER")
                ct = (src.headers.get("Content-Type") or "").lower()
                if "text/html" in ct:
                    block("MEDIAFIRE_RETORNOU_HTML_EM_VEZ_DE_ARQUIVO")
                digest = hashlib.sha256()
                size = 0
                while True:
                    chunk = src.read(CHUNK)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > limit or size > claimed_size:
                        block("ARQUIVO_EXCEDE_TAMANHO_DECLARADO")
                    dst.write(chunk)
                    digest.update(chunk)
            dst.flush()
            os.fsync(dst.fileno())
        if size != claimed_size:
            block("DOWNLOAD_INCOMPLETO_TAMANHO_DIVERGENTE")
        if target.exists() or target.is_symlink():
            block("FONTE_PREEXISTENTE_NAO_SUBSTITUIR")
        temp.rename(target)
        return {"bytes": size, "sha256": digest.hexdigest(),
                "private_path": str(target.relative_to(root)), "path": target}
    finally:
        if temp is not None and temp.exists():
            temp.unlink(missing_ok=True)


def safe_meta(info: dict, key: str) -> dict:
    # No authentication tokens, private links, uploader emails or rights claims.
    filename = info.get("filename")
    try:
        size = int(info.get("size"))
    except (ValueError, TypeError):
        block("METADADOS_SEM_TAMANHO")
    if not isinstance(filename, str) or len(filename) > 200 or size <= 0:
        block("METADADOS_INVALIDOS")
    return {
        "quickkey": key,
        "provider_filename": filename,
        "provider_size_bytes": size,
        "provider_hash_unverified": info.get("hash") if isinstance(info.get("hash"), str) else None,
        "provider_upload_date_unverified": info.get("created") if isinstance(info.get("created"), str) else None,
    }


def probe(project: Path, *, download: bool) -> dict:
    # E04 stays unapproved unless source bytes and origin/rights evidence are reviewed.
    report = {
        "schema": 1, "region": "UNOVA", "phase": "E04",
        "mode": "MEDIAFIRE_ORIGINAL_LINK_PROBE_EPHEMERAL",
        "status": "BLOCKED_SOURCE_NOT_OBTAINED",
        "source_post": POST,
        "original_mediafire_keys": {k:v[0] for k,v in FIXED.items()},
        "provider_file_info": {}, "download_attempted": download,
        "zip_downloaded": False, "zip_sha256": None, "zip_bytes": None,
        "whole_donor_project_map_count": None,
        "unova_map_count": None,
        "credits_downloaded": False, "credits_sha256": None,
        "source_identity_verified_with_author": False,
        "copyright_rights_verified": False, "rights_per_asset_verified": False,
        "may_redistribute": False, "game_files_modified": False,
        "may_install": False, "game_exe_tested": False,
        "android_tested": False, "e04_complete": False,
        "errors": [],
    }
    for kind, (key, expected_name) in FIXED.items():
        try:
            raw = get_api_file_info(key)
            obj = safe_meta(raw, key)
            report["provider_file_info"][kind] = obj
            approved_names = (
                {"Pokemon_World_V18.zip", "Pokemon World V18.zip"}
                if kind == "zip" else {"Credits.txt"}
            )
            if obj["provider_filename"].casefold() not in {
                name.casefold() for name in approved_names
            }:
                report["errors"].append(kind + ": NOME_ARQUIVO_DIVERGENTE")
                continue
            if not download:
                continue
            if obj["provider_size_bytes"] > (MAX_SOURCE if kind == "zip" else MAX_CREDITS):
                report["errors"].append(kind + ": ARQUIVO_MAIOR_QUE_LIMITE")
                continue
            url = get_direct_link(key, expected_name, raw)
            entry = download_private(
                project, url, expected_name, obj["provider_size_bytes"],
                MAX_SOURCE if kind == "zip" else MAX_CREDITS,
            )
            if kind == "zip":
                try:
                    audited = audit_zip(entry["path"])
                except (ValueError, OSError, Exception) as exc:
                    # Only .blue-work private bytes exist; will be discarded on runner.
                    report["errors"].append("zip: ESTRUTURA_NAO_AUDITADA_" + type(exc).__name__)
                    continue
                report["zip_downloaded"] = True
                report["zip_sha256"] = entry["sha256"]
                report["zip_bytes"] = entry["bytes"]
                report["whole_donor_project_map_count"] = audited["all_regions_source_map_count"]
            else:
                report["credits_downloaded"] = True
                report["credits_sha256"] = entry["sha256"]
        except (SourceBlocked, HTTPError, URLError, TimeoutError, OSError) as exc:
            if isinstance(exc, SourceBlocked):
                error = str(exc)
            elif isinstance(exc, HTTPError):
                error = f"HTTP_{exc.code}"
            else:
                error = type(exc).__name__
            report["errors"].append(kind + ": " + error[:150])
    if report["zip_downloaded"]:
        report["status"] = "PRIVATE_SOURCE_BYTES_AUDITED_NOT_LICENSED"
    elif report["provider_file_info"].get("zip"):
        report["status"] = "PROVIDER_METADATA_ONLY_NOT_SOURCE_AUDIT"
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", type=Path, default=ROOT)
    p.add_argument("--download", action="store_true",
                   help="Attempt temporary download on runner; never publish source bytes")
    args = p.parse_args(argv)
    project = args.project.absolute()
    result = probe(project, download=args.download)
    _, audit = verify_workspace(project)
    path = audit / "e04-remote-origin-probe.json"
    if path.is_symlink():
        block("SYMLINK_RELATORIO")
    # Run-specific CI workspace. Never overwrite an existing report with differing evidence.
    payload = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if path.exists():
        if path.read_text("utf-8") != payload:
            block("EVIDENCIA_DIFERENTE_RELATORIO_EXISTENTE")
    else:
        path.write_text(payload, encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    # A blocked remote source is an expected recorded outcome, not false success.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
