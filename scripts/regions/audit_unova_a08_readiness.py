#!/usr/bin/env python3
"""Unova A08: read-only Map001 event context and regional installer evidence.

Does not run Ruby, modify game or claim reservation. A08 is a diagnostic,
not proof that future installs or computed MapIDs cannot collide.
"""
from __future__ import annotations

import hashlib
import json
import re
import zlib
from collections import Counter
from pathlib import Path

import audit_unova_a04_mapids as a04
import audit_unova_a07_reference_provenance as a07
from server.ruby_marshal import RubyObject, loads, text

OUT = Path(".blue-work/unova/audit")
TARGETS = (1, 2)
REGION_PROOFS = (
    "blue-kanto-install.json",
    "blue-johto-main-preview.json",
    "blue-hoenn-install.json",
    "blue-sinnoh-install.json",
    "blue-unova-install.json",
)
PLANNING_FILES = (
    "data/regions/unova-a05-mapid-candidates.json",
    "data/regions/sinnoh-b05-mapid-planning.json",
    "data/regions/sinnoh-b03-installer-evidence.json",
)
MAX_JSON = 1024 * 1024
MAX_FINDINGS = 300
# Matches a wider set of *potential* computed transfers, not a Ruby parser.
TRANSFER_CALL = re.compile(
    r"\b(?:reserve_transfer|pbWarp|pbTeleport|pbTransferPlayer|pbTransfer|"
    r"transfer_player|player_new_map_id)\b", re.I
)
VARIABLE_MAP = re.compile(r"\b(?:map_id|mapid|new_map_id)\b", re.I)
STATIC_NUMBER = re.compile(r"\b(?:3|5(?:1[89]|[2-9]\d))\b")
MAPPING_KEYS = {"maps", "map_ids", "mapping", "remap",
                "destination_map_ids", "new_ids", "assigned_map_ids"}

def deny(msg: str):
    raise ValueError("UNOVA_A08_BLOQUEADO: " + msg)

def fields(obj):
    return obj.attrs if isinstance(obj, RubyObject) else {}

def plain(value, limit=90):
    try:
        result = text(value) if isinstance(value, bytes) else str(value)
    except (TypeError, ValueError, UnicodeError):
        result = ""
    return "".join(ch if " " <= ch <= "~" else " " for ch in result)[:limit].strip()

def integer(value):
    return value if type(value) is int else None

def read_json(path: Path):
    if path.is_symlink() or not path.is_file():
        deny("manifesto ausente ou link: " + path.name)
    if not 0 < path.stat().st_size <= MAX_JSON:
        deny("manifesto excede tamanho permitido: " + path.name)
    return json.loads(path.read_text(encoding="utf-8-sig"))

def extract_targets(obj, *, depth=0):
    """Read only known mapping fields, not unrelated numbers like coordinates."""
    if depth > 8:
        deny("manifesto excessivamente aninhado")
    out = set()
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in MAPPING_KEYS:
                if isinstance(value, dict):
                    # For old->new remaps the destination is the mapping value.
                    for target in value.values():
                        if type(target) is int:
                            out.add(target)
                        elif isinstance(target, dict):
                            out.update(extract_targets(target, depth=depth+1))
                        elif isinstance(target, list):
                            out.update(t for t in target if type(t) is int)
                elif isinstance(value, list):
                    out.update(t for t in value if type(t) is int)
            elif isinstance(value, (dict, list)):
                out.update(extract_targets(value, depth=depth+1))
    elif isinstance(obj, list):
        for entry in obj[:20000]:
            if isinstance(entry, (dict, list)):
                out.update(extract_targets(entry, depth=depth+1))
    return out

def local_proofs(game: Path) -> dict:
    data = a04.directory_root(game)
    entries = []
    all_claims = set()
    incomplete = False
    for name in REGION_PROOFS:
        path = data/name
        if not path.exists() and not path.is_symlink():
            entries.append({"file": name, "status": "NOT_FOUND_NOT_PROOF"})
            incomplete = True
            continue
        try:
            obj = read_json(path)
            if not isinstance(obj, dict):
                deny("formato inesperado")
            ids = extract_targets(obj)
            overlaps = sorted(i for i in ids if 518 <= i <= 599)
            all_claims.update(overlaps)
            # A manifest may use a different schema; no claim means NOT certified.
            entries.append({"file": name,
                            "status": "OVERLAP_FOUND" if overlaps else "PARTIAL_SCHEMA_REVIEW",
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                            "candidate_overlap_ids": overlaps[:MAX_FINDINGS],
                            "recognized_destination_id_count": len(ids)})
            if not ids:
                incomplete = True
        except (ValueError, OSError, TypeError, json.JSONDecodeError,
                RecursionError, UnicodeError) as exc:
            entries.append({"file": name, "status": "READ_OR_SCHEMA_ERROR",
                            "reason": str(exc)[:140]})
            incomplete = True
    return {"manifests": entries, "observed_candidate_overlaps": sorted(all_claims),
            "manifest_coverage_incomplete": incomplete,
            "future_install_claims_verified": False,
            "blue_story_installer_code_executed": False}

