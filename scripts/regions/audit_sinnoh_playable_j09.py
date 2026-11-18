#!/usr/bin/env python3
"""Sinnoh J09 physical source intake: read-only donor ZIP and private original maps.

Historical four outdoors must exactly match B00/J02. Five missing maps must
come from explicit private ORIGINAL source files, never empty templates.
Optional R07 occupancy and R08 per-map review are local human ATTESTATIONS,
not approvals of rights, MapIDs, licensing, Game.exe/JoiPlay or native play.
No game writes, saves, extraction, third-party Ruby evaluation or redistribution.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT, ROOT/"scripts/regions"):
    if str(p) not in sys.path:sys.path.insert(0,str(p))

from bind_sinnoh_playable_j02 import source_catalog,read_real_source,game_inventory
from audit_sinnoh_rxdata import read_marshal, attrs
from server.ruby_marshal import RubyObject,RubyData

SHA=re.compile(r"[a-f0-9]{64}\Z")
SYMBOL=re.compile(r"SINNOH_[A-Z0-9_]{2,90}\Z")
STAGE_DIR="sinnoh-j09-authored"
MISSING_STATUS="MISSING_REAL_NONEMPTY_TERRAIN"
CATALOG="data/regions/sinnoh-j02-map-source-catalog.json"
R07_KEYS={"schema","region","stage","mode","baseline_mapinfos_sha256",
          "occupied_ids","candidate_sinnoh_ids","reserved_by_region",
          "locally_reviewed","review_reference"}
REGIONS=("DECADES","KANTO","JOHTO","HOENN","UNOVA")
R08_KEYS={"schema","region","stage","mode","locally_reviewed","redistribution_authorized",
          "review_reference","maps"}
RIGHTS_BASIS={"ORIGINAL_USER_AUTHORED","EXPLICIT_PRIVATE_USE_PERMISSION",
              "LICENSED_FOR_PRIVATE_QA"}
R08_ROW={"sha256","basis","permission_evidence","private_qa_permitted"}

def block(code:str):
    raise ValueError("SINNOH_J09_BLOCKED:"+code)

def checksum(raw:bytes)->str:
    return hashlib.sha256(raw).hexdigest()

def safe_private(project:Path,path:Path,*,kind:str)->Path:
    project=project.absolute()
    work=project/".blue-work"
    path=Path(path).absolute()
    if (project.is_symlink() or not project.is_dir() or work.is_symlink()
            or not path.is_relative_to(work) or not path.resolve().is_relative_to(work.resolve())
            or any(p.is_symlink() for p in (path,*path.parents))):
        block("PRIVATE_"+kind+"_PATH_REQUIRED")
    return path

def read_private_json(project:Path,path:Path,max_bytes:int=2_000_000)->dict:
    path=safe_private(project,path,kind="REVIEW")
    if (not path.is_file() or path.stat().st_size>max_bytes
            or path.stat().st_size<2):
        block("PRIVATE_REVIEW_MISSING_OR_OVERSIZED")
    try: value=json.loads(path.read_text("utf-8"))
    except (ValueError,UnicodeError):block("PRIVATE_REVIEW_JSON_INVALID")
    if type(value) is not dict:block("PRIVATE_REVIEW_OBJECT_REQUIRED")
    return value

def audit_map(raw:bytes,*,empty_allowed:bool=False)->dict:
    if type(raw) is not bytes or not 10<len(raw)<=16_000_000:
        block("MAP_FILE_MISSING_OR_OVERSIZED")
    try: obj=read_marshal(raw,"SINNOH_J09_RMXP")
    except (ValueError,IndexError,TypeError,KeyError,OverflowError):
        block("INVALID_RMXP_MAP")
    if not isinstance(obj,RubyObject) or obj.name!="RPG::Map":
        block("NOT_RPG_MAP")
    data=attrs(obj)
    width,height,tile=data.get("@width"),data.get("@height"),data.get("@tileset_id")
    if (any(type(v) is not int for v in (width,height,tile))
            or width<8 or height<8 or width>500 or height>500 or tile<1):
        block("UNREASONABLE_MAP_DIMENSIONS_OR_TILESET")
    raw_table=data.get("@data")
    if not isinstance(raw_table,RubyData) or raw_table.name!="Table" or len(raw_table.data)<20:
        block("INVALID_RMXP_TABLE")
    dims,tw,th,layers,count=struct.unpack_from("<5I",raw_table.data)
    if ((dims,tw,th,layers,count)!=(3,width,height,3,width*height*3)
            or len(raw_table.data)!=20+2*count):
        block("MAP_TABLE_DIMENSIONS_INVALID")
    values=struct.unpack_from("<"+str(count)+"H",raw_table.data,20)
    nonzero=sum(v!=0 for v in values)
    # Empty 20x15 placeholders are NOT real terrain; one-tile gimmicks do not
    # constitute a house, lake, building or navigable original scene.
    if not empty_allowed and nonzero<max(12,(width*height)//20):
        block("TERRAIN_EMPTY_OR_PLACEHOLDER")
    events=data.get("@events",{})
    if type(events) is not dict:block("MAP_EVENTS_INVALID")
    # Never import unknown scripted events or donor NPCs. The original Blue
    # J04/J05 compilers own event creation after QA terrain import.
    return {"sha256":checksum(raw),"width":width,"height":height,
            "tileset_id":tile,"nonzero_tiles":nonzero,
            "foreign_events_not_imported":len(events),
            "nonempty_terrain":True}

def verify_original_zip(source:Path,catalog:dict)->dict:
    source=Path(source).absolute()
    if source.is_symlink() or source.suffix.lower()!=".zip" or not source.is_file():
        block("ORIGINAL_B00_ZIP_REQUIRED")
    refs=[r for r in catalog["maps"] if r["source_id"] is not None]
    if len(refs)!=4: block("EXPECTED_FOUR_B00_TERRAIN_REFERENCES")
    source_meta,found=read_real_source(source,{r["source_id"] for r in refs})
    if (source_meta["source_archive_sha256"]!=catalog["source_archive_sha256"]
            or source_meta["source_mapinfos_sha256"]!=catalog["source_mapinfos_sha256"]):
        block("DONOR_ZIP_OR_MAPINFOS_SHA_NOT_B00")
    seen=set()
    for row in refs:
        sid=row["source_id"]
        item=found[sid]
        if (sid in seen or item["sha256"]!=row["source_sha256"]
                or [item["width"],item["height"]]!=row["source_dimensions"]
                or item.get("nonempty_terrain") is not True):
            block("DONOR_MAP_SHA_DIMENSIONS_OR_GEOMETRY_CHANGED")
        seen.add(sid)
    return {"archive_sha256":source_meta["source_archive_sha256"],
            "mapinfos_sha256":source_meta["source_mapinfos_sha256"],
            "source_tilesets_sha256":source_meta["source_tilesets_sha256"],
            "original_four":{r["symbol"]:{"source_id":r["source_id"],
                           "sha256":found[r["source_id"]]["sha256"],
                           "width":found[r["source_id"]]["width"],
                           "height":found[r["source_id"]]["height"]}
                             for r in refs}}

def authored_five(project:Path,folder:Path,catalog:dict)->dict:
    folder=safe_private(project,folder,kind="AUTHORED_MAPS")
    if folder.name!=STAGE_DIR or folder.is_symlink() or not folder.is_dir():
        block("PRIVATE_AUTHORED_FOLDER_REQUIRED")
    required=[r["symbol"] for r in catalog["maps"] if r["source_id"] is None]
    if len(required)!=5 or len(set(required))!=5 or any(not SYMBOL.fullmatch(x) for x in required):
        block("EXPECTED_FIVE_MISSING_MAP_SYMBOLS")
    files=list(folder.iterdir())
    if any(x.is_symlink() or not x.is_file() for x in files):
        block("AUTHORED_FOLDER_CONTAINS_SYMLINK_OR_DIRECTORY")
    if len(files)!=5 or {p.name for p in files}!={s+".rxdata" for s in required}:
        block("ALL_FIVE_EXACT_AUTHORED_MAPS_REQUIRED")
    maps={}
    seen=set()
    for symbol in required:
        path=folder/(symbol+".rxdata")
        if path.stat().st_size>16_000_000:block("AUTHORED_MAP_TOO_LARGE")
        info=audit_map(path.read_bytes())
        if info["sha256"] in seen:block("DUPLICATED_MAP_BYTES_NOT_DISTINCT_SCENE")
        seen.add(info["sha256"])
        # The Blue project owns the events; do not import donor events.
        if info["foreign_events_not_imported"]!=0:
            block("AUTHORED_SCENE_HAS_FOREIGN_EVENTS")
        maps[symbol]=info
    return maps

def local_r07(project:Path,game_data:Path,review_path:Path)->dict:
    game_data=Path(game_data).absolute()
    project=project.absolute()
    if (game_data != project/"game"/"Data" or
            any(p.is_symlink() for p in (game_data,*game_data.parents))):
        block("NATIVE_MAPID_BASELINE_PATH_REQUIRED")
    baseline,occupied=game_inventory(game_data)
    review=read_private_json(project,review_path)
    if (set(review)!=R07_KEYS
            or (review["schema"],review["region"],review["stage"],review["mode"])!=
               (1,"SINNOH","J09","LOCAL_R07_RESERVATIONS_NOT_NATIVE_APPROVAL")
            or review["baseline_mapinfos_sha256"]!=baseline
            or review["occupied_ids"]!=sorted(occupied)
            or review["locally_reviewed"] is not True
            or type(review["review_reference"]) is not str
            or not 8<=len(review["review_reference"])<=240):
        block("R07_BASELINE_OR_HUMAN_REVIEW_MISSING")
    by_region=review.get("reserved_by_region")
    if type(by_region) is not dict or set(by_region)!=set(REGIONS):
        block("R07_REGION_COVERAGE_INCOMPLETE")
    reserved=set()
    for region in REGIONS:
        seq=by_region[region]
        if (type(seq) is not list or len(seq)!=len(set(seq))
                or any(type(i) is not int or not 1<=i<=999 for i in seq)):
            block("R07_DUPLICATE_OR_INVALID_FUTURE_IDS")
        if reserved & set(seq):
            block("R07_OVERLAPPING_REGIONAL_RESERVATIONS")
        reserved.update(seq)
    candidates=review.get("candidate_sinnoh_ids")
    if (type(candidates) is not list or len(candidates)!=9
            or len(set(candidates))!=9
            or any(type(i) is not int or not 442<=i<=517 for i in candidates)
            or set(candidates)&(occupied|reserved)):
        block("R07_SINNOH_MAPID_COLLISION_OR_FABRICATION")
    return {"r07_snapshot_occupied_count":len(occupied),
            "r07_candidate_ids":sorted(candidates),
            "r07_baseline_mapinfos_sha256":baseline,
            "r07_locally_attested":True,"r07_independently_approved":False}

def local_r08(project:Path,review_path:Path,map_hashes:dict)->dict:
    review=read_private_json(project,review_path)
    if (set(review)!=R08_KEYS or
            (review["schema"],review["region"],review["stage"],review["mode"])!=
               (1,"SINNOH","J09","LOCAL_R08_MAP_RIGHTS_NOT_REDISTRIBUTABLE")
            or review["locally_reviewed"] is not True
            or review["redistribution_authorized"] is not False
            or type(review["review_reference"]) is not str
            or not 8<=len(review["review_reference"])<=240):
        block("R08_LOCAL_REVIEW_REQUIRED")
    rows=review.get("maps")
    if type(rows) is not dict or set(rows)!=set(map_hashes):
        block("R08_NINE_MAPS_PER_ASSET_REQUIRED")
    for symbol,row in rows.items():
        if (type(row) is not dict or set(row)!=R08_ROW
                or row["sha256"]!=map_hashes[symbol]
                or row["basis"] not in RIGHTS_BASIS
                or row["private_qa_permitted"] is not True
                or type(row["permission_evidence"]) is not str
                or not 8<=len(row["permission_evidence"])<=240):
            block("R08_RIGHTS_MISSING_OR_MAP_SHA_CHANGED")
    return {"r08_nine_maps_locally_attested":True,
            "r08_full_graphics_audio_rights_checked":False,
            "r08_independently_approved":False}

def make_report(catalog:dict,source:dict|None,authored:dict|None,
                r07:dict|None,r08:dict|None)->dict:
    known={r["symbol"] for r in catalog["maps"] if r["source_id"] is not None}
    missing=[r["symbol"] for r in catalog["maps"] if r["source_id"] is None]
    original=source["original_four"] if source else {}
    authored=authored or {}
    candidates={s:row["sha256"] for s,row in {**original,**authored}.items()}
    ready=len(original)==4 and len(authored)==5
    return {
        "schema":1,"region":"SINNOH","stage":"J09",
        "status":("NINE_SOURCE_MAPS_VERIFIED_PRIVATELY_R07_R08_R09_PENDING"
                  if ready else "BLOCKED_MISSING_REAL_SOURCE_MAPS"),
        "source_archive_sha256":source["archive_sha256"] if source else None,
        "source_mapinfos_sha256":source["mapinfos_sha256"] if source else None,
        "historical_exteriors_verified_this_run":len(original),
        "authored_missing_maps_verified_this_run":len(authored),
        "total_original_source_candidates_verified":len(candidates),
        "missing_source_symbols":[s for s in missing if s not in authored],
        "historical_source_symbols":sorted(known),
        "verified_source_metadata":{s:{"sha256":d["sha256"],"width":d["width"],
                                   "height":d["height"]}
                                    for s,d in sorted({**original,**authored}.items())},
        "r07":r07 or {"r07_locally_attested":False,"r07_independently_approved":False},
        "r08":r08 or {"r08_nine_maps_locally_attested":False,
                     "r08_independently_approved":False},
        "r09_windows_native_cases_verified":0,
        "r09_android_joiplay_cases_verified":0,
        "native_maps_installed":0,"native_playable":False,
        "can_install":False,"can_publish":False,
        "source_assets_exported":False,
        "main_game_or_saves_modified":False,
        "next_gate":"J06/J07 isolated QA after independent R07/R08 and real source permission",
    }

def audit(project:Path=ROOT,*,source:Path|None=None,
          authored:Path|None=None,game_data:Path|None=None,
          r07_review:Path|None=None,r08_review:Path|None=None)->dict:
    project=Path(project).absolute()
    catalog=source_catalog(project)
    if any((authored,game_data,r07_review,r08_review)) and source is None:
        block("ORIGINAL_B00_SOURCE_REQUIRED_FOR_LOCAL_APPROVAL")
    donor=verify_original_zip(source,catalog) if source is not None else None
    extra=authored_five(project,authored,catalog) if authored is not None else None
    if (game_data is None)!=(r07_review is None):
        block("R07_REQUIRES_BOTH_GAME_DATA_AND_PRIVATE_REVIEW")
    checked_r07=local_r07(project,game_data,r07_review) if game_data is not None else None
    if r08_review is not None and extra is None:
        block("R08_REQUIRES_ALL_FIVE_REAL_ORIGINAL_MAP_FILES")
    combined={s:v["sha256"] for s,v in
              {**(donor["original_four"] if donor else {}),**(extra or {})}.items()}
    checked_r08=local_r08(project,r08_review,combined) if r08_review is not None else None
    return make_report(catalog,donor,extra,checked_r07,checked_r08)

def save_private_receipt(project:Path,output:Path,report:dict)->None:
    output=safe_private(project,output,kind="REPORT")
    if output.name!="sinnoh-j09-source-intake.json" or output.parent!=project.absolute()/".blue-work":
        block("REPORT_MUST_STAY_UNDER_BLUE_WORK")
    if output.exists() or output.is_symlink():block("NO_REPORT_OVERWRITE")
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open("x",encoding="utf-8") as stream:
        json.dump(report,stream,ensure_ascii=False,indent=2,sort_keys=True)
        stream.write("\n")

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--source-zip",type=Path)
    parser.add_argument("--authored-dir",type=Path)
    parser.add_argument("--game-data",type=Path)
    parser.add_argument("--r07-review",type=Path)
    parser.add_argument("--r08-review",type=Path)
    parser.add_argument("--require-complete",action="store_true")
    parser.add_argument("--report",type=Path)
    args=parser.parse_args(argv)
    try:
        report=audit(args.project,source=args.source_zip,authored=args.authored_dir,
                     game_data=args.game_data,r07_review=args.r07_review,
                     r08_review=args.r08_review)
        if args.require_complete and not (
                report["total_original_source_candidates_verified"]==9
                and report["r07"].get("r07_locally_attested") is True
                and report["r08"].get("r08_nine_maps_locally_attested") is True):
            block("NINE_MAPS_R07_R08_REQUIRED_STILL_NOT_NATIVE_APPROVAL")
        if args.report is not None:save_private_receipt(args.project,args.report,report)
    except (OSError,ValueError,KeyError,TypeError,UnicodeError,
            json.JSONDecodeError) as e:
        print("SINNOH_J09_BLOQUEADO:"+str(e),file=sys.stderr)
        return 2
    print(json.dumps(report,ensure_ascii=False,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
