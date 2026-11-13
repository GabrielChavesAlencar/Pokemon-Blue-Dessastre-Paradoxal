"""Prepare and launch the Kanto pilot in a separate copy of the installed Blue game."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from audit import KANTO, ROOT, json_file, load
from export_kanto import LOCATION_NAMES
from pbs import read_blocks
from server.ruby_marshal import RubyObject, text
from stage import serialize, stage

SAVE_ORG = "Dessastre Paradoxal Kanto Testes"
SAVE_APP = "Kanto Piloto"
OUTPUT = ROOT / ".blue-work/kanto-pilot"
SOURCE = ROOT / ".blue-work/frlg-source/Essentials FRLG"
PILOT_META = "Kanto pilot.json"
# Changes to any of these inputs require a new isolated pilot build.
PILOT_INPUTS = (
    "scripts/regions/pilot.py",
    "scripts/regions/stage.py",
    "scripts/regions/pbs.py",
    "scripts/regions/export_kanto.py",
    "scripts/regions/KantoPilot.rb",
    "scripts/battle_polish/RegionStart.rb",
    "scripts/battle_polish/Story.rb",
    "scripts/battle_polish/RegionalWild.rb",
    "data/regions/kanto-source.json",
    "data/kanto-music-rules.json",
    "data/kanto-music.json",
    "data/shared-music.json",
    "scripts/music/compile_kanto_music.py",
    "scripts/music/BlueMusic.rb",
)


def build_signature():
    digest = hashlib.sha256()
    for relative in PILOT_INPUTS:
        path = ROOT / relative
        digest.update(relative.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def pilot_is_current(output):
    marker = output / PILOT_META
    if not marker.is_file():
        return False
    try:
        return json.loads(marker.read_text(encoding="utf-8"))["build_signature"] == build_signature()
    except (OSError, ValueError, KeyError, TypeError):
        return False


def revised_path(output):
    suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    return output.parent / f"{output.name}-revisao-{suffix}"


EVENT_CLASSES = {
    "RPG::Event", "RPG::Event::Page", "RPG::Event::Page::Condition", "RPG::Event::Page::Graphic",
    "RPG::MoveRoute", "RPG::MoveCommand", "RPG::EventCommand",
}
SYSTEM_CLASSES = {"RPG::System", "RPG::System::Words", "RPG::System::TestBattler"}
TYPES = {
    "RIVAL": "RIVAL1", "BUGCATCHER": "BUGCATCHER",
    "CAMPER": "CAMPER", "LEADER": "LEADER_Brock",
    "LASS": "LASS", "YOUNGSTER": "YOUNGSTER",
    "SUPERNERD": "SUPERNERD", "HIKER": "HIKER",
    "ROCKET": "TEAMROCKET_M", "SWIMMER": "SWIMMER2_M",
    "PICNICKER": "PICNICKER", "LEADER_MISTY": "LEADER_Misty",
    "SAILOR": "SAILOR", "ENGINEER": "ENGINEER",
    "GENTLEMAN": "GENTLEMAN", "FISHERMAN": "FISHERMAN",
    "LEADER_SURGE": "ENGINEER",  # Provisional electric-themed battle portrait; original FRLG trainer art not redistributed.
    "LEADER_ERIKA": "LEADER_Erika",
    "BEAUTY": "BEAUTY",
    "COOLTRAINER_F": "COOLTRAINER_F",
    "LEADER_KOGA": "LEADER_Koga",
    "JUGGLER": "JUGGLER",
    "LEADER_SABRINA": "LEADER_Sabrina",
    "PSYCHIC": "PSYCHIC_M",
    "CHANNELER": "CHANNELER",
    "BLACKBELT": "BLACKBELT",
    "RIVAL_SILPH": "RIVAL2",
    "ROCKETBOSS": "ROCKETBOSS",
    "TAMER": "TAMER",
    # Temporary Decades portraits until separately licensed FRLG trainer art is reviewed.
    "BURGLAR": "SUPERNERD", "SCIENTIST": "SUPERNERD",
    "LEADER_BLAINE": "SUPERNERD",
    "COOLTRAINER_M": "COOLTRAINER_F",  # Provisional battle portrait; authentic male overworld sprites.
    "LEADER_GIOVANNI": "ROCKETBOSS",  # Local fallback battle portrait pending art licensing.
    "POKEMANIAC": "SUPERNERD",
    "COOLCOUPLE": "COOLTRAINER_F",
    "ELITE_LORELEI": "LEADER_Erika",
    "ELITE_BRUNO": "LEADER_Brock",
    "ELITE_AGATHA": "LEADER_Sabrina",
    "ELITE_LANCE": "ROCKETBOSS",
    "CHAMPION_BLUE": "RIVAL1",
}
TRAINERS = {
    24: {16: ("BUGCATCHER", "Rick"), 17: ("BUGCATCHER", "Doug"), 18: ("BUGCATCHER", "Anthony"),
         19: ("BUGCATCHER", "Charlie"), 20: ("BUGCATCHER", "Sammy")},
    28: {6: ("CAMPER", "Liam"), 7: ("LEADER", "Brock")},
}
# These event IDs and trainer roles come from a read-only source map audit.
TRAINERS.update({
    32: {
        1: ("LASS", "Janice"), 2: ("BUGCATCHER", "Colton"),
        3: ("YOUNGSTER", "Ben"), 4: ("LASS", "Sally"),
        5: ("BUGCATCHER", "Greg"), 6: ("BUGCATCHER", "James"),
        7: ("YOUNGSTER", "Calvin"), 8: ("LASS", "Robin"),
    },
    36: {
        1: ("LASS", "Iris"), 3: ("BUGCATCHER", "Kent"),
        4: ("BUGCATCHER", "Robby"), 5: ("SUPERNERD", "Jovan"),
        7: ("LASS", "Miriam"), 8: ("YOUNGSTER", "Josh"),
        9: ("HIKER", "Marcos"),
    },
    38: {
        5: ("ROCKET", "Grunt", 1), 8: ("ROCKET", "Grunt", 2),
        12: ("ROCKET", "Grunt", 3), 18: ("ROCKET", "Grunt", 4),
        19: ("SUPERNERD", "Miguel"),
    },
    42: {
        1: ("LEADER_MISTY", "Misty"), 11: ("SWIMMER", "Luis"),
        16: ("PICNICKER", "Diana"),
    },
})

TRAINERS.update({
    61: {
        8: ("BUGCATCHER", "Keigo"), 9: ("PICNICKER", "Nancy"),
        10: ("CAMPER", "Ricky"), 12: ("BUGCATCHER", "Elijah"),
        13: ("PICNICKER", "Isabelle"), 14: ("CAMPER", "Jeff"),
    },
    67: {
        1: ("SAILOR", "Dwayne"), 2: ("ENGINEER", "Bailey"),
        3: ("GENTLEMAN", "Tucker"), 5: ("LEADER_SURGE", "Lt. Surge"),
    },
    74: {
        30: ("LASS", "Ann"), 31: ("YOUNGSTER", "Tyler"),
        38: ("GENTLEMAN", "Thomas"), 49: ("GENTLEMAN", "Arthur"),
    },
    75: {
        39: ("GENTLEMAN", "Brooks"), 40: ("FISHERMAN", "Dale"),
        44: ("GENTLEMAN", "Lamar"), 46: ("LASS", "Dawn"),
    },
    77: {
        18: ("FISHERMAN", "Barny"), 19: ("SAILOR", "Phillip"),
        21: ("SAILOR", "Huey"), 23: ("SAILOR", "Dylan"),
        24: ("SAILOR", "Duncan"), 25: ("SAILOR", "Leonard"),
    },
    78: {
        9: ("SAILOR", "Trevor"), 10: ("SAILOR", "Edmond"),
    },
})

# Celadon Gym: all eight event IDs and sight values audited in the
# pinned Essentials FRLG 1.1 Map124; no Rocket/Game Corner imports.
TRAINERS[124] = {
    1: ("LEADER_ERIKA", "Erika"),
    7: ("PICNICKER", "Tina"),
    42: ("LASS", "Kay"),
    43: ("BEAUTY", "Bridget"),
    44: ("BEAUTY", "Tamia"),
    45: ("BEAUTY", "Lori"),
    46: ("LASS", "Lisa"),
    47: ("COOLTRAINER_F", "Mary"),
}

# Fuchsia Gym: Map147 anchors verified from pinned FRLG 1.1:
# Koga + six trainers with authored battle wrappers; no source scripts run.
TRAINERS[147] = {
    3: ("JUGGLER", "Nate"),
    4: ("JUGGLER", "Kayden"),
    5: ("JUGGLER", "Kirk"),
    6: ("TAMER", "Edgar"),
    7: ("TAMER", "Phil"),
    8: ("JUGGLER", "Shawn"),
    11: ("LEADER_KOGA", "Koga"),
}

# Verified in read-only FRLG Map171/172 audit. No source Ruby commands run.
TRAINERS[171] = {
    2: ("LEADER_SABRINA", "Sabrina"),
    3: ("PSYCHIC", "Cameron"), 5: ("CHANNELER", "Tasha"),
    6: ("CHANNELER", "Stacy"), 7: ("PSYCHIC", "Preston"),
    8: ("CHANNELER", "Amanda"), 9: ("PSYCHIC", "Johan"),
    13: ("PSYCHIC", "Tyron"),
}
TRAINERS[172] = {
    6: ("BLACKBELT", "Hideki"),
    7: ("BLACKBELT", "Hitoshi"),  # Source event typo: Hitoshii; PBS: Hitoshi.
    9: ("BLACKBELT", "Aaron"), 10: ("BLACKBELT", "Mike"),
    12: ("BLACKBELT", "Koichi"),
}
SILPH_ROCKET_EVENTS = {
    179: {5: 21, 6: 22},
    180: {5: 23}, 181: {5: 24, 7: 25},
    182: {5: 26, 8: 27}, 183: {5: 28, 7: 29},
    184: {5: 30, 6: 31, 10: 32},
    185: {5: 33, 6: 34}, 186: {5: 35, 9: 36},
    187: {6: 37}, 188: {4: 38, 7: 39},
}
for source_id, versions in SILPH_ROCKET_EVENTS.items():
    TRAINERS[source_id] = {eid: ("ROCKET", "Grunt", version)
                           for eid, version in versions.items()}
TRAINERS[188][10] = ("ROCKETBOSS", "Giovanni", 2)

# Phase 12: IDs, coordinates and trainer names verified against the pinned
# FRLG Map199-208 source by audit_cinnabar.py. No source event scripts run.
# Viridian Gym 13: audited event identities and trainer Sight(n) triggers.
# FRLG mistakenly starts Tamer Cole for the event named Jason (8); use the
# distinct [TAMER,Jason] PBS team instead of executing that foreign script.
TRAINERS[13] = {
    2: ("BLACKBELT", "Takashi"),
    3: ("COOLTRAINER_M", "Samuel"),
    4: ("LEADER_GIOVANNI", "Giovanni"),
    5: ("BLACKBELT", "Kiyo"),
    6: ("TAMER", "Cole"),
    7: ("COOLTRAINER_M", "Yuji"),
    8: ("TAMER", "Jason"),
    9: ("BLACKBELT", "Atsushi"),
    10: ("COOLTRAINER_M", "Warren"),
}
VIRIDIAN_GYM_EVENTS = set(TRAINERS[13]) | {11, 16}

# Phase 14 / Victory Road source IDs. Trainer events 15 and 16 on 3F
# are the same original double battle, with one shared victory key.
TRAINERS[211] = {7: ("COOLTRAINER_F", "Naomi"),
                 11: ("COOLTRAINER_M", "Rolando")}
TRAINERS[212] = {9: ("BLACKBELT", "Daisuke"), 11: ("TAMER", "Vincent"),
                 13: ("JUGGLER", "Nelson"), 14: ("JUGGLER", "Gregory"),
                 16: ("POKEMANIAC", "Dawson")}
TRAINERS[213] = {10: ("COOLTRAINER_M", "George"),
                 12: ("COOLTRAINER_F", "Alexa"),
                 13: ("COOLTRAINER_F", "Caroline"),
                 14: ("COOLTRAINER_M", "Colby"),
                 15: ("COOLCOUPLE", "Ray & Tyra"),
                 16: ("COOLCOUPLE", "Ray & Tyra")}

# Only reviewed events may enter the pilot; source global switches,
# rival commands, wall/boulder position checks, credits and story flags
# must never be copied from the FRLG project.
LEAGUE_BADGE_GATES = {17: {4: (1, 5)}, 209: {
    7: (2, 6), 9: (3, 8), 11: (4, 10), 13: (5, 12),
    15: (6, 14), 17: (7, 16), 19: (8, 18),
}}
LEAGUE_BARRIER_GATES = {17: {5: 1}, 209: {
    6: 2, 8: 3, 10: 4, 12: 5, 14: 6, 16: 7, 18: 8,
}}
VICTORY_ROAD_BARRIERS = {211: (14, 15), 212: (21, 22, 24, 25),
                         213: (17, 18)}
VICTORY_ROAD_BOULDERS = {211: (3, 5, 16), 212: (7, 26, 27),
                         213: (6, 7, 8, 19)}
LEAGUE_EVENT_WHITELIST = {
    16: {1},
    17: {1, 3, 4, 5},
    209: {1, 2, 4, *range(6,20)},
    211: {1, 2, 3, 5, 7, 11, 14, 15, 16},
    212: {1,2,3,4,5,6,7,9,11,13,14,16,21,22,24,25,26,27},
    213: {1,2,3,4,5,6,7,8,10,12,13,14,15,16,17,18,19},
    214: {1},
    215: {1,3,4,6,14},
    216: {1,3},
    217: {1,3},
    218: {1,3},
    219: {1,3},
    220: {1,2,6},
    221: {1,2},
}
LEAGUE_NEXT_ROOMS = {
    216: (1,217,6,12), 217:(3,218,6,12), 218:(3,219,23,10),
    219:(3,220,7,19), 220:(2,221,5,12),
}
LEAGUE_TRAINER_SPECS = {
    216:(3,"ELITE_LORELEI","Lorelei",0,0),
    217:(1,"ELITE_BRUNO","Bruno",1,0),
    218:(1,"ELITE_AGATHA","Agatha",2,0),
    219:(1,"ELITE_LANCE","Lance",3,0),
    220:(6,"CHAMPION_BLUE","Blue",4,-1),
}

TRAINERS[202] = {
    4: ("BURGLAR", "Quinn"), 5: ("SUPERNERD", "Erik"),
    6: ("SUPERNERD", "Avery"), 7: ("BURGLAR", "Ramon"),
    8: ("SUPERNERD", "Derek"), 9: ("BURGLAR", "Dusty"),
    10: ("SUPERNERD", "Zac"), 16: ("LEADER_BLAINE", "Blaine"),
}
TRAINERS[205] = {3: ("YOUNGSTER", "Johnson"), 9: ("SCIENTIST", "Ted")}
TRAINERS[206] = {5: ("BURGLAR", "Arnie")}
TRAINERS[207] = {4: ("BURGLAR", "Simon"), 5: ("SCIENTIST", "Braydon")}
TRAINERS[208] = {4: ("BURGLAR", "Lewis"), 5: ("SCIENTIST", "Ivan")}

CINNABAR_GYM_DOORS = {
    1: (20, 21, 22, 23), 2: (1, 25, 26, 27),
    3: (2, 18, 19, 29), 4: (13, 31, 32),
    5: (34, 35, 36, 37), 6: (39, 40, 41, 42),
}
CINNABAR_GYM_QUIZZES = {24: 1, 28: 2, 30: 3, 33: 4, 38: 5, 43: 6}
CINNABAR_GYM_TRAINER_GROUPS = {4: 1, 6: 2, 7: 3, 8: 4, 9: 5, 10: 6}
CINNABAR_DOOR_TO_GROUP = {
    event: group for group, events in CINNABAR_GYM_DOORS.items() for event in events
}
MANSION_DOORS = {
    205: (14, *range(16, 39)),
    206: (*range(9, 14), *range(16, 27)),
    207: tuple(range(10, 21)),
    208: tuple(range(12, 34)),
}
MANSION_STATUES = {205: (4,), 206: (15,), 207: (9,), 208: (10, 11)}
MANSION_WARPS = {
    205: (1, 2, 5, 6), 206: (1, 2, 3, 4),
    207: (1, 2, 3, 21, 22, 23, 24, 25), 208: (1,),
}
CINNABAR_EVENTS = {
    199: {1, 2, 3, 4, 5},
    200: {1, 2}, 201: {1, 2}, 203: {1, 2, 3, 4, 5, 6, 7},
    202: ({3} | set(TRAINERS[202]) | set(CINNABAR_GYM_QUIZZES)
          | set(CINNABAR_DOOR_TO_GROUP)),
}
for _map_id in MANSION_DOORS:
    CINNABAR_EVENTS[_map_id] = (set(MANSION_WARPS[_map_id]) |
                                 set(MANSION_STATUES[_map_id]) |
                                 set(MANSION_DOORS[_map_id]) |
                                 set(TRAINERS[_map_id]) |
                                 ({8} if _map_id == 208 else set()))

SAFFRON_STATIC_EVENTS = {
    168: {6, 10, 12, 13, 14},             # City <-> gym, Silph, Mart, Center, Dojo
    169: {1, 2},                         # Center exit + nurse
    170: {1, 2},                         # Mart exit + clerk
    171: {2, 3, 5, 6, 7, 8, 9, 10, 11, 13, *range(17, 46)},
    172: {1, 2, 4, 6, 7, 9, 10, 12},     # Dojo fights, prizes, exit
    189: {1, 2},                         # Local elevator replaces original warps
}
SILPH_EXTRAS = {(178, 1), (182, 9), (184, 43), (188, 18)}
# Map189 source elevator jumps to unimported Map207..217. Safe
# destinations are interior tiles adjacent to the audited elevator entrances.
SILPH_FLOOR_LANDINGS = {
    178: (22, 5), 179: (22, 5), 180: (22, 5),
    181: (22, 5), 182: (22, 5), 183: (20, 5),
    184: (23, 5), 185: (22, 5), 186: (24, 5),
    187: (13, 5), 188: (13, 5),
}

def league_event_allowed(source_id, event_id):
    return source_id not in LEAGUE_EVENT_WHITELIST or (
        event_id in LEAGUE_EVENT_WHITELIST[source_id]
    )


def viridian_event_allowed(source_id, event_id):
    # Do not leak FRLG Gym plaques, global script page conditions, or its
    # original variable-controlled events into Decades.
    return source_id != 13 or event_id in VIRIDIAN_GYM_EVENTS


def cinnabar_event_allowed(source_id, event_id):
    if source_id in CINNABAR_EVENTS:
        return event_id in CINNABAR_EVENTS[source_id]
    return True


def saffron_event_allowed(source_id, event_id, event):
    if source_id in SAFFRON_STATIC_EVENTS:
        return event_id in SAFFRON_STATIC_EVENTS[source_id]
    if 178 <= source_id <= 188:
        name = text(event.attrs["@name"])
        return (event_id in TRAINERS.get(source_id, {}) or
                (source_id, event_id) in SILPH_EXTRAS or
                name.startswith(("Stairs ", "Elevator Door", "Warp Tile ", "Locked Door")))
    return True

def silph_locked_group(events, event_id):
    """Group only orthogonally adjacent locked-door event tiles."""
    doors = {eid: (ev.attrs["@x"], ev.attrs["@y"])
             for eid, ev in events.items()
             if text(ev.attrs["@name"]) == "Locked Door"}
    if event_id not in doors:
        raise ValueError(f"Missing audited Silph locked door {event_id}")
    seen, pending = {event_id}, [event_id]
    while pending:
        x, y = doors[pending.pop()]
        for other, (xx, yy) in doors.items():
            if other not in seen and abs(x - xx) + abs(y - yy) == 1:
                seen.add(other)
                pending.append(other)
    return sorted(seen)

SURGE_CANS = {4, 10, *range(22, 35)}
SURGE_LOCKS = {8, *range(11, 20)}

MART = 'pbPokemonMart([:POKEBALL, :POTION, :ANTIDOTE, :PARALYZEHEAL])'
VIRIDIAN_MART = "BlueKantoPilot.viridian_mart"


def write_map(path, obj, classes=()):
    path.write_bytes(serialize(obj, classes))


def command(code, *params, indent=0):
    return RubyObject("RPG::EventCommand", {"@code": code, "@indent": indent, "@parameters": list(params)})


def extract_warps(event, mapping):
    for page in event.attrs["@pages"]:
        for op in page.attrs["@list"]:
            row = op.attrs
            if row["@code"] == 201:
                mode, map_id, x, y, direction, fade = row["@parameters"]
                if mode == 0 and map_id in mapping:
                    return command(201, mode, mapping[map_id], x, y, direction, fade)
    return None


def new_event(event, ops, trigger, character):
    clone = copy.deepcopy(event)
    page = clone.attrs["@pages"][0].attrs
    clone.attrs["@pages"] = clone.attrs["@pages"][:1]
    condition = page["@condition"].attrs
    for key in tuple(condition):
        if key.endswith("_valid"):
            condition[key] = False
    graphic = page["@graphic"].attrs
    graphic["@character_name"] = character
    if not character:
        graphic["@tile_id"] = 0
    page["@move_type"] = 0
    page["@move_route"] = RubyObject("RPG::MoveRoute", {
        "@repeat": False, "@skippable": True,
        "@list": [RubyObject("RPG::MoveCommand", {"@code": 0, "@parameters": []})],
    })
    page["@trigger"] = trigger
    page["@through"] = trigger == 1
    page["@direction_fix"] = trigger == 1
    page["@list"] = ops + [command(0)]
    return clone


def move_actor(event_id, *steps):
    # Through only for the duration of the authored cutscene.
    route = RubyObject("RPG::MoveRoute", {
        "@repeat": False, "@skippable": True,
        "@list": [RubyObject("RPG::MoveCommand", {"@code": step, "@parameters": []})
                  for step in (37, *steps, 38, 0)],
    })
    return command(209, event_id, route, indent=1)


def if_scene(condition, actions):
    return [command(111, 12, condition), *actions, command(0, indent=1), command(412)]


def oak_escort(event_id, lab, scene_id):
    # Both northbound lanes use the same source path, with a one-tile offset.
    right = 1 if event_id == 11 else 2
    return if_scene(b"!BlueKantoPilot.starter", [
        command(355, b"BlueKantoPilot.oak_warning", indent=1),
        move_actor(-1, 16),
        command(355, b'BlueKantoPilot.show_approaching_oak(true)', indent=1),
        move_actor(12, *([4] * 5), *([3] * right), 4, 16),
        command(210, indent=1),
        command(355, b"BlueKantoPilot.oak_invitation", indent=1),
        move_actor(12, 1, *([2] * right), *([1] * 11), *([3] * 5), 19),
        move_actor(-1, 1, 1, *([2] * right), *([1] * 12), *([3] * 5), 19),
        command(210, indent=1),
        command(355, b'BlueKantoPilot.show_approaching_oak(false)', indent=1),
        command(355, f"BlueKantoPilot.prepare_lab_escort({lab}, {scene_id})".encode(), indent=1),
        command(201, 0, lab, 6, 12, 8, 0, indent=1),
    ])



def lab_starter_balls(events):
    """Use only the three visible starter-ball objects from the pinned source."""
    matches = []
    for event_id, event in events.items():
        name = text(event.attrs["@name"])
        graphic = event.attrs["@pages"][0].attrs["@graphic"].attrs
        visible = bool(graphic["@character_name"]) or graphic["@tile_id"] > 0
        if visible and re.search(r"pok[eé]\\s*ball|pok[eé]bola|starter|bulbasaur|charmander|squirtle", name, re.I):
            matches.append((event_id, event))
    if len(matches) != 3:
        raise ValueError(
            "Map006: the three visible source Poké Balls were not identified. "
            "Audit original event names/graphics before importing.")
    matches.sort(key=lambda row: (row[1].attrs["@x"], row[1].attrs["@y"]))
    return [event_id for event_id, _ in matches]


def walk_from_to(x, y, target_x, target_y):
    """Safe, temporarily-through-enabled authored movement for cutscenes."""
    return ([4] * max(y - target_y, 0) +
            [1] * max(target_y - y, 0) +
            [2] * max(x - target_x, 0) +
            [3] * max(target_x - x, 0) +
            [16])


def gary_challenge(gary, at_x, at_y):
    x, y = gary.attrs["@x"], gary.attrs["@y"]
    target_x = at_x + (1 if at_x <= x else -1)
    approach = walk_from_to(x, y, target_x, at_y)
    retreat = walk_from_to(target_x, at_y, x, y)
    return if_scene(b"BlueKantoPilot.rival_pending?", [
        move_actor(-1, 19),
        move_actor(14, *approach),
        command(210, indent=1),
        command(355, b"BlueKantoPilot.rival", indent=1),
        move_actor(14, *retreat),
        command(210, indent=1),
    ])


def lab_arrival_scene(events, event_id):
    """One-shot autorun armed ONLY by Oak's exterior Pallet escort."""
    oak, gary = events[15], events[14]
    entry_x, entry_y = 6, 12
    oak_x, oak_y = oak.attrs["@x"], oak.attrs["@y"]
    gary_x, gary_y = gary.attrs["@x"], gary.attrs["@y"]
    side_x = gary_x + (-1 if gary_x >= entry_x else 1)
    if not (0 <= side_x and 0 <= gary_y < 1000):
        raise ValueError("Invalid Gary lab escort target")
    blank = new_event(oak, [], 0, b"")
    blank.attrs.update({"@id": event_id, "@name": b"Blue Oak Laboratory Escort",
                        "@x": entry_x, "@y": entry_y})
    base = blank.attrs["@pages"][0].attrs
    base["@through"] = True
    base["@list"] = [command(0)]
    active = copy.deepcopy(blank.attrs["@pages"][0])
    page = active.attrs
    page["@condition"].attrs.update({"@self_switch_valid": True, "@self_switch_ch": b"A"})
    page["@trigger"] = 3
    page["@through"] = True
    page["@list"] = [
        command(355, b"BlueKantoPilot.lab_escort_started"),
        command(203, 15, 0, entry_x, entry_y - 1, 8),
        move_actor(15, *walk_from_to(entry_x, entry_y - 1, oak_x, oak_y)),
        move_actor(-1, *walk_from_to(entry_x, entry_y, side_x, gary_y)),
        command(210),
        command(355, b"BlueKantoPilot.oak_lab_briefing"),
        command(123, b"A", 1),
        command(0),
    ]
    blank.attrs["@pages"].append(active)
    return blank


