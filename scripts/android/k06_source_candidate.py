"""Install the Celadon approach locally from the pinned source and owned K05."""
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
from ensure_source import RELATIVE_ARCHIVE, RELATIVE_SOURCE, prepare
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
UPDATER="ATUALIZAR-ANDROID.py"
RELEASE=ROOT/"data/regions/android-k06-recipe.json"


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


def identity(ci):
    def git(*args):
        return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
    head=git("rev-parse","HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}",head) or head==k05.PRODUCT_REVISION:
        raise ValueError("Invalid isolated K06 identity")
    if ci:
        return head,head
    if not RELEASE.is_file() or git("status","--porcelain","--untracked-files=no"):
        raise ValueError("Use a receita oficial K06 sem alterações locais.")
    info=json_file(RELEASE)
    target=info.get("product_revision")
    if (info.get("schema")!=1 or info.get("stage")!="K06_APPROACH" or
        not isinstance(target,str) or not re.fullmatch(r"[0-9a-f]{40}",target) or
        target==k05.PRODUCT_REVISION):
        raise ValueError("A receita não aponta para a revisão oficial K06.")
    subprocess.run(["git","merge-base","--is-ancestor",target,head],cwd=ROOT,check=True)
    owned={"data/regions/android-k06-recipe.json","docs/ANDROID_K06_ATUALIZACAO_PELA_FONTE.md",
           ".github/workflows/android-k06-source-release.yml"}
    if set(git("diff","--name-only",target,head).splitlines())-owned:
        raise ValueError("A receita difere do produto K06 verificado.")
    return target,head


def provenance(files,target,head,base,ci):
    return {**k05.installed_provenance(files,head),"product_revision":target,
            "mode":"k06-ci-candidate" if ci else "pinned-source-local","stage":"K06_APPROACH",
            "previous_inventory_sha256":base["source_update"]["inventory_sha256"]}


def root_work(root,work,ci):
    root=root.expanduser().resolve()
    if ci and root!=require_ci():
        raise ValueError("K06 source CI received an unexpected installation")
    fallback=STAGING if ci else root.parent/(root.name+"-Compilar-K06")
    return root,work or fallback


def stage(root,work=None,ci=False):
    root,work=root_work(root,work,ci)
    target,recipe=identity(ci)
    old,_=verify_k05_android_predecessor(root)
    source=authenticated_source() if ci else prepare()
    holder=k05.work_holder(root,old["revision"],work)
    staged=holder/"game"
    changes,witness=plan(root,source,summarize(source,json_file(KANTO)),
                         {name:row["sha256"] for name,row in old["files"].items()})
    k05.clone_verified_install(root,staged,old)
    try:
        for name,data in changes.items():
            k05.atomic_file(staged/name,data)
        config=staged/"mkxp.json"
        config.write_text(k05.compiler_config(config.read_text("utf-8-sig"),PROFILE),encoding="utf8")
        if not save_namespace_valid(staged,PROFILE) or (ci and (staged/SAVE).exists()):
            raise ValueError("The isolated compiler could access the original player profile")
        if UPDATER not in old["files"]:
            raise ValueError("The existing mobile updater is not tracked")
        shutil.copyfile(ROOT/"scripts/android/update_client.py",staged/UPDATER)
        k05.write_compiler_ini(staged)
        request_compile(staged)
        expected=sorted([*changes,BUILD,CONNECTION_CACHE,UPDATER])
        marker=holder/"proof.json"
        marker.write_text(json.dumps({"target":target,"recipe":recipe,"paths":expected,"root":str(root),
                                      "staged":str(staged),"base":old["source_update"],
                                      "source_ids":witness["source_ids"]},sort_keys=True),encoding="utf8")
        verify_native_graph(staged)
    except BaseException:
        shutil.rmtree(holder)
        raise
    print("KANTO_K06_ANDROID_PREPARED_FROM_K05_OK",flush=True)
    return staged


