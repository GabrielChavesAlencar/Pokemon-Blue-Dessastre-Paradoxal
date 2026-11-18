#!/usr/bin/env python3
"""Sinnoh J03: private, geometry-only four-map stage with two-step SHA receipt.

Uses only the four B00-audited terrain sources: Twinleaf, Route 201,
Sandgem, Route 202. Never creates the five missing interiors/Verity maps.
No source events, scripts, trainers, audio, saves or ROMs can enter the stage.
This is local private QA staging, NOT an install, a licence, or native proof.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
for folder in (ROOT, ROOT / "scripts/regions"):
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))

from audit_sinnoh_rxdata import Source, attrs, read_marshal
from bind_sinnoh_playable_j02 import (source_catalog, game_inventory,
                                      local_input, SHA)
from convert_sinnoh_geometry import (TILE_ATTRS, PNG, graphic_name,
                                      silent_audio, table_valid)
from server.ruby_marshal import RubyObject, text
from sinnoh_staging_transaction import (ALLOWED, LABEL, digest, preview, stage,
                                        rollback, stage_root)
from stage import serialize

DESTINATION_MIN, DESTINATION_MAX = 442, 495
SOURCE_IDS = (209, 227, 210, 228)
PILOT_SYMBOLS = ("SINNOH_TWINLEAF_TOWN", "SINNOH_ROUTE_201",
                 "SINNOH_SANDGEM_TOWN", "SINNOH_ROUTE_202")
RIGHTS_MODE = "LOCAL_PRIVATE_QA_ONLY_NO_REDISTRIBUTION"
INPUT_KEYS = {"schema", "region", "mode", "baseline_mapinfos_sha256",
              "source_mapinfos_sha256", "source_archive_sha256", "bindings"}
RIGHTS_KEYS = {"schema", "region", "mode", "allowed_use",
               "source_mapinfos_sha256", "source_archive_sha256",
               "reviewed_locally", "asset_sha256"}
RESERVATION_KEYS = {"schema", "region", "mode", "baseline_mapinfos_sha256",
                    "protected_ids"}

def fail(code):
    raise ValueError("SINNOH_J03_BLOCKED:" + code)

def sha256(raw):
    return hashlib.sha256(raw).hexdigest()

def _safe_game_data(root, game_data):
    root = root.absolute()
    game_data = game_data.absolute()
    if (root.is_symlink() or not root.is_dir()
            or game_data.is_symlink() or not game_data.is_dir()
            or not (game_data / "MapInfos.rxdata").is_file()
            or (game_data / "MapInfos.rxdata").is_symlink()
            or not (game_data / "Tilesets.rxdata").is_file()
            or (game_data / "Tilesets.rxdata").is_symlink()):
        fail("GAME_DATA_NOT_SAFE")
    return game_data

def _safe_source(root, source, game_data):
    source = source.absolute()
    game = game_data.absolute()
    if (source.is_symlink() or not source.exists()
            or source == root or source == game or source == game.parent
            or source.is_relative_to(game.parent)
            or game.is_relative_to(source)):
        fail("UNSAFE_OR_NESTED_SOURCE")
    return source

def _native(game_data):
    info_hash, occupied = game_inventory(game_data)
    tiles = game_data / "Tilesets.rxdata"
    tiles_raw = tiles.read_bytes()
    if len(tiles_raw) > 32_000_000:
        fail("NATIVE_TILESETS_OVERSIZED")
    native_infos = read_marshal((game_data / "MapInfos.rxdata").read_bytes(), "NATIVE_INFOS")
    native_tiles = read_marshal(tiles_raw, "NATIVE_TILESETS")
    if (not isinstance(native_infos, dict)
            or any(type(k) is not int or k < 1
                   or not isinstance(v, RubyObject) or v.name != "RPG::MapInfo"
                   for k,v in native_infos.items())
            or not isinstance(native_tiles, list) or len(native_tiles) > 5000):
        fail("NATIVE_DATA_INVALID")
    return info_hash, sha256(tiles_raw), occupied, native_infos, native_tiles

def _validate_plan(catalog, plan, baseline, source_infos_sha, archive_sha,
                   occupied, protected):
    if (type(plan) is not dict or set(plan) != INPUT_KEYS
            or (plan.get("schema"), plan.get("region"), plan.get("mode")) !=
            (1, "SINNOH", "J03_FOUR_TERRAIN_DRY_RUN")
            or plan.get("baseline_mapinfos_sha256") != baseline
            or plan.get("source_mapinfos_sha256") != source_infos_sha
            or plan.get("source_archive_sha256") != archive_sha):
        fail("PLAN_INVALID_OR_STALE")
    rows = plan.get("bindings")
    if not isinstance(rows, list) or len(rows) != 4:
        fail("FOUR_ONLY_EXPLICIT_BINDINGS_REQUIRED")
    refs = {row["symbol"]:row for row in catalog["maps"] if row["source_id"] is not None}
    if (set(refs) != set(PILOT_SYMBOLS)
            or [r.get("symbol") for r in rows if isinstance(r,dict)] != list(PILOT_SYMBOLS)):
        fail("FOUR_SOURCE_SYMBOLS_MISMATCH")
    seen = set()
    for row in rows:
        if (type(row) is not dict
                or set(row) != {"symbol","source_id","destination_id",
                                "source_sha256","width","height"}):
            fail("BINDING_ROW_INVALID")
        ref = refs[row["symbol"]]
        sid, dst = row["source_id"], row["destination_id"]
        if (type(sid) is not int or sid != ref["source_id"]
                or type(dst) is not int
                or dst < DESTINATION_MIN or dst > DESTINATION_MAX
                or dst in seen or dst in occupied or dst in protected
                or row["source_sha256"] != ref["source_sha256"]
                or [row["width"],row["height"]] != ref["source_dimensions"]
                or type(row["width"]) is not int or type(row["height"]) is not int):
            fail("SOURCE_DESTINATION_HASH_OR_COLLISION")
        seen.add(dst)
    return rows

def _validate_reservations(r, baseline):
    if (type(r) is not dict or set(r) != RESERVATION_KEYS
            or (r.get("schema"),r.get("region"),r.get("mode")) !=
                (1,"SINNOH","LOCAL_RESERVATIONS_CANDIDATE")
            or r.get("baseline_mapinfos_sha256") != baseline):
        fail("RESERVATIONS_INVALID_OR_STALE")
    ids = r["protected_ids"]
    if (type(ids) is not list or len(ids) > 5000
            or any(type(i) is not int or i < 1 or i > 999 for i in ids)
            or len(set(ids)) != len(ids)):
        fail("RESERVATIONS_INVALID_IDS")
    return set(ids)

def _validate_rights(a, source_sha, archive_sha):
    if (type(a) is not dict or set(a) != RIGHTS_KEYS
            or (a.get("schema"),a.get("region"),a.get("mode"),a.get("allowed_use")) !=
              (1,"SINNOH","J03_LOCAL_ASSET_REVIEW",RIGHTS_MODE)
            or a.get("source_mapinfos_sha256") != source_sha
            or a.get("source_archive_sha256") != archive_sha
            or a.get("reviewed_locally") is not True
            or type(a.get("asset_sha256")) is not dict
            or not a["asset_sha256"] or len(a["asset_sha256"]) > 200):
        fail("LOCAL_PRIVATE_RIGHTS_REVIEW_MISSING")
    for rel,h in a["asset_sha256"].items():
        if (type(rel) is not str or
                not re.fullmatch(r"Graphics/(Tilesets|Autotiles)/[A-Za-z0-9_ .()-]{1,100}\.png",rel)
                or ".." in rel or type(h) is not str or not SHA.fullmatch(h)):
            fail("ASSET_ATTESTATION_INVALID")
    return a["asset_sha256"]

def _png_name(original, raw, folder):
    name = graphic_name(original)
    if not name:
        return None
    if not raw.startswith(PNG) or len(raw) < len(PNG)+4:
        fail("ASSET_NOT_PNG")
    new_name = "SN_J03_" + sha256(raw)[:16] + "_" + name[:60]
    target = f"Graphics/{folder}/{new_name}.png"
    if not ALLOWED.fullmatch(target):
        fail("UNSAFE_STAGED_GRAPHIC_NAME")
    return target, new_name.encode("utf-8")

def build_overlay(root: Path, source: Path, game_data: Path, plan: dict,
                  reservations: dict, rights: dict) -> tuple[dict[str, bytes], dict]:
    """Pure in-memory transformation. Stage is a separate explicit action."""
    root = root.absolute()
    game_data = _safe_game_data(root, game_data)
    source = _safe_source(root, source, game_data)
    catalog = source_catalog(root)
    game_sha, game_tiles_sha, occupied, native_infos, native_tiles = _native(game_data)
    protected = _validate_reservations(reservations, game_sha)

    with Source(source) as donor:
        source_infos_raw = donor.read("Data/MapInfos.rxdata")
        source_tiles_raw = donor.read("Data/Tilesets.rxdata")
        source_sha = sha256(source_infos_raw)
        archive_sha = donor.metadata.get("sha256_zip")
        if source_sha != catalog["source_mapinfos_sha256"]:
            fail("SOURCE_ORIGINAL_MAPINFOS_HASH_CHANGED")
        if archive_sha is not None and archive_sha != catalog["source_archive_sha256"]:
            fail("SOURCE_ARCHIVE_HASH_CHANGED")
        rows = _validate_plan(catalog, plan, game_sha, source_sha, archive_sha,
                              occupied, protected)
        image_hashes = _validate_rights(rights, source_sha, archive_sha)
        source_tiles = read_marshal(source_tiles_raw, "SOURCE_TILESETS")
        if not isinstance(source_tiles, list) or len(source_tiles) > 5000:
            fail("SOURCE_TILESETS_UNSUPPORTED")

        result_infos = copy.deepcopy(native_infos)
        result_tiles = copy.deepcopy(native_tiles)
        original_tileset_ids = {}
        staging_files = {}
        consumed_images = set()
        new_graphics = {}
        maps = donor.map_paths()

        def copy_graphic(folder, original):
            name = graphic_name(original)
            if not name:
                return b""
            relative = f"Graphics/{folder}/{name}.png"
            raw = donor.read(relative)
            if not raw.startswith(PNG):
                fail("GRAPHIC_NOT_PNG")
            observed = sha256(raw)
            if image_hashes.get(relative) != observed:
                fail("IMAGE_SHA_OR_RIGHTS_MISMATCH")
            consumed_images.add(relative)
            if relative in new_graphics:
                return new_graphics[relative]
            output = _png_name(original, raw, folder)
            if output is None:
                fail("EMPTY_GRAPHIC")
            target, filename = output
            if target in staging_files and staging_files[target] != raw:
                fail("GRAPHIC_NAME_COLLISION")
            staging_files[target] = raw
            new_graphics[relative] = filename
            return filename

        for row in rows:
            sid, dest = row["source_id"], row["destination_id"]
            if sid not in maps:
                fail("SOURCE_MAP_MISSING")
            raw = donor.read(maps[sid])
            if sha256(raw) != row["source_sha256"]:
                fail("SOURCE_MAP_SHA_CHANGED")
            map_obj = read_marshal(raw, "SOURCE_RMXP_MAP")
            if not isinstance(map_obj,RubyObject) or map_obj.name != "RPG::Map":
                fail("SOURCE_NOT_RMXP_MAP")
            data = attrs(map_obj)
            w,h,old_tile = data.get("@width"),data.get("@height"),data.get("@tileset_id")
            if (type(w) is not int or type(h) is not int or type(old_tile) is not int
                    or w != row["width"] or h != row["height"]
                    or old_tile < 1 or not table_valid(data.get("@data"),w,h)
                    or not any(data["@data"].data[20:])):
                fail("EMPTY_OR_UNVERIFIED_GEOMETRY")
            if old_tile not in original_tileset_ids:
                if old_tile >= len(source_tiles):
                    fail("SOURCE_TILESET_ID_MISSING")
                tile = source_tiles[old_tile]
                if not isinstance(tile,RubyObject) or tile.name != "RPG::Tileset":
                    fail("SOURCE_TILESET_INVALID")
                ta = attrs(tile)
                if not isinstance(ta.get("@autotile_names"),list):
                    fail("SOURCE_AUTOTILES_INVALID")
                tileid = len(result_tiles)
                if tileid > 9999:
                    fail("NATIVE_TILESET_CAPACITY_EXCEEDED")
                new_attrs = {key:copy.deepcopy(value) for key,value in ta.items()
                             if key in TILE_ATTRS}
                new_attrs["@id"] = tileid
                new_attrs["@name"] = b"Sinnoh J03 private geometry"
                new_attrs["@tileset_name"] = copy_graphic("Tilesets",ta.get("@tileset_name"))
                new_attrs["@autotile_names"] = [
                    copy_graphic("Autotiles",n) for n in ta["@autotile_names"]
                ]
                for key in ("@panorama_name","@fog_name","@battleback_name"):
                    new_attrs[key] = b""
                result_tiles.append(RubyObject("RPG::Tileset",new_attrs))
                original_tileset_ids[old_tile] = tileid
            output_map = RubyObject("RPG::Map",{
                "@tileset_id": original_tileset_ids[old_tile],
                "@width": w, "@height": h,
                "@autoplay_bgm":False,"@bgm":silent_audio(),
                "@autoplay_bgs":False,"@bgs":silent_audio(),
                "@encounter_list":[],"@encounter_step":30,
                "@data":copy.deepcopy(data["@data"]),
                "@events":{},
            })
            key = f"Data/Map{dest:03d}.rxdata"
            staging_files[key] = serialize(output_map)
            confirmed = read_marshal(staging_files[key], "STAGED_MAP_CHECK")
            if attrs(confirmed).get("@events") != {}:
                fail("DONOR_EVENTS_NOT_STRIPPED")
            result_infos[dest] = RubyObject("RPG::MapInfo",{
                "@name":("[Sinnoh QA] "+row["symbol"]).encode("ascii"),
                "@parent_id":0,"@order":100000+dest,
                "@expanded":False,"@scroll_x":0,"@scroll_y":0,
            })
        if consumed_images != set(image_hashes):
            fail("EXTRA_OR_UNUSED_RIGHTS_DECLARATIONS")
        staging_files["Data/MapInfos.rxdata"] = serialize(result_infos)
        staging_files["Data/Tilesets.rxdata"] = serialize(result_tiles)
        if sha256((game_data/"MapInfos.rxdata").read_bytes()) != game_sha:
            fail("NATIVE_MAPINFOS_CHANGED_DURING_CONVERSION")
        if sha256((game_data/"Tilesets.rxdata").read_bytes()) != game_tiles_sha:
            fail("NATIVE_TILESETS_CHANGED_DURING_CONVERSION")

    report = {
        "schema":1,"region":"SINNOH","stage":"J03",
        "mode":"FOUR_TERRAIN_GEOMETRY_ONLY_LOCAL_QA",
        "status":"FOUR_MAPS_PRIVATE_PREVIEW_NOT_INSTALLABLE",
        "terrain_maps_in_memory":4,"missing_real_pilot_maps":5,
        "destination_ids":[r["destination_id"] for r in rows],
        "mapinfos_before_sha256":game_sha,
        "tilesets_before_sha256":game_tiles_sha,
        "source_mapinfos_sha256":source_sha,
        "source_tilesets_sha256":sha256(source_tiles_raw),
        "staged_tilesets":len(original_tileset_ids),
        "staged_graphics":len(consumed_images),
        "donor_events_copied":0,"donor_scripts_copied":0,
        "donor_music_copied":0,"donor_trainers_copied":0,
        "local_private_asset_attestation_present":True,
        "asset_rights_independently_verified":False,
        "future_reservations_globally_verified":False,
        "r07_complete":False,"r08_complete":False,"r09_complete":False,
        "game_modified":False,"saves_read_or_modified":False,
        "can_install":False,"native_playable":False,
        "next_stage":"J04",
    }
    return staging_files,report

def stage_verify(root:Path,label:str,plan_sha:str) -> dict:
    """Read-only verifier of the exact immutable stage receipt; never removes."""
    if (not LABEL.fullmatch(label) or not label.startswith(("j03-", "j04-"))
            or not SHA.fullmatch(plan_sha)):
        fail("STAGE_ID_INVALID")
    folder=stage_root(root) / f"{label}-{plan_sha[:16]}"
    receipt=folder/"stage-manifest.json"
    if folder.is_symlink() or receipt.is_symlink() or not receipt.is_file():
        fail("STAGE_NOT_PRESENT")
    m=json.loads(receipt.read_text("utf-8"))
    keys={"schema","region","mode","label","plan_sha256","files",
          "total_bytes","stage_relative_path","writes_to_main_game",
          "may_install_into_game","source_rights_verified","mapping_verified"}
    if (type(m) is not dict or set(m)!=keys or m["mode"]!="LOCAL_STAGE_ONLY"
            or m["schema"]!=1 or m["region"]!="SINNOH"
            or m["label"]!=label or m["plan_sha256"]!=plan_sha
            or m["writes_to_main_game"] is not False
            or m["may_install_into_game"] is not False
            or m["source_rights_verified"] is not False
            or m["mapping_verified"] is not False):
        fail("STAGE_RECEIPT_INVALID")
    rows=m["files"]
    if not isinstance(rows,list) or not rows or len(rows)>5000:
        fail("STAGE_FILE_ROWS_INVALID")
    paths=[]
    total=0
    dirs=set()
    for r in rows:
        if (type(r) is not dict or set(r)!={"path","bytes","sha256"}
                or type(r["path"]) is not str or not ALLOWED.fullmatch(r["path"])
                or type(r["bytes"]) is not int or r["bytes"]<1
                or not SHA.fullmatch(str(r["sha256"]))):
            fail("STAGE_PATH_OR_HASH_INVALID")
        paths.append(r["path"])
        total+=r["bytes"]
        p=Path(r["path"])
        dirs.update(str(x.as_posix()) for x in p.parents if str(x)!=".")
    canonical={"label":label,"files":rows}
    signed=digest(json.dumps(canonical,ensure_ascii=True,sort_keys=True,
                              separators=(",",":")).encode("ascii"))
    if (signed!=plan_sha or len(set(p.casefold() for p in paths))!=len(paths)
            or paths!=sorted(paths) or total!=m["total_bytes"]
            or m["stage_relative_path"] !=
               f".blue-work/sinnoh-stage/{label}-{plan_sha[:16]}"):
        fail("STAGE_RECEIPT_CHANGED")
    actual_files=set()
    for path in folder.rglob("*"):
        if path.is_symlink():
            fail("STAGE_SYMLINK")
        rel=path.relative_to(folder).as_posix()
        if path.is_dir() and rel not in dirs:
            fail("STAGE_EXTRA_DIRECTORY")
        if path.is_file():
            actual_files.add(rel)
    if actual_files!=set(paths)|{"stage-manifest.json"}:
        fail("STAGE_EXTRA_OR_MISSING_FILES")
    for row in rows:
        p=folder/row["path"]
        if not p.is_file() or p.stat().st_size!=row["bytes"] or sha256(p.read_bytes())!=row["sha256"]:
            fail("STAGE_BYTES_CHANGED")
    return {"schema":1,"region":"SINNOH","stage":"J03",
            "status":"LOCAL_PRIVATE_STAGE_HASHES_OK_NOT_NATIVE_APPROVAL",
            "files_verified":len(rows),"plan_sha256":plan_sha,
            "can_install":False,"native_playable":False,
            "rights_verified":False}

def preview_only(root=ROOT):
    c=source_catalog(root)
    return {
        "schema":1,"region":"SINNOH","stage":"J03",
        "status":"BLOCKED_REAL_SOURCE_AND_LOCAL_RIGHTS_NOT_PROVIDED",
        "source_terrain_references":c["source_terrain_candidates"],
        "missing_real_maps":c["source_maps_missing"],
        "local_stage_created":False,"map_ids_approved":0,
        "native_maps_installed":0,"r07_complete":False,
        "r08_complete":False,"r09_complete":False,
        "game_modified":False,"saves_read_or_modified":False,
        "can_install":False,"native_playable":False,"next_stage":"J04",
    }

def main(argv=None):
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--project",type=Path,default=ROOT)
    cli.add_argument("--source",type=Path)
    cli.add_argument("--game-data",type=Path)
    cli.add_argument("--bindings",type=Path)
    cli.add_argument("--reservations",type=Path)
    cli.add_argument("--asset-review",type=Path)
    cli.add_argument("--label",default="j03-twinleaf")
    cli.add_argument("--expected-dry-run")
    cli.add_argument("--stage",action="store_true")
    cli.add_argument("--verify-stage",action="store_true")
    cli.add_argument("--rollback",action="store_true")
    args=cli.parse_args(argv)
    try:
        root=args.project.absolute()
        if root.is_symlink() or not root.is_dir() or not args.label.startswith("j03-"):
            fail("PROJECT_OR_LABEL_INVALID")
        actions=sum([args.stage,args.verify_stage,args.rollback])
        if actions>1:
            fail("ONLY_ONE_ACTION")
        if args.verify_stage or args.rollback:
            if not args.expected_dry_run or any(p is not None for p in
                 (args.source,args.game_data,args.bindings,args.reservations,args.asset_review)):
                fail("STAGE_REFERENCE_ARGS_REQUIRED")
            if args.rollback:
                result=rollback(root,args.label,args.expected_dry_run)
            else:
                result=stage_verify(root,args.label,args.expected_dry_run)
        elif not any((args.source,args.game_data,args.bindings,args.reservations,args.asset_review)):
            if args.stage or args.expected_dry_run:
                fail("CANNOT_STAGE_WITHOUT_REAL_INPUTS")
            result=preview_only(root)
        else:
            if not all((args.source,args.game_data,args.bindings,args.reservations,args.asset_review)):
                fail("ALL_LOCAL_INPUTS_REQUIRED")
            plan=local_input(root,args.bindings)
            reservations=local_input(root,args.reservations)
            rights=local_input(root,args.asset_review)
            files,report=build_overlay(root,args.source,args.game_data,plan,reservations,rights)
            dry=preview(root,args.label,files)
            if args.stage:
                if not args.expected_dry_run:
                    fail("REQUIRE_PRIOR_DRY_RUN_HASH")
                result={**report,"transaction":stage(root,args.label,files,args.expected_dry_run)}
            else:
                if args.expected_dry_run:
                    fail("UNUSED_DRY_RUN_HASH")
                result={**report,"transaction":dry}
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,
            ImportError,IndexError,OverflowError):
        # A user's local path, private title or raw file content never appears.
        print("SINNOH_J03_BLOCKED:INVALID_OR_UNVERIFIED_LOCAL_INPUT",file=sys.stderr)
        return 2
    print(json.dumps(result,ensure_ascii=False,indent=2))
    allowed = (result.get("status") in (
        "FOUR_MAPS_PRIVATE_PREVIEW_NOT_INSTALLABLE",
        "LOCAL_PRIVATE_STAGE_HASHES_OK_NOT_NATIVE_APPROVAL")
        or result.get("mode") == "LOCAL_ROLLBACK")
    return 0 if allowed else 2

if __name__=="__main__":
    raise SystemExit(main())
