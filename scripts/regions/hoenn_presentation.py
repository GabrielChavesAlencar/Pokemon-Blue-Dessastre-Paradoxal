"""Presentation changes for the pinned Hoenn pilot maps."""

from __future__ import annotations

import copy
import re
import struct

from build_johto_events import command, ruby
from hoenn_audio import BGM, MAP_BGM, RECOVERY, RECOVERY_DEST, bgm_source
from server.ruby_marshal import loads, text

TRAINER_SCRIPT = re.compile(
    r'BlueHoennPilot\.(battle(?:_stage3)?)\(\s*:(\w+)\s*,\s*"([^"]+)"'
    r'(?:\s*,\s*(\d+)(?:\s*,\s*(true))?)?\s*\)'
)
SIGHT = re.compile(r"(?:Trainer|Sight)\((\d+)\)", re.I)


def add_littleroot_trees(world):
    attrs = world.attrs
    width, height = attrs["@width"], attrs["@height"]
    table = attrs["@data"]
    # Copy only the ornamental layer at an isolated tree in the same map.
    # The floor, map dimensions, exits and event coordinates stay in place.
    if (width, height) != (20, 20):
        raise ValueError("Dimensões de Littleroot diferentes da origem auditada")
    cells = list(struct.unpack_from(f"<{width * height * 3}H", table.data, 20))
    pattern = (828, 829, 836, 837)
    coordinates = ((0, 0), (1, 0), (0, 1), (1, 1))
    sample = tuple(cells[width * height + y * width + x + 2] for x, y in coordinates)
    if sample != pattern:
        raise ValueError("Árvore de origem alterada em Littleroot")
    occupied = {(e.attrs["@x"], e.attrs["@y"]) for e in attrs["@events"].values()}
    for left, top in ((0, 4), (18, 4), (0, 14), (16, 14)):
        target = [(left + x, top + y) for x, y in coordinates]
        if occupied.intersection(target):
            raise ValueError("Árvore de Littleroot sobre um evento")
        positions = [y * width + x for x, y in target]
        if tuple(cells[width * height + index] for index in positions) == pattern:
            continue
        if any((cells[index], cells[width * height + index], cells[2 * width * height + index])
               != (385, 0, 0) for index in positions):
            raise ValueError("O canto de Littleroot não contém apenas grama")
        for index, tile in zip(positions, pattern):
            cells[width * height + index] = tile
    table.data = table.data[:20] + struct.pack(f"<{len(cells)}H", *cells)


def activate_trainer_sight(world, original):
    donor = {}
    for obj in original.attrs["@events"].values():
        event = obj.attrs
        sight = SIGHT.search(text(event["@name"]))
        page = event["@pages"][0].attrs
        if sight and page["@trigger"] == 2:
            donor[(event["@x"], event["@y"])] = (sight[1], page["@graphic"].attrs["@direction"])

    installed = 0
    for obj in world.attrs["@events"].values():
        event = obj.attrs
        page = event["@pages"][0].attrs
        if len(event["@pages"]) != 1 or page["@trigger"] != 0:
            continue
        ops = page["@list"]
        if len(ops) != 2 or ops[0].attrs["@code"] != 355:
            continue
        match = TRAINER_SCRIPT.fullmatch(text(ops[0].attrs["@parameters"][0]))
        if not match:
            continue
        pose = donor.get((event["@x"], event["@y"]))
        if not pose:
            continue
        distance, direction = pose
        _, kind, name, version, double = match.groups()
        binding = f':{kind},"{name}",{version or 102}'
        battle = f'{binding},{"true" if double else "false"}'
        event["@name"] = event["@name"] + f" Trainer({distance})".encode("ascii")
        page["@graphic"].attrs["@direction"] = direction
        page["@trigger"] = 2
        script = f"BlueHoennPilot.challenge_trainer(get_self,{battle})"
        page["@list"] = [command(355, script.encode("ascii")), command(0)]
        finished = copy.deepcopy(event["@pages"][0])
        finished.attrs["@condition"].attrs["@self_switch_valid"] = True
        finished.attrs["@trigger"] = 0
        finished.attrs["@list"] = ops
        event["@pages"].append(finished)
        installed += 1
    return installed


def apply_presentation(maps, source, overlay):
    trainers = {}
    for mid, world in maps.items():
        track = MAP_BGM[mid]
        world.attrs["@autoplay_bgm"] = True
        world.attrs["@bgm"] = ruby("RPG::AudioFile", name=f"BLUE_HOENN_{track}".encode(),
                                  volume=80, pitch=100)
        # Keep the original event IDs and apply sight only when the pinned map
        # contains a matching trainer position and active Event Touch page.
        if any("BlueHoennPilot.battle" in text(op.attrs["@parameters"][0])
               for event in world.attrs["@events"].values()
               for op in event.attrs["@pages"][0].attrs["@list"]
               if op.attrs["@code"] == 355):
            original = loads(source.read(f"Data/Map{mid:03}.rxdata"))
            count = activate_trainer_sight(world, original)
            if count:
                trainers[str(mid)] = count
    for dest, original in [
        *((f"Audio/BGM/BLUE_HOENN_{label}.ogg", bgm_source(track)) for label, track in BGM.items()),
        (RECOVERY_DEST, RECOVERY),
    ]:
        blob = source.read(original)
        if not blob.startswith(b"OggS"):
            raise ValueError(f"Áudio de Hoenn inválido: {original}")
        overlay[dest] = blob
    return {"version": 1, "map_tracks": len(set(MAP_BGM[mid] for mid in maps)),
            "trainer_sight_by_source_map": trainers}


def upgrade_presentation(copy, source):
    """Update the pinned 199-map QA copy while retaining map and event IDs."""
    import json

    from hoenn_qa_phase11 import audit_generated
    from hoenn_qa_teleport_upgrade import replace_private_files
    from hoenn_stage10 import SOURCE_MAPS_STAGE10
    from pilot_hoenn import EVENT_CLASSES, SOURCE_MAPS, regular, serialize

    manifest_path = copy / "Hoenn pilot.json"
    report = json.loads(regular(manifest_path).read_text("utf8"))
    if report.get("hoenn_presentation", {}).get("version") == 1:
        return report["hoenn_presentation"]
    paths = {int(key): f"Data/Map{value:03}.rxdata" for key, value in report["maps"].items()}
    worlds = {mid: loads(regular(copy / rel).read_bytes()) for mid, rel in paths.items()}
    add_littleroot_trees(worlds[7])
    updates = {}
    report["hoenn_presentation"] = apply_presentation(worlds, source, updates)
    report["qa11"] = audit_generated(worlds, SOURCE_MAPS, MAP_BGM, set(SOURCE_MAPS_STAGE10))
    for mid, relative in paths.items():
        updates[relative] = serialize(worlds[mid], EVENT_CLASSES)
    updates[manifest_path.name] = (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf8")
    replace_private_files(copy, updates)
    return report["hoenn_presentation"]
