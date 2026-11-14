#!/usr/bin/env python3
"""Refresh Hoenn QA12 teleport tools IN PLACE, without touching saves or game/.

Older QA12 copies did not include Data/blue-hoenn-test-stops.txt or the in-game
test menu. Recreate the 199 landing coordinates from the actual staged RXDATA,
back up existing pilot script/manifest, and atomically replace ONLY these QA
tool files. No donor ZIP or ROM is required to refresh an existing copy.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

from server.ruby_marshal import loads
from pilot_hoenn import ROOT, SOURCE_MAPS, UPSTREAM, build_test_stops, serialize_test_stops
from hoenn_qa_phase12 import audit_generated
from hoenn_qa_phase1 import require_private_path, verify_copy as base_verify_copy

STOPS = "Data/blue-hoenn-test-stops.txt"
PLUGIN = "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb"
MANIFEST = "Hoenn pilot.json"


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, tmp = tempfile.mkstemp(prefix=".hoenn-qa-teleport-", dir=path.parent)
    try:
        with os.fdopen(handle, "wb") as out:
            out.write(content)
            out.flush()
            os.fsync(out.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def prepare_updates(copy: Path, game: Path) -> dict[str, bytes]:
    copy = require_private_path(copy)
    if copy.name != "hoenn-qa-fase12":
        raise ValueError("Atualização do teleporte limitada ao perfil Hoenn QA Fase12")
    # Before touching a byte, ensure this is the original Blue private copy:
    # 199 RXDATA maps, a pinned donor ID, an isolated save profile, and an
    # unchanged Game.exe compared to the locally installed base.
    base_verify_copy(copy, game)
    manifest = json.loads((copy / MANIFEST).read_text("utf-8"))
    if (manifest.get("source_commit") != UPSTREAM or
        manifest.get("region") != "HOENN" or
        manifest.get("save_profile") != "Hoenn QA Fase12" or
        set(manifest.get("maps", {})) != {str(mid) for mid in SOURCE_MAPS}):
        raise ValueError("QA12 é de outra versão; não atualizar dados desconhecidos")
    ids = {int(k): v for k,v in manifest["maps"].items()}
    all_tiles = loads((copy / "Data/Tilesets.rxdata").read_bytes())
    maps, tiles = {}, {}
    for old, native in ids.items():
        source = copy / f"Data/Map{native:03}.rxdata"
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"Mapa original ausente ou link simbólico: {old}")
        world = loads(source.read_bytes())
        maps[old] = world
        tiles[old] = all_tiles[world.attrs["@tileset_id"]]
    stops = build_test_stops(maps, tiles, ids)
    raw = serialize_test_stops(stops)
    manifest["qa_test_stops"] = {
        "schema": 1, "count": len(stops),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "file": STOPS, "source_ids": [row[0] for row in stops],
        "real_terrain_walkable": True,
        "debug_only_no_story_flag_mutation": True,
        "game_exe_tested": False,
    }
    manifest["qa12"] = audit_generated(manifest)
    plugin = ROOT / "scripts/regions/HoennPilot.rb"
    if plugin.is_symlink() or not plugin.is_file():
        raise ValueError("HoennPilot.rb de QA não encontrado no projeto")
    return {
        STOPS: raw,
        PLUGIN: plugin.read_bytes(),
        MANIFEST: (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    }


def ensure_test_tools(copy: Path, game: Path = ROOT / "game") -> dict:
    copy = require_private_path(copy)
    desired = prepare_updates(copy, game)
    changes = {}
    for relative, content in desired.items():
        path = copy / relative
        if path.is_symlink():
            raise ValueError(f"Arquivo de teleporte não pode ser link simbólico: {relative}")
        previous = path.read_bytes() if path.exists() else None
        if previous != content:
            changes[path] = (previous, content)
    if not changes:
        return {"status": "ALREADY_CURRENT", "files_updated": 0,
                "stops": 199, "saves_touched": False, "native_tested": False}

    # Backup is in ignored .blue-work and NEVER in game/ or the save directory.
    backup = require_private_path(copy.parent / "hoenn-qa12-debug-backups" /
                                  f"update-{time.time_ns()}")
    backup.mkdir(parents=True, exist_ok=False)
    for path,(previous,_) in changes.items():
        if previous is not None:
            atomic_write(backup / path.relative_to(copy), previous)
    written = []
    try:
        for path,(_,content) in changes.items():
            atomic_write(path, content)
            written.append(path)
    except (OSError, ValueError):
        for path in reversed(written):
            previous = changes[path][0]
            if previous is None:
                path.unlink(missing_ok=True)
            else:
                atomic_write(path, previous)
        raise
    return {
        "status": "UPDATED_PRIVATE_DEBUG_TOOLS",
        "files_updated": len(changes), "stops": 199,
        "backup": str(backup.relative_to(ROOT)),
        "saves_touched": False, "native_tested": False,
    }


if __name__ == "__main__":
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", type=Path, default=ROOT/".blue-work/hoenn-qa-fase12")
    parser.add_argument("--game", type=Path, default=ROOT/"game")
    args=parser.parse_args()
    try:
        print(json.dumps(ensure_test_tools(args.copy,args.game), ensure_ascii=False))
    except (OSError, ValueError, KeyError, TypeError, IndexError, json.JSONDecodeError) as exc:
        parser.exit(2, f"Hoenn QA12 atualização de teleporte: {exc}\n")
