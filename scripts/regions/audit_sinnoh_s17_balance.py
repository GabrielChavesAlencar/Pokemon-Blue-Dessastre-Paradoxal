#!/usr/bin/env python3
"""S17: static contract gate for REAL shared trainer-scaling Ruby regressions.

The battle behavior is exercised separately by CH19's Ruby fixture. This
Python gate prevents historical Platinum teams, invented fixed levels or
fixture results from being presented as installed native Sinnoh gameplay.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/regions/sinnoh-trainer-balance-s17.json"
CH12 = ROOT / "data/regions/sinnoh-trainer-evolution-contract.json"
CH15 = ROOT / "data/regions/sinnoh-trainer-teams-ch15.json"
RUBY = ROOT / "tests/sinnoh_s17_trainer_balance_runtime.rb"
REQUIRED_RULES = {
    "source_level": "highest_non_egg_party_level",
    "normal_percent": 70,
    "master_percent": 90,
    "rounding": "integer_floor",
    "master_requires_stage": 3,
    "master_team_target": 4,
    "max_opponents_per_side": 6,
    "apply_after_cloning_original_trainer": True,
    "natural_evolution_after_scaling": True,
    "preserve_authored_boss_species": True,
    "preserve_native_pbs_input": True,
    "no_fake_numeric_level_cap": True,
    "no_fixed_trainer_levels_published": True,
}
MUST_BE_FALSE = (
    "native_trainer_pbs_verified", "native_trainer_events_verified",
    "native_maps_installed", "game_exe_executed", "joiplay_executed",
    "gameplay_verified", "can_install",
)
EMPTY_NATIVE = ("real_trainer_levels", "real_trainer_teams", "physical_map_ids")
FIXTURE_KEYS = {
    "normal_70_percent", "master_90_percent",
    "egg_excluded_from_highest_party_level",
    "normal_multi_trainer_no_team_growth",
    "master_team_1_to_3_expands_to_4",
    "master_team_4_to_6_preserved",
    "double_battle_total_no_more_than_6",
    "first_leader_elite_champion_preserved_rivals_obey_bst",
    "evolution_thresholds_after_level_scaling",
    "original_trainer_pbs_and_player_party_unchanged",
    "level_min_and_engine_max",
    "battle_mode_does_not_scale",
    "no_cross_region_campaign_regression",
}


def fail(reason: str) -> None:
    raise ValueError("SINNOH_S17_BLOCKED: " + reason)


def audit(contract: dict, ch12: dict, ch15: dict, *, ruby_source: str) -> dict:
    if (type(contract) is not dict
            or contract.get("schema") != 1
            or contract.get("region") != "SINNOH"
            or contract.get("stage") != "S17"
            or contract.get("status") !=
            "SHARED_TRAINER_BALANCE_VERIFIED_IN_OFFLINE_FIXTURES_ONLY"):
        fail("contrato S17 adulterado ou nao Sinnoh")
    if any(contract.get(key) is not False for key in MUST_BE_FALSE):
        fail("certificacao de treinador/Mapa/Game.exe nativo nao existente")
    if any(contract.get(key) != [] for key in EMPTY_NATIVE):
        fail("times, niveis ou MapIDs jogaveis inventados")
    rules = contract.get("rules")
    if type(rules) is not dict or rules != REQUIRED_RULES:
        fail("regra dinamica 70/90, cap, clones ou Master divergente")
    records = contract.get("verified_in_offline_fixtures")
    if (type(records) is not list or set(records) != FIXTURE_KEYS
            or len(records) != len(FIXTURE_KEYS)):
        fail("cobertura de testes S17 incompleta ou duplicada")
    refs = contract.get("references")
    if (type(refs) is not dict or refs != {
        "campaign": "scripts/battle_polish/Campaign.rb",
        "story": "scripts/battle_polish/Story.rb",
        "evolution": "scripts/battle_polish/EvolutionScaling.rb",
        "base_contract": "data/regions/sinnoh-trainer-evolution-contract.json",
        "native_team_catalog": "data/regions/sinnoh-trainer-teams-ch15.json",
        "runtime_fixture": "tests/sinnoh_s17_trainer_balance_runtime.rb",
    }):
        fail("fonte real da politica ou fixture alterada")
    if (type(ch12) is not dict or ch12.get("region") != "SINNOH"
            or ch12.get("native_trainers_installed") is not False
            or ch12.get("gameplay_verified") is not False
            or ch12.get("can_install") is not False):
        fail("CH12 falsamente instalado ou inconsistente")
    base = ch12.get("balance", {})
    for key, value in (
        ("normal_percent", 70), ("master_percent", 90),
        ("master_team_target", 4), ("max_opponent_pokemon", 6),
        ("evolution_after_scaling", True),
        ("authored_boss_species_preserved", True),
        ("trainer_pbs_never_mutated", True),
    ):
        if base.get(key) != value:
            fail("CH12 divergente: " + key)
    level_cap = ch12.get("level_cap", {})
    if (level_cap.get("regional_numeric_cap_in_save") is not None
            or level_cap.get("bst_cap_is_not_a_level_cap") is not True):
        fail("CH12 inventa nivel fixo por insignia")
    if (type(ch15) is not dict or ch15.get("region") != "SINNOH"
            or ch15.get("native_source_available_in_repository") is not False
            or ch15.get("native_pbs_compilation_verified") is not False
            or ch15.get("native_event_battle_bindings_verified") is not False
            or ch15.get("gameplay_verified") is not False
            or ch15.get("can_install") is not False
            or ch15.get("may_write_pbs") is not False):
        fail("CH15 catalogo historico apresentado como PBS jogavel")
    policy = ch15.get("dynamic_balance", {})
    if (policy.get("normal_percent") != 70
            or policy.get("master_percent") != 90
            or policy.get("reference_level") != "highest_non_egg_party_level"
            or policy.get("boss_species_preserved") is not True):
        fail("CH15 contradiz politica do jogo")
    trainers = ch15.get("trainers")
    if (type(trainers) is not list or len(trainers) != 13
            or any(type(row) is not dict
                   or row.get("native_pbs", {}).get("compiled") is not False
                   or row.get("native_pbs", {}).get("event_bound") is not False
                   or row.get("native_pbs", {}).get("team") is not None
                   or row.get("first_battle", {}).get("verified_in_blue_pbs") is not False
                   for row in trainers)):
        fail("13 equipes historicas indevidamente promovidas a nativas")
    if (not isinstance(ruby_source, str)
            or "Battle.new(nil, nil, [], nil, trainers)" not in ruby_source
            or "SINNOH_S17_DYNAMIC_LEVELS_BOSSES_DOUBLE_MASTER_NO_MUTATION_OFFLINE_OK" not in ruby_source
            or "Marshal.dump(trainers)" not in ruby_source):
        fail("fixture de runtime real S17 ausente/incompleta")
    return {
        "schema": 1, "region": "SINNOH", "stage": "S17",
        "status": "STATIC_CONTRACT_VALIDATED_NATIVE_TRAINERS_PENDING",
        "ruby_runtime_required_in_ci": True,
        "fixture_scenarios": len(records),
        "reference_teams_only": len(trainers),
        "normal_percent": 70, "master_percent": 90,
        "master_team_target": 4, "max_opponents_per_side": 6,
        "fixed_runtime_levels": None,
        "native_trainers_installed": False,
        "trainer_event_bindings_verified": False,
        "game_exe_joiplay_executed": False,
        "gameplay_certified": False,
        "original_pbs_or_saves_modified": False,
    }


def main() -> int:
    try:
        documents = []
        for p in (CONTRACT, CH12, CH15):
            if p.is_symlink() or not p.is_file():
                fail("contrato ausente ou symlink: " + str(p))
            documents.append(json.loads(p.read_text("utf-8")))
        if RUBY.is_symlink() or not RUBY.is_file():
            fail("fixture Ruby S17 ausente")
        result = audit(*documents, ruby_source=RUBY.read_text("utf-8"))
    except (ValueError, OSError, TypeError, KeyError, UnicodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
