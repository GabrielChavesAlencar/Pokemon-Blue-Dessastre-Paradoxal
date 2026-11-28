"""Extend the isolated K04 terrain fixture with native gameplay, not a release."""
from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path

from audit import ROOT, inventory, json_file, load
from build_k04_geometry import digest
from k04_corridor import DARK, MAPS, NAMES, connections, verify_source
from k04_gameplay import (install_actors, install_aide_and_runtime, install_pbs_payload,
                          append, trainer_profiles)
from pilot import EVENT_CLASSES, write_map

SAVE_APP = "Kanto K04 Gameplay CI"


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
        actor_report, cut_report = {}, {}
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
            actors, cut, nurse = install_actors(
                source, target, load(source_maps[source_id]), native, source_id, report)
            actor_report.update(actors)
            cut_report.update(cut)
            if nurse is not None:
                nurse_id = nurse
            write_map(data / path.name, native, EVENT_CLASSES)
        gate_path = install_aide_and_runtime(source, target, source_maps, active)

        write_map(data / "MapInfos.rxdata", info)
        write_map(data / "Tilesets.rxdata", tiles)

        pbs = target / "PBS"
        tables = install_pbs_payload(source, target, tmp, specs, delta)
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
        allowed_change = gate_path.relative_to(target)
        if any((rel != allowed_change and digest(target / rel) != sha) or digest(baseline / rel) != sha
               for rel, sha in checks.items()):
            raise ValueError("K04 gameplay changed preexisting map bytes")
        target.rename(output)
    summary = {"status": "STAGED_FOR_NATIVE_BOOT_NOT_PUBLISHED", "maps": delta, "prior_map_files": len(checks),
               "trained_events": actor_report, "distinct_profiles": len(specs), "encounter_tables": tables,
               "center": {"destination": delta[88], "nurse_event": nurse_id}, "darkness": [delta[s] for s in sorted(DARK)],
               "cut_obstacles": cut_report, "prior_flash_aide_map_only": int(gate_path.stem[3:]), "native_boot": False, "manual_gameplay": False}
    (work / "kanto-k04-gameplay-proof.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("KANTO_K04_GAMEPLAY_FIXTURE_STAGED_OK:", len(actor_report), len(specs), tables, flush=True)


if __name__ == "__main__":
    run()
