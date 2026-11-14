#!/usr/bin/env python3
"""Hoenn QA 04/12: conservative pinned field-obstacle inventory + native copy audit.

Only exact, unambiguous obstacle names are candidates for reauthoring. Never
execute or copy donor event scripts. No claim that game field movement is proven.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from server.ruby_marshal import RubyObject, text, loads

REGIONAL_BADGES = {
    "CUT": "STONE", "FLASH": "KNUCKLE", "ROCKSMASH": "DYNAMO",
    "STRENGTH": "HEAT", "SURF": "BALANCE",
    "DIVE": "MIND", "WATERFALL": "RAIN",
}
# Source MapID in the fixed donor, not the remapped native Blue map number.
UNDERWATER = frozenset((255,258,259,260,261,262,263,266))
SEAFLOOR_CAVERN = frozenset(range(227,237))
WATERFALL_ENTRANCE = (91,322)
OBSTACLE_ROCK = re.compile(
    r"^(?:Rock[\s_-]*Smash(?:[\s_-]*Rock)?|Smashable[\s_-]*Rock|"
    r"Breakable[\s_-]*Rock|RockSmashRock)$", re.I)
OBSTACLE_BOULDER = re.compile(
    r"^(?:Strength[\s_-]*Boulder|Pushable[\s_-]*(?:Rock|Boulder)|"
    r"Strength[\s_-]*Rock|Boulder[\s_-]*Strength)$", re.I)
OBSTACLE_ICE = re.compile(
    r"^(?:Ice[\s_-]*(?:Floor(?:[\s_-]*Puzzle)?|Puzzle|Tile|Cracked)|"
    r"Thin[\s_-]*Ice|Cracked[\s_-]*Ice|Sliding[\s_-]*Ice)$", re.I)
FIELD_SCRIPT = re.compile(
    r"\b(?:pbRockSmash|pbStrength|pbWaterfall|pbDive|pbSurf)\b")
FIELD_SCRIPT_OBSTACLE = {
    "pbRockSmash": "rock_smash",
    "pbStrength": "strength",
    "pbWaterfall": "waterfall",
    "pbDive": "dive",
    "pbSurf": "surf",
}
GENERIC_NAMES = re.compile(
    r"\b(?:waterfall|diving?|surf(?:ing)?|"
    r"strength|rock[\s_-]*smash|boulder|rock|ice)\b", re.I)
NATIVE_ROCK_SPRITES = (
    "Object_Rock", "Object_RockSmash", "Object_BreakableRock",
    "Object_SmashableRock", "Object_Boulder",
)
NATIVE_BOULDER_SPRITES = (
    "Object_Boulder", "Object_StrengthBoulder",
    "Object_StrengthRock", "Object_Rock",
)


def classify_obstacle(name: str, script: str = "") -> str | None:
    """Report probable obstacle category without claiming native semantics."""
    name = name.strip()
    if OBSTACLE_ROCK.fullmatch(name):
        return "rock_smash"
    if OBSTACLE_BOULDER.fullmatch(name):
        return "strength"
    if OBSTACLE_ICE.fullmatch(name):
        return "ice"
    for call, kind in FIELD_SCRIPT_OBSTACLE.items():
        if re.search(r"\b"+re.escape(call)+r"\s*(?:\(|$)",script):
            return kind
    if GENERIC_NAMES.search(name):
        return "manual_field_review"
    return None


def categorize_source_events(events_by_map: dict, source_maps: dict) -> dict:
    """Safe read-only summary: all candidates, no source dialog/script bytes."""
    report=[]
    counts=Counter()
    for old, events in events_by_map.items():
        world=source_maps[old]
        width,height=world.attrs["@width"],world.attrs["@height"]
        for event in events.values():
            if not isinstance(event,RubyObject) or event.name!="RPG::Event":
                continue
            name=text(event.attrs.get("@name",b""))
            x,y=event.attrs.get("@x"),event.attrs.get("@y")
            if not (isinstance(x,int) and isinstance(y,int) and
                    0<=x<width and 0<=y<height):
                counts["source_invalid_coordinate"]+=1
                continue
            pages=event.attrs.get("@pages",[])
            lines=[]
            for page in pages:
                for cmd in page.attrs.get("@list",[]):
                    if isinstance(cmd,RubyObject) and cmd.attrs.get("@code") in (355,655):
                        lines.extend(text(v) for v in cmd.attrs.get("@parameters",[])
                                     if isinstance(v,(bytes,str)))
            kind=classify_obstacle(name,"\n".join(lines))
            if kind is None:
                continue
            counts[kind]+=1
            report.append({
                "source_map_id":old,"x":x,"y":y,
                "kind":kind, "source_pages":len(pages),
                "original_event_name":name[:100],
                "has_source_script":bool(lines),
            })
    report.sort(key=lambda x:(x["source_map_id"],x["x"],x["y"],x["kind"]))
    return {"source_obstacles_by_type":dict(sorted(counts.items())),
            "source_obstacle_candidates":report,
            "ice_puzzle_tile_flags_untested":True,
            "native_field_move_handlers_untested":True,
            "source_ruby_scripts_executed":False}


def _safe_obstacle_name(name: str,kind: str) -> bool:
    # Do not infer a safe, unconditional wall from a script alone.
    return bool((kind=="rock_smash" and OBSTACLE_ROCK.fullmatch(name)) or
                (kind=="strength" and OBSTACLE_BOULDER.fullmatch(name)))


def install_simple_obstacles(events_by_map: dict, donor_maps: dict,
                             target_maps: dict, game: Path,
                             source=None, overlay: dict | None = None) -> dict:
    """Reauthor exact named rocks only if a compatible native sprite exists.

    Source RXDATA scripts/conditions are not copied or evaluated.
    Strength boulders must be pushed by the player's facing direction; they
    do not disappear permanently, and require engine validation.
    """
    from build_johto_events import command, event_page
    from pilot_hoenn import append_event

    summary=categorize_source_events(events_by_map,donor_maps)
    counts=Counter()
    installed=[]
    skipped=[]
    for entry in summary["source_obstacle_candidates"]:
        mid,x,y=entry["source_map_id"],entry["x"],entry["y"]
        kind=entry["kind"]
        name=entry["original_event_name"]
        if kind not in ("rock_smash","strength"):
            skipped.append([mid,x,y,kind,"manual_or_other_field_move"])
            continue
        if not _safe_obstacle_name(name,kind):
            skipped.append([mid,x,y,kind,"not_exact_obstacle_name"])
            continue
        original=[v for v in events_by_map[mid].values()
                  if v.attrs.get("@x")==x and v.attrs.get("@y")==y and
                     text(v.attrs.get("@name",b""))==name]
        if len(original)!=1 or len(original[0].attrs.get("@pages",[]))!=1:
            skipped.append([mid,x,y,kind,"ambiguous_or_multipage"])
            continue
        page_orig=original[0].attrs["@pages"][0]
        condition=page_orig.attrs.get("@condition")
        if condition is None or any(condition.attrs.get(flag,False) for flag in (
           "@switch1_valid","@switch2_valid","@variable_valid",
           "@self_switch_valid","@item_valid","@actor_valid")):
            skipped.append([mid,x,y,kind,"conditional_original"])
            continue
        if any(ev.attrs["@x"]==x and ev.attrs["@y"]==y
               for ev in target_maps[mid].attrs["@events"].values()):
            skipped.append([mid,x,y,kind,"already_authored"])
            continue
        choices = (NATIVE_ROCK_SPRITES if kind=="rock_smash" else NATIVE_BOULDER_SPRITES)
        sprite=next((n for n in choices
                     if (game/f"Graphics/Characters/{n}.png").is_file() and
                     not (game/f"Graphics/Characters/{n}.png").is_symlink()),None)
        if sprite is None and source is not None and overlay is not None:
            # The pinned character graphic may be used ONLY inside the
            # isolated local Blue copy. Source.read verifies its Git blob hash.
            # No third-party character image is added to public Git history.
            original_graphic=page_orig.attrs.get("@graphic")
            original_name=text(original_graphic.attrs.get("@character_name",b"")) if original_graphic else ""
            if re.fullmatch(r"[A-Za-z0-9_ ()-]+",original_name):
                rel=f"Graphics/Characters/{original_name}.png"
                try:
                    blob=source.read(rel)
                except (OSError,FileNotFoundError):
                    # Missing optional graphics are reported; a Git SHA mismatch
                    # is fatal and must not be downgraded to a silent fallback.
                    blob=b""
                if blob.startswith(b"\x89PNG\r\n\x1a\n"):
                    sprite="BLUE_HOENN_QA4_"+original_name
                    target=f"Graphics/Characters/{sprite}.png"
                    if (game/target).exists() or (target in overlay and overlay[target]!=blob):
                        skipped.append([mid,x,y,kind,"sprite_name_collision"])
                        continue
                    if target not in overlay:
                        counts["private_pinned_sprite_assets"]+=1
                    overlay[target]=blob
        if sprite is None:
            skipped.append([mid,x,y,kind,"no_native_or_pinned_sprite"])
            continue
        page=event_page(script="nil",sprite=sprite)
        script=("BlueHoennPilot.rock_smash_obstacle({event})"
                if kind=="rock_smash" else
                "BlueHoennPilot.strength_boulder({event})")
        new_id=append_event(target_maps[mid],f"HN_QA4_{kind}_{mid}_{x}_{y}",x,y,page)
        page.attrs["@through"]=False
        page.attrs["@list"][0]=command(355,script.format(event=new_id).encode("ascii"))
        if kind=="rock_smash":
            clear=event_page(script="nil")
            clear.attrs["@condition"].attrs["@self_switch_valid"]=True
            clear.attrs["@condition"].attrs["@self_switch_ch"]=b"A"
            clear.attrs["@through"]=True
            clear.attrs["@list"]=[command(0)]
            target_maps[mid].attrs["@events"][new_id].attrs["@pages"].append(clear)
        installed.append([mid,x,y,kind,sprite,new_id])
        counts[kind]+=1
    return {
        **summary,
        "new_safe_obstacles":installed,
        "new_safe_obstacles_by_type":dict(counts),
        "source_obstacles_needing_review":skipped,
        "strength_boulder_move_route_native_test_pending":True,
        "rock_smash_animation_native_test_pending":True,
    }


def verify_copy(copy: Path) -> dict:
    from hoenn_qa_phase1 import require_private_path
    copy=require_private_path(copy)
    report=json.loads((copy/"Hoenn pilot.json").read_text("utf-8"))
    if report.get("kind")!="ISOLATED_HOENN_TEST" or len(report.get("maps",{}))!=199:
        raise ValueError("Piloto privado não possui 199 mapas Hoenn")
    qa4=report.get("qa4")
    if not isinstance(qa4,dict) or not isinstance(qa4.get("source_obstacles_by_type"),dict):
        raise ValueError("Piloto anterior à Fase4; recrie cópia NOVA para preservar os saves anteriores")
    if qa4.get("native_field_move_handlers_untested") is not True:
        raise ValueError("Relatório QA4 reivindica comprovação nativa inexistente")
    if not isinstance(qa4.get("new_safe_obstacles"),list):
        raise ValueError("Relatório QA4 não contém obstáculos novos")
    if qa4.get("source_ruby_scripts_executed") is not False:
        raise ValueError("A cópia não pode executar código doador")
    return {
        "schema":1,"region":"HOENN","phase":"04/12",
        "status":"FIELD_OBSTACLE_CONTRACT_PREPARED",
        "mapped_maps":199,
        "source_obstacle_candidates":len(qa4["source_obstacle_candidates"]),
        "new_scripted_obstacles":len(qa4["new_safe_obstacles"]),
        "remaining_field_obstacle_candidates":len(qa4["source_obstacles_needing_review"]),
        "source_obstacles_by_type":qa4["source_obstacles_by_type"],
        "badge_gates":REGIONAL_BADGES,
        "waterfall_ever_grande_gate":list(WATERFALL_ENTRANCE),
        "underwater_ids":sorted(UNDERWATER),
        "game_exe_tested":False,"native_field_moves_approved":False,
        "puzzles_and_ice_floor_approved":False,
        "android_tested":False,
    }


def main(argv: list[str] | None = None) -> int:
    from hoenn_qa_phase1 import WORK, require_private_path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy",type=Path,default=WORK/"hoenn-qa-fase04")
    parser.add_argument("--report",type=Path,default=WORK/"hoenn-qa-fase04-report.json")
    args=parser.parse_args(argv)
    path=None
    try:
        path=require_private_path(args.report)
        result=verify_copy(args.copy)
        status=0
    except (OSError,ValueError,KeyError,TypeError,IndexError,json.JSONDecodeError) as error:
        status=2
        result={"schema":1,"region":"HOENN","phase":"04/12",
                "status":"BLOCKED","game_exe_tested":False,"errors":[str(error)]}
    if path is not None:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return status

if __name__=="__main__":
    raise SystemExit(main())
