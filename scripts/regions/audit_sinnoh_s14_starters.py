#!/usr/bin/env python3
"""S14: fail-closed audit of physical starter balls in CH06, S13, compiler & Ruby."""
from __future__ import annotations
import json
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from audit_sinnoh_twinleaf_events import BALLS, audit as audit_ch06
from audit_sinnoh_s13_intro import audit as audit_s13

MANIFEST=ROOT/"data/regions/sinnoh-starters-s14.json"
EVENTS=ROOT/"data/regions/sinnoh-twinleaf-events.json"
SCHEMA=ROOT/"data/regions/sinnoh-twinleaf-events.schema.json"
S13=ROOT/"data/regions/sinnoh-intro-s13.json"
PILOT=ROOT/"scripts/regions/SinnohPilot.rb"
INTRO=ROOT/"scripts/regions/SinnohIntroContracts.rb"
COMPILER=ROOT/"scripts/regions/build_sinnoh_twinleaf_events.py"
BRIDGE=ROOT/"scripts/regions/SinnohStarterContracts.rb"
ORDER=("TURTWIG","CHIMCHAR","PIPLUP")
COUNTERS={"TURTWIG":("CHIMCHAR",0),"CHIMCHAR":("PIPLUP",1),"PIPLUP":("TURTWIG",2)}
TOP={
  "schema": 1,
  "region": "SINNOH",
  "task": "S14",
  "status": "PHYSICAL_STARTERS_OFFLINE_CONTRACT_NOT_INSTALLED",
  "source_events": "data/regions/sinnoh-twinleaf-events.json",
  "source_compiler": "scripts/regions/build_sinnoh_twinleaf_events.py",
  "source_runtime": "scripts/regions/SinnohPilot.rb",
  "source_intro": "data/regions/sinnoh-intro-s13.json",
  "native_map_id": None,
  "native_compiled_events": 0,
  "native_verified_starter_balls": 0,
  "starter_count": 3,
  "physical_interaction": "action",
  "grant_seed_level": 5,
  "save_key": "sinnoh_pilot",
  "approved_for_install": False,
  "starter_selection_playable": False,
  "game_exe_verified": False,
  "joiplay_verified": False,
  "native_qa_approved": False,
  "source_assets_verified": False,
  "compiled_pbs_barry_verified": False,
  "cross_region_key_items_migrated": False,
  "can_write_game": False,
  "verified_native_sources": {},
  "policies": {
    "rowan_explanation_required": True,
    "physical_ball_not_dialog": True,
    "one_starter_per_sinnoh_save": True,
    "starter_choice_immutable_after_grant": True,
    "reentrant_grant_blocked": True,
    "no_state_write_after_failed_grant": True,
    "save_reload_persists_choice": True,
    "region_travel_does_not_grant_other_starter": True,
    "reject_unknown_starter": True,
    "action_trigger_only": True,
    "event_key_map_species_must_match_ch06": True,
    "barry_counter_is_exact": True,
    "do_not_copy_native_donor_scripts": True,
    "never_install_missing_map_assets": True,
    "no_fake_gameplay_qa": True
  },
  "note": "S14 conclui somente o contrato e regressao das tres Pokebolas fisicas em fixtures; eventos reais em Lago Verity continuam sem MapID, coordenadas ou sprites verificados. I06-I08 permanecem incompletos (5/8). Nao ha PBS Barry compilado, Game.exe/JoiPlay ou save nativo testado. A entrega nao instala nem distribui fonte doadora."
};
NULL_ROWS=("native_map_id","native_event_id","verified_position",
           "verified_sprite","verified_native_callback")
FALSE_ROWS=("event_compiled","grant_tested_in_game","save_load_tested_in_game")
COMPILER_REQUIRED=(
    "from audit_sinnoh_twinleaf_events import BALLS as STATIC_BALLS, HANDLERS as STATIC_HANDLERS",
    'if trigger != "action" or STATIC_BALLS.get(key) != (symbol, species):',
    'if STATIC_HANDLERS.get(key) != (symbol, handler):',
    'script = f"BlueSinnohPilot.choose_starter_from_ball(:{species})"',
    "row.get(\"verified_sprite\") is not True",
    "source_file.is_symlink()",
    "result_files[name] = serialize(out, EVENT_CLASSES)",
)
PILOT_REQUIRED=(
    "STARTERS = [:TURTWIG, :CHIMCHAR, :PIPLUP].freeze",
    "return false if @starter_grant_in_progress",
    "return false unless pbAddPokemonSilent(requested, 5)",
    "return false unless scope && regional_state.equal?(scope)",
    'current["starter_received"] != true',
    'scope["sinnoh_pilot"]["starter"] = requested.to_s',
    'scope["sinnoh_pilot"]["starter_received"] = true',
    'return false if flags["starter_received"] || flags.key?("starter")',
)
BRIDGE_REQUIRED=(
    "module BlueSinnohStarterContracts",
    "VERIFIED_NATIVE_SOURCES = {}.freeze",
    "def self.preview(state, species)",
    "BlueSinnohPilot.valid_flags?(flags)",
    "def self.native_event_ready?(state, species, source_id)",
    "return false unless VERIFIED_NATIVE_SOURCES.key?(event_key)",
)
BRIDGE_FORBIDDEN=(
    "EventHandlers.add(", "BlueSinnohPilot.choose_starter_from_ball(",
    "pbAddPokemonSilent(", "BlueRegions.award(", "TrainerBattle.start(",
    "Game_Map.prepend(", "File.write(", "def self.install",
)