def starter_ball(event, species):
    graphic = event.attrs["@pages"][0].attrs["@graphic"]
    result = new_event(event, [
        command(355, f"BlueKantoPilot.pick_starter(:{species}, {event.attrs['@id']})".encode()),
    ], 0, graphic.attrs["@character_name"])
    result.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(graphic)
    result.attrs["@pages"][0].attrs["@direction_fix"] = True
    taken = copy.deepcopy(result.attrs["@pages"][0])
    condition = taken.attrs["@condition"].attrs
    condition.update({"@self_switch_valid": True, "@self_switch_ch": b"A"})
    taken.attrs["@through"] = True
    taken.attrs["@graphic"].attrs.update({"@character_name": b"", "@tile_id": 0})
    taken.attrs["@list"] = [command(0)]
    result.attrs["@pages"].append(taken)
    return result


def rival_counter_trigger(events, event_id):
    exit_event, gary = events[1], events[14]
    y = min(exit_event.attrs["@y"] - 2, gary.attrs["@y"] + 4)
    if not (gary.attrs["@y"] < y < exit_event.attrs["@y"]):
        raise ValueError("Map006: no corridor past the counter before the exit")
    x = exit_event.attrs["@x"]
    marker = new_event(exit_event, gary_challenge(gary, x, y), 1, b"")
    marker.attrs.update({"@id": event_id, "@name": b"Blue Gary Counter Battle",
                         "@x": x, "@y": y})
    return marker

