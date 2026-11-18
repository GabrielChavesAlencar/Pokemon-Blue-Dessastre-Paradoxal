#!/usr/bin/env python3
"""J01 Sinnoh jogável: pré-voo EXECUTÁVEL de fonte e instalação, sem importação.

Lê apenas metadados de game/Data e da fonte RMXP/ZIP indicada. Valida a
topologia Twinleaf→Sandgem e detecta ocupação de MapIDs. Nunca executa
Game.exe/JoiPlay, descompacta ZIP, importa eventos, salva jogos ou instala mapas.
O JSON não inclui paths locais, saves, nomes pessoais nem dados de assets.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_source as source_audit
import audit_sinnoh_twinleaf_events as twinleaf

SOURCE_CONTRACT = ROOT / "data/regions/sinnoh-twinleaf-events.json"
SOURCE_SCHEMA = ROOT / "data/regions/sinnoh-twinleaf-events.schema.json"
LOCAL_REPORT = ".blue-work/sinnoh-jogavel/j01-preflight.json"
ALLOWED = {
    "ABSENT_GAME_DATA", "MISSING_GAME_FILES", "REAL_GAME_BASELINE_READ",
    "SOURCE_NOT_PROVIDED", "REAL_SOURCE_METADATA_READ", "SOURCE_ONLY_TEMPLATE",
    "SYMBOL_BINDINGS_PENDING", "REAL_MAPS_PENDING", "NATIVE_QA_PENDING",
    "R07_RESERVATIONS_PENDING", "R08_RIGHTS_PENDING",
}

def refuse(reason):
    raise ValueError("SINNOH_J01_BLOCKED:" + reason)

def read_json(file: Path) -> dict:
    if file.is_symlink() or not file.is_file() or file.stat().st_size > 400000:
        refuse("CONTRACT_UNAVAILABLE")
    data = json.loads(file.read_text("utf-8"))
    if type(data) is not dict:
        refuse("CONTRACT_INVALID")
    return data

def sha256_file(file: Path) -> str:
    if file.is_symlink() or not file.is_file() or file.stat().st_size > 32000000:
        refuse("GAME_MAPINFOS_INVALID")
    sha = hashlib.sha256()
    with file.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1048576), b""):
            sha.update(chunk)
    return sha.hexdigest()

def contracts(project: Path = ROOT) -> dict:
    spec = read_json(project / "data/regions/sinnoh-twinleaf-events.json")
    schema = read_json(project / "data/regions/sinnoh-twinleaf-events.schema.json")
    # Reuse the existing full topology and JSON-schema auditor.
    topology = twinleaf.audit(spec, schema)
    rows = spec["maps"]
    if (len(rows) != 9 or set(m["symbol"] for m in rows) != set(twinleaf.MAPS)
            or spec["start"]["map_id"] is not None
            or any(m["map_id"] is not None or m["map_sha256"] is not None
                   for m in rows)):
        refuse("UNVERIFIED_MAP_BINDINGS")
    counts = {kind: sum(e["kind"] == kind for m in rows for e in m["events"])
              for kind in ("warp", "handler", "starter_ball")}
    if counts != {"warp": 16, "handler": 5, "starter_ball": 3}:
        refuse("TOPOLOGY_COUNTS_CHANGED")
    return {"symbols": [m["symbol"] for m in rows],
            "event_counts": counts, "symbols_bound": 0,
            "contracts_audited": True}

def game_inventory(game_data: Path | None) -> tuple[dict, set[int]]:
    empty = {"status": "NOT_PROVIDED", "occupied_count": None,
             "mapinfos_sha256": None, "required_files_present": False}
    if game_data is None:
        return empty, set()
    game_data = Path(game_data)
    if not game_data.exists():
        return {**empty, "status": "ABSENT"}, set()
    if game_data.is_symlink() or not game_data.is_dir():
        refuse("GAME_DATA_LINK_OR_INVALID")
    required = ("MapInfos.rxdata", "Tilesets.rxdata", "Scripts.rxdata",
                "System.rxdata")
    for name in required:
        file = game_data / name
        if file.is_symlink():
            refuse("GAME_FILE_SYMLINK")
    if any(not (game_data / name).is_file() for name in required):
        return {**empty, "status": "INCOMPLETE"}, set()
    ids = source_audit.inspect_native(game_data)
    if ids["status"] != "LOCAL_READ_ONLY" or not ids["occupied_ids"]:
        refuse("GAME_BASELINE_INVALID")
    return {
        "status": "READ_ONLY_OBSERVED",
        "occupied_count": ids["occupied_count"],
        "mapinfos_sha256": sha256_file(game_data / "MapInfos.rxdata"),
        "required_files_present": True,
    }, set(ids["occupied_ids"])

def source_inventory(source: Path | None) -> tuple[dict, set[int]]:
    if source is None:
        return {"status": "NOT_PROVIDED", "map_count": None,
                "archive_sha256": None, "rights_verified": False}, set()
    file = Path(source)
    if file.is_symlink() or not file.exists():
        refuse("SOURCE_UNAVAILABLE")
    if file.is_file() and file.suffix.lower() == ".zip":
        result = source_audit.inspect_zip(file)
    elif file.is_dir():
        result = source_audit.inspect_directory(file)
    else:
        refuse("SOURCE_FORMAT_UNSUPPORTED")
    if result["map_count"] < 1:
        refuse("SOURCE_EMPTY")
    return {
        "status": "TEMPLATE_ONLY" if result["empty_or_template_source"]
                  else "METADATA_OBSERVED",
        "map_count": result["map_count"],
        "archive_sha256": result["sha256_zip"],
        "rights_verified": False,
    }, set(result["source_map_ids"])

def inspect(project: Path = ROOT, *, game_data: Path | None = None,
            source: Path | None = None) -> dict:
    project = Path(project)
    links = contracts(project)
    native, occupied = game_inventory(game_data)
    donor, donor_ids = source_inventory(source)
    problems = []
    if native["status"] == "NOT_PROVIDED":
        problems.append("ABSENT_GAME_DATA")
    elif native["status"] != "READ_ONLY_OBSERVED":
        problems.append("MISSING_GAME_FILES")
    if donor["status"] == "NOT_PROVIDED":
        problems.append("SOURCE_NOT_PROVIDED")
    elif donor["status"] == "TEMPLATE_ONLY":
        problems.append("SOURCE_ONLY_TEMPLATE")
    problems.extend(("SYMBOL_BINDINGS_PENDING", "R07_RESERVATIONS_PENDING",
                     "R08_RIGHTS_PENDING", "NATIVE_QA_PENDING"))
    if not set(problems).issubset(ALLOWED):
        refuse("UNEXPECTED_STATUS")
    return {
        "schema": 1, "region": "SINNOH", "stage": "J01",
        "mode": "READ_ONLY_REAL_INSTALL_SOURCE_PREFLIGHT",
        "status": ("BASELINES_OBSERVED_UNVERIFIED" if native["status"] == "READ_ONLY_OBSERVED"
                   and donor["status"] == "METADATA_OBSERVED"
                   else "MISSING_INPUTS_OR_NATIVE_EVIDENCE"),
        "game": native, "source": donor,
        "pilot": {**links, "actual_game_maps_linked": 0,
                  "warps_compiled": 0, "handlers_compiled": 0,
                  "balls_compiled": 0, "start_position_verified": False},
        # Donor MapIDs are NOT a destination plan; overlap is for diagnostics only.
        "unremapped_source_ids_already_occupied_count":
            len(occupied & donor_ids) if occupied and donor_ids else None,
        "blockers": problems,
        "rights_verified": False, "mapids_reserved": False,
        "source_license_accepted": False, "game_modified": False,
        "saves_read_or_modified": False, "runtime_executed": False,
        "can_install": False, "native_playable": False,
        "next_stage": "J02",
    }

def write_local_report(project: Path, report: dict) -> None:
    project = Path(project)
    if not project.is_dir() or project.is_symlink():
        refuse("PROJECT_INVALID")
    work = project / ".blue-work"
    folder = work / "sinnoh-jogavel"
    file = folder / "j01-preflight.json"
    if work.is_symlink() or folder.is_symlink() or file.is_symlink():
        refuse("OUTPUT_LINK")
    folder.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2)+"\n"
    # No overwrite: preserve independent observations, never touch game/ or saves.
    with file.open("x", encoding="utf-8") as handle:
        handle.write(payload)

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT,
                        help="Raiz do checkout Pokémon Blue (somente leitura)")
    parser.add_argument("--game-data", type=Path,
                        help="Data/ do jogo instalado, somente leitura")
    parser.add_argument("--source", type=Path,
                        help="Pasta RMXP ou ZIP de fonte autorizado; não é extraído")
    parser.add_argument("--write-local-report", action="store_true",
                        help="Gravar uma única vez em .blue-work/sinnoh-jogavel")
    args = parser.parse_args(argv)
    try:
        report = inspect(args.project, game_data=args.game_data, source=args.source)
        if args.write_local_report:
            write_local_report(args.project, report)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError,
            ImportError) as err:
        # Error details could include private path: emit stable code only.
        print("SINNOH_J01_BLOCKED:INVALID_OR_UNVERIFIED_LOCAL_INPUT", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "BASELINES_OBSERVED_UNVERIFIED" else 2

if __name__ == "__main__":
    raise SystemExit(main())
