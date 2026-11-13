"""Audit the REAL New Bark exterior (Map079) read-only from the user's v1 ZIP.

Records graphic doorway CANDIDATES, not authorized/verified event positions.
Does not need or touch game/. Does not evaluate Ruby or import external scripts.
"""
from __future__ import annotations

import argparse
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

from audit_johto import ROOT, checksum
from server.ruby_marshal import RubyObject, RubyData, loads

SPEC = ROOT / "data/regions/johto-new-bark-exterior-v1.json"
ARCHIVE = ROOT / ".blue-work/johto-source/original.zip"
OUTPUT = ROOT / ".blue-work/johto-new-bark-exterior-audit.json"
MAX_BYTES = 32_000_000
SHA = re.compile(r"[a-f0-9]{64}\Z")


def read_archive_member(archive: zipfile.ZipFile, suffix: str) -> bytes:
    options = [i for i in archive.infolist()
               if i.filename.replace("\\", "/").endswith(suffix)]
    if len(options) != 1:
        raise ValueError("ZIP deve conter exatamente um arquivo: " + suffix)
    info = options[0]
    if (info.is_dir() or info.file_size <= 0 or info.file_size > MAX_BYTES or
            info.compress_size <= 0 or info.file_size > info.compress_size * 400 or
            ((info.external_attr >> 16) & 0o170000) == 0o120000 or
            ".." in Path(info.filename).parts):
        raise ValueError("Arquivo suspeito ou excessivo dentro do ZIP: " + suffix)
    return archive.read(info)


def decode_table(value: RubyData, dimensions: int, width: int, height: int):
    if (not isinstance(value, RubyData) or value.name != "Table" or
            not isinstance(value.data, bytes) or len(value.data) < 20):
        raise ValueError("Tabela de tiles RPG Maker XP ausente")
    dim, w, h, depth, count = struct.unpack("<5I", value.data[:20])
    if (dim, w, h, depth) != (dimensions, width, height, 3 if dimensions == 3 else 1):
        raise ValueError("Dimensoes da Table nao correspondem ao mapa/tileset")
    if count != width * height * (3 if dimensions == 3 else 1):
        raise ValueError("Quantidade de tiles incompatível")
    if len(value.data) != 20 + count * 2:
        raise ValueError("Tabela de tiles truncada")
    return struct.unpack("<" + str(count) + "H", value.data[20:])


