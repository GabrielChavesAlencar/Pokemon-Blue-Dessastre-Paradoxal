"""Prepare reviewable Kanto PBS fragments from the FRLG kit, never the live PBS."""
import re
from math import lcm
from pathlib import Path

HEADER = re.compile(r"^\[([^]]+)]\s*(?:#.*)?$")
# Extended Gen 9/Essentials encounter variants used inside Mt. Moon.
ENCOUNTER_TYPES = {
    "Land", "LandMorning", "LandDay", "LandAfternoon", "LandEvening", "LandNight",
    "Cave", "CaveMorning", "CaveDay", "CaveAfternoon", "CaveEvening", "CaveNight",
    "Water", "WaterMorning", "WaterDay", "WaterNight",
    "OldRod", "GoodRod", "SuperRod", "RockSmash",
}
# Source keys stay attached to the original roster. Destination names are stable.
TRAINERS = {
    "RIVAL1,Blue,11": ("RIVAL", "Blue", 11),
    "RIVAL1,Blue,12": ("RIVAL", "Blue", 12),
    "RIVAL1,Blue,13": ("RIVAL", "Blue", 13),
    "BUGCATCHER,Rick": ("BUGCATCHER", "Rick", 0),
    "BUGCATCHER,Doug": ("BUGCATCHER", "Doug", 0),
    "BUGCATCHER,Anthony": ("BUGCATCHER", "Anthony", 0),
    "BUGCATCHER,Charlie": ("BUGCATCHER", "Charlie", 0),
    "BUGCATCHER,Sammy": ("BUGCATCHER", "Sammy", 0),
    "CAMPER,Liam": ("CAMPER", "Liam", 0),
    "LEADER_Brock,Brock": ("LEADER", "Brock", 0),
}
# Verified against FRLG Map32 / Map36 / Map38 / Map42 source event calls.
TRAINERS.update({
    "LASS,Janice": ("LASS", "Janice", 0),
    "BUGCATCHER,Colton": ("BUGCATCHER", "Colton", 0),
    "YOUNGSTER,Ben": ("YOUNGSTER", "Ben", 0),
    "LASS,Sally": ("LASS", "Sally", 0),
    "BUGCATCHER,Greg": ("BUGCATCHER", "Greg", 0),
    "BUGCATCHER,James": ("BUGCATCHER", "James", 0),
    "YOUNGSTER,Calvin": ("YOUNGSTER", "Calvin", 0),
    "LASS,Robin": ("LASS", "Robin", 0),
    "LASS,Iris": ("LASS", "Iris", 0),
    "BUGCATCHER,Kent": ("BUGCATCHER", "Kent", 0),
    "BUGCATCHER,Robby": ("BUGCATCHER", "Robby", 0),
    "SUPERNERD,Jovan": ("SUPERNERD", "Jovan", 0),
    "LASS,Miriam": ("LASS", "Miriam", 0),
    "YOUNGSTER,Josh": ("YOUNGSTER", "Josh", 0),
    "HIKER,Marcos": ("HIKER", "Marcos", 0),
    "TEAMROCKET_M,Grunt,1": ("ROCKET", "Grunt", 1),
    "TEAMROCKET_M,Grunt,2": ("ROCKET", "Grunt", 2),
    "TEAMROCKET_M,Grunt,3": ("ROCKET", "Grunt", 3),
    "TEAMROCKET_M,Grunt,4": ("ROCKET", "Grunt", 4),
    "SUPERNERD,Miguel": ("SUPERNERD", "Miguel", 0),
    "LEADER_Misty,Misty": ("LEADER_MISTY", "Misty", 0),
    "SWIMMER2_M,Luis": ("SWIMMER", "Luis", 0),
    "PICNICKER,Diana": ("PICNICKER", "Diana", 0),
})


# Phase 08: source IDs, names and event anchors audited in the pinned FRLG kit.
# Team data are copied from the source PBS; no levels or moves are fabricated.
TRAINERS.update({
    **{f"{kind},{name}": (dest, name, 0)
       for kind, dest, names in (
           ("BUGCATCHER", "BUGCATCHER", ("Keigo", "Elijah")),
           ("PICNICKER", "PICNICKER", ("Nancy", "Isabelle")),
           ("CAMPER", "CAMPER", ("Ricky", "Jeff")),
           ("SAILOR", "SAILOR", ("Dwayne", "Phillip", "Huey",
                                "Dylan", "Duncan", "Leonard", "Trevor", "Edmond")),
           ("ENGINEER", "ENGINEER", ("Bailey",)),
           ("GENTLEMAN", "GENTLEMAN", ("Tucker", "Thomas", "Arthur",
                                      "Brooks", "Lamar")),
           ("FISHERMAN", "FISHERMAN", ("Dale", "Barny")),
           ("LASS", "LASS", ("Ann", "Dawn")),
           ("YOUNGSTER", "YOUNGSTER", ("Tyler",)),
           ("LEADER_LtSurge", "LEADER_SURGE", ("Lt. Surge",)),
       )
       for name in names},
})



