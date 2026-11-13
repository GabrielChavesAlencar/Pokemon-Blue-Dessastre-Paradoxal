"""Create an original New Bark player bedroom in a private Johto geometry preview.

Uses installed Inside tiles, NOT third-party RXDATA in GitHub. No game/ edits,
event installs or native runtime promises. Preview only.
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

ROOT = Path(__file__).resolve().parents[2]
SYMBOL = "JOHTO_NEW_BARK_PLAYER_HOME_2F"
WIDTH, HEIGHT = 14, 11
START = (6, 7)
STAIRS_APPROACH = (9, 8)


def tile(row: int, column: int) -> int:
    if not (0 <= column < 8 and 0 <= row < 618):
        raise ValueError("Outside Inside.png tile sheet")
    return 384 + 8 * row + column


def table_values(data: bytes, *, dimensions: int | None = None):
    if not isinstance(data, bytes) or len(data) < 20:
        raise ValueError("RGSS Table truncada")
    dim, w, h, z, count = struct.unpack_from("<5I", data)
    if ((dimensions is not None and dim != dimensions)
            or count != w * h * z or len(data) != 20 + 2 * count):
        raise ValueError("RGSS Table inconsistente")
    return (w, h, z), struct.unpack_from(f"<{count}H", data, 20)


def blueprint(passages: tuple[int, ...]) -> tuple[bytes, dict]:
    """Build actual NEW tile geometry. Proposed coordinates are NOT verified in-game."""
    cells = [0] * (WIDTH * HEIGHT * 3)
    furniture_items = []

    def cell(x: int, y: int, z: int, number: int, label: str):
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT and 0 <= z < 3):
            raise ValueError("Outside bedroom: " + label)
        if number >= len(passages):
            raise ValueError("Inside tileset lacks tile " + str(number))
        index = x + WIDTH * (y + HEIGHT * z)
        if z and cells[index]:
            raise ValueError("Overlapping bedroom decor: " + label)
        cells[index] = number

    # Author-created wood flooring (no cloned cabin layout) with proper borders.
    for y in range(1, HEIGHT - 1):
        for x in range(1, WIDTH - 1):
            cell(x, y, 0, tile(88, (x + y) % 2), "wooden floor")
    for x in range(1, WIDTH - 1):
        cell(x, 0, 0, tile(190, 3), "upper wall")
        cell(x, 1, 1, tile(191, 3), "wall")
        cell(x, HEIGHT - 1, 0, tile(190, 0), "lower wall")
    for y in range(HEIGHT):
        cell(0, y, 0, tile(190, 0), "left wall")
        cell(WIDTH - 1, y, 0, tile(190, 0), "right wall")

    def furniture(name: str, x: int, y: int, row: int, col: int, width: int, height: int):
        for dy in range(height):
            for dx in range(width):
                cell(x + dx, y + dy, 2, tile(row + dy, col + dx), name)
        furniture_items.append({
            "name": name, "x": x, "y": y, "width": width, "height": height
        })

    furniture("bed_blue", 2, 3, 275, 0, 2, 3)
    furniture("writing_desk", 6, 3, 280, 0, 3, 2)
    furniture("wardrobe", 10, 3, 280, 4, 2, 2)
    furniture("wall_window", 5, 1, 208, 1, 2, 1)
    furniture("stairs_visual", 10, 7, 238, 1, 2, 2)

    def walkable(x, y):
        return all(not (passages[cells[x + WIDTH * (y + HEIGHT * z)]] & 0x0F)
                   for z in range(3))

    if not (walkable(*START) and walkable(*STAIRS_APPROACH)):
        raise ValueError("Proposed spawn/stairs approach blocked in static tileset")
    reached, queue = {START}, [START]
    while queue:
        x, y = queue.pop()
        for nx, ny in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
            if (1 <= nx < WIDTH-1 and 2 <= ny < HEIGHT-1
                    and (nx,ny) not in reached and walkable(nx,ny)):
                reached.add((nx,ny))
                queue.append((nx,ny))
    if STAIRS_APPROACH not in reached or len(reached) < 15:
        raise ValueError("Stair approach not reachable from proposed spawn")
    raw = struct.pack("<5I", 3, WIDTH, HEIGHT, 3, len(cells))
    raw += struct.pack(f"<{len(cells)}H", *cells)
    return raw, {
        "schema": 1, "region": "JOHTO", "symbol": SYMBOL,
        "status": "AUTHORED_BEDROOM_GEOMETRY_OFFLINE_NOT_PLAYABLE",
        "size": [WIDTH, HEIGHT], "furniture": furniture_items,
        "spawn_proposal": {"x": START[0], "y": START[1], "verified_in_game": False},
        "stairs_approach_proposal": {
            "x": STAIRS_APPROACH[0], "y": STAIRS_APPROACH[1],
            "verified_in_game": False
        },
        "static_reachable_tiles": len(reached),
        "passability": "STATIC_TILE_FLAGS_ONLY",
        "events_installed": 0,
        "native_game_modified": False,
        "gameplay_playable": False, "tested_in_game": False
    }


def build(*, root: Path = ROOT, preview: Path | None = None,
          output: Path | None = None) -> dict:
    from audit_johto import checksum, read_map_data
    from stage import serialize
    from verify_johto import inspect
    from server.ruby_marshal import RubyData, RubyObject, text

    root = root.resolve()
    work = (root / ".blue-work").resolve()
    preview = (preview or root / ".blue-work/johto-staging-interiors").absolute()
    output = (output or root / ".blue-work/johto-staging-bedroom-v1").absolute()
    game = root / "game"
    if (work.is_symlink() or preview.is_symlink() or output.is_symlink()
            or not preview.resolve().is_relative_to(work)
            or not output.resolve().is_relative_to(work)
            or output.resolve() in (work, preview.resolve())
            or output.resolve().is_relative_to(preview.resolve())
            or preview.resolve().is_relative_to(output.resolve())
            or output.exists()):
        raise ValueError("Origem/destino NOVO devem ficar separados em .blue-work/")
    if inspect(preview, game, root=root).get("status") != "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE":
        raise ValueError("Previa de mapas nao verificada")
    stage = json.loads((preview / "johto-stage.json").read_text(encoding="utf-8"))
    rows = [r for r in stage["maps"] if r.get("symbol") == SYMBOL]
    if len(rows) != 1 or rows[0].get("origin") != "BLUE_NATIVE_INTERIOR_TEMPLATE":
        raise ValueError("O quarto provisório não foi encontrado na prévia")
    map_id = rows[0].get("destination_id")
    if type(map_id) is not int or not 600 <= map_id <= 999:
        raise ValueError("MapID Johto inválido")
    filename = preview / "Data" / f"Map{map_id:03d}.rxdata"
    room = read_map_data(filename)
    tiles = read_map_data(preview / "Data/Tilesets.rxdata")
    if not isinstance(room, RubyObject) or room.name != "RPG::Map" or not isinstance(tiles, list):
        raise ValueError("Mapa/Tilesets RMXP inválidos")
    tid = room.attrs.get("@tileset_id")
    if (type(tid) is not int or not 0 < tid < len(tiles)
            or not isinstance(tiles[tid], RubyObject)
            or text(tiles[tid].attrs.get("@tileset_name")).lower() != "inside"):
        raise ValueError("Quarto requer tileset nativo Inside.png")
    p = tiles[tid].attrs.get("@passages")
    if not isinstance(p, RubyData) or p.name != "Table":
        raise ValueError("Tileset não tem passabilidade RMXP")
    _, flags = table_values(p.data, dimensions=1)
    table, proof = blueprint(flags)

    created = copy.deepcopy(room)
    created.attrs["@width"], created.attrs["@height"] = WIDTH, HEIGHT
    created.attrs["@data"] = RubyData("Table", table)
    created.attrs["@events"] = {}
    created.attrs["@encounter_list"] = []
    created.attrs["@autoplay_bgm"] = created.attrs["@autoplay_bgs"] = False
    for sound in ("@bgm","@bgs"):
        audio = created.attrs.get(sound)
        if isinstance(audio, RubyObject):
            audio.attrs["@name"] = b""
    binary = serialize(created)
    proof.update({
        "map_id": map_id, "native_tileset_id": tid,
        "original_map_sha256": checksum(filename),
        "new_map_sha256": hashlib.sha256(binary).hexdigest(),
        "source_archive_sha256": stage["source_archive_sha256"]
    })
    planned = copy.deepcopy(stage)
    target_row = next(r for r in planned["maps"] if r["symbol"] == SYMBOL)
    target_row.update({
        "origin": "BLUE_AUTHORED_OFFLINE_BEDROOM_V1",
        "bedroom_authored_geometry": True,
        "layout_is_hgss_verified": False, "events_imported": 0
    })
    planned["warnings"].append(
        "Bedroom geometry authored offline; spawn, warp and gameplay need Windows QA"
    )
    planned["bedroom_offline_preview"] = proof

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-bedroom-", dir=output.parent) as t:
        dest = Path(t) / "preview"
        shutil.copytree(preview, dest)
        (dest / "Data" / f"Map{map_id:03d}.rxdata").write_bytes(binary)
        (dest / "johto-stage.json").write_text(
            json.dumps(planned, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        if inspect(dest, game, root=root).get("status") != "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE":
            raise ValueError("Quarto novo não passou auditoria de geometria")
        if output.exists() or output.is_symlink():
            raise ValueError("Destino criado durante a montagem: sem overwrite")
        dest.rename(output)
    return proof


def main(argv=None) -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root", type=Path, default=ROOT)
    cli.add_argument("--preview", type=Path)
    cli.add_argument("--output", type=Path)
    opts = cli.parse_args(argv)
    try:
        report = build(root=opts.root, preview=opts.preview, output=opts.output)
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print("[JOHTO][BLOQUEADO]", exc, file=sys.stderr)
        return 2
    print("[JOHTO] Quarto novo construido em preview: Map%03d.rxdata" % report["map_id"])
    print("[JOHTO] Spawn somente PROPOSTO:", report["spawn_proposal"])
    print("[JOHTO] Nao executa Game.exe nem altera game/ ou saves")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
