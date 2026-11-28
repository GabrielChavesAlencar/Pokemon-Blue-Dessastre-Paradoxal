"""Compile the original Unova corridor as an RMXP overlay for disposable QA."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import tempfile

import audit_unova_a04_mapids as a04
import audit_unova_a05_candidates as a05
import audit_unova_a06_references as a06
import audit_unova_a08_readiness as a08
import audit_unova_a10_dynamic_matrix as a10
from audit_unova_a13_private_qa import no_symlink_ancestors
from build_johto_events import EVENT_CLASSES, command, event_page, ruby
from compile_sinnoh_playable_j04 import passable_point
from generate_sinnoh_original_j10a import GRASS
from prepare_sinnoh_nine_original_j11c import decode1, proposal, table1
from server.ruby_marshal import RubyObject, loads
from stage import serialize
import unova_original_opening as opening

ROOT = opening.ROOT
OUTPUT = Path(".blue-work/unova/opening-fieldwork-qa")
TILESET = "BlueUnovaOpeningQA"
ART_PATH = f"Graphics/Tilesets/{TILESET}.png"
STORY = "Data/unova-opening-story.rb"
ENCOUNTERS_PBS = "PBS/encounters_unova_opening_qa.txt"
MAP_INFOS = "Data/MapInfos.rxdata"
TILESETS = "Data/Tilesets.rxdata"
MAP_IDS = {
    opening.BEDROOM: 276,
    opening.HOUSE: 277,
    opening.NUVEMA: 278,
    opening.LAB: 279,
    opening.ROUTE: 280,
    opening.ACCUMULA: 281,
    opening.CENTER: 282,
}
JOURNEY = (
    opening.BEDROOM, opening.HOUSE, opening.NUVEMA, opening.LAB, opening.NUVEMA,
    opening.ROUTE, opening.ACCUMULA, opening.CENTER, opening.ACCUMULA,
    opening.ROUTE, opening.NUVEMA, opening.HOUSE, opening.BEDROOM,
)
FIELDWORK = {
    opening.LAB: ("check_in", 11, 3),
    opening.ROUTE: ("read_gauge", 18, 13),
    opening.CENTER: ("deliver_report", 10, 4),
}
ENCOUNTERS = ((60, "PATRAT", 2, 3), (40, "LILLIPUP", 2, 3))


def encounters_pbs():
    rows = (",".join(map(str, encounter)) for encounter in ENCOUNTERS)
    return (f"[{MAP_IDS[opening.ROUTE]:03d}]\nLand,21\n" + "\n".join(rows) + "\n").encode("ascii")


def guard_route(page):
    transfer, terminator = page.attrs["@list"]
    transfer.attrs["@indent"] = 1
    prompt = command(355, b"BlueUnovaOpeningStory.block_route")
    prompt.attrs["@indent"] = 1
    page.attrs["@list"] = [
        command(111, 12, b"BlueUnovaOpeningStory.checked_in?"),
        transfer, command(411), prompt, command(412), terminator,
    ]


def fieldwork_event(world, tiles, symbol, map_id):
    action, x, y = FIELDWORK[symbol]
    events = world.attrs["@events"]
    if any((event.attrs["@x"], event.attrs["@y"]) == (x, y) for event in events.values()):
        raise ValueError("Interação do posto sobre uma porta.")
    passable_point(world, tiles, x, y + 1)
    event_id = len(events) + 1
    page = event_page(script=f"BlueUnovaOpeningStory.{action}")
    events[event_id] = ruby("RPG::Event", id=event_id, name=action.encode("ascii"),
                            x=x, y=y, pages=[page])
    return {"map": map_id, "event": event_id, "approach": [x, y + 1]}


def read_data(game, relative):
    path = game / relative
    no_symlink_ancestors(path)
    return a04._bounded_file(path)


def common_destinations(game):
    entries = loads(read_data(game, "Data/CommonEvents.rxdata"))
    if not isinstance(entries, list):
        raise ValueError("CommonEvents fora do formato RMXP.")
    destinations = set()
    for event in entries:
        if event is None:
            continue
        if not isinstance(event, RubyObject) or event.name != "RPG::CommonEvent":
            raise ValueError("Evento comum fora do formato RMXP.")
        for command in event.attrs["@list"]:
            if command.attrs["@code"] == 201:
                args = command.attrs["@parameters"]
                if len(args) >= 2 and args[0] == 0:
                    destinations.add(args[1])
    return destinations


def other_claims(game):
    data = game / "Data"
    claims = common_destinations(game)
    system = loads(read_data(game, "Data/System.rxdata"))
    if not isinstance(system, RubyObject) or system.name != "RPG::System":
        raise ValueError("System fora do formato RMXP.")
    claims.update(value for key, value in system.attrs.items()
                  if key.endswith("map_id") and type(value) is int)
    links = loads(read_data(game, "Data/map_connections.dat"))
    if not isinstance(links, list) or any(not isinstance(row, list) or len(row) != 6 for row in links):
        raise ValueError("Conexões compiladas fora do formato esperado.")
    claims.update(row[index] for row in links for index in (0, 3))
    for relative in ("Data/map_metadata.dat", "Data/metadata.dat"):
        metadata = loads(read_data(game, relative))
        if not isinstance(metadata, dict):
            raise ValueError("Metadados compilados fora do formato esperado.")
        if relative == "Data/map_metadata.dat":
            claims.update(key for key in metadata if type(key) is int)
        for entry in metadata.values():
            if isinstance(entry, RubyObject):
                for field in ("@home", "@home_position", "@healing_spot", "@respawn"):
                    point = entry.attrs.get(field)
                    if isinstance(point, list) and point and type(point[0]) is int:
                        claims.add(point[0])
    for name in a08.REGION_PROOFS:
        path = data / name
        if path.exists() or path.is_symlink():
            no_symlink_ancestors(path)
            ids, _ = a10.candidate_destinations(a08.read_json(path))
            claims.update(ids)
    return claims


def inspect_baselines(game, android_manifest):
    snapshot = a04.scan_source(game, "DECADES", base=True)
    report = a04.analyze(snapshot, {})
    potential = set(MAP_IDS.values())
    android, android_ids = a05.read_android_occupancy(android_manifest)
    occupied = set(report["observed_or_declared_occupied_map_ids"]) | android_ids
    if blocked := potential & occupied:
        raise ValueError(f"MapIDs de QA já ocupados no Windows ou Android: {sorted(blocked)}")
    static = a06.audit(game, report)
    if static["map_read_failures"]:
        raise ValueError("A leitura de eventos da base Windows ficou incompleta.")
    used = set(static["static_destination_mapids"]) | other_claims(game)
    if blocked := potential & used:
        raise ValueError(f"MapIDs de QA já referenciados na base Windows: {sorted(blocked)}")
    return {
        "windows_mapinfos_sha256": snapshot["mapinfos_sha256"],
        "windows_map_files_parsed": static["map_files_parsed"],
        "android": android,
        "windows_variable_transfers": static["dynamic_transfer_commands"],
        "dynamic_script_references_certified": False,
    }


def compile_overlay(game, android_manifest):
    no_symlink_ancestors(game)
    evidence = inspect_baselines(game, android_manifest)
    base_infos = read_data(game, MAP_INFOS)
    base_tiles = read_data(game, TILESETS)
    if opening.checksum(base_infos) != evidence["windows_mapinfos_sha256"]:
        raise ValueError("MapInfos mudou depois da auditoria.")
    infos, tiles = loads(base_infos), loads(base_tiles)
    if not isinstance(tiles, list) or not 0 < len(tiles) < 5000:
        raise ValueError("Tilesets fora do formato RMXP.")
    if (game / ART_PATH).exists() or (game / ART_PATH).is_symlink():
        raise ValueError("Já existe um gráfico com o nome do corredor de QA.")

    sources, manifest = opening.generate()
    art = sources["BlueOriginalOpening.png"]
    tile_id = len(tiles)
    tile = proposal("J10A_INTERIORS", manifest["tileset_sha256"], tile_id)
    tile.attrs.update({"@name": b"Blue Unova abertura QA", "@tileset_name": TILESET.encode("ascii")})
    tags = decode1(tile.attrs["@terrain_tags"])
    tags[GRASS] = 2  # Essentials 21.1 Grass terrain
    tile.attrs["@terrain_tags"] = table1(tags)
    tiles.append(tile)
    files = {
        ART_PATH: art,
        STORY: (ROOT / "scripts/regions/UnovaOpeningStory.rb").read_bytes(),
        ENCOUNTERS_PBS: encounters_pbs(),
    }
    doors = []
    fieldwork = {}
    order = max(info.attrs["@order"] for info in infos.values())
    for symbol, map_id in MAP_IDS.items():
        row = manifest["maps"][symbol]
        world = loads(sources[row["file"]])
        world.attrs["@tileset_id"] = tile_id
        order += 1
        infos[map_id] = ruby("RPG::MapInfo", name=("[Unova QA] " + symbol).encode("ascii"),
                             parent_id=0, order=order, expanded=False, scroll_x=0, scroll_y=0)
        for event_id, door in enumerate(row["candidate_doors"], 1):
            x, y = door["threshold"]
            passable_point(world, tiles, x, y)
            dest_id = MAP_IDS[door["destination"]]
            page = event_page(warp=(dest_id, *door["arrival"]), touch=True)
            if symbol == opening.NUVEMA and door["destination"] == opening.ROUTE:
                guard_route(page)
            world.attrs["@events"][event_id] = ruby(
                "RPG::Event", id=event_id, name=f"Unova QA door {event_id}".encode("ascii"),
                x=x, y=y, pages=[page])
            doors.append({"source": map_id, "event": event_id, "threshold": door["threshold"],
                          "destination": dest_id, "arrival": door["arrival"]})
        if symbol in FIELDWORK:
            action = FIELDWORK[symbol][0]
            fieldwork[action] = fieldwork_event(world, tiles, symbol, map_id)
        files[f"Data/Map{map_id:03d}.rxdata"] = serialize(world, EVENT_CLASSES)

    thresholds = {(door["source"], *door["threshold"]) for door in doors}
    for door in doors:
        destination = door["destination"]
        if (destination, *door["arrival"]) in thresholds:
            raise ValueError("A chegada de uma porta coincide com outro gatilho.")
        passable_point(loads(files[f"Data/Map{destination:03d}.rxdata"]), tiles, *door["arrival"])
    files[MAP_INFOS] = serialize(infos)
    files[TILESETS] = serialize(tiles)
    return files, {
        "status": "OPENING_RMXP_QA_OVERLAY",
        "publishable": False,
        "baselines": evidence,
        "base_tilesets_sha256": opening.checksum(base_tiles),
        "map_ids": MAP_IDS,
        "tileset_id": tile_id,
        "spawn": [MAP_IDS[opening.BEDROOM], 8, 6],
        "journey": [MAP_IDS[symbol] for symbol in JOURNEY],
        "doors": doors,
        "fieldwork": fieldwork,
        "encounters": ENCOUNTERS,
        "files_sha256": {name: opening.checksum(raw) for name, raw in files.items()},
    }


def write_overlay(project, game, android_manifest):
    target = project / OUTPUT
    no_symlink_ancestors(target)
    if target.exists():
        raise ValueError("Já existe uma exportação do corredor RMXP.")
    if target.is_relative_to(game) or game.is_relative_to(target):
        raise ValueError("A exportação precisa ficar separada da base.")
    files, receipt = compile_overlay(game, android_manifest)
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".unova-rmxp-", dir=target.parent) as directory:
        pending = Path(directory) / "overlay"
        for name, raw in files.items():
            path = pending / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        (pending / "manifest.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        pending.rename(target)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-game", required=True, type=Path)
    parser.add_argument("--android-manifest", required=True, type=Path)
    args = parser.parse_args()
    game = args.base_game.absolute()
    print(json.dumps(write_overlay(ROOT, game, args.android_manifest), indent=2))


if __name__ == "__main__":
    main()
