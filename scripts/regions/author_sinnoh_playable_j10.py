#!/usr/bin/env python3
"""J10: compile FIVE HUMAN-DRAWN Sinnoh map drafts into private RMXP sources.

No map designs, positions, R07 IDs, map events, coordinates, permissions or
Game.exe/JoiPlay evidence are fabricated. A human must supply 3 full tile
layers of each of the five missing locations, with a hash-pinned local
authorized tileset image. Outputs are original *geometry-only* RPG::Map
RXDATA in ignored .blue-work, not installable or redistributable releases.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile
import zlib

ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT/"scripts/regions"):
    if str(p) not in sys.path:sys.path.insert(0,str(p))

from audit_sinnoh_playable_j09 import (
    authored_five,audit_map,safe_private,source_catalog,STAGE_DIR)
from server.ruby_marshal import RubyObject,RubyData
from stage import serialize
from build_johto_events import EVENT_CLASSES

DRAFT_DIR="sinnoh-j10-drafts"
TILESET_DIR="sinnoh-j10-tilesets"
PNG=b"\x89PNG\r\n\x1a\n"
SHA=re.compile(r"[a-f0-9]{64}\Z")
IMAGE=re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}\.png\Z")
REVIEW=re.compile(r"[^\r\n<>]{12,220}\Z")
KEYS={
    "schema","region","stage","symbol","kind","width","height",
    "tileset_id","tileset_png","tileset_sha256","tileset_permission_reference",
    "author_reference","authored_by_user","geometry_reviewed_locally",
    "layers","events","destination_map_id","native_gameplay_verified",
}
KIND="HUMAN_AUTHORED_PRIVATE_GEOMETRY_NOT_NATIVE_APPROVED"
LAYER_COUNT=3

def fail(code):
    raise ValueError("SINNOH_J10_BLOCKED:"+code)

def digest(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def _read_regular(path:Path,limit:int)->bytes:
    if (path.is_symlink() or not path.is_file()
            or not 0<path.stat().st_size<=limit):
        fail("UNSAFE_MISSING_OR_OVERSIZED_INPUT")
    return path.read_bytes()

def parse_png(raw:bytes)->tuple[int,int]:
    # Check native tileset dimensions and IHDR checksum in immutable local
    # source. This validates file structure, NOT image rights or gameplay.
    if not PNG==raw[:8] or not 100<=len(raw)<=32_000_000:
        fail("LOCAL_TILESET_PNG_INVALID")
    size=struct.unpack_from(">I",raw,8)[0]
    if size!=13 or raw[12:16]!=b"IHDR":
        fail("LOCAL_TILESET_PNG_IHDR_MISSING")
    w,h=struct.unpack_from(">II",raw,16)
    crc=struct.unpack_from(">I",raw,29)[0]
    if (zlib.crc32(raw[12:29])&0xffffffff)!=crc:
        fail("LOCAL_TILESET_PNG_HEADER_CRC")
    if (w!=256 or h<96 or h>8192 or h%32
            or raw[24]!=8 or raw[25] not in (2,6)
            or b"IEND" not in raw[-40:]):
        fail("LOCAL_TILESET_PNG_NOT_RMXP_256PX")
    return w,h

def missing_symbols(project:Path)->list[str]:
    catalog=source_catalog(project)
    rows=catalog.get("maps")
    if not isinstance(rows,list):fail("J02_SOURCE_CATALOG_MISSING")
    missing=[r["symbol"] for r in rows if r.get("source_id") is None]
    if len(missing)!=5 or len(set(missing))!=5:
        fail("J02_FIVE_MISSING_MAP_SYMBOLS_CHANGED")
    return missing

def _private_subdir(project:Path, subdir:str)->Path:
    project=Path(project).absolute()
    work=project/".blue-work"
    if not project.is_dir() or project.is_symlink() or work.is_symlink():
        fail("PROJECT_WORKSPACE_INVALID")
    return work/subdir

def validate_draft(project:Path,symbol:str)->tuple[dict,bytes,dict]:
    if symbol not in missing_symbols(project):fail("NON_MISSING_MAP_SYMBOL")
    drafts=_private_subdir(project,DRAFT_DIR)
    pngs=_private_subdir(project,TILESET_DIR)
    path=safe_private(project,drafts/(symbol+".json"),kind="HUMAN_DRAFT")
    try: raw=_read_regular(path,2_500_000)
    except (OSError,ValueError):raise
    try: data=json.loads(raw)
    except (UnicodeError,ValueError):fail("DRAFT_NOT_JSON")
    if (type(data) is not dict or set(data)!=KEYS
            or (data["schema"],data["region"],data["stage"],data["kind"])!=
            (1,"SINNOH","J10",KIND)
            or data["symbol"]!=symbol
            or data["events"]!=[]
            or data["destination_map_id"] is not None
            or data["native_gameplay_verified"] is not False
            or data["authored_by_user"] is not True
            or data["geometry_reviewed_locally"] is not True
            or type(data["author_reference"]) is not str
            or not REVIEW.fullmatch(data["author_reference"])
            or type(data["tileset_permission_reference"]) is not str
            or not REVIEW.fullmatch(data["tileset_permission_reference"])):
        fail("DRAFT_MUST_BE_ORIGINALLY_AUTHORED_AND_REVIEWED")
    w,h,tid=data["width"],data["height"],data["tileset_id"]
    if (type(w) is not int or type(h) is not int
            or not 12<=w<=120 or not 10<=h<=120
            or w*h>14_400 or type(tid) is not int
            or not 1<=tid<=999):
        fail("MAP_SIZE_OR_TILESET_ID_NOT_HUMAN_VALID")
    img=data["tileset_png"]
    if type(img) is not str or not IMAGE.fullmatch(img):
        fail("INVALID_TILESET_PNG_BASENAME")
    imagepath=safe_private(project,pngs/img,kind="LOCAL_TILESET")
    rawpng=_read_regular(imagepath,32_000_000)
    if (type(data["tileset_sha256"]) is not str
            or not SHA.fullmatch(data["tileset_sha256"])
            or digest(rawpng)!=data["tileset_sha256"]):
        fail("TILESET_CHANGED_OR_RIGHTS_REFERENCE_MISSING")
    _,ih=parse_png(rawpng)
    # Native XP tileset: IDs 384 + 8 columns per 32px image row.
    max_id=384+8*(ih//32)-1
    layers=data["layers"]
    if type(layers) is not list or len(layers)!=3:
        fail("EXACTLY_THREE_EXPLICIT_LAYERS_REQUIRED")
    result=[];coverage=set();distinct=set();lower=[];upper=0
    for z,layer in enumerate(layers):
        if type(layer) is not list or len(layer)!=w*h:
            fail("FULL_EXPLICIT_LAYERS_REQUIRED")
        for i,tile in enumerate(layer):
            if (type(tile) is not int or
                    (tile!=0 and not 384<=tile<=max_id)):
                fail("TILE_OUT_OF_LICENSED_IMAGE_RANGE")
            result.append(tile)
            if tile:
                coverage.add(i);distinct.add(tile)
                if z==0:lower.append(tile)
                else:upper+=1
    if (len(lower)<w*h*3//5 or len(coverage)<w*h*7//10
            or len(distinct)<4 or upper<4):
        fail("DRAFT_HAS_NO_MEANINGFUL_HAND_PAINTED_TERRAIN")
    # Full painted geometry can be produced; no passability or coordinates
    # are inferred. Those require J11 and an actual tileset passage table.
    info={"symbol":symbol,"width":w,"height":h,"tileset_id":tid,
          "tileset_png":img,"tileset_sha256":data["tileset_sha256"],
          "draft_sha256":digest(raw),
          "painted_tiles":sum(x!=0 for x in result),
          "distinct_tile_ids":len(distinct),
          "events_supplied":0,
          "permission_human_attested_not_independently_verified":True,
          "no_R07_destination_map_id_assigned":True}
    return data,rawpng,info

def build_rxdata(data:dict,rawpng:bytes)->bytes:
    w,h=data["width"],data["height"]
    cells=[0]*(3*w*h)
    for z in range(3):
        for idx,value in enumerate(data["layers"][z]):
            cells[idx+z*w*h]=value
    table=(struct.pack("<5I",3,w,h,3,len(cells))
           +struct.pack("<"+str(len(cells))+"H",*cells))
    silent=lambda:RubyObject("RPG::AudioFile",
            {"@name":b"","@volume":80,"@pitch":100})
    native=RubyObject("RPG::Map",{
        "@tileset_id":data["tileset_id"],
        "@width":w,"@height":h,
        "@autoplay_bgm":False,"@bgm":silent(),
        "@autoplay_bgs":False,"@bgs":silent(),
        "@encounter_list":[],"@encounter_step":30,
        "@data":RubyData("Table",table),
        "@events":{},
    })
    raw=serialize(native,EVENT_CLASSES)
    structure=audit_map(raw)
    if (structure["width"]!=w or structure["height"]!=h
            or structure["foreign_events_not_imported"]!=0):
        fail("GENERATED_RMXP_ROUND_TRIP_MISMATCH")
    return raw

def preflight(project:Path)->tuple[dict[str,bytes],dict]:
    project=Path(project).absolute()
    symbols=missing_symbols(project)
    blobs={};infos={};tilesets=set()
    for symbol in symbols:
        data,png,info=validate_draft(project,symbol)
        raw=build_rxdata(data,png)
        blobs[symbol+".rxdata"]=raw
        info["rxdata_sha256"]=digest(raw)
        infos[symbol]=info
        tilesets.add(info["tileset_sha256"])
    # Every scene must be separately authored. No cloned interiors allowed.
    if len({digest(x) for x in blobs.values()})!=5:
        fail("FIVE_SCENES_ARE_DUPLICATE_COPIES")
    report={
        "schema":1,"region":"SINNOH","stage":"J10",
        "status":"FIVE_HUMAN_DRAFTS_STRUCTURALLY_VALID_NOT_NATIVE_APPROVED",
        "maps":infos,"map_count":5,
        "distinct_tileset_image_sha256":sorted(tilesets),
        "all_geometry_exported_only_to_private_directory":True,
        "permissions_independently_approved":False,
        "r07_mapids_approved":False,"r08_full_asset_rights_approved":False,
        "r09_game_exe_or_joiplay_tested":False,
        "can_install":False,"can_publish":False,
        "native_maps_installed":0,"native_qa_cases_passed":0,
    }
    return blobs,report

def private_build(project:Path)->dict:
    project=Path(project).absolute()
    blobs,report=preflight(project)
    work=_private_subdir(project,STAGE_DIR)
    if work.exists() or work.is_symlink():
        fail("AUTHORED_MAPS_ALREADY_EXIST_NEVER_OVERWRITE")
    parent=work.parent
    parent.mkdir(parents=True,exist_ok=True)
    if parent.is_symlink():fail("SYMLINK_WORKSPACE")
    temp=Path(tempfile.mkdtemp(prefix=".sinnoh-j10-atomic-",dir=parent))
    try:
        for name,blob in blobs.items():
            with (temp/name).open("xb") as file:file.write(blob)
        # Reuse the independent J09 five-map intake for a second check.
        check=authored_five(project,temp,source_catalog(project))
        if (len(check)!=5 or
                any(check[s]["sha256"]!=report["maps"][s]["rxdata_sha256"]
                    for s in check)):
            fail("INDEPENDENT_J09_RECHECK_FAILED")
        if work.exists() or work.is_symlink():
            fail("AUTHORED_MAPS_CREATED_BY_ANOTHER_PROCESS")
        temp.rename(work)
    finally:
        if temp.exists():shutil.rmtree(temp)
    return {**report,"private_source_directory":str(work),
            "actual_original_map_files_written":5,
            "ready_for_R07_R08_REVIEW_ONLY":True}

def main(argv=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--build",action="store_true",
                        help="write exactly five original files only after all private drafts validate")
    args=parser.parse_args(argv)
    try:
        _,report=preflight(args.project) if not args.build else (None,private_build(args.project))
    except (OSError,ValueError,TypeError,KeyError,struct.error) as exc:
        print("SINNOH_J10_BLOQUEADO:"+str(exc),file=sys.stderr)
        return 2
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
