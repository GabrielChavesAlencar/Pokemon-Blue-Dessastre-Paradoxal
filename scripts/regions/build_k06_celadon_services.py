"""Stage Celadon interiors on a detached, installed K06 approach CI fixture."""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
from fnmatch import fnmatchcase
from pathlib import Path

from audit import KANTO, ROOT, inventory, json_file, load, text
from audit_k06_celadon_services import CITY_DOORS, DEFERRED, INTERIORS, STORE, summarize
from build_k05_city import digest
from k04_gameplay import sprite
from k06_approach_migration import INSTALL, SAVE, verify_native_graph
from pbs import catalogue, read_blocks
from pilot import EVENT_CLASSES, command, new_event, write_map

BASE = ".blue-work/kanto-k06-integrated"
OUTPUT = ".blue-work/kanto-k06-services-fixture"
# CI candidates only. 622–625 are already in Johto's preview range. These
# four other IDs still require native proof on BOTH channels before release.
CANDIDATES = dict(zip(INTERIORS, range(276, 280), strict=True))
FLOORS = tuple(range(117, 122))
SHOPS = {(118, 5), (118, 6), (120, 5), (121, 5), (121, 6)}
CABIN = (123, 2)
DOOR_SOUND = 0
STAGE_LOCAL = "K06_CELADON_SERVICES_CI"
PROFILE = "Kanto K06 Celadon Services CI"
SERVICES = {
    (122, 2): ("vend", (), False),
    (122, 6): ("exchange", ("TM16", "TM20", "TM33"), True),
    (125, 5): ("coin_case", ("COINCASE",), True),
    (128, 1): ("tea", ("TEA",), True),
    (128, 23): ("eevee", ("EEVEE",), True),
}
DRINKS = (("FRESHWATER", 200), ("SODAPOP", 300), ("LEMONADE", 350))


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


def ensure_tea_item(target, report):
    """Install only an authored, inert key item when the native ID is absent."""
    tea = [r for r in report["services"] if (r["source"],r["event"],r["page"]) == (128,1,1)]
    if (len(tea) != 1 or tea[0]["at"] != [2,9] or tea[0]["conditions"] or tea[0]["trigger"] != 0
            or tea[0]["rewards"] != [{"operation":"pbReceiveItem", "item_or_species":"TEA"}]):
        raise ValueError("Mansion Tea reward absent or no longer the authored source anchor")
    pbs = target / "PBS"
    by_item = {}
    for path in sorted(pbs.glob("items*.txt")):
        for key, rows in read_blocks(path, {"BICYCLE","TEA"}).items():
            if key in by_item:
                raise ValueError(f"Duplicate Celadon compatibility item {key}")
            by_item[key] = {k.strip():v.split("#",1)[0].strip()
                            for row in rows for k,sep,v in [row.partition("=")] if sep}
    if "TEA" in by_item:
        fields = by_item["TEA"]
        flags = {flag.strip().casefold() for flag in fields.get("Flags","").split(",")}
        if "keyitem" not in flags or fields.get("Consumable","false").casefold() != "false":
            raise ValueError("Existing Tea item is not a compatible nonconsumable key item")
        return False
    bicycle = by_item.get("BICYCLE", {})
    pocket = bicycle.get("Pocket","")
    flags = {flag.strip().casefold() for flag in bicycle.get("Flags","").split(",")}
    if not pocket.isascii() or not pocket.isdecimal() or not 1 <= int(pocket) <= 32 or "keyitem" not in flags:
        raise ValueError("Cannot resolve native key-item pocket for Celadon Tea")
    with (pbs / "items_kanto.txt").open("a",encoding="utf8") as out:
        out.write("\n# Celadon Mansion: original event grants this inert key item.\n"
                  "[TEA]\nName = Tea\nNamePlural = Tea\n"
                  f"Pocket = {pocket}\nPrice = 0\nConsumable = false\nFlags = KeyItem\n"
                  "Description = A gift of tea from Celadon Mansion.\n")
    return True


def reward_anchors(report, items, species):
    rows = {}
    for row in report["services"]:
        key = row["source"], row["event"]
        if key in SERVICES:
            rows.setdefault(key, []).append(row)
    if rows.keys() != SERVICES.keys() or not {d for d,_ in DRINKS} <= items or "EEVEE" not in species:
        raise ValueError("Missing source services or installed item/species catalogue")
    for key, (method, rewards, actor) in SERVICES.items():
        specs = rows[key]
        first = specs[0]
        if (first["page"] != 1 or first["trigger"] != 0 or first["conditions"] or
                any(row["at"] != first["at"] for row in specs) or
                [r["item_or_species"] for row in specs for r in row["rewards"]] != list(rewards) or
                not (set(rewards) - {"EEVEE"}) <= items):
            raise ValueError(f"Unexpected Celadon reward witness at {key}")
        if method == "vend":
            add = [arg["item_or_species"] for arg in first["item_arguments"] if arg["operation"] == "add"]
            amount_pairs = [(r["operation"], r["operand"]) for r in first["money"] if "operand" in r]
            expected = [(op, price) for _, price in DRINKS
                        for op in ("native_gold_condition", "native_gold_change")]
            if list(dict.fromkeys(add)) != [d for d,_ in DRINKS] or amount_pairs != expected:
                raise ValueError("Vending source money and drinks no longer match")
        elif method == "exchange":
            if [[a["item_or_species"] for a in row["item_arguments"] if a["operation"] == "remove"]
                    for row in specs] != [[d] for d,_ in DRINKS]:
                raise ValueError("The three roof exchanges no longer match")
        elif method == "eevee":
            if first["item_arguments"] != [{"operation":"pbAddPokemon", "item_or_species":"EEVEE", "quantity":25}]:
                raise ValueError("Mansion gift level no longer matches")
        rows[key] = (first["at"], method, actor)
    return rows


