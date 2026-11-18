#!/usr/bin/env python3
"""J08 Sinnoh: private JoiPlay delta candidate, NEVER a live Android update.

No downloaded donor files, network, Windows Game.exe execution, Android device
access or save modification. Requires the SHA-bound J06/J07 private nine-map
sources and an *explicit human* Windows-review receipt. Test fixtures are not
human/native evidence. Generates only a local, never-applied delta ZIP from
TWO isolated Android QA snapshots, excluding root profiles and every save.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
for folder in (ROOT, ROOT/"scripts/regions"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from scripts.android.update_client import safe_path
from prepare_sinnoh_playable_j06 import file_digest, project_paths, regular_file, SHA
from prepare_sinnoh_playable_j07 import (
    inspect_private_qa, check_session, audit_session,
    read_json
)

BASE = re.compile(r"sinnoh-j08-android-(?:base|qa)-([0-9a-f]{12})\Z")
DELTA = re.compile(r"SINNOH-J08-[0-9a-f]{12}-[0-9a-f]{12}\.delta\.zip\Z")
TOKEN = re.compile(r"[0-9a-f]{12}\Z")
CASE = re.compile(r"[A-Za-z0-9_-]{4,110}\Z")
REVIEW_MODES = {"windows":"INDEPENDENT_WINDOWS_HUMAN_REVIEW_LOCAL_ONLY",
                "android":"LOCAL_ANDROID_QA_RIGHTS_REVIEW_NOT_REDISTRIBUTABLE"}
IMMUTABLE = {"mkxp.json", "Game.ini"}
ALLOWED_SUFFIXES = {".rxdata",".rb",".txt",".json",".png",".jpg",".jpeg",
                    ".ogg",".mp3",".wav",".mid",".ttf",".otf",".dat",".bin"}
EXTRA_PROTECTED = {".exe",".dll",".so",".apk",".aab",".sh",".bat",".py",
                   ".zip",".rar",".7z",".sav",".bak",".log",".tmp"}
MANDATORY = {
    "Data/MapInfos.rxdata", "Data/System.rxdata",
    "Data/PluginScripts.rxdata", "PBS/trainers_sinnoh_barry.txt",
    "PBS/trainer_types_sinnoh_barry.txt",
}
WIN_KEYS = {
    "schema","region","stage","mode","session_sha256","j06_receipt_sha256",
    "independent_human_reviewed","reviewer_reference","cases",
}
WIN_CASE_KEYS = {"record_sha256","evidence_checked","native_windows_run_observed"}
AND_KEYS = {
    "schema","region","stage","mode","reviewed_locally",
    "redistribution_authorized","j06_receipt_sha256","j07_session_sha256",
    "windows_review_sha256","android_stage_profile_sha256",
    "android_plugin_cache_sha256","android_mapinfos_sha256",
    "reviewer_reference","files",
}
AND_FILE_KEYS = {"sha256","permission_evidence","private_qa_permitted"}

def fail(reason: str):
    raise ValueError("SINNOH_J08_BLOCKED:"+reason)

def sha(raw: bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def no_links(path: Path):
    if any(p.is_symlink() for p in (path,*path.parents)):
        fail("SYMLINK_OR_REPARSE_POINT_DENIED")

def local_review(project: Path,path: Path)->tuple[dict,str]:
    project,_,work=project_paths(project)
    path=Path(path).absolute()
    if path.parent!=work or not path.name.startswith("j08-"):
        fail("REVIEW_MUST_REMAIN_PRIVATE_BLUE_WORK_ROOT")
    no_links(path)
    return read_json(path,limit=1_000_000)

def valid_entry(name: str)->bool:
    if not safe_path(name):
        return False
    p=Path(name)
    if (len(name)>420 or any(part in (".","..","") or part.endswith((".", " "))
             for part in name.split("/"))):
        return False
    if not p.name.isascii() or p.suffix.lower() not in ALLOWED_SUFFIXES:
        return False
    if p.suffix.lower() in EXTRA_PROTECTED:
        return False
    # JoiPlay payload is restricted to data/media/Blue script sources, not
    # arbitrary executable/install scripts or metadata outside game folders.
    if name.startswith("Plugins/") and p.suffix.lower() not in {".rb",".txt",".json"}:
        return False
    if name.startswith("PBS/") and p.suffix.lower() not in {".txt",".json"}:
        return False
    if name.startswith("Data/") and p.suffix.lower() not in {
        ".rxdata",".json",".txt",".dat",".bin"}:
        return False
    return True

def profile(stage: Path,token:str)->dict:
    mk=regular_file(stage/"mkxp.json",max_bytes=100_000)
    ini=regular_file(stage/"Game.ini",max_bytes=100_000)
    no_links(mk);no_links(ini)
    data,_=read_json(mk,limit=100_000)
    expected={
        "dataPathApp":"Sinnoh-QA-Android-"+token,
        "dataPathOrg":"Dessastre-Sinnoh-Android-QA-"+token,
        "windowTitle":"Sinnoh Android QA "+token,
    }
    if (any(data.get(k)!=v for k,v in expected.items())
            or any("save" in k.casefold() or "userdata" in k.casefold()
                   for k in data)
            or sum(x.strip()=="Title="+expected["windowTitle"]
                   for x in ini.read_text("utf-8").splitlines())!=1):
        fail("ANDROID_PRIVATE_SAVE_NAMESPACE_INVALID")
    return {"sha256":file_digest(mk),"settings":expected}

def inspect_snapshot(project:Path,stage:Path,kind:str)->tuple[dict,dict,str]:
    project,main,work=project_paths(project)
    stage=Path(stage).absolute()
    if stage.parent!=work or stage.is_symlink() or not stage.is_dir():
        fail("ANDROID_SNAPSHOT_MUST_BE_ISOLATED")
    m=BASE.fullmatch(stage.name)
    if not m or stage.name!=f"sinnoh-j08-android-{kind}-{m.group(1)}":
        fail("ANDROID_SNAPSHOT_NAME_INVALID")
    no_links(stage)
    token=m.group(1)
    identity=profile(stage,token)
    assets={};casefold=set();total=0
    for entry in stage.rglob("*"):
        no_links(entry)
        if entry.is_dir():continue
        if not entry.is_file():fail("ANDROID_SNAPSHOT_CONTAINS_NONREGULAR")
        rel=entry.relative_to(stage).as_posix()
        if rel in IMMUTABLE:continue
        if (not valid_entry(rel) or rel.casefold() in casefold or
                len(assets)>=15000 or entry.stat().st_size<=0
                or entry.stat().st_size>512*1024*1024):
            fail("ANDROID_UNSAFE_ENTRY_OR_DUPLICATE")
        total+=entry.stat().st_size
        if total>4*1024**3:fail("ANDROID_SNAPSHOT_SIZE_LIMIT")
        casefold.add(rel.casefold())
        assets[rel]={"sha256":file_digest(entry),"size":entry.stat().st_size}
    if len(assets)<3 or not MANDATORY.intersection(assets):
        fail("ANDROID_REQUIRED_BASE_FILES_MISSING")
    return dict(sorted(assets.items())),identity,token

def reviewed_windows(project:Path,pre:dict,session:Path,session_sha:str,
                     winreview:Path)->str:
    session,manifest=check_session(project,pre,session,session_sha)
    audit=audit_session(project,pre,session,session_sha)
    if (audit["windows_evidence_submitted_unreviewed"]!=43
            or audit["native_windows_cases_independently_verified"]!=0
            or audit["native_android_cases_independently_verified"]!=0):
        fail("43_WINDOWS_EVIDENCE_FILES_REQUIRED_BEFORE_ANDROID")
    record,review_sha=local_review(project,winreview)
    if (set(record)!=WIN_KEYS
            or (record["schema"],record["region"],record["stage"],
                record["mode"])!=(1,"SINNOH","J08",REVIEW_MODES["windows"])
            or record["session_sha256"]!=session_sha
            or record["j06_receipt_sha256"]!=pre["receipt_sha"]
            or record["independent_human_reviewed"] is not True
            or type(record["reviewer_reference"]) is not str
            or not 8<=len(record["reviewer_reference"])<=200):
        fail("INDEPENDENT_NATIVE_WINDOWS_HUMAN_REVIEW_MISSING")
    candidates=set(manifest["windows_case_ids"])
    checks=record.get("cases")
    if type(checks) is not dict or set(checks)!=candidates:
        fail("43_WINDOWS_CASE_REVIEWS_REQUIRED")
    for ident,row in checks.items():
        path=session/"records"/(ident+".json")
        if (type(row) is not dict or set(row)!=WIN_CASE_KEYS
                or row["record_sha256"]!=file_digest(regular_file(path,max_bytes=40_000))
                or row["evidence_checked"] is not True
                or row["native_windows_run_observed"] is not True):
            fail("WINDOWS_REVIEW_RECORD_CHANGED_OR_UNVERIFIED")
    # This remains a *human declaration*, not independent ChatGPT evidence.
    return review_sha

def check_stage(project:Path,pre:dict,stage:Path,baseline:Path,
                android_review:Path,windows_sha:str,session_sha:str)->dict:
    target,ident,token=inspect_snapshot(project,stage,"qa")
    previous,bident,btoken=inspect_snapshot(project,baseline,"base")
    if (btoken!=token or bident["settings"]!=ident["settings"]
            or bident["sha256"]!=ident["sha256"]):
        fail("ANDROID_PROFILE_CHANGED_OR_NOT_ISOLATED")
    if not {"Data/MapInfos.rxdata","Data/System.rxdata","Data/PluginScripts.rxdata"}.issubset(previous):
        fail("BASELINE_NOT_PRECOMPILED_ANDROID_GAME")
    if not MANDATORY.issubset(target):
        fail("COMPLETE_ANDROID_BASE_AND_BARRY_PBS_REQUIRED")
    # No deletion, no rewriting any regional save/profile, no inherited
    # candidate-map occupancy in the baseline. All 9 physical IDs must exist.
    if set(previous)-set(target):
        fail("ANDROID_DELTA_REMOVES_EXISTING_CONTENT")
    if any(previous.get(name)!=target.get(name) for name in IMMUTABLE):
        fail("ANDROID_PROTECTED_PROFILE_CHANGED")
    spec=pre["meta"]["event_contract"]
    mids=[row.get("id") for row in spec]
    if (len(spec)!=9 or len(set(mids))!=9
            or any(type(i) is not int or i<442 or i>517 for i in mids)):
        fail("ANDROID_NINE_MAPS_NOT_PROVEN")
    maps={f"Data/Map{i:03}.rxdata" for i in mids}
    if not maps.issubset(target):
        fail("ANDROID_NINE_PHYSICAL_RXDATA_MISSING")
    if maps.intersection(previous):
        fail("ANDROID_MAPID_ALREADY_PRESENT_IN_BASELINE")
    # Every visible NPC/starter uses a png whose stage hash is explicit.
    sprites={f"Graphics/Characters/{e['sprite']}.png"
             for m in spec for e in m["events"]
             if e.get("kind") in ("handler","starter_ball")}
    if not sprites or not sprites.issubset(target):
        fail("ANDROID_NPC_STARTER_ARTWORK_MISSING")
    plugins=[x for x in target if x.startswith("Plugins/")
             and x.endswith("/SinnohPilot.rb")]
    if len(plugins)!=1:
        fail("ANDROID_BLUE_SINNOH_PLUGIN_MISSING")
    # Bind the Android candidate to the actual nine J06 map bytes, three
    # Barry PBS variants and artwork instead of accepting arbitrary files
    # of the right names. The compiled Android plugin cache remains an
    # independent, explicitly reviewed input; never pretend to compile it.
    pinned=(maps|sprites|{"PBS/trainers_sinnoh_barry.txt",
                          "PBS/trainer_types_sinnoh_barry.txt"}|set(plugins))
    for name in pinned:
        original=pre["qa"]/name
        no_links(original)
        if (not original.is_file()
                or file_digest(original)!=target[name]["sha256"]):
            fail("ANDROID_MAP_PBS_OR_SPRITE_DIFFERS_FROM_J06")
    if not target["Data/PluginScripts.rxdata"]["sha256"]:
        fail("ANDROID_COMPILED_PLUGIN_CACHE_REQUIRED")
    changed={k:v for k,v in target.items() if previous.get(k)!=v}
    if not changed or len(changed)>2000 or not (maps & set(changed)):
        fail("ANDROID_DELTA_NOT_NINE_MAP_INSERTION")
    doc,docsha=local_review(project,android_review)
    if (set(doc)!=AND_KEYS
            or (doc["schema"],doc["region"],doc["stage"],doc["mode"])!=
                 (1,"SINNOH","J08",REVIEW_MODES["android"])
            or doc["reviewed_locally"] is not True
            or doc["redistribution_authorized"] is not False
            or doc["j06_receipt_sha256"]!=pre["receipt_sha"]
            or doc["j07_session_sha256"]!=session_sha
            or doc["windows_review_sha256"]!=windows_sha
            or doc["android_stage_profile_sha256"]!=ident["sha256"]
            or doc["android_plugin_cache_sha256"]!=target["Data/PluginScripts.rxdata"]["sha256"]
            or doc["android_mapinfos_sha256"]!=target["Data/MapInfos.rxdata"]["sha256"]
            or type(doc["reviewer_reference"]) is not str
            or not 8<=len(doc["reviewer_reference"])<=200
            or type(doc["files"]) is not dict or set(doc["files"])!=set(changed)):
        fail("ANDROID_PRIVATE_RIGHTS_PER_FILE_MISSING")
    for name,item in doc["files"].items():
        if (type(item) is not dict or set(item)!=AND_FILE_KEYS
                or item["sha256"]!=changed[name]["sha256"]
                or item["private_qa_permitted"] is not True
                or type(item["permission_evidence"]) is not str
                or not 8<=len(item["permission_evidence"])<=240):
            fail("ANDROID_ASSET_PERMISSION_OR_HASH_INVALID")
    return {"stage":Path(stage).absolute(),"baseline":Path(baseline).absolute(),
            "changed":dict(sorted(changed.items())),"previous":previous,
            "target":target,"token":token,"profile_sha256":ident["sha256"],
            "android_review_sha256":docsha,"windows_review_sha256":windows_sha}

def preflight(project:Path,qa:Path,receipt_sha:str,overlay:Path,spec:Path,
              rights:Path,reservations:Path,session:Path,session_sha:str,
              winreview:Path,stage:Path,baseline:Path,android_review:Path)->dict:
    pre=inspect_private_qa(project,qa,receipt_sha,overlay=overlay,spec=spec,
                            rights=rights,reservations=reservations)
    windows_sha=reviewed_windows(project,pre,session,session_sha,winreview)
    result=check_stage(project,pre,stage,baseline,android_review,windows_sha,session_sha)
    result.update({"j06_receipt_sha256":receipt_sha,
                   "j07_session_sha256":session_sha,
                   "windows_evidence_files_present":43,
                   "windows_native_independently_verified_by_chatgpt":False,
                   "android_native_test_executed":False,"can_publish":False})
    return result

def candidate_manifest(pre:dict)->dict:
    return {
        "schema":1,"region":"SINNOH","stage":"J08",
        "mode":"PRIVATE_ANDROID_DELTA_CANDIDATE_NOT_JOIPLAY_TESTED",
        "android_save_profile_sha256":pre["profile_sha256"],
        "j06_receipt_sha256":pre["j06_receipt_sha256"],
        "j07_session_sha256":pre["j07_session_sha256"],
        "windows_review_sha256":pre["windows_review_sha256"],
        "android_review_sha256":pre["android_review_sha256"],
        "new_files":pre["changed"],
        "previous_files_sha256":{name:meta["sha256"] for name,meta in
                                 pre["previous"].items()},
        "no_deletions":True,"no_backup_created":True,
        "main_android_install_modified":False,"user_saves_accessed":False,
        "joiplay_real_test_executed":False,"can_publish":False,
        "can_install_into_main_android":False,
    }

def plan(pre:dict)->dict:
    return {"schema":1,"region":"SINNOH","stage":"J08",
            "status":"PRIVATE_QA_DELTA_PREVIEW_NOT_ANDROID_QA_APPROVAL",
            "candidate_files":len(pre["changed"]),
            "unchanged_files":len(pre["target"])-len(pre["changed"]),
            "candidate_uncompressed_bytes":sum(r["size"] for r in pre["changed"].values()),
            "no_backup":True,"no_saves_read":True,
            "real_joiplay_cases_verified":0,"can_publish":False}

def package(project:Path,pre:dict)->dict:
    project,_,work=project_paths(project)
    name="SINNOH-J08-"+pre["token"]+"-"+secrets.token_hex(6)+".delta.zip"
    output_dir=work/"sinnoh-j08-candidates"
    no_links(output_dir)
    output_dir.mkdir(parents=True,exist_ok=True)
    output=output_dir/name
    if output.exists() or output.is_symlink():fail("NO_OVERWRITE_CANDIDATES")
    descriptor=candidate_manifest(pre)
    tmp=None
    try:
        with tempfile.NamedTemporaryFile(prefix=".j08-",suffix=".tmp",
                                         dir=output_dir,delete=False) as fd:
            tmp=Path(fd.name)
        with zipfile.ZipFile(tmp,"w",compression=zipfile.ZIP_DEFLATED,
                             compresslevel=6) as archive:
            for name,metadata in sorted(pre["changed"].items()):
                path=pre["stage"]/name
                no_links(path)
                if (not valid_entry(name) or not path.is_file()
                        or file_digest(path)!=metadata["sha256"]
                        or path.stat().st_size!=metadata["size"]):
                    fail("SOURCE_CHANGED_DURING_PACKAGING")
                archive.write(path,arcname=name)
            blob=(json.dumps(descriptor,sort_keys=True,ensure_ascii=False,
                             indent=2)+"\n").encode("utf-8")
            archive.writestr("J08-delta.json",blob)
        verify_candidate(project,tmp,None,strict_name=False)
        if output.exists():fail("OUTPUT_RACE")
        tmp.rename(output)
        tmp=None
    finally:
        if tmp is not None:tmp.unlink(missing_ok=True)
    return {**plan(pre),"status":"PRIVATE_QA_DELTA_CREATED_UNRELEASED",
            "path":str(output),"zip_sha256":file_digest(output),
            "joiplay_real_test_executed":False,
            "main_android_install_modified":False}

def verify_candidate(project:Path,path:Path,expected_sha:str|None,
                     *,strict_name=True)->dict:
    project,_,work=project_paths(project)
    path=Path(path).absolute()
    if (strict_name and (path.parent!=work/"sinnoh-j08-candidates"
                         or not DELTA.fullmatch(path.name))):
        fail("NOT_PRIVATE_ANDROID_CANDIDATE")
    no_links(path)
    regular_file(path,max_bytes=2*1024**3)
    if expected_sha is not None and (
            type(expected_sha) is not str or not SHA.fullmatch(expected_sha)
            or file_digest(path)!=expected_sha):
        fail("ANDROID_DELTA_SHA_MISMATCH")
    with zipfile.ZipFile(path) as archive:
        names=archive.namelist()
        if (len(names)!=len(set(names)) or "J08-delta.json" not in names
                or len(names)>2001):
            fail("ANDROID_DELTA_ZIP_STRUCTURE_INVALID")
        info=archive.getinfo("J08-delta.json")
        if info.file_size>1_000_000:fail("MANIFEST_OVERSIZED")
        desc=json.loads(archive.read("J08-delta.json"))
        if (type(desc) is not dict or
                (desc.get("schema"),desc.get("region"),desc.get("stage"),
                 desc.get("mode"))!=(1,"SINNOH","J08",
                     "PRIVATE_ANDROID_DELTA_CANDIDATE_NOT_JOIPLAY_TESTED")
                or desc.get("can_publish") is not False
                or desc.get("can_install_into_main_android") is not False
                or desc.get("main_android_install_modified") is not False
                or desc.get("user_saves_accessed") is not False
                or desc.get("joiplay_real_test_executed") is not False
                or desc.get("no_deletions") is not True
                or desc.get("no_backup_created") is not True):
            fail("ANDROID_UNSAFE_RELEASE_MANIFEST")
        files=desc.get("new_files")
        if type(files) is not dict or set(files)!=(set(names)-{"J08-delta.json"}):
            fail("ANDROID_ZIP_INVENTORY_INCONSISTENT")
        for name,expected in files.items():
            if (not valid_entry(name) or type(expected) is not dict
                    or set(expected)!={"sha256","size"}
                    or type(expected["size"]) is not int
                    or not 0<expected["size"]<=512*1024*1024
                    or type(expected["sha256"]) is not str
                    or not SHA.fullmatch(expected["sha256"])):
                fail("ANDROID_ZIP_FILE_NOT_PERMITTED")
            item=archive.getinfo(name)
            if (item.is_dir() or item.file_size!=expected["size"]
                    or item.file_size>512*1024*1024
                    or item.compress_size>512*1024*1024
                    or ((item.external_attr>>16)&0o170000)==0o120000
                    or sha(archive.read(name))!=expected["sha256"]):
                fail("ANDROID_ZIP_CONTENT_CHANGED")
    return {"schema":1,"stage":"J08","verified_zip_structure":True,
            "changed_files":len(files),"sha256":file_digest(path),
            "android_native_verified":False,"can_publish":False}

def discard_candidate(project:Path,path:Path,expected_sha:str,confirm:bool):
    if confirm is not True:fail("EXPLICIT_DISCARD_CONFIRMATION_REQUIRED")
    verified=verify_candidate(project,path,expected_sha)
    Path(path).absolute().unlink()
    return {"schema":1,"stage":"J08","discarded_only_unapplied_zip":True,
            "user_saves_modified":False,"android_install_modified":False,
            "android_native_verified":False}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project",type=Path,default=ROOT)
    actions=p.add_mutually_exclusive_group()
    actions.add_argument("--package",action="store_true")
    actions.add_argument("--verify",type=Path)
    actions.add_argument("--discard",type=Path)
    p.add_argument("--zip-sha")
    p.add_argument("--confirm-discard",action="store_true")
    p.add_argument("--qa",type=Path)
    p.add_argument("--receipt-sha")
    p.add_argument("--overlay",type=Path)
    p.add_argument("--spec",type=Path)
    p.add_argument("--rights",type=Path)
    p.add_argument("--reservations",type=Path)
    p.add_argument("--session",type=Path)
    p.add_argument("--session-sha")
    p.add_argument("--windows-review",type=Path)
    p.add_argument("--android-stage",type=Path)
    p.add_argument("--android-baseline",type=Path)
    p.add_argument("--android-review",type=Path)
    args=p.parse_args(argv)
    try:
        if args.verify or args.discard:
            if any((args.qa,args.overlay,args.spec,args.rights,args.reservations,
                    args.session,args.windows_review,args.android_stage,args.android_review)):
                fail("VERIFY_DISCARD_ACCEPTS_ONLY_PRIVATE_CANDIDATE")
            if args.discard:
                result=discard_candidate(args.project,args.discard,args.zip_sha,
                                         args.confirm_discard)
            else:
                if args.confirm_discard:fail("DISCARD_FLAG_INVALID_FOR_VERIFY")
                result=verify_candidate(args.project,args.verify,args.zip_sha)
        else:
            required=(args.qa,args.receipt_sha,args.overlay,args.spec,args.rights,
                      args.reservations,args.session,args.session_sha,
                      args.windows_review,args.android_stage,args.android_baseline,
                      args.android_review)
            if not all(required) or args.zip_sha or args.confirm_discard:
                fail("ALL_PRIVATE_J06_J07_ANDROID_SOURCES_REQUIRED")
            pre=preflight(args.project,args.qa,args.receipt_sha,args.overlay,args.spec,
                args.rights,args.reservations,args.session,args.session_sha,
                args.windows_review,args.android_stage,args.android_baseline,
                args.android_review)
            result=package(args.project,pre) if args.package else plan(pre)
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            json.JSONDecodeError,zipfile.BadZipFile) as exc:
        print("SINNOH_J08_BLOQUEADO:"+str(exc),file=sys.stderr)
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
