#!/usr/bin/env python3
"""S13: audit authored story order, source handlers and safe runtime guards."""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from audit_sinnoh_twinleaf_events import audit as audit_ch06

MANIFEST=ROOT/"data/regions/sinnoh-intro-s13.json"
TEMPLATE=ROOT/"data/regions/sinnoh-twinleaf-events.json"
SCHEMA=ROOT/"data/regions/sinnoh-twinleaf-events.schema.json"
PILOT=ROOT/"scripts/regions/SinnohPilot.rb"
BRIDGE=ROOT/"scripts/regions/SinnohIntroContracts.rb"
FLAGS=["mother_intro","barry_intro","rowan_briefcase_seen","starter_received","rival_fought","pokedex_received"]
POLICIES={
  "ordered_flag_commits": True,
  "reject_unknown_keys": True,
  "no_start_without_sinnoh_state": True,
  "no_cross_region_state_write": True,
  "no_starter_without_physical_ball": True,
  "no_duplicate_starter": True,
  "no_barry_without_verified_compiled_trainer": True,
  "no_story_after_nil_battle": True,
  "can_lose_confirmed_false_result_is_valid": True,
  "pokedex_after_confirmed_rival": True,
  "only_actual_player_gets_dex": True,
  "no_map_ids_or_positions_fabricated": True,
  "isolated_qa_not_native_acceptance": True
};
TOP={
  "schema": 1,
  "region": "SINNOH",
  "task": "S13",
  "status": "INTRO_SEQUENCE_OFFLINE_ONLY_NOT_INSTALLED",
  "source_events": "data/regions/sinnoh-twinleaf-events.json",
  "source_runtime": "scripts/regions/SinnohPilot.rb",
  "state_key": "sinnoh_pilot",
  "reference": "BLUE_AUTHORED_PLATINUM_SEQUENCE",
  "step_count": 6,
  "native_maps_compiled": 0,
  "native_handlers_verified": 0,
  "native_barry_pbs_compiled": False,
  "source_sprites_verified": False,
  "start_spawn_verified": False,
  "game_exe_executed": False,
  "joiplay_executed": False,
  "native_qa_approved": False,
  "can_install": False,
  "gameplay_approved": False,
  "global_hooks_installed": False,
  "policies": {
    "ordered_flag_commits": True,
    "reject_unknown_keys": True,
    "no_start_without_sinnoh_state": True,
    "no_cross_region_state_write": True,
    "no_starter_without_physical_ball": True,
    "no_duplicate_starter": True,
    "no_barry_without_verified_compiled_trainer": True,
    "no_story_after_nil_battle": True,
    "can_lose_confirmed_false_result_is_valid": True,
    "pokedex_after_confirmed_rival": True,
    "only_actual_player_gets_dex": True,
    "no_map_ids_or_positions_fabricated": True,
    "isolated_qa_not_native_acceptance": True
  },
  "note": "Seis checkpoints de introducao autoral para a copia isolada. I06/I07/I08 seguem com prova nativa pendente (5/8). Nao ha mapa, sprite, PBS de Barry nem coordenada real auditada para publicar no jogo. Nao escreve novos hooks nem importa eventos doador."
};
PILOT_REQUIRED=(
    "module BlueSinnohPilot", "return false unless flags.keys.all?",
    "def self.commit_flag(key)", "return false unless previous.key?(key)",
    "return false if key == \"rival_fought\" && !@rival_battle_in_progress",
    "return false if key == \"pokedex_received\" && !@pokedex_grant_in_progress",
    "return false unless valid_flags?(flags.merge(key => true))",
    "accepted = pbAddPokemonSilent(requested, 5)",
    "return false unless accepted && added",
    "party.length == before.length + 1",
    "return false if @starter_grant_in_progress",
    "flags.replace(candidate)",
    "unless committed",
    "party.pop",
    "return false unless result == true || result == false",
    "compiled_rival_valid?", "return false unless commit_flag(\"pokedex_received\")",
    "BlueSinnohQAStart.barry_test_authorized?",
    "state[\"sinnoh_pilot\"] ||= {}",
)
BRIDGE_REQUIRED=(
    "module BlueSinnohIntroContracts",
    "VERIFIED_NATIVE_HANDLERS = {}.freeze",
    "def self.preview(state)",
    "BlueSinnohPilot.valid_flags?(flags)",
    "def self.native_ready?(state,checkpoint,callback)",
    "return false unless VERIFIED_NATIVE_HANDLERS.key?(checkpoint)",
)
FORBIDDEN=("EventHandlers.add(", "def self.install", "Game_Map.prepend(",
    "File.write(", "pbAddPokemonSilent(", "BlueRegions.award(",
    "TrainerBattle.start(", "Object.prepend(")
