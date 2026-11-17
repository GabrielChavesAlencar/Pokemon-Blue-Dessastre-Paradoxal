#!/usr/bin/env python3
"""Unova A06: inert static RPG Maker XP transfer-reference audit of native maps.

Reads only existing MapNNN.rxdata files included in an A04 snapshot. Verifies
their hashes and extracts event command 201 static transfer destinations.
Never loads executable Ruby, changes files, assigns MapIDs or certifies reserves.

LIMITATION: dynamic transfers, scripts, CommonEvents and installer manifests
remain unaudited. Even a zero-conflict report cannot approve native MapIDs.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import audit_unova_a04_mapids as a04
from server.ruby_marshal import RubyObject, loads

MAX_FINDINGS=1500
MAX_MAP_FAILURES=1500
OUT=Path(".blue-work/unova/audit")


def fields(obj):
    return obj.attrs if isinstance(obj,RubyObject) else {}


def reject(message):
    raise ValueError("UNOVA_A06_BLOQUEADO: "+message)


def parse_map(raw: bytes, map_id: int) -> dict:
    """Read only event lists from Marshal data, without executing anything."""
    root=loads(raw)
    if not isinstance(root,RubyObject) or root.name!="RPG::Map":
        reject("Map%03d nao contem RPG::Map"%map_id)
    events=fields(root).get("@events",{})
    if not isinstance(events,dict) or len(events)>12000:
        reject("eventos invalidos no mapa "+str(map_id))
    destinations=[]
    dynamic=0
    script_commands=0
    commands=0
    for eid,event in events.items():
        if type(eid) is not int or not isinstance(event,RubyObject):
            reject("evento invalido no mapa "+str(map_id))
        pages=fields(event).get("@pages",[])
        if not isinstance(pages,list) or len(pages)>250:
            reject("paginas invalidas no mapa "+str(map_id))
        for page in pages:
            if not isinstance(page,RubyObject):
                reject("pagina invalida no mapa "+str(map_id))
            cmdlist=fields(page).get("@list",[])
            if not isinstance(cmdlist,list) or len(cmdlist)>50000:
                reject("lista de comandos invalida no mapa "+str(map_id))
            for command in cmdlist:
                args=fields(command)
                code=args.get("@code")
                parameters=args.get("@parameters",[])
                if type(code) is not int:
                    reject("codigo do evento invalido no mapa "+str(map_id))
                commands+=1
                if code in (355,655):
                    script_commands+=1
                if code!=201:
                    continue
                if (isinstance(parameters,list) and len(parameters)>1
                    and type(parameters[0]) is int
                    and parameters[0]==0
                    and type(parameters[1]) is int
                    and 0<parameters[1]<=99999):
                    destinations.append(parameters[1])
                else:
                    dynamic+=1
    return {
        "static_destinations":destinations,
        "dynamic_transfer_commands":dynamic,
        "script_commands_not_executed":script_commands,
        "command_count":commands,
        "event_count":len(events),
    }


def audit(game_dir: Path, a04_report: dict) -> dict:
    game_dir=a04.safe_path(game_dir)
    data=a04.directory_root(game_dir)
    base=a04_report.get("sources",{}).get("DECADES")
    if (a04_report.get("phase")!="A04" or
        a04_report.get("base_decades_scanned") is not True or
        not isinstance(base,dict) or base.get("mapinfos_present") is not True or
        not isinstance(base.get("maps"),list) or not base["maps"]):
        reject("A04 real e obrigatorio para analise de referencias")
    occupied=set(a04_report.get("observed_or_declared_occupied_map_ids",[]))
    if not occupied or any(type(i) is not int for i in occupied):
        reject("A04 com IDs ocupados invalidos")
    refs=Counter()
    dynamic=0
    scripts=0
    fail=[]
    total_commands=0
    parsed=0
    for row in base["maps"]:
        mid=row["id"]
        filename=row["source_filename"]
        if (type(mid) is not int or
            not isinstance(filename,str) or "/" in filename or "\\" in filename or
            a04._map_id(filename)!=mid):
            reject("MapNNN listado por A04 tem caminho inseguro")
        path=data/filename
        try:
            if path.is_symlink() or not path.is_file():
                reject("MapNNN ausente/symlink durante leitura")
            raw=a04._bounded_file(path)
            if hashlib.sha256(raw).hexdigest()!=row["sha256"]:
                reject("MapNNN foi alterado desde A04")
            parsed_map=parse_map(raw,mid)
            parsed+=1
            refs.update(parsed_map["static_destinations"])
            dynamic+=parsed_map["dynamic_transfer_commands"]
            scripts+=parsed_map["script_commands_not_executed"]
            total_commands+=parsed_map["command_count"]
        except (ValueError,KeyError,TypeError,IndexError,OverflowError,RecursionError,OSError) as exc:
            if len(fail)>=MAX_MAP_FAILURES:
                reject("limite de falhas ao ler mapas")
            fail.append({"source_map_id":mid,"reason":str(exc)[:160]})
    dests=set(refs)
    unova_candidate={i for i in dests if 518<=i<=599}
    sinnoh_hold={i for i in dests if 442<=i<=517}
    unresolved=dests-occupied
    result={
        "schema":1,"region":"UNOVA","phase":"A06",
        "mode":"READ_ONLY_INERT_STATIC_EVENT_TRANSFER_AUDIT",
        "status":"PARTIAL_MAP_PARSE_REVIEW_REQUIRED" if fail else
                 "STATIC_TRANSFERS_REVIEW_REQUIRED_NOT_CERTIFIED",
        "mapinfos_sha256":base["mapinfos_sha256"],
        "map_files_expected":len(base["maps"]),
        "map_files_parsed":parsed,
        "map_read_failures":fail,
        "static_transfer_command_count":sum(refs.values()),
        "static_destination_mapids":sorted(dests),
        "static_unresolved_destination_ids":sorted(unresolved),
        "candidate_unova_518_599_referenced":sorted(unova_candidate),
        "sinnoh_442_517_referenced":sorted(sinnoh_hold),
        "dynamic_transfer_commands":dynamic,
        "event_script_commands_not_executed":scripts,
        "event_command_count":total_commands,
        "script_assets_examined":False,
        "common_events_examined":False,
        "installer_manifests_examined":False,
        "all_mapid_references_certified":False,
        "mapids_allocated":False,"can_reserve_mapids":False,
        "can_install":False,"game_exe_tested":False,
        "android_tested":False,"game_or_saves_modified":False,
        "bar_a_completed":0,"bar_a_total":8,
        "limitations":[
            "201/transferencias estaticas nos mapas sao apenas uma parte dos destinos",
            "Variaveis, scripts, eventos comuns, conexoes, plugins e instalador nao foram auditados",
            "Falhas de parsing nao sao interpretadas como ausencia de referencias",
            "Nenhum MapID pode ser reservado ou instalado por este diagnostico",
        ]
    }
    return result


def save(project: Path, report: dict) -> Path:
    project=a04.safe_path(project)
    for folder in (project/".blue-work",project/".blue-work/unova",project/OUT):
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            reject("caminho privado de QA inseguro")
        folder.mkdir(exist_ok=True)
    payload=(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode("utf-8")
    out=project/OUT/("a06-references-"+hashlib.sha256(payload).hexdigest()[:16]+".json")
    if out.is_symlink():
        reject("relatorio protegido contra symlink")
    if out.exists():
        if out.read_bytes()!=payload:
            reject("nao sobrescrever relatorio divergente")
    else:
        out.write_bytes(payload)
    return out
