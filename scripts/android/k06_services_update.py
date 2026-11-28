"""Apply the Celadon store source build locally after compiling an isolated copy."""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from k06_services_candidate import (
    ROOT, PRODUCT as PREVIOUS, RECIPE as PREVIOUS_RECIPE, GAME as CI_GAME, SAVE, PROFILE,
    CANDIDATES, STAGE_LOCAL, STORE, source, verify_predecessor, pinned_source, require_ci,
    verify_clone, KANTO_PLUGIN, REGION_START_PLUGIN, HOENN_PLUGIN, INSTALL, checked_file, KANTO,
    inventory, json_file, summarize, stage_services, save_namespace_valid, request_compile, compiled_region,
)
from ensure_source import prepare
from scripts.android.update_client import MARKER, read_installed, safe_path

STAGE = "K06_CELADON_SERVICES"
RELEASE = ROOT/"data/regions/android-k06-services-recipe.json"
UPDATER = "ATUALIZAR-ANDROID.py"
BUILD = "Data/blue-mobile-build.txt"
CACHE = {"Data/items.dat","Data/map_metadata.dat","Data/PluginScripts.rxdata"}
SHARED = {"Data/MapInfos.rxdata","Data/Tilesets.rxdata","Data/blue-kanto-ready.txt",
          "PBS/items_kanto.txt","PBS/map_metadata_kanto.txt",KANTO_PLUGIN,REGION_START_PLUGIN}


def identity(ci):
    def git(*args):
        return subprocess.check_output(["git",*args],cwd=ROOT,text=True).strip()
    head = git("rev-parse","HEAD")
    if not re.fullmatch("[0-9a-f]{40}",head) or head == PREVIOUS:
        raise ValueError("Invalid Celadon recipe checkout")
    if ci:
        return head,head
    if not RELEASE.is_file() or RELEASE.is_symlink() or git("status","--porcelain","--untracked-files=no"):
        raise ValueError("Use a receita oficial de Celadon, sem alterações locais.")
    desc = json_file(RELEASE)
    product = desc.get("product_revision")
    if ((desc.get("schema"),desc.get("stage"),desc.get("predecessor_recipe")) != (1,STAGE,PREVIOUS_RECIPE)
            or not isinstance(product,str) or not re.fullmatch("[0-9a-f]{40}",product)
            or product in (head,PREVIOUS)):
        raise ValueError("A receita de Celadon não aponta para uma revisão funcional válida.")
    subprocess.run(["git","merge-base","--is-ancestor",PREVIOUS,product],cwd=ROOT,check=True)
    subprocess.run(["git","merge-base","--is-ancestor",product,head],cwd=ROOT,check=True)
    allowed = {"data/regions/android-k06-services-recipe.json","docs/ANDROID_K06_CELADON_PELA_FONTE.md",
               ".github/workflows/android-k06-services-release.yml"}
    if set(git("diff","--name-only",product,head).splitlines())-allowed:
        raise ValueError("A receita difere da revisão funcional verificada de Celadon.")
    return product,head


def candidate_paths(root, staged, old):
    """Accept known Kanto files, plus only added donor graphics in approved folders."""
    prior = json_file(checked_file(root,INSTALL))["maps"]
    authored = {**prior,**{str(sid):mid for sid,mid in CANDIDATES.items()}}
    changed_maps = {f"Data/Map{authored[str(sid)]:03}.rxdata"
                    for sid in (114,*STORE,*CANDIDATES)}
    tracked = {*old["files"],*old.get("immutable",{})}
    graphics = set()
    for folder,prefix in (("Tilesets","FRLG_Preview_"),("Autotiles","FRLG_Preview_"),
                          ("Characters","FRLG_Pilot_")):
        for file in (staged/"Graphics"/folder).glob(prefix+"*.png"):
            name = file.relative_to(staged).as_posix()
            if name in tracked:
                continue
            if file.resolve()!=file or source.checked_row(root/name) is not None:
                raise ValueError("Gráfico novo de Celadon coincide com um arquivo local.")
            graphics.add(name)
    names = changed_maps|graphics|SHARED|CACHE|{INSTALL,UPDATER,BUILD}
    if any(not safe_path(name) or name in old.get("immutable",{}) for name in names):
        raise ValueError("Celadon faria uma gravação fora do inventário autorizado.")
    return names,changed_maps


def manifest_delta(root,staged,old,names):
    delta,previous = {},{}
    for name in sorted(names):
        before = source.checked_row(root/name)
        if before != old["files"].get(name):
            raise ValueError("Arquivo local mudou desde a conferência de Celadon: "+name)
        row = source.manifest_row(checked_file(staged,name))
        if row != before:
            delta[name] = row
            previous[name] = before
    return delta,previous


