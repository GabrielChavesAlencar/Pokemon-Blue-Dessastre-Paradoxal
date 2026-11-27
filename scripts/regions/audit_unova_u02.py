#!/usr/bin/env python3
"""U02: inert inventory of a locally provided Pokemon World V18 RMXP ZIP.

Never downloads, extracts, executes, converts, installs, or allocates map IDs.
Only metadata is inspected; RMXP event/scripts and media are never executed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = re.compile(r"Map0*([1-9][0-9]*)\.rxdata\Z", re.IGNORECASE)
MAX_ZIP_BYTES = 4 * 1024**3
MAX_ENTRIES = 60000
MAX_UNCOMPRESSED = 12 * 1024**3
MAX_SINGLE = 768 * 1024**2
MAX_MAPS = 7500
MAX_RATIO = 1000
RESOURCE_FOLDERS = (
    "Graphics/Characters", "Graphics/Tilesets", "Graphics/Autotiles",
    "Graphics/Pictures", "Graphics/Animations", "Audio/BGM", "Audio/BGS",
    "Audio/ME", "Audio/SE", "PBS", "Plugins", "Data",
)


def fail(message: str) -> None:
    raise ValueError("UNOVA_U02_BLOQUEADO: " + message)


def safe_parts(name: str) -> tuple[str, ...]:
    if not name or name[0] == "/" or "\\" in name or "\x00" in name:
        fail("caminho ZIP absoluto ou inseguro")
    parts = tuple(name.rstrip("/").split("/"))
    if any(not p or p in (".", "..") or ":" in p or
           any(ord(ch) < 32 for ch in p) for p in parts):
        fail("caminho ZIP com travessia ou caractere inseguro")
    return parts


def zip_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_zip(source: Path) -> dict:
    """Do not decompress or open any ZIP member; do not infer its region."""
    if source.is_symlink() or not source.is_file():
        fail("ZIP real ausente ou symlink")
    if not (0 < source.stat().st_size <= MAX_ZIP_BYTES):
        fail("tamanho ZIP invalido/maior que limite")
    records = []
    seen = set()
    uncompressed = 0
    with zipfile.ZipFile(source) as archive:
        members = archive.infolist()
        if len(members) > MAX_ENTRIES:
            fail("entradas demais no ZIP")
        for info in members:
            parts = safe_parts(info.orig_filename)
            key = "/".join(parts).casefold()
            if key in seen:
                fail("entrada duplicada por caixa ou caminho: " + info.filename[:90])
            seen.add(key)
            mode = stat.S_IFMT(info.external_attr >> 16)
            if mode == stat.S_IFLNK:
                fail("ZIP contem link simbolico")
            if info.flag_bits & 1:
                fail("ZIP contem membro criptografado")
            if info.file_size > MAX_SINGLE:
                fail("membro excessivamente grande")
            uncompressed += info.file_size
            if uncompressed > MAX_UNCOMPRESSED:
                fail("ZIP ultrapassa limite descompactado")
            if (info.file_size > 1024**2 and
                    info.file_size / max(info.compress_size, 1) > MAX_RATIO):
                fail("risco de ZIP bomb")
            if not info.is_dir():
                records.append((parts, info.file_size))

    # Locate exactly one RMXP Data root; other Data folders are not assumed.
    roots = {}
    for parts, size in records:
        if len(parts) < 2 or parts[-2].casefold() != "data":
            continue
        base = tuple(part.casefold() for part in parts[:-2])
        group = roots.setdefault(base, {"entries": [], "files": set()})
        group["entries"].append((parts[-1], size))
        group["files"].add(parts[-1].casefold())
    candidates = [(base, group) for base, group in roots.items()
                  if {"mapinfos.rxdata", "tilesets.rxdata"} <= group["files"]]
    if len(candidates) != 1:
        fail("esperado um projeto RMXP com MapInfos e Tilesets (encontrados: %d)" % len(candidates))
    base, data = candidates[0]
    if len(base) > 3:
        fail("Data/ esta dentro de wrappers profundos demais")
    ids = {}
    for filename, _ in data["entries"]:
        match = MAP.fullmatch(filename)
        if match:
            number = int(match.group(1))
            if number > 99999:
                fail("MapID fonte fora do limite")
            if number in ids:
                fail("MapID fonte duplicado (com zeros a esquerda)")
            ids[number] = filename
    if not ids or len(ids) > MAX_MAPS:
        fail("projeto sem mapas RMXP ou muitos mapas")
    assets = {folder: {"count": 0, "bytes": 0, "examples": []}
              for folder in RESOURCE_FOLDERS}
    for parts, size in records:
        relative = parts[len(base):] if tuple(p.casefold() for p in parts[:len(base)]) == base else ()
        if len(relative) < 2:
            continue
        rel = "/".join(relative).casefold()
        for folder in RESOURCE_FOLDERS:
            prefix = folder.casefold() + "/"
            if rel.startswith(prefix):
                row = assets[folder]
                row["count"] += 1
                row["bytes"] += size
                if len(row["examples"]) < 12:
                    row["examples"].append("/".join(relative))
                break
    return {
        "schema": 1,
        "region": "UNOVA",
        "phase": "U02",
        "mode": "ZIP_METADATA_READ_ONLY_NO_EXTRACTION",
        "status": "ZIP_METADATA_AUDITED_UNOVA_CONTENT_UNVERIFIED",
        "source_label": "Pokemon World V18 (candidate, not certified)",
        "archive_filename": source.name,
        "archive_size_bytes": source.stat().st_size,
        "archive_sha256": zip_sha256(source),
        "project_wrapper": "/".join(base),
        "entries_total": len(records),
        "uncompressed_bytes_declared": uncompressed,
        "all_regions_source_map_count": len(ids),
        "all_regions_source_map_ids": sorted(ids),
        "unova_map_ids": None,
        "unova_map_count": None,
        "map_names_from_mapinfos_verified": False,
        "map_event_pages_verified": False,
        "assets_by_folder": assets,
        "rights_per_asset_verified": False,
        "native_mapinfos_checked": False,
        "destination_ids_allocated": False,
        "can_install": False,
        "game_or_saves_modified": False,
        "game_exe_tested": False,
        "android_tested": False,
        "blockers": [
            "MapInfos e mapas RMXP ainda precisam de parse inerte para identificar Unova",
            "Direitos de NPCs, mapas, tilesets, eventos e musicas por arquivo pendentes",
            "MapIDs ocupados do Decades/Kanto/Johto/Hoenn/Sinnoh nao foram lidos",
            "Conversao em piloto isolado, compilacao e QA Game.exe/JoiPlay pendentes",
        ],
    }


def missing_source_report() -> dict:
    return {
        "schema": 1, "region": "UNOVA", "phase": "U02",
        "mode": "ZIP_METADATA_READ_ONLY_NO_EXTRACTION",
        "status": "BLOCKED_SOURCE_NOT_PROVIDED",
        "archive_sha256": None, "all_regions_source_map_count": None,
        "unova_map_count": None, "unova_map_ids": None,
        "rights_per_asset_verified": False, "can_install": False,
        "game_or_saves_modified": False, "game_exe_tested": False,
        "android_tested": False,
        "blockers": ["Pokemon_World_V18.zip local ausente: nao e permitido simular mapas ou importar fontes nao auditadas"],
    }


def is_within_source(project: Path, source: Path) -> bool:
    project = project.absolute()
    root = project / ".blue-work" / "unova" / "sources"
    if not source.absolute().is_relative_to(root):
        return False
    # Reject symlinks throughout user-controlled subtree.
    for target in (project / ".blue-work", project / ".blue-work" / "unova", root, source):
        if target.is_symlink():
            return False
    return source.resolve().is_relative_to(root.resolve())


def write_report(project: Path, report: dict) -> Path:
    project = project.absolute()
    dest = project / ".blue-work" / "unova" / "audit"
    for parent in (project / ".blue-work", project / ".blue-work" / "unova", dest):
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            fail("pasta de relatorio insegura")
    if report.get("can_install") is not False or report.get("region") != "UNOVA":
        fail("relatorio declara instalacao proibida como aprovada")
    dest.mkdir(parents=True, exist_ok=True)
    output = dest / "u02-source.json"
    if output.is_symlink():
        fail("saida de relatorio por symlink")
    payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    tmp = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=dest, encoding="utf-8", prefix=".u02-", delete=False) as fh:
            tmp = Path(fh.name)
            fh.write(payload)
            fh.flush()
            os.fsync(fh.fileno())
        tmp.replace(output)
    finally:
        if tmp is not None:
            tmp.unlink(missing_ok=True)
    return output


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project", type=Path, default=ROOT)
    p.add_argument("--source", type=Path,
                   help="ZIP local em .blue-work/unova/sources/ (nunca faz download)")
    p.add_argument("--write", action="store_true", help="gravar somente .blue-work/unova/audit/u02-source.json")
    args = p.parse_args(argv)
    project = args.project.absolute()
    source = args.source or project / ".blue-work/unova/sources/Pokemon_World_V18.zip"
    try:
        if not is_within_source(project, source):
            fail("fonte deve ficar dentro de .blue-work/unova/sources, sem symlink")
        report = audit_zip(source) if source.is_file() else missing_source_report()
        if args.write:
            report["report_path"] = str(write_report(project, report))
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["status"] == "ZIP_METADATA_AUDITED_UNOVA_CONTENT_UNVERIFIED" else 2
    except (OSError, ValueError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
