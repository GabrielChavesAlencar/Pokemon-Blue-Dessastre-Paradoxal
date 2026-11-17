#!/usr/bin/env python3
"""Unova A13: make a private baseline QA copy WITHOUT Unova maps or execution.

A verified copy is not proof of save isolation at runtime or Game.exe playability.
This module only copies existing installation files, rewrites QA-only mkxp and INI,
and reports missing dynamic checks. No map installer is ever imported or called.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import stat
from pathlib import Path

import audit_unova_a04_mapids as a04

OUT=Path(".blue-work/unova/audit")
MAX_FILES=60000
MAX_FILE_BYTES=2*1024*1024*1024
MAX_BYTES=16*1024*1024*1024
MAX_DEPTH=24
MIN_FREE_MARGIN=128*1024*1024
REPARSE=0x400
EXCLUDE_DIRS=frozenset({
    "save","saves","savedata","save data","saved games","user data",
    "userdata","appdata",".blue-work",".blue-backups",".git",
    ".cache","__pycache__","temp","tmp","backups","backup",
})
SAVE_FILE=re.compile(r"(?i)^(?:(?:save|file|autosave|quicksave|game)\d*|save(?:game|data)?)\.(?:rxdata|rvdata2?|sav|dat|json|bak)$")
IGNORE_FILES=frozenset({".ds_store","thumbs.db"})
REQUIRED=(
    "Game.exe","Game.ini","mkxp.json","Data/MapInfos.rxdata",
    "Data/Map001.rxdata","Data/Scripts.rxdata","Data/System.rxdata",
)
STATUS="QA_BASELINE_COPIED_RUNTIME_UNVERIFIED"
INVENTORY_FILE="unova-a13-copy-evidence.json"
KEEP_FILE="UNOVA_A13_NAO_ABRIR_ANTES_DOS_TESTES.txt"

def blocked(detail):
    raise ValueError("UNOVA_A13_BLOCKED: "+str(detail))

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def path_is_link(path:Path):
    try:
        st=path.lstat()
        return stat.S_ISLNK(st.st_mode) or bool(getattr(st,"st_file_attributes",0)&REPARSE)
    except FileNotFoundError:
        return False

def no_symlink_ancestors(path:Path):
    for part in (path,*path.parents):
        if path_is_link(part):blocked("reparse point/junction/symlink: "+str(part))

def hash_file(path:Path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        while chunk:=f.read(1024*1024):
            h.update(chunk)
    return h.hexdigest()

def should_skip(relative:Path,is_dir:bool):
    if any(x.casefold() in EXCLUDE_DIRS for x in relative.parts):return True
    if is_dir:return False
    if relative.name.casefold() in IGNORE_FILES:return True
    if SAVE_FILE.match(relative.name):return True
    return False

def inventory(game:Path):
    """Exhaustive bounded snapshot, including checks against reparse points."""
    game=Path(game).absolute()
    if not game.is_dir():blocked("jogo nao encontrado")
    no_symlink_ancestors(game)
    entries=[];excluded=0;total=0;keys=set();dirs=0
    def descend(folder,depth=0):
        nonlocal excluded,total,dirs
        if depth>MAX_DEPTH:blocked("diretorios profundos demais")
        dirs+=1
        if dirs>MAX_FILES:blocked("diretorios demais")
        with os.scandir(folder) as it:
            children=sorted(it,key=lambda e:e.name.casefold())
        for item in children:
            rel=Path(item.path).relative_to(game)
            if item.is_symlink() or path_is_link(Path(item.path)):
                blocked("symlink/junction detectado na origem: "+rel.as_posix())
            if item.is_dir(follow_symlinks=False):
                if should_skip(rel,True):
                    excluded+=1;continue
                descend(Path(item.path),depth+1)
                continue
            if not item.is_file(follow_symlinks=False):
                blocked("entrada nao regular: "+rel.as_posix())
            if should_skip(rel,False):
                excluded+=1;continue
            key=rel.as_posix().casefold()
            if key in keys:blocked("colisao de maiusculas/minusculas")
            keys.add(key)
            size=item.stat(follow_symlinks=False).st_size
            if size<0 or size>MAX_FILE_BYTES:blocked("arquivo muito grande: "+rel.as_posix())
            total+=size
            if total>MAX_BYTES or len(entries)>=MAX_FILES:
                blocked("limite de arquivos ou bytes excedido")
            digest=hash_file(Path(item.path))
            if item.stat(follow_symlinks=False).st_size!=size:
                blocked("arquivo alterado durante inventario")
            entries.append({"path":rel.as_posix(),"size":size,"sha256":digest})
    descend(game)
    lookup={x["path"]:x for x in entries}
    missing=set(REQUIRED)-set(lookup)
    if missing:blocked("arquivo necessario ausente: "+", ".join(sorted(missing)))
    return {"files":entries,"file_count":len(entries),"total_bytes":total,
            "excluded_entries":excluded,
            "inventory_sha256":sha(json.dumps(entries,sort_keys=True).encode("utf-8")),
            "mapinfos_sha256":lookup["Data/MapInfos.rxdata"]["sha256"],
            "map001_sha256":lookup["Data/Map001.rxdata"]["sha256"]}

def jsonc(text):
    # Preserve quoted URLs and strip only actual JavaScript comments/trailing commas.
    pattern=r'"(?:[^"\\]|\\.)*"|//[^\r\n]*|/\*[\s\S]*?\*/'
    clean=re.sub(pattern,lambda m:"" if m.group().startswith(("//","/*"))
                 else m.group(),text)
    clean=re.sub(r'"(?:[^"\\]|\\.)*"|,(?=\s*[}\]])',
                 lambda m:"" if m.group()=="," else m.group(),clean)
    value=json.loads(clean)
    if not isinstance(value,dict):blocked("mkxp.json nao eh um objeto")
    return value

def restricted_keys(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if isinstance(k,str) and ("save" in k.casefold() or "userdata" in k.casefold()):
                return True
            if restricted_keys(v):return True
    elif isinstance(value,list):
        return any(restricted_keys(x) for x in value)
    return False

def make_configs(game:Path,token:str):
    """Offline proposed profile, never a runtime save isolation certificate."""
    if not re.fullmatch(r"[a-f0-9]{16}",token):
        blocked("identificador QA invalido")
    raw_mkxp=(game/"mkxp.json").read_text("utf-8-sig")
    raw_ini=(game/"Game.ini").read_text("utf-8-sig")
    config=jsonc(raw_mkxp)
    if restricted_keys(config):blocked("mkxp contem override de saves nao auditado")
    app="BlueUnovaA13QA-"+token
    org="DessastreUnovaA13QA-"+token
    title="Blue Unova QA "+token
    if app==config.get("dataPathApp") or org==config.get("dataPathOrg"):
        blocked("namespace QA conflita com o perfil atual")
    updated=dict(config,windowTitle=title,dataPathApp=app,dataPathOrg=org)
    ini,changes=re.subn(r"(?m)^Title=[^\r\n]*",lambda _: "Title="+title,raw_ini)
    if changes!=1:blocked("Game.ini deve ter exatamente um Title")
    if "Title="+title in raw_ini:blocked("Game.ini ja pertence a esta QA")
    return ((json.dumps(updated,ensure_ascii=False,indent=2)+"\n").encode("utf-8"),
            ini.encode("utf-8"),
            {"window_title":title,"dataPathApp":app,"dataPathOrg":org,
             "save_namespace_static_check_only":True,
             "essentials_runtime_save_isolation_verified":False})

def baselines(game:Path,a04_report,a12_report):
    data=a04_report.get("sources",{}).get("DECADES",{})
    digest=data.get("mapinfos_sha256")
    if (a04_report.get("phase")!="A04" or a12_report.get("phase")!="A12"
            or a12_report.get("status")!="A12_SOURCE_REVIEW_DONE_ISOLATED_QA_NOT_CREATED"
            or a12_report.get("mapinfos_sha256")!=digest or
            a12_report.get("can_install") is not False or
            a12_report.get("can_reserve_mapids") is not False):
        blocked("cadeia A04-A12 nao esta validada")
    row=next((m for m in data.get("maps",[]) if m.get("id")==1),None)
    if not row or row.get("source_filename")!="Map001.rxdata":
        blocked("Map001 hash nao documentado")
    if ((game/"Data/MapInfos.rxdata").is_symlink() or
        hash_file(game/"Data/MapInfos.rxdata")!=digest or
        hash_file(game/"Data/Map001.rxdata")!=row.get("sha256")):
        blocked("arquivos da origem mudaram desde A04")
    return {"mapinfos_sha256":digest,"map001_sha256":row["sha256"]}

def private_root(game:Path,root:Path):
    game=Path(game).absolute()
    root=Path(root).absolute()
    no_symlink_ancestors(root)
    if game==root or root.is_relative_to(game) or game.is_relative_to(root):
        blocked("QA fora da instalacao e de seus ancestrais obrigatoria")
    return root

def clone(game:Path,qa_root:Path,a04_report:dict,a12_report:dict)->dict:
    """Create or verify only a private clone. No game process, maps or save writes."""
    game=Path(game).absolute()
    roots=baselines(game,a04_report,a12_report)
    qa_root=private_root(game,qa_root)
    inv=inventory(game)
    if (inv["mapinfos_sha256"]!=roots["mapinfos_sha256"] or
        inv["map001_sha256"]!=roots["map001_sha256"]):
        blocked("baseline mudou durante o inventario")
    identity=sha((str(game).casefold()+"|"+roots["mapinfos_sha256"]).encode("utf-8"))[:16]
    destination=qa_root/("qa-unova-a13-"+identity)
    no_symlink_ancestors(qa_root)
    token=identity
    mkxp,ini,profile=make_configs(game,token)
    source_paths={x["path"] for x in inv["files"]}
    if INVENTORY_FILE in source_paths or KEEP_FILE in source_paths:
        blocked("arquivos QA ja fazem parte da instalacao")
    # All non-writing validation precedes creation of even the QA root.
    if not qa_root.exists():qa_root.mkdir(parents=True,exist_ok=False)
    if not qa_root.is_dir():blocked("pasta privada QA invalida")
    proof={"schema":1,"phase":"A13","region":"UNOVA",
        "status":STATUS,"source_mapinfos_sha256":roots["mapinfos_sha256"],
        "source_map001_sha256":roots["map001_sha256"],
        "source_inventory_sha256":inv["inventory_sha256"],
        "source_file_count":inv["file_count"],
        "source_bytes":inv["total_bytes"],
        "excluded_save_or_private_entries":inv["excluded_entries"],
        "copied_files":[x for x in inv["files"]],
        "qa_profile":profile,"qa_clone_path":str(destination),
        "source_changed":False,"no_source_saves_accessed":True,
        "unova_maps_installed":False,
        "source_maps_518_599_allocated":False,
        "game_exe_launched":False,"runtime_save_isolation_tested":False,
        "approved_for_gameplay":False,"allowed_to_launch_without_manual_qa":False,
        "native_game_modified":False,"bar_a_completed":0,"bar_a_total":8}
    note=("A13: COPIA PRIVADA DO DECADES PARA AUDITORIA\n"
          "Nao ha mapas de Unova nem reserva de IDs nesta copia.\n"
          "Game.exe NAO foi executado. O isolamento de saves precisa de teste nativo.\n"
          "Nao use saves reais nem inicie o jogo ate aprovar a QA do perfil.\n")
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() or not destination.is_dir():
            blocked("destino QA existente inseguro")
        manifest=destination/INVENTORY_FILE
        if manifest.is_symlink() or not manifest.is_file():blocked("QA existente sem prova")
        saved=json.loads(manifest.read_text("utf-8"))
        if saved!=proof:blocked("QA existente pertence a outra versao ou foi alterada")
        # Never silently trust a previously modified or partially copied clone.
        actual=inventory(destination)
        expected_copied={x["path"]:x for x in inv["files"]}
        original_overrides={x["path"]:x for x in inv["files"] if x["path"] not in
                            ("Game.ini","mkxp.json")}
        actual_files={x["path"]:x for x in actual["files"]
                      if x["path"] not in (INVENTORY_FILE,KEEP_FILE)}
        if set(actual_files)!=set(expected_copied):
            blocked("QA existente tem arquivos novos, faltantes ou adulterados")
        for rel,entry in actual_files.items():
            expected_sha=(sha(mkxp) if rel=="mkxp.json"
                          else sha(ini) if rel=="Game.ini"
                          else expected_copied[rel]["sha256"])
            if entry["sha256"]!=expected_sha:blocked("QA existente nao integra: "+rel)
        return {"status":"QA_BASELINE_EXISTING_VERIFIED_RUNTIME_UNVERIFIED",
                "path":str(destination),"file_count":inv["file_count"],
                "source_bytes":inv["total_bytes"],"profile":profile,
                "no_user_game_modified":True,"game_exe_launched":False,
                "qa_runtime_tested":False,"unova_installed":False}
    if shutil.disk_usage(qa_root).free<inv["total_bytes"]+MIN_FREE_MARGIN:
        blocked("espaco livre insuficiente para QA e margem de seguranca")
    stage=qa_root/(".building-qa-unova-a13-"+identity+"-"+secrets.token_hex(6))
    no_symlink_ancestors(stage)
    try:
        stage.mkdir(exist_ok=False)
        for entry in inv["files"]:
            rel=Path(entry["path"])
            source=game/rel
            dest=stage/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            if path_is_link(source):blocked("link detectado apos inventario")
            if rel.as_posix()=="mkxp.json":blob=mkxp
            elif rel.as_posix()=="Game.ini":blob=ini
            else:blob=None
            if blob is not None:
                with dest.open("xb") as f:f.write(blob)
            else:
                with source.open("rb") as src, dest.open("xb") as out:
                    shutil.copyfileobj(src,out,1024*1024)
            expected=(sha(blob) if blob is not None else entry["sha256"])
            if hash_file(dest)!=expected:
                blocked("copia QA com hash divergente: "+rel.as_posix())
            if source.stat().st_size!=entry["size"] or hash_file(source)!=entry["sha256"]:
                blocked("origem alterada durante copia: "+rel.as_posix())
        if (hash_file(game/"Data/MapInfos.rxdata")!=roots["mapinfos_sha256"] or
            hash_file(game/"Data/Map001.rxdata")!=roots["map001_sha256"]):
            blocked("baseline mudou durante copia")
        with (stage/INVENTORY_FILE).open("x",encoding="utf-8") as f:
            json.dump(proof,f,ensure_ascii=False,indent=2,sort_keys=True)
            f.write("\n")
        with (stage/KEEP_FILE).open("x",encoding="utf-8") as f:f.write(note)
        if destination.exists() or destination.is_symlink():
            blocked("pasta QA foi criada por outro processo")
        stage.rename(destination)
    except BaseException:
        # Only ever remove the private, uniquely created *staging* folder.
        if stage.is_dir() and not stage.is_symlink():
            shutil.rmtree(stage)
        raise
    return {"status":STATUS,"path":str(destination),"file_count":inv["file_count"],
            "source_bytes":inv["total_bytes"],"profile":profile,
            "no_user_game_modified":True,"game_exe_launched":False,
            "qa_runtime_tested":False,"unova_installed":False}

def audit(game:Path,qa_root:Path,a04_report:dict,a12_report:dict):
    return clone(game,qa_root,a04_report,a12_report)

def save(project:Path,report:dict):
    project=a04.safe_path(project)
    for folder in (project/".blue-work",project/".blue-work/unova",project/OUT):
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            blocked("diretorio de auditoria inseguro")
        folder.mkdir(exist_ok=True)
    data=(json.dumps(report,indent=2,ensure_ascii=False,sort_keys=True)+"\n").encode("utf-8")
    path=project/OUT/("a13-private-qa-"+sha(data)[:16]+".json")
    if path.is_symlink():blocked("relatorio link")
    if path.exists():
        if path.read_bytes()!=data:blocked("colisao relatorio")
    else:
        with path.open("xb") as f:f.write(data)
    return path
