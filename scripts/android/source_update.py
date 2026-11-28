"""Read-only preflight and direct-source fetch for an existing JoiPlay install.

Unlike an ordinary patch this distributes no packed game data. A fetched
archive is a local input, not an installed update or proof of compilation.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
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

PRODUCT_REVISION="0eaf9401b2d9e828e8549f7c7fea28c5de748157"
RECIPE_PATHS=frozenset({
    ".github/workflows/android-k05-source-update.yml",
    "scripts/android/source_update.py",
    "scripts/android/update_client.py",
    "scripts/regions/ensure_source.py",
    "tests/test_android_source_update.py",
    "docs/ANDROID_KANTO_ATUALIZACAO_PELA_FONTE.md",
})


def recipe_revision():
    """Keep user-facing Kanto product identity separate from tooling lineage."""
    def git(*argv):
        return subprocess.check_output(["git",*argv],cwd=ROOT,text=True).strip()
    head=git("rev-parse","HEAD")
    if not re.fullmatch("[0-9a-f]{40}",head) or git("status","--porcelain","--untracked-files=no"):
        raise ValueError("Use uma cópia da receita fixada, sem alterações locais nos arquivos do projeto.")
    subprocess.run(["git","merge-base","--is-ancestor",PRODUCT_REVISION,head],cwd=ROOT,check=True)
    changed=set(git("diff","--name-only",PRODUCT_REVISION,head).splitlines())
    if changed-RECIPE_PATHS:
        raise ValueError("A receita não corresponde aos arquivos funcionais da edição K05.")
    return head


def installed_provenance(files,recipe):
    inventory=json.dumps(files,sort_keys=True,separators=(",",":")).encode("utf8")
    return {"mode":"pinned-source-local","product_revision":PRODUCT_REVISION,
            "recipe_revision":recipe,"inventory_sha256":hashlib.sha256(inventory).hexdigest()}



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


def compiler_config(original, app):
    from qa_k04_migration import isolated_config
    config=json.loads(isolated_config(original,app))
    # Do not inherit a machine-specific root or alternate entry point from the
    # released runtime. All paths below refer only to the disposable copy.
    config.update(gameFolder=".",execName="Game",customScript="",rgssVersion=1)
    return json.dumps(config,ensure_ascii=True,indent=2)+"\n"


def write_compiler_ini(game):
    """ASCII native bootstrap is only for the disposable compile copy."""
    path=game/"Game.ini"
    path.write_bytes(
        b"[Game]\r\nLibrary=RGSS104E.dll\r\nScripts=Data\\Scripts.rxdata\r\n"
        b"Title=Kanto Android Source Build\r\n"
    )


def work_holder(root, revision, work=None):
    """Use a separate exact checkpoint, optionally visible to Android apps."""
    if not re.fullmatch(r"[0-9a-f]{40}",revision):
        raise ValueError("Revisão Android local inválida.")
    home=ROOT/".blue-work/android-source-update" if work is None else Path(work).expanduser()
    root,home=root.resolve(),home.resolve()
    holder=home/revision
    if (home==ROOT.resolve() or ROOT.resolve().is_relative_to(home) or
        home.is_relative_to(root) or root.is_relative_to(home) or holder.resolve()!=holder):
        raise ValueError("A preparação deve ficar em uma pasta separada do jogo.")
    return holder


def stage_local(root,work=None):
    """Prepare sandboxed assets, leave public revision markers untouched."""
    from install_kanto import migrate_existing, verify_installed
    from scripts.android.package import request_compile, REGION_START_PLUGIN
    from qa_k04_migration import save_namespace_valid
    root=root.resolve()
    proof=preflight(root)
    if proof["kanto_maps"]==178:
        raise ValueError("Lavender já consta nesta instalação.")
    installed=read_installed(root)
    recipe=recipe_revision()
    revision=installed["revision"]
    holder=work_holder(root,revision,work)
    if holder.exists():
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
        gameconf.write_text(compiler_config(original_conf.decode("utf-8-sig"),app),encoding="utf8")
        pristine.write_bytes(original_conf)
        if not save_namespace_valid(game,app):
            raise ValueError("Não foi possível isolar o perfil da compilação.")
        write_compiler_ini(game)
        # The existing manifest tracks this authored updater as a mutable
        # file. Install it only with the verified game transaction.
        if "ATUALIZAR-ANDROID.py" not in installed["files"]:
            raise ValueError("O atualizador local não é rastreado por esta versão.")
        shutil.copyfile(ROOT/"scripts/android/update_client.py",game/"ATUALIZAR-ANDROID.py")
        request_compile(game)
        proof.update(status="SOURCE_UPDATE_STAGED_AWAITING_COMPILER",staged_game=str(game),installed_root=str(root),
                     pinned_source_prepared_locally=True,protected_hoenn_maps=len(old_hoenn),target_revision=PRODUCT_REVISION,recipe_revision=recipe)
        (holder/"proof.json").write_text(json.dumps(proof,ensure_ascii=False),encoding="utf8")
    except Exception:
        shutil.rmtree(holder)
        raise
    return proof


def manifest_row(path):
    return {"size":path.stat().st_size,"sha256":digest(path)}


# Only databases affected by Kanto's own PBS and the shared plugin cache.
# The native compiler can rewrite unrelated PBS and compiled game tables. Do
# not install those side effects, and never ship the scratch boot hooks.
K05_COMPILED={
    "Data/PluginScripts.rxdata","Data/encounters.dat","Data/trainers.dat",
    "Data/trainer_types.dat","Data/map_metadata.dat","Data/map_connections.dat","Data/items.dat",
}
K05_RUNTIME={
    "ATUALIZAR-ANDROID.py",
    "Data/blue-kanto-install.json","Data/blue-kanto-ready.txt","Data/blue-kanto-start.txt",
    "Data/blue-mobile-build.txt","Plugins/ZZZZ Blue Story and Presentation/RegionStart.rb",
}


def local_delta(root,staged,old,installed_kanto):
    """Select the regional write set, not incidental RPG Maker resaves."""
    candidate_maps={int(v) for v in installed_kanto["maps"].values()}
    written={k.replace(chr(92),"/") for k in installed_kanto["installed_sha256"]}
    names=written | K05_RUNTIME | K05_COMPILED
    # Foreign maps must not change even in the scratch build. Other unrelated
    # cache/PBS rewrites never enter the plan or the new installed inventory.
    for name,row in old["files"].items():
        m=re.fullmatch(r"Data/Map(\d{3})\.rxdata",name)
        if m and int(m[1]) not in candidate_maps:
            checked=staged/name
            if not checked.is_file() or checked.resolve()!=checked or manifest_row(checked)!=row:
                raise ValueError(f"Rejeitada modificação em mapa fora de Kanto: {name}")
    changed={}
    for name in sorted(names):
        m=re.fullmatch(r"Data/Map(\d{3})\.rxdata",name)
        if not safe_path(name) or (m and int(m[1]) not in candidate_maps):
            raise ValueError(f"Caminho não aceito no inventário de atualização: {name}")
        orig,source=root/name,staged/name
        if source.is_symlink() or source.resolve()!=source or not source.is_file():
            raise ValueError(f"A compilação local perdeu um arquivo: {name}")
        meta=manifest_row(source)
        previous=old["files"].get(name)
        if previous==meta:
            continue
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


RECOVERY_FILE=".blue-k05-recovery.json"
UPDATE_LOCK=".blue-k05-update.lock"


@contextmanager
def update_lock(root):
    """An OS lock releases on process death, without deleting its inode."""
    path=root/UPDATE_LOCK
    if path.resolve()!=path:
        raise ValueError("Trava da atualização não é um arquivo local.")
    with path.open("a+b") as stream:
        if os.name=="nt":
            import msvcrt
            stream.seek(0)
            try:
                msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            except OSError as exc:
                raise ValueError("Já há um atualizador usando esta instalação.") from exc
        else:
            import fcntl
            try:
                fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
            except OSError as exc:
                raise ValueError("Já há um atualizador usando esta instalação.") from exc
        yield


def checked_row(path):
    if path.resolve()!=path or (path.exists() and not path.is_file()):
        raise ValueError(f"Caminho de atualização inseguro: {path.name}")
    return manifest_row(path) if path.is_file() else None


def recovery_plan(root,*,record_marker=MARKER):
    path=root/RECOVERY_FILE
    if checked_row(path) is None:
        return None
    data=json.loads(path.read_text("utf8"))
    if (data.get("schema")!=1 or data.get("root")!=str(root) or not isinstance(data.get("rows"),dict)
            or record_marker not in data["rows"] or not isinstance(data.get("backup"),str)):
        raise ValueError("Registro de recuperação Android inválido.")
    return data


def recover_under_lock(root,backup_base,data,*,record_marker=MARKER):
    """Validate all files before restoring any; no saves enter the journal."""
    backup=Path(data["backup"])
    if (backup.resolve()!=backup or backup.parent!=backup_base.resolve().parent
            or not backup.name.startswith(backup_base.name+"-") or not backup.is_dir()):
        raise ValueError("Abra o atualizador com a mesma pasta de compilação para recuperar a instalação.")
    actions=[]
    states=[]
    rows=data["rows"]
    for name,versions in rows.items():
        if name!=record_marker and not safe_path(name):
            raise ValueError("Caminho inesperado no registro de recuperação.")
        target=root/name
        previous,new=versions["old"],versions["new"]
        stored=backup/name
        if checked_row(stored)!=previous:
            raise ValueError("Backup de recuperação diverge: "+name)
        now=checked_row(target)
        if now not in (previous,new):
            raise ValueError("Arquivo editado depois da interrupção: "+name)
        states.append(now==new)
        if now!=previous:
            actions.append((target,stored,previous))
    revision=checked_row(root/record_marker)
    if revision==rows[record_marker]["new"]:
        if not all(states):
            raise ValueError("A revisão mudou sem que todos os arquivos correspondam à atualização.")
        result="committed"
    elif revision==rows[record_marker]["old"]:
        for target,stored,previous in reversed(actions):
            if previous is None:
                target.unlink()
            else:
                atomic_file(target,stored.read_bytes())
        result="rolled_back"
    else:
        raise ValueError("Revisão desconhecida no registro de recuperação.")
    (root/RECOVERY_FILE).unlink()
    return result


def recover_source_install(root,work,apply):
    if not (root/RECOVERY_FILE).exists():
        return None
    if not apply:
        raise ValueError("Há uma atualização interrompida. Feche o JoiPlay e execute com --source --update.")
    with update_lock(root):
        receipt=recovery_plan(root)
        if receipt is None:
            return None
        original=receipt.get("baseline")
        if not isinstance(original,str):
            raise ValueError("Revisão de recuperação ausente.")
        result=recover_under_lock(root,work_holder(root,original,work)/"backup",receipt)
    if result=="rolled_back":
        print("[OK] Atualização interrompida restaurada. Retomando a instalação.",flush=True)
    return result


def commit_local(root,staged,changed,new_manifest,backup,verify=None,before_marker=None,baseline=None,*,record_marker=MARKER,before_files=None):
    """Persist backups and hashes before touching files; commit revision last."""
    if record_marker not in {MARKER,"Data/blue-kanto-install.json"}:
        raise ValueError("Marcador local de instalação não autorizado.")
    root,staged,backup=root.resolve(),staged.resolve(),backup.resolve()
    with update_lock(root):
        if recovery_plan(root,record_marker=record_marker) is not None:
            raise ValueError("Recupere a atualização anterior antes de gravar novos arquivos.")
        if before_marker is not None and (root/record_marker).read_bytes()!=before_marker:
            raise ValueError("O inventário mudou desde a conferência da instalação.")
        if before_files is not None:
            if set(before_files)!=set(changed) or any(
                    not safe_path(name) or checked_row(root/name)!=row for name,row in before_files.items()):
                raise ValueError("Os arquivos locais mudaram desde a conferência da atualização.")
        saved=Path(tempfile.mkdtemp(prefix=backup.name+"-",dir=backup.parent)).resolve()
        paths={}
        for name in (*changed,record_marker):
            if name!=record_marker and not safe_path(name):
                raise ValueError("Caminho de atualização não autorizado: "+name)
            orig=root/name
            previous=checked_row(orig)
            if previous is not None:
                atomic_file(saved/name,orig.read_bytes())
                if checked_row(saved/name)!=previous:
                    raise OSError("Backup local não confere: "+name)
            new=changed.get(name,{"size":len(new_manifest),"sha256":hashlib.sha256(new_manifest).hexdigest()})
            paths[name]={"old":previous,"new":new}
        receipt={"schema":1,"root":str(root),"backup":str(saved),"rows":paths,"baseline":baseline}
        atomic_file(root/RECOVERY_FILE,json.dumps(receipt,sort_keys=True).encode("utf8"))
        try:
            for name,meta in changed.items():
                data=(staged/name).read_bytes()
                if len(data)!=meta["size"] or hashlib.sha256(data).hexdigest()!=meta["sha256"]:
                    raise ValueError(f"O arquivo compilado mudou antes de gravar: {name}")
                atomic_file(root/name,data)
            if verify is not None:
                verify(root)
            atomic_file(root/record_marker,new_manifest)
        except Exception:
            recover_under_lock(root,backup,receipt,record_marker=record_marker)
            raise
        (root/RECOVERY_FILE).unlink()
        return len(changed)


def finish_local(root,revision,apply=False,work=None):
    from scripts.android.package import verify_regions,fingerprint
    from scripts.android.k05_package_contract import verify_registry
    root=root.resolve()
    recover_source_install(root,work,apply)
    before_marker=(root/MARKER).read_bytes()
    old=read_installed(root)
    original=old["revision"]
    if len(original)!=40 or not re.fullmatch("[0-9a-f]{40}",original) or not re.fullmatch("[0-9a-f]{40}",revision):
        raise ValueError("Identidades de revisão inválidas.")
    if revision==original or revision!=PRODUCT_REVISION:
        raise ValueError("A atualização é apenas para a revisão funcional K05, não para o SHA da receita.")
    recipe=recipe_revision()
    holder=work_holder(root,original,work)
    staged=holder/"game"
    if not staged.is_dir() or staged.resolve()!=staged:
        raise ValueError("Nenhuma cópia local isolada encontrada.")
    header=json.loads((holder/"proof.json").read_text("utf8"))
    if (header.get("status")!="SOURCE_UPDATE_STAGED_AWAITING_COMPILER" or
            header.get("installed_root")!=str(root) or header.get("staged_game")!=str(staged) or
            header.get("current_revision")!=original or header.get("target_revision")!=revision or
            header.get("recipe_revision")!=recipe or read_installed(staged)!=old):
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
    files={**old["files"],**changed}
    provenance=installed_provenance(files,recipe)
    new={**old,"revision":revision,"files":files,"source_update":provenance}
    if apply:
        commit_local(root,staged,changed,json.dumps(new,sort_keys=True).encode("utf8"),holder/"backup",verify=verify_regions,
                     before_marker=before_marker,baseline=original)
    return {"status":"SOURCE_UPDATE_APPLIED" if apply else "SOURCE_UPDATE_READY",
            "from_revision":original,"to_revision":revision,"compile_verified":True,
            "files_changed":len(changed),"hoenn_maps_preserved":len(old_hoenn),"updated":apply,
            **provenance}

def source_workflow(root,work=None,apply=False):
    """Run the update flow without any GitHub game ZIP or binary patch."""
    root=root.expanduser().resolve()
    work=work if work is not None else root.parent/(root.name+"-Compilar-K05")
    recover_source_install(root,work,apply)
    installed=read_installed(root)
    revision=installed["revision"]
    proof=preflight(root)
    if revision==PRODUCT_REVISION:
        stamp=installed.get("source_update",{})
        wanted=installed_provenance(installed["files"],stamp.get("recipe_revision"))
        if not (
            proof["kanto_maps"]==178 and stamp==wanted and
            re.fullmatch(r"[0-9a-f]{40}",str(wanted["recipe_revision"]))
        ):
            raise ValueError("A revisão local K05 não tem a prova de instalação pela fonte.")
        return {**proof,"status":"SOURCE_UPDATE_ALREADY_INSTALLED","compile_verified":True}
    holder=work_holder(root,revision,work)
    if not apply:
        return {**proof,"target_revision":PRODUCT_REVISION,"no_binary_zip":True}
    if not holder.exists():
        return stage_local(root,work)
    staged=holder/"game"
    if not staged.is_dir() or staged.resolve()!=staged:
        raise ValueError("Cópia de compilação incompleta; nenhum arquivo original alterado.")
    if not (staged/"Data/blue-android-compiled.txt").is_file():
        header=json.loads((holder/"proof.json").read_text("utf8"))
        if header.get("installed_root")!=str(root) or header.get("staged_game")!=str(staged):
            raise ValueError("A cópia preparada não pertence a esta instalação.")
        return header
    return finish_local(root,PRODUCT_REVISION,True,work)


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir",type=Path,required=True)
    parser.add_argument("--work-dir",type=Path,help="Pasta separada, acessível ao JoiPlay, para preparar a compilação")
    parser.add_argument("--source-workflow",action="store_true",help=argparse.SUPPRESS)
    parser.add_argument("--update",action="store_true",help=argparse.SUPPRESS)
    parser.add_argument("--fetch-source",action="store_true",
                        help="Baixar a fonte fixada no cache do projeto, sem alterar o jogo")
    parser.add_argument("--stage",action="store_true",
                        help="Preparar uma cópia separada; nunca modificar a instalação original")
    parser.add_argument("--finish",metavar="REVISAO",help="Conferir a compilação local para esta revisão")
    parser.add_argument("--apply-local",action="store_true",help="Confirmar instalação local após a conferência")
    args=parser.parse_args(argv)
    if args.source_workflow:
        result=source_workflow(args.game_dir,args.work_dir,args.update)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        if result["status"]=="SOURCE_UPDATE_STAGED_AWAITING_COMPILER":
            print("No JoiPlay, adicione temporariamente a cópia abaixo como um jogo separado.")
            print(str(Path(result["staged_game"])/"Game.exe"))
            print("Após a compilação fechar, feche o JoiPlay e execute o mesmo comando para atualizar.")
        return
    if args.apply_local and not args.finish:
        parser.error("--apply-local exige a revisão com --finish")
    if args.finish:
        print(json.dumps(finish_local(args.game_dir,args.finish,args.apply_local,args.work_dir),ensure_ascii=False,indent=2))
        return
    if args.stage:
        print(json.dumps(stage_local(args.game_dir,args.work_dir),ensure_ascii=False,indent=2))
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
