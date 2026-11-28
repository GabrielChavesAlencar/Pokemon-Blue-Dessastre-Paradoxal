"""Stage Celadon interiors on a detached, installed K06 approach CI fixture."""
from __future__ import annotations

import copy
import json
import os
import re
from pathlib import Path

from audit import KANTO, ROOT, inventory, json_file, load, text
from audit_k06_celadon_services import CITY_DOORS, DEFERRED, INTERIORS, STORE, summarize
from build_k05_city import digest
from k04_gameplay import sprite
from k06_approach_migration import INSTALL, verify_native_graph
from pbs import catalogue
from pilot import EVENT_CLASSES, command, new_event, write_map
from qa_k04_migration import copy_for_ci

BASE = ".blue-work/kanto-k06-integrated"
OUTPUT = ".blue-work/kanto-k06-services-fixture"
# CI candidates only. 622–625 are already in Johto's preview range. These
# four other IDs still require native proof on BOTH channels before release.
CANDIDATES = dict(zip(INTERIORS, range(276, 280), strict=True))
FLOORS = tuple(range(117, 122))
SHOPS = {(118, 5), (118, 6), (120, 5), (121, 5), (121, 6)}
CABIN = (123, 2)
DOOR_SOUND = 0


def allocate(infos, files, previous):
    if (len(previous) != 178 or len(set(previous.values())) != 178
            or not set(previous.values()) <= (infos.keys() & files.keys())
            or previous.keys() & CANDIDATES.keys()
            or set(CANDIDATES.values()) & (infos.keys() | files.keys())):
        raise ValueError("Celadon candidate MapID collision or exact approach registry missing")
    return {**previous, **CANDIDATES}


def commands_for(warps, mapping):
    """Use native 201 transfers and store elevator state only in this save."""
    first = warps[0]
    sid = first["source"]
    if sid == 123:
        if (len(warps) != len(FLOORS)
                or {w["destination"] for w in warps} != set(FLOORS)
                or any(w["xy"] != [6, 2] or w["direction"] != 0 for w in warps)):
            raise ValueError("Unexpected authored elevator exits")
        ops = []
        for row in sorted(warps, key=lambda r: r["destination"]):
            dst = row["destination"]
            ops.extend([
                command(111, 12, f"BlueKantoCeladonServices.take_exit?({dst})".encode("ascii")),
                command(201, 0, mapping[dst], *row["xy"], 0, DOOR_SOUND, indent=1),
                command(412),
            ])
        return ops
    if len(warps) != 1:
        raise ValueError("Non-elevator event has multiple destinations")
    dst = first["destination"]
    ops = []
    if dst == 123:
        if sid not in FLOORS or first["xy"] != [2, 5]:
            raise ValueError("Unexpected department elevator origin")
        ops.append(command(355, f"BlueKantoCeladonServices.enter_cabin({sid})".encode("ascii")))
    return ops + [command(201, 0, mapping[dst], *first["xy"], first["direction"], DOOR_SOUND)]


