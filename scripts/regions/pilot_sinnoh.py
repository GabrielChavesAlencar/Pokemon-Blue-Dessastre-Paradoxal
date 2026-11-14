"""Build a private Sinnoh pilot from the verified Ancient Platinum release."""
from __future__ import annotations

import argparse
import copy
import json
import re
import zipfile
import shutil
import uuid
from pathlib import Path

from build_johto_events import EVENT_CLASSES, command, event_page, ruby
from compile_johto_connections import merge_pbs
from johto_qa import SYSTEM_CLASSES, checksum, json_bytes, regular, safe_path
from pilot_hoenn import append_event, copy_game, install_copy, open_tile, reachable, startup
from server.ruby_marshal import loads, text
from stage import ROOT, serialize

SOURCE_SHA256 = "a8480968f93a81e81a0b2b0aedb00bd3069aed828432ec78ed890602e2d5d697"
PREFIX = "Pokemon-Ancient-Platinum-Release/"
NAMES = {32: "Twinleaf Town", 102: "Casa do jogador", 42: "Rota 201",
         43: "Sandgem Town", 104: "Laboratório do Professor Rowan", 96: "Centro Pokémon de Sandgem"}
IDS = dict(zip(NAMES, range(800, 806)))
START = (102, 29, 5)
WARPS = (
    ((32, 24, 23), (32, 24, 24), (102, 7, 10), (102, 7, 9)),
    ((102, 10, 4), (102, 9, 4), (102, 32, 4), (102, 31, 4)),
    ((43, 7, 9), (43, 7, 10), (104, 7, 15), (104, 7, 14)),
    ((43, 16, 8), (43, 16, 9), (96, 10, 14), (96, 10, 13)),
)
ACTORS = (
    (102, 8, 8, "Mom", "NPC_GSC_Mom", "BlueSinnohPreview.mother"),
    (104, 7, 7, "Rowan", "NPC_DPP_Rowan", "BlueSinnohPreview.rowan"),
    (96, 9, 6, "Nurse", "NPC_DPP_PokeCenter_Nurse", "BlueSinnohPreview.heal"),
)
CONNECTIONS = ((32, "North", 0, 42, "South", 6), (43, "West", 4, 42, "East", 0))
PLUGIN = "Plugins/ZZZZZ Blue Sinnoh Pilot"


