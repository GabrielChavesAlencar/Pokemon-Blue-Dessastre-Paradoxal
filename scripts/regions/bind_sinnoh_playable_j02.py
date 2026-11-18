#!/usr/bin/env python3
"""J02: bind nine REAL Sinnoh pilot maps to collision-checked candidate MapIDs.

Never installs anything. Reads actual RMXP source map bytes and Decades
MapInfos/Map files without executing donor events or scripts. All output is
sanitized metadata only. Rights, future reservations, native Game.exe and
save isolation remain independent, unapproved gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts/regions") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts/regions"))

import preflight_sinnoh_playable_j01 as j01
from audit_sinnoh_rxdata import Source, read_marshal, attrs
from audit_sinnoh_source import inspect_native
from server.ruby_marshal import RubyData, RubyObject

CATALOG = ROOT / "data/regions/sinnoh-j02-map-source-catalog.json"
LOCAL_FILENAME = "j02-map-bindings.json"
SHA = re.compile(r"[a-f0-9]{64}\Z")
SOURCE_MISSING = "MISSING_REAL_NONEMPTY_TERRAIN"
SOURCE_HISTORICAL = "AUDITED_HISTORICAL_TERRAIN_REFERENCE_ONLY"

def blocked(code: str):
    raise ValueError("SINNOH_J02_BLOCKED:" + code)

def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def object_json(path: Path, limit=200_000) -> dict:
    if path.is_symlink() or not path.is_file() or path.stat().st_size > limit:
        blocked("INPUT_MISSING_UNSAFE_OR_OVERSIZED")
    result = json.loads(path.read_text(encoding="utf-8-sig"))
    if type(result) is not dict:
        blocked("INVALID_JSON_ROOT")
    return result

def source_catalog(root: Path = ROOT) -> dict:
    c = object_json(root / "data/regions/sinnoh-j02-map-source-catalog.json")
    prior = object_json(root / "data/regions/sinnoh-b00-actual-source.json")
    topology = j01.contracts(root)
    if (c.get("schema"), c.get("region"), c.get("stage"), c.get("mode")) != (
            1, "SINNOH", "J02", "HISTORICAL_SOURCE_REFERENCE_ONLY"):
        blocked("CATALOG_HEADER_CHANGED")
    if c.get("source_archive_sha256") != prior.get("source_zip_sha256"):
        blocked("CATALOG_ARCHIVE_PROVENANCE_CHANGED")
    if c.get("source_mapinfos_sha256") != prior.get("mapinfos_sha256"):
        blocked("CATALOG_MAPINFOS_PROVENANCE_CHANGED")
    if (c.get("source_rights_verified") is not False
            or c.get("destination_game_maps_installed") != 0
            or c.get("destination_mapids_assigned") != 0
            or c.get("native_playable") is not False):
        blocked("CATALOG_FALSE_NATIVE_APPROVAL")
    rows = c.get("maps")
    if not isinstance(rows, list) or len(rows) != 9:
        blocked("CATALOG_NOT_NINE_MAPS")
    if [r.get("symbol") for r in rows] != topology["symbols"]:
        blocked("CATALOG_TOPOLOGY_MISMATCH")
    present = 0
    for row in rows:
        if row.get("destination_map_id") is not None or row.get("installed") is not False:
            blocked("CATALOG_FALSE_INSTALLED_MAP")
        source_id = row.get("source_id")
        if source_id is None:
            if any(row.get(k) is not None for k in ("source_sha256", "source_dimensions", "source_name")):
                blocked("CATALOG_FABRICATED_MISSING_SOURCE")
            if row.get("source_status") != SOURCE_MISSING:
                blocked("CATALOG_MISSING_STATUS_FORGED")
        else:
            present += 1
            if (type(source_id) is not int or source_id not in prior["terrain_filled_ids"]
                    or row.get("source_status") != SOURCE_HISTORICAL
                    or not isinstance(row.get("source_sha256"), str)
                    or not SHA.fullmatch(row["source_sha256"])
                    or not isinstance(row.get("source_name"), str)
                    or row["source_name"] not in ("Twinleaf Town", "Sandgem Town", "Route 201", "Route 202")
                    or not isinstance(row.get("source_dimensions"), list)
                    or len(row["source_dimensions"]) != 2
                    or any(type(x) is not int or x < 1 or x > 500 for x in row["source_dimensions"])):
                blocked("CATALOG_SOURCE_METADATA_INVALID")
        if row.get("source_asset_rights_verified") is not False:
            blocked("CATALOG_RIGHTS_CLAIM_FORGED")
    if present != 4 or c.get("source_terrain_candidates") != 4 or c.get("source_maps_missing") != 5:
        blocked("CATALOG_COUNTS_CHANGED")
    return c

def local_input(root: Path, path: Path) -> dict:
    """Local plans must stay inside the ignored workspace, never a GitHub file."""
    project = root.absolute()
    work = project / ".blue-work"
    path = path.absolute()
    if (work.is_symlink() or path.is_symlink() or not path.is_relative_to(work)
            or not path.resolve().is_relative_to(work.resolve())):
        blocked("LOCAL_INPUT_MUST_BE_IN_BLUE_WORK")
    return object_json(path)

def original_metadata_view(root: Path = ROOT) -> dict:
    c = source_catalog(root)
    missing = [r["symbol"] for r in c["maps"] if r["source_id"] is None]
    return {
        "schema": 1, "region": "SINNOH", "stage": "J02",
        "mode": "READ_ONLY_NO_NATIVE_INSTALLATION",
        "status": "SOURCE_REFS_4_OF_9_MISSING_LOCAL_INPUTS",
        "terrain_references": 4, "source_maps_missing": 5,
        "source_real_map_bindings_confirmed": 0,
        "candidate_destination_ids_verified": 0,
        "native_maps_installed": 0, "native_warps_compiled": 0,
        "missing_symbols": missing,
        "available_source_symbols": [r["symbol"] for r in c["maps"] if r["source_id"] is not None],
        "r07_complete": False, "r08_complete": False, "r09_complete": False,
        "can_install": False, "native_playable": False,
        "game_modified": False, "saves_read_or_modified": False,
        "next_stage": "J03",
    }

def game_inventory(data_path: Path) -> tuple[str, set[int]]:
    if data_path.is_symlink() or not data_path.is_dir():
        blocked("NATIVE_DATA_UNAVAILABLE_OR_SYMLINK")
    info = data_path / "MapInfos.rxdata"
    if info.is_symlink() or not info.is_file() or info.stat().st_size > 32_000_000:
        blocked("NATIVE_MAPINFOS_UNAVAILABLE")
    if not (data_path / "Tilesets.rxdata").is_file():
        blocked("NATIVE_TILESETS_UNAVAILABLE")
    inv = inspect_native(data_path)
    if inv.get("status") != "LOCAL_READ_ONLY":
        blocked("NATIVE_MAPIDS_UNREADABLE")
    return sha256(info.read_bytes()), set(inv["occupied_ids"])

def read_real_source(source: Path, source_ids: set[int]) -> tuple[dict, dict[int, dict]]:
    """Verify raw RPG::Map bytes and non-empty terrain, no scripts executed."""
    if source.is_symlink() or not source.exists():
        blocked("SOURCE_MISSING_OR_SYMLINK")
    with Source(source) as donor:
        archive_sha = donor.metadata.get("sha256_zip")
        mapinfos_sha = sha256(donor.read("Data/MapInfos.rxdata"))
        tilesets_sha = sha256(donor.read("Data/Tilesets.rxdata"))
        files = donor.map_paths()
        found = {}
        for source_id in sorted(source_ids):
            rel = files.get(source_id)
            if rel is None:
                blocked("SOURCE_MAP_MISSING")
            payload = donor.read(rel)
            obj = read_marshal(payload, "RPG_MAP")
            if not isinstance(obj, RubyObject) or obj.name != "RPG::Map":
                blocked("SOURCE_NOT_RMXP_MAP")
            a = attrs(obj)
            width, height, tileset = a.get("@width"), a.get("@height"), a.get("@tileset_id")
            if any(type(v) is not int for v in (width, height, tileset)):
                blocked("SOURCE_DIMENSIONS_INVALID")
            if not (1 <= width <= 500 and 1 <= height <= 500 and tileset > 0):
                blocked("SOURCE_DIMENSIONS_OUT_OF_RANGE")
            table = a.get("@data")
            if not isinstance(table, RubyData) or table.name != "Table" or len(table.data) < 20:
                blocked("SOURCE_TERRAIN_TABLE_INVALID")
            d, w, h, z, count = struct.unpack_from("<5I", table.data)
            if (d != 3 or (w, h, z) != (width, height, 3)
                    or count != width * height * 3 or len(table.data) != 20 + 2 * count):
                blocked("SOURCE_TERRAIN_DIMENSIONS_MISMATCH")
            if not any(table.data[20:]):
                blocked("SOURCE_TERRAIN_EMPTY_PLACEHOLDER")
            found[source_id] = {"sha256": sha256(payload), "width": width,
                                "height": height, "tileset_id": tileset,
                                "nonempty_terrain": True}
        return {"source_mapinfos_sha256": mapinfos_sha,
                "source_tilesets_sha256": tilesets_sha,
                "source_archive_sha256": archive_sha}, found

def _ids(raw, *, allow_empty=True):
    if (type(raw) is not list or len(raw) > 5000
            or any(type(v) is not int or v < 1 or v > 999 for v in raw)
            or len(raw) != len(set(raw))
            or (not allow_empty and not raw)):
        blocked("PROTECTED_IDS_INVALID")
    return set(raw)

def validate_candidate(plan: dict, catalog: dict, game_sha: str, occupied: set[int],
                       source_meta: dict, source_maps: dict[int, dict],
                       reservations: dict | None) -> dict:
    if (type(plan) is not dict
            or set(plan) != {"schema", "region", "mode", "baseline_mapinfos_sha256",
                             "source_mapinfos_sha256", "source_archive_sha256", "bindings"}
            or (plan["schema"], plan["region"], plan["mode"]) !=
                (1, "SINNOH", "J02_LOCAL_BINDING_CANDIDATE")):
        blocked("CANDIDATE_SCHEMA_INVALID")
    if not isinstance(game_sha, str) or not SHA.fullmatch(game_sha):
        blocked("NATIVE_BASELINE_INVALID")
    if plan["baseline_mapinfos_sha256"] != game_sha:
        blocked("NATIVE_BASELINE_SHA_MISMATCH")
    if plan["source_mapinfos_sha256"] != source_meta["source_mapinfos_sha256"]:
        blocked("SOURCE_MAPINFOS_SHA_MISMATCH")
    if plan["source_archive_sha256"] != source_meta["source_archive_sha256"]:
        blocked("SOURCE_ARCHIVE_SHA_MISMATCH")
    if reservations is not None:
        if (type(reservations) is not dict
                or set(reservations) != {"schema", "region", "mode", "baseline_mapinfos_sha256", "protected_ids"}
                or (reservations["schema"], reservations["region"], reservations["mode"]) !=
                    (1, "SINNOH", "LOCAL_RESERVATIONS_CANDIDATE")
                or reservations["baseline_mapinfos_sha256"] != game_sha):
            blocked("RESERVATIONS_INVALID_OR_STALE")
        protected = _ids(reservations["protected_ids"])
    else:
        protected = set()
    if type(occupied) is not set or any(type(i) is not int or i < 1 for i in occupied):
        blocked("GAME_MAPIDS_INVALID")
    rows = plan["bindings"]
    if not isinstance(rows, list) or len(rows) != 9:
        blocked("NINE_BINDINGS_REQUIRED")
    expected_symbols = [r["symbol"] for r in catalog["maps"]]
    if [r.get("symbol") for r in rows if isinstance(r, dict)] != expected_symbols:
        blocked("BINDING_ORDER_OR_SYMBOLS_INVALID")
    used_sources, used_destinations = set(), set()
    projection = []
    for r, ref in zip(rows, catalog["maps"]):
        if type(r) is not dict or set(r) != {"symbol", "source_id", "destination_id",
                                             "source_sha256", "width", "height"}:
            blocked("BINDING_ROW_INVALID")
        sid, dst = r["source_id"], r["destination_id"]
        if (type(sid) is not int or sid < 1 or sid > 9999
                or type(dst) is not int or not 442 <= dst <= 517):
            blocked("SOURCE_OR_DESTINATION_ID_OUT_OF_RANGE")
        if sid in used_sources or dst in used_destinations:
            blocked("SOURCE_OR_DESTINATION_DUPLICATE")
        used_sources.add(sid)
        used_destinations.add(dst)
        if dst in occupied or dst in protected:
            blocked("DESTINATION_COLLIDES_WITH_NATIVE_OR_FUTURE_REGION")
        info = source_maps.get(sid)
        if (type(info) is not dict or info.get("nonempty_terrain") is not True
                or not SHA.fullmatch(str(info.get("sha256", "")))
                or info.get("sha256") != r["source_sha256"]
                or r["width"] != info.get("width")
                or r["height"] != info.get("height")):
            blocked("SOURCE_MAP_MISSING_CHANGED_OR_EMPTY")
        if ref["source_id"] is not None:
            if (sid != ref["source_id"]
                    or info["sha256"] != ref["source_sha256"]
                    or [info["width"], info["height"]] != ref["source_dimensions"]):
                blocked("HISTORICAL_SOURCE_REFERENCE_TAMPERED")
        projection.append({"symbol": r["symbol"], "source_id": sid,
                           "destination_id": dst, "map_sha256": info["sha256"],
                           "width": info["width"], "height": info["height"],
                           "source_terrain_verified_in_local_data": True})
    return {
        "schema": 1, "region": "SINNOH", "stage": "J02",
        "status": "NINE_LOCAL_CANDIDATES_VERIFIED_NOT_INSTALLABLE",
        "mode": "NONINSTALLABLE_LOCAL_MAP_BINDINGS",
        "original_source_terrain_references": 4,
        "new_source_maps_required_and_checked": 5,
        "candidate_map_count": len(projection),
        "destination_ids_checked_against_observed_game": True,
        "future_reservations_supplied_as_local_claim": reservations is not None,
        "future_reservations_complete_verified": False,
        "r07_complete": False, "r08_complete": False, "r09_complete": False,
        "rights_verified": False, "native_compilation_verified": False,
        "can_install": False, "native_playable": False,
        "game_modified": False, "saves_read_or_modified": False,
        "baseline_mapinfos_sha256": game_sha,
        "source_mapinfos_sha256": source_meta["source_mapinfos_sha256"],
        "source_archive_sha256": source_meta["source_archive_sha256"],
        "candidate_bindings": projection, "next_stage": "J03",
    }

def local_report(root: Path, data: dict):
    work = root / ".blue-work"
    folder = work / "sinnoh-jogavel"
    output = folder / LOCAL_FILENAME
    if root.is_symlink() or work.is_symlink() or folder.is_symlink() or output.is_symlink():
        blocked("OUTPUT_LINK_DENIED")
    folder.mkdir(parents=True, exist_ok=True)
    # x mode prevents overwriting an earlier immutable local diagnosis.
    with output.open("x", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--game-data", type=Path)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--bindings", type=Path,
                        help="Local .blue-work JSON with all 9 explicit source/destination IDs")
    parser.add_argument("--reservations", type=Path,
                        help="Optional local protected IDs; never certifies R07")
    parser.add_argument("--write-local-report", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = args.project.absolute()
        if root.is_symlink() or not root.is_dir():
            blocked("PROJECT_UNAVAILABLE")
        catalog = source_catalog(root)
        report = original_metadata_view(root)
        provided = (args.game_data, args.source, args.bindings)
        if any(p is not None for p in provided) and not all(p is not None for p in provided):
            blocked("GAME_SOURCE_AND_BINDINGS_REQUIRED_TOGETHER")
        if all(p is not None for p in provided):
            plan = local_input(root, args.bindings)
            local_reserved = local_input(root, args.reservations) if args.reservations else None
            if args.source.absolute().is_relative_to((root / "game").absolute()):
                blocked("SOURCE_IS_MAIN_GAME")
            game_sha, occupied = game_inventory(args.game_data)
            raw_bindings = plan.get("bindings", [])
            if type(raw_bindings) is not list or len(raw_bindings) != 9:
                blocked("NINE_BINDINGS_REQUIRED")
            source_ids = set()
            for row in raw_bindings:
                if type(row) is not dict or type(row.get("source_id")) is not int:
                    blocked("SOURCE_ID_INVALID")
                source_ids.add(row["source_id"])
            source_meta, source_maps = read_real_source(args.source, source_ids)
            report = validate_candidate(plan, catalog, game_sha, occupied,
                                        source_meta, source_maps, local_reserved)
        elif args.reservations:
            blocked("RESERVATIONS_WITHOUT_BINDINGS")
        if args.write_local_report:
            local_report(root, report)
    except (OSError, ValueError, TypeError, KeyError, UnicodeError,
            ImportError, struct.error, json.JSONDecodeError):
        # Never disclose user-local paths or map contents through stderr.
        print("SINNOH_J02_BLOCKED:INVALID_OR_UNVERIFIED_INPUT", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["status"] == "NINE_LOCAL_CANDIDATES_VERIFIED_NOT_INSTALLABLE" else 2

if __name__ == "__main__":
    raise SystemExit(main())