def fail(msg):
    raise ValueError("SINNOH_S14_BLOCKED: "+msg)

def audit(manifest,events,schema,s13,pilot,intro,compiler,bridge):
    if not isinstance(manifest,dict) or set(manifest)!=(set(TOP)|{"balls"}):
        fail("manifesto incompleto ou campos adicionais")
    for key,expected in TOP.items():
        if type(manifest[key]) is not type(expected) or manifest[key]!=expected:
            fail("prova nativa, historico, politicas ou instalacao forjadas: "+key)
    audit_ch06(events,schema)
    audit_s13(s13,events,schema,pilot,intro)
    if (events["starter_selection"]!="THREE_PHYSICAL_BALL_EVENTS_NOT_ROWAN_DIALOG"
        or events["approved_for_install"] is not False
        or events["gameplay_verified"] is not False
        or events["start"]["map_id"] is not None):
        fail("escolha de inicial fora das tres bolas ou mapa ficticio")
    source={}
    for area in events["maps"]:
        for e in area["events"]:
            if e["kind"]=="starter_ball":
                source[e["species"]]=(e,area["symbol"],area["map_id"])
    if set(source)!=set(ORDER) or len(BALLS)!=3 or len(manifest["balls"])!=3:
        fail("trio fisico de iniciais incompleto")
    for i,(species,row) in enumerate(zip(ORDER,manifest["balls"])):
        e,area,mid=source[species]
        native=BALLS[e["key"]]
        if (native!=(area,species) or mid is not None or
            e["trigger"]!="action" or e["sprite"] is not None or
            e["verified_position"] is not False):
            fail("bola foi remapeada ou falsamente verificada")
        expected={
            "species":species,"event_key":e["key"],"map_symbol":area,
            "trigger":"action","rival_species":COUNTERS[species][0],
            "rival_pbs_version":COUNTERS[species][1],
            **{x:None for x in NULL_ROWS},**{x:False for x in FALSE_ROWS},
            "status":"AUTHOR_ONLY_NOT_INSTALLED"
        }
        if (not isinstance(row,dict) or set(row)!=set(expected) or
            any(type(row[k]) is not type(v) or row[k]!=v for k,v in expected.items())):
            fail("especie/versao rival/evento nativo adulterado: "+species)
    if any(s not in compiler for s in COMPILER_REQUIRED):
        fail("compilador nao garante correspondencia CH06 e action trigger")
    if any(s not in pilot for s in PILOT_REQUIRED):
        fail("runtime nao preserva a escolha unica por save")
    if any(s not in bridge for s in BRIDGE_REQUIRED):
        fail("preflight Ruby sem guardas regionais")
    code="\n".join(l for l in bridge.splitlines() if not l.lstrip().startswith("#"))
    if any(s in code for s in BRIDGE_FORBIDDEN):
        fail("preflight Ruby tenta escrever save, instalar evento ou dar Pokemon")
    return {
        "region":"SINNOH","task":"S14","status":TOP["status"],
        "physical_starter_events":3,"native_maps":0,"native_balls_installed":0,
        "game_exe_verified":False,"joiplay_verified":False,"can_install":False,
        "code_only":True
    }

def run():
    paths=(MANIFEST,EVENTS,SCHEMA,S13)
    obj=[json.loads(x.read_text("utf-8")) for x in paths]
    src=[x.read_text("utf-8") for x in (PILOT,INTRO,COMPILER,BRIDGE)]
    return audit(*obj,*src)

if __name__=="__main__":
    try:
        print(json.dumps(run(),ensure_ascii=False,indent=2))
        print("SINNOH_S14_PHYSICAL_STARTERS_OK_OFFLINE")
    except (OSError,KeyError,TypeError,ValueError,IndexError) as exc:
        print(str(exc),file=sys.stderr);sys.exit(2)
