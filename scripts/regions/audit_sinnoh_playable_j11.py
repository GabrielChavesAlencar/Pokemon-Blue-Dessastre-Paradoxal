#!/usr/bin/env python3
"""J11: independent read-only audit of five J10-A originals, nine-map intake gates.

No donor maps, user game/Data, saves, Game.exe, or JoiPlay are touched.
The optional *explicit* inputs MUST live in private .blue-work. R07/R08
human self-attestations never become independent rights or native QA approval.
The only write is --write-plan: a new, non-installable JSON readiness receipt.
"""
from __future__ import annotations
import argparse
from collections import Counter, deque
import hashlib
import json
from pathlib import Path
import struct
import sys
import xml.etree.ElementTree as ET
import zlib

ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT,ROOT/"scripts/regions"):
    if str(p) not in sys.path:sys.path.insert(0,str(p))

import generate_sinnoh_original_j10a as j10a
from audit_sinnoh_playable_j09 import (
    R07_KEYS, REGIONS, audit_map, local_r08, read_private_json,
    safe_private, source_catalog, verify_original_zip)
from audit_sinnoh_rxdata import attrs, read_marshal
from audit_sinnoh_twinleaf_events import MAPS, PAIRS, SCHEMA, SPEC, audit as audit_events, read_json
from bind_sinnoh_playable_j02 import game_inventory
from server.ruby_marshal import RubyData

PLAN="sinnoh-j11-readonly-plan.json"
VERSION=1
MAPIDS=None  # No MapID is assigned at J11 without real baseline R07.
COUNTS={"warps":16,"handlers":5,"starter_balls":3}
SHA_LENGTH=64
# Independent *heuristic* classification; RPG::Tileset.@passages still required.
WALK_BLOCKS=frozenset(j10a.BLOCKS)|{j10a.WATER,j10a.SHORE}

def block(msg):
    raise ValueError("SINNOH_J11_BLOCKED:"+msg)

def digest(blob):
    return hashlib.sha256(blob).hexdigest()

def _private(project:Path,source:Path,kind:str)->Path:
    project=Path(project).absolute()
    path=safe_private(project,source,kind=kind)
    if not path.is_file() or path.is_symlink() or not (0<path.stat().st_size<=32_000_000):
        block("PRIVATE_"+kind+"_MISSING_OR_OVERSIZED")
    return path

def verify_png(blob:bytes)->dict:
    """Verify CRC and decompressed 32x32 original tile pixels, not just IHDR."""
    if not blob.startswith(b"\x89PNG\r\n\x1a\n") or len(blob)>4_000_000:
        block("ORIGINAL_TILESET_SIGNATURE")
    off=8;chunks=[];ids=[];pixels=None
    while off+12<=len(blob):
        n=struct.unpack_from(">I",blob,off)[0]
        if n>4_000_000 or off+n+12>len(blob):block("PNG_CHUNK_BOUNDS")
        label=blob[off+4:off+8]
        raw=blob[off+8:off+8+n]
        crc=struct.unpack_from(">I",blob,off+8+n)[0]
        if zlib.crc32(label+raw)&0xffffffff!=crc:block("PNG_CHUNK_CRC")
        chunks.append(label)
        if label==b"IHDR":
            if n!=13 or struct.unpack_from(">IIBBBBB",raw)!=(256,256,8,6,0,0,0):
                block("PNG_IHDR_NOT_ORIGINAL_RMXP")
        elif label==b"IDAT":ids.append(raw)
        elif label==b"IEND":
            if n!=0 or off+12!=len(blob):block("PNG_TRAILING_BYTES")
        else:
            block("PNG_UNEXPECTED_EXTERNAL_OR_UNKNOWN_CHUNK")
        off+=12+n
        if label==b"IEND":break
    if chunks[:1]!=[b"IHDR"] or chunks[-1:]!=[b"IEND"] or not ids or chunks.count(b"IHDR")!=1:
        block("PNG_REQUIRED_CHUNKS")
    packed=b"".join(ids); expected=256*(256*4+1)
    decoder=zlib.decompressobj()
    pixels=decoder.decompress(packed,expected+1)
    if len(pixels)!=expected or decoder.unconsumed_tail or not decoder.eof or decoder.unused_data:
        block("PNG_PIXEL_DATA_INVALID")
    if any(pixels[y*(256*4+1)]!=0 for y in range(256)):
        block("PNG_UNSUPPORTED_SCANLINE_FILTER")
    # Confirm real, distinct 32x32 pixel drawings, not an empty dummy tileset.
    rows=[pixels[y*(256*4+1)+1:(y+1)*(256*4+1)] for y in range(256)]
    hashes=[]
    for i in range(32):
        x,y=i%8*32,i//8*32
        raw=b"".join(row[x*4:(x+32)*4] for row in rows[y:y+32])
        if len(raw)!=4096 or not any(raw):block("BLANK_OR_TRUNCATED_ORIGINAL_TILE")
        hashes.append(digest(raw))
    if len(set(hashes))<24:block("TILESET_NOT_32_DISTINCT_ORIGINAL_TILES")
    return {"sha256":digest(blob),"width":256,"height":256,
            "tile_size_px":32,"authored_tile_count":32,
            "unique_drawn_tile_count":len(set(hashes)),
            "rpg_maker_passages_checked":False,
            "license_independently_verified":False}

