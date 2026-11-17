#!/usr/bin/env python3
"""E06: create a PRIVATE per-asset rights checklist from a donor ZIP.

No extraction, execution, music copying, or licensing assumptions.
Even Credits.txt only proves a file is present, not permission to redistribute.
"""
from __future__ import annotations

import argparse
import json
import hashlib
import sys
import zipfile
from pathlib import Path

from audit_unova_u02 import audit_zip, is_within_source, safe_parts, fail

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(".blue-work/unova/audit/e06-rights-inventory.json")
MAX_CREDITS = 512_000
MAX_RIGHTS_ENTRIES = 60000


def group_name(path: str) -> str:
    rel = path.casefold()
    if rel.startswith("graphics/"):
        if rel.startswith("graphics/characters/"):
            return "character_sprites"
        if rel.startswith("graphics/tilesets/"):
            return "tilesets"
        if rel.startswith("graphics/autotiles/"):
            return "autotiles"
        return "other_graphics"
    if rel.startswith("audio/bgm/") or rel.startswith("audio/bgs/"):
        return "audio_bgm_bgs"
    if rel.startswith("audio/me/") or rel.startswith("audio/se/"):
        return "audio_me_se"
    if rel.startswith("data/map") and rel.endswith(".rxdata"):
        return "map_geometry_and_events"
    if rel.startswith("data/"):
        return "other_rmxp_data"
    if rel.startswith("pbs/"):
        return "pbs_data"
    if rel.startswith("plugins/"):
        return "plugins"
    return "other_unclassified"


def sha256_bytes(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024*1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def credits_status(project: Path, filename: Path | None) -> dict:
    if filename is None:
        filename = project / ".blue-work/unova/sources/Credits.txt"
    allowed = project / ".blue-work/unova/sources"
    path = filename.absolute()
    if path != allowed / "Credits.txt":
        fail("Credits.txt deve estar na pasta de fontes com nome exato")
    for folder in (project/".blue-work", project/".blue-work"/"unova", allowed, path):
        if folder.is_symlink():
            fail("Credits.txt contem symlink")
    if not path.is_file():
        return {"credits_file_present": False, "credits_sha256": None,
                "credits_lines": None, "credits_are_reuse_permission": False}
    if path.stat().st_size > MAX_CREDITS:
        fail("Credits.txt grande demais")
    raw = path.read_bytes()
    # Don't copy or commit any third-party credit text. Just hash and count lines.
    return {
        "credits_file_present": True,
        "credits_sha256": hashlib.sha256(raw).hexdigest(),
        "credits_lines": len(raw.decode("utf-8-sig", errors="replace").splitlines()),
        "credits_are_reuse_permission": False,
    }


def inspect(project: Path, source: Path, credits: Path | None = None) -> dict:
    project = Path(project).absolute()
    if not is_within_source(project, source):
        fail("ZIP deve ficar em .blue-work/unova/sources; symlink bloqueado")
    meta = audit_zip(source)
    base = tuple(x.casefold() for x in meta["project_wrapper"].split("/") if x)
    rows = []
    total_zip_members = 0
    with zipfile.ZipFile(source) as archive:
        for member in archive.infolist():
            if member.is_dir():
                continue
            total_zip_members += 1
            parts = safe_parts(member.filename)
            if tuple(x.casefold() for x in parts[:len(base)]) != base:
                continue
            rel_parts = parts[len(base):]
            if len(rel_parts) < 2:
                continue
            relative = "/".join(rel_parts)
            group = group_name(relative)
            if group == "other_unclassified":
                continue
            if len(rows) >= MAX_RIGHTS_ENTRIES:
                fail("inventario de direitos excedeu limite")
            rows.append({
                "source_path": relative,
                "category": group,
                "bytes_declared": member.file_size,
                "zip_crc32_reference_only": format(member.CRC, "08x"),
                "authors": [],
                "license_url": None,
                "reuse_permission_document": None,
                "rights_status": "REVIEW_REQUIRED_NOT_LICENSED",
                "can_redistribute": False,
                "approved_for_game": False,
            })
    if not rows:
        fail("ZIP sem assets identificados")
    rows.sort(key=lambda row: row["source_path"].casefold())
    return {
        "schema": 1, "region": "UNOVA", "phase": "E06",
        "mode": "PRIVATE_ASSET_PROVENANCE_INDEX_NO_INSTALL",
        "status": "RIGHTS_UNVERIFIED_SOURCE_CONTENT_NOT_CLEARED",
        "source_zip_sha256": meta["archive_sha256"],
        "whole_donor_project_map_count": meta["all_regions_source_map_count"],
        "all_file_count_in_zip": total_zip_members,
        "classified_asset_count": len(rows),
        "credits": credits_status(project, credits),
        "assets": rows,
        "all_assets_rights_cleared": False,
        "license_verified": False,
        "redistribution_approved": False,
        "game_or_saves_modified": False,
        "game_exe_tested": False,
        "can_install": False,
        "next_action": ("Verificar cada asset com o autor e Credits.txt. "
                        "Substituir por recurso original/licenciado qualquer arquivo sem permissao clara."),
    }


def save(project: Path, report: dict) -> Path:
    project = project.absolute()
    work = project / ".blue-work"
    local = work / "unova"
    dest = local / "audit"
    for path in (work, local, dest):
        if path.is_symlink() or (path.exists() and not path.is_dir()):
            fail("pasta de relatorio insegura")
    dest.mkdir(parents=True, exist_ok=True)
    output = project / OUTPUT
    if output.is_symlink():
        fail("relatorio symlink")
    payload = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if output.exists():
        if output.read_text("utf-8") != payload:
            fail("relatorio E06 anterior diverge; nao sobrescrever provas")
    else:
        with output.open("x", encoding="utf-8") as fh:
            fh.write(payload)
    return output


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--credits", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    project = args.project.absolute()
    source = args.source or project/".blue-work/unova/sources/Pokemon_World_V18.zip"
    try:
        report = inspect(project, source, args.credits)
        if args.write:
            save(project, report)
        print(json.dumps({k:v for k,v in report.items() if k != "assets"},
                         indent=2,ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError, zipfile.BadZipFile) as exc:
        print("UNOVA_E06_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
