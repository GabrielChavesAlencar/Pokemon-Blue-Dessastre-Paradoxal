#!/usr/bin/env python3
"""Sinnoh B07: private, isolated geometry pilot for 54 real terrain maps.

Source and B01 inventory are user-provided local ZIPs. No external Ruby,
events, scripts, music, PBS, saves or native game data are executed/written.
Binary assets stay in ignored .blue-work/sinnoh-stage; never ship to GitHub.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import stat
import struct
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from audit_sinnoh_b06_technical_candidate import (
    B00,B01,B04,B05,B06,audit as audit_b06,load,
    verify_source_zip,verify_native_zip,
)
from audit_sinnoh_b01_inventory import unpack as unpack_native
from convert_sinnoh_geometry import (
    TILE_ATTRS,table_valid,silent_audio,graphic_name,
)
from server.ruby_marshal import RubyObject,RubyData,loads,text
from sinnoh_staging_transaction import preview,stage,rollback
from stage import serialize

CONTRACT=ROOT/"data/regions/sinnoh-b07-private-stage.json"
MAPNAME=re.compile(r"Map0*([1-9][0-9]{0,4})\.rxdata\Z",re.I)
PNG_SIGNATURE=b"\x89PNG\r\n\x1a\n"
TERRAIN_COUNT=54
PLACEHOLDERS=22
SLOT_START=442
MAX_GRAPHIC_BYTES=32_000_000
LABEL="sinnoh-b07"
SOURCE_TILE_IDS={1,31}

def blocked(message):
    raise ValueError("SINNOH_B07_BLOCKED: "+message)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def check_contract(contract,b06,b00,b01,b04,b05):
    audit_b06(b06,b00,b01,b04,b05)
    rows=b06["remap_preview"]
    terrain=rows[:TERRAIN_COUNT]
    placeholders=rows[TERRAIN_COUNT:]
    expected={
      "schema":1,"region":"SINNOH","stage":"B07",
      "status":"PRIVATE_GEOMETRY_BUILDER_READY_NOT_NATIVE_INSTALLED",
      "source_zip_sha256":b06["source_zip_sha256"],
      "native_inventory_zip_sha256":b06["native_b01_inventory_zip_sha256"],
      "native_mapinfos_sha256":b01["mapinfos_sha256"],
      "native_tilesets_sha256":b01["tilesets_sha256"],
      "b04v2_provenance_sha256":b04["uploaded_zip_sha256"],
      "source_mapids_with_terrain":[r["source_map_id"] for r in terrain],
      "candidate_terrain_destinations":[r["candidate_destination_map_id"] for r in terrain],
      "excluded_empty_source_ids":[r["source_map_id"] for r in placeholders],
      "excluded_empty_destinations":[r["candidate_destination_map_id"] for r in placeholders],
      "required_source_tilesets":[1,31],
      "native_tileset_strategy":"APPEND_TO_SNAPSHOT_COPY_ONLY",
      "private_stage_subdir":".blue-work/sinnoh-stage",
      "required_game_data_current_sha_match_for_stage":True,
      "dry_run_without_writes":True,
      "stage_requires_explicit_user_action":True,
      "rollback_requires_original_stage_sha":True,
      "copies_donor_graphics_only_into_private_stage":True,
      "imports_donor_events":False,"imports_donor_scripts":False,
      "imports_donor_audio":False,"imports_donor_pbs":False,
      "preserves_game_data":True,"preserves_saves":True,
      "can_install_into_game":False,"redistribution_approved":False,
      "rights_per_asset_verified":False,"r07_complete":False,
      "r08_complete":False,"r09_complete":False,
      "native_game_exe_tested":False,"joiplay_tested":False,
      "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
    }
    if type(contract) is not dict or contract!=expected:
        blocked("contrato B07 adulterado ou aprovado sem evidencias")
    if (len(terrain)!=TERRAIN_COUNT or len(placeholders)!=PLACEHOLDERS
        or {x["candidate_destination_map_id"] for x in terrain}!=set(range(442,496))
        or {x["candidate_destination_map_id"] for x in placeholders}!=set(range(496,518))
        or any(x["category"]!="TERRAIN" for x in terrain)
        or any(x["category"]!="EMPTY_PLACEHOLDER" for x in placeholders)):
        blocked("54 mapas e 22 placeholders B06 inconsistentes")
    return terrain

def zip_member(archive,relative):
    matches=[m for m in archive.infolist() if m.filename==relative]
    if len(matches)!=1:
        blocked("arquivo ausente/duplicado: "+relative)
    item=matches[0]
    if (item.is_dir() or item.flag_bits&1
        or stat.S_IFMT(item.external_attr>>16)==stat.S_IFLNK
        or not 0<item.file_size<=MAX_GRAPHIC_BYTES):
        blocked("arquivo inseguro ou grande demais: "+relative)
    return archive.read(item)

def graphic(archive,root,folder,original,files,renames):
    name=graphic_name(original)
    if not name:
        return b""
    key=(folder,name.casefold())
    if key in renames:
        return renames[key]
    relative=f"{root}/Graphics/{folder}/{name}.png"
    raw=zip_member(archive,relative)
    if not raw.startswith(PNG_SIGNATURE):
        blocked("imagem nao e PNG: "+relative)
    candidate=f"SN_B07_{digest(raw)[:16]}_{name[:55]}"
    output=f"Graphics/{folder}/{candidate}.png"
    if output in files and files[output]!=raw:
        blocked("nome de grafico privado duplicado: "+output)
    files[output]=raw
    renames[key]=candidate.encode("utf-8")
    return renames[key]

def build_files(source_zip,native_infos_raw,native_tiles_raw,rows,*,source_root):
    """In-memory transformation, no filesystem writes. Supports synthetic tests."""
    infos=loads(native_infos_raw)
    native_tiles=loads(native_tiles_raw)
    if (type(infos) is not dict or not isinstance(native_tiles,list)
        or len(native_tiles)>5000
        or any(type(k) is not int or k<1 for k in infos)):
        blocked("MapInfos/Tilesets nativos invalidos")
    output_infos=copy.deepcopy(infos)
    output_tiles=copy.deepcopy(native_tiles)
    files={}
    new_tile_ids={}
    graphic_names={}
    observed_source_tiles=set()
    total_nonzero=0
    max_order=max((v.attrs.get("@order",0) for v in infos.values()
                   if isinstance(v,RubyObject)
                   and type(v.attrs.get("@order",0)) is int),default=0)
    with zipfile.ZipFile(source_zip) as archive:
        donor_infos=loads(zip_member(archive,f"{source_root}/Data/MapInfos.rxdata"))
        donor_tiles=loads(zip_member(archive,f"{source_root}/Data/Tilesets.rxdata"))
        if type(donor_infos) is not dict or not isinstance(donor_tiles,list):
            blocked("indices do doador invalidos")
        for index,item in enumerate(rows):
            source_id=item["source_map_id"]
            destination=item["candidate_destination_map_id"]
            if (type(source_id) is not int or type(destination) is not int
                or destination in output_infos or destination<1 or destination>=600
                or item.get("category")!="TERRAIN"):
                blocked("destino candidato colide com base ou invalido")
            raw=zip_member(archive,f"{source_root}/Data/Map{source_id:03d}.rxdata")
            obj=loads(raw)
            if not isinstance(obj,RubyObject) or obj.name!="RPG::Map":
                blocked("mapa doador invalido: "+str(source_id))
            props=obj.attrs
            width,height,tile_id=props.get("@width"),props.get("@height"),props.get("@tileset_id")
            if (any(type(x) is not int for x in (width,height,tile_id))
                or not 1<=width<=500 or not 1<=height<=500
                or tile_id not in SOURCE_TILE_IDS
                or not table_valid(props.get("@data"),width,height)):
                blocked("geometria/tileset invalido no Map"+str(source_id))
            grid=props["@data"].data[20:]
            used=sum(1 for (n,) in struct.iter_unpack("<H",grid) if n!=0)
            if used==0:
                blocked("mapa sem terreno incluído no piloto: "+str(source_id))
            total_nonzero+=used
            observed_source_tiles.add(tile_id)
            if tile_id not in new_tile_ids:
                if not 0<tile_id<len(donor_tiles):
                    blocked("tileset do doador nao existe")
                donor_tile=donor_tiles[tile_id]
                if not isinstance(donor_tile,RubyObject) or donor_tile.name!="RPG::Tileset":
                    blocked("classe de tileset desconhecida")
                old=donor_tile.attrs
                if not isinstance(old.get("@autotile_names"),list):
                    blocked("autotiles do doador invalidos")
                tile_copy={k:copy.deepcopy(v) for k,v in old.items() if k in TILE_ATTRS}
                new_tile_id=len(output_tiles)
                if new_tile_id>9999:
                    blocked("tabela de tilesets excede capacidade")
                tile_copy["@id"]=new_tile_id
                tile_copy["@name"]=b"[Sinnoh B07 private geometry]"
                tile_copy["@tileset_name"]=graphic(
                    archive,source_root,"Tilesets",old.get("@tileset_name"),
                    files,graphic_names)
                tile_copy["@autotile_names"]=[
                    graphic(archive,source_root,"Autotiles",v,files,graphic_names)
                    for v in old["@autotile_names"]
                ]
                for k in ("@panorama_name","@fog_name","@battleback_name"):
                    tile_copy[k]=b""
                output_tiles.append(RubyObject("RPG::Tileset",tile_copy))
                new_tile_ids[tile_id]=new_tile_id
            # Explicitly strip source events, trainers, warps, scripts and audio.
            new_map=RubyObject("RPG::Map",{
                "@tileset_id":new_tile_ids[tile_id],
                "@width":width,"@height":height,
                "@autoplay_bgm":False,"@bgm":silent_audio(),
                "@autoplay_bgs":False,"@bgs":silent_audio(),
                "@encounter_list":[],"@encounter_step":30,
                "@data":copy.deepcopy(props["@data"]),"@events":{},
            })
            info_obj=donor_infos.get(source_id)
            name=text(info_obj.attrs.get("@name",b"")) if isinstance(info_obj,RubyObject) else ""
            output_infos[destination]=RubyObject("RPG::MapInfo",{
                "@name":("[Sinnoh B07 PRIVATE] "+name[:80]).encode("utf-8"),
                "@parent_id":0,"@order":max_order+index+1,
                "@expanded":False,"@scroll_x":0,"@scroll_y":0,
            })
            rel=f"Data/Map{destination:03d}.rxdata"
            rendered=serialize(new_map)
            if loads(rendered).attrs["@events"]!={}:
                blocked("eventos do doador foram serializados")
            files[rel]=rendered
    if len(rows)!=TERRAIN_COUNT or observed_source_tiles!=SOURCE_TILE_IDS:
        blocked("piloto B07 nao cobriu exatamente 54 terrenos e tilesets 1/31")
    files["Data/MapInfos.rxdata"]=serialize(output_infos)
    files["Data/Tilesets.rxdata"]=serialize(output_tiles)
    # Serializing from copied objects cannot mutate the input bytes.
    if (len(output_infos)!=len(infos)+TERRAIN_COUNT
        or len(output_tiles)!=len(native_tiles)+2
        or any(output_tiles[i]!=native_tiles[i] for i in range(len(native_tiles)))
        or any(output_infos[i]!=infos[i] for i in infos)):
        blocked("conteudo base nao foi preservado")
    if len([x for x in files if re.fullmatch(r"Data/Map[0-9]{3}\.rxdata",x)])!=TERRAIN_COUNT:
        blocked("piloto possui contagem de mapas inesperada")
    return files,{
        "schema":1,"region":"SINNOH","stage":"B07",
        "mode":"PRIVATE_GEOMETRY_ONLY_NO_NATIVE_INSTALL",
        "source_terrain_maps_prepared":TERRAIN_COUNT,
        "empty_placeholders_excluded":PLACEHOLDERS,
        "nonzero_terrain_tiles":total_nonzero,
        "donor_tileset_to_new_private_index":{str(k):v for k,v in sorted(new_tile_ids.items())},
        "private_png_count":len([k for k in files if k.startswith("Graphics/")]),
        "private_file_count":len(files),
        "donor_events_imported":0,"donor_audio_imported":0,
        "donor_scripts_executed":0,
        "writes_to_game_or_saves":False,"can_install":False,
        "rights_verified":False,"r07_complete":False,"r08_complete":False,
        "phase_b_approved":0,
    }

def check_current_game(game_data,native_report,ids):
    if game_data is None:
        blocked("--stage requer --game-data da instalacao atual")
    root=Path(game_data).expanduser().absolute()
    if root.is_symlink() or not root.is_dir():
        blocked("game/Data local nao encontrado ou symlink")
    for filename,key in (("MapInfos.rxdata","mapinfos_sha256"),
                         ("Tilesets.rxdata","tilesets_sha256")):
        file=root/filename
        if (file.is_symlink() or not file.is_file()
            or digest(file.read_bytes())!=native_report[key]):
            blocked("baseline local mudou: "+filename)
    present=set()
    for file in root.iterdir():
        if file.is_symlink():blocked("game/Data contem symlink")
        found=MAPNAME.fullmatch(file.name)
        if found:
            if not file.is_file():blocked("MapNNN nao e arquivo")
            mid=int(found.group(1))
            if mid in present:blocked("MapID fisico duplicado")
            present.add(mid)
    if present!=set(ids):
        blocked("MapIDs da instalacao mudaram desde B01/B04 V2")
    return {"actual_game_data_verified_against_b01":True}

def main(argv=None):
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--source-zip",type=Path)
    cli.add_argument("--native-inventory",type=Path)
    cli.add_argument("--game-data",type=Path)
    cli.add_argument("--label",default=LABEL)
    cli.add_argument("--stage",action="store_true",help="write ONLY .blue-work private stage")
    cli.add_argument("--expected-sha",help="SHA of prior dry-run; required with --stage")
    cli.add_argument("--rollback-sha",help="delete ONLY exact untouched local stage")
    args=cli.parse_args(argv)
    try:
        if args.rollback_sha:
            if args.stage or args.source_zip or args.native_inventory or args.expected_sha:
                blocked("rollback nao pode ser misturado com builder")
            print(json.dumps(rollback(ROOT,args.label,args.rollback_sha),indent=2))
            return 0
        c,b00,b01,b04,b05,b06=(load(p) for p in (CONTRACT,B00,B01,B04,B05,B06))
        rows=check_contract(c,b06,b00,b01,b04,b05)
        if args.source_zip is None and args.native_inventory is None and not args.stage:
            print(json.dumps({"status":"B07_PREFLIGHT_METADATA_READY_NOT_STAGED",
                "maps":len(rows),"tilesets":[1,31],
                "installable":False,"r07_complete":False,
                "phase_b_approved":0},ensure_ascii=False,indent=2))
            return 0
        if args.source_zip is None or args.native_inventory is None:
            blocked("para converter e necessario fornecer ZIP doador E ZIP B01")
        source_checked=verify_source_zip(args.source_zip,b06,b00)
        native_checked=verify_native_zip(args.native_inventory,b06,b05)
        inventory,raw=unpack_native(args.native_inventory)
        if args.stage:
            check_current_game(args.game_data,inventory,inventory["physical_map_ids"])
        files,report=build_files(
            args.source_zip,raw["MapInfos.rxdata"],raw["Tilesets.rxdata"],
            rows,source_root=b06["source_zip_internal_root"])
        dry=preview(ROOT,args.label,files)
        if args.stage:
            if not args.expected_sha or args.expected_sha!=dry["plan_sha256"]:
                blocked("antes de stage, execute dry-run e confirme --expected-sha")
            transaction=stage(ROOT,args.label,files,args.expected_sha)
        else:
            if args.expected_sha:blocked("--expected-sha so pode ser usado com --stage")
            transaction=dry
        print(json.dumps({**report,**source_checked,**native_checked,
            "transaction":transaction},ensure_ascii=False,indent=2))
        return 0
    except (ValueError,KeyError,TypeError,IndexError,OverflowError,OSError,
            zipfile.BadZipFile,UnicodeError) as exc:
        print(str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
