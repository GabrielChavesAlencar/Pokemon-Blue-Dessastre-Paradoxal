#!/usr/bin/env python3
"""Hoenn QA09 — Elite Four and Champion Wallace in a PRIVATE Blue test copy.

The source's MapIDs, author-owned event scripts and reference PBS parties are
audited statically. There is NO execution of a donor script, gameplay in
Game.exe or confirmation of visual battles, scaling, rewards or League flow.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from server.ruby_marshal import RubyObject, loads
from hoenn_qa_phase5 import required_event
from hoenn_stage10 import (
    ELITE_EVENTS, ELITE_PBS, ELITE_TEAMS,
    CHAMPION_EVENT, CHAMPION_PBS, CHAMPION_TEAM,
    LEAGUE_EXIT_EVENT,
)

# Original donor IDs (not remapped Blue IDs): lobby, corridors, 4 rooms,
# champion, Hall of Fame. Native collision/door direction remains unverified.
LEAGUE_MAPS = tuple(range(93, 101))
ELITE_NAMES = ("Sidney", "Phoebe", "Glacia", "Drake")
ELITE_FLAGS = tuple(f"elite_{name.lower()}_defeated" for name in ELITE_NAMES)
LEAGUE_BOSS_EVENTS = (
    (94, *ELITE_EVENTS[0][1:], "HN10_Boss_Sidney", "BlueHoennPilot.elite_four(0)", 0),
    (95, *ELITE_EVENTS[1][1:], "HN10_Boss_Phoebe", "BlueHoennPilot.elite_four(1)", 0),
    (96, *ELITE_EVENTS[2][1:], "HN10_Boss_Glacia", "BlueHoennPilot.elite_four(2)", 0),
    (97, *ELITE_EVENTS[3][1:], "HN10_Boss_Drake", "BlueHoennPilot.elite_four(3)", 0),
    (98, *CHAMPION_EVENT[1:], "HN10_Boss_Wallace", "BlueHoennPilot.champion_wallace", 0),
)
LEAGUE_EXIT = (*LEAGUE_EXIT_EVENT, "HN10_Story_ChampionExit",
               "BlueHoennPilot.stage10_transfer(98,99,9,18)", 1)
HOF_ENTRY = (99, 9, 18, "HN10_Story_HallOfFame",
             "BlueHoennPilot.hall_of_fame_stage10", 1)
NATIVE_UNVERIFIED = (
    "native_game_exe_tested",
    "native_elite_battles_verified",
    "native_champion_battle_verified",
    "native_dynamic_balance_verified",
    "native_league_warps_verified",
    "native_league_ui_verified",
    "native_hall_of_fame_verified",
    "native_story_approved",
)
RUBY_GUARDS = (
    "def self.qa9_at_league_map?(source_id)",
    "def self.qa9_elite_unlocked?(index)",
    "def self.qa9_champion_unlocked?",
    "return false unless qa9_at_league_map?(94 + index)",
    "return false unless qa9_at_league_map?(98) && qa9_champion_unlocked?",
    "qa9_elite_unlocked?(dest_id-94)",
    "dest_id==98 && !qa9_champion_unlocked?",
    "qa8_league_badges?",
    'flags["wally_road_defeated"]',
)


def headers_and_teams() -> tuple[tuple[str, tuple[tuple[str, int], ...]], ...]:
    if (len(ELITE_EVENTS) != 4 or len(ELITE_PBS) != 4 or
            len(ELITE_TEAMS) != 4 or len(CHAMPION_TEAM) != 6):
        raise ValueError("QA09: Elite Four ou equipe de Wallace incompleta")
    if tuple(x[1] for x in ELITE_PBS) != ELITE_NAMES:
        raise ValueError("QA09: ordem/nome da Elite Four divergente")
    if len({(k, n, v) for k, n, v in (*ELITE_PBS, CHAMPION_PBS)}) != 5:
        raise ValueError("QA09: identidade PBS dos cinco chefes repetida")
    if any(len(team) != 5 for team in ELITE_TEAMS):
        raise ValueError("QA09: time da Elite Four deveria conter cinco Pokémon")
    if CHAMPION_PBS != ("BLUE_HOENN_CHAMPION", "Wallace", 1098):
        raise ValueError("QA09: Wallace campeão não é a equipe referência")
    return tuple(
        (f"[{kind},{name},{version}]", team)
        for (kind, name, version), team
        in zip((*ELITE_PBS, CHAMPION_PBS), (*ELITE_TEAMS, CHAMPION_TEAM))
    )


def verify_league_events(maps: dict[int, RubyObject]) -> dict:
    missing = sorted(set(LEAGUE_MAPS) - set(maps))
    if missing:
        raise ValueError(f"QA09: faltam mapas originais da Liga: {missing}")
    headers = headers_and_teams()
    for mid, x, y, name, handler, trigger in (
        *LEAGUE_BOSS_EVENTS, LEAGUE_EXIT, HOF_ENTRY
    ):
        required_event(maps[mid], mid, x, y, name, handler, trigger)
    return {
        "league_source_map_ids": list(LEAGUE_MAPS),
        "verified_league_boss_events": len(LEAGUE_BOSS_EVENTS),
        "verified_champion_exit_and_hall_entry": 2,
        "elite_four_order": list(ELITE_NAMES),
        "ordered_elite_flag_keys": list(ELITE_FLAGS),
        "champion_flag_key": "champion_wallace_defeated",
        "pbs_headers": [header for header, _ in headers],
        "pbs_reference_party_sizes": [len(team) for _, team in headers],
        "elite_battle_source_map_ids": [e[0] for e in LEAGUE_BOSS_EVENTS[:4]],
        "champion_source_map_id": CHAMPION_EVENT[0],
    }


def verify_league_pbs(contents: str) -> None:
    """Require ONE canonical party per leader; never assume fixed gameplay levels."""
    for header, expected in headers_and_teams():
        matches = list(re.finditer(
            r"(?m)^" + re.escape(header) + r"\s*$", contents
        ))
        if len(matches) != 1:
            raise ValueError(f"QA09: treinador PBS ausente/duplicado: {header}")
        tail = contents[matches[0].end():]
        following = re.search(r"(?m)^\[[^\r\n]+\]", tail)
        body = tail[:following.start()] if following else tail
        observed = re.findall(
            r"(?m)^Pokemon\s*=\s*([A-Z0-9_]+)\s*,\s*(\d+)\s*$", body
        )
        canonical = [(species, str(level)) for species, level in expected]
        if observed != canonical:
            raise ValueError(f"QA09: equipe PBS divergente para {header}")


def audit_generated(maps: dict[int, RubyObject]) -> dict:
    return {
        **verify_league_events(maps),
        "eight_regional_badges_and_wally_required": True,
        "all_previous_elite_victories_required": True,
        "map_local_boss_event_guards": True,
        "defeat_does_not_advance_league": True,
        "champion_requires_four_complete_victories": True,
        "battle_engine_owned_by_blue_decades": True,
        "pbs_levels_are_references_not_fixed": True,
        "source_event_scripts_reused": False,
        **{key: False for key in NATIVE_UNVERIFIED},
    }


def verify_copy(copy: Path) -> dict:
    from hoenn_qa_phase1 import require_private_path
    copy = require_private_path(copy)
    report = json.loads((copy / "Hoenn pilot.json").read_text("utf-8"))
    ids = report.get("maps")
    qa = report.get("qa9")
    if (report.get("region") != "HOENN"
        or report.get("kind") != "ISOLATED_HOENN_TEST"
        or report.get("save_profile") not in ("Hoenn QA Fase09", "Hoenn QA Fase10", "Hoenn QA Fase11", "Hoenn QA Fase12")
        or not isinstance(ids, dict) or len(ids) != 199
        or not isinstance(qa, dict)):
        raise ValueError("QA09: exige 199 mapas e save privado Hoenn QA Fase09")
    if any(qa.get(key) is not False for key in NATIVE_UNVERIFIED):
        raise ValueError("QA09: relatório não pode alegar aprovação nativa")
    if qa.get("source_event_scripts_reused") is not False:
        raise ValueError("QA09: scripts do projeto de origem não podem ser reutilizados")
    remap = {}
    for mid in LEAGUE_MAPS:
        dest = ids.get(str(mid))
        if type(dest) is not int or not 700 <= dest <= 999:
            raise ValueError(f"QA09: MapID remapeado inválido: {mid}")
        remap[mid] = dest
    if len(set(remap.values())) != len(remap):
        raise ValueError("QA09: dois mapas da Liga compartilham ID Blue")
    maps = {mid: loads((copy / f"Data/Map{dest:03}.rxdata").read_bytes())
            for mid, dest in remap.items()}
    expected = audit_generated(maps)
    if qa != expected:
        raise ValueError("QA09: RXDATA/manifesto da Liga divergentes")
    trainers = (copy / "PBS/trainers_hoenn_pilot.txt").read_text("utf-8-sig")
    verify_league_pbs(trainers)
    ruby_source = (copy / "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb").read_text("utf-8")
    missing = [guard for guard in RUBY_GUARDS if guard not in ruby_source]
    if missing:
        raise ValueError(f"QA09: guardas Ruby da Liga não instaladas: {missing}")
    return {
        "schema": 1,
        "region": "HOENN",
        "qa_phase": "09/12",
        "status": "LEAGUE_ELITE_CHAMPION_STATICALLY_VERIFIED",
        **expected,
        "regional_save_isolated": True,
        "native_game_exe_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    from hoenn_qa_phase1 import WORK, require_private_path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", type=Path, default=WORK / "hoenn-qa-fase09")
    parser.add_argument("--report", type=Path, default=WORK / "hoenn-qa-fase09-report.json")
    args = parser.parse_args(argv)
    target = None
    try:
        target = require_private_path(args.report)
        result = verify_copy(args.copy)
        status = 0
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            json.JSONDecodeError) as error:
        result = {
            "schema": 1,
            "region": "HOENN",
            "qa_phase": "09/12",
            "status": "BLOCKED",
            "native_game_exe_approved": False,
            "errors": [str(error)],
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