# Celadon Gym source identities and teams audited from the pinned FRLG
# Map124 and PBS/trainers.txt. Individual Pokémon/moves/levels remain sourced.
TRAINERS.update({
    "LEADER_Erika,Erika": ("LEADER_ERIKA", "Erika", 0),
    "PICNICKER,Tina": ("PICNICKER", "Tina", 0),
    "LASS,Kay": ("LASS", "Kay", 0),
    "BEAUTY,Bridget": ("BEAUTY", "Bridget", 0),
    "BEAUTY,Tamia": ("BEAUTY", "Tamia", 0),
    "BEAUTY,Lori": ("BEAUTY", "Lori", 0),
    "LASS,Lisa": ("LASS", "Lisa", 0),
    "COOLTRAINER_F,Mary": ("COOLTRAINER_F", "Mary", 0),
})


# Fuchsia Gym Map147: six sight trainers + Koga. Teams/levels/moves
# are copied verbatim from the pinned source's selected PBS trainer blocks.
TRAINERS.update({
    "LEADER_Koga,Koga": ("LEADER_KOGA", "Koga", 0),
    "JUGGLER,Nate": ("JUGGLER", "Nate", 0),
    "JUGGLER,Kayden": ("JUGGLER", "Kayden", 0),
    "JUGGLER,Kirk": ("JUGGLER", "Kirk", 0),
    "JUGGLER,Shawn": ("JUGGLER", "Shawn", 0),
    "TAMER,Edgar": ("TAMER", "Edgar", 0),
    "TAMER,Phil": ("TAMER", "Phil", 0),
})



# Saffron gym, Fighting Dojo and Silph Co. PBS identities audited from
# the pinned FRLG 1.1 source. Preserve real versions, levels and moves.
TRAINERS.update({
    "LEADER_Sabrina,Sabrina": ("LEADER_SABRINA", "Sabrina", 0),
    **{f"PSYCHIC_M,{name}": ("PSYCHIC", name, 0)
       for name in ("Cameron", "Preston", "Johan", "Tyron")},
    **{f"CHANNELER,{name}": ("CHANNELER", name, 0)
       for name in ("Tasha", "Stacy", "Amanda")},
    **{f"BLACKBELT,{name}": ("BLACKBELT", name, 0)
       for name in ("Hideki", "Hitoshi", "Aaron", "Mike", "Koichi")},
    **{f"TEAMROCKET_M,Grunt,{version}": ("ROCKET", "Grunt", version)
       for version in range(21, 40)},
    "ROCKETBOSS,Giovanni,2": ("ROCKETBOSS", "Giovanni", 2),
    **{f"RIVAL2,Blue,{version}": ("RIVAL_SILPH", "Blue", version)
       for version in (51, 52, 53)},
})


# Phase 12: verified FRLG Map202 gym and Mansion Map205-208 trainers.
# PBS supplies the original species, move sets and levels. Do not fake teams.
TRAINERS.update({
    "LEADER_Blaine,Blaine": ("LEADER_BLAINE", "Blaine", 0),
    **{f"BURGLAR,{name}": ("BURGLAR", name, 0)
       for name in ("Quinn", "Ramon", "Dusty", "Arnie", "Simon", "Lewis")},
    **{f"SUPERNERD,{name}": ("SUPERNERD", name, 0)
       for name in ("Erik", "Avery", "Derek", "Zac")},
    **{f"SCIENTIST,{name}": ("SCIENTIST", name, 0)
       for name in ("Ted", "Braydon", "Ivan")},
    "YOUNGSTER,Johnson": ("YOUNGSTER", "Johnson", 0),
})

