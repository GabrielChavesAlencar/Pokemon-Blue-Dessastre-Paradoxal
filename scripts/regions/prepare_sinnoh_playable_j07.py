#!/usr/bin/env python3
"""J07: executable Windows native QA harness for an AUTHORIZED Sinnoh QA copy.

Safe by default. It cannot supply missing maps, permissions, Game.exe or
native gameplay evidence. It binds the G12 43-Windows/1-Android matrix to the
SHA-pinned J06 private copy and records *unreviewed* human observations
outside both the main game and QA game. No personal saves are read or copied.
Only explicit --launch on Windows can call the existing guarded QA launcher.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
for folder in (ROOT, ROOT/"scripts/regions"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from audit_sinnoh_playtest import expected_cases, validate_observation
from prepare_sinnoh_playable_j06 import (
    receipt_checked, validate_review, project_paths, file_digest, regular_file,
    SHA
)
from launch_sinnoh_qa import run as qa_launch

G12 = "data/regions/sinnoh-g12-native-handoff.json"
META = "Sinnoh qa.json"
ENGINE = "Data/blue-sinnoh-qa-engine-check.json"
SESSION = "j07-session.json"
CASE_DIR = "records"
INPUT_DIR = "evidence"
CASE = re.compile(r"[A-Za-z0-9_-]{4,110}\Z")
S_TOKEN = re.compile(r"[0-9a-f]{16}\Z")
QA_TOKEN = re.compile(r"game-sinnoh-qa-[0-9a-f]{12}\Z")
EVIDENCE_SUFFIX = {".png",".jpg",".jpeg",".txt",".log",".json"}
KIND_COUNTS = {
    "starter":3, "barry":12, "save_reload":3, "warp":16,
    "npc":5, "regression":4, "android":1,
}
REGIONS = {"DECADES","KANTO","JOHTO","HOENN"}
EXPECTED_KEYS = {
    "schema","region","stage","mode","qa_name","qa_receipt_sha256",
    "game_exe_sha256","engine_report_sha256","compile_token",
    "g12_catalog_sha256","rights_sha256","reservations_sha256",
    "spec_sha256","overlay_report_sha256","profile",
    "windows_case_ids","android_case_id","native_gameplay_verified",
    "may_publish","saves_accessed","native_cases_executed",
}
RECORD_KEYS = {
    "schema","stage","case_id","status","session_sha256",
    "observation_sha256","evidence_sha256","evidence_name",
    "verified_pass_claim_only","independent_native_proof",
}

def blocked(msg: str):
    raise ValueError("SINNOH_J07_BLOCKED:"+msg)

def sha_obj(obj) -> str:
    return hashlib.sha256(json.dumps(
        obj,sort_keys=True,ensure_ascii=True,separators=(",",":")
    ).encode("ascii")).hexdigest()

def read_json(path: Path, limit: int = 5_000_000):
    path=regular_file(path,max_bytes=limit)
    raw=path.read_bytes()
    try:
        value=json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError,json.JSONDecodeError):
        blocked("INVALID_JSON_INPUT")
    if type(value) is not dict:
        blocked("JSON_OBJECT_REQUIRED")
    return value, hashlib.sha256(raw).hexdigest()

def require_no_links(path: Path):
    if any(p.is_symlink() for p in (path,*path.parents)):
        blocked("SYMLINK_OR_JUNCTION_DENIED")

def approved_catalog(project: Path) -> tuple[list[dict],str]:
    source=project/G12
    g12,source_sha=read_json(source,max_bytes=1_000_000)
    if (g12.get("region")!="SINNOH" or g12.get("stage")!="G12"
            or g12.get("total_cases")!=44
            or g12.get("windows_cases")!=43
            or g12.get("android_cases")!=1
            or g12.get("category_counts")!=KIND_COUNTS
            or g12.get("completed_native_cases")!=0
            or g12.get("game_exe_tested") is not False
            or g12.get("joiplay_tested") is not False
            or g12.get("can_install_live_game") is not False):
        blocked("G12_NATIVE_GATE_NOT_PENDING")
    rows=g12.get("cases")
    if type(rows) is not list or len(rows)!=44:
        blocked("G12_CASES_MISSING")
    names=set()
    counts=Counter()
    for row in rows:
        if (type(row) is not dict or type(row.get("id")) is not str
                or not CASE.fullmatch(row["id"]) or row["id"] in names
                or row.get("kind") not in KIND_COUNTS
                or row.get("native_status")!="pending"
                or row.get("evidence") is not None
                or row.get("observation") is not None
                or row.get("platform") not in ("windows","android")
                or row["platform"]!=("android" if row["kind"]=="android" else "windows")):
            blocked("G12_CASE_NOT_PENDING_OR_DUPLICATE")
        names.add(row["id"]);counts[row["kind"]]+=1
        if row["kind"]=="barry":
            if (row.get("expected_scaling_percent") !=
                    (70 if row.get("mode")=="normal" else 90)
                    or row.get("outcome") not in ("win","loss")):
                blocked("BARRY_DYNAMIC_LEVEL_OR_OUTCOME_INVALID")
        if row["kind"]=="regression" and row.get("region") not in REGIONS:
            blocked("REGIONAL_REGRESSION_MISSING")
    if dict(counts)!=KIND_COUNTS:
        blocked("G12_CASE_COVERAGE_INVALID")
    return rows,source_sha

def inspect_private_qa(project: Path, qa: Path, receipt_sha: str, *,
                       overlay: Path, spec: Path, rights: Path,
                       reservations: Path) -> dict:
    project,main,work=project_paths(project)
    qa=Path(qa).absolute()
    if (qa.parent!=work or not QA_TOKEN.fullmatch(qa.name)
            or qa==main or qa.is_symlink()):
        blocked("QA_FOLDER_MUST_BE_J06_PRIVATE_COPY")
    # J06 checks exact original executable and MapInfos SHA; QA namespace,
    # PBS/Sinnoh files, original inventory and compiled/engine report.
    checked=receipt_checked(project,qa,receipt_sha)
    receipt,state=checked["receipt"],checked["verification"]
    if (not state.get("compiled_marker_present")
            or not state.get("engine_structural_report_consistent")
            or not state.get("ready_to_launch_for_manual_testing")
            or state.get("save_namespace_verified") is not True
            or state.get("foreign_save_inherited") is not False
            or state.get("playable_approved") is not False):
        blocked("NATIVE_ENGINE_COMPILE_AND_SAVE_ISOLATION_REQUIRED")
    private=validate_review(project,overlay,spec,rights,reservations)
    for key in ("source_game_exe_sha256","source_mapinfos_sha256",
                "overlay_report_sha256","rights_sha256",
                "reservations_sha256","spec_sha256"):
        if receipt.get(key)!=private.get(key):
            blocked("SOURCE_OR_RIGHTS_CHANGED_SINCE_J06")
    meta,meta_sha=read_json(qa/META,max_bytes=8_000_000)
    engine,engine_sha=read_json(qa/ENGINE,max_bytes=8_000_000)
    if (meta.get("region")!="SINNOH"
            or meta.get("runtime_playable") is not False
            or meta.get("intro_maps")!=9 or meta.get("event_count")!=24
            or meta.get("warps")!=16 or meta.get("barry_versions")!=[0,1,2]
            or sorted(meta.get("starter_balls",[]))!=["CHIMCHAR","PIPLUP","TURTWIG"]
            or meta.get("profile")!=receipt.get("save_profile")
            or engine.get("compile_token")!=meta.get("compile_token")
            or engine.get("maps_inspected")!=9
            or engine.get("warps_inspected")!=16
            or engine.get("events_inspected")!=24
            or engine.get("gameplay_approved") is not False):
        blocked("NATIVE_STATIC_PROBE_CONTRADICTS_QA_COPY")
    cases,g12_sha=approved_catalog(project)
    dynamic=expected_cases(meta)
    if set(c["id"] for c in cases)!=set(c["id"] for c in dynamic):
        blocked("G12_CASE_IDS_MISMATCH_WITH_REAL_QA_EVENTS")
    if Counter(c["kind"] for c in dynamic)!=Counter(KIND_COUNTS):
        blocked("G12_CASE_TYPES_MISMATCH")
    for source_case in cases:
        ident=source_case["id"]
        derived=next(x for x in dynamic if x["id"]==ident)
        if source_case["kind"]!=derived["kind"]:
            blocked("G12_CASE_KIND_CHANGED")
        if source_case["kind"]=="warp" and (source_case["to_symbol"] not in
               {m["symbol"] for m in meta["event_contract"]}):
            blocked("G12_WARP_DESTINATION_ABSENT")
        if source_case["kind"]=="barry" and (
                source_case.get("expected_rival")!=derived["opponent"] or
                source_case.get("mode")!=derived["mode"] or
                source_case.get("outcome")!=derived["outcome"]):
            blocked("G12_BARRY_VARIANT_NOT_COMPATIBLE")
    return {
        "qa":qa,"receipt":receipt,"state":state,"meta":meta,
        "engine_report_sha256":engine_sha,"cases":cases,
        "derived":{v["id"]:v for v in dynamic},
        "g12_sha":g12_sha,"receipt_sha":receipt_sha,
        "source_rights_declared_locally":True,
    }

def session_path(project: Path, qa: Path, sid: str) -> Path:
    project,main,work=project_paths(project)
    qa=Path(qa).absolute()
    if qa.parent!=work or not QA_TOKEN.fullmatch(qa.name):
        blocked("QA_LOCATION_INVALID")
    if type(sid) is not str or not S_TOKEN.fullmatch(sid):
        blocked("SESSION_ID_INVALID")
    parent=work/"sinnoh-j07-sessions"
    require_no_links(parent)
    return parent/(qa.name+"-"+sid)

def _manifest(preflight: dict) -> dict:
    receipt=preflight["receipt"]
    cases=preflight["cases"]
    return {
        "schema":1,"region":"SINNOH","stage":"J07",
        "mode":"PRIVATE_WINDOWS_QA_SESSION_NOT_NATIVE_APPROVAL",
        "qa_name":preflight["qa"].name,
        "qa_receipt_sha256":preflight["receipt_sha"],
        "game_exe_sha256":receipt["source_game_exe_sha256"],
        "engine_report_sha256":preflight["engine_report_sha256"],
        "compile_token":preflight["meta"]["compile_token"],
        "g12_catalog_sha256":preflight["g12_sha"],
        "rights_sha256":receipt["rights_sha256"],
        "reservations_sha256":receipt["reservations_sha256"],
        "spec_sha256":receipt["spec_sha256"],
        "overlay_report_sha256":receipt["overlay_report_sha256"],
        "profile":receipt["save_profile"],
        "windows_case_ids":[r["id"] for r in cases if r["platform"]=="windows"],
        "android_case_id":next(r["id"] for r in cases if r["platform"]=="android"),
        "native_gameplay_verified":False,
        "may_publish":False,
        "saves_accessed":False,
        "native_cases_executed":0,
    }

def create_session(project: Path, preflight: dict, *, sid: str|None=None) -> dict:
    sid=sid or secrets.token_hex(8)
    dest=session_path(project,preflight["qa"],sid)
    if dest.exists() or dest.is_symlink():
        blocked("SESSION_ALREADY_EXISTS_NEVER_OVERWRITE")
    parent=dest.parent
    parent.mkdir(parents=True,exist_ok=True)
    require_no_links(parent)
    temp=Path(tempfile.mkdtemp(prefix=".j07-pending-",dir=parent))
    try:
        manifest=_manifest(preflight)
        if set(manifest)!=EXPECTED_KEYS or len(manifest["windows_case_ids"])!=43:
            blocked("J07_MANIFEST_INVALID")
        raw=(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode()
        (temp/SESSION).write_bytes(raw)
        (temp/CASE_DIR).mkdir()
        (temp/INPUT_DIR).mkdir()
        if dest.exists() or dest.is_symlink():
            blocked("SESSION_CREATED_IN_PARALLEL")
        temp.rename(dest)
    except BaseException:
        if temp.exists(): shutil.rmtree(temp)
        raise
    return {
        "created":True,"session_directory":str(dest),
        "session_sha256":file_digest(dest/SESSION),
        "windows_cases_pending":43,"android_cases_reserved_for_J08":1,
        "native_cases_independently_verified":0,"may_publish":False,
    }

def check_session(project: Path, preflight: dict, session: Path,
                  session_sha: str) -> tuple[Path,dict]:
    session=Path(session).absolute()
    expected_parent=session_path(project,preflight["qa"],"0"*16).parent
    if (session.parent!=expected_parent
            or not session.name.startswith(preflight["qa"].name+"-")
            or not S_TOKEN.fullmatch(session.name[-16:])
            or session.is_symlink() or not session.is_dir()):
        blocked("SESSION_OUTSIDE_ISOLATED_WORKSPACE")
    require_no_links(session)
    if type(session_sha) is not str or not SHA.fullmatch(session_sha):
        blocked("SESSION_SHA_REQUIRED")
    path=regular_file(session/SESSION,max_bytes=400_000)
    if file_digest(path)!=session_sha:
        blocked("SESSION_MANIFEST_HASH_MISMATCH")
    manifest=json.loads(path.read_text("utf-8"))
    if type(manifest) is not dict or manifest!=_manifest(preflight):
        blocked("SESSION_BOUND_TO_DIFFERENT_QA_OR_CASE_MATRIX")
    for dirname in (INPUT_DIR,CASE_DIR):
        p=session/dirname
        if p.is_symlink() or not p.is_dir():
            blocked("SESSION_SUBDIRECTORY_MISSING")
    return session,manifest

def evidence_path(session: Path, path: Path, suffixes: set[str]) -> Path:
    path=Path(path).absolute()
    if (path.parent!=session/INPUT_DIR or path.suffix.lower() not in suffixes
            or not path.name.isascii() or len(path.name)>120
            or not CASE.fullmatch(path.stem)):
        blocked("EVIDENCE_MUST_BE_IN_PRIVATE_SESSION_EVIDENCE_FOLDER")
    require_no_links(path)
    if not path.is_file() or not 0<path.stat().st_size<=20_000_000:
        blocked("EVIDENCE_NOT_REGULAR_OR_TOO_LARGE")
    return path

def record_case(project: Path, preflight: dict, session: Path,
                session_sha: str, case_id: str, observed_file: Path,
                observed_sha: str, attachment: Path, attachment_sha: str) -> dict:
    session,_=check_session(project,preflight,session,session_sha)
    if type(case_id) is not str or not CASE.fullmatch(case_id):
        blocked("CASE_ID_INVALID")
    dynamic=preflight["derived"].get(case_id)
    if not dynamic or dynamic["kind"]=="android":
        blocked("ONLY_43_WINDOWS_CASES_IN_J07")
    if any(type(s) is not str or not SHA.fullmatch(s)
           for s in (observed_sha,attachment_sha)):
        blocked("EVIDENCE_SHA_REQUIRED")
    observed=evidence_path(session,observed_file,{".json"})
    attach=evidence_path(session,attachment,EVIDENCE_SUFFIX-{".json"})
    if file_digest(observed)!=observed_sha or file_digest(attach)!=attachment_sha:
        blocked("EVIDENCE_CHANGED_SINCE_SHA_ATTESTATION")
    report,_=read_json(observed,max_bytes=1_000_000)
    # Existing native QA schema tests Barry level 70/90, team size, victory,
    # warp arrivals, singleton starters, save reload and four regions.
    validate_observation(dynamic,report)
    record={
        "schema":1,"stage":"J07","case_id":case_id,
        "status":"EVIDENCE_SUBMITTED_NEEDS_INDEPENDENT_NATIVE_REVIEW",
        "session_sha256":session_sha,
        "observation_sha256":observed_sha,
        "evidence_sha256":attachment_sha,
        "evidence_name":attach.name,
        "verified_pass_claim_only":True,
        "independent_native_proof":False,
    }
    file=session/CASE_DIR/(case_id+".json")
    if file.is_symlink() or file.exists():
        blocked("CASE_ALREADY_RECORDED_NEVER_OVERWRITE")
    file.write_text(json.dumps(record,ensure_ascii=False,sort_keys=True,indent=2)+"\n",encoding="utf-8",errors="strict")
    return {"case":case_id,"recorded":True,
            "status":record["status"],"native_cases_verified":0}

def audit_session(project: Path, preflight: dict, session: Path,
                  session_sha: str) -> dict:
    session,manifest=check_session(project,preflight,session,session_sha)
    candidates={c["id"] for c in preflight["cases"] if c["platform"]=="windows"}
    found=0
    kinds=Counter()
    for file in (session/CASE_DIR).iterdir():
        if file.is_symlink() or not file.is_file() or file.suffix!=".json":
            blocked("UNEXPECTED_CASE_RECORD")
        ident=file.stem
        if ident not in candidates:
            blocked("UNEXPECTED_OR_ANDROID_CASE_ID")
        row,_=read_json(file,max_bytes=40_000)
        if (set(row)!=RECORD_KEYS or row.get("schema")!=1
                or row.get("stage")!="J07" or row.get("case_id")!=ident
                or row.get("session_sha256")!=session_sha
                or row.get("status")!="EVIDENCE_SUBMITTED_NEEDS_INDEPENDENT_NATIVE_REVIEW"
                or row.get("verified_pass_claim_only") is not True
                or row.get("independent_native_proof") is not False
                or not isinstance(row.get("evidence_name"),str)):
            blocked("CASE_RECORD_TAMPERED")
        observed=session/INPUT_DIR/(ident+".json")
        # Preserve arbitrary evidence name but ensure safe, local and pinned.
        attachment=session/INPUT_DIR/row["evidence_name"]
        observed=evidence_path(session,observed,{".json"})
        attachment=evidence_path(session,attachment,EVIDENCE_SUFFIX-{".json"})
        if file_digest(observed)!=row.get("observation_sha256") or \
                file_digest(attachment)!=row.get("evidence_sha256"):
            blocked("RECORDED_EVIDENCE_CHANGED")
        report,_=read_json(observed,max_bytes=1_000_000)
        validate_observation(preflight["derived"][ident],report)
        kinds[preflight["derived"][ident]["kind"]]+=1
        found+=1
    if found>43:
        blocked("MORE_THAN_43_WINDOWS_CASES")
    return {
        "schema":1,"region":"SINNOH","stage":"J07",
        "status":"HUMAN_EVIDENCE_PENDING_INDEPENDENT_NATIVE_REVIEW",
        "session_sha256":session_sha,
        "qa_source_hash_validated":True,
        "j06_save_namespace_verified":True,
        "j06_engine_structural_probe_verified":True,
        "g12_windows_cases":43,"g12_android_cases_reserved":1,
        "windows_evidence_submitted_unreviewed":found,
        "by_kind_evidence_submitted":dict(sorted(kinds.items())),
        "native_windows_cases_independently_verified":0,
        "native_android_cases_independently_verified":0,
        "gameplay_approved":False,"barry_ready_marker_created":False,
        "main_game_or_user_saves_modified":False,
        "can_publish_or_merge_qa_into_main_game":False,
    }

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project",type=Path,default=ROOT)
    p.add_argument("--qa",type=Path,required=True)
    p.add_argument("--receipt-sha",required=True)
    p.add_argument("--overlay",type=Path,required=True)
    p.add_argument("--spec",type=Path,required=True)
    p.add_argument("--rights",type=Path,required=True)
    p.add_argument("--reservations",type=Path,required=True)
    modes=p.add_mutually_exclusive_group()
    modes.add_argument("--init",action="store_true")
    modes.add_argument("--launch",action="store_true")
    modes.add_argument("--audit",action="store_true")
    modes.add_argument("--record",metavar="CASE_ID")
    p.add_argument("--session",type=Path)
    p.add_argument("--session-sha")
    p.add_argument("--observed",type=Path)
    p.add_argument("--observed-sha")
    p.add_argument("--attachment",type=Path)
    p.add_argument("--attachment-sha")
    args=p.parse_args(argv)
    try:
        if (args.init or args.launch) and (sys.platform!="win32" or os.name!="nt"):
            blocked("WINDOWS_ONLY_FOR_PRIVATE_QA_INIT_OR_LAUNCH")
        preflight=inspect_private_qa(args.project,args.qa,args.receipt_sha,
            overlay=args.overlay,spec=args.spec,rights=args.rights,
            reservations=args.reservations)
        if args.init:
            if any((args.session,args.session_sha,args.observed,args.attachment,
                    args.record,args.audit)):
                blocked("INIT_TAKES_NO_RECORD_ARGS")
            out=create_session(args.project,preflight)
        elif args.launch:
            if (not args.session or not args.session_sha or args.record or
                    args.observed or args.attachment):
                blocked("LAUNCH_REQUIRES_SIGNED_SESSION")
            audit_session(args.project,preflight,args.session,args.session_sha)
            out=qa_launch(preflight["qa"],project=args.project,mode="launch")
            out["native_qa_not_automatically_approved"]=True
        elif args.audit:
            if not args.session or not args.session_sha or args.record:
                blocked("AUDIT_REQUIRES_SESSION")
            out=audit_session(args.project,preflight,args.session,args.session_sha)
        elif args.record:
            if not all((args.session,args.session_sha,args.observed,
                        args.observed_sha,args.attachment,args.attachment_sha)):
                blocked("RECORD_REQUIRES_ALL_EVIDENCE_HASHES")
            out=record_case(args.project,preflight,args.session,
                args.session_sha,args.record,args.observed,args.observed_sha,
                args.attachment,args.attachment_sha)
        else:
            out={
                "schema":1,"stage":"J07","status":"J06_QA_PROBE_AND_G12_READY_FOR_HUMAN_QA",
                "windows_cases_pending":43,"android_cases_pending":1,
                "main_game_modified":False,
                "native_gameplay_approved":False,
                "engine_structure_checked":True,
                "private_save_namespace_checked":True,
            }
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("SINNOH_J07_BLOQUEADO:"+str(exc),file=sys.stderr)
        return 2
    print(json.dumps(out,ensure_ascii=False,indent=2,default=str))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
