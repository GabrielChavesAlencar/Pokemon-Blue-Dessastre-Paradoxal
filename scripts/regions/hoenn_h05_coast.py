"""Authored, Surf-only seams to the pinned Hoenn coast maps."""
from __future__ import annotations

import re

from hoenn_qa_phase3 import assemble_encounters, parse_reference_encounters
from pilot_hoenn import EVENT_CLASSES, open_tile, ruby, serialize, table_values
from server.ruby_marshal import RubyObject, loads

ROUTES = {107: 105, 109: 107, 110: 108}
COAST_BORDERS = (
    (107, "South", 0, 108, "North", 0),
    (108, "East", 0, 109, "West", 7),
    (109, "East", 0, 110, "West", 0),
    (110, "East", 0, 111, "West", 40),
)
MAP_INFOS = "Data/MapInfos.rxdata"
MAP_METADATA = "PBS/map_metadata_hoenn_pilot.txt"
CONNECTIONS = "PBS/map_connections.txt"
ENCOUNTERS = "PBS/encounters_hoenn_pilot.txt"


def coast_paths(mapping: dict[int, int]) -> set[str]:
    return {MAP_INFOS, MAP_METADATA, CONNECTIONS, ENCOUNTERS,
            *(f"Data/Map{mapping[key]:03}.rxdata" for key in ROUTES)}


def terrain_border(world, tileset, side: str) -> list[tuple[bool, bool]]:
    attrs = world.attrs
    (width, height, depth), cells = table_values(attrs["@data"].data, 3)
    _, tags = table_values(tileset.attrs["@terrain_tags"].data)
    if side in ("North", "South"):
        y = 0 if side == "North" else height - 1
        points = ((x, y) for x in range(width))
    else:
        x = 0 if side == "West" else width - 1
        points = ((x, y) for y in range(height))
    result = []
    for x, y in points:
        layers = (cells[x + width * (y + height * z)] for z in reversed(range(depth)))
        terrain = next((tags[tile] for tile in layers if tile < len(tags) and tags[tile]), 0)
        result.append((terrain in (5, 6, 7), open_tile(world, tileset, x, y)))
    return result


def verify_coast_seams(worlds: dict, tiles: list) -> None:
    for a, side_a, offset_a, b, side_b, offset_b in COAST_BORDERS:
        left = terrain_border(worlds[a], tiles[worlds[a].attrs["@tileset_id"]], side_a)
        right = terrain_border(worlds[b], tiles[worlds[b].attrs["@tileset_id"]], side_b)
        pairs = list(zip(left[offset_a:], right[offset_b:]))
        if not any(aquatic and peer_aquatic for (aquatic, _), (peer_aquatic, _) in pairs):
            raise ValueError(f"A costa de Hoenn perdeu a passagem de Surf entre {a} e {b}.")
        if any(not aquatic and floor and not peer_aquatic and peer_floor
               for (aquatic, floor), (peer_aquatic, peer_floor) in pairs):
            raise ValueError(f"A costa de Hoenn permite contornar Surf entre {a} e {b}.")


def border_rows(mapping: dict[int, int]) -> list[bytes]:
    return [
        f"{mapping[a]},{side_a},{offset_a},{mapping[b]},{side_b},{offset_b}".encode("ascii")
        for a, side_a, offset_a, b, side_b, offset_b in COAST_BORDERS
    ]


def read_coast(read, mapping: dict[int, int]) -> dict:
    return {
        key: loads(read(f"Data/Map{mapping[key]:03}.rxdata"))
        for key in (*ROUTES, 108, 111)
    }


def verify_coast(read, mapping: dict[int, int]) -> None:
    worlds = read_coast(read, mapping)
    tiles = loads(read("Data/Tilesets.rxdata"))
    verify_coast_seams(worlds, tiles)
    rows = [b",".join(part.strip() for part in line.split(b"#", 1)[0].split(b","))
            for line in read(CONNECTIONS).splitlines()]
    if any(rows.count(row) != 1 for row in border_rows(mapping)):
        raise ValueError("As bordas costeiras de Hoenn estão ausentes ou repetidas.")
    for path in (MAP_METADATA, ENCOUNTERS):
        sections = re.findall(rb"(?m)^\[([0-9]+)\]", read(path))
        if any(sum(int(section) == mapping[key] for section in sections) != 1 for key in ROUTES):
            raise ValueError(f"Seções costeiras de Hoenn ausentes ou duplicadas: {path}.")


def coast_overlay(read, mapping: dict[int, int], read_source) -> dict[str, bytes]:
    worlds = {
        key: loads(read(f"Data/Map{mapping[key]:03}.rxdata"))
        for key in (108, 111)
    }
    tiles = loads(read("Data/Tilesets.rxdata"))
    route_tileset = worlds[108].attrs["@tileset_id"]
    if tiles[route_tileset].attrs["@tileset_name"] != b"BLUE_HOENN_RSE_Outside":
        raise ValueError("A Rota 106 perdeu o tileset de origem.")
    infos = loads(read(MAP_INFOS))
    order = max(info.attrs.get("@order", 0) for info in infos.values())
    changes = {}
    metadata = []
    for key, route in ROUTES.items():
        mid = mapping[key]
        if mid in infos:
            raise ValueError(f"MapID da rota de Hoenn já registrado: {mid}.")
        world = loads(read_source(f"Data/Map{key:03}.rxdata"))
        if not isinstance(world, RubyObject) or world.name != "RPG::Map" or world.attrs["@tileset_id"] != 24:
            raise ValueError(f"Geometria costeira fora da origem auditada: {key}.")
        audio = ruby("RPG::AudioFile", name=b"", volume=100, pitch=100)
        world.attrs.update({
            "@events": {}, "@tileset_id": route_tileset, "@encounter_list": [],
            "@encounter_step": 30, "@autoplay_bgm": False, "@autoplay_bgs": False,
            "@bgm": audio, "@bgs": audio,
        })
        worlds[key] = world
        changes[f"Data/Map{mid:03}.rxdata"] = serialize(world, EVENT_CLASSES)
        name = f"Rota {route}"
        order += 1
        infos[mid] = ruby("RPG::MapInfo", name=name.encode("ascii"), parent_id=0, order=order,
                          expanded=False, scroll_x=0, scroll_y=0)
        metadata.append(f"[{mid}]\nName = {name}\nOutdoor = true\nSnapEdges = true\n".encode("ascii"))

    profiles, _ = parse_reference_encounters(read_source("PBS/encounters.txt").decode("utf-8-sig"), set(ROUTES))
    if profiles.keys() != ROUTES.keys() or any(
            not {"Water", "OldRod", "GoodRod", "SuperRod"} <= methods.keys() for methods in profiles.values()):
        raise ValueError("As rotas costeiras de Hoenn precisam dos encontros da fonte fixada.")
    blocks, _ = assemble_encounters(profiles, {key: mapping[key] for key in ROUTES}, {}, {})
    changes.update({
        MAP_INFOS: serialize(infos),
        MAP_METADATA: read(MAP_METADATA).rstrip(b"\r\n") + b"\n" + b"".join(metadata),
        ENCOUNTERS: read(ENCOUNTERS).rstrip(b"\r\n") + b"\n" + blocks,
        CONNECTIONS: read(CONNECTIONS).rstrip(b"\r\n") + b"\n" + b"\n".join(border_rows(mapping)) + b"\n",
    })
    verify_coast(lambda rel: changes[rel] if rel in changes else read(rel), mapping)
    return changes
