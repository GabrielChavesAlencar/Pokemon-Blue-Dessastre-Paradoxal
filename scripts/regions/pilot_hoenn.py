"""Build the local Hoenn test game from pinned RMXP geometry and a Blue copy."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import uuid
import zlib
from collections import deque
from pathlib import Path

from build_johto_elm_lab_v1 import table_values
from build_johto_events import EVENT_CLASSES, command, event_page, ruby
from compile_johto_connections import merge_pbs
from johto_qa import SAVE, SYSTEM_CLASSES, Marshal, RubyString, dump, json_bytes, regular, safe_path
from server.ruby_marshal import RubyObject, loads, text
from stage import ROOT, serialize
from hoenn_stage3 import (
    SOURCE_MAPS_STAGE3, OFFSET_BORDERS, WARP_PAIRS_STAGE3,
    LAND_ENCOUNTERS_STAGE3, TRAINERS_STAGE3, PICKUPS_STAGE3,
    SIGNS_STAGE3, NPCS_STAGE3, FOREST_AQUA_TRIGGERS,
    FOREST_AQUA_PBS, FOREST_AQUA_TEAM,
)
from hoenn_stage4 import (
    SOURCE_MAPS_STAGE4, OFFSET_BORDERS_STAGE4, WARP_PAIRS_STAGE4,
    LAND_ENCOUNTERS_STAGE4, CAVE_ENCOUNTERS_STAGE4, TRAINERS_STAGE4,
    ROXANNE_PBS, ROXANNE_TEAM, TUNNEL_AQUA_PBS, TUNNEL_AQUA_TEAM,
    PICKUPS_STAGE4, SIGNS_STAGE4, NPCS_STAGE4, CUT_TREES_STAGE4,
    RUSTBORO_THEFT_TRIGGERS, TUNNEL_AQUA_EVENT, ROXANNE_EVENT,
    TUNNEL_VERDANTURF_GATE,
)
from hoenn_stage5 import (
    SOURCE_MAPS_STAGE5, OFFSET_BORDERS_STAGE5, WARP_PAIRS_STAGE5,
    BOAT_POINTS_STAGE5, CAVE_ENCOUNTERS_STAGE5, TRAINERS_STAGE5,
    BRAWLY_PBS, BRAWLY_TEAM, MUSEUM_AQUA, NPCS_STAGE5,
    MUSEUM_FEE_GATE, SLATEPORT_NORTH_GATE, SIGNS_STAGE5, PICKUPS_STAGE5,
)
from hoenn_stage6 import (
    SOURCE_MAPS_STAGE6, OFFSET_BORDERS_STAGE6, WARP_PAIRS_STAGE6,
    CYCLE_TRANSFERS_STAGE6, LAND_ENCOUNTERS_STAGE6, TRAINERS_STAGE6,
    WATTSON_PBS, WATTSON_TEAM, WALLY_PBS, WALLY_TEAM, RIVAL_110_TEAMS,
    RIVAL_110_EVENT, RIVAL_110_TRIGGERS, WALLY_EVENT,
    WALLY_UNCLE_EVENT, WATTSON_EVENT, RYDEL_EVENT, GYM_GATES_STAGE6,
    GYM_SWITCHES_STAGE6, NPCS_STAGE6, PICKUPS_STAGE6, SIGNS_STAGE6,
    MAUVILLE_FUTURE_GATES,
)
from hoenn_stage7 import (
    SOURCE_MAPS_STAGE7, OFFSET_BORDERS_STAGE7, WARP_PAIRS_STAGE7,
    CABLE_POINTS_STAGE7, LAND_ENCOUNTERS_STAGE7, CAVE_ENCOUNTERS_STAGE7,
    TRAINERS_STAGE7, FLANNERY_PBS, FLANNERY_TEAM,
    TABITHA_PBS, TABITHA_TEAM, MAXIE_PBS, MAXIE_TEAM,
    MAGMA_GRUNTS_STAGE7, MAGMA_GRUNT_EVENTS, TABITHA_EVENT, MAXIE_EVENT,
    METEORITE_MACHINE_EVENT, METEOR_FALLS_CUTSCENE, FLANNERY_EVENT,
    ROUTE112_MAGMA_BLOCKERS, NPCS_STAGE7, FUTURE_GATES_STAGE7,
    PICKUPS_STAGE7, SIGNS_STAGE7, GYM_STEAM_PAIRS_STAGE7,
)
from hoenn_stage8 import (
    SOURCE_MAPS_STAGE8, OFFSET_BORDERS_STAGE8, WARP_PAIRS_STAGE8,
    LAND_ENCOUNTERS_STAGE8, NORMAN_EVENT, NORMAN_PBS, NORMAN_TEAM,
    WINONA_EVENT, WINONA_PBS, WINONA_TEAM, SHELLY_EVENT, SHELLY_PBS, SHELLY_TEAM,
    AQUA_INSTITUTE, RIVAL_119_EVENT, RIVAL_LILYCOVE_EVENT, RIVAL_119_TEAMS,
    RIVAL_LILYCOVE_TEAMS, TRAINERS_STAGE8, STEVEN_SCOPE_EVENT,
    FORTREE_KECLEON_EVENT, ROUTE120_KECLEON_EVENT, WEATHER_REWARD_EVENT,
    NPCS_STAGE8, FUTURE_GATES_STAGE8, SIGNS_STAGE8, PICKUPS_STAGE8,
    NORMAN_GYM_DOORS,
)
from hoenn_stage9 import (
    SOURCE_MAPS_STAGE9, SURF_BORDERS_STAGE9,
    TATE_LIZA_EVENTS, TATE_LIZA_PBS, TATE_LIZA_TEAM,
    MATT_PBS, MATT_TEAM, MAXIE_HIDEOUT_PBS, MAXIE_HIDEOUT_TEAM,
    TABITHA_HIDEOUT_PBS, TABITHA_HIDEOUT_TEAM, MAXIE_SPACE_PBS,
    MAXIE_SPACE_TEAM, TABITHA_SPACE_PBS, TABITHA_SPACE_TEAM,
    ARCHIE_ORB_EVENT, MT_PYRE_ARCHIE, MT_PYRE_OLD_LADY,
    TABITHA_HIDEOUT_EVENT, MAXIE_HIDEOUT_EVENT, GROUDON_CUTSCENE_EVENT,
    MATT_HIDEOUT_EVENT, SUBMARINE_EVENT,
    SPACE_MAXIE_EVENT, SPACE_STEVEN_EVENT, SPACE_GRUNT_EVENTS,
    TRAINERS_STAGE9, PYRE_AQUA_GRUNTS, MAGMA_HIDEOUT_GRUNTS,
    AQUA_HIDEOUT_GRUNTS, NPCS_STAGE9, SIGNS_STAGE9,
    MAGMA_HIDEOUT_GATE, AQUA_HIDEOUT_GATE,
)

from hoenn_stage10 import (
    SOURCE_MAPS_STAGE10, SURF_BORDERS_STAGE10, STAGE10_MAP_GRAPH_EDGES,
    JUAN_EVENT, JUAN_PBS, JUAN_TEAM, ARCHIE_PBS, ARCHIE_TEAM,
    WALLY_ROAD_PBS, WALLY_ROAD_TEAM, ELITE_EVENTS, ELITE_PBS,
    ELITE_TEAMS, CHAMPION_EVENT, CHAMPION_PBS, CHAMPION_TEAM,
    SOOTOPOLIS_CRISIS_EVENT, ORIGIN_WALLACE_EVENT,
    SKY_PILLAR_WALLACE_EVENT, RAYQUAZA_EVENT,
    SEAFLOOR_AWAKENING_EVENT, WALLY_VICTORY_ROAD_EVENT,
    LEAGUE_EXIT_EVENT, HALL_OF_FAME_EVENT, STAGE10_SIGNS,
)
from hoenn_qa_phase3 import (
    parse_reference_encounters, assemble_encounters,
    reauthor_safe_items_and_audit,
)
from hoenn_qa_phase4 import install_simple_obstacles

UPSTREAM = "c59233bdbaac4fbfeca6aa01c7f05be628da2a92"
SOURCE_MAPS = {
    7: "Littleroot Town", 8: "Casa do jogador", 11: "Laboratório do Birch",
    101: "Rota 101", 12: "Oldale Town", 13: "Centro Pokémon de Oldale",
    14: "Poké Mart de Oldale", 102: "Rota 102", 103: "Rota 103",
    **SOURCE_MAPS_STAGE3,
    **SOURCE_MAPS_STAGE4,
    **SOURCE_MAPS_STAGE5,
    **SOURCE_MAPS_STAGE6,
    **SOURCE_MAPS_STAGE7,
    **SOURCE_MAPS_STAGE8,
    **SOURCE_MAPS_STAGE9,
    **SOURCE_MAPS_STAGE10,
}
WARP_PAIRS = (
    ((7, 5, 8), (7, 5, 9), (8, 10, 10), (8, 10, 9)),
    ((8, 10, 4), (8, 10, 5), (8, 28, 3), (8, 28, 4)),
    ((7, 7, 16), (7, 7, 17), (11, 8, 14), (11, 8, 13)),
    ((12, 6, 16), (12, 6, 17), (13, 8, 10), (13, 8, 9)),
    ((12, 14, 6), (12, 14, 7), (14, 5, 9), (14, 5, 8)),
) + WARP_PAIRS_STAGE3 + WARP_PAIRS_STAGE4 + WARP_PAIRS_STAGE5 + WARP_PAIRS_STAGE6 + WARP_PAIRS_STAGE7 + WARP_PAIRS_STAGE8
PEOPLE = (
    (8, 4, 8, "Mae", "NPC_GSC_Mom", "BlueHoennPilot.mother"),
    (11, 8, 6, "Birch", "NPC_ORAS_Professor_Birch", "BlueHoennPilot.birch"),
    (11, 7, 5, "Treecko", "Object_Ball", "BlueHoennPilot.choose_starter(:TREECKO)"),
    (11, 8, 5, "Torchic", "Object_Ball", "BlueHoennPilot.choose_starter(:TORCHIC)"),
    (11, 9, 5, "Mudkip", "Object_Ball", "BlueHoennPilot.choose_starter(:MUDKIP)"),
    (13, 9, 4, "Enfermeira", "NPC_DPP_PokeCenter_Nurse", "BlueHoennPilot.heal"),
    (14, 3, 5, "Mart", "NPC_DPP_PokeMart_Man", "BlueHoennPilot.mart"),
)
BGM = {
    "Littleroot": "City - Littleroot (Littleroot Town)",
    "Birch": "Location - Birch Pokemon Lab (Birch Pokemon Lab)",
    "Route101": "Route 101 (Route 101)",
    "Oldale": "City - Oldale (Oldale Town)",
    "Center": "Location - Pokemon Center (Pokemon Center)",
    "Wild": "Battle Music - Wild Pokemon (Battle! (Wild Pokemon))",
    "WildVictory": "Battle Victory - Wild Pokemon (Victory! (Wild Pokemon))",
}
MAP_BGM = {7: "Littleroot", 8: "Littleroot", 11: "Birch", 101: "Route101",
           12: "Oldale", 13: "Center", 14: "Oldale", 102: "Route101", 103: "Route101",
           16: "Oldale", 17: "Center", 18: "Oldale", 19: "Oldale", 20: "Birch",
           104: "Route101", 105: "Oldale", 106: "Oldale", 156: "Route101",
           21: "Oldale", 22: "Center", 23: "Oldale", 24: "Oldale", 25: "Birch",
           26: "Birch", 27: "Birch", 130: "Route101", 131: "Oldale",
           157: "Route101",
           28: "Oldale", 29: "Center", 30: "Oldale", 31: "Birch",
           32: "Oldale", 33: "Oldale", 34: "Center", 35: "Oldale",
           36: "Oldale", 37: "Oldale", 38: "Birch", 39: "Birch",
           40: "Oldale", 108: "Route101", 111: "Route101",
           112: "Oldale", 159: "Route101", 160: "Route101",
           161: "Route101", 162: "Route101",
           41: "Oldale", 42: "Center", 43: "Oldale", 44: "Oldale",
           45: "Oldale", 46: "Oldale", 47: "Birch",
           113: "Route101", 114: "Route101", 115: "Oldale",
           **{mid: ("Center" if mid in (54, 59) else "Birch" if mid in (63, 124) else
                    "Route101" if mid in (117, 121, 123, 125, 177, 178, 180, 191, 192)
                    else "Oldale") for mid in SOURCE_MAPS_STAGE7},
           **{mid: ("Center" if mid in (49, 65, 71) else
                    "Route101" if mid in (132, 134, 135, 138, 139) else
                    "Birch" if mid in (68, 137) else "Oldale")
              for mid in SOURCE_MAPS_STAGE8},
           **{mid: ("Center" if mid == 77 else
                    "Birch" if mid in (81,82,189,213,217) else
                    "Route101" if mid in (141,144,212) else "Oldale")
              for mid in SOURCE_MAPS_STAGE9}}
OUTDOORS = (7, 12, 16, 21, 28, 32, 41, 53, 58, 101, 102, 103, 104,
            108, 111, 113, 114, 117, 121, 123, 125, 130, 132, 134,
            135, 138, 139, 141, 144, 156, 178, 180, 212, 213, 48, 64, 69, 76,
            83,88,91,146,147,148,149,150,151,152,153,154,155,241,322)
BORDERS = ((7, "North", 101, "South"), (12, "South", 101, "North"),
           (102, "East", 12, "West"), (103, "South", 12, "North"))
LAND_ENCOUNTERS = {
    101: ((45, "ZIGZAGOON", 2, 3), (35, "POOCHYENA", 2, 3), (20, "WURMPLE", 2, 3)),
    102: ((30, "POOCHYENA", 3, 4), (15, "ZIGZAGOON", 3, 4), (30, "WURMPLE", 3, 4),
          (10, "LOTAD", 3, 4), (10, "SEEDOT", 3, 3), (4, "RALTS", 4, 4), (1, "SURSKIT", 3, 3)),
    103: ((60, "POOCHYENA", 2, 4), (20, "ZIGZAGOON", 3, 4), (20, "WINGULL", 2, 4)),
    **LAND_ENCOUNTERS_STAGE3,
    **LAND_ENCOUNTERS_STAGE4,
    **LAND_ENCOUNTERS_STAGE6,
    **LAND_ENCOUNTERS_STAGE7,
    **LAND_ENCOUNTERS_STAGE8,
}
CAVE_ENCOUNTERS = {**CAVE_ENCOUNTERS_STAGE4, **CAVE_ENCOUNTERS_STAGE5, **CAVE_ENCOUNTERS_STAGE7}
ROUTE_102_TRAINERS = (
    (33, 14, "YOUNGSTER", "Calvin", "trainer_YOUNGSTER", (("POOCHYENA", 5),)),
    (25, 15, "BUGCATCHER", "Rick", "trainer_BUGCATCHER", (("WURMPLE", 4), ("WURMPLE", 4))),
    (19, 4, "YOUNGSTER", "Allen", "trainer_YOUNGSTER", (("ZIGZAGOON", 4), ("TAILLOW", 4))),
    (8, 7, "LASS", "Tiana", "trainer_LASS", (("ZIGZAGOON", 4), ("SHROOMISH", 4))),
)
# Native RIVAL1 class; versions cannot overlap the four Route 102 trainers.
RIVAL_TEAMS = {"TREECKO": ("TORCHIC", 210), "TORCHIC": ("MUDKIP", 211),
               "MUDKIP": ("TREECKO", 212)}
RIVAL_NAMES = ("May", "Brendan")
START = (8, 25, 6)
PROFILE = "Hoenn Piloto"
PLUGIN = "Plugins/ZZZZZ Blue Hoenn Pilot"
STORY = "Plugins/ZZZZ Blue Story and Presentation"
PNG = b"\x89PNG\r\n\x1a\n"
COPY_DIRS = ("Audio", "Data", "Fonts", "Graphics", "PBS", "Plugins")
ROOT_FILES = ("Game.exe", "Game.ini", "mkxp.json", "preload.rb", "soundfont.sf2", "Credits.txt")


class Source:
    def __init__(self, data: Path, inventory: Path):
        manifest = json.loads(regular(inventory).read_text("utf-8"))
        if manifest["revision"] != UPSTREAM or manifest["truncated"] is not False:
            raise ValueError("Use a árvore Hoenn completa da revisão auditada")
        self.blobs = {row["path"]: row["sha"] for row in manifest["tree"] if row["type"] == "blob"}
        self.data = data

    def read(self, name: str) -> bytes:
        path = self.data / name
        if not path.exists() and name.startswith("Data/"):
            path = self.data / Path(name).name
        blob = regular(path).read_bytes()
        actual = hashlib.sha1(f"blob {len(blob)}\0".encode("ascii") + blob).hexdigest()
        if actual != self.blobs.get(name):
            raise ValueError(f"Arquivo de origem divergente da revisão Hoenn: {name}")
        return blob


# Decode each Ruby Marshal table only once. Route 104 alone is 150x80;
# repeatedly parsing its 3-layer tiles during a BFS is prohibitively slow.
_TILE_CACHE = {}


def open_tile(map_data, tileset, x, y):
    key = (id(map_data), id(tileset))
    cached = _TILE_CACHE.get(key)
    if cached is None:
        attrs = map_data.attrs
        dims, cells = table_values(attrs["@data"].data, 3)
        _, passages = table_values(tileset.attrs["@passages"].data)
        _, priorities = table_values(tileset.attrs["@priorities"].data)
        cached = (dims, cells, passages, priorities)
        _TILE_CACHE[key] = cached
    (w, h, depth), cells, passages, priorities = cached
    if not (0 <= x < w and 0 <= y < h):
        return False
    for layer in reversed(range(depth)):
        tile = cells[x + w * (y + h * layer)]
        if not tile:
            continue
        if passages[tile] & 15:
            return False
        if priorities[tile] == 0:
            return True
    return False


def reachable(start, points, tiles, maps, edges, blocked):
    """Conservative 4-way tile check, including physical map borders."""
    def open_point(p):
        mid, x, y = p
        return p not in blocked and open_tile(maps[mid], tiles[mid], x, y)

    if not open_point(start):
        raise ValueError(f"Ponto inicial bloqueado: {start}")
    remaining = set(points) - {start}
    visited = {start}
    queue = deque([start])
    while queue and remaining:
        mid, x, y = queue.popleft()
        neighbors = [(mid, x + dx, y + dy) for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0))]
        neighbors.extend(edges.get((mid, x, y), ()))
        for point in neighbors:
            if point not in visited and open_point(point):
                remaining.discard(point)
                visited.add(point)
                queue.append(point)
    if remaining:
        raise ValueError(f"Pontos do piloto sem caminho estático: {sorted(remaining)}")


def validate_geometry(maps, tiles):
    edges, required = {}, set()
    blocked = {row[:3] for row in PEOPLE}
    for a, a_arrival, b, b_arrival in WARP_PAIRS:
        # A door event can sit on an impassable threshold tile (the donor's
        # indoor doors do). Validate the STANDING CELLS on either side, not
        # the blocked event graphics themselves.
        if a[0] != a_arrival[0] or b[0] != b_arrival[0]:
            raise ValueError("Warp Hoenn cruza MapID incorreto na origem")
        def close_to_door(door, landing):
            dx, dy = abs(door[1] - landing[1]), abs(door[2] - landing[2])
            return dx <= 1 and dy <= 1 and dx + dy >= 1
        if not close_to_door(a, a_arrival) or not close_to_door(b, b_arrival):
            raise ValueError(f"Destino do warp não é vizinho da porta: {a}/{b}")
        edges.setdefault(a_arrival, []).append(b_arrival)
        edges.setdefault(b_arrival, []).append(a_arrival)
        required.update((a_arrival, b_arrival))
    # Emerald's Route 102 -> Petalburg and Route 104 -> Petalburg borders
    # have real nonzero offsets. Zip only the overlapping segment.
    for first, edge, off_a, second, other_edge, off_b in (
        *((a, d1, 0, b, d2, 0) for a, d1, b, d2 in BORDERS),
        *OFFSET_BORDERS,
        *OFFSET_BORDERS_STAGE4,
        *OFFSET_BORDERS_STAGE5,
        *OFFSET_BORDERS_STAGE6,
        *OFFSET_BORDERS_STAGE7,
        *OFFSET_BORDERS_STAGE8,
    ):
        def border(map_id, side):
            w, h = (maps[map_id].attrs[key] for key in ("@width", "@height"))
            if side in ("North", "South"):
                return [(map_id, x, 0 if side == "North" else h - 1) for x in range(w)]
            return [(map_id, 0 if side == "West" else w - 1, y) for y in range(h)]

        pa, pb = border(first, edge), border(second, other_edge)
        if off_a < 0 or off_b < 0 or off_a >= len(pa) or off_b >= len(pb):
            raise ValueError(f"Deslocamento da borda Hoenn inválido: {first}/{second}")
        pairs = [(a, b) for a, b in zip(pa[off_a:], pb[off_b:])
                 if open_tile(maps[first], tiles[first], *a[1:])
                 and open_tile(maps[second], tiles[second], *b[1:])]
        if not pairs:
            raise ValueError(f"Borda Hoenn sem cruzamento passável: {first}/{second}")
        required.update(pairs[0])
        for a, b in pairs:
            edges.setdefault(a, []).append(b)
            edges.setdefault(b, []).append(a)
    # Test the exact standing cells used to interact with the NPCs and Poké Balls.
    required.update(((8, 4, 9), (11, 8, 7), (11, 7, 6), (11, 9, 6), (13, 9, 6), (14, 5, 5)))
    # The ferry is a controlled story-only transfer between Route104 house,
    # Dewford and Slateport beach, using passable pinned donor landing tiles.
    house, dewford, beach = BOAT_POINTS_STAGE5
    for left, right in ((house, dewford), (dewford, beach)):
        edges.setdefault(left, []).append(right)
        edges.setdefault(right, []).append(left)
    required.update(BOAT_POINTS_STAGE5)
    # Cycling Road is reached only through an item-gated event, not a free
    # physical warp. Include its landing cells for geometry verification.
    for src, ex, ey, sx, sy, dest, dx, dy in CYCLE_TRANSFERS_STAGE6:
        if not (open_tile(maps[src], tiles[src], sx, sy) and
                open_tile(maps[dest], tiles[dest], dx, dy)):
            raise ValueError(f"Portaria de Cycling Road sem célula passável: {src}/{dest}")
        edges.setdefault((src, sx, sy), []).append((dest, dx, dy))
        edges.setdefault((dest, dx, dy), []).append((src, sx, sy))
        required.update(((src, sx, sy), (dest, dx, dy)))
    # Summit cable only unlocks after the meteorite cutscene. Static
    # connectivity validation includes the conditional edge but the real
    # runtime checks Hoenn's quest flag before moving the player.
    lower, upper = CABLE_POINTS_STAGE7
    if not (open_tile(maps[lower[0]], tiles[lower[0]], *lower[1:]) and
            open_tile(maps[upper[0]], tiles[upper[0]], *upper[1:])):
        raise ValueError("Pontos do teleférico bloqueados em RXDATA auditado")
    edges.setdefault(lower, []).append(upper)
    edges.setdefault(upper, []).append(lower)
    required.update((lower, upper))
    reachable(START, required, tiles, maps, edges, blocked)
    return edges, required


def starter_ball_positions(maps, tiles, edges, required):
    """Locate three separate Poké Ball objects on pinned Route 101 geometry.

    Never use invented coordinates: require all approaches reachable on actual
    map tiles before constructing a private pilot.
    """
    width, height = (maps[101].attrs[key] for key in ("@width", "@height"))
    blocked = {row[:3] for row in PEOPLE}
    # Route 101 donor geometry is 20x20. The southern entry is at y=18/19;
    # three balls must sit north of the Birch encounter, around row 16.
    for y in sorted(range(3, min(height - 2, 18)), key=lambda v: abs(v - 16)):
        for x in sorted(range(2, width - 5), key=lambda v: abs(v + 2 - 8)):
            balls = [(101, x + dx, y) for dx in (0, 2, 4)]
            approach = [(101, px, y + 1) for _, px, _ in balls]
            if not all(open_tile(maps[101], tiles[101], px, py)
                       for _, px, py in balls + approach):
                continue
            if set(balls) & (blocked | {(101, 10, 18), (101, 11, 18)}):
                continue
            try:
                reachable(START, required | set(approach), tiles, maps, edges,
                          blocked | set(balls))
            except ValueError:
                continue
            return balls
    raise ValueError("Maleta Birch: três Poké Bolas sem posições caminháveis verificadas")


def rival_position(maps, tiles, edges, required, balls):
    """Place the Route 103 rival on a reachable northern approach."""
    width, height = (maps[103].attrs[key] for key in ("@width", "@height"))
    blocked = {row[:3] for row in PEOPLE} | set(balls)
    # Pinned Map103 is 80x20, with its main approach near (10,7).
    # Prefer the canonical player-facing path instead of a distant side branch.
    for y in sorted(range(2, height - 2), key=lambda v: abs(v - 7)):
        for x in sorted(range(1, width - 1), key=lambda v: abs(v - 10)):
            if not (open_tile(maps[103], tiles[103], x, y)
                    and open_tile(maps[103], tiles[103], x, y + 1)):
                continue
            try:
                reachable(START, required | {(103, x, y), (103, x, y + 1)},
                          tiles, maps, edges, blocked)
            except ValueError:
                continue
            return (103, x, y)
    raise ValueError("Rota 103: nenhum ponto acessível para o encontro do rival")


def rival_sprite(game: Path) -> tuple[str, bool]:
    """Prefer a native rival sprite; fall back to a verified native class."""
    for candidate in ("NPC_ORAS_May", "NPC_ORAS_Brendan",
                      "NPC_RSE_May", "NPC_RSE_Brendan"):
        path = game / f"Graphics/Characters/{candidate}.png"
        if path.is_file() and not path.is_symlink() and path.read_bytes().startswith(PNG):
            return candidate, False
    return "trainer_LASS", True


def startup(blob: bytes, *, region="hoenn", module="BlueHoennPilot") -> bytes:
    rows = Marshal(blob).read()
    mains = [row for row in rows if row[1] == b"Main"]
    if len(mains) != 1:
        raise ValueError("A base não tem um único script Main")
    row = mains[0]
    source = zlib.decompress(row[2]).decode("utf-8")
    run_plugins = "    PluginManager.runPlugins"
    initialize = "    Game.initialize"
    if source.count(run_plugins) != 1 or source.count(initialize) != 1:
        raise ValueError("O fluxo de inicialização do jogo difere da base conhecida")
    before = """    if File.file?("Data/blue-hoenn-compile-request.txt")
      $DEBUG = true
      Object.send(:define_method, :pbPrintException) do |error|
        File.write("Data/blue-hoenn-compile-error.txt", error.full_message)
        exit! 1
      end
      %w[PluginScripts.rxdata encounters.dat].each do |name|
        path = "Data/#{name}"
        File.delete(path) if File.file?(path)
      end
    end