def planning(project: Path, expected_hash: str) -> dict:
    entries = []
    issues = []
    for relative in PLANNING_FILES:
        path = project / relative
        try:
            obj = read_json(path)
            if not isinstance(obj, dict):
                deny("JSON de planejamento nao e objeto")
            if relative.endswith("unova-a05-mapid-candidates.json"):
                block = obj.get("unova_preferred_candidate", {})
                if (block.get("start"), block.get("end"), block.get("count")) != (518,599,82):
                    issues.append("A05 candidate block divergent")
                if obj.get("can_reserve_mapids") is not False:
                    issues.append("A05 falsely reports reservation")
            if relative.endswith("sinnoh-b05-mapid-planning.json"):
                block = obj.get("unova", {}).get("preferred_contiguous_candidate", {})
                if (block.get("start"), block.get("end"), block.get("count")) != (518,599,82):
                    issues.append("Sinnoh B05 candidate block divergent")
                if obj.get("unova", {}).get("reservation_confirmed") is not False:
                    issues.append("Sinnoh B05 falsely reports reservation")
            entries.append({"file": relative, "status": "READ_ONLY_PARSED",
                            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
        except (ValueError, OSError, TypeError, KeyError, json.JSONDecodeError) as exc:
            entries.append({"file": relative, "status": "UNAVAILABLE_OR_INVALID",
                            "reason": str(exc)[:140]})
            issues.append("Missing or invalid planning evidence: " + relative)
    return {"sources": entries, "issues": issues,
            "future_install_ownership_verified": False}

def context_of_event(event, event_id):
    d = fields(event)
    pages = d.get("@pages", [])
    if not isinstance(pages, list) or len(pages)>a07.MAX_PAGES:
        deny("paginas de Map001 invalidas")
    result={"event_id":event_id, "name":plain(d.get("@name", b"")),
            "x":integer(d.get("@x")), "y":integer(d.get("@y")), "pages":[]}
    for pi,page in enumerate(pages,1):
        p = fields(page)
        commands=p.get("@list", [])
        if not isinstance(commands,list) or len(commands)>a07.MAX_COMMANDS:
            deny("comandos Map001 invalidos")
        condition=fields(p.get("@condition"))
        flags={key[1:]:bool(condition.get(key)) for key in (
            "@switch1_valid","@switch2_valid","@variable_valid",
            "@self_switch_valid") if key in condition}
        guards={key[1:]:integer(condition.get(key)) for key in (
            "@switch1_id","@switch2_id","@variable_id","@variable_value")
            if key in condition}
        if "@self_switch_ch" in condition:
            guards["self_switch_ch"]=plain(condition["@self_switch_ch"],10)
        transfers=[]
        histogram=Counter()
        script_related=0
        for ci,cmd in enumerate(commands):
            c=fields(cmd)
            code=c.get("@code")
            if type(code) is not int:
                deny("codigo Map001 invalido")
            histogram[code]+=1
            if code in (355,655):script_related+=1
            if code==201:
                params=c.get("@parameters")
                if (isinstance(params,list) and len(params)>1 and
                    type(params[0]) is int and params[0]==0 and type(params[1]) is int):
                    transfers.append({"command_index":ci,"mode":"STATIC",
                                      "destination_map_id":params[1],
                                      "x":integer(params[2]) if len(params)>2 else None,
                                      "y":integer(params[3]) if len(params)>3 else None})
                else:
                    transfers.append({"command_index":ci,"mode":"DYNAMIC_OR_INVALID"})
        result["pages"].append({
            "page_index":pi,"trigger":integer(p.get("@trigger")),
            "conditions_active_flags":flags,"condition_inputs":guards,
            "command_count":len(commands),"script_command_count":script_related,
            "command_code_counts":{str(k):v for k,v in histogram.items()},
            "transfers":transfers[:MAX_FINDINGS],
            "transfers_truncated":len(transfers)>MAX_FINDINGS,
            "activation_verified_at_runtime":False})
    return result

def script_indicators(game:Path, map1:RubyObject)->dict:
    """Only target-map events + Scripts.rxdata; context is never exposed."""
    text_calls=0; variable_mentions=0; literal_clues=0
    scanned=0; issues=[]
    def record(blob):
        nonlocal text_calls,variable_mentions,literal_clues,scanned
        if isinstance(blob,bytes):
            s=blob.decode("utf-8","replace")
        elif isinstance(blob,str):
            s=blob
        else:
            issues.append("UNSUPPORTED_SCRIPT_TEXT")
            return
        if len(s)>a07.SCRIPT_ENTRY_LIMIT:
            issues.append("SCRIPT_TEXT_TOO_LARGE")
            return
        scanned+=1
        text_calls+=len(TRANSFER_CALL.findall(s))
        variable_mentions+=len(VARIABLE_MAP.findall(s))
        literal_clues+=len(STATIC_NUMBER.findall(s))
    for eid in TARGETS:
        ev=fields(map1).get("@events",{}).get(eid)
        for page in fields(ev).get("@pages",[]):
            for cmd in fields(page).get("@list",[]):
                p=fields(cmd)
                if p.get("@code") in (355,655):
                    params=p.get("@parameters",[])
                    if isinstance(params,list) and params:
                        record(params[0])
    path=a04.directory_root(game)/"Scripts.rxdata"
    decompressed=0
    if path.exists() or path.is_symlink():
        try:
            root=loads(a07.limited_read(path,a07.MAP_LIMIT))
            if not isinstance(root,list) or len(root)>3000:
                deny("Scripts.rxdata com estrutura inesperada")
            for entry in root:
                if not isinstance(entry,list) or len(entry)<3 or not isinstance(entry[2],bytes):
                    issues.append("UNSUPPORTED_COMPRESSED_SCRIPT_ENTRY")
                    continue
                dec=zlib.decompressobj()
                payload=dec.decompress(entry[2],a07.SCRIPT_ENTRY_LIMIT+1)
                if (not dec.eof or dec.unconsumed_tail or dec.unused_data or
                    len(payload)>a07.SCRIPT_ENTRY_LIMIT):
                    issues.append("INCOMPLETE_COMPRESSED_SCRIPT")
                    continue
                decompressed+=1
                record(payload)
        except (ValueError,TypeError,IndexError,OverflowError,
                OSError,zlib.error,RecursionError) as exc:
            issues.append("SCRIPTS_RXDATA_UNREADABLE: "+str(exc)[:120])
    else:
        issues.append("SCRIPTS_RXDATA_NOT_FOUND")
    return {"scan_scope":"MAP001_EVENTS_1_2_AND_SCRIPTS_RXDATA_ONLY",
            "text_entries_scanned":scanned,"script_entries_decompressed":decompressed,
            "transfer_api_name_occurrences":text_calls,
            "variable_map_name_occurrences":variable_mentions,
            "literal_id_3_or_518_599_occurrences":literal_clues,
            "issues":issues[:MAX_FINDINGS], "ruby_executed":False,
            "computed_mapids_resolved":False,"dynamic_scan_exhaustive":False}

def audit(game:Path,project:Path,a04_report:dict,a06_report:dict,a07_report:dict)->dict:
    game=a04.safe_path(game)
    project=a04.safe_path(project)
    base=a04_report.get("sources",{}).get("DECADES",{})
    digest=base.get("mapinfos_sha256")
    if (a04_report.get("phase")!="A04" or a06_report.get("phase")!="A06" or
        a07_report.get("phase")!="A07" or not digest or
        a06_report.get("mapinfos_sha256")!=digest or
        a07_report.get("mapinfos_sha256")!=digest or
        a07_report.get("review_errors_count")!=0 or
        a06_report.get("map_read_failures") or
        a07_report.get("map_files_parsed")!=len(base.get("maps",[]))):
        deny("A04 A06 A07 reais e coerentes sao obrigatorios")
    row=next((m for m in base["maps"] if m["id"]==1),None)
    if row is None:deny("Map001 nao consta do A04")
    path=a04.directory_root(game)/row["source_filename"]
    raw=a07.limited_read(path,a07.MAP_LIMIT)
    if hashlib.sha256(raw).hexdigest()!=row["sha256"]:
        deny("Map001 mudou depois de A04")
    parsed=loads(raw)
    if not isinstance(parsed,RubyObject) or parsed.name!="RPG::Map":
        deny("Map001 nao e RPG::Map")
    events=fields(parsed).get("@events",{})
    if not isinstance(events,dict):deny("Map001 eventos invalidos")
    rows=[]
    problems=[]
    for eid in TARGETS:
        event=events.get(eid)
        if not isinstance(event,RubyObject):
            problems.append("Map001 event "+str(eid)+" absent")
        else:
            rows.append(context_of_event(event,eid))
    reconstructed=sorted((e["event_id"],p["page_index"],t["command_index"],t.get("destination_map_id"))
        for e in rows for p in e["pages"] for t in p["transfers"]
        if t["mode"]=="STATIC" and t.get("destination_map_id")==3)
    a07_refs=sorted((i.get("event_id"),i.get("page_index"),i.get("command_index"),3)
        for i in a07_report.get("static_interest_references",[])
        if (i.get("source_type")=="MAP" and i.get("source_map_id")==1 and
            i.get("event_id") in TARGETS and i.get("destination_map_id")==3))
    if reconstructed!=a07_refs:
        problems.append("Map001 MapID3 provenance does not match A07")
    map3_present=3 in set(a04_report.get("observed_or_declared_occupied_map_ids",[]))
    local=local_proofs(game)
    plan=planning(project,digest)
    extra=script_indicators(game,parsed)
    occupied=set(a04_report.get("observed_or_declared_occupied_map_ids",[]))
    overlaps=sorted(i for i in range(518,600) if i in occupied)
    if overlaps:problems.append("MapIDs already observed as occupied in candidate block")
    if local["observed_candidate_overlaps"]:
        problems.append("Local installer manifests claim candidate MapIDs")
    problems.extend(plan["issues"])
    return {
        "schema":1,"region":"UNOVA","phase":"A08",
        "mode":"INERT_MAP001_AND_REGIONAL_READINESS_REVIEW",
        "status":"BLOCKED_CANDIDATE_CONFLICT_REVIEW" if overlaps or local["observed_candidate_overlaps"]
                 else "READ_ONLY_REVIEW_COMPLETE_RESERVATION_PENDING",
        "mapinfos_sha256":digest,
        "map001_event_context":rows,
        "map001_target_events_missing":sorted(int(x.rsplit(" ",2)[1]) for x in problems if x.startswith("Map001 event ")) if False else [i for i in TARGETS if i not in events],
        "mapid3_physically_or_declared_present":map3_present,
        "mapid3_referenced_but_not_found":bool(reconstructed) and not map3_present,
        "mapid3_transfers_reconciled_with_a07":reconstructed==a07_refs,
        "candidate_518_599_occupied_ids":overlaps,
        "candidate_518_599_observed_vacant":not overlaps,
        "local_region_manifests":local,"planning_evidence":plan,
        "additional_script_indicators":extra,
        "review_problems":problems[:MAX_FINDINGS],
        "review_problems_count":len(problems),
        "manual_decisions_pending":[
            "Identify why Map001 events 1 and 2 transfer to absent MapID 3",
            "Confirm player conditions and intended targets inside Game.exe runtime",
            "Verify future Blue-Story installer claims and dynamic transfers beyond heuristic scope",
            "Obtain lawful Unova source maps and mapping, then stage rollback and native QA",
        ],
        "all_mapid_references_certified":False,
        "blue_story_future_claims_certified":False,
        "region_source_rights_verified":False,
        "can_reserve_mapids":False,"can_install":False,
        "game_exe_tested":False,"android_tested":False,
        "game_or_saves_modified":False,"bar_a_completed":0,"bar_a_total":8,
    }

def save(project:Path, report:dict)->Path:
    project=a04.safe_path(project)
    for folder in (project/".blue-work",project/".blue-work/unova",project/OUT):
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            deny("pasta privada de relatorios insegura")
        folder.mkdir(exist_ok=True)
    raw=(json.dumps(report,sort_keys=True,ensure_ascii=False,indent=2)+"\n").encode("utf-8")
    out=project/OUT/("a08-readiness-"+hashlib.sha256(raw).hexdigest()[:16]+".json")
    if out.is_symlink():deny("relatorio symlink")
    if out.exists():
        if out.read_bytes()!=raw:deny("evidencia com conteudo divergente")
    else:
        with out.open("xb") as handle:handle.write(raw)
    return out
