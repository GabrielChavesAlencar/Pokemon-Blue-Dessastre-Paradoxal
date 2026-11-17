#!/usr/bin/env python3
"""A07 read-only provenance of static transfers and literal script MapID hints.

Focus: missing MapID 3 and candidate region 518..599; not a free-ID proof.
No Ruby code is executed. Scripts.rxdata code is only zlib-decompressed with
bounds and inspected for selected textual API patterns. Dynamic references
and installer manifests remain unknown and block approval.
"""
from __future__ import annotations
import hashlib
import json
import re
import zlib
from pathlib import Path
import audit_unova_a04_mapids as a04
from server.ruby_marshal import loads, RubyObject, text

OUT=Path(".blue-work/unova/audit")
INTEREST=set(range(518,600))|{3}
STATIC_LIMIT=2500
SCRIPT_LIMIT=1500
SCRIPT_ENTRY_LIMIT=400_000
SCRIPT_TOTAL_LIMIT=32*1024*1024
MAP_LIMIT=a04.MAX_FILE_BYTES
API_RE=re.compile(
    r"(?:\b(?:reserve_transfer|pbWarp|pbTeleport|pbTransferPlayer|pbTransfer)"
    r"\s*\(\s*|\bplayer_new_map_id\s*=\s*)(\d{1,5})\b",re.I)
MAX_EVENTS=12000
MAX_PAGES=250
MAX_COMMANDS=50000

def refuse(msg):
    raise ValueError("UNOVA_A07_BLOQUEADO: "+msg)

def props(obj):
    return obj.attrs if isinstance(obj,RubyObject) else {}

def limited_read(path:Path,limit:int)->bytes:
    if path.is_symlink() or not path.is_file():
        refuse("arquivo ausente ou symlink: "+path.name)
    size=path.stat().st_size
    if not 0<size<=limit:
        refuse("arquivo excede limite: "+path.name)
    return path.read_bytes()

def walk_commands(commands,location,found,errors):
    if not isinstance(commands,list) or len(commands)>MAX_COMMANDS:
        refuse("lista de comandos de evento invalida")
    for i,entry in enumerate(commands):
        d=props(entry)
        code=d.get("@code")
        params=d.get("@parameters",[])
        if type(code) is not int:
            refuse("codigo invalido em evento")
        if code==201:
            if (isinstance(params,list) and len(params)>1 and
                type(params[0]) is int and params[0]==0 and
                type(params[1]) is int and 0<params[1]<=99999):
                mid=params[1]
                if mid in INTEREST:
                    if len(found["static"])>=STATIC_LIMIT: refuse("limite de findings estaticos")
                    found["static"].append({**location,"command_index":i,"destination_map_id":mid})
            else:
                found["dynamic"]+=1
        if code not in (355,655):
            continue
        found["scripts_seen"]+=1
        if not isinstance(params,list) or not params:
            errors.append({**location,"reason":"script event command without params"})
            continue
        script=params[0]
        if not isinstance(script,(bytes,str)):
            errors.append({**location,"reason":"script event command not text"})
            continue
        if isinstance(script,bytes): script=script.decode("utf-8","replace")
        if len(script)>SCRIPT_ENTRY_LIMIT:
            errors.append({**location,"reason":"script event text exceeds safety limit"})
            continue
        inspect_literal(script,{**location,"command_index":i},found)

def inspect_literal(script,location,found):
    """Heuristic literal matches only. Never imply complete script coverage."""
    for match in API_RE.finditer(script):
        target=int(match.group(1))
        if target not in INTEREST: continue
        if len(found["script_hints"])>=SCRIPT_LIMIT:
            refuse("muitos indícios em scripts; relatório bloqueado")
        found["script_hints"].append({**location,"target_literal":target,
                                      "pattern":"NAMED_MAP_TRANSFER_API_LITERAL"})

