"""Read-only preflight and direct-source fetch for an existing JoiPlay install.

Unlike an ordinary patch this distributes no packed game data. A fetched
archive is a local input, not an installed update or proof of compilation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
import subprocess
import re
from pathlib import PurePosixPath
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts/regions"))

from scripts.android.update_client import MARKER, read_installed, safe_path
from scripts.regions.k05_contract import published_destinations
from ensure_source import prepare, SOURCE_URL


def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for data in iter(lambda:stream.read(1024*1024),b""):
            h.update(data)
    return h.hexdigest()


def protected_map_inventory(root,installed):
    root=root.resolve()
    paths={}
    known={}
    for region,count in (("kanto",None),("hoenn",199)):
        rel=f"Data/blue-{region}-install.json"
        f=root/rel
        if f.is_symlink() or not f.is_file() or not f.resolve().is_relative_to(root):
            raise ValueError(f"Use uma instalação integrada que contenha {region.title()}.")
        proof=json.loads(f.read_text("utf8"))
        maps=proof.get("maps")
        if not isinstance(maps,dict) or (count is not None and count!=len(maps)):
            raise ValueError(f"Registro inválido da região {region}.")
        if len(set(maps.values()))!=len(maps) or any(type(mid) is not int or not 0<mid<1000 for mid in maps.values()):
            raise ValueError(f"MapIDs duplicados ou inválidos de {region}.")
        if region=="kanto" and len(maps) not in (156,160,165,178):
            raise ValueError("Esta revisão de Kanto não tem uma migração K05 verificada.")
        for mid in maps.values():
            label=f"Data/Map{mid:03d}.rxdata"
            entry=root/label
            record=installed["files"].get(label,{})
            if (label in paths or entry.is_symlink() or not entry.is_file()
                    or not entry.resolve().is_relative_to(root)
                    or digest(entry)!=record.get("sha256")):
                raise ValueError(f"Mapa local ausente ou alterado; atualização não iniciada: {label}")
            paths[label]=record["sha256"]
        known[region]=maps
    kanto=known["kanto"]
    proposed=published_destinations()
    if len(kanto)==178:
        if any(kanto.get(sid)!=i for sid,i in proposed.items()):
            raise ValueError("Registro local K05 usa MapIDs inesperados.")
    else:
        for map_id in proposed.values():
            candidate=root/f"Data/Map{map_id:03d}.rxdata"
            if candidate.exists() or candidate.is_symlink():
                raise ValueError(f"MapID de Lavender em uso: {map_id}. Nenhum arquivo foi alterado.")
    return known,paths


def preflight(root):
    root=root.expanduser().resolve()
    installed=read_installed(root)
    if installed["channel"]!="multiregion":
        raise ValueError("Este fluxo é só para a edição Android multirregional existente.")
    known,paths=protected_map_inventory(root,installed)
    return {"status":"SOURCE_UPDATE_PREFLIGHT","current_revision":installed["revision"],
            "kanto_maps":len(known["kanto"]),"hoenn_maps":len(known["hoenn"]),
            "present_map_hashes_verified":len(paths),"source":"Essentials FRLG",
            "pinned_source_url":SOURCE_URL,"installed_changed":False,
            "compile_verified":False,"updated":False}



def clone_verified_install(root,stage,installed):
    """Copy only verified package files and never browse/copy any save folder."""
    old=root.resolve()
    stage=stage.resolve()
    files={**installed["files"],**installed.get("immutable",{})}
    if stage.exists() or stage.is_relative_to(old) or old.is_relative_to(stage):
        raise ValueError("Escolha uma pasta separada e vazia para a compilação.")
    stage.mkdir(parents=True,exist_ok=False)
    try:
        for name,row in files.items():
            p=PurePosixPath(name)
            if (not p.parts or p.is_absolute() or p.as_posix()!=name or "\\" in name or ":" in name or
                any(part.lower() in (".","..","save","saves","backup","backups") for part in p.parts)
                or p.suffix.lower() in (".sav",".rxsave") or p.name.lower()=="game.rxdata"
                or p.name.lower().startswith(("game_","lastsave","autosave"))):
                raise ValueError(f"Caminho não permitido no inventário Android: {name}")
            origin=old/name
            if (origin.resolve()!=origin or not origin.is_file() or
                origin.stat().st_size!=row.get("size") or digest(origin)!=row.get("sha256")):
                raise ValueError(f"Arquivo local diverge do pacote instalado: {name}")
            out=stage/name
            out.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(origin,out)
            if digest(out)!=row["sha256"]:
                raise ValueError(f"Arquivo mudou durante a cópia: {name}")
        (stage/MARKER).write_text(json.dumps(installed),encoding="utf8")
    except Exception:
        shutil.rmtree(stage)
        raise


def stage_local(root):
    """Prepare sandboxed assets, leave public revision markers untouched."""
    from install_kanto import migrate_existing, verify_installed
    from scripts.android.package import request_compile, REGION_START_PLUGIN
    from qa_k04_migration import isolated_config, save_namespace_valid
    root=root.resolve()
    proof=preflight(root)
    if proof["kanto_maps"]==178:
        raise ValueError("Lavender já consta nesta instalação.")
    installed=read_installed(root)
    target=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip()
    if not re.fullmatch("[0-9a-f]{40}",target):
        raise ValueError("A receita local não está vinculada a uma revisão Git.")
    revision=installed["revision"]
    if len(revision)!=40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("Revisão Android local inválida.")
    holder=(ROOT/".blue-work/android-source-update"/revision).resolve()
    if holder.exists() or holder.is_relative_to(root) or root.is_relative_to(holder):
        raise ValueError("Use uma pasta de preparação separada e vazia.")
    game=holder/"game"
    pristine=holder/"mkxp.original.json"
    app="Kanto Android Source Build"
    clone_verified_install(root,game,installed)
    try:
        source=prepare()
        old_regions,old_maps=protected_map_inventory(root,installed)
        old_hoenn={f"Data/Map{i:03d}.rxdata" for i in old_regions["hoenn"].values()}
        gameconf=game/"mkxp.json"
        # The staged Kanto importer must not inherit a user save namespace.
        # The importer uses the same compiled base and never touches saves.
        original_conf=gameconf.read_bytes()
        migrated=migrate_existing(game,source,holder/"pilot",True)
        if migrated["maps"]!=178 or verify_installed(game)["maps"]!=178:
            raise ValueError("A migração local não instalou os 178 mapas previstos.")
        if any(digest(game/p)!=old_maps[p] for p in old_hoenn):
            raise ValueError("A preparação tentou alterar um mapa de Hoenn.")
        shutil.copyfile(ROOT/"scripts/battle_polish/RegionStart.rb",game/REGION_START_PLUGIN)
        gameconf.write_text(isolated_config(original_conf.decode("utf-8-sig"),app),encoding="utf8")
        pristine.write_bytes(original_conf)
        if not save_namespace_valid(game,app):
            raise ValueError("Não foi possível isolar o perfil da compilação.")
        request_compile(game)
        proof.update(status="SOURCE_UPDATE_STAGED_AWAITING_COMPILER",staged_game=str(game),
                     pinned_source_prepared_locally=True,protected_hoenn_maps=len(old_hoenn),target_revision=target)
        (holder/"proof.json").write_text(json.dumps(proof,ensure_ascii=False),encoding="utf8")
    except Exception:
        shutil.rmtree(holder)
        raise
    return proof


def manifest_row(path):
    return {"size":path.stat().st_size,"sha256":digest(path)}


def local_delta(root,staged,old,installed_kanto):
    """No deletions or overwrites of a Hoenn/foreign map are possible."""
    candidate_maps={int(v) for v in installed_kanto["maps"].values()}
    written={k.replace("\\","/") for k in installed_kanto["installed_sha256"]}
    names=set(old["files"]) | {k for k in written if safe_path(k)}
    changed={}
    for name in sorted(names):
        if not safe_path(name):
            raise ValueError(f"Caminho não aceito no inventário de atualização: {name}")
        orig,source=root/name,staged/name
        if source.is_symlink() or source.resolve()!=source or not source.is_file():
            raise ValueError(f"A compilação local perdeu um arquivo: {name}")
        meta=manifest_row(source)
        previous=old["files"].get(name)
        if previous==meta:
            continue
        m=re.fullmatch(r"Data/Map(\d{3})\.rxdata",name)
        if (m and int(m[1]) not in candidate_maps) or (
                not m and name not in written and not name.startswith("Data/") and
                name!="Plugins/ZZZZ Blue Story and Presentation/RegionStart.rb"):
            raise ValueError(f"Rejeitada modificação fora de Kanto: {name}")
        if orig.resolve()!=orig or (previous and (not orig.is_file() or manifest_row(orig)!=previous)) or (
                previous is None and orig.exists()):
            raise ValueError(f"Arquivo original mudou desde a auditoria: {name}")
        changed[name]=meta
    return changed


def atomic_file(path, data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix=".k05-source-",dir=path.parent)
    try:
        with os.fdopen(fd,"wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
        os.replace(temp,path)
    finally:
        Path(temp).unlink(missing_ok=True)


def commit_local(root,staged,changed,new_manifest,backup):
    """Apply only already-verified files. Hold a local lock and commit version last."""
    root,staged,backup=root.resolve(),staged.resolve(),backup.resolve()
    lock=root/".blue-k05-local-update"
    lock.mkdir(exist_ok=False)
    backups={}
    applied=[]
    safe_recovery=False
    try:
        backup.mkdir(exist_ok=False)
        for name in [*changed,MARKER]:
            orig=root/name
            if orig.resolve()!=orig:
                raise ValueError(f"Caminho de destino inseguro: {name}")
            if orig.is_file():
                prior=backup/name
                prior.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(orig,prior)
                backups[name]=prior
            else:
                backups[name]=None
        for name in [*changed,MARKER]:
            data=(staged/name).read_bytes() if name!=MARKER else new_manifest
            if name!=MARKER and hashlib.sha256(data).hexdigest()!=changed[name]["sha256"]:
                raise ValueError(f"O arquivo compilado mudou antes de gravar: {name}")
            atomic_file(root/name,data)
            applied.append(name)
        safe_recovery=True
        return len(changed)
    except Exception:
        for name in reversed(applied):
            prior=backups[name]
            if prior is not None:
                atomic_file(root/name,prior.read_bytes())
            else:
                (root/name).unlink(missing_ok=True)
        safe_recovery=True
        raise
    finally:
        # Preserve the lock and backup if rollback itself fails.
        if safe_recovery:
            lock.rmdir()


def finish_local(root,revision,apply=False):
    from scripts.android.package import verify_regions,fingerprint
    from scripts.android.k05_package_contract import verify_registry
    root=root.resolve()
    old=read_installed(root)
    original=old["revision"]
    if len(original)!=40 or not re.fullmatch("[0-9a-f]{40}",original) or not re.fullmatch("[0-9a-f]{40}",revision):
        raise ValueError("Identidades de revisão inválidas.")
    if revision==original:
        raise ValueError("A revisão de origem e destino não podem ser iguais.")
    holder=(ROOT/".blue-work/android-source-update"/original).resolve()
    staged=holder/"game"
    if not staged.is_dir() or not holder.is_relative_to(ROOT.resolve()) or holder.is_relative_to(root):
        raise ValueError("Nenhuma cópia local isolada encontrada.")
    header=json.loads((holder/"proof.json").read_text("utf8"))
    if (header.get("status")!="SOURCE_UPDATE_STAGED_AWAITING_COMPILER" or
            header.get("current_revision")!=original or header.get("target_revision")!=revision or read_installed(staged)!=old):
        raise ValueError("A instalação original não corresponde à cópia preparada.")
    marker=staged/"Data/blue-android-compiled.txt"
    if not marker.is_file() or marker.read_text()!=fingerprint(staged):
        raise ValueError("A cópia ainda não foi compilada. Nenhum arquivo instalado foi alterado.")
    verify_regions(staged)
    if not verify_registry(lambda name:(staged/name).read_bytes()):
        raise ValueError("Os dados compilados não contêm K05.")
    regions,old_paths=protected_map_inventory(root,old)
    old_hoenn={f"Data/Map{i:03d}.rxdata" for i in regions["hoenn"].values()}
    if any(digest(staged/name)!=old_paths[name] for name in old_hoenn):
        raise ValueError("Mudança em mapa existente de Hoenn, nada instalado.")
    kanto=json.loads((staged/"Data/blue-kanto-install.json").read_text("utf8"))
    build=staged/"Data/blue-mobile-build.txt"
    old_build=build.read_text("utf8")
    fixed,n=re.subn(r"(?m)^Revision: [0-9a-f]{40}$","Revision: "+revision,old_build)
    if n!=1:
        raise ValueError("Metadados Android da compilação incompletos.")
    build.write_text(fixed,encoding="utf8")
    changed=local_delta(root,staged,old,kanto)
    if not {f"Data/Map{i:03d}.rxdata" for i in published_destinations().values()}<=changed.keys():
        raise ValueError("A atualização está incompleta; faltam mapas de Lavender.")
    new={**old,"revision":revision,"files":{**old["files"],**changed}}
    if apply:
        commit_local(root,staged,changed,json.dumps(new,sort_keys=True).encode("utf8"),holder/"backup")
    return {"status":"SOURCE_UPDATE_APPLIED" if apply else "SOURCE_UPDATE_READY",
            "from_revision":original,"to_revision":revision,"compile_verified":True,
            "files_changed":len(changed),"hoenn_maps_preserved":len(old_hoenn),"updated":apply}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir",type=Path,required=True)
    parser.add_argument("--fetch-source",action="store_true",
                        help="Baixar a fonte fixada no cache do projeto, sem alterar o jogo")
    parser.add_argument("--stage",action="store_true",
                        help="Preparar uma cópia separada; nunca modificar a instalação original")
    parser.add_argument("--finish",metavar="REVISAO",help="Conferir a compilação local para esta revisão")
    parser.add_argument("--apply-local",action="store_true",help="Confirmar instalação local após a conferência")
    args=parser.parse_args(argv)
    if args.apply_local and not args.finish:
        parser.error("--apply-local exige a revisão com --finish")
    if args.finish:
        print(json.dumps(finish_local(args.game_dir,args.finish,args.apply_local),ensure_ascii=False,indent=2))
        return
    if args.stage:
        print(json.dumps(stage_local(args.game_dir),ensure_ascii=False,indent=2))
        return
    result=preflight(args.game_dir)
    if args.fetch_source:
        game=args.game_dir.resolve()
        cache=(ROOT/".blue-work/frlg-source").resolve()
        if cache.is_relative_to(game):
            raise ValueError("O cache da fonte não pode ficar na instalação.")
        prepare()
        result["pinned_source_prepared_locally"]=True
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