def verify_svg(raw:bytes,scene:dict)->dict:
    if len(raw)>1_000_000 or b"<!DOCTYPE" in raw or b"<!ENTITY" in raw:
        block("SVG_UNSAFE_OR_OVERSIZED")
    try:root=ET.fromstring(raw)
    except ET.ParseError:block("SVG_NOT_XML")
    if root.tag!="{http://www.w3.org/2000/svg}svg":block("SVG_ROOT")
    w,h=scene["width"],scene["height"]
    if root.attrib.get("width")!=str(w*14) or root.attrib.get("height")!=str(h*14+32):
        block("SVG_DIMENSIONS")
    elements=list(root.iter())
    names={node.tag.rsplit("}",1)[-1] for node in elements}
    if not names.issubset({"svg","rect","text","g","circle"}):
        block("SVG_ACTIVE_OR_EXTERNAL_ELEMENT")
    if any(any(k.rsplit("}",1)[-1].lower().startswith("on") or
               "href" in k.lower() or "url(" in v.lower() or "javascript:" in v.lower()
               for k,v in node.attrib.items()) for node in elements):
        block("SVG_EXTERNAL_SCRIPT_OR_IMAGE")
    if sum(node.tag.endswith("}rect") for node in elements)!=w*h+1:
        block("SVG_NOT_FULL_GEOMETRY_GRID")
    if not any((node.text or "").strip()==scene["symbol"] for node in elements):
        block("SVG_SYMBOL_MISSING")
    return {"sha256":digest(raw),"cell_count":w*h,"external_content":False}

def verify_rxdata(raw:bytes,scene:dict,original_png_sha:str)->dict:
    result=audit_map(raw)
    w,h=scene["width"],scene["height"]
    if result["width"]!=w or result["height"]!=h or result["tileset_id"]!=1:
        block("RXDATA_DIMENSIONS_OR_PROVISIONAL_TILESET_CHANGED")
    if result["foreign_events_not_imported"]!=0:block("NO_FOREIGN_EVENTS_ALLOWED")
    world=read_marshal(raw,"SINNOH_J11_GENERATED")
    meta=attrs(world);table=meta.get("@data")
    if not isinstance(table,RubyData) or table.name!="Table":
        block("RXDATA_RMXP_TABLE_MISSING")
    dims=struct.unpack_from("<5I",table.data,0)
    if dims!=(3,w,h,3,w*h*3) or len(table.data)!=20+6*w*h:
        block("RXDATA_THREE_LAYER_STRUCTURE")
    decoded=struct.unpack_from("<"+str(w*h*3)+"H",table.data,20)
    for z in range(3):
        if list(decoded[z*w*h:(z+1)*w*h])!=scene["layers"][z]:
            block("RXDATA_PIXELS_DIFFER_FROM_SOURCE_LAYOUT")
    if any(value not in range(384,416) and value!=0 for value in decoded):
        block("RXDATA_TILE_ID_NOT_IN_ORIGINAL_TILESET")
    if meta.get("@events")!={} or meta.get("@autoplay_bgm") or meta.get("@autoplay_bgs"):
        block("RXDATA_FOREIGN_EVENTS_OR_AUDIO")
    if result["nonzero_tiles"]<w*h:block("RXDATA_EMPTY_TERRAIN")
    return {"sha256":digest(raw),"width":w,"height":h,"layers":3,
            "nonzero_cells":result["nonzero_tiles"],
            "provisional_tileset_id":1,"tileset_png_sha256":original_png_sha,
            "has_native_events":False,"native_tileset_registered":False}

