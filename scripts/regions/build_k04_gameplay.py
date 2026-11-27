"""Extend the isolated K04 terrain fixture with native gameplay, not a release."""
from __future__ import annotations

import copy
import json
import os
import re
import shutil
import tempfile
from pathlib import Path

from audit import ROOT, inventory, json_file, load, text
from build_k04_geometry import digest
from k04_corridor import DARK, MAPS, NAMES, connections, verify_source
from pbs import catalogue, normalize_encounters, read_blocks, trainer_draft
from pilot import EVENT_CLASSES, TYPES, command, new_event, write_map

TRAINERS = {
    86: {2: "PICNICKER,Alicia", 3: "HIKER,Jeremy", 4: "CAMPER,Chris",
         5: "BUGCATCHER,Brent", 6: "CAMPER,Drew", 7: "BUGCATCHER,Conner",
         8: "HIKER,Brice", 9: "PICNICKER,Caitlin", 10: "HIKER,Alan"},
    87: {5: "PICNICKER,Heidi", 10: "POKEMANIAC,Mark", 16: "PICNICKER,Carol",
         17: "HIKER,Clark", 18: "HIKER,Trent", 21: "POKEMANIAC,Herman"},
    90: {2: "HIKER,Lenny", 3: "HIKER,Oliver", 6: "POKEMANIAC,Ashton",
         8: "HIKER,Lucas", 9: "PICNICKER,Leah", 10: "PICNICKER,Ariana", 12: "PICNICKER,Dana"},
    91: {1: "HIKER,Allen", 2: "HIKER,Eric", 3: "POKEMANIAC,Steve",
         19: "POKEMANIAC,Winston", 21: "PICNICKER,Martha", 22: "PICNICKER,Sofia",
         25: "HIKER,Allen", 26: "POKEMANIAC,Cooper"},
}
NURSE = re.compile(r"\b(?:pbPokeCenter|pbPokemonCenter|pbHealAll|pbSetPokemonCenter)\b|\$player\.heal_party")
SAVE_APP = "Kanto K04 Gameplay CI"


def trainer_profiles(report):
    expected = {f"{sid}/{eid}": k for sid, rows in TRAINERS.items() for eid, k in rows.items()}
    if {eid: list(profiles) for eid, profiles in report["trainers"].items()} != {
            eid: [kind_name] for eid, kind_name in expected.items()}:
        raise ValueError("K04 trainer event or source profile changed")
    specs = {}
    for spec in expected.values():
        kind, name = spec.split(",")
        if kind not in TYPES or not re.fullmatch(r"[A-Za-z]+", name):
            raise ValueError(f"Unsupported K04 trainer identity {spec}")
        specs[spec] = (kind, name, 0)
    return specs


def clean_trainer_source(source, destination, specs):
    blocks = read_blocks(source, specs)
    # Exactly one pinned stray line follows Alicia's lose text. It isn't a
    # property, and no other malformed input is discarded.
    alicia = blocks["PICNICKER,Alicia"]
    if (alicia.count("x") != 1 or alicia.index("x") == 0
            or not alicia[alicia.index("x") - 1].startswith("LoseText =")):
        raise ValueError("K04 Alicia's source normalization no longer matches")
    alicia.remove("x")
    destination.write_text("".join(f"[{key}]\n" + "\n".join(lines) + "\n"
                                   for key, lines in blocks.items()), encoding="utf-8")


def sprite(source, target, event):
    graphic = text(event.attrs["@pages"][0].attrs["@graphic"].attrs["@character_name"])
    if not re.fullmatch(r"[\w .()\-]+", graphic) or graphic in (".", ".."):
        raise ValueError(f"Invalid K04 actor graphic {graphic!r}")
    name = "FRLG_Pilot_" + graphic
    folder = source / "Graphics/Characters"
    src = folder / (graphic + ".png")
    if not src.resolve().is_relative_to(folder.resolve()):
        raise ValueError("K04 actor points outside the pinned source")
    dst = target / "Graphics/Characters" / (name + ".png")
    if not src.is_file():
        src = target / "Graphics/Characters" / (graphic + ".png")
    raw = src.read_bytes()
    if not raw.startswith(b"\x89PNG\r\n\x1a\n") or (dst.exists() and dst.read_bytes() != raw):
        raise ValueError(f"Invalid K04 actor graphic or asset collision: {graphic}")
    if not dst.exists():
        dst.write_bytes(raw)
    return name.encode("utf-8")


