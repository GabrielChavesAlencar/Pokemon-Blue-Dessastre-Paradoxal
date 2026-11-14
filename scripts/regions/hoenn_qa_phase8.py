#!/usr/bin/env python3
"""Hoenn QA08: Victory Road, Wally and League entry in the PRIVATE Blue copy.

This is a STATIC inspection of reauthored RXDATA/PBS and the QA04 obstacle
backlog, not proof of playable cave geometry, HM animations or Game.exe.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from server.ruby_marshal import RubyObject, loads
from hoenn_qa_phase5 import required_event
from hoenn_stage10 import (
    STAGE10_MAP_GRAPH_EDGES, WALLY_ROAD_PBS, WALLY_ROAD_TEAM,
    WALLY_VICTORY_ROAD_EVENT,
)

ROAD_MAPS = (250, 251, 252)
ACCESS_MAPS = (91, 92, 250, 251, 252, 322, 93)
WALLY_EVENT = (*WALLY_VICTORY_ROAD_EVENT, "HN10_Story_Wally",
               "BlueHoennPilot.wally_victory_road", 1)
LEAGUE_SIGN = (322, 23, 16, "HN10_Sign_LEAGUE_GATE",
               "BlueHoennPilot.sign_stage10(:LEAGUE_GATE)", 0)
EXPECTED_EDGES = ((91, 250), (250, 251), (251, 252),
                  (250, 322), (322, 93))
WALLY_HEADER = f"[{WALLY_ROAD_PBS[0]},{WALLY_ROAD_PBS[1]},{WALLY_ROAD_PBS[2]}]"
NATIVE_FALSE = (
    "native_game_exe_tested", "native_victory_road_traversal_verified",
    "native_strength_puzzles_verified", "native_rock_smash_verified",
    "native_waterfall_verified", "native_wally_battle_verified",
    "native_league_entry_verified", "native_accepted",
)


def verify_road_events(maps: dict[int, RubyObject]) -> dict:
    missing = sorted(set(ACCESS_MAPS) - maps.keys())
    if missing:
        raise ValueError(f"QA08: mapa de Victory Road/Ever Grande/Liga ausente: {missing}")
    for mid, x, y, name, handler, trigger in (WALLY_EVENT, LEAGUE_SIGN):
        required_event(maps[mid], mid, x, y, name, handler, trigger)
    edges = set(STAGE10_MAP_GRAPH_EDGES)
    if not set(EXPECTED_EDGES).issubset(edges):
        raise ValueError("QA08: inventário de adjacências original foi modificado")
    if len(ROAD_MAPS) != 3 or len(WALLY_ROAD_TEAM) != 5:
        raise ValueError("QA08: equipe de Wally ou três andares da caverna incompletos")
    return {
        "victory_road_source_map_ids": list(ROAD_MAPS),
        "ever_grande_and_league_source_map_ids": list(ACCESS_MAPS),
        "verified_wally_event": list(WALLY_EVENT[:3]),
        "verified_league_sign": list(LEAGUE_SIGN[:3]),
        "intended_map_adjacencies_unproven": [list(edge) for edge in EXPECTED_EDGES],
        "wally_trainer_header": WALLY_HEADER,
        "wally_reference_party": [list(entry) for entry in WALLY_ROAD_TEAM],
    }


def inventory_road_obstacles(qa4: dict) -> dict:
    """Distinguish authored safe rock events from original donor QA backlog."""
    new = qa4.get("new_safe_obstacles")
    review = qa4.get("source_obstacles_needing_review")
    candidates = qa4.get("source_obstacle_candidates")
    if not all(isinstance(row, list) for row in (new, review, candidates)):
        raise ValueError("QA08: manifesto QA04 de obstáculos incompleto")
    actual_new = [row for row in new if isinstance(row, list) and row and row[0] in ROAD_MAPS]
    actual_review = [row for row in review if isinstance(row, list) and row and row[0] in ROAD_MAPS]
    actual_candidates = [row for row in candidates if
                         isinstance(row, dict) and row.get("source_map_id") in ROAD_MAPS]
    if any(len(row) != 6 or row[3] not in ("strength", "rock_smash") or
           type(row[5]) is not int for row in actual_new):
        raise ValueError("QA08: evento de obstáculo instalado inconsistente")
    if any(len(row) < 5 for row in actual_review):
        raise ValueError("QA08: pendência de obstáculo inválida")
    if len(actual_new) + len(actual_review) < len(actual_candidates):
        raise ValueError("QA08: há obstáculos da fonte sem classificação")
    return {
        "source_road_obstacle_candidates": len(actual_candidates),
        "recreated_safe_rock_events": len(actual_new),
        "obstacle_candidates_for_manual_review": len(actual_review),
        "recreated_source_obstacle_positions": [row[:4] for row in actual_new],
        "manual_review_obstacle_positions": [row[:4] for row in actual_review],
        "source_event_scripts_reused": False,
    }


def verify_obstacle_events(maps: dict[int, RubyObject], qa4: dict) -> None:
    for row in qa4.get("new_safe_obstacles", []):
        if not isinstance(row, list) or len(row) != 6 or row[0] not in ROAD_MAPS:
            continue
        mid, x, y, kind, _sprite, event_id = row
        name = f"HN_QA4_{kind}_{mid}_{x}_{y}"
        handler = (f"BlueHoennPilot.strength_boulder({event_id})"
                   if kind == "strength" else
                   f"BlueHoennPilot.rock_smash_obstacle({event_id})")
        # Rock Smash has two pages; Strength has one. Inspect the precise
        # first page rather than using required_event (single-page contract).
        matches = [ev for ev in maps[mid].attrs["@events"].values()
                   if ev.attrs.get("@name") == name.encode()]
        if len(matches) != 1:
            raise ValueError(f"QA08: pedra autoral ausente/duplicada no mapa {mid}")
        ev = matches[0]
        if (ev.attrs.get("@id") != event_id or ev.attrs.get("@x") != x
                or ev.attrs.get("@y") != y):
            raise ValueError(f"QA08: pedra com coordenada/ID diferente no mapa {mid}")
        scripts = [
            str(v.decode("utf-8", "replace") if isinstance(v, bytes) else v)
            for cmd in ev.attrs["@pages"][0].attrs["@list"]
            if cmd.attrs.get("@code") in (355, 655)
            for v in cmd.attrs.get("@parameters", [])
        ]
        if handler not in scripts:
            raise ValueError(f"QA08: pedra sem handler Ruby autoral: {name}")


def verify_wally_pbs(text: str) -> None:
    matches = list(re.finditer(r"(?m)^" + re.escape(WALLY_HEADER) + r"\s*$", text))
    if len(matches) != 1:
        raise ValueError("QA08: equipe PBS do Wally ausente ou duplicada")
    tail = text[matches[0].end():]
    next_team = re.search(r"(?m)^\[[^\r\n]+\]", tail)
    team = tail[:next_team.start()] if next_team else tail
    members = re.findall(r"(?m)^Pokemon\s*=\s*([A-Z0-9_]+)\s*,\s*(\d+)\s*$", team)
    expected = [(species, str(level)) for species, level in WALLY_ROAD_TEAM]
    if members != expected:
        raise ValueError("QA08: equipe PBS de Victory Road não corresponde à referência verificada")


def audit_generated(maps: dict[int, RubyObject], qa4: dict) -> dict:
    summary = verify_road_events(maps)
    inventory = inventory_road_obstacles(qa4)
    return {
        **summary, **inventory,
        "wally_requires_eight_local_badges": True,
        "wally_battle_map_guard": True,
        "victory_road_exit_requires_wally": True,
        "south_entrance_requires_waterfall": True,
        "league_requires_wally_and_eight_badges": True,
        "defeat_does_not_complete_wally_flag": True,
        "native_game_exe_tested": False,
        "native_victory_road_traversal_verified": False,
        "native_strength_puzzles_verified": False,
        "native_rock_smash_verified": False,
        "native_waterfall_verified": False,
        "native_wally_battle_verified": False,
        "native_league_entry_verified": False,
        "native_accepted": False,
    }


def verify_copy(copy: Path) -> dict:
    from hoenn_qa_phase1 import require_private_path
    copy = require_private_path(copy)
    report = json.loads((copy / "Hoenn pilot.json").read_text("utf-8"))
    ids = report.get("maps")
    qa8 = report.get("qa8")
    if (report.get("region") != "HOENN"
            or report.get("kind") != "ISOLATED_HOENN_TEST"
            or report.get("save_profile") != "Hoenn QA Fase08"
            or not isinstance(ids, dict) or len(ids) != 199
            or not isinstance(qa8, dict)):
        raise ValueError("QA08: exige cópia privada isolada com 199 mapas e save Fase08")
    if any(qa8.get(key) is not False for key in NATIVE_FALSE):
        raise ValueError("QA08: manifesto não pode declarar teste nativo aprovado")
    if qa8.get("source_event_scripts_reused") is not False:
        raise ValueError("QA08: scripts de eventos do doador não são permitidos")
    remapped = {}
    for mid in ACCESS_MAPS:
        target = ids.get(str(mid))
        if type(target) is not int or not 700 <= target <= 999:
            raise ValueError(f"QA08: remapeamento inválido {mid}")
        remapped[mid] = target
    if len(set(remapped.values())) != len(remapped):
        raise ValueError("QA08: mapas de Victory Road colidem")
    actual = {mid: loads((copy / f"Data/Map{target:03}.rxdata").read_bytes())
              for mid, target in remapped.items()}
    qa4 = report.get("qa4")
    if not isinstance(qa4, dict):
        raise ValueError("QA08: auditoria QA04 ausente")
    verified = audit_generated(actual, qa4)
    if verified != qa8:
        raise ValueError("QA08: eventos físicos/pendências divergem do manifesto")
    verify_obstacle_events(actual, qa4)
    trainers = (copy / "PBS/trainers_hoenn_pilot.txt").read_text("utf-8-sig")
    verify_wally_pbs(trainers)
    ruby_source = (copy / "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb").read_text("utf-8")
    for guard in ("def self.qa8_league_badges?", "def self.wally_victory_road",
                  "$game_map.map_id == maps[250]",
                  "source_id==250 && dest_id==322",
                  "source_id==91 && [250,322].include?(dest_id)",
                  "QA8_LEAGUE_BADGES.all?"):
        if guard not in ruby_source:
            raise ValueError(f"QA08: proteção Ruby de Victory Road ausente: {guard}")
    return {
        "schema": 1, "region": "HOENN", "qa_phase": "08/12",
        "status": "VICTORY_ROAD_WALLY_STATICALLY_VERIFIED",
        **verified,
        "regional_save_isolated": True, "native_game_exe_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    from hoenn_qa_phase1 import WORK, require_private_path
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--copy", type=Path, default=WORK / "hoenn-qa-fase08")
    p.add_argument("--report", type=Path, default=WORK / "hoenn-qa-fase08-report.json")
    args = p.parse_args(argv)
    target = None
    try:
        target = require_private_path(args.report)
        result = verify_copy(args.copy)
        status = 0
    except (OSError, ValueError, TypeError, KeyError, IndexError,
            json.JSONDecodeError) as exc:
        result = {"schema": 1, "region": "HOENN", "qa_phase": "08/12",
                  "status": "BLOCKED", "native_game_exe_approved": False,
                  "errors": [str(exc)]}
        status = 2
    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