def potential_walkability(scene:dict)->dict:
    """Independent BFS / obstacle rejection, NOT actual RMXP directional passages."""
    w,h=scene["width"],scene["height"];layers=scene["layers"]
    def free(x,y):
        if not (0<=x<w and 0<=y<h):return False
        i=y*w+x
        return layers[0][i] not in WALK_BLOCKS and layers[1][i] not in WALK_BLOCKS
    starts=scene["access"]
    if len(starts)!=1 or not all(type(v) is int for v in starts[0]):block("UNREVIEWED_ENTRANCE_SHAPE")
    start=tuple(starts[0])
    if not free(*start):block("ENTRANCE_POTENTIALLY_BLOCKED")
    q=deque([start]);visited={start}
    while q:
        x,y=q.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nxt=(x+dx,y+dy)
            if nxt not in visited and free(*nxt):
                visited.add(nxt);q.append(nxt)
    for marker in scene["landmarks"]:
        if tuple(marker) not in visited:block("LANDMARK_NOT_REACHABLE")
    if len(visited)<w*h//6:block("NAVIGABLE_AREA_TOO_SMALL")
    return {"entrance_candidate":list(start),
            "landmark_candidates":scene["landmarks"],
            "potential_reachable_cells":len(visited),
            "blocked_tile_ids":sorted(WALK_BLOCKS),
            "only_hypothetical_collision_classes":True,
            "directional_passages_checked":False,
            "engine_priority_and_terrain_tags_checked":False}

def verify_contracts(project:Path)->dict:
    spec=read_json(project/"data/regions/sinnoh-twinleaf-events.json")
    schema=read_json(project/"data/regions/sinnoh-twinleaf-events.schema.json")
    audit_events(spec,schema)
    rows=spec["maps"]
    if [m["symbol"] for m in rows]!=list(MAPS):block("NINE_MAP_EVENT_ORDER_CHANGED")
    if (spec.get("approved_for_install") is not False
            or spec.get("gameplay_verified") is not False
            or any(m["map_id"] is not None or m["map_sha256"] is not None for m in rows)):
        block("EVENT_SPEC_PREMATURE_BINDING")
    kinds=Counter()
    links=set()
    for row in rows:
        for event in row["events"]:
            kinds[event["kind"]]+=1
            if event["x"] is not None or event["y"] is not None or event["verified_position"] is not False:
                block("EVENT_POSITION_NOT_NATIVE_REVIEWED")
            if event["kind"]=="warp":
                if (event["arrival_x"] is not None or event["arrival_y"] is not None
                        or event["verified_arrival"] is not False):
                    block("WARP_ARRIVAL_UNREVIEWED")
                links.add((row["symbol"],event["destination"]))
            else:
                if event["sprite"] is not None or event["verified_sprite"] is not False:
                    block("EVENT_SPRITE_PERMISSION_UNREVIEWED")
    if (dict(kinds)!={"warp":16,"handler":5,"starter_ball":3}
            or len(links)!=16 or
            {frozenset((a,b)) for a,b in links}!=set(PAIRS)
            or spec["start"]["x"] is not None
            or spec["start"]["map_id"] is not None):
        block("PORTAL_NPC_STARTER_OR_SPAWN_CONTRACT")
    return {"map_count":9,"warp_pairs":8,"directional_warps":16,
            "npc_handlers":5,"starter_balls":3,"coordinates_approved":False,
            "sprite_rights_approved":False,"actual_collision_tests_passed":0,
            "compilation_j04_allowed":False}

