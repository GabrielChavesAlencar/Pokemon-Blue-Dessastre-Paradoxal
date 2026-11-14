"""Read-only structural verification of the separately installed Kanto pilot.

Run after pilot.py creates .blue-work/kanto-pilot, before the native smoke test.
This checks data integrity; it does not prove walkability, battle UI or PC/Android compatibility.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import deque
from pathlib import Path

from audit import KANTO, ROOT, json_file, load
from pilot import (PILOT_META, TRAINERS, CINNABAR_EVENTS, CINNABAR_GYM_DOORS,
                   CINNABAR_GYM_QUIZZES, CINNABAR_GYM_TRAINER_GROUPS,
                   MANSION_DOORS, MANSION_STATUES, VIRIDIAN_GYM_EVENTS,
                   LEAGUE_BADGE_GATES, LEAGUE_BARRIER_GATES,
                   VICTORY_ROAD_BARRIERS, VICTORY_ROAD_BOULDERS,
                   LEAGUE_EVENT_WHITELIST, LEAGUE_NEXT_ROOMS,
                   LEAGUE_TRAINER_SPECS, KANTO_MOONSTONE_CALLBACK)
from server.ruby_marshal import text


def reachable(edges: dict[int, set[int]], start: int) -> set[int]:
    seen = {start}
    pending = deque([start])
    while pending:
        for neighbor in edges[pending.popleft()]:
            if neighbor not in seen:
                seen.add(neighbor)
                pending.append(neighbor)
    return seen


def inspect(game: Path) -> dict:
    game = game.resolve()
    workspace = (ROOT / ".blue-work").resolve()
    if not game.is_relative_to(workspace):
        raise ValueError("Verification only accepts a copy within .blue-work")
    meta_path = game / PILOT_META
    if not meta_path.is_file():
        raise ValueError("Not a prepared Kanto pilot")
    mapping = {int(source): int(dest) for source, dest in json_file(meta_path)["maps"].items()}
    manifest = json_file(KANTO)
    expected = {int(source): name for source, name in manifest["maps"].items()}
    preview_only = set(manifest.get("preview_only", []))
    if preview_only - expected.keys():
        raise ValueError("Preview map IDs do not exist in the Kanto manifest")
    if preview_only & set(TRAINERS):
        raise ValueError("No trainer scripts can be installed on preview-only maps")
    if set(mapping) != set(expected) or len(set(mapping.values())) != len(expected):
        raise ValueError("Pilot map manifest is missing locations or contains duplicate destination IDs")
    ids = set(mapping.values())
    maps = {}
    for source, dest in mapping.items():
        file = game / "Data" / f"Map{dest:03d}.rxdata"
        if not file.is_file():
            raise ValueError(f"Missing {expected[source]} map: {file.name}")
        maps[dest] = load(file)
    # Native field objects are generated from their real source EventIDs.
    # Reject invented coordinates, foreign-preview events and malformed
    # one-shot item and physical HM obstacle callbacks.
    field_path = game / "Data/blue-kanto-field-events.json"
    if not field_path.is_file():
        raise ValueError("Missing Kanto source-grounded field event inventory")
    field_report = json.loads(field_path.read_text("utf-8"))
    if field_report.get("schema") != 1:
        raise ValueError("Unsupported Kanto field inventory schema")
    if field_report.get("preview_maps_untouched") != sorted(preview_only):
        raise ValueError("Kanto field importer touched an unaudited preview")
    known = {"item", "npc_dialogue", "rock_smash", "strength"}
    seen = set()
    for row in field_report["imported"]:
        source, destination, event_id = row["source_map"], row["map"], row["event"]
        if source not in mapping or source in preview_only or mapping[source] != destination:
            raise ValueError("Kanto field event points outside the active Kanto maps")
        if (destination, event_id) in seen:
            raise ValueError("Duplicate source-grounded Kanto field event")
        seen.add((destination, event_id))
        if row["kind"] not in known:
            raise ValueError("Unreviewed source-grounded Kanto event kind")
        event = maps[destination].attrs["@events"].get(event_id)
        if event is None or (event.attrs["@x"], event.attrs["@y"]) != (row["x"], row["y"]):
            raise ValueError("A source-grounded Kanto field event changed coordinates")
        page = event.attrs["@pages"][0].attrs
        commands = [text(op.attrs["@parameters"][0]) for op in page["@list"]
                    if op.attrs["@code"] == 355 and op.attrs["@parameters"]]
        if row["kind"] == "item":
            if (len(event.attrs["@pages"]) != 2 or
                    not event.attrs["@pages"][1].attrs["@condition"].attrs["@self_switch_valid"] or
                    not any("BlueKantoPilot.pickup(" in script for script in commands)):
                raise ValueError("Ground item missing a safe pickup and persistent hide page")
        if row["kind"] == "strength":
            if page["@trigger"] != 1 or page["@through"] or commands != ["pbPushThisBoulder"]:
                raise ValueError("Source boulder cannot be pushed by native Strength")
        if row["kind"] == "rock_smash":
            if page["@trigger"] != 0 or not any("pbSmashThisEvent" in c for c in commands):
                raise ValueError("SmashRock event does not invoke native Rock Smash")
    # Missing PNGs for *optional* field NPCs must be recorded and omitted,
    # not silently imported as invisible blockers or crash the game builder.
    for row in field_report.get("missing_graphics", []):
        source, destination, event_id = row["source_map"], row["map"], row["event"]
        if (source not in mapping or source in preview_only or
                mapping[source] != destination):
            raise ValueError("Missing graphic reported outside active Kanto")
        if (not row.get("graphic") or
                not row.get("reason", "").startswith("Missing actor graphic: ")):
            raise ValueError("Missing graphic report contains an invalid reason")
        if event_id in maps[destination].attrs["@events"]:
            raise ValueError("Missing graphic imported as an invisible active field event")
    # Celadon phase 09 is map-terrain only. Not even source self-switches,
    # NPCs, warps or trainer events may slip into these compiled RPG maps.
    for source in preview_only:
        if maps[mapping[source]].attrs["@events"]:
            raise ValueError(f"Phase 09-11 preview must not import events into {expected[source]}")
    system = load(game / "Data/System.rxdata").attrs
    if system["@start_map_id"] != mapping[7]:
        raise ValueError("Kanto new game must start in the player's house")
    if not (0 <= system["@start_x"] < maps[mapping[7]].attrs["@width"] and
            0 <= system["@start_y"] < maps[mapping[7]].attrs["@height"]):
        raise ValueError("New-game start position is outside the player's house")

    # MAN-01: only audited pairs of original exterior/interior door events.
    # Both directions must be present after remapping to Blue map IDs; an
    # accessible house with no exit is a softlock, not a successful import.
    safe_interior_pairs = (
        (5, 1, 7, 1),          # Player residence; initial spawn
        (5, 2, 8, 1),          # Pallet rival house
        (5, 3, 6, 1),          # Professor Oak's lab
        (10, 2, 14, 4),        # Viridian houses
        (10, 3, 15, 3),
        (18, 8, 21, 4),        # Route 2 gatehouse — main entry
        (18, 9, 21, 5),        # Gatehouse rear door 1
        (18, 11, 21, 5),       # Gatehouse rear door 2
        (18, 2, 22, 4),        # Route 2 hidden house
        (25, 1, 29, 1),        # Pewter Museum front door
        (25, 2, 29, 2),        # Museum secondary entrance
        (25, 3, 30, 1),        # Pewter homes
        (25, 7, 31, 1),
    )

    def event_transfers(source_id: int, event_id: int) -> set[int]:
        source_events = maps[mapping[source_id]].attrs["@events"]
        if event_id not in source_events:
            raise ValueError(f"Missing interior door event {source_id}/{event_id}")
        results = set()
        for page in source_events[event_id].attrs["@pages"]:
            for opcode in page.attrs["@list"]:
                code = opcode.attrs
                args = code["@parameters"]
                if code["@code"] == 201 and len(args) >= 4 and args[0] == 0:
                    results.add(args[1])
        return results

    for eid in (1, 2, 3, 4, 5):
        door = maps[mapping[10]].attrs["@events"][eid]
        if door.attrs["@pages"][0].attrs["@trigger"] != 1:
            raise ValueError(f"Viridian building {eid} must open on touch")
    for eid in (1, 2, 3):
        pallet_event = maps[mapping[5]].attrs["@events"][eid]
        if pallet_event.attrs["@pages"][0].attrs["@trigger"] != 1:
            raise ValueError(f"Pallet residence/lab door {eid} must trigger on touch")
    for source, event_id, actor_id in ((5, 11, 12), (5, 13, 12), (6, 35, 14), (6, 36, 14), (6, 37, 14), (7, 4, 13)):
        event = maps[mapping[source]].attrs["@events"][event_id]
        page = event.attrs["@pages"][0].attrs
        codes = [op.attrs for op in page["@list"]]
        actor = maps[mapping[source]].attrs["@events"][actor_id]
        if (page["@trigger"] != 1 or
                not actor.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"] or
                not any(op["@code"] == 209 and op["@parameters"][0] == actor_id for op in codes) or
                not any(op["@code"] == 210 for op in codes)):
            raise ValueError(f"Pallet scene {source}/{event_id} must walk actor {actor_id} on touch")
    agent = maps[mapping[5]].attrs["@events"][9]
    agent_scripts = [text(op.attrs["@parameters"][0])
                     for page in agent.attrs["@pages"] for op in page.attrs["@list"]
                     if op.attrs["@code"] in (355, 655) and op.attrs["@parameters"]]
    if not any("BlueRegionTravel.agent" in cmd for cmd in agent_scripts):
        raise ValueError("Pallet NPC for regional travel is not installed")
    if mapping[7] not in event_transfers(7, 3) or mapping[7] not in event_transfers(7, 4):
        raise ValueError("Player home upstairs/downstairs warps do not return")
    for outer, entry, inside, exit_id in safe_interior_pairs:
        if mapping[inside] not in event_transfers(outer, entry):
            raise ValueError(f"Interior {inside}: missing entry from {outer}/{entry}")
        if mapping[outer] not in event_transfers(inside, exit_id):
            raise ValueError(f"Interior {inside}: missing return to {outer}/{entry}")
    if 23 in mapping:
        raise ValueError("Diglett Cave was imported before its source audit")

    # A unique Viridian Mart shopkeeper now anchors the Pallet <-> Viridian
    # story loop, without executing foreign source event scripts or forcing a
    # nonexistent quest item into the Decades item catalogue.
    parcel_mart = []
    for event_id, event in maps[mapping[12]].attrs["@events"].items():
        scripts = [
            op.attrs["@parameters"][0]
            for page in event.attrs["@pages"]
            for op in page.attrs["@list"]
            if op.attrs["@code"] in (355, 655) and op.attrs["@parameters"]
        ]
        if any("BlueKantoPilot.viridian_mart" in
               (raw.decode("utf-8") if isinstance(raw, bytes) else str(raw))
               for raw in scripts):
            if event.attrs["@pages"][0].attrs["@trigger"] != 0:
                raise ValueError("Viridian parcel/Mart event must use Action Button")
            parcel_mart.append(event_id)
    if len(parcel_mart) != 1:
        raise ValueError(f"Expected one Viridian parcel shopkeeper: {parcel_mart}")
    mart_events = maps[mapping[12]].attrs["@events"]
    intro = [ev for ev in mart_events.values()
             if text(ev.attrs["@name"]) == "Kanto Oak Parcel Intro"]
    if len(intro) != 1:
        raise ValueError("Viridian Mart must contain exactly one automatic parcel intro")
    intro_page = intro[0].attrs["@pages"][0].attrs
    scripts = [text(cmd.attrs["@parameters"][0]) for cmd in intro_page["@list"]
               if cmd.attrs["@code"] in (355, 655) and cmd.attrs["@parameters"]]
    if intro_page["@trigger"] != 3 or not any(
            cmd.startswith("BlueKantoPilot.walk_to_viridian_clerk(") for cmd in scripts):
        raise ValueError("Viridian Mart must automatically walk the player to the vendor")
    entrance_scripts = [
        text(op.attrs["@parameters"][0])
        for event in maps[mapping[10]].attrs["@events"].values()
        for page in event.attrs["@pages"]
        for op in page.attrs["@list"]
        if op.attrs["@code"] == 355 and op.attrs["@parameters"]
    ]
    if not any("BlueKantoPilot.prepare_viridian_mart_visit(" in script
               for script in entrance_scripts):
        raise ValueError("Viridian Mart door does not rearm pending parcel saves")
    # Real exterior block is on City 10 -> Route 2 (18), NOT Forest Gate.
    gates = [ev for ev in maps[mapping[10]].attrs["@events"].values()
             if text(ev.attrs["@name"]) == "Kanto Viridian Route 2 Parcel Gate"]
    if not gates or any(
            ev.attrs["@y"] != 0 or
            ev.attrs["@pages"][0].attrs["@trigger"] != 1 or
            ev.attrs["@pages"][0].attrs["@through"] or
            len(ev.attrs["@pages"]) != 2 or
            not ev.attrs["@pages"][1].attrs["@through"]
            for ev in gates):
        raise ValueError("Viridian Route 2 must have solid north-border parcel gates")
    for source_id in (19, 20):
        for event in maps[mapping[source_id]].attrs["@events"].values():
            scripts = [text(op.attrs["@parameters"][0])
                       for pg in event.attrs["@pages"]
                       for op in pg.attrs["@list"]
                       if op.attrs["@code"] in (355, 655) and op.attrs["@parameters"]]
            if any("forest_unlocked?" in x for x in scripts):
                raise ValueError("Forest tunnel must not contain the Oak parcel gate")


    # Phase 09 gameplay nucleus: exact Celadon event whitelist.
    # The source also has Rocket, Game Corner, mansions, item pickups,
    # cut trees and the department store. None of those may slip in.
    core_events = {
        114: {3, 20},                     # Celadon -> gym, Center
        115: {1, 2},                     # Center -> Celadon, nurse
        124: {1, 5, 7, 42, 43, 44, 45, 46, 47},  # Erika + 7 trainers + exit
    }
    for origin, allowed in core_events.items():
        actual = set(maps[mapping[origin]].attrs["@events"])
        if actual != allowed:
            raise ValueError(f"Celadon {origin}: unreviewed events imported: {actual ^ allowed}")
    for outside, eid, inside, return_event in ((114, 3, 124, 5),
                                                (114, 20, 115, 1)):
        if mapping[inside] not in event_transfers(outside, eid):
            raise ValueError(f"Celadon {outside}/{eid} missing entry to {inside}")
        if mapping[outside] not in event_transfers(inside, return_event):
            raise ValueError(f"Celadon {inside}/{return_event} missing return to {outside}")
    nurse = maps[mapping[115]].attrs["@events"][2]
    nurse_scripts = [
        text(op.attrs["@parameters"][0])
        for op in nurse.attrs["@pages"][0].attrs["@list"]
        if op.attrs["@code"] in (355, 655) and op.attrs["@parameters"]
    ]
    if nurse_scripts != ["BlueKantoPilot.heal"]:
        raise ValueError("Celadon Center must use exactly the local heal callback")

    # Stage 10: restricted Fuchsia gameplay core. Warden, Safari South,
    # Gold Teeth, encounters and the 15 protected Fuchsia maps stay untouched.
    fuchsia = {
        144: {5, 17, 18, 24},           # City to gym/Center/Mart/Safari gate
        145: {1, 2},                   # Center exit + nurse
        146: {1, 2},                   # Mart exit + licensed generic Mart
        147: {3, 4, 5, 6, 7, 8, 9, 11},  # Six trainers, Koga, gym exit
        153: {1, 2, 5},                # Gate counter/guide (not admission), exit
    }
    for origin, allowed in fuchsia.items():
        found_ids = set(maps[mapping[origin]].attrs["@events"])
        if found_ids != allowed:
            raise ValueError(f"Fuchsia {origin}: unexpected or missing event IDs {found_ids ^ allowed}")
    fuchsia_returns = (
        (144, 5, 147, 9),
        (144, 17, 145, 1),
        (144, 18, 146, 1),
        (144, 24, 153, 2),
    )
    for exterior, entry, interior, leave in fuchsia_returns:
        if mapping[interior] not in event_transfers(exterior, entry):
            raise ValueError(f"Fuchsia {exterior}/{entry} missing doorway to {interior}")
        if mapping[exterior] not in event_transfers(interior, leave):
            raise ValueError(f"Fuchsia {interior}/{leave} missing return to {exterior}")
        exterior_event = maps[mapping[exterior]].attrs["@events"][entry]
        if exterior_event.attrs["@pages"][0].attrs["@trigger"] != 1:
            raise ValueError("Fuchsia city entrances must trigger when walked into")
    for origin, eid, script in ((145, 2, "BlueKantoPilot.heal"),
                                (146, 2, "pbPokemonMart"),
                                (153, 1, "BlueKantoPilot.safari_preview"),
                                (153, 5, "BlueKantoPilot.safari_preview")):
        found_scripts = [
            text(op.attrs["@parameters"][0])
            for op in maps[mapping[origin]].attrs["@events"][eid].attrs["@pages"][0].attrs["@list"]
            if op.attrs["@code"] in (355, 655) and op.attrs["@parameters"]
        ]
        if len(found_scripts) != 1 or script not in found_scripts[0]:
            raise ValueError(f"Fuchsia {origin}/{eid}: unsafe shop/nurse/gate callback")
    for event in maps[mapping[153]].attrs["@events"].values():
        for page in event.attrs["@pages"]:
            for op in page.attrs["@list"]:
                args = op.attrs["@parameters"]
                if op.attrs["@code"] == 201 and len(args) > 1 and args[1] == mapping[155]:
                    raise ValueError("Safari admission must not bypass the unimplemented session and catch rules")


    # Saffron 10th functional nucleus: exact city, Center, Mart, Gym,
    # Dojo and elevator scripts; 11 floor maps have source-verified stairs.
    saffron = {
        168: {6, 10, 12, 13, 14},
        169: {1, 2}, 170: {1, 2},
        171: {2, 3, 5, 6, 7, 8, 9, 10, 11, 13, *range(17, 46)},
        172: {1, 2, 4, 6, 7, 9, 10, 12},
        189: {1, 2},
    }
    for original, whitelist in saffron.items():
        actual = set(maps[mapping[original]].attrs["@events"])
        if actual != whitelist:
            raise ValueError(f"Saffron {original}: leaked/missing events {actual ^ whitelist}")
    saffron_pairs = (
        (168, 6, 171, 10), (168, 10, 178, 1),
        (168, 12, 170, 1), (168, 13, 169, 1),
        (168, 14, 172, 4),
    )
    for city, entry, interior, leave in saffron_pairs:
        if mapping[interior] not in event_transfers(city, entry):
            raise ValueError(f"Saffron door {city}/{entry} missing {interior}")
        if mapping[city] not in event_transfers(interior, leave):
            raise ValueError(f"Saffron door {interior}/{leave} has no return")
        if maps[mapping[city]].attrs["@events"][entry].attrs["@pages"][0].attrs["@trigger"] != 1:
            raise ValueError(f"Saffron entrance {city}/{entry} is not player-touch")
    silph_stairs = (
        (178, 4, 179, 2), (179, 1, 180, 3),
        (180, 2, 181, 3), (181, 4, 182, 3),
        (182, 4, 183, 3), (183, 4, 184, 3),
        (184, 4, 185, 4), (185, 3, 186, 3),
        (186, 4, 187, 4), (187, 3, 188, 3),
    )
    for lower, ascend, upper, descend in silph_stairs:
        if mapping[upper] not in event_transfers(lower, ascend):
            raise ValueError(f"Silph stairs {lower}/{ascend} missing ascending transfer")
        if mapping[lower] not in event_transfers(upper, descend):
            raise ValueError(f"Silph stairs {upper}/{descend} missing descending transfer")
    gym = maps[mapping[171]].attrs["@events"]
    gym_teleports = [event for event in gym.values()
                     if text(event.attrs["@name"]).startswith("Warp Tile ")]
    if len(gym_teleports) != 30:
        raise ValueError(f"Sabrina warp network is incomplete: {len(gym_teleports)}")
    for ev in gym_teleports:
        if ev.attrs["@pages"][0].attrs["@trigger"] != 1:
            raise ValueError("Sabrina warp must activate on Player Touch")
        for page in ev.attrs["@pages"]:
            for op in page.attrs["@list"]:
                if op.attrs["@code"] == 201 and op.attrs["@parameters"][1] != mapping[171]:
                    raise ValueError("Sabrina warp escaped the gym")
    for original, eid, script in (
            (169, 2, "BlueKantoPilot.heal"), (170, 2, "pbPokemonMart"),
            (182, 9, "BlueKantoPilot.silph_card_key"),
            (184, 43, "BlueKantoPilot.silph_rival"),
            (188, 18, "BlueKantoPilot.silph_president"),
            (189, 1, "BlueKantoPilot.silph_elevator"),
            (189, 2, "BlueKantoPilot.silph_elevator")):
        ev = maps[mapping[original]].attrs["@events"].get(eid)
        commands = [text(op.attrs["@parameters"][0])
                    for p in ev.attrs["@pages"] for op in p.attrs["@list"]
                    if op.attrs["@code"] in (355, 655) and op.attrs["@parameters"]]
        if not any(script in line for line in commands):
            raise ValueError(f"Saffron {original}/{eid}: required local callback missing")
    if any(event_transfers(189, eid) for eid in (1, 2)):
        raise ValueError("Silph elevator retained foreign Map207-217 destinations")
    floors_file = game / "Data/blue-kanto-silph-floors.txt"
    lines = floors_file.read_text(encoding="ascii").splitlines()
    if len(lines) != 11:
        raise ValueError("Silph elevator must serve 11 verified local floors")
    for floor, line in enumerate(lines, 1):
        parts = [int(x) for x in line.split("|")]
        source = 177 + floor
        if len(parts) != 5 or parts[0] != floor or parts[1] != mapping[source]:
            raise ValueError(f"Silph elevator floor {floor}: invalid local mapping")
        x, y = parts[2:4]
        size = maps[mapping[source]].attrs
        if not (0 <= x < size["@width"] and 0 <= y < size["@height"]):
            raise ValueError(f"Silph elevator floor {floor}: landing is out of bounds")
    for original in range(179, 189):
        for eid, event in maps[mapping[original]].attrs["@events"].items():
            if text(event.attrs["@name"]) != "Locked Door":
                continue
            if len(event.attrs["@pages"]) != 2:
                raise ValueError(f"Silph {original}/{eid} missing Card Key open state")
            cond = event.attrs["@pages"][1].attrs["@condition"].attrs
            if cond["@self_switch_valid"] is not True or cond["@self_switch_ch"] != b"A":
                raise ValueError(f"Silph {original}/{eid} Card Key state is unsafe")
    if len([e for e in maps[mapping[171]].attrs["@events"].values()
            if e.attrs["@pages"][0].attrs["@trigger"] == 2]) != 7:
        raise ValueError("Sabrina gym must have seven sight trainers")

    # Phase 12: strictly local Cinnabar core. The original foreign switches
    # and quizzes must NOT be copied into Decades.
    for origin, expected_ids in CINNABAR_EVENTS.items():
        actual = set(maps[mapping[origin]].attrs["@events"])
        if actual != set(expected_ids):
            raise ValueError(f"Cinnabar {origin}: leaked/missing source events {actual ^ set(expected_ids)}")
    cinnabar_pairs = (
        (199, 1, 201, 1), (199, 2, 200, 1),
        (199, 3, 205, 1), (199, 5, 203, 1),
    )
    for city, entry, interior, leave in cinnabar_pairs:
        if mapping[interior] not in event_transfers(city, entry):
            raise ValueError(f"Cinnabar city {city}/{entry} missing entrance to {interior}")
        if mapping[city] not in event_transfers(interior, leave):
            raise ValueError(f"Cinnabar interior {interior}/{leave} cannot return")
        if maps[mapping[city]].attrs["@events"][entry].attrs["@pages"][0].attrs["@trigger"] != 1:
            raise ValueError(f"Cinnabar city entrance {city}/{entry} must be Player Touch")
    if mapping[199] not in event_transfers(202, 3):
        raise ValueError("Cinnabar gym is missing the exit back to the city")
    if mapping[199] not in event_transfers(205, 2):
        raise ValueError("Cinnabar Mansion lacks its second emergency exit")

    def first_scripts(original, event_id):
        event = maps[mapping[original]].attrs["@events"][event_id]
        return [text(row.attrs["@parameters"][0])
                for row in event.attrs["@pages"][0].attrs["@list"]
                if row.attrs["@code"] in (355, 655) and row.attrs["@parameters"]]

    required = (
        (199, 4, "BlueKantoPilot.cinnabar_gym_gate("),
        (200, 2, "BlueKantoPilot.heal"),
        (201, 2, "pbPokemonMart("),
        (208, 8, "BlueKantoPilot.mansion_secret_key"),
    )
    for source, eid, callback in required:
        if len(first_scripts(source, eid)) != 1 or callback not in first_scripts(source, eid)[0]:
            raise ValueError(f"Cinnabar {source}/{eid}: unsafe or absent local callback")
    for eid, group in CINNABAR_GYM_QUIZZES.items():
        if first_scripts(202, eid) != [f"BlueKantoPilot.cinnabar_quiz({group})"]:
            raise ValueError(f"Cinnabar gym quiz {eid} has not been adapted")
    for group, ids_group in CINNABAR_GYM_DOORS.items():
        for eid in ids_group:
            event = maps[mapping[202]].attrs["@events"][eid]
            if first_scripts(202, eid) != [f"BlueKantoPilot.cinnabar_door({group})"]:
                raise ValueError(f"Cinnabar gym door {eid} is not locally gated")
            if len(event.attrs["@pages"]) != 2:
                raise ValueError(f"Cinnabar door {eid} has no open state")
            cond = event.attrs["@pages"][1].attrs["@condition"].attrs
            if not cond["@self_switch_valid"] or cond["@self_switch_ch"] != b"A":
                raise ValueError(f"Cinnabar door {eid} uses a foreign switch")
    for floor, door_ids in MANSION_DOORS.items():
        for eid in door_ids:
            event = maps[mapping[floor]].attrs["@events"][eid]
            if not first_scripts(floor, eid) or "BlueKantoPilot.mansion_door" not in first_scripts(floor, eid)[0]:
                raise ValueError(f"Mansion {floor}/{eid}: original switch leaked")
            if len(event.attrs["@pages"]) != 2:
                raise ValueError(f"Mansion {floor}/{eid}: missing open-state page")
        for eid in MANSION_STATUES[floor]:
            if not first_scripts(floor, eid) or "BlueKantoPilot.mansion_switch" not in first_scripts(floor, eid)[0]:
                raise ValueError(f"Mansion {floor}/{eid}: statue not adapted")
    if len(TRAINERS[202]) != 8 or any(eid not in maps[mapping[202]].attrs["@events"] for eid in TRAINERS[202]):
        raise ValueError("Blaine and seven Cinnabar trainers must be present")

    # Stage 13: source Map013 must be safely re-implemented, while keeping
    # the original Map010 entrance and the exact one-way return.
    gym_events = maps[mapping[13]].attrs["@events"]
    if set(gym_events) != VIRIDIAN_GYM_EVENTS:
        raise ValueError(f"Viridian Gym whitelist changed: {set(gym_events) ^ VIRIDIAN_GYM_EVENTS}")
    if len(TRAINERS[13]) != 9:
        raise ValueError("Viridian Gym must have Giovanni and exactly eight source trainers")
    if mapping[10] not in event_transfers(13, 11):
        raise ValueError("Viridian gym has no return to its city")
    exit_event = gym_events[11].attrs["@pages"][0].attrs
    if exit_event["@trigger"] != 1:
        raise ValueError("Viridian gym exit must activate on Player Touch")
    entry = maps[mapping[10]].attrs["@events"].get(1)
    if entry is None or len(entry.attrs["@pages"]) != 1:
        raise ValueError("Viridian City gym door still has unsafe source pages")
    door = entry.attrs["@pages"][0].attrs
    if door["@trigger"] != 1 or not door["@through"] or not door["@graphic"].attrs["@character_name"]:
        raise ValueError("Viridian Gym source door must be visible and Player Touch")
    if event_transfers(10, 1):
        raise ValueError("Viridian gym door bypassed badge guard by direct RPG warp")
    expected_gate = f"BlueKantoPilot.viridian_gym_gate({mapping[13]}, 17, 22)"
    if first_scripts(10, 1) != [expected_gate]:
        raise ValueError("Viridian entrance lacks an exact safe badge-gated callback")
    if first_scripts(13, 16) != ["BlueKantoPilot.viridian_gym_guide"]:
        raise ValueError("Viridian Gym guide retained unreviewed foreign scripts")
    for eid in TRAINERS[13]:
        if eid not in gym_events:
            raise ValueError(f"Viridian trainer {eid} absent")
    if not first_scripts(13, 4) or "BLUE_KANTO_LEADER_GIOVANNI" not in first_scripts(13, 4)[0]:
        raise ValueError("Viridian Giovanni not bound to independent gym leader type")
    battle_scripts = [line for line in first_scripts(13, 8) if "BlueKantoPilot.battle(" in line]
    if len(battle_scripts) != 1 or '"Jason"' not in battle_scripts[0] or '"Cole"' in battle_scripts[0]:
        raise ValueError("FRLG source typo Tamer Jason -> Cole has leaked into Blue")

    # Stage 14: the League must use only audited local events and the
    # eight badges of Kanto. No raw source story switches, credits or
    # completion flags may be executed in the Decades installation.
    for original, allowed in LEAGUE_EVENT_WHITELIST.items():
        actual = set(maps[mapping[original]].attrs["@events"])
        if actual != allowed:
            raise ValueError(f"League {original}: foreign events or missing local events {actual ^ allowed}")
    if maps[mapping[210]].attrs["@events"]:
        raise ValueError("Empty Victory Road Map210 unexpectedly contains source events")
    for original, entries in LEAGUE_BADGE_GATES.items():
        for guard_id, (required, barrier_id) in entries.items():
            expected_callback = f"BlueKantoPilot.league_badge_check({required}, {guard_id}, {barrier_id})"
            for eid in (guard_id, barrier_id):
                event = maps[mapping[original]].attrs["@events"][eid]
                if first_scripts(original, eid) != [expected_callback]:
                    raise ValueError(f"League badge gate {original}/{eid} is not locally guarded")
                pages = event.attrs["@pages"]
                cond = pages[1].attrs["@condition"].attrs if len(pages) == 2 else {}
                if cond.get("@self_switch_valid") is not True or cond.get("@self_switch_ch") != b"A":
                    raise ValueError(f"League gate {original}/{eid} has no safe local open page")
    for original, eid, callback in (
            (17,3,"BlueKantoPilot.league_route_gate"),
            (209,2,"BlueKantoPilot.league_route_gate"),
            (209,4,"BlueKantoPilot.league_route_gate"),
            (214,1,"BlueKantoPilot.league_route_gate"),
            (215,3,"BlueKantoPilot.league_begin"),
            (215,4,"BlueKantoPilot.heal"),
            (215,14,"BlueKantoPilot.league_guide"),
            (220,1,"BlueKantoPilot.league_champion_npc"),
            (221,1,"BlueKantoPilot.league_finalize"),
            (221,2,"BlueKantoPilot.league_oak")):
        if len(first_scripts(original,eid)) != 1 or not first_scripts(original,eid)[0].startswith(callback):
            raise ValueError(f"Missing safe League script in {original}/{eid}")
    for original, door in LEAGUE_NEXT_ROOMS.items():
        eid, target, x, y = door
        script = first_scripts(original,eid)
        if len(script) != 1 or not script[0].startswith("BlueKantoPilot.league_advance("):
            raise ValueError(f"League door {original}/{eid} is not victory-gated")
        if event_transfers(original,eid):
            raise ValueError(f"League door {original}/{eid} bypasses the winner gate")
    for original, (eid, kind, name, _, _) in LEAGUE_TRAINER_SPECS.items():
        script = first_scripts(original,eid)
        if len(script) != 1 or not script[0].startswith("BlueKantoPilot.league_battle(") or (
            f':BLUE_KANTO_{kind}, "{name}"' not in script[0]):
            raise ValueError(f"Elite/Champion {original}/{eid} does not use the audited roster")
    if event_transfers(215,3) or event_transfers(221,1):
        raise ValueError("League completion has an unguarded source warp")
    for floor, barrier_ids in VICTORY_ROAD_BARRIERS.items():
        for eid in (*barrier_ids, *VICTORY_ROAD_BOULDERS[floor]):
            if not first_scripts(floor,eid) or not first_scripts(floor,eid)[0].startswith("BlueKantoPilot.victory_strength("):
                raise ValueError(f"Victory Road {floor}/{eid} retains unsafe strength scripts")
    if (first_scripts(213,15)[:1] != ["pbTrainerIntro(:BLUE_KANTO_COOLCOUPLE)"] or
        "BlueKantoPilot.victory_couple" not in first_scripts(213,15) or
        "BlueKantoPilot.victory_couple" not in first_scripts(213,16)):
        raise ValueError("Victory Road's Ray/Tyra double battle was split or discarded")

    # MAN-02: the source-proven 122 line-of-sight trainers require Event Touch,
    # with a non-triggering second page selected by self-switch A after victory.
    sight_count = 0
    for original, profiles in TRAINERS.items():
        for event_id, spec in profiles.items():
            event = maps[mapping[original]].attrs["@events"][event_id]
            pages = event.attrs["@pages"]
            if len(pages) != 2:
                raise ValueError(f"Trainer {original}/{event_id} missing win-state page")
            sight = bool(re.search(r"(?i)(?:trainer|sight)\((\d+)\)",
                                   text(event.attrs["@name"])))
            expected_trigger = 2 if sight else 0
            if pages[0].attrs["@trigger"] != expected_trigger:
                raise ValueError(f"Trainer {original}/{event_id} has wrong sight trigger")
            post = pages[1].attrs
            condition = post["@condition"].attrs
            if (post["@trigger"] != 0 or
                condition["@self_switch_valid"] is not True or
                condition["@self_switch_ch"] != b"A"):
                raise ValueError(f"Trainer {original}/{event_id} has unsafe repeat behavior")
            commands = [
                opcode.attrs["@parameters"][0]
                for opcode in pages[0].attrs["@list"]
                if opcode.attrs["@code"] in (355, 655) and opcode.attrs["@parameters"]
            ]
            script = "\\n".join(value.decode("utf-8") if isinstance(value, bytes)
                                  else str(value) for value in commands)
            key = f"KANTO_{original:03d}_{event_id:03d}"
            if (not ("BlueKantoPilot.battle(" in script or
                     "BlueKantoPilot.cinnabar_trainer(" in script or
                     "BlueKantoPilot.victory_couple" in script) or
                f'BlueKantoPilot.sync_trainer_event("{key}"' not in script):
                raise ValueError(f"Trainer {original}/{event_id} does not persist victory")
            if sight:
                sight_count += 1
                if "pbNoticePlayer(get_self)" not in script:
                    raise ValueError(f"Trainer {original}/{event_id} will not alert the player")
    if sight_count != 122:
        raise ValueError(f"Source-proven trainer sight count changed: {sight_count}")

    # Route connections are bidirectional, but transfer events are directed.
    # Check reachability both from and back to Pallet to avoid accepting
    # one-way maps as if their exit events were reciprocal.
    edges = {map_id: set() for map_id in ids}
    connections = game / "PBS/map_connections_kanto.txt"
    if not connections.is_file():
        raise ValueError("The regional map connections PBS is missing")
    count_connections = 0
    for raw in connections.read_text(encoding="utf-8-sig").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        fields = [item.strip() for item in line.split(",")]
        if len(fields) != 6:
            raise ValueError(f"Invalid map connection: {line}")
        left, right = int(fields[0]), int(fields[3])
        if left not in ids or right not in ids:
            raise ValueError(f"Map connection refers outside the prepared pilot: {line}")
        edges[left].add(right)
        edges[right].add(left)
        count_connections += 1

    anchors = {
        (5, 11): "BlueKantoPilot.oak_invitation",
        (5, 13): "BlueKantoPilot.oak_invitation",
        (6, 18): "BlueKantoPilot.choose_starter_ball(:BULBASAUR)",
        (6, 19): "BlueKantoPilot.choose_starter_ball(:SQUIRTLE)",
        (6, 20): "BlueKantoPilot.choose_starter_ball(:CHARMANDER)",
        (6, 28): "BlueKantoPilot.finish_lab_escort",
        (6, 35): "BlueKantoPilot.rival",
        (6, 36): "BlueKantoPilot.rival",
        (6, 37): "BlueKantoPilot.rival",
        (7, 4): "BlueKantoPilot.meet_mom",
        (7, 14): "BlueKantoPilot.choose_profile",
        (6, 15): "BlueKantoPilot.choose_starter",
        (10, 1): "BlueKantoPilot.viridian_gym_gate",
        (13, 16): "BlueKantoPilot.viridian_gym_guide",
        (6, 14): "BlueKantoPilot.rival_hint",
        (11, 2): "BlueKantoPilot.heal",
        (26, 2): "BlueKantoPilot.heal",
        (34, 2): "BlueKantoPilot.heal",
        (40, 2): "BlueKantoPilot.heal",
        (65, 2): "BlueKantoPilot.heal",
        (64, 7): "BlueKantoPilot.ticketmaster",
        (76, 2): "BlueKantoPilot.captain",
        (36, 18): KANTO_MOONSTONE_CALLBACK,
        (28, 6): 'BlueKantoPilot.battle(:BLUE_KANTO_CAMPER, "Liam", "KANTO_028_006")',
        (28, 7): 'BlueKantoPilot.battle(:BLUE_KANTO_LEADER, "Brock", "KANTO_028_007")',
        (24, 16): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Rick", "KANTO_024_016")',
        (24, 17): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Doug", "KANTO_024_017")',
        (24, 18): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Anthony", "KANTO_024_018")',
        (24, 19): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Charlie", "KANTO_024_019")',
        (24, 20): 'BlueKantoPilot.battle(:BLUE_KANTO_BUGCATCHER, "Sammy", "KANTO_024_020")',
    }
    for source_id, entries in TRAINERS.items():
        for event_id, spec in entries.items():
            kind, name = spec[:2]
            key = f"KANTO_{source_id:03d}_{event_id:03d}"
            anchors[(source_id, event_id)] = (
                f'BlueKantoPilot.battle(:BLUE_KANTO_{kind}, "{name}", "{key}"'
            )
    for event_id, group in CINNABAR_GYM_TRAINER_GROUPS.items():
        kind, name, *_ = TRAINERS[202][event_id]
        key = f"KANTO_202_{event_id:03d}"
        anchors[(202, event_id)] = (
            f'BlueKantoPilot.cinnabar_trainer(:BLUE_KANTO_{kind}, "{name}", "{key}", {group})'
        )
    for eid in (15,16):
        anchors[(213,eid)] = "BlueKantoPilot.victory_couple"
    for original, (eid,kind,name,stage,_) in LEAGUE_TRAINER_SPECS.items():
        anchors[(original,eid)] = "BlueKantoPilot.league_battle"
    for original, (eid,_,x,y) in LEAGUE_NEXT_ROOMS.items():
        anchors[(original,eid)] = "BlueKantoPilot.league_advance"
    for entry in (9, 29, 30):
        anchors[(64, entry)] = "BlueKantoPilot.harbor_gate"
    for entry in (4, 10, *range(22, 35)):
        anchors[(67, entry)] = "BlueKantoPilot.surge_can"
    for entry in (8, *range(11, 20)):
        anchors[(67, entry)] = "BlueKantoPilot.surge_gate"
    # Only exact whitelisted script strings are admitted as transfer edges
    # in the directed graph. They remain guarded at runtime.
    league_scripted_transfers = {
        (17,3):(209,14,153,1),
        (209,2):(211,18,25,8),
        (209,4):(212,55,17,8),
        (214,1):(215,11,16,8),
        (215,3):(216,6,12,8),
        (216,1):(217,6,12,8),
        (217,3):(218,6,12,8),
        (218,3):(219,23,10,8),
        (219,3):(220,7,19,8),
        (220,2):(221,5,12,8),
        (221,1):(5,18,8,8),
    }
    def league_expected_callback(source,event_id,target,x,y,required):
        if source == 17:
            return f"BlueKantoPilot.league_route_gate({mapping[target]}, {x}, {y}, 1)"
        if source in (209,214):
            return f"BlueKantoPilot.league_route_gate({mapping[target]}, {x}, {y}, 8)"
        if source == 215:
            return f"BlueKantoPilot.league_begin({mapping[target]}, {x}, {y})"
        if source == 221:
            return f"BlueKantoPilot.league_finalize({mapping[target]})"
        name = {216:"LORELEI",217:"BRUNO",218:"AGATHA",219:"LANCE",220:"CHAMPION"}[source]
        return f'BlueKantoPilot.league_advance("{name}", {mapping[target]}, {x}, {y})'

    found = set()
    warps = 0
    for source, dest in mapping.items():
        data = maps[dest].attrs
        for event_id, event in data["@events"].items():
            for page in event.attrs["@pages"]:
                for op in page.attrs["@list"]:
                    code = op.attrs["@code"]
                    params = op.attrs["@parameters"]
                    if code == 201 and params[0] == 0:
                        target, x, y = params[1:4]
                        if target not in ids:
                            raise ValueError(f"Unmapped transfer: {source}/{event_id} -> {target}")
                        target_map = maps[target].attrs
                        if not (0 <= x < target_map["@width"] and 0 <= y < target_map["@height"]):
                            raise ValueError(f"Out-of-bounds transfer: {source}/{event_id} -> {target} ({x},{y})")
                        edges[dest].add(target)
                        warps += 1
                    if code in (355, 655) and params:
                        script = params[0].decode("utf-8") if isinstance(params[0], bytes) else str(params[0])
                        expected_script = anchors.get((source, event_id))
                        if expected_script and expected_script in script:
                            found.add((source, event_id))
                        # The harbor entrance is a ticket-gated scripted
                        # transfer, not an RPG::EventCommand 201. Admit it into
                        # the topology only if the whitelisted destination
                        # agrees with the pinned FRLG harbor exit.
                        # Phase 12: the only scripted Cinnabar map transfer
                        # is gated by the unique Mansion Secret Key. Check the
                        # exact local callback/landing before adding this edge.
                        if (source,event_id) in league_scripted_transfers:
                            target, x, y, required = league_scripted_transfers[(source,event_id)]
                            expected_local = league_expected_callback(source,event_id,target,x,y,required)
                            if script == expected_local:
                                edges[dest].add(mapping[target])
                        if source == 10 and event_id == 1:
                            if script == f"BlueKantoPilot.viridian_gym_gate({mapping[13]}, 17, 22)":
                                edges[dest].add(mapping[13])
                        if source == 199 and event_id == 4:
                            guarded = f"BlueKantoPilot.cinnabar_gym_gate({mapping[202]}, 25, 23)"
                            if script == guarded:
                                edges[dest].add(mapping[202])
                        if source == 64 and event_id in (9, 29, 30):
                            allowed = f"BlueKantoPilot.harbor_gate({mapping[72]}, 9, 7)"
                            if script == allowed:
                                edges[dest].add(mapping[72])

    # The Map189 source elevator used foreign Map207-217 targets. Native
    # local controls are validated above and provide return edges to every floor.
    if mapping[189] in edges:
        for source in range(178, 189):
            edges[mapping[189]].add(mapping[source])
    if found != set(anchors):
        missing = sorted(set(anchors) - found)
        raise ValueError(f"Required Kanto event scripts are missing: {missing}")

    seen = reachable(edges, mapping[5])
    active_ids = {dest for source, dest in mapping.items() if source not in preview_only}
    if not active_ids.issubset(seen):
        missing = [expected[source] for source, dest in mapping.items()
                   if source not in preview_only and dest not in seen]
        raise ValueError(f"Maps unreachable FROM Pallet by real transfer direction: {missing}")
    backwards = {map_id: set() for map_id in ids}
    for origin, destinations in edges.items():
        for destination in destinations:
            backwards[destination].add(origin)
    returnable = reachable(backwards, mapping[5])
    if not active_ids.issubset(returnable):
        trapped = [expected[source] for source, dest in mapping.items()
                   if source not in preview_only and dest not in returnable]
        raise ValueError(f"Maps without a directed route BACK to Pallet: {trapped}")
    route = [5, 9, 10, 18, 19, 24, 20, 25, 28, 32, 33, 34,
             36, 37, 38, 39, 40, 41, 42,
             56, 59, 60, 63, 61, 64, 65, 66, 67,
             72, 74, 75, 76, 77, 78]
    for source in route:
        if mapping[source] not in seen:
            raise ValueError(f"Story route is not connected to Pallet: {expected[source]}")
    # The test-only teleport manifest must refer exclusively to prepared maps
    # and coordinates proven in the pinned FRLG source's incoming warps.
    stops_file = game / "Data/blue-kanto-experimental-stops.txt"
    if not stops_file.is_file():
        raise ValueError("Experimental Kanto destinations were not generated")
    required_stops = {"PALLET", "PLAYER_HOME", "VIRIDIAN", "PEWTER", "ROUTE4", "MOON_CENTER",
                      "MOON_1F", "MOON_B1F", "MOON_B2F", "CERULEAN", "MISTY",
                      "ROUTE5", "ROUTE6", "VERMILION", "SURGE", "HARBOR",
                      "SSANNE", "SSCAPTAIN", "SSDECK",
                      "ROUTE7", "CELADON", "ERIKA", "CEL_CENTER", "CEL_STORE",
                      "FUCHSIA", "KOGA", "FUCH_CENTER", "FUCH_MART", "FUCH_WARDEN",
                      "SAF_GATE", "SAF_SOUTH", "SAF_NORTH", "SAF_WEST", "ROUTE15",
                      "ROUTE8", "SAFF_WEST", "SAFFRON", "SABRINA", "SAFF_DOJO",
                      "SAFF_CENTER", "SILPH_1F", "SILPH_5F", "SILPH_11F", "SILPH_LIFT",
                       "ROUTE19", "ROUTE20", "SEAFOAM", "CINNABAR", "CIN_CENTER",
                       "CIN_GYM", "CIN_LAB", "MANSION", "MANSION_B1F", "VIR_GYM",
                       "ROUTE22", "ROUTE23", "ROAD_1F", "ROAD_2F", "INDIGO",
                       "LEAGUE", "LORELEI", "LANCE", "CHAMPION", "HALL"}
    seen_stops = set()
    for raw in stops_file.read_text(encoding="utf-8").splitlines():
        parts = raw.split("|")
        if len(parts) != 6:
            raise ValueError(f"Malformed experimental destination: {raw}")
        code, label, map_no, x, y, direction = parts
        if code in seen_stops or code not in required_stops or not label:
            raise ValueError(f"Invalid test destination: {code}")
        seen_stops.add(code)
        dest_map, tx, ty, direction = map(int, (map_no, x, y, direction))
        if dest_map not in maps or not 0 <= tx < maps[dest_map].attrs["@width"] or not 0 <= ty < maps[dest_map].attrs["@height"] or direction not in (2,4,6,8):
            raise ValueError(f"Experimental destination outside prepared map: {code}")
    if seen_stops != required_stops:
        raise ValueError(f"Missing experimental stops: {required_stops - seen_stops}")

    return {
        "result": "structural_check_passed",
        "maps": len(maps),
        "preview_geometry_only": len(preview_only),
        "phase12_cinnabar_functional_maps": len(CINNABAR_EVENTS),
        "phase12_preview_only": len(preview_only & {190,191,193,194,195,196,197,198}),
        "phase12_mansion_floors": len(MANSION_DOORS),
        "phase13_viridian_gym_trainers": len(TRAINERS[13]),
        "phase14_league_rooms": len(LEAGUE_TRAINER_SPECS),
        "phase14_victory_road_trainer_events": sum(len(TRAINERS[n]) for n in (211,212,213)),
        "phase14_protected_badge_checkpoints": 8,
        "phase13_viridian_gym_gate_required_badges": 7,
        "phase09_geometry_only": len(preview_only & {111,114,115,117,118,119,120,121,122,123,124}),
        "phase09_functional_maps": len(set(core_events) - preview_only),
        "celadon_verified_return_pairs": 2,
        "erika_roster_events": len(TRAINERS.get(124, {})),
        "phase10_geometry_only": len(preview_only & {141,142,143,144,145,146,147,152,153,155,156,157,158,159,160,161,162,163,164,165}),
        "fuchsia_functional_maps": len(set(fuchsia) - preview_only),
        "fuchsia_bidirectional_core_doors": len(fuchsia_returns),
        "fuchsia_gym_battle_events": len(TRAINERS[147]),
        "safari_admission_blocked": True,
        "phase11_geometry_only": len(preview_only & {57,62,107,108,109,110,112,113,168,169,170,171,172,173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189}),
        "preview_event_count": sum(len(maps[mapping[source]].attrs["@events"])
                                   for source in preview_only),
        "active_maps": len(active_ids),
        "audited_interiors_bidirectional": len(safe_interior_pairs),
        "pallet_residence_doors": 3,
        "kanto_start_inside_player_home": True,
        "viridian_oak_parcel_shopkeeper": parcel_mart[0],
        "trainers_with_line_of_sight": sight_count,
        "connections": count_connections,
        "mapped_transfers": warps,
        "returnable_maps": len(returnable),
        "required_events": len(found),
        "experimental_stops": len(seen_stops),
        "route": [expected[source] for source in route],
        "limitations": "Celadon and Fuchsia City/Center/Gym plus Fuchsia Mart and Safari Gate have limited selective gameplay. Remaining 36 preview maps include Safari capture areas, Warden, Fuchsia approaches and Saffron gatehouses; Safari admission/capture, Gold Teeth, Surf/Strength and interactive Windows/JoiPlay QA remain pending.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", type=Path, nargs="?", default=ROOT / ".blue-work/kanto-pilot")
    args = parser.parse_args()
    print(json.dumps(inspect(args.pilot), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
