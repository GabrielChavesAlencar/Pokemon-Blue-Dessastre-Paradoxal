#!/usr/bin/env python3
"""E05: audit events of maps under the donor's *named* Unova Region branch.

Inert Ruby Marshal reading only. Does not run map events, scripts, Ruby or RPG
Maker; does not import or allocate destination IDs. Some older RXDATA maps may
fail parsing; record each failure rather than losing the whole audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from server.ruby_marshal import RubyObject, loads, text
from audit_unova_u02 import audit_zip, is_within_source
from audit_unova_e05_mapinfos_only import inspect as mapinfos_inspect

MAX_ONE_MAP = 24 * 1024 * 1024
MAX_SELECTED_TOTAL = 300 * 1024 * 1024
MAX_EVENT_NAMES = 30
MAP_PATTERN = re.compile(r"map0*([1-9]\d*)\.rxdata\Z", re.I)
INTERESTING = {101:"message_header", 401:"message_line",
               201:"transfer", 301:"battle_command",
               355:"ruby_script", 655:"ruby_script_continuation",
               111:"branch_condition", 121:"switches",
               122:"variables", 123:"self_switch",
               108:"comment", 408:"comment_continuation"}


def fail(message: str):
    raise ValueError("UNOVA_EVENT_AUDIT_BLOQUEADO: " + message)


def get_attrs(o, kind):
    if not isinstance(o, RubyObject) or o.name != kind:
        fail("objeto RMXP incompatível: " + kind)
    return o.attrs


def inspect_one_map(raw: bytes, mid: int, name: str, ancestor: list[str]) -> dict:
    if len(raw) > MAX_ONE_MAP:
        fail("mapa excede limite de leitura")
    obj = get_attrs(loads(raw), "RPG::Map")
    width, height = obj.get("@width"), obj.get("@height")
    if any(type(n) is not int or not 1 <= n <= 1500 for n in (width, height)):
        fail("dimensoes invalidas")
    ev = obj.get("@events", {})
    if not isinstance(ev, dict) or len(ev) > 5000:
        fail("eventos fora de limite")
    counts = Counter()
    transfer_targets = set()
    event_names = []
    pages_total = 0
    for event in ev.values():
        e = get_attrs(event, "RPG::Event")
        label = text(e.get("@name", b"")).strip()
        if label and len(event_names) < MAX_EVENT_NAMES:
            event_names.append(label[:90])
        pages = e.get("@pages", [])
        if not isinstance(pages, list) or len(pages) > 100:
            fail("paginas de evento fora de limite")
        pages_total += len(pages)
        for page in pages:
            p = get_attrs(page, "RPG::Event::Page")
            commands = p.get("@list", [])
            if not isinstance(commands, list) or len(commands) > 30000:
                fail("comandos de evento fora de limite")
            for c in commands:
                cmd = get_attrs(c, "RPG::EventCommand")
                code = cmd.get("@code")
                if type(code) is not int:
                    fail("codigo de comando invalido")
                if code in INTERESTING:
                    counts[INTERESTING[code]] += 1
                if code == 201:
                    parms = cmd.get("@parameters", [])
                    if isinstance(parms, list) and len(parms) >= 2 and parms[0] == 0 and type(parms[1]) is int and parms[1] > 0:
                        transfer_targets.add(parms[1])

    return {
        "source_map_id": mid, "name": name, "parent_chain": ancestor,
        "parse_status": "MAP_BYTES_PARSED_EVENT_STRUCTURE_ONLY",
        "width": width, "height": height,
        "event_containers": len(ev),
        "event_pages": pages_total,
        "command_counts": dict(sorted(counts.items())),
        "event_names_first_30": event_names,
        "static_transfer_target_source_ids": sorted(transfer_targets),
        "source_map_sha256": hashlib.sha256(raw).hexdigest(),
        "all_script_lines_inert": True, "events_gameplay_verified": False,
        "trainer_battles_verified": False, "source_rights_verified": False,
        "destination_map_id": None, "installed": False, "game_exe_tested": False,
    }


def inspect(source: Path, catalog: dict) -> dict:
    if not isinstance(catalog, dict) or catalog.get("state") != "PLANNED_REFERENCE_ONLY":
        fail("catalogo de Unova nao esta em planned")
    header = audit_zip(source)
    infos = mapinfos_inspect(source, catalog)
    if infos["source_zip_sha256"] != header["archive_sha256"]:
        fail("fonte divergiu da auditoria MapInfos")
    selected = sorted(
        (m for m in infos["maps"]
         if m["ancestor_unova_or_isshu_keyword"] and m["source_map_file_in_zip"]),
        key=lambda m:m["source_map_id"],
    )
    prefix = (header["project_wrapper"] + "/" if header["project_wrapper"] else "") + "Data/"
    rows = []
    total_read = 0
    with zipfile.ZipFile(source) as z:
        entries = {v.filename.casefold(): v for v in z.infolist() if not v.is_dir()}
        by_id = {}
        for file in z.infolist():
            if not file.filename.casefold().startswith(prefix.casefold()):
                continue
            match = MAP_PATTERN.fullmatch(file.filename.split("/")[-1])
            if match:
                mid = int(match.group(1))
                if mid in by_id:
                    fail("MapID fonte ambiguo")
                by_id[mid] = file
        for row in selected:
            mid = row["source_map_id"]
            inf = by_id.get(mid)
            if inf is None or inf.file_size > MAX_ONE_MAP or total_read + inf.file_size > MAX_SELECTED_TOTAL:
                rows.append({
                    "source_map_id": mid, "name": row["name"],
                    "parse_status": "BLOCKED_MISSING_OR_OVERSIZE",
                    "error_kind": "FILE_OR_SIZE",
                    "event_containers": None,
                    "events_gameplay_verified": False, "source_rights_verified": False,
                    "installed": False, "destination_map_id": None,
                })
                continue
            with z.open(inf) as file:
                raw = file.read(MAX_ONE_MAP+1)
            total_read += len(raw)
            try:
                if len(raw) != inf.file_size:
                    fail("arquivo truncado")
                result = inspect_one_map(raw,mid,row["name"],row["ancestor_names"])
                rows.append(result)
            except (ValueError, TypeError, KeyError, IndexError, RecursionError, OverflowError) as exc:
                rows.append({
                    "source_map_id":mid, "name":row["name"],
                    "parse_status":"BLOCKED_MAP_PARSER_INCOMPATIBLE",
                    "error_kind":type(exc).__name__,
                    "source_map_sha256":hashlib.sha256(raw).hexdigest(),
                    "event_containers":None,
                    "events_gameplay_verified":False, "source_rights_verified":False,
                    "installed":False, "destination_map_id":None,
                })
    count = Counter(x["parse_status"] for x in rows)
    commands = Counter()
    for x in rows:
        if x["parse_status"]=="MAP_BYTES_PARSED_EVENT_STRUCTURE_ONLY":
            commands.update(x["command_counts"])
    return {
        "schema":1,"region":"UNOVA","phase":"E05_ANCHORED_EVENTS",
        "mode":"INERT_RMXP_EVENT_STRUCTURE_WITH_PER_MAP_ERRORS",
        "status":"SOURCE_REGION_CANDIDATES_INSPECTED_NOT_PLAYABLE",
        "source_zip_sha256":header["archive_sha256"],
        "source_mapinfos_sha256":infos["mapinfos_sha256"],
        "source_mapinfos_count":infos["mapinfos_entry_count"],
        "whole_donor_project_map_count":header["all_regions_source_map_count"],
        "unova_parent_context_map_files":len(selected),
        "region_context_assumed_from_parent_name_only":True,
        "parsed_map_count":count["MAP_BYTES_PARSED_EVENT_STRUCTURE_ONLY"],
        "unparsed_map_count":len(selected)-count["MAP_BYTES_PARSED_EVENT_STRUCTURE_ONLY"],
        "total_event_containers_parsed":sum(x["event_containers"] or 0 for x in rows),
        "command_totals_parsed":dict(sorted(commands.items())),
        "maps":rows,
        "gameplay_approved":False,"copyright_rights_verified":False,
        "can_install":False,"native_mapids_audited":False,
        "game_or_saves_modified":False,"game_exe_tested":False,"android_tested":False,
        "blockers":[
            "As hierarquias Unova misturam roteiro BW, BW2 e anime: verificar historia e gaps",
            "Mapas apenas interpretados como dados; eventos/NPCs nao testados no Game.exe",
            "Mapas nao interpretados exigem tratamento individual sem contornar limites",
            "Licencas de tilesets, NPCs, musica e scripts ainda pendentes",
        ],
    }


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project",type=Path,default=ROOT)
    p.add_argument("--source",type=Path)
    p.add_argument("--catalog",type=Path,default=ROOT/"data/regions/unova-u03-areas.json")
    p.add_argument("--write",action="store_true")
    args=p.parse_args(argv)
    project=args.project.absolute()
    source=args.source or project/".blue-work/unova/sources/Pokemon_World_V18.zip"
    try:
        if not is_within_source(project,source):
            fail("ZIP fora da area de trabalho privada")
        if args.catalog.is_symlink() or not args.catalog.is_file():
            fail("catalogo de Unova ausente")
        catalog=json.loads(args.catalog.read_text("utf-8"))
        report=inspect(source,catalog)
        if args.write:
            work=project/".blue-work"; local=work/"unova"; folder=local/"audit"
            for part in (work,local,folder):
                if part.is_symlink() or (part.exists() and not part.is_dir()):
                    fail("pasta de relatorio insegura")
            folder.mkdir(parents=True,exist_ok=True)
            target=folder/"e05-anchored-events.json"
            if target.is_symlink():
                fail("relatorio symlink")
            payload=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
            if target.exists():
                if target.read_text("utf-8")!=payload:
                    fail("relatorio divergente anterior: nao sobrescrever")
            else:
                with target.open("x",encoding="utf-8") as f:f.write(payload)
        summary={k:v for k,v in report.items() if k!="maps"}
        summary["map_examples"]=[{
            "source_map_id":m["source_map_id"],"name":m["name"],
            "status":m["parse_status"],"events":m.get("event_containers")}
            for m in report["maps"][:50]]
        print(json.dumps(summary,indent=2,ensure_ascii=False))
        return 0
    except (ValueError,OSError,TypeError,KeyError,zipfile.BadZipFile) as exc:
        print("UNOVA_EVENT_AUDIT_BLOQUEADO: "+str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
