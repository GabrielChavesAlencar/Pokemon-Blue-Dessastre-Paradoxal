"""Prepare reviewable Kanto PBS fragments from the FRLG kit, never the live PBS."""
import re
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
                levels = list(map(int, fields[2:]))
                if not 0 < weight <= 100 or not all(1 <= n <= 100 for n in levels):
                    raise ValueError(f"Invalid encounter weight or level in map {key}")
                # Essentials stores an inclusive min/max range. Do not fill gaps
                # in a source encounter's levels without an explicit decision.
                if levels != list(range(levels[0], levels[-1] + 1)):
                    raise ValueError(f"Non-contiguous encounter range in pilot map {key}: {line}")
                methods[method][1].append([weight, fields[1], levels[0], levels[-1]])
        for method, (_, entries) in methods.items():
            if sum(row[0] for row in entries) != 100:
                raise ValueError(f"Encounter weights must total 100: {key}/{method}")
        tables[dst_id, version] = methods
    out = []
    for (map_id, version), methods in sorted(tables.items()):
        out.append(f"[{map_id:03d}" + (f",{version}" if version else "") + "]")
        for header, entries in methods.values():
            out.append(",".join(header))
            out.extend("    " + ",".join(map(str, row)) for row in entries)
        out.append("")
    return "\n".join(out), len(tables)


def trainer_draft(path, species, moves):
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
            elif field != "LoseText":
                raise ValueError(f"Field {field} in {original} requires manual review.")
            out.append(line)
        if not 1 <= roster <= 6:
            raise ValueError(f"Invalid roster size: {original}")
        out.append("")
    return "\n".join(out)


def build_drafts(source, game, plan):
    species, moves = catalogue(game, "pokemon"), catalogue(game, "moves")
    mapping = {row["source_id"]: row["proposed_id"] for row in plan["maps"]}
    encounters, count = normalize_encounters(source / "PBS/encounters.txt", mapping, species)
    trainers = trainer_draft(source / "PBS/trainers.txt", species, moves)
    plan["drafts"] = {"encounter_tables": count, "trainer_profiles": len(TRAINERS),
                      "source_policy": "Essentials FRLG merged tables; independent official verification pending"}
    warning = "# REVIEW ONLY. Not loaded by the game. Source: Essentials FRLG 1.1.\n"
    return {Path("drafts", "encounters.txt"): (warning + encounters).encode("utf-8"),
            Path("drafts", "trainers.txt"): (warning + trainers).encode("utf-8")}