def find_shopkeeper(events):
    for event_id, event in events.items():
        for page in event.attrs["@pages"]:
            for op in page.attrs["@list"]:
                if op.attrs["@code"] == 355 and b"pbPokemonMart" in op.attrs["@parameters"][0]:
                    return event_id
    raise ValueError("The Viridian shopkeeper event was not found")


def install_events(source, target, mapping):
    event_graphics = source / "Graphics/Characters"
    dest_graphics = target / "Graphics/Characters"

    def actor(event):
        raw = event.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"]
        name = text(raw)
        if not re.fullmatch(r"[\w .()\-]+", name):
            raise ValueError(f"Invalid actor graphic: {name!r}")
        src = event_graphics / (name + ".png")
        if not src.resolve().is_relative_to(event_graphics.resolve()) or not src.is_file():
            raise ValueError(f"Missing actor graphic: {name}")
        new_name = "FRLG_Pilot_" + name
        shutil.copyfile(src, dest_graphics / (new_name + ".png"))
        return new_name.encode("utf8")

    lab_source_events = load(source / "Data/Map006.rxdata").attrs["@events"]
    for required in (1, 14, 15):
        if required not in lab_source_events:
            raise ValueError(f"Oak lab missing audited event {required}")
    starter_balls = lab_starter_balls(lab_source_events)
    lab_scene_id = max(lab_source_events) + 1
    rival_counter_id = lab_scene_id + 1
    preview_only = set(json_file(KANTO).get("preview_only", []))
    if preview_only - mapping.keys():
        raise ValueError("Preview-only map ID is missing from the source manifest")
    for original, destination in mapping.items():
        # Celadon: three maps; Fuchsia: five audited core maps (including
        # Safari Gate informational NPC) with adapted gameplay only.
        # All 53 remaining previews forbid any foreign event.
        # stage() already serializes a blank event table for every imported map.
        if original in preview_only:
            dest_file = target / "Data" / f"Map{destination:03}.rxdata"
            staged_map = load(dest_file)
            if staged_map.attrs["@events"]:
                raise ValueError(f"Phase 09-11 preview map {original} contains foreign events")
            continue
        events = load(source / "Data" / f"Map{original:03}.rxdata").attrs["@events"]
        dest_file = target / "Data" / f"Map{destination:03}.rxdata"
        map_data = load(dest_file)
        selected = {}
        script_events = {5: {9: "BlueRegionTravel.agent(true)"},
                          17: {3: f"BlueKantoPilot.league_route_gate({mapping[209]}, 14, 153, 1)"},
                          209: {
                              2: f"BlueKantoPilot.league_route_gate({mapping[211]}, 18, 25, 8)",
                              4: f"BlueKantoPilot.league_route_gate({mapping[212]}, 55, 17, 8)",
                          },
                          214: {1: f"BlueKantoPilot.league_route_gate({mapping[215]}, 11, 16, 8)"},
                          215: {1: MART,
                                3: f"BlueKantoPilot.league_begin({mapping[216]}, 6, 12)",
                                4: "BlueKantoPilot.heal",
                                14: "BlueKantoPilot.league_guide"},
                          220: {1: "BlueKantoPilot.league_champion_npc"},
                          221: {1: f"BlueKantoPilot.league_finalize({mapping[5]})",
                                2: "BlueKantoPilot.league_oak"},
                         10: {1: f"BlueKantoPilot.viridian_gym_gate({mapping[13]}, 17, 22)"},
                         13: {16: "BlueKantoPilot.viridian_gym_guide"},
                          7: {13: "BlueKantoPilot.mom"},
                          8: {8: "BlueKantoPilot.daisy"},
                          6: {15: "BlueKantoPilot.talk_to_oak", 14: "BlueKantoPilot.gary_talk"},
                         11: {2: "BlueKantoPilot.heal"},
                         115: {2: "BlueKantoPilot.heal"},
                         145: {2: "BlueKantoPilot.heal"},
                          169: {2: "BlueKantoPilot.heal"},
                          170: {2: MART},
                          172: {1: "BlueKantoPilot.dojo_prize(:HITMONLEE, 1)",
                                2: "BlueKantoPilot.dojo_prize(:HITMONCHAN, 2)"},
                          182: {9: "BlueKantoPilot.silph_card_key"},
                          184: {43: "BlueKantoPilot.silph_rival"},
                          188: {18: "BlueKantoPilot.silph_president"},
                          189: {1: "BlueKantoPilot.silph_elevator",
                                2: "BlueKantoPilot.silph_elevator"},
                          199: {4: f"BlueKantoPilot.cinnabar_gym_gate({mapping[202]}, 25, 23)"},
                          200: {2: "BlueKantoPilot.heal"},
                          201: {2: MART},
                          208: {8: "BlueKantoPilot.mansion_secret_key"},
                         146: {2: MART},
                         153: {1: "BlueKantoPilot.safari_preview", 5: "BlueKantoPilot.safari_preview"},
                         26: {2: "BlueKantoPilot.heal"},
                         34: {2: "BlueKantoPilot.heal"},
                         40: {2: "BlueKantoPilot.heal"},
                         36: {18: 'BlueKantoPilot.pickup(:MOONSTONE, "KANTO_036_018")'},
                         65: {2: "BlueKantoPilot.heal"},
                         64: {7: "BlueKantoPilot.ticketmaster"},
                         76: {2: "BlueKantoPilot.captain"}}
        scripts = dict(script_events.get(original, {}))
        if original in (12, 27, 41, 66):
            scripts[find_shopkeeper(events)] = VIRIDIAN_MART if original == 12 else MART
        if original == 64:
            for event_id in (9, 29, 30):
                if event_id not in events:
                    raise ValueError(f"Missing Vermilion harbor gate {event_id}")
                scripts[event_id] = (
                    f"BlueKantoPilot.harbor_gate({mapping[72]}, 9, 7)"
                )
        for event_id, spec in TRAINERS.get(original, {}).items():
            kind, name, *versions = spec
            version = versions[0] if versions else 0
            # Map/event identity prevents two NPCs with the same display name
            # from sharing their victory flag. Never key trainer progress by name.
            key = f"KANTO_{original:03d}_{event_id:03d}"
            arguments = f':BLUE_KANTO_{kind}, "{name}", "{key}"'
            arguments += f", {version}" if version else ""
            scripts[event_id] = f"BlueKantoPilot.battle({arguments})"
        for event_id, required in LEAGUE_BARRIER_GATES.get(original, {}).items():
            guard = (4 if original == 17 else event_id + 1)
            scripts[event_id] = f"BlueKantoPilot.league_badge_check({required}, {guard}, {event_id})"
        for guard_id, (required, barrier_id) in LEAGUE_BADGE_GATES.get(original, {}).items():
            scripts[guard_id] = f"BlueKantoPilot.league_badge_check({required}, {guard_id}, {barrier_id})"
        for floor, (eid, next_map, x, y) in LEAGUE_NEXT_ROOMS.items():
            if original == floor:
                stage = ("CHAMPION" if floor == 220 else
                         {216:"LORELEI",217:"BRUNO",218:"AGATHA",219:"LANCE"}[floor])
                scripts[eid] = f'BlueKantoPilot.league_advance("{stage}", {mapping[next_map]}, {x}, {y})'
        if original in LEAGUE_TRAINER_SPECS:
            eid, kind, name, stage, _ = LEAGUE_TRAINER_SPECS[original]
            script = (f'BlueKantoPilot.league_battle("{["LORELEI","BRUNO","AGATHA","LANCE","CHAMPION"][stage]}", '
                      f':BLUE_KANTO_{kind}, "{name}", {mapping[215]})')
            scripts[eid] = script
        if original == 213:
            scripts[15] = "BlueKantoPilot.victory_couple"
            scripts[16] = "BlueKantoPilot.victory_couple"
        if original == 202:
            for gym_id, group in CINNABAR_GYM_TRAINER_GROUPS.items():
                kind, name, *_ = TRAINERS[202][gym_id]
                key = f"KANTO_202_{gym_id:03d}"
                scripts[gym_id] = (
                    f'BlueKantoPilot.cinnabar_trainer(:BLUE_KANTO_{kind}, "{name}", '
                    f'"{key}", {group})'
                )
        if scripts.keys() - events.keys():
            raise ValueError(f"Missing event anchor in map {original}")
        for event_id, event in events.items():
            if original == 6 and event_id in starter_balls:
                # Left to right: Bulbasaur, Charmander, Squirtle (FRLG).
                species = ("BULBASAUR", "CHARMANDER", "SQUIRTLE")[starter_balls.index(event_id)]
                selected[event_id] = starter_ball(event, species)
                continue
            if not saffron_event_allowed(original, event_id, event):
                continue
            if not cinnabar_event_allowed(original, event_id):
                continue
            if not viridian_event_allowed(original, event_id):
                continue
            if not league_event_allowed(original, event_id):
                continue
            if original in LEAGUE_BARRIER_GATES and event_id in LEAGUE_BARRIER_GATES[original]:
                required = LEAGUE_BARRIER_GATES[original][event_id]
                guard = 4 if original == 17 else event_id + 1
                e = new_event(event, [
                    command(355, f"BlueKantoPilot.league_badge_check({required}, {guard}, {event_id})".encode())
                ], 2, b"")
                e.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(
                    event.attrs["@pages"][0].attrs["@graphic"])
                opened = copy.deepcopy(e.attrs["@pages"][0])
                cond = opened.attrs["@condition"].attrs
                cond["@self_switch_valid"] = True
                cond["@self_switch_ch"] = b"A"
                opened.attrs["@trigger"] = 0
                opened.attrs["@through"] = True
                opened.attrs["@graphic"].attrs["@tile_id"] = 0
                opened.attrs["@graphic"].attrs["@character_name"] = b""
                opened.attrs["@list"] = [command(0)]
                e.attrs["@pages"].append(opened)
                selected[event_id] = e
                continue
            if original in LEAGUE_BADGE_GATES and event_id in LEAGUE_BADGE_GATES[original]:
                required, barrier = LEAGUE_BADGE_GATES[original][event_id]
                e = new_event(event, [
                    command(355, f"BlueKantoPilot.league_badge_check({required}, {event_id}, {barrier})".encode())
                ], 0, actor(event))
                opened = copy.deepcopy(e.attrs["@pages"][0])
                cond = opened.attrs["@condition"].attrs
                cond["@self_switch_valid"] = True
                cond["@self_switch_ch"] = b"A"
                opened.attrs["@trigger"] = 0
                opened.attrs["@through"] = True
                opened.attrs["@list"] = [command(0)]
                e.attrs["@pages"].append(opened)
                selected[event_id] = e
                continue
            if original in VICTORY_ROAD_BARRIERS and event_id in VICTORY_ROAD_BARRIERS[original]:
                barrier_ids = list(VICTORY_ROAD_BARRIERS[original])
                e = new_event(event, [
                    command(355, f"BlueKantoPilot.victory_strength({barrier_ids})".encode())
                ], 0, b"")
                e.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(
                    event.attrs["@pages"][0].attrs["@graphic"])
                opened = copy.deepcopy(e.attrs["@pages"][0])
                cond = opened.attrs["@condition"].attrs
                cond["@self_switch_valid"] = True
                cond["@self_switch_ch"] = b"A"
                opened.attrs["@trigger"] = 0
                opened.attrs["@through"] = True
                opened.attrs["@graphic"].attrs["@tile_id"] = 0
                opened.attrs["@graphic"].attrs["@character_name"] = b""
                opened.attrs["@list"] = [command(0)]
                e.attrs["@pages"].append(opened)
                selected[event_id] = e
                continue
            if original in VICTORY_ROAD_BOULDERS and event_id in VICTORY_ROAD_BOULDERS[original]:
                barrier_ids = list(VICTORY_ROAD_BARRIERS[original])
                base = event.attrs["@pages"][0].attrs["@graphic"]
                ch = base.attrs["@character_name"]
                e = new_event(event, [
                    command(355, f"BlueKantoPilot.victory_strength({barrier_ids})".encode())
                ], 0, actor(event) if ch else b"")
                e.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(base)
                selected[event_id] = e
                continue

            if original == 202 and event_id in CINNABAR_DOOR_TO_GROUP:
                group = CINNABAR_DOOR_TO_GROUP[event_id]
                locked = new_event(event, [
                    command(355, f"BlueKantoPilot.cinnabar_door({group})".encode())
                ], 0, b"")
                locked.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(
                    event.attrs["@pages"][0].attrs["@graphic"])
                opened = copy.deepcopy(locked.attrs["@pages"][0])
                cond = opened.attrs["@condition"].attrs
                cond["@self_switch_valid"] = True
                cond["@self_switch_ch"] = b"A"
                opened.attrs["@through"] = True
                opened.attrs["@graphic"].attrs["@tile_id"] = 0
                opened.attrs["@graphic"].attrs["@character_name"] = b""
                opened.attrs["@list"] = [command(0)]
                locked.attrs["@pages"].append(opened)
                selected[event_id] = locked
                continue
            if original == 202 and event_id in CINNABAR_GYM_QUIZZES:
                group = CINNABAR_GYM_QUIZZES[event_id]
                quiz = new_event(event, [
                    command(355, f"BlueKantoPilot.cinnabar_quiz({group})".encode())
                ], 0, b"")
                quiz.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(
                    event.attrs["@pages"][0].attrs["@graphic"])
                selected[event_id] = quiz
                continue
            if original in MANSION_DOORS and event_id in MANSION_DOORS[original]:
                door_list = list(MANSION_DOORS[original])
                door = new_event(event, [
                    command(355, f"BlueKantoPilot.mansion_door({original}, {door_list})".encode())
                ], 0, b"")
                door.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(
                    event.attrs["@pages"][0].attrs["@graphic"])
                opened = copy.deepcopy(door.attrs["@pages"][0])
                cond = opened.attrs["@condition"].attrs
                cond["@self_switch_valid"] = True
                cond["@self_switch_ch"] = b"A"
                opened.attrs["@graphic"].attrs["@tile_id"] = 0
                opened.attrs["@graphic"].attrs["@character_name"] = b""
                opened.attrs["@through"] = True
                opened.attrs["@list"] = [command(0)]
                door.attrs["@pages"].append(opened)
                selected[event_id] = door
                continue
            if original in MANSION_STATUES and event_id in MANSION_STATUES[original]:
                door_list = list(MANSION_DOORS[original])
                statue = new_event(event, [
                    command(355, f"BlueKantoPilot.mansion_switch({original}, {door_list})".encode())
                ], 0, b"")
                statue.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(
                    event.attrs["@pages"][0].attrs["@graphic"])
                selected[event_id] = statue
                continue
            # Phase 09 selective import: only audited doors, healing, and
            # gym battles. Do not leak Celadon NPCs, items, Rocket, stores,
            # Cut trees, elevators or untranslated foreign story events.
            if original == 114 and event_id not in (3, 20):
                continue
            if original == 115 and event_id not in (1, 2):
                continue
            if original == 124 and event_id not in (1, 5, 7, 42, 43, 44, 45, 46, 47):
                continue
            # Phase 10: exact Fuchsia whitelists, no Warden/Gold Teeth,
            # Safari captures, Park South event transfers or source quests.
            if original == 144 and event_id not in (5, 17, 18, 24):
                continue
            if original == 145 and event_id not in (1, 2):
                continue
            if original == 146 and event_id not in (1, 2):
                continue
            if original == 147 and event_id not in (3, 4, 5, 6, 7, 8, 9, 11):
                continue
            if original == 153 and event_id not in (1, 2, 5):
                continue
            if 179 <= original <= 188 and text(event.attrs["@name"]) == "Locked Door":
                peers = silph_locked_group(events, event_id)
                expr = f"BlueKantoPilot.silph_door({peers})"
                door = new_event(event, [command(355, expr.encode())], 0, b"")
                opened = copy.deepcopy(door.attrs["@pages"][0])
                cond = opened.attrs["@condition"].attrs
                cond["@self_switch_valid"] = True
                cond["@self_switch_ch"] = b"A"
                opened.attrs["@through"] = True
                opened.attrs["@list"] = [command(0)]
                door.attrs["@pages"].append(opened)
                selected[event_id] = door
                continue
            if original == 67 and event_id in (SURGE_CANS | SURGE_LOCKS):
                # The foreign gym's puzzle depends on game-wide switches.
                # Translate each trash can to a single audited callback, and
                # each barrier to a local self-switch-driven two-page event.
                is_can = event_id in SURGE_CANS
                script = (f"BlueKantoPilot.surge_can({event_id})" if is_can
                          else "BlueKantoPilot.surge_gate")
                original_graphic = event.attrs["@pages"][0].attrs["@graphic"]
                graphic_name = original_graphic.attrs["@character_name"]
                character = actor(event) if graphic_name else b""
                replacement = new_event(event, [command(355, script.encode())], 0, character)
                if not graphic_name:
                    replacement.attrs["@pages"][0].attrs["@graphic"] = copy.deepcopy(original_graphic)
                if not is_can:
                    opened = copy.deepcopy(replacement.attrs["@pages"][0])
                    c = opened.attrs["@condition"].attrs
                    c["@self_switch_valid"] = True
                    c["@self_switch_ch"] = b"A"
                    g = opened.attrs["@graphic"].attrs
                    g["@tile_id"] = 0
                    g["@character_name"] = b""
                    opened.attrs["@through"] = True
                    opened.attrs["@list"] = [command(0)]
                    replacement.attrs["@pages"].append(opened)
                selected[event_id] = replacement
                continue
            if event_id in scripts:
                floor_trigger = ((original == 64 and event_id in (9, 29, 30)) or
                                 (original == 189 and event_id == 1) or
                                 (original == 199 and event_id == 4) or
                                 (original == 17 and event_id == 3) or
                                 (original == 209 and event_id in (2,4)) or
                                 (original == 214 and event_id == 1) or
                                 (original == 215 and event_id == 3) or
                                 (original in LEAGUE_NEXT_ROOMS and
                                  event_id == LEAGUE_NEXT_ROOMS[original][0]) or
                                 (original == 220 and event_id == 6) or
                                 (original == 221 and event_id == 1))
                if event_id in TRAINERS.get(original, {}):
                    kind, trainer_name, *_ = TRAINERS[original][event_id]
                    key = f"KANTO_{original:03d}_{event_id:03d}"
                    # Essentials 21.1 only triggers a Trainer(n) line of sight
                    # when the active RPG Event page uses Event Touch (2).
                    # Preserve Trainer(n)/Sight(n) from the audited FRLG event name;
                    # gym leaders/NPCs without Trainer(n) stay Action Button.
                    source_name = text(event.attrs["@name"])
                    sight = re.search(r"(?i)(?:trainer|sight)\((\d+)\)", source_name)
                    auto = (bool(sight) and
                            event.attrs["@pages"][0].attrs["@trigger"] == 2 and
                            not kind.startswith("LEADER"))
                    ops = []
                    if auto:
                        ops.append(command(355, f"pbTrainerIntro(:BLUE_KANTO_{kind})".encode()))
                        ops.append(command(355, b"pbNoticePlayer(get_self)"))
                    ops.append(command(355, scripts[event_id].encode()))
                    ops.append(command(355,
                        f'BlueKantoPilot.sync_trainer_event("{key}", "{trainer_name}", {event_id})'.encode()))
                    if auto:
                        ops.append(command(355, b"pbTrainerEnd"))
                    trainer = new_event(event, ops, 2 if auto else 0, actor(event))
                    # Self Switch A is set ONLY after a true battle victory or
                    # recognition of the old pre-ID save flag. The second page
                    # keeps the trainer visible but disables the sight trigger.
                    after_win = copy.deepcopy(trainer.attrs["@pages"][0])
                    condition = after_win.attrs["@condition"].attrs
                    condition["@self_switch_valid"] = True
                    condition["@self_switch_ch"] = b"A"
                    after_win.attrs["@trigger"] = 0
                    after_win.attrs["@through"] = False
                    after_win.attrs["@direction_fix"] = False
                    after_win.attrs["@list"] = [
                        command(355, f'BlueKantoPilot.trainer_repeat("{trainer_name}")'.encode()),
                        command(0)]
                    trainer.attrs["@pages"].append(after_win)
                    selected[event_id] = trainer
                else:
                    scripted = new_event(
                        event, [command(355, scripts[event_id].encode())],
                        1 if floor_trigger else 0,
                        b"" if (floor_trigger or
                                not event.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"])
                        else actor(event))
                    if (original, event_id) in {(182, 9), (172, 1), (172, 2), (208, 8)}:
                        # A one-time Card Key/Dojo prize no longer appears
                        # after the region-local reward has been recorded.
                        collected = copy.deepcopy(scripted.attrs["@pages"][0])
                        condition = collected.attrs["@condition"].attrs
                        condition["@self_switch_valid"] = True
                        condition["@self_switch_ch"] = b"A"
                        graphic = collected.attrs["@graphic"].attrs
                        graphic["@character_name"] = b""
                        graphic["@tile_id"] = 0
                        collected.attrs["@through"] = True
                        collected.attrs["@list"] = [command(0)]
                        scripted.attrs["@pages"].append(collected)
                    if original == 5 and event_id == 9:
                        scripted.attrs["@name"] = b"Agente Regional"
                    if original == 17 and event_id == 3:
                        scripted.attrs["@pages"][0].attrs["@trigger"] = 1
                    if original == 10 and event_id == 1:
                        # FRLG Map010/1 has a foreign global-switch second
                        # page. Replace that gate with our guarded transfer,
                        # preserving the visible doors6 sprite on Player Touch.
                        local_page = scripted.attrs["@pages"][0].attrs
                        local_page["@trigger"] = 1
                        local_page["@through"] = True
                        local_page["@direction_fix"] = True
                    selected[event_id] = scripted
                continue
            if original == 5 and event_id in (11, 13):
                selected[event_id] = new_event(event, oak_escort(event_id, mapping[6], lab_scene_id), 1, b"")
                continue
            if original == 5 and event_id == 12:
                oak = new_event(event, [], 0, actor(event))
                condition = oak.attrs["@pages"][0].attrs["@condition"].attrs
                condition["@self_switch_valid"] = True
                condition["@self_switch_ch"] = b"A"
                selected[event_id] = oak
                continue
            if original == 6 and event_id == 1:
                warp = extract_warps(event, mapping)
                if warp is None:
                    raise ValueError("Missing Oak laboratory exit")
                challenge = gary_challenge(events[14], event.attrs["@x"], event.attrs["@y"] - 1)
                selected[event_id] = new_event(event, [*challenge, warp], 1, b"")
                continue
            if original == 7 and event_id == 4:
                warp = extract_warps(event, mapping)
                if warp is None:
                    raise ValueError("Missing Pallet bedroom staircase")
                arrival = if_scene(b"!BlueKantoPilot.met_mom?", [
                    move_actor(13, 3, 4, 4, 18),
                    command(210, indent=1),
                    command(355, b"BlueKantoPilot.meet_mom", indent=1),
                    move_actor(13, 1, 1, 2, 17),
                    command(210, indent=1),
                ])
                selected[event_id] = new_event(event, [warp, *arrival], 1, b"")
                continue
            warp = extract_warps(event, mapping)
            if warp:
                name = text(event.attrs["@name"])
                # Automatic exits and route gateways are floor tiles. Visible doors use action.
                graphic = event.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"]
                # Only explicitly supported source door destinations survive. Import no other commands.
                character = actor(event) if graphic else b""
                is_door = "door" in name.lower() and bool(character)
                # For the audited Celadon entrance doors, keep the original
                # Player Touch semantics rather than requiring an action key.
                auto_entry = (original == 5 and event_id in (1, 2, 3)) or (
                    original == 114 and event_id in (3, 20)) or (
                    original == 144 and event_id in (5, 17, 18, 24)) or (
                    original == 168 and event_id in (6, 10, 12, 13, 14)) or (
                    original == 199 and event_id in (1, 2, 3, 5))
                trigger = 1 if auto_entry else (0 if is_door else 1)
                selected[event_id] = new_event(event, [warp], trigger, character)
        if original == 6:
            selected[lab_scene_id] = lab_arrival_scene(events, lab_scene_id)
            selected[rival_counter_id] = rival_counter_trigger(events, rival_counter_id)
        if original == 7:
            profile = new_event(events[4], [
                command(355, b"BlueKantoPilot.choose_profile"),
                command(123, b"A", 0),
            ], 3, b"")
            profile_id = max(events) + 1
            profile.attrs.update({"@id": profile_id, "@name": b"Kanto Player Profile"})
            closed = copy.deepcopy(profile.attrs["@pages"][0])
            closed.attrs["@condition"].attrs.update({"@self_switch_valid": True, "@self_switch_ch": b"A"})
            closed.attrs.update({"@trigger": 0, "@through": True, "@list": [command(0)]})
            profile.attrs["@pages"][0].attrs["@through"] = True
            profile.attrs["@pages"].append(closed)
            selected[profile_id] = profile
        map_data.attrs["@events"] = selected
        write_map(dest_file, map_data, EVENT_CLASSES)


def copy_game(game, target):
    for name in ("Audio", "Data", "Fonts", "Graphics", "PBS", "Plugins"):
        def ignore(folder, names):
            return [item for item in names if item.startswith("blue-") and item != "blue-trainer-album.dat"]
        shutil.copytree(game / name, target / name, ignore=ignore)
    for path in game.iterdir():
        if path.is_file() and (path.suffix.lower() == ".dll" or path.name in {
                "Game.exe", "Game.ini", "mkxp.json", "preload.rb", "soundfont.sf2", "Credits.txt"}):
            shutil.copyfile(path, target / path.name)


def install_pbs(preview, target, mapping):
    pbs = target / "PBS"
    draft = preview / "drafts"
    for name in ("encounters", "trainers"):
        shutil.copyfile(draft / f"{name}.txt", pbs / f"{name}_kanto.txt")
    shutil.copyfile(preview / "connections-preview.txt", pbs / "map_connections_kanto.txt")

    kinds = read_blocks(pbs / "trainer_types.txt", set(TYPES.values()))
    trainer_types = []
    for kind, base in TYPES.items():
        new_type = f"BLUE_KANTO_{kind}"
        trainer_types.extend([f"[{new_type}]", *kinds[base], ""])
        graphics = target / "Graphics/Trainers"
        sprite = graphics / f"{base}.png"
        shutil.copyfile(sprite, graphics / f"{new_type}.png")
    (pbs / "trainer_types_kanto.txt").write_text("\n".join(trainer_types), encoding="utf8")
    metadata = []
    source_keys = json_file(KANTO)["maps"]
    for source_id, map_id in mapping.items():
        metadata.extend([f"[{map_id:03}]", f"Name = {LOCATION_NAMES[source_keys[str(source_id)]]}"])
        if source_id in (5, 9, 10, 18, 24, 25, 32, 33, 39, 56, 61, 64, 72, 111, 114, 141, 143, 144, 155, 157, 159, 161, 164, 107, 168, 190, 191, 198, 199, 16, 209, 214):
            metadata.extend(["Outdoor = true", "ShowArea = true"])
        metadata.append("")
    (pbs / "map_metadata_kanto.txt").write_text("\n".join(metadata), encoding="utf8")


def install_runtime(target, mapping, game):
    presentation = target / "Plugins/ZZZZ Blue Story and Presentation"
    for name in ("RegionStart.rb", "Story.rb"):
        shutil.copyfile(ROOT / "scripts/battle_polish" / name, presentation / name)
    plugin = target / "Plugins/ZZZZZ Blue Kanto Pilot"
    plugin.mkdir()
    shutil.copyfile(ROOT / "scripts/regions/KantoPilot.rb", plugin / "KantoPilot.rb")
    (plugin / "meta.txt").write_text(
        "Name = Blue Kanto Pilot\nVersion = 1.0\nEssentials = 21.1\n"
        "Requires = Blue Battle Presentation and Story\nScripts = KantoPilot.rb\n", encoding="utf8")
    data = target / "Data"
    system = load(data / "System.rxdata")
    system.attrs.update({"@start_map_id": mapping[7], "@start_x": 25, "@start_y": 7})
    write_map(data / "System.rxdata", system, SYSTEM_CLASSES)
    infos = load(data / "MapInfos.rxdata")
    for source_id, key in json_file(KANTO)["maps"].items():
        infos[mapping[int(source_id)]].attrs["@name"] = LOCATION_NAMES[key].encode("utf8")
    write_map(data / "MapInfos.rxdata", infos)
    ini = target / "Game.ini"
    ini.write_text(re.sub(r"(?m)^Title=.*$", f"Title={SAVE_APP}", ini.read_text(encoding="utf-8-sig")), encoding="utf8")
    config = target / "mkxp.json"
    config_text = config.read_text(encoding="utf-8-sig")
    if re.search(r'(?m)^\s*"dataPath(?:App|Org)"', config_text):
        raise ValueError("The base already defines a custom save directory in mkxp.json.")
    isolated = json.dumps({"dataPathApp": SAVE_APP, "dataPathOrg": SAVE_ORG})[1:-1]
    config_text = config_text.replace("{", "{\n  " + isolated + ",", 1)
    config_text = re.sub(r'(?m)^(\s*"windowTitle"\s*:).*$', r'\1 "Pokémon Blue — Piloto de Kanto",', config_text)
    config.write_text(config_text, encoding="utf8")
    # The standalone pilot must always select Kanto automatically on a new
    # game. The main installation uses this marker only after explicit import.
    (data / "blue-kanto-start.txt").write_text(
        f"BLUE_KANTO_START_V1,KANTO,{mapping[7]},25,7\n", encoding="ascii"
    )
    # Experimental shortcuts are available ONLY in this isolated pilot;
    # install_kanto.py never imports this file into the main campaign.
    stops = [
        ("PALLET", "Pallet Town (Oak)", 5, 28, 14),
        ("PLAYER_HOME", "Casa do jogador (inicio)", 7, 25, 7),
        ("VIRIDIAN", "Viridian City (Ginasio)", 10, 36, 11),
        ("VIR_GYM", "Ginasio Viridian Giovanni (sete insignias)", 13, 17, 22),
        ("PEWTER", "Pewter City (Gym)", 25, 19, 21),
        ("ROUTE4", "Route 4 (Mt Moon exit)", 33, 92, 21),
        ("MOON_CENTER", "Mt Moon Pokemon Center", 34, 7, 8),
        ("MOON_1F", "Mt Moon - 1F", 36, 24, 41),
        ("MOON_B1F", "Mt Moon - B1F", 37, 25, 8),
        ("MOON_B2F", "Mt Moon - B2F", 38, 31, 24),
        ("CERULEAN", "Cerulean City (Center)", 39, 22, 20),
        ("MISTY", "Cerulean Gym (Misty)", 42, 8, 18),
        ("ROUTE5", "Route 5 (Underground)", 56, 31, 32),
        ("ROUTE6", "Route 6 (Underground)", 61, 35, 13),
        ("VERMILION", "Vermilion City (Center)", 64, 19, 7),
        ("SURGE", "Vermilion Gym (Lt. Surge)", 67, 5, 19),
        ("HARBOR", "Vermilion Harbor", 72, 9, 7),
        ("SSANNE", "S.S. Anne (1F)", 74, 20, 2),
        ("SSCAPTAIN", "S.S. Anne (Captain)", 76, 4, 8),
        ("SSDECK", "S.S. Anne (Deck)", 78, 58, 3),
        # Phase 09: verified incoming warp coordinates; preview maps have NO events.
        ("ROUTE7", "Rota 7 (cenario, sem eventos)", 111, 15, 25),
        ("CELADON", "Celadon City (cenario)", 114, 48, 17),
        ("ERIKA", "Ginasio Celadon (Erika, sem batalha)", 124, 6, 18),
        ("CEL_CENTER", "Celadon Center (cenario)", 115, 7, 8),
        ("CEL_STORE", "Celadon Loja 1F (cenario)", 117, 2, 14),
        # Phase 10: audited incoming warp coordinates. Core Fuchsia and Koga active.
        ("FUCHSIA", "Fuchsia City (Centro e Ginásio ativos)", 144, 25, 36),
        ("KOGA", "Ginasio Fuchsia Koga (batalha experimental)", 147, 7, 21),
        ("FUCH_CENTER", "Fuchsia Centro Pokemon (cura)", 145, 7, 8),
        ("FUCH_MART", "Fuchsia Mart (loja)", 146, 4, 7),
        ("FUCH_WARDEN", "Casa Warden (cenario)", 152, 6, 9),
        ("SAF_GATE", "Safari Zone Portao (entrada bloqueada)", 153, 4, 7),
        ("SAF_SOUTH", "Safari Zone Sul (cenario)", 155, 26, 31),
        ("SAF_NORTH", "Safari Zone Norte (cenario)", 159, 25, 6),
        ("SAF_WEST", "Safari Zone Oeste (cenario)", 161, 14, 9),
        ("ROUTE15", "Rota 15 (cenario)", 164, 16, 25),
        # Phase 11: only audited incoming-warp coordinates, geometry only.
        ("ROUTE8", "Rota 8 (cenario)", 107, 3, 25),
        ("SAFF_WEST", "Portaria Oeste Saffron (cenario)", 112, 11, 5),
        ("SAFFRON", "Saffron City (Centro, Ginasio e Silph)", 168, 28, 4),
        ("SABRINA", "Ginasio Sabrina (Marsh apos Silph)", 171, 15, 23),
        ("SAFF_DOJO", "Fighting Dojo (batalhas)", 172, 5, 13),
        ("SAFF_CENTER", "Saffron Centro Pokemon (cura)", 169, 7, 8),
        ("SILPH_1F", "Silph Co. 1F (escadas)", 178, 8, 20),
        ("SILPH_5F", "Silph Co. 5F (Card Key)", 182, 28, 2),
        ("SILPH_11F", "Silph Co. 11F (Giovanni)", 188, 7, 2),
        ("SILPH_LIFT", "Silph Co. Elevador (local)", 189, 2, 5),
        # Phase 12: source-proven incoming coordinates, isolated pilot only.
        ("ROUTE19", "Rota 19 (cenario aquático)", 190, 11, 24),
        ("ROUTE20", "Rota 20 (cenario aquático)", 191, 72, 55),
        ("SEAFOAM", "Seafoam 1F (cenario, puzzles pendentes)", 193, 11, 24),
        ("CINNABAR", "Cinnabar Island (Centro, Mart e Mansion)", 199, 26, 12),
        ("CIN_CENTER", "Cinnabar Centro Pokémon (cura)", 200, 7, 8),
        ("CIN_GYM", "Ginasio Cinnabar Blaine (Secret Key)", 202, 25, 23),
        ("CIN_LAB", "Laboratorio Cinnabar (sem revival)", 203, 4, 9),
        ("MANSION", "Pokémon Mansion 1F (estátuas)", 205, 8, 33),
        ("MANSION_B1F", "Pokémon Mansion B1F (Secret Key)", 208, 6, 7),
        # Phase 14: source-proven indoor arrival tiles. These test shortcuts
        # never bypass the actual in-room League progress guards.
        ("ROUTE22", "Route 22 (Plateau Gate)", 16, 14, 10),
        ("ROUTE23", "Route 23 (oito guardas)", 209, 14, 153),
        ("ROAD_1F", "Victory Road 1F (mecanismos)", 211, 18, 25),
        ("ROAD_2F", "Victory Road 2F (treinadores)", 212, 8, 14),
        ("INDIGO", "Indigo Plateau", 214, 17, 7),
        ("LEAGUE", "Indigo Lobby (Elite Four)", 215, 11, 16),
        ("LORELEI", "Elite Four Lorelei (primeira sala)", 216, 6, 12),
        ("LANCE", "Elite Four Lance (quarta sala)", 219, 23, 10),
        ("CHAMPION", "Campeao Blue (final)", 220, 7, 19),
        ("HALL", "Hall of Fame Kanto (conclusao)", 221, 5, 12),
    ]
    (data / "blue-kanto-experimental-stops.txt").write_text(
        "".join(f"{code}|{title}|{mapping[old]}|{x}|{y}|2\n"
                for code, title, old, x, y in stops), encoding="utf-8"
    )
    (data / "blue-kanto-silph-floors.txt").write_text(
        "".join(f"{floor}|{mapping[source]}|{x}|{y}|2\n"
                for floor, (source, (x, y)) in enumerate(SILPH_FLOOR_LANDINGS.items(), 1)),
        encoding="ascii",
    )
    # Force compiler to consume new PBS, but keep a real release-mode title after the first boot.
    (data / "blue-compile-request.txt").write_text("compile", encoding="ascii")
    (data / "PluginScripts.rxdata").unlink(missing_ok=True)
    (target / PILOT_META).write_text(json.dumps({
        "save_app": SAVE_APP, "save_org": SAVE_ORG,
        "maps": mapping, "build_signature": build_signature(),
        "base_data_sha256": {
            name: hashlib.sha256((game / "Data" / name).read_bytes()).hexdigest()
            for name in ("MapInfos.rxdata", "Tilesets.rxdata")
        },
    }), encoding="utf8")
    # Only the isolated copy receives the generated Kanto soundtrack scope.
    from scripts.music.compile_kanto_music import compile_bytes
    compiled, _ = compile_bytes(ROOT, target, mapping)
    (data / "blue-kanto-music.txt").write_bytes(compiled)


def build(source, game, output):
    output = output.resolve()
    work = (ROOT / ".blue-work").resolve()
    if not output.is_relative_to(work) or output == work or output.exists():
        raise ValueError("Choose a new pilot directory inside .blue-work.")
    if not (game / "Game.exe").is_file():
        raise ValueError("Install and prepare the Blue game first.")
    if not (game / "Plugins/ZZZZ Blue Story and Presentation/Regions.rb").is_file():
        raise ValueError("Prepare the installed Blue game with scripts/launch_game.py --prepare-only first.")
    if not (source / "Data/MapInfos.rxdata").is_file():
        raise ValueError("The editable Essentials FRLG 1.1 project was not found. See docs/CIRCUITO_REGIONAL.md.")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".kanto-build-", dir=output.parent) as tmp:
        preview, target = Path(tmp) / "preview", Path(tmp) / "game"
        plan = stage(ROOT, source, game, preview)
        mapping = {row["source_id"]: row["proposed_id"] for row in plan["maps"]}
        target.mkdir()
        copy_game(game, target)
        for folder in ("Data", "Graphics"):
            shutil.copytree(preview / folder, target / folder, dirs_exist_ok=True)
        install_events(source, target, mapping)
        install_pbs(preview, target, mapping)
        # Copy approved F2/F3 BGM and six confirmed F4 ME in this isolated pilot.
        # Hash verification and exclusive copy protect the original game audio.
        from scripts.music.compile_kanto_music import approved_audio_track_numbers
        from scripts.music.install_kanto_music import install as install_kanto_audio
        install_kanto_audio(target, apply=True, numbers=approved_audio_track_numbers(ROOT))
        install_runtime(target, mapping, game)
        if output.exists():
            raise ValueError("Another pilot already exists at the output path.")
        target.rename(output)
    return output


def launch(output):
    if not (output / PILOT_META).is_file() or not (output / "Game.exe").is_file():
        raise ValueError("This directory is not a prepared Kanto pilot.")
    subprocess.Popen([str(output / "Game.exe")], cwd=output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--game", type=Path, default=ROOT / "game")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--launch", action="store_true")
    args = parser.parse_args()
    output = args.output.resolve()
    if args.launch and output.exists() and not pilot_is_current(output):
        replacement = revised_path(output)
        print(f"[INFO] Piloto antigo detectado; preservando {output}", flush=True)
        print(f"[INFO] Preparando nova copia: {replacement}", flush=True)
        output = replacement
    if not args.launch or not output.exists():
        build(args.source.resolve(), args.game.resolve(), output)
        print(f"Piloto de Kanto preparado em {output}")
    if args.launch:
        launch(output)


if __name__ == "__main__":
    main()