def event_pages(items,origin,found,errors):
    if not isinstance(items,dict) or len(items)>MAX_EVENTS:
        refuse("lista de eventos invalida")
    for eid,event in items.items():
        if type(eid) is not int or not isinstance(event,RubyObject):
            refuse("objeto de evento invalido")
        pages=props(event).get("@pages",[])
        if not isinstance(pages,list) or len(pages)>MAX_PAGES:
            refuse("paginas invalidas")
        for page_index,page in enumerate(pages):
            if not isinstance(page,RubyObject):
                refuse("pagina nao RubyObject")
            walk_commands(props(page).get("@list",[]),
                          {**origin,"event_id":eid,"page_index":page_index+1},found,errors)

def map_audit(game_data:Path,base:dict,found:dict,errors:list)->int:
    parsed=0
    for row in base.get("maps",[]):
        mid=row["id"];name=row["source_filename"]
        if (type(mid) is not int or not isinstance(name,str) or
            a04._map_id(name)!=mid or "/" in name or "\\" in name):
            refuse("arquivo MapNNN invalido no manifesto A04")
        try:
            raw=limited_read(game_data/name,MAP_LIMIT)
            if hashlib.sha256(raw).hexdigest()!=row["sha256"]:
                refuse("mapa alterado desde A04")
            m=loads(raw)
            if not isinstance(m,RubyObject) or m.name!="RPG::Map":
                refuse("nao e RPG::Map")
            event_pages(props(m).get("@events",{}),
                        {"source_type":"MAP","source_map_id":mid},found,errors)
            parsed+=1
        except (ValueError,KeyError,TypeError,IndexError,OverflowError,RecursionError,OSError) as exc:
            errors.append({"source_type":"MAP","source_map_id":mid,
                           "reason":str(exc)[:160]})
    return parsed

def scan_common_events(game_data:Path,found:dict,errors:list)->dict:
    path=game_data/"CommonEvents.rxdata"
    if not path.exists():
        return {"present":False,"status":"NOT_FOUND","objects":0}
    try:
        root=loads(limited_read(path,MAP_LIMIT))
        if not isinstance(root,list) or len(root)>30000:
            refuse("CommonEvents não é uma lista válida")
        count=0
        for i,item in enumerate(root):
            if item is None:continue
            if not isinstance(item,RubyObject) or item.name!="RPG::CommonEvent":
                refuse("CommonEvent invalido")
            walk_commands(props(item).get("@list",[]),
                          {"source_type":"COMMON_EVENT","common_event_index":i},found,errors)
            count+=1
        return {"present":True,"status":"READ_ONLY_INSPECTED","objects":count}
    except (ValueError,TypeError,IndexError,KeyError,OverflowError,RecursionError,OSError) as exc:
        errors.append({"source_type":"COMMON_EVENTS","reason":str(exc)[:160]})
        return {"present":True,"status":"PARSE_FAILED","objects":0}

def scan_scripts(game_data:Path,found:dict,errors:list)->dict:
    path=game_data/"Scripts.rxdata"
    if not path.exists():
        return {"present":False,"status":"NOT_FOUND","entries":0,"decompressed_entries":0}
    try:
        root=loads(limited_read(path,MAP_LIMIT))
        if not isinstance(root,list) or len(root)>3000:
            refuse("Scripts.rxdata não é uma lista válida")
    except (ValueError,TypeError,KeyError,OverflowError,RecursionError,OSError) as exc:
        errors.append({"source_type":"SCRIPTS","reason":str(exc)[:160]})
        return {"present":True,"status":"PARSE_FAILED","entries":0,"decompressed_entries":0}
    count=0;decoded=0;total=0
    for i,row in enumerate(root):
        if not isinstance(row,list) or len(row)<3 or not isinstance(row[2],bytes):
            errors.append({"source_type":"SCRIPTS","index":i,"reason":"script entry format unsupported"})
            continue
        count+=1
        try:
            z=zlib.decompressobj()
            payload=z.decompress(row[2],SCRIPT_ENTRY_LIMIT+1)
            if len(payload)>SCRIPT_ENTRY_LIMIT or not z.eof or z.unused_data or z.unconsumed_tail:
                refuse("script comprimido excede limite ou esta incompleto")
            total+=len(payload)
            if total>SCRIPT_TOTAL_LIMIT: refuse("total de scripts acima de limite")
            inspect_literal(payload.decode("utf-8","replace"),
                            {"source_type":"SCRIPTS_RXDATA","script_entry":i},found)
            decoded+=1
        except (zlib.error,ValueError,TypeError) as exc:
            errors.append({"source_type":"SCRIPTS","index":i,"reason":str(exc)[:160]})
    return {"present":True,"status":"PARTIAL_REVIEW" if decoded!=count else "TEXT_SCANNED_INERT",
            "entries":count,"decompressed_entries":decoded}

