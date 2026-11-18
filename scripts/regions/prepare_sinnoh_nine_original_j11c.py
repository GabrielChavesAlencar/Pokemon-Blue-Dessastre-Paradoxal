#!/usr/bin/env python3
"""J11-C: build INERT RMXP nine-map QA overlays from ONLY original J11-B.

No native install, Game.exe, JoiPlay, personal saves, rights attestations,
R07 approvals or real map IDs are invented. Without private local baseline
AND a real R07 receipt the CLI only generates a read-only blocked plan.
A private overlay always remains UNINSTALLABLE until independent R08/R09.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import struct
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
for folder in (ROOT,ROOT/"scripts/regions"):
    if str(folder) not in sys.path:sys.path.insert(0,str(folder))

import generate_sinnoh_original_j10a as j10a
import generate_sinnoh_four_exteriors_j11b as j11b
import audit_sinnoh_playable_j11 as j11
from audit_sinnoh_rxdata import attrs,read_marshal
from audit_sinnoh_twinleaf_events import MAPS,SPEC,SCHEMA,audit as event_audit
from compile_sinnoh_playable_j04 import passability_table,passable_point
from convert_sinnoh_geometry import table_valid
from server.ruby_marshal import RubyObject,RubyData
from stage import serialize

STAGE="J11-C"
OUTPUT="sinnoh-j11c-private-qa-overlay"
R07_MIN,R07_MAX=442,517
SHA=re.compile(r"[a-f0-9]{64}\Z")
GRAPHIC={
    "J10A_INTERIORS":("OriginalJ10A.png","SN_J11C_Original_Interior"),
    "J11B_EXTERIORS":("ExteriorJ11B.png","SN_J11C_Original_Exterior"),
}
PASSAGE_LIMIT=416
# Registry is only a proposed behavior: engine and human collision checks pending.
FORBIDDEN=frozenset(j10a.BLOCKS)|{j10a.WATER,j10a.SHORE}
PREVIEW_DIR="sinnoh-j11c-qa-only"

def fail(reason):
    raise ValueError("SINNOH_J11C_BLOCKED:"+reason)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def table1(values):
    if not isinstance(values,list) or not values or len(values)>20000:
        fail("INVALID_1D_TABLE")
    if any(type(v) is not int or v<0 or v>65535 for v in values):
        fail("INVALID_1D_TABLE_VALUE")
    return RubyData("Table",struct.pack("<5I",1,len(values),1,1,len(values))+
                    struct.pack("<"+str(len(values))+"H",*values))

def decode1(data):
    if not isinstance(data,RubyData) or data.name!="Table" or len(data.data)<20:
        fail("RPG_TABLE_MISSING")
    dims,w,h,z,n=struct.unpack_from("<5I",data.data)
    if (dims,w,h,z,n)!=(1,w,1,1,w) or w!=PASSAGE_LIMIT or len(data.data)!=20+2*n:
        fail("RPG_TABLE_DIMENSIONS")
    return list(struct.unpack_from("<"+str(n)+"H",data.data,20))

def proposal(group,png_sha,assigned_id):
    if group not in GRAPHIC or type(assigned_id) is not int or not 1<=assigned_id<5000:
        fail("TILESET_GROUP_OR_ID_NOT_VALID")
    name=GRAPHIC[group][1]
    # Empty tiles other than 0 are conservative blockers; never mark unseen
    # autotiles or unknown tile types as passable.
    passages=[15]*PASSAGE_LIMIT
    passages[0]=0
    priorities=[0]*PASSAGE_LIMIT
    for tid in range(384,416):
        passages[tid]=15 if tid in FORBIDDEN else 0
        priorities[tid]=1 if tid in FORBIDDEN else 0
    tile=RubyObject("RPG::Tileset",{
        "@id":assigned_id,
        "@name":("Sinnoh J11C QA "+group).encode("ascii"),
        "@tileset_name":name.encode("ascii"),
        "@tileset_hue":0,
        "@autotile_names":[b""]*7,
        "@panorama_name":b"","@panorama_hue":0,
        "@fog_name":b"","@fog_hue":0,"@fog_opacity":64,
        "@fog_blend_type":0,"@fog_zoom":100,"@fog_sx":0,"@fog_sy":0,
        "@battleback_name":b"",
        "@passages":table1(passages),
        "@priorities":table1(priorities),
        "@terrain_tags":table1([0]*PASSAGE_LIMIT),
    })
    return tile

def verify_tile(tile,expected_id):
    if not isinstance(tile,RubyObject) or tile.name!="RPG::Tileset" or tile.attrs.get("@id")!=expected_id:
        fail("NOT_REAL_RPG_TILESET_OBJECT")
    p=decode1(tile.attrs.get("@passages"))
    pr=decode1(tile.attrs.get("@priorities"))
    tags=decode1(tile.attrs.get("@terrain_tags"))
    if (any(p[t] != (15 if t in FORBIDDEN else 0) for t in range(384,416))
        or any(pr[t] != (1 if t in FORBIDDEN else 0) for t in range(384,416))
        or any(tags) or p[0]!=0 or any(p[t]!=15 for t in range(1,384))):
        fail("TILESET_PASSAGES_PRIORITIES_CHANGED")
    if tile.attrs.get("@autotile_names")!=[b""]*7:
        fail("AUTOTILES_REQUIRE_REAL_REVIEW")
    return {"id":expected_id,"passages_entries":len(p),"priority_entries":len(pr),
            "blocking_classes":[tid for tid in range(384,416) if p[tid]],
            "actual_game_collision_tested":False,
            "human_reviewed":False}

def source_audit():
    files,manifest=j11b.generate()
    if (manifest.get("nine_distinct_rxdata_count")!=9
        or manifest.get("mapids_assigned")!=0
        or manifest.get("native_maps_installed")!=0
        or manifest.get("r07_approved") is not False
        or manifest.get("r08_approved") is not False):
        fail("J11B_SOURCE_UNAPPROVED_OR_CHANGED")
    if len({digest(files[s+".rxdata"]) for s in MAPS})!=9:
        fail("MISSING_OR_DUPLICATE_NINE_ORIGINALS")
    if (set(manifest["files_sha256"]) != set(files)-{"manifest.json"}
        or any(digest(files[k])!=h for k,h in manifest["files_sha256"].items())):
        fail("SOURCE_HASHES_CHANGED")
    registries=json.loads(files["tileset-registration-proposal.json"])
    if (set(registries.get("tilesets",{}))!=set(GRAPHIC)
        or registries.get("native_tilesets_rxdata_generated") is not False
        or registries.get("can_install") is not False):
        fail("J11B_TILESET_SOURCE_CORRUPTED")
    for group,(filename,name) in GRAPHIC.items():
        if registries["tilesets"][group]["png_sha256"]!=digest(files[filename]):
            fail("PNG_SHA_OR_SOURCE_GROUP_CHANGED")
        j11.verify_png(files[filename])
    return files,manifest

def event_contract():
    spec=j11.read_json(ROOT/"data/regions/sinnoh-twinleaf-events.json")
    schema=j11.read_json(ROOT/"data/regions/sinnoh-twinleaf-events.schema.json")
    event_audit(spec,schema)
    counts=j11.verify_contracts(ROOT)
    if counts["directional_warps"]!=16 or counts["npc_handlers"]!=5 or counts["starter_balls"]!=3:
        fail("CH06_CONTRACT_COUNT_CHANGED")
    symbol_map={row["symbol"]:row for row in spec["maps"]}
    topology=[]
    for symbol in MAPS:
        for event in symbol_map[symbol]["events"]:
            if (event["x"] is not None or event["y"] is not None
                or event["verified_position"] is not False):
                fail("EVENT_COORDINATES_WERE_FABRICATED")
            row={"source":symbol,"event_key":event["key"],"kind":event["kind"],
                 "coordinate":None,"native_collision_verified":False}
            if event["kind"]=="warp":
                if event["arrival_x"] is not None or event["arrival_y"] is not None or event["verified_arrival"] is not False:
                    fail("WARP_ARRIVAL_COORDINATES_FABRICATED")
                row["destination"]=event["destination"]
                row["arrival"]=None
            else:
                if event["sprite"] is not None or event["verified_sprite"] is not False:
                    fail("NPC_SPRITE_PREMATURELY_APPROVED")
            topology.append(row)
    if len(topology)!=24:fail("J04_EVENT_COUNT_MISMATCH")
    return {"contracts":topology,"counts":counts,"real_coordinates_validated":False,
            "native_j04_events_compiled":False}

def sanitize_map(raw,expected_png_id):
    world=read_marshal(raw,"ORIGINAL_MAP")
    if not isinstance(world,RubyObject) or world.name!="RPG::Map":
        fail("SOURCE_NOT_RMXP_MAP")
    obj=copy.deepcopy(world)
    d=obj.attrs
    w,h=d.get("@width"),d.get("@height")
    if type(w) is not int or type(h) is not int or not table_valid(d.get("@data"),w,h):
        fail("RPG_MAP_THREE_LAYER_TABLE_INVALID")
    if d.get("@tileset_id")!=1 or d.get("@events")!={}:
        fail("SOURCE_ALREADY_BOUND_OR_EVENTS_PRESENT")
    if d.get("@autoplay_bgm") or d.get("@autoplay_bgs"):
        fail("SOURCE_AUDIO_NOT_ALLOWED")
    d["@tileset_id"]=expected_png_id
    encoded=serialize(obj)
    checked=read_marshal(encoded,"STAGED_MAP")
    if checked.attrs["@tileset_id"]!=expected_png_id or checked.attrs["@data"].data!=d["@data"].data or checked.attrs["@events"]!={}:
        fail("RPG_MAP_REMAP_NOT_BYTE_PRESERVING")
    return encoded

def candidate_ids(occupied,protected,ids):
    if (type(ids) is not list or len(ids)!=9 or len(set(ids))!=9
        or any(type(x) is not int or x<R07_MIN or x>R07_MAX for x in ids)):
        fail("R07_NINE_DISTINCT_IDS_REQUIRED")
    if set(ids)&(occupied|protected):
        fail("R07_IDS_COLLIDE_WITH_EXISTING_OR_RESERVED")
    return dict(zip(MAPS,ids))

def validate_baseline(infos,tiles):
    if (type(infos) is not dict or len(infos)>5000
        or any(type(k) is not int or k<=0 or not isinstance(v,RubyObject) or v.name!="RPG::MapInfo" for k,v in infos.items())
        or not isinstance(tiles,list) or len(tiles)>4997
        or any(x is not None and (not isinstance(x,RubyObject) or x.name!="RPG::Tileset") for x in tiles)):
        fail("BASELINE_NOT_SAFE_RMXP")
    if len(tiles)<1 or tiles[0] is not None:
        fail("RPG_TILESET_ZERO_INDEX_RESERVED")
    return True

def mock_or_private_native_overlay(infos,tiles,ids,*,occupied,protected,
                                   baseline_hashes=None,synthetic_fixture=False):
    """Pure in-memory RPG::Map / RPG::Tileset / MapInfos candidate.

    Synthetic fixtures are tests ONLY. For real use, caller must verify
    actual isolated baseline/R07 (separate function). No file writes here.
    """
    validate_baseline(infos,tiles)
    mapping=candidate_ids(occupied|set(infos),protected,ids)
    files,source=source_audit()
    tile_ids={g:len(tiles)+i for i,g in enumerate(GRAPHIC)}
    if any(n>=5000 for n in tile_ids.values()):fail("TILESET_REGISTRY_CAPACITY")
    after_tiles=copy.deepcopy(tiles)
    after_infos=copy.deepcopy(infos)
    blobs={}
    checked_tiles={}
    for group,(filename,gname) in GRAPHIC.items():
        png=files[filename]
        new_id=tile_ids[group]
        candidate=proposal(group,digest(png),new_id)
        checked_tiles[group]=verify_tile(candidate,new_id)
        after_tiles.append(candidate)
        blobs["Graphics/Tilesets/"+gname+".png"]=png
    for symbol in MAPS:
        src=files[symbol+".rxdata"]
        group="J10A_INTERIORS" if symbol in j10a.SYMBOLS else "J11B_EXTERIORS"
        data=sanitize_map(src,tile_ids[group])
        mid=mapping[symbol]
        blobs["Data/Map"+str(mid).zfill(3)+".rxdata"]=data
        after_infos[mid]=RubyObject("RPG::MapInfo",{
            "@name":("[SN J11-C QA] "+symbol).encode("ascii"),
            "@parent_id":0,"@order":100000+mid,
            "@expanded":False,"@scroll_x":0,"@scroll_y":0,
        })
    blobs["Data/MapInfos.rxdata"]=serialize(after_infos)
    blobs["Data/Tilesets.rxdata"]=serialize(after_tiles)
    read_infos=read_marshal(blobs["Data/MapInfos.rxdata"],"OVERLAY_MAPINFOS")
    read_tiles=read_marshal(blobs["Data/Tilesets.rxdata"],"OVERLAY_TILESETS")
    if (any(serialize(read_infos[k])!=serialize(v) for k,v in infos.items())
        or any(serialize(read_tiles[i])!=serialize(v) for i,v in enumerate(tiles))):
        fail("BASELINE_OVERWRITTEN_IN_MEMORY")
    for group,tid in tile_ids.items():
        verify_tile(read_tiles[tid],tid)
    for symbol,mid in mapping.items():
        obj=read_marshal(blobs["Data/Map"+str(mid).zfill(3)+".rxdata"],"QA_MAP")
        if obj.attrs["@tileset_id"] not in tile_ids.values():fail("STAGED_TILESET_NOT_ASSIGNED")
        if len(obj.attrs["@data"].data)!=20+6*obj.attrs["@width"]*obj.attrs["@height"]:
            fail("THREE_LAYERS_NOT_PRESERVED")
    topo=event_contract()
    # Passability: verify chosen entry candidates are clear with native-style
    # Table passages. This remains a local model, NOT real engine testing.
    scene_lookup={s["symbol"]:s for s in j10a.scenes()+j11b.scenes()}
    simulated_passable=0
    for symbol,mid in mapping.items():
        world=read_marshal(blobs["Data/Map"+str(mid).zfill(3)+".rxdata"],"QA_MAP")
        sc=scene_lookup[symbol]
        for x,y in sc["access"]:
            passable_point(world,read_tiles,x,y)
            simulated_passable+=1
    manifest={"schema":1,"region":"SINNOH","stage":STAGE,
        "status":"PRIVATE_QA_RMXP_OVERLAY_UNINSTALLABLE",
        "source_geometries":9,"rpg_map_entries":9,"tilesets_created":2,
        "mapids":mapping,"tileset_ids":tile_ids,
        "candidate_access_points_model_only":simulated_passable,
        "event_contract_counts":{"warps":16,"handlers":5,"starter_balls":3},
        "natively_compiled_events":0,"rights_independently_approved":False,
        "r07_local_attestation_only":not synthetic_fixture,
        "r07_globally_approved":False,"r08_approved":False,"r09_approved":False,
        "synthetic_baseline_fixture":synthetic_fixture,
        "can_install":False,"can_publish":False,"native_maps_installed":0,
        "native_qa_cases_executed":0,"game_exe_tested":False,"joiplay_tested":False,
        "main_game_modified":False,"personal_saves_accessed":False,
        "files_sha256":{path:digest(value) for path,value in sorted(blobs.items())},
        "baseline_source_hashes":baseline_hashes,
        "required_before_native":["INDEPENDENT_R07","INDEPENDENT_R08",
          "REAL_TILESET_PRIORITY_COLLISION_QA","CH06_EVENT_COORDINATES_SPRITES",
          "NATIVE_WINDOWS_43_AND_JOIPLAY_1"]}
    return blobs,manifest

def private_inputs(root:Path,baseline:Path,review:Path):
    root=Path(root).absolute()
    allowed=(root/".blue-work/sinnoh-j11-baseline/Data").absolute()
    if (baseline.absolute()!=allowed or baseline.is_symlink() or baseline.parent.is_symlink()
        or not baseline.is_dir() or root.is_symlink() or not root.is_dir()):
        fail("REQUIRE_ISOLATED_PRIVATE_BASELINE_ONLY")
    work=root/".blue-work"
    if work.is_symlink() or (work/"sinnoh-j11-reviews").is_symlink():
        fail("PRIVATE_SYMLINK_REJECTED")
    reviews=(work/"sinnoh-j11-reviews/r07.json").absolute()
    if review.absolute()!=reviews or review.is_symlink() or not review.is_file():
        fail("REQUIRE_EXISTING_LOCAL_R07_RECEIPT")
    for filename in ("MapInfos.rxdata","Tilesets.rxdata","Scripts.rxdata","System.rxdata"):
        path=baseline/filename
        if path.is_symlink() or not path.is_file() or path.stat().st_size>32_000_000:
            fail("BASELINE_NOT_COMPLETE_OR_SAFE")
    r07=j11.check_r07(root,baseline,review)
    row=j11.read_private_json(root,review)
    ids=row["candidate_sinnoh_ids"]
    info_raw=(baseline/"MapInfos.rxdata").read_bytes()
    tiles_raw=(baseline/"Tilesets.rxdata").read_bytes()
    infos=read_marshal(info_raw,"BASELINE_MAPINFOS")
    tiles=read_marshal(tiles_raw,"BASELINE_TILESETS")
    validate_baseline(infos,tiles)
    # Only J11's real file inventory can validate occupied native slots.
    _,occupied=j11._baseline(root,baseline)
    reserved=set(x for values in row["reserved_by_region"].values() for x in values)
    return (infos,tiles,ids,occupied,reserved,
            {"mapinfos":digest(info_raw),"tilesets":digest(tiles_raw)})

def build_private(root:Path,baseline:Path,review:Path):
    root=Path(root).absolute()
    work=root/".blue-work"
    target=work/OUTPUT
    if not root.is_dir() or root.is_symlink() or work.is_symlink() or target.exists() or target.is_symlink():
        fail("PRIVATE_OUTPUT_UNSAFE_OR_ALREADY_PRESENT")
    args=private_inputs(root,baseline,review)
    blobs,meta=mock_or_private_native_overlay(*args[:3],occupied=args[3],
                 protected=args[4],baseline_hashes=args[5])
    # Create-only, no overwrite. Never produce the real game/ or J03 stage path.
    target.parent.mkdir(parents=True,exist_ok=True)
    if work.is_symlink():fail("WORKSPACE_SYMLINK")
    stage=Path(tempfile.mkdtemp(prefix=".j11c-atomic-",dir=work))
    try:
        for name,payload in blobs.items():
            dest=stage/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            with dest.open("xb") as handle:handle.write(payload)
        sanitized={k:v for k,v in meta.items() if k not in ("mapids","tileset_ids")}
        sanitized["candidate_mapids_not_published"]=True
        (stage/"readiness.json").write_text(json.dumps(sanitized,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        for name,payload in blobs.items():
            if digest((stage/name).read_bytes())!=digest(payload):fail("STAGE_HASH_CHANGED")
        if target.exists():fail("PRIVATE_TARGET_RACE")
        stage.rename(target)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return {**sanitized,"private_output_created":True}

def audit_only():
    files,raw=source_audit()
    topology=event_contract()
    return {"schema":1,"region":"SINNOH","stage":STAGE,
      "status":"R07_BASELINE_REQUIRED_BEFORE_PRIVATE_RMXP_OVERLAY",
      "original_nine_source_hashes":{s:digest(files[s+".rxdata"]) for s in MAPS},
      "tileset_png_shas":{group:digest(files[name]) for group,(name,_) in GRAPHIC.items()},
      "tile_groups":list(GRAPHIC),"unverified_passability_model":True,
      "source_events":topology["counts"],
      "native_tilesets_created_in_real_game":0,"mapids_reserved":0,
      "native_maps_installed":0,"native_qa_cases_executed":0,
      "r07_approved":False,"r08_approved":False,"r09_approved":False,
      "can_install":False,"can_publish":False,
      "next":"PRIVATE_MAPINFOS_R07_THEN_HUMAN_R08_AND_REAL_NATIVE_QA"}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--baseline",type=Path,
                        help="ONLY .blue-work/sinnoh-j11-baseline/Data (isolated copy)")
    parser.add_argument("--review",type=Path,
                        help="ONLY .blue-work/sinnoh-j11-reviews/r07.json (local, not independent)")
    parser.add_argument("--stage",action="store_true",
                        help="Write new private QA overlay ONLY with complete local R07 inputs")
    args=parser.parse_args(argv)
    try:
        if args.stage:
            if args.baseline is None or args.review is None:fail("STAGE_REQUIRES_BOTH_PRIVATE_INPUTS")
            out=build_private(args.project,args.baseline,args.review)
        else:
            if args.baseline or args.review:fail("PRIVATE_INPUTS_REQUIRE_STAGE_EXPLICIT")
            out=audit_only()
    except (ValueError,TypeError,KeyError,IndexError,OSError,OverflowError,
            struct.error) as error:
        print("J11C_BLOQUEADO:"+str(error),file=sys.stderr)
        return 2
    print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
