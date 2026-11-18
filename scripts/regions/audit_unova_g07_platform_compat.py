#!/usr/bin/env python3
"""G07.4: fail-closed Windows/Android compatibility *contracts* and offline demos.

This module NEVER imports or invokes Blue-Story, Windows installer, Termux
updater or JoiPlay. Its only payloads are G07.2 synthetic documentation bytes.
G07.3 'commit' returns a new in-memory dictionary, not a real install.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any, Mapping

import audit_unova_g07_incremental_manifest as g72
import audit_unova_g07_transaction as g73

ROOT = Path(__file__).resolve().parents[2]
FILE = "data/regions/unova-g07-platform-compatibility-contract.json"
PLATFORMS = ("windows", "android")
SOURCE_PATHS = {
    "schema":g72.SCHEMA_PATH,
    "package_contract":g72.CONTRACT_PATH,
    "package_validator":"scripts/regions/audit_unova_g07_incremental_manifest.py",
    "transaction_contract":g73.CONTRACT_PATH,
    "transaction_simulator":"scripts/regions/audit_unova_g07_transaction.py",
    "windows_bootstrap":"scripts/windows/Bootstrap.cs",
    "windows_installer":"scripts/install_game.py",
    "android_updater":"scripts/android/update_client.py",
    "native_owner_audit":"scripts/regions/audit_unova_a12_ownership.py",
    "region_registry":g72.REGISTRY,
    "progress_board":g72.TRACKER,
}
WINDOWS_PROTECTED=["game","saves","bluehub",".git",".blue-work",".blue-backups","tools"]
ANDROID_PROTECTED=["save","saves","backup","__pycache__"]
WIN_EVIDENCE={
 "source_zip_expected_sha256":None,"game_exe_runtime_qa":None,
 "region_mapid_ownership":None,"redistribution_rights":None,
 "atomic_rollback_qa":None,
}
ANDROID_EVIDENCE={
 "unova_release_channel":None,"verified_release_manifest":None,
 "revision_ancestry_qa":None,"joi_play_runtime_qa":None,
 "region_mapid_ownership":None,"redistribution_rights":None,
 "atomic_rollback_qa":None,
}
EVIDENCE={
 "mapids":None,"source_rights":None,"windows_game_exe_qa":None,
 "android_joiplay_qa":None,"unova_release_signature":None,
}
POLICY={
 "exact_channels_required":True,"source_package_hashes_required":True,
 "manifest_origin_verified":True,"rights_declaration_required":True,
 "sha256_not_signature":True,"version_chain_currently_baseline_only":True,
 "reject_cross_channel":True,"reject_downgrade":True,
 "reject_native_map_payload":True,"reject_real_user_paths":True,
 "reject_unverified_rights":True,"reject_unverified_runtime":True,
 "reject_real_source_download_as_unova_patch":True,
 "require_g072_validation":True,"require_g073_cas_preview":True,
 "safe_fallback_no_action":True,"real_backup_never_created":True,
 "in_memory_rollback_only":True,"never_write_saves_or_game_exe":True,
 "never_download_or_extract":True,"never_invoke_installers":True,
 "never_mark_unova_playable":True,
 "windows_unova_adapter_installed":False,
 "android_unova_channel_published":False,
 "joiplay_unova_runtime_tested":False,
}
WIN = {
 "client":"Blue-Story","runtime_file":"scripts/windows/Bootstrap.cs",
 "platform_id":"WINDOWS_BLUE_STORY",
 "existing_update_channel":"github-main-source-zip",
 "existing_source_download_digest_pinned":False,
 "existing_source_protected_top_level":WINDOWS_PROTECTED,
 "existing_source_backup_behavior":"copies-overwritten-source-files-without-certified-atomic-rollback",
 "accepted_mode":"documentation_fixture_simulation_only",
 "native_patch_supported":False,"required_native_evidence":WIN_EVIDENCE,
}
ANDROID={
 "client":"Termux Python / JoiPlay","runtime_file":"scripts/android/update_client.py",
 "platform_id":"ANDROID_JOIPLAY",
 "existing_update_channels":["decades","kanto","multiregion"],
 "existing_source_download_digest_pinned":None,
 "existing_source_protected_top_level":ANDROID_PROTECTED,
 "existing_source_backup_behavior":"incremental-patch-without-backup-resumable-not-atomic",
 "accepted_mode":"documentation_fixture_simulation_only",
 "native_patch_supported":False,"required_native_evidence":ANDROID_EVIDENCE,
}
ROOT_KEYS={
 "schema_version","phase","region","campaign","status","sources",
 "permitted_fixture_channel","permitted_fixture_root","platforms","policy",
 "protected_resources","generated_artifacts_allowed","native_evidence",
 "native_technical_completed","native_playable_completed",
 "can_install","can_release","save_modified","notes",
}
PROTECTED_RESOURCES=[
 "Game.exe","Data/Map*.rxdata","Data/MapInfos.rxdata","saves",
 "save","JoiPlay save profile","regional checkpoints","regional key items",
 "regional HMs","Boxes","gameplay progression",
]
REQUEST_KEYS={
 "platform_id","mode","channel","package_id","package_version",
 "package_sha256","source_manifest_sha256","source_revision",
 "target_revision","requested_paths","expected_generation",
 "expected_snapshot_sha256","rights_status","redistribution_approved",
 "native_install_requested","download_requested","save_write_requested",
 "game_exe_write_requested","runtime_qa","source_archive_sha256",
 "approved_native_mapids","unova_release_channel","dry_run_only",
}
NATIVE_FLAGS=("native_install_requested","download_requested",
              "save_write_requested","game_exe_write_requested")

SOURCE_SIGNATURES={
 "windows_bootstrap":(
    "static string Hash(string path)",
    "static void Download(string url,string target,string expected)",
    "internal static string SafePath(string folder,string relative)",
    "static bool Protected(string relative)",
    'return top=="game" || top=="saves"',
    'Download("https://codeload.github.com/"+Repo+"/zip/"+revision,zip,null)',
    'string backup=Path.Combine(Root,".blue-backups"',
    "File.Copy(path,dest,true)",
 ),
 "windows_installer":("def install(project,game,hub_only=False", "scripts/regions/auto_integrate_johto.py"),
 "android_updater":(
    'CHANNELS = {',
    '"decades": ("Blue-Android-JoiPlay.zip"',
    '"kanto": ("Blue-Android-Kanto-Piloto.zip"',
    '"multiregion": ("Blue-Android-Decades-Kanto-Hoenn.zip"',
    'ALLOWED_ROOTS = {"Audio", "Graphics", "Fonts", "PBS", "Plugins", "Data"}',
    "def safe_path(name):",
    'if name in FORBIDDEN or len(path.parts) < 2',
    "def verify_forward_revision(installed_revision, candidate_revision):",
    "def compatible_patch(release, installed, manifest):",
    'if digest.hexdigest() != meta["sha256"]:',
    '"""Install only the changed files. No backup and safely resumable."""',
    'return len(todo), len(removed), None  # No backup directory is ever created.',
 ),
 "native_owner_audit":("def audit_installer_sources(project):","parsed, not imported or executed"),
}
def deny(reason:str)->None:
    raise ValueError("UNOVA_G07_4_BLOCKED: "+reason)

def audit_contract(root:Path=ROOT)->dict:
    g72.validate_catalog(root)
    g73.audit_contract(root)
    doc=g72.j(root,FILE)
    g72.strict(doc,ROOT_KEYS,"G07.4 contract")
    expected={
        "schema_version":1,"phase":"G07.4","region":"UNOVA","campaign":"WHITE_BW",
        "status":"PLANNED_PLATFORM_COMPATIBILITY_CONTRACTS_ONLY",
        "sources":SOURCE_PATHS,
        "permitted_fixture_channel":g72.CHANNEL,
        "permitted_fixture_root":g72.PREFIX,
        "platforms":{"windows":WIN,"android":ANDROID},
        "policy":POLICY,
        "protected_resources":PROTECTED_RESOURCES,
        "generated_artifacts_allowed":["reports emitted to stdout only"],
        "native_evidence":EVIDENCE,
        "native_technical_completed":0,"native_playable_completed":0,
        "can_install":False,"can_release":False,"save_modified":False,
    }
    for key,val in expected.items():
        if doc[key]!=val or type(doc[key]) is not type(val):
            deny("platform contract/provenance/flags drift: "+key)
    if not isinstance(doc["notes"],list) or len(doc["notes"])<6 or any(
        type(x) is not str or not x.strip() for x in doc["notes"]
    ):
        deny("native safety limitations removed")
    for key,tokens in SOURCE_SIGNATURES.items():
        source=g72.body(root,SOURCE_PATHS[key])
        if any(token not in source for token in tokens):
            deny("native platform source changed; re-audit first: "+key)
    board=g72.j(root,g72.TRACKER)
    g07=next((grp for grp in board.get("groups",[]) if grp.get("id")=="G07"),{})
    if (not any(t.get("id")=="G07.3" and t.get("status")=="done" for t in g07.get("tasks",[]))
        or not any(t.get("id")=="G07.4" and t.get("status") in ("pending","done")
                   for t in g07.get("tasks",[]))):
        deny("required G07.3 completed / G07.4 pending status missing")
    return {
        "phase":"G07.4","status":"SOURCE_AUDIT_PASSED_OFFLINE_ONLY",
        "platforms":list(PLATFORMS),"native_installers_modified":False,
        "windows_native_compatible":False,"android_native_compatible":False,
        "joiplay_runtime_tested":False,"source_zip_sha256_pinned":False,
        "native_saves_modified":False,"can_install":False,
        "native_technical_completed":0,"native_playable_completed":0,
    }

def fixture_request(platform:str, package:dict, snapshot:dict)->dict:
    if platform not in PLATFORMS:deny("unknown platform profile")
    info=WIN if platform=="windows" else ANDROID
    return {
        "platform_id":info["platform_id"],
        "mode":"documentation_fixture_simulation_only",
        "channel":g72.CHANNEL,
        "package_id":package["package_id"],
        "package_version":package["package_version"],
        "package_sha256":package["package_sha256"],
        "source_manifest_sha256":package["source"]["manifest_sha256"],
        "source_revision":package["source"]["origin_revision"],
        "target_revision":package["source"]["target_revision"],
        "requested_paths":[row["path"] for row in package["files"]],
        "expected_generation":snapshot["generation"],
        "expected_snapshot_sha256":g73.state_etag(snapshot),
        "rights_status":g72.RIGHTS["status"],
        "redistribution_approved":False,
        "native_install_requested":False,"download_requested":False,
        "save_write_requested":False,"game_exe_write_requested":False,
        "runtime_qa":None,"source_archive_sha256":None,
        "approved_native_mapids":None,"unova_release_channel":None,
        "dry_run_only":True,
    }

def validate_request(req:Any,platform:str,package:dict,snapshot:dict)->dict:
    if platform not in PLATFORMS:deny("platform not in allowlist")
    g72.strict(req,REQUEST_KEYS,"platform compatibility request")
    expected=fixture_request(platform,package,snapshot)
    for field,val in expected.items():
        if req.get(field)!=val or type(req.get(field)) is not type(val):
            deny("platform request mismatch or unsafe native claim: "+field)
    if any(req[x] for x in NATIVE_FLAGS):
        deny("native/write/download requested")
    if (req["runtime_qa"] is not None or req["approved_native_mapids"] is not None
        or req["unova_release_channel"] is not None
        or req["source_archive_sha256"] is not None):
        deny("unsupported real runtime proofs or signed release claim")
    for name in req["requested_paths"]:
        if not g72.path_ok(name) or name==g72.SOURCE_MANIFEST:
            deny("non-documentation path in requested patch")
    return {"platform":platform,"mode":req["mode"],
            "windows_native_compatible":False,"android_native_compatible":False,
            "supported_as_native_release":False,
            "allow_real_download":False,"allow_real_write":False}

def preview(platform:str,request:dict,package:dict,origin_manifest:bytes,
            old_files:Mapping[str,bytes],new_files:Mapping[str,bytes],
            snapshot:dict, *,fail_at:str|None=None,
            observed_after_staging:dict|None=None,
            observed_before_publish:dict|None=None)->dict:
    # Both G07.2 byte-level and G07.3 state-level checks run for every profile.
    compat=validate_request(request,platform,package,snapshot)
    g72.validate_package(package,origin_manifest,old_files,new_files)
    result=g73.transact(
        snapshot,package,origin_manifest,old_files,new_files,
        expected_generation=request["expected_generation"],
        expected_snapshot_sha256=request["expected_snapshot_sha256"],
        fail_at=fail_at,observed_after_staging=observed_after_staging,
        observed_before_publish=observed_before_publish,
    )
    return {
        **compat,
        "status":"PLATFORM_DOCS_PREVIEW_NOT_INSTALLABLE"
                 if result["status"]=="SIMULATED_ATOMIC_COMMIT_NOT_INSTALLED"
                 else "PLATFORM_NOOP_"+result["status"],
        "transaction_status":result["status"],
        "state":result["state"],
        "trace":result["trace"],
        "backup_manifest":result["backup_manifest"],
        "native_files_written":0,"bytes_written":0,
        "saves_modified":False,"game_exe_modified":False,
        "joiplay_invoked":False,"blue_story_invoked":False,
        "install_allowed":False,"release_allowed":False,
        "fallback":"KEEP_EXISTING_INSTALLATION_UNCHANGED",
        "simulated_in_memory_only":True,
    }

def demo(root:Path=ROOT)->dict:
    audit_contract(root)
    pkg,manifest,old,new=g73.multi_file_fixture()
    baseline=g73.base_fixture(pkg,manifest,old)
    report={}
    for platform in PLATFORMS:
        request=fixture_request(platform,pkg,baseline)
        result=preview(platform,request,pkg,manifest,old,new,baseline)
        rollback=preview(platform,request,pkg,manifest,old,new,baseline,
                         fail_at="after_first_candidate_write")
        conflict=copy.deepcopy(baseline)
        conflict["protected"]["saves"]["FIXTURE_SAVES_LEDGER"]="FIXTURE_EXTERNAL_CHANGE"
        denied=preview(platform,request,pkg,manifest,old,new,baseline,
                       observed_before_publish=conflict)
        if (result["transaction_status"]!="SIMULATED_ATOMIC_COMMIT_NOT_INSTALLED"
            or rollback["state"]!=baseline or denied["state"]!=baseline
            or result["state"]["protected"]!=baseline["protected"]):
            deny("platform dry-run/rollback did not preserve synthetic state")
        report[platform]={
            "dry_run":result["status"],
            "rollback":rollback["transaction_status"],
            "stale_save":denied["transaction_status"],
            "files_simulated":len(new),"native_files_written":0,
            "safe_fallback":result["fallback"],"can_install":False,
        }
    return {"phase":"G07.4","status":"PLATFORM_CONTRACTS_SIMULATED_ONLY",
            "platforms":report,"source_contracts":["G07.2","G07.3"],
            "native_files_written":0,"saves_modified":False,
            "unova_playable":False,"can_install":False}

def main(argv:list[str]|None=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    g=p.add_mutually_exclusive_group(required=True)
    g.add_argument("--check",action="store_true")
    g.add_argument("--simulate-demo",action="store_true")
    args=p.parse_args(argv)
    try:
        report=audit_contract() if args.check else demo()
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except (ValueError,OSError,TypeError,KeyError,IndexError,RecursionError) as exc:
        print("UNOVA_G07_4_BLOCKED: "+str(exc)[:300])
        return 2
if __name__=="__main__":raise SystemExit(main())