# Stage 13 / FRLG Map013. Exact source PBS rosters, levels and moves; the
# native trainer script for Jason incorrectly calls Cole, so match the event
# name and the dedicated existing [TAMER,Jason] PBS record instead.
TRAINERS.update({
    "LEADER_Giovanni,Giovanni": ("LEADER_GIOVANNI", "Giovanni", 0),
    **{f"BLACKBELT,{name}": ("BLACKBELT", name, 0)
       for name in ("Takashi", "Kiyo", "Atsushi")},
    **{f"COOLTRAINER_M,{name}": ("COOLTRAINER_M", name, 0)
       for name in ("Samuel", "Yuji", "Warren")},
    **{f"TAMER,{name}": ("TAMER", name, 0)
       for name in ("Cole", "Jason")},
})


# Phase 14 source PBS teams. Elite Four and Champion retain exact FRLG
# species/levels/moves, including all three Champion starter variants.
TRAINERS.update({
    "ELITEFOUR_Lorelei,Lorelei": ("ELITE_LORELEI","Lorelei",0),
    "ELITEFOUR_Bruno,Bruno": ("ELITE_BRUNO","Bruno",0),
    "ELITEFOUR_Agatha,Agatha": ("ELITE_AGATHA","Agatha",0),
    "ELITEFOUR_Lance,Lance": ("ELITE_LANCE","Lance",0),
    **{f"CHAMPION,Blue,{version}": ("CHAMPION_BLUE","Blue",version)
       for version in (1,2,3)},
    **{f"COOLTRAINER_F,{name}": ("COOLTRAINER_F", name, 0)
       for name in ("Naomi","Alexa","Caroline")},
    **{f"COOLTRAINER_M,{name}": ("COOLTRAINER_M", name, 0)
       for name in ("Rolando","George","Colby")},
    **{f"JUGGLER,{name}": ("JUGGLER", name, 0)
       for name in ("Nelson","Gregory")},
    "BLACKBELT,Daisuke": ("BLACKBELT","Daisuke",0),
    "TAMER,Vincent": ("TAMER","Vincent",0),
    "POKEMANIAC,Dawson": ("POKEMANIAC","Dawson",0),
    "COOLCOUPLE,Ray & Tyra": ("COOLCOUPLE","Ray & Tyra",0),
})

def read_blocks(path, selected=None):
    blocks = {}
    key = None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        if header := HEADER.fullmatch(line.strip()):
            key = header[1] if selected is None or header[1] in selected else None
            if key is None:
                continue
            if key in blocks:
                raise ValueError(f"Duplicate PBS section {key}: {path.name}")
            blocks[key] = []
        elif key is not None and line.strip() and not line.lstrip().startswith("#"):
            blocks[key].append(line)
    return blocks


def catalogue(game, prefix):
    keys = set()
    for path in (game / "PBS").glob(prefix + "*.txt"):
        for line in path.read_text(encoding="utf-8-sig", errors="replace").splitlines():
            if header := HEADER.fullmatch(line.strip()):
                keys.add(header[1])
    return keys


