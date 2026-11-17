#!/usr/bin/env python3
"""E05: read real RMXP MapInfos without executing donor Ruby or opening maps.

Always independent from MapNNN parse failures in older RMXP sources.
Names, parents and file existence are only CANDIDATES, not rights, events,
source-region signoff, usable map IDs or tested content.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from server.ruby_marshal import RubyObject, loads, text
from audit_unova_u02 import audit_zip, is_within_source
from audit_unova_source_detail import normalized

MAX_INFOS = 24 * 1024 * 1024
MAX_DEPTH = 32
MAX_NAME = 200


def fail(message):
    raise ValueError("UNOVA_MAPINFOS_BLOQUEADO: " + message)


def ancestor_names(mid, maps):
    names, visited = [], set()
    current = mid
    for _ in range(MAX_DEPTH):
        if current not in maps:
            break
        if current in visited:
            fail("ciclo de pais encontrado em MapInfos")
        visited.add(current)
        meta = maps[current]
        names.append(meta["name"])
        current = meta["parent_id"]
        if not current:
            break
    else:
        fail("arvore MapInfos profunda demais")
    return names


def inspect(source: Path, catalog: dict) -> dict:
    if (not isinstance(catalog, dict) or
            catalog.get("state") != "PLANNED_REFERENCE_ONLY" or
            catalog.get("may_install") is not False or
            catalog.get("reference_version") != "WHITE_BW"):
        fail("catalogo nao esta em estado planned")
    areas = catalog.get("areas")
    if not isinstance(areas, list) or len(areas) != 74:
        fail("74 areas simbolicas exigidas")

    meta = audit_zip(source)
    wrapper = meta["project_wrapper"]
    prefix = (wrapper + "/" if wrapper else "") + "Data/"
    with zipfile.ZipFile(source) as archive:
        names = {name.casefold(): name for name in archive.namelist()}
        infos_path = names.get((prefix + "MapInfos.rxdata").casefold())
        if not infos_path:
            fail("MapInfos.rxdata indisponivel")
        info = archive.getinfo(infos_path)
        if not 0 < info.file_size <= MAX_INFOS:
            fail("MapInfos possui tamanho inseguro")
        with archive.open(info) as fh:
            raw = fh.read(MAX_INFOS + 1)
        if len(raw) != info.file_size:
            fail("MapInfos tamanho truncado ou divergente")
    try:
        parsed = loads(raw)
    except (ValueError, TypeError, KeyError, IndexError, RecursionError, OverflowError) as exc:
        fail("MapInfos Ruby Marshal incompativel: " + exc.__class__.__name__)
    if not isinstance(parsed, dict) or not 1 <= len(parsed) <= 7500:
        fail("MapInfos invalido")

    real_map_files = set(meta["all_regions_source_map_ids"])
    maps = {}
    for mid, obj in parsed.items():
        if (type(mid) is not int or not 1 <= mid <= 99999 or
                not isinstance(obj, RubyObject) or obj.name != "RPG::MapInfo"):
            fail("MapInfo ausente ou com tipo inesperado")
        name = text(obj.attrs.get("@name", b"")).strip()
        if not name or len(name) > MAX_NAME:
            fail("nome MapInfo vazio ou longo")
        parent = obj.attrs.get("@parent_id", 0)
        if type(parent) is not int or not 0 <= parent <= 99999:
            fail("parent_id invalido")
        maps[mid] = {
            "source_map_id": mid, "name": name, "parent_id": parent,
            "source_map_file_in_zip": mid in real_map_files,
        }

    all_areas = []
    counters = {"anchored_by_unova_parent_name": 0, "direct_name_candidates": 0}
    for mid, row in sorted(maps.items()):
        ancestors = ancestor_names(mid, maps)
        ancestry_norm = [normalized(x) for x in ancestors]
        anchored = any("unova" in x.split() or "isshu" in x.split() for x in ancestry_norm)
        if anchored and row["source_map_file_in_zip"]:
            counters["anchored_by_unova_parent_name"] += 1
        direct_matches = []
        for area in areas:
            canonical = normalized(area["name"])
            current = normalized(row["name"])
            eq = current == canonical
            qualified = (current.endswith(" " + canonical) and
                         any(current.startswith(prefix) for prefix in
                             ("unova ", "isshu ")))
            if eq or qualified:
                direct_matches.append(area["key"])
        if direct_matches:
            counters["direct_name_candidates"] += 1
        all_areas.append({
            **row,
            "ancestor_names": ancestors,
            "ancestor_unova_or_isshu_keyword": anchored,
            "matched_symbolic_area_keys": direct_matches,
            "identity_confirmed": False,
            "event_pages_checked": False,
            "rights_verified": False,
            "destination_map_id": None,
            "game_exe_tested": False,
        })
    matches_by_area = []
    for area in areas:
        candidates = [
            m for m in all_areas if area["key"] in m["matched_symbolic_area_keys"]
        ]
        generic = area.get("kind") == "route" or area["key"] in {
            "UNOVA_VICTORY_ROAD", "UNOVA_ELITE_FOUR", "UNOVA_POKEMON_LEAGUE"
        }
        matches_by_area.append({
            "area_key": area["key"],
            "candidate_source_map_ids": [m["source_map_id"] for m in candidates],
            "candidate_names": [m["name"] for m in candidates],
            "generic_name_unresolved": generic and bool(candidates),
            "candidates_are_not_verification": True,
            "map_not_found_is_not_proof_of_absence": len(candidates) == 0,
            "manually_verified": False,
        })

    return {
        "schema": 1, "region": "UNOVA", "phase": "E05_MAPINFOS_ONLY",
        "mode": "INERT_MAPINFOS_NAMES_AND_PARENTS_NO_MAP_PARSE",
        "status": "SOURCE_MAPINFOS_INDEXED_NOT_UNOVA_APPROVED",
        "source_zip_sha256": meta["archive_sha256"],
        "mapinfos_sha256": hashlib.sha256(raw).hexdigest(),
        "whole_donor_project_map_count": len(real_map_files),
        "mapinfos_entry_count": len(maps),
        "symbolic_areas": len(matches_by_area),
        "clues": counters,
        "maps": all_areas, "areas": matches_by_area,
        "events_inspected": False, "rights_verified": False,
        "native_mapids_checked": False, "can_install": False,
        "game_or_saves_modified": False, "game_exe_tested": False,
        "android_tested": False,
        "blockers": [
            "Nomes/parentes e matches NAO atestam regiao nem licenca",
            "Eventos doador precisam ser verificados separadamente (Map008 pode ser incompativel)",
            "MapIDs do destino e reservas Kanto/Johto/Hoenn/Sinnoh nao auditados",
        ],
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--catalog", type=Path, default=ROOT/"data/regions/unova-u03-areas.json")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    root = args.project.absolute()
    source = args.source or root/".blue-work/unova/sources/Pokemon_World_V18.zip"
    try:
        if not is_within_source(root, source):
            fail("ZIP fora da pasta privada")
        if args.catalog.is_symlink() or not args.catalog.is_file():
            fail("catalogo simbolico ausente ou inseguro")
        data = json.loads(args.catalog.read_text("utf-8"))
        report = inspect(source, data)
        if args.write:
            folder = root/".blue-work/unova/audit"
            for directory in (root/".blue-work", root/".blue-work/unova", folder):
                if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
                    fail("pasta de auditoria insegura")
            folder.mkdir(parents=True, exist_ok=True)
            output = folder/"e05-mapinfos-only.json"
            if output.is_symlink():
                fail("relatorio symlink")
            payload = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
            if output.exists():
                if output.read_text("utf-8") != payload:
                    fail("relatorio anterior divergente; preservar evidencias")
            else:
                with output.open("x", encoding="utf-8") as out:
                    out.write(payload)
        summary = {k:v for k,v in report.items() if k not in ("maps", "areas")}
        summary["unova_keyword_parent_examples"] = [
            (x["source_map_id"], x["name"])
            for x in report["maps"] if x["ancestor_unova_or_isshu_keyword"]
        ][:40]
        summary["matched_area_examples"] = [
            (x["area_key"],x["candidate_source_map_ids"])
            for x in report["areas"] if x["candidate_source_map_ids"]
        ][:40]
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    except (ValueError, OSError, TypeError, KeyError, zipfile.BadZipFile) as exc:
        print("UNOVA_MAPINFOS_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
