#!/usr/bin/env python3
"""Sinnoh G11: audit the five PUBLIC contracts as one read-only CI chain.

No local installation discovery, source ZIP, B07/B08 stage, B09 clone, Windows
Sandbox, personal saves, Game.exe, or JoiPlay is opened. Only static metadata,
synthetic regression coverage, and the B10 policy *template* are assessed.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))

import audit_sinnoh_b06_technical_candidate as b06
import build_sinnoh_b07_private_stage as b07
import audit_sinnoh_b08_private_qa as b08
import build_sinnoh_b09_native_qa as b09
import prepare_sinnoh_b10_save_isolation as b10
import audit_sinnoh_b11_host_saves as b11

CONTRACT_PATHS={
    "b00":b06.B00, "b01":b06.B01, "b04":b06.B04, "b05":b06.B05, "b06":b06.B06,
    "b07":b07.CONTRACT, "b08":b08.CONTRACT, "b09":b09.CONTRACT,
    "b10":b10.CONTRACT, "b11":b11.CONTRACT,
}
SUITES={
    "B07":"tests/test_sinnoh_b07_private_stage.py",
    "B08":"tests/test_sinnoh_b08_private_qa.py",
    "B09":"tests/test_sinnoh_b09_native_qa.py",
    "B10":"tests/test_sinnoh_b10_save_isolation.py",
    "B11":"tests/test_sinnoh_b11_host_saves.py",
    "G11":"tests/test_sinnoh_g11_ci_chain.py",
}
STATUS={
    "B07":"PRIVATE_GEOMETRY_BUILDER_READY_NOT_NATIVE_INSTALLED",
    "B08":"PRIVATE_QA_AUDITOR_READY_USER_STAGE_NOT_RECEIVED",
    "B09":"PRIVATE_NATIVE_QA_CLONE_BUILDER_READY_B08_RUNTIME_EVIDENCE_PENDING",
    "B10":"WINDOWS_SANDBOX_SAVE_ISOLATION_PREPARED_NO_NATIVE_EXECUTION",
    "B11":"HOST_SAVE_WATCH_AND_GUEST_DIAGNOSTICS_READY_NOT_EXECUTED",
}

def blocked(message):
    raise ValueError("SINNOH_G11_BLOCKED: "+message)

def count_synthetic_tests(source):
    if type(source) is not str:blocked("test suite source is not text")
    try:
        root=ast.parse(source)
    except (SyntaxError,ValueError):
        blocked("invalid Python test source")
    cases=[
        node for top in root.body if isinstance(top,ast.ClassDef)
        and any(isinstance(base,(ast.Name,ast.Attribute)) for base in top.bases)
        for node in top.body
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    if not cases or any(node.args.args[0].arg!="self" for node in cases
                        if node.args.args):
        blocked("missing synthetic test methods")
    return len(cases)

def audit(docs, sources):
    if (type(docs) is not dict or set(docs)!=set(CONTRACT_PATHS)
            or any(type(obj) is not dict for obj in docs.values())
            or type(sources) is not dict or set(sources)!=set(SUITES)):
        blocked("incomplete public contract or test suite list")
    try:
        rows07=b07.check_contract(docs["b07"],docs["b06"],docs["b00"],
                                  docs["b01"],docs["b04"],docs["b05"])
        rows08=b08.check_contract(docs["b08"],docs["b07"],docs["b06"],
                                  docs["b00"],docs["b01"],docs["b04"],docs["b05"])
        rows09=b09.check_contract(docs["b09"],docs["b08"],docs["b07"],docs["b06"],
                                  docs["b00"],docs["b01"],docs["b04"],docs["b05"])
        rows10=b10.check_contract(docs["b10"],docs["b09"],docs["b08"],docs["b07"],
                                  docs["b06"],docs["b00"],docs["b01"],docs["b04"],docs["b05"])
        b11.check_contract(docs["b11"],docs["b10"],docs["b09"])
    except (ValueError,KeyError,TypeError,IndexError,AttributeError):
        blocked("B07-B11 metadata contract or provenance was altered")
    if any(len(rows)!=54 for rows in (rows07,rows08,rows09,rows10)):
        blocked("the four stage maps must match 54 terrain candidates")
    ids=[row["candidate_destination_map_id"] for row in rows07]
    if ids!=list(range(442,496)) or any(
            [row["candidate_destination_map_id"] for row in rows]!=ids
            for rows in (rows08,rows09,rows10)):
        blocked("candidate IDs mismatch or published as installed")
    if docs["b07"].get("source_zip_sha256")!=docs["b08"].get("b07_source_sha256"):
        blocked("B07/B08 source hash mismatch")
    if (docs["b07"].get("native_mapinfos_sha256")!=docs["b09"].get("native_baseline_mapinfos_sha256")
            or docs["b07"].get("native_tilesets_sha256")!=docs["b09"].get("native_baseline_tilesets_sha256")
            or docs["b09"].get("native_inventory_sha256")!=docs["b10"].get("native_b01_inventory_sha256")
            or docs["b09"].get("clone_workspace_subdir")!=docs["b10"].get("b09_clone_workspace")):
        blocked("B07/B09/B10 native baseline or clone identity drift")
    if (docs["b10"].get("expected_original_maps")!=648
            or docs["b10"].get("expected_sinnoh_maps")!=54
            or docs["b10"].get("expected_clone_maps")!=702
            or docs["b11"].get("expected_clone_maps")!=702):
        blocked("expected QA-only map counts drift")
    if any(docs[k].get("region")!="SINNOH" or docs[k].get("stage")!=k.upper()
           or docs[k].get("status")!=STATUS[k.upper()]
           for k in ("b07","b08","b09","b10","b11")):
        blocked("stage identity or state changed")
    if any(docs[k].get("phase_"+phase+"_approved")!=0
           for k in ("b07","b08","b09","b10","b11") for phase in ("b","c","d")):
        blocked("B/C/D advances without native execution")
    if any(docs[k].get(p) is not False
           for k in ("b07","b08","b09","b10","b11")
           for p in ("r07_complete","r08_complete","r09_complete")):
        blocked("unapproved regional reservation, rights or runtime")
    if docs["b07"].get("preserves_saves") is not True or docs["b09"].get("excludes_saved_games_and_user_profiles") is not True or docs["b10"].get("host_data_and_saves_never_mapped") is not True or docs["b11"].get("host_saves_never_copied") is not True:
        blocked("save isolation contract was weakened")
    if (docs["b07"].get("imports_donor_events") is not False
            or docs["b07"].get("imports_donor_scripts") is not False
            or docs["b07"].get("imports_donor_pbs") is not False
            or docs["b08"].get("overlay_is_a_non_runnable_private_copy") is not True
            or docs["b09"].get("never_launches_executable") is not True
            or docs["b10"].get("no_logon_command") is not True
            or docs["b11"].get("no_autostart_Game_exe") is not True):
        blocked("B07-B11 acquired executable or donor-event capability")

    # Only synthesize XML in memory: check the exact two read-only mappings and
    # disabled networking, clipboard, input and logon command. NEVER spawn a VM.
    clone=r"C:\Synthetic\QAClone"
    tools=r"C:\Synthetic\QATools"
    xml=b10.xml_wsb(clone,tools)
    try:
        if b10.check_wsb_policy(xml,clone,tools) is not True:
            blocked("WSB policy did not verify")
    except (ValueError,TypeError,KeyError,AttributeError):
        blocked("WSB policy is unsafe")

    counts={stage:count_synthetic_tests(sources[stage]) for stage in SUITES}
    if any(count<8 for count in counts.values()):
        blocked("incomplete CI synthetic fixture suite")

    return {
        "schema":1,"region":"SINNOH","stage":"G11",
        "status":"B07_B11_PUBLIC_CONTRACT_CHAIN_RECONCILED_SYNTHETIC_ONLY",
        "mode":"GITHUB_CI_STATIC_AND_SYNTHETIC_NO_NATIVE_EXECUTION",
        "chain":[{
            "stage":stage,
            "source_contract_verified":True,
            "test_suite":SUITES[stage],
            "discovered_test_methods":counts[stage],
            "native_runtime_verified":False,
        } for stage in ("B07","B08","B09","B10","B11")],
        "integration_suite":{
            "test_file":SUITES["G11"],
            "discovered_test_methods":counts["G11"],
            "includes_synthetic_full_chain":True,
        },
        "expected_terrain_candidate_ids":[442,495],
        "expected_synthetic_clone_map_count":702,
        "candidate_terrain_maps":54,
        "empty_placeholders_not_staged":22,
        "private_pngs_required_by_B08":14,
        "png_bytes_of_real_donor_inspected_in_CI":0,
        "assumed_installed_or_playable":False,
        "wsb_template_readonly":True,
        "wsb_template_network_disabled":True,
        "wsb_template_clipboard_disabled":True,
        "no_game_autostart":True,
        "saves_excluded_from_B09":True,
        "save_snapshot_coverage_proven":False,
        "sandbox_run_performed":False,
        "game_exe_tested":False,"joiplay_tested":False,
        "r07_complete":False,"r08_complete":False,"r09_complete":False,
        "can_install_live_game":False,
        "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
        "public_report_only":True,
        "private_baseline_uploaded":False,
    }

def run(root=ROOT):
    root=Path(root)
    docs={k:b06.load(root / v.relative_to(ROOT)) for k,v in CONTRACT_PATHS.items()}
    sources={}
    for k,path in SUITES.items():
        f=root/path
        if f.is_symlink() or not f.is_file() or f.stat().st_size>300000:
            blocked("unsafe test source")
        sources[k]=f.read_text(encoding="utf-8")
    return audit(docs,sources)

def main(argv=None):
    try:
        if argv not in (None,[]):
            blocked("G11 receives no local paths or private evidence as arguments")
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,TypeError,IndexError,KeyError,UnicodeError,AttributeError):
        print("SINNOH_G11_BLOCKED: public contract chain or CI suites inconsistent",
              file=sys.stderr)
        return 2

if __name__=="__main__":
    raise SystemExit(main(sys.argv[1:]))