def copy_celadon_fixture(baseline, target):
    # Bulk copy never imports any saves. Carry only the byte-exact sentinel
    # from stage_ci so the verifier can detect an accidental write to it.
    sentinel = baseline / SAVE
    expected = b"test save marker; not actual game data"
    if sentinel.is_symlink() or sentinel.read_bytes() != expected:
        raise ValueError("K06 fixture is missing the exact synthetic save sentinel")
    def ignore_saved_data(_folder, names):
        patterns = ("game_*.rxdata", "game.rxdata", "*.sav", "*.rxsave", "save*", "backups")
        return [name for name in names if any(fnmatchcase(name.casefold(), p) for p in patterns)]

    shutil.copytree(baseline, target, ignore=ignore_saved_data)
    copy = target / SAVE
    copy.parent.mkdir(exist_ok=True)
    with copy.open("xb") as stream:
        stream.write(expected)


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
    copy_celadon_fixture(baseline, target)
    append_terrain(source, target, donors, original_infos, mapping, infos, tiles)
    if any(infos[mid] != info for mid, info in old_info.items()):
        raise ValueError("The existing map registry was changed")
    for filename, data in (("MapInfos.rxdata", infos), ("Tilesets.rxdata", tiles)):
        write_map(target / "Data" / filename, data)
    tea_defined_locally = ensure_tea_item(target, report)
    items = catalogue(target, "items")
    rewards = reward_anchors(report, items, catalogue(target, "pokemon"))
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
        for (area, eid), (at, method, actor) in rewards.items():
            if area == sid:
                add(eid, at, [command(355, f"BlueKantoCeladonServices.{method}".encode("ascii"))],
                    0, actor=actor and bool(dm["@events"][eid].attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"]))
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
    for rel in (SAVE, "Game.ini", "mkxp.json", "PBS/map_connections_kanto.txt"):
        before, after = baseline / rel, target / rel
        if before.is_symlink() or after.is_symlink() or not after.is_file() or digest(before) != digest(after):
            raise ValueError(f"Unrelated protected file changed: {rel}")
    verify_native_graph(target)
    # A native fixture receives the same checked registry format used by
    # releases. Its stage remains CI-only and cannot reach the updater.
    stamp.update(maps=mapping, content_stage=STAGE_LOCAL)
    (target / INSTALL).write_text(json.dumps(stamp,indent=2)+"\n",encoding="utf8")
    gate = target / "Data/blue-kanto-ready.txt"
    gate.write_text(f"BLUE_KANTO_READY_V1,182,{mapping[7]}\n",encoding="ascii")
    meta = target / "PBS/map_metadata_kanto.txt"
    with meta.open("a",encoding="utf8") as pbs:
        for sid, label in zip(INTERIORS, ("Celadon Diner","Celadon Hotel","Celadon House","Celadon Mansion"), strict=True):
            pbs.write(f"\n[{mapping[sid]:03}]\nName = {label}\n")
    from k06_approach_migration import CI_PROFILE
    from qa_k04_migration import jsonc, save_namespace_valid
    cfg = target / "mkxp.json"
    if not save_namespace_valid(baseline, CI_PROFILE):
        raise ValueError("Celadon fixture predecessor save isolation missing")
    config = jsonc(cfg.read_text("utf-8-sig"))
    cfg.write_text(json.dumps({**config, "dataPathApp": PROFILE}, ensure_ascii=False, indent=2)+"\n", encoding="utf8")
    if not save_namespace_valid(target, PROFILE):
        raise ValueError("Celadon fixture save isolation missing")
    (target / "Data/blue-compile-request.txt").write_text("compile", encoding="ascii")
    (target / "Data/PluginScripts.rxdata").unlink(missing_ok=True)
    return {"status": "K06_CELADON_PRIVATE_FIXTURE", "candidate_slots": CANDIDATES,
            "unchanged_old_ids": len(previous), "unrelated_maps_byte_identical": len(files)-len(changed),
            "unlocked_city_entrances": sorted(CITY_DOORS), "native_marts": len(markets),
            "deferred": sorted(DEFERRED), "new_slots_verified_on_android": False,
            "staged_authored_reward_events": len(rewards), "defined_inert_tea": tea_defined_locally, "publish_allowed": False}


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
