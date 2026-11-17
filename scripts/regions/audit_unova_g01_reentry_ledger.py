#!/usr/bin/env python3
"""Unova G01.3 — idempotent U07 event intents and chapter revisits, OFFLINE ONLY.

Extends G01.1 state and G01.2 machine with a separate *in-memory* receipt ledger.
No native inventory, saves, RXDATA, Game.exe, reward grants or filesystem writes.
G01.4 will address explicit synthetic serialization/migration separately.
"""
from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
from typing import Any

import audit_unova_g01_state_schema as g01
import audit_unova_g01_chapter_machine as machine
import audit_unova_u07_events as u07

ROOT=Path(__file__).resolve().parents[2]
POLICY=ROOT/"data/regions/unova-g01-reentry-policy.json"
SCOPE="SIMULATED_ONLY_NOT_GAME_SAVE"
RECEIPT_STATUS="OFFLINE_RECEIPT_NOT_A_GAME_REWARD"
STATUS_APPLIED="SIMULATED_APPLIED"
STATUS_ALREADY="SIMULATED_ALREADY_APPLIED"
STATUS_REENTER="SIMULATED_REENTER_READ_ONLY"
STATUS_RETRY="BATTLE_LOST_RETRY_REQUIRED"
STARTERS=frozenset({"SNIVY","TEPIG","OSHAWOTT"})

def deny(reason:str)->None:
    raise ValueError("UNOVA_G01_3_BLOCKED: "+reason)

def _exact(obj:Any,keys:set[str],label:str)->None:
    if not isinstance(obj,dict) or set(obj)!=keys:
        deny(label+" unexpected or missing fields")

def _copy(obj:Any)->Any:
    return copy.deepcopy(obj)

def load_project(root:Path=ROOT)->tuple[dict,dict,dict,list[dict]]:
    """Revalidate the original U07 catalog, G01.1 contract and G01.2 rules."""
    root=Path(root)
    contract,rules=machine.load_project(root)
    _,events=u07.load_project(root)
    policy=machine._safe_source(root/"data/regions/unova-g01-reentry-policy.json")
    validate_policy(policy,contract,rules,events)
    return contract,rules,policy,events

def validate_policy(policy:dict,contract:dict,rules:dict,events:list[dict])->dict:
    _exact(policy,{
        "schema","region","campaign","phase","status","state_schema_version",
        "ledger_schema_version","g01_contract","g01_machine","source_u07_events",
        "scope","allowed_operations","duplicate_event","conflicting_replay",
        "past_chapter_reentry","failed_required_win","reward_intents_not_inventory",
        "actual_items_granted","game_exe_tested","can_install",
        "release_native_claims","events","reward_keys","notes"
    },"G01.3 policy")
    expect={
        "schema":1,"region":"UNOVA","campaign":"WHITE_BW","phase":"G01.3",
        "status":"OFFLINE_RECEIPT_LEDGER_NOT_NATIVE_INVENTORY",
        "state_schema_version":1,"ledger_schema_version":1,
        "g01_contract":"data/regions/unova-g01-state-contract.json",
        "g01_machine":"data/regions/unova-g01-chapter-transitions.json",
        "source_u07_events":"data/regions/unova-u07-nuvema-events.json",
        "scope":SCOPE,
        "allowed_operations":["begin","record_u07","complete","advance","reenter"],
        "duplicate_event":"NO_OP_ONLY_IF_INPUT_MATCHES_ORIGINAL",
        "conflicting_replay":"REJECT_FAIL_CLOSED",
        "past_chapter_reentry":"READ_ONLY_NO_CHECKPOINT_ROLLBACK",
        "failed_required_win":"NO_OP_RETRY_WITHOUT_RECEIPT",
        "reward_intents_not_inventory":True,"actual_items_granted":False,
        "game_exe_tested":False,"can_install":False,"release_native_claims":False,
    }
    for key,value in expect.items():
        if type(policy.get(key)) is not type(value) or policy[key]!=value:
            deny("unsafe or inconsistent policy field: "+key)
    if (contract.get("contract_version")!=1 or
        rules.get("phase")!="G01.2" or rules.get("simulation_gate")!=machine.SIMULATION_GATE or
        not isinstance(events,list) or len(events)!=13):
        deny("G01.1/G01.2/U07 sources incompatible")
    source_order=[{
        "event_key":e["key"],"requires":e["requires"],
        "battle_policy":e["battle_policy"],"kind":e["kind"],
        "grants_once":e["grants_once"],
    } for e in events]
    if policy["events"]!=source_order:
        deny("U07 reward data or event order differs from source")
    reward_keys=[]
    for event in events:
        for reward in event["grants_once"]:
            _exact(reward,{"category","token","amount"},"source reward")
            token=reward["category"]+":"+reward["token"]
            if (not isinstance(reward["category"],str) or
                not isinstance(reward["token"],str) or
                type(reward["amount"]) is not int or reward["amount"]<=0 or
                reward["amount"]>9999 or token in reward_keys):
                deny("unsafe, invalid or repeated U07 source reward")
            reward_keys.append(token)
    if reward_keys!=policy["reward_keys"] or len(reward_keys)!=5:
        deny("5 source-grounded reward tokens required")
    if not isinstance(policy["notes"],list) or len(policy["notes"])<3:
        deny("missing safety notes")
    return {"phase":"G01.3","u07_events":13,
            "unique_reward_intent_tokens":len(reward_keys),
            "status":"OFFLINE_LEDGER_POLICY_VALIDATED",
            "can_install":False,"game_exe_tested":False,
            "native_items_granted":False}

