"""Audit the pinned Hoenn source and the shared Windows/Android H00 baseline."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
import zipfile
from collections import Counter
from pathlib import Path

from hoenn_qa_phase1 import (
    PINNED_MAPINFOS_SHA256, PINNED_TILESETS_SHA256, ROOT, UPSTREAM,
    check_tree, load_tree, require_private_path,
)
from ensure_hoenn_source import sha_git
from hoenn_catalog import CATALOG_REVISION, MAP_RANGE, approved_source_ids, validate_manifest, verify_markers
from hoenn_qa_phase2 import audit_map, inspect_connections
from hoenn_qa_phase3 import parse_compiled_encounters, parse_reference_encounters
from install_hoenn import MANIFEST, verify_installed
from scripts.android.build_manifest import verify_manifest
from scripts.android.package import verify_archive
from server.ruby_marshal import RubyData, RubyObject, loads, text


ARCHIVE_ROOT = "Pokemon-Blue-Android/"
MAP_FILE = re.compile(r"Data/Map([0-9]{3,})\.rxdata")
ROUTE = re.compile(r"Route (10[1-9]|1[12][0-9]|13[0-4])", re.IGNORECASE)
MANIFESTS = (
    ("KANTO", "Data/blue-kanto-install.json", "maps"),
    ("JOHTO", "Data/blue-johto-main-preview.json", "map_ids"),
    ("JOHTO", "Data/blue-johto-install.json", "file_hashes"),
    ("SINNOH", "Data/blue-sinnoh-shared.json", "map_ids"),
    ("HOENN", MANIFEST.as_posix(), "maps"),
)
FRONTIER_AREAS = {
    "Altering Cave", "Battle Frontier", "Desert Underpass", "Marine Cave",
    "S.S. Tidal", "Terra Cave", "Marine Cave_U", "Battle Frontier First Visit",
}
EXTERNAL_AREAS = {"Birth Island", "Southern Island", "The... Moon?"}

STORY_DUNGEONS = {
    "Petalburg Woods", "Rusturf Tunnel", "Granite Cave", "Fiery Path",
    "Mt. Chimney", "Jagged Pass", "Magma Hideout", "Meteor Falls",
    "Mt. Pyre", "Aqua Hideout", "Seafloor Cavern", "Cave of Origin",
    "Sky Pillar", "Victory Road",
}
OPTIONAL_AREAS = {
    "Abandoned Ship", "New Mauville", "Mirage Tower", "Scorched Slab",
    "Safari Zone", "Shoal Cave High", "Shoal Cave Low", "Sealed Chamber",
    "Island Cave", "Desert Ruins", "Ancient Tomb", "Trainer Hill",
}
STORY_LOCATIONS = {
    "Littleroot Town", "Oldale Town", "Petalburg City", "Rustboro City",
    "Dewford Town", "Slateport City", "Mauville City", "Verdanturf Town",
    "Fallarbor Town", "Lavaridge Town", "Fortree City", "Lilycove City",
    "Mossdeep City", "Sootopolis City", "Pacifidlog Town",
    "Ever Grande City South", "Ever Grande City North", "Birch's Lab",
    "Devon Corporation", "Slateport City Harbor", "Oceanic Museum",
    "Mossdeep Space Center", "Weather Institute", "Mr. Briney's House",
    "Intro Truck", "Hall of Fame", "League Champion", "E4 Hallways",
    "Pokémon League", "Pokemon League",
}


def digest(blob: bytes) -> str:
    return hashlib.sha256(blob).hexdigest()


def materialized_ids(paths) -> set[int]:
    return {int(match[1]) for path in paths if (match := MAP_FILE.fullmatch(path))}


def tiles_present(world: RubyObject) -> bool:
    table = world.attrs["@data"]
    if not isinstance(table, RubyData) or table.name != "Table" or len(table.data) < 20:
        raise ValueError("Tabela de terreno RPG Maker inválida")
    dimension, width, height, depth, cells = struct.unpack_from("<5I", table.data)
    if (dimension != 3 or (width, height) != (world.attrs["@width"], world.attrs["@height"])
            or depth != 3 or cells != width * height * depth or len(table.data) != 20 + 2 * cells):
        raise ValueError("Terreno e dimensões do mapa divergem")
    return any(table.data[20:])


def scope_for(name: str, ancestors: list[str], has_tiles: bool, event_count: int) -> str:
    if not has_tiles and not event_count:
        return "hierarchy_or_empty"
    names = {name, *ancestors}
    if names & EXTERNAL_AREAS:
        return "external_event"
    if "Delta Episode" in name or "(STORMING)" in name or "Filler Maps" in names:
        return "donor_variant_or_filler"
    if names & FRONTIER_AREAS:
        return "postgame_candidate"
    if ROUTE.fullmatch(name):
        return "emerald_main_route"
    if names & STORY_DUNGEONS:
        return "emerald_story_dungeon_reference"
    if names & OPTIONAL_AREAS:
        return "emerald_optional_reference"
    if "Underwater Maps" in names:
        return "emerald_underwater_reference"
    if "Cutscene Maps" in names or name in {"Intro", "Region Transfer Map", "Routes"}:
        return "donor_scene_or_integration_reference"
    if name in STORY_LOCATIONS or name.endswith(" Gym") or name.startswith("Elite Four "):
        return "emerald_story_location_reference"
    if "Cities" in ancestors or "Routes" in ancestors:
        return "city_or_route_interior_reference"
    return "scope_review_required"


def ancestry(infos: dict, map_id: int) -> list[str]:
    parents = []
    seen = {map_id}
    while parent := infos[map_id].attrs["@parent_id"]:
        if parent in seen or parent not in infos:
            raise ValueError(f"Hierarquia inválida da fonte de Hoenn no MapID {map_id}")
        seen.add(parent)
        parents.append(text(infos[parent].attrs["@name"]))
        map_id = parent
    return parents


def routes_by_number(rows: list[dict]) -> dict[int, int]:
    routes = {}
    for row in rows:
        if not (match := ROUTE.fullmatch(row["name"])):
            continue
        route = int(match[1])
        if route in routes or not row["has_terrain"]:
            raise ValueError(f"Rota {route} sem identidade física única na fonte")
        routes[route] = row["source_id"]
    if set(routes) != set(range(101, 135)):
        raise ValueError("Inventário fonte não identifica as 34 rotas principais de Hoenn")
    return routes


def source_inventory(tree_path: Path, source: Path) -> dict:
    tree = load_tree(tree_path, offline=True)
    check_tree(tree)
    blobs = {row["path"]: row["sha"] for row in tree["tree"] if row.get("type") == "blob"}

    def checked(path: str) -> bytes:
        raw = (source / path).read_bytes()
        if sha_git(raw) != blobs[path]:
            raise ValueError(f"Arquivo fora da origem fixada: {path}")
        return raw

    index = checked("Data/MapInfos.rxdata")
    tiles_raw = checked("Data/Tilesets.rxdata")
    if digest(index) != PINNED_MAPINFOS_SHA256 or digest(tiles_raw) != PINNED_TILESETS_SHA256:
        raise ValueError("A identidade de MapInfos/Tilesets da fonte diverge da versão aprovada para auditoria")
    infos, tiles = loads(index), loads(tiles_raw)
    map_ids = materialized_ids(blobs)
    if len(map_ids) != 373 or map_ids != set(infos):
        raise ValueError("Inventário de 373 mapas e MapInfos da fonte divergem")
    encounters, encounter_audit = parse_reference_encounters(
        checked("PBS/encounters.txt").decode("utf-8-sig"), map_ids)
    checked("PBS/map_connections.txt")
    catalogued = approved_source_ids(CATALOG_REVISION)
    rows = []
    for map_id in sorted(map_ids):
        raw = checked(f"Data/Map{map_id:03}.rxdata")
        world = loads(raw)
        if not isinstance(world, RubyObject) or world.name != "RPG::Map":
            raise ValueError(f"RXDATA inválido na fonte: {map_id}")
        tile_id = world.attrs["@tileset_id"]
        if not 0 < tile_id < len(tiles) or not isinstance(tiles[tile_id], RubyObject):
            raise ValueError(f"Tileset da fonte não encontrado para {map_id}")
        tile = tiles[tile_id].attrs
        name = text(infos[map_id].attrs["@name"])
        parents = ancestry(infos, map_id)
        has_terrain = tiles_present(world)
        events = []
        for event_id, event in sorted(world.attrs["@events"].items()):
            events.append({
                "id": event_id, "name": text(event.attrs["@name"]),
                "xy": [event.attrs["@x"], event.attrs["@y"]],
                "triggers": [page.attrs["@trigger"] for page in event.attrs["@pages"]],
                "command_codes": sorted({
                    command.attrs["@code"] for page in event.attrs["@pages"]
                    for command in page.attrs["@list"]
                }),
            })
        rows.append({
            "source_id": map_id, "name": name, "parents": parents, "sha256": digest(raw),
            "catalogued": map_id in catalogued, "has_terrain": has_terrain,
            "dimensions": [world.attrs["@width"], world.attrs["@height"]],
            "tileset": tile_id, "tileset_name": text(tile["@tileset_name"]),
            "tileset_tables": sorted(key for key in tile if key in {"@passages", "@priorities", "@terrain_tags"}),
            "scope": scope_for(name, parents, has_terrain, len(events)), "events": events,
            "encounter_methods": sorted(encounters.get(map_id, {})),
        })
    first_copy_by_digest = {}
    for row in rows:
        if row["has_terrain"] or row["events"]:
            first_copy = first_copy_by_digest.setdefault(row["sha256"], row["source_id"])
            if first_copy != row["source_id"]:
                row["identical_rxdata_to"] = first_copy
    routes = routes_by_number(rows)
    return {
        "revision": UPSTREAM, "map_count": len(rows),
        "tileset_count": sum(isinstance(tile, RubyObject) for tile in tiles),
        "catalogued": len(catalogued),
        "scope_counts": dict(Counter(row["scope"] for row in rows)),
        "scope_review_ids": [row["source_id"] for row in rows if row["scope"] == "scope_review_required"],
        "identical_non_empty_rxdata": {row["source_id"]: row["identical_rxdata_to"]
                                     for row in rows if "identical_rxdata_to" in row},
        "primary_routes": routes,
        "uncatalogued_routes": {number: mid for number, mid in routes.items() if mid not in catalogued},
        "route_classification_basis": "exact source names and physical terrain",
        "encounter_audit": encounter_audit, "maps": rows,
    }


def no_overlap_borders(contents: str, mapping: dict[int, int], maps: dict) -> list[dict]:
    """Measure the shared axis using the same relative anchors as MapFactory."""
    inverse = {dest: source for source, dest in mapping.items()}
    errors = []
    for line in contents.splitlines():
        fields = line.split("#", 1)[0].split(",")
        if len(fields) != 6 or not (fields[0].strip().isdigit() and fields[3].strip().isdigit()):
            continue
        src, side, a, dest, other_side, b = (part.strip() for part in fields)
        if int(src) not in inverse or int(dest) not in inverse:
            continue
        if (side, other_side) not in {
            ("North", "South"), ("South", "North"), ("East", "West"), ("West", "East"),
        }:
            continue
        if not re.fullmatch(r"-?[0-9]+", a) or not re.fullmatch(r"-?[0-9]+", b):
            continue
        source_ids = [inverse[int(src)], inverse[int(dest)]]
        axis = "@width" if side in {"North", "South"} else "@height"
        width, other_width = (maps[mid].attrs[axis] for mid in source_ids)
        shift = int(a) - int(b)
        overlap = min(width, shift + other_width) - max(0, shift)
        if overlap <= 0:
            errors.append({
                "record": ",".join((src, side, a, dest, other_side, b)),
                "source_ids": source_ids, "edge_lengths": [width, other_width],
                "shared_tiles": 0,
            })
    return errors


def inspect_delivery(read, paths: set[str]) -> dict:
    infos = loads(read("Data/MapInfos.rxdata"))
    ids = materialized_ids(paths)
    ownership = {}
    for region, rel, key in MANIFESTS:
        if rel not in paths:
            continue
        proof = json.loads(read(rel))
        claimed = proof.get(key) if isinstance(proof, dict) else None
        if key == "maps" and isinstance(claimed, dict):
            values = list(claimed.values())
        elif key == "file_hashes" and isinstance(claimed, dict):
            values = [int(match[1]) for path in claimed if (match := MAP_FILE.fullmatch(path))]
        elif key == "map_ids" and isinstance(claimed, list):
            values = claimed
        else:
            raise ValueError(f"Manifesto de MapIDs inválido: {rel}")
        if not values or any(type(dest) is not int or dest <= 0 for dest in values):
            raise ValueError(f"{region} tem MapIDs ausentes ou inválidos: {rel}")
        destinations = set(values)
        if len(destinations) != len(values) or not destinations <= ids.intersection(infos):
            raise ValueError(f"{region} perdeu arquivos, identidades ou entradas em MapInfos")
        if any(destinations.intersection(current) for owner, current in ownership.items()
               if owner != region):
            raise ValueError(f"MapID compartilhado por duas regiões: {region}")
        ownership[region] = sorted(destinations.union(ownership.get(region, [])))
    proof = json.loads(read(MANIFEST.as_posix()))
    mapping = validate_manifest(proof)
    verify_markers(read, proof)
    maps = {source: loads(read(f"Data/Map{dest:03}.rxdata")) for source, dest in mapping.items()}
    summaries, errors = {}, {}
    for source, world in sorted(maps.items()):
        try:
            summaries[source] = audit_map(source, world, maps, mapping)
        except ValueError as error:
            errors[source] = str(error)
    connections = read("PBS/map_connections.txt").decode("utf-8-sig")
    untraversable = no_overlap_borders(connections, mapping, maps)
    try:
        borders = {"status": "VERIFIED", **inspect_connections(connections, mapping, maps)}
    except ValueError as error:
        borders = {"status": "BLOCKED_INVENTORY", "first_strict_error": str(error)}
    borders["edges_without_geometric_overlap"] = untraversable
    encounters = parse_compiled_encounters(
        read("PBS/encounters_hoenn_pilot.txt").decode("utf-8-sig"), set(mapping.values()))
    occupied = ids | set(infos)
    claimed = set().union(*ownership.values())
    return {
        "maps": mapping, "start": proof["start"], "town": proof["town"],
        "installed_encounter_maps": len(encounters), "encounter_methods_by_destination": encounters,
        "observed_transfer_graph": summaries, "map_audit_errors": errors, "borders": borders,
        "global_mapinfo_ids": sorted(infos), "global_file_ids": sorted(ids),
        "highest_observed_id": max(occupied), "manifest_ownership": ownership,
        "observed_other_ids": sorted(occupied - claimed),
        "observed_unoccupied_in_hoenn_range": sorted(set(MAP_RANGE) - occupied),
        "allocation_approved": False,
    }


def read_android(archive_path: Path, manifest_path: Path, revision: str) -> dict:
    manifest = json.loads(manifest_path.read_text("utf-8"))
    if archive_path.stat().st_size != manifest["full"]["size"]:
        raise ValueError("Tamanho do ZIP Android difere do manifesto publicado")
    with archive_path.open("rb") as stream:
        archive_sha = hashlib.file_digest(stream, "sha256").hexdigest()
    if archive_sha != manifest["full"]["sha256"]:
        raise ValueError("Hash do ZIP Android difere do manifesto publicado")
    verify_archive(archive_path, revision, channel="multiregion")
    with zipfile.ZipFile(archive_path) as archive:
        installed = verify_manifest(archive, ARCHIVE_ROOT, "multiregion", revision)
        for field in ("channel", "revision", "files", "immutable"):
            if manifest[field] != installed[field]:
                raise ValueError(f"Manifesto Android publicado diverge do ZIP: {field}")
        paths = {name.removeprefix(ARCHIVE_ROOT) for name in archive.namelist() if name.startswith(ARCHIVE_ROOT)}
        result = inspect_delivery(lambda path: archive.read(ARCHIVE_ROOT + path), paths)
    return {"revision": revision, "zip_sha256": archive_sha, **result}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tree", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--windows-game", type=Path, default=ROOT / "game")
    parser.add_argument("--android-zip", type=Path, required=True)
    parser.add_argument("--android-manifest", type=Path, required=True)
    parser.add_argument("--revision", required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        report_path = require_private_path(args.report)
        game = args.windows_game.resolve()
        if game != ROOT / "game":
            require_private_path(game)
        verify_installed(game)
        source = source_inventory(args.tree, args.source)
        paths = {f"Data/{path.name}" for path in (game / "Data").iterdir() if path.is_file()}
        windows = inspect_delivery(lambda path: (game / path).read_bytes(), paths)
        android = read_android(args.android_zip, args.android_manifest, args.revision)
        mapping_matches = windows["maps"] == android["maps"]
        blocked = not mapping_matches or any(
            delivery["map_audit_errors"] or delivery["borders"]["status"] != "VERIFIED"
            or delivery["borders"]["edges_without_geometric_overlap"]
            for delivery in (windows, android)
        )
        status = "BLOCKED_INVENTORY" if blocked else "STATIC_BASELINE_VERIFIED"
        report = {
            "schema": 1, "region": "HOENN", "phase": "H00", "status": status, "source": source,
            "windows_installation": windows, "android_published_bundle": android,
            "map_ids_match_across_platforms": mapping_matches,
            "rights": "BLOCKED_RIGHTS", "android_native_qa": "BLOCKED_ENV",
            "gameplay_acceptance": False,
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": status, "source_maps": source["map_count"], "catalogued": source["catalogued"],
            "uncatalogued_routes": source["uncatalogued_routes"],
            "map_ids_match_across_platforms": mapping_matches,
            "windows_map_audit_errors": len(windows["map_audit_errors"]),
            "android_map_audit_errors": len(android["map_audit_errors"]),
        }))
        return 2 if blocked else 0
    except (OSError, RuntimeError, ValueError, KeyError, TypeError, zipfile.BadZipFile) as error:
        parser.exit(2, f"Auditoria H00 bloqueada: {error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