def normalize_encounters(source, rows, species):
    tables = {}
    for key, lines in read_blocks(source).items():
        old_id, _, version = key.partition(",")
        old_id = int(old_id)
        if old_id not in rows:
            continue
        dst_id = rows[old_id]
        if (dst_id, version) in tables:
            raise ValueError(f"Duplicate encounter table {key}")
        methods = {}
        method = None
        for line in lines:
            fields = [s.strip() for s in line.split("#", 1)[0].strip().split(",")]
            if not fields[0].isdigit():
                method = fields[0]
                if method not in ENCOUNTER_TYPES or method in methods or len(fields) > 2:
                    raise ValueError(f"Unsupported encounter method {fields[0]}")
                methods[method] = (fields, [])
            else:
                if method is None or len(fields) < 3 or fields[1] not in species:
                    raise ValueError(f"Invalid encounter {line} in map {key}")
                weight = int(fields[0])
                # This particular source kit lists EVERY possible level:
                # "45,SPEAROW,3,5" means levels {3,5}, not a min/max pair.
                # Long explicit lists (e.g. 5..40) are common in its PBS.
                levels = [int(v) for v in fields[2:]]
                if (not 0 < weight <= 100 or not levels or
                    not all(1 <= n <= 100 for n in levels)):
                    raise ValueError(f"Invalid source encounter in map {key}: {line}")
                # Keep the authored order and even repeated levels, since
                # repetitions change the source's relative level probabilities.
                methods[method][1].append([weight, fields[1], levels])
        for encounter_method, (_, original_slots) in methods.items():
            if sum(row[0] for row in original_slots) != 100:
                raise ValueError(f"Encounter weights must total 100: {key}/{encounter_method}")
            # Expand only discontinuous level lists into single-level slots.
            # Relative probabilities are preserved EXACTLY with integer
            # scaling by the LCM of their level counts; vanilla Essentials
            # has no syntax for an arbitrary discrete set in one slot.
            scale = 1
            for chance, ident, levels in original_slots:
                if levels != list(range(levels[0], levels[-1] + 1)):
                    scale = lcm(scale, len(levels))
            converted = []
            for chance, ident, levels in original_slots:
                consecutive = levels == list(range(levels[0], levels[-1] + 1))
                targets = [(levels[0], levels[-1], chance * scale)] if consecutive else [
                    (level, level, chance * scale // len(levels)) for level in levels
                ]
                for low, high, units in targets:
                    # Each generated PBS chance must fit an Essentials entry
                    # (1–100). Duplicate the SAME range to represent >100,
                    # never round the probability or create new level values.
                    while units:
                        weight = min(units, 100)
                        converted.append([weight, ident, low, high])
                        units -= weight
                    if len(converted) > 4096:
                        raise ValueError(
                            f"Exact source level distribution needs too many slots: {key}/{encounter_method}"
                        )
            methods[encounter_method] = (methods[encounter_method][0], converted)
        tables[dst_id, version] = methods
    out = []
    for (map_id, version), methods in sorted(tables.items()):
        out.append(f"[{map_id:03d}" + (f",{version}" if version else "") + "]")
        for header, entries in methods.values():
            out.append(",".join(header))
            out.extend("    " + ",".join(map(str, row)) for row in entries)
        out.append("")
    return "\n".join(out), len(tables)


def trainer_draft(path, species, moves, items):
    blocks = read_blocks(path, TRAINERS)
    out = []
    for original, (kind, name, version) in TRAINERS.items():
        # This type needs a proper trainer type/graphic when the events are wired.
        dest_type = f"BLUE_KANTO_{kind}"
        out.extend([f"# Source: [{original}]", f"[{dest_type},{name},{version}]"])
        roster = 0
        for line in blocks[original]:
            field, _, value = line.partition("=")
            field, value = field.strip(), value.strip()
            if field == "Pokemon":
                ident, level = [x.strip() for x in value.split(",")]
                if ident not in species or not 1 <= int(level) <= 100:
                    raise ValueError(f"Unknown Pokémon or level in {original}: {value}")
                roster += 1
            elif field == "Moves":
                if any(move.strip() not in moves for move in value.split(",")):
                    raise ValueError(f"Unknown move in {original}: {value}")
            elif field == "Item":
                # Held item on this trainer's Pokémon: preserve native PBS value
                # only when Decades already knows the exact item identifier.
                if value not in items:
                    raise ValueError(f"Unknown held item in {original}: {value}")
            elif field != "LoseText":
                raise ValueError(f"Field {field} in {original} requires manual review.")
            out.append(line)
        if not 1 <= roster <= 6:
            raise ValueError(f"Invalid roster size: {original}")
        out.append("")
    return "\n".join(out)


def build_drafts(source, game, plan):
    species, moves, items = (catalogue(game, "pokemon"), catalogue(game, "moves"),
                             catalogue(game, "items"))
    # Enable source-derived wild tables only on functional maps; ALL 45
    # geometry-only previews remain protected. Route 22/23, Victory Road,
    # Fuchsia, Cinnabar, Saffron, etc. can now retain their actual FRLG
    # inclusive level ranges instead of being rejected as "non-contiguous".
    # This does not grant access to maps/events still gated by story/HMs.
    from audit import KANTO, json_file
    no_gameplay = set(json_file(KANTO).get("preview_only", []))
    mapping = {row["source_id"]: row["proposed_id"] for row in plan["maps"]
               if row["source_id"] not in no_gameplay}
    encounters, count = normalize_encounters(source / "PBS/encounters.txt", mapping, species)
    trainers = trainer_draft(source / "PBS/trainers.txt", species, moves, items)
    plan["drafts"] = {"encounter_tables": count, "trainer_profiles": len(TRAINERS),
                      "source_policy": "Essentials FRLG 1.1 tables; inclusive min/max and exact source weights; official FireRed/LeafGreen version exclusivities not independently verified"}
    warning = "# REVIEW ONLY. Not loaded by the game. Source: Essentials FRLG 1.1.\n"
    return {Path("drafts", "encounters.txt"): (warning + encounters).encode("utf-8"),
            Path("drafts", "trainers.txt"): (warning + trainers).encode("utf-8")}
