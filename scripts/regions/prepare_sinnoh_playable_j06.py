#!/usr/bin/env python3
"""J06: guarded Windows launcher + install/rollback for a PRIVATE Sinnoh QA copy.

J01–J05 source engineering is NOT native approval. The user's private 9-map
overlay, rights and MapID review receipts, game executable and PBS must be
present and hash bound before ANY copy. --plan is read-only on every platform;
installation and execution are Windows-only, and never target game/ or saves.

The existing install_sinnoh_qa_copy and launch_sinnoh_qa own native isolation
and runtime checks; J06 wraps them without bypassing a single failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "scripts/regions"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from install_sinnoh_qa_copy import (prepare, install, verify, load_overlay,
                                    QA_META, BARRY_READY)
from launch_sinnoh_qa import run as launch_native
from prepare_sinnoh_pilot_bundle import native_map_ids
from sinnoh_save_isolation import validate_namespace

SHA = re.compile(r"[0-9a-f]{64}\Z")
TOKEN = re.compile(r"[0-9a-f]{12}\Z")
REL = re.compile(r"[A-Za-z0-9_ .()/-]{1,240}\Z")
RECEIPT = "J06_PRIVATE_QA_RECEIPT.json"
RIGHT_KEYS = {"schema","region","stage","mode","reviewed_locally",
              "redistribution_authorized","overlay_report_sha256",
              "source_game_exe_sha256","source_mapinfos_sha256","spec_sha256",
              "reviewer_reference","files"}
RESERVE_KEYS = {"schema","region","stage","mode","reviewed_locally",
                "r07_global_reservations_approved","source_mapinfos_sha256",
                "candidate_map_ids","protected_map_ids","reviewer_reference"}
FILE_REVIEW = {"sha256","basis","permission_evidence","private_qa_permitted"}
ALLOWED_BASIS = {"OWNED_ORIGINAL","EXPLICIT_PERMISSION","REUSABLE_LICENSE"}
RECEIPT_KEYS = {"schema","region","stage","mode","qa_folder",
                "source_game_exe_sha256","source_mapinfos_sha256",
                "overlay_report_sha256","rights_sha256","reservations_sha256",
                "spec_sha256","save_profile","files_sha256",
                "main_game_modified","saves_read_or_modified",
                "game_exe_executed","native_gameplay_verified","can_publish"}

def fail(reason: str):
    raise ValueError("SINNOH_J06_BLOCKED:" + reason)

def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()

def file_digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024*1024), b""):
            h.update(part)
    return h.hexdigest()

def regular_file(path: Path, *, max_bytes: int = 16_000_000) -> Path:
    if (path.is_symlink() or any(parent.is_symlink() for parent in path.parents)
            or not path.is_file() or path.stat().st_size <= 0
            or path.stat().st_size > max_bytes):
        fail("FILE_MISSING_SYMLINK_OR_OVERSIZED")
    return path

def json_file(path: Path) -> tuple[dict, str]:
    p = regular_file(Path(path), max_bytes=8_000_000)
    raw = p.read_bytes()
    obj = json.loads(raw.decode("utf-8"))
    if type(obj) is not dict:
        fail("REVIEW_NOT_OBJECT")
    return obj,digest(raw)

def project_paths(project: Path) -> tuple[Path,Path,Path]:
    # Never infer the native game's location from cwd or a user-supplied
    # external directory. No user library, personal save or AppData scanning.
    project = Path(project).absolute()
    if project.is_symlink() or not project.is_dir():
        fail("PROJECT_NOT_AVAILABLE")
    work = project / ".blue-work"
    main = project / "game"
    if (work.is_symlink() or main.is_symlink() or not main.is_dir()
            or any(p.is_symlink() for p in main.parents)):
        fail("MAIN_GAME_OR_WORKSPACE_INVALID")
    return project,main,work

def validate_review(project: Path, overlay: Path, spec_path: Path,
                    rights_path: Path, reservations_path: Path) -> dict:
    project,main,work = project_paths(project)
    overlay = Path(overlay).absolute()
    if (not overlay.is_relative_to(work) or overlay.is_symlink()
            or any(p.is_symlink() for p in overlay.parents)
            or not overlay.is_dir()):
        fail("PRIVATE_OVERLAY_REQUIRED")
    rights_path = Path(rights_path).absolute()
    reservations_path = Path(reservations_path).absolute()
    spec_path = Path(spec_path).absolute()
    # Reviews remain local inside .blue-work. Never require uploading private
    # maps, rights contracts, executable or sensitive saves into a public PR.
    if any(not p.is_relative_to(work) for p in
           (rights_path,reservations_path,spec_path)):
        fail("PRIVATE_REVIEW_INPUTS_REQUIRED")
    rights,rights_sha = json_file(rights_path)
    reserved,reserved_sha = json_file(reservations_path)
    spec,spec_sha = json_file(spec_path)
    report,overlay_files = load_overlay(overlay,project=project)
    report_sha = file_digest(regular_file(
        overlay / "sinnoh-qa-overlay-report.json",max_bytes=8_000_000))
    exe_sha = file_digest(regular_file(main / "Game.exe",max_bytes=512*1024*1024))
    info_sha = file_digest(regular_file(main / "Data/MapInfos.rxdata",max_bytes=64*1024*1024))
    if (type(rights) is not dict or set(rights)!=RIGHT_KEYS
            or (rights["schema"],rights["region"],rights["stage"],rights["mode"]) !=
                (1,"SINNOH","J06","LOCAL_RIGHTS_REVIEW_NOT_REDISTRIBUTABLE")
            or rights["reviewed_locally"] is not True
            or rights["redistribution_authorized"] is not False
            or any(rights[k]!=v for k,v in (
                ("overlay_report_sha256",report_sha),
                ("source_game_exe_sha256",exe_sha),
                ("source_mapinfos_sha256",info_sha),
                ("spec_sha256",spec_sha)))
            or type(rights["reviewer_reference"]) is not str
            or not 8<=len(rights["reviewer_reference"])<=200):
        fail("RIGHTS_NOT_EXPLICITLY_REVIEWED")
    expected=set(overlay_files)
    actual=rights.get("files")
    if type(actual) is not dict or set(actual)!=expected or len(actual)>5000:
        fail("RIGHTS_MISSING_PER_FILE")
    for rel,raw in actual.items():
        if (type(rel) is not str or not REL.fullmatch(rel)
                or type(raw) is not dict or set(raw)!=FILE_REVIEW
                or raw.get("sha256")!=digest(overlay_files[rel])
                or raw.get("basis") not in ALLOWED_BASIS
                or raw.get("private_qa_permitted") is not True
                or type(raw.get("permission_evidence")) is not str
                or not 8<=len(raw["permission_evidence"])<=240):
            fail("RIGHTS_RECORD_UNVERIFIED_OR_HASH_CHANGED")
    rows=spec.get("maps")
    if (type(spec) is not dict or spec.get("region")!="SINNOH"
            or type(rows) is not list or len(rows)!=9
            or any(type(x) is not dict or type(x.get("map_id")) is not int
                   or not 442<=x["map_id"]<=517
                   or type(x.get("events")) is not list for x in rows)
            or sum(len(x["events"]) for x in rows)!=24):
        fail("NINE_REAL_MAP_EVENT_SPEC_REQUIRED")
    # NPCs and three physical starter balls MUST have reviewed artwork in
    # the overlay itself. Never silently borrow an unknown file from the
    # main game or call an unverified filename a real sprite.
    sprites=set()
    for row in rows:
        for event in row["events"]:
            if type(event) is not dict:
                fail("EVENT_SPEC_INVALID")
            if event.get("kind") not in ("handler","starter_ball"):
                continue
            name=event.get("sprite")
            if (type(name) is not str or not re.fullmatch(
                    r"[A-Za-z0-9_ .()-]{1,100}",name)
                    or event.get("verified_sprite") is not True):
                fail("NPC_OR_STARTER_SPRITE_NOT_VERIFIED")
            sprites.add("Graphics/Characters/"+name+".png")
    if not sprites or not sprites.issubset(overlay_files):
        fail("PHYSICAL_CHARACTER_SPRITES_MISSING_IN_PRIVATE_OVERLAY")
    for rel in sprites:
        image=overlay_files[rel]
        if len(image)<16 or not image.startswith(b"\x89PNG\r\n\x1a\n"):
            fail("SPRITE_FILE_NOT_VALID_PNG")
    mids=[x["map_id"] for x in rows]
    all_mids=report.get("geometry_all_map_ids",[])
    if (type(all_mids) is not list or len(all_mids)<9 or
            any(type(i) is not int or not 442<=i<=517 for i in all_mids) or
            len(set(all_mids))!=len(all_mids) or
            len(set(mids))!=9 or not set(mids).issubset(set(all_mids)) or
            sum(e["kind"]=="warp" for x in rows for e in x["events"])!=16 or
            sum(e["kind"]=="handler" for x in rows for e in x["events"])!=5 or
            sum(e["kind"]=="starter_ball" for x in rows for e in x["events"])!=3):
        fail("NINE_MAPS_16_WARPS_5_NPCS_3_BALLS_REQUIRED")
    if (type(reserved) is not dict or set(reserved)!=RESERVE_KEYS
            or (reserved.get("schema"),reserved.get("region"),
                reserved.get("stage"),reserved.get("mode")) !=
               (1,"SINNOH","J06","PRIVATE_REGIONAL_MAPID_REVIEW")
            or reserved["reviewed_locally"] is not True
            or reserved["r07_global_reservations_approved"] is not True
            or reserved["source_mapinfos_sha256"]!=info_sha
            or reserved["candidate_map_ids"]!=sorted(all_mids)
            or type(reserved["protected_map_ids"]) is not list
            or len(reserved["protected_map_ids"])>5000
            or any(type(m) is not int or m<1 or m>999
                   for m in reserved["protected_map_ids"])
            or len(set(reserved["protected_map_ids"])) != len(reserved["protected_map_ids"])
            or type(reserved["reviewer_reference"]) is not str
            or not 8<=len(reserved["reviewer_reference"])<=200):
        fail("R07_MAPID_REVIEW_NOT_APPROVED")
    protected=set(reserved["protected_map_ids"])
    native=native_map_ids(main)
    if set(all_mids) & (protected|native):
        fail("MAPID_COLLISION_NATIVE_OR_RESERVED")
    # This is explicit LOCAL human attestation, not an OpenAI decision about
    # legal rights or an R07 global certification. User must provide evidence.
    return {
        "schema":1,"region":"SINNOH","stage":"J06",
        "status":"LOCAL_PRIVATE_QA_INPUTS_VERIFIED_NOT_NATIVE_PLAYABLE",
        "source_game_exe_sha256":exe_sha,"source_mapinfos_sha256":info_sha,
        "overlay_report_sha256":report_sha,"rights_sha256":rights_sha,
        "reservations_sha256":reserved_sha,"spec_sha256":spec_sha,
        "private_map_input_count":9,"private_total_stage_map_ids":len(all_mids),
        "private_character_sprite_files_hash_verified":len(sprites),
        "events_expected":24,"warps_expected":16,
        "npc_handlers_expected":5,"starter_balls_expected":3,
        "private_qa_rights_human_attested":True,
        "rights_independently_confirmed_by_chatgpt":False,
        "native_barry_pbs_compiled_verified":False,
        "qa_native_tests_executed":0,"can_publish":False,
        "can_merge_game":False,"game_exe_executed":False,
        "main_game_modified":False,"saves_read_or_modified":False,
        "_spec":spec,
    }

def qa_copy_path(project: Path, token: str) -> Path:
    project,main,work = project_paths(project)
    if type(token) is not str or not TOKEN.fullmatch(token):
        fail("QA_TOKEN_INVALID")
    path=work / ("game-sinnoh-qa-"+token)
    if (path.is_symlink() or any(p.is_symlink() for p in path.parents)
            or not path.is_relative_to(work) or path==main):
        fail("QA_PATH_UNSAFE")
    return path

def safe_windows_inventory_name(rel: str) -> bool:
    """Reject Windows traversal/reparse aliases but allow native Unicode names."""
    if type(rel) is not str or not rel or len(rel)>1024 or rel.startswith("/"):
        return False
    if any(ord(ch)<32 or ch in '<>:"\\|?*' for ch in rel):
        return False
    parts=rel.split("/")
    if any(not part or part in (".","..") or part.endswith((".", " "))
           or len(part)>255 for part in parts):
        return False
    reserved=re.compile(r"(?i:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?\Z")
    return not any(reserved.fullmatch(p) for p in parts)

def inventory(folder: Path) -> dict[str,str]:
    if folder.is_symlink() or not folder.is_dir():
        fail("QA_DIR_MISSING_OR_LINK")
    result={}
    seen=set()
    for p in folder.rglob("*"):
        if p.is_symlink() or any(parent.is_symlink() for parent in p.parents):
            fail("QA_CONTAINS_LINK_OR_JUNCTION")
        if p.is_dir():
            continue
        if not p.is_file():
            fail("QA_NONREGULAR_ENTRY")
        rel=p.relative_to(folder).as_posix()
        if rel==RECEIPT:
            continue
        if (len(result)>=40000 or not safe_windows_inventory_name(rel)
                or rel.casefold() in seen):
            fail("QA_FILES_INVALID_OR_TOO_MANY")
        seen.add(rel.casefold())
        result[rel]=file_digest(p)
    return dict(sorted(result.items()))

def seal_copy(project: Path, qa: Path, checked: dict) -> tuple[str,dict]:
    current=verify(qa,project=project)
    if (current["compile_request_pending"] is not True or
            current["compiled_marker_present"] is not False or
            current["save_namespace_verified"] is not True or
            current["foreign_save_inherited"] is not False):
        fail("QA_INSTALLER_SAVE_OR_COMPILE_INCONSISTENT")
    trans=json_file(qa / "sinnoh-qa-transaction.json")[0]
    meta=json_file(qa / QA_META)[0]
    snapshot=inventory(qa)
    if not snapshot:
        fail("QA_EMPTY")
    receipt={
        "schema":1,"region":"SINNOH","stage":"J06",
        "mode":"SEALED_PRIVATE_QA_COPY_UNEXECUTED",
        "qa_folder":qa.name,
        "source_game_exe_sha256":checked["source_game_exe_sha256"],
        "source_mapinfos_sha256":checked["source_mapinfos_sha256"],
        "overlay_report_sha256":checked["overlay_report_sha256"],
        "rights_sha256":checked["rights_sha256"],
        "reservations_sha256":checked["reservations_sha256"],
        "spec_sha256":checked["spec_sha256"],
        "save_profile":trans["save_isolation"],
        "files_sha256":snapshot,
        "main_game_modified":False,"saves_read_or_modified":False,
        "game_exe_executed":False,"native_gameplay_verified":False,
        "can_publish":False,
    }
    target=qa/RECEIPT
    if target.exists() or target.is_symlink():
        fail("QA_RECEIPT_ALREADY_EXISTS")
    raw=(json.dumps(receipt,ensure_ascii=False,sort_keys=True,indent=2)+"\n").encode("utf-8")
    with target.open("xb") as fd:
        fd.write(raw);fd.flush();os.fsync(fd.fileno())
    return digest(raw),receipt

def create_private_copy(project: Path, overlay: Path, spec_path: Path,
                        rights_path: Path, reservations_path: Path,
                        *, token: str | None=None, dry_run: bool=True) -> dict:
    checked=validate_review(project,overlay,spec_path,rights_path,reservations_path)
    project,main,work=project_paths(project)
    token=token or secrets.token_hex(6)
    qa=qa_copy_path(project,token)
    # Delegate nine-map RXDATA event consistency, PBS generation, plugin
    # bootstrap order and save namespace validation to the existing installer.
    report,output,native=prepare(main,overlay,checked["_spec"],
                                  token=token,project=project)
    if (report.get("runtime_playable") is not False or
            report.get("can_install_into_main_game") is not False or
            report.get("save_isolation") is None):
        fail("LEGACY_INSTALLER_CLAIMED_PLAYABLE")
    result={k:v for k,v in checked.items() if k!="_spec"}
    result.update(qa_directory=str(qa),dry_run=dry_run,
                  native_compilation_executed=False,
                  existing_installer_prepared=True,
                  save_namespace_checked=True,files_to_overlay=len(output))
    if dry_run:
        return result
    if qa.exists() or qa.is_symlink():
        fail("DESTINATION_ALREADY_EXISTS")
    install(project,main,qa,report,output,native)
    receipt_sha,receipt=seal_copy(project,qa,checked)
    return {**result,"dry_run":False,"copy_created":True,
            "receipt_sha256":receipt_sha,
            "save_profile":receipt["save_profile"]}

def receipt_checked(project: Path, qa: Path, receipt_sha: str,
                    *, pristine: bool=False) -> dict:
    project,main,work=project_paths(project)
    qa=Path(qa).absolute()
    if (not qa.is_relative_to(work) or qa.parent!=work
            or not re.fullmatch(r"game-sinnoh-qa-[a-f0-9]{12}",qa.name)
            or qa.is_symlink() or not qa.is_dir()):
        fail("QA_COPY_NOT_ISOLATED")
    token=qa.name.rsplit("-",1)[-1]
    qa_copy_path(project,token)
    if type(receipt_sha) is not str or not SHA.fullmatch(receipt_sha):
        fail("RECEIPT_SHA_REQUIRED")
    path=regular_file(qa / RECEIPT,max_bytes=8_000_000)
    if file_digest(path)!=receipt_sha:
        fail("RECEIPT_CHANGED")
    receipt=json.loads(path.read_text("utf-8"))
    if (type(receipt) is not dict or set(receipt)!=RECEIPT_KEYS
            or (receipt["schema"],receipt["region"],receipt["stage"],
                receipt["mode"],receipt["qa_folder"]) !=
               (1,"SINNOH","J06","SEALED_PRIVATE_QA_COPY_UNEXECUTED",qa.name)
            or any(receipt[k] is not False for k in (
                "main_game_modified","saves_read_or_modified",
                "game_exe_executed","native_gameplay_verified","can_publish"))
            or type(receipt["files_sha256"]) is not dict
            or not receipt["files_sha256"]):
        fail("RECEIPT_UNTRUSTED")
    for key in ("source_game_exe_sha256","source_mapinfos_sha256",
                "overlay_report_sha256","rights_sha256","reservations_sha256",
                "spec_sha256"):
        if type(receipt[key]) is not str or not SHA.fullmatch(receipt[key]):
            fail("RECEIPT_BINDINGS_MISSING")
    if not (main/"Game.exe").is_file() or file_digest(main/"Game.exe")!=receipt["source_game_exe_sha256"]:
        fail("MAIN_GAME_EXE_CHANGED")
    if file_digest(regular_file(main/"Data/MapInfos.rxdata",max_bytes=64*1024*1024))!=receipt["source_mapinfos_sha256"]:
        fail("MAIN_MAPINFOS_CHANGED")
    if pristine:
        if inventory(qa)!=receipt["files_sha256"]:
            fail("QA_CHANGED_REFUSE_ROLLBACK_TO_PRESERVE_SAVES")
    state=verify(qa,project=project)
    if (state["save_namespace_verified"] is not True
            or state["foreign_save_inherited"] is not False
            or state["playable_approved"] is not False):
        fail("QA_OR_SAVE_VERIFICATION_FAILED")
    return {"receipt":receipt,"verification":state}

def rollback_private_copy(project: Path, qa: Path, receipt_sha: str,
                          *, confirm: bool=False) -> dict:
    if confirm is not True:
        fail("EXPLICIT_ROLLBACK_CONFIRMATION_REQUIRED")
    qa=Path(qa).absolute()
    receipt_checked(project,qa,receipt_sha,pristine=True)
    # No saves, compile markers, added files or modifications: only a pristine
    # never-run copy is deletable. A used QA is kept for manual review, rather
    # than deleting someone's newly created test save.
    main=Path(project).absolute()/"game"
    if qa==main or main.is_relative_to(qa) or qa.is_relative_to(main):
        fail("MAIN_GAME_CANNOT_BE_REMOVED")
    shutil.rmtree(qa)
    return {"schema":1,"stage":"J06","mode":"PRISTINE_COPY_ROLLBACK",
            "copy_removed":True,"main_game_modified":False,
            "saves_deleted":False,"native_gameplay_verified":False}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project",type=Path,default=ROOT)
    p.add_argument("--overlay",type=Path)
    p.add_argument("--spec",type=Path)
    p.add_argument("--rights",type=Path)
    p.add_argument("--reservations",type=Path)
    actions=p.add_mutually_exclusive_group()
    actions.add_argument("--install",action="store_true")
    actions.add_argument("--verify",type=Path)
    actions.add_argument("--rollback",type=Path)
    actions.add_argument("--compile",type=Path)
    actions.add_argument("--launch",type=Path)
    p.add_argument("--receipt-sha")
    p.add_argument("--confirm-rollback",action="store_true")
    args=p.parse_args(argv)
    try:
        if any((args.verify,args.rollback,args.compile,args.launch)):
            if (any((args.overlay,args.spec,args.rights,args.reservations,args.install))
                or not args.receipt_sha):
                fail("REVIEW_OR_RECEIPT_ARGUMENTS_INVALID")
            qa=args.verify or args.rollback or args.compile or args.launch
            data=receipt_checked(args.project,qa,args.receipt_sha,
                                 pristine=bool(args.rollback))
            if args.rollback:
                result=rollback_private_copy(args.project,qa,args.receipt_sha,
                                             confirm=args.confirm_rollback)
            elif args.verify:
                result={"stage":"J06","status":"QA_COPY_VALID_NOT_PLAYABLE",
                        **data["verification"],"receipt_verified":True}
            else:
                if args.confirm_rollback:
                    fail("ROLLBACK_FLAG_NOT_ALLOWED_FOR_LAUNCH")
                if sys.platform!="win32" or os.name!="nt":
                    fail("WINDOWS_ONLY")
                # Native launcher itself verifies compilation and save isolation.
                # No shell, no fallback to main; Game.exe only in distinct QA.
                result=launch_native(qa,project=args.project,
                                    mode="compile" if args.compile else "launch")
        else:
            if (not all((args.overlay,args.spec,args.rights,args.reservations))
                    or args.receipt_sha or args.confirm_rollback):
                fail("ALL_PRIVATE_INPUTS_REQUIRED")
            if args.install and (sys.platform!="win32" or os.name!="nt"):
                fail("WINDOWS_ONLY")
            result=create_private_copy(
                args.project,args.overlay,args.spec,args.rights,args.reservations,
                dry_run=not args.install)
    except (OSError,ValueError,TypeError,KeyError,IndexError,UnicodeError,
            json.JSONDecodeError) as exc:
        print("SINNOH_J06_BLOQUEADO:"+str(exc),file=sys.stderr)
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2,default=str))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