def compile_audit(archive: Path, spec: dict, *, root: Path = ROOT) -> dict:
    root = root.resolve()
    archive = archive.absolute()
    work = (root / ".blue-work").resolve()
    if (archive.is_symlink() or not archive.resolve().is_relative_to(work) or
            not archive.is_file()):
        raise ValueError("O ZIP deve estar dentro de .blue-work/ sem symlinks")
    if (spec.get("schema"), spec.get("region"), spec.get("can_install"),
            spec.get("all_door_identifications_verified")) != (1, "JOHTO", False, False):
        raise ValueError("Somente candidatos New Bark sem aprovar jogabilidade")
    source_sha = checksum(archive)
    if source_sha != spec.get("source_archive_sha256") or not SHA.fullmatch(source_sha):
        raise ValueError("ZIP v1 difere do SHA-256 real auditado")
    with zipfile.ZipFile(archive) as package:
        raw_map = read_archive_member(package, "/Data/Map079.rxdata")
        raw_tiles = read_archive_member(package, "/Data/Tilesets.rxdata")
    import hashlib
    if (hashlib.sha256(raw_map).hexdigest() != spec.get("map", {}).get("source_sha256")
            or hashlib.sha256(raw_tiles).hexdigest() != spec.get("tilesets_source_sha256")):
        raise ValueError("New Bark Map079/Tilesets mudou desde a auditoria")
    world = loads(raw_map)
    tilesets = loads(raw_tiles)
    if not isinstance(world, RubyObject) or world.name != "RPG::Map":
        raise ValueError("Map079 nao e RPG::Map")
    w, h, tid = (world.attrs.get("@width"), world.attrs.get("@height"),
                 world.attrs.get("@tileset_id"))
    expected = spec["map"]
    if (w, h, tid) != (expected.get("width"), expected.get("height"),
                        expected.get("tileset_id")):
        raise ValueError("Dimensoes/tileset de New Bark divergiram")
    if (type(w) is not int or type(h) is not int or
            not isinstance(tilesets, list) or
            type(tid) is not int or tid >= len(tilesets) or
            not isinstance(tilesets[tid], RubyObject)):
        raise ValueError("Tileset original nao encontrado")
    world_tiles = decode_table(world.attrs.get("@data"), 3, w, h)
    ts = tilesets[tid]
    if ts.name != "RPG::Tileset":
        raise ValueError("Johto tem tileset nao suportado")
    passages = ts.attrs.get("@passages")
    priorities = ts.attrs.get("@priorities")
    def read_1d(tab):
        if not isinstance(tab, RubyData) or len(tab.data) < 20:
            raise ValueError("Flags de passagem/prioridade ausentes")
        _, number, _, _, _ = struct.unpack("<5I", tab.data[:20])
        return decode_table(tab, 1, number, 1)
    blocked = read_1d(passages)
    prio = read_1d(priorities)
    rows = spec.get("entrances")
    if not isinstance(rows, list) or len(rows) != 4:
        raise ValueError("Quatro candidatos de fachada sao obrigatorios")
    result = []
    ids = set()
    for candidate in rows:
        eid = candidate.get("id")
        x, y, street_y = (candidate.get("x"), candidate.get("y"),
                          candidate.get("street_y"))
        if (not isinstance(eid, str) or eid in ids or
                type(x) is not int or type(y) is not int or
                type(street_y) is not int or street_y != y + 2 or
                not 0 <= x < w or not 0 <= y < h-2 or
                candidate.get("verified_position") is not False):
            raise ValueError("Coordenada candidata invalida/ja aprovada: " + str(eid))
        ids.add(eid)
        def at(col: int, line: int):
            return [world_tiles[k * w * h + line * w + col] for k in range(3)]
        tile1, tile2, tile3 = at(x,y), at(x,y+1), at(x,street_y)
        if (tile1 != candidate.get("expected_door_tiles") or
                tile2 != candidate.get("expected_south_tile")):
            raise ValueError("Tiles de fachada mudaram desde a inspecao: " + eid)
        flags = []
        for one in (tile1, tile2, tile3):
            if any(t >= len(blocked) for t in one):
                raise ValueError("ID de tile fora do tileset real: " + eid)
            flags.append({
                "tiles": one,
                "passage_bits": [blocked[t] for t in one],
                "priorities": [prio[t] for t in one],
                "no_full_blocker_visible": all((blocked[t] & 15) != 15 for t in one if t),
            })
        result.append({
            "candidate": eid, "x": x, "y": y,
            "sidewalk_below": [x, street_y],
            "building_role": candidate["building_role"],
            "source_tiles_confirmed": True,
            "sprite_collisions_verified": False,
            "passability_tested_in_engine": False,
            "door_identification_verified": False,
            "tile_flags": flags
        })
    return {
        "schema": 1, "region": "JOHTO",
        "status": "REAL_EXTERIOR_TILES_VERIFIED_DOORS_NOT_PLAYABLE",
        "map_source_id": 79, "source_archive_sha256": source_sha,
        "width": w, "height": h, "tileset_id": tid,
        "candidates_checked": len(result), "candidates": result,
        "gameplay_playable": False, "gameplay_tested": False,
        "can_install": False,
        "note": ("A visual tile candidate is not a tested door. Confirm the actual "
                 "home and lab roles, arrivals, sprite collisions and game save locally.")
    }


def publish(result: dict, output: Path, *, root: Path = ROOT) -> None:
    work = (root.resolve() / ".blue-work").resolve()
    target = output.absolute()
    if (target.is_symlink() or target.exists() or target.resolve() == work or
            not target.resolve().is_relative_to(work)):
        raise ValueError("Relatorio deve ser arquivo NOVO em .blue-work")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ARCHIVE)
    parser.add_argument("--spec", type=Path, default=SPEC)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args(argv)
    try:
        spec = json.loads(args.spec.read_text(encoding="utf-8"))
        result = compile_audit(args.archive, spec)
        publish(result, args.output)
    except (OSError, ValueError, TypeError, KeyError, zipfile.BadZipFile) as e:
        print("[JOHTO][BLOQUEADO] " + str(e), file=sys.stderr)
        return 2
    print("[JOHTO] %d fachadas candidatas comparadas com Map079 real."
          % result["candidates_checked"])
    print("[JOHTO] Nenhuma porta ou fase jogavel foi declarada validada.")
    print("[JOHTO] Saida:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
