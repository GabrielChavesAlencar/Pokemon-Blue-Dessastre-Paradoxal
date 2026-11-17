#!/usr/bin/env python3
"""Sinnoh B09: build an isolated NATIVE QA copy from a verified B08 overlay.

ONLY local, user-provided game binaries. Never launch executables, upload
assets, include saves or modify source game/Data. QA copy is not cleared for
play until independent save-data isolation, future reservations and rights.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from audit_sinnoh_b06_technical_candidate import B00,B01,B04,B05,B06,load,verify_native_zip
from audit_sinnoh_b01_inventory import unpack as unpack_native
from build_sinnoh_b07_private_stage import CONTRACT as B07, check_current_game
from audit_sinnoh_b08_private_qa import (
    CONTRACT as B08, STAGE_LABEL,
    check_contract as check_b08_contract,latest_stage,read_stage,
    audit_files,qa_root)
from sinnoh_staging_transaction import ALLOWED,stage_root

CONTRACT=ROOT/"data/regions/sinnoh-b09-native-qa.json"
PRIVATE_DIR=".blue-work/sinnoh-b09-native-qa"
ALLOWED_FOLDERS=frozenset({
    "Data","Graphics","Audio","Fonts","Plugins","PBS","Scripts","System","Mods"
})
ROOT_FILE=re.compile(r"(?i:(?:Game\.exe|Game\.ini|Game\.rxproj|mkxp\.(?:conf|json)|"
                     r"[A-Za-z0-9_-]{1,80}\.(?:dll|so|pak|rgssad|rgss2a|rgss3a|json|ini)))\Z")
SENSITIVE_DIRS=frozenset({
    "saves","save","savedata","savedgames","userdata","cache","logs",
    "backups","backup","crash","crashes","temp","tmp",".git",
    ".blue-work","node_modules","__pycache__", ".venv"
})
SENSITIVE_FILE=re.compile(r"(?i:(?:save|autosave|backup|quick.?save|"
                          r"profile|account|user.?data|crash)[A-Za-z0-9 _.-]*|"
                          r".*\.(?:sav|save|rsv|bak|log|dmp|tmp))\Z")
SHA=re.compile(r"[0-9a-f]{64}\Z")
MAX_FILES=40000
MAX_SIZE=12*1024*1024*1024
MAX_SINGLE=3*1024*1024*1024

def blocked(message):
    raise ValueError("SINNOH_B09_BLOCKED: "+message)

def file_sha(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b""):
            digest.update(chunk)
    return digest.hexdigest()

def byte_sha(raw):
    return hashlib.sha256(raw).hexdigest()

def is_link(p):
    return p.is_symlink() or bool(getattr(p,"is_junction",lambda:False)())

def check_contract(c,b08,b07,b06,b00,b01,b04,b05):
    terrain=check_b08_contract(b08,b07,b06,b00,b01,b04,b05)
    expected={
      "schema":1,"region":"SINNOH","stage":"B09",
      "status":"PRIVATE_NATIVE_QA_CLONE_BUILDER_READY_B08_RUNTIME_EVIDENCE_PENDING",
      "b08_status":b08["status"],
      "b08_qa_folder":b08["qa_overlay_subdir"],
      "native_baseline_mapinfos_sha256":b01["mapinfos_sha256"],
      "native_baseline_tilesets_sha256":b01["tilesets_sha256"],
      "native_inventory_sha256":b07["native_inventory_zip_sha256"],
      "candidate_installed_sinnoh_ids":[x["candidate_destination_map_id"] for x in terrain],
      "sinnoh_empty_placeholder_ids":b07["excluded_empty_destinations"],
      "expected_installed_native_map_count":648,
      "expected_sinnoh_terrain_maps_in_clone":54,
      "expected_qa_clone_map_count":702,
      "expected_png_count":14,
      "clone_workspace_subdir":PRIVATE_DIR,
      "excludes_saved_games_and_user_profiles":True,
      "requires_full_stage_b07_and_b08_qa_match":True,
      "requires_b01_hash_and_physical_id_match":True,
      "requires_explicit_plan_sha_before_clone":True,
      "never_launches_executable":True,
      "cloned_executable_is_not_authorized_to_run":True,
      "runtime_save_isolation_verified":False,
      "future_reservations_verified":False,
      "third_party_asset_rights_verified":False,
      "native_b08_user_report_received":False,
      "game_exe_tested":False,"joiplay_tested":False,
      "can_install_live_game":False,"can_mark_native_playable":False,
      "r07_complete":False,"r08_complete":False,"r09_complete":False,
      "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0
    }
    if type(c) is not dict or c!=expected:
        blocked("contrato B09 ou aprovacoes alterados")
    return terrain

def check_qa_overlay(project,plan_sha,*,native_raw,expected_ids):
    """Verify every B08 QA file against its immutable B07 stage and B01."""
    project=Path(project).absolute()
    stage_files,dry=read_stage(project,STAGE_LABEL,plan_sha)
    root=qa_root(project)
    folder=root/f"qa-{plan_sha[:16]}"
    if is_link(folder) or not folder.is_dir() or not folder.resolve().is_relative_to(root.resolve()):
        blocked("overlay B08 ausente/inseguro; execute B08 primeiro")
    manifest_file=folder/"qa-overlay-manifest.json"
    if is_link(manifest_file) or not manifest_file.is_file() or manifest_file.stat().st_size>2_000_000:
        blocked("manifesto B08 ausente ou inseguro")
    manifest=json.loads(manifest_file.read_text("utf-8"))
    invalid={
      "schema":1,"region":"SINNOH","stage":"B08",
      "mode":"PRIVATE_QA_OVERLAY_NOT_RUNNABLE",
      "source_stage_sha256":plan_sha,
      "may_copy_into_live_game":False,"executable_included":False,
      "saves_included":False,"rights_verified":False,
      "r07_complete":False,"r08_complete":False,
      "game_exe_tested":False,"joiplay_tested":False,"phase_b_approved":0
    }
    if (type(manifest) is not dict or set(manifest)!=set(invalid)|{"files","verification"}
        or any(manifest.get(k)!=v for k,v in invalid.items())):
        blocked("manifesto B08 forjado ou nao correspondente ao B07")
    expected_rows=[
      {"path":p,"sha256":byte_sha(raw),"bytes":len(raw)}
      for p,raw in sorted(stage_files.items())]
    if manifest["files"]!=expected_rows:
        blocked("B08 nao coincide com o B07 validado")
    info=audit_files(stage_files,native_raw["MapInfos.rxdata"],
        native_raw["Tilesets.rxdata"],expected_ids)
    proof={k:info[k] for k in ("maps_validated","nonzero_terrain_cells",
       "pngs_verified","new_private_tileset_ids","all_png_references_resolved",
       "native_infos_preserved","native_tiles_preserved")}
    if manifest["verification"]!=proof:
        blocked("resumo de QA B08 difere dos dados reais")
    actual=set()
    for node in folder.rglob("*"):
        if is_link(node):blocked("overlay B08 contem junction/symlink")
        if node.is_file():actual.add(node.relative_to(folder).as_posix())
    if actual!=set(stage_files)|{"qa-overlay-manifest.json"}:
        blocked("overlay B08 contem arquivos extras/ausentes")
    for rel,raw in stage_files.items():
        p=folder/rel
        if is_link(p) or not p.is_file() or p.stat().st_size!=len(raw):
            blocked("overlay B08 ausente/inseguro: "+rel)
        if file_sha(p)!=byte_sha(raw):
            blocked("hash do overlay B08 alterado: "+rel)
    return stage_files,info

def secure_game_dir(project,source):
    project=Path(project).resolve()
    source=Path(source).absolute()
    if (is_link(source) or not source.is_dir()
        or source.resolve().is_relative_to(project)
        or project.is_relative_to(source.resolve())):
        blocked("origem do jogo invalida, symlink ou dentro do repositorio")
    if not (source/"Data").is_dir() or is_link(source/"Data"):
        blocked("a origem selecionada precisa conter game/Data")
    return source

def should_skip(relative):
    parts=relative.parts
    if any(x.casefold() in SENSITIVE_DIRS for x in parts):
        return True
    if SENSITIVE_FILE.fullmatch(parts[-1]):
        return True
    if parts[0] in ALLOWED_FOLDERS:
        return False
    return True if len(parts)!=1 or not ROOT_FILE.fullmatch(parts[0]) else False

def scan_native_game(project,game_dir):
    """Allowlisted local files; reject any reparse point/junction/symlink."""
    source=secure_game_dir(project,game_dir)
    entries=[];skipped=0;total=0
    for current,dirs,filenames in os.walk(source,topdown=True,followlinks=False):
        folder=Path(current)
        for dirname in dirs[:]:
            p=folder/dirname
            if is_link(p):blocked("game contem link ou junction: "+dirname)
            rel=p.relative_to(source)
            if should_skip(rel) or (len(rel.parts)==1 and rel.parts[0] not in ALLOWED_FOLDERS):
                dirs.remove(dirname)
        for filename in filenames:
            p=folder/filename
            if is_link(p) or not p.is_file():blocked("arquivo do jogo nao regular ou symlink")
            rel=p.relative_to(source)
            if should_skip(rel):
                skipped+=1
                continue
            s=p.stat().st_size
            if s>MAX_SINGLE:blocked("arquivo acima do limite de copia privada")
            total+=s
            if total>MAX_SIZE or len(entries)>=MAX_FILES:
                blocked("tamanho/contagem da copia acima do limite")
            entries.append({"path":rel.as_posix(),"bytes":s,"sha256":file_sha(p)})
    entries.sort(key=lambda x:x["path"])
    if not entries or "Data/MapInfos.rxdata" not in {r["path"] for r in entries}:
        blocked("arquivo MapInfos ausente no projeto local")
    if "Game.exe" not in {r["path"] for r in entries}:
        blocked("Game.exe nao encontrado na origem selecionada")
    folded=set()
    for row in entries:
        name=row["path"].casefold()
        if name in folded:blocked("nome de arquivo duplicado no Windows")
        folded.add(name)
    return entries,{"native_files":len(entries),"native_bytes":total,
                    "skipped_private_or_unrecognized_files":skipped}

def plan_clone(native_rows,overlay,stage_sha):
    """Deterministic plan only: no writes, no filenames of saves in report."""
    if not isinstance(stage_sha,str) or not SHA.fullmatch(stage_sha):
        blocked("SHA de stage invalido")
    rows=[dict(row,origin="NATIVE") for row in native_rows]
    originals={row["path"].casefold() for row in rows}
    overlay_paths=set()
    for rel,raw in sorted(overlay.items()):
        if not isinstance(raw,bytes) or not ALLOWED.fullmatch(rel):
            blocked("arquivo do B08 inesperado")
        if rel.casefold() in overlay_paths:blocked("overlay com caminho duplicado")
        overlay_paths.add(rel.casefold())
        if rel.casefold() in originals and rel not in (
              "Data/MapInfos.rxdata","Data/Tilesets.rxdata"):
            blocked("o overlay colidiria com arquivo existente: "+rel)
        rows.append({"path":rel,"bytes":len(raw),
                     "sha256":byte_sha(raw),"origin":"OVERLAY"})
    rows.sort(key=lambda x:(x["path"],x["origin"]))
    count=CounterOrigin(rows)
    if (count["OVERLAY"]!=len(overlay)
        or len([k for k in overlay if re.fullmatch(r"Data/Map[0-9]{3}\.rxdata",k)])!=54):
        blocked("overlay de Sinnoh incompleto")
    encoded=json.dumps({"stage_sha256":stage_sha,"files":rows},
        ensure_ascii=True,sort_keys=True,separators=(",",":")).encode("ascii")
    sha_value=byte_sha(encoded)
    return {"schema":1,"region":"SINNOH","stage":"B09",
            "status":"PRIVATE_NATIVE_CLONE_PLAN_NOT_EXECUTED",
            "stage_sha256":stage_sha,"plan_sha256":sha_value,
            "native_file_count":count["NATIVE"],
            "overlay_file_count":count["OVERLAY"],
            "total_copy_bytes":sum(v["bytes"] for v in rows),
            "files":rows,"live_game_modified":False,
            "game_exe_launched":False,"saves_copied":False,
            "native_playability_approved":False}

def CounterOrigin(rows):
    result={"NATIVE":0,"OVERLAY":0}
    for row in rows:result[row["origin"]]+=1
    return result

def clone_root(project):
    project=Path(project).absolute()
    work=stage_root(project).parent
    target=work/"sinnoh-b09-native-qa"
    if is_link(work) or is_link(target) or not target.resolve().is_relative_to(project.resolve()):
        blocked("destino nao e workspace privado dentro do projeto")
    return target

def clone_private(project,game_dir,overlay,plan,expected_sha):
    if expected_sha!=plan["plan_sha256"] or not SHA.fullmatch(expected_sha):
        blocked("SHA do planejamento nao corresponde; recusar clonagem")
    project=Path(project).absolute()
    source=secure_game_dir(project,game_dir)
    base=clone_root(project)
    target=base/f"native-{expected_sha[:16]}"
    if target.exists() or is_link(target):
        blocked("copia privada ja existe; recusar sobrescrita")
    base.mkdir(parents=True,exist_ok=True)
    temp=Path(tempfile.mkdtemp(prefix=".b09-native-",dir=base))
    try:
        for row in plan["files"]:
            rel=row["path"]
            if row["origin"]=="OVERLAY":
                data=overlay[rel]
                if byte_sha(data)!=row["sha256"]:
                    blocked("hash B08 mudou durante clonagem")
                target_file=temp/rel
                target_file.parent.mkdir(parents=True,exist_ok=True)
                with target_file.open("wb") as f:f.write(data)
            else:
                original=source/rel
                if is_link(original) or not original.is_file():
                    blocked("arquivo da instalacao foi substituido: "+rel)
                if (original.stat().st_size!=row["bytes"]
                    or file_sha(original)!=row["sha256"]):
                    blocked("jogo mudou entre dry-run e clonagem: "+rel)
                target_file=temp/rel
                target_file.parent.mkdir(parents=True,exist_ok=True)
                with original.open("rb") as reader,target_file.open("xb") as writer:
                    shutil.copyfileobj(reader,writer,1024*1024)
            if (target_file.stat().st_size!=row["bytes"]
                or file_sha(target_file)!=row["sha256"]):
                blocked("hash da copia privada nao corresponde: "+rel)
        receipt={
           "schema":1,"region":"SINNOH","stage":"B09",
           "mode":"PRIVATE_NATIVE_QA_CLONE_UNTESTED",
           "stage_sha256":plan["stage_sha256"],
           "plan_sha256":expected_sha,"files":plan["files"],
           "native_files_copied":plan["native_file_count"],
           "overlay_files_copied":plan["overlay_file_count"],
           "game_exe_in_clone":True,"game_exe_launched":False,
           "saves_copied":False,"save_isolation_verified":False,
           "DO_NOT_LAUNCH":True,
           "rights_verified":False,"r07_complete":False,
           "r08_complete":False,"r09_complete":False,
           "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
           "source_game_untouched":True
        }
        with (temp/"B09_PRIVATE_QA_MANIFEST.json").open("x",encoding="utf-8") as f:
            json.dump(receipt,f,indent=2,ensure_ascii=False);f.write("\n")
        (temp/"NAO_EXECUTAR_ANTES_DE_ISOLAR_SAVES.txt").write_text(
            "QA PRIVADO B09 - nao execute Game.exe: o caminho de saves ainda "
            "nao foi isolado. Este clone nao esta homologado nem pode ser distribuido.\n",
            encoding="utf-8")
        if target.exists() or is_link(target):
            blocked("copia concorrente detectada")
        temp.rename(target)
    except BaseException:
        if temp.exists():shutil.rmtree(temp)
        raise
    return {"status":"PRIVATE_NATIVE_QA_CLONE_CREATED_NOT_RUNNABLE_YET",
            "relative_path":target.relative_to(project).as_posix(),
            "native_file_count":plan["native_file_count"],
            "sinnoh_overlay_files":plan["overlay_file_count"],
            "map_ids_native":648,"map_ids_sinnoh":54,
            "map_ids_clone_total":702,"saves_copied":False,
            "game_exe_executed":False,"safe_to_launch":False,
            "phase_b_approved":0,"r07_complete":False}

def rollback_clone(project,plan_sha):
    if not isinstance(plan_sha,str) or not SHA.fullmatch(plan_sha):
        blocked("SHA do rollback invalido")
    base=clone_root(project)
    folder=base/f"native-{plan_sha[:16]}"
    if is_link(folder) or not folder.is_dir():
        blocked("clone privado nao encontrado")
    path=folder/"B09_PRIVATE_QA_MANIFEST.json"
    if is_link(path) or not path.is_file() or path.stat().st_size>20_000_000:
        blocked("manifesto de rollback invalido")
    m=json.loads(path.read_text("utf-8"))
    if (m.get("schema")!=1 or m.get("stage")!="B09"
        or m.get("mode")!="PRIVATE_NATIVE_QA_CLONE_UNTESTED"
        or m.get("plan_sha256")!=plan_sha
        or m.get("DO_NOT_LAUNCH") is not True
        or m.get("saves_copied") is not False
        or m.get("source_game_untouched") is not True):
        blocked("manifesto do clone nao permite rollback")
    rows=m.get("files")
    if not isinstance(rows,list) or len(rows)>MAX_FILES+100:
        blocked("lista de rollback invalida")
    if len({(r.get("path"),r.get("origin")) for r in rows})!=len(rows):
        blocked("arquivos repetidos em rollback")
    actual=set()
    for p in folder.rglob("*"):
        if is_link(p):blocked("clone contem symlink; nao apagar")
        if p.is_file():actual.add(p.relative_to(folder).as_posix())
    expected={x["path"] for x in rows}|{
        "B09_PRIVATE_QA_MANIFEST.json","NAO_EXECUTAR_ANTES_DE_ISOLAR_SAVES.txt"}
    if actual!=expected:blocked("clone foi modificado ou contem saves; rollback negado")
    final={}
    total=0
    canonical=[]
    for row in rows:
        name=row.get("path")
        if (not isinstance(name,str) or not name or
            Path(name).is_absolute() or ".." in Path(name).parts or
            type(row.get("bytes")) is not int or not 0<=row["bytes"]<=MAX_SINGLE or
            type(row.get("sha256")) is not str or not SHA.fullmatch(row["sha256"])
            or row.get("origin") not in ("NATIVE","OVERLAY")
            or (row["origin"]=="OVERLAY" and not ALLOWED.fullmatch(name))
            or (row["origin"]=="NATIVE" and should_skip(Path(name)))
            or ("\\\\" in name)):
            blocked("manifesto de rollback contem caminhos invalidos")
        total+=row["bytes"]
        if total>MAX_SIZE+512*1024*1024:blocked("clone fora do limite")
        if row["origin"]=="OVERLAY" and name.casefold() in {
            p.casefold() for p,v in final.items() if v["origin"]=="OVERLAY"
        }:
            blocked("mapas duplicados no rollback")
        canonical.append(row)
        final[name]=row
    if canonical!=sorted(canonical,key=lambda x:(x["path"],x["origin"])):
        blocked("ordem do plano foi alterada")
    actual_plan=byte_sha(json.dumps(
        {"stage_sha256":m.get("stage_sha256"),"files":canonical},
        ensure_ascii=True,sort_keys=True,separators=(",",":")).encode("ascii"))
    if actual_plan!=plan_sha:blocked("assinatura do plano B09 foi alterada")
    for name,row in final.items():
        p=folder/name
        if (is_link(p) or not p.is_file() or
            p.stat().st_size!=row["bytes"] or file_sha(p)!=row["sha256"]):
            blocked("clone alterado; rollback negado")
    note=folder/"NAO_EXECUTAR_ANTES_DE_ISOLAR_SAVES.txt"
    if not note.is_file() or "QA PRIVADO B09" not in note.read_text("utf-8"):
        blocked("aviso do QA privado foi alterado")
    shutil.rmtree(folder)
    return {"stage":"B09","status":"PRIVATE_CLONE_REMOVED_ONLY",
            "plan_sha256":plan_sha,"source_game_untouched":True}

def run(*,project=ROOT,game_dir,native_inventory,stage_sha=None,
        use_latest=False,clone=False,expected_sha=None):
    project=Path(project).absolute()
    c,b08,b07,b06,b00,b01,b04,b05=(
       load(project/p) for p in (
       "data/regions/sinnoh-b09-native-qa.json",
       "data/regions/sinnoh-b08-private-qa.json",
       "data/regions/sinnoh-b07-private-stage.json",
       "data/regions/sinnoh-b06-technical-candidate.json",
       "data/regions/sinnoh-b00-actual-source.json",
       "data/regions/sinnoh-b01-actual-native.json",
       "data/regions/sinnoh-b04-v2-validated.json",
       "data/regions/sinnoh-b05-mapid-planning.json"))
    terrain=check_contract(c,b08,b07,b06,b00,b01,b04,b05)
    if bool(stage_sha)==bool(use_latest):
        blocked("escolha --latest OU --stage-sha")
    native_zip=Path(native_inventory)
    verify_native_zip(native_zip,b06,b05)
    inv,raw=unpack_native(native_zip)
    source=secure_game_dir(project,game_dir)
    check_current_game(source/"Data",inv,inv["physical_map_ids"])
    sha_value=latest_stage(project,STAGE_LABEL) if use_latest else stage_sha
    overlay,audit=check_qa_overlay(project,sha_value,
        native_raw=raw,expected_ids=[
          x["candidate_destination_map_id"] for x in terrain])
    native,summary=scan_native_game(project,source)
    plan=plan_clone(native,overlay,sha_value)
    if clone:
        if not expected_sha:blocked("--clone exige --expected-plan-sha")
        result=clone_private(project,source,overlay,plan,expected_sha)
    else:
        if expected_sha:blocked("--expected-plan-sha so e permitido com --clone")
        result={"status":"B09_DRY_RUN_NO_FILES_WRITTEN",
                "plan_sha256":plan["plan_sha256"],
                "native_files_count":len(native),
                "overlay_files_count":len(overlay),
                "estimated_bytes":plan["total_copy_bytes"],
                "expected_map_count":702,
                "excluded_private_files":summary["skipped_private_or_unrecognized_files"],
                "game_exe_will_be_copied_but_not_launched":True,
                "source_game_untouched":True,"phase_b_approved":0}
    return {**result,"b08_maps_validated":audit["maps_validated"],
            "b08_pngs_validated":audit["pngs_verified"],
            "b08_nonzero_terrain_cells":audit["nonzero_terrain_cells"],
            "future_reservations_verified":False,
            "native_game_tested":False,"joiplay_tested":False,
            "can_install_live_game":False,"r07_complete":False}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir",type=Path)
    parser.add_argument("--native-inventory",type=Path)
    parser.add_argument("--latest",action="store_true")
    parser.add_argument("--stage-sha")
    parser.add_argument("--clone",action="store_true")
    parser.add_argument("--expected-plan-sha")
    parser.add_argument("--rollback-sha")
    args=parser.parse_args(argv)
    try:
        if args.rollback_sha:
            if any((args.game_dir,args.native_inventory,args.latest,
                    args.stage_sha,args.clone,args.expected_plan_sha)):
                blocked("rollback nao pode incluir opcoes de clonagem")
            result=rollback_clone(ROOT,args.rollback_sha)
        elif not any((args.game_dir,args.native_inventory,args.latest,
                      args.stage_sha,args.clone,args.expected_plan_sha)):
            result={"status":"B09_READY_AWAITING_LOCAL_B07_B08_EVIDENCE",
                    "expected_existing_native_maps":648,
                    "expected_sinnoh_overlay_maps":54,
                    "expected_total_in_private_copy":702,
                    "requires_verified_B08_overlay":True,
                    "safe_to_launch":False,"phase_b_approved":0,
                    "r07_complete":False}
        else:
            if not args.game_dir or not args.native_inventory:
                blocked("informe --game-dir e --native-inventory")
            result=run(game_dir=args.game_dir,
                native_inventory=args.native_inventory,
                stage_sha=args.stage_sha,use_latest=args.latest,
                clone=args.clone,expected_sha=args.expected_plan_sha)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (ValueError,KeyError,TypeError,OSError,UnicodeError,
            ImportError,IndexError) as err:
        print(str(err),file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