def original_audit(project:Path=ROOT,*,payload:dict|None=None,scenes:list|None=None)->dict:
    project=Path(project).absolute()
    c=source_catalog(project)
    refs={r["symbol"]:r for r in c["maps"]}
    if set(refs)!=set(MAPS) or len(refs)!=9:block("J02_NINE_MAP_CATALOG_CHANGED")
    if ({r["symbol"] for r in c["maps"] if r["source_id"] is None} !=set(j10a.SYMBOLS)
        or len([r for r in c["maps"] if r["source_id"] is not None])!=4):
        block("J02_FIVE_MISSING_FOUR_EXTERIORS_CHANGED")
    if c.get("source_rights_verified") is not False or c.get("destination_game_maps_installed")!=0:
        block("J02_UNSUPPORTED_APPROVAL")
    if payload is None:
        files,manifest=j10a.generate()
    else:
        files,manifest=payload
    originals=j10a.scenes() if scenes is None else scenes
    if len(originals)!=5 or {s["symbol"] for s in originals}!=set(j10a.SYMBOLS):
        block("FIVE_GENERATED_SCENE_SYMBOLS_MISSING")
    if (type(manifest) is not dict or manifest.get("stage")!="J10-A"
            or manifest.get("map_count")!=5 or manifest.get("can_install") is not False
            or manifest.get("r07_approved") is not False
            or manifest.get("r08_approved") is not False
            or manifest.get("r09_native_verified") is not False
            or manifest.get("native_maps_installed")!=0
            or manifest.get("actual_human_authorship_attested") is not False):
        block("J10A_PROVENANCE_OR_NATIVE_STATUS_TAMPERED")
    expected_files={s+".rxdata" for s in j10a.SYMBOLS}|{
        "previews/"+s+".svg" for s in j10a.SYMBOLS}|{"OriginalJ10A.png","manifest.json"}
    if set(files)!=expected_files or not isinstance(files["OriginalJ10A.png"],bytes):
        block("J10A_ALL_FILES_REQUIRED_NO_EXTRA")
    if set(manifest.get("output_checksums",{}))!=expected_files-{"manifest.json"}:
        block("J10A_MANIFEST_FILE_SET_CHANGED")
    for path,sha in manifest["output_checksums"].items():
        if digest(files[path])!=sha:block("J10A_MANIFEST_SHA_MISMATCH")
    png=verify_png(files["OriginalJ10A.png"])
    if manifest.get("tileset_sha256")!=png["sha256"]:
        block("J10A_TILESET_SHA_MISMATCH")
    results={}
    for scene in originals:
        j10a.validate_scene(scene)
        symbol=scene["symbol"]
        binary=verify_rxdata(files[symbol+".rxdata"],scene,png["sha256"])
        svg=verify_svg(files["previews/"+symbol+".svg"],scene)
        if manifest["map_sources"][symbol]["rxdata_sha256"]!=binary["sha256"]:
            block("J10A_ORIGINAL_SOURCE_SHA_MISMATCH")
        # Independent byte-perfect comparison to the procedural SVG at this revision.
        if files["previews/"+symbol+".svg"]!=j10a.svg_preview(scene).encode("utf-8"):
            block("SVG_NOT_AN_EXACT_SCENE_RENDER")
        results[symbol]={"rxdata":binary,"preview_svg":svg,
                         "potential_path":potential_walkability(scene),
                         "human_geometry_reviewed":False}
    return {"images":png,"maps":results,"count":len(results),"all_three_layers":True,
            "verified_only_inert_geometry":True,"native_gameplay_verified":False}

def _baseline(project:Path,folder:Path)->tuple[str,set[int]]:
    path=(project/".blue-work/sinnoh-j11-baseline/Data").absolute()
    if folder.absolute()!=path or folder.is_symlink() or not folder.is_dir():
        block("R07_EXPECTS_EXPLICIT_PRIVATE_BASELINE_DATA")
    for name in ("MapInfos.rxdata","Tilesets.rxdata"):
        _private(project,folder/name,"BASELINE")
    if len((folder/"Tilesets.rxdata").read_bytes())>32_000_000:
        block("R07_TILESETS_TOO_LARGE")
    original=read_marshal((folder/"Tilesets.rxdata").read_bytes(),"J11_TILES")
    if not isinstance(original,list) or len(original)>5000:
        block("R07_TILESETS_RXDATA_INVALID")
    baseline,occupied=game_inventory(folder)
    return baseline,occupied

