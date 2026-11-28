"""Disposable CI: apply the Celadon approach on an actual source-built Android K05."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT),str(ROOT/"scripts/regions")]

from audit import KANTO, json_file
from audit_k06_rocket import summarize
from ensure_source import RELATIVE_ARCHIVE, RELATIVE_SOURCE
from k06_approach_migration import checked_file, plan, verify_k05_android_predecessor, verify_native_graph
from qa_k04_migration import save_namespace_valid
from scripts.android import source_update as k05
from scripts.android.package import fingerprint, request_compile, verify_regions
from scripts.android.update_client import MARKER, read_installed

K05_RECIPE="4bda388e0f6d07763c95cfd9877ce337e61f9cb9"
WORK=ROOT/".blue-work/k06-android-ci"
INPUT=WORK/"Pokemon-Blue-Android"
ORIGINAL=WORK/"k05-recipe"
STAGING=WORK/"k06-overlay"
PROFILE="Kanto K06 Android Candidate CI"
BUILD="Data/blue-mobile-build.txt"
CONNECTION_CACHE="Data/map_connections.dat"
SAVE="K06-SAVE-SYNTHETIC.rxsave"


def require_ci():
    if os.name!="nt" or os.getenv("GITHUB_ACTIONS")!="true" or not INPUT.is_dir():
        raise ValueError("K06 candidate can only use its disposable Windows CI Android fixture")
    if INPUT.resolve()!=WORK.resolve()/INPUT.name or WORK.resolve()!=WORK:
        raise ValueError("Android candidate paths resolve outside the disposable workspace")
    return INPUT


def authenticated_source():
    head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ORIGINAL,text=True).strip()
    if head!=K05_RECIPE or k05.digest(ORIGINAL/RELATIVE_ARCHIVE)!=json_file(KANTO)["sha256"]:
        raise ValueError("Android CI did not build K05 from the pinned released recipe and original source")
    return ORIGINAL/RELATIVE_SOURCE


def provenance(files,head,base):
    return {**k05.installed_provenance(files,head),"product_revision":head,
            "mode":"k06-ci-candidate","previous_inventory_sha256":base["source_update"]["inventory_sha256"]}


def stage():
    root=require_ci()
    candidate=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    if not re.fullmatch(r"[0-9a-f]{40}",candidate) or candidate==k05.PRODUCT_REVISION:
        raise ValueError("Invalid isolated K06 candidate identity")
    old,_=verify_k05_android_predecessor(root)
    source=authenticated_source()
    holder=k05.work_holder(root,old["revision"],STAGING)
    staged=holder/"game"
    changes,witness=plan(root,source,summarize(source,json_file(KANTO)),
                         {name:row["sha256"] for name,row in old["files"].items()})
    k05.clone_verified_install(root,staged,old)
    try:
        for name,data in changes.items():
            k05.atomic_file(staged/name,data)
        config=staged/"mkxp.json"
        config.write_text(k05.compiler_config(config.read_text("utf-8-sig"),PROFILE),encoding="utf8")
        if not save_namespace_valid(staged,PROFILE) or (staged/SAVE).exists():
            raise ValueError("The candidate compiler could access the original player profile")
        k05.write_compiler_ini(staged)
        request_compile(staged)
        expected=sorted([*changes,BUILD,CONNECTION_CACHE])
        marker=holder/"proof.json"
        marker.write_text(json.dumps({"candidate":candidate,"paths":expected,"root":str(root),
                                      "staged":str(staged),"base":old["source_update"],
                                      "source_ids":witness["source_ids"]},sort_keys=True),encoding="utf8")
        verify_native_graph(staged)
    except BaseException:
        shutil.rmtree(holder)
        raise
    print("KANTO_K06_ANDROID_PREPARED_FROM_K05_OK",flush=True)


def finish():
    root=require_ci()
    k05.recover_source_install(root,STAGING,True)
    before=(root/MARKER).read_bytes()
    old,all_maps=verify_k05_android_predecessor(root)
    candidate=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    holder=k05.work_holder(root,old["revision"],STAGING)
    staged=holder/"game"
    proof=json_file(holder/"proof.json")
    if (proof["candidate"]!=candidate or proof["base"]!=old["source_update"]
            or proof["root"]!=str(root) or proof["staged"]!=str(staged)
            or read_installed(staged)!=old):
        raise ValueError("Candidate receipt does not bind these two installations")
    marker=staged/"Data/blue-android-compiled.txt"
    if not marker.is_file() or marker.read_text("ascii")!=fingerprint(staged):
        raise ValueError("The Android K06 candidate has not been compiled")
    verify_regions(staged)
    verify_native_graph(staged,compiled=True)
    graph=json_file(staged/"Data/blue-kanto-k06-approach.json")
    expected=set(graph["destinations"].values())|{"PBS/map_connections_kanto.txt",
              "Data/blue-kanto-install.json","Data/blue-kanto-k06-approach.json",BUILD,CONNECTION_CACHE}
    if set(proof["paths"])!=expected or len(expected)!=12:
        raise ValueError("Unexpected Android K06 change scope")
    display=staged/BUILD
    current=display.read_text("utf8")
    anchored,n=re.subn(r"(?m)^Revision: "+k05.PRODUCT_REVISION+r"$","Revision: "+candidate,current)
    if n!=1:
        raise ValueError("K06 candidate cannot claim or reuse the K05 product revision")
    display.write_text(anchored,encoding="utf8")
    changed={}
    for name in sorted(expected):
        actual=k05.checked_row(root/name)
        if actual!=old["files"].get(name):
            raise ValueError(f"Android predecessor changed before K06 apply: {name}")
        row=k05.manifest_row(checked_file(staged,name))
        if row!=actual:
            changed[name]=row
    if not set(graph["destinations"].values())<=changed.keys() or CONNECTION_CACHE not in changed:
        raise ValueError("K06 compiler did not generate all controlled maps and the new graph")
    files={**old["files"],**changed}
    installed={**old,"files":files,"revision":candidate,"source_update":provenance(files,candidate,old)}
    sentinel=k05.digest(checked_file(root,SAVE))
    nonregional={name:row for name,row in old["files"].items()
                 if re.fullmatch(r"Data/Map\d+\.rxdata",name) and name not in changed}
    def postcheck(game):
        verify_regions(game)
        verify_native_graph(game,compiled=True)
        _,after=k05.protected_map_inventory(game,installed)
        if (any(after.get(name)!=sha for name,sha in all_maps.items() if name not in changed)
                or any(k05.checked_row(game/name)!=row for name,row in nonregional.items())
                or k05.digest(checked_file(game,SAVE))!=sentinel):
            raise ValueError("K06 changed unrelated Android content or the synthetic save")
    k05.commit_local(root,staged,changed,json.dumps(installed,sort_keys=True).encode("utf8"),
                     holder/"backup",verify=postcheck,before_marker=before,baseline=old["revision"])
    if read_installed(root)!=installed:
        raise ValueError("K06 candidate final marker was not committed")
    print("KANTO_K06_ANDROID_FORWARD_COMPILED_OK:"+json.dumps(
        {"changed":len(changed),"unmodified_maps":len(nonregional),"hoenn":199,
         "candidate_sha":candidate,"physical_mobile_test":False}),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step",choices=["stage","finish"])
    globals()[parser.parse_args().step]()
