"""Author New Bark 1F house from native Inside tiles in a PRIVATE Johto stage.

No Game.exe, no events/warps, no game/ or save writes. Only updates Map675
in a NEW .blue-work copy of the already-audited 77-map bedroom staging.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

from build_johto_bedroom_v1 import tile, table_values

ROOT = Path(__file__).resolve().parents[2]
SYMBOL = "JOHTO_NEW_BARK_PLAYER_HOME_1F"
BEDROOM = "JOHTO_NEW_BARK_PLAYER_HOME_2F"
WIDTH, HEIGHT = 16, 13
STAIRS_APPROACH = (11, 9)
ARRIVAL_FROM_2F = (11, 8)
DOOR_APPROACH = (7, 9)
ARRIVAL_FROM_TOWN = (7, 8)
MOTHER_PROPOSAL = (6, 8)


def blueprint(passages: tuple[int, ...]) -> tuple[bytes, dict]:
    """Create original 16x13 geometry. Proposals are NOT verified in-engine."""
    if not isinstance(passages, (tuple, list)) or len(passages) <= tile(281, 5):
        raise ValueError("Tileset Inside sem tabela completa de passagem")
    layers = [0] * (WIDTH * HEIGHT * 3)
    decorated = set()
    furniture = []

    def put(x, y, z, value, name):
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT and 0 <= z < 3):
            raise ValueError("Tile fora do mapa: " + name)
        if value < 0 or value >= len(passages):
            raise ValueError("Tile nao encontrado: " + name)
        index = x + WIDTH * (y + HEIGHT * z)
        if z == 2 and (x, y) in decorated:
            raise ValueError("Moveis sobrepostos: " + name)
        layers[index] = value
        if z == 2:
            decorated.add((x, y))

    # Floors/walls are authored afresh, never copied from Center/Gym geometry.
    for y in range(1, HEIGHT - 1):
        for x in range(1, WIDTH - 1):
            put(x, y, 0, tile(88, (x + y) % 2), "piso")
    for x in range(1, WIDTH - 1):
        put(x, 0, 0, tile(190, 3), "parede de cima")
        put(x, 1, 1, tile(191, 3), "parede interna")
        put(x, HEIGHT - 1, 0, tile(190, 0), "parede de baixo")
    for y in range(HEIGHT):
        put(0, y, 0, tile(190, 0), "parede esquerda")
        put(WIDTH - 1, y, 0, tile(190, 0), "parede direita")

    def place(name, x, y, row, col, width, height):
        for dy in range(height):
            for dx in range(width):
                put(x+dx, y+dy, 2, tile(row+dy, col+dx), name)
        furniture.append({"name": name, "x": x, "y": y,
                          "width": width, "height": height})

    place("kitchen_counter", 2, 3, 257, 0, 4, 3)
    place("dining_table_with_chairs", 7, 4, 275, 4, 4, 3)
    place("tv_cabinet", 8, 3, 264, 0, 3, 1)
    place("sofa", 3, 7, 267, 0, 2, 2)
    place("potted_plant", 13, 3, 269, 4, 1, 3)
    place("stairs_visual", 12, 8, 238, 1, 2, 2)
    place("front_door_visual", 7, 10, 200, 4, 2, 2)

    def walkable(x, y):
        return 0 <= x < WIDTH and 0 <= y < HEIGHT and all(
            not (passages[layers[x+WIDTH*(y+HEIGHT*z)]] & 0x0F)
            for z in range(3)
        )

    positions = {
        "stairs_approach": STAIRS_APPROACH,
        "arrival_from_2f": ARRIVAL_FROM_2F,
        "door_approach": DOOR_APPROACH,
        "arrival_from_town": ARRIVAL_FROM_TOWN,
        "mother_position": MOTHER_PROPOSAL,
    }
    if len(set(positions.values())) != len(positions):
        raise ValueError("Coordenadas candidatas duplicadas")
    for name, xy in positions.items():
        if xy in decorated or not walkable(*xy):
            raise ValueError("Coordenada candidata bloqueada: " + name)
    reached = {ARRIVAL_FROM_2F}
    stack = [ARRIVAL_FROM_2F]
    while stack:
        x, y = stack.pop()
        for nx, ny in ((x-1,y), (x+1,y), (x,y-1), (x,y+1)):
            if (1 <= nx < WIDTH-1 and 2 <= ny < HEIGHT-1
                    and (nx,ny) not in reached and walkable(nx,ny)):
                reached.add((nx,ny))
                stack.append((nx,ny))
    if len(reached) < 25 or any(pos not in reached for pos in positions.values()):
        raise ValueError("Corredor interno do quarto, mae e porta sem acesso estatico")

    grid = struct.pack("<5I", 3, WIDTH, HEIGHT, 3, len(layers))
    grid += struct.pack(f"<{len(layers)}H", *layers)
    report = {
        "schema": 1, "region": "JOHTO", "symbol": SYMBOL,
        "status": "AUTHORED_HOME_1F_GEOMETRY_OFFLINE_NOT_PLAYABLE",
        "size": [WIDTH, HEIGHT], "furniture": furniture,
        "proposed_positions": {
            name: {"x": xy[0], "y": xy[1],
                   "static_passability_checked": True, "verified_in_game": False}
            for name, xy in positions.items()
        },
        "static_reachable_tiles": len(reached),
        "passability": "STATIC_TILE_FLAGS_ONLY",
        "events_installed": 0, "engine_warps_installed": False,
        "native_game_modified": False,
        "gameplay_playable": False, "tested_in_game": False,
    }
    return grid, report


def build(*, root: Path = ROOT, preview: Path | None = None,
          output: Path | None = None) -> dict:
    from audit_johto import checksum, read_map_data
    from stage import serialize
    from verify_johto import inspect
    from server.ruby_marshal import RubyData, RubyObject, text

    root = root.resolve()
    work = (root / ".blue-work").resolve()
    preview = (preview or root / ".blue-work/johto-staging-bedroom-v1").absolute()
    output = (output or root / ".blue-work/johto-staging-home1f-v1").absolute()
    game = root / "game"
    if (work.is_symlink() or preview.is_symlink() or output.is_symlink()
            or not preview.resolve().is_relative_to(work)
            or not output.resolve().is_relative_to(work)
            or preview.resolve() == work or output.resolve() == work
            or preview.resolve() == output.resolve() or output.exists()
            or output.resolve().is_relative_to(preview.resolve())
            or preview.resolve().is_relative_to(output.resolve())):
        raise ValueError("Entrada/saida devem ser pastas separadas e NOVAS em .blue-work")
    if inspect(preview, game, root=root).get("status") != "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE":
        raise ValueError("Preview de origem ainda nao verificada")
    stage = json.loads((preview / "johto-stage.json").read_text(encoding="utf-8"))
    rows = {r["symbol"]: r for r in stage["maps"]}
    if (rows.get(BEDROOM, {}).get("origin") != "BLUE_AUTHORED_OFFLINE_BEDROOM_V1"
            or "bedroom_offline_preview" not in stage
            or rows.get(SYMBOL, {}).get("origin") != "BLUE_NATIVE_INTERIOR_TEMPLATE"):
        raise ValueError("Primeiro concluir 4/12 com quarto e preservar casa 1F provisoria")
    map_id = rows[SYMBOL].get("destination_id")
    if type(map_id) is not int or not 600 <= map_id <= 999:
        raise ValueError("MapID de New Bark 1F invalido")
    input_map = preview / "Data" / f"Map{map_id:03d}.rxdata"
    room = read_map_data(input_map)
    tilesets = read_map_data(preview / "Data/Tilesets.rxdata")
    if not isinstance(room, RubyObject) or room.name != "RPG::Map" or not isinstance(tilesets, list):
        raise ValueError("Dados RXDATA invalidos")
    tid = room.attrs.get("@tileset_id")
    if (type(tid) is not int or not 0 < tid < len(tilesets)
            or not isinstance(tilesets[tid], RubyObject)
            or text(tilesets[tid].attrs.get("@tileset_name")).casefold() != "inside"):
        raise ValueError("Casa 1F exige tileset nativo Inside.png")
    passages = tilesets[tid].attrs.get("@passages")
    if not isinstance(passages, RubyData) or passages.name != "Table":
        raise ValueError("Passabilidade real de Inside ausente")
    _, flags = table_values(passages.data, dimensions=1)
    raw, report = blueprint(flags)

    new_room = copy.deepcopy(room)
    new_room.attrs.update({
        "@width": WIDTH, "@height": HEIGHT, "@data": RubyData("Table", raw),
        "@events": {}, "@encounter_list": [],
        "@autoplay_bgm": False, "@autoplay_bgs": False,
    })
    for key in ("@bgm", "@bgs"):
        audio = new_room.attrs.get(key)
        if isinstance(audio, RubyObject):
            audio.attrs["@name"] = b""
    binary = serialize(new_room)
    report.update({
        "map_id": map_id, "tileset_id": tid,
        "original_map_sha256": checksum(input_map),
        "new_map_sha256": hashlib.sha256(binary).hexdigest(),
        "source_archive_sha256": stage["source_archive_sha256"],
        "bedroom_map_id": rows[BEDROOM]["destination_id"],
    })
    edited = copy.deepcopy(stage)
    entry = next(r for r in edited["maps"] if r["symbol"] == SYMBOL)
    entry.update({
        "origin": "BLUE_AUTHORED_OFFLINE_HOME1F_V1",
        "home_1f_authored_geometry": True, "layout_is_hgss_verified": False,
        "events_imported": 0,
    })
    edited["warnings"].append(
        "Casa 1F gerada offline; NPC mae, escada e porta ainda SEM eventos/teste real"
    )
    edited["home_1f_offline_preview"] = report
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-home1f-", dir=output.parent) as tmp:
        stage_dir = Path(tmp) / "preview"
        shutil.copytree(preview, stage_dir)
        (stage_dir / "Data" / f"Map{map_id:03d}.rxdata").write_bytes(binary)
        (stage_dir / "johto-stage.json").write_text(
            json.dumps(edited, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        if inspect(stage_dir, game, root=root).get("status") != "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE":
            raise ValueError("Casa 1F nao passou verificacao estrutural")
        if output.exists() or output.is_symlink():
            raise ValueError("Preview ja existe: nao sobrescrever")
        stage_dir.rename(output)
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--preview", type=Path)
    p.add_argument("--output", type=Path)
    args = p.parse_args(argv)
    try:
        result = build(root=args.root, preview=args.preview, output=args.output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("[JOHTO][BLOQUEADO]", exc, file=sys.stderr)
        return 2
    print("[JOHTO] Casa 1F pronta em PREVIEW: Map%03d" % result["map_id"])
    print("[JOHTO] Sem executar Game.exe, alterar game/, saves ou Kanto")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