def append_terrain(source, target, donors, original_infos, mapping, infos, tiles):
    source_tiles = load(source / "Data/Tilesets.rxdata")
    previous_tiles = copy.deepcopy(tiles)
    for sid in INTERIORS:
        donor = copy.deepcopy(donors[sid])
        m = donor.attrs
        tile = copy.deepcopy(source_tiles[m["@tileset_id"]])
        if tile is None:
            raise ValueError(f"Missing interior tileset: {sid}")
        t = tile.attrs

        def graphic(folder, value):
            name = text(value)
            if not name:
                return b""
            if not re.fullmatch(r"[\w .()\-]+", name) or name in (".", ".."):
                raise ValueError("Invalid interior terrain graphic name")
            src = source / "Graphics" / folder / (name + ".png")
            dest = target / "Graphics" / folder / ("FRLG_Preview_" + name + ".png")
            if not src.resolve().is_relative_to(source.resolve()):
                raise ValueError("Interior source asset left its pinned tree")
            src_data = src.read_bytes()
            if (not src_data.startswith(b"\x89PNG\r\n\x1a\n") or dest.is_symlink()
                    or (dest.exists() and dest.read_bytes() != src_data)):
                raise ValueError("Interior terrain graphic collision or invalid source asset")
            if not dest.exists():
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(src_data)
            return dest.stem.encode("utf8")

        t["@name"] = b"FRLG Preview " + t["@name"]
        t["@tileset_name"] = graphic("Tilesets", t["@tileset_name"])
        t["@autotile_names"] = [graphic("Autotiles", a) for a in t["@autotile_names"]]
        for key in ("@panorama_name", "@fog_name", "@battleback_name"):
            t[key] = b""
        row = next((i for i, existing in enumerate(tiles) if existing is not None and
                    {**t, "@id": i} == existing.attrs), None)
        if row is None:
            row = len(tiles)
            t["@id"] = row
            tiles.append(tile)
        m.update({"@tileset_id": row, "@events": {}, "@autoplay_bgm": False, "@autoplay_bgs": False})
        m["@bgm"].attrs["@name"] = m["@bgs"].attrs["@name"] = b""
        dest = mapping[sid]
        info = copy.deepcopy(original_infos[sid])
        info.attrs["@parent_id"] = mapping[114]
        info.attrs["@order"] = max(x.attrs["@order"] for x in infos.values()) + 1
        infos[dest] = info
        write_map(target / f"Data/Map{dest:03}.rxdata", donor)
    if tiles[:len(previous_tiles)] != previous_tiles:
        raise ValueError("Registered foreign tileset changed")