def verify_installed(game, installed):
    stamp = json_file(checked_file(game,INSTALL))
    positions = stamp.get("maps",{})
    keys = set(json_file(KANTO)["maps"])|{str(i) for i in CANDIDATES}
    if (set(positions)!=keys or len(set(positions.values()))!=182
            or any(positions[str(sid)]!=mid for sid,mid in CANDIDATES.items())
            or stamp.get("content_stage")!=STAGE):
        raise ValueError("O registro final do Kanto de Celadon não confere.")
    hoenn = json_file(checked_file(game,"Data/blue-hoenn-install.json"))["maps"]
    if len(hoenn)!=199 or set(hoenn.values())&set(positions.values()):
        raise ValueError("O registro final de Hoenn mudou ou colidiu com Kanto.")
    combined = {*positions.values(),*hoenn.values()}
    infos,paths = inventory(game)
    if not combined <= set(infos)&set(paths):
        raise ValueError("Mapas ausentes no registro final.")
    for mid,path in paths.items():
        if source.checked_row(path) != installed["files"].get(path.relative_to(game).as_posix()):
            raise ValueError(f"Mapa local final incompatível: {mid}")
    if checked_file(game,"Data/blue-kanto-ready.txt").read_text("ascii").strip()!=f"BLUE_KANTO_READY_V1,182,{positions['7']}":
        raise ValueError("Marcador final de acesso a Kanto incompatível.")
    for name in {INSTALL,*SHARED,*CACHE,BUILD,UPDATER}:
        if source.checked_row(game/name)!=installed["files"].get(name):
            raise ValueError("Inventário final de Celadon não confere: "+name)
    cache = checked_file(game,"Data/PluginScripts.rxdata").read_bytes()
    for rel in (KANTO_PLUGIN,REGION_START_PLUGIN,HOENN_PLUGIN):
        compiled_region(cache,Path(rel).name,checked_file(game,rel).read_bytes())


def holder_for(root,work):
    return source.work_holder(root,PREVIOUS,work or root.parent/(root.name+"-Compilar-Celadon"))


def stage_update(root,holder,old,target,recipe,ci):
    original = pinned_source() if ci else prepare()
    staged = holder/"game"
    before = source.digest(checked_file(root,MARKER))
    holder.mkdir(parents=True,exist_ok=False)
    try:
        report = stage_services(original,root,staged,summarize(original,json_file(KANTO)),android_base=old)
        cfg = staged/"mkxp.json"
        cfg.write_text(source.compiler_config(cfg.read_text("utf-8-sig"),PROFILE),encoding="utf8")
        if not save_namespace_valid(staged,PROFILE) or (ci and (staged/SAVE).exists()):
            raise ValueError("A cópia para compilar não isolou o perfil de save.")
        source.write_compiler_ini(staged)
        (staged/REGION_START_PLUGIN).write_bytes((ROOT/"scripts/battle_polish/RegionStart.rb").read_bytes())
        shutil.copyfile(ROOT/"scripts/android/update_client.py",staged/UPDATER)
        request_compile(staged)
        report.update(root=str(root),target=target,release_recipe=recipe,before_update_sha256=before)
        if ci:
            report["sentinel"] = source.digest(checked_file(root,SAVE))
        (holder/"proof.json").write_text(json.dumps(report,sort_keys=True),encoding="utf8")
    except BaseException:
        if holder.exists():
            shutil.rmtree(holder)
        raise
    if source.digest(checked_file(root,MARKER))!=before:
        raise ValueError("O inventário da instalação mudou durante a montagem.")
    print("KANTO_K06_CELADON_ANDROID_TRANSACTION_STAGED_OK",flush=True)


