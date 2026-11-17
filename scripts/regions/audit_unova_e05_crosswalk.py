#!/usr/bin/env python3
"""E05: compare inert donor MapInfos audit with Unova's symbolic 74-area catalog.

No donor executable or Ruby script is run. No source/destination MapIDs are
allocated and no candidate is marked as imported or confirmed to be Unova.
A name match is a research lead, NEVER a verified donor map.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

from audit_unova_source_detail import normalized

ROOT = Path(__file__).resolve().parents[2]
SOURCE_REPORT = Path(".blue-work/unova/audit/u02-rxdata-detail.json")
OUTPUT = Path(".blue-work/unova/audit/e05-crosswalk.json")
CATALOG = Path("data/regions/unova-u03-areas.json")
HEX = re.compile(r"[a-f0-9]{64}\Z")
GENERIC = {"route", "victory road", "pokemon league", "elite four", "pokemon center",
           "pokecenter", "gym", "cave", "p2 laboratory"}
MAX_AUDIT = 24 * 1024 * 1024


def reject(message: str) -> None:
    raise ValueError("UNOVA_E05_BLOQUEADO: " + message)


def inside(project: Path, candidate: Path, subdir: str) -> Path:
    project = project.absolute()
    allowed = project / ".blue-work" / "unova" / subdir
    path = candidate.absolute()
    if not path.is_relative_to(allowed) or path == allowed:
        reject("relatorio fora da area .blue-work/unova/" + subdir)
    # Check every component below the known project root. Never follow symlinks.
    for folder in (project / ".blue-work", project / ".blue-work" / "unova", allowed, path):
        if folder.is_symlink():
            reject("symlink em entrada/saida")
    if not path.resolve().is_relative_to(allowed.resolve()):
        reject("caminho resolve fora da pasta privada")
    return path


def read_json(path: Path, size: int = MAX_AUDIT) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > size:
        reject("JSON ausente, symlink ou grande demais")
    obj = json.loads(path.read_text("utf-8-sig"))
    if not isinstance(obj, dict):
        reject("JSON nao e objeto")
    return obj


def verify_source(report: dict) -> list[dict]:
    if (report.get("schema"), report.get("region"), report.get("phase"),
        report.get("mode"), report.get("status")) != (
            1, "UNOVA", "U02_E05", "READ_ONLY_INERT_SOURCE_INSPECTION",
            "SOURCE_RXDATA_INSPECTED_NOT_APPROVED"):
        reject("relatorio RXDATA real e inerte obrigatorio")
    if any(report.get(k) is not False for k in (
        "rights_verified", "native_mapinfos_verified", "can_install",
        "game_or_saves_modified", "game_exe_tested", "android_tested")):
        reject("relatorio afirma direito, alteracao de jogo ou QA inexistente")
    if report.get("confirmed_unova_map_count") is not None:
        reject("fonte nao pode se declarar Unova confirmada automaticamente")
    for k in ("source_zip_sha256", "source_mapinfos_sha256"):
        if not isinstance(report.get(k), str) or not HEX.fullmatch(report[k]):
            reject("hash real ausente/invalido: " + k)
    maps = report.get("maps")
    if (not isinstance(maps, list) or not maps or len(maps) > 7500 or
            report.get("all_regions_source_map_count") != len(maps)):
        reject("total de mapas do projeto nao confere")
    found = set()
    for row in maps:
        if not isinstance(row, dict):
            reject("linha doadora invalida")
        mid = row.get("source_map_id")
        if type(mid) is not int or mid < 1 or mid > 99999 or mid in found:
            reject("MapID fonte duplicado/invalido")
        found.add(mid)
        if not isinstance(row.get("name"), str) or len(row["name"]) > 200:
            reject("nome fonte ausente/invalido")
        if not isinstance(row.get("source_sha256"), str) or not HEX.fullmatch(row["source_sha256"]):
            reject("hash de mapa invalido")
        for number in ("event_count", "event_pages", "static_transfer_commands",
                       "dynamic_transfer_commands", "untrusted_script_commands_not_executed"):
            if type(row.get(number)) is not int or row[number] < 0:
                reject("contagem de evento invalida")
        ids = row.get("static_transfer_target_ids")
        if not isinstance(ids, list) or any(type(x) is not int or x < 1 for x in ids):
            reject("transferencias invalidas")
        if (row.get("candidate_confirmed_as_unova") is not False or
                row.get("destination_map_id") is not None or
                row.get("rights_verified") is not False or
                row.get("compiled_in_game") is not False):
            reject("mapeamento ou direito falsamente aprovado")
    return maps


def verify_areas(catalog: dict) -> list[dict]:
    if (catalog.get("schema"), catalog.get("region"),
        catalog.get("reference_version"), catalog.get("state"),
        catalog.get("may_install"), catalog.get("unova_game_files_audited")) != (
            1, "UNOVA", "WHITE_BW", "PLANNED_REFERENCE_ONLY", False, False):
        reject("catalogo deve permanecer em planejamento")
    areas = catalog.get("areas")
    if not isinstance(areas, list) or len(areas) != 74:
        reject("catalogo de 74 areas ausente")
    unique = set()
    for row in areas:
        if not isinstance(row, dict) or not isinstance(row.get("key"), str) or row["key"] in unique:
            reject("area ausente/duplicada")
        unique.add(row["key"])
        if (row.get("state") != "planned" or row.get("source_map_id") is not None or
            row.get("destination_map_id") is not None or
            row.get("game_exe_tested") is not False or
            row.get("distribution_rights_verified") is not False):
            reject("area ja declara importacao/QA/direitos falsos")
    return areas


def classify(report: dict, catalog: dict) -> dict:
    maps = verify_source(report)
    areas = verify_areas(catalog)
    matches = defaultdict(list)
    names = Counter(normalized(row["name"]) for row in maps)
    for row in maps:
        name = normalized(row["name"])
        for area in areas:
            area_name = normalized(area["name"])
            # Route 1, Victory Road, etc. occur in several regions and cannot
            # establish Unova origin from name alone.
            if name == area_name:
                matches[area["key"]].append(row)
    rows = []
    stats = Counter()
    for area in areas:
        name = normalized(area["name"])
        candidates = sorted(matches.get(area["key"], []), key=lambda x:x["source_map_id"])
        generic = (area.get("kind") == "route" or name in GENERIC or
                   name.startswith("pokemon league") or name.startswith("elite four"))
        if not candidates:
            status = "NO_NAME_MATCH_NOT_PROOF_OF_ABSENCE"
        elif generic:
            status = "GENERIC_NAME_UNRESOLVED"
        elif len(candidates) > 1 or names[name] > 1:
            status = "MULTIPLE_NAME_MATCHES_UNRESOLVED"
        else:
            status = "SINGLE_NAME_CANDIDATE_UNCONFIRMED"
        stats[status] += 1
        rows.append({
            "area_key": area["key"], "area_name": area["name"],
            "chapter": area["chapter"], "planned_phase": area["phase"],
            "status": status, "candidate_source_map_ids": [
                m["source_map_id"] for m in candidates],
            "candidate_source_map_hashes": [m["source_sha256"] for m in candidates],
            "candidate_event_counts": [m["event_count"] for m in candidates],
            "candidate_only": True, "region_identity_confirmed": False,
            "rights_verified": False, "destination_map_id": None,
            "installed": False, "game_exe_tested": False,
            "manual_review_required": True,
        })
    return {
        "schema": 1, "region": "UNOVA", "phase": "E05",
        "mode": "SOURCE_NAME_CROSSWALK_READ_ONLY",
        "status": "CANDIDATES_ONLY_NOT_SOURCE_ACCEPTANCE",
        "source_zip_sha256": report["source_zip_sha256"],
        "source_mapinfos_sha256": report["source_mapinfos_sha256"],
        "whole_donor_project_map_count": len(maps),
        "confirmed_unova_map_count": 0,
        "symbolic_area_count": len(areas), "counts_by_status": dict(sorted(stats.items())),
        "areas": rows,
        "unresolved_source_transfer_ids": report.get("unresolved_transfer_ids", []),
        "copyright_cleared": False, "can_install": False,
        "native_mapids_checked": False, "game_or_saves_modified": False,
        "game_exe_tested": False, "android_tested": False,
        "next_action": "Revisar cada candidato contra coordenadas, interiores, eventos, creditos e o roteiro White; nunca importar por nome somente.",
    }


def save(project: Path, output: Path, data: dict) -> None:
    target = inside(project, output, "audit")
    for folder in (project/".blue-work",project/".blue-work"/"unova",target.parent):
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            reject("pasta de saida insegura")
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if target.exists():
        if target.read_text("utf-8") != payload:
            reject("relatorio ja existe com fonte/conteudo diferente")
    else:
        target.write_text(payload, encoding="utf-8")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--audit", type=Path)
    parser.add_argument("--catalog", type=Path)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    project = args.project.absolute()
    audit_path = args.audit or project/SOURCE_REPORT
    catalog_path = args.catalog or project/CATALOG
    try:
        source = read_json(inside(project, audit_path, "audit"))
        if (catalog_path.is_symlink() or
            catalog_path.absolute() != (project/CATALOG).absolute()):
            reject("catalogo precisa ser o arquivo versionado do projeto")
        doc = read_json(catalog_path)
        output = classify(source, doc)
        if args.write:
            save(project, project/OUTPUT, output)
        print(json.dumps({k:v for k,v in output.items() if k != "areas"},
                         indent=2, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("UNOVA_E05_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
