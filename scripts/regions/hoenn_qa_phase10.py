#!/usr/bin/env python3
"""Hoenn QA10: Hall of Fame and circuit unlock, STATIC private-copy audit.

The original Hall event is reauthored in Blue; donor scripts/dialogue are
never copied or executed. Green RXDATA/Ruby checks are not Game.exe acceptance,
credits, actual travel, rematch AI or multi-region save compatibility.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from server.ruby_marshal import RubyObject, loads
from hoenn_qa_phase5 import required_event
from hoenn_qa_phase9 import LEAGUE_EXIT, HOF_ENTRY, verify_league_events

FINAL_MAPS = (93, 98, 99, 322)
LEAGUE_NEIGHBORS = ("JOHTO", "SINNOH")
LEGACY_REGIONS = ("DECADES", "KANTO", "JOHTO", "SINNOH")
HALL_EVENT = HOF_ENTRY
LEAGUE_GATE_SIGN = (322, 23, 16, "HN10_Sign_LEAGUE_GATE",
                    "BlueHoennPilot.sign_stage10(:LEAGUE_GATE)", 0)
RUBY_REQUIREMENTS = (
    "def self.qa10_hall_ready?",
    "def self.qa10_postgame_status",
    "def self.hall_of_fame_stage10",
    "qa9_at_league_map?(99)",
    'flags["champion_wallace_defeated"]',
    "qa9_champion_unlocked?",
    'region["leagues"].is_a?(Array)',
    'region["leagues"].include?("HOENN")',
    'BlueRegions.complete_league(region,"HOENN")',
    'flags["hoenn_hall_of_fame"]=true',
    'neighbors.sort==%w[JOHTO SINNOH]',
)
CORE_REQUIREMENTS = (
    "def self.neighbors(region)",
    "def self.unlocked(state)",
    "def self.complete_league(state, region)",
    'state["leagues"] << region',
)
NATIVE_UNVERIFIED = (
    "native_game_exe_tested",
    "native_hall_animation_verified",
    "native_hall_credits_verified",
    "native_postgame_warps_verified",
    "native_region_travel_verified",
    "native_johto_sinnoh_installed_verified",
    "native_rematch_verified",
    "native_save_roundtrip_verified",
    "native_story_approved",
)


def verify_final_events(maps: dict[int, RubyObject]) -> dict:
    missing = sorted(set(FINAL_MAPS) - set(maps))
    if missing:
        raise ValueError(f"QA10: mapas finais de Hoenn ausentes: {missing}")
    for mid, x, y, name, script, trigger in (
        LEAGUE_EXIT, HALL_EVENT, LEAGUE_GATE_SIGN
    ):
        required_event(maps[mid], mid, x, y, name, script, trigger)
    if LEAGUE_EXIT[0] != 98 or HALL_EVENT[:3] != (99, 9, 18):
        raise ValueError("QA10: âncoras finais doadas foram alteradas")
    return {
        "final_source_map_ids": list(FINAL_MAPS),
        "champion_exit_anchor": list(LEAGUE_EXIT[:3]),
        "hall_of_fame_anchor": list(HALL_EVENT[:3]),
        "postgame_league_sign_anchor": list(LEAGUE_GATE_SIGN[:3]),
        "expected_neighbor_unlocks": list(LEAGUE_NEIGHBORS),
        "previously_completed_hoenn_leagues_not_duplicated": True,
        "complete_league_only_after_hall_event": True,
    }


def audit_generated(maps: dict[int, RubyObject]) -> dict:
    return {
        **verify_final_events(maps),
        "completion_requires_all_8_local_badges": True,
        "completion_requires_wally_and_elite_four": True,
        "completion_requires_wallace_victory": True,
        "completion_requires_original_hall_map": True,
        "regional_save_only": True,
        "circuit_unlock_not_immediate_travel": True,
        "preserves_original_decades_badges_and_switches": True,
        "hall_event_codes_owned_by_blue": True,
        "donor_event_scripts_copied": False,
        **{key: False for key in NATIVE_UNVERIFIED},
    }


def verify_copy(copy: Path) -> dict:
    from hoenn_qa_phase1 import require_private_path

    copy = require_private_path(copy)
    report = json.loads((copy / "Hoenn pilot.json").read_text("utf-8"))
    ids, qa10 = report.get("maps"), report.get("qa10")
    if (report.get("region") != "HOENN"
        or report.get("kind") != "ISOLATED_HOENN_TEST"
        or report.get("save_profile") not in ("Hoenn QA Fase10", "Hoenn QA Fase11")
        or not isinstance(ids, dict) or len(ids) != 199
        or not isinstance(qa10, dict) or not isinstance(report.get("qa9"), dict)):
        raise ValueError("QA10 exige cópia privada, 199 mapas, QA09 e perfil Fase10")
    if qa10.get("donor_event_scripts_copied") is not False:
        raise ValueError("QA10 proibiu importar scripts do doador")
    if any(qa10.get(key) is not False for key in NATIVE_UNVERIFIED):
        raise ValueError("QA10 não pode reivindicar conclusão jogável de Game.exe")
    mapped = {}
    for mid in FINAL_MAPS:
        native = ids.get(str(mid))
        if type(native) is not int or not 700 <= native <= 999:
            raise ValueError(f"QA10: MapID remapeado inválido em {mid}")
        mapped[mid] = native
    if len(set(mapped.values())) != len(mapped):
        raise ValueError("QA10: MapIDs de fim de campanha duplicados")
    maps = {mid: loads((copy / f"Data/Map{native:03}.rxdata").read_bytes())
            for mid, native in mapped.items()}
    verified = audit_generated(maps)
    if qa10 != verified:
        raise ValueError("QA10: eventos físicos e manifesto do Hall divergentes")
    ruby = (copy / "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb").read_text("utf-8")
    missing = [token for token in RUBY_REQUIREMENTS if token not in ruby]
    if missing:
        raise ValueError(f"QA10: gates de conclusão Hoenn ausentes: {missing}")
    core = copy / "Plugins/ZZZZ Blue Story and Presentation/Regions.rb"
    if not core.is_file() or core.is_symlink():
        raise ValueError("QA10: módulo BlueRegions autoral não está instalado na cópia")
    core_script = core.read_text("utf-8")
    missing_core = [token for token in CORE_REQUIREMENTS if token not in core_script]
    if missing_core:
        raise ValueError(f"QA10: circuito BlueRegions instalado não oferece conclusão de Liga: {missing_core}")
    return {
        "schema": 1,
        "region": "HOENN",
        "qa_phase": "10/12",
        "status": "HALL_OF_FAME_CIRCUIT_STATICALLY_VERIFIED",
        **verified,
        "private_save_isolated": True,
        "native_game_exe_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    from hoenn_qa_phase1 import WORK, require_private_path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", type=Path, default=WORK / "hoenn-qa-fase10")
    parser.add_argument("--report", type=Path, default=WORK / "hoenn-qa-fase10-report.json")
    args = parser.parse_args(argv)
    path = None
    try:
        path = require_private_path(args.report)
        outcome = verify_copy(args.copy)
        status = 0
    except (OSError, TypeError, ValueError, KeyError, IndexError,
            json.JSONDecodeError) as error:
        status = 2
        outcome = {
            "schema": 1,
            "region": "HOENN",
            "qa_phase": "10/12",
            "status": "BLOCKED",
            "native_game_exe_approved": False,
            "errors": [str(error)],
        }
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(outcome, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
