"""Build the local Hoenn test game from pinned RMXP geometry and a Blue copy."""

from __future__ import annotations

import argparse
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
from build_johto_events import EVENT_CLASSES, event_page, ruby
from compile_johto_connections import merge_pbs
from johto_qa import SAVE, SYSTEM_CLASSES, Marshal, RubyString, dump, json_bytes, regular, safe_path
from server.ruby_marshal import RubyObject, loads, text
from stage import ROOT, serialize

UPSTREAM = "c59233bdbaac4fbfeca6aa01c7f05be628da2a92"
SOURCE_MAPS = {
    7: "Littleroot Town", 8: "Casa do jogador", 11: "Laboratório do Birch",
    101: "Rota 101", 12: "Oldale Town", 13: "Centro Pokémon de Oldale",
}
WARP_PAIRS = (
    ((7, 5, 8), (7, 5, 9), (8, 10, 10), (8, 10, 9)),
    ((8, 10, 4), (8, 10, 5), (8, 28, 3), (8, 28, 4)),
    ((7, 7, 16), (7, 7, 17), (11, 8, 14), (11, 8, 13)),
    ((12, 6, 16), (12, 6, 17), (13, 8, 10), (13, 8, 9)),
)
PEOPLE = (
    (8, 4, 8, "Mae", "NPC_GSC_Mom", "BlueHoennPilot.mother"),
    (11, 8, 6, "Birch", "NPC_ORAS_Professor_Birch", "BlueHoennPilot.birch"),
    (11, 7, 5, "Treecko", "Object_Ball", "BlueHoennPilot.choose_starter(:TREECKO)"),
    (11, 8, 5, "Torchic", "Object_Ball", "BlueHoennPilot.choose_starter(:TORCHIC)"),
    (11, 9, 5, "Mudkip", "Object_Ball", "BlueHoennPilot.choose_starter(:MUDKIP)"),
    (13, 9, 6, "Enfermeira", "NPC_DPP_PokeCenter_Nurse", "BlueHoennPilot.heal"),
)
BORDERS = ((7, "North", 101, "South"), (12, "South", 101, "North"))
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


def open_tile(map_data, tileset, x, y):
    attrs = map_data.attrs
    (w, h, depth), cells = table_values(attrs["@data"].data, 3)
    if not (0 <= x < w and 0 <= y < h):
        return False
    _, passages = table_values(tileset.attrs["@passages"].data)
    _, priorities = table_values(tileset.attrs["@priorities"].data)
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
        edges[a] = [b_arrival]
        edges[b] = [a_arrival]
        required.update((a, a_arrival, b, b_arrival))
    for first, edge, second, _ in BORDERS:
        if maps[first].attrs["@width"] != maps[second].attrs["@width"]:
            raise ValueError("Borda Hoenn diverge da largura auditada")
        y = 0 if edge == "North" else maps[first].attrs["@height"] - 1
        other_y = maps[second].attrs["@height"] - 1 if edge == "North" else 0
        pairs = [((first, x, y), (second, x, other_y))
                 for x in range(maps[first].attrs["@width"])
                 if open_tile(maps[first], tiles[first], x, y)
                 and open_tile(maps[second], tiles[second], x, other_y)]
        if not pairs:
            raise ValueError("Borda Hoenn sem cruzamento passável")
        for a, b in pairs:
            edges.setdefault(a, []).append(b)
            edges.setdefault(b, []).append(a)
    # Test the exact standing cells used to interact with the NPCs and Poké Balls.
    required.update(((8, 4, 9), (11, 8, 7), (11, 7, 6), (11, 9, 6), (13, 9, 7)))
    reachable(START, required, tiles, maps, edges, blocked)


def startup(blob: bytes) -> bytes:
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
    source = source.replace(run_plugins, before + run_plugins).replace(initialize, after + initialize)
    row[2] = RubyString(zlib.compress(source.encode("utf-8")))
    return b"\x04\x08" + dump(rows)


def append_event(map_data, name, x, y, page):
    events = map_data.attrs["@events"]
    if any((obj.attrs["@x"], obj.attrs["@y"]) == (x, y) for obj in events.values()):
        raise ValueError(f"Eventos Hoenn se sobrepõem em {(x, y)}")
    n = len(events) + 1
    events[n] = ruby("RPG::Event", id=n, name=name.encode("ascii"), x=x, y=y, pages=[page])


def build_overlay(game, source):
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
        m.attrs.update({
            "@tileset_id": tile_ids[native_id], "@events": {}, "@autoplay_bgm": False,
            "@autoplay_bgs": False, "@bgm": ruby("RPG::AudioFile", name=b"", volume=100, pitch=100),
            "@bgs": ruby("RPG::AudioFile", name=b"", volume=100, pitch=100),
            "@encounter_list": [], "@encounter_step": 30,
        })
    validate_geometry(maps, tiles)

    upstream_connections = set(source.read("PBS/map_connections.txt").decode("utf-8-sig").splitlines())
    rows = []
    for a, edge_a, b, edge_b in BORDERS:
        if f"{a},{edge_a},0,{b},{edge_b},0" not in upstream_connections:
            raise ValueError(f"Conexão de origem não encontrada: {a}/{b}")
        rows.append(f"{ids[a]},{edge_a},0,{ids[b]},{edge_b},0")
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
        append_event(maps[mid], f"HN_{name}", x, y, event_page(script=handler, sprite=sprite))

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
    overlay["PBS/encounters_hoenn_pilot.txt"] = (
        f"[{ids[101]}]\nLand,21\n"
        "    45,ZIGZAGOON,2,3\n    35,POOCHYENA,2,3\n    20,WURMPLE,2,3\n"
    ).encode("ascii")
    overlay["PBS/map_metadata_hoenn_pilot.txt"] = "".join(
        f"[{ids[mid]}]\nName = {name}\n" + ("Outdoor = true\n" if mid in (7, 12, 101) else "")
        for mid, name in SOURCE_MAPS.items()
    ).encode("utf-8")
    overlay["Data/blue-hoenn-compile-request.txt"] = (UPSTREAM + "\n").encode("ascii")
    report = {"region": "HOENN", "kind": "ISOLATED_HOENN_TEST", "source_commit": UPSTREAM,
              "start": [ids[START[0]], *START[1:]], "maps": ids, "save_profile": PROFILE}
    overlay["Hoenn pilot.json"] = json_bytes(report)
    marker_rows = ["BLUE_HOENN_PILOT_V1", ",".join(map(str, report["start"]))]
    marker_rows.extend(f"{old},{new}" for old, new in ids.items())
    overlay["Data/blue-hoenn-pilot.txt"] = ("\n".join(marker_rows) + "\n").encode("ascii")
    overlay[f"{PLUGIN}/meta.txt"] = (
        b"Name = Blue Hoenn Pilot\nVersion = 0.1\nEssentials = 21.1\n"
        b"Requires = Blue Battle Presentation and Story\nScripts = HoennPilot.rb\n"
    )
    overlay[f"{PLUGIN}/HoennPilot.rb"] = regular(ROOT / "scripts/regions/HoennPilot.rb").read_bytes()
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
