"""Read-only verification of Johto's non-executable geometry staging folder.

Does NOT certify playable maps, NPCs, music, assets licenses or completed Johto.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from audit_johto import ROOT, checksum, map_files, read_map_data
from server.ruby_marshal import RubyObject


def inspect(preview: Path, game: Path, *, root: Path = ROOT) -> dict:
    work = (root.resolve() / ".blue-work").resolve()
    preview = preview.resolve()
    game = game.resolve()
    if (not preview.is_relative_to(work)
            or game != (root.resolve() / "game").resolve()):
        raise ValueError("Verify only .blue-work previews against the original game/")
    info = preview / "johto-stage.json"
    if not info.is_file():
        raise ValueError("Not a staged Johto preview")
    report = json.loads(info.read_text(encoding="utf-8"))
    if (report.get("schema"), report.get("region"), report.get("status"),
        report.get("can_install"), report.get("not_playable")) != (
            1, "JOHTO", "GEOMETRY_PREVIEW_ONLY", False, True):
        raise ValueError("Unrecognized/unsafe Johto staging metadata")
    if not isinstance(report.get("maps"), list) or not report["maps"]:
        raise ValueError("Johto preview has no audited maps")

    forbidden = {"Game.exe", "Data/System.rxdata", "Data/Scripts.rxdata",
                 "Data/PluginScripts.rxdata", "Game.ini"}
    files = [f for f in preview.rglob("*") if f.is_file() or f.is_symlink()]
    for file in files:
        relative = file.relative_to(preview)
        safe_top = (relative.parts[0] in ("Data", "Graphics")
                    or relative.name in ("johto-stage.json", "LEIA-ME.txt"))
        if (file.is_symlink() or not safe_top
                or relative.as_posix() in forbidden
                or relative.parts[0] == "Audio"
                or file.suffix.lower() in (".rb", ".exe", ".dll", ".bat", ".cmd", ".py")):
            raise ValueError("Unexpected executable or asset in Johto stage: " + str(relative))
    if checksum(game / "Data/MapInfos.rxdata") != report["native_mapinfos_sha256"]:
        raise ValueError("Native MapInfos changed since preview")
    if checksum(game / "Data/Tilesets.rxdata") != report["native_tilesets_sha256"]:
        raise ValueError("Native Tilesets changed since preview")

    base_infos = read_map_data(game / "Data/MapInfos.rxdata")
    base_tiles = read_map_data(game / "Data/Tilesets.rxdata")
    infos = read_map_data(preview / "Data/MapInfos.rxdata")
    tiles = read_map_data(preview / "Data/Tilesets.rxdata")
    if not (isinstance(base_infos, dict) and isinstance(infos, dict)
            and isinstance(base_tiles, list) and isinstance(tiles, list)):
        raise ValueError("Johto MapInfos or Tilesets have the wrong format")
    for map_id, old_info in base_infos.items():
        if map_id not in infos or infos[map_id] != old_info:
            raise ValueError("Original Decades/Kanto MapInfos changed")
    if tiles[:len(base_tiles)] != base_tiles:
        raise ValueError("Original Decades/Kanto Tilesets changed")

    rows = report["maps"]
    expected_ids = [x["destination_id"] for x in rows]
    if (any(type(n) is not int or n < 600 or n > 999 for n in expected_ids)
            or len(set(expected_ids)) != len(expected_ids)):
        raise ValueError("Invalid staged Johto destination MapIDs")
    original_ids = set(base_infos) | set(map_files(game / "Data"))
    if original_ids & set(expected_ids):
        raise ValueError("Johto preview overwrote a native MapID")
    generated = set(map_files(preview / "Data"))
    if generated != set(expected_ids):
        raise ValueError("Unexpected/missing preview map data files")

    for row in rows:
        dest = row["destination_id"]
        m = read_map_data(preview / "Data" / f"Map{dest:03d}.rxdata")
        if not isinstance(m, RubyObject) or m.name != "RPG::Map":
            raise ValueError("Staged Johto file is not an RMXP map")
        if m.attrs.get("@events") != {}:
            raise ValueError("Foreign events in Johto preview")
        if m.attrs.get("@autoplay_bgm") or m.attrs.get("@autoplay_bgs"):
            raise ValueError("Johto preview plays unverified music")
        for attr in ("@bgm", "@bgs"):
            audio = m.attrs.get(attr)
            if isinstance(audio, RubyObject) and audio.attrs.get("@name"):
                raise ValueError("Unapproved foreign music cue in preview")
        tid = m.attrs.get("@tileset_id")
        if (type(tid) is not int or not len(base_tiles) <= tid < len(tiles)):
            raise ValueError("Staged Johto tileset is missing/remapped incorrectly")
        if dest not in infos or not isinstance(infos[dest], RubyObject):
            raise ValueError("Staged Johto MapInfo is missing")
        if row["events_imported"] != 0:
            raise ValueError("Johto stage cannot mark source events imported")

    return {"region": "JOHTO", "status": "STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE",
            "maps": len(rows), "original_maps_preserved": len(base_infos),
            "original_tilesets_preserved": len(base_tiles),
            "events_imported": 0, "can_install": False}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--preview", type=Path, default=ROOT / ".blue-work/johto-staging")
    p.add_argument("--game", type=Path, default=ROOT / "game")
    args = p.parse_args(argv)
    try:
        result = inspect(args.preview, args.game)
    except (OSError, ValueError, TypeError, KeyError) as error:
        print("[JOHTO][BLOQUEADO] " + str(error), file=sys.stderr)
        return 2
    print("[JOHTO] %d mapas de terreno verificados, ZERO eventos; jogo mestre preservado."
          % result["maps"])
    print("[JOHTO] Nao comprova jogabilidade. Status: " + result["status"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
