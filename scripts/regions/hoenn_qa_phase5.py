#!/usr/bin/env python3
"""Hoenn QA05 — verify Aqua/Magma story anchors and Seafloor campaign gates.

Works only on a separately generated private Hoenn pilot. Donor events are
inspected as data; never import, execute or redistribute third-party scripts.
A passing STATIC report is not native Game.exe playable acceptance.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from server.ruby_marshal import RubyObject, loads, text
from hoenn_stage9 import (
    PYRE_AQUA_GRUNTS, MAGMA_HIDEOUT_GRUNTS,
    AQUA_HIDEOUT_GRUNTS, SPACE_GRUNT_EVENTS,
)

# Source IDs (not the remapped native Blue IDs), verified by earlier stages.
STORY_EVENTS = (
    (213,22,11,"HN9_Story_PyreOrb","BlueHoennPilot.pyre_orb_scene",1),
    (213,23,9,"HN9_Story_PyreElder","BlueHoennPilot.pyre_elder",0),
    (189,21,19,"HN9_Story_Groudon","BlueHoennPilot.groudon_hideout",1),
    (189,21,23,"HN9_Boss_Maxie","BlueHoennPilot.magma_hideout_maxie",0),
    (217,25,21,"HN9_Boss_Matt","BlueHoennPilot.aqua_hideout_matt",0),
    (217,19,22,"HN9_Story_Submarine","BlueHoennPilot.submarine_escape",1),
    (81,27,10,"HN9_Boss_SpaceSteven","BlueHoennPilot.space_center_steven",0),
    (236,14,46,"HN10_Boss_Archie","BlueHoennPilot.seafloor_archie",0),
    (236,23,46,"HN10_Story_Kyogre","BlueHoennPilot.seafloor_awakening",1),
)
STORY_KEYS = (
    "groudon_awakened", "slateport_submarine_stolen",
    "submarine_escaped", "space_center_saved", "hm_dive_received",
)
SOURCE_SCOPE = frozenset((69,81,83,180,182,183,184,185,186,187,188,189,
                         206,212,213,215,216,217,*range(227,237)))
KEYWORDS = re.compile(
    r"aqua|magma|grunt|submarine|groudon|kyogre|archie|"
    r"maxie|tabitha|matt|cavern|emblem|orb|boss|crisis",
    re.I,
)
BOSS_PBS = (
    "[BLUE_HOENN_MAXIE,Maxie,989]",
    "[BLUE_HOENN_TABITHA,Tabitha,988]",
    "[BLUE_HOENN_MATT,Matt,917]",
    "[BLUE_HOENN_ARCHIE,Archie,1026]",
)

GRUNT_GROUPS = (
    ("pyre_aqua_grunt",PYRE_AQUA_GRUNTS),
    ("magma_hideout_grunt",MAGMA_HIDEOUT_GRUNTS),
    ("aqua_hideout_grunt",AQUA_HIDEOUT_GRUNTS),
    ("space_magma_grunt",SPACE_GRUNT_EVENTS),
)


def _native_events(map_obj: RubyObject, mid: int) -> dict:
    if not isinstance(map_obj,RubyObject) or map_obj.name!="RPG::Map":
        raise ValueError(f"Map{mid}: RXDATA não é RPG::Map")
    events=map_obj.attrs.get("@events")
    if not isinstance(events,dict):
        raise ValueError(f"Map{mid}: sem eventos RXDATA")
    return events


def _event_handler(event: RubyObject) -> str:
    scripts=[]
    for page in event.attrs.get("@pages",[]):
        for cmd in page.attrs.get("@list",[]):
            if isinstance(cmd,RubyObject) and cmd.attrs.get("@code") in (355,655):
                scripts.extend(text(p) for p in cmd.attrs.get("@parameters",[])
                               if isinstance(p,(bytes,str)))
    return "\n".join(scripts)


def required_event(map_obj: RubyObject,mid:int,x:int,y:int,
                   event_name:str,script:str,trigger:int) -> None:
    matches=[ev for ev in _native_events(map_obj,mid).values()
             if text(ev.attrs.get("@name",b""))==event_name]
    if len(matches)!=1:
        raise ValueError(f"Map{mid}: cena {event_name} ausente ou duplicada")
    ev=matches[0]
    if (ev.attrs.get("@x"),ev.attrs.get("@y"))!=(x,y):
        raise ValueError(f"Map{mid}: cena {event_name} fora da âncora {x}/{y}")
    pages=ev.attrs.get("@pages",[])
    if len(pages)!=1:
        raise ValueError(f"Map{mid}: cena {event_name} com páginas inesperadas")
    if pages[0].attrs.get("@trigger")!=trigger:
        raise ValueError(f"Map{mid}: trigger incorreto em {event_name}")
    if trigger==1 and pages[0].attrs.get("@through") is not True:
        raise ValueError(f"Map{mid}: trigger automático não atravessável em {event_name}")
    if _event_handler(ev).strip()!=script:
        raise ValueError(f"Map{mid}: script de {event_name} divergente")


def verify_story_events(maps:dict[int,RubyObject]) -> dict:
    for mid,x,y,name,handler,trigger in STORY_EVENTS:
        if mid not in maps:
            raise ValueError(f"Map{mid}: mapa de história ausente")
        required_event(maps[mid],mid,x,y,name,handler,trigger)
    grunts=Counter()
    for handler,group in GRUNT_GROUPS:
        for mid,x,y,version,_team in group:
            required_event(
                maps[mid],mid,x,y,f"HN9_Grunt_{version}",
                f"BlueHoennPilot.{handler}({version})",0,
            )
            grunts[handler]+=1
    return {
        "verified_story_events":len(STORY_EVENTS),
        "verified_grunt_event_bindings":sum(grunts.values()),
        "verified_grunts_by_group":dict(sorted(grunts.items())),
        "groudon_auto_player_touch":True,
        "kyogre_auto_player_touch":True,
        "trainer_team_scaling_owned_by_blue":True,
        "native_encounters_approved":False,
        "source_script_event_handlers_copied":False,
    }


def inventory_source(events_by_map: dict[int,dict]) -> dict:
    """Candidate counts only: source NPC/scripts never copied into pilot."""
    found=[]
    counts=Counter()
    for mid in sorted(set(events_by_map)&SOURCE_SCOPE):
        for ev in events_by_map[mid].values():
            name=text(ev.attrs.get("@name",b""))
            if not KEYWORDS.search(name):
                continue
            counts[str(mid)]+=1
            found.append({
                "source_map_id":mid,
                "x":ev.attrs.get("@x"),"y":ev.attrs.get("@y"),
                "source_event_name":name[:90],
                "pages":len(ev.attrs.get("@pages",[])),
            })
    return {
        "source_story_candidates":found,
        "source_candidate_count_by_map":dict(sorted(counts.items(),key=lambda p:int(p[0]))),
        "events_have_not_been_assumed_functional":True,
        "source_dialogues_or_scripts_redistributed":False,
    }


def audit_generated(maps:dict[int,RubyObject], donor_events:dict) -> dict:
    status=verify_story_events(maps)
    status.update(inventory_source(donor_events))
    status.update({
        "story_prerequisites":list(STORY_KEYS),
        "seafloor_source_interior_maps":list(range(227,237)),
        "game_exe_tested":False,"story_accepted":False,
        "seafloor_puzzles_native_approved":False,
    })
    return status


def verify_copy(copy:Path) -> dict:
    from hoenn_qa_phase1 import require_private_path
    copy=require_private_path(copy)
    report=json.loads((copy/"Hoenn pilot.json").read_text("utf-8"))
    qa5=report.get("qa5")
    maps=report.get("maps",{})
    if (report.get("region")!="HOENN" or
            report.get("kind")!="ISOLATED_HOENN_TEST" or
            report.get("save_profile") not in ("Hoenn QA Fase05","Hoenn QA Fase06","Hoenn QA Fase07","Hoenn QA Fase08","Hoenn QA Fase09") or
            not isinstance(maps,dict) or len(maps)!=199):
        raise ValueError("Não é a cópia isolada de Hoenn QA05 com 199 mapas e save próprio")
    if (not isinstance(qa5,dict) or
            qa5.get("story_prerequisites")!=list(STORY_KEYS) or
            qa5.get("game_exe_tested") is not False or
            qa5.get("source_dialogues_or_scripts_redistributed") is not False):
        raise ValueError("Manifesto QA05 ausente, divergente ou reivindica aprovação indevida")
    actual_maps={}
    mids={mid for mid,*_ in STORY_EVENTS}
    for _handler,group in GRUNT_GROUPS:
        mids.update(row[0] for row in group)
    for mid in mids:
        actual_maps[mid]=loads((copy/f"Data/Map{maps[str(mid)]:03}.rxdata").read_bytes())
    physical=verify_story_events(actual_maps)
    if (physical["verified_story_events"]!=qa5.get("verified_story_events") or
            physical["verified_grunt_event_bindings"]!=qa5.get("verified_grunt_event_bindings")):
        raise ValueError("RXDATA de Hoenn diverge do manifesto QA05")
    trainer_text=(copy/"PBS/trainers_hoenn_pilot.txt").read_text("utf-8-sig")
    missing=[name for name in BOSS_PBS if name not in trainer_text]
    if missing:
        raise ValueError(f"Equipes PBS essenciais Aqua/Magma/Seafloor ausentes: {missing}")
    return {
        "schema":1,"region":"HOENN","qa_phase":"05/12",
        "status":"STORY_ANCHORS_STATICALLY_VERIFIED",
        "source_interior_maps":len(range(227,237)),
        "story_events":physical["verified_story_events"],
        "grunt_bindings":physical["verified_grunt_event_bindings"],
        "story_prerequisites":list(STORY_KEYS),
        "source_event_candidate_count":len(qa5.get("source_story_candidates",[])),
        "source_scripts_executed":False,
        "native_game_exe_approved":False,
        "seafloor_puzzles_native_approved":False,
        "aqua_magma_campaign_fully_playable":False,
    }


def main(argv:list[str]|None=None)->int:
    from hoenn_qa_phase1 import WORK,require_private_path
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--copy",type=Path,default=WORK/"hoenn-qa-fase05")
    p.add_argument("--report",type=Path,default=WORK/"hoenn-qa-fase05-report.json")
    args=p.parse_args(argv)
    path=None
    try:
        path=require_private_path(args.report)
        result=verify_copy(args.copy)
        status=0
    except (OSError,ValueError,TypeError,KeyError,IndexError,json.JSONDecodeError) as err:
        status=2
        result={"schema":1,"region":"HOENN","qa_phase":"05/12",
                "status":"BLOCKED","native_game_exe_approved":False,"errors":[str(err)]}
    if path is not None:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return status


if __name__=="__main__":
    raise SystemExit(main())
