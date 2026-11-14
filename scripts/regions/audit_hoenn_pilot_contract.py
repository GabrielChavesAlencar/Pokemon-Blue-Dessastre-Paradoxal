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
from hoenn_stage6 import (
    SOURCE_MAPS_STAGE6, OFFSET_BORDERS_STAGE6, WARP_PAIRS_STAGE6,
    CYCLE_TRANSFERS_STAGE6, LAND_ENCOUNTERS_STAGE6, TRAINERS_STAGE6,
    WATTSON_PBS, WATTSON_TEAM, WALLY_PBS, WALLY_TEAM,
    RIVAL_110_TEAMS, RIVAL_110_EVENT, RIVAL_110_TRIGGERS,
    WALLY_EVENT, WATTSON_EVENT, GYM_GATES_STAGE6, GYM_SWITCHES_STAGE6,
    NPCS_STAGE6, PICKUPS_STAGE6, SIGNS_STAGE6, MAUVILLE_FUTURE_GATES,
)
from hoenn_stage7 import (
    SOURCE_MAPS_STAGE7, OFFSET_BORDERS_STAGE7, WARP_PAIRS_STAGE7,
    CABLE_POINTS_STAGE7, LAND_ENCOUNTERS_STAGE7, CAVE_ENCOUNTERS_STAGE7,
    TRAINERS_STAGE7, FLANNERY_PBS, FLANNERY_TEAM,
    TABITHA_PBS, TABITHA_TEAM, MAXIE_PBS, MAXIE_TEAM,
    MAGMA_GRUNTS_STAGE7, MAGMA_GRUNT_EVENTS, TABITHA_EVENT, MAXIE_EVENT,
    METEORITE_MACHINE_EVENT, METEOR_FALLS_CUTSCENE, FLANNERY_EVENT,
    ROUTE112_MAGMA_BLOCKERS, NPCS_STAGE7, FUTURE_GATES_STAGE7,
    PICKUPS_STAGE7, SIGNS_STAGE7, GYM_STEAM_PAIRS_STAGE7,
)
from hoenn_stage8 import (
    SOURCE_MAPS_STAGE8, OFFSET_BORDERS_STAGE8, WARP_PAIRS_STAGE8,
    LAND_ENCOUNTERS_STAGE8, NORMAN_EVENT, NORMAN_PBS, NORMAN_TEAM,
    WINONA_EVENT, WINONA_PBS, WINONA_TEAM, SHELLY_EVENT, SHELLY_PBS, SHELLY_TEAM,
    AQUA_INSTITUTE, RIVAL_119_EVENT, RIVAL_LILYCOVE_EVENT, RIVAL_119_TEAMS,
    RIVAL_LILYCOVE_TEAMS, TRAINERS_STAGE8, STEVEN_SCOPE_EVENT,
    FORTREE_KECLEON_EVENT, ROUTE120_KECLEON_EVENT, WEATHER_REWARD_EVENT,
    NPCS_STAGE8, FUTURE_GATES_STAGE8, SIGNS_STAGE8, PICKUPS_STAGE8,
    NORMAN_GYM_DOORS,
)
from hoenn_stage9 import (
    SOURCE_MAPS_STAGE9, SURF_BORDERS_STAGE9, STAGE9_MAP_GRAPH_EDGES,
    TATE_LIZA_EVENTS, TATE_LIZA_PBS, TATE_LIZA_TEAM,
    MATT_PBS, MATT_TEAM, MAXIE_HIDEOUT_PBS, MAXIE_HIDEOUT_TEAM,
    TABITHA_HIDEOUT_PBS, TABITHA_HIDEOUT_TEAM, MAXIE_SPACE_PBS,
    MAXIE_SPACE_TEAM, TABITHA_SPACE_PBS, TABITHA_SPACE_TEAM,
    ARCHIE_ORB_EVENT, MT_PYRE_ARCHIE, MT_PYRE_OLD_LADY,
    TABITHA_HIDEOUT_EVENT, MAXIE_HIDEOUT_EVENT, GROUDON_CUTSCENE_EVENT,
    MATT_HIDEOUT_EVENT, SUBMARINE_EVENT, SPACE_MAXIE_EVENT,
    SPACE_STEVEN_EVENT, SPACE_GRUNT_EVENTS, TRAINERS_STAGE9,
    PYRE_AQUA_GRUNTS, MAGMA_HIDEOUT_GRUNTS, AQUA_HIDEOUT_GRUNTS,
    NPCS_STAGE9, SIGNS_STAGE9, MAGMA_HIDEOUT_GATE, AQUA_HIDEOUT_GATE,
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
    native_trainers.update({name: (SOURCE_MAPS[mid], tuple(team))
                            for mid, _, _, kind, name, _, team, _ in TRAINERS_STAGE6})
    native_trainers["Wattson"] = (SOURCE_MAPS[47], tuple(WATTSON_TEAM))
    native_trainers["Wally"] = (SOURCE_MAPS[41], tuple(WALLY_TEAM))
    for name in RIVAL_NAMES:
        for chosen, (version, team) in RIVAL_110_TEAMS.items():
            native_trainers[f"{name} (Rota 110/{chosen.title()})"] = (
                SOURCE_MAPS[113], tuple(team))
    native_trainers.update({name: (SOURCE_MAPS[mid], tuple(team))
                            for mid, _, _, kind, name, _, team, _ in TRAINERS_STAGE7})
    native_trainers["Flannery"] = (SOURCE_MAPS[63], tuple(FLANNERY_TEAM))
    native_trainers["Tabitha"] = (SOURCE_MAPS[178], tuple(TABITHA_TEAM))
    native_trainers["Maxie"] = (SOURCE_MAPS[178], tuple(MAXIE_TEAM))
    for index, (_kind, _name, _version, team) in enumerate(MAGMA_GRUNTS_STAGE7, 1):
        native_trainers[f"Recruta Magma (Mt. Chimney {index})"] = (SOURCE_MAPS[178], tuple(team))
    native_trainers.update({name: (SOURCE_MAPS[mid], tuple(team))
                            for mid, _, _, kind, name, _, team, _ in TRAINERS_STAGE8})
    native_trainers["Norman"] = (SOURCE_MAPS[20], tuple(NORMAN_TEAM))
    native_trainers["Winona"] = (SOURCE_MAPS[68], tuple(WINONA_TEAM))
    native_trainers["Shelly"] = (SOURCE_MAPS[137], tuple(SHELLY_TEAM))
    for mid,x,y,version,team in AQUA_INSTITUTE:
        native_trainers[f"Recruta Aqua (Instituto {version})"] = (
            SOURCE_MAPS[137], tuple(team))
    for name in RIVAL_NAMES:
        for chosen,(version,team) in RIVAL_119_TEAMS.items():
            native_trainers[f"{name} (Rota 119/{chosen.title()})"] = (
                SOURCE_MAPS[135],tuple(team))
        for chosen,(version,team) in RIVAL_LILYCOVE_TEAMS.items():
            native_trainers[f"{name} (Lilycove/{chosen.title()})"] = (
                SOURCE_MAPS[69],tuple(team))
    native_trainers.update({name:(SOURCE_MAPS[mid],tuple(team))
                            for mid,_,_,kind,name,_,team,_ in TRAINERS_STAGE9})
    for group,title,area in (
        (PYRE_AQUA_GRUNTS,"Aqua · Mt. Pyre",SOURCE_MAPS[213]),
        (MAGMA_HIDEOUT_GRUNTS,"Magma · Hideout",None),
        (AQUA_HIDEOUT_GRUNTS,"Aqua · Hideout",None),
        (SPACE_GRUNT_EVENTS,"Magma · Space Center",SOURCE_MAPS[81]),
    ):
        for mid,x,y,version,team in group:
            native_trainers[f"Recruta {title} ({version})"] = (SOURCE_MAPS[mid],tuple(team))
    native_trainers["Tate & Liza"]=(SOURCE_MAPS[82],tuple(TATE_LIZA_TEAM))
    native_trainers["Matt"]=(SOURCE_MAPS[217],tuple(MATT_TEAM))
    native_trainers["Maxie (Esconderijo Magma)"]=(SOURCE_MAPS[189],tuple(MAXIE_HIDEOUT_TEAM))
    native_trainers["Tabitha (Esconderijo Magma)"]=(SOURCE_MAPS[189],tuple(TABITHA_HIDEOUT_TEAM))
    native_trainers["Maxie (Centro Espacial)"]=(SOURCE_MAPS[81],tuple(MAXIE_SPACE_TEAM))
    native_trainers["Tabitha (Centro Espacial)"]=(SOURCE_MAPS[81],tuple(TABITHA_SPACE_TEAM))
    published = catalog.get("trainers", [])
    names_published = [row.get("name") for row in published]
    if len(names_published) != len(set(names_published)):
        errors.append("Duplicate trainers in published Hoenn pilot")
    if set(names_published) != set(native_trainers):
        errors.append(f"Published trainers differ from pilot: {sorted(set(names_published) ^ set(native_trainers))}")
    if len(native_trainers) != (len(ROUTE_102_TRAINERS) + len(TRAINERS_STAGE3) +
                                len(TRAINERS_STAGE4) + len(TRAINERS_STAGE5) +
                                len(TRAINERS_STAGE6) + len(TRAINERS_STAGE7) +
                                len(TRAINERS_STAGE8) + len(MAGMA_GRUNTS_STAGE7) +
                                len(MUSEUM_AQUA) + len(AQUA_INSTITUTE) +
                                12 + 2 * (len(RIVAL_110_TEAMS) +
                                          len(RIVAL_119_TEAMS) +
                                          len(RIVAL_LILYCOVE_TEAMS)) +
                                len(TRAINERS_STAGE9) +
                                len(PYRE_AQUA_GRUNTS)+len(MAGMA_HIDEOUT_GRUNTS)+
                                len(AQUA_HIDEOUT_GRUNTS)+len(SPACE_GRUNT_EVENTS)+6):
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
        expect_leader = name in ("Roxanne", "Brawly", "Wattson", "Flannery", "Norman", "Winona", "Tate & Liza")
        expect_badge = ("STONE" if name == "Roxanne" else
                        "KNUCKLE" if name == "Brawly" else
                        "DYNAMO" if name == "Wattson" else
                        "HEAT" if name == "Flannery" else
                        "BALANCE" if name == "Norman" else
                        "FEATHER" if name == "Winona" else
                        "MIND" if name == "Tate & Liza" else None)
        if row.get("leader") is not expect_leader or row.get("badge") != expect_badge:
            errors.append(f"Trainer {name}: incorrect gym leader/badge metadata")

    all_edges = [tuple(pair) for pair in BORDERS]
    if any(a not in source_ids or b not in source_ids for a, _, b, _ in all_edges):
        errors.append("A border connection references an unknown source map")
    if any(a not in source_ids or b not in source_ids for a, _, _, b, _, _ in (*OFFSET_BORDERS, *OFFSET_BORDERS_STAGE4, *OFFSET_BORDERS_STAGE5, *OFFSET_BORDERS_STAGE6, *OFFSET_BORDERS_STAGE7, *OFFSET_BORDERS_STAGE8)):
        errors.append("An offset border references an unknown source map")
    if any(a[0] not in source_ids or b[0] not in source_ids
           for a, _, b, _ in WARP_PAIRS):
        errors.append("A door/ladder references an unknown source map")
    adjacency = {mid: set() for mid in source_ids}
    for a, b in ([(a, b) for a, _, b, _ in BORDERS] +
                 [(a, b) for a, _, _, b, _, _ in (*OFFSET_BORDERS, *OFFSET_BORDERS_STAGE4, *OFFSET_BORDERS_STAGE5, *OFFSET_BORDERS_STAGE6, *OFFSET_BORDERS_STAGE7, *OFFSET_BORDERS_STAGE8)]):
        if a in adjacency and b in adjacency:
            adjacency[a].add(b)
            adjacency[b].add(a)
    for a,_,_,b,_,_ in SURF_BORDERS_STAGE9:
        if a in adjacency and b in adjacency:
            adjacency[a].add(b)
            adjacency[b].add(a)
    for a,b in STAGE9_MAP_GRAPH_EDGES:
        if a not in adjacency or b not in adjacency:
            errors.append(f"Stage9 graph references unknown source map: {a}/{b}")
            continue
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
    for src, _ex, _ey, _sx, _sy, dst, _dx, _dy in CYCLE_TRANSFERS_STAGE6:
        adjacency[src].add(dst)
        adjacency[dst].add(src)
    bottom, summit = CABLE_POINTS_STAGE7
    adjacency[bottom[0]].add(summit[0])
    adjacency[summit[0]].add(bottom[0])
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
        + [(mid, x, y, f"trainer6:{name}") for mid, x, y, _, name, _, _, _ in TRAINERS_STAGE6]
        + [(mid, x, y, f"npc6:{handler}") for mid, x, y, _, handler in NPCS_STAGE6]
        + [(42, 9, 5, "Mauville nurse counter"), (43, 4, 5, "Mauville mart counter")]
        + [(mid, x, y, f"sign6:{key}") for mid, x, y, key, _ in SIGNS_STAGE6]
        + [(mid, x, y, f"item6:{key}") for mid, x, y, key, _, _ in PICKUPS_STAGE6]
        + [(*RIVAL_110_EVENT, "Rival Route110"), (*WALLY_EVENT, "Wally Mauville"),
           (*WATTSON_EVENT, "Wattson")]
        + [(mid, x, y, "rival Route110 touch") for mid, x, y in RIVAL_110_TRIGGERS]
        + [(mid, x, y, "Wattson gate") for mid, x, y, _, _ in GYM_GATES_STAGE6]
        + [(mid, x, y, "Wattson switch") for mid, x, y in GYM_SWITCHES_STAGE6]
        + [(src, x, y, "Cycling Road gate") for src, x, y, *_ in CYCLE_TRANSFERS_STAGE6]
        + [(mid, x, y, "future route gate") for mid, x, y in MAUVILLE_FUTURE_GATES]
        + [(mid, x, y, f"trainer7:{name}") for mid, x, y, _, name, _, _, _ in TRAINERS_STAGE7]
        + [(mid, x, y, f"npc7:{handler}") for mid, x, y, _, handler in NPCS_STAGE7]
        + [(54, 9, 5, "Fallarbor nurse counter"), (55, 4, 5, "Fallarbor mart counter"),
           (59, 9, 5, "Lavaridge nurse counter"), (60, 4, 5, "Lavaridge mart counter")]
        + [(mid, x, y, f"sign7:{key}") for mid, x, y, key, _ in SIGNS_STAGE7]
        + [(mid, x, y, f"item7:{key}") for mid, x, y, key, _, _ in PICKUPS_STAGE7]
        + [(mid, x, y, "Magma grunt") for mid, x, y, _ in MAGMA_GRUNT_EVENTS]
        + [(mid, x, y, "Magma blockade") for mid, x, y in ROUTE112_MAGMA_BLOCKERS]
        + [(*TABITHA_EVENT, "Tabitha"), (*MAXIE_EVENT, "Maxie"),
           (*FLANNERY_EVENT, "Flannery"), (*METEOR_FALLS_CUTSCENE, "Meteor Falls story"),
           (*METEORITE_MACHINE_EVENT, "Meteorite machine")]
        + [(mid, x, y, f"future7:{why}") for mid, x, y, why in FUTURE_GATES_STAGE7
           if why != "MAGMA_HIDEOUT"]
        + [(63, x, y, "Flannery steam fall") for a, b in GYM_STEAM_PAIRS_STAGE7 for x, y in (a,)]
        + [(63, x, y, "Flannery steam launch") for a, b in GYM_STEAM_PAIRS_STAGE7 for x, y in (b,)]
        + [(mid,x,y,f"trainer8:{name}") for mid,x,y,_,name,_,_,_ in TRAINERS_STAGE8]
        + [(mid,x,y,f"npc8:{handler}") for mid,x,y,_,handler in NPCS_STAGE8]
        + [(mid,9,5,f"center counter8 {mid}") for mid in (49,65,71)]
        + [(mid,4,5,f"mart counter8 {mid}") for mid in (50,66)]
        + [(mid,x,y,f"sign8:{key}") for mid,x,y,key,_ in SIGNS_STAGE8]
        + [(mid,x,y,f"item8:{key}") for mid,x,y,key,_,_ in PICKUPS_STAGE8]
        + [(20,x,y,"Norman gym door") for x,y,tx,ty in NORMAN_GYM_DOORS]
        + [(*NORMAN_EVENT,"Norman"),(*WINONA_EVENT,"Winona"),
           (*SHELLY_EVENT,"Shelly"),(*RIVAL_119_EVENT,"Rival119"),
           (*RIVAL_LILYCOVE_EVENT,"RivalLilycove"),
           (*STEVEN_SCOPE_EVENT,"Steven Devon Scope"),
           (*FORTREE_KECLEON_EVENT,"Kecleon Fortree"),
           (*ROUTE120_KECLEON_EVENT,"Kecleon Route120"),
           (*WEATHER_REWARD_EVENT,"Castform Scientist")]
        + [(mid,x,y,f"Aqua Institute {version}")
           for mid,x,y,version,_ in AQUA_INSTITUTE]
        + [(mid,x,y,f"future8:{key}") for mid,x,y,key in FUTURE_GATES_STAGE8
           if key not in ("AQUA_HIDEOUT","MT_PYRE_PIER")]
        + [(mid,x,y,f"trainer9:{name}") for mid,x,y,_,name,_,_,_ in TRAINERS_STAGE9]
        + [(mid,x,y,f"npc9:{handler}") for mid,x,y,_,handler in NPCS_STAGE9]
        + [(77,9,5,"Stage9 center counter"),(78,4,5,"Stage9 Mart counter")]
        + [(mid,x,y,f"sign9:{key}") for mid,x,y,key,_ in SIGNS_STAGE9]
        + [(mid,x,y,"Tate and Liza") for mid,x,y in TATE_LIZA_EVENTS]
        + [(*MT_PYRE_ARCHIE,"Archie"),(*MT_PYRE_OLD_LADY,"Mt Pyre Elder"),
           (*ARCHIE_ORB_EVENT,"Orb Steal"),(*TABITHA_HIDEOUT_EVENT,"Tabitha Hideout"),
           (*MAXIE_HIDEOUT_EVENT,"Maxie Hideout"),
           (*GROUDON_CUTSCENE_EVENT,"Groudon"),
           (*MATT_HIDEOUT_EVENT,"Matt Hideout"),(*SUBMARINE_EVENT,"Submarine"),
           (*SPACE_MAXIE_EVENT,"Space Maxie"),(*SPACE_STEVEN_EVENT,"Space Steven"),
           (*MAGMA_HIDEOUT_GATE,"Magma entrance"),(*AQUA_HIDEOUT_GATE,"Aqua entrance")]
        + [(mid,x,y,f"Stage9 grunt {ver}") for group in
           (PYRE_AQUA_GRUNTS,MAGMA_HIDEOUT_GRUNTS,AQUA_HIDEOUT_GRUNTS,SPACE_GRUNT_EVENTS)
           for mid,x,y,ver,_ in group]
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
                "slateport_north_gate", "soothe_bell", "soft_sand",
                "sign_stage6", "dynamo_badge?", "rival_110",
                "rival_110_itemfinder", "wally_mauville", "wally_uncle_mauville",
                "wattson", "wattson_tm", "rock_smash_teacher",
                "rydel_bikes", "has_hoenn_bike?", "cycling_gate",
                "wattson_gate", "wattson_switch", "mauville_future_gate",
                "sign_stage7", "heat_badge?", "meteor_falls_ambush",
                "magma_blocker", "cable_car", "magma_grunt",
                "tabitha", "maxie", "meteorite_machine",
                "flannery_tm", "flannery", "gym_steam_vent",
                "glass_workshop", "fossil_house", "stage7_future_gate",
                "sign_stage8", "balance_badge?", "feather_badge?",
                "norman_gym_warp", "norman_tm", "norman",
                "surf_from_wally_family", "good_rod_fisherman",
                "daycare_info", "weather_aqua", "weather_shelly",
                "weather_castform", "rival_119_fly", "rival_119",
                "steven_scope", "kecleon_scope", "winona_tm", "winona",
                "rival_lilycove", "harbor_stage8", "contest_stage8",
                "stage8_future_gate",
                "sign_stage9","mind_badge?","stage9_transfer",
                "stage9_grunt","pyre_aqua_grunt","pyre_archie",
                "pyre_orb_scene","pyre_elder","enter_magma_hideout",
                "magma_hideout_grunt","magma_hideout_tabitha",
                "magma_hideout_maxie","groudon_hideout",
                "slateport_submarine_news","enter_aqua_hideout",
                "aqua_hideout_grunt","aqua_hideout_matt","submarine_escape",
                "tate_liza_tm","tate_liza","space_magma_grunt",
                "space_center_maxie","space_center_steven",
                "steven_house_stage9","super_rod_stage9",
                "mossdeep_space_scientist"}
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


    gaps = [
        "Stage9 is scripted in an isolated Hoenn copy; not tested on Game.exe or Android.",
        "Static donor warp scanner reauthors direct teleports; ambiguous multi-page and scripted doors are excluded.",
        "The source Mossdeep Gym's statue/button puzzle is not faithfully reconstructed or approved.",
        "The original Steven co-op double battle in Space Center remains a guarded sequential-boss fallback.",
        "Aqua/Magma grunt parties are provisional; exact source event versions remain to be mapped.",
        "Surf routes and Mossdeep coastal crossings need native field-move collision and water testing.",
        "Mt Pyre fog/orb cutscenes, Groudon animation and submarine scene are text/flag-only, not native cutscenes.",
        "MIND badge and HM Dive field activation require Game.exe and region save QA.",
        "No donor RXDATA, graphics, music or licensed assets are committed.",
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
        "stage6_source_maps": len(SOURCE_MAPS_STAGE6),
        "stage6_trainer_presets": len(TRAINERS_STAGE6) + 2 + len(RIVAL_NAMES) * len(RIVAL_110_TEAMS),
        "stage6_pickup_events": len(PICKUPS_STAGE6),
        "stage6_cycling_gates": len(CYCLE_TRANSFERS_STAGE6),
        "stage6_gym_switches": len(GYM_SWITCHES_STAGE6),
        "stage6_gym_barriers": len(GYM_GATES_STAGE6),
        "stage6_scripted_only": True,
        "stage7_source_maps": len(SOURCE_MAPS_STAGE7),
        "stage7_trainer_presets": len(TRAINERS_STAGE7) + len(MAGMA_GRUNTS_STAGE7) + 3,
        "stage7_pickup_events": len(PICKUPS_STAGE7),
        "stage7_cave_maps": len(CAVE_ENCOUNTERS_STAGE7),
        "stage7_cable_stops": len(CABLE_POINTS_STAGE7),
        "stage7_steam_vent_pairs": len(GYM_STEAM_PAIRS_STAGE7),
        "stage7_scripted_only": True,
        "stage8_source_maps": len(SOURCE_MAPS_STAGE8),
        "stage8_trainer_presets": len(TRAINERS_STAGE8)+len(AQUA_INSTITUTE)+
                                   3+len(RIVAL_NAMES)*(len(RIVAL_119_TEAMS)+len(RIVAL_LILYCOVE_TEAMS)),
        "stage8_pickup_events": len(PICKUPS_STAGE8),
        "stage8_norman_gym_doors": len(NORMAN_GYM_DOORS),
        "stage8_rival_variants": len(RIVAL_NAMES)*(len(RIVAL_119_TEAMS)+len(RIVAL_LILYCOVE_TEAMS)),
        "stage8_scripted_only": True,
        "stage9_source_maps": len(SOURCE_MAPS_STAGE9),
        "stage9_trainer_presets": len(TRAINERS_STAGE9) +
                                   len(PYRE_AQUA_GRUNTS)+len(MAGMA_HIDEOUT_GRUNTS)+
                                   len(AQUA_HIDEOUT_GRUNTS)+len(SPACE_GRUNT_EVENTS)+6,
        "stage9_surf_borders": len(SURF_BORDERS_STAGE9),
        "stage9_graph_edges": len(STAGE9_MAP_GRAPH_EDGES),
        "stage9_scripted_only": True,
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