def check_r07(project:Path,folder:Path,review_path:Path)->dict:
    baseline,occupied=_baseline(project,folder)
    row=read_private_json(project,review_path)
    if (set(row)!=R07_KEYS or
            (row.get("schema"),row.get("region"),row.get("stage"),row.get("mode")) !=
            (1,"SINNOH","J09","LOCAL_R07_RESERVATIONS_NOT_NATIVE_APPROVAL")
            or row.get("baseline_mapinfos_sha256")!=baseline
            or row.get("occupied_ids")!=sorted(occupied)
            or row.get("locally_reviewed") is not True
            or type(row.get("review_reference")) is not str
            or not 8<=len(row["review_reference"])<=240):
        block("R07_BASELINE_OR_SELF_ATTESTATION_MISSING")
    reserve=row.get("reserved_by_region")
    if type(reserve) is not dict or set(reserve)!=set(REGIONS):
        block("R07_REGIONAL_RESERVATIONS_NOT_COMPLETE")
    future=set()
    for region in REGIONS:
        values=reserve[region]
        if (type(values) is not list or len(values)!=len(set(values))
                or any(type(v) is not int or not 1<=v<=999 for v in values)
                or set(values)&future):
            block("R07_DUPLICATE_OR_UNSAFE_REGIONAL_RESERVATION")
        future.update(values)
    ids=row.get("candidate_sinnoh_ids")
    if (type(ids) is not list or len(ids)!=9 or len(set(ids))!=9
            or any(type(v) is not int or not 442<=v<=517 for v in ids)
            or set(ids)&(occupied|future)):
        block("R07_NINE_MAPIDS_COLLIDE_OR_INVALID")
    return {"local_baseline_sha256":baseline,
            "local_candidates_checked_no_collision":len(ids),
            "region_sets_checked":len(REGIONS),
            "local_attestation_only":True,"r07_independent_approval":False}

def check_r08(project:Path,review_dir:Path,source:dict,originals:dict)->dict:
    combined={symbol:info["sha256"] for symbol,info in source["original_four"].items()}
    combined.update({symbol:entry["rxdata"]["sha256"] for symbol,entry in originals["maps"].items()})
    if len(combined)!=9:block("R08_REQUIRES_ALL_NINE_MAP_HASHES")
    review=local_r08(project,review_dir/"r08.json",combined)
    art=read_private_json(project,review_dir/"j10a-art-rights.json")
    keys={"schema","region","stage","kind","tileset_sha256",
          "license_reference","review_reference","locally_reviewed",
          "private_qa_permission","independent_approval"}
    if (set(art)!=keys or
            (art.get("schema"),art.get("region"),art.get("stage"),art.get("kind")) !=
            (1,"SINNOH","J11","J10A_PROCEDURAL_ORIGINAL_ART_RIGHTS")
            or art.get("tileset_sha256")!=originals["images"]["sha256"]
            or art.get("locally_reviewed") is not True
            or art.get("private_qa_permission") is not True
            or art.get("independent_approval") is not False
            or any(type(art.get(k)) is not str or not 12<=len(art[k])<=240
                   for k in ("license_reference","review_reference"))):
        block("R08_TILESET_ART_LICENSE_REVIEW_MISSING")
    return {"nine_map_hashes_locally_attested":True,
            "j10a_art_sha_reviewed_locally":True,
            "r08_independently_approved":False,
            "full_nine_map_graphics_rights_approved":False,
            **review}

