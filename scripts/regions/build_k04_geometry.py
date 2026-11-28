"""Stage isolated Rock Tunnel terrain and authored native transfer commands in CI."""
from __future__ import annotations

import hashlib
import json
import os

from audit import KANTO, ROOT, inventory, json_file, load
from k04_corridor import DARK, LAVENDER_BOUNDARY, MAPS, WARPS, connections, verify_source
from pilot import EVENT_CLASSES, command, new_event, write_map
from stage import stage


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inject_warps(source_map, native_map, source_id, mapping):
    if native_map.attrs["@events"]:
        raise ValueError("K04 staging must not carry foreign events")
    for (sid, event_id), (dest, x, y, direction) in WARPS.items():
        if sid != source_id:
            continue
        event = source_map.attrs["@events"][event_id]
        ops = [command(201, 0, mapping[dest], x, y, direction, 0)]
        native_map.attrs["@events"][event_id] = new_event(event, ops, 1, b"")


def main():
    if os.environ.get("GITHUB_ACTIONS") != "true":
        raise ValueError("K04 geometry requires a disposable CI workspace")
    work = ROOT / ".blue-work"
    source = work / "frlg-source/Essentials FRLG"
    pilot = work / "kanto-release-pilot"
    output = work / "kanto-k04-geometry"
    expected = json_file(work / "kanto-k04-source.json")
    verify_source(expected)
    manifest = json_file(KANTO)
    active = {int(k): v for k, v in json_file(pilot / "Kanto pilot.json")["maps"].items()}
    if len(active) != 160 or set(active) != set(map(int, manifest["maps"])):
        raise ValueError("K04 must start from the current K03-E release pilot")
    candidate = {**manifest, "maps": {**manifest["maps"], **{str(k): v for k, v in MAPS.items()}}}
    _, old = inventory(pilot)
    old_files = [old[d] for d in active.values()]
    old_files += [pilot / "Data" / n for n in ("MapInfos.rxdata", "Tilesets.rxdata")]
    hashes = {p: digest(p) for p in old_files}
    plan = stage(ROOT, source, pilot, output, existing=active, manifest=candidate)
    mapping = {row["source_id"]: row["proposed_id"] for row in plan["maps"]}
    if (len(mapping) != 165 or mapping != {**active, **{m["id"]: m["destination_candidate"] for m in expected["maps"]}}):
        raise ValueError("K04 geometry relocated the released pilot maps or new slots")
    wanted_seams = connections(mapping)
    if any(row not in plan["connections"] for row in wanted_seams):
        raise ValueError("K04 physical seams do not match the source plan")
    native_paths = {sid: output / "Data" / f"Map{mapping[sid]:03d}.rxdata" for sid in MAPS}
    floors = {sid: load(p) for sid, p in native_paths.items()}
    for (sid, event_id), (dest, x, y, direction) in WARPS.items():
        area = floors[dest].attrs
        if not (0 <= x < area["@width"] and 0 <= y < area["@height"]):
            raise ValueError(f"K04 invalid landing at {sid}/{event_id}")
    _, inputs = inventory(source)
    staged = []
    for sid, path in native_paths.items():
        donor, floor = load(inputs[sid]), floors[sid]
        if (floor.attrs["@data"] != donor.attrs["@data"]
                or tuple(floor.attrs[k] for k in ("@width", "@height")) !=
                   tuple(donor.attrs[k] for k in ("@width", "@height"))):
            raise ValueError(f"K04 raw tiles differ from pinned source: {sid}")
        inject_warps(donor, floor, sid, mapping)
        write_map(path, floor, EVENT_CLASSES)
        compiled = load(path).attrs["@events"]
        expected_events = {event: (mapping[dest], x, y, direction)
                           for (src, event), (dest, x, y, direction) in WARPS.items() if src == sid}
        if set(compiled) != set(expected_events):
            raise ValueError(f"K04 extra event at {sid}")
        for eid, event in compiled.items():
            page, = event.attrs["@pages"]
            ops = [cmd.attrs for cmd in page.attrs["@list"]]
            if (page.attrs["@trigger"] != 1 or [cmd["@code"] for cmd in ops] != [201, 0]
                    or ops[0]["@parameters"] != [0, *expected_events[eid], 0]):
                raise ValueError(f"K04 foreign or incorrect transfer at {sid}/{eid}")
        staged.append({"source": sid, "destination": mapping[sid], "event_ids": sorted(compiled)})
    if any(digest(p) != sha for p, sha in hashes.items()):
        raise ValueError("K04 geometry modified the existing 160-map pilot")
    receipt = {"status": "CI_TERRAIN_AND_TRANSFER_FIXTURE", "candidate_maps": 165,
               "published_maps_preserved": 160, "transfers": len(WARPS),
               "new_maps": staged, "verified_seams": wanted_seams,
               "source_dark_floors": sorted(DARK), "deferred_lavender_boundary": LAVENDER_BOUNDARY,
               "manual_gameplay": False, "not_a_release": True}
    result = json.dumps(receipt, ensure_ascii=True, indent=2) + "\n"
    (work / "kanto-k04-geometry-proof.json").write_text(result, encoding="utf-8")
    print("KANTO_K04_GEOMETRY_NATIVE_TRANSFERS_OK:" + json.dumps(receipt), flush=True)


if __name__ == "__main__":
    main()
