"""Kanto phase-0: read-only 64-track audio and regional integration baseline.

Checks actual MP3 bytes using the existing Git-blob SHA audit. Source map IDs
are FRLG IDs, not the compiled Blue MapIDs. Never modifies game/, maps,
music settings, audio, or saves; reports go under ignored .blue-work only.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if __package__:
    from . import install_kanto_music
else:
    import install_kanto_music

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/regions/kanto-source.json"
RUNTIME = ROOT / "scripts/music/BlueMusic.rb"
PLANNED = ROOT / "docs/KANTO_PLANO_APLICAR_MUSICAS.md"
TOTAL_MAPS = 142
PREVIEW_MAPS = 45

# Strictly real names from the pinned source: never use these FRLG source
# IDs as compiled map IDs or mark a missing city/feature as implemented.
CANDIDATE_MAP_GROUPS = {
    "pallet": ("PALLET_TOWN", "OAK_LAB"),
    "route_1": ("ROUTE_1",),
    "viridian_forest": ("VIRIDIAN_FOREST",),
    "pewter": ("PEWTER_CITY",),
    "mt_moon": ("MT_MOON_1F", "MT_MOON_B1F", "MT_MOON_B2F"),
    "route_4": ("ROUTE_4",),
    "pokemon_centers": ("*_CENTER",),
    "gyms": ("*_GYM",),
    "vermilion": ("VERMILION_CITY",),
    "ss_anne": ("SS_ANNE_*",),
    "celadon": ("CELADON_CITY",),
    "rocket_game_corner": ("ROCKET_GAME_CORNER",),
    "rocket_hideout": ("ROCKET_HIDEOUT*",),
    "silph": ("SILPH_LOBBY", "SILPH_1F", "SILPH_2F", "SILPH_3F",
              "SILPH_4F", "SILPH_5F", "SILPH_6F", "SILPH_7F",
              "SILPH_8F", "SILPH_9F", "SILPH_10F", "SILPH_11F"),
    "fuchsia": ("FUCHSIA_CITY",),
    "cinnabar": ("CINNABAR_ISLAND",),
    "mansion": ("MANSION_1F", "MANSION_2F", "MANSION_3F", "MANSION_B1F"),
    "lavender": ("LAVENDER_TOWN",),
    "pokemon_tower": ("POKEMON_TOWER*",),
    "net_center": ("POKEMON_NET_CENTER",),
    "sevii": ("SEVII_*",),
}


def expand_groups(maps: dict[str, str], preview: set[int]) -> dict:
    result = {}
    for group, patterns in CANDIDATE_MAP_GROUPS.items():
        matched = [
            {"source_id": int(source_id), "key": key,
             "status": "preview_only" if int(source_id) in preview
             else "experimental"}
            for source_id, key in maps.items()
            if any(__import__("fnmatch").fnmatchcase(key, pattern)
                   for pattern in patterns)
        ]
        matched.sort(key=lambda row: row["source_id"])
        result[group] = {
            "source_map_ids_only": matched,
            "source_count": len(matched),
            "status": "absent_from_pilot_manifest" if not matched else
                      "preview_only" if all(m["status"] == "preview_only"
                                            for m in matched) else "candidate",
        }
    return result


def inspect_runtime(plugin_text: str) -> dict:
    """Report *static* hook presence, not simulated or real sound playback."""
    required = {
        "map_bgm_hook": "def self.apply_map(",
        "wild_battle_bgm_hook": "def pbGetWildBattleBGM(",
        "trainer_battle_bgm_hook": "def pbGetTrainerBattleBGM(",
        "wild_victory_bgm_hook": "def pbGetWildVictoryBGM(",
        "trainer_victory_bgm_hook": "def pbGetTrainerVictoryBGM(",
    }
    missing = [label for label, token in required.items()
               if token not in plugin_text]
    if missing:
        raise ValueError("Regressão: hook BlueMusic existente ausente: " +
                         ", ".join(missing))
    return {
        "map_bgm_hook": "present_static",
        "wild_battle_bgm_hook": "present_static",
        "trainer_battle_bgm_hook": "present_static",
        "wild_victory_bgm_hook": "present_static",
        "trainer_victory_bgm_hook": "present_static",
        "gym_victory_separate_hook": (
            "present_static" if "def pbGetGymVictoryBGM(" in plugin_text
            else "not_implemented"
        ),
        "me_event_playback_hook": (
            "present_static" if re.search(
                r"(?<!\w)(?:pbMEPlay|pbMEFade|Audio\.me_play)\b", plugin_text
            ) else "not_implemented"
        ),
        "kanto_region_guard": (
            "present_static" if ("BlueRegions" in plugin_text
                                 or "BlueRegionalPolicy" in plugin_text)
            else "not_implemented"
        ),
        "global_battle_config": (
            "present_static" if "entry('global',key)" in plugin_text
            else "not_detected"
        ),
        "native_audio_decoder_tested": False,
        "visual_gameplay_tested": False,
        "note": ("Source-code inspection only; the RPG Maker engine may support "
                 "other playback APIs, but no native audio was played here."),
    }


def inspect_game(game: Path, tracks: list[dict]) -> dict:
    """Read-only comparison for an EXPLICIT game path (not by default)."""
    root = game.resolve()
    if not root.is_dir() or not (root / "Game.exe").is_file():
        return {"status": "unavailable", "tested_playback": False}
    if not (root / "Audio").is_dir():
        return {"status": "missing_audio_directory", "tested_playback": False}
    available = 0
    missing = 0
    mismatch = []
    for row in tracks:
        target = root / row["game_path"]
        if not target.resolve().is_relative_to(root):
            raise ValueError("Destino de áudio usa symlink fora do game: " +
                             row["game_path"])
        if not target.is_file():
            missing += 1
        elif (target.stat().st_size == row["bytes"] and
              install_kanto_music.git_blob_sha(target) == row["git_blob_sha"]):
            available += 1
        else:
            mismatch.append(row["game_path"])
    return {
        "status": "files_present" if available == 64 and not mismatch
                  else "incomplete",
        "matched": available, "missing": missing,
        "conflicting": mismatch,
        "tested_playback": False,
    }


def inspect(root: Path = ROOT, game: Path | None = None,
            *, check_audio_bytes: bool = True) -> dict:
    """Build an inert report; raises on any real catalog or source regression."""
    manifest_file = root / "data/kanto-music.json"
    catalog = json.loads(manifest_file.read_text(encoding="utf-8"))
    if check_audio_bytes:
        integrity = install_kanto_music.audit(manifest_file, root)
        if (integrity["files"], integrity["BGM"], integrity["ME"],
            integrity["bytes"]) != (64, 50, 14, 135_768_381):
            raise ValueError("Regressão na integridade do catálogo Kanto")
    else:
        # Intended only for synthetic unit-test fixtures; the CLI always
        # hashes 100% of the real MP3 bytes with check_audio_bytes=True.
        integrity = {"files": len(catalog["files"]),
                     "BGM": sum(t["kind"] == "BGM" for t in catalog["files"]),
                     "ME": sum(t["kind"] == "ME" for t in catalog["files"]),
                     "bytes": sum(t["bytes"] for t in catalog["files"])}
    if len(catalog["files"]) != 64:
        raise ValueError("Inventário incompleto")
    source = json.loads((root / "data/regions/kanto-source.json").read_text(
        encoding="utf-8"))
    maps = source["maps"]
    preview = set(source["preview_only"])
    if len(maps) != TOTAL_MAPS or len(preview) != PREVIEW_MAPS:
        raise ValueError("Regressão: Kanto deveria ter 142 mapas e 45 previews")
    if not preview.issubset({int(k) for k in maps}):
        raise ValueError("Preview aponta para mapa inexistente")
    plugin = (root / "scripts/music/BlueMusic.rb").read_text(encoding="utf-8")
    grouped = expand_groups(maps, preview)
    # Do not invent map existence for absent parts of the original soundtrack.
    source_names = set(maps.values())
    if "LAVENDER_TOWN" in source_names or "SEVII_ISLANDS" in source_names:
        # This is a legitimate future expansion; the report must be updated
        # before such a source map is claimed as an installed route.
        raise ValueError("Mapa novo requer revisão da classificação musical")
    result = {
        "schema": 1, "phase": 0, "region": "KANTO",
        "result": "PASS_STATIC_BASELINE",
        "audio_catalog": {
            "tracks_verified_by_git_blob_sha": integrity["files"],
            "BGM": integrity["BGM"],
            "ME": integrity["ME"],
            "total_bytes": integrity["bytes"],
            "files_changed": False, "playback_tested": False,
        },
        "source_maps": {
            "source_count": len(maps), "preview_only": len(preview),
            "compiled_map_ids_audited": False,
            "reason": "Kanto pilot.json in a generated game is required to resolve compiled IDs",
            "groups": grouped,
        },
        "runtime_hooks": inspect_runtime(plugin),
        "integration": {
            "map_music_bindings_added": 0,
            "event_music_bindings_added": 0,
            "new_audio_hooks_added": 0,
            "save_or_decades_changes": False,
            "next_phase": 1,
            "blocking_future_tests": [
                "Compile source map keys to installed pilot MapIDs",
                "Isolate Kanto battle music from global Decades preferences",
                "Implement ME event hooks and conditional gym victory BGM",
                "Test native MP3/ME playback on an interactive Windows game"
            ],
        },
        "local_game": (
            {"status": "not_checked", "tested_playback": False}
            if game is None else inspect_game(game, catalog["files"])
        ),
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path,
                        help="Optional read-only check of a local game/ or pilot; no writes")
    parser.add_argument("--output", type=Path,
                        default=ROOT / ".blue-work/kanto-music-phase0.json")
    args = parser.parse_args(argv)
    output = args.output.resolve()
    allowed = (ROOT / ".blue-work").resolve()
    if not output.is_relative_to(allowed) or output == allowed:
        parser.error("Relatórios somente dentro de .blue-work (ignorado pelo Git)")
    try:
        report = inspect(ROOT, args.game)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8")
        print("KANTO_MUSIC_PHASE_0:" + json.dumps({
            "result": report["result"],
            "verified": report["audio_catalog"]["tracks_verified_by_git_blob_sha"],
            "bgm": report["audio_catalog"]["BGM"],
            "me": report["audio_catalog"]["ME"],
            "source_maps": report["source_maps"]["source_count"],
            "previews": report["source_maps"]["preview_only"],
            "local_game_status": report["local_game"]["status"],
            "report": str(output),
            "native_playback_tested": False,
        }, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError,
            json.JSONDecodeError) as error:
        print("[KANTO MUSIC PHASE 0 ERROR] " + str(error), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