def finish(root,work=None,ci=False):
    root,work=root_work(root,work,ci)
    target,recipe=identity(ci)
    k05.recover_source_install(root,work,True)
    before=(root/MARKER).read_bytes()
    old,all_maps=verify_k05_android_predecessor(root)
    holder=k05.work_holder(root,old["revision"],work)
    staged=holder/"game"
    proof=json_file(holder/"proof.json")
    if (proof["target"]!=target or proof["recipe"]!=recipe or proof["base"]!=old["source_update"]
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
              "Data/blue-kanto-install.json","Data/blue-kanto-k06-approach.json",BUILD,CONNECTION_CACHE,UPDATER}
    if set(proof["paths"])!=expected or len(expected)!=13:
        raise ValueError("Unexpected Android K06 change scope")
    display=staged/BUILD
    current=display.read_text("utf8")
    anchored,n=re.subn(r"(?m)^Revision: "+k05.PRODUCT_REVISION+r"$","Revision: "+target,current)
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
    installed={**old,"files":files,"revision":target,"source_update":provenance(files,target,recipe,old,ci)}
    sentinel=k05.digest(checked_file(root,SAVE)) if ci else None
    nonregional={name:row for name,row in old["files"].items()
                 if re.fullmatch(r"Data/Map\d+\.rxdata",name) and name not in changed}
    def postcheck(game):
        verify_regions(game)
        verify_native_graph(game,compiled=True)
        _,after=k05.protected_map_inventory(game,installed)
        if (any(after.get(name)!=sha for name,sha in all_maps.items() if name not in changed)
                or any(k05.checked_row(game/name)!=row for name,row in nonregional.items())
                or (ci and k05.digest(checked_file(game,SAVE))!=sentinel)):
            raise ValueError("K06 changed unrelated Android content or the synthetic save")
    k05.commit_local(root,staged,changed,json.dumps(installed,sort_keys=True).encode("utf8"),
                     holder/"backup",verify=postcheck,before_marker=before,baseline=old["revision"])
    if read_installed(root)!=installed:
        raise ValueError("K06 candidate final marker was not committed")
    print("KANTO_K06_ANDROID_FORWARD_COMPILED_OK:"+json.dumps(
        {"changed":len(changed),"unmodified_maps":len(nonregional),"hoenn":199,
         "product_revision":target,"recipe_revision":recipe,"physical_mobile_test":False}),flush=True)


def workflow(root,work=None,apply=False,ci=False):
    root,work=root_work(root,work,ci)
    target,recipe=identity(ci)
    k05.recover_source_install(root,work,apply)
    installed=read_installed(root)
    if installed["revision"]==target:
        stamp=installed.get("source_update") or {}
        actual=k05.installed_provenance(installed["files"],recipe)["inventory_sha256"]
        if (stamp.get("product_revision"),stamp.get("recipe_revision"),stamp.get("inventory_sha256"),
            stamp.get("stage"))!=(target,recipe,actual,"K06_APPROACH"):
            raise ValueError("The installed K06 source receipt is invalid")
        k05.protected_map_inventory(root,installed)
        verify_native_graph(root,compiled=True)
        print("K06 já está instalado pela fonte.")
        return
    old,_=verify_k05_android_predecessor(root)
    if not apply:
        print("K06 está disponível pela fonte para a sua instalação K05. Use --source --source-stage k06 --update.")
        return
    holder=k05.work_holder(root,old["revision"],work)
    staged=holder/"game"
    if not holder.exists():
        staged=stage(root,work,ci)
    elif staged.is_dir() and (staged/"Data/blue-android-compiled.txt").is_file():
        finish(root,work,ci)
        return
    else:
        proof=json_file(holder/"proof.json")
        if (proof.get("root"),proof.get("staged"),proof.get("target"),proof.get("recipe"))!=(
                str(root),str(staged),target,recipe):
            raise ValueError("A cópia de compilação não pertence a esta receita e instalação.")
    print("Adicione só esta cópia temporária como outro jogo no JoiPlay:")
    print(staged/"Game.exe")
    print("Depois que compilar, feche o JoiPlay e execute de novo o mesmo comando.")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("step",nargs="?",choices=["stage","finish"])
    parser.add_argument("--game-dir",type=Path)
    parser.add_argument("--work-dir",type=Path)
    parser.add_argument("--source-workflow",action="store_true")
    parser.add_argument("--update",action="store_true")
    parser.add_argument("--ci",action="store_true",help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.source_workflow and args.game_dir:
        workflow(args.game_dir,args.work_dir,args.update,args.ci)
    elif args.step:
        globals()[args.step](require_ci(),STAGING,True)
    else:
        parser.error("Use o atualizador oficial com --source --source-stage k06.")
