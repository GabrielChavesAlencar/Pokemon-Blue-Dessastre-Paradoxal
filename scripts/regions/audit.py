"""Read regional source projects without running any Ruby or changing the game."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from server.ruby_marshal import loads, text

REGISTRY = ROOT / "site/public/data/regions.json"
KANTO = ROOT / "data/regions/kanto-source.json"
MAP_NAME = re.compile(r"Map(\d+)\.rxdata", re.I)
BADGE = re.compile(r"^\$player\.badges\[(\d+)\]\s*=\s*true$")
DIRECTION = {"North": "South", "South": "North", "West": "East", "East": "West"}
# The original 13-map pilot used these source IDs in this order. Keep their
# destination slots stable when adding Mt. Moon/Cerulean, so old Kanto save
# coordinates continue to refer to the same area in future integrations.
PILOT_V1_SOURCE_IDS = (5, 6, 7, 9, 10, 11, 12, 18, 19, 20, 24, 25, 28)


# Freeze the phase-10 order: earlier saves and map transfers refer to these
# assigned Kanto IDs. Appending later source maps by their raw numeric order
# would shift prior ids (e.g. new Saffron gates have source IDs below Fuchsia).
KANTO_PHASE10_SOURCE_IDS = (
    5, 6, 7, 9, 10, 11, 12, 18, 19, 20, 24, 25, 28,
    26, 27, 32, 33, 34, 36, 37, 38, 39, 40, 41,
    42, 56, 59, 60, 61, 63, 64, 65, 66, 67, 72,
    74, 75, 76, 77, 78, 111, 114, 115, 117, 118, 119,
    120, 121, 122, 123, 124, 141, 142, 143, 144, 145, 146,
    147, 152, 153, 155, 156, 157, 158, 159, 160, 161, 162,
    163, 164, 165,
)


# Preserve the order of the first 29 Saffron preview maps too. The Club
# House (source 173) was discovered after the initial preview was published;
# append it rather than shifting the existing 174-189 slots.
KANTO_PHASE11_EARLY_SOURCE_IDS = (
    57, 62, 107, 108, 109, 110, 112, 113, 168, 169,
    170, 171, 172, 174, 175, 176, 177, 178, 179, 180,
    181, 182, 183, 184, 185, 186, 187, 188, 189,
    173,  # Late-discovered Saffron Fan Club; keep its already published slot.
)


# Eight interiors appended after the Saffron preview. Preserve every one of
# the 109 source-to-destination slots allocated before phase 12.
KANTO_PHASE11_LATE_SOURCE_IDS = (8, 14, 15, 21, 22, 29, 30, 31)


def stable_source_order(wanted):
    chosen = set(wanted)
    stable = (*KANTO_PHASE10_SOURCE_IDS, *KANTO_PHASE11_EARLY_SOURCE_IDS,
              *KANTO_PHASE11_LATE_SOURCE_IDS)
    result = [source for source in stable if source in chosen]
    result.extend(sorted(chosen - set(stable)))
    return result



def load(path):
    return loads(path.read_bytes())


def json_file(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def inventory(game):
    data = game / "Data"
    infos = load(data / "MapInfos.rxdata")
    maps = {}
    for path in data.iterdir():
        match = MAP_NAME.fullmatch(path.name)
        if match:
            key = int(match[1])
            if key in maps:
                raise ValueError(f"Map ID duplicated on disk: {key}")
            maps[key] = path
    return infos, maps


def commands(map_data):
    for event_id, event in sorted(map_data.attrs["@events"].items()):
        for page_id, page in enumerate(event.attrs["@pages"], 1):
            for line, command in enumerate(page.attrs["@list"], 1):
                yield event_id, page_id, line, command.attrs


def check_decades(game, registry):
    """Audit the ending in the installed copy, including exclusivity of its switch."""
    infos, files = inventory(game)
    ending = registry["decades"]["league"]
    expected = {row["badge"]: (row["map"], row["event"]) for row in registry["decades"]["milestones"]}
    expected[ending["badge"]] = ending["map"], ending["event"]
    badges = {key: set() for key in expected}
    switch_sites = set()
    ending_branches = []
    for map_id, path in sorted(files.items()):
        data = load(path)
        by_page = {}
        for event, page, line, row in commands(data):
            code, params = row["@code"], row["@parameters"]
            if code == 121 and params[0] <= ending["switch"] <= params[1]:
                switch_sites.add((map_id, event, tuple(params)))
            if code in (355, 655) and params:
                match = BADGE.fullmatch(text(params[0]).strip())
                if match and int(match[1]) in badges:
                    badges[int(match[1])].add((map_id, event))
            if (map_id, event) == expected[ending["badge"]]:
                by_page.setdefault(page, []).append(row)
        for page in by_page.values():
            for i, row in enumerate(page):
                if row["@code"] != 355 or row["@parameters"] != [b"pbHallOfFameEntry"]:
                    continue
                indent = row["@indent"]
                if i + 1 >= len(page):
                    continue
                later = page[i + 1]
                # Decades exits the loss branch before awarding the Stellar Emerald.
                award = f"$player.badges[{ending['badge']}] = true".encode()
                earlier = page[max(0, i - 65):i]
                if not (later["@indent"] == indent and later["@code"] == 121
                        and later["@parameters"] == [ending["switch"], ending["switch"], 0]
                        and any(c["@indent"] == indent and c["@code"] == 655
                                and c["@parameters"] == [award] for c in earlier)):
                    continue
                # Find the victory conditional and its explicit exit on loss.
                for j in range(len(earlier) - 7, -1, -1):
                    c = earlier[j]
                    if c["@indent"] < indent:
                        break
                    p = c["@parameters"]
                    if (c["@code"] == 111 and c["@indent"] == indent and len(p) == 2
                            and p[0] == 12 and re.match(r'^TrainerBattle\.start\(:\w+,\s*"Danny(?:[ (])', text(p[1]))
                            and [(x["@code"], x["@indent"] - indent) for x in earlier[j+1:j+6]]
                                == [(0, 1), (411, 0), (115, 1), (0, 1), (412, 0)]):
                        ending_branches.append(text(p[1]))
                        break
    verified = (bool(ending_branches)
                and switch_sites == {(ending["map"], ending["event"], (ending["switch"], ending["switch"], 0))}
                and badges[ending["badge"]] == {expected[ending["badge"]]})
    return {"map_count": len(files), "max_id": max(files, default=0),
            "orphan_files": sorted(files.keys() - infos.keys()), "missing_files": sorted(infos.keys() - files.keys()),
            "league_verified": verified, "league_branches": ending_branches,
            "native_milestones": [badge for badge, source in expected.items()
                                  if badge != ending["badge"] and badges[badge] == {source}]}


def map_plan(source, game, manifest):
    infos, files = inventory(source)
    dest_infos, dest_files = inventory(game)
    source_system = load(source / "Data/System.rxdata").attrs
    dest_system = load(game / "Data/System.rxdata").attrs
    wanted = {int(key): "KANTO_" + value for key, value in manifest["maps"].items()}
    if not wanted.keys() <= (infos.keys() & files.keys()):
        raise ValueError("Source is missing one or more pilot maps.")
    # Three digits is the supported project tooling range, not a claimed engine maximum.
    free = iter(n for n in range(max(300, max(dest_infos.keys() | dest_files.keys(), default=0) + 1), 1000) if n not in dest_infos and n not in dest_files)
    ids = {n: next(free, None) for n in stable_source_order(wanted)}
    if None in ids.values():
        raise ValueError("No free map IDs in the supported 1–999 range.")
    tilesets = load(source / "Data/Tilesets.rxdata")
    metadata = (source / "PBS/map_metadata.txt").read_text(encoding="utf-8-sig")
    metadata_rows = {int(n): block for n, block in re.findall(r"(?ms)^\[(\d+)\]([^\[]*)", metadata)}
    encounters = (source / "PBS/encounters.txt").read_text(encoding="utf-8-sig")
    encounter_ids = {int(n) for n in re.findall(r"(?m)^\[(\d+)(?:,\d+)?\]", encounters)}
    pbs = (source / "PBS/map_connections.txt").read_text(encoding="utf-8-sig")
    internal, external = [], []
    for line in pbs.splitlines():
        row = line.split("#", 1)[0].strip()
        if not row:
            continue
        a, side_a, off_a, b, side_b, off_b = row.split(",")
        a, b = int(a), int(b)
        if a not in ids and b not in ids:
            continue
        if DIRECTION.get(side_a) != side_b:
            raise ValueError(f"Invalid map connection: {row}")
        if a in ids and b in ids:
            internal.append([ids[a], side_a, int(off_a), ids[b], side_b, int(off_b)])
        else:
            external.append(row)
    result = []
    for n in sorted(wanted):
        map_data = load(files[n])
        m = map_data.attrs
        tile_id = m["@tileset_id"]
        tileset = tilesets[tile_id].attrs
        dependencies = {"switches": set(), "variables": set(), "common_events": set(), "self_switches": set()}
        transfers, review = [], []
        graphics = set()
        for event, ev in m["@events"].items():
            for page in ev.attrs["@pages"]:
                attrs = page.attrs
                g = attrs["@graphic"].attrs
                graphic = text(g["@character_name"])
                if graphic:
                    graphics.add(graphic)
                cond = attrs["@condition"].attrs
                for valid, key, name in (("@switch1_valid", "@switch1_id", "switches"),
                                         ("@switch2_valid", "@switch2_id", "switches"),
                                         ("@variable_valid", "@variable_id", "variables"),
                                         ("@self_switch_valid", "@self_switch_ch", "self_switches")):
                    if cond[valid]:
                        dependencies[name].add(cond[key] if name != "self_switches" else f"{event}:{text(cond[key])}")
        for event, page, line, command in commands(map_data):
            code, params = command["@code"], command["@parameters"]
            where = {"event": event, "page": page, "command": line, "code": code}
            if code in (121, 122):
                key = "switches" if code == 121 else "variables"
                dependencies[key].update(range(params[0], params[1] + 1))
                if code == 122 and params[3] != 0:
                    review.append({**where, "reason": "variable operand"})
            elif code == 123:
                dependencies["self_switches"].add(f"{event}:{text(params[0])}")
            elif code == 117:
                dependencies["common_events"].add(params[0])
            elif code == 201 and params[0] == 0:
                transfers.append({**where, "source_target": params[1], "dest_target": ids.get(params[1]),
                                  "x": params[2], "y": params[3]})
            elif code in (111, 201, 202, 209, 231, 232, 235, 355, 509, 655):
                review.append({**where, "reason": "embedded script or project-specific event dependency"})
        meta = metadata_rows.get(n, "")
        result.append({"key": wanted[n], "source_id": n, "proposed_id": ids[n],
                       "name": text(infos[n].attrs["@name"]), "map_sha256": hashlib.sha256(files[n].read_bytes()).hexdigest(),
                       "parent": ids.get(infos[n].attrs["@parent_id"]), "dimensions": [m["@width"], m["@height"]],
                       "tileset": tile_id, "tileset_graphic": text(tileset["@tileset_name"]),
                       "autotiles": [text(x) for x in tileset["@autotile_names"] if x],
                       "characters": sorted(graphics), "encounters": n in encounter_ids,
                       "map_position": next(iter(re.findall(r"(?m)^MapPosition\s*=\s*([0-9,]+)", meta)), None),
                       "healing_spot": next(iter(re.findall(r"(?m)^HealingSpot\s*=\s*([0-9,]+)", meta)), None),
                       "references": {k: sorted(v) for k, v in dependencies.items()},
                       "transfers": transfers, "needs_manual_review": review})
    return {"region": manifest["region"], "source": manifest["source"], "package_sha256": manifest["sha256"],
            "status": "review_required", "destination_maps": len(dest_files), "source_maps": len(files),
            "namespaces": {key: {"source_slots": len(source_system["@" + key]),
                                 "destination_slots": len(dest_system["@" + key])}
                           for key in ("switches", "variables")},
            "maps": result, "connections": internal, "external_connections": external}


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--game", type=Path, default=ROOT / "game")
    cli.add_argument("--source", type=Path, help="Editable Essentials FRLG 1.1 project folder")
    cli.add_argument("--output", type=Path, help="Write report JSON to this path instead of stdout")
    args = cli.parse_args(argv)
    report = check_decades(args.game, json_file(REGISTRY))
    if args.source:
        report["kanto"] = map_plan(args.source, args.game, json_file(KANTO))
    raw = json.dumps(report, indent=2, ensure_ascii=True) + "\n"
    if args.output:
        args.output.write_text(raw, encoding="utf-8")
    else:
        print(raw, end="")


if __name__ == "__main__":
    main()
