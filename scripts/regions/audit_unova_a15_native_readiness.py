#!/usr/bin/env python3
"""A15: GitHub-only, fail-closed Unova native-readiness source audit.

Read JSON, Markdown and source text from the repository only. Never read
installed game data, archives, private receipts, maps, saves or donor assets.
Never run Game.exe, installers, Windows Sandbox, JoiPlay or arbitrary Python.
A passing audit means ONLY that the BLOCKERS are properly recorded.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
FILE = "data/regions/unova-a15-native-readiness-matrix.json"
STAGES = tuple(f"A{i:02d}" for i in range(4,15))
GATES = tuple(f"A_TECH_{i:02d}" for i in range(1,9))
GATE_DEPS = (
 ("A04","A12"),
 ("A04","A05","A06","A07","A08","A09","A10","A11","A12"),
 ("A_TECH_01","A_TECH_02"),
 ("A_TECH_03","A13","A14"),
 ("A_TECH_03",),
 ("A_TECH_04","A_TECH_05"),
 ("A_TECH_04","A_TECH_06"),
 ("A_TECH_01","A_TECH_02","A_TECH_03","A_TECH_04",
  "A_TECH_05","A_TECH_06","A_TECH_07"),
)
GATE_EVIDENCE = (
 ("donor_asset_manifest_sha256","per_asset_rights_approval"),
 ("native_mapids_reserved_review","dynamic_references_review",
  "mapid_3_design_and_runtime_resolution"),
 ("source_to_destination_mapid_mapping","unova_map_and_tileset_authorization"),
 ("source_installer_claims_review","native_atomic_rollback_qa"),
 ("native_story_events_verified","native_trainers_encounters_pbs_verified"),
 ("native_save_isolation_verified","regional_checkpoint_and_blackout_qa"),
 ("windows_release_manifest_and_qa","android_joiplay_release_manifest_and_qa"),
 ("independent_human_approval","signed_reproducible_native_qa_receipts"),
)
STEP_DEPS = (
 (),("A04",),("A04","A05"),("A04","A06"),("A07",),
 ("A08",),("A09",),("A10",),("A11",),("A12",),("A13",),
)
SCRIPT_SUFFIXES = (
 "mapids","candidates","references","reference_provenance","readiness",
 "intro_and_claims","dynamic_matrix","intro_preflight","ownership",
 "private_qa","sandbox",
)
DOC_SUFFIXES = (
 "MAPIDS_MULTIRREGIONAIS","PROPOSTA_MAPIDS_B01_B04",
 "REFERENCIAS_NATIVAS_MAPIDS","RASTREIO_MAPID3_E_SCRIPTS",
 "EVENTOS_MAP001_MANIFESTOS","FORENSE_INTRO_E_REIVINDICACOES",
 "DESTINOS_DINAMICOS_MATRIZ","INTRO_PRE_RESERVA_REVERSIVEL",
 "PROPRIEDADE_REGIONAL_QA_ISOLADO","COPIA_QA_PRIVADA",
 "SANDBOX_ISOLAMENTO_SAVES",
)
SOURCES = {
 "historical_mapids":"data/regions/unova-a05-mapid-candidates.json",
 "region_registry":"site/public/data/regions.json",
 "github_tracker":"site/public/data/unova-github-progress.json",
 "prior_G08":"data/regions/unova-g08-multiregional-contract.json",
 "donor_rights_auditor":"scripts/regions/audit_unova_e06_rights_inventory.py",
 "existing_native_installer":"scripts/install_game.py",
 "windows_blue_story":"scripts/windows/Bootstrap.cs",
 "android_joiplay":"scripts/android/update_client.py",
 "historical_report":"docs/MAPIDS_DECADES_SINNOH_UNOVA_2026-11-17.md",
 "native_blockers_report":"docs/UNOVA_G08_3_MATRIZ_MULTIRREGIONAL_OFFLINE.md",
}
ROOT_FIELDS = {
 "schema_version","phase","region","campaign","status","sources",
 "historical_snapshot","provenance_notes","steps","technical_gates",
 "required_native_evidence","cross_region_safeguards","safe_next_action",
 "generated_writes_allowed","native_game_files_modified","saves_read",
 "saves_modified","tests_game_exe_executed","tests_joiplay_executed",
 "native_technical_completed","native_technical_total",
 "native_playable_completed","native_playable_total",
 "g_github_completed","g_github_total","can_install",
 "can_reserve_mapids","can_release",
}
STEP_FIELDS = {
 "id","title","depends_on","tool_path","doc_path","tool_state",
 "native_acceptance","verified_receipt","operator_only_required",
 "required_evidence","can_reserve","can_install",
 "game_exe_qa_verified","android_qa_verified",
}
GATE_FIELDS = {"id","title","depends_on","evidence_keys","status",
               "approved","can_install"}
EXPECTED_HISTORY = {
 "date":"2026-11-17",
 "mapinfos_sha256":"8f2d23d49ee0bb97779b129ffd7d14c161f4bef27fede6b89111ce266760a420",
 "physically_observed_mapids":648,
 "legacy_b04_missed_short_ids":31,
 "unova_candidate_start":518,"unova_candidate_end":599,"unova_candidates":82,
 "sinnoh_hold_start":442,"sinnoh_hold_end":517,"sinnoh_hold_count":76,
 "total_unova_planning_candidates":174,"symbolic_unova_areas":74,
 "mapid_3_missing_reported":True,"map001_intro_refs_to_3_reported":2,
 "computed_expressions_a09_reported":20,
 "independently_verified_native_mapids_from_repo":False,
 "future_mapid_reservations_verified":False,
 "candidate_block_native_reserved":False,
}
NEXT_ACTION = {
 "id":"A16","title":"Recepção segura de recibos A04–A14 e verificação cruzada de proveniência",
 "mode":"GITHUB_ONLY_REDACTED_MANIFEST_VALIDATION",
 "prerequisites":["A15 CI green","No raw Game.exe, saves, maps or licensed assets in GitHub"],
 "do_not_collect":["Game.exe","Map*.rxdata","Saves","Savedata",
                   "player account data","donor media files"],
 "accept_only":["redacted JSON receipts with hashes",
                "source attribution and rights records",
                "independent review outcomes"],
 "auto_reserve_mapids":False,"auto_install":False,
 "auto_approve_rights":False,
}

def refuse(message:str)->None:
    raise ValueError("UNOVA_A15_BLOCKED: "+message)

def exact(obj:Any,fields:set[str],context:str)->dict:
    if type(obj) is not dict or set(obj)!=fields:
        refuse(context+" has missing/extra keys")
    return obj

def source(root:Path,path:str)->str:
    if not re.fullmatch(r"[a-zA-Z0-9_./-]+",path) or ".." in path.split("/"):
        refuse("unsafe repository path")
    target=root/path
    if target.is_symlink() or not target.is_file():
        refuse("missing/untrusted repository file: "+path)
    if target.stat().st_size>2_000_000:
        refuse("unexpectedly large source file: "+path)
    return target.read_text(encoding="utf-8")

def read_json(root:Path,path:str)->dict:
    return json.loads(source(root,path))

def validate_document(matrix:Any,root:Path=ROOT)->dict:
    root=Path(root)
    exact(matrix,ROOT_FIELDS,"A15 matrix")
    expected={
        "schema_version":1,"phase":"A15","region":"UNOVA",
        "campaign":"WHITE_BW",
        "status":"TECHNICAL_READINESS_ONLY_NO_NATIVE_APPROVAL",
        "sources":SOURCES,
        "historical_snapshot":EXPECTED_HISTORY,
        "cross_region_safeguards":["DECADES","KANTO","JOHTO","HOENN","SINNOH","UNOVA"],
        "safe_next_action":NEXT_ACTION,
        "generated_writes_allowed":False,"native_game_files_modified":False,
        "saves_read":False,"saves_modified":False,
        "tests_game_exe_executed":False,"tests_joiplay_executed":False,
        "native_technical_completed":0,"native_technical_total":8,
        "native_playable_completed":0,"native_playable_total":32,
        "g_github_completed":32,"g_github_total":32,
        "can_install":False,"can_reserve_mapids":False,"can_release":False,
    }
    for key,val in expected.items():
        if type(matrix[key]) is not type(val) or matrix[key]!=val:
            refuse("false readiness, changed source or premature approval: "+key)
    notes=matrix["provenance_notes"]
    if type(notes) is not list or len(notes)<5 or any(
        type(n) is not str or len(n)<40 for n in notes):
        refuse("provenance caveats incomplete")
    stages=matrix["steps"]
    if type(stages) is not list or len(stages)!=len(STAGES):
        refuse("A04–A14 stages incomplete")
    for n,(id,row) in enumerate(zip(STAGES,stages)):
        exact(row,STEP_FIELDS,"native stage "+id)
        if (row["id"]!=id or type(row["title"]) is not str
            or not row["title"].strip()
            or tuple(row["depends_on"])!=STEP_DEPS[n]
            or row["tool_path"]!=f"scripts/regions/audit_unova_{id.lower()}_{SCRIPT_SUFFIXES[n]}.py"
            or row["doc_path"]!=f"docs/UNOVA_{id}_{DOC_SUFFIXES[n]}.md"
            or row["tool_state"]!="SOURCE_TOOL_PRESENT_UNEXECUTED_IN_CI"
            or row["native_acceptance"]!="BLOCKED_MISSING_REVIEWED_EVIDENCE"
            or row["verified_receipt"] is not None
            or row["operator_only_required"] is not True
            or type(row["required_evidence"]) is not str
            or len(row["required_evidence"])<50):
            refuse("A04–A14 native acceptance tampered: "+id)
        for field in ("can_reserve","can_install",
                      "game_exe_qa_verified","android_qa_verified"):
            if row[field] is not False:
                refuse("A04–A14 false native claim "+id+"."+field)
        tool=source(root,row["tool_path"])
        doc=source(root,row["doc_path"])
        if not ("def " in tool and "Unova" in doc and id in doc[:200]):
            refuse("missing historical A-step auditor/document pairing: "+id)
    technical=matrix["technical_gates"]
    if type(technical) is not list or len(technical)!=8:
        refuse("8 technical gates incomplete")
    expected_keys=set(k for grp in GATE_EVIDENCE for k in grp)
    req=exact(matrix["required_native_evidence"],expected_keys,"native evidence gate set")
    if any(value is not None for value in req.values()):
        refuse("unsigned real-world evidence cannot be approved by the GitHub-only matrix")
    for i,(id,row) in enumerate(zip(GATES,technical)):
        exact(row,GATE_FIELDS,"technical gate "+id)
        if (row["id"]!=id or type(row["title"]) is not str
            or not row["title"].strip()
            or tuple(row["depends_on"])!=GATE_DEPS[i]
            or tuple(row["evidence_keys"])!=GATE_EVIDENCE[i]
            or row["status"]!="PENDING_NATIVE_EVIDENCE"
            or row["approved"] is not False or row["can_install"] is not False):
            refuse("false technical gate approval or dependency: "+id)
    old=read_json(root,SOURCES["historical_mapids"])
    h=matrix["historical_snapshot"]
    observed=old["evidence"]
    preferred=old["unova_preferred_candidate"]
    hold=old["sinnoh_administrative_hold"]
    if (observed["historical_mapinfos_sha256"]!=h["mapinfos_sha256"]
        or observed["b01_physical_map_count"]!=h["physically_observed_mapids"]
        or observed["b04_omitted_short_mapid_count"]!=h["legacy_b04_missed_short_ids"]
        or any(preferred[k]!=h["unova_candidate_"+k]
               for k in ("start","end"))
        or preferred["count"]!=h["unova_candidates"]
        or hold["start"]!=h["sinnoh_hold_start"]
        or hold["end"]!=h["sinnoh_hold_end"]
        or hold["count"]!=h["sinnoh_hold_count"]
        or sum(x["count"] for x in old["unova_other_candidate_ranges"])+preferred["count"]!=174
        or old["unova_symbolic_areas_count"]!=h["symbolic_unova_areas"]
        or old["can_reserve_mapids"] is not False or old["can_install"] is not False
        or old["future_reservations_verified"] is not False
        or old["proposed_area_to_native_mapid"]!={}):
        refuse("historical A05/B05 candidate baseline changed or native MapIDs assigned")
    registry=read_json(root,SOURCES["region_registry"])
    progress=read_json(root,SOURCES["github_tracker"])
    prior=read_json(root,SOURCES["prior_G08"])
    if (registry["regions"]["UNOVA"]["status"]!="planned"
        or progress["status"]!="PLANNED_NOT_NATIVE_PLAYABLE"
        or progress["native_technical_bar"]!={"completed":0,"total":8}
        or progress["native_playable_bar"]!={"completed":0,"total":32}
        or sum(x["status"]=="done" for g in progress["groups"] for x in g["tasks"])!=32
        or prior["can_install"] is not False
        or prior["native_playable_completed"]!=0):
        refuse("live GitHub bars or regional registry falsely promoted")
    for name,path in SOURCES.items():
        text=source(root,path)
        if not text.strip():
            refuse("empty audit source "+name)
    rights=source(root,SOURCES["donor_rights_auditor"])
    if ('"rights_status": "REVIEW_REQUIRED_NOT_LICENSED"' not in rights
        or '"license_verified": False' not in rights
        or '"can_install": False' not in rights):
        refuse("rights-review gate changed without independent acceptance")
    a07=source(root,"docs/UNOVA_A07_RASTREIO_MAPID3_E_SCRIPTS.md")
    a09=source(root,"docs/UNOVA_A09_FORENSE_INTRO_E_REIVINDICACOES.md")
    a10=source(root,"docs/UNOVA_A10_DESTINOS_DINAMICOS_MATRIZ.md")
    if "MapID 3" not in a07 or "duas" not in a07 or "20" not in a10 or "518" not in a09:
        refuse("reported Map001/mapID3/dynamic expressions provenance missing")
    return {
        "phase":"A15","status":"SOURCE_GATES_VERIFIED_NATIVE_BLOCKED",
        "historical_mapids":648,"historical_unova_candidates":82,
        "historical_unova_other_candidates":92,
        "sinnoh_hold":76,"area_symbols":74,"mapid3_unresolved":True,
        "a04_to_a14_tools_present":len(STAGES),
        "pending_native_gates":len(GATES),
        "missing_accepted_native_evidence":len(expected_keys),
        "github_g_bar":32,"native_a_bar":0,
        "native_playable_bar":0,"can_install":False,
        "can_reserve_mapids":False,"game_exe_tested":False,
        "joiplay_tested":False,"saves_read":False,
        "native_files_written":0,
        "next_safe_step":"A16_REDACTED_RECEIPT_INTAKE_ONLY",
    }

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check",action="store_true")
    group.add_argument("--matrix",action="store_true")
    args=parser.parse_args(argv)
    try:
        matrix=read_json(ROOT,FILE)
        outcome=validate_document(matrix)
        if args.matrix:
            outcome.update({
                "blockers":[{"phase":s["id"],"status":s["native_acceptance"],
                             "evidence_required":s["required_evidence"]}
                            for s in matrix["steps"]],
                "technical_gates":[{"gate":g["id"],"title":g["title"],
                                   "missing_evidence":g["evidence_keys"]}
                                  for g in matrix["technical_gates"]],
            })
        print(json.dumps(outcome,ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,TypeError,KeyError,OSError,IndexError,RecursionError) as exc:
        print("UNOVA_A15_BLOCKED: "+str(exc)[:320])
        return 2

if __name__=="__main__":
    raise SystemExit(main())
