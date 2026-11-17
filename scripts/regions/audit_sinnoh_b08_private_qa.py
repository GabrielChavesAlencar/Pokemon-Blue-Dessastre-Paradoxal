#!/usr/bin/env python3
"""B08 private Sinnoh QA: audit B07 stage and prepare a NON-RUNNABLE QA overlay.

Only reads an existing immutable B07 stage, the pinned B01 inventory and
optionally the user's current game/Data. Any output goes solely to the ignored
.blue-work/sinnoh-b08-qa/ tree; never edits the live game, saves or donor.
No Ruby code is evaluated. Third-party art must never enter public GitHub.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import struct
import sys
import tempfile
import zlib

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from audit_sinnoh_b06_technical_candidate import (
    B00,B01,B04,B05,B06,load,verify_native_zip)
from audit_sinnoh_b01_inventory import unpack as unpack_native
from build_sinnoh_b07_private_stage import (
    CONTRACT as B07,check_contract as check_b07_contract,
    check_current_game,MAPNAME)
from convert_sinnoh_geometry import table_valid
from server.ruby_marshal import RubyObject,loads,text
from sinnoh_staging_transaction import (
    ALLOWED,LABEL,preview,stage_root)
CONTRACT=ROOT/"data/regions/sinnoh-b08-private-qa.json"
PNG=b"\x89PNG\r\n\x1a\n"
STAGE_LABEL="sinnoh-b07"
SHA=re.compile(r"[0-9a-f]{64}\Z")
MAX_PNG_BYTES=32_000_000
EXPECTED_TERRAIN_CELLS=484722
EXPECTED_PNGS=14

def blocked(reason):
    raise ValueError("SINNOH_B08_BLOCKED: "+reason)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def check_contract(c,b07,b06,b00,b01,b04,b05):
    rows=check_b07_contract(b07,b06,b00,b01,b04,b05)
    expected={
      "schema":1,"region":"SINNOH","stage":"B08",
      "status":"PRIVATE_QA_AUDITOR_READY_USER_STAGE_NOT_RECEIVED",
      "b07_source_sha256":b07["source_zip_sha256"],
      "native_b01_inventory_zip_sha256":b07["native_inventory_zip_sha256"],
      "native_mapinfos_sha256":b01["mapinfos_sha256"],
      "native_tilesets_sha256":b01["tilesets_sha256"],
      "expected_staged_terrain_ids":[r["candidate_destination_map_id"] for r in rows],
      "excluded_empty_ids":b07["excluded_empty_destinations"],
      "expected_staged_maps":54,"expected_pngs":14,
      "expected_nonzero_terrain_cells":484722,
      "source_tilesets_to_new_indices":[1,31],
      "qa_overlay_subdir":".blue-work/sinnoh-b08-qa",
      "source_stage_subdir":".blue-work/sinnoh-stage",
      "must_verify_stage_manifest_and_every_file":True,
      "must_verify_png_chunks_references_and_native_tileset_append":True,
      "must_verify_live_game_data_before_overlay":True,
      "overlay_is_a_non_runnable_private_copy":True,
      "never_copy_saves_or_game_exe":True,
      "may_write_to_main_game":False,
      "can_install":False,"can_mark_gameplay":False,
      "has_live_stage_evidence":False,
      "r07_complete":False,"r08_complete":False,"r09_complete":False,
      "rights_per_asset_verified":False,
      "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
    }
    if type(c) is not dict or c!=expected:
        blocked("contrato B08 nao corresponde a B07 ou aprovacoes foram forjadas")
    return rows

def png_geometry(data):
    if not isinstance(data,bytes) or len(data)>MAX_PNG_BYTES or not data.startswith(PNG):
        blocked("PNG ausente, invalido ou acima do limite")
    pos=8;dimensions=None;has_idat=False;ended=False
    while pos<len(data):
        if len(data)-pos<12:blocked("PNG com chunk truncado")
        n=struct.unpack_from(">I",data,pos)[0]
        tag=data[pos+4:pos+8];start=pos+8;end=start+n
        if n>MAX_PNG_BYTES or end+4>len(data):
            blocked("PNG com chunk muito grande/truncado")
        content=data[start:end]
        if (zlib.crc32(tag+content)&0xffffffff)!=struct.unpack_from(">I",data,end)[0]:
            blocked("PNG com CRC divergente")
        if pos==8:
            if tag!=b"IHDR" or n!=13:
                blocked("PNG sem IHDR valido")
            w,h,depth,colour,_,_,_=struct.unpack(">IIBBBBB",content)
            if not 1<=w<=16384 or not 1<=h<=100000 or w*h>40_000_000 or depth not in (1,2,4,8,16) or colour not in (0,2,3,4,6):
                blocked("PNG com dimensoes/formato nao suportado")
            dimensions=(w,h)
        if tag==b"IDAT":has_idat=True
        if tag==b"IEND":
            if n!=0 or end+4!=len(data):
                blocked("IEND invalido")
            ended=True;break
        pos=end+4
    if not (has_idat and ended and dimensions):
        blocked("PNG incompleto ou sem dados")
    return dimensions

def check_stage_identity(project,label,plan_sha):
    project=Path(project).absolute()
    if not LABEL.fullmatch(label) or not isinstance(plan_sha,str) or not SHA.fullmatch(plan_sha):
        blocked("identidade de stage invalida")
    base=stage_root(project)
    folder=base/f"{label}-{plan_sha[:16]}"
    if folder.is_symlink() or not folder.is_dir():
        blocked("stage B07 ainda nao existe ou e symlink")
    if not folder.resolve().is_relative_to(base.resolve()):
        blocked("stage escapa do workspace privado")
    return folder

def read_stage(project,label,plan_sha):
    folder=check_stage_identity(project,label,plan_sha)
    manifest_path=folder/"stage-manifest.json"
    if manifest_path.is_symlink() or not manifest_path.is_file():
        blocked("stage-manifest ausente ou symlink")
    manifest=json.loads(manifest_path.read_text("utf-8"))
    if (type(manifest) is not dict
        or manifest.get("schema")!=1 or manifest.get("region")!="SINNOH"
        or manifest.get("mode")!="LOCAL_STAGE_ONLY"
        or manifest.get("label")!=label
        or manifest.get("plan_sha256")!=plan_sha
        or manifest.get("stage_relative_path")!=
            f".blue-work/sinnoh-stage/{label}-{plan_sha[:16]}"
        or manifest.get("writes_to_main_game") is not False
        or manifest.get("may_install_into_game") is not False
        or manifest.get("source_rights_verified") is not False
        or manifest.get("mapping_verified") is not False):
        blocked("manifesto do stage nao confere com a identidade B07")
    records=manifest.get("files")
    if type(records) is not list or not records or len(records)>100:
        blocked("lista de arquivos do stage invalida")
    names=set();files={}
    for row in records:
        if (type(row) is not dict or set(row)!={"path","bytes","sha256"}
            or type(row["path"]) is not str or not ALLOWED.fullmatch(row["path"])
            or row["path"].casefold() in names
            or type(row["bytes"]) is not int or row["bytes"]<1
            or type(row["sha256"]) is not str or not SHA.fullmatch(row["sha256"])):
            blocked("arquivo nao permitido pelo manifesto")
        names.add(row["path"].casefold())
        f=folder/row["path"]
        if f.is_symlink() or not f.is_file() or f.stat().st_size!=row["bytes"]:
            blocked("arquivo ausente, link ou tamanho alterado: "+row["path"])
        content=f.read_bytes()
        if sha(content)!=row["sha256"]:
            blocked("SHA do stage alterado: "+row["path"])
        files[row["path"]]=content
    actual=set()
    allowed_dirs=set()
    for rel in files:
        allowed_dirs.update(str(p.as_posix()) for p in Path(rel).parents if str(p)!=".")
    for node in folder.rglob("*"):
        if node.is_symlink():blocked("stage contem symlink")
        relative=node.relative_to(folder).as_posix()
        if node.is_dir() and relative not in allowed_dirs:
            blocked("stage contem diretorio inesperado")
        if node.is_file():actual.add(relative)
    if actual!=set(files)|{"stage-manifest.json"}:
        blocked("stage contem arquivo inesperado/ausente")
    dry=preview(project,label,files)
    if (dry["plan_sha256"]!=plan_sha
        or manifest!={**dry,"mode":"LOCAL_STAGE_ONLY"}):
        blocked("assinatura do dry-run ou manifesto divergiu")
    return files,dry

def audit_files(files,native_infos_raw,native_tiles_raw,expected_ids,
                *,expected_png_count=EXPECTED_PNGS,
                expected_cells=EXPECTED_TERRAIN_CELLS):
    native_infos=loads(native_infos_raw)
    native_tiles=loads(native_tiles_raw)
    out_infos=loads(files["Data/MapInfos.rxdata"])
    out_tiles=loads(files["Data/Tilesets.rxdata"])
    if (type(native_infos) is not dict or type(out_infos) is not dict
        or type(native_tiles) is not list or type(out_tiles) is not list
        or set(out_infos)!=set(native_infos)|set(expected_ids)
        or len(out_tiles)!=len(native_tiles)+2):
        blocked("tabelas MapInfos/Tilesets de overlay inconsistentes")
    if (any(out_infos[k]!=native_infos[k] for k in native_infos)
        or out_tiles[:len(native_tiles)]!=native_tiles):
        blocked("o stage alterou registros nativos existentes")
    appended_ids=set(range(len(native_tiles),len(native_tiles)+2))
    refs=set();pngs={k for k in files if k.startswith("Graphics/")}
    if len(pngs)!=expected_png_count:
        blocked("quantidade de PNGs nao corresponde ao B07")
    png_dimensions={}
    for path in pngs:
        parts=path.split("/")
        if len(parts)!=3 or parts[1] not in ("Tilesets","Autotiles"):
            blocked("PNG fora da pasta privada esperada")
        content=files[path]
        if not Path(path).stem.startswith(f"SN_B07_{sha(content)[:16]}_"):
            blocked("nome de PNG nao corresponde ao SHA dos bytes")
        png_dimensions[path]=png_geometry(content)
    for id in appended_ids:
        item=out_tiles[id]
        if not isinstance(item,RubyObject) or item.name!="RPG::Tileset" or item.attrs.get("@id")!=id:
            blocked("tileset privado com ID/classe incorretos")
        t=item.attrs
        if t.get("@name")!=b"[Sinnoh B07 private geometry]":
            blocked("nome do tileset privado nao identificado")
        if not isinstance(t.get("@autotile_names"),list):
            blocked("lista de autotiles invalida")
        for folder,name in [("Tilesets",t.get("@tileset_name")), *[
            ("Autotiles",x) for x in t["@autotile_names"]]]:
            if not isinstance(name,bytes):
                blocked("referencia grafica nao e bytes")
            decoded=text(name).strip()
            if not decoded:
                continue
            path=f"Graphics/{folder}/{decoded}.png"
            if path not in pngs:blocked("referencia grafica sem PNG: "+path)
            refs.add(path)
        if any(t.get(x) not in (b"","") for x in
               ("@panorama_name","@fog_name","@battleback_name")):
            blocked("fundo/som do doador indevidamente preservado")
    if refs!=pngs:
        blocked("PNG privado orfao ou nao referenciado")
    expected_map_names={f"Data/Map{n:03d}.rxdata" for n in expected_ids}
    map_files={name for name in files if re.fullmatch(r"Data/Map[0-9]{3}\.rxdata",name)}
    if map_files!=expected_map_names:
        blocked("MapIDs staged nao conferem com B07 (54 somente)")
    if set(files)!=(expected_map_names|pngs|{"Data/MapInfos.rxdata","Data/Tilesets.rxdata"}):
        blocked("stage contem Data extra ou faltando")
    tile_usage=Counter();nonzero=0
    for destination in sorted(expected_ids):
        obj=loads(files[f"Data/Map{destination:03d}.rxdata"])
        if not isinstance(obj,RubyObject) or obj.name!="RPG::Map":
            blocked("objeto Map do stage invalido")
        at=obj.attrs
        w,h,tid=at.get("@width"),at.get("@height"),at.get("@tileset_id")
        if (type(w) is not int or type(h) is not int
            or type(tid) is not int or tid not in appended_ids
            or not table_valid(at.get("@data"),w,h)
            or at.get("@events")!={}
            or at.get("@encounter_list")!=[]
            or at.get("@autoplay_bgm") is not False
            or at.get("@autoplay_bgs") is not False
            or not isinstance(at.get("@bgm"),RubyObject)
            or not isinstance(at.get("@bgs"),RubyObject)
            or at["@bgm"].attrs.get("@name")!=b""
            or at["@bgs"].attrs.get("@name")!=b""):
            blocked("mapa nao sanitizado, fora de tileset ou table invalida: "+str(destination))
        tile_usage[tid]+=1
        grid=at["@data"].data
        nonzero+=sum(x[0]!=0 for x in struct.iter_unpack("<H",grid[20:]))
        info=out_infos[destination]
        if (not isinstance(info,RubyObject) or
            not text(info.attrs.get("@name",b"")).startswith("[Sinnoh B07 PRIVATE] ")):
            blocked("MapInfo privado inesperado: "+str(destination))
    if sorted(tile_usage.values())!=[1,len(expected_ids)-1] or nonzero!=expected_cells:
        blocked("uso de tilesets ou celulas do terreno mudou")
    return {
       "maps_validated":len(expected_ids),
       "nonzero_terrain_cells":nonzero,
       "new_private_tileset_ids":sorted(appended_ids),
       "tile_usage_by_private_id":{str(k):v for k,v in sorted(tile_usage.items())},
       "pngs_verified":len(pngs),
       "png_dimensions":{k:{"width":v[0],"height":v[1]} for k,v in sorted(png_dimensions.items())},
       "all_png_references_resolved":True,
       "native_infos_preserved":True,
       "native_tiles_preserved":True,
       "source_events_audio_script_included":False,
       "playable":False,
       "rights_verified":False,
    }

def qa_root(project):
    project=Path(project).absolute()
    base=stage_root(project).parent
    qa=base/"sinnoh-b08-qa"
    if qa.is_symlink() or not qa.resolve().is_relative_to(project.resolve()):
        blocked("workspace QA aponta para fora do repositorio")
    return qa

def prepare_qa(project,plan_sha,files,audit,*,live_game_verified=False):
    """Create only an immutable local overlay; never a standalone executable."""
    if live_game_verified is not True:
        blocked("overlay exige comprovacao de game/Data atual")
    project=Path(project).absolute()
    target_root=qa_root(project)
    if not target_root.parent.exists():
        blocked("workspace .blue-work de B07 nao encontrado")
    target=target_root/f"qa-{plan_sha[:16]}"
    if target.exists() or target.is_symlink():
        blocked("overlay privado ja existe: recusar sobrescrita")
    target_root.mkdir(parents=True,exist_ok=True)
    temporary=Path(tempfile.mkdtemp(prefix=".b08-qa-",dir=target_root))
    try:
        records=[]
        for rel,raw in sorted(files.items()):
            if not ALLOWED.fullmatch(rel):blocked("arquivo inesperado para overlay")
            path=temporary/rel
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("xb") as handle:
                handle.write(raw);handle.flush();os.fsync(handle.fileno())
            if sha(path.read_bytes())!=sha(raw):
                blocked("copia do overlay falhou verificacao SHA")
            records.append({"path":rel,"sha256":sha(raw),"bytes":len(raw)})
        manifest={
           "schema":1,"region":"SINNOH","stage":"B08",
           "mode":"PRIVATE_QA_OVERLAY_NOT_RUNNABLE",
           "source_stage_sha256":plan_sha,"files":records,
           "verification":{k:audit[k] for k in (
                "maps_validated","nonzero_terrain_cells","pngs_verified",
                "new_private_tileset_ids","all_png_references_resolved",
                "native_infos_preserved","native_tiles_preserved")},
           "may_copy_into_live_game":False,"executable_included":False,
           "saves_included":False,"rights_verified":False,
           "r07_complete":False,"r08_complete":False,
           "game_exe_tested":False,"joiplay_tested":False,
           "phase_b_approved":0
        }
        (temporary/"qa-overlay-manifest.json").write_text(
            json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        if target.exists() or target.is_symlink():
            blocked("overlay existente apareceu durante preparacao")
        temporary.rename(target)
    except BaseException:
        if temporary.exists():shutil.rmtree(temporary)
        raise
    return {"mode":"PRIVATE_QA_OVERLAY_NOT_RUNNABLE",
            "relative_path":str(target.relative_to(project).as_posix()),
            "files_copied":len(records),
            "source_stage_sha256":plan_sha,
            "writes_to_live_game":False,"gameplay_approved":False}

def latest_stage(project,label):
    root=stage_root(project)
    matches=[]
    if root.is_dir():
        for item in root.iterdir():
            if item.is_dir() and re.fullmatch(re.escape(label)+r"-[0-9a-f]{16}",item.name):
                matches.append(item)
    if len(matches)!=1:
        blocked(f"esperado 1 stage B07, encontrados {len(matches)}; escolha --stage-sha")
    f=matches[0]/"stage-manifest.json"
    if f.is_symlink() or not f.is_file():
        blocked("stage B07 sem manifesto")
    sha_value=json.loads(f.read_text("utf-8")).get("plan_sha256")
    if not isinstance(sha_value,str) or not SHA.fullmatch(sha_value):
        blocked("SHA do stage nao valido")
    return sha_value

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage-sha")
    parser.add_argument("--latest",action="store_true",
                        help="Use ONLY when exactly one private B07 stage exists")
    parser.add_argument("--native-inventory",type=Path)
    parser.add_argument("--game-data",type=Path)
    parser.add_argument("--prepare-qa",action="store_true",
                        help="Create private NON-RUNNABLE copy after full audit")
    parser.add_argument("--label",default=STAGE_LABEL)
    args=parser.parse_args(argv)
    try:
        c,b07,b06,b00,b01,b04,b05=(load(p) for p in (
            CONTRACT,B07,B06,B00,B01,B04,B05))
        rows=check_contract(c,b07,b06,b00,b01,b04,b05)
        if args.latest and args.stage_sha:
            blocked("escolha --latest ou --stage-sha")
        if not args.latest and not args.stage_sha:
            if args.prepare_qa or args.native_inventory or args.game_data:
                blocked("informe --latest ou --stage-sha para inspecao")
            print(json.dumps({"status":"B08_READY_AWAITING_LOCAL_B07_STAGE",
                "maps_expected":54,"pngs_expected":14,
                "future_reservations_verified":False,"can_install":False,
                "phase_b_approved":0},ensure_ascii=False,indent=2))
            return 0
        if not args.native_inventory:
            blocked("informe --native-inventory B01 para comparar tilesets nativos")
        chosen_sha=latest_stage(ROOT,args.label) if args.latest else args.stage_sha
        verify_native_zip(args.native_inventory,b06,b05)
        inv,native=unpack_native(args.native_inventory)
        files,dry=read_stage(ROOT,args.label,chosen_sha)
        expected=[x["candidate_destination_map_id"] for x in rows]
        info=audit_files(files,native["MapInfos.rxdata"],
                native["Tilesets.rxdata"],expected)
        game=None
        if args.game_data:
            game=check_current_game(args.game_data,inv,inv["physical_map_ids"])
        if args.prepare_qa and not game:
            blocked("--prepare-qa exige --game-data atual validado")
        result={"schema":1,"region":"SINNOH","stage":"B08",
                "status":"STAGED_GEOMETRY_AUDITED_PRIVATE_QA_ONLY",
                "stage_sha256":chosen_sha,
                "stage_file_count":len(files),
                "live_game_verified":bool(game),
                "audit":info,"overlay":None,
                "game_exe_tested":False,"joiplay_tested":False,
                "can_install":False,"r07_complete":False,
                "r08_complete":False,"phase_b_approved":0}
        if args.prepare_qa:
            result["overlay"]=prepare_qa(ROOT,chosen_sha,files,info,live_game_verified=bool(game))
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,TypeError,IndexError,KeyError,
            OverflowError,UnicodeError) as exc:
        print(str(exc),file=sys.stderr)
        return 2
if __name__=="__main__":
    raise SystemExit(main())