def trainer_event(event, source_id, event_id, spec, graphic):
    kind, name = spec.split(",")
    key = f"KANTO_{source_id:03d}_{event_id:03d}"
    first = event.attrs["@pages"][0].attrs
    if any(value for field, value in first["@condition"].attrs.items() if field.endswith("_valid")):
        raise ValueError(f"K04 trainer requires authored conditions at {source_id}/{event_id}")
    label = text(event.attrs["@name"])
    auto = first["@trigger"] == 2 and re.search(r"(?i)(?:trainer|sight)\([1-9]\d*\)", label)
    intro = [f"pbTrainerIntro(:BLUE_KANTO_{kind})", "pbNoticePlayer(get_self)"] if auto else []
    calls = [*intro, f'BlueKantoPilot.battle(:BLUE_KANTO_{kind}, "{name}", "{key}")',
             f'BlueKantoPilot.sync_trainer_event("{key}", "{name}", {event_id})']
    if auto:
        calls.append("pbTrainerEnd")
    native = new_event(event, [command(355, c.encode("ascii")) for c in calls], 2 if auto else 0, graphic)
    after = copy.deepcopy(native.attrs["@pages"][0])
    after.attrs["@condition"].attrs.update({"@self_switch_valid": True, "@self_switch_ch": b"A"})
    after.attrs.update({"@trigger": 0, "@through": False, "@direction_fix": False,
                        "@list": [command(355, f'BlueKantoPilot.trainer_repeat("{name}", :BLUE_KANTO_{kind})'.encode("ascii")), command(0)]})
    native.attrs["@pages"].append(after)
    return native


def center_anchor(donor):
    def visible_service(event):
        pages = event.attrs["@pages"]
        visible = bool(pages[0].attrs["@graphic"].attrs["@character_name"])
        return visible and any(
            NURSE.search(text(op.attrs["@parameters"][0]))
            for pg in pages for op in pg.attrs["@list"]
            if op.attrs["@code"] in (355, 655) and len(op.attrs["@parameters"]) == 1)
    events = donor.attrs["@events"]
    candidates = [eid for eid, ev in events.items() if visible_service(ev)]
    if len(candidates) != 1:
        raise ValueError(f"K04 expected one original visible nurse, found {candidates}")
    return candidates[0]


def append(path, addition):
    with path.open("a", encoding="utf-8") as f:
        f.write("\n" + addition.strip() + "\n")