def initial(contract:dict)->dict:
    return {"schema":1,"region":"UNOVA","campaign":"WHITE_BW",
            "scope":SCOPE,"state":g01.empty_state(contract),
            "event_receipts":[],"reward_intents":{}}

def _expected_receipt(event:dict,starter_choice:str|None,
                      outcome:str|None)->dict:
    policy=event["battle_policy"]
    if event["kind"]=="choice":
        if starter_choice not in STARTERS or outcome is not None:
            deny("starter receipt requires an original Unova choice and no battle outcome")
    elif policy in {"WIN_REQUIRED","ADVANCE_ON_LOSS"}:
        if starter_choice is not None or outcome not in {"WIN","LOSS"} or (
            policy=="WIN_REQUIRED" and outcome!="WIN"):
            deny("battle receipt missing or contradicts U07 policy")
    elif starter_choice is not None or outcome is not None:
        deny("dialogue, grant and milestone do not accept battle/choice arguments")
    return {
        "event_key":event["key"],"starter_choice":starter_choice,
        "outcome":outcome,"reward_intents":_copy(event["grants_once"]),
        "receipt_status":RECEIPT_STATUS,
    }

def validate_envelope(envelope:dict,contract:dict,rules:dict,
                      policy:dict,events:list[dict])->dict:
    """Reject forged receipts, rewards, state flags and future chapter progress."""
    _exact(envelope,{"schema","region","campaign","scope",
        "state","event_receipts","reward_intents"},"G01.3 envelope")
    if (type(envelope["schema"]) is not int or envelope["schema"]!=1 or
        envelope["region"]!="UNOVA" or envelope["campaign"]!="WHITE_BW" or
        envelope["scope"]!=SCOPE):
        deny("unknown ledger version or cross-region scope")
    # A syntactically valid G01.1 state must also be reachable under G01.2.
    machine.validate_progression(envelope["state"],contract,rules)
    receipts=envelope["event_receipts"]
    if not isinstance(receipts,list) or len(receipts)>len(events):
        deny("event receipt list must be bounded")
    expected_totals={}
    for index,receipt in enumerate(receipts):
        event=events[index]
        _exact(receipt,{"event_key","starter_choice","outcome",
            "reward_intents","receipt_status"},"event receipt")
        expected=_expected_receipt(event,receipt["starter_choice"],receipt["outcome"])
        if receipt!=expected:
            deny("event receipt wrong order, inputs or reward amounts")
        if envelope["state"]["flags"].get(event["key"]) is not True:
            deny("receipt without completed event flag")
        for reward in event["grants_once"]:
            token=reward["category"]+":"+reward["token"]
            if token in expected_totals:
                deny("duplicate reward token across U07 events")
            expected_totals[token]=reward["amount"]
    true_flags=[e["key"] for e in events if envelope["state"]["flags"].get(e["key"]) is True]
    if true_flags!=[r["event_key"] for r in receipts]:
        deny("event completion flags and receipts must match exactly")
    stored_totals=envelope["reward_intents"]
    if (not isinstance(stored_totals,dict) or
        any(type(value) is not int for value in stored_totals.values()) or
        stored_totals!=expected_totals):
        deny("reward intent ledger differs from canonical single grants")
    return {"events_recorded":len(receipts),"unique_reward_tokens":len(expected_totals),
            "offline_only":True,"native_inventory_verified":False}