def audit(game:Path,a04_report:dict,a06_report:dict)->dict:
    game=a04.safe_path(game)
    data=a04.directory_root(game)
    base=a04_report.get("sources",{}).get("DECADES")
    if (a04_report.get("phase")!="A04" or not isinstance(base,dict) or
        not base.get("maps") or a06_report.get("phase")!="A06" or
        a06_report.get("mapinfos_sha256")!=base.get("mapinfos_sha256")):
        refuse("relatorios A04/A06 incoerentes ou ausentes")
    if a06_report.get("map_files_parsed")!=len(base["maps"]) or a06_report.get("map_read_failures"):
        refuse("A06 precisa ter 100 por cento dos mapas parseados")
    found={"static":[],"script_hints":[],"dynamic":0,"scripts_seen":0}
    errors=[]
    parsed=map_audit(data,base,found,errors)
    common=scan_common_events(data,found,errors)
    scripts=scan_scripts(data,found,errors)
    observed={item["destination_map_id"] for item in found["static"]}
    a06_observed=set(a06_report.get("static_unresolved_destination_ids",[])) & INTEREST
    if observed & a06_observed != a06_observed:
        errors.append({"source_type":"COHERENCE",
                       "reason":"A06 informa destino órfão não localizado por A07"})
    if found["dynamic"]!=a06_report.get("dynamic_transfer_commands"):
        errors.append({"source_type":"COHERENCE","reason":"transferencias dinamicas divergem de A06"})
    return {
        "schema":1,"region":"UNOVA","phase":"A07",
        "mode":"INERT_TARGETED_REFERENCE_PROVENANCE",
        "status":"TARGETED_REVIEW_PARTIAL_OR_UNRESOLVED",
        "mapinfos_sha256":base["mapinfos_sha256"],
        "map_files_expected":len(base["maps"]),"map_files_parsed":parsed,
        "static_interest_references":found["static"],
        "mapid_3_static_reference_count":sum(x["destination_map_id"]==3 for x in found["static"]),
        "unova_518_599_static_reference_count":sum(518<=x["destination_map_id"]<=599 for x in found["static"]),
        "script_literal_hints":found["script_hints"],
        "script_event_commands_seen":found["scripts_seen"],
        "dynamic_transfer_commands_seen":found["dynamic"],
        "common_events":common,"scripts_rxdata":scripts,
        "review_errors":errors[:1000],"review_errors_count":len(errors),
        "maps_or_scripts_executed":False,"script_scan_exhaustive":False,
        "all_mapid_references_certified":False,"installer_manifests_examined":False,
        "region_ownership_verified":False,"can_reserve_mapids":False,
        "can_install":False,"game_or_saves_modified":False,
        "bar_a_completed":0,"bar_a_total":8,
        "limitations":[
           "Script search is a narrow textual pattern scan, not Ruby execution or complete parsing",
           "Computed/variable IDs, plugins, generated events, installer code and other API names remain unknown",
           "Scripts and CommonEvents with errors or unsupported encodings remain pending",
           "No native MapIDs allocated, legal rights checked or game runtime QA performed",
        ],
    }

def save(project:Path,report:dict)->Path:
    project=a04.safe_path(project)
    for folder in (project/".blue-work",project/".blue-work/unova",project/OUT):
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            refuse("caminho de relatório inseguro")
        folder.mkdir(exist_ok=True)
    content=(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    out=project/OUT/("a07-provenance-"+hashlib.sha256(content).hexdigest()[:16]+".json")
    if out.is_symlink():refuse("relatório symlink")
    if out.exists():
        if out.read_bytes()!=content:refuse("não sobrescrever evidência divergente")
    else:
        with out.open("xb") as f:f.write(content)
    return out
