"""Validate an absent Route 29 <-> Cherrygrove boundary using real RMXP tiles.

Read-only: no native game/ modifications, no region enablement, no executable.
Only an isolated candidate PBS connection and its audited JSON evidence are written.
A static tile passability check NEVER certifies an engine walking test.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
from dataclasses import dataclass
from pathlib import Path

# RGSS tile values observed on *both* real east/west map paths; reject changes.
PATH_SIGNATURE = (116, 96, 124)
SOURCE_IDS = {"JOHTO_ROUTE_29": 104, "JOHTO_CHERRYGROVE_CITY": 80}
ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RoomGrid:
    width: int
    height: int
    layers: tuple[int, ...]
    passages: tuple[int, ...]

    def cell(self, x: int, y: int, z: int) -> int:
        return self.layers[x + self.width * (y + self.height * z)]

    def passable(self, x: int, y: int) -> bool:
        if not (0 <= x < self.width and 0 <= y < self.height):
            return False
        for z in range(3):
            tile = self.cell(x, y, z)
            if tile >= len(self.passages) or self.passages[tile] & 0x0F:
                return False
        return True


def parse_rgss_table(raw: bytes, *, expected: tuple[int, int, int] | None = None) -> tuple[int, int, int, tuple[int, ...]]:
    if not isinstance(raw, bytes) or len(raw) < 20:
        raise ValueError("RGSS Table ausente ou curta")
    dimension, width, height, depth, count = struct.unpack_from("<5I", raw)
    if not (dimension in (1, 3) and 1 <= width <= 5000
            and 1 <= height <= 5000 and 1 <= depth <= 3
            and count == width * height * depth and len(raw) == 20 + 2 * count):
        raise ValueError("RGSS Table inconsistente")
    if expected is not None and (width, height, depth) != expected:
        raise ValueError("RGSS Table tem dimensoes diferentes das declaradas")
    return width, height, depth, struct.unpack_from(f"<{count}H", raw, 20)


def inspect_corridor(room: RoomGrid, side: str) -> list[int]:
    """Unique 3-tile horizontal road observed in source; 4 inward tiles checked."""
    if room.width < 5 or room.height < 3 or side not in ("West", "East"):
        raise ValueError("Mapa ou lado invalido")
    positions = [i for i in range(room.height - 2)
                 if all(room.cell(0 if side == "West" else room.width - 1, i + d, 0)
                        == PATH_SIGNATURE[d] for d in range(3))]
    result = []
    for y in positions:
        x_positions = range(4) if side == "West" else range(room.width - 4, room.width)
        if all(room.passable(x, y + d) for x in x_positions for d in range(3)):
            result.append(y)
    return result


def derive_connection(route: RoomGrid, city: RoomGrid, *, route_id: int,
                      city_id: int, existing: str = "") -> dict:
    if (type(route_id) is not int or type(city_id) is not int or
            not 600 <= route_id <= 999 or not 600 <= city_id <= 999 or
            route_id == city_id):
        raise ValueError("MapIDs Johto fora do namespace isolado ou duplicados")
    r = inspect_corridor(route, "West")
    c = inspect_corridor(city, "East")
    if len(r) != 1 or len(c) != 1:
        raise ValueError("Passagens nao sao unicas/continuas: route=%r, city=%r" % (r, c))
    # Connection offsets are relative to a shared world-space Y origin.
    # Route29 left starts at row 11; Cherrygrove right starts at row 23.
    # Therefore Cherrygrove needs a +12 offset relative to Route29.
    delta = c[0] - r[0]
    if delta < 0:
        raise ValueError("Deslocamento negativo ainda nao suportado para esta borda")
    output = f"{city_id},East,{delta},{route_id},West,0"
    reverse = f"{route_id},West,0,{city_id},East,{delta}"
    for line in existing.splitlines():
        line = line.split("#", 1)[0].strip().replace(" ", "")
        if not line:
            continue
        cols = line.split(",")
        if len(cols) == 6 and {cols[0], cols[3]} == {str(city_id), str(route_id)}:
            raise ValueError("Route29/Cherrygrove ja possui conexao no PBS, nao duplicar")
        if line in (output, reverse):
            raise ValueError("Conexao duplicada")
    return {
        "schema": 1, "region": "JOHTO", "status": "STATIC_GEOMETRY_BORDER_CANDIDATE_NOT_PLAYABLE",
        "route29_id": route_id, "cherrygrove_id": city_id,
        "route29_west_road_start_y": r[0], "cherrygrove_east_road_start_y": c[0],
        "signature": list(PATH_SIGNATURE), "checked_inward_columns": 4,
        "offset_y": delta, "pbs_line": output,
        "static_tile_passability": "DIRECTION_BITS_CLEAR_ON_3x4_EACH_SIDE",
        "actual_game_engine_passability_verified": False,
        "tested_in_game": False, "can_install": False, "gameplay_playable": False,
        "next_action": "Validar transicao e retorno em Game.exe isolado antes de aprovar jogabilidade",
    }


def load_grid(path: Path, tiles: list) -> RoomGrid:
    from audit_johto import read_map_data
    from server.ruby_marshal import RubyData, RubyObject

    map_ = read_map_data(path)
    if not isinstance(map_, RubyObject) or map_.name != "RPG::Map" or map_.attrs.get("@events") != {}:
        raise ValueError("Esperado mapa RMXP geometrico isolado SEM eventos")
    w, h = map_.attrs.get("@width"), map_.attrs.get("@height")
    tid = map_.attrs.get("@tileset_id")
    if not all(type(x) is int for x in (w, h, tid)) or not 2 <= w <= 300 or not 2 <= h <= 300:
        raise ValueError("Mapa/tamanho/tileset invalido")
    if not 0 < tid < len(tiles):
        raise ValueError("Tileset referenciado nao existe")
    table = map_.attrs.get("@data")
    tile = tiles[tid]
    if not isinstance(table, RubyData) or not isinstance(tile, RubyObject):
        raise ValueError("Faltam dados reais Table/Tileset")
    _, _, _, values = parse_rgss_table(table.data, expected=(w, h, 3))
    passage_table = tile.attrs.get("@passages")
    if not isinstance(passage_table, RubyData):
        raise ValueError("Tileset sem tabela de passagem")
    count, ph, pd, passages = parse_rgss_table(passage_table.data)
    if ph != 1 or pd != 1 or count < max(values, default=0) + 1:
        raise ValueError("Tileset sem passagem para cada tile do mapa")
    return RoomGrid(w, h, values, passages)


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preview", type=Path, default=ROOT / ".blue-work/johto-staging")
    p.add_argument("--existing", type=Path, default=ROOT / ".blue-work/johto-connections-preview.txt")
    p.add_argument("--output", type=Path, default=ROOT / ".blue-work/johto-route29-cherrygrove.json")
    args = p.parse_args(argv)
    try:
        from audit_johto import checksum, read_map_data
        root = ROOT.resolve()
        work = (root / ".blue-work").resolve()
        preview = args.preview.resolve()
        if (not preview.is_relative_to(work) or preview == work
                or args.preview.is_symlink() or args.existing.is_symlink()
                or args.output.is_symlink() or args.output.exists()
                or not args.output.resolve().is_relative_to(work)):
            raise ValueError("Entradas/saidas precisam ficar em .blue-work sem symlinks/overwrite")
        stage_file = preview / "johto-stage.json"
        stage = json.loads(stage_file.read_text(encoding="utf-8"))
        if (stage.get("schema"), stage.get("region"), stage.get("status"),
                stage.get("not_playable"), stage.get("can_install")) != (
                1, "JOHTO", "GEOMETRY_PREVIEW_ONLY", True, False):
            raise ValueError("Preview geometrica nao auditada")
        if not re.fullmatch(r"[0-9a-f]{64}", stage.get("source_archive_sha256", "")):
            raise ValueError("SHA-256 da fonte Johto ausente")
        rows = stage["maps"]
        matches = {}
        for name, source_id in SOURCE_IDS.items():
            hit = [row for row in rows if row.get("symbol") == name
                   and row.get("source_id") == source_id]
            if len(hit) != 1 or type(hit[0].get("destination_id")) is not int:
                raise ValueError("Mapa simbolico/ID da origem incorreto: " + name)
            matches[name] = hit[0]["destination_id"]
        tiles = read_map_data(preview / "Data/Tilesets.rxdata")
        if not isinstance(tiles, list):
            raise ValueError("Tilesets.rxdata invalido")
        route_id, city_id = matches["JOHTO_ROUTE_29"], matches["JOHTO_CHERRYGROVE_CITY"]
        route = load_grid(preview / "Data" / f"Map{route_id:03d}.rxdata", tiles)
        city = load_grid(preview / "Data" / f"Map{city_id:03d}.rxdata", tiles)
        existing = args.existing.read_text(encoding="utf-8")
        report = derive_connection(route, city, route_id=route_id, city_id=city_id,
                                   existing=existing)
        report["map_sha256"] = {"route29": checksum(preview / "Data" / f"Map{route_id:03d}.rxdata"),
                                "cherrygrove": checksum(preview / "Data" / f"Map{city_id:03d}.rxdata")}
        report["source_archive_sha256"] = stage["source_archive_sha256"]
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as out:
            json.dump(report, out, ensure_ascii=False, indent=2)
            out.write("\n")
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("[JOHTO][BLOQUEADO]", exc, file=sys.stderr)
        return 2
    print("[JOHTO][CANDIDATA] PBS:", report["pbs_line"])
    print("[JOHTO] Relatorio:", args.output)
    print("[JOHTO] Off-line: sem Game.exe, flags de 1/13 continuam pendentes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
