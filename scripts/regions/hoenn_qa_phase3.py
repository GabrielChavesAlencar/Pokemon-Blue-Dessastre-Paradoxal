#!/usr/bin/env python3
"""Hoenn QA 03/12: merge pinned donor's ordinary encounter methods safely.

Donor PBS/RXDATA are read locally and verified via Source.read (git blob SHA-1).
No donor code is run, and no third-party assets/dialogue are committed.
Trainer/NPC/sign completeness remains a separately reported MANUAL backlog.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from server.ruby_marshal import RubyObject, loads, text

METHODS = ("Land", "Cave", "Water", "OldRod", "GoodRod", "SuperRod", "RockSmash")
METHOD_SET = frozenset(METHODS)
HEAD = re.compile(r"^\[\s*(\d+)(?:\s*,\s*(\d+))?\s*\]")
METHOD = re.compile(r"^([A-Za-z][A-Za-z0-9]*)(?:,(\d+))?$")
SPECIES = re.compile(r"^[A-Z][A-Z0-9_]*$")
ITEM_NAME = re.compile(r"^(?:Item|HiddenItem)(?:\b|$)", re.I)
ITEM_CALL = re.compile(r"\bpb(?:Hidden)?ItemBall\(\s*:([A-Z0-9_]+)\s*[,)]")
SIGN_NAME = re.compile(r"sign|notice|placa|board|trainer tips|signpost", re.I)
TRAINER_NAME = re.compile(
    r"\b(?:trainer|youngster|lass|bug ?catcher|hiker|fisherman|"
    r"swimmer|ace ?trainer|collector|psychic|hex ?maniac|"
    r"black ?belt|interviewer|cooltrainer|gentleman|expert|"
    r"tuber|bird ?keeper|aroma lady|camper|picnicker)\b", re.I)
TRAINER_SCRIPT = re.compile(r"\b(?:TrainerBattle\.start|pbTrainerBattle)\b")
UNSAFE_CONDITIONS = ("@switch1_valid", "@switch2_valid",
                     "@variable_valid", "@self_switch_valid",
                     "@item_valid", "@actor_valid")


def _weights(rows: list[tuple[int,str,int,int]]) -> tuple[list[tuple[int,str,int,int]], int]:
    """Normalize unusual 200%/95% donor defaults, preserving positive rare slots."""
    total = sum(row[0] for row in rows)
    if total <= 0 or len(rows) > 100:
        raise ValueError("Tabela de encontros sem chance válida")
    if total == 100:
        return rows, total
    # Give every explicitly selected species slot at least 1% and apply
    # largest remainders to the remaining 100 - N chances deterministically.
    remainder = 100 - len(rows)
    raw = [remainder * row[0] / total for row in rows]
    floors = [int(value) for value in raw]
    leftover = remainder - sum(floors)
    for index in sorted(range(len(rows)),
                        key=lambda i: (-(raw[i] - floors[i]), i))[:leftover]:
        floors[index] += 1
    adjusted = [(floors[i] + 1, species, low, high)
                for i, (_, species, low, high) in enumerate(rows)]
    if sum(row[0] for row in adjusted) != 100:
        raise AssertionError("Normalização de encontros não totalizou 100%")
    return adjusted, total


def parse_reference_encounters(source: str, allowed_maps: set[int]) -> tuple[dict,dict]:
    """Only default [MapID] sections. Swarm/alternate [MapID,version] are not activated."""
    result = {}
    alternate = []
    current = None
    method = None
    source_line = 0
    for line_no, raw in enumerate(source.lstrip("\ufeff").splitlines(),1):
        line = raw.split("#",1)[0].strip()
        if not line:
            continue
        header = HEAD.fullmatch(line)
        if header:
            mid = int(header.group(1))
            version = header.group(2)
            current = None
            method = None
            if mid not in allowed_maps:
                continue
            if version is not None:
                alternate.append({"source_map_id":mid,"version":int(version)})
                continue
            if mid in result:
                raise ValueError(f"PBS Hoenn contém [MapID] base repetido: {mid}")
            result[mid] = {}
            current = mid
            source_line = line_no
            continue
        if current is None:
            continue
        fields = line.split(",")
        if fields[0].isdecimal():
            if method is None:
                raise ValueError(f"Slot de encontro sem método: mapa {current}, linha {line_no}")
            if len(fields) not in (3, 4):
                raise ValueError(f"Slot de encontro inválido: mapa {current}, linha {line_no}")
            weight = int(fields[0])
            species = fields[1].strip().upper()
            if not SPECIES.fullmatch(species):
                raise ValueError(f"Espécie inválida no PBS: mapa {current}, linha {line_no}")
            try:
                low = int(fields[2])
                high = int(fields[3]) if len(fields)==4 else low
            except ValueError as error:
                raise ValueError(f"Níveis inválidos no PBS: mapa {current}, linha {line_no}") from error
            if not (weight > 0 and 1 <= low <= high <= 100):
                raise ValueError(f"Chance ou nível fora dos limites: mapa {current}, linha {line_no}")
            result[current][method]["rows"].append((weight,species,low,high))
        else:
            match = METHOD.fullmatch(line)
            if not match or match.group(1) not in METHOD_SET:
                raise ValueError(f"Método de encontro não aceito: mapa {current}, linha {line_no}: {line}")
            method = match.group(1)
            rate = match.group(2)
            if method in result[current]:
                raise ValueError(f"Método duplicado: mapa {current}, {method}")
            if rate is not None and not (1 <= int(rate) <= 255):
                raise ValueError(f"Frequência de encontro inválida: {current}/{method}")
            result[current][method] = {"rate":int(rate) if rate is not None else None,
                                       "rows":[],"line":line_no}
    normalized = []
    for mid, methods in result.items():
        for kind, entry in methods.items():
            if not entry["rows"]:
                raise ValueError(f"Tabela de encontro vazia: {mid}/{kind}")
            before = entry["rows"]
            after, total = _weights(before)
            entry["rows"] = after
            if total != 100:
                normalized.append({"map_id":mid,"method":kind,
                                   "source_total":total,"normalized_total":100})
    return result, {"source_default_maps":len(result),
                    "alternate_profiles_not_activated":alternate,
                    "normalized_weights":normalized,
                    "special_encounter_events_not_activated":True}


def _authored_method(rows: tuple, rate: int) -> dict:
    parsed=[]
    for weight,species,low,high in rows:
        if not (isinstance(weight,int) and weight>0 and
                SPECIES.fullmatch(species) and
                1 <= low <= high <= 100):
            raise ValueError("Preset autoral de encontros Hoenn inválido")
        parsed.append((weight,species,low,high))
    if sum(item[0] for item in parsed)!=100:
        raise ValueError("Preset autoral Hoenn não soma 100%")
    return {"rate":rate,"rows":parsed,"from":"original_blue_preset"}


def assemble_encounters(reference: dict, mapping: dict[int,int],
                        authored_land: dict, authored_cave: dict) -> tuple[bytes,dict]:
    """One [remapped ID] per map, never duplicate Land/Cave or change existing rates."""
    if len(set(mapping.values())) != len(mapping):
        raise ValueError("MapID de saída duplicado em encontros Hoenn")
    profiles={mid:{} for mid in mapping}
    for kind,authored in (("Land",authored_land),("Cave",authored_cave)):
        for mid,rows in authored.items():
            if mid not in profiles:
                raise ValueError(f"Preset Hoenn fora do piloto: {mid}")
            profiles[mid][kind]=_authored_method(rows,21 if mid==101 and kind=="Land"
                                                else 11 if kind=="Land" else 5)
    authored_count = sum(len(v) for v in profiles.values())
    added = Counter()
    additional_maps=set()
    for mid,methods in reference.items():
        if mid not in profiles:
            continue
        for kind,definition in methods.items():
            if kind in profiles[mid]:
                continue   # Blue-authored Land/Cave always have precedence.
            profiles[mid][kind]={**definition,"from":"pinned_donor_default"}
            added[kind]+=1
            additional_maps.add(mid)
    sections=[]
    coverage={}
    for mid in mapping:   # preserve the same map ordering as the pilot.
        kinds=profiles[mid]
        if not kinds:
            continue
        sections.append(f"[{mapping[mid]}]\n")
        coverage[str(mid)]={}
        for kind in METHODS:
            if kind not in kinds:
                continue
            data=kinds[kind]
            marker = kind + (f",{data['rate']}" if data["rate"] is not None else "")
            sections.append(marker+"\n")
            sections.extend(
                f"    {chance},{species},{low},{high}\n"
                for chance,species,low,high in data["rows"]
            )
            coverage[str(mid)][kind] = {"source":data["from"],
                                        "slots":len(data["rows"]),
                                        "weight_total":sum(row[0] for row in data["rows"])}
    return "".join(sections).encode("ascii"), {
        "authored_method_profiles_preserved":authored_count,
        "new_default_profiles_installed":sum(added.values()),
        "added_by_method":dict(sorted(added.items())),
        "maps_with_new_profiles":len(additional_maps),
        "maps_with_any_encounters":sum(bool(kinds) for kinds in profiles.values()),
        "methods_by_source_map":coverage,
        "old_pbs_overwritten_in_main_game":False,
        "runtime_encounters_tested":False,
    }


def _safe_events(original_events: dict, source_maps: dict,
                 authored_maps: dict, add_event, event_page, command, ruby) -> dict:
    """Adds only unconditional Item/HiddenItem sources not already authored.

    Maintains source map original ids; does not copy donor commands or NPC text.
    All other source signs, people and trainer scripts are *review candidates*.
    """
    stats=Counter()
    backlog=[]
    inserted=[]
    for mid,events in original_events.items():
        authored=authored_maps[mid]
        occupied={(ev.attrs["@x"],ev.attrs["@y"]) for ev in authored.attrs["@events"].values()}
        size=source_maps[mid].attrs
        for ev in events.values():
            name=text(ev.attrs.get("@name",b""))
            x,y=ev.attrs.get("@x"),ev.attrs.get("@y")
            if not (isinstance(x,int) and isinstance(y,int) and
                    0<=x<size["@width"] and 0<=y<size["@height"]):
                stats["donor_event_out_of_bounds"]+=1
                continue
            pages=ev.attrs.get("@pages",[])
            statements=[]
            for page in pages:
                for cmd in page.attrs.get("@list",[]):
                    if isinstance(cmd,RubyObject) and cmd.name=="RPG::EventCommand":
                        if cmd.attrs.get("@code") in (355,655):
                            statements.extend(text(v) for v in cmd.attrs.get("@parameters",[])
                                              if isinstance(v,(bytes,str)))
            scripting=" ".join(statements)
            potential = None
            if ITEM_NAME.match(name):
                potential="item"
            elif TRAINER_NAME.search(name) or TRAINER_SCRIPT.search(scripting):
                potential="trainer"
            elif SIGN_NAME.search(name):
                potential="sign"
            elif any(
                isinstance(cmd,RubyObject) and cmd.attrs.get("@code") in (101,401)
                for page in pages for cmd in page.attrs.get("@list",[])
            ):
                potential="npc_or_dialog"
            if not potential:
                continue
            stats["source_"+potential]+=1
            if (x,y) in occupied:
                stats["position_already_authored"]+=1
                continue
            if potential=="item":
                identities=set(ITEM_CALL.findall(scripting))
                if len(identities)!=1 or not pages:
                    stats["items_need_manual_review"]+=1
                    backlog.append([mid,x,y,"item","conditional_or_unrecognized"])
                    continue
                first_cond=pages[0].attrs.get("@condition")
                if first_cond is None or any(first_cond.attrs.get(k,False) for k in UNSAFE_CONDITIONS):
                    stats["items_need_manual_review"]+=1
                    backlog.append([mid,x,y,"item","conditional"])
                    continue
                item=next(iter(identities))
                if not SPECIES.fullmatch(item):
                    stats["items_need_manual_review"]+=1
                    backlog.append([mid,x,y,"item","invalid_item_id"])
                    continue
                # Never shadow a trainer/door/story anchor; occupied check above.
                key=f"QA3_{mid}_{x}_{y}"
                page=event_page(script="nil",sprite="Object_Ball" if name.lower()=="item" else "")
                eid=add_event(authored,f"HN_QA3_Pickup_{mid}_{x}_{y}",x,y,page)
                page.attrs["@list"][0]=command(
                    355,f'BlueHoennPilot.pickup(:{item},"{key}",{eid})'.encode("ascii"))
                cleared=event_page(script="nil")
                cleared.attrs["@condition"].attrs["@self_switch_valid"]=True
                cleared.attrs["@condition"].attrs["@self_switch_ch"]=b"A"
                cleared.attrs["@through"]=True
                cleared.attrs["@list"]=[command(0)]
                authored.attrs["@events"][eid].attrs["@pages"].append(cleared)
                occupied.add((x,y))
                stats["source_items_newly_authored"]+=1
                inserted.append([mid,x,y,item])
                continue
            stats["pending_"+potential]+=1
            backlog.append([mid,x,y,potential,"source_event_not_copied"])
    return {
        "source_event_counts":dict(sorted(stats.items())),
        "new_item_positions":inserted,
        "unimplemented_source_event_candidates":backlog,
        "candidate_classifier_not_exhaustive":True,
        "source_dialogue_or_scripts_executed":False,
        "trainer_npc_sign_cleared_for_playable":False,
    }


def reauthor_safe_items_and_audit(original_events: dict, source_maps: dict,
                                  authored_maps: dict) -> dict:
    # Late imports avoid import cycles: pilot_hoenn imports this module.
    from build_johto_events import event_page,command,ruby
    from pilot_hoenn import append_event
    return _safe_events(original_events,source_maps,authored_maps,
                        append_event,event_page,command,ruby)


def parse_compiled_encounters(body: str, allowed_ids: set[int]) -> dict:
    """QA3 read-only validator: one map/method block, valid slots and sums 100."""
    profiles = {}
    mid=None
    method=None
    for ln,line in enumerate(body.lstrip("\ufeff").splitlines(),1):
        row=line.split("#",1)[0].strip()
        if not row:
            continue
        h=HEAD.fullmatch(row)
        if h:
            mid=int(h.group(1))
            if h.group(2) is not None or mid not in allowed_ids or mid in profiles:
                raise ValueError(f"PBS Hoenn tem mapa inválido/repetido: linha {ln}")
            profiles[mid]={}
            method=None
            continue
        if mid is None:
            raise ValueError(f"PBS sem [MapID] na linha {ln}")
        parts=row.split(",")
        if parts[0].isdecimal():
            if method is None or len(parts)!=4:
                raise ValueError(f"Slot PBS sem método válido na linha {ln}")
            weight=int(parts[0])
            species=parts[1]
            if (weight<1 or not SPECIES.fullmatch(species) or
                not parts[2].isdecimal() or not parts[3].isdecimal() or
                not 1 <= int(parts[2]) <= int(parts[3]) <= 100):
                raise ValueError(f"Encontro PBS Hoenn inválido: linha {ln}")
            profiles[mid][method]["rows"].append(weight)
        else:
            k=parts[0]
            if k not in METHOD_SET or k in profiles[mid] or len(parts)>2:
                raise ValueError(f"Método PBS Hoenn duplicado/desconhecido: linha {ln}")
            if len(parts)==2 and (not parts[1].isdecimal() or
                                   not 1<=int(parts[1])<=255):
                raise ValueError(f"Frequência PBS inválida na linha {ln}")
            profiles[mid][k]={"rows":[]}
            method=k
    for mapid,methods in profiles.items():
        for kind,record in methods.items():
            if sum(record["rows"])!=100:
                raise ValueError(f"Distribuição PBS incorreta: {mapid}/{kind}")
    return {mapid:{kind:len(profile["rows"]) for kind,profile in methods.items()}
            for mapid,methods in profiles.items()}


def verify_copy(copy: Path) -> dict:
    """Called after the stage 1 + stage 2 audits; no native gameplay claim."""
    from hoenn_qa_phase1 import require_private_path
    copy=require_private_path(copy)
    report=json.loads((copy/"Hoenn pilot.json").read_text("utf-8"))
    q=report.get("qa3")
    if not isinstance(q,dict) or not q.get("method_imports"):
        raise ValueError("Cópia anterior à Fase 3: reconstrua em pasta NOVA, preserve saves antigos")
    mapping=report.get("maps",{})
    if len(mapping)!=199 or len(set(mapping.values()))!=199:
        raise ValueError("Remapeamento de 199 mapas não corresponde ao piloto")
    entries=parse_compiled_encounters(
        (copy/"PBS/encounters_hoenn_pilot.txt").read_text("utf-8-sig"),
        set(mapping.values()))
    actual={str(mid):set(kinds) for mid,kinds in entries.items()}
    announced={str(mapping[mid]):set(kinds) for mid,kinds in
               q["method_imports"]["methods_by_source_map"].items()}
    if actual!=announced:
        raise ValueError("PBS real não corresponde ao manifesto de encontros da Fase 3")
    if not q.get("source_events") or q["source_events"].get("source_dialogue_or_scripts_executed") is not False:
        raise ValueError("Relatório de cobertura dos NPCs/itens incompleto")
    return {
        "schema":1,"region":"HOENN","qa_phase":"03/12",
        "status":"SOURCE_ENCOUNTERS_MERGED_STATICALLY",
        "mapped_locations":len(mapping),"encountered_locations":len(entries),
        "new_donor_method_profiles":q["method_imports"]["new_default_profiles_installed"],
        "methods_added_by_type":q["method_imports"]["added_by_method"],
        "normalized_reference_profiles":q["reference"]["normalized_weights"],
        "swarm_profiles_intentionally_not_activated":len(q["reference"]["alternate_profiles_not_activated"]),
        "new_pinned_item_events":q["source_events"]["source_event_counts"].get("source_items_newly_authored",0),
        "unresolved_trainer_npc_sign_candidates":len(q["source_events"]["unimplemented_source_event_candidates"]),
        "event_inventory_complete":False,"native_game_exe_approved":False,
        "gameplay_accepted":False,"android_tested":False,
    }


def main(argv: list[str] | None = None) -> int:
    from hoenn_qa_phase1 import ROOT,WORK,require_private_path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy",type=Path,default=WORK/"hoenn-qa-fase03")
    parser.add_argument("--report",type=Path,default=WORK/"hoenn-qa-fase03-report.json")
    args=parser.parse_args(argv)
    report_path=None
    try:
        report_path=require_private_path(args.report)
        result=verify_copy(args.copy)
        status=0
    except (OSError,ValueError,KeyError,TypeError,IndexError,json.JSONDecodeError) as error:
        result={"schema":1,"region":"HOENN","qa_phase":"03/12",
                "status":"BLOCKED","native_game_exe_approved":False,
                "errors":[str(error)]}
        status=2
    if report_path:
        report_path.parent.mkdir(parents=True,exist_ok=True)
        report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                               encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return status


if __name__=="__main__":
    raise SystemExit(main())