def stage_services(source, baseline, target, report):
    verify_native_graph(baseline)
    stamp = json_file(baseline / INSTALL)
    if stamp.get("content_stage") != "K06_APPROACH":
        raise ValueError("Celadon services require the delivered approach stage")
    previous = {int(sid): mid for sid, mid in stamp["maps"].items()}
    infos, files = inventory(baseline)
    mapping = allocate(infos, files, previous)
    old_info = copy.deepcopy(infos)
    tiles = load(baseline / "Data/Tilesets.rxdata")
    original_infos, source_files = inventory(source)
    by_source = {row["source"]: row for row in report["maps"]}
    donors = {}
    for sid in (114, *STORE, *INTERIORS):
        if digest(source_files[sid]) != by_source[sid]["sha256"]:
            raise ValueError(f"Celadon pinned source map changed: {sid}")
        donors[sid] = load(source_files[sid])
    copy_for_ci(baseline, target)
    append_terrain(source, target, donors, original_infos, mapping, infos, tiles)
    if any(infos[mid] != info for mid, info in old_info.items()):
        raise ValueError("The existing map registry was changed")
    for filename, data in (("MapInfos.rxdata", infos), ("Tilesets.rxdata", tiles)):
        write_map(target / "Data" / filename, data)
    items = catalogue(target, "items")
    markets = {(r["source"], r["event"]): r for r in report["services"] if r["shops"]}
    if set(markets) != SHOPS:
        raise ValueError("Unexpected native clerk catalog")
    for sid, donor in donors.items():
        path = target / f"Data/Map{mapping[sid]:03}.rxdata"
        native = load(path)
        m = native.attrs
        dm = donor.attrs
        if (any(m[k] != dm[k] for k in ("@width", "@height", "@data"))
                or (sid != 114 and m["@events"])):
            raise ValueError(f"Celadon expected original event-free preview: {sid}")
        city_original = copy.deepcopy(m["@events"]) if sid == 114 else {}
        groups = {}
        for warp in report["warps"]:
            if warp["source"] == sid:
                groups.setdefault(warp["event"], []).append(warp)
        if sid == 114 and set(groups) != CITY_DOORS.keys():
            raise ValueError("Unexpected city entrance set")

        def add(eid, at, ops, trigger, actor=False):
            event = dm["@events"][eid]
            if (eid in m["@events"] or tuple(at) != (event.attrs["@x"], event.attrs["@y"])
                    or any((other.attrs["@x"], other.attrs["@y"]) == tuple(at)
                           for other in m["@events"].values())):
                raise ValueError(f"Celadon event anchor collision or drift: {sid}/{eid}")
            m["@events"][eid] = new_event(event, ops, trigger, sprite(source, target, event) if actor else b"")

        for eid, warps in groups.items():
            for w in warps:
                dst = donors[w["destination"]].attrs
                if not (0 <= w["xy"][0] < dst["@width"] and 0 <= w["xy"][1] < dst["@height"]):
                    raise ValueError(f"Transfer outside target geometry: {sid}/{eid}")
            add(eid, warps[0]["at"], commands_for(warps, mapping), 1)
        for (area, eid), row in markets.items():
            if area != sid:
                continue
            stock = row["shops"]
            if (row["trigger"] != 0 or row["conditions"] or len(stock) != 1 or not stock[0]["literal"]
                    or not set(stock[0]["items"]) <= items):
                raise ValueError(f"Store inventory unavailable in target game: {sid}/{eid}")
            call = "pbPokemonMart([" + ", ".join(":" + k for k in stock[0]["items"]) + "])"
            add(eid, row["at"], [command(355, call.encode("ascii"))], 0, actor=True)
        if sid == CABIN[0]:
            add(CABIN[1], [0, 2], [command(355, b"BlueKantoCeladonServices.select_floor")], 0)
        if any(m["@events"][eid] != e for eid, e in city_original.items()):
            raise ValueError("Celadon legacy city doors/events changed")
        write_map(path, native, EVENT_CLASSES)
    plugin = target / "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb"
    with plugin.open("ab") as out:
        out.write(b"\n" + (ROOT / "scripts/regions/KantoK06CeladonServices.rb").read_bytes())
    after_infos, after_paths = inventory(target)
    if set(after_infos) - set(old_info) != set(CANDIDATES.values()) or set(after_paths) - set(files) != set(CANDIDATES.values()):
        raise ValueError("New Celadon map delta exceeds authorized scope")
    changed = {mapping[sid] for sid in (114, *STORE)}
    if any(digest(path) != digest(after_paths[mid]) for mid, path in files.items() if mid not in changed):
        raise ValueError("Unrelated map bytes changed")
    for rel in ("saves/K06-SYNTHETIC-SENTINEL.rxdata", "Game.ini", "mkxp.json", "PBS/map_connections_kanto.txt"):
        before, after = baseline / rel, target / rel
        if before.is_symlink() or after.is_symlink() or (before.is_file() and digest(before) != digest(after)):
            raise ValueError(f"Unrelated protected file changed: {rel}")
    verify_native_graph(target)
    return {"status": "K06_CELADON_PRIVATE_FIXTURE", "candidate_slots": CANDIDATES,
            "unchanged_old_ids": len(previous), "unrelated_maps_byte_identical": len(files)-len(changed),
            "unlocked_city_entrances": sorted(CITY_DOORS), "native_marts": len(markets),
            "deferred": sorted(DEFERRED), "new_slots_verified_on_android": False,
            "roof_items_and_interior_rewards_complete": False, "publish_allowed": False}


def run():
    if os.getenv("GITHUB_ACTIONS") != "true" or os.name != "nt":
        raise ValueError("Celadon staging is disposable Windows CI only")
    source = ROOT / ".blue-work/frlg-source/Essentials FRLG"
    report = summarize(source, json_file(KANTO))
    result = stage_services(source, (ROOT / BASE).resolve(), (ROOT / OUTPUT).resolve(), report)
    dest = ROOT / "k06-services-receipts/celadon-services-fixture.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(result, indent=2)+"\n", encoding="utf8")
    print("KANTO_K06_CELADON_PRIVATE_FIXTURE_OK:"+json.dumps(result), flush=True)


if __name__ == "__main__":
    run()
