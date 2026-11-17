#!/usr/bin/env python3
"""G08: reconcile Sinnoh opening, Barry's three PBS drafts, and Blue level policy.

GitHub-only. Run existing CH06/S13/S14/S17/G07 gates, then produce a strictly
NON-native QA matrix for fixture execution. Never create a ready marker,
MapIDs, sprites, levels, engine saves or files in the game directory.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from audit_sinnoh_g07_twinleaf_bindings import audit as audit_g07, FILES as G07_FILES
from audit_sinnoh_s13_intro import audit as audit_s13
from audit_sinnoh_s14_starters import audit as audit_s14
from audit_sinnoh_s17_balance import audit as audit_s17
from build_sinnoh_barry_pbs import MATCHUPS, RIVAL_TYPE, RIVAL_NAME, SEED_LEVEL, READY_MARKER

DATA_FILES={
    **G07_FILES,
    "s17":"data/regions/sinnoh-trainer-balance-s17.json",
    "ch12":"data/regions/sinnoh-trainer-evolution-contract.json",
    "ch15":"data/regions/sinnoh-trainer-teams-ch15.json",
}
CODE_FILES={
    "pilot":"scripts/regions/SinnohPilot.rb",
    "intro_bridge":"scripts/regions/SinnohIntroContracts.rb",
    "starter_bridge":"scripts/regions/SinnohStarterContracts.rb",
    "compiler":"scripts/regions/build_sinnoh_twinleaf_events.py",
    "campaign":"scripts/battle_polish/Campaign.rb",
    "balance_fixture":"tests/sinnoh_s17_trainer_balance_runtime.rb",
}
EXPECTED={
    "TURTWIG":("CHIMCHAR",0),
    "CHIMCHAR":("PIPLUP",1),
    "PIPLUP":("TURTWIG",2),
}
CHECKPOINTS=(
    "mother_intro","barry_intro","rowan_briefcase_seen",
    "starter_received","rival_fought","pokedex_received",
)
OUTCOMES=("victory_true","can_lose_defeat_false","unconfirmed_nil")


def blocked(reason: str) -> None:
    raise ValueError("SINNOH_G08_BLOCKED: "+reason)


def load_public(path: Path, *, text: bool=False):
    if (path.is_symlink() or not path.is_file() or
            path.stat().st_size>250000):
        blocked("fonte publica ausente, nao regular ou grande demais")
    try:
        content=path.read_text(encoding="utf-8-sig")
        return content if text else json.loads(content)
    except (OSError, UnicodeError, ValueError):
        blocked("fonte publica invalida")


def audit(docs: dict, sources: dict) -> dict:
    if (type(docs) is not dict or set(docs)!=set(DATA_FILES)
            or type(sources) is not dict or set(sources)!=set(CODE_FILES)):
        blocked("fontes incompletas de introducao ou balanceamento")
    if any(type(row) is not dict for row in docs.values()):
        blocked("contrato nao e objeto JSON")
    if any(type(row) is not str for row in sources.values()):
        blocked("fonte de codigo nao e texto")

    # Preserve the original validators, including their event/Ruby source
    # guards; don't weaken or reinterpret their approval policies.
    try:
        g07=audit_g07(**{k:docs[k] for k in G07_FILES})
        s13=audit_s13(docs["intro"],docs["events"],docs["schema"],
                      sources["pilot"],sources["intro_bridge"])
        s14=audit_s14(docs["starters"],docs["events"],docs["schema"],
                      docs["intro"],sources["pilot"],sources["intro_bridge"],
                      sources["compiler"],sources["starter_bridge"])
        s17=audit_s17(docs["s17"],docs["ch12"],docs["ch15"],
                      ruby_source=sources["balance_fixture"])
    except (ValueError,KeyError,TypeError,AttributeError):
        blocked("regressao em CH06/G07/S13/S14/S17")

    if (g07["counts"]["physically_bound_maps"]!=0
            or g07["counts"]["physically_bound_events"]!=0
            or g07["counts"]["native_transfers_verified"]!=0
            or g07["counts"]["story_checkpoints"]!=6
            or s13.get("can_install") is not False
            or s14.get("can_install") is not False
            or s17.get("gameplay_certified") is not False):
        blocked("roteiro mudou para pseudo-jogavel")

    if (tuple(MATCHUPS)!=tuple((p,r[0]) for p,r in EXPECTED.items())
            or RIVAL_TYPE!="BLUE_SINNOH_RIVAL" or RIVAL_NAME!="Barry"
            or type(SEED_LEVEL) is not int or SEED_LEVEL!=5
            or READY_MARKER!="Data/blue-sinnoh-rival-ready.txt"):
        blocked("origem do gerador PBS/Barry mudou")

    intro_steps=docs["intro"]["steps"]
    s14_balls=docs["starters"]["balls"]
    g07_balls={b["species"]:b for b in g07["starter_balls"]}
    if (tuple(s["flag"] for s in intro_steps)!=CHECKPOINTS
            or len(s14_balls)!=3 or set(g07_balls)!=set(EXPECTED)):
        blocked("roteiro de Rowan/Barry/S13 nao reconciliado")
    if (docs["starters"].get("grant_seed_level")!=SEED_LEVEL
            or docs["starters"].get("compiled_pbs_barry_verified") is not False
            or docs["intro"].get("native_barry_pbs_compiled") is not False):
        blocked("seed ou estado PBS adulterados")
    if (docs["s17"]["rules"].get("normal_percent")!=70
            or docs["s17"]["rules"].get("master_percent")!=90
            or docs["s17"]["rules"].get("master_requires_stage")!=3
            or docs["s17"]["rules"].get("master_team_target")!=4
            or docs["s17"]["rules"].get("source_level")!="highest_non_egg_party_level"
            or docs["s17"]["rules"].get("no_fixed_trainer_levels_published") is not True):
        blocked("contrato S17 70/90 foi alterado")
    if (docs["ch12"]["level_cap"].get("regional_numeric_cap_in_save") is not None
            or docs["ch12"]["level_cap"].get("bst_cap_is_not_a_level_cap") is not True
            or docs["ch15"]["dynamic_balance"].get("normal_percent")!=70
            or docs["ch15"]["dynamic_balance"].get("master_percent")!=90):
        blocked("CH12/CH15 criou level cap numerico ou ignorou escala")
    required_pilot=(
        "def self.choose_starter_from_ball(species)",
        "return false unless pbAddPokemonSilent(requested, 5)",
        "return false if @starter_grant_in_progress",
        "def self.compiled_rival_valid?",
        "team.is_a?(Array) && team.length == 1",
        "level.is_a?(Integer) && level == 5",
        'setBattleRule("canLose")',
        "return false unless result == true || result == false",
        "return false unless scope && regional_state.equal?(scope) && starter == chosen",
        'return false unless commit_flag("rival_fought")',
        'return false unless commit_flag("pokedex_received")',
        "return false unless defined?($player) && $player &&",
    )
    if any(fragment not in sources["pilot"] for fragment in required_pilot):
        blocked("portao de Rowan/Barry ou de escrita no save removido")
    if (any(fragment not in sources["campaign"] for fragment in (
            "module BlueCampaign","master? ? 90 : 70",
            "def self.trainer_level(trainer,party=$player.party)",
            "pkmn.level=level", "BlueCampaign.active?"))
            or not all(name in sources["balance_fixture"] for name in (
                "SINNOH_S17_DYNAMIC_LEVELS_BOSSES_DOUBLE_MASTER_NO_MUTATION_OFFLINE_OK",
                "Marshal.dump(trainers)", "Battle.new(nil, nil, [], nil, trainers)"))):
        blocked("escala real compartilhada ou fixture S17 mudou")

    choices=[]
    for ball in s14_balls:
        selected=ball["species"]
        expected,version=EXPECTED.get(selected,("",-1))
        g07_row=g07_balls.get(selected,{})
        if (ball.get("rival_species")!=expected
                or type(ball.get("rival_pbs_version")) is not int
                or ball["rival_pbs_version"]!=version
                or ball.get("event_key")!=g07_row.get("event_key")
                or g07_row.get("barry_counter_species")!=expected
                or g07_row.get("barry_pbs_version")!=version
                or ball.get("map_symbol")!="SINNOH_LAKE_VERITY"):
            blocked("S14/G07 contradizem versao PBS de Barry: "+selected)
        choices.append({
            "starter":selected,"ball_event_key":ball["event_key"],
            "location_symbol":"SINNOH_LAKE_VERITY",
            "rival_species":expected,"rival_pbs_version":version,
            "pbs_seed_level_not_battle_level":SEED_LEVEL,
            "native_pbs_compilation_verified":False,
            "battle_binding_verified":False,
            "possible_outcomes_for_offline_fixture":list(OUTCOMES),
        })
    cases=[{
        "player_starter":row["starter"],
        "rival_species":row["rival_species"],
        "rival_version":row["rival_pbs_version"],
        "battle_result":(True if case=="victory_true" else
                          False if case=="can_lose_defeat_false" else None),
        "expected_story_progresses":case!="unconfirmed_nil",
        "expected_heal_after_confirmed_battle":case!="unconfirmed_nil",
        "native_result_verified":False,
    } for row in choices for case in OUTCOMES]

    return {
        "schema":1,"region":"SINNOH","stage":"G08",
        "status":"ROWAN_BARRY_OFFLINE_CONTRACTS_CROSSCHECKED_NATIVE_BATTLE_PENDING",
        "mode":"READ_ONLY_GITHUB_STATIC_AND_SYNTHETIC_QA",
        "source_contracts":["CH06","G07","S13","S14","CH08","S17","CH12","CH15"],
        "story_checkpoint_order":list(CHECKPOINTS),
        "player_choices":choices,
        "offline_battle_matrix":cases,
        "balance":{
            "normal_percent":70,"master_percent":90,
            "highest_non_egg_party_level":True,
            "rounding":"integer_floor","master_requires_stage":3,
            "master_team_target":4,"max_opponents_per_side":6,
            "pbs_seed_level_only":SEED_LEVEL,
            "numeric_fixed_trainer_level":None,
            "real_runtime_scaling_verified_in_game":False,
        },
        "gates":{
            "three_physical_balls_no_rowan_dialog":True,
            "story_order_and_state_dependencies_checked":True,
            "no_duplicate_starter_intent_checked":True,
            "barry_three_counter_versions_checked":True,
            "nil_battle_must_not_advance":True,
            "can_lose_false_is_completed_battle":True,
            "pokedex_only_after_confirmed_barry":True,
            "region_save_separation_required":True,
            "ready_marker_generated":False,
            "compiled_pbs_from_real_game_verified":False,
            "map_ids_and_event_positions_verified":False,
            "sprite_assets_verified":False,
            "native_runtime_qc_executed":False,
        },
        "offline_fixture_runs_required":[
            "tests/sinnoh_s13_intro_runtime.rb",
            "tests/sinnoh_s14_starter_runtime.rb",
            "tests/sinnoh_barry_ch08_runtime.rb",
            "tests/sinnoh_s17_trainer_balance_runtime.rb",
            "tests/sinnoh_g08_opening_runtime.rb",
        ],
        "real_game_data_or_saves_accessed":False,
        "game_exe_tested":False,"joiplay_tested":False,
        "r07_complete":False,"r08_complete":False,"r09_complete":False,
        "can_install_live_game":False,"gameplay_approved":False,
        "phase_b_approved":0,"phase_c_approved":0,"phase_d_approved":0,
    }


def run(root: Path=ROOT):
    return audit(
        {name:load_public(root/path) for name,path in DATA_FILES.items()},
        {name:load_public(root/path,text=True) for name,path in CODE_FILES.items()},
    )


def main(argv=None) -> int:
    try:
        if argv not in (None,[]):
            blocked("G08 nao aceita dados privados nem flags")
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        return 0
    except (ValueError,OSError,TypeError,KeyError,AttributeError):
        print("SINNOH_G08_BLOCKED: fontes publicas inconsistentes ou inseguras",
              file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main(sys.argv[1:]))
