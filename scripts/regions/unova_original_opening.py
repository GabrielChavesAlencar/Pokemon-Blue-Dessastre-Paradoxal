"""Author the opening corridor as private RMXP geometry using Blue's original tiles."""

import argparse
import json
from pathlib import Path
import sys
import tempfile

from generate_sinnoh_original_j10a import (
    BED, BOOK, BRIDGE, COMPUTER, COUNTER, DESK, DOOR, FENCE, FLOOR, FLOOR_ALT,
    FLOWERS, GRASS, LAB_BENCH, LAMP, MACHINE, PATH, PILLOW, PLANT, ROCK, RUG,
    SHELF, SINK, SOFA, STAIR, TABLE, TREE, WALL, WATER, WINDOW,
    at, box, checksum, fill, png_bytes, svg_preview, validate_scene,
)
from author_sinnoh_playable_j10 import build_rxdata
from audit_unova_a13_private_qa import no_symlink_ancestors

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(".blue-work/unova/original-opening")

BEDROOM = "UNOVA_PLAYER_BEDROOM"
HOUSE = "UNOVA_PLAYER_HOUSE"
NUVEMA = "UNOVA_NUVEMA_TOWN"
LAB = "UNOVA_NUVEMA_LAB"
ROUTE = "UNOVA_ROUTE_01"
ACCUMULA = "UNOVA_ACCUMULA_TOWN"
CENTER = "UNOVA_ACCUMULA_CENTER"

# A walkable threshold and distinct arrival cell on each end of every door.
# Store symbols until F01 assigns stable destination MapIDs.
LINKS = (
    ((BEDROOM, (15, 3), (14, 3)), (HOUSE, (3, 4), (4, 4))),
    ((HOUSE, (11, 13), (11, 12)), (NUVEMA, (7, 8), (7, 9))),
    ((NUVEMA, (23, 8), (23, 9)), (LAB, (8, 14), (8, 13))),
    ((NUVEMA, (29, 16), (28, 16)), (ROUTE, (0, 18), (1, 18))),
    ((ROUTE, (29, 5), (28, 5)), (ACCUMULA, (0, 12), (1, 12))),
    ((ACCUMULA, (24, 8), (24, 9)), (CENTER, (9, 12), (9, 11))),
)


def layout(symbol, width, height, base, *, exterior=False):
    scene = {"symbol": symbol, "width": width, "height": height,
             "layers": [[0] * (width * height) for _ in range(3)],
             "access": [], "landmarks": []}
    fill(scene, 0, 0, 0, width - 1, height - 1, base)
    box(scene, 0, 0, width - 1, height - 1, TREE if exterior else WALL)
    if not exterior:
        fill(scene, 1, 1, 1, width - 2, 1, WALL)
        for x in (3, width - 4):
            at(scene, 2, x, 1, WINDOW)
    return scene


def bedroom():
    scene = layout(BEDROOM, 18, 13, FLOOR_ALT)
    fill(scene, 0, 6, 4, 12, 9, RUG)
    fill(scene, 1, 2, 3, 3, 6, BED)
    fill(scene, 2, 2, 3, 3, 3, PILLOW)
    fill(scene, 1, 8, 2, 12, 2, DESK)
    at(scene, 2, 10, 2, COMPUTER)
    fill(scene, 1, 11, 10, 15, 10, SHELF)
    at(scene, 2, 12, 10, BOOK)
    at(scene, 1, 15, 3, STAIR)
    scene["landmarks"] = [(8, 6), (4, 5)]
    return scene


def house():
    scene = layout(HOUSE, 22, 14, FLOOR)
    fill(scene, 0, 6, 6, 13, 11, RUG)
    fill(scene, 1, 2, 6, 3, 9, SOFA)
    fill(scene, 1, 7, 7, 9, 8, TABLE)
    fill(scene, 1, 15, 3, 19, 3, COUNTER)
    at(scene, 2, 16, 3, SINK)
    at(scene, 1, 3, 4, STAIR)
    at(scene, 1, 19, 10, PLANT)
    scene["landmarks"] = [(6, 8)]
    return scene


def nuvema():
    scene = layout(NUVEMA, 30, 23, GRASS, exterior=True)
    fill(scene, 0, 14, 0, 15, 21, WATER)
    fill(scene, 0, 5, 12, 25, 14, PATH)
    fill(scene, 0, 14, 12, 15, 14, BRIDGE)
    fill(scene, 0, 6, 8, 8, 12, PATH)
    fill(scene, 0, 22, 8, 24, 12, PATH)
    fill(scene, 0, 24, 13, 29, 17, PATH)
    for left, right, door_x in ((4, 10, 7), (20, 26, 23)):
        fill(scene, 1, left, 4, right, 8, WALL)
        fill(scene, 2, left + 1, 5, right - 1, 5, WINDOW)
        at(scene, 1, door_x, 8, DOOR)
    fill(scene, 1, 2, 18, 10, 18, FENCE)
    fill(scene, 1, 18, 18, 25, 19, FLOWERS)
    scene["landmarks"] = [(10, 13), (25, 15)]
    return scene


