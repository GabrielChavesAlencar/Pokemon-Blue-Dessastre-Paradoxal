#!/usr/bin/env python3
"""Unova G01.4: deterministic, in-memory, synthetic-only state serialization.

Encodes *only* G01.3 envelopes with G01.1 v1/G01.2/U07 invariants.
Explicit synthetic legacy storage-v0 fixture migration replays all events.
Never reads or writes player saves, never executes Game.exe, never installs maps.
SHA-256 is an integrity checksum, NOT authentication or an anti-tamper signature.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import audit_unova_g01_chapter_machine as machine
import audit_unova_g01_reentry_ledger as ledger

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/"data/regions/unova-g01-serialization-contract.json"
V1="UNOVA_G01_4_OFFLINE_STATE_V1"
LEGACY="UNOVA_G01_4_SYNTHETIC_FIXTURE_V0"
GATE="EXPLICIT_TEST_FIXTURE_ONLY"
SCOPE=ledger.SCOPE
LIMIT=262144
HEX64=re.compile(r"[0-9a-f]{64}\Z")
V1_FIELDS=frozenset({"format","storage_version","region","campaign","scope",
    "state_schema_version","ledger_schema_version","canonical_sha256","payload"})
V0_FIELDS=frozenset({"format","storage_version","region","campaign","scope",
    "migration_gate","state","events","reward_intents"})

def deny(reason:str)->None:
    raise ValueError("UNOVA_G01_4_BLOCKED: "+reason)

def _keys(value:Any,expected:frozenset[str]|set[str],label:str)->None:
    if not isinstance(value,dict) or set(value)!=set(expected):
        deny(label+" unexpected or missing fields")

def _canonical(value:Any)->bytes:
    try:
        return json.dumps(value,sort_keys=True,separators=(",",":"),
                          ensure_ascii=False,allow_nan=False).encode("utf-8")
    except (TypeError,ValueError,OverflowError,UnicodeError,RecursionError) as exc:
        deny("non-JSON or non-finite value: "+type(exc).__name__)

def _pairs_unique(pairs:list[tuple[str,Any]])->dict:
    out={}
    for key,value in pairs:
        if key in out:
            deny("duplicate JSON key: "+str(key))
        out[key]=value
    return out

def _invalid_constant(value:str)->None:
    deny("non-JSON numeric constant: "+value)

def _read_bytes(blob:bytes)->dict:
    if not isinstance(blob,bytes) or not 0<len(blob)<=LIMIT:
        deny("persistence input must be bounded, nonempty UTF-8 bytes")
    try:
        raw=blob.decode("utf-8")
    except UnicodeDecodeError:
        deny("invalid UTF-8 bytes")
    if raw.startswith("\ufeff"):
        deny("UTF-8 BOM not accepted")
    try:
        document=json.loads(raw,object_pairs_hook=_pairs_unique,
                            parse_constant=_invalid_constant)
    except (ValueError,TypeError,RecursionError) as exc:
        deny("malformed JSON: "+type(exc).__name__)
    if not isinstance(document,dict):
        deny("persistence root must be JSON object")
    return document

def load_project(root:Path=ROOT)->tuple[dict,dict,dict,list[dict],dict]:
    contract,rules,reentry,events=ledger.load_project(root)
    policy=machine._safe_source(Path(root)/"data/regions/unova-g01-serialization-contract.json")
    validate_policy(policy,contract,rules,reentry,events)
    return contract,rules,reentry,events,policy

def validate_policy(policy:dict,contract:dict,rules:dict,
                    reentry:dict,events:list[dict])->dict:
    _keys(policy,{"schema","region","campaign","phase","status",
          "format_v1","legacy_format_v0","storage_version",
          "accepted_current_storage_versions","explicit_legacy_storage_version",
          "state_schema_version","ledger_schema_version","scope",
          "payload_source","state_contract","transition_contract",
          "receipt_policy","hash_algorithm","canonical_json","max_payload_bytes",
          "legacy_migration","legacy_fixture_only","auto_migration",
          "real_game_save_adapter","native_items_granted","can_install",
          "game_exe_tested","notes"},"codec policy")
    expected={
        "schema":1,"region":"UNOVA","campaign":"WHITE_BW","phase":"G01.4",
        "status":"OFFLINE_TEST_FIXTURE_CODEC_NOT_NATIVE_SAVE",
        "format_v1":V1,"legacy_format_v0":LEGACY,"storage_version":1,
        "accepted_current_storage_versions":[1],"explicit_legacy_storage_version":0,
        "state_schema_version":1,"ledger_schema_version":1,"scope":SCOPE,
        "payload_source":"scripts/regions/audit_unova_g01_reentry_ledger.py",
        "state_contract":"data/regions/unova-g01-state-contract.json",
        "transition_contract":"data/regions/unova-g01-chapter-transitions.json",
        "receipt_policy":"data/regions/unova-g01-reentry-policy.json",
        "hash_algorithm":"SHA256_CANONICAL_UTF8_JSON_PAYLOAD",
        "canonical_json":"UTF8_SORT_KEYS_COMPACT_NO_NAN","max_payload_bytes":LIMIT,
        "legacy_migration":"EXPLICIT_ONLY_REPLAY_SOURCE_EVENTS_AND_COMPARE_STATE",
        "legacy_fixture_only":True,"auto_migration":False,
        "real_game_save_adapter":False,"native_items_granted":False,
        "can_install":False,"game_exe_tested":False,
    }
    for key,value in expected.items():
        if type(policy[key]) is not type(value) or policy[key]!=value:
            deny("unsupported version or native security claim: "+key)
    if (contract["compatibility"]["current_state_schema_version"]!=1 or
        contract["compatibility"]["native_save_adapter"]!="NOT_IMPLEMENTED" or
        rules["phase"]!="G01.2" or reentry["phase"]!="G01.3" or
        reentry["scope"]!=SCOPE or len(events)!=13):
        deny("G01.1-G01.3 dependencies incompatible")
    if not isinstance(policy["notes"],list) or len(policy["notes"])<3:
        deny("codec safety notes missing")
    return {"phase":"G01.4","status":"OFFLINE_CODEC_POLICY_VALIDATED",
            "current_storage_version":1,"explicit_legacy_fixture_version":0,
            "can_install":False,"game_exe_tested":False,
            "native_save_compatible":False}

def _check_envelope(envelope:dict,ctx:tuple)->None:
    c,r,p,events,_=ctx
    ledger.validate_envelope(envelope,c,r,p,events)

def encode_current(envelope:dict,ctx:tuple)->bytes:
    """Canonical v1 UTF-8 bytes; no path, file, save or native operation."""
    _check_envelope(envelope,ctx)
    payload=copy.deepcopy(envelope)
    payload_bytes=_canonical(payload)
    doc={"format":V1,"storage_version":1,"region":"UNOVA",
         "campaign":"WHITE_BW","scope":SCOPE,
         "state_schema_version":1,"ledger_schema_version":1,
         "canonical_sha256":hashlib.sha256(payload_bytes).hexdigest(),
         "payload":payload}
    out=_canonical(doc)
    if len(out)>LIMIT:
        deny("encoded synthetic state exceeds maximum")
    return out

def decode_current(blob:bytes,ctx:tuple)->dict:
    """Decode only v1: never auto-migrate v0 or native save formats."""
    doc=_read_bytes(blob)
    _keys(doc,V1_FIELDS,"v1 document")
    expected={
        "format":V1,"storage_version":1,"region":"UNOVA","campaign":"WHITE_BW",
        "scope":SCOPE,"state_schema_version":1,"ledger_schema_version":1}
    for key,value in expected.items():
        if type(doc[key]) is not type(value) or doc[key]!=value:
            deny("invalid or future storage/state version, region or scope: "+key)
    token=doc["canonical_sha256"]
    if not isinstance(token,str) or not HEX64.fullmatch(token):
        deny("invalid checksum")
    if hashlib.sha256(_canonical(doc["payload"])).hexdigest()!=token:
        deny("checksum mismatch")
    _check_envelope(doc["payload"],ctx)
    if _canonical(doc)!=blob:
        deny("v1 document must be canonical, not an alternate encoding")
    return copy.deepcopy(doc["payload"])

def _replay_legacy(doc:dict,ctx:tuple)->dict:
    """Reconstruct ONLY reproducible synthetic history using G01.3 public API."""
    c,r,policy,events,_=ctx
    _keys(doc,V0_FIELDS,"legacy fixture")
    expected={"format":LEGACY,"storage_version":0,"region":"UNOVA",
              "campaign":"WHITE_BW","scope":SCOPE,"migration_gate":GATE}
    for key,value in expected.items():
        if type(doc[key]) is not type(value) or doc[key]!=value:
            deny("not an explicitly marked synthetic legacy fixture: "+key)
    state=doc["state"]
    # Reject state schema v0/native saves: only STORAGE v0 is migratable.
    machine.validate_progression(state,c,r)
    recorded=doc["events"]
    if not isinstance(recorded,list) or len(recorded)>13:
        deny("legacy event sequence invalid")
    for ix,event in enumerate(recorded):
        _keys(event,{"event_key","starter_choice","outcome"},"legacy event")
        if event["event_key"]!=events[ix]["key"]:
            deny("legacy event out of source order")
    chapter_index=machine._chapter_index(state,c)
    rebuilt=ledger.initial(c)
    if chapter_index>0:
        rebuilt=ledger.apply(rebuilt,c,r,policy,events,"begin")["envelope"]
    elif recorded:
        deny("prestart legacy fixture contains completed events")
    for ev in recorded:
        rebuilt=ledger.apply(rebuilt,c,r,policy,events,"record_u07",
            event_key=ev["event_key"],starter_choice=ev["starter_choice"],
            outcome=ev["outcome"])["envelope"]
    if chapter_index>0:
        for index in range(1,chapter_index+1):
            current=c["chapters"][index]["key"]
            should_complete=index<chapter_index or (
                state["missions"].get(c["missions"][index-1]["key"])=="completed")
            if should_complete:
                rebuilt=ledger.apply(rebuilt,c,r,policy,events,"complete",
                    chapter_key=current,simulation_gate=machine.SIMULATION_GATE)["envelope"]
            if index<chapter_index:
                rebuilt=ledger.apply(rebuilt,c,r,policy,events,"advance",
                    chapter_key=current)["envelope"]
    if rebuilt["state"]!=state:
        deny("legacy state cannot be reconstructed from sanctioned history")
    if rebuilt["reward_intents"]!=doc["reward_intents"]:
        deny("legacy reward intentions disagree with canonical replay")
    _check_envelope(rebuilt,ctx)
    return rebuilt

def migrate_legacy(blob:bytes,ctx:tuple,*,acknowledge_fixture_only:bool=False)->bytes:
    """Explicit storage 0→1 migration; returns v1 bytes, never touches a file."""
    if acknowledge_fixture_only is not True:
        deny("explicit acknowledgement required for synthetic legacy migration")
    doc=_read_bytes(blob)
    replayed=_replay_legacy(doc,ctx)
    return encode_current(replayed,ctx)

def make_legacy_fixture(envelope:dict,ctx:tuple)->bytes:
    """Test-only legacy storage v0 fixture for verified, replayable states."""
    _check_envelope(envelope,ctx)
    doc={"format":LEGACY,"storage_version":0,
         "region":"UNOVA","campaign":"WHITE_BW","scope":SCOPE,
         "migration_gate":GATE,"state":copy.deepcopy(envelope["state"]),
         "events":[{key:copy.deepcopy(receipt[key])
                    for key in ("event_key","starter_choice","outcome")}
                   for receipt in envelope["event_receipts"]],
         "reward_intents":copy.deepcopy(envelope["reward_intents"])}
    # Do not create an un-migratable fixture in the first place.
    _replay_legacy(doc,ctx)
    encoded=_canonical(doc)
    if len(encoded)>LIMIT:deny("legacy fixture exceeds maximum")
    return encoded

def demo(ctx:tuple)->dict:
    c,r,policy,events,_=ctx
    env=ledger.initial(c)
    def apply(action,**kwargs):
        nonlocal env
        env=ledger.apply(env,c,r,policy,events,action,**kwargs)["envelope"]
    apply("begin")
    for event in events:
        kwargs={"event_key":event["key"]}
        if event["kind"]=="choice":kwargs["starter_choice"]="SNIVY"
        if event["battle_policy"] in ("ADVANCE_ON_LOSS","WIN_REQUIRED"):
            kwargs["outcome"]="WIN"
        apply("record_u07",**kwargs)
    apply("complete",chapter_key=c["chapters"][1]["key"],
          simulation_gate=machine.SIMULATION_GATE)
    apply("advance",chapter_key=c["chapters"][1]["key"])
    current=encode_current(env,ctx)
    loaded=decode_current(current,ctx)
    if loaded!=env:deny("v1 round-trip failed")
    legacy=make_legacy_fixture(env,ctx)
    migrated=migrate_legacy(legacy,ctx,acknowledge_fixture_only=True)
    if decode_current(migrated,ctx)!=env:deny("explicit legacy fixture migration failed")
    return {"phase":"G01.4","status":"OFFLINE_ROUNDTRIP_AND_EXPLICIT_MIGRATION_ONLY",
            "current_version":1,"synthetic_legacy_storage_version":0,
            "current_bytes":len(current),"migrated_bytes":len(migrated),
            "roundtrip_equal":True,"migration_equal":True,
            "events":len(env["event_receipts"]),
            "reward_tokens":len(env["reward_intents"]),
            "game_exe_tested":False,"native_save_modified":False,
            "native_items_granted":False,"can_install":False}

def main(argv:list[str]|None=None)->int:
    parser=argparse.ArgumentParser(description=__doc__)
    opts=parser.add_mutually_exclusive_group(required=True)
    opts.add_argument("--check",action="store_true")
    opts.add_argument("--simulate-demo",action="store_true")
    args=parser.parse_args(argv)
    try:
        ctx=load_project()
        report=(validate_policy(ctx[4],*ctx[:4])
                if args.check else demo(ctx))
        print(json.dumps(report,ensure_ascii=False,sort_keys=True))
        return 0
    except (OSError,ValueError,KeyError,TypeError,OverflowError,RecursionError) as exc:
        print("UNOVA_G01_4_BLOCKED: "+str(exc))
        return 2

if __name__=="__main__":
    raise SystemExit(main())
