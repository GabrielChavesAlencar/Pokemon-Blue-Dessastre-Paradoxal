#!/usr/bin/env python3
"""Sinnoh L00: strict PUBLIC report readiness check, not native approval.

Only versioned repository contracts and a manually supplied, allowlisted JSON
summary may be read. The optional --workspace-reports always names ONE fixed
file in .blue-work; it does not scan a PC or accept arbitrary paths.
No map, PNG, private snapshot, game binary, personal save, VM, or JoiPlay is read,
executed or uploaded. A self-reported summary is NEVER independent proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_g12_handoff as g12
import audit_sinnoh_g11_ci_chain as g11

TEMPLATE="data/regions/sinnoh-l00-public-reports.json"
PRIVATE_REPORT=".blue-work/sinnoh-l00-input/public-reports.json"
CONTRACTS={
    "B09":"data/regions/sinnoh-b09-native-qa.json",
    "B10":"data/regions/sinnoh-b10-save-isolation.json",
    "B11":"data/regions/sinnoh-b11-host-save-audit.json",
    "R07":"data/regions/sinnoh-b02-reservations.json",
    "R08":"data/regions/sinnoh-source.json",
}
STAGES=("B09","B10","B11","R07","R08")
SHA=re.compile(r"[0-9a-f]{64}\Z")
STATUS={
    "B09":"PRIVATE_NATIVE_QA_CLONE_CREATED_NOT_RUNNABLE_YET",
    "B10":"WSB_CONFIG_PREPARED_NOT_LAUNCHED",
    "R08":"RIGHTS_REVIEW_PENDING",
}
L00_FALSE_FIELDS=("native_approval","safe_to_launch","can_install_live_game",
                  "game_exe_tested","joiplay_tested","r07_complete",
                  "r08_complete","r09_complete","rights_verified")
BLOCKERS={
    "B09":"Clone privado B09 não comprovado fisicamente ou não revisado independentemente",
    "B10":"WSB B10 não executada e isolamento de runtime não demonstrado",
    "B11":"Comparação B11 limitada aos diretórios monitorados; cobertura global não provada",
    "R07":"Reservas futuras, propriedade de MapIDs e colisões precisam de comprovação física",
    "R08":"Licenças de cada ativo, 14 PNGs reais, mapas/warps e PBS compilado não comprovados",
}
EXPECTED_FIELDS={
 "B09":{"stage","status","plan_sha256","native_inventory_sha256",
        "map_ids_clone_total","b08_maps_validated","b08_pngs_validated",
        "saves_copied","game_exe_executed","safe_to_launch",
        "can_install_live_game","r07_complete","phase_b_approved"},
 "B10":{"stage","status","source_clone_sha256",
        "native_map_ids","sinnoh_terrain_map_ids","expected_total_maps",
        "all_cloned_files_sha_verified","sandbox_feature_enabled_on_host",
        "mapped_folders_read_only","internet_networking_enabled",
        "clipboard_enabled","sandbox_session_started","game_exe_started",
        "host_save_directories_mapped","save_write_isolation_runtime_verified",
        "rights_verified","r07_complete","phase_b_approved"},
 "B11":{"stage","before","after"},
 "R07":{"stage","status","native_snapshot_present","native_occupied_count",
        "native_mapinfos_sha256","future_regions_with_evidence",
        "future_regions_required","collisions_count",
        "candidate_safety_reviewable","r07_complete",
        "may_apply_to_main_game","rights_verified"},
 "R08":{"stage","status","source_expected_png_count",
        "per_asset_licenses_reviewed_count","source_asset_rights_verified",
        "physical_maps_approved","twinleaf_map_bindings_verified",
        "twinleaf_warps_verified","barry_pbs_compiled",
        "r08_complete","can_install"},
}
B11_BEFORE={"status","monitored_directories_count","scope_selection_mode",
            "default_scopes_not_monitored","monitored_files_before",
            "paths_names_and_saves_in_report","windows_sandbox_started",
            "Game_exe_started","host_saves_runtime_isolation_confirmed",
            "coverage_is_partial","r07_complete","phase_b_approved"}
B11_AFTER={"status","monitored_directories_count","scope_selection_mode",
           "default_scopes_not_monitored","monitored_files_before",
           "monitored_files_after","files_added","files_removed",
           "files_changed","watch_unchanged","coverage_is_partial",
           "guest_observation_self_reported",
           "guest_vm_execution_independently_verified",
           "complete_host_save_coverage_verified",
           "true_runtime_save_path_in_source_verified",
           "host_saves_globally_isolated_proven","assets_rights_verified",
           "R07_R08_R09_approved","gameplay_approved",
           "phase_b_approved","phase_c_approved","phase_d_approved",
           "paths_names_and_saves_in_report"}

def blocked(reason):
    raise ValueError("SINNOH_L00_BLOCKED: "+reason)

def exact(obj,keys):
    if type(obj) is not dict or set(obj)!=set(keys):
        blocked("campo privado, desconhecido ou ausente no relatório sanitizado")

def is_sha(x):
    return type(x) is str and SHA.fullmatch(x) is not None

def int_in(x,lo,hi):
    return type(x) is int and lo<=x<=hi

def require_false(d,fields):
    if any(d.get(k) is not False for k in fields):
        blocked("evidência fabricada ou aprovação não autorizada")

def digest(d):
    raw=json.dumps(d,ensure_ascii=True,sort_keys=True,separators=(",",":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

def check_report(stage,record,contracts,others):
    exact(record,EXPECTED_FIELDS[stage])
    if record["stage"]!=stage:blocked("etapa não corresponde ao contrato")
    if stage=="B09":
        if record["status"]!=STATUS["B09"] or not is_sha(record["plan_sha256"]) or not is_sha(record["native_inventory_sha256"]):
            blocked("B09 com status ou hash inválido")
        if (record["native_inventory_sha256"]!=contracts["B09"]["native_inventory_sha256"]
                or not int_in(record["map_ids_clone_total"],702,702)
                or not int_in(record["b08_maps_validated"],54,54)
                or not int_in(record["b08_pngs_validated"],14,14)):
            blocked("recibo B09 diverge da base pública")
        require_false(record,("saves_copied","game_exe_executed","safe_to_launch",
                              "can_install_live_game","r07_complete"))
        if not int_in(record["phase_b_approved"],0,0):blocked("B09 fase não aprovada")
    elif stage=="B10":
        if (record["status"]!=STATUS["B10"] or not is_sha(record["source_clone_sha256"])
                or record["source_clone_sha256"]!=others["B09"]["plan_sha256"]):
            blocked("B10 sem vínculo SHA com B09")
        for k,n in (("native_map_ids",648),("sinnoh_terrain_map_ids",54),
                    ("expected_total_maps",702)):
            if not int_in(record[k],n,n):blocked("contagem B10 mudou")
        for k in ("all_cloned_files_sha_verified","sandbox_feature_enabled_on_host",
                  "mapped_folders_read_only"):
            if record[k] is not True:blocked("B10 configuração de isolamento ausente")
        require_false(record,("internet_networking_enabled","clipboard_enabled",
                              "sandbox_session_started","game_exe_started",
                              "host_save_directories_mapped",
                              "save_write_isolation_runtime_verified",
                              "rights_verified","r07_complete"))
        if not int_in(record["phase_b_approved"],0,0):blocked("B10 fase não aprovada")
    elif stage=="B11":
        before,after=record["before"],record["after"]
        exact(before,B11_BEFORE)
        exact(after,B11_AFTER)
        if before["status"]!="HOST_SAVE_SNAPSHOT_BEFORE_RECORDED_SANDBOX_NOT_RUN":
            blocked("B11 snapshot inicial inválido")
        if after["status"] not in ("HOST_WATCHED_FILES_CHANGED_REVIEW_REQUIRED",
                                   "HOST_WATCHED_FILES_UNCHANGED_LIMITED_EVIDENCE"):
            blocked("B11 snapshot final inválido")
        for key in ("monitored_directories_count","monitored_files_before"):
            if not int_in(before[key],0,200000) or after[key]!=before[key]:
                blocked("B11 scope ou baseline diverge")
        if (before["monitored_directories_count"]<1 or
                before["scope_selection_mode"] not in ("explicit","default") or
                after["scope_selection_mode"]!=before["scope_selection_mode"]):
            blocked("B11 sem escopo monitorado válido")
        for item in (before,after):
            v=item["default_scopes_not_monitored"]
            if v is not None and not int_in(v,0,50):
                blocked("B11 escopo padrão inválido")
        if after["default_scopes_not_monitored"]!=before["default_scopes_not_monitored"]:
            blocked("B11 relatórios se referem a escopos diferentes")
        for key in ("monitored_files_after","files_added","files_removed","files_changed"):
            if not int_in(after[key],0,200000):blocked("B11 contagem inválida")
        if after["files_changed"]+after["files_removed"]+after["files_added"]==0:
            if after["watch_unchanged"] is not True or after["status"]!="HOST_WATCHED_FILES_UNCHANGED_LIMITED_EVIDENCE":
                blocked("B11 estado de comparação incoerente")
        else:
            if after["watch_unchanged"] is not False or after["status"]!="HOST_WATCHED_FILES_CHANGED_REVIEW_REQUIRED":
                blocked("B11 alteração de save ocultada")
        if after["monitored_files_after"]!=before["monitored_files_before"]+after["files_added"]-after["files_removed"]:
            blocked("B11 contagem antes/depois incoerente")
        if after["guest_observation_self_reported"] not in ("not_run","launch_failed","launched","rendered_map","save_inside_vm"):
            blocked("B11 observação não reconhecida")
        for obj in (before,after):
            require_false(obj,tuple(k for k in obj if k in (
                "paths_names_and_saves_in_report","r07_complete","windows_sandbox_started",
                "Game_exe_started","host_saves_runtime_isolation_confirmed",
                "guest_vm_execution_independently_verified","complete_host_save_coverage_verified",
                "true_runtime_save_path_in_source_verified","host_saves_globally_isolated_proven",
                "assets_rights_verified","R07_R08_R09_approved","gameplay_approved")))
            if obj["coverage_is_partial"] is not True:blocked("B11 deve afirmar cobertura parcial")
        for field in ("phase_b_approved","phase_c_approved","phase_d_approved"):
            for obj in (before,after):
                if field in obj and not int_in(obj[field],0,0):
                    blocked("B11 fase falsamente aprovada")
    elif stage=="R07":
        if (record["status"] not in (
            "BLOCKED_MISSING_NATIVE_RESERVATION_EVIDENCE",
            "CANDIDATE_READY_FOR_MANUAL_REVIEW_NOT_APPROVED") or
            record["future_regions_required"]!=["KANTO","JOHTO","HOENN"] or
            not int_in(record["future_regions_with_evidence"],0,3) or
            not int_in(record["collisions_count"],0,5000)):
            blocked("R07 estrutura de reservas inválida")
        require_false(record,("r07_complete","may_apply_to_main_game","rights_verified"))
        if record["native_snapshot_present"] is True:
            if record["native_occupied_count"] is None or not int_in(record["native_occupied_count"],1,2000):
                blocked("R07 inventário sem contagem")
            if (not is_sha(record["native_mapinfos_sha256"]) or
                    record["native_mapinfos_sha256"]!=contracts["B09"]["native_baseline_mapinfos_sha256"]):
                blocked("R07 MapInfos não corresponde a B09")
        elif record["native_snapshot_present"] is False:
            if record["native_occupied_count"] is not None or record["native_mapinfos_sha256"] is not None:
                blocked("R07 baseline falsamente declarado")
        else:blocked("R07 status de inventário inválido")
        ready=(record["native_snapshot_present"] is True and
               record["future_regions_with_evidence"]==3 and
               record["collisions_count"]==0)
        if record["candidate_safety_reviewable"] is True:
            if not ready or record["status"]!="CANDIDATE_READY_FOR_MANUAL_REVIEW_NOT_APPROVED":
                blocked("R07 revisão de candidato sem comprovantes")
        elif record["candidate_safety_reviewable"] is False:
            if record["status"]!="BLOCKED_MISSING_NATIVE_RESERVATION_EVIDENCE":
                blocked("R07 divergência de status")
        else:blocked("R07 review flag inválida")
    elif stage=="R08":
        if (record["status"]!="RIGHTS_REVIEW_PENDING" or
            not int_in(record["source_expected_png_count"],14,14) or
            not int_in(record["per_asset_licenses_reviewed_count"],0,14)):
            blocked("R08 documento de direitos inválido")
        require_false(record,("source_asset_rights_verified","physical_maps_approved",
                              "twinleaf_map_bindings_verified","twinleaf_warps_verified",
                              "barry_pbs_compiled","r08_complete","can_install"))
    return {
        "status":"RECEIVED_SANITIZED_REPORT_UNVERIFIED",
        "sanitized_report_sha256":digest(record),
        "independent_physical_review_accepted":False,
        "stage_specific_review_needed":BLOCKERS[stage],
    }


def audit(bundle,contracts,handoff,final_report):
    exact(bundle,{"schema","region","stage","mode","reports"})
    if (bundle["schema"]!=1 or bundle["region"]!="SINNOH" or bundle["stage"]!="L00"
            or bundle["mode"]!="SANITIZED_REPORTS_NOT_INDEPENDENT_PROOF"):
        blocked("L00 envelope inválido")
    reports=bundle["reports"]
    exact(reports,STAGES)
    if (handoff.get("stage")!="G12" or handoff.get("status")!="GITHUB_HANDOFF_ONLY_NATIVE_QA_NOT_STARTED" or
            handoff.get("completed_native_cases")!=0 or handoff.get("total_cases")!=44 or
            handoff.get("game_exe_tested") is not False or handoff.get("joiplay_tested") is not False or
            any(handoff.get("phase_"+x+"_approved")!=0 for x in ("b","c","d")) or
            final_report.get("stage")!="G12" or
            final_report.get("completed_native_cases")!=0 or
            final_report.get("native_cases_total")!=44 or
            final_report.get("can_install_live_game") is not False):
        blocked("G12 native handoff moved without independent signoff")
    if set(contracts)!=set(CONTRACTS):
        blocked("contract set incomplete")
    b09,b10,b11,r07,r08=[contracts[s] for s in STAGES]
    if (b09.get("region")!="SINNOH" or b09.get("stage")!="B09" or
            b09.get("expected_qa_clone_map_count")!=702 or
            b09.get("expected_png_count")!=14 or
            b09.get("native_inventory_sha256")!=b10.get("native_b01_inventory_sha256") or
            b09.get("native_baseline_mapinfos_sha256")!=b10.get("native_mapinfos_sha256") or
            b09.get("native_baseline_tilesets_sha256")!=b10.get("native_tilesets_sha256") or
            b10.get("host_data_and_saves_never_mapped") is not True or
            b10.get("network_disabled") is not True or
            b10.get("clipboard_disabled") is not True or
            b10.get("mapped_clone_read_only") is not True or
            b10.get("mapped_tools_read_only") is not True or
            b10.get("no_logon_command") is not True or
            b11.get("coverage_known_incomplete_until_save_code_audited") is not True or
            r07.get("all_future_reservations_verified") is not False or
            r07.get("r07_complete") is not False or
            r08.get("received_real_source",{}).get("source_rights_verified") is not False or
            r08.get("import_control",{}).get("imports_enabled") is not False):
        blocked("public B09/B10/B11/R07/R08 baseline drift")
    result={}
    for stage in STAGES:
        record=reports[stage]
        if record is None:
            result[stage]={
                "status":"MISSING_REPORT",
                "sanitized_report_sha256":None,
                "independent_physical_review_accepted":False,
                "stage_specific_review_needed":BLOCKERS[stage],
            }
        else:
            result[stage]=check_report(stage,record,contracts,reports)
    # Reports can only record metadata. Receipt hashes are *not* signatures,
    # and a reporter could have created a file without running native QA.
    return {
        "schema":1,"region":"SINNOH","stage":"L00",
        "status":"NO_NATIVE_READINESS_APPROVAL_GITHUB_ONLY",
        "mode":"PUBLIC_CONTRACTS_AND_OPTIONAL_ALLOWLISTED_RECEIPTS",
        "sources":{
            k:{"contract_path":CONTRACTS[k],
               "contract_sha256":digest(contracts[k]),
               **result[k]} for k in STAGES
        },
        "received_reports":sum(reports[k] is not None for k in STAGES),
        "missing_reports":sum(reports[k] is None for k in STAGES),
        "reports_are_self_described_not_authenticated":True,
        "reported_b09_clone_is_not_verified_running_game":True,
        "reported_b10_wsb_is_not_proof_guest_executed":True,
        "b11_watch_unchanged_never_proves_global_save_isolation":True,
        "r07_candidate_reviewable_is_not_allocated_mapids":True,
        "r08_licenses_review_count_is_not_rights_approval":True,
        "needed_for_windows":[
            "B09 physical copy and source SHA independent audit",
            "B10 safe VM configuration plus real guest isolation proof",
            "B11 monitored scope coverage review and save before/after",
            "R07 real future reservations and map collisions",
            "R08 per-asset licensing, 14 native PNGs, Twinleaf maps/warps and Barry PBS",
            "R09 independent reviewed 43 Windows native playtests",
        ],
        "needed_for_android":[
            "authorized Android/JoiPlay package",
            "independent save profile and 1 real device playtest",
        ],
        "native_cases_total":44,"windows_cases":43,"android_cases":1,
        "completed_native_cases":0,"independently_accepted_cases":0,
        "local_gates":{f"L{i:02}":"PENDING" for i in range(1,6)},
        "r07_complete":False,"r08_complete":False,"r09_complete":False,
        "game_exe_tested":False,"joiplay_tested":False,
        "sandbox_run_performed":False,"host_save_isolation_globally_proven":False,
        "may_start_game_in_host":False,"may_start_game_in_vm":False,
        "may_install_live_game":False,"native_approved":False,
        "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
    }


def read_json(root,relative,maxsize=150000):
    f=Path(root)/relative
    # Refuse symlink at every existing ancestor, even if the leaf is safe.
    if any(p.is_symlink() for p in (f,*f.parents) if p.exists()):
        blocked("symbolic link in public report path")
    if not f.is_file() or f.stat().st_size>maxsize:
        blocked("report missing or too large")
    try:
        doc=json.loads(f.read_text(encoding="utf-8-sig"))
    except (OSError,UnicodeError,ValueError):
        blocked("report not valid UTF-8 JSON")
    if type(doc) is not dict:
        blocked("report must be a JSON object")
    return doc


def run(root=ROOT,*,workspace=False):
    root=Path(root)
    source=PRIVATE_REPORT if workspace else TEMPLATE
    bundle=read_json(root,source,maxsize=65536)
    contracts={k:read_json(root,path) for k,path in CONTRACTS.items()}
    handoff=read_json(root,g12.HANDOFF)
    return audit(bundle,contracts,handoff,g12.run(root))


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--workspace-reports",action="store_true",
                   help="read only .blue-work/sinnoh-l00-input/public-reports.json")
    args=p.parse_args(argv)
    try:
        print(json.dumps(run(workspace=args.workspace_reports),
                         indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,KeyError,TypeError,AttributeError,IndexError,UnicodeError):
        print("SINNOH_L00_BLOCKED: invalid sanitized reports or public contracts",
              file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