def _result(envelope:dict,status:str,*,new_intents:list[dict]|None=None)->dict:
    return {"status":status,"envelope":_copy(envelope),
            "new_reward_intents":_copy(new_intents) if new_intents is not None else [],
            "actual_items_granted":False,"native_save_modified":False,
            "game_exe_tested":False,"can_install":False}

def apply(envelope:dict,contract:dict,rules:dict,policy:dict,events:list[dict],
          action:str,*,event_key:str|None=None,starter_choice:str|None=None,
          outcome:str|None=None,chapter_key:str|None=None,
          simulation_gate:str|None=None)->dict:
    """Pure, fail-closed operation. Successful identical replays are no-ops."""
    validate_policy(policy,contract,rules,events)
    validate_envelope(envelope,contract,rules,policy,events)
    if action not in policy["allowed_operations"]:
        deny("unknown action")
    if action!="record_u07" and (
            event_key is not None or starter_choice is not None or outcome is not None):
        deny("event arguments only valid for record_u07")
    if action not in {"complete"} and simulation_gate is not None:
        deny("simulation_gate only valid for complete")
    if action in {"begin","record_u07"} and chapter_key is not None:
        deny("chapter_key not permitted for this action")
    if action in {"complete","advance","reenter"} and (
            not isinstance(chapter_key,str)):
        deny("explicit chapter_key required for replay-safe operation")
    state=envelope["state"]
    current=machine._chapter_index(state,contract)
    chapters=contract["chapters"]
    if action=="begin":
        if current>0:
            return _result(envelope,STATUS_ALREADY)
        next_state=machine.step(state,contract,rules,"begin")["state"]
        changed=_copy(envelope);changed["state"]=next_state
        validate_envelope(changed,contract,rules,policy,events)
        return _result(changed,STATUS_APPLIED)
    if action=="record_u07":
        if not isinstance(event_key,str):
            deny("event_key must be a U07 key")
        known={e["key"]:e for e in events}
        if event_key not in known:
            deny("unknown U07 event")
        event=known[event_key]
        receipt=_expected_receipt(event,starter_choice,outcome) if not (
            event["battle_policy"]=="WIN_REQUIRED" and outcome=="LOSS"
        ) else None
        old=next((r for r in envelope["event_receipts"] if r["event_key"]==event_key),None)
        if old is not None:
            if receipt is None or old!=receipt:
                deny("conflicting duplicate event outcome, starter or receipt")
            return _result(envelope,STATUS_ALREADY)
        if current!=1 or state["missions"].get(contract["missions"][0]["key"])!="active":
            deny("new U07 event outside active opening chapter")
        if event["battle_policy"]=="WIN_REQUIRED" and outcome=="LOSS":
            if starter_choice is not None:
                deny("N battle loss cannot carry starter input")
            next_event=machine.available(state,contract,rules)
            if len(next_event)!=1 or next_event[0].get("event")!=event_key:
                deny("N loss attempt is out of order")
            return _result(envelope,STATUS_RETRY)
        # G01.2 enforces order and prerequisites for new U07 completions.
        next_state=machine.step(state,contract,rules,"record_u07",
                               event_key=event_key,starter_choice=starter_choice,
                               outcome=outcome)["state"]
        changed=_copy(envelope)
        changed["state"]=next_state
        changed["event_receipts"].append(receipt)
        new_intents=[]
        for reward in receipt["reward_intents"]:
            token=reward["category"]+":"+reward["token"]
            if token in changed["reward_intents"]:
                deny("duplicate planned reward token")
            changed["reward_intents"][token]=reward["amount"]
            new_intents.append({"kind":"REWARD_INTENT_NOT_GRANTED_IN_GAME",
                                "category":reward["category"],"token":reward["token"],
                                "amount":reward["amount"],"source_event":event_key})
        validate_envelope(changed,contract,rules,policy,events)
        return _result(changed,STATUS_APPLIED,new_intents=new_intents)
    chapter_keys=[row["key"] for row in chapters]
    if chapter_key not in chapter_keys:
        deny("unknown chapter")
    index=chapter_keys.index(chapter_key)
    if action=="reenter":
        if index>current or (index==0 and current>0):
            deny("cannot reenter a future or prestart chapter")
        return _result(envelope,STATUS_REENTER)
    if index==0:
        deny("cannot complete/advance prestart chapter")
    if index>current:
        deny("cannot skip to a future chapter")
    if action=="complete":
        if simulation_gate!=machine.SIMULATION_GATE:
            deny("explicit offline completion token required")
        if index<current or state["missions"].get(contract["missions"][index-1]["key"])=="completed":
            if (state["missions"].get(contract["missions"][index-1]["key"])!="completed"
                or state["flags"].get(machine.completion_flag(index)) is not True):
                deny("prior chapter is not completed")
            return _result(envelope,STATUS_ALREADY)
        next_state=machine.step(state,contract,rules,"complete",
                                simulation_gate=simulation_gate)["state"]
    elif action=="advance":
        if index>=12:
            deny("last chapter has no next transition")
        if index<current:
            if (state["missions"].get(contract["missions"][index-1]["key"])!="completed"
                or state["flags"].get(machine.completion_flag(index)) is not True):
                deny("prior chapter advance not proven")
            return _result(envelope,STATUS_ALREADY)
        next_state=machine.step(state,contract,rules,"advance")["state"]
    else:
        deny("unsupported action")
    changed=_copy(envelope)
    changed["state"]=next_state
    validate_envelope(changed,contract,rules,policy,events)
    return _result(changed,STATUS_APPLIED)

