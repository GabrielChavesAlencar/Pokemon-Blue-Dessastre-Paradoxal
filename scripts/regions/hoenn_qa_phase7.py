#!/usr/bin/env python3
"""Hoenn QA07: audit all 8 regional gyms and 9 authored leader NPC events.

Static verification of a private 199-map Hoenn copy, not native Game.exe QA.
Only the public author code/metadata are shipped; no donor RXDATA or scripts.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from server.ruby_marshal import RubyObject, loads
from hoenn_qa_phase5 import required_event

# (original map id, x, y, event name, local badge, battle handler, PBS identity)
# Tate/Liza share one Double Battle identity but have two real NPC interactions.
GYM_EVENTS = (
    (27, 7, 4, "HN4_Leader_Roxanne", "STONE", "roxanne",
     ("BLUE_HOENN_ROXANNE", "Roxanne", 427)),
    (31, 6, 5, "HN5_NPC_31_6_5", "KNUCKLE", "brawly",
     ("BLUE_HOENN_BRAWLY", "Brawly", 531)),
    (47, 7, 4, "HN6_Leader_Wattson", "DYNAMO", "wattson",
     ("BLUE_HOENN_WATTSON", "Wattson", 647)),
    (63, 15, 15, "HN7_Boss_Flannery", "HEAT", "flannery",
     ("BLUE_HOENN_FLANNERY", "Flannery", 763)),
    (20, 6, 4, "HN8_Boss_Norman", "BALANCE", "norman",
     ("BLUE_HOENN_NORMAN", "Norman", 820)),
    (68, 17, 4, "HN8_Boss_Winona", "FEATHER", "winona",
     ("BLUE_HOENN_WINONA", "Winona", 868)),
    (82, 25, 11, "HN9_Boss_Tate", "MIND", "tate_liza",
     ("BLUE_HOENN_TATE_LIZA", "Tate & Liza", 982)),
    (82, 26, 11, "HN9_Boss_Liza", "MIND", "tate_liza",
     ("BLUE_HOENN_TATE_LIZA", "Tate & Liza", 982)),
    (87, 10, 4, "HN10_Boss_Juan", "RAIN", "juan",
     ("BLUE_HOENN_JUAN", "Juan", 1087)),
)
GYM_MAPS = tuple(dict.fromkeys(entry[0] for entry in GYM_EVENTS))
BADGES = tuple(dict.fromkeys(entry[4] for entry in GYM_EVENTS))
TRAINERS = tuple(dict.fromkeys(entry[6] for entry in GYM_EVENTS))
FIELD_UNLOCKS = {
    "STONE": "CUT", "KNUCKLE": "FLASH", "DYNAMO": "ROCKSMASH",
    "HEAT": "STRENGTH", "BALANCE": "SURF",
    "FEATHER": "FLY", "MIND": "DIVE", "RAIN": "WATERFALL",
}
TM_REWARD_KEYS = {
    "STONE": "roxanne_tm_given", "KNUCKLE": "brawly_tm_given",
    "DYNAMO": "wattson_tm_given", "HEAT": "flannery_tm_given",
    "BALANCE": "norman_tm_given", "FEATHER": "winona_tm_given",
    "MIND": "tate_liza_tm_given", "RAIN": "juan_tm_given",
}


def verify_gyms(maps: dict[int, RubyObject]) -> dict:
    if len(GYM_MAPS) != 8 or len(GYM_EVENTS) != 9 or len(BADGES) != 8 or len(TRAINERS) != 8:
        raise ValueError("QA07: catálogo precisa de oito ginásios e nove eventos (Tate e Liza)")
    if set(BADGES) != set(FIELD_UNLOCKS) or set(BADGES) != set(TM_REWARD_KEYS):
        raise ValueError("QA07: badge local sem recompensa ou liberação correspondente")
    for mid, x, y, event_name, badge, _handler, _trainer in GYM_EVENTS:
        if mid not in maps:
            raise ValueError(f"QA07: MapID original ausente: {mid}")
        required_event(maps[mid], mid, x, y, event_name,
                       f"BlueHoennPilot.qa7_gym_battle(:{badge})", 0)
    return {
        "verified_gym_event_bindings": len(GYM_EVENTS),
        "verified_distinct_gym_maps": len(GYM_MAPS),
        "gym_source_map_ids": list(GYM_MAPS),
        "regional_badges": list(BADGES),
        "leader_pbs_headers": [f"[{kind},{name},{version}]"
                               for kind, name, version in TRAINERS],
        "tm_reward_keys": dict(TM_REWARD_KEYS),
        "reference_field_unlocks": dict(FIELD_UNLOCKS),
    }


def audit_generated(maps: dict[int, RubyObject]) -> dict:
    return {
        **verify_gyms(maps),
        "battle_engine": "Blue/Decades TrainerBattle.start",
        "base_pbs_levels_not_fixed_gameplay_levels": True,
        "gym_trigger_map_guard": True,
        "tate_liza_double_battle": True,
        "source_scripts_copied": False,
        "native_game_exe_tested": False,
        "native_gym_puzzles_verified": False,
        "native_badges_in_trainer_card_verified": False,
        "native_battle_scaling_verified": False,
        "native_story_approved": False,
    }


def verify_copy(copy: Path) -> dict:
    from hoenn_qa_phase1 import require_private_path
    copy = require_private_path(copy)
    report = json.loads((copy / "Hoenn pilot.json").read_text("utf-8"))
    qa7 = report.get("qa7")
    mapping = report.get("maps")
    if (report.get("region") != "HOENN"
            or report.get("kind") != "ISOLATED_HOENN_TEST"
            or report.get("save_profile") not in ("Hoenn QA Fase07", "Hoenn QA Fase08")
            or not isinstance(mapping, dict) or len(mapping) != 199):
        raise ValueError("QA07 exige 199 mapas e perfil de save Hoenn QA Fase07")
    if not isinstance(qa7, dict) or qa7.get("gym_trigger_map_guard") is not True:
        raise ValueError("Manifesto de QA07 incompleto ou ausente")
    for key in ("source_scripts_copied", "native_game_exe_tested",
                "native_gym_puzzles_verified", "native_badges_in_trainer_card_verified",
                "native_battle_scaling_verified", "native_story_approved"):
        if qa7.get(key) is not False:
            raise ValueError(f"Manifesto QA07 afirma aprovação indevida: {key}")
    actual = {}
    for mid in GYM_MAPS:
        remapped = mapping.get(str(mid))
        if not isinstance(remapped, int) or not 700 <= remapped <= 999:
            raise ValueError(f"QA07: MapID remapeado inválido para ginásio {mid}")
        actual[mid] = loads((copy / f"Data/Map{remapped:03}.rxdata").read_bytes())
    verified = verify_gyms(actual)
    if any(qa7.get(key) != value for key, value in verified.items()):
        raise ValueError("QA07: RXDATA divergente do manifesto de ginásios")
    trainers = (copy / "PBS/trainers_hoenn_pilot.txt").read_text("utf-8-sig")
    missing = [header for header in verified["leader_pbs_headers"] if trainers.count(header) != 1]
    if missing:
        raise ValueError(f"QA07: equipes PBS ausentes ou duplicadas: {missing}")
    ruby_source = (copy / "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb").read_text("utf-8")
    for badge in BADGES:
        if f"{badge}: " not in ruby_source:
            raise ValueError(f"QA07: guarda Ruby de ginásio não inclui {badge}")
    if "def self.qa7_gym_battle(badge)" not in ruby_source or "send(config[1])" not in ruby_source:
        raise ValueError("QA07: dispatcher Ruby ausente na cópia")
    return {
        "schema": 1, "region": "HOENN", "qa_phase": "07/12",
        "status": "EIGHT_GYM_BINDINGS_STATICALLY_VERIFIED",
        **verified,
        "source_scripts_copied": False,
        "native_game_exe_approved": False,
        "native_gym_puzzles_verified": False,
        "native_badges_in_trainer_card_verified": False,
        "native_battle_scaling_verified": False,
        "regional_save_isolated": True,
    }


def main(argv: list[str] | None = None) -> int:
    from hoenn_qa_phase1 import WORK, require_private_path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", type=Path, default=WORK / "hoenn-qa-fase07")
    parser.add_argument("--report", type=Path, default=WORK / "hoenn-qa-fase07-report.json")
    args = parser.parse_args(argv)
    path = None
    try:
        path = require_private_path(args.report)
        report = verify_copy(args.copy)
        code = 0
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as exc:
        report = {"schema": 1, "region": "HOENN", "qa_phase": "07/12",
                  "status": "BLOCKED", "native_game_exe_approved": False,
                  "errors": [str(exc)]}
        code = 2
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