def audit(project:Path=ROOT,*,donor_zip:Path|None=None,
          baseline_dir:Path|None=None,review_dir:Path|None=None,
          payload:dict|None=None,scenes:list|None=None)->dict:
    project=Path(project).absolute()
    original=original_audit(project,payload=payload,scenes=scenes)
    events=verify_contracts(project)
    catalog=source_catalog(project)
    four=None;check07=None;check08=None
    if donor_zip is not None:
        path=_private(project,donor_zip,"DONOR_ZIP")
        four=verify_original_zip(path,catalog)
    if (baseline_dir is None)!=(review_dir is None):
        block("R07_NEEDS_BOTH_ISOLATED_BASELINE_AND_REVIEW")
    if review_dir is not None:
        review_dir=Path(review_dir).absolute()
        target=project/".blue-work/sinnoh-j11-reviews"
        if review_dir!=target or review_dir.is_symlink() or not review_dir.is_dir():
            block("REVIEWS_MUST_BE_PRIVATE_J11_PATH")
        check07=check_r07(project,baseline_dir,review_dir/"r07.json")
        if four is None:block("R08_REQUIRES_VERIFIED_FOUR_HISTORICAL_SOURCES")
        check08=check_r08(project,review_dir,four,original)
    source={symbol:{"origin":"J10A_PROCEDURAL_ORIGINAL","rxdata_sha256":entry["rxdata"]["sha256"],
                     "destination_map_id":None,"installed":False}
            for symbol,entry in original["maps"].items()}
    for row in catalog["maps"]:
        if row["source_id"] is not None:
            symbol=row["symbol"]
            source[symbol]={"origin":"B00_HISTORICAL_PRIVATE_DONOR",
                            "rxdata_sha256":row["source_sha256"],
                            "verified_donor_this_run":bool(four),
                            "rights_verified":False,
                            "destination_map_id":None,"installed":False}
    blockers=["R07_NATIVE_MAPINFOS_AND_REGIONAL_RESERVATIONS_NOT_INDEPENDENTLY_APPROVED",
              "R08_NINE_MAPS_AND_TILESET_PERMISSIONS_NOT_INDEPENDENTLY_APPROVED",
              "R09_GAME_EXE_AND_JOIPLAY_NOT_EXECUTED",
              "TILESET_RMXP_PASSAGES_AND_PRIORITIES_NOT_PROVEN",
              "J04_16_WARPS_5_NPCS_3_BALLS_COORDINATES_NOT_REVIEWED",
              "J06_PRIVATE_QA_OVERLAY_NOT_BUILT",
              "FOUR_HISTORICAL_SOURCES_NOT_CLEARED_FOR_USE"]
    return {"schema":VERSION,"region":"SINNOH","stage":"J11",
        "status":"FIVE_ORIGINALS_AUDITED_NINE_MAP_ISOLATED_STAGING_BLOCKED",
        "j10a_originals":original,"j04_events":events,
        "nine_map_source_plan":{s:source[s] for s in MAPS},
        "nine_map_symbolic_slots":9,"historical_donor_verified":bool(four),
        "r07":check07 or {"local_attestation":False,"r07_independent_approval":False},
        "r08":check08 or {"local_attestation":False,"r08_independently_approved":False},
        "r09": {"windows_executed":0,"android_joiplay_executed":0,"native_approved":False},
        "blockers":blockers,"next":"J11_MANUAL_RIGHTS_AND_MAPINFOS_THEN_J12_NATIVE_QA",
        "can_promote_to_j09":False,"can_stage_j03_j04_j06":False,
        "can_install":False,"can_publish_game":False,
        "native_maps_installed":0,"native_qa_cases_executed":0,
        "native_game_or_personal_saves_accessed":False,
        "other_regions_modified":False}

def private_plan(project:Path=ROOT,**kwargs)->dict:
    project=Path(project).absolute()
    if not project.is_dir() or project.is_symlink():block("ROOT_INVALID")
    target=project/".blue-work"/PLAN
    if target.exists() or target.is_symlink() or target.parent.is_symlink():
        block("PRIVATE_PLAN_ALREADY_EXISTS_OR_UNSAFE")
    report=audit(project,**kwargs)
    target.parent.mkdir(parents=True,exist_ok=True)
    if target.parent.is_symlink():block("WORKSPACE_LINK")
    with target.open("xb") as stream:
        stream.write((json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode("utf-8"))
    return {**report,"local_readonly_plan":str(target)}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--donor-zip",type=Path,
                        help="Optional authorized source ZIP in .blue-work, READ ONLY")
    parser.add_argument("--baseline-dir",type=Path,
                        help="Optional QA-only .blue-work/sinnoh-j11-baseline/Data")
    parser.add_argument("--review-dir",type=Path,
                        help="Optional .blue-work/sinnoh-j11-reviews; not independent approval")
    parser.add_argument("--write-plan",action="store_true",
                        help="Write inert JSON readiness plan only, never map assets")
    args=parser.parse_args(argv)
    try:
        options=dict(donor_zip=args.donor_zip,baseline_dir=args.baseline_dir,
                     review_dir=args.review_dir)
        report=private_plan(args.project,**options) if args.write_plan else audit(args.project,**options)
    except (ValueError,OSError,TypeError,KeyError,struct.error,OverflowError,zlib.error) as err:
        print("J11_BLOQUEADO:"+str(err),file=sys.stderr)
        return 2
    print(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True))
    return 0

if __name__=="__main__":raise SystemExit(main())