def build_overlay(game, archive):
    if checksum(regular(archive)) != SOURCE_SHA256:
        raise ValueError("O ZIP não corresponde à edição auditada do Ancient Platinum")
    native_infos = loads(regular(game / "Data/MapInfos.rxdata").read_bytes())
    native_tiles = loads(regular(game / "Data/Tilesets.rxdata").read_bytes())
    occupied = {int(m[1]) for p in (game / "Data").iterdir()
                if (m := re.fullmatch(r"Map(\d+)\.rxdata", p.name, re.I))}
    for path in (game / "PBS").glob("*.txt"):
        if path.stem.startswith(("encounters", "map_metadata")):
            data = regular(path).read_text("utf-8-sig")
            occupied.update(int(m[1]) for m in re.finditer(r"(?m)^\s*\[\s*(\d+)", data))
        if path.stem.startswith("map_connections"):
            for line in regular(path).read_text("utf-8-sig").splitlines():
                fields = line.split("#", 1)[0].split(",")
                if len(fields) == 6:
                    occupied.update(int(fields[i]) for i in (0, 3) if fields[i].strip().isdigit())
    if set(IDS.values()) & (occupied | set(native_infos)):
        raise ValueError("Os IDs do piloto Sinnoh 800–805 já estão em uso")
    overlay, maps, tiles, remap = {}, {}, {}, {}
    with zipfile.ZipFile(archive) as z:
        def read(name):
            info = z.getinfo(PREFIX + name)
            if info.file_size > 16_000_000:
                raise ValueError("Recurso de Sinnoh excede o tamanho esperado")
            return z.read(info)

        donor_tiles = loads(read("Data/Tilesets.rxdata"))
        native_links = loads(read("Data/map_connections.dat"))
        for a, ae, ax, b, be, bx in CONNECTIONS:
            if [a, ae[0].encode(), ax, b, be[0].encode(), bx] not in native_links:
                raise ValueError(f"Borda da fonte divergente: {a}/{b}")
        for old in NAMES:
            m = loads(read(f"Data/Map{old:03}.rxdata"))
            tid = m.attrs["@tileset_id"]
            if tid not in remap:
                ts = donor_tiles[tid]
                for key in ("@panorama_name", "@fog_name", "@battleback_name"):
                    ts.attrs[key] = b""
                for key, folder in (("@tileset_name", "Tilesets"), ("@autotile_names", "Autotiles")):
                    names = ts.attrs[key] if folder == "Autotiles" else [ts.attrs[key]]
                    refs = []
                    for raw_name in names:
                        if not raw_name:
                            refs.append(b"")
                            continue
                        name = text(raw_name)
                        if not re.fullmatch(r"[A-Za-z0-9_ ()-]+", name):
                            raise ValueError(f"Gráfico inválido: {name}")
                        ref = f"BLUE_SINNOH_{name}"
                        asset = read(f"Graphics/{folder}/{name}.png")
                        if not asset.startswith(b"\x89PNG\r\n\x1a\n"):
                            raise ValueError(f"PNG inválido: {name}")
                        overlay[f"Graphics/{folder}/{ref}.png"] = asset
                        refs.append(ref.encode("ascii"))
                    ts.attrs[key] = refs if folder == "Autotiles" else refs[0]
                remap[tid] = len(native_tiles)
                native_tiles.append(ts)
            m.attrs.update({"@tileset_id": remap[tid], "@events": {}, "@autoplay_bgm": False,
                            "@autoplay_bgs": False, "@encounter_list": [], "@encounter_step": 30})
            for key in ("@bgm", "@bgs"):
                m.attrs[key] = ruby("RPG::AudioFile", name=b"", volume=100, pitch=100)
            maps[old], tiles[old] = m, native_tiles[remap[tid]]

    required, edges = set(), {}
    for index, (a, ar, b, br) in enumerate(WARPS):
        for point, arrival, suffix in ((a, br, "a"), (b, ar, "b")):
            mid, x, y = point
            dest, dx, dy = arrival
            edges[point] = [arrival]
            required.update((point, arrival))
            append_event(maps[mid], f"SN_Door{index}_{suffix}", x, y,
                         event_page(warp=(IDS[dest], dx, dy), touch=True))
    for a, ae, ax, b, be, bx in CONNECTIONS:
        ma, mb = maps[a].attrs, maps[b].attrs
        for coord in range(ma["@width"] if ae == "North" else ma["@height"]):
            other = coord - ax + bx
            p, q = ((a, coord, 0), (b, other, mb["@height"] - 1)) if ae == "North" else (
                (a, 0, coord), (b, mb["@width"] - 1, other))
            if all(open_tile(maps[i], tiles[i], x, y) for i, x, y in (p, q)):
                edges.setdefault(p, []).append(q)
                edges.setdefault(q, []).append(p)
    for old, x, y, name, sprite, code in ACTORS:
        regular(game / f"Graphics/Characters/{sprite}.png")
        append_event(maps[old], f"SN_{name}", x, y, event_page(script=code, sprite=sprite))
    reachable(START, required | {(102, 8, 9), (104, 7, 8), (96, 9, 7)}, tiles, maps, edges,
              {row[:3] for row in ACTORS})
    profile = event_page(script="BlueSinnohPreview.profile")
    profile.attrs.update({"@trigger": 3, "@through": True})
    profile.attrs["@list"].insert(-1, command(123, b"A", 0))
    append_event(maps[102], "SN_Profile", *START[1:], profile)
    off = copy.deepcopy(profile)
    off.attrs["@condition"].attrs.update({"@self_switch_valid": True, "@self_switch_ch": b"A"})
    off.attrs.update({"@trigger": 0, "@list": [command(0)]})
    list(maps[102].attrs["@events"].values())[-1].attrs["@pages"].append(off)
    order = max(info.attrs.get("@order", 0) for info in native_infos.values())
    for ix, (old, label) in enumerate(NAMES.items(), 1):
        new = IDS[old]
        native_infos[new] = ruby("RPG::MapInfo", name=label.encode(), parent_id=0, order=order+ix,
                                 expanded=False, scroll_x=0, scroll_y=0)
        overlay[f"Data/Map{new:03}.rxdata"] = serialize(maps[old], EVENT_CLASSES)
    overlay["Data/MapInfos.rxdata"] = serialize(native_infos)
    overlay["Data/Tilesets.rxdata"] = serialize(native_tiles)
    path = "PBS/map_connections.txt"
    rows = "\n".join(f"{IDS[a]},{ae},{ax},{IDS[b]},{be},{bx}" for a, ae, ax, b, be, bx in CONNECTIONS)
    original = regular(game / path).read_bytes()
    merged = merge_pbs(original, rows)
    overlay[path] = original + merged[len(original):].replace(b"Blue Johto", b"Blue Sinnoh")
    overlay["PBS/map_metadata_sinnoh_pilot.txt"] = "".join(
        f"[{IDS[old]}]\nName = {label}\n" + ("Outdoor = true\n" if old in (32, 42, 43) else "")
        for old, label in NAMES.items()).encode()
    overlay["PBS/encounters_sinnoh_pilot.txt"] = (
        f"[{IDS[42]}]\nLand,21\n    50,STARLY,2,3\n    50,BIDOOF,2,3\n").encode()
    system = loads(regular(game / "Data/System.rxdata").read_bytes())
    start = (IDS[START[0]], *START[1:])
    system.attrs.update(dict(zip(("@start_map_id", "@start_x", "@start_y"), start)))
    overlay["Data/System.rxdata"] = serialize(system, SYSTEM_CLASSES)
    overlay["Data/Scripts.rxdata"] = startup(regular(game / "Data/Scripts.rxdata").read_bytes(),
                                             region="sinnoh", module="BlueSinnohPreview")
    overlay["Data/blue-sinnoh-compile-request.txt"] = (SOURCE_SHA256 + "\n").encode()
    report = {"region": "SINNOH", "start": start, "maps": IDS, "source_sha256": SOURCE_SHA256}
    overlay["Sinnoh pilot.json"] = json_bytes(report)
    overlay[f"{PLUGIN}/meta.txt"] = (
        b"Name = Blue Sinnoh Pilot\nVersion = 0.1\nEssentials = 21.1\n"
        b"Requires = Blue Battle Presentation and Story\nScripts = SinnohPreview.rb\n")
    overlay[f"{PLUGIN}/SinnohPreview.rb"] = regular(Path(__file__).with_name("SinnohPreview.rb")).read_bytes()
    music = "Plugins/ZZZZ Blue Music/BlueMusic.rb"
    if (game / music).is_file():
        overlay[music] = regular(ROOT / "scripts/music/BlueMusic.rb").read_bytes()
    config = regular(game / "mkxp.json").read_text("utf-8-sig")
    config = re.sub(r'(?m)^\s*"(?:windowTitle|dataPathApp|dataPathOrg)"\s*:[^\r\n]*(?:\r?\n|$)', "", config)
    options = json.dumps({"windowTitle": "Pokemon Blue - Sinnoh Piloto",
                          "dataPathOrg": "Dessastre Paradoxal Sinnoh Testes",
                          "dataPathApp": "Sinnoh Piloto"})[1:-1]
    header = re.search(r"(?m)^\s*\{", config)
    if header is None:
        raise ValueError("mkxp.json inválido")
    overlay["mkxp.json"] = (config[:header.end()] + "\n    " + options + ",\n" + config[header.end():]).encode()
    ini, count = re.subn(r"(?m)^Title=[^\r\n]*", "Title=Sinnoh Piloto",
                         regular(game / "Game.ini").read_text("utf-8-sig"))
    if count != 1:
        raise ValueError("Game.ini precisa de um Title")
    overlay["Game.ini"] = ini.encode()
    return overlay, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("game", "source", "output"):
        parser.add_argument(f"--{name}", required=True, type=Path)
    args = parser.parse_args()
    game, source, output = (safe_path(p) for p in (args.game, args.source, args.output))
    pending = safe_path(output.parent / f".sinnoh-{uuid.uuid4().hex}")
    if output.exists() or output.is_relative_to(game) or game.is_relative_to(output):
        parser.error("Escolha um destino novo e fora do jogo principal")
    overlay, report = build_overlay(game, source)
    pending.mkdir(parents=True)
    try:
        copy_game(game, pending)
        install_copy(pending, game, output, overlay)
    finally:
        if pending.exists() and safe_path(pending).parent == output.parent:
            shutil.rmtree(pending)
    print(json.dumps(report, ensure_ascii=True))


if __name__ == "__main__":
    main()
