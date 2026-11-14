#!/usr/bin/env python3
"""Audit the public Hoenn pilot against its own source definitions (read-only).

This check uses committed scripts and site JSON only. It DOES NOT inspect the
private donor ZIP, native Data/*.rxdata, installed Game.exe, save files, or a
running RPG Maker XP engine. Passing this check is never gameplay approval.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import deque
from pathlib import Path

from audit_hoenn_baseline import PILOT
from pilot_hoenn import (
    BGM, BORDERS, LAND_ENCOUNTERS, CAVE_ENCOUNTERS, MAP_BGM, OUTDOORS, PEOPLE,
    ROUTE_102_TRAINERS, RIVAL_NAMES, RIVAL_TEAMS, SOURCE_MAPS, START, UPSTREAM, WARP_PAIRS,
)
from hoenn_stage3 import (
    SOURCE_MAPS_STAGE3, OFFSET_BORDERS, LAND_ENCOUNTERS_STAGE3,
    TRAINERS_STAGE3, PICKUPS_STAGE3, SIGNS_STAGE3, NPCS_STAGE3,
    FOREST_AQUA_TRIGGERS, FOREST_AQUA_PBS, FOREST_AQUA_TEAM,
)
from hoenn_stage4 import (
    SOURCE_MAPS_STAGE4, OFFSET_BORDERS_STAGE4, TRAINERS_STAGE4,
    ROXANNE_PBS, ROXANNE_TEAM, TUNNEL_AQUA_PBS, TUNNEL_AQUA_TEAM,
    PICKUPS_STAGE4, SIGNS_STAGE4, NPCS_STAGE4, CUT_TREES_STAGE4,
    RUSTBORO_THEFT_TRIGGERS, TUNNEL_AQUA_EVENT, ROXANNE_EVENT,
    TUNNEL_VERDANTURF_GATE,
)
from hoenn_stage5 import (
    SOURCE_MAPS_STAGE5, OFFSET_BORDERS_STAGE5, WARP_PAIRS_STAGE5,
    BOAT_POINTS_STAGE5, CAVE_ENCOUNTERS_STAGE5, TRAINERS_STAGE5,
    BRAWLY_PBS, BRAWLY_TEAM, MUSEUM_AQUA, NPCS_STAGE5,
    MUSEUM_FEE_GATE, SLATEPORT_NORTH_GATE, SIGNS_STAGE5, PICKUPS_STAGE5,
)

ROOT = Path(__file__).resolve().parents[2]
CATALOG = "site/public/data/hoenn-pilot.json"
REGISTRY = "site/public/data/regions.json"
HANDLERS = "scripts/regions/HoennPilot.rb"
AUDIT_VERSION = 1


def audit(root: Path = ROOT) -> dict:
    """Return every inconsistency rather than treating public catalog as proof."""
    root = Path(root)
    catalog = json.loads((root / CATALOG).read_text(encoding="utf-8"))
    registry = json.loads((root / REGISTRY).read_text(encoding="utf-8"))
    plugin = (root / HANDLERS).read_text(encoding="utf-8")
    errors: list[str] = []
    source_ids = set(SOURCE_MAPS)
    if source_ids != set(PILOT):
        errors.append(f"Baseline/source MapIDs differ: {sorted(source_ids ^ set(PILOT))}")
    if not re.fullmatch(r"[a-f0-9]{40}", UPSTREAM):
        errors.append("Unpinned or invalid upstream revision")
    if START[0] not in source_ids:
        errors.append("Starting source map is not part of the pilot")
    if catalog.get("region") != "hoenn" or catalog.get("schema") != 1:
        errors.append("Wrong Hoenn site catalog identity/schema")
    if registry["regions"]["HOENN"]["status"] not in ("planned", "prototype"):
        errors.append("Hoenn must not be declared playable by a static audit")

    locations = catalog.get("locations", [])
    names = [row.get("name") for row in locations]
    if len(names) != len(set(names)):
        errors.append("Duplicate locations in the site catalog")
    if set(names) != set(SOURCE_MAPS.values()):
        errors.append(f"Map catalog differs from pilot source: {sorted(set(names) ^ set(SOURCE_MAPS.values()))}")
    by_name = {row["name"]: row for row in locations}
    for map_id, name in SOURCE_MAPS.items():
        if name not in by_name:
            continue
        expected = LAND_ENCOUNTERS.get(map_id, ())
        actual = by_name[name].get("encounters", {})
        expected_slots = sorted((species, low, high, weight) for weight, species, low, high in expected)
        actual_slots = sorted(tuple(row) for row in actual.get("Grama", []))
        if expected_slots != actual_slots:
            errors.append(f"Map {map_id} ({name}): grass encounter slots differ from native pilot generator")
        cave_slots = sorted((species, low, high, weight)
                            for weight, species, low, high in CAVE_ENCOUNTERS.get(map_id, ()))
        if sorted(tuple(row) for row in actual.get("Caverna", [])) != cave_slots:
            errors.append(f"Map {map_id} ({name}): cave encounter slots differ from native pilot generator")
        if set(actual) - {"Grama", "Caverna"}:
            errors.append(f"Map {map_id} ({name}): unsupported encounter method in public catalog")
    for map_id, encounters in CAVE_ENCOUNTERS.items():
        if map_id not in source_ids or sum(weight for weight, *_ in encounters) != 100:
            errors.append(f"Invalid cave encounter weights/map: {map_id}")
        if any(weight <= 0 or low <= 0 or high < low for weight, _, low, high in encounters):
            errors.append(f"Invalid cave encounter level/weight bounds: {map_id}")
    for map_id, encounters in LAND_ENCOUNTERS.items():
        if map_id not in source_ids:
            errors.append(f"Encounter route {map_id} has no imported map")
        if sum(weight for weight, *_ in encounters) != 100:
            errors.append(f"Encounter weights on map {map_id} do not total 100")
        if any(weight <= 0 or low <= 0 or high < low for weight, _, low, high in encounters):
            errors.append(f"Invalid encounter chance/level bounds on map {map_id}")
        if len({species for _, species, _, _ in encounters}) != len(encounters):
            errors.append(f"Duplicate species slot on map {map_id}")

    native_trainers = {name: (SOURCE_MAPS[102], tuple(team))
                       for _, _, _, name, _, team in ROUTE_102_TRAINERS}
    native_trainers.update({name: (SOURCE_MAPS[mid], tuple(team))
                            for mid, _, _, kind, name, _, team, _ in TRAINERS_STAGE3})
    native_trainers["Recruta"] = (SOURCE_MAPS[156], tuple(FOREST_AQUA_TEAM))
    native_trainers.update({name: (SOURCE_MAPS[mid], tuple(team))
                            for mid, _, _, kind, name, _, team, _ in TRAINERS_STAGE4})
    native_trainers["Roxanne"] = (SOURCE_MAPS[27], tuple(ROXANNE_TEAM))
    # Recruta appears in both woods and Rusturf. Catalog titles disambiguate
    # the two identical PBS names (versions 304 and 405).
    native_trainers["Recruta Aqua (Rusturf)"] = (SOURCE_MAPS[157], tuple(TUNNEL_AQUA_TEAM))
    native_trainers.update({name: (SOURCE_MAPS[mid], tuple(team))
                            for mid, _, _, kind, name, _, team, _ in TRAINERS_STAGE5})
    native_trainers["Brawly"] = (SOURCE_MAPS[31], tuple(BRAWLY_TEAM))
    for index, (_, _, _, team) in enumerate(MUSEUM_AQUA, 1):
        native_trainers[f"Recruta Aqua (Museu {index})"] = (SOURCE_MAPS[39], tuple(team))
    published = catalog.get("trainers", [])
    names_published = [row.get("name") for row in published]
    if len(names_published) != len(set(names_published)):
        errors.append("Duplicate trainers in published Hoenn pilot")
    if set(names_published) != set(native_trainers):
        errors.append(f"Published trainers differ from pilot: {sorted(set(names_published) ^ set(native_trainers))}")
    if len(native_trainers) != (len(ROUTE_102_TRAINERS) + len(TRAINERS_STAGE3) +
                                len(TRAINERS_STAGE4) + len(TRAINERS_STAGE5) +
                                len(MUSEUM_AQUA) + 4):
        errors.append("Duplicate trainer definitions in native Hoenn pilot")
    for row in published:
        name = row.get("name")
        if name not in native_trainers:
            continue
        teams = row.get("teams", [])
        party = [tuple(pokemon) for pokemon in teams[0].get("pokemon", [])] if len(teams) == 1 else []
        area, expected_team = native_trainers[name]
        if row.get("area") != area or party != list(expected_team):
            errors.append(f"Trainer {name}: team/area differs from pilot generator")
        expect_leader = name in ("Roxanne", "Brawly")
        expect_badge = ("STONE" if name == "Roxanne" else "KNUCKLE" if name == "Brawly" else None)
        if row.get("leader") is not expect_leader or row.get("badge") != expect_badge:
            errors.append(f"Trainer {name}: incorrect gym leader/badge metadata")

    all_edges = [tuple(pair) for pair in BORDERS]
    if any(a not in source_ids or b not in source_ids for a, _, b, _ in all_edges):
        errors.append("A border connection references an unknown source map")
    if any(a not in source_ids or b not in source_ids for a, _, _, b, _, _ in (*OFFSET_BORDERS, *OFFSET_BORDERS_STAGE4, *OFFSET_BORDERS_STAGE5)):
        errors.append("An offset border references an unknown source map")
    if any(a[0] not in source_ids or b[0] not in source_ids
           for a, _, b, _ in WARP_PAIRS):
        errors.append("A door/ladder references an unknown source map")
    adjacency = {mid: set() for mid in source_ids}
    for a, b in ([(a, b) for a, _, b, _ in BORDERS] +
                 [(a, b) for a, _, _, b, _, _ in (*OFFSET_BORDERS, *OFFSET_BORDERS_STAGE4, *OFFSET_BORDERS_STAGE5)]):
        if a in adjacency and b in adjacency:
            adjacency[a].add(b)
            adjacency[b].add(a)
    for a, _, b, _ in WARP_PAIRS:
        if a[0] in adjacency and b[0] in adjacency:
            adjacency[a[0]].add(b[0])
            adjacency[b[0]].add(a[0])
    house, dewford, slateport = BOAT_POINTS_STAGE5
    for a, b in ((house, dewford), (dewford, slateport)):
        adjacency[a[0]].add(b[0])
        adjacency[b[0]].add(a[0])
    seen = {START[0]}
    queue = deque(seen)
    while queue:
        for nxt in adjacency.get(queue.popleft(), ()):
            if nxt not in seen:
                seen.add(nxt)
                queue.append(nxt)
    if seen != source_ids:
        errors.append(f"Disconnected pilot map nodes: {sorted(source_ids - seen)}")

    occupied: dict[tuple[int, int, int], str] = {}
    points = (
        [(mid, x, y, f"NPC:{name}") for mid, x, y, name, _, _ in PEOPLE]
        + [(a[0], a[1], a[2], "warp") for a, _, b, _ in WARP_PAIRS]
        + [(b[0], b[1], b[2], "warp") for a, _, b, _ in WARP_PAIRS]
        + [(102, x, y, f"trainer:{name}") for x, y, _, name, _, _ in ROUTE_102_TRAINERS]
        + [(mid, x, y, f"trainer:{name}") for mid, x, y, _, name, _, _, _ in TRAINERS_STAGE3]
        + [(104, 138, 15, "Twins Mia")]
        + [(mid, x, y, f"NPC:{handler}") for mid, x, y, _, handler in NPCS_STAGE3]
        + [(17, 9, 4, "nurse"), (17, 9, 5, "nurse counter"), (18, 3, 5, "mart")]
        + [(mid, x, y, f"sign:{key}") for mid, x, y, key, _ in SIGNS_STAGE3]
        + [(mid, x, y, f"pickup:{key}") for mid, x, y, key, _, _ in PICKUPS_STAGE3]
        + [(mid, x, y, "Aqua trigger") for mid, x, y in FOREST_AQUA_TRIGGERS]
        + [(mid, x, y, f"trainer4:{name}") for mid, x, y, _, name, _, _, _ in TRAINERS_STAGE4]
        + [(mid, x, y, f"npc4:{handler}") for mid, x, y, _, handler in NPCS_STAGE4]
        + [(22, 9, 5, "Rustboro nurse counter"), (23, 4, 5, "Rustboro mart counter")]
        + [(mid, x, y, f"sign4:{key}") for mid, x, y, key, _ in SIGNS_STAGE4]
        + [(mid, x, y, f"item4:{key}") for mid, x, y, key, _, _ in PICKUPS_STAGE4]
        + [(mid, x, y, "CutTree") for mid, x, y in CUT_TREES_STAGE4]
        + [(mid, x, y, "Devon theft trigger") for mid, x, y in RUSTBORO_THEFT_TRIGGERS]
        + [(mid, x, y, f"trainer5:{name}") for mid, x, y, _, name, _, _, _ in TRAINERS_STAGE5]
        + [(mid, x, y, f"npc5:{handler}") for mid, x, y, _, handler in NPCS_STAGE5]
        + [(29, 9, 5, "Dewford Center counter"), (34, 9, 5, "Slateport Center counter"),
           (35, 4, 5, "Slateport Mart counter")]
        + [(mid, x, y, f"sign5:{key}") for mid, x, y, key, _ in SIGNS_STAGE5]
        + [(mid, x, y, f"item5:{key}") for mid, x, y, key, _, _ in PICKUPS_STAGE5]
        + [(mid, x, y, "museum fee") for mid, x, y in MUSEUM_FEE_GATE]
        + [(mid, x, y, "Slateport north gate") for mid, x, y in SLATEPORT_NORTH_GATE]
        + [(39, 35, 7, "Aqua museum one"), (39, 37, 7, "Aqua museum two")]
        + [(*ROXANNE_EVENT, "Roxanne"), (*TUNNEL_AQUA_EVENT, "Aqua"),
           (*TUNNEL_VERDANTURF_GATE, "blocked Verdanturf exit")]
        + [(8, 25, 6, "profile"), (8, 26, 3, "clock"),
           (101, 10, 18, "Birch rescue"), (101, 11, 18, "Birch rescue")]
    )
    for mid, x, y, label in points:
        if mid not in source_ids:
            errors.append(f"Event {label} references missing map {mid}")
        key = (mid, x, y)
        if key in occupied:
            errors.append(f"Overlapping events on {key}: {occupied[key]} vs {label}")
        occupied[key] = label

    defined = set(re.findall(r"(?m)^\s*def self\.([a-z0-9_]+[!?]?)(?=\s|\(|$)", plugin))
    required = {"state", "choose_profile", "choose_starter", "route_birch",
                "choose_birch_ball", "rescue_birch_battle", "rival_103",
                "rival_name", "birch", "mother", "mart", "heal", "clock",
                "battle", "verify_compilation", "norman_intro", "wally_family",
                "flower_shop", "briney", "pickup", "sign", "forest_aqua",
                "battle_stage3", "roxanne", "roxanne_tm", "stone_badge?",
                "cutter", "cut_tree", "teacher", "rustboro_theft", "peeko",
                "briney_route116", "rusturf_aqua", "rusturf_goods_reward",
                "devon_employee", "devon_route116", "mr_stone", "tunnelers",
                "rusturf_east_gate", "sign_stage4",
                "sign_stage5", "knuckle_badge?", "brawly", "flash_hiker",
                "steven_letter", "boat_to", "dewford_boat", "slateport_boat",
                "shipyard", "museum_entry", "museum_aqua", "stern",
                "slateport_north_gate", "soothe_bell", "soft_sand"}
    required.update(re.match(r"BlueHoennPilot\.([a-z_]+)", handler).group(1)
                    for *_, handler in PEOPLE)
    if missing := required - defined:
        errors.append(f"Hoenn runtime handler(s) missing: {sorted(missing)}")
    if any(mid not in source_ids for mid in MAP_BGM):
        errors.append("Regional BGM references missing pilot map")
    if any(label not in BGM for label in MAP_BGM.values()):
        errors.append("Regional BGM refers to an unknown pilot track alias")
    if not set(OUTDOORS).issubset(source_ids):
        errors.append("Outdoor metadata refers to missing maps")
    if set(RIVAL_TEAMS) != {"TREECKO", "TORCHIC", "MUDKIP"} or set(RIVAL_NAMES) != {"May", "Brendan"}:
        errors.append("Wrong rival starter/gender variants")
    if len({version for _, version in RIVAL_TEAMS.values()}) != 3:
        errors.append("Duplicate rival trainer PBS versions")
    if any(starter == enemy for starter, (enemy, _) in RIVAL_TEAMS.items()):
        errors.append("Rival must choose counter-starter species")


    # A passing static audit still does not approve gameplay in Game.exe.
    gaps = [
        "Dewford, Slateport and Granite Cave scripts were authored without replacing original Blue battle engine.",
        "Briney's scripted boat skips sea routes 105,107,108 and islands; Surf and water trainers are not imported.",
        "Brawly KNUCKLE badge, trainer visuals and Bulk Up TM require Windows Game.exe proof.",
        "Flash HM is awarded in Granite Cave but native darkness/Cut/Flash use still needs field QA.",
        "Granite Cave B1F cracked-floor puzzle is not yet animated or implemented; ladders are mapped.",
        "Steven LETTER/Steel Wing and Stern Devon package require save/reload and item identity tests.",
        "Two museum Aqua battles are scripted with separate PBS and flags; confirm scene and colliders natively.",
        "Slateport Route 110 is not installed; north exit remains blocked pending the next phase.",
        "Original local music, crowds, full trainer roster, beach water and all NPCs need later audits.",
    ]
    return {
        "schema": AUDIT_VERSION,
        "region": "HOENN",
        "mode": "READ_ONLY_REPOSITORY_CONTRACT",
        "source_revision": UPSTREAM,
        "source_maps": len(source_ids),
        "source_ids": list(SOURCE_MAPS),
        "public_catalog_locations": len(locations),
        "route_102_trainers": len(ROUTE_102_TRAINERS),
        "stage3_trainer_presets": len(TRAINERS_STAGE3) + 1,
        "stage3_pickup_events": len(PICKUPS_STAGE3),
        "stage3_source_maps": len(SOURCE_MAPS_STAGE3),
        "stage4_source_maps": len(SOURCE_MAPS_STAGE4),
        "stage4_cut_trees": len(CUT_TREES_STAGE4),
        "stage4_trainer_presets": len(TRAINERS_STAGE4) + 2,
        "stage4_pickup_events": len(PICKUPS_STAGE4),
        "stage4_scripted_only": True,
        "stage5_source_maps": len(SOURCE_MAPS_STAGE5),
        "stage5_boat_stops": len(BOAT_POINTS_STAGE5),
        "stage5_trainer_presets": len(TRAINERS_STAGE5) + len(MUSEUM_AQUA) + 1,
        "stage5_pickup_events": len(PICKUPS_STAGE5),
        "stage5_cave_maps": len(CAVE_ENCOUNTERS_STAGE5),
        "stage5_scripted_only": True,
        "stage3_provisional_runtime_only": True,
        "rival_pbs_variants_prepared": len(RIVAL_NAMES) * len(RIVAL_TEAMS),
        "three_physical_starter_ball_events_prepared": True,
        "rival_route103_event_prepared": True,
        "pokedex_running_shoes_handlers_prepared": True,
        "wild_route_maps": sorted(LAND_ENCOUNTERS),
        "cave_route_maps": sorted(CAVE_ENCOUNTERS),
        "wild_slots": sum(len(entries) for entries in LAND_ENCOUNTERS.values()),
        "map_graph_connected": seen == source_ids,
        "runtime_handlers_checked": len(required),
        "static_contract_validated": not errors,
        "native_assets_examined": False,
        "game_exe_tested": False,
        "android_tested": False,
        "errors": errors,
        "known_story_gaps": gaps,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, help="Write JSON report at this path")
    parser.add_argument("--strict", action="store_true", help="Exit 2 if any source/catalog contract fails")
    args = parser.parse_args()
    report = audit(args.root)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Hoenn audit written to: {args.output}")
    else:
        print(output, end="")
    return 2 if args.strict and report["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
