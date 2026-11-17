#!/usr/bin/env python3
"""U07: audit initial Unova White story contracts and simulate save-safe events.

Strictly offline and inert. NEVER executes RPG Maker/Ruby scripts, edits
Game.exe/MapInfos, gives real Pokemon/items, or modifies game saves.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
EVENT_FILE=Path("data/regions/unova-u07-nuvema-events.json")
AREA_FILE=Path("data/regions/unova-u03-areas.json")
NPC_FILE=Path("data/regions/unova-sp04-npcs.json")
REGION_FILE=Path("site/public/data/regions.json")
REPORT=Path(".blue-work/unova/audit/u07-events-contract-preview.json")
STARTERS=("SNIVY","TEPIG","OSHAWOTT")
RIVALS={
    "SNIVY":{"CHEREN":"TEPIG","BIANCA":"OSHAWOTT"},
    "TEPIG":{"CHEREN":"OSHAWOTT","BIANCA":"SNIVY"},
    "OSHAWOTT":{"CHEREN":"SNIVY","BIANCA":"TEPIG"},
}
STAGES=(
    ("STARTER_GIFT","choice","NUVEMA_TOWN",None),
    ("BIANCA_FIRST_BATTLE","battle","NUVEMA_TOWN","BIANCA"),
    ("CHEREN_FIRST_BATTLE","battle","NUVEMA_TOWN","CHEREN"),
    ("MOM_XTRANSCEIVER","grant","NUVEMA_TOWN","MOM"),
    ("VISIT_BIANCA_HOME","dialogue","NUVEMA_TOWN","BIANCA"),
    ("JUNIPER_LAB_POKEDEX","grant","NUVEMA_TOWN","JUNIPER"),
    ("MOM_TOWN_MAP","grant","NUVEMA_TOWN","MOM"),
    ("ROUTE1_GROUP","dialogue","ROUTE_01","BIANCA"),
    ("JUNIPER_CAPTURE_TUTORIAL","grant","ROUTE_01","JUNIPER"),
    ("ACCUMULA_CENTER_INTRO","dialogue","ACCUMULA_TOWN","JUNIPER"),
    ("PLASMA_SPEECH","dialogue","ACCUMULA_TOWN","GHETSIS"),
    ("N_FIRST_BATTLE","battle","ACCUMULA_TOWN","N"),
    ("ROUTE2_PASSAGE","milestone","ACCUMULA_TOWN",None),
)
EXPECTED_REWARDS={
    "MOM_XTRANSCEIVER":[{"category":"KEY_ITEM","token":"XTRANSCEIVER","amount":1}],
    "JUNIPER_LAB_POKEDEX":[{"category":"KEY_ITEM","token":"POKEDEX","amount":1}],
    "MOM_TOWN_MAP":[{"category":"KEY_ITEM","token":"TOWN_MAP","amount":1}],
    "JUNIPER_CAPTURE_TUTORIAL":[{"category":"ITEM","token":"POKE_BALL","amount":5}],
    "ROUTE2_PASSAGE":[{"category":"STORY_TOKEN","token":"ROUTE_2_PASSAGE_READY","amount":1}],
}
BATTLES={
    "BIANCA_FIRST_BATTLE":("ADVANCE_ON_LOSS","RIVAL_BIANCA_WEAK_TO_PLAYER"),
    "CHEREN_FIRST_BATTLE":("ADVANCE_ON_LOSS","RIVAL_CHEREN_STRONG_AGAINST_PLAYER"),
    "N_FIRST_BATTLE":("WIN_REQUIRED","N_ACCUMULA_FIRST_ENCOUNTER"),
}
EVENT_KEYS=tuple("UNOVA_U07_"+x[0] for x in STAGES)
ENTRY_FIELDS={
    "key","kind","area_key","location_hint","actor_npc_key","requires",
    "dialogue_pt_br","starter_options","battle_policy","opponent_party_role",
    "grants_once","map_id","event_id","coordinates","source_event_id",
    "npc_sprite_verified","dialogue_installed","rights_verified",
    "game_exe_tested","android_tested","installed",
}
FALSE_FIELDS=("npc_sprite_verified","dialogue_installed","rights_verified",
              "game_exe_tested","android_tested","installed")
NULL_FIELDS=("map_id","event_id","coordinates","source_event_id")
KIND_SET={"choice","battle","grant","dialogue","milestone"}


def reject(reason: str) -> None:
    raise ValueError("UNOVA_U07_BLOQUEADO: "+reason)


def load_json(path: Path, max_size: int = 180_000) -> dict:
    path=Path(path).absolute()
    if path.is_symlink() or not path.is_file() or not 0 < path.stat().st_size <= max_size:
        reject("fonte JSON ausente/insegura ou grande demais: "+str(path))
    data=json.loads(path.read_text("utf-8-sig"))
    if not isinstance(data,dict):
        reject("arquivo JSON nao contem objeto")
    return data


def validate_contract(doc: dict, areas: dict, npcs: dict, regions: dict) -> list[dict]:
    expected={
        "schema":1,"region":"UNOVA","phase":"U07_CONTRACTS",
        "story_version":"WHITE_BW","status":"PLANNED_EVENT_CONTRACTS_NOT_INSTALLED",
        "area_catalog":str(AREA_FILE).replace("\\","/"),
        "npc_catalog":str(NPC_FILE).replace("\\","/"),
        "starter_choices":list(STARTERS),
        "rival_starter_by_player":RIVALS,
        "original_dialogue_reference_only":True,
        "trainer_team_data_installed":False,
        "mapids_audited":False,"game_exe_tested":False,
        "android_tested":False,"can_install":False,
    }
    if not isinstance(doc,dict) or set(doc)!=set(expected)|{"progression_rules","notes","events"}:
        reject("schema/colunas do catalogo de eventos incorretos")
    for key,value in expected.items():
        if type(doc.get(key)) is not type(value) or doc[key]!=value:
            reject("campo do catalogo alterado ou ativado indevidamente: "+key)
    rules={
        "save_state_region":"UNOVA",
        "save_state_schema":"SIMULATED_ONLY_NEVER_GAME_SAVE",
        "early_rival_battles":"ADVANCE_ON_LOSS",
        "n_first_battle":"WIN_REQUIRED",
        "all_rewards_once":True,"reentry_safe":True,
        "flags_namespaced":True,"physical_transfers_implemented":False,
    }
    if doc["progression_rules"]!=rules:
        reject("regras de save/reentradas alteradas")
    if (not isinstance(doc["notes"],list) or len(doc["notes"])<4 or
        any(not isinstance(s,str) or len(s)<25 for s in doc["notes"])):
        reject("notas tecnicas insuficientes")
    if (regions.get("regions",{}).get("UNOVA",{}).get("status")!="planned" or
        areas.get("state")!="PLANNED_REFERENCE_ONLY" or
        areas.get("may_install") is not False):
        reject("Unova ou catalogo U03 nao permanecem planned")
    area_rows=areas.get("areas")
    if not isinstance(area_rows,list) or len(area_rows)!=74:
        reject("catalogo U03 nao tem 74 areas")
    area_keys={a.get("key"):a for a in area_rows if isinstance(a,dict)}
    if len(area_keys)!=74:
        reject("area U03 duplicada/invalida")
    for key in ("UNOVA_NUVEMA_TOWN","UNOVA_ROUTE_01","UNOVA_ACCUMULA_TOWN"):
        area=area_keys.get(key)
        if not isinstance(area,dict) or area.get("phase")!="U07" or area.get("state")!="planned":
            reject("area U07 nao planejada: "+key)
        if area.get("source_map_id") is not None or area.get("destination_map_id") is not None:
            reject("area U07 tem MapID nao auditado")
    npc_rows=npcs.get("characters")
    if not isinstance(npc_rows,list) or len(npc_rows)!=73:
        reject("SP04 nao contem 73 NPCs planejados")
    roster={x.get("key") for x in npc_rows if isinstance(x,dict)}
    if len(roster)!=73:
        reject("NPC SP04 duplicado")
    events=doc.get("events")
    if not isinstance(events,list) or len(events)!=len(STAGES):
        reject("precisa de 13 eventos canonicos em ordem narrativa")
    for i,(row,stage) in enumerate(zip(events,STAGES)):
        suffix,kind,area,actor=stage
        if not isinstance(row,dict) or set(row)!=ENTRY_FIELDS:
            reject("campos invalidos no evento "+str(i))
        key="UNOVA_U07_"+suffix
        if row["key"]!=key or row["kind"]!=kind or kind not in KIND_SET:
            reject("identidade/tipo/ordem alterados em "+key)
        if row["area_key"]!="UNOVA_"+area:
            reject("area narrativa incorreta: "+key)
        actor_key=("UNOVA_NPC_"+actor) if actor else None
        if row["actor_npc_key"]!=actor_key or (actor_key and actor_key not in roster):
            reject("ator invalido: "+key)
        expected_deps=[events[i-1]["key"]] if i else []
        if row["requires"]!=expected_deps:
            reject("dependencia fora de ordem ou faltando: "+key)
        if (not isinstance(row["location_hint"],str) or not 8<=len(row["location_hint"])<=160 or
            not isinstance(row["dialogue_pt_br"],str) or not 15<=len(row["dialogue_pt_br"])<=300):
            reject("descricao/fala PT-BR ausente: "+key)
        for field in NULL_FIELDS:
            if row[field] is not None:
                reject("coordenada/MapID/evento real falsamente atribuido: "+key)
        for field in FALSE_FIELDS:
            if row[field] is not False:
                reject("eventos ja instalados ou testados falsamente: "+key)
        if row["starter_options"]!=(list(STARTERS) if kind=="choice" else []):
            reject("opcoes de inicial invalidas: "+key)
        batt=BATTLES.get(suffix)
        if row["battle_policy"]!=(batt[0] if batt else None) or row["opponent_party_role"]!=(batt[1] if batt else None):
            reject("regra de batalha contraditoria ou treinadores inventados: "+key)
        if row["grants_once"]!=EXPECTED_REWARDS.get(suffix,[]):
            reject("recompensa falsa/duplicada: "+key)
    return events


def load_project(project: Path) -> tuple[dict,list[dict]]:
    root=Path(project).absolute()
    doc=load_json(root/EVENT_FILE)
    areas=load_json(root/AREA_FILE)
    npcs=load_json(root/NPC_FILE, max_size=500_000)
    registry=load_json(root/REGION_FILE, max_size=500_000)
    events=validate_contract(doc,areas,npcs,registry)
    return doc,events


def empty_state() -> dict:
    """Simulation data only; never an Essentials savegame format."""
    return {"schema":1,"region":"UNOVA","story_version":"WHITE_BW",
            "completed_events":[],"starter":None,"rival_starters":{},"rewards":{}}


def _expected_rewards(events: list[dict], completed: list[str]) -> dict:
    result={}
    for row in events:
        if row["key"] not in completed:
            continue
        for reward in row["grants_once"]:
            key=reward["category"]+":"+reward["token"]
            result[key]=result.get(key,0)+reward["amount"]
    return result


def validate_state(state: dict, events: list[dict]) -> None:
    if not isinstance(state,dict) or set(state)!=set(empty_state()):
        reject("estado de simulacao invalido; nao fornecer saves do jogo")
    if (state.get("schema")!=1 or state.get("region")!="UNOVA" or
        state.get("story_version")!="WHITE_BW"):
        reject("estado de outra regiao/versao")
    completed=state["completed_events"]
    if (not isinstance(completed,list) or
        any(type(v) is not str for v in completed) or
        completed!=list(EVENT_KEYS[:len(completed)])):
        reject("flags fora de ordem, duplicadas ou de outra regiao")
    initial=completed!=[]
    starter=state["starter"]
    if (not initial and starter is not None) or (initial and starter not in STARTERS):
        reject("inicial sem evento ou evento sem inicial")
    expected_rivals=RIVALS[starter] if initial else {}
    if state["rival_starters"]!=expected_rivals:
        reject("rival alterado ou escolha inicial inconsistente")
    if state["rewards"]!=_expected_rewards(events,completed):
        reject("recompensas duplicadas/forjadas ou ausentes")


def apply_event(events: list[dict], state: dict, key: str,
                *, starter: str | None = None, outcome: str | None = None) -> dict:
    """Pure, simulated state transition; emits intentions, never real game actions."""
    validate_state(state,events)
    if type(key) is not str or key not in EVENT_KEYS:
        reject("evento inexistente ou fora do escopo U07")
    target=events[EVENT_KEYS.index(key)]
    if key in state["completed_events"]:
        if target["kind"]=="choice" and starter is not None and starter!=state["starter"]:
            reject("tentativa de trocar inicial depois da escolha")
        return {"status":"ALREADY_COMPLETED_NO_EFFECT","state":copy.deepcopy(state),"effects":[]}
    if any(flag not in state["completed_events"] for flag in target["requires"]):
        reject("pre-requisito da historia nao concluido: "+key)
    kind=target["kind"]
    if kind=="choice":
        if starter not in STARTERS or outcome is not None:
            reject("escolha deve ser exatamente Snivy, Tepig ou Oshawott")
    elif kind=="battle":
        if starter is not None or outcome not in ("WIN","LOSS"):
            reject("batalha precisa de resultado WIN/LOSS sem escolher novo inicial")
        if target["battle_policy"]=="WIN_REQUIRED" and outcome=="LOSS":
            return {"status":"BATTLE_LOST_RETRY_REQUIRED",
                    "state":copy.deepcopy(state),"effects":[]}
    elif starter is not None or outcome is not None:
        reject("evento simples nao aceita batalha ou escolha de inicial")
    new_state=copy.deepcopy(state)
    effects=[{"kind":"STORY_EVENT_FLAG_SIMULATED_ONLY","key":key}]
    if kind=="choice":
        new_state["starter"]=starter
        new_state["rival_starters"]=copy.deepcopy(RIVALS[starter])
        effects.append({"kind":"PARTNER_CHOICE_REFERENCE_ONLY","species":starter})
    if kind=="battle":
        role=target["opponent_party_role"]
        selected=(
            new_state["rival_starters"]["BIANCA"] if "BIANCA" in role else
            new_state["rival_starters"]["CHEREN"] if "CHEREN" in role else None
        )
        effects.append({"kind":"BATTLE_OUTCOME_REFERENCE_ONLY",
                        "opponent_role":role,"opponent_starter_reference":selected,
                        "result":outcome})
    for reward in target["grants_once"]:
        token=reward["category"]+":"+reward["token"]
        if token in new_state["rewards"]:
            reject("recompensa token repetido antes do evento")
        new_state["rewards"][token]=reward["amount"]
        effects.append({"kind":"REWARD_INTENT_NOT_GRANTED_IN_GAME",
                        "category":reward["category"],"token":reward["token"],
                        "amount":reward["amount"]})
    new_state["completed_events"].append(key)
    validate_state(new_state,events)
    return {"status":"SIMULATED_EVENT_COMPLETED_NOT_INSTALLED",
            "state":new_state,"effects":effects}


def demo(events: list[dict], chosen: str = "SNIVY") -> dict:
    state=empty_state()
    steps=[]
    for row in events:
        result=apply_event(
            events,state,row["key"],
            starter=chosen if row["kind"]=="choice" else None,
            outcome="WIN" if row["kind"]=="battle" else None,
        )
        state=result["state"]
        steps.append({"event_key":row["key"],"result":result["status"],
                      "effect_types":[effect["kind"] for effect in result["effects"]]})
    return {"mode":"OFFLINE_STORY_CONTRACT_SIMULATION_ONLY",
            "status":"SIMULATION_COMPLETED_NOT_GAMEPLAY",
            "steps":steps,"final_state":state,
            "game_or_saves_modified":False,"game_exe_tested":False,
            "android_tested":False,"can_install":False}


def write_private(project: Path, report: dict) -> Path:
    project=Path(project).absolute()
    folders=[project/".blue-work",project/".blue-work/unova",
             project/".blue-work/unova/audit"]
    for folder in [project,*folders]:
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            reject("pasta de relatorio insegura ou symlink")
    for folder in folders:
        folder.mkdir(exist_ok=True)
    out=project/REPORT
    if out.is_symlink():
        reject("relatorio preexistente e symlink")
    content=json.dumps(report,indent=2,ensure_ascii=False)+"\n"
    if out.exists():
        if out.read_text("utf-8")!=content:
            reject("relatorio ja existente diferente; nao sobrescrever evidencia")
    else:
        with out.open("x",encoding="utf-8") as fh:
            fh.write(content)
    return out


def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--simulate-demo",action="store_true",
                        help="simular eventos em memoria sem tocar em saves")
    parser.add_argument("--starter",choices=STARTERS,default="SNIVY")
    parser.add_argument("--write",action="store_true",
                        help="gravar apenas sumario privado em .blue-work/unova/audit")
    args=parser.parse_args(argv)
    try:
        doc,events=load_project(args.project)
        result={
            "schema":1,"region":"UNOVA","phase":"U07_CONTRACTS",
            "status":"CONTRACTS_VALIDATED_NOT_INSTALLED",
            "event_count":len(events),
            "event_keys":list(EVENT_KEYS),
            "unique_reward_events":sum(bool(e["grants_once"]) for e in events),
            "starter_choices":list(STARTERS),
            "mapids_verified":False,"scripts_installed":False,
            "game_exe_tested":False,"android_tested":False,
            "can_install":False,"game_or_saves_modified":False,
        }
        if args.simulate_demo:
            sim=demo(events,args.starter)
            result["simulation"]={
                "status":sim["status"],
                "event_count":len(sim["steps"]),
                "starter":sim["final_state"]["starter"],
                "rival_starters":sim["final_state"]["rival_starters"],
                "rewards":sim["final_state"]["rewards"],
                "completed_flags":len(sim["final_state"]["completed_events"]),
                "can_install":False,
            }
        if args.write:
            dest=write_private(args.project,result)
            print("U07_PRIVATE_REPORT="+str(dest),file=sys.stderr)
        print(json.dumps(result,ensure_ascii=False,indent=2))
        return 0
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(str(exc),file=sys.stderr)
        return 2


if __name__=="__main__":
    raise SystemExit(main())