def demo(contract:dict,rules:dict,policy:dict,events:list[dict])->dict:
    """Simulate U07, five original rewards, a losing N attempt, and replay."""
    snapshot=initial(contract)
    def once(action,**kwargs):
        nonlocal snapshot
        result=apply(snapshot,contract,rules,policy,events,action,**kwargs)
        snapshot=result["envelope"]
        return result
    once("begin")
    attempts=0
    duplicate_noops=0
    for event in events:
        kwargs={"event_key":event["key"]}
        if event["kind"]=="choice":
            kwargs["starter_choice"]="SNIVY"
        if event["battle_policy"] in ("ADVANCE_ON_LOSS","WIN_REQUIRED"):
            kwargs["outcome"]="WIN"
        if event["battle_policy"]=="WIN_REQUIRED":
            trial=once("record_u07",event_key=event["key"],outcome="LOSS")
            if trial["status"]!=STATUS_RETRY:deny("synthetic N loss invariant")
            attempts+=1
        first=once("record_u07",**kwargs)
        if first["status"]!=STATUS_APPLIED:deny("event not applied in offline demo")
        retry=once("record_u07",**kwargs)
        if retry["status"]!=STATUS_ALREADY or retry["new_reward_intents"]:
            deny("offline replay issued duplicate rewards")
        duplicate_noops+=1
    once("complete",chapter_key=contract["chapters"][1]["key"],
         simulation_gate=machine.SIMULATION_GATE)
    once("advance",chapter_key=contract["chapters"][1]["key"])
    reentry=once("reenter",chapter_key=contract["chapters"][1]["key"])
    if reentry["status"]!=STATUS_REENTER:deny("reentry changed chapter")
    report=validate_envelope(snapshot,contract,rules,policy,events)
    return {"phase":"G01.3","status":"OFFLINE_LEDGER_DEMO_NOT_NATIVE_GAME",
            "events_recorded":report["events_recorded"],
            "unique_reward_intent_tokens":report["unique_reward_tokens"],
            "reward_intents":_copy(snapshot["reward_intents"]),
            "duplicate_event_noops":duplicate_noops,
            "failed_n_attempts_without_progress":attempts,
            "chapter_after_reentry":snapshot["state"]["current_chapter"],
            "native_items_granted":False,"native_save_modified":False,
            "game_exe_tested":False,"can_install":False}

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check",action="store_true")
    group.add_argument("--simulate-demo",action="store_true")
    args=parser.parse_args(argv)
    try:
        contract,rules,policy,events=load_project()
        result=(validate_policy(policy,contract,rules,events)
                if args.check else demo(contract,rules,policy,events))
        print(json.dumps(result,sort_keys=True,ensure_ascii=False))
        return 0
    except (ValueError,OSError,KeyError,TypeError,RecursionError) as exc:
        print("UNOVA_G01_3_BLOCKED: "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