def finish_update(root,holder,old,report,ci,interrupt=False):
    staged = holder/"game"
    before = checked_file(root,MARKER).read_bytes()
    unchanged = verify_clone(root,staged,report,old)
    stamp = json_file(checked_file(staged,INSTALL))
    names,changed_maps = candidate_paths(root,staged,old)
    stamp["content_stage"] = STAGE
    recorded = {rel.replace(chr(92),"/"):sha for rel,sha in stamp["installed_sha256"].items()}
    for name in names-{INSTALL,BUILD,UPDATER,*CACHE}:
        recorded[name] = source.digest(checked_file(staged,name))
    stamp["installed_sha256"] = recorded
    (staged/INSTALL).write_text(json.dumps(stamp,sort_keys=True)+"\n",encoding="utf8")
    display = checked_file(staged,BUILD)
    target = report["target"]
    current = display.read_text("utf8")
    updated,n = re.subn(r"(?m)^Revision: "+PREVIOUS+r"$","Revision: "+target,current)
    if n!=1:
        raise ValueError("A edição funcional anterior não foi autenticada.")
    display.write_text(updated,encoding="utf8")
    delta,expected = manifest_delta(root,staged,old,names)
    if not (changed_maps|CACHE|{INSTALL,BUILD,UPDATER}) <= delta.keys():
        raise ValueError("Nem todos os arquivos de Celadon mudaram como esperado.")
    files = {**old["files"],**delta}
    recipe = report["release_recipe"]
    proof = {**source.installed_provenance(files,recipe),"product_revision":target,"stage":STAGE,
             "mode":"k06-services-ci" if ci else "pinned-source-local",
             "previous_inventory_sha256":old["source_update"]["inventory_sha256"]}
    installed = {**old,"files":files,"revision":target,"source_update":proof}

    def postcheck(path):
        verify_installed(path,installed)
        if ci and source.digest(checked_file(path,SAVE))!=report["sentinel"]:
            raise ValueError("O save sintético foi alterado.")
        if interrupt:
            # Called only on the disposable CI installation after staging.
            # Abrupt process death leaves a durable journal on disk.
            os._exit(77)

    source.commit_local(root,staged,delta,json.dumps(installed,sort_keys=True).encode("utf8"),
        holder/"backup",verify=postcheck,before_marker=before,baseline=old["revision"],before_files=expected)
    if read_installed(root)!=installed:
        raise ValueError("O recibo de Celadon não foi publicado localmente.")
    print("KANTO_K06_CELADON_ANDROID_TRANSACTION_COMMITTED_OK:"+json.dumps(
        {"files":len(delta),"unchanged_maps":unchanged,"hoenn":199,"physical_android":False,
         "target":target,"recipe":recipe}),flush=True)


def workflow(root,work=None,apply=False,ci=False,interrupt=False):
    root = root.expanduser().resolve(strict=True)
    if ci:
        require_ci()
        if root!=CI_GAME:
            raise ValueError("Unexpected Android CI game directory")
    if interrupt and not (ci and apply):
        raise ValueError("Transaction interruption is only for disposable CI")
    target,recipe = identity(ci)
    holder = holder_for(root,work)
    recovered = source.recover_source_install(root,holder.parent,apply)
    installed = read_installed(root)
    if installed["revision"]==target:
        proof = installed.get("source_update") or {}
        digest = source.installed_provenance(installed["files"],recipe)["inventory_sha256"]
        if (proof.get("stage"),proof.get("product_revision"),proof.get("recipe_revision"),
            proof.get("inventory_sha256"),proof.get("mode")) != (STAGE,target,recipe,digest,
                "k06-services-ci" if ci else "pinned-source-local"):
            raise ValueError("O recibo de instalação de Celadon não confere.")
        verify_installed(root,installed)
        print("KANTO_K06_CELADON_ANDROID_TRANSACTION_IDEMPOTENT_OK",flush=True)
        return
    old = verify_predecessor(root)
    if not apply:
        print("Celadon está disponível pela fonte. Use --source --source-stage k06-services --update.")
        return
    staged = holder/"game"
    if not holder.exists():
        stage_update(root,holder,old,target,recipe,ci)
    else:
        report = json_file(checked_file(holder,"proof.json"))
        if (report.get("root"),report.get("target"),report.get("release_recipe"),report.get("before_update_sha256")) != (
                str(root),target,recipe,source.digest(checked_file(root,MARKER))):
            raise ValueError("A cópia para compilar não corresponde a esta instalação.")
        if recovered=="rolled_back":
            print("KANTO_K06_CELADON_ANDROID_TRANSACTION_RECOVERED_OK",flush=True)
        if (staged/"Data/blue-android-compiled.txt").is_file():
            # Restore the exact candidate marker after an interrupted commit
            # before rechecking all registers and compiled cache hashes.
            stamp = json_file(checked_file(staged,INSTALL))
            if stamp.get("content_stage")==STAGE:
                stamp["content_stage"] = STAGE_LOCAL
                (staged/INSTALL).write_text(json.dumps(stamp,sort_keys=True)+"\n",encoding="utf8")
                display = checked_file(staged,BUILD)
                display.write_text(display.read_text("utf8").replace("Revision: "+target,"Revision: "+PREVIOUS,1),encoding="utf8")
            finish_update(root,holder,old,report,ci,interrupt=interrupt)
            return
    print("Abra somente esta cópia descartável no JoiPlay para compilar:")
    print(staged/"Game.exe")
    print("Depois de compilar, feche o JoiPlay e execute exatamente o mesmo comando.")


if __name__=="__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--game-dir",required=True,type=Path)
    p.add_argument("--work-dir",type=Path)
    p.add_argument("--source-workflow",action="store_true",required=True)
    p.add_argument("--update",action="store_true")
    p.add_argument("--ci",action="store_true",help=argparse.SUPPRESS)
    p.add_argument("--interrupt-test",action="store_true",help=argparse.SUPPRESS)
    a = p.parse_args()
    workflow(a.game_dir,a.work_dir,a.update,a.ci,a.interrupt_test)