def run():
    if os.getenv("GITHUB_ACTIONS") != "true":
        raise ValueError("K04 gameplay requires a disposable CI workspace")
    work = ROOT / ".blue-work"
    source = work / "frlg-source/Essentials FRLG"
    baseline, geometry = (work / f"kanto-{label}" for label in ("release-pilot", "k04-geometry"))
    output = work / "kanto-k04-gameplay"
    if output.exists():
        raise ValueError("K04 gameplay candidate directory already exists")
    receipt = json_file(work / "kanto-k04-geometry-proof.json")
    report = json_file(work / "kanto-k04-source.json")
    verify_source(report)
    specs = trainer_profiles(report)
    meta = json_file(baseline / "Kanto pilot.json")
    active = {int(k): v for k, v in meta["maps"].items()}
    delta = {m["id"]: m["destination_candidate"] for m in report["maps"]}
    if len(active) != 160 or set(active) & delta.keys() or set(active.values()) & set(delta.values()):
        raise ValueError("Unexpected K04 allocation overlap")
    if {m["source"]: m["destination"] for m in receipt["new_maps"]} != delta:
        raise ValueError("K04 geometry receipt does not match gameplay allocation")
    _, baseline_maps = inventory(baseline)
    _, source_maps = inventory(source)
    if set(delta.values()) & baseline_maps.keys():
        raise ValueError("K04 may not replace any existing map")
    checks = {p.relative_to(baseline): digest(p) for p in baseline_maps.values()}
    with tempfile.TemporaryDirectory(prefix=".k04-gameplay-", dir=work) as folder:
        tmp = Path(folder)
        target = tmp / "game"
        # The active fixture is pre-boot. Do not copy a save, and keep title
        # and mkxp save namespace isolated even on a persistent CI runner.
        shutil.copytree(baseline, target, ignore=shutil.ignore_patterns("*.rxsave", "*.sav", "Game.rxdata", "Game_*.rxdata", "Save*", "Backups"))
        for config in ("Game.ini", "mkxp.json"):
            path = target / config
            orig = path.read_text("utf-8-sig")
            if orig.count(meta["save_app"]) != 1:
                raise ValueError(f"Can't isolate K04 save namespace in {config}")
            path.write_text(orig.replace(meta["save_app"], SAVE_APP), "utf-8")
        meta.update({"save_app": SAVE_APP, "maps": {**active, **delta}, "k04_fixture_only": True})
        (target / "Kanto pilot.json").write_text(json.dumps(meta), encoding="utf-8")

        data = target / "Data"
        info, tiles = (load(data / name) for name in ("MapInfos.rxdata", "Tilesets.rxdata"))
        geom_data = geometry / "Data"
        new_info, new_tiles = (load(geom_data / name) for name in ("MapInfos.rxdata", "Tilesets.rxdata"))
        shutil.copytree(geometry / "Graphics", target / "Graphics", dirs_exist_ok=True)
        allocated_tiles = {}
        actor_report = {}
        for source_id, dest in delta.items():
            path = geom_data / f"Map{dest:03d}.rxdata"
            native = load(path)
            idx = native.attrs["@tileset_id"]
            if idx not in allocated_tiles:
                tile = new_tiles[idx]
                tile.attrs["@id"] = allocated_tiles[idx] = len(tiles)
                tiles.append(tile)
            native.attrs["@tileset_id"] = allocated_tiles[idx]
            info[dest] = new_info[dest]
            info[dest].attrs["@name"] = NAMES[tuple(MAPS).index(source_id)].encode("utf-8")
            donor = load(source_maps[source_id])
            source_events, events = donor.attrs["@events"], native.attrs["@events"]
            declared = TRAINERS.get(source_id, {})
            occupied = {tuple(event.attrs[k] for k in ("@x", "@y")) for event in events.values()}
            for eid, spec in declared.items():
                event = source_events[eid]
                xy = tuple(event.attrs[k] for k in ("@x", "@y"))
                if xy in occupied or eid in events:
                    raise ValueError(f"K04 trainer conflicts with an event at {source_id}/{eid}")
                occupied.add(xy)
                events[eid] = trainer_event(event, source_id, eid, spec, sprite(source, target, event))
                actor_report[f"{source_id}/{eid}"] = {"profile": spec, "xy": xy,
                    "sight": events[eid].attrs["@pages"][0].attrs["@trigger"] == 2}
            if source_id == 88:
                nurse_id = center_anchor(donor)
                if nurse_id in events:
                    raise ValueError("K04 nurse conflicts with a transfer")
                ev = source_events[nurse_id]
                events[nurse_id] = new_event(ev, [command(355, b"BlueKantoPilot.heal")], 0, sprite(source, target, ev))
            write_map(data / path.name, native, EVENT_CLASSES)
        write_map(data / "MapInfos.rxdata", info)
        write_map(data / "Tilesets.rxdata", tiles)

        species, moves, items = (catalogue(target, k) for k in ("pokemon", "moves", "items"))
        pbs = target / "PBS"
        fixed = tmp / "k04-trainer-subset.txt"
        clean_trainer_source(source / "PBS/trainers.txt", fixed, specs)
        trainer_pbs = pbs / "trainers_kanto.txt"
        native_profiles = {f"BLUE_KANTO_{kind},{name},{version}" for kind, name, version in specs.values()}
        if read_blocks(trainer_pbs, native_profiles):
            raise ValueError("K04 trainer profile would replace a released profile")
        append(trainer_pbs, trainer_draft(fixed, species, moves, items, specs))
        wild, tables = normalize_encounters(source / "PBS/encounters.txt", delta, species)
        if tables != 4 or {int(n) for n in re.findall(r"(?m)^\[(\d+)(?:,\d+)?\]", wild)} != {
                delta[i] for i in (86, 87, 90, 91)}:
            raise ValueError("K04 must retain exactly the four original encounter tables")
        append(pbs / "encounters_kanto.txt", wild)
        append(pbs / "map_connections_kanto.txt",
               "\n".join(",".join(map(str, row)) for row in connections({**active, **delta})))
        for sid, dst in delta.items():
            value = f"[{dst:03d}]\nName = {NAMES[tuple(MAPS).index(sid)]}"
            if sid in (86, 87):
                value += "\nOutdoor = true\nShowArea = true"
            if sid in DARK:
                value += "\nDarkMap = true\nShowArea = true"
            append(pbs / "map_metadata_kanto.txt", value)
        (data / "blue-compile-request.txt").write_text("compile", encoding="ascii")
        (data / "PluginScripts.rxdata").unlink(missing_ok=True)
        if any(digest(target / rel) != sha or digest(baseline / rel) != sha for rel, sha in checks.items()):
            raise ValueError("K04 gameplay changed preexisting map bytes")
        target.rename(output)
    summary = {"status": "STAGED_FOR_NATIVE_BOOT_NOT_PUBLISHED", "maps": delta, "prior_map_files": len(checks),
               "trained_events": actor_report, "distinct_profiles": len(specs), "encounter_tables": tables,
               "center": {"destination": delta[88], "nurse_event": nurse_id}, "darkness": [delta[s] for s in sorted(DARK)],
               "native_boot": False, "manual_gameplay": False}
    (work / "kanto-k04-gameplay-proof.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("KANTO_K04_GAMEPLAY_FIXTURE_STAGED_OK:", len(actor_report), len(specs), tables, flush=True)


if __name__ == "__main__":
    run()
