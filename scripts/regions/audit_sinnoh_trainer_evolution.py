#!/usr/bin/env python3
"""CH12: read-only check of Sinnoh trainer/evolution contract against Blue runtime.

The save has no numeric regional level cap.  Keep that fact explicit:
trainer levels are derived from the highest non-egg party level, and the
separate 350/450/540 BST gates are NOT level caps.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / "data/regions/sinnoh-trainer-evolution-contract.json"
CAMPAIGN = ROOT / "scripts/battle_polish/Campaign.rb"
EVOLUTION = ROOT / "scripts/battle_polish/EvolutionScaling.rb"
STORY = ROOT / "scripts/battle_polish/Story.rb"
REGISTRY = ROOT / "site/public/data/regions.json"

FAMILIES = (
    ("LEVEL", ("TURTWIG", "GROTLE", "TORTERRA"), (23, 37)),
    ("LEVEL", ("CHIMCHAR", "MONFERNO", "INFERNAPE"), (19, 41)),
    ("LEVEL", ("PIPLUP", "PRINPLUP", "EMPOLEON"), (21, 41)),
    ("STONE", ("ROSELIA", "ROSERADE"), (30,)),
    ("TRADE", ("GRAVELER", "GOLEM"), (40,)),
    ("FRIENDSHIP", ("RIOLU", "LUCARIO"), (45,)),
)
SOURCES = {
    "trainer_level": "scripts/battle_polish/Campaign.rb",
    "story_stage_and_bst": "scripts/battle_polish/Story.rb",
    "evolution": "scripts/battle_polish/EvolutionScaling.rb",
    "badges": "site/public/data/regions.json",
}


def fail(message: str):
    raise ValueError("SINNOH_CH12_BLOQUEADO: " + message)


def read(path: Path) -> str:
    if path.is_symlink() or not path.is_file():
        fail("Arquivo ausente ou symlink: " + str(path))
    return path.read_text(encoding="utf-8")


def require(code: str, snippets: tuple[str, ...], label: str):
    for snippet in snippets:
        if snippet not in code:
            fail(label + " perdeu a regra compartilhada: " + snippet)


def audit(contract: dict, campaign: str, evolution: str,
          story: str, registry: dict) -> dict:
    if not isinstance(contract, dict):
        fail("Contrato deve ser JSON objeto")
    expected_keys = {
        "schema", "region", "status", "source_of_truth",
        "gameplay_verified", "native_trainers_installed", "can_install",
        "level_cap", "balance", "evolution", "trainer_examples", "notes",
    }
    if set(contract) != expected_keys:
        fail("Campos de contrato ausentes ou desconhecidos")
    if (type(contract["schema"]) is not int or contract["schema"] != 1 or
            contract["region"] != "SINNOH" or
            contract["status"] != "PLANNED_CONTRACT_NOT_INSTALLED" or
            contract["source_of_truth"] != SOURCES or
            any(contract[key] is not False for key in (
                "gameplay_verified", "native_trainers_installed",
                "can_install"))):
        fail("Contrato falso, instalado ou com fonte de regras incorreta")
    cap = contract["level_cap"]
    cap_expected = {
        "regional_numeric_cap_in_save": None,
        "regional_badge_to_level_cap_implemented": False,
        "reference": "highest_non_egg_party_level",
        "maximum": "GameData::GrowthRate.max_level",
        "minimum": 1,
        "bst_stage_caps": [350, 450, 540, None],
        "bst_cap_is_not_a_level_cap": True,
    }
    if cap != cap_expected:
        fail("Level cap numérico ou teto BST inventado/adulterado")
    balance_expected = {
        "normal_percent": 70,
        "master_percent": 90,
        "rounding": "integer_floor",
        "master_trigger": "BlueStory.stage == 3",
        "master_team_target": 4,
        "max_opponent_pokemon": 6,
        "evolution_after_scaling": True,
        "regular_trainers_auto_evolve": True,
        "authored_boss_species_preserved": True,
        "trainer_pbs_never_mutated": True,
    }
    if contract["balance"] != balance_expected:
        fail("Balanceamento Normal/Master ou limites de equipe adulterados")
    evolution_expected = {
        "native_source": "GameData::Species#get_evolutions(true)",
        "level_required_plus_grace": 5, "stone_level": 30,
        "trade_level": 40, "friendship_level": 45,
        "unsupported_conditions_blocked": True,
        "ambiguous_branch_blocked": True, "special_forms_blocked": True,
        "conditions_by_gender_and_time_respected": True,
    }
    if contract["evolution"] != evolution_expected:
        fail("Regra de evolução nativa adulterada ou condições inventadas")
    examples = contract["trainer_examples"]
    if not isinstance(examples, list) or len(examples) != len(FAMILIES):
        fail("Exemplos sintéticos de evolução de Sinnoh incompletos")
    for row, (method, family, thresholds) in zip(examples, FAMILIES):
        if (not isinstance(row, dict) or
                set(row) != {"family", "method", "thresholds",
                             "synthetic_fixture_only"} or
                row["family"] != list(family) or row["method"] != method or
                row["thresholds"] != list(thresholds) or
                row["synthetic_fixture_only"] is not True or
                any(type(threshold) is not int for threshold in
                    row["thresholds"])):
            fail("Família de Sinnoh, limiar ou status de fixture adulterado")
    if not isinstance(contract["notes"], str) or len(contract["notes"]) < 70:
        fail("Aviso sobre level cap/jogabilidade insuficiente")
    if (not isinstance(registry, dict) or
            not isinstance(registry.get("regions"), dict) or
            registry["regions"].get("SINNOH", {}).get("status") != "planned"):
        fail("Região Sinnoh não está registrada como planned")
    if len(registry["regions"]["SINNOH"].get("milestones", [])) != 8:
        fail("Sinnoh não possui as oito conquistas de origem")
    require(campaign, (
        "master? ? 90 : 70",
        "highest=party.reject(&:egg?).map(&:level).max || 1",
        "[[highest*percent/100,1].max,GameData::GrowthRate.max_level].min",
        "level=BlueCampaign.trainer_level(Array(args[4]).first)",
        "pkmn=Marshal.load(Marshal.dump(original));pkmn.level=level",
        "BlueEvolutionScaling.upgrade_trainer!(pkmn)",
        "!BlueCampaign.boss?(trainer)",
        "slots=[6-trainers.sum",
        "trainer.party.length.between?(1,3)",
    ), "Campaign.rb")
    require(story, (
        "BlueRegions.crystal_total(state, badges)",
        "def self.cap;[350,450,540,nil][stage];end",
        "badges >= 11 ? 3",
        "BlueEvolutionScaling.legitimate_trainer_form?(p)",
        "BlueStory.regional_first_boss?(args[4])",
    ), "Story.rb")
    require(evolution, (
        "TRAINER_GRACE = 5", "STONE_LEVEL = 30", "TRADE_LEVEL = 40",
        "FRIENDSHIP_LEVEL = 45",
        "source.get_evolutions(true)",
        "return [] unless targets.length == 1",
        "level = parameter + TRAINER_GRACE",
        "return nil unless parameter.is_a?(Integer) && parameter > 0",
        "return nil unless pokemon && pokemon.respond_to?(:male?) && pokemon.male?",
        "return nil unless defined?(PBDayNight) && PBDayNight.isDay?",
        "return pokemon unless pokemon && !pokemon.egg? && !pokemon.shadowPokemon?",
        "return pokemon unless active?",
        "return [] if special?(source)",
        "pokemon.species = evolved",
        "GameData::GrowthRate.max_level",
    ), "EvolutionScaling.rb")
    # These strings are not proof of compiled GameData. They are a guard
    # against accidental changed constants; the paired Ruby test executes
    # the real runtime and checks outcomes, rather than reimplementing it.
    return {
        "schema": 1, "region": "SINNOH",
        "status": "DECLARATIVE_GUARDS_PASS_NOT_PLAYABLE",
        "normal_percent": 70, "master_percent": 90,
        "evolution_methods_checked": 4, "synthetic_families": len(examples),
        "regional_badge_level_cap_defined": False,
        "gameplay_verified": False, "can_install": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, default=CONTRACT)
    parser.add_argument("--campaign", type=Path, default=CAMPAIGN)
    parser.add_argument("--evolution", type=Path, default=EVOLUTION)
    parser.add_argument("--story", type=Path, default=STORY)
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    args = parser.parse_args()
    try:
        result = audit(json.loads(read(args.contract)),
                       read(args.campaign), read(args.evolution),
                       read(args.story), json.loads(read(args.registry)))
    except (OSError, ValueError, TypeError, KeyError) as e:
        print(str(e), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