def laboratory():
    scene = layout(LAB, 22, 15, FLOOR_ALT)
    fill(scene, 0, 7, 4, 14, 12, FLOOR)
    fill(scene, 1, 3, 4, 4, 9, LAB_BENCH)
    fill(scene, 1, 16, 4, 18, 9, LAB_BENCH)
    for x in (4, 17):
        at(scene, 2, x, 5, COMPUTER)
        at(scene, 2, x, 8, LAMP)
    fill(scene, 1, 8, 3, 13, 3, MACHINE)
    scene["landmarks"] = [(11, 5), (6, 8)]
    return scene


def route():
    scene = layout(ROUTE, 30, 24, GRASS, exterior=True)
    fill(scene, 0, 0, 17, 10, 19, PATH)
    fill(scene, 0, 9, 11, 11, 19, PATH)
    fill(scene, 0, 9, 10, 22, 12, PATH)
    fill(scene, 0, 20, 4, 22, 12, PATH)
    fill(scene, 0, 20, 4, 29, 6, PATH)
    fill(scene, 0, 13, 0, 16, 22, WATER)
    fill(scene, 0, 13, 10, 16, 12, BRIDGE)
    fill(scene, 1, 2, 8, 7, 9, TREE)
    fill(scene, 1, 19, 16, 23, 16, FENCE)
    for x, y in ((5, 14), (7, 15), (24, 9), (25, 11)):
        at(scene, 1, x, y, FLOWERS)
    at(scene, 1, 18, 13, ROCK)
    at(scene, 2, 24, 5, LAMP)
    scene["landmarks"] = [(6, 15), (24, 10)]
    return scene


def accumula():
    scene = layout(ACCUMULA, 32, 23, GRASS, exterior=True)
    fill(scene, 0, 0, 11, 29, 14, PATH)
    fill(scene, 0, 9, 5, 19, 18, PATH)
    fill(scene, 0, 12, 9, 16, 13, WATER)
    fill(scene, 0, 23, 8, 25, 11, PATH)
    fill(scene, 1, 21, 4, 28, 8, WALL)
    fill(scene, 2, 22, 5, 27, 5, WINDOW)
    at(scene, 1, 24, 8, DOOR)
    for x, y in ((10, 6), (18, 6), (10, 17), (18, 17)):
        at(scene, 1, x, y, PLANT)
    fill(scene, 1, 20, 18, 28, 19, FLOWERS)
    at(scene, 1, 8, 13, LAMP)
    scene["landmarks"] = [(10, 12), (18, 15)]
    return scene


def center():
    scene = layout(CENTER, 20, 13, FLOOR_ALT)
    fill(scene, 0, 7, 4, 12, 11, RUG)
    fill(scene, 1, 7, 4, 12, 4, COUNTER)
    at(scene, 2, 10, 4, COMPUTER)
    fill(scene, 1, 2, 5, 3, 8, SOFA)
    fill(scene, 1, 15, 5, 17, 8, SHELF)
    at(scene, 1, 16, 3, PLANT)
    scene["landmarks"] = [(9, 5), (5, 7)]
    return scene


def generate():
    scenes = {scene["symbol"]: scene for scene in
              (bedroom(), house(), nuvema(), laboratory(), route(), accumula(), center())}
    transfers = {symbol: [] for symbol in scenes}
    for first, second in LINKS:
        for (symbol, threshold, arrival), (target, _, target_arrival) in ((first, second), (second, first)):
            scene = scenes[symbol]
            x, y = threshold
            if abs(x - arrival[0]) + abs(y - arrival[1]) != 1:
                raise ValueError(f"Chegada fora da vizinhança da porta: {symbol}")
            at(scene, 1, x, y, DOOR if symbol != ROUTE else 0)
            scene["access"].append(threshold)
            scene["landmarks"].extend((threshold, arrival))
            transfers[symbol].append({"threshold": threshold, "destination": target,
                                      "arrival": target_arrival})

    art = png_bytes()
    files = {"BlueOriginalOpening.png": art}
    maps = {}
    for symbol, scene in scenes.items():
        validate_scene(scene)
        geometry = build_rxdata({**scene, "tileset_id": 1}, art)
        name = symbol + ".rxdata"
        files[name] = geometry
        files[f"previews/{symbol}.svg"] = svg_preview(scene).encode("utf-8")
        maps[symbol] = {"file": name, "map_id": None, "size": [scene["width"], scene["height"]],
                        "sha256": checksum(geometry), "candidate_doors": transfers[symbol],
                        "reachable_cells": scene["walkable_reachable"]}
    receipt = {
        "schema": 1, "phase": "F02_F03_F05", "region": "UNOVA",
        "status": "ORIGINAL_GEOMETRY_FOR_PRIVATE_QA",
        "tileset_sha256": checksum(art), "tileset_id_bound": False,
        "maps": maps, "native_events_installed": False, "runtime_verified": False,
    }
    files["manifest.json"] = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return files, receipt


def build(project):
    output = project / OUTPUT
    no_symlink_ancestors(output)
    if output.exists():
        raise ValueError("Já existe uma exportação de QA.")
    files, receipt = generate()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".opening-", dir=output.parent) as workspace:
        pending = Path(workspace) / "export"
        pending.mkdir()
        for name, content in files.items():
            path = pending / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        pending.rename(output)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build", action="store_true", help="Exportar para .blue-work/unova/original-opening")
    args = parser.parse_args()
    try:
        receipt = build(ROOT) if args.build else generate()[1]
    except (ValueError, OSError) as error:
        print(error, file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
