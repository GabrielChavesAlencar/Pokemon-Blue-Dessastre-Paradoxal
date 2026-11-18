#!/usr/bin/env python3
"""Sinnoh J04: compile 24 Blue-authored events for nine VERIFIED private maps.

Input is a hash-sealed *private* nine-map stage, a complete CH06-validated
event spec with real coordinates, a current Decades MapInfos baseline and
explicit local sprite attestations. The public draft has no coordinates or
five required maps and MUST fail closed. No Game.exe, saves, donor events,
ROM, or main-game writes. This does not implement NPC gameplay (J05).
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
for path in (ROOT,ROOT/"scripts/regions"):
    if str(path) not in sys.path:
        sys.path.insert(0,str(path))

from audit_sinnoh_rxdata import read_marshal
from audit_sinnoh_twinleaf_events import (MAPS,HANDLERS,BALLS,audit,read_json,
                                          SCHEMA,SPEC)
from bind_sinnoh_playable_j02 import game_inventory,local_input,SHA
from build_johto_events import ruby,event_page,EVENT_CLASSES
from convert_sinnoh_geometry import table_valid,PNG
from prepare_sinnoh_playable_j03 import stage_verify
from server.ruby_marshal import RubyObject,RubyData
from sinnoh_staging_transaction import (LABEL,preview,stage,rollback,stage_root)
from stage import serialize

HANDLER_METHODS={
    "mother":"BlueSinnohPilot.mother",
    "barry_intro":"BlueSinnohPilot.barry_intro",
    "rowan_briefcase":"BlueSinnohPilot.rowan_briefcase",
    "barry_rival":"BlueSinnohPilot.barry_rival",
    "rowan_pokedex":"BlueSinnohPilot.rowan_pokedex",
}
STARTER_SPECIES={"TURTWIG","CHIMCHAR","PIPLUP"}
SPRITE_RE=re.compile(r"[A-Za-z0-9_ .()-]{1,100}\Z")
REVIEW_KEYS={"schema","region","mode","baseline_mapinfos_sha256",
             "map_stage_plan_sha256","reviewed_locally","sprite_sha256"}
MAX_IMAGE=8*1024*1024

def blocked(code):
    raise ValueError("SINNOH_J04_BLOCKED:"+code)

def sha(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def native_baseline(game_data:Path):
    game_data=game_data.absolute()
    if (game_data.is_symlink() or not game_data.is_dir()
            or any((game_data/k).is_symlink()
                   for k in ("MapInfos.rxdata","Tilesets.rxdata"))
            or any(not (game_data/k).is_file()
                   for k in ("MapInfos.rxdata","Tilesets.rxdata"))):
        blocked("NATIVE_DATA_MISSING")
    mapinfos_sha,occupied=game_inventory(game_data)
    tiles_path=game_data/"Tilesets.rxdata"
    if tiles_path.stat().st_size>32_000_000:
        blocked("NATIVE_TILESETS_OVERSIZED")
    native_maps=read_marshal((game_data/"MapInfos.rxdata").read_bytes(),"NATIVE_INFOS")
    native_tiles=read_marshal(tiles_path.read_bytes(),"NATIVE_TILES")
    if (type(native_maps) is not dict or type(native_tiles) is not list
            or len(native_tiles)>5000):
        blocked("NATIVE_DATA_NOT_RMXP")
    return mapinfos_sha,sha(tiles_path.read_bytes()),occupied,native_maps,native_tiles

def passability_table(raw):
    if isinstance(raw,list):
        if len(raw)>20_000 or not raw or any(type(v) is not int or not 0<=v<=255 for v in raw):
            blocked("PASSAGES_INVALID")
        return raw
    if isinstance(raw,RubyData) and raw.name=="Table" and len(raw.data)>=20:
        dims,w,h,z,n=struct.unpack_from("<5I",raw.data)
        if (dims!=1 or h!=1 or z!=1 or n!=w or w>20000
                or len(raw.data)!=20+2*n):
            blocked("PASSAGES_TABLE_INVALID")
        return struct.unpack_from("<"+str(n)+"H",raw.data,20)
    blocked("PASSAGES_REQUIRED")

def passable_point(world,tilesets,x,y):
    data=world.attrs
    w,h,tid=data["@width"],data["@height"],data["@tileset_id"]
    if not isinstance(tilesets,list) or type(tid) is not int or not 0<tid<len(tilesets):
        blocked("MAP_TILESET_MISSING")
    tile=tilesets[tid]
    if not isinstance(tile,RubyObject) or tile.name!="RPG::Tileset":
        blocked("MAP_TILESET_INVALID")
    passages=passability_table(tile.attrs.get("@passages"))
    raw=data["@data"]
    if not table_valid(raw,w,h):
        blocked("MAP_TILE_TABLE_INVALID")
    count=w*h*3
    cells=struct.unpack_from("<"+str(count)+"H",raw.data,20)
    nonzero=False
    for layer in range(3):
        tile_id=cells[layer*w*h+y*w+x]
        if tile_id==0:
            continue
        nonzero=True
        if tile_id>=len(passages):
            blocked("TILE_PASSAGES_MISSING")
        # Conservative: require all four directions usable; never infer stairs.
        if passages[tile_id]&0x0f:
            blocked("EVENT_TILE_BLOCKED")
    if not nonzero:
        blocked("EVENT_TILE_VOID")
    return True

def _stage_input(root,label,stage_sha):
    if (not isinstance(label,str) or not LABEL.fullmatch(label)
            or not label.startswith("j04-")
            or not isinstance(stage_sha,str) or not SHA.fullmatch(stage_sha)):
        blocked("INPUT_STAGE_ID_INVALID")
    stage_verify(root,label,stage_sha)
    folder=stage_root(root)/f"{label}-{stage_sha[:16]}"
    receipt=folder/"stage-manifest.json"
    meta=json.loads(receipt.read_text("utf-8"))
    return folder,{row["path"]:row["sha256"] for row in meta["files"]},meta

def _sprites(root,review,baseline,stage_sha,needed,folder,manifest):
    if (type(review) is not dict or set(review)!=REVIEW_KEYS
            or (review.get("schema"),review.get("region"),review.get("mode"))!=
            (1,"SINNOH","J04_PRIVATE_SPRITE_REVIEW")
            or review.get("baseline_mapinfos_sha256")!=baseline
            or review.get("map_stage_plan_sha256")!=stage_sha
            or review.get("reviewed_locally") is not True
            or type(review.get("sprite_sha256")) is not dict):
        blocked("SPRITE_REVIEW_NOT_VERIFIED")
    images=review["sprite_sha256"]
    expected={f"Graphics/Characters/{name}.png" for name in needed}
    if set(images)!=expected:
        blocked("SPRITE_SET_INCOMPLETE_OR_EXTRA")
    for path in sorted(expected):
        if path not in manifest or type(images[path]) is not str or not SHA.fullmatch(images[path]):
            blocked("SPRITE_HASH_NOT_ATTESTED")
        original=folder/path
        if original.is_symlink() or not original.is_file() or original.stat().st_size>MAX_IMAGE:
            blocked("SPRITE_FILE_MISSING")
        image=original.read_bytes()
        if len(image)<12 or not image.startswith(PNG) or sha(image)!=images[path] or manifest[path]!=images[path]:
            blocked("SPRITE_CHANGED_OR_INVALID")

def _preserve_native_infos(stage_infos,native_infos,occupied,dest_ids):
    if type(stage_infos) is not dict:
        blocked("STAGED_MAPINFOS_INVALID")
    for key,item in native_infos.items():
        if key not in stage_infos or serialize(stage_infos[key])!=serialize(item):
            blocked("STAGE_CHANGED_EXISTING_REGION_MAPINFO")
    if any(mid in occupied or mid in native_infos for mid in dest_ids):
        blocked("MAPID_ALREADY_USED")
    if any(mid not in stage_infos for mid in dest_ids):
        blocked("DESTINATION_MAPINFO_MISSING")

def _preserve_native_tiles(stage_tiles,native_tiles):
    if (type(stage_tiles) is not list or len(stage_tiles)<len(native_tiles)
            or len(stage_tiles)>5000):
        blocked("STAGED_TILESETS_INVALID")
    for i,tile in enumerate(native_tiles):
        if serialize(stage_tiles[i])!=serialize(tile):
            blocked("STAGE_CHANGED_EXISTING_REGION_TILESET")

def compile_private_events(root:Path,input_label:str,input_sha:str,
                           spec:dict,review:dict,game_data:Path,
                           reservations:dict)->tuple[dict[str,bytes],dict]:
    """Create a complete stage overlay in memory; no external writes."""
    root=root.absolute()
    folder,manifest,receipt=_stage_input(root,input_label,input_sha)
    baseline,tiles_sha,occupied,native_infos,native_tiles=native_baseline(game_data)
    if (type(reservations) is not dict or set(reservations)!=
            {"schema","region","mode","baseline_mapinfos_sha256","protected_ids"}
            or (reservations["schema"],reservations["region"],reservations["mode"]) !=
                (1,"SINNOH","LOCAL_RESERVATIONS_CANDIDATE")
            or reservations["baseline_mapinfos_sha256"]!=baseline
            or type(reservations["protected_ids"]) is not list
            or len(reservations["protected_ids"])>5000
            or any(type(i) is not int or i<1 or i>999 for i in reservations["protected_ids"])
            or len(set(reservations["protected_ids"]))!=len(reservations["protected_ids"])):
        blocked("RESERVATIONS_NOT_CURRENT")
    protected=set(reservations["protected_ids"])
    schema=read_json(root/"data/regions/sinnoh-twinleaf-events.schema.json")
    # Exact schema and topology; no hand-edited list of arbitrary event commands.
    map_rows=spec.get("maps") if type(spec) is dict else None
    if (not isinstance(map_rows,list) or len(map_rows)!=9
            or [m.get("symbol") for m in map_rows if isinstance(m,dict)]!=list(MAPS)):
        blocked("REQUIRE_NINE_ORDERED_MAPS")
    sizes={}
    dests=[]
    objects={}
    for row in map_rows:
        mid=row.get("map_id")
        if type(mid) is not int or not 442<=mid<=517 or mid in protected or mid in occupied or mid in dests:
            blocked("UNSAFE_MAPID_OR_DUPLICATE")
        dests.append(mid)
        path=f"Data/Map{mid:03d}.rxdata"
        if path not in manifest or type(row.get("map_sha256")) is not str:
            blocked("STAGE_MAP_MISSING")
        source=folder/path
        if source.is_symlink() or not source.is_file() or source.stat().st_size>32_000_000:
            blocked("STAGE_MAP_UNSAFE")
        raw=source.read_bytes()
        if sha(raw)!=row["map_sha256"] or sha(raw)!=manifest[path]:
            blocked("MAP_SHA_CHANGED_OR_SPEC_STALE")
        world=read_marshal(raw,"J04_MAP")
        if not isinstance(world,RubyObject) or world.name!="RPG::Map":
            blocked("NOT_RMXP_MAP")
        w,h=world.attrs.get("@width"),world.attrs.get("@height")
        if (type(w) is not int or type(h) is not int or
                not 2<=w<=500 or not 2<=h<=500 or
                not table_valid(world.attrs.get("@data"),w,h)
                or not any(world.attrs["@data"].data[20:])):
            blocked("MISSING_NONEMPTY_REAL_GEOMETRY")
        if world.attrs.get("@events")!={} or world.attrs.get("@autoplay_bgm") or world.attrs.get("@autoplay_bgs"):
            blocked("DONOR_EVENTS_OR_AUDIO_PRESENT")
        sizes[row["symbol"]]=[w,h]
        objects[row["symbol"]]=world
    # This also verifies explicit 16 reverse warps, five handlers, 3 unique
    # starter balls, all coordinates/arrivals, the requested bedroom spawn.
    audit(spec,schema,dimensions=sizes)
    passable_point(objects["SINNOH_PLAYER_BEDROOM"],
                   read_marshal((folder/"Data/Tilesets.rxdata").read_bytes(),"START_TILESETS"),
                   spec["start"]["x"],spec["start"]["y"])
    other_maps=set(re.fullmatch(r"Data/Map(\d{3,5})\.rxdata",name).group(1)
                   for name in manifest if re.fullmatch(r"Data/Map(\d{3,5})\.rxdata",name))
    if len(other_maps)!=9 or set(other_maps)!={str(mid).zfill(3) for mid in dests}:
        blocked("STAGE_CONTAINS_WRONG_MAP_SET")
    infos=read_marshal((folder/"Data/MapInfos.rxdata").read_bytes(),"STAGE_INFOS")
    tiles=read_marshal((folder/"Data/Tilesets.rxdata").read_bytes(),"STAGE_TILESETS")
    _preserve_native_infos(infos,native_infos,occupied,dests)
    _preserve_native_tiles(tiles,native_tiles)
    all_events=[e for m in map_rows for e in m["events"]]
    expected_sprites=set()
    for e in all_events:
        if e["kind"]!="warp":
            s=e["sprite"]
            if type(s) is not str or not SPRITE_RE.fullmatch(s):
                blocked("SPRITE_NAME_INVALID")
            expected_sprites.add(s)
    _sprites(root,review,baseline,input_sha,expected_sprites,folder,manifest)
    mapids={m["symbol"]:m["map_id"] for m in map_rows}
    output={name:(folder/name).read_bytes() for name in manifest}
    compiled_keys=set()
    for row in map_rows:
        mid=row["map_id"]
        world=objects[row["symbol"]]
        events={}
        occupied_positions=set()
        for i,e in enumerate(row["events"],start=1):
            x,y=e["x"],e["y"]
            if (x,y) in occupied_positions:
                blocked("DUPLICATE_POSITION")
            occupied_positions.add((x,y))
            passable_point(world,tiles,x,y)
            if e["kind"]=="warp":
                dest=e["destination"]
                xx,yy=e["arrival_x"],e["arrival_y"]
                passable_point(objects[dest],tiles,xx,yy)
                page=event_page(warp=(mapids[dest],xx,yy),touch=True)
            elif e["kind"]=="handler":
                method=HANDLER_METHODS.get(e["handler"])
                if not method or HANDLERS.get(e["key"])!=(row["symbol"],e["handler"]):
                    blocked("HANDLER_NOT_BLUE_ALLOWLISTED")
                page=event_page(script=method,sprite=e["sprite"],
                                touch=(e["trigger"]=="touch"))
            elif e["kind"]=="starter_ball":
                species=e["species"]
                if species not in STARTER_SPECIES or BALLS.get(e["key"])!=(row["symbol"],species):
                    blocked("STARTER_NOT_ALLOWLISTED")
                # Fixed literal generated by us, never from user Ruby source.
                page=event_page(script=f"BlueSinnohPilot.choose_starter(:{species})",
                                sprite=e["sprite"],touch=False)
            else:
                blocked("UNKNOWN_EVENT_TYPE")
            if e["key"] in compiled_keys:
                blocked("DUPLICATE_EVENT_NAME")
            compiled_keys.add(e["key"])
            events[i]=ruby("RPG::Event",id=i,name=e["key"].encode("ascii"),
                           x=x,y=y,pages=[page])
        result=copy.deepcopy(world)
        result.attrs["@events"]=events
        path=f"Data/Map{mid:03d}.rxdata"
        encoded=serialize(result,EVENT_CLASSES)
        audit_map=read_marshal(encoded,"COMPILED_BLUE_MAP")
        if len(audit_map.attrs.get("@events",{}))!=len(events):
            blocked("EVENT_SERIALIZATION_FAILURE")
        output[path]=encoded
    # The nine-map J04 overlay is still private. No runtime handlers, PBS,
    # native QA or independent rights approval are implied.
    if len(compiled_keys)!=24 or len(output)<11:
        blocked("INCOMPLETE_BLUE_EVENT_COMPILATION")
    if sha((game_data/"MapInfos.rxdata").read_bytes())!=baseline or sha((game_data/"Tilesets.rxdata").read_bytes())!=tiles_sha:
        blocked("NATIVE_BASELINE_CHANGED_DURING_COMPILATION")
    report={
        "schema":1,"region":"SINNOH","stage":"J04",
        "mode":"PRIVATE_BLUE_EVENT_OVERLAY_NOT_INSTALLABLE",
        "status":"24_OWNED_EVENTS_COMPILED_IN_MEMORY",
        "maps_in_source_stage_verified":9,
        "events_compiled":24,"warps_compiled":16,
        "npc_handlers_compiled":5,"starter_balls_compiled":3,
        "sprite_files_hash_checked":len(expected_sprites),
        "input_stage_plan_sha256":input_sha,
        "baseline_mapinfos_sha256":baseline,
        "donor_events_imported":0,"donor_scripts_imported":0,
        "story_handlers_runtime_verified":False,
        "real_map_assets_rights_independently_verified":False,
        "future_mapid_reservations_globally_verified":False,
        "start_position_native_verified":False,
        "r07_complete":False,"r08_complete":False,"r09_complete":False,
        "game_modified":False,"saves_read_or_modified":False,
        "can_install":False,"native_playable":False,
        "next_stage":"J05",
    }
    return output,report

def no_real_inputs(root):
    draft=read_json(root/"data/regions/sinnoh-twinleaf-events.json")
    schema=read_json(root/"data/regions/sinnoh-twinleaf-events.schema.json")
    audit(draft,schema)
    return {
        "schema":1,"region":"SINNOH","stage":"J04",
        "status":"BLOCKED_FIVE_REAL_MAPS_COORDINATES_AND_ASSETS_MISSING",
        "planned_warps":16,"planned_npc_handlers":5,
        "planned_starter_balls":3,"compiled_native_events":0,
        "nine_map_stage_verified":False,
        "sprites_verified":False,
        "r07_complete":False,"r08_complete":False,"r09_complete":False,
        "main_game_modified":False,"saves_read_or_modified":False,
        "can_install":False,"native_playable":False,
        "next_stage":"J05",
    }

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--input-label",type=str)
    parser.add_argument("--input-sha",type=str)
    parser.add_argument("--game-data",type=Path)
    parser.add_argument("--spec",type=Path)
    parser.add_argument("--reservations",type=Path)
    parser.add_argument("--sprite-review",type=Path)
    parser.add_argument("--output-label",default="j04-events")
    parser.add_argument("--stage",action="store_true")
    parser.add_argument("--expected-dry-run")
    parser.add_argument("--verify-stage",action="store_true")
    parser.add_argument("--rollback",action="store_true")
    args=parser.parse_args(argv)
    try:
        root=args.project.absolute()
        if root.is_symlink() or not root.is_dir():
            blocked("PROJECT_INVALID")
        actions=sum((args.stage,args.verify_stage,args.rollback))
        if actions>1:
            blocked("MULTIPLE_ACTIONS")
        if args.verify_stage or args.rollback:
            if (not args.expected_dry_run or not args.output_label.startswith("j04-")
                    or any((args.input_label,args.input_sha,args.game_data,
                            args.spec,args.reservations,args.sprite_review))):
                blocked("ROLLBACK_OR_VERIFY_ARGS")
            if args.verify_stage:
                result=stage_verify(root,args.output_label,args.expected_dry_run)
            else:
                result=rollback(root,args.output_label,args.expected_dry_run)
        elif not any((args.input_label,args.input_sha,args.game_data,
                      args.spec,args.reservations,args.sprite_review)):
            if args.stage or args.expected_dry_run:
                blocked("CANNOT_STAGE_MISSING_MAPS")
            result=no_real_inputs(root)
        else:
            if not all((args.input_label,args.input_sha,args.game_data,
                        args.spec,args.reservations,args.sprite_review)
                       ) or not args.output_label.startswith("j04-"):
                blocked("SIX_REQUIRED_INPUTS")
            spec=local_input(root,args.spec)
            reserved=local_input(root,args.reservations)
            review=local_input(root,args.sprite_review)
            files,info=compile_private_events(
                root,args.input_label,args.input_sha,spec,review,
                args.game_data,reserved)
            dry=preview(root,args.output_label,files)
            if args.stage:
                if not args.expected_dry_run:
                    blocked("EXPECTED_DRYRUN_SHA_REQUIRED")
                result={**info,"transaction":stage(root,args.output_label,files,
                                                    args.expected_dry_run)}
            else:
                if args.expected_dry_run:
                    blocked("SHA_GIVEN_WITHOUT_STAGE")
                result={**info,"transaction":dry}
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,ImportError,
            IndexError,OverflowError,struct.error):
        print("SINNOH_J04_BLOCKED:UNVERIFIED_LOCAL_INPUT",file=sys.stderr)
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if result.get("status") in (
        "24_OWNED_EVENTS_COMPILED_IN_MEMORY",
        "LOCAL_PRIVATE_STAGE_HASHES_OK_NOT_NATIVE_APPROVAL"
    ) or result.get("mode")=="LOCAL_ROLLBACK":
        return 0
    return 2

if __name__=="__main__":
    raise SystemExit(main())
