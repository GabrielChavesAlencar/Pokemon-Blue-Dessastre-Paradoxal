#!/usr/bin/env python3
"""Hoenn QA06 — audit climate story anchors in a PRIVATE isolated game copy.

Static RXDATA/manifest checks do not prove cutscenes, weather, audio or Game.exe.
Never copies or runs donor scripts and never writes to game/ or other saves.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from server.ruby_marshal import RubyObject, loads
from hoenn_qa_phase5 import required_event

# Original donor MapIDs, not their remapped 700–999 IDs.
CLIMATE_EVENTS = (
    (236, 23, 46, "HN10_Story_Kyogre", "BlueHoennPilot.seafloor_awakening", 1),
    (83, 32, 33, "HN10_Story_Sootopolis", "BlueHoennPilot.sootopolis_crisis", 1),
    (240, 11, 16, "HN10_Boss_OriginWallace", "BlueHoennPilot.origin_wallace_stage10", 0),
    (241, 13, 8, "HN10_Boss_PillarWallace", "BlueHoennPilot.sky_pillar_wallace", 0),
    (248, 15, 15, "HN10_Story_Rayquaza", "BlueHoennPilot.rayquaza_stage10", 1),
)
CAVE_MAPS = (238, 239, 240)
PILLAR_MAPS = tuple(range(241, 249))
REQUIRED_FLAGS = (
    "seafloor_archie_defeated", "groudon_awakened", "kyogre_awakened",
    "sootopolis_crisis_started", "sky_pillar_task", "sky_pillar_open",
    "rayquaza_summoned", "crisis_resolved",
)
RUBY_GUARDS = (
    "def self.qa6_at_map?(source_id)",
    "flags[\"seafloor_archie_defeated\"]",
    "qa6_at_map?(83)", "qa6_at_map?(240)",
    "qa6_at_map?(241)", "qa6_at_map?(248)",
    "!(243..248).cover?(source_id)",
    "flags[\"crisis_resolved\"]",
)


def verify_story_events(maps: dict[int, RubyObject]) -> dict:
    for mid, x, y, name, script, trigger in CLIMATE_EVENTS:
        if mid not in maps:
            raise ValueError(f"Hoenn QA06 sem mapa {mid} para {name}")
        required_event(maps[mid], mid, x, y, name, script, trigger)
    return {
        "verified_climate_events": len(CLIMATE_EVENTS),
        "cave_of_origin_source_maps": list(CAVE_MAPS),
        "sky_pillar_source_maps": list(PILLAR_MAPS),
        "story_flags": list(REQUIRED_FLAGS),
    }


def audit_generated(maps: dict[int, RubyObject]) -> dict:
    missing = set(CAVE_MAPS + PILLAR_MAPS + (83, 236)) - set(maps)
    if missing:
        raise ValueError(f"QA06: mapas ausentes: {sorted(missing)}")
    return {
        **verify_story_events(maps),
        "map_local_story_guards": True,
        "native_game_exe_tested": False,
        "native_weather_visuals_verified": False,
        "native_rayquaza_cinematic_verified": False,
        "native_sky_pillar_puzzles_verified": False,
        "donor_scripts_executed": False,
        "native_story_accepted": False,
    }


def verify_copy(copy: Path) -> dict:
    from hoenn_qa_phase1 import require_private_path
    copy = require_private_path(copy)
    report = json.loads((copy / "Hoenn pilot.json").read_text("utf-8"))
    ids = report.get("maps", {})
    qa = report.get("qa6")
    if (report.get("region") != "HOENN"
            or report.get("kind") != "ISOLATED_HOENN_TEST"
            or report.get("save_profile") not in ("Hoenn QA Fase06", "Hoenn QA Fase07", "Hoenn QA Fase08", "Hoenn QA Fase09", "Hoenn QA Fase10", "Hoenn QA Fase11")
            or not isinstance(ids, dict) or len(ids) != 199):
        raise ValueError("QA06 exige a cópia isolada com 199 mapas e perfil próprio")
    if (not isinstance(qa, dict)
            or qa.get("native_game_exe_tested") is not False
            or qa.get("native_weather_visuals_verified") is not False
            or qa.get("native_rayquaza_cinematic_verified") is not False
            or qa.get("donor_scripts_executed") is not False
            or qa.get("map_local_story_guards") is not True):
        raise ValueError("Manifesto QA06 ausente, incoerente ou com aceite nativo indevido")
    all_ids = set(CAVE_MAPS + PILLAR_MAPS + (83, 236))
    if any(str(mid) not in ids for mid in all_ids):
        raise ValueError("Manifesto sem Cave of Origin, Sootopolis ou Sky Pillar")
    actual = {}
    for mid, *_ in CLIMATE_EVENTS:
        mapped = ids[str(mid)]
        if not isinstance(mapped, int) or not 700 <= mapped <= 999:
            raise ValueError(f"MapID inválido para {mid}")
        actual[mid] = loads((copy / f"Data/Map{mapped:03}.rxdata").read_bytes())
    verified = verify_story_events(actual)
    if any(qa.get(key) != value for key, value in verified.items()):
        raise ValueError("Eventos físicos de clima divergem do manifesto QA06")
    ruby_path = copy / "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb"
    ruby_source = ruby_path.read_text("utf-8")
    if any(guard not in ruby_source for guard in RUBY_GUARDS):
        raise ValueError("Código Ruby de QA06 não está instalado na cópia")
    return {
        "schema": 1,
        "region": "HOENN",
        "qa_phase": "06/12",
        "status": "CLIMATE_STORY_STATICALLY_VERIFIED",
        **verified,
        "source_scripts_executed": False,
        "native_game_exe_approved": False,
        "native_weather_visuals_verified": False,
        "native_rayquaza_cinematic_verified": False,
        "native_sky_pillar_puzzles_verified": False,
        "regional_save_isolated": True,
    }


def main(argv: list[str] | None = None) -> int:
    from hoenn_qa_phase1 import WORK, require_private_path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", type=Path, default=WORK / "hoenn-qa-fase06")
    parser.add_argument("--report", type=Path, default=WORK / "hoenn-qa-fase06-report.json")
    args = parser.parse_args(argv)
    target = None
    try:
        target = require_private_path(args.report)
        result = verify_copy(args.copy)
        status = 0
    except (OSError, ValueError, KeyError, IndexError, TypeError,
            json.JSONDecodeError) as exc:
        result = {
            "schema": 1, "region": "HOENN", "qa_phase": "06/12",
            "status": "BLOCKED", "native_game_exe_approved": False,
            "errors": [str(exc)],
        }
        status = 2
    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
