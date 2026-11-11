"""Stage Kanto's terrain in a NEW local workspace; never patch the installed game.

Original event scripts are intentionally excluded from this geometry preview.
Consult plan.json before adapting the campaign events and PBS.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import tempfile
from pathlib import Path

from audit import ROOT, KANTO, inventory, json_file, load, map_plan
from pbs import build_drafts
from server.ruby_marshal import RubyData, RubyObject, integer, loads, text

CLASSES = {"RPG::Map", "RPG::MapInfo", "RPG::Tileset", "RPG::AudioFile"}
NATIVE = {"Table", "Color", "Tone"}


def serialize(value):
    """Serialize only the structures used by this map/tileset preview."""
    def symbol(s):
        b = s.encode("ascii")
        return b":" + integer(len(b)) + b

    def write(obj):
        if obj is None:
            return b"0"
        if type(obj) is bool:
            return b"T" if obj else b"F"
        if type(obj) is int:
            return b"i" + integer(obj)
        if isinstance(obj, bytes):
            return b'"' + integer(len(obj)) + obj
        if isinstance(obj, list):
            return b"[" + integer(len(obj)) + b"".join(map(write, obj))
        if isinstance(obj, dict):
            return b"{" + integer(len(obj)) + b"".join(write(k) + write(v) for k, v in obj.items())
        if isinstance(obj, RubyObject) and obj.name in CLASSES:
            return b"o" + symbol(obj.name) + integer(len(obj.attrs)) + b"".join(
                symbol(k) + write(v) for k, v in obj.attrs.items())
        if isinstance(obj, RubyData) and obj.name in NATIVE:
            return b"u" + symbol(obj.name) + integer(len(obj.data)) + obj.data
        raise ValueError(f"Cannot stage {type(obj).__name__} {getattr(obj, 'name', '')}")

    result = b"\x04\x08" + write(value)
    if loads(result) != value:
        raise ValueError("RPG Maker round trip changed staged data")
    return result


def stage(project, source, game, output):
    """Publish a complete preview directory by rename, or leave no output at all."""
    allowed = (project / ".blue-work").resolve()
    output = output.resolve()
    if not output.is_relative_to(allowed) or output == allowed or output.exists():
        raise ValueError("Staging requires a new folder inside .blue-work")
    if source.resolve().is_relative_to(output) or game.resolve().is_relative_to(output):
        raise ValueError("Staging cannot replace the source or the installed game")
    plan = map_plan(source, game, json_file(KANTO))
    source_infos, files = inventory(source)
    dest_infos, dest_files = inventory(game)
    source_tiles = load(source / "Data/Tilesets.rxdata")
    tiles = load(game / "Data/Tilesets.rxdata")
    new_tiles = {}
    blobs = {}

    def graphic(folder, value):
        name = text(value)
        if not name:
            return b""
        if not re.fullmatch(r"[\w .()\-]+", name) or name in (".", ".."):
            raise ValueError(f"Invalid source graphic: {name}")
        filename = f"FRLG_Preview_{name}.png"
        path = source / "Graphics" / folder / (name + ".png")
        if not path.resolve().is_relative_to(source.resolve()) or not path.is_file():
            raise ValueError(f"Missing {folder} graphic: {name}")
        raw = path.read_bytes()
        if not raw.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError(f"Invalid PNG: {path}")
        relative = Path("Graphics", folder, filename)
        if (game / relative).exists():
            raise ValueError(f"Preview graphic clashes with installed project: {relative}")
        blobs[relative] = raw
        return filename[:-4].encode("utf-8")

    for row in plan["maps"]:
        src_id, dst_id = row["source_id"], row["proposed_id"]
        assert dst_id not in dest_infos and dst_id not in dest_files
        m = load(files[src_id])
        old_tile = m.attrs["@tileset_id"]
        if old_tile not in new_tiles:
            tile = source_tiles[old_tile]
            new_tiles[old_tile] = len(tiles)
            tile.attrs["@id"] = len(tiles)
            tile.attrs["@name"] = b"FRLG Preview " + tile.attrs["@name"]
            tile.attrs["@tileset_name"] = graphic("Tilesets", tile.attrs["@tileset_name"])
            tile.attrs["@autotile_names"] = [graphic("Autotiles", g) for g in tile.attrs["@autotile_names"]]
            for key in ("@panorama_name", "@fog_name", "@battleback_name"):
                tile.attrs[key] = b""
            tiles.append(tile)
        m.attrs["@tileset_id"] = new_tiles[old_tile]
        m.attrs["@events"] = {}   # No foreign switches, scripts, transfers or NPC rewards.
        m.attrs["@autoplay_bgm"] = m.attrs["@autoplay_bgs"] = False
        m.attrs["@bgm"].attrs["@name"] = m.attrs["@bgs"].attrs["@name"] = b""
        blobs[Path("Data", f"Map{dst_id:03d}.rxdata")] = serialize(m)
        info = source_infos[src_id]
        info.attrs["@name"] = b"[Kanto preview] " + info.attrs["@name"]
        info.attrs["@parent_id"] = row["parent"] or 0
        info.attrs["@order"] = max((x.attrs["@order"] for x in dest_infos.values()), default=0) + 1
        dest_infos[dst_id] = info
        row["staged_tileset"] = new_tiles[old_tile]
    blobs[Path("Data/MapInfos.rxdata")] = serialize(dest_infos)
    blobs[Path("Data/Tilesets.rxdata")] = serialize(tiles)
    blobs.update(build_drafts(source, game, plan))
    plan["status"] = "geometry_staged"
    plan["existing_binary_sha256"] = {
        name: hashlib.sha256((game / "Data" / name).read_bytes()).hexdigest()
        for name in ("MapInfos.rxdata", "Tilesets.rxdata")
    }
    blobs[Path("plan.json")] = (json.dumps(plan, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    blobs[Path("connections-preview.txt")] = (
        "\n".join(",".join(map(str, c)) for c in plan["connections"]) + "\n").encode("ascii")
    blobs[Path("LEIA-ME.txt")] = (
        "Previa de terreno: nao copiar para o jogo ativo. Eventos e musica foram removidos.\n"
        "Fonte: Essentials FRLG 1.1, TheTinfoilTemplar e equipe do Pokemon Essentials.\n"
        "Creditos da fonte: https://eeveeexpo.com/resources/1797/\n"
    ).encode("utf-8")
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".kanto-stage-", dir=output.parent) as directory:
        temporary = Path(directory) / "complete"
        for path, raw in blobs.items():
            target = temporary / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
        if output.exists():
            raise ValueError("Output was created by another process")
        temporary.rename(output)
    return plan


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--game", default=ROOT / "game", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    result = stage(ROOT, args.source, args.game, args.output)
    print(f"{len(result['maps'])} mapas de geometria preparados em {args.output}")


if __name__ == "__main__":
    main()