"""
    after = """    if File.file?("Data/blue-hoenn-compile-request.txt")
      begin
        BlueHoennPilot.verify_compilation
        File.write("Data/blue-hoenn-compiled.txt", File.read("Data/blue-hoenn-compile-request.txt"))
        File.delete("Data/blue-hoenn-compile-request.txt")
      rescue StandardError => error
        pbPrintException(error)
      end
      exit
    end
"""
    before = before.replace("blue-hoenn-", f"blue-{region}-")
    after = after.replace("blue-hoenn-", f"blue-{region}-").replace("BlueHoennPilot", module)
    source = source.replace(run_plugins, before + run_plugins).replace(initialize, after + initialize)
    row[2] = RubyString(zlib.compress(source.encode("utf-8")))
    return b"\x04\x08" + dump(rows)


def append_event(map_data, name, x, y, page):
    events = map_data.attrs["@events"]
    if any((obj.attrs["@x"], obj.attrs["@y"]) == (x, y) for obj in events.values()):
        raise ValueError(f"Eventos Hoenn se sobrepõem em {(x, y)}")
    n = len(events) + 1
    events[n] = ruby("RPG::Event", id=n, name=name.encode("ascii"), x=x, y=y, pages=[page])
    return n


def add_opening(maps, balls, rival, sprite):
    # Trigger profile once on a new save. The self switch also works for
    # existing saves with no pending profile.
    profile = event_page(script="BlueHoennPilot.choose_profile")
    profile.attrs.update({"@trigger": 3, "@through": True})
    profile.attrs["@list"].insert(-1, command(123, b"A", 0))
    append_event(maps[8], "HN_PlayerProfile", 25, 6, profile)
    off = copy.deepcopy(profile)
    off.attrs["@condition"].attrs.update({"@self_switch_valid": True, "@self_switch_ch": b"A"})
    off.attrs.update({"@trigger": 0, "@list": [command(0)]})
    maps[8].attrs["@events"][len(maps[8].attrs["@events"])].attrs["@pages"].append(off)
    append_event(maps[8], "HN_Clock", 26, 3, event_page(script="BlueHoennPilot.clock"))
    # These two cells are the complete width of the northbound Rota 101
    # entrance. The invisible player-touch event starts the rescue scene.
    for x in (10, 11):
        page = event_page(script="BlueHoennPilot.route_birch", touch=True)
        append_event(maps[101], f"HN_BirchRescue_{x}", x, 18, page)
    for (mid, x, y), species in zip(balls, ("TREECKO", "TORCHIC", "MUDKIP")):
        page = event_page(script=f"BlueHoennPilot.choose_birch_ball(:{species})",
                          sprite="Object_Ball")
        append_event(maps[mid], f"HN_BirchBag_{species}", x, y, page)
    mid, x, y = rival
    page = event_page(script="BlueHoennPilot.rival_103",
                      sprite=sprite, touch=True)
    append_event(maps[mid], "HN_Rival_103", x, y, page)



def add_stage3_events(maps, game):
    """Author events ONLY onto cleared donor maps, with all coordinates sourced."""
    sprites_used = set()
    for mid, x, y, name, script in NPCS_STAGE3:
        chosen = name
        if not (game / f"Graphics/Characters/{chosen}.png").is_file():
            raise ValueError(f"Sprite do NPC Hoenn indisponível: {chosen}")
        sprites_used.add(chosen)
        append_event(maps[mid], f"HN3_NPC_{mid}_{x}_{y}", x, y,
                     event_page(script=script, sprite=chosen))
    for mid, x, y, script, sprite in (
        (17, 9, 4, "BlueHoennPilot.heal", "NPC_DPP_PokeCenter_Nurse"),
        (18, 3, 5, "BlueHoennPilot.mart", "NPC_DPP_PokeMart_Man"),
    ):
        if not (game / f"Graphics/Characters/{sprite}.png").is_file():
            raise ValueError(f"Sprite de Petalburg indisponível: {sprite}")
        append_event(maps[mid], f"HN3_Service_{mid}", x, y,
                     event_page(script=script, sprite=sprite))
        if mid == 17:
            # Register the healing counter as on Oldale's pilot.
            append_event(maps[mid], "HN3_HealingCounter", 9, 5,
                         event_page(script=script))
    for mid, x, y, name, message in SIGNS_STAGE3:
        # Portuguese messages live in the Blue Ruby plugin, never injected
        # into foreign RMXP event scripts or a donor text blob.
        append_event(maps[mid], f"HN3_Sign_{name}", x, y,
                     event_page(script=f"BlueHoennPilot.sign(:{name})"))
    for mid, x, y, key, item, visible in PICKUPS_STAGE3:
        page = event_page(script="nil", sprite="Object_Ball" if visible else "")
        event_id = append_event(maps[mid], f"HN3_Item_{key}", x, y, page)
        call = f'BlueHoennPilot.pickup(:{item}, "{key}", {event_id})'
        page.attrs["@list"][0] = command(355, call.encode("ascii"))
        hidden = event_page(script="nil")
        hidden.attrs["@condition"].attrs["@self_switch_valid"] = True
        hidden.attrs["@condition"].attrs["@self_switch_ch"] = b"A"
        hidden.attrs["@list"] = [command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(hidden)
    for mid, x, y in FOREST_AQUA_TRIGGERS:
        append_event(maps[mid], f"HN3_AquaGrunt_{x}", x, y,
                     event_page(script="BlueHoennPilot.forest_aqua", touch=True))
    for mid, x, y, kind, name, sprite, team, double in TRAINERS_STAGE3:
        if not (game / f"Graphics/Characters/{sprite}.png").is_file():
            raise ValueError(f"Sprite do treinador da etapa 3 ausente: {sprite}")
        if double:
            script = f'BlueHoennPilot.battle_stage3(:{kind}, "{name}", {mid}, true)'
        else:
            script = f'BlueHoennPilot.battle_stage3(:{kind}, "{name}", {mid})'
        append_event(maps[mid], f"HN3_Trainer_{mid}_{x}_{y}", x, y,
                     event_page(script=script, sprite=sprite))
    # A second Twins sprite shares the same combat key: no duplicate reward.
    append_event(maps[104], "HN3_Twins_Mia", 138, 15,
                 event_page(script='BlueHoennPilot.battle_stage3(:TWINS, "Gina & Mia", 104, true)',
                            sprite="trainer_LASS"))
    return {"stage3_npcs": len(NPCS_STAGE3) + 2, "stage3_signs": len(SIGNS_STAGE3),
            "stage3_pickups": len(PICKUPS_STAGE3),
            "stage3_trainers": len(TRAINERS_STAGE3), "stage3_aqua_triggers": len(FOREST_AQUA_TRIGGERS)}




def select_native_character(game: Path, candidates: tuple[str, ...], *, role: str) -> tuple[str, bool]:
    """Select a real, existing *Blue* character graphic; mark fallbacks."""
    for index, candidate in enumerate(candidates):
        path = game / f"Graphics/Characters/{candidate}.png"
        if path.is_file() and not path.is_symlink() and regular(path).read_bytes().startswith(PNG):
            return candidate, index > 0
    raise ValueError(f"Sem sprite nativo seguro para {role}: {', '.join(candidates)}")


def add_stage4_events(maps, game):
    """Rustboro/Rusturf events authored on cleared maps only, with original
    Emerald source positions. All event assets are from the LOCAL Blue copy.
    """
    native_npcs = 0
    for mid, x, y, sprite, handler in NPCS_STAGE4:
        if not regular(game / f"Graphics/Characters/{sprite}.png").read_bytes().startswith(PNG):
            raise ValueError(f"Sprite do NPC da Etapa 4 inválido: {sprite}")
        append_event(maps[mid], f"HN4_NPC_{mid}_{x}_{y}", x, y,
                     event_page(script=handler, sprite=sprite))
        native_npcs += 1
        if mid in (22, 23):
            counter_x, counter_y = (9, 5) if mid == 22 else (4, 5)
            page = event_page(script=handler)
            page.attrs["@trigger"] = 0
            append_event(maps[mid], f"HN4_Counter_{mid}", counter_x, counter_y, page)
    for mid, x, y, key, _message in SIGNS_STAGE4:
        append_event(maps[mid], f"HN4_Sign_{key}", x, y,
                     event_page(script=f"BlueHoennPilot.sign_stage4(:{key})"))
    for mid, x, y, key, item, visible in PICKUPS_STAGE4:
        page = event_page(script="nil", sprite="Object_Ball" if visible else "")
        event_id = append_event(maps[mid], f"HN4_Item_{key}", x, y, page)
        page.attrs["@list"][0] = command(355, f'BlueHoennPilot.pickup(:{item}, "{key}", {event_id})'.encode("ascii"))
        consumed = event_page(script="nil")
        consumed.attrs["@condition"].attrs["@self_switch_valid"] = True
        consumed.attrs["@condition"].attrs["@self_switch_ch"] = b"A"
        consumed.attrs["@through"] = True
        consumed.attrs["@list"] = [command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(consumed)

    leader_sprite, leader_placeholder = select_native_character(
        game, ("NPC_ORAS_Roxanne", "NPC_RSE_Roxanne", "trainer_LEADER_Roxanne",
               "trainer_LASS"), role="Roxanne")
    aqua_sprite, aqua_placeholder = select_native_character(
        game, ("NPC_RSE_AquaGrunt", "NPC_ORAS_AquaGrunt", "trainer_YOUNGSTER"),
        role="recruta Aqua no Rusturf")
    cut_sprite, cut_placeholder = select_native_character(
        game, ("Object_CutTree", "Object_Cut_Tree", "Object_CuttableTree",
               "Object_Cuttable_Tree", "Object_Tree", "Object_Ball"),
        role="árvore cortável Route 116")

    gx, gy = ROXANNE_EVENT[1:]
    append_event(maps[27], "HN4_Leader_Roxanne", gx, gy,
                 event_page(script="BlueHoennPilot.roxanne", sprite=leader_sprite))
    mid, x, y = TUNNEL_AQUA_EVENT
    append_event(maps[mid], "HN4_AquaRusturf", x, y,
                 event_page(script="BlueHoennPilot.rusturf_aqua", sprite=aqua_sprite))
    for mid, x, y in RUSTBORO_THEFT_TRIGGERS:
        page = event_page(script="BlueHoennPilot.rustboro_theft", touch=True)
        page.attrs["@through"] = True
        append_event(maps[mid], f"HN4_Theft_{x}_{y}", x, y, page)
    mid, x, y = TUNNEL_VERDANTURF_GATE
    append_event(maps[mid], "HN4_VerdanturfGate", x, y,
                 event_page(script="BlueHoennPilot.rusturf_east_gate", touch=True))
    for mid, x, y in CUT_TREES_STAGE4:
        page = event_page(script="nil", sprite=cut_sprite)
        event_id = append_event(maps[mid], f"HN4_CutTree_{x}_{y}", x, y, page)
        page.attrs["@through"] = False
        page.attrs["@list"][0] = command(355, f"BlueHoennPilot.cut_tree({event_id})".encode("ascii"))
        cleared = event_page(script="nil")
        cleared.attrs["@condition"].attrs["@self_switch_valid"] = True
        cleared.attrs["@condition"].attrs["@self_switch_ch"] = b"A"
        cleared.attrs["@through"] = True
        cleared.attrs["@list"] = [command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(cleared)
    for mid, x, y, kind, name, sprite, team, _double in TRAINERS_STAGE4:
        if not regular(game / f"Graphics/Characters/{sprite}.png").read_bytes().startswith(PNG):
            raise ValueError(f"Sprite nativo de treinador Rustboro inválido: {sprite}")
        script = f'BlueHoennPilot.battle_stage3(:{kind}, "{name}", {mid})'
        append_event(maps[mid], f"HN4_Trainer_{mid}_{x}_{y}", x, y,
                     event_page(script=script, sprite=sprite))
    return {
        "new_maps": len(SOURCE_MAPS_STAGE4), "npcs": native_npcs,
        "trainer_battles": len(TRAINERS_STAGE4) + 2,
        "pickups": len(PICKUPS_STAGE4), "signs": len(SIGNS_STAGE4),
        "cut_trees": len(CUT_TREES_STAGE4),
        "roxanne_sprite": leader_sprite, "roxanne_sprite_placeholder": leader_placeholder,
        "rusturf_aqua_sprite": aqua_sprite, "rusturf_aqua_sprite_placeholder": aqua_placeholder,
        "cut_tree_sprite": cut_sprite, "cut_tree_sprite_placeholder": cut_placeholder,
        "gameplay_verified": False,
    }




def add_stage5_events(maps, game):
    """Author, not copy, Dewford/Slateport events on the 20 stage-5 maps."""
    for mid, x, y, sprite, handler in NPCS_STAGE5:
        if not regular(game / f"Graphics/Characters/{sprite}.png").read_bytes().startswith(PNG):
            raise ValueError(f"Sprite nativo da etapa 5 inválido: {sprite}")
        append_event(maps[mid], f"HN5_NPC_{mid}_{x}_{y}", x, y,
                     event_page(script=handler, sprite=sprite))
        if mid in (29, 34, 35):
            cx, cy = (9, 5) if mid in (29, 34) else (4, 5)
            proxy = event_page(script=handler)
            proxy.attrs["@trigger"] = 0
            append_event(maps[mid], f"HN5_Counter_{mid}", cx, cy, proxy)
    for mid, x, y, key, _message in SIGNS_STAGE5:
        page = event_page(script=f"BlueHoennPilot.sign_stage5(:{key})")
        append_event(maps[mid], f"HN5_Sign_{key}", x, y, page)
    for mid, x, y, key, item, visible in PICKUPS_STAGE5:
        page = event_page(script="nil", sprite="Object_Ball" if visible else "")
        event_id = append_event(maps[mid], f"HN5_Item_{key}", x, y, page)
        page.attrs["@list"][0] = command(
            355, f'BlueHoennPilot.pickup(:{item}, "{key}", {event_id})'.encode("ascii"))
        done = event_page(script="nil")
        done.attrs["@condition"].attrs["@self_switch_valid"] = True
        done.attrs["@condition"].attrs["@self_switch_ch"] = b"A"
        done.attrs["@through"] = True
        done.attrs["@list"] = [command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(done)
    for mid, x, y in MUSEUM_FEE_GATE:
        page = event_page(script="BlueHoennPilot.museum_entry", touch=True)
        page.attrs["@through"] = True
        append_event(maps[mid], f"HN5_MuseumFee_{x}", x, y, page)
    aqua_sprite, aqua_fallback = select_native_character(
        game, ("NPC_RSE_AquaGrunt", "NPC_ORAS_AquaGrunt", "trainer_YOUNGSTER"),
        role="Equipe Aqua - Museu de Slateport")
    for index, (x, y) in enumerate(((35, 7), (37, 7)), 1):
        page = event_page(script=f"BlueHoennPilot.museum_aqua({index})",
                          sprite=aqua_sprite)
        append_event(maps[39], f"HN5_AquaMuseum_{index}", x, y, page)
    for mid, x, y in SLATEPORT_NORTH_GATE:
        page = event_page(script="BlueHoennPilot.slateport_north_gate", touch=True)
        page.attrs["@through"] = True
        append_event(maps[mid], f"HN5_NorthGate_{x}", x, y, page)
    for mid, x, y, kind, name, sprite, team, double in TRAINERS_STAGE5:
        if not regular(game / f"Graphics/Characters/{sprite}.png").read_bytes().startswith(PNG):
            raise ValueError(f"Treinador Hoenn da etapa 5 sem sprite: {sprite}")
        script = f'BlueHoennPilot.battle_stage3(:{kind}, "{name}", {mid})'
        append_event(maps[mid], f"HN5_Trainer_{mid}_{x}_{y}", x, y,
                     event_page(script=script, sprite=sprite))
    return {"maps": len(SOURCE_MAPS_STAGE5), "npcs": len(NPCS_STAGE5),
            "trainers": len(TRAINERS_STAGE5) + len(MUSEUM_AQUA) + 1,
            "pickup_events": len(PICKUPS_STAGE5),
            "cave_maps": len(CAVE_ENCOUNTERS_STAGE5),
            "boat_stops": len(BOAT_POINTS_STAGE5),
            "museum_aqua_sprite": aqua_sprite,
            "museum_aqua_sprite_placeholder": aqua_fallback,
            "gameplay_verified": False}




def add_stage6_events(maps, game, rival_image):
    """Insert Route 110/Mauville events into source maps cleared by the pilot.

    Gym gates use source-matched sprite names when present. Missing RSE gate
    images are explicitly reported as temporary art; no native visual/gameplay
    approval is inferred from the synthetic checks.
    """
    for mid, x, y, sprite, handler in NPCS_STAGE6:
        asset = game / f"Graphics/Characters/{sprite}.png"
        if not regular(asset).read_bytes().startswith(PNG):
            raise ValueError(f"Gráfico de NPC Mauville inválido: {asset}")
        append_event(maps[mid], f"HN6_NPC_{mid}_{x}_{y}", x, y,
                     event_page(script=handler, sprite=sprite))
        if mid in (42, 43):
            cx, cy = ((9, 5) if mid == 42 else (4, 5))
            append_event(maps[mid], f"HN6_Counter_{mid}", cx, cy,
                         event_page(script=handler))
    for mid, x, y, key, _message in SIGNS_STAGE6:
        append_event(maps[mid], f"HN6_Sign_{key}", x, y,
                     event_page(script=f"BlueHoennPilot.sign_stage6(:{key})"))
    for mid, x, y, key, item, visible in PICKUPS_STAGE6:
        page = event_page(script="nil", sprite="Object_Ball" if visible else "")
        event_id = append_event(maps[mid], f"HN6_Item_{key}", x, y, page)
        page.attrs["@list"][0] = command(
            355, f'BlueHoennPilot.pickup(:{item}, "{key}", {event_id})'.encode("ascii"))
        done = event_page(script="nil")
        done.attrs["@condition"].attrs["@self_switch_valid"] = True
        done.attrs["@condition"].attrs["@self_switch_ch"] = b"A"
        done.attrs["@through"] = True
        done.attrs["@list"] = [command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(done)

    wally_img, wally_fallback = select_native_character(
        game, ("NPC_RSE_Wally", "NPC_ORAS_Wally", "trainer_YOUNGSTER"),
        role="Wally Mauville")
    wattson_img, wattson_fallback = select_native_character(
        game, ("NPC_RSE_Wattson", "NPC_ORAS_Wattson", "trainer_YOUNGSTER"),
        role="Wattson Mauville")
    x, y = WALLY_EVENT[1:]
    append_event(maps[41], "HN6_Wally_Mauville", x, y,
                 event_page(script="BlueHoennPilot.wally_mauville", sprite=wally_img))
    x, y = WATTSON_EVENT[1:]
    append_event(maps[47], "HN6_Leader_Wattson", x, y,
                 event_page(script="BlueHoennPilot.wattson", sprite=wattson_img))

    x, y = RIVAL_110_EVENT[1:]
    append_event(maps[113], "HN6_Rival110", x, y,
                 event_page(script="BlueHoennPilot.rival_110",
                            sprite=rival_image))
    for mid, x, y in RIVAL_110_TRIGGERS:
        p = event_page(script="BlueHoennPilot.rival_110", touch=True)
        p.attrs["@through"] = True
        append_event(maps[mid], f"HN6_RivalTrigger_{x}", x, y, p)

    gate_images = {}
    for orientation in ("H", "V"):
        preferred = f"OBJ_RSE_Electric Gate {orientation}"
        image, placeholder = select_native_character(
            game, (preferred, "Object_Ball"),
            role=f"barreira {orientation} do ginásio Wattson")
        gate_images[orientation] = (image, placeholder)
    gate_ids = {"blue": [], "pink": []}
    for mid, x, y, color, direction in GYM_GATES_STAGE6:
        image, _ = gate_images[direction]
        page = event_page(script="BlueHoennPilot.wattson_gate", sprite=image)
        page.attrs["@through"] = False
        if not image == "Object_Ball":
            page.attrs["@graphic"].attrs["@direction"] = 2 if color == "blue" else 4
        event_id = append_event(maps[mid], f"HN6_Gate_{color}_{x}_{y}",
                                x, y, page)
        clear = event_page(script="nil")
        clear.attrs["@condition"].attrs["@self_switch_valid"] = True
        clear.attrs["@condition"].attrs["@self_switch_ch"] = b"A"
        clear.attrs["@through"] = True
        clear.attrs["@list"] = [command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(clear)
        gate_ids[color].append(event_id)
    blue_ids = repr(gate_ids["blue"])
    pink_ids = repr(gate_ids["pink"])
    for mid, x, y in GYM_SWITCHES_STAGE6:
        trigger = event_page(script=f"BlueHoennPilot.wattson_switch({blue_ids}, {pink_ids})",
                             touch=True)
        trigger.attrs["@through"] = True
        append_event(maps[mid], f"HN6_GymSwitch_{x}_{y}", x, y, trigger)

    for src, ex, ey, sx, sy, dst, dx, dy in CYCLE_TRANSFERS_STAGE6:
        p = event_page(script=f"BlueHoennPilot.cycling_gate({dst}, {dx}, {dy})",
                       touch=True)
        p.attrs["@through"] = True
        append_event(maps[src], f"HN6_CyclingGate_{src}_{ex}_{ey}",
                     ex, ey, p)
    for mid, x, y in MAUVILLE_FUTURE_GATES:
        page = event_page(script="BlueHoennPilot.mauville_future_gate",
                          touch=True)
        page.attrs["@through"] = True
        append_event(maps[mid], f"HN6_FutureGate_{x}_{y}", x, y, page)
    for mid, x, y, kind, name, sprite, team, double in TRAINERS_STAGE6:
        if not regular(game / f"Graphics/Characters/{sprite}.png").read_bytes().startswith(PNG):
            raise ValueError(f"Treinador Route 110/Mauville sem sprite nativo: {sprite}")
        append_event(maps[mid], f"HN6_Trainer_{mid}_{x}_{y}", x, y,
                     event_page(script=f'BlueHoennPilot.battle_stage3(:{kind}, "{name}", {mid})',
                                sprite=sprite))
    return {
        "new_maps": len(SOURCE_MAPS_STAGE6),
        "trainers": len(TRAINERS_STAGE6) + 2 + len(RIVAL_110_TEAMS) * 2,
        "gym_switches": len(GYM_SWITCHES_STAGE6),
        "gym_gates": len(GYM_GATES_STAGE6),
        "cycling_gate_events": len(CYCLE_TRANSFERS_STAGE6),
        "pickups": len(PICKUPS_STAGE6),
        "wattson_sprite_placeholder": wattson_fallback,
        "wally_sprite_placeholder": wally_fallback,
        "gate_graphic_placeholders": {k: v[1] for k, v in gate_images.items()},
        "bike_cycling_animation_verified": False,
        "gameplay_verified": False,
    }




def add_stage7_events(maps, game):
    """Author chapter-seven event pages, not donor event code.

    All boss sprites use existing native Blue characters or are labelled as
    placeholders. Source MapIDs are remapped by the isolated installer.
    """
    for mid, x, y, sprite, handler in NPCS_STAGE7:
        path = game / f"Graphics/Characters/{sprite}.png"
        if not regular(path).read_bytes().startswith(PNG):
            raise ValueError(f"Sprite de NPC Fallarbor/Lavaridge inválido: {sprite}")
        append_event(maps[mid], f"HN7_NPC_{mid}_{x}_{y}", x, y,
                     event_page(script=handler, sprite=sprite))
        if mid in (54, 55, 59, 60):
            cx, cy = (9,5) if mid in (54,59) else (4,5)
            append_event(maps[mid], f"HN7_Counter_{mid}", cx, cy,
                         event_page(script=handler))
    for mid,x,y,key,_text in SIGNS_STAGE7:
        append_event(maps[mid], f"HN7_Sign_{key}", x,y,
                     event_page(script=f"BlueHoennPilot.sign_stage7(:{key})"))
    for mid,x,y,key,item,visible in PICKUPS_STAGE7:
        page = event_page(script="nil", sprite="Object_Ball" if visible else "")
        event_id = append_event(maps[mid], f"HN7_Item_{key}", x,y,page)
        page.attrs["@list"][0] = command(
            355,f'BlueHoennPilot.pickup(:{item},"{key}",{event_id})'.encode("ascii"))
        cleared = event_page(script="nil")
        cleared.attrs["@condition"].attrs["@self_switch_valid"] = True
        cleared.attrs["@condition"].attrs["@self_switch_ch"] = b"A"
        cleared.attrs["@through"] = True
        cleared.attrs["@list"] = [command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(cleared)
    for mid,x,y,kind,name,sprite,team,double in TRAINERS_STAGE7:
        if not regular(game / f"Graphics/Characters/{sprite}.png").read_bytes().startswith(PNG):
            raise ValueError(f"Gráfico treinador da etapa 7 ausente: {sprite}")
        append_event(maps[mid], f"HN7_Trainer_{mid}_{x}_{y}", x,y,
                     event_page(
                         script=f'BlueHoennPilot.battle_stage3(:{kind},"{name}",{mid})',
                         sprite=sprite))
    magma_sprite, magma_placeholder = select_native_character(
        game,("NPC_RSE_MagmaGrunt","NPC_ORAS_MagmaGrunt","trainer_YOUNGSTER"),
        role="Equipe Magma em Mt Chimney")
    for mid,x,y,index in MAGMA_GRUNT_EVENTS:
        append_event(maps[mid], f"HN7_MagmaGrunt_{index}", x,y,
                     event_page(script=f"BlueHoennPilot.magma_grunt({index})",
                                sprite=magma_sprite))
    for mid,x,y in ROUTE112_MAGMA_BLOCKERS:
        page = event_page(script="nil",sprite=magma_sprite)
        event_id = append_event(maps[mid],f"HN7_CableBlocker_{x}_{y}",x,y,page)
        page.attrs["@list"][0] = command(
            355,f"BlueHoennPilot.magma_blocker({event_id})".encode("ascii"))
        done = event_page(script="nil")
        done.attrs["@condition"].attrs["@self_switch_valid"] = True
        done.attrs["@condition"].attrs["@self_switch_ch"] = b"A"
        done.attrs["@through"] = True
        done.attrs["@list"] = [command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(done)
    for mid,x,y,label,candidates,handler in (
        (*TABITHA_EVENT,"Tabitha",
         ("NPC_RSE_Tabitha","NPC_ORAS_Tabitha","trainer_YOUNGSTER"),
         "BlueHoennPilot.tabitha"),
        (*MAXIE_EVENT,"Maxie",
         ("NPC_RSE_Maxie","NPC_ORAS_Maxie","trainer_YOUNGSTER"),
         "BlueHoennPilot.maxie"),
        (*FLANNERY_EVENT,"Flannery",
         ("NPC_RSE_Flannery","NPC_ORAS_Flannery","trainer_LASS"),
         "BlueHoennPilot.flannery"),
    ):
        sprite, placeholder = select_native_character(game,candidates,role=label)
        append_event(maps[mid],f"HN7_Boss_{label}",x,y,
                     event_page(script=handler,sprite=sprite))
    mid,x,y = METEOR_FALLS_CUTSCENE
    page=event_page(script="BlueHoennPilot.meteor_falls_ambush",touch=True)
    page.attrs["@through"]=True
    append_event(maps[mid],"HN7_MeteorFalls_Ambush",x,y,page)
    mid,x,y = METEORITE_MACHINE_EVENT
    append_event(maps[mid],"HN7_MeteoriteMachine",x,y,
                 event_page(script="BlueHoennPilot.meteorite_machine"))
    for mid,x,y,reason in FUTURE_GATES_STAGE7:
        if reason == "MAGMA_HIDEOUT" and 182 in maps:
            continue  # Stage9 replaces this closed gate with a guarded entry.
        page=event_page(script=f"BlueHoennPilot.stage7_future_gate(:{reason})",
                        touch=True)
        page.attrs["@through"]=True
        append_event(maps[mid],f"HN7_Future_{reason}",x,y,page)
    for index,(fall,launch) in enumerate(GYM_STEAM_PAIRS_STAGE7,1):
        fx,fy=fall; lx,ly=launch
        p=event_page(script=f"BlueHoennPilot.gym_steam_vent({lx},{ly})",
                     touch=True)
        p.attrs["@through"]=True
        append_event(maps[63],f"HN7_SteamFall_{index}",fx,fy,p)
        p=event_page(script=f"BlueHoennPilot.gym_steam_vent({fx},{fy})")
        p.attrs["@through"]=True
        append_event(maps[63],f"HN7_SteamLaunch_{index}",lx,ly,p)
    return {
        "new_maps":len(SOURCE_MAPS_STAGE7),
        "trainer_events":len(TRAINERS_STAGE7)+len(MAGMA_GRUNT_EVENTS)+3,
        "cutscene_events":1,
        "cable_blocker_events":len(ROUTE112_MAGMA_BLOCKERS),
        "pickups":len(PICKUPS_STAGE7),
        "steam_vent_pairs":len(GYM_STEAM_PAIRS_STAGE7),
        "magma_graphic":magma_sprite,
        "magma_graphic_placeholder":magma_placeholder,
        "gameplay_verified":False,
    }




def add_stage8_events(maps, game, rival_image):
    """Author isolated Norman/Fortree/Weather/Lilycove chapter events.

    Donor events are NOT copied: only audited placements and party templates
    are recreated with Brazilian Portuguese Ruby handlers. Missing graphic
    candidates use an explicitly unapproved native fallback.
    """
    for mid,x,y,sprite,handler in NPCS_STAGE8:
        asset=game / f"Graphics/Characters/{sprite}.png"
        if not regular(asset).read_bytes().startswith(PNG):
            raise ValueError(f"Sprite da Etapa 8 ausente: {sprite}")
        append_event(maps[mid],f"HN8_NPC_{mid}_{x}_{y}",x,y,
                     event_page(script=handler,sprite=sprite))
        if mid in (49,50,65,66,71):
            cx,cy=(9,5) if mid in (49,65,71) else (4,5)
            append_event(maps[mid],f"HN8_ServiceCounter_{mid}",cx,cy,
                         event_page(script=handler))
    for mid,x,y,key,_msg in SIGNS_STAGE8:
        append_event(maps[mid],f"HN8_Sign_{key}",x,y,
                     event_page(script=f"BlueHoennPilot.sign_stage8(:{key})"))
    for mid,x,y,key,item,visible in PICKUPS_STAGE8:
        page=event_page(script="nil",sprite="Object_Ball" if visible else "")
        event_id=append_event(maps[mid],f"HN8_Item_{key}",x,y,page)
        page.attrs["@list"][0]=command(
            355,f'BlueHoennPilot.pickup(:{item},"{key}",{event_id})'.encode("ascii"))
        gone=event_page(script="nil")
        gone.attrs["@condition"].attrs["@self_switch_valid"]=True
        gone.attrs["@condition"].attrs["@self_switch_ch"]=b"A"
        gone.attrs["@through"]=True
        gone.attrs["@list"]=[command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(gone)
    for x,y,tx,ty in NORMAN_GYM_DOORS:
        ev=event_page(script=f"BlueHoennPilot.norman_gym_warp({tx},{ty})",
                      touch=True)
        ev.attrs["@through"]=True
        append_event(maps[20],f"HN8_NormanDoor_{x}_{y}",x,y,ev)
    for mid,x,y,kind,name,sprite,team,double in TRAINERS_STAGE8:
        if not regular(game / f"Graphics/Characters/{sprite}.png").read_bytes().startswith(PNG):
            raise ValueError(f"Sprite de treinador Etapa8 ausente: {sprite}")
        script=f'BlueHoennPilot.battle_stage3(:{kind},"{name}",{mid})'
        append_event(maps[mid],f"HN8_Trainer_{mid}_{x}_{y}",x,y,
                     event_page(script=script,sprite=sprite))
    boss_art={}
    for label,(mid,x,y),choices,handler in (
        ("Norman",NORMAN_EVENT,("NPC_RSE_Norman","NPC_ORAS_Norman","trainer_YOUNGSTER"),
         "BlueHoennPilot.norman"),
        ("Winona",WINONA_EVENT,("NPC_RSE_Winona","NPC_ORAS_Winona","trainer_LASS"),
         "BlueHoennPilot.winona"),
        ("Shelly",SHELLY_EVENT,("NPC_RSE_Shelly","NPC_ORAS_Shelly","trainer_LASS"),
         "BlueHoennPilot.weather_shelly"),
    ):
        art,placeholder=select_native_character(game,choices,role=label)
        append_event(maps[mid],f"HN8_Boss_{label}",x,y,
                     event_page(script=handler,sprite=art))
        boss_art[label]={"sprite":art,"placeholder":placeholder}
    aqua_art,aqua_placeholder=select_native_character(
        game,("NPC_RSE_AquaGrunt","NPC_ORAS_AquaGrunt","trainer_YOUNGSTER"),
        role="recruta Aqua Weather Institute")
    for mid,x,y,version,_team in AQUA_INSTITUTE:
        append_event(maps[mid],f"HN8_AquaInstitute_{version}",x,y,
                     event_page(script=f"BlueHoennPilot.weather_aqua({version})",
                                sprite=aqua_art))
    rival_events=((RIVAL_119_EVENT,"rival_119",True),
                  (RIVAL_LILYCOVE_EVENT,"rival_lilycove",False))
    for (mid,x,y),name,touch in rival_events:
        page=event_page(script=f"BlueHoennPilot.{name}",
                        sprite="" if touch else rival_image,touch=touch)
        if touch: page.attrs["@through"]=True
        append_event(maps[mid],f"HN8_{name}",x,y,page)
    special=(
        (WEATHER_REWARD_EVENT,"HN8_WeatherScientist",
         "BlueHoennPilot.weather_castform",
         ("NPC_DPP_PokeMart_Man","trainer_YOUNGSTER")),
        (STEVEN_SCOPE_EVENT,"HN8_StevenScope",
         "BlueHoennPilot.steven_scope",
         ("NPC_RSE_Steven","NPC_ORAS_Steven","trainer_YOUNGSTER")),
    )
    special_art={}
    for (mid,x,y),label,script,options in special:
        sprite,placeholder=select_native_character(game,options,role=label)
        append_event(maps[mid],label,x,y,
                     event_page(script=script,sprite=sprite))
        special_art[label]={"sprite":sprite,"placeholder":placeholder}
    kc_art,kc_placeholder=select_native_character(
        game,("NPC_RSE_Kecleon","OBJ_RSE_Kecleon","Object_Ball"),
        role="Kecleon Fortree/Route120")
    for (mid,x,y),tag in ((FORTREE_KECLEON_EVENT,"FORTREE"),
                          (ROUTE120_KECLEON_EVENT,"ROUTE120")):
        page=event_page(script="nil",sprite=kc_art)
        event_id=append_event(maps[mid],f"HN8_Kecleon_{tag}",x,y,page)
        page.attrs["@list"][0]=command(
            355,f"BlueHoennPilot.kecleon_scope({event_id},:{tag})".encode("ascii"))
        gone=event_page(script="nil")
        gone.attrs["@condition"].attrs["@self_switch_valid"]=True
        gone.attrs["@condition"].attrs["@self_switch_ch"]=b"A"
        gone.attrs["@through"]=True
        gone.attrs["@list"]=[command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(gone)
    for mid,x,y,key in FUTURE_GATES_STAGE8:
        if (key == "AQUA_HIDEOUT" and 215 in maps or
            key == "MT_PYRE_PIER" and 141 in maps):
            continue  # No Stage8 placeholder on an audited Stage9 approach.
        page=event_page(script=f"BlueHoennPilot.stage8_future_gate(:{key})",
                        touch=True)
        page.attrs["@through"]=True
        append_event(maps[mid],f"HN8_Future_{key}",x,y,page)
    return {
        "new_maps":len(SOURCE_MAPS_STAGE8),
        "ordinary_trainer_events":len(TRAINERS_STAGE8),
        "aqua_institute_battles":len(AQUA_INSTITUTE)+1,
        "rival_pbs_variants":(len(RIVAL_119_TEAMS)+len(RIVAL_LILYCOVE_TEAMS))*2,
        "gym_norman_room_warps":len(NORMAN_GYM_DOORS),
        "pickup_events":len(PICKUPS_STAGE8),
        "boss_graphics":boss_art,
        "aqua_graphic_placeholder":aqua_placeholder,
        "aux_graphics":special_art,
        "kecleon_placeholder":kc_placeholder,
        "native_surf_fly_verified":False,
        "gameplay_verified":False,
    }



def scan_stage9_source_events(original_events, maps, allowed_maps=None, strict=True):
    """Extract ONLY simple direct transfers + known pbItemBall from pinned RXDATA.

    Reads source event headers to locate original geometry; never copies or
    runs third-party Ruby commands. Multi-page/ambiguous warp events and any
    transfer to an uninstalled map are intentionally excluded. Sea borders
    are governed by SURF_BORDERS_STAGE9 in PBS, not land-only graph edges.
    """
    allowed_maps = set(SOURCE_MAPS_STAGE9) if allowed_maps is None else set(allowed_maps)
    transfer_names=re.compile(r"door|exit|entrance|stairs|ladder|warp tile",re.I)
    item_names=re.compile(r"^(?:HiddenItem|Item)(?:\b|$)",re.I)
    item_call=re.compile(r"\bpb(?:Hidden)?ItemBall\(\s*:([A-Z0-9_]+)\s*[,)]")
    transfers, pickups = [], []
    for mid, events in original_events.items():
        if mid not in allowed_maps:
            raise ValueError(f"Fonte não autoriza eventos no mapa Map{mid:03}")
        mp=maps[mid]
        w,h=mp.attrs["@width"],mp.attrs["@height"]
        for ev in events.values():
            name=text(ev.attrs["@name"])
            x,y=ev.attrs["@x"],ev.attrs["@y"]
            if not (0<=x<w and 0<=y<h):
                raise ValueError(f"Evento RXDATA Stage9 fora de limites: {mid}/{name}")
            pages=ev.attrs.get("@pages",[])
            raw_cmds=[cmd for page in pages
                      for cmd in page.attrs.get("@list",[])
                      if isinstance(cmd,RubyObject) and cmd.name=="RPG::EventCommand"]
            if transfer_names.search(name) and not re.search(r"activate|controller|trigger|cutscene|battle",name,re.I):
                choices=set()
                for cmd in raw_cmds:
                    if cmd.attrs.get("@code")!=201:
                        continue
                    ps=cmd.attrs.get("@parameters",[])
                    if (len(ps)>=4 and ps[0]==0 and
                        all(isinstance(v,int) for v in ps[1:4])):
                        choices.add(tuple(ps[1:4]))
                if len(choices)==1:
                    dst,dx,dy=next(iter(choices))
                    if dst in maps:
                        dw,dh=maps[dst].attrs["@width"],maps[dst].attrs["@height"]
                        if not 0<=dx<dw or not 0<=dy<dh:
                            if strict:
                                raise ValueError(f"Warp RXDATA fora de mapa {mid}/{name} -> {dst}/{dx}/{dy}")
                            # Pinned donor contains some alternate-map warps
                            # with mismatched target geometry. Never invent a landing.
                            continue
                        transfers.append((mid,x,y,dst,dx,dy,name))
            if item_names.match(name):
                identities=set()
                for cmd in raw_cmds:
                    if cmd.attrs.get("@code") not in (355,655):continue
                    for p in cmd.attrs.get("@parameters",[]):
                        if isinstance(p,(bytes,str)):
                            match=item_call.search(text(p))
                            if match:identities.add(match.group(1))
                if len(identities)==1:
                    item=next(iter(identities))
                    pickups.append((mid,x,y,item,name=="Item"))
    return transfers,pickups


def add_stage9_events(maps,game,source_warps,source_pickups):
    """Remap audited source locations into safe, original Blue Ruby events."""
    from_stage9=set(SOURCE_MAPS_STAGE9)
    used_items=set()
    for mid,x,y,dst,dx,dy,_original_name in source_warps:
        if mid not in from_stage9 or dst not in maps:
            raise ValueError(f"Warp Stage9 desconhecido {mid}->{dst}")
        page=event_page(
            script=f"BlueHoennPilot.stage9_transfer({mid},{dst},{dx},{dy})",
            touch=True)
        page.attrs["@through"]=True
        append_event(maps[mid],f"HN9_SourceWarp_{mid}_{x}_{y}",x,y,page)
    for mid,x,y,item,visible in source_pickups:
        key=f"STAGE9_{mid}_{x}_{y}"
        if key in used_items:raise ValueError("Item RXDATA Stage9 duplicado")
        used_items.add(key)
        page=event_page(script="nil",sprite="Object_Ball" if visible else "")
        event_id=append_event(maps[mid],f"HN9_SourceItem_{mid}_{x}_{y}",x,y,page)
        page.attrs["@list"][0]=command(
            355,f'BlueHoennPilot.pickup(:{item},"{key}",{event_id})'.encode("ascii"))
        cleared=event_page(script="nil")
        cleared.attrs["@condition"].attrs["@self_switch_valid"]=True
        cleared.attrs["@condition"].attrs["@self_switch_ch"]=b"A"
        cleared.attrs["@through"]=True
        cleared.attrs["@list"]=[command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(cleared)
    for mid,x,y,sprite,handler in NPCS_STAGE9:
        asset=game/f"Graphics/Characters/{sprite}.png"
        if not regular(asset).read_bytes().startswith(PNG):
            raise ValueError(f"Sprite de NPC Mossdeep inválido {sprite}")
        append_event(maps[mid],f"HN9_NPC_{mid}_{x}_{y}",x,y,
                     event_page(script=handler,sprite=sprite))
        if mid in (77,78):
            cx,cy=(9,5) if mid==77 else (4,5)
            append_event(maps[mid],f"HN9_ServiceCounter_{mid}",cx,cy,
                         event_page(script=handler))
    for mid,x,y,key,_message in SIGNS_STAGE9:
        append_event(maps[mid],f"HN9_Sign_{key}",x,y,
                     event_page(script=f"BlueHoennPilot.sign_stage9(:{key})"))
    for mid,x,y,kind,name,sprite,team,double in TRAINERS_STAGE9:
        path=game/f"Graphics/Characters/{sprite}.png"
        if not regular(path).read_bytes().startswith(PNG):
            raise ValueError(f"Sprite do treinador Stage9 inválido {sprite}")
        script=f'BlueHoennPilot.battle_stage3(:{kind},"{name}",{mid})'
        append_event(maps[mid],f"HN9_Trainer_{mid}_{x}_{y}",x,y,
                     event_page(script=script,sprite=sprite))
    art={}
    for label,candidates,handler,positions in (
        ("Tate",("NPC_RSE_Tate","NPC_ORAS_Tate","trainer_YOUNGSTER"),
         "BlueHoennPilot.tate_liza",(TATE_LIZA_EVENTS[0],)),
        ("Liza",("NPC_RSE_Liza","NPC_ORAS_Liza","trainer_LASS"),
         "BlueHoennPilot.tate_liza",(TATE_LIZA_EVENTS[1],)),
        ("Archie",("NPC_RSE_Archie","NPC_ORAS_Archie","trainer_YOUNGSTER"),
         "BlueHoennPilot.pyre_archie",(MT_PYRE_ARCHIE,)),
        ("Tabitha",("NPC_RSE_Tabitha","NPC_ORAS_Tabitha","trainer_YOUNGSTER"),
         "BlueHoennPilot.magma_hideout_tabitha",(TABITHA_HIDEOUT_EVENT,)),
        ("Maxie",("NPC_RSE_Maxie","NPC_ORAS_Maxie","trainer_YOUNGSTER"),
         "BlueHoennPilot.magma_hideout_maxie",(MAXIE_HIDEOUT_EVENT,)),
        ("Matt",("NPC_RSE_Matt","NPC_ORAS_Matt","trainer_YOUNGSTER"),
         "BlueHoennPilot.aqua_hideout_matt",(MATT_HIDEOUT_EVENT,)),
        ("SpaceMaxie",("NPC_RSE_Maxie","NPC_ORAS_Maxie","trainer_YOUNGSTER"),
         "BlueHoennPilot.space_center_maxie",(SPACE_MAXIE_EVENT,)),
        ("SpaceSteven",("NPC_RSE_Steven","NPC_ORAS_Steven","trainer_YOUNGSTER"),
         "BlueHoennPilot.space_center_steven",(SPACE_STEVEN_EVENT,)),
    ):
        image,placeholder=select_native_character(game,candidates,role=label)
        art[label]={"sprite":image,"placeholder":placeholder}
        for mid,x,y in positions:
            append_event(maps[mid],f"HN9_Boss_{label}",x,y,
                         event_page(script=handler,sprite=image))
    for (mid,x,y),handler,label in (
        (ARCHIE_ORB_EVENT,"BlueHoennPilot.pyre_orb_scene","PyreOrb"),
        (MT_PYRE_OLD_LADY,"BlueHoennPilot.pyre_elder","PyreElder"),
        (GROUDON_CUTSCENE_EVENT,"BlueHoennPilot.groudon_hideout","Groudon"),
        (SUBMARINE_EVENT,"BlueHoennPilot.submarine_escape","Submarine"),
    ):
        # The Groudon awakening is an invisible story coordinate: require
        # a player-touch trigger, not an impossible manual talk interaction.
        automatic = label in ("PyreOrb","Submarine","Groudon")
        page=event_page(script=handler,touch=automatic)
        if automatic:page.attrs["@through"]=True
        append_event(maps[mid],f"HN9_Story_{label}",x,y,page)
    aqua_image,aqua_placeholder=select_native_character(
        game,("NPC_RSE_AquaGrunt","NPC_ORAS_AquaGrunt","trainer_YOUNGSTER"),
        role="Aqua Pyre/Hideout")
    magma_image,magma_placeholder=select_native_character(
        game,("NPC_RSE_MagmaGrunt","NPC_ORAS_MagmaGrunt","trainer_YOUNGSTER"),
        role="Magma Hideout/Space")
    for group,image,handler in (
        (PYRE_AQUA_GRUNTS,aqua_image,"pyre_aqua_grunt"),
        (AQUA_HIDEOUT_GRUNTS,aqua_image,"aqua_hideout_grunt"),
        (MAGMA_HIDEOUT_GRUNTS,magma_image,"magma_hideout_grunt"),
        (SPACE_GRUNT_EVENTS,magma_image,"space_magma_grunt"),
    ):
        for mid,x,y,version,_team in group:
            append_event(maps[mid],f"HN9_Grunt_{version}",x,y,
                         event_page(script=f"BlueHoennPilot.{handler}({version})",
                                    sprite=image))
    # Replace previously gated cave/harbor entrances, not their original
    # donor map events. These remain closed until correct story flags.
    for (mid,x,y),label,script in (
        (MAGMA_HIDEOUT_GATE,"MagmaEntry","BlueHoennPilot.enter_magma_hideout"),
        (AQUA_HIDEOUT_GATE,"AquaEntry","BlueHoennPilot.enter_aqua_hideout"),
    ):
        page=event_page(script=script,touch=True)
        page.attrs["@through"]=True
        append_event(maps[mid],f"HN9_Gate_{label}",x,y,page)
    return {
        "new_maps":len(SOURCE_MAPS_STAGE9),
        "auto_source_warp_events":len(source_warps),
        "auto_source_item_events":len(source_pickups),
        "ordinary_trainers":len(TRAINERS_STAGE9),
        "aqua_grunts":len(PYRE_AQUA_GRUNTS)+len(AQUA_HIDEOUT_GRUNTS),
        "magma_grunts":len(MAGMA_HIDEOUT_GRUNTS)+len(SPACE_GRUNT_EVENTS),
        "source_battle_party_levels_only":True,
        "boss_graphics":art,
        "aqua_placeholder":aqua_placeholder,
        "magma_placeholder":magma_placeholder,
        "native_gym_switch_puzzle_approved":False,
        "native_space_partner_battle_approved":False,
        "native_gameplay_verified":False,
    }



def add_stage10_events(maps, game, source_warps, source_pickups):
    """Reauthor only audited static entrances/items; never run source scripts."""
    for mid,x,y,dst,dx,dy,_name in source_warps:
        if mid not in SOURCE_MAPS_STAGE10 or dst not in maps:
            raise ValueError(f"Stage10 RXDATA entrada inválida {mid}->{dst}")
        page=event_page(
            script=f"BlueHoennPilot.stage10_transfer({mid},{dst},{dx},{dy})",
            touch=True)
        page.attrs["@through"]=True
        append_event(maps[mid],f"HN10_Warp_{mid}_{x}_{y}",x,y,page)
    for mid,x,y,item,visible in source_pickups:
        key=f"STAGE10_{mid}_{x}_{y}"
        page=event_page(script="nil",sprite="Object_Ball" if visible else "")
        event_id=append_event(maps[mid],f"HN10_Item_{mid}_{x}_{y}",x,y,page)
        page.attrs["@list"][0]=command(
            355,f'BlueHoennPilot.pickup(:{item},"{key}",{event_id})'.encode("ascii"))
        cleared=event_page(script="nil")
        cleared.attrs["@condition"].attrs["@self_switch_valid"]=True
        cleared.attrs["@condition"].attrs["@self_switch_ch"]=b"A"
        cleared.attrs["@through"]=True
        cleared.attrs["@list"]=[command(0)]
        maps[mid].attrs["@events"][event_id].attrs["@pages"].append(cleared)
    for mid,x,y,key in STAGE10_SIGNS:
        append_event(maps[mid],f"HN10_Sign_{key}",x,y,
                     event_page(script=f"BlueHoennPilot.sign_stage10(:{key})"))
    for mid,x,y,handler,label in (
        (*SOOTOPOLIS_CRISIS_EVENT,"BlueHoennPilot.sootopolis_crisis","Sootopolis"),
        (*SEAFLOOR_AWAKENING_EVENT,"BlueHoennPilot.seafloor_awakening","Kyogre"),
        (*RAYQUAZA_EVENT,"BlueHoennPilot.rayquaza_stage10","Rayquaza"),
        (*WALLY_VICTORY_ROAD_EVENT,"BlueHoennPilot.wally_victory_road","Wally"),
        (*LEAGUE_EXIT_EVENT,"BlueHoennPilot.stage10_transfer(98,99,9,18)","ChampionExit"),
        (*HALL_OF_FAME_EVENT,"BlueHoennPilot.hall_of_fame_stage10","HallOfFame"),
    ):
        page=event_page(script=handler,touch=True)
        page.attrs["@through"]=True
        append_event(maps[mid],f"HN10_Story_{label}",x,y,page)
    bosses=(
        ("Juan",JUAN_EVENT,"BlueHoennPilot.juan",
         ("NPC_RSE_Juan","trainer_YOUNGSTER")),
        ("Archie",(236,14,46),"BlueHoennPilot.seafloor_archie",
         ("NPC_RSE_Archie","trainer_YOUNGSTER")),
        ("OriginWallace",ORIGIN_WALLACE_EVENT,
         "BlueHoennPilot.origin_wallace_stage10",
         ("NPC_RSE_Wallace","trainer_YOUNGSTER")),
        ("PillarWallace",SKY_PILLAR_WALLACE_EVENT,
         "BlueHoennPilot.sky_pillar_wallace",
         ("NPC_RSE_Wallace","trainer_YOUNGSTER")),
        ("Sidney",ELITE_EVENTS[0],"BlueHoennPilot.elite_four(0)",
         ("NPC_RSE_Sidney","trainer_YOUNGSTER")),
        ("Phoebe",ELITE_EVENTS[1],"BlueHoennPilot.elite_four(1)",
         ("NPC_RSE_Phoebe","trainer_LASS")),
        ("Glacia",ELITE_EVENTS[2],"BlueHoennPilot.elite_four(2)",
         ("NPC_RSE_Glacia","trainer_LASS")),
        ("Drake",ELITE_EVENTS[3],"BlueHoennPilot.elite_four(3)",
         ("NPC_RSE_Drake","trainer_YOUNGSTER")),
        ("Wallace",CHAMPION_EVENT,"BlueHoennPilot.champion_wallace",
         ("NPC_RSE_Wallace","trainer_YOUNGSTER")),
    )
    art={}
    for label,(mid,x,y),handler,candidates in bosses:
        sprite,placeholder=select_native_character(game,candidates,role=label)
        art[label]={"sprite":sprite,"placeholder":placeholder}
        append_event(maps[mid],f"HN10_Boss_{label}",x,y,
                     event_page(script=handler,sprite=sprite))
    return {
        "new_maps":len(SOURCE_MAPS_STAGE10),
        "original_direct_warps":len(source_warps),
        "original_audited_item_events":len(source_pickups),
        "scripted_bosses":8,
        "boss_graphics":art,
        "puzzle_ice_native_verified":False,
        "dive_waterfall_native_verified":False,
        "rayquaza_cinematic_native_verified":False,
        "hall_of_fame_ui_native_verified":False,
        "native_gameplay_verified":False,
    }


def preflight_route102_trainers(game: Path) -> list[dict]:
    """Fail closed if any target trainer already exists in the native Blue PBS.

    The version 102 is intentionally namespaced in the Hoenn pilot. Reusing a
    conflicting trainer block would silently change the NPC's battle party.
    No source or game files are written by this preflight.
    """
    expected = {(kind, name, 102) for _, _, kind, name, _, _ in ROUTE_102_TRAINERS}
    if len(expected) != len(ROUTE_102_TRAINERS):
        raise ValueError("Treinadores de Hoenn repetidos na definição do piloto")
    root = game / "PBS"
    if not root.is_dir() or root.is_symlink():
        raise ValueError("PBS nativo de Hoenn indisponível")
    for path in sorted(root.glob("trainers*.txt")):
        body = regular(path).read_text("utf-8-sig")
        for header in re.finditer(r"(?m)^\s*\[([^\]\r\n]+)\]", body):
            fields = [v.strip() for v in header[1].split(",")]
            if len(fields) not in (2, 3):
                continue
            if len(fields) == 3 and not fields[2].isdigit():
                continue
            identity = (fields[0], fields[1], int(fields[2]) if len(fields) == 3 else 0)
            if identity in expected:
                raise ValueError(f"Treinador de Hoenn já existe no PBS nativo: {identity} ({path.name})")
    return [
        {"source_map_id": 102, "trainer_type": kind, "name": name,
         "pbs_version": 102, "event_key": f"HN_{name}", "x": x, "y": y,
         "compiled": False, "gameplay_verified": False}
        for x, y, kind, name, _, _ in ROUTE_102_TRAINERS
    ]


def build_overlay(game, source):
    trainer_bindings = preflight_route102_trainers(game)
    for name in ("Game.exe", "Game.ini", "mkxp.json", f"{STORY}/RegionStart.rb"):
        regular(game / name)
    native_infos = loads(regular(game / "Data/MapInfos.rxdata").read_bytes())
    native_tiles = loads(regular(game / "Data/Tilesets.rxdata").read_bytes())
    disk_ids = {int(m[1]) for p in (game / "Data").iterdir()
                if (m := re.fullmatch(r"Map(\d+)\.rxdata", p.name, re.I))}
    pbs_ids = set()
    for path in (game / "PBS").glob("*.txt"):
        if path.stem.startswith(("encounters", "map_metadata")):
            body = regular(path).read_text("utf-8-sig")
            pbs_ids.update(int(m[1]) for m in re.finditer(r"(?m)^\s*\[\s*(\d+)", body))
        elif path.stem.startswith("map_connections"):
            body = regular(path).read_text("utf-8-sig")
            for line in body.splitlines():
                fields = line.split("#", 1)[0].split(",")
                if len(fields) == 6:
                    pbs_ids.update(int(fields[i]) for i in (0, 3) if fields[i].strip().isdecimal())
    reserved = set(native_infos) | disk_ids | pbs_ids | set(range(600, 682))
    free = [n for n in range(700, 1000) if n not in reserved]
    if len(free) < len(SOURCE_MAPS):
        raise ValueError("Sem MapIDs livres para o piloto abaixo de 1000")
    ids = dict(zip(SOURCE_MAPS, free))
    donor_tiles = loads(source.read("Data/Tilesets.rxdata"))
    maps, tiles, tile_ids, overlay = {}, {}, {}, {}
    stage9_original_events = {}
    stage10_original_events = {}
    all_original_events = {}
    for old in SOURCE_MAPS:
        m = loads(source.read(f"Data/Map{old:03}.rxdata"))
        if not isinstance(m, RubyObject) or m.name != "RPG::Map":
            raise ValueError(f"Mapa inválido na fonte: {old}")
        native_id = m.attrs["@tileset_id"]
        if native_id not in tile_ids:
            ts = donor_tiles[native_id]
            for key in ("@panorama_name", "@fog_name", "@battleback_name"):
                ts.attrs[key] = b""
            for key, directory in (("@tileset_name", "Tilesets"), ("@autotile_names", "Autotiles")):
                old_names = ts.attrs[key] if key == "@autotile_names" else [ts.attrs[key]]
                names = []
                for raw_name in old_names:
                    name = text(raw_name)
                    if not name:
                        names.append(b"")
                        continue
                    if not re.fullmatch(r"[A-Za-z0-9_ ()-]+", name):
                        raise ValueError(f"Referência gráfica inválida: {name}")
                    blob = source.read(f"Graphics/{directory}/{name}.png")
                    relative = f"Graphics/{directory}/BLUE_HOENN_{name}.png"
                    if not blob.startswith(PNG) or (game / relative).exists():
                        raise ValueError(f"PNG inválido ou colisão em {relative}")
                    overlay[relative] = blob
                    names.append(f"BLUE_HOENN_{name}".encode("ascii"))
                ts.attrs[key] = names if key == "@autotile_names" else names[0]
            tile_ids[native_id] = len(native_tiles)
            native_tiles.append(ts)
        maps[old], tiles[old] = m, native_tiles[tile_ids[native_id]]
        # Keep only decoded source events in memory for read-only QA inventory.
        # No donor scripts or dialogue are copied into the new Blue map.
        all_original_events[old] = dict(m.attrs.get("@events", {}))
        if old in SOURCE_MAPS_STAGE9:
            stage9_original_events[old] = dict(m.attrs.get("@events", {}))
        if old in SOURCE_MAPS_STAGE10:
            stage10_original_events[old] = dict(m.attrs.get("@events", {}))
        m.attrs.update({
            "@tileset_id": tile_ids[native_id], "@events": {}, "@autoplay_bgm": False,
            "@autoplay_bgs": False, "@bgm": ruby("RPG::AudioFile", name=b"", volume=100, pitch=100),
            "@bgs": ruby("RPG::AudioFile", name=b"", volume=100, pitch=100),
            "@encounter_list": [], "@encounter_step": 30,
        })
    stage9_source_warps, stage9_source_items = scan_stage9_source_events(
        stage9_original_events, maps)
    if not stage9_source_warps:
        raise ValueError("Mapas Stage9 sem warps auditáveis na fonte RXDATA")
    stage10_source_warps, stage10_source_items = scan_stage9_source_events(
        stage10_original_events, maps, allowed_maps=SOURCE_MAPS_STAGE10, strict=False)
    if not stage10_source_warps:
        raise ValueError("Mapas Stage10 sem transferências de origem verificadas")
    edges, required = validate_geometry(maps, tiles)
    balls = starter_ball_positions(maps, tiles, edges, required)
    rival = rival_position(maps, tiles, edges, required, balls)
    rival_image, rival_image_fallback = rival_sprite(game)

    upstream_connections = set(source.read("PBS/map_connections.txt").decode("utf-8-sig").splitlines())
    rows = []
    for a, edge_a, off_a, b, edge_b, off_b in (
        *((a, d1, 0, b, d2, 0) for a, d1, b, d2 in BORDERS),
        *OFFSET_BORDERS,
        *OFFSET_BORDERS_STAGE4,
        *OFFSET_BORDERS_STAGE5,
        *OFFSET_BORDERS_STAGE6,
        *OFFSET_BORDERS_STAGE7,
        *OFFSET_BORDERS_STAGE8,
        *SURF_BORDERS_STAGE9,
        *SURF_BORDERS_STAGE10,
    ):
        donor = f"{a},{edge_a},{off_a},{b},{edge_b},{off_b}"
        if donor not in upstream_connections:
            raise ValueError(f"Conexão de origem não encontrada: {donor}")
        rows.append(f"{ids[a]},{edge_a},{off_a},{ids[b]},{edge_b},{off_b}")
    connection = "PBS/map_connections.txt"
    if (game / connection).is_file():
        native = regular(game / connection).read_bytes()
    else:
        native = None
    # The existing merger validates the six fields and preserves native lines.
    merged = merge_pbs(native, "\n".join(rows))
    prefix = len(native or b"")
    overlay[connection] = merged[:prefix] + merged[prefix:].replace(
        b"# Blue Johto - experimental audited geometry only", b"# Blue Hoenn - isolated pilot", 1
    )
    for index, (a, a_arrival, b, b_arrival) in enumerate(WARP_PAIRS, 1):
        for source_point, arrival, suffix in ((a, b_arrival, "A"), (b, a_arrival, "B")):
            mid, x, y = source_point
            dest, dest_x, dest_y = arrival
            page = event_page(warp=(ids[dest], dest_x, dest_y), touch=True)
            append_event(maps[mid], f"HN_DOOR_{index}_{suffix}", x, y, page)

    for mid, x, y, name, sprite, handler in PEOPLE:
        if not regular(game / f"Graphics/Characters/{sprite}.png").read_bytes().startswith(PNG):
            raise ValueError(f"Sprite nativo inválido: {sprite}")
        page = event_page(script=handler, sprite=sprite)
        append_event(maps[mid], f"HN_{name}", x, y, page)
        if mid in (13, 14):
            # The original counter tile sits between the player and the attendant.
            px, py = (9, 5) if mid == 13 else (4, 5)
            proxy = event_page(script=handler, touch=True)
            proxy.attrs["@trigger"] = 0
            append_event(maps[mid], f"HN_{name}_counter", px, py, proxy)

    add_opening(maps, balls, rival, rival_image)
    stage3_counts = add_stage3_events(maps, game)
    stage4_counts = add_stage4_events(maps, game)
    stage5_counts = add_stage5_events(maps, game)
    stage6_counts = add_stage6_events(maps, game, rival_image)
    stage7_counts = add_stage7_events(maps, game)
    stage8_counts = add_stage8_events(maps, game, rival_image)
    stage9_counts = add_stage9_events(
        maps, game, stage9_source_warps, stage9_source_items)
    stage10_counts = add_stage10_events(
        maps, game, stage10_source_warps, stage10_source_items)
    trainer_sections = []
    for x, y, trainer_type, name, sprite, team in ROUTE_102_TRAINERS:
        regular(game / f"Graphics/Characters/{sprite}.png")
        page = event_page(script=f'BlueHoennPilot.battle(:{trainer_type}, "{name}")', sprite=sprite)
        append_event(maps[102], f"HN_{name}", x, y, page)
        trainer_sections.append(
            f"[{trainer_type},{name},102]\nLoseText = Boa batalha!\n" +
            "".join(f"Pokemon = {species},{level}\n" for species, level in team)
        )
    # The class RIVAL1 must already be defined by the native Blue engine.
    # Refuse a colliding trainer ID instead of silently changing a base team.
    exists = False
    for candidate in sorted((game / "PBS").glob("trainer_types*.txt")):
        text_body = regular(candidate).read_text("utf-8-sig")
        exists |= bool(re.search(r"(?m)^\s*\[RIVAL1\]\s*$", text_body))
    if not exists:
        raise ValueError("Tipo nativo RIVAL1 não encontrado na instalação Blue")
    rival_keys = {(name, version) for name in RIVAL_NAMES
                  for _, version in RIVAL_TEAMS.values()}
    rival_keys.update((name, version) for name in RIVAL_NAMES
                      for version, _team in RIVAL_110_TEAMS.values())
    for teams in (RIVAL_119_TEAMS, RIVAL_LILYCOVE_TEAMS):
        rival_keys.update((name, version) for name in RIVAL_NAMES
                          for version, _team in teams.values())
    for candidate in sorted((game / "PBS").glob("trainers*.txt")):
        text_body = regular(candidate).read_text("utf-8-sig")
        for match in re.finditer(r"(?m)^\s*\[RIVAL1,([^,\]\r\n]+),(\d+)\]\s*$", text_body):
            if (match[1].strip(), int(match[2])) in rival_keys:
                raise ValueError(f"Rival Hoenn duplicado em {candidate.name}")
    for name in RIVAL_NAMES:
        for chosen, (opponent, version) in RIVAL_TEAMS.items():
            trainer_sections.append(
                f"# Inicial do jogador: {chosen}; {name}: {opponent}\n"
                f"[RIVAL1,{name},{version}]\nLoseText = Boa batalha!\n"
                f"Pokemon = {opponent},5\n"
            )
    for name in RIVAL_NAMES:
        for chosen, (version, team) in RIVAL_110_TEAMS.items():
            trainer_sections.append(
                f"# Rival Rota 110: player starter {chosen}, rival {name}\n"
                f"[RIVAL1,{name},{version}]\nLoseText = Nossa jornada continua!\n" +
                "".join(f"Pokemon = {species},{level}\n" for species, level in team)
            )
    for event, teams in (("Rota 119", RIVAL_119_TEAMS),
                         ("Lilycove", RIVAL_LILYCOVE_TEAMS)):
        for name in RIVAL_NAMES:
            for chosen, (version, team) in teams.items():
                trainer_sections.append(
                    f"# Rival {event}: player starter {chosen}, rival {name}\n"
                    f"[RIVAL1,{name},{version}]\nLoseText = Nossa jornada continua!\n" +
                    "".join(f"Pokemon = {species},{level}\n" for species,level in team)
                )
    # Fail closed on absent native types/overlapping PBS identities.
    types = set()
    for candidate in sorted((game / "PBS").glob("trainer_types*.txt")):
        body = regular(candidate).read_text("utf-8-sig")
        types.update(match.group(1).strip() for match in
                     re.finditer(r"(?m)^\s*\[([^\]\r\n]+)\]", body))
    needed = {kind for _, _, _, kind, _, _, _, _ in TRAINERS_STAGE3}
    needed.update(kind for _, _, _, kind, _, _, _, _ in TRAINERS_STAGE4)
    needed.update(kind for _, _, _, kind, _, _, _, _ in TRAINERS_STAGE5)
    needed.update(kind for _, _, _, kind, _, _, _, _ in TRAINERS_STAGE6)
    needed.update(kind for _, _, _, kind, _, _, _, _ in TRAINERS_STAGE7)
    needed.update(kind for _, _, _, kind, _, _, _, _ in TRAINERS_STAGE8)
    needed.update(kind for _, _, _, kind, _, _, _, _ in TRAINERS_STAGE9)
    missing = needed - types
    if missing:
        raise ValueError(f"Tipos de treinador não existentes na engine Blue: {sorted(missing)}")
    extra_ids = {(kind, name, mid) for mid, _, _, kind, name, _, _, _ in TRAINERS_STAGE3}
    extra_ids.add(FOREST_AQUA_PBS)
    extra_ids.update((kind, name, mid)
                     for mid, _, _, kind, name, _, _, _ in TRAINERS_STAGE4)
    extra_ids.update((ROXANNE_PBS, TUNNEL_AQUA_PBS))
    extra_ids.update((kind, name, mid)
                     for mid, _, _, kind, name, _, _, _ in TRAINERS_STAGE5)
    extra_ids.update((kind, name, version)
                     for kind, name, version, _ in MUSEUM_AQUA)
    extra_ids.add(BRAWLY_PBS)
    extra_ids.update((kind, name, mid)
                     for mid, _, _, kind, name, _, _, _ in TRAINERS_STAGE6)
    extra_ids.update((WATTSON_PBS, WALLY_PBS))
    extra_ids.update((kind, name, mid)
                     for mid, _, _, kind, name, _, _, _ in TRAINERS_STAGE7)
    extra_ids.update((FLANNERY_PBS, TABITHA_PBS, MAXIE_PBS))
    extra_ids.update((kind, name, version)
                     for kind, name, version, _team in MAGMA_GRUNTS_STAGE7)
    extra_ids.update((kind, name, mid)
                     for mid, _, _, kind, name, _, _, _ in TRAINERS_STAGE8)
    extra_ids.update((NORMAN_PBS, WINONA_PBS, SHELLY_PBS))
    extra_ids.update(("BLUE_HOENN_AQUA", "Recruta", version)
                     for mid,x,y,version,_team in AQUA_INSTITUTE)
    extra_ids.update((kind,name,mid)
                     for mid,_,_,kind,name,_,_,_ in TRAINERS_STAGE9)
    extra_ids.update((TATE_LIZA_PBS,MATT_PBS,MAXIE_HIDEOUT_PBS,
                      TABITHA_HIDEOUT_PBS,MAXIE_SPACE_PBS,TABITHA_SPACE_PBS))
    extra_ids.update((JUAN_PBS,ARCHIE_PBS,WALLY_ROAD_PBS,CHAMPION_PBS,*ELITE_PBS))
    for group,kind in (
        (PYRE_AQUA_GRUNTS,"BLUE_HOENN_AQUA"),
        (AQUA_HIDEOUT_GRUNTS,"BLUE_HOENN_AQUA"),
        (MAGMA_HIDEOUT_GRUNTS,"BLUE_HOENN_MAGMA"),
        (SPACE_GRUNT_EVENTS,"BLUE_HOENN_MAGMA"),
    ):
        extra_ids.update((kind,"Recruta",version)
                         for mid,x,y,version,team in group)
    if len(extra_ids) != (len(TRAINERS_STAGE3) + len(TRAINERS_STAGE4) +
                          len(TRAINERS_STAGE5) + len(TRAINERS_STAGE6) +
                          len(TRAINERS_STAGE7) + len(MUSEUM_AQUA) +
                          len(MAGMA_GRUNTS_STAGE7) + len(TRAINERS_STAGE8) +
                          len(AQUA_INSTITUTE) + 12 +
                          len(TRAINERS_STAGE9) + len(PYRE_AQUA_GRUNTS) +
                          len(AQUA_HIDEOUT_GRUNTS) + len(MAGMA_HIDEOUT_GRUNTS) +
                          len(SPACE_GRUNT_EVENTS) + 6 + 8):
        raise ValueError("Treinadores da etapa 3 duplicados no catálogo")
    for candidate in sorted((game / "PBS").glob("trainers*.txt")):
        body = regular(candidate).read_text("utf-8-sig")
        for match in re.finditer(r"(?m)^\s*\[([^\]\r\n]+)\]", body):
            fields = [v.strip() for v in match.group(1).split(",")]
            if len(fields) not in (2, 3):
                continue
            ver = int(fields[2]) if len(fields) == 3 and fields[2].isdigit() else 0
            if (fields[0], fields[1], ver) in extra_ids:
                raise ValueError(f"Treinador Hoenn da etapa 3 já existe: {fields} ({candidate.name})")
    if {"BLUE_HOENN_AQUA", "BLUE_HOENN_ROXANNE", "BLUE_HOENN_BRAWLY",
        "BLUE_HOENN_WATTSON", "BLUE_HOENN_WALLY", "BLUE_HOENN_MAGMA",
        "BLUE_HOENN_TABITHA", "BLUE_HOENN_MAXIE", "BLUE_HOENN_FLANNERY",
        "BLUE_HOENN_NORMAN", "BLUE_HOENN_WINONA", "BLUE_HOENN_SHELLY",
        "BLUE_HOENN_TATE_LIZA", "BLUE_HOENN_MATT",
        "BLUE_HOENN_JUAN", "BLUE_HOENN_ARCHIE",
        "BLUE_HOENN_ELITE", "BLUE_HOENN_CHAMPION"} & types:
        raise ValueError("Tipo de chefe Hoenn já existe no PBS nativo")
    overlay["PBS/trainer_types_hoenn_pilot.txt"] = (
        "[BLUE_HOENN_AQUA]\nName = Equipe Aqua\nGender = Male\n"
        "BaseMoney = 20\nSkillLevel = 50\n"
        "[BLUE_HOENN_ROXANNE]\nName = Líder de Ginásio\nGender = Female\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
        "[BLUE_HOENN_BRAWLY]\nName = Líder de Ginásio\nGender = Male\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
        "[BLUE_HOENN_WATTSON]\nName = Líder de Ginásio\nGender = Male\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
        "[BLUE_HOENN_WALLY]\nName = Treinador\nGender = Male\n"
        "BaseMoney = 20\nSkillLevel = 70\n"
        "[BLUE_HOENN_MAGMA]\nName = Equipe Magma\nGender = Male\n"
        "BaseMoney = 20\nSkillLevel = 50\n"
        "[BLUE_HOENN_TABITHA]\nName = Admin Magma\nGender = Male\n"
        "BaseMoney = 80\nSkillLevel = 85\n"
        "[BLUE_HOENN_MAXIE]\nName = Líder Magma\nGender = Male\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
        "[BLUE_HOENN_FLANNERY]\nName = Líder de Ginásio\nGender = Female\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
        "[BLUE_HOENN_NORMAN]\nName = Líder de Ginásio\nGender = Male\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
        "[BLUE_HOENN_WINONA]\nName = Líder de Ginásio\nGender = Female\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
        "[BLUE_HOENN_SHELLY]\nName = Admin Aqua\nGender = Female\n"
        "BaseMoney = 90\nSkillLevel = 90\n"
        "[BLUE_HOENN_TATE_LIZA]\nName = Lideres de Ginasio\nGender = Male\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
        "[BLUE_HOENN_MATT]\nName = Admin Aqua\nGender = Male\n"
        "BaseMoney = 80\nSkillLevel = 85\n"
        "[BLUE_HOENN_JUAN]\nName = Líder de Ginásio\nGender = Male\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
        "[BLUE_HOENN_ARCHIE]\nName = Líder Aqua\nGender = Male\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
        "[BLUE_HOENN_ELITE]\nName = Elite Four\nGender = Male\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
        "[BLUE_HOENN_CHAMPION]\nName = Campeão\nGender = Male\n"
        "BaseMoney = 100\nSkillLevel = 100\n"
    ).encode("utf-8")
    # Use only native trainer graphics; a fallback is explicitly NOT a visual
    # approval for the actual Aqua sprite.
    aqua_art = None
    aqua_art_name = None
    for name in ("RSE_AQUAGRUNT_M", "AQUAGRUNT", "GRUNTMALE", "YOUNGSTER"):
        path = game / f"Graphics/Trainers/{name}.png"
        if path.is_file() and not path.is_symlink():
            blob = regular(path).read_bytes()
            if blob.startswith(PNG):
                aqua_art, aqua_art_name = blob, name
                break
    if aqua_art is None:
        raise ValueError("Sem sprite de treinador Aqua/grunt nativo para a cópia; instalar somente após revisão gráfica")
    overlay["Graphics/Trainers/BLUE_HOENN_AQUA.png"] = aqua_art
    for mid, x, y, kind, name, sprite, team, is_double in TRAINERS_STAGE3:
        trainer_sections.append(
            f"[{kind},{name},{mid}]\nLoseText = Boa batalha!\n" +
            "".join(f"Pokemon = {species},{level}\n" for species, level in team)
        )
    kind, name, version = FOREST_AQUA_PBS
    trainer_sections.append(
        f"[{kind},{name},{version}]\nLoseText = Recuar!\n" +
        "".join(f"Pokemon = {species},{level}\n" for species, level in FOREST_AQUA_TEAM)
    )
    # Stage 4 uses source-map versions for ordinary trainers; unique versions
    # for bosses. A separate copy cannot change native trainer definitions.
    for mid, _, _, kind, name, sprite, team, _double in TRAINERS_STAGE4:
        trainer_sections.append(
            f"[{kind},{name},{mid}]\nLoseText = Boa batalha!\n" +
            "".join(f"Pokemon = {species},{level}\n" for species, level in team)
        )
    kind, name, version = ROXANNE_PBS
    trainer_sections.append(
        f"[{kind},{name},{version}]\nItems = POTION,POTION\n"
        "LoseText = Você venceu a líder de Rustboro!\n"
        "Pokemon = GEODUDE,12\n    Moves = TACKLE,DEFENSECURL,ROCKTHROW,ROCKTOMB\n"
        "Pokemon = GEODUDE,12\n    Moves = TACKLE,DEFENSECURL,ROCKTHROW,ROCKTOMB\n"
        "Pokemon = NOSEPASS,15\n    Moves = BLOCK,HARDEN,TACKLE,ROCKTOMB\n"
        "    Item = ORANBERRY\n"
    )
    kind, name, version = TUNNEL_AQUA_PBS
    trainer_sections.append(
        f"[{kind},{name},{version}]\nLoseText = Vou recuar!\n" +
        "".join(f"Pokemon = {species},{level}\n" for species, level in TUNNEL_AQUA_TEAM)
    )
    leader_art, leader_art_name = None, None
    for candidate_name in ("RSE_LEADER_Roxanne", "LEADER_ROXANNE", "ROXANNE", "LASS"):
        candidate = game / f"Graphics/Trainers/{candidate_name}.png"
        if candidate.is_file() and not candidate.is_symlink():
            blob = regular(candidate).read_bytes()
            if blob.startswith(PNG):
                leader_art, leader_art_name = blob, candidate_name
                break
    if leader_art is None:
        raise ValueError("Sem sprite de batalha Roxanne nem fallback nativo na instalação Blue")
    overlay["Graphics/Trainers/BLUE_HOENN_ROXANNE.png"] = leader_art
    for mid, _, _, kind, name, sprite, team, _double in TRAINERS_STAGE5:
        trainer_sections.append(
            f"[{kind},{name},{mid}]\nLoseText = Boa batalha!\n" +
            "".join(f"Pokemon = {species},{level}\n" for species, level in team)
        )
    kind, name, version = BRAWLY_PBS
    trainer_sections.append(
        f"[{kind},{name},{version}]\nItems = SUPERPOTION,SUPERPOTION\n"
        "LoseText = Você venceu Brawly em Dewford!\n"
        "Pokemon = MACHOP,16\n    Moves = KARATECHOP,LOWKICK,SEISMICTOSS,BULKUP\n"
        "Pokemon = MEDITITE,16\n    Moves = FOCUSPUNCH,LIGHTSCREEN,REFLECT,BULKUP\n"
        "Pokemon = MAKUHITA,19\n    Moves = ARMTHRUST,VITALTHROW,REVERSAL,BULKUP\n"
        "    Item = SITRUSBERRY\n"
    )
    for kind, name, version, team in MUSEUM_AQUA:
        trainer_sections.append(
            f"[{kind},{name},{version}]\nLoseText = Recuar!\n" +
            "".join(f"Pokemon = {species},{level}\n" for species, level in team)
        )
    brawly_art, brawly_art_source = None, None
    for candidate_name in ("RSE_LEADER_Brawly", "LEADER_BRAWLY", "BRAWLY", "YOUNGSTER"):
        candidate = game / f"Graphics/Trainers/{candidate_name}.png"
        if candidate.is_file() and not candidate.is_symlink():
            data = regular(candidate).read_bytes()
            if data.startswith(PNG):
                brawly_art, brawly_art_source = data, candidate_name
                break
    if brawly_art is None:
        raise ValueError("Sem sprite de batalha Brawly nem fallback nativo seguro")
    overlay["Graphics/Trainers/BLUE_HOENN_BRAWLY.png"] = brawly_art
    for mid, _, _, kind, name, sprite, team, _double in TRAINERS_STAGE6:
        trainer_sections.append(
            f"[{kind},{name},{mid}]\nLoseText = Boa batalha!\n" +
            "".join(f"Pokemon = {species},{level}\n" for species, level in team)
        )
    for kind, name, version, team in (
        (*WALLY_PBS, WALLY_TEAM), (*WATTSON_PBS, WATTSON_TEAM)
    ):
        if kind == WALLY_PBS[0]:
            trainer_sections.append(
                f"[{kind},{name},{version}]\nLoseText = Preciso treinar mais!\n" +
                "".join(f"Pokemon = {species},{level}\n" for species, level in team)
            )
        else:
            trainer_sections.append(
                f"[{kind},{name},{version}]\nItems = SUPERPOTION,SUPERPOTION\n"
                "LoseText = Você desligou minha energia!\n"
                "Pokemon = VOLTORB,20\n    Moves = ROLLOUT,SPARK,SELFDESTRUCT,SHOCKWAVE\n"
                "Pokemon = ELECTRIKE,20\n    Moves = SHOCKWAVE,LEER,QUICKATTACK,HOWL\n"
                "Pokemon = MAGNETON,22\n    Moves = SUPERSONIC,SHOCKWAVE,THUNDERWAVE,SONICBOOM\n"
                "Pokemon = MANECTRIC,24\n    Moves = QUICKATTACK,THUNDERWAVE,SHOCKWAVE,HOWL\n"
            )
    boss_art_sources = {}
    for key, choices in (
        ("BLUE_HOENN_WATTSON", ("RSE_LEADER_Wattson", "LEADER_WATTSON", "WATTSON", "YOUNGSTER")),
        ("BLUE_HOENN_WALLY", ("RSE_POKEMONTRAINER_Wally", "WALLY", "YOUNGSTER")),
    ):
        for candidate_name in choices:
            candidate = game / f"Graphics/Trainers/{candidate_name}.png"
            if candidate.is_file() and not candidate.is_symlink():
                blob = regular(candidate).read_bytes()
                if blob.startswith(PNG):
                    overlay[f"Graphics/Trainers/{key}.png"] = blob
                    boss_art_sources[key] = candidate_name
                    break
        if key not in boss_art_sources:
            raise ValueError(f"Sprite nativo de batalha indisponível: {key}")
    for mid, _, _, kind, name, sprite, team, _double in TRAINERS_STAGE7:
        trainer_sections.append(
            f"[{kind},{name},{mid}]\nLoseText = Boa batalha!\n" +
            "".join(f"Pokemon = {species},{level}\n"
                    for species, level in team)
        )
    for kind, name, version, team in MAGMA_GRUNTS_STAGE7:
        trainer_sections.append(
            f"[{kind},{name},{version}]\nLoseText = Vamos recuar!\n" +
            "".join(f"Pokemon = {species},{level}\n" for species, level in team)
        )
    kind,name,version=TABITHA_PBS
    trainer_sections.append(
        f"[{kind},{name},{version}]\nLoseText = Derrota provisória...\n" +
        "".join(f"Pokemon = {species},{level}\n" for species, level in TABITHA_TEAM)
    )
    kind,name,version=MAXIE_PBS
    trainer_sections.append(
        f"[{kind},{name},{version}]\nItems = SUPERPOTION,SUPERPOTION\n"
        "LoseText = Nossa energia foi interrompida!\n" +
        "".join(f"Pokemon = {species},{level}\n" for species, level in MAXIE_TEAM)
    )
    kind,name,version=FLANNERY_PBS
    trainer_sections.append(
        f"[{kind},{name},{version}]\nItems = HYPERPOTION,HYPERPOTION\n"
        "LoseText = Você dominou as chamas de Lavaridge!\n"
        "Pokemon = NUMEL,24\n    Moves = OVERHEAT,TAKEDOWN,MAGNITUDE,SUNNYDAY\n"
        "Pokemon = SLUGMA,24\n    Moves = OVERHEAT,SMOG,LIGHTSCREEN,SUNNYDAY\n"
        "Pokemon = CAMERUPT,26\n    Moves = OVERHEAT,TACKLE,SUNNYDAY,ATTRACT\n"
        "Pokemon = TORKOAL,29\n    Moves = OVERHEAT,SUNNYDAY,BODYSLAM,ATTRACT\n"
        "    Item = WHITEHERB\n"
    )
    stage7_boss_art={}
    for kind, candidates in (
        ("BLUE_HOENN_FLANNERY",("RSE_LEADER_Flannery","LEADER_FLANNERY","FLANNERY","LASS")),
        ("BLUE_HOENN_TABITHA",("RSE_MAGMAADMIN_Tabitha","TABITHA","YOUNGSTER")),
        ("BLUE_HOENN_MAXIE",("RSE_MAGMALEADER_Maxie","MAXIE","YOUNGSTER")),
        ("BLUE_HOENN_MAGMA",("RSE_MAGMAGRUNT_M","MAGMAGRUNT","GRUNTMALE","YOUNGSTER")),
    ):
        for candidate_name in candidates:
            candidate=game / f"Graphics/Trainers/{candidate_name}.png"
            if candidate.is_file() and not candidate.is_symlink():
                data=regular(candidate).read_bytes()
                if data.startswith(PNG):
                    overlay[f"Graphics/Trainers/{kind}.png"]=data
                    stage7_boss_art[kind]=candidate_name
                    break
        if kind not in stage7_boss_art:
            raise ValueError(f"Faltou sprite nativo para chefe do piloto Hoenn: {kind}")
    for mid,x,y,kind,name,sprite,team,double in TRAINERS_STAGE8:
        trainer_sections.append(
            f"[{kind},{name},{mid}]\nLoseText = Boa batalha!\n" +
            "".join(f"Pokemon = {species},{level}\n" for species,level in team)
        )
    for _mid,_x,_y,version,team in AQUA_INSTITUTE:
        trainer_sections.append(
            f"[BLUE_HOENN_AQUA,Recruta,{version}]\n"
            "LoseText = A Equipe Aqua vai recuar!\n" +
            "".join(f"Pokemon = {species},{level}\n" for species,level in team)
        )
    kind,name,ver=NORMAN_PBS
    trainer_sections.append(
        f"[{kind},{name},{ver}]\nItems = HYPERPOTION,HYPERPOTION\n"
        "LoseText = Você cresceu como treinador!\n"
        "Pokemon = SPINDA,27\n    Moves = TEETERDANCE,PSYBEAM,FACADE,ENCORE\n"
        "Pokemon = VIGOROTH,27\n    Moves = SLASH,FACADE,ENCORE,FEINTATTACK\n"
        "Pokemon = LINOONE,29\n    Moves = SLASH,BELLYDRUM,FACADE,HEADBUTT\n"
        "Pokemon = SLAKING,31\n    Moves = COUNTER,YAWN,FACADE,FEINTATTACK\n"
    )
    kind,name,ver=WINONA_PBS
    trainer_sections.append(
        f"[{kind},{name},{ver}]\nItems = HYPERPOTION,HYPERPOTION\n"
        "LoseText = Seus Pokémon voaram mais alto!\n"
        "Pokemon = SWABLU,29\n    Moves = PERISHSONG,MIRRORMOVE,SAFEGUARD,AERIALACE\n"
        "Pokemon = TROPIUS,29\n    Moves = SUNNYDAY,AERIALACE,SOLARBEAM,SYNTHESIS\n"
        "Pokemon = PELIPPER,30\n    Moves = WATERGUN,SUPERSONIC,PROTECT,AERIALACE\n"
        "Pokemon = SKARMORY,31\n    Moves = SANDATTACK,FURYATTACK,STEELWING,AERIALACE\n"
        "Pokemon = ALTARIA,33\n    Moves = EARTHQUAKE,DRAGONBREATH,DRAGONDANCE,AERIALACE\n"
    )
    kind,name,ver=SHELLY_PBS
    trainer_sections.append(
        f"[{kind},{name},{ver}]\nLoseText = Precisamos recuar!\n" +
        "".join(f"Pokemon = {species},{level}\n" for species,level in SHELLY_TEAM)
    )
    stage8_boss_art={}
    for key,choices in (
        ("BLUE_HOENN_NORMAN",("RSE_LEADER_Norman","NORMAN","YOUNGSTER")),
        ("BLUE_HOENN_WINONA",("RSE_LEADER_Winona","WINONA","LASS")),
        ("BLUE_HOENN_SHELLY",("RSE_AQUAADMIN_Shelly","SHELLY","LASS")),
    ):
        for candidate_name in choices:
            candidate=game / f"Graphics/Trainers/{candidate_name}.png"
            if candidate.is_file() and not candidate.is_symlink():
                data=regular(candidate).read_bytes()
                if data.startswith(PNG):
                    overlay[f"Graphics/Trainers/{key}.png"]=data
                    stage8_boss_art[key]=candidate_name
                    break
        if key not in stage8_boss_art:
            raise ValueError(f"Sem sprite nativo de batalha Etapa8: {key}")
    for mid,x,y,kind,name,sprite,team,_double in TRAINERS_STAGE9:
        trainer_sections.append(
            f"[{kind},{name},{mid}]\nLoseText = Boa batalha!\n" +
            "".join(f"Pokemon = {species},{level}\n"
                    for species,level in team)
        )
    for group,kind in (
        (PYRE_AQUA_GRUNTS,"BLUE_HOENN_AQUA"),
        (AQUA_HIDEOUT_GRUNTS,"BLUE_HOENN_AQUA"),
        (MAGMA_HIDEOUT_GRUNTS,"BLUE_HOENN_MAGMA"),
        (SPACE_GRUNT_EVENTS,"BLUE_HOENN_MAGMA"),
    ):
        for mid,x,y,ver,team in group:
            trainer_sections.append(
                f"[{kind},Recruta,{ver}]\nLoseText = Vamos recuar!\n" +
                "".join(f"Pokemon = {species},{level}\n"
                        for species,level in team)
            )
    def stage9_boss(kind_name_ver, team, *, items=()):
        kind,name,version=kind_name_ver
        return (f"[{kind},{name},{version}]\n"
                + (f"Items = {','.join(items)}\n" if items else "")
                + "LoseText = Voce venceu!\n"
                + "".join(f"Pokemon = {species},{level}\n"
                          for species,level in team))
    trainer_sections.append(stage9_boss(TATE_LIZA_PBS,TATE_LIZA_TEAM,
                                       items=("HYPERPOTION",)*4))
    trainer_sections.append(stage9_boss(MATT_PBS,MATT_TEAM,
                                       items=("SUPERPOTION",)))
    trainer_sections.append(stage9_boss(TABITHA_HIDEOUT_PBS,TABITHA_HIDEOUT_TEAM))
    trainer_sections.append(stage9_boss(MAXIE_HIDEOUT_PBS,MAXIE_HIDEOUT_TEAM,
                                       items=("SUPERPOTION","SUPERPOTION")))
    trainer_sections.append(stage9_boss(TABITHA_SPACE_PBS,TABITHA_SPACE_TEAM))
    trainer_sections.append(stage9_boss(MAXIE_SPACE_PBS,MAXIE_SPACE_TEAM))

    # Emerald reference rosters; Blue's scaling replaces source levels.
    for definition,team,items in (
        (JUAN_PBS,JUAN_TEAM,("HYPERPOTION","HYPERPOTION")),
        (ARCHIE_PBS,ARCHIE_TEAM,("SUPERPOTION","SUPERPOTION")),
        (WALLY_ROAD_PBS,WALLY_ROAD_TEAM,("FULLRESTORE","FULLRESTORE")),
        *((definition,team,("FULLRESTORE","FULLRESTORE"))
          for definition,team in zip(ELITE_PBS,ELITE_TEAMS)),
        (CHAMPION_PBS,CHAMPION_TEAM,("FULLRESTORE",)*4),
    ):
        trainer_sections.append(stage9_boss(definition,team,items=items))
    stage10_boss_art={}
    for kind,choices in (
        ("BLUE_HOENN_JUAN",("RSE_LEADER_Juan","JUAN","YOUNGSTER")),
        ("BLUE_HOENN_ARCHIE",("RSE_AQUALEADER_Archie","ARCHIE","YOUNGSTER")),
        ("BLUE_HOENN_ELITE",("RSE_ELITEFOUR_Sidney","SIDNEY","YOUNGSTER")),
        ("BLUE_HOENN_CHAMPION",("RSE_CHAMPION_Wallace","WALLACE","YOUNGSTER")),
    ):
        for candidate_name in choices:
            candidate=game/f"Graphics/Trainers/{candidate_name}.png"
            if candidate.is_file() and not candidate.is_symlink():
                data=regular(candidate).read_bytes()
                if data.startswith(PNG):
                    overlay[f"Graphics/Trainers/{kind}.png"]=data
                    stage10_boss_art[kind]=candidate_name
                    break
        if kind not in stage10_boss_art:
            raise ValueError(f"Sem sprite nativo Stage10 seguro: {kind}")
    stage9_boss_art={}
    for kind,choices in (
        ("BLUE_HOENN_TATE_LIZA",
         ("RSE_LEADER_TateandLiza","LEADER_TateandLiza","TATEANDLIZA","LASS")),
        ("BLUE_HOENN_MATT",
         ("RSE_AQUAADMIN_Matt","MATT","YOUNGSTER")),
    ):
        for candidate_name in choices:
            candidate=game/f"Graphics/Trainers/{candidate_name}.png"
            if candidate.is_file() and not candidate.is_symlink():
                data=regular(candidate).read_bytes()
                if data.startswith(PNG):
                    overlay[f"Graphics/Trainers/{kind}.png"]=data
                    stage9_boss_art[kind]=candidate_name
                    break
        if kind not in stage9_boss_art:
            raise ValueError(f"Sem arte nativa Stage9 segura: {kind}")
    overlay["PBS/trainers_hoenn_pilot.txt"] = "".join(trainer_sections).encode("utf-8")
    for label, track in BGM.items():
        source_path = f"Audio/BGM/ORAS {track}.ogg"
        blob = source.read(source_path)
        if not blob.startswith(b"OggS"):
            raise ValueError(f"Áudio inválido: {source_path}")
        overlay[f"Audio/BGM/BLUE_HOENN_{label}.ogg"] = blob
    for old, label in MAP_BGM.items():
        maps[old].attrs["@autoplay_bgm"] = True
        maps[old].attrs["@bgm"] = ruby("RPG::AudioFile", name=f"BLUE_HOENN_{label}".encode(),
                                     volume=80, pitch=100)

    order = max(info.attrs.get("@order", 0) for info in native_infos.values())
    for index, (old, name) in enumerate(SOURCE_MAPS.items(), 1):
        native_infos[ids[old]] = ruby("RPG::MapInfo", name=name.encode("utf-8"),
                                    parent_id=0, order=order + index,
                                    expanded=False, scroll_x=0, scroll_y=0)
        overlay[f"Data/Map{ids[old]:03}.rxdata"] = serialize(maps[old], EVENT_CLASSES)
    overlay["Data/MapInfos.rxdata"] = serialize(native_infos)
    overlay["Data/Tilesets.rxdata"] = serialize(native_tiles)
    system = loads(regular(game / "Data/System.rxdata").read_bytes())
    system.attrs.update({"@start_map_id": ids[START[0]], "@start_x": START[1], "@start_y": START[2]})
    overlay["Data/System.rxdata"] = serialize(system, SYSTEM_CLASSES)
    overlay["Data/Scripts.rxdata"] = startup(regular(game / "Data/Scripts.rxdata").read_bytes())
    # QA 3/12 imports ONLY ordinary default encounter methods from the
    # pinned donor PBS. Original Blue Land/Cave presets keep priority.
    # Alternate swarm versions and conditional encounters are not activated.
    reference_profiles, reference_audit = parse_reference_encounters(
        source.read("PBS/encounters.txt").decode("utf-8-sig"), set(SOURCE_MAPS))
    encounter_bytes, encounters_audit = assemble_encounters(
        reference_profiles, ids, LAND_ENCOUNTERS, CAVE_ENCOUNTERS)
    overlay["PBS/encounters_hoenn_pilot.txt"] = encounter_bytes
    overlay["PBS/map_metadata_hoenn_pilot.txt"] = "".join(
        f"[{ids[mid]}]\nName = {name}\n" + ("Outdoor = true\nSnapEdges = true\n" if mid in OUTDOORS else "")
        for mid, name in SOURCE_MAPS.items()
    ).encode("utf-8")
    overlay["Data/blue-hoenn-compile-request.txt"] = (UPSTREAM + "\n").encode("ascii")
    report = {"region": "HOENN", "kind": "ISOLATED_HOENN_TEST", "source_commit": UPSTREAM,
              "start": [ids[START[0]], *START[1:]], "maps": ids, "save_profile": PROFILE,
              "trainer_bindings": [{**binding, "destination_map_id": ids[102]}
                                   for binding in trainer_bindings],
              "starter_ball_coordinates": [list(pos) for pos in balls],
              "rival_coordinate": list(rival),
              "rival_sprite": rival_image,
              "rival_sprite_placeholder": rival_image_fallback,
              "rival_versions": [{"player_starter": chosen, "rival_species": opponent,
                                  "version": version} for chosen, (opponent, version)
                                 in RIVAL_TEAMS.items()],
              "stage3": {**stage3_counts, "map_ids": list(SOURCE_MAPS_STAGE3),
                         "extra_borders": list(OFFSET_BORDERS),
                         "trainer_bindings": [{"source_map_id": mid, "x": x, "y": y,
                                               "trainer_type": kind, "name": name,
                                               "pbs_version": mid, "double": is_double}
                                              for mid, x, y, kind, name, sprite, team, is_double
                                              in TRAINERS_STAGE3],
                         "aqua_sprite_source": aqua_art_name,
                         "aqua_sprite_placeholder": aqua_art_name != "RSE_AQUAGRUNT_M",
                         "gameplay_approved": False},
              "stage4": {**stage4_counts,
                         "source_map_ids": list(SOURCE_MAPS_STAGE4),
                         "extra_borders": list(OFFSET_BORDERS_STAGE4),
                         "trainer_bindings": [{"source_map_id": mid, "x": x, "y": y,
                                               "trainer_type": kind, "name": name,
                                               "pbs_version": mid}
                                              for mid, x, y, kind, name, sprite, team, double
                                              in TRAINERS_STAGE4],
                         "roxanne_trainer_art": leader_art_name,
                         "roxanne_battle_art_placeholder": leader_art_name != "RSE_LEADER_Roxanne",
                         "stage5": {**stage5_counts,
                         "source_map_ids": list(SOURCE_MAPS_STAGE5),
                         "boat_points": [list(point) for point in BOAT_POINTS_STAGE5],
                         "bridge_borders": list(OFFSET_BORDERS_STAGE5),
                         "brawly_battle_art": brawly_art_source,
                         "brawly_battle_art_placeholder": brawly_art_source != "RSE_LEADER_Brawly",
                         "stage6": {**stage6_counts,
                         "source_map_ids": list(SOURCE_MAPS_STAGE6),
                         "new_border_connections": list(OFFSET_BORDERS_STAGE6),
                         "cycling_transfers": list(CYCLE_TRANSFERS_STAGE6),
                         "rival_versions": [version for version, _ in RIVAL_110_TEAMS.values()],
                         "boss_battle_art": boss_art_sources,
                         "boss_battle_art_placeholder": {
                             "wattson": boss_art_sources["BLUE_HOENN_WATTSON"] != "RSE_LEADER_Wattson",
                             "wally": boss_art_sources["BLUE_HOENN_WALLY"] != "RSE_POKEMONTRAINER_Wally"},
                         "native_gameplay_verified": False},
              "stage7": {**stage7_counts,
                         "source_map_ids": list(SOURCE_MAPS_STAGE7),
                         "conditional_cable_points": list(CABLE_POINTS_STAGE7),
                         "base_team_levels_not_game_levels": True,
                         "boss_battle_art": stage7_boss_art,
                         "boss_battle_art_placeholder": {
                             "flannery": stage7_boss_art["BLUE_HOENN_FLANNERY"] != "RSE_LEADER_Flannery",
                             "tabitha": stage7_boss_art["BLUE_HOENN_TABITHA"] != "RSE_MAGMAADMIN_Tabitha",
                             "maxie": stage7_boss_art["BLUE_HOENN_MAXIE"] != "RSE_MAGMALEADER_Maxie",
                             "magma": stage7_boss_art["BLUE_HOENN_MAGMA"] != "RSE_MAGMAGRUNT_M"},
                         "native_gameplay_verified": False},
              "stage8": {**stage8_counts,
                         "source_map_ids": list(SOURCE_MAPS_STAGE8),
                         "original_norman_gym_reused": True,
                         "surf_fly_native_gameplay_verified": False,
                         "boss_battle_art": stage8_boss_art,
                         "battle_art_placeholder": {
                             "norman": stage8_boss_art["BLUE_HOENN_NORMAN"] != "RSE_LEADER_Norman",
                             "winona": stage8_boss_art["BLUE_HOENN_WINONA"] != "RSE_LEADER_Winona",
                             "shelly": stage8_boss_art["BLUE_HOENN_SHELLY"] != "RSE_AQUAADMIN_Shelly"},
                         "native_gameplay_verified": False},
              "stage9": {**stage9_counts,
                         "source_map_ids": list(SOURCE_MAPS_STAGE9),
                         "surf_only_borders": list(SURF_BORDERS_STAGE9),
                         "story_reference_levels_not_fixed": True,
                         "boss_battle_art":stage9_boss_art,
                         "boss_battle_art_placeholder":{
                             "tate_liza":stage9_boss_art["BLUE_HOENN_TATE_LIZA"]!="RSE_LEADER_TateandLiza",
                             "matt":stage9_boss_art["BLUE_HOENN_MATT"]!="RSE_AQUAADMIN_Matt"},
                         "original_partner_battle_pending": True,
                         "native_gameplay_verified": False},
              "stage10": {**stage10_counts,
                          "source_map_ids":list(SOURCE_MAPS_STAGE10),
                          "surf_only_borders":list(SURF_BORDERS_STAGE10),
                          "boss_battle_art":stage10_boss_art,
                          "boss_battle_art_placeholder":{
                              kind:source=="YOUNGSTER"
                              for kind,source in stage10_boss_art.items()},
                          "native_puzzles_and_hall_ui_pending":True,
                          "native_gameplay_verified":False},
              "native_gameplay_verified": False},
              "native_gameplay_verified": False},
              "native_gameplay_verified": False}
    # Reauthor only simple unconditional source pickups not already located
    # on an original Blue event. Other trainer/NPC/sign anchors are inventoried
    # as a *manual QA backlog*, not fictitious events or copied donor dialogue.
    qa3_event_audit = reauthor_safe_items_and_audit(
        all_original_events, maps, maps, game)
    # The QA3 item injection occurs after stage events; refresh RXDATA for every
    # map whose items were appended before writing the final pilot report.
    # Important: no changes to the native game/ data on disk.
    for old,x,y,item in qa3_event_audit["new_item_positions"]:
        overlay[f"Data/Map{ids[old]:03}.rxdata"] = serialize(maps[old], EVENT_CLASSES)
    report["qa3"] = {
        "reference": reference_audit,
        "method_imports": encounters_audit,
        "source_events": qa3_event_audit,
        "native_gameplay_verified": False,
        "all_trainers_npcs_signs_added": False,
    }
    # QA 4/12: source-derived *names and coordinates* only, not donor scripts.
    # Existing script/item locations always win. Any conditional, multipage,
    # ambiguous or non-renderable obstacle goes to the manual audit backlog.
    qa4_obstacles = install_simple_obstacles(all_original_events, maps, maps, game,
                                             source=source, overlay=overlay)
    for old, x, y, kind, sprite, event_id in qa4_obstacles["new_safe_obstacles"]:
        overlay[f"Data/Map{ids[old]:03}.rxdata"] = serialize(maps[old], EVENT_CLASSES)
    report["qa4"] = {
        **qa4_obstacles,
        "field_badges": {
            "CUT":"STONE", "FLASH":"KNUCKLE", "ROCKSMASH":"DYNAMO",
            "STRENGTH":"HEAT", "SURF":"BALANCE",
            "DIVE":"MIND", "WATERFALL":"RAIN",
        },
        "ever_grande_waterfall_entrance": [91,322],
        "native_gameplay_verified": False,
        "native_surf_dive_waterfall_puzzles_verified": False,
    }
    overlay["Hoenn pilot.json"] = json_bytes(report)
    marker_rows = ["BLUE_HOENN_PILOT_V1", ",".join(map(str, report["start"]))]
    marker_rows.extend(f"{old},{new}" for old, new in ids.items())
    overlay["Data/blue-hoenn-pilot.txt"] = ("\n".join(marker_rows) + "\n").encode("ascii")
    overlay[f"{PLUGIN}/meta.txt"] = (
        b"Name = Blue Hoenn Pilot\nVersion = 0.1\nEssentials = 21.1\n"
        b"Requires = Blue Battle Presentation and Story\nScripts = HoennPilot.rb\n"
    )
    overlay[f"{PLUGIN}/HoennPilot.rb"] = regular(ROOT / "scripts/regions/HoennPilot.rb").read_bytes()
    music = "Plugins/ZZZZ Blue Music/BlueMusic.rb"
    if (game / music).is_file():
        overlay[music] = regular(ROOT / "scripts/music/BlueMusic.rb").read_bytes()
    economy = f"{STORY}/Economy.rb"
    if (game / economy).is_file():
        overlay[economy] = regular(ROOT / "scripts/battle_polish/Economy.rb").read_bytes()
    ini, count = re.subn(r"(?m)^Title=[^\r\n]*", "Title=Hoenn Piloto",
                         regular(game / "Game.ini").read_text("utf-8-sig"))
    if count != 1:
        raise ValueError("Game.ini deve ter um Title")
    overlay["Game.ini"] = ini.encode("utf-8")
    config = regular(game / "mkxp.json").read_text("utf-8-sig")
    # Keep native mkxp comment syntax and insert explicit options first.
    keys = re.compile(r'(?m)^\s*"(?:windowTitle|dataPathApp|dataPathOrg)"\s*:[^\r\n]*(?:\r?\n|$)')
    config = keys.sub("", config)
    options = json.dumps({"windowTitle": "Pokémon Blue - Hoenn Piloto",
                          "dataPathOrg": "Dessastre Paradoxal Hoenn Testes",
                          "dataPathApp": PROFILE}, ensure_ascii=False)[1:-1]
    marker = re.search(r"(?m)^\s*\{", config)
    if marker is None:
        raise ValueError("mkxp.json sem configuração inicial")
    config = config[:marker.end()] + "\n    " + options + ",\n" + config[marker.end():]
    overlay["mkxp.json"] = config.encode("utf-8")
    return overlay, report


def copy_game(source: Path, target: Path) -> None:
    if os.name == "nt":
        flags = ["/COPY:DAT", "/NODCOPY", "/R:1", "/W:1", "/XJ", "/NFL", "/NDL", "/NP", "/NJH"]
        exclusions = ["/XF", "File *.rxdata", "Auto *.rxdata", "Game.rxdata",
                      "Save*.rxdata", "*.bak", "*.log", "blue-*-request.txt"]
        for name in COPY_DIRS:
            result = subprocess.run(["robocopy", str(source / name), str(target / name), "/E", "/MT:16",
                                     *flags, *exclusions], check=False)
            if result.returncode >= 8:
                raise OSError(f"Falha ao copiar {name}: {result.returncode}")
    else:
        def exclude(_, names):
            return [n for n in names if SAVE.fullmatch(n) or n.endswith((".bak", ".log", "-request.txt"))]
        for name in COPY_DIRS:
            shutil.copytree(source / name, target / name, ignore=exclude)
    for path in source.iterdir():
        if path.name in ROOT_FILES or path.suffix.lower() == ".dll":
            shutil.copyfile(regular(path), target / path.name)


def stage(game: Path, source: Source, output: Path) -> dict:
    game, output = safe_path(game), safe_path(output)
    if output.exists() or output.is_relative_to(game) or game.is_relative_to(output):
        raise ValueError("Escolha uma nova pasta fora da instalação principal")
    overlay, report = build_overlay(game, source)
    # QA04 is an additional Windows test installation. A separate folder
    # alone is not sufficient: mkxp stores saves under dataPathOrg/App.
    # Rewriting these two keys is allowed ONLY for our opted-in QA04 output.
    if output.name == "hoenn-qa-fase04":
        conf = overlay["mkxp.json"].decode("utf-8")
        substitutions = (
            ('"dataPathApp": "Hoenn Piloto"', '"dataPathApp": "Hoenn QA Fase04"'),
            ('"dataPathOrg": "Dessastre Paradoxal Hoenn Testes"',
             '"dataPathOrg": "Dessastre Paradoxal Hoenn QA04"'),
        )
        for before, after in substitutions:
            if conf.count(before) != 1:
                raise ValueError(f"Perfil de save QA04 não pôde ser isolado: {before}")
            conf = conf.replace(before, after)
        overlay["mkxp.json"] = conf.encode("utf-8")
        report["save_profile"] = "Hoenn QA Fase04"
        overlay["Hoenn pilot.json"] = json_bytes(report)
    output.parent.mkdir(parents=True, exist_ok=True)
    target = safe_path(output.parent / f".hoenn-{uuid.uuid4().hex}")
    target.mkdir()
    try:
        copy_game(game, target)
        install_copy(target, game, output, overlay)
    finally:
        if target.exists() and safe_path(target).parent == output.parent:
            shutil.rmtree(target)
    return report


def install_copy(target, game, output, overlay):
    # Confirm the source did not change while the base was being copied.
    for name in ("Game.exe", "Game.ini", "mkxp.json", "Data/Scripts.rxdata", "Data/System.rxdata",
                 "Data/MapInfos.rxdata", "Data/Tilesets.rxdata"):
        if regular(target / name).read_bytes() != regular(game / name).read_bytes():
            raise ValueError(f"A cópia preparada diverge da base: {name}")
    for name, content in overlay.items():
        dst = safe_path(target / name)
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(content)
    if output.exists():
        raise ValueError("O destino apareceu durante a montagem")
    target.rename(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", required=True, type=Path)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--inventory", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    try:
        report = stage(args.game, Source(args.source, args.inventory), args.output)
    except (OSError, ValueError, KeyError, TypeError, IndexError, zlib.error) as error:
        parser.exit(2, f"Piloto de Hoenn: {error}\n")
    print(json.dumps(report, ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