NIL_KEYS=("native_map_id","native_event_id")
BOOL_KEYS=("native_callback_verified","player_interaction_verified",
           "game_exe_verified","joiplay_verified")

def fail(reason):
    raise ValueError("SINNOH_S13_BLOCKED: "+reason)

def audit(manifest,template,schema,pilot,bridge):
    if not isinstance(manifest,dict) or set(manifest)!=set(TOP)|{"steps"}:
        fail("contrato incompleto ou campos adicionais")
    for key,value in TOP.items():
        if type(manifest[key]) is not type(value) or manifest[key]!=value:
            fail("escopo, direitos, instalacao ou flags adulterados: "+key)
    report=audit_ch06(template,schema)
    if (template.get("approved_for_install") is not False or
        template.get("gameplay_verified") is not False or
        any(m["map_id"] is not None or m["map_sha256"] is not None
            for m in template["maps"])):
        fail("fonte nao instalada foi declarada jogavel")
    handler={}
    balls=[]
    for m in template["maps"]:
        for e in m["events"]:
            if e["kind"]=="handler":
                if e["handler"] in handler:
                    fail("evento de NPC duplicado")
                handler[e["handler"]]=(m["symbol"],e["key"])
            elif e["kind"]=="starter_ball":
                balls.append({"map":m["symbol"],"event":e["key"],
                              "species":e["species"]})
    if len(handler)!=5 or len(balls)!=3:
        fail("templates de eventos/bolas nao correspondem a CH06")
    if set(x["species"] for x in balls)!={"TURTWIG","CHIMCHAR","PIPLUP"}:
        fail("trio de iniciais diferente")
    steps=manifest["steps"]
    if not isinstance(steps,list) or len(steps)!=6 or [x.get("flag") for x in steps]!=FLAGS:
        fail("cadeia narrativa com ordem adulterada")
    handlers=("mother","barry_intro","rowan_briefcase",
              "choose_starter_from_ball","barry_rival","rowan_pokedex")
    kinds=("dialogue","dialogue","dialogue","physical_starter",
           "confirmed_battle_can_lose","engine_pokedex_flag")
    for i,(step,handler_name,kind) in enumerate(zip(steps,handlers,kinds)):
        if not isinstance(step,dict):
            fail("checkpoint nao e objeto")
        location,event=handler.get(handler_name,("SINNOH_LAKE_VERITY",None))
        expected={
            "flag":FLAGS[i],"handler":handler_name,"needs":[FLAGS[i-1]] if i else [],
            "kind":kind,"order":i+1,"map":location,
            "event":event,"physical_balls":balls if kind=="physical_starter" else [],
            **{k:None for k in NIL_KEYS},**{k:False for k in BOOL_KEYS},
            "status":"OFFLINE_CONTRACT_ONLY"
        }
        if (set(step)!=set(expected) or any(type(step[k]) is not type(v) or
               step[k]!=v for k,v in expected.items())):
            fail("historia/posicao/resultado nativo fabricado: "+FLAGS[i])
    if any(part not in pilot for part in PILOT_REQUIRED):
        fail("guardas de runtime do piloto ausentes")
    if any(part not in bridge for part in BRIDGE_REQUIRED):
        fail("API read-only do preflight ausente")
    executable="\n".join(x for x in bridge.splitlines() if not x.lstrip().startswith("#"))
    if any(term in executable for term in FORBIDDEN):
        fail("bridge tenta instalar eventos ou criar recompensas")
    return {
        "region":"SINNOH","task":"S13","status":TOP["status"],
        "story_checkpoints":6,"native_maps_verified":0,"native_events_installed":0,
        "barry_pbs_compiled":False,"game_exe_executed":False,
        "joiplay_executed":False,"can_install":False,"code_only":True,
        "template_events_verified_offline":True,
    }

def run():
    return audit(json.loads(MANIFEST.read_text("utf-8")),
                 json.loads(TEMPLATE.read_text("utf-8")),
                 json.loads(SCHEMA.read_text("utf-8")),
                 PILOT.read_text("utf-8"),BRIDGE.read_text("utf-8"))

if __name__=="__main__":
    try:
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        print("SINNOH_S13_INTRO_CONTRACT_OK_OFFLINE")
    except (OSError,ValueError,TypeError,KeyError) as exc:
        print(str(exc),file=sys.stderr);sys.exit(2)
