#!/usr/bin/env python3
"""Sinnoh J12E: opt-in local Windows TEST COPY installer.

Uses the user's own installed Blue game solely as a read-only source. Generates
nine ORIGINAL J10-A/J11-B RXDATA maps, locally allocates unused MapIDs, appends
two RPG::Tileset objects, builds 24 original Blue event pages, compiles a
three-version Barry PBS candidate, isolates save namespace and copies the
result to a NEW QA directory. Does not touch the live game or any personal
save. A test copy is NOT approved playability / R07 / R08 / R09 native QA.
"""
from __future__ import annotations

import argparse
from collections import deque
import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import stat
import struct
import sys
import tempfile
import zlib

ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT,ROOT/"scripts/regions"):
    if str(p) not in sys.path:sys.path.insert(0,str(p))
import generate_sinnoh_original_j10a as five
import generate_sinnoh_four_exteriors_j11b as four
import prepare_sinnoh_nine_original_j11c as j11c
import sinnoh_visual_qa as visual
import sinnoh_private_visual as private_visual
import sinnoh_qa_teleport as qa_teleport
import sinnoh_forest_edge as forest_edge
import sinnoh_city_expansion as city_expansion
import sinnoh_route_expansion as route_expansion
import sinnoh_natural_expansion as natural_expansion
import sinnoh_interior_expansion as interior_expansion
import sinnoh_connection_expansion as connection_expansion
import sinnoh_f08c_expansion as f08c_expansion
import sinnoh_f09_encounters as f09_encounters
import sinnoh_f09b_original as f09b_original
import sinnoh_f09c_refinement as f09c_refinement
import sinnoh_f09d_relative as f09d_relative
import sinnoh_f10b_trainers as f10b_trainers
import sinnoh_f10b7_field_audit as f10b7_field_audit
import sinnoh_f10c_npcs as f10c_npcs
import sinnoh_f11a_gym as f11a_gym
import sinnoh_f12b3_windworks_preflight as f12b3_windworks
import sinnoh_f12b4_windworks_access as f12b4_windworks
import sinnoh_f12b5_authored_quest as f12b5_quest
import sinnoh_f12b5_pickup_catalog as f12b5_pickups
import sinnoh_f12c_eterna_audit as f12c_audit
import sinnoh_f12c2_eterna_preview as f12c_preview
import sinnoh_f12c3_jupiter_candidate as f12c_quest
import sinnoh_f12c4_install as f12c_install
import sinnoh_f12d_runtime as f12d_runtime
import sinnoh_f12d_integrated as f12d_integrated
import sinnoh_regional_catalogue as regional_catalogue
from audit_sinnoh_rxdata import read_marshal
from audit_sinnoh_twinleaf_events import MAPS,HANDLERS as CH06_HANDLERS,BALLS as CH06_BALLS
from build_sinnoh_twinleaf_events import HANDLERS as SCRIPT_HANDLERS
from build_johto_events import event_page,ruby,EVENT_CLASSES
from build_sinnoh_barry_pbs import build as build_barry
from compile_sinnoh_playable_j04 import passable_point
from install_sinnoh_qa_copy import jsonc
from prepare_sinnoh_pilot_bundle import native_map_ids
from sinnoh_save_isolation import namespace
from server.ruby_marshal import RubyObject
from stage import serialize
from pilot import SYSTEM_CLASSES
sys.path.insert(0,str(ROOT/"scripts/official_rules"))
from prepare_restore import Marshal,RubyString,dump

MODE="SINNOH_EXPERIMENTAL_TEST_COPY_NOT_NATIVE_APPROVED"
REPO_OUTPUT=".blue-work"
DEFAULT_GAME=Path(os.environ.get("LOCALAPPDATA",str(Path.home())))/"PokemonBlueDessastreParadoxal"/"game"
QA_DIR="game-sinnoh-experimental"
EXPERIMENT_PLUGIN="Plugins/ZZZZZ Blue Sinnoh Experimental"
INTRO_PLUGIN="Plugins/ZZZZZ Blue Sinnoh Intro"
QA_TITLE_PLUGIN="Plugins/ZZZZ Blue Story and Presentation/TitleKanto.rb"
ROOT_COPY={"Game.exe","Game.ini","mkxp.json","preload.rb","soundfont.sf2","Credits.txt"}
ROOT_DIRS={"Data","Audio","Graphics","Fonts","PBS","Plugins","Scripts"}
SKIP_PARTS={"saves","save","savedata","backups","backup","logs","tmp","cache"}
SKIP_FILES=re.compile(r"(File\s*[A-H]|Auto\s*[1-9]|Save\d*|Game)\.rxdata(?:\.bak)?\Z",re.I)
PRIVATE_EXCLUDED_REQUESTS=frozenset({
    "data/blue-verify-request.txt",
    "data/blue-battle-lab-request.txt",
    "data/blue-reference-export-request.txt",
})
MAX_FILES=45000
MAX_BYTES=8*1024*1024*1024
ANCHORS={
 "SN_BEDROOM_TO_1F":(5,11),
 "SN_NPC_MOTHER":(15,11),"SN_1F_TO_BEDROOM":(4,15),
 "SN_1F_TO_TWINLEAF":(12,17),
 "SN_TOWN_TO_HOME":(10,17),"SN_TOWN_TO_BARRY_HOME":(34,17),
 "SN_TOWN_TO_ROUTE201":(21,2),
 "SN_NPC_BARRY_INTRO":(11,11),"SN_BARRY_HOME_TO_TOWN":(11,16),
 "SN_ROUTE201_TO_TOWN":(2,12),"SN_ROUTE201_TO_LAKE":(26,12),
 "SN_ROUTE201_TO_SANDGEM":(47,12),
 "SN_NPC_ROWAN_BRIEFCASE":(8,20),"SN_BALL_TURTWIG":(7,19),
 "SN_BALL_CHIMCHAR":(9,19),"SN_BALL_PIPLUP":(11,19),
 "SN_NPC_BARRY_BATTLE":(12,21),"SN_LAKE_TO_ROUTE201":(8,25),
 "SN_SANDGEM_TO_ROUTE201":(23,2),
 "SN_SANDGEM_TO_ROWAN_LAB":(36,19),
 "SN_SANDGEM_TO_ROUTE202":(44,21),
 "SN_NPC_ROWAN_POKEDEX":(14,13),"SN_ROWAN_LAB_TO_TOWN":(14,19),
 "SN_ROUTE202_TO_SANDGEM":(18,44),
}

def fail(message):
    raise ValueError("SINNOH_EXPERIMENTAL_BLOCKED:"+message)

def sha(blob):
    return hashlib.sha256(blob).hexdigest()

def safe_path(path:Path):
    path=Path(path).absolute()
    if ".." in path.parts:fail("PARENT_TRAVERSAL")
    for elem in (path,*path.parents):
        if not elem.exists() and not elem.is_symlink():continue
        st=elem.lstat()
        if stat.S_ISLNK(st.st_mode) or getattr(st,"st_file_attributes",0)&0x400:
            fail("SYMLINK_OR_WINDOWS_JUNCTION:"+str(elem))
    return path

def regular(path:Path):
    safe_path(path)
    if not path.is_file():fail("FILE_MISSING:"+str(path))
    return path

def select_ids(base:Path,infos:dict,minimum=442,maximum=517):
    """Local collision-free IDs are QA ONLY, not a global R07 reservation."""
    occupied=native_map_ids(base)|set(infos)
    free=[i for i in range(minimum,maximum+1) if i not in occupied]
    if len(free)<9:fail("NOT_ENOUGH_FREE_SINNOH_QA_IDS_442_517")
    selected=free[:9]
    mapping=j11c.candidate_ids(occupied,set(),selected)
    if set(selected)&occupied:fail("LOCAL_R07_COLLISION")
    return selected,mapping,occupied

def all_scenes():
    scenes=list(five.scenes())+list(four.scenes())
    if len(scenes)!=9 or {s["symbol"] for s in scenes}!=set(MAPS):
        fail("NINE_ORIGINAL_SCENES_NOT_AVAILABLE")
    return {s["symbol"]:s for s in scenes}

def component(scene):
    w,h=scene["width"],scene["height"];layers=scene["layers"]
    def free(x,y):
        if not 0<=x<w or not 0<=y<h:return False
        index=y*w+x
        for v in (layers[0][index],layers[1][index],layers[2][index]):
            if v in j11c.FORBIDDEN:return False
        return any(layers[z][index]!=0 for z in range(3))
    start=tuple(scene["access"][0])
    if not free(*start):fail("SCENE_ACCESS_BLOCKED:"+scene["symbol"])
    reachable={start};todo=deque([start])
    while todo:
        x,y=todo.popleft()
        for dx,dy in ((0,1),(0,-1),(1,0),(-1,0)):
            nxt=x+dx,y+dy
            if nxt not in reachable and free(*nxt):
                reachable.add(nxt);todo.append(nxt)
    if len(reachable)<12:fail("SCENE_ACCESS_COMPONENT_TOO_SMALL")
    return reachable

def choose_point(reachable,anchor,used):
    choices=reachable-set(used)
    if not choices:fail("NO_FREE_EVENT_POSITION")
    return min(choices,key=lambda p:(abs(p[0]-anchor[0])+abs(p[1]-anchor[1]),abs(p[1]-anchor[1]),p[1],p[0]))

def plan_events(blobs:dict,mapping:dict,private_components=None,private_anchors=None):
    """Model-verified coordinates. NEVER claim human or native verification."""
    scenes=all_scenes()
    draft=json.loads((ROOT/"data/regions/sinnoh-twinleaf-events.json").read_text("utf-8"))
    if [row["symbol"] for row in draft["maps"]]!=list(MAPS):
        fail("CH06_SYMBOL_ORDER_MISMATCH")
    chars={}
    for symbol,scene in scenes.items():
        chars[symbol]=component(scene)
    chars.update(private_components or {})
    anchors=dict(ANCHORS)
    anchors.update(private_anchors or {})
    positions={}
    local_used={}
    all_keys=set()
    for row in draft["maps"]:
        symbol=row["symbol"];used=set();chosen={}
        world=read_marshal(blobs["Data/Map%03d.rxdata"%mapping[symbol]],"QA_MAP")
        tiles=read_marshal(blobs["Data/Tilesets.rxdata"],"QA_TILES")
        for event in row["events"]:
            key=event["key"];anchor=anchors.get(key)
            if anchor is None or key in all_keys:fail("UNKNOWN_OR_DUPLICATE_CH06_KEY")
            all_keys.add(key)
            point=choose_point(chars[symbol],anchor,used)
            passable_point(world,tiles,*point)
            used.add(point);chosen[key]=point
        local_used[symbol]=used
        positions[symbol]=chosen
    if set(all_keys)!=set(ANCHORS) or len(all_keys)!=24:
        fail("CH06_EXACTLY_24_EVENTS_REQUIRED")
    # Destination landings must not sit on a touch-warp tile or another event.
    arrivals={}
    for row in draft["maps"]:
        for event in row["events"]:
            if event["kind"]!="warp":continue
            dest=event["destination"]
            if dest not in chars:fail("CH06_DESTINATION_UNKNOWN")
            # Land near the actual reciprocal portal, not a shared map origin.
            reverse=[e for target in draft["maps"] if target["symbol"]==dest
                     for e in target["events"] if e["kind"]=="warp" and e["destination"]==row["symbol"]]
            if len(reverse)!=1:fail("CH06_RECIPROCAL_PORTAL_NOT_UNIQUE")
            near=positions[dest][reverse[0]["key"]]
            arrival=choose_point(chars[dest],near,local_used[dest])
            world=read_marshal(blobs["Data/Map%03d.rxdata"%mapping[dest]],"QA_DEST")
            tiles=read_marshal(blobs["Data/Tilesets.rxdata"],"QA_TILES")
            passable_point(world,tiles,*arrival)
            arrivals[event["key"]]=arrival
    start=choose_point(chars["SINNOH_PLAYER_BEDROOM"],(10,8),
                       local_used["SINNOH_PLAYER_BEDROOM"])
    passable_point(read_marshal(blobs["Data/Map%03d.rxdata"%mapping["SINNOH_PLAYER_BEDROOM"]],"START"),
                   read_marshal(blobs["Data/Tilesets.rxdata"],"T"),*start)
    details=[]
    for row in draft["maps"]:
        symbol=row["symbol"]
        for event in row["events"]:
            key=event["key"];kind=event["kind"]
            record={"map":symbol,"key":key,"kind":kind,
                    "position":list(positions[symbol][key]),"model_reachable":True,
                    "native_engine_verified":False,"human_reviewed":False}
            if kind=="warp":
                record.update(destination=event["destination"],
                              arrival=list(arrivals[key]),
                              destination_map_id=mapping[event["destination"]])
            else:
                if kind=="starter_ball":record["sprite"]="SNQA_BALL"
                else:
                    role={"mother":"MOTHER","barry_intro":"BARRY","barry_rival":"BARRY",
                          "rowan_briefcase":"ROWAN","rowan_pokedex":"ROWAN"}[event["handler"]]
                    record["sprite"]="SNQA_"+role
            details.append(record)
    if len([x for x in details if x["kind"]=="warp"])!=16 or len(details)!=24:
        fail("CH06_WRONG_EVENT_COUNTS")
    return details,start

def compile_events(blobs,mapping,private_components=None,private_anchors=None):
    records,start=plan_events(blobs,mapping,private_components,private_anchors)
    grouped={s:[] for s in MAPS}
    for row in records:grouped[row["map"]].append(row)
    compiled=dict(blobs)
    for symbol,items in grouped.items():
        rel="Data/Map%03d.rxdata"%mapping[symbol]
        world=read_marshal(blobs[rel],"EMPTY_SOURCE_MAP")
        if not isinstance(world,RubyObject) or world.attrs.get("@events")!={}:
            fail("EVENT_SOURCE_NOT_EMPTY")
        out=copy.deepcopy(world)
        events={}
        for i,row in enumerate(items,1):
            if row["kind"]=="warp":
                page=event_page(warp=(row["destination_map_id"],*row["arrival"]),
                                touch=True)
            else:
                source=next(x for x in json.loads((ROOT/"data/regions/sinnoh-twinleaf-events.json").read_text("utf-8"))["maps"]
                            if x["symbol"]==symbol)
                orig=next(x for x in source["events"] if x["key"]==row["key"])
                if row["kind"]=="handler":
                    handler=orig["handler"]
                    if SCRIPT_HANDLERS.get(handler) is None or CH06_HANDLERS.get(row["key"])!=(symbol,handler):
                        fail("HANDLER_NOT_ALLOWLISTED")
                    script=SCRIPT_HANDLERS[handler]
                else:
                    species=orig["species"]
                    if CH06_BALLS.get(row["key"])!=(symbol,species):
                        fail("STARTER_BALL_NOT_ALLOWLISTED")
                    script=f"BlueSinnohPilot.choose_starter_from_ball(:{species})"
                page=event_page(script=script,sprite=row["sprite"],touch=orig["trigger"]=="touch")
            events[i]=ruby("RPG::Event",id=i,name=row["key"].encode("ascii"),
                           x=row["position"][0],y=row["position"][1],pages=[page])
        out.attrs["@events"]=events
        compiled[rel]=serialize(out,EVENT_CLASSES)
        reread=read_marshal(compiled[rel],"AUDITED_EVENT_MAP")
        if len(reread.attrs["@events"])!=len(items) or reread.attrs["@data"].data!=world.attrs["@data"].data:
            fail("EVENT_COMPILATION_CHANGED_SOURCE_GEOMETRY")
    return compiled,records,start

def sprite_png(kind:str):
    # 4x4 frame character sheet, 32x32 per frame, generated locally without any game assets.
    if kind not in ("NPC","BALL"):fail("UNKNOWN_CHARACTER_SPRITE")
    w=h=128
    pixels=bytearray(w*h*4)
    def pix(x,y,rgb):
        if 0<=x<w and 0<=y<h:
            off=(y*w+x)*4
            pixels[off:off+4]=bytes((*rgb,255))
    for fy in range(4):
        for fx in range(4):
            sx,sy=fx*32,fy*32
            for dy in range(32):
                for dx in range(32):
                    if kind=="NPC":
                        color=None
                        if 8<=dx<=23 and 4<=dy<=13:color=(215,176,138)
                        if 6<=dx<=25 and 3<=dy<=7:color=(69,78,128)
                        if 10<=dx<=21 and 15<=dy<=26:color=(85,156,167)
                        if 11<=dx<=14 and 26<=dy<=30 or 18<=dx<=21 and 26<=dy<=30:color=(65,75,100)
                        if dy==11 and dx in (12,19):color=(31,44,48)
                    else:
                        q=(dx-16)**2+(dy-16)**2
                        color=None
                        if q<110:color=(238,242,239) if dy>=16 else (218,69,72)
                        if 15<=dy<=17 and 6<=dx<=26:color=(45,55,57)
                        if q<15:color=(241,227,162)
                        if 2<=q<110 and (abs(dx-16)<2 or abs(dy-16)<2) and dy>=16:color=(210,219,226)
                    if color:pix(sx+dx,sy+dy,color)
    def chunk(name,body):
        return struct.pack(">I",len(body))+name+body+struct.pack(">I",zlib.crc32(name+body)&0xffffffff)
    data=b"".join(b"\x00"+pixels[i*w*4:(i+1)*w*4] for i in range(h))
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",w,h,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(data,9))+chunk(b"IEND",b"")

def runtime_config(base:Path,token:str):
    from install_sinnoh_qa_copy import unique_save_configs
    # Use established save-isolation semantics, but do NOT use its main-game path.
    original=jsonc((base/"mkxp.json").read_text("utf-8-sig"))
    if any("save" in x.casefold() or "userdata" in x.casefold()
           for x in original if isinstance(x,str)):
        fail("CUSTOM_SAVE_PATH_UNSAFE")
    profile=namespace(token)
    if any(original.get(x)==profile[x] for x in ("dataPathApp","dataPathOrg")):
        fail("QA_PROFILE_EQUALS_MAIN")
    config=dict(original)
    config.update(windowTitle=profile["title"],
                  dataPathApp=profile["dataPathApp"],
                  dataPathOrg=profile["dataPathOrg"])
    text=(base/"Game.ini").read_text("utf-8-sig")
    result,count=re.subn(r"(?m)^Title=[^\r\n]*","Title="+profile["title"],text)
    if count!=1:fail("GAME_INI_TITLE_NOT_UNIQUE")
    return (json.dumps(config,ensure_ascii=False,indent=2)+"\n").encode(),result.encode(),profile

def patch_bootstrap(raw:bytes,token:str,map_ids=(),connected=False,story_profile=False,save_token=None,route201=None,encounter_coverage=None,route_trainers=False,encounter_expected=None,f10b=False,f11a=False,f11b=False,f11c=False,f11d=False,f11e=False,f11f=False,f11g=False,f11h=False,f12b5=False,f12c4=False,f12d=False,f12d_integrated=False):
    """Require real Essentials Compiler and all three Barry PBS data; no fake success."""
    rows=Marshal(raw).read()
    matches=[row for row in rows if isinstance(row,list) and len(row)>=3 and row[1]==b"Main"]
    if len(matches)!=1:fail("NATIVE_MAIN_SCRIPT_NOT_UNIQUE")
    main=matches[0]
    code=zlib.decompress(main[2]).decode("utf-8")
    anchor="    PluginManager.runPlugins"
    compiler="    Compiler.main"
    if code.count(anchor)!=1 or code.count(compiler)!=1 or code.index(anchor)>=code.index(compiler):
        fail("ESSENTIALS_MAIN_BOOTSTRAP_NOT_RECOGNIZED")
    if "sinnoh-experimental-compile-request" in code:fail("QA_ALREADY_PATCHED")
    if not re.fullmatch(r"[a-f0-9]{12}",token):fail("INVALID_QA_TOKEN")
    if map_ids and (len(map_ids) not in (9,10,22,56,natural_expansion.COUNT,interior_expansion.COUNT,f08c_expansion.COUNT,f08c_expansion.COUNT+1,f08c_expansion.COUNT+2,f08c_expansion.COUNT+3,f08c_expansion.COUNT+4,f08c_expansion.COUNT+5,f08c_expansion.COUNT+6,f08c_expansion.COUNT+7,f08c_expansion.COUNT+8,f08c_expansion.COUNT+9,f08c_expansion.COUNT+13) or len(set(map_ids))!=len(map_ids) or
                    any(type(n) is not int or not 442<=n<=(599 if len(map_ids)>=natural_expansion.COUNT else 517) for n in map_ids)):
        fail("INVALID_QA_COMPILE_MAP_IDS")
    scope='File.basename(Dir.pwd) == "game-sinnoh-experimental-'+token+'" && '
    scope+='File.file?("sinnoh-experimental-qa.json") && File.file?("Data/sinnoh-experimental-compile-request.txt")'
    hook="""    if __QA_SCOPE__
      $DEBUG = true
      %w[PluginScripts.rxdata trainers.dat].each do |name|
        path = "Data/#{name}"
        File.delete(path) if File.file?(path)
      end
    end
"""
    verify="""    if __QA_SCOPE__
      begin
        GameData::Trainer.load
        unless (0..2).all? { |v| GameData::Trainer.exists?(:BLUE_SINNOH_RIVAL, "Barry", v) }
          raise "Sinnoh QA: faltam as tres equipes Barry compiladas"
        end
        File.write("Data/sinnoh-experimental-compiled.txt",
                   File.read("Data/sinnoh-experimental-compile-request.txt").strip)
        File.delete("Data/sinnoh-experimental-compile-request.txt")
      rescue StandardError => error
        File.write("Data/sinnoh-experimental-compile-error.txt", error.full_message)
        # Stop retriggering the compiler forever on an invalid Barry candidate.
        # Barry stays blocked: do NOT create the compiled marker on failure.
        File.delete("Data/sinnoh-experimental-compile-request.txt")
      end
      exit
    end
"""
    if route201 is not None:
        if route201 not in map_ids:fail("INVALID_ROUTE201_COMPILE_ID")
        hook=hook.replace("trainers.dat", "trainers.dat encounters.dat")
        verify=verify.replace("        File.write(", f"        GameData::Encounter.load\n        encounter = GameData::Encounter.get({route201},0)\n        unless encounter && encounter.types[:Land] && !encounter.types[:Land].empty?\n          raise \"Sinnoh QA: encontros da Rota 201 ausentes\"\n        end\n        File.write(",1)
    if encounter_coverage:
        if any(mid not in map_ids for mid in encounter_coverage):fail("INVALID_ENCOUNTER_COVERAGE_ID")
        checks=[]
        for mid,methods in sorted(encounter_coverage.items()):
            for method in methods:
                if not re.fullmatch(r"[A-Za-z]+",method):fail("INVALID_ENCOUNTER_METHOD")
                checks.append(f'        raise "Sinnoh QA: encontro ausente {mid}/{method}" unless GameData::Encounter.get({mid},0)&.types&.fetch(:{method},nil)&.any?')
        if route201 is None:hook=hook.replace("trainers.dat","trainers.dat encounters.dat")
        verify=verify.replace("        File.write(", "        GameData::Encounter.load\n"+"\n".join(checks)+"\n        File.write(",1)
    if encounter_expected:
        checks=[]
        for mid,methods in sorted(encounter_expected.items()):
            if mid not in map_ids:fail("INVALID_RELATIVE_ENCOUNTER_ID")
            for method,slots in sorted(methods.items()):
                if not re.fullmatch(r"[A-Za-z]+",method) or not slots:fail("INVALID_RELATIVE_ENCOUNTER_METHOD")
                if any(len(slot)!=4 or type(slot[0]) is not int or not 1<=slot[0]<=100 or not re.fullmatch(r"[A-Z][A-Z0-9_]*",slot[1]) or not 1<=slot[2]<=slot[3]<=100 for slot in slots):
                    fail("INVALID_RELATIVE_ENCOUNTER_SLOT")
                expected=json.dumps(sorted(slots),ensure_ascii=True,separators=(",",":"))
                checks.append(f'        actual = GameData::Encounter.get({mid},0)&.types&.fetch(:{method},nil)')
                checks.append(f'        raise "Sinnoh QA: pesos relativos alterados {mid}/{method}" unless actual && actual.map {{ |e| [e[0],e[1].to_s,e[2],e[3]] }}.sort == {expected}.sort')
        verify=verify.replace("        File.write(", "        GameData::Encounter.load\n"+"\n".join(checks)+"\n        File.write(",1)
    if route_trainers:
        checks=[]
        for key,kind,name,mon in private_visual.ROUTE202_TRAINERS:
            checks.append(f'        raise "Sinnoh QA: treinador ausente {name}" unless GameData::Trainer.exists?(:{kind}, "{name}", {private_visual.TRAINER_VERSION})')
        verify=verify.replace("        File.write(", "\n".join(checks)+"\n        File.write(",1)
    if f10b:
        verify=verify.replace("        File.write(", "        BlueSinnohF10B.verify_compiled!\n        File.write(",1)
    if f11a:
        verify=verify.replace("        File.write(", "        BlueSinnohF11A.verify_compiled!\n        File.write(",1)
    if f11b:
        verify=verify.replace("        File.write(", "        BlueSinnohF11B.verify_compiled!\n        File.write(",1)
    if f11c:
        verify=verify.replace("        File.write(", "        BlueSinnohF11C.verify_compiled!\n        File.write(",1)
    if f11d:
        verify=verify.replace("        File.write(", "        BlueSinnohF11D.verify_compiled!\n        File.write(",1)
    if f11e:
        verify=verify.replace("        File.write(", "        BlueSinnohF11E.verify_compiled!\n        File.write(",1)
    if f11f:
        verify=verify.replace("        File.write(", "        BlueSinnohF11F.verify_compiled!\n        File.write(",1)
    if f11g:
        verify=verify.replace("        File.write(", "        BlueSinnohF11G.verify_compiled!\n        File.write(",1)
    if f11h:
        verify=verify.replace("        File.write(", "        BlueSinnohF11H.verify_compiled!\n        File.write(",1)
    if f12b5:
        hook=hook.replace("trainers.dat","trainers.dat items.dat")
        verify=verify.replace("        File.write(", "        GameData::Item.load\n        BlueSinnohF12B5.verify_compiled!\n        File.write(",1)
    if f12c4:
        verify=verify.replace("        File.write(", "        BlueSinnohF12C3.verify_compiled!\n        File.write(",1)
    if f12d:
        verify=verify.replace("        File.write(", "        BlueSinnohF12D.verify_compiled!\n        File.write(",1)
    if f12d_integrated:
        if "items.dat" not in hook:hook=hook.replace("trainers.dat","trainers.dat items.dat")
        verify=verify.replace("        File.write(", "        GameData::Item.load\n        BlueSinnohF12DIntegrated.verify_compiled!\n        File.write(",1)
    # Essentials normalizes transfer events (door SFX/fades) during PBS
    # compilation and rewrites their maps. These authored QA files are pinned
    # byte-for-byte by the title/supervisor. Preserve their verified input bytes
    # only across this compiler call, without accepting new hashes or touching
    # other maps, trainer output, the source game or a later gameplay session.
    protected=[f"Data/Map{mid:03d}.rxdata" for mid in map_ids]
    protected += ["Data/MapInfos.rxdata","Data/Tilesets.rxdata"] if map_ids else []
    if connected:protected.append("Data/map_connections.dat")
    guarded="""    blue_sinnoh_native_sources = nil
    if __QA_SCOPE__
      blue_sinnoh_native_sources = {}
      %w[__QA_PROTECTED__].each do |path|
        blue_sinnoh_native_sources[path] = File.binread(path)
      end
    end
    begin
      Compiler.main
    ensure
      if blue_sinnoh_native_sources
        blue_sinnoh_native_sources.each do |path, original|
          File.binwrite(path, original) if !File.file?(path) || File.binread(path) != original
        end
      end
    end
"""
    guarded=guarded.replace("__QA_PROTECTED__"," ".join(protected))
    if f12d_integrated:
        # The native compiler can change files and raise non-StandardError.
        # Capture the exact request before plugin load, and keep it immutable
        # through compilation rather than re-evaluating the filesystem scope.
        hook=hook.replace("    if __QA_SCOPE__","    blue_sinnoh_compile_only = (__QA_SCOPE__)\n    if blue_sinnoh_compile_only",1)
        hook=hook.replace("      $DEBUG = true","      blue_sinnoh_request = File.binread(\"Data/sinnoh-experimental-compile-request.txt\").strip\n      raise \"Sinnoh F12D: invalid compile token\" unless blue_sinnoh_request.match?(/\\A[a-f0-9]{64}\\z/)\n      raise \"Sinnoh F12D: foreign diagnostic request in private copy\" if File.exist?(\"Data/blue-verify-request.txt\") || File.exist?(\"Data/blue-battle-lab-request.txt\") || File.exist?(\"Data/blue-reference-export-request.txt\")\n      puts \"SINNOH_F12D_NATIVE_STAGE FOREIGN_REQUESTS_ISOLATED\"\n      $DEBUG = true\n      puts \"SINNOH_F12D_NATIVE_STAGE REQUEST_ACCEPTED\"",1)
        guarded=guarded.replace("if __QA_SCOPE__","if blue_sinnoh_compile_only",1)
        # The core compiler returns before the Blue/Decades alias chain has
        # finished. Restore the pinned QA bytes at that boundary, not only
        # after the outer method returns: native post-hooks may inspect them.
        # Never prepend Compiler.main (the installed plugins alias that method).
        guarded=guarded.replace("      Compiler.main", """      if blue_sinnoh_compile_only
        blue_sinnoh_core_compiled = false
        blue_sinnoh_restore = proc do
          blue_sinnoh_native_sources.each do |path, original|
            File.binwrite(path, original) if !File.file?(path) || File.binread(path) != original
          end
        end
        blue_sinnoh_core = Compiler.method(:compile_all)
        Compiler.define_singleton_method(:compile_all) do |must_compile|
          begin
            value = blue_sinnoh_core.call(must_compile)
            if must_compile
              blue_sinnoh_restore.call
              blue_sinnoh_core_compiled = true
              puts "SINNOH_F12D_NATIVE_STAGE CORE_COMPILED_AND_RESTORED"
            end
            value
          ensure
            blue_sinnoh_restore.call
          end
        end
        begin
          Compiler.main
          raise "Sinnoh F12D: core did not compile fresh PBS" unless blue_sinnoh_core_compiled
          puts "SINNOH_F12D_NATIVE_STAGE COMPILER_RETURNED"
        rescue Exception => error
          message = [error.class.to_s, error.message, *Array(error.backtrace)].join("\\n")
          warn "SINNOH_F12D_NATIVE_VERIFY_FAILED: COMPILER #{message}"
          File.binwrite("Data/sinnoh-experimental-compile-error.txt", message)
          File.delete("Data/sinnoh-experimental-compiled.txt") if File.file?("Data/sinnoh-experimental-compiled.txt")
          raise
        ensure
          Compiler.singleton_class.send(:define_method, :compile_all, blue_sinnoh_core)
          blue_sinnoh_restore.call
        end
      else
        Compiler.main
      end""",1)
        verify=verify.replace("    if __QA_SCOPE__","    if blue_sinnoh_compile_only",1)
        verify=verify.replace("        GameData::Trainer.load","        raise \"Sinnoh F12D: compile request changed\" unless File.binread(\"Data/sinnoh-experimental-compile-request.txt\").strip==blue_sinnoh_request\n        puts \"SINNOH_F12D_NATIVE_STAGE VERIFY_ENTERED\"\n        GameData::Item.load\n        raise \"Sinnoh F12D: invalid compiled SecretPotion\" unless BlueSinnohF12D3Transaction.compiled_item_valid?\n        puts \"SINNOH_F12D_NATIVE_ITEM_COMPILED_OK\"\n        BlueSinnohF12DIntegrated.verify_native_movement!\n        puts \"SINNOH_F12D_NATIVE_MOVEMENT_PROBE_OK\"\n        BlueSinnohF12DIntegrated.verify_native_transaction!\n        puts \"SINNOH_F12D_NATIVE_TRANSACTION_PROBE_OK\"\n        GameData::Trainer.load",1)
        # Keep all previous encounter/trainer/terrain/hook checks, not just
        # the new native probes. Only their joint pass writes the final receipt.
        verify=verify.replace("        File.write(\"Data/sinnoh-experimental-compiled.txt\",\n                   File.read(\"Data/sinnoh-experimental-compile-request.txt\").strip)","        File.binwrite(\"Data/sinnoh-experimental-compiled.txt\", blue_sinnoh_request)\n        raise \"Sinnoh F12D: compile receipt write failed\" unless File.binread(\"Data/sinnoh-experimental-compiled.txt\")==blue_sinnoh_request\n        puts \"SINNOH_F12D_NATIVE_STAGE ALL_VERIFIERS_PASSED\"")
        verify=verify.replace("      rescue StandardError => error\n        File.write(\"Data/sinnoh-experimental-compile-error.txt\", error.full_message)","      rescue StandardError, ScriptError => error\n        message = [error.class.to_s, error.message, *Array(error.backtrace)].join(\"\\n\")\n        warn \"SINNOH_F12D_NATIVE_VERIFY_FAILED: #{message}\"\n        File.binwrite(\"Data/sinnoh-experimental-compile-error.txt\", message)\n        File.delete(\"Data/sinnoh-experimental-compiled.txt\") if File.file?(\"Data/sinnoh-experimental-compiled.txt\")")
    late = ""
    if story_profile:
        late = '\n    if File.basename(Dir.pwd) == "game-sinnoh-experimental-'+token+'" && File.file?("sinnoh-experimental-qa.json")\n      BlueSinnohExperimental.install_fresh_hooks!\n      BlueSinnohSafeMovement.install!\n      BlueSinnohQATeleport.install!\n      BlueSinnohForestEdge.install!\n      if defined?(EventHandlers)\n        EventHandlers.add(:on_enter_map, :blue_sinnoh_hide_starter_balls, proc { |*args| BlueSinnohPilot.hide_starter_balls; BlueSinnohPilot.sync_route_trainers })\n      end\n    end'
    if f12d_integrated:
        late += '\n    if File.basename(Dir.pwd) == "game-sinnoh-experimental-'+token+'" && File.file?("sinnoh-experimental-qa.json")\n      raise "Sinnoh F12D: hooks indisponiveis" unless BlueSinnohF12DIntegrated.bind_pages!\n      unless File.file?("Data/sinnoh-experimental-compile-request.txt")\n        raise "Sinnoh F12D: compilacao privada nao aprovada" unless defined?(BlueKantoTitle) && BlueKantoTitle.sinnoh_experimental_barry_compiled?\n      end\n    end'
    if save_token is not None:
        if not re.fullmatch(r"[a-f0-9]{12}",save_token):fail("INVALID_SAVE_PROFILE_TOKEN")
        # The original Auto Multi Save plugin falls back to "." if the
        # platform directory is absent. Resolve a private persistent path
        # before loading plugins; pin the plugin constant after loading.
        prepare = """    if File.basename(Dir.pwd) == "game-sinnoh-experimental-__COPY__" && File.file?("sinnoh-experimental-qa.json")
      begin
        candidate = File.expand_path(System.data_directory)
        parts = candidate.tr("\\\\", "/").split("/")
        expected = ["Sinnoh-QA-__SAVE__", "Dessastre-Sinnoh-QA-__SAVE__", "Sinnoh QA __SAVE__"]
        raise "non-private native path" unless (parts & expected).any?
        require "fileutils"
        FileUtils.mkdir_p(candidate)
        raise "unsafe save path" if File.symlink?(candidate) || !File.directory?(candidate)
        $blue_sinnoh_save_dir = candidate
      rescue StandardError, LoadError
        # Stable fallback, exclusive to the first compatible QA namespace.
        candidate = File.expand_path("../sinnoh-private-saves-__SAVE__")
        Dir.mkdir(candidate) unless File.directory?(candidate)
        raise "Sinnoh QA: pasta de saves insegura" if File.symlink?(candidate) || !File.directory?(candidate)
        $blue_sinnoh_save_dir = candidate
      end
    end
"""
        hook+=prepare.replace("__COPY__",token).replace("__SAVE__",save_token)
        late += '\n    if $blue_sinnoh_save_dir && defined?(SaveData) && SaveData.const_defined?(:SAVE_DIR, false)\n      SaveData.send(:remove_const, :SAVE_DIR)\n      SaveData.const_set(:SAVE_DIR, $blue_sinnoh_save_dir)\n    end'
    code=code.replace(anchor,hook+anchor+late).replace(compiler,guarded+verify)
    code=code.replace("__QA_SCOPE__",scope)
    main[2]=RubyString(zlib.compress(code.encode("utf-8")))
    return b"\x04\x08"+dump(rows)

def experiment_plugin(start,token,platinum_player=False,platinum_dawn=False,story_profile=False):

    if story_profile:
        # Independent late hook: old installed bases may not have RegionStart,
        # or the previous prepend ran before that module was loaded. Do not
        # rely on the base's optional NewGame/SaveValues hooks.
        return ("""# Isolated Sinnoh new-game bootstrap, loaded after native plugins.
module BlueSinnohExperimental
  START = [__START__].freeze
  TOKEN = "__TOKEN__".freeze

  def self.private_copy?
    File.basename(Dir.pwd) == "game-sinnoh-experimental-" + TOKEN &&
      File.file?("sinnoh-experimental-qa.json")
  end

  def self.fresh?
    private_copy? && @fresh == true
  end

  def self.state_template(region)
    if defined?(BlueRegions) && BlueRegions.respond_to?(:new_state)
      return BlueRegions.new_state(region)
    end
    # Canonical Regions.rb v1 schema for older installed bases. Never
    # synthesize progression or run this outside a genuine QA new game.
    {"version"=>1, "initial"=>region, "current"=>region, "leagues"=>[],
     "achievements"=>{}, "field_events"=>{}, "hisui_complete"=>false, "hisui_quest"=>false}
  end

  def self.prepare_fresh!
    raise "Sinnoh QA: fora de Novo Jogo privado" unless fresh?
    raise "Sinnoh QA: save nativo ainda nao inicializado" unless $PokemonGlobal
    # Native save values must have completed, or a new metadata object must
    # have been created by Game.start_new. Never initialize a loaded save.
    return false unless @values_loaded || !$PokemonGlobal.equal?(@previous_global)
    unless $PokemonGlobal.respond_to?(:blue_regions) && $PokemonGlobal.respond_to?(:blue_regions=)
      $PokemonGlobal.class.class_eval { attr_accessor :blue_regions }
    end
    record = $PokemonGlobal.blue_regions
    valid = record.is_a?(Hash) && record["version"] == 1 &&
      record["initial"] == "SINNOH" && record["current"] == "SINNOH"
    unless valid
      if record && record != state_template("DECADES")
        raise "Sinnoh QA: estado regional nao inicial ou de outra regiao"
      end
      $PokemonGlobal.blue_regions = state_template("SINNOH")
    end
    # Set spawn before map factory, and do not clear a bag twice if both
    # the base hook and this independent hook see the same fresh object.
    if $data_system
      $data_system.start_map_id = START[0]
      $data_system.start_x = START[1]
      $data_system.start_y = START[2]
    end
    unless @prepared_global.equal?($PokemonGlobal)
      BlueStory.choose_mode(:story) if defined?(BlueStory)
      BlueCampaign.begin_journey(false) if defined?(BlueCampaign) && $bag
      $PokemonGlobal.blue_traditional_starters = true if $PokemonGlobal.respond_to?(:blue_traditional_starters=)
      $PokemonGlobal.blue_campaign_departure = false if $PokemonGlobal.respond_to?(:blue_campaign_departure=)
      @prepared_global = $PokemonGlobal
    end
    true
  end

  def self.with_fresh
    raise "Sinnoh QA: mapas ou perfil privado invalidos" unless
      defined?(BlueKantoTitle) && BlueKantoTitle.sinnoh_experimental_maps_ready?
    @fresh = true
    @values_loaded = false
    @previous_global = $PokemonGlobal
    @prepared_global = nil
    result = yield
    raise "Sinnoh QA: Novo Jogo nao inicializou save nativo" unless prepare_fresh!
    result
  ensure
    @fresh = false
    @values_loaded = false
    @previous_global = nil
    @prepared_global = nil
  end

  module FreshGame
    def start_new(*args, &block)
      return super unless BlueSinnohExperimental.private_copy?
      BlueSinnohExperimental.with_fresh { super(*args, &block) }
    end
  end

  module FreshValues
    def load_new_game_values(*args, &block)
      result = super
      if BlueSinnohExperimental.fresh?
        BlueSinnohExperimental.values_loaded!
      end
      result
    end
  end

  def self.values_loaded!
    @values_loaded = true
    prepare_fresh!
  end

  module LegacyRegionOverride
    def select_and_prepare(*args)
      return super unless BlueSinnohExperimental.fresh?
      # Called from the older base SaveValues wrapper AFTER native values.
      BlueSinnohExperimental.values_loaded!
      nil
    end
  end

  def self.install_fresh_hooks!
    return unless private_copy?
    raise "Sinnoh QA: API nativa de Novo Jogo indisponivel" unless
      defined?(Game) && Game.respond_to?(:start_new) &&
      defined?(SaveData) && SaveData.respond_to?(:load_new_game_values)
    Game.singleton_class.prepend(FreshGame) unless Game.singleton_class.ancestors.include?(FreshGame)
    SaveData.singleton_class.prepend(FreshValues) unless SaveData.singleton_class.ancestors.include?(FreshValues)
    if defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:select_and_prepare)
      BlueRegionStart.singleton_class.prepend(LegacyRegionOverride) unless
        BlueRegionStart.singleton_class.ancestors.include?(LegacyRegionOverride)
    end
  end
end
# Character and name are selected in the bedroom autorun.
""").replace("__START__",",".join(str(x) for x in start)).replace("__TOKEN__",token).encode("utf-8")
    code="""# Only for one isolated experimental copy; no main-game hooks.
module BlueSinnohExperimental
  START = [__START__].freeze
  TOKEN = "__TOKEN__".freeze
  module Override
    def select_and_prepare(*args)
      unless @new_game
        return super
      end
      raise "Sinnoh QA: regional runtime ausente" unless defined?(BlueRegions) &&
        defined?(BlueRegionStart) && defined?($PokemonGlobal) && $PokemonGlobal &&
        $PokemonGlobal.respond_to?(:blue_regions=) && BlueRegions.respond_to?(:new_state)
      raise "Sinnoh QA: dados de inicio ausentes" unless defined?($data_system) &&
        $data_system && $data_system.respond_to?(:start_map_id=)
      # Walking the nine QA maps does not depend on Barry's trainer PBS.
      # Never start an unverified map, however: the title plugin checks the
      # private namespace and SHA-256 for all nine RXDATA + MapInfos/Tilesets.
      raise "Sinnoh QA: mapas ou perfil privado invalidos" unless
        defined?(BlueKantoTitle) &&
        BlueKantoTitle.respond_to?(:sinnoh_experimental_maps_ready?) &&
        BlueKantoTitle.sinnoh_experimental_maps_ready?
      raise "Sinnoh QA: save de outra regiao nao pode ser herdado" if
        $PokemonGlobal.respond_to?(:blue_regions) &&
        $PokemonGlobal.blue_regions &&
        $PokemonGlobal.blue_regions.is_a?(Hash) &&
        $PokemonGlobal.blue_regions["current"] != "SINNOH"
      $PokemonGlobal.blue_regions = BlueRegions.new_state("SINNOH")
      BlueStory.choose_mode(:story) if defined?(BlueStory)
      BlueCampaign.begin_journey(false) if defined?(BlueCampaign)
      $PokemonGlobal.blue_traditional_starters = true
      $PokemonGlobal.blue_campaign_departure = false
      __PLATINUM_PLAYER__
      $data_system.start_map_id = START[0]
      $data_system.start_x = START[1]
      $data_system.start_y = START[2]
      nil
    end
  end
  if defined?(BlueRegionStart)
    BlueRegionStart.singleton_class.prepend(Override)
  end
end
"""
    code=code.replace("__START__",",".join(str(x) for x in start)).replace("__TOKEN__",token)
    player_code = 'if $game_player && defined?(pbChangePlayer); pbChangePlayer(9); $game_player.refresh_charset; $game_player.transparent = false; end' if platinum_player else '# native player unchanged for original QA'
    if platinum_dawn:
        choose = 'choice = pbMessage("Escolha seu protagonista de Sinnoh:", ["Lucas", "Dawn"], 1); pbChangePlayer(choice == 1 ? 10 : 9)' if platinum_player else 'pbChangePlayer(10)'
        player_code = 'if $game_player && defined?(pbChangePlayer); ' + choose + '; $game_player.refresh_charset; $game_player.transparent = false; end'
    if story_profile:
        player_code = '# Character and name are selected in the bedroom autorun after map initialization.'
    code=code.replace("__PLATINUM_PLAYER__",player_code)
    return code.encode("utf-8")

def compatible_save_token(project,mapping,base_hash,generated_maps=None,previous_maps=None,intermediate_maps=None,refined_maps=None,pre_f10b_maps=None,f10b2_maps=None,f10b3_maps=None,f10b4_maps=None,f10b5_maps=None,f10b6_maps=None,f10b8_maps=None,f10c1_maps=None,f10c2_maps=None,f11a_maps=None,f11b_maps=None,f11c_maps=None,f11d_maps=None,f11e_maps=None,f11f_maps=None,f11g_maps=None,f12b4_maps=None,f12c_previous_maps=None,f12d_previous_maps=None,f12d_integrated_previous_maps=None):
    # Read manifests/config only; never enumerate or open save files.
    work=safe_path(project/REPO_OUTPUT)
    candidates=[]
    for folder in work.glob(QA_DIR+"-*"):
        if not re.fullmatch(QA_DIR+r"-[a-f0-9]{12}",folder.name):continue
        try:
            safe_path(folder)
            path=folder/"sinnoh-experimental-qa.json";regular(path)
            data=json.loads(path.read_text("utf-8"))
            copy_token=folder.name.rsplit("-",1)[-1]
            token=data.get("save_profile_token",copy_token)
            if (data.get("schema")!=1 or data.get("region")!="SINNOH" or
                data.get("mode")!=MODE or data.get("profile_token")!=copy_token or
                data.get("main_game_modified") is not False or
                data.get("personal_saves_copied") is not False or
                data.get("base_mapinfos_sha256")!=base_hash or
                data.get("save_profile")!=namespace(token)):continue
            prior=data.get("mapids")
            if prior!=mapping:
                # Only the audited append-only F04 transition may reuse a
                # namespace. Verify every old map against its prior hash and
                # the freshly generated bytes; never read a save.
                if not (generated_maps and isinstance(prior,dict) and ((set(prior)==city_expansion.OLD and set(mapping)==route_expansion.PRIOR) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR) and set(mapping)==route_expansion.ALL) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL) and set(mapping)==natural_expansion.ALL) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL,natural_expansion.ALL) and set(mapping)==interior_expansion.ALL) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL,natural_expansion.ALL,interior_expansion.ALL) and set(mapping)==f08c_expansion.ALL) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL,natural_expansion.ALL,interior_expansion.ALL,f08c_expansion.ALL) and set(mapping)==f11a_gym.GYM_SETS[0]) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL,natural_expansion.ALL,interior_expansion.ALL,f08c_expansion.ALL,f11a_gym.GYM_SETS[0]) and set(mapping)==f11a_gym.GYM_SETS[1]) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL,natural_expansion.ALL,interior_expansion.ALL,f08c_expansion.ALL,*f11a_gym.GYM_SETS[:2]) and set(mapping)==f11a_gym.GYM_SETS[2]) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL,natural_expansion.ALL,interior_expansion.ALL,f08c_expansion.ALL,*f11a_gym.GYM_SETS[:3]) and set(mapping)==f11a_gym.GYM_SETS[3]) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL,natural_expansion.ALL,interior_expansion.ALL,f08c_expansion.ALL,*f11a_gym.GYM_SETS[:4]) and set(mapping)==f11a_gym.GYM_SETS[4]) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL,natural_expansion.ALL,interior_expansion.ALL,f08c_expansion.ALL,*f11a_gym.GYM_SETS[:5]) and set(mapping)==f11a_gym.GYM_SETS[5]) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL,natural_expansion.ALL,interior_expansion.ALL,f08c_expansion.ALL,*f11a_gym.GYM_SETS[:6]) and set(mapping)==f11a_gym.GYM_SETS[6]) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL,natural_expansion.ALL,interior_expansion.ALL,f08c_expansion.ALL,*f11a_gym.GYM_SETS[:7]) and set(mapping)==f11a_gym.GYM_SETS[7]) or
                         (set(prior) in (city_expansion.OLD,route_expansion.PRIOR,route_expansion.ALL,natural_expansion.ALL,interior_expansion.ALL,f08c_expansion.ALL,*f11a_gym.GYM_SETS) and set(mapping)==f12b4_windworks.ALL) or (set(prior)==f12b4_windworks.ALL and set(mapping)==f12c_install.ALL)) and
                        all(mapping.get(k)==v for k,v in prior.items())):continue
                hashes=data.get("file_sha256",{})
                if not isinstance(hashes,dict):continue
                if not any(all(hashes.get(f"Data/Map{mid:03d}.rxdata")==sha(candidate.get(f"Data/Map{mid:03d}.rxdata",b"")) for mid in prior.values()) for candidate in (generated_maps,previous_maps,intermediate_maps,refined_maps,pre_f10b_maps,f10b2_maps,f10b3_maps,f10b4_maps,f10b5_maps,f10b6_maps,f10b8_maps,f10c1_maps,f10c2_maps,f11a_maps,f11b_maps,f11c_maps,f11d_maps,f11e_maps,f11f_maps,f11g_maps,f12b4_maps,f12c_previous_maps,f12d_previous_maps,f12d_integrated_previous_maps) if candidate):continue
            elif set(mapping) in (interior_expansion.ALL,f08c_expansion.ALL,*f11a_gym.GYM_SETS,f12b4_windworks.ALL,f12c_install.ALL):
                hashes=data.get("file_sha256",{})
                if not isinstance(hashes,dict) or not any(all(hashes.get(f"Data/Map{mid:03d}.rxdata")==sha(candidate.get(f"Data/Map{mid:03d}.rxdata",b"")) for mid in mapping.values()) for candidate in (generated_maps,previous_maps,intermediate_maps,refined_maps,pre_f10b_maps,f10b2_maps,f10b3_maps,f10b4_maps,f10b5_maps,f10b6_maps,f10b8_maps,f10c1_maps,f10c2_maps,f11a_maps,f11b_maps,f11c_maps,f11d_maps,f11e_maps,f11f_maps,f11g_maps,f12b4_maps,f12c_previous_maps,f12d_previous_maps,f12d_integrated_previous_maps) if candidate):continue
            config_path=folder/"mkxp.json";regular(config_path)
            conf=jsonc(config_path.read_text("utf-8-sig"))
            profile=namespace(token)
            if any(conf.get(k)!=profile[k] for k in ("dataPathApp","dataPathOrg")):continue
            candidates.append((path.stat().st_mtime_ns,copy_token,token))
        except (OSError,ValueError,TypeError,KeyError):continue
    return max(candidates)[2] if candidates else None


def build_files(base:Path,project:Path=ROOT):
    base=safe_path(base)
    if not base.is_dir():fail("GAME_FOLDER_NOT_FOUND")
    for name in ("Game.exe","Game.ini","mkxp.json","Data/MapInfos.rxdata",
                 "Data/Tilesets.rxdata","Data/System.rxdata","Data/Scripts.rxdata",
                 "PBS/trainer_types.txt","PBS/pokemon.txt","PBS/moves.txt",
                 QA_TITLE_PLUGIN):
        regular(base/name)
    # Existing Sinnoh previews/plugins could conflict with experimental bootstrap.
    if (base/EXPERIMENT_PLUGIN).exists() or (base/INTRO_PLUGIN).exists():
        fail("SINNOH_ALREADY_PRESENT_IN_BASE_UNSUPPORTED")
    infos=read_marshal((base/"Data/MapInfos.rxdata").read_bytes(),"LOCAL_INFOS")
    tiles=read_marshal((base/"Data/Tilesets.rxdata").read_bytes(),"LOCAL_TILESETS")
    j11c.validate_baseline(infos,tiles)
    ids,mapping,occupied=select_ids(base,infos)
    src_barry,barry_files=build_barry(base,root=project)
    if src_barry.get("status")!="VALIDATED_NATIVE_PBS_DRAFT_NOT_COMPILED":
        fail("BARRY_PBS_SOURCE_INVALID")
    empty,manifest=j11c.mock_or_private_native_overlay(
      infos,tiles,ids,occupied=occupied,protected=set(),
      synthetic_fixture=False,
      baseline_hashes={"mapinfos":sha((base/"Data/MapInfos.rxdata").read_bytes()),
                       "tilesets":sha((base/"Data/Tilesets.rxdata").read_bytes())})
    maps,events,start=compile_events(empty,mapping)
    maps=visual.upgrade(maps,mapping,manifest["tileset_ids"],events,start)
    sources=private_visual.discover(project)
    imported={}
    story={}
    continuity={}
    movement=b""
    teleport=b""
    teleport_entries=[]
    forest_code=b""
    forest_report={}
    city_report={}
    route_report={}
    natural_report={}
    interior_report={}
    connection_report={}
    previous_maps=None
    intermediate_maps=None
    refined_maps=None
    f08c_report={}
    f09_report={}
    f09b_report={}
    f09c_report={}
    f09d_report={}
    f10b_report={}
    f10b7_report={}
    f10b_plugin=b""
    pre_f10b_maps=None
    f10b2_maps=None
    f10b3_maps=None
    f10b4_maps=None
    f10b5_maps=None
    f10b6_maps=None
    f10b8_maps=None
    f10c_report={}
    f10c1_maps=None
    f10c2_maps=None
    f11a_report={}
    f11a_plugin=b""
    f11a_maps=None
    f11b_report={}
    f11b_plugin=b""
    f11b_maps=None
    f11c_report={}
    f11c_plugin=b""
    f11c_maps=None
    f11d_report={}
    f11d_plugin=b""
    f11d_maps=None
    f11e_report={}
    f11e_plugin=b""
    f11e_maps=None
    f11f_report={}
    f11f_plugin=b""
    f11f_maps=None
    f11g_report={}
    f11g_plugin=b""
    f11g_maps=None
    f11h_report={}
    f12b3_report=f12b3_windworks.blocked("requires_full_f11h_baseline")
    f12b4_report={"status":"WINDWORKS_ACCESS_BLOCKED","new_seams":0,"runtime_install_enabled":False}
    f12b4_maps=None
    f12b5_report={}
    f12b5_pickup_report={"status":"NOT_EVALUATED","items_granted":0,"native_verified":False}
    f12c_report={"status":"NOT_EVALUATED","runtime_install_enabled":False,"native_verified":False}
    f12c4_report={"status":"NOT_EVALUATED","runtime_install_enabled":False,"native_verified":False}
    f12c_previous_maps=None
    f12c4_plugin=b""
    f12d_plugin=b""
    f12d_previous_maps=None
    f12d_report={"status":"NOT_EVALUATED","runtime_install_enabled":False,"native_verified":False}
    f12d_integrated_report={"status":"NOT_EVALUATED","runtime_install_enabled":False,"native_verified":False}
    f12d_integrated_previous_maps=None
    f12d_integrated_plugin=b""
    regional_catalogue_report={"status":"NOT_EVALUATED"}
    f12b5_plugin=b""
    f11h_plugin=b""
    f10c_plugin=b""
    encounter_expected={}
    encounter_coverage={}
    route_trainers=[]
    if "maps" in sources:
        extra=next((i for i in range(442,518) if i not in occupied and i not in ids),None)
        if extra is None:fail("NO_FREE_LAKEFRONT_QA_ID")
        mapping[private_visual.LAKEFRONT]=extra
        print("SINNOH QA: importando seis exteriores e quatro interiores autorais do ZIP local (sem eventos externos)",flush=True)
        maps,components,imported=private_visual.apply_maps(maps,mapping,sources["maps"])
        maps,events,start=compile_events(maps,mapping,components,{**private_visual.ANCHORS,**private_visual.INTERIOR_ANCHORS})
        maps,continuity=private_visual.bind_audio_and_connections(maps,mapping,components,sources["maps"],base)
        maps,story=private_visual.extend_lake_story(maps,mapping,components)
        masks=private_visual.movement_masks(maps,mapping)
        private_visual.verify_starter_corridor(masks,mapping)
        movement=private_visual.movement_plugin(masks,mapping["SINNOH_ROUTE_202"])
        maps["PBS/encounters.txt"],encounter_coverage=private_visual.coverage_encounters(base,mapping,masks)
        maps,route_trainers=private_visual.route202_trainer_events(maps,mapping,components)
        maps["PBS/trainers_sinnoh_route202.txt"]=private_visual.route202_trainer_pbs(base)
        for role in ("YOUNGSTER","LASS"):
            maps["Graphics/Characters/SNQA_"+role+".png"]=sprite_png("NPC")
        maps,mapping,components,city_report=city_expansion.append(maps,mapping,components,sources["maps"],occupied,project)
        maps,mapping,components,route_report=route_expansion.append(maps,mapping,components,sources["maps"],occupied,project)
        maps,mapping,components,natural_report=natural_expansion.append(maps,mapping,components,sources["maps"],occupied,project)
        maps,mapping,components,interior_report=interior_expansion.append(maps,mapping,components,sources["maps"],occupied,project)
        previous_maps=maps
        intermediate_maps,_=connection_expansion.append(maps,mapping,components,sources["maps"],project)
        maps,connection_report=connection_expansion.append(maps,mapping,components,sources["maps"],project,refine=True)
        refined_maps=maps
        maps,mapping,components,f08c_report=f08c_expansion.append(maps,mapping,components,sources["maps"],occupied,connection_report,project)
        masks=private_visual.movement_masks(maps,mapping,extra_symbols=city_expansion.CITIES|route_expansion.ROUTES|natural_expansion.NATURAL|interior_expansion.INTERIORS|f08c_expansion.EXTERIORS)
        # Existing early-route PBS bytes and all MapIDs/events stay intact.
        maps["PBS/encounters.txt"],encounter_coverage,f09_report=f09_encounters.append(
            maps["PBS/encounters.txt"],encounter_coverage,base,mapping,masks,sources["maps"],project)
        maps["PBS/encounters.txt"],encounter_coverage,f09b_report=f09b_original.append(
            maps["PBS/encounters.txt"],encounter_coverage,base,mapping,masks,sources["maps"],project)
        maps["PBS/encounters.txt"],encounter_coverage,f09c_report=f09c_refinement.append(
            maps["PBS/encounters.txt"],encounter_coverage,base,mapping,masks,maps,sources["maps"],f09b_report,project)
        maps["PBS/encounters.txt"],encounter_coverage,f09d_report,encounter_expected=f09d_relative.append(
            maps["PBS/encounters.txt"],encounter_coverage,base,mapping,masks,sources["maps"],f09c_report,project)
        pre_f10b_maps=maps
        f10b2_maps,_,_=f10b_trainers.append(maps,mapping,masks,components,sources["maps"],base,project,overworlds=sources.get("overworlds"),revision=2)
        f10b3_maps,_,_=f10b_trainers.append(maps,mapping,masks,components,sources["maps"],base,project,overworlds=sources.get("overworlds"),revision=3)
        f10b4_maps,_,_=f10b_trainers.append(maps,mapping,masks,components,sources["maps"],base,project,overworlds=sources.get("overworlds"),revision=4)
        f10b5_maps,_,_=f10b_trainers.append(maps,mapping,masks,components,sources["maps"],base,project,overworlds=sources.get("overworlds"),revision=5)
        maps,f10b_report,f10b_plugin=f10b_trainers.append(maps,mapping,masks,components,sources["maps"],base,project,overworlds=sources.get("overworlds"),revision=6)
        f10b6_maps=maps
        f10b7_report=f10b7_field_audit.audit(maps,mapping,components,sources["maps"],project)
        print("SINNOH_F10B7_FIELD_GATE_REPORT "+json.dumps(f10b7_report,sort_keys=True),flush=True)
        maps,f10b_report,f10b_plugin=f10b_trainers.append(pre_f10b_maps,mapping,masks,components,sources["maps"],base,project,overworlds=sources.get("overworlds"),revision=8)
        movement=private_visual.movement_plugin(masks,mapping["SINNOH_ROUTE_202"])
        teleport_entries=qa_teleport.build(maps,mapping,components,project)
        teleport=qa_teleport.plugin(teleport_entries,project)
        f10b8_maps=maps
        f10c1_maps,_,_=f10c_npcs.build(maps,mapping,masks,components,sources["maps"],base,project,revision=1)
        maps,f10c_report,f10c_plugin=f10c_npcs.build(maps,mapping,masks,components,sources["maps"],base,project,revision=2)
        f10c2_maps=maps
        print("SINNOH_F10C_NPC_REPORT "+json.dumps(f10c_report,sort_keys=True),flush=True)
        forest_png,forest_code,forest_report=forest_edge.build(maps,mapping,project,extra_symbols=city_expansion.CITIES|route_expansion.ROUTES|natural_expansion.OUTDOORS|f08c_expansion.EXTERIORS)
        maps[forest_edge.TEXTURE]=forest_png
        catalogue_delta,regional_catalogue_report=regional_catalogue.prepare(base,maps)
        maps={**maps,**catalogue_delta}
        print("SINNOH_PRIVATE_REGIONAL_CATALOGUE_REPORT "+json.dumps(regional_catalogue_report,sort_keys=True),flush=True)
        maps,mapping,components,f11a_report,f11a_plugin=f11a_gym.append(maps,mapping,components,occupied,base,project,sources.get("overworlds"),allow_authored=True)
        print("SINNOH_F11A2_GYM_REPORT "+json.dumps(f11a_report,sort_keys=True),flush=True)
        f11a_maps=maps
        maps,mapping,components,f11b_report,f11b_plugin=f11a_gym.append(maps,mapping,components,occupied,base,project,sources.get("overworlds"),leader="Gardenia",allow_authored=True)
        print("SINNOH_F11B_GYM_REPORT "+json.dumps(f11b_report,sort_keys=True),flush=True)
        f11b_maps=maps
        maps,mapping,components,f11c_report,f11c_plugin=f11a_gym.append(maps,mapping,components,occupied,base,project,sources.get("overworlds"),leader="Fantina",allow_authored=True)
        print("SINNOH_F11C_GYM_REPORT "+json.dumps(f11c_report,sort_keys=True),flush=True)
        f11c_maps=maps
        maps,mapping,components,f11d_report,f11d_plugin=f11a_gym.append(maps,mapping,components,occupied,base,project,sources.get("overworlds"),leader="Maylene",allow_authored=True)
        print("SINNOH_F11D_GYM_REPORT "+json.dumps(f11d_report,sort_keys=True),flush=True)
        f11d_maps=maps
        maps,mapping,components,f11e_report,f11e_plugin=f11a_gym.append(maps,mapping,components,occupied,base,project,sources.get("overworlds"),leader="Crasher Wake",allow_authored=True)
        print("SINNOH_F11E_GYM_REPORT "+json.dumps(f11e_report,sort_keys=True),flush=True)
        f11e_maps=maps
        maps,mapping,components,f11f_report,f11f_plugin=f11a_gym.append(maps,mapping,components,occupied,base,project,sources.get("overworlds"),leader="Byron",allow_authored=True)
        print("SINNOH_F11F_GYM_REPORT "+json.dumps(f11f_report,sort_keys=True),flush=True)
        f11f_maps=maps
        maps,mapping,components,f11g_report,f11g_plugin=f11a_gym.append(maps,mapping,components,occupied,base,project,sources.get("overworlds"),leader="Candice",allow_authored=True)
        print("SINNOH_F11G_GYM_REPORT "+json.dumps(f11g_report,sort_keys=True),flush=True)
        f11g_maps=maps
        maps,mapping,components,f11h_report,f11h_plugin=f11a_gym.append(maps,mapping,components,occupied,base,project,sources.get("overworlds"),leader="Volkner",allow_authored=True)
        print("SINNOH_F11H_GYM_REPORT "+json.dumps(f11h_report,sort_keys=True),flush=True)
        f12b3_report=f12b3_windworks.preflight(maps,mapping,sources["maps"],project)
        print("SINNOH_F12B3_WINDWORKS_INSTALLER_PREFLIGHT "+json.dumps(f12b3_report,sort_keys=True),flush=True)
        maps,mapping,components,f12b4_report=f12b4_windworks.append(maps,mapping,components,sources["maps"],occupied,project)
        print("SINNOH_F12B4_WINDWORKS_ACCESS_REPORT "+json.dumps(f12b4_report,sort_keys=True),flush=True)
        f12b4_maps=maps
        if f12b4_report.get("runtime_install_enabled"):
            try:
                f12b5_pickup_report=f12b5_pickups.audit(base,f12b5_quest.pickup_candidates(sources["maps"]))
            except (OSError,ValueError,TypeError,KeyError,UnicodeError) as exc:
                f12b5_pickup_report={"status":"BLOCKED","reason":"source_diagnostic_failed:"+type(exc).__name__,"items_granted":0,"native_verified":False}
            print("SINNOH_F12B5_LOCAL_PICKUP_CATALOG_REPORT "+json.dumps(f12b5_pickup_report,sort_keys=True),flush=True)
        maps,f12b5_report,f12b5_plugin=f12b5_quest.append(maps,mapping,components,base,project)
        print("SINNOH_F12B5_AUTHORED_QUEST_REPORT "+json.dumps(f12b5_report,sort_keys=True),flush=True)
        if set(mapping)==f12b4_windworks.ALL:
            try:
                audit=f12c_audit.audit(maps,mapping,sources["maps"])
                delta,pr=f12c_preview.preview(maps,mapping,components,occupied,audit,project)
                local_quest=f12c_quest.local_preview(maps,mapping,delta,pr,base,project)
                f12c_report={"source":audit,"preview":pr,"entry_source":f12c_quest.entrance_source(sources["maps"]),"local_quest":local_quest,"runtime_install_enabled":False,"native_verified":False}
                f12c_previous_maps=maps
                maps,mapping,components,f12c4_report,f12c4_plugin=f12c_install.append(maps,mapping,components,delta,pr,base,project,f12b5_report)
                print("SINNOH_F12C4_INSTALL_REPORT "+json.dumps(f12c4_report,sort_keys=True),flush=True)
            except (OSError,ValueError,TypeError,KeyError,UnicodeError) as exc:
                f12c_report={"status":"BLOCKED","reason":"audit_failed:"+type(exc).__name__,"runtime_install_enabled":False,"native_verified":False}
            print("SINNOH_F12C_INSTALLER_PREFLIGHT_REPORT "+json.dumps(f12c_report,sort_keys=True),flush=True)
        if f12c4_report.get("runtime_install_enabled"):
            f12d_previous_maps=maps
            maps,f12d_report,f12d_plugin=f12d_runtime.append(maps,mapping,components,base,project,sources["maps"])
            print("SINNOH_F12D_RUNTIME_REPORT "+json.dumps(f12d_report,sort_keys=True),flush=True)
            if f12d_report.get("runtime_install_enabled"):
                candidate={}
                f12d_integrated_report=f12d_integrated.installer_preflight(maps,mapping,components,f12d_report,base,project,sources["maps"],staged=candidate)
                if f12d_integrated_report.get("runtime_install_enabled"):
                    f12d_integrated_previous_maps=maps
                    maps=candidate["maps"];f12d_integrated_plugin=candidate["plugin"]
                print("SINNOH_F12D_INTEGRATED_INSTALLER_PREFLIGHT_REPORT "+json.dumps(f12d_integrated_report,sort_keys=True),flush=True)
        gym_symbols=set(mapping)-f08c_expansion.ALL
        if gym_symbols:
            masks=private_visual.movement_masks(maps,mapping,extra_symbols=city_expansion.CITIES|route_expansion.ROUTES|natural_expansion.NATURAL|interior_expansion.INTERIORS|f08c_expansion.EXTERIORS|gym_symbols)
            movement=private_visual.movement_plugin(masks,mapping["SINNOH_ROUTE_202"])
        teleport_mapping={k:v for k,v in mapping.items() if k not in f12c_preview.SYMBOLS}
        teleport_entries=qa_teleport.build(maps,teleport_mapping,components,project)
        teleport=qa_teleport.plugin(teleport_entries,project)
        story["grass_guard"]=True
        story["visual_only_connections_omitted"]=2
        ids=list(mapping.values())
    if "overworlds" in sources:
        print("SINNOH QA: sprites DPPt locais; creditos PurpleZaffre",flush=True)
        maps=private_visual.apply_sprites(maps,sources["overworlds"])
    platinum_player=private_visual.has_platinum_player(base)
    platinum_dawn=private_visual.has_platinum_player(base,10)
    token=secrets.token_hex(6)
    base_hash=sha((base/"Data/MapInfos.rxdata").read_bytes())
    save_token=compatible_save_token(project,mapping,base_hash,maps,previous_maps,intermediate_maps,refined_maps,pre_f10b_maps,f10b2_maps,f10b3_maps,f10b4_maps,f10b5_maps,f10b6_maps,f10b8_maps,f10c1_maps,f10c2_maps,f11a_maps,f11b_maps,f11c_maps,f11d_maps,f11e_maps,f11f_maps,f11g_maps,f12b4_maps,f12c_previous_maps,f12d_previous_maps,f12d_integrated_previous_maps) or token
    config,game_ini,profile=runtime_config(base,save_token)
    # This is an isolated copy, never the installed game:
    final=dict(maps)
    final.update(barry_files)
    final.update({
        "Graphics/Characters/SNQA_NPC.png":sprite_png("NPC"),
        "Graphics/Characters/SNQA_BALL.png":sprite_png("BALL"),
        "Data/System.rxdata":None,
        "Data/Scripts.rxdata":patch_bootstrap((base/"Data/Scripts.rxdata").read_bytes(),token,ids,connected=bool(continuity),story_profile=bool(story),save_token=save_token,route201=mapping["SINNOH_ROUTE_201"] if story else None,encounter_coverage={mapping[sym]:v["methods"] for sym,v in encounter_coverage.items() if v["methods"]},route_trainers=bool(route_trainers),encounter_expected=encounter_expected,f10b=bool(f10b_report.get("new_trainers")),f11a=bool(f11a_report.get("gym_leaders_added")),f11b=bool(f11b_report.get("gym_leaders_added")),f11c=bool(f11c_report.get("gym_leaders_added")),f11d=bool(f11d_report.get("gym_leaders_added")),f11e=bool(f11e_report.get("gym_leaders_added")),f11f=bool(f11f_report.get("gym_leaders_added")),f11g=bool(f11g_report.get("gym_leaders_added")),f11h=bool(f11h_report.get("gym_leaders_added")),f12b5=bool(f12b5_report.get("candidate_runtime_handlers")),f12c4=bool(f12c4_report.get("runtime_install_enabled")),f12d=bool(f12d_report.get("runtime_install_enabled")),f12d_integrated=bool(f12d_integrated_report.get("runtime_install_enabled"))),
        "mkxp.json":config,"Game.ini":game_ini,
        # Only inside the NEW private QA copy. Blue-Story source-only sync
        # cannot update the installed main-game title when Kanto is 142/145.
        # Refresh the title plugin in QA so Testar Sinnoh routes to local
        # New Game instead of searching for the legacy Sinnoh pilot.json.
        QA_TITLE_PLUGIN:(project/"scripts/battle_polish/TitleKanto.rb").read_bytes(),
        f"{INTRO_PLUGIN}/SinnohPilot.rb":(project/"scripts/regions/SinnohPilot.rb").read_bytes(),
        f"{INTRO_PLUGIN}/meta.txt":b"Name = Blue Sinnoh Intro\nVersion = 0.1\nEssentials = 21.1\nScripts = SinnohPilot.rb\n",
        f"{EXPERIMENT_PLUGIN}/SinnohExperimentalStart.rb":experiment_plugin(
                  [mapping["SINNOH_PLAYER_BEDROOM"],*start],token,platinum_player,platinum_dawn,story_profile=bool(story))+b"\n"+movement+b"\n"+teleport+b"\n"+forest_code+b"\n"+f10b_plugin+b"\n"+f10c_plugin+b"\n"+f11a_plugin+b"\n"+f11b_plugin+b"\n"+f11c_plugin+b"\n"+f11d_plugin+b"\n"+f11e_plugin+b"\n"+f11f_plugin+b"\n"+f11g_plugin+b"\n"+f11h_plugin+b"\n"+f12b5_plugin+b"\n"+f12c4_plugin+b"\n"+f12d_plugin+b"\n"+f12d_integrated_plugin,
        f"{EXPERIMENT_PLUGIN}/meta.txt":b"Name = Blue Sinnoh Experimental\nVersion = 0.1\nEssentials = 21.1\nRequires = Blue Sinnoh Intro\nScripts = SinnohExperimentalStart.rb\n",
    })
    sysdata=read_marshal((base/"Data/System.rxdata").read_bytes(),"BASE_SYSTEM")
    if not isinstance(sysdata,RubyObject) or sysdata.name!="RPG::System":
        fail("BAD_NATIVE_RPG_SYSTEM")
    sysdata.attrs.update({"@start_map_id":mapping["SINNOH_PLAYER_BEDROOM"],
                          "@start_x":start[0],"@start_y":start[1]})
    final["Data/System.rxdata"]=serialize(sysdata,SYSTEM_CLASSES)
    # A native first-run compiler may regenerate Tilesets.rxdata. The title
    # may restore only these exact preverified bytes, never accept a new hash.
    # This is inside the isolated QA copy, never the user's main installation.
    final["Data/sinnoh-experimental-tilesets-pristine.bin"]=final["Data/Tilesets.rxdata"]
    file_hashes={path:sha(content) for path,content in final.items()}
    if f12d_integrated_report.get("runtime_install_enabled"):
        # Bind the private compile receipt to its maps, connections, PBS,
        # generated plugin and base instead of just the map index.
        identity={"profile":token,"base_mapinfos_sha256":base_hash,"files":file_hashes}
        proof=sha(json.dumps(identity,sort_keys=True,separators=(",",":")).encode("ascii"))
    else:
        proof=sha(("SinnohExperimental:"+token+file_hashes["Data/MapInfos.rxdata"]).encode())
    final["Data/sinnoh-experimental-compile-request.txt"]=proof.encode("ascii")
    # These hashes do not claim human rights approval, or native gameplay acceptance.
    report={"schema":1,"region":"SINNOH","mode":MODE,
        "maps_prepared":len(mapping),"static_events_placed":len(events)+story.get("extra_event_count",0)+len(route_trainers)+len(connection_report.get("portals",[]))+len(f08c_report.get("portals",[]))+f10b_report.get("new_trainers",0)+f10c_report.get("new_npcs",0)+f11a_report.get("gym_leaders_added",0)+f11a_report.get("new_portals",0)+f11b_report.get("gym_leaders_added",0)+f11b_report.get("new_portals",0)+f11c_report.get("gym_leaders_added",0)+f11c_report.get("new_portals",0)+f11d_report.get("gym_leaders_added",0)+f11d_report.get("new_portals",0)+f11e_report.get("gym_leaders_added",0)+f11e_report.get("new_portals",0)+f11f_report.get("gym_leaders_added",0)+f11f_report.get("new_portals",0)+f11g_report.get("gym_leaders_added",0)+f11g_report.get("new_portals",0)+f11h_report.get("gym_leaders_added",0)+f11h_report.get("new_portals",0)+f12b5_report.get("new_events",0)+f12c4_report.get("new_events",0)+f12d_report.get("new_events",0)+f12d_integrated_report.get("new_events",0),
        "static_warps":16-len(continuity.get("retired_warp_keys",[]))+(3 if story else 0)+len(connection_report.get("portals",[]))+len(f08c_report.get("portals",[])),"native_seam_pairs":sum(not p.get("visual_only") for p in continuity.get("connections",[]))+len(connection_report.get("seams",[]))+f12b4_report.get("new_seams",0)+f12d_report.get("new_seams",0)+f12d_integrated_report.get("new_seams",0),"static_handlers":5,"static_starter_balls":3,
        "local_reserved_qa_only":True,"independent_r07_approved":False,
        "independent_r08_approved":False,"r09_native_qa_executed":0,
        "game_exe_executed":False,"runtime_playable_verified":False,
        "main_game_modified":False,"personal_saves_copied":False,
        "save_profile":profile,"profile_token":token,"save_profile_token":save_token,
        "mapids":mapping,"start":[mapping["SINNOH_PLAYER_BEDROOM"],*start],
        "coordinates_provenance":"PRIVATE_DONOR_GEOMETRY_AND_MODEL_PASSABILITY_ONLY" if imported else "ORIGINAL_GENERATED_GEOMETRY_AND_MODEL_PASSABILITY_ONLY",
        "private_visual_import":{"maps":imported,"overworlds":"overworlds" in sources,
                                 "platinum_player":platinum_player,"platinum_dawn":platinum_dawn,"credits":private_visual.CREDITS if sources else "",
                                 "source_sha256":{k:private_visual.PACKS[k][1] for k in sources},
                                 "native_approved":False,"distribution_approved":False},
        "visual_revision":"SINNOH_ORIGINAL_PIXEL_ART_V2",
        "private_continuity":continuity,
        "private_lake_story":story,
        "forest_edge":forest_report,
        "city_expansion":city_report,
        "route_expansion":route_report,
        "natural_expansion":natural_report,
        "interior_expansion":interior_report,
        "connection_expansion":connection_report,
        "f08c_expansion":f08c_report.get("maps",{}),
        "f08c_connections":f08c_report,
        "f09_encounters":f09_report,
        "f09b_original_encounters":f09b_report,
        "f09c_refinement":f09c_report,
        "f09d_relative":f09d_report,
        "f10b_trainers":f10b_report,"f10b7_field_gate_audit":f10b7_report,"f10c_npcs":f10c_report,"f11a_gym":f11a_report,"f11b_gym":f11b_report,"f11c_gym":f11c_report,"f11d_gym":f11d_report,"f11e_gym":f11e_report,"f11f_gym":f11f_report,"f11g_gym":f11g_report,"f11h_gym":f11h_report,
        "f12b3_windworks_preflight":f12b3_report,
        "f12b4_windworks_access":f12b4_report,
        "f12b5_authored_quest":f12b5_report,
        "f12b5_local_pickup_catalog":f12b5_pickup_report,
        "f12c_eterna_preflight":f12c_report,
        "f12c4_install":f12c4_report,
        "f12d_runtime":f12d_report,
        "f12d_integrated":f12d_integrated_report,
        "private_regional_catalogue":regional_catalogue_report,
        "qa_teleport":{"catalog_count":len(teleport_entries),"available_count":sum(row[3] is not None for row in teleport_entries),"destinations":teleport_entries,"native_verified":False},
        "encounter_coverage":encounter_coverage,"route202_trainers":route_trainers,
        "visual_native_reviewed":False,
        "human_positions_reviewed":False,"native_collision_verified":False,
        "compile_token":proof,
        "file_sha256":{**file_hashes,"Data/sinnoh-experimental-compile-request.txt":sha(proof.encode("ascii"))},
        "base_mapinfos_sha256":base_hash}
    final["sinnoh-experimental-qa.json"]=(json.dumps(report,indent=2,sort_keys=True,ensure_ascii=False)+"\n").encode()
    return final,report

def scan_source(base:Path):
    base=safe_path(base)
    if not base.is_dir():fail("LOCAL_GAME_NOT_FOUND")
    seen=set();files={};total=0
    for current,dirs,names in os.walk(base):
        here=Path(current)
        rel=here.relative_to(base)
        if rel==Path("."):
            dirs[:]=[d for d in dirs if d in ROOT_DIRS]
            names=[n for n in names if n in ROOT_COPY or n.lower().endswith(".dll")]
        else:
            dirs[:]=[d for d in dirs if d.casefold() not in SKIP_PARTS]
        for d in dirs:safe_path(here/d)
        for name in names:
            if SKIP_FILES.fullmatch(name) or name.lower().endswith((".bak",".log",".tmp")):
                continue
            path=safe_path(here/name)
            if not path.is_file():fail("NONFILE_SOURCE_ENTRY")
            relpath=path.relative_to(base).as_posix()
            key=relpath.casefold()
            if key in PRIVATE_EXCLUDED_REQUESTS:
                # The live official verification request stays untouched.
                continue
            if key in seen:fail("WINDOWS_CASE_COLLISION")
            seen.add(key);files[relpath]=path
            total+=path.stat().st_size
            if len(files)>MAX_FILES or total>MAX_BYTES:fail("GAME_COPY_TOO_LARGE")
    for item in ("Game.exe","Game.ini","mkxp.json","Data/Scripts.rxdata","Data/System.rxdata",
                 "Data/MapInfos.rxdata","Data/Tilesets.rxdata"):
        if item not in files:fail("BASE_REQUIRED_FILE_NOT_IN_SNAPSHOT:"+item)
    return files

def install_copy(base:Path,outputs:dict,report:dict,project:Path=ROOT):
    project=safe_path(project)
    base=safe_path(base)
    work=safe_path(project/REPO_OUTPUT)
    # The Blue-Story managed layout is ROOT/game beside ROOT/.blue-work.
    # This overlap is EXPECTED: only the private .blue-work copy is writable.
    # Reject all other nested layouts and any project contained by game.
    managed_game = project / "game"
    if (project == base or project.is_relative_to(base) or
        (base.is_relative_to(project) and base != managed_game)):
        fail("INSTALLER_SOURCE_AND_GAME_OVERLAP")
    if work.is_relative_to(base) or work == base:
        fail("QA_OUTPUT_MUST_BE_OUTSIDE_GAME")
    dest=work/(QA_DIR+"-"+report["profile_token"])
    if dest.exists() or dest.is_symlink() or work.is_symlink():
        fail("OUTPUT_EXISTS_OR_UNSAFE")
    original=scan_source(base)
    for rel in outputs:
        if isinstance(rel,str) and rel.casefold() in PRIVATE_EXCLUDED_REQUESTS:
            fail("QA_FOREIGN_REQUEST_NOT_ALLOWED")
        if not isinstance(rel,str) or "\\" in rel or ".." in PurePosixPath(rel).parts:
            fail("UNSAFE_OUTPUT_PATH")
        if rel.startswith("Data/Map") and re.fullmatch(r"Data/Map\d{3}\.rxdata",rel):
            if rel in original:fail("WOULD_OVERWRITE_NATIVE_MAP")
        if rel.startswith("Audio/BGM/SNQA_") and any(rel.casefold()==x.casefold() for x in original):
            fail("WOULD_OVERWRITE_EXISTING_AUDIO")
        if rel.startswith(("Plugins/","Graphics/")) and rel in original:
            if rel == QA_TITLE_PLUGIN:
                # The sole allowlisted replacement is a project-owned Title
                # plugin in the newly created QA copy, NEVER in the source.
                verified=(project/"scripts/battle_polish/TitleKanto.rb")
                if (not verified.is_file() or verified.is_symlink() or
                    original[rel] != base/QA_TITLE_PLUGIN or
                    outputs[rel] != verified.read_bytes()):
                    fail("QA_TITLE_PLUGIN_OVERRIDE_NOT_TRUSTED")
            else:
                fail("WOULD_OVERWRITE_EXISTING_PLUGIN_OR_GRAPHICS")
    work.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix=".sinnoh-experimental-",dir=work))
    try:
        for rel,source in original.items():
            target=stage.joinpath(*PurePosixPath(rel).parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            if safe_path(source)!=source:fail("SOURCE_PATH_CHANGED")
            shutil.copy2(source,target)
            if source.stat().st_size!=target.stat().st_size:
                fail("COPY_SIZE_MISMATCH")
        for rel,data in sorted(outputs.items()):
            file=stage.joinpath(*PurePosixPath(rel).parts)
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_bytes(data)
            if sha(file.read_bytes())!=sha(data):fail("PATCH_HASH_MISMATCH")
        (stage/"INICIAR_SINNOH_EXPERIMENTAL.bat").write_text(
          '@echo off\ncd /d "%~dp0"\n'
          'if exist "Data\\sinnoh-experimental-compile-error.txt" (\n'
          ' echo ATENCAO: Barry PBS nao compilou. Apenas EXPLORACAO dos 9 mapas QA.\n'
          ' echo Consulte Data\\sinnoh-experimental-compile-error.txt antes de testar Barry.\n)\n'
          'if exist "Data\\sinnoh-experimental-compile-request.txt" (\n'
          ' echo Primeira execucao: compilar os PBS Barry somente nesta copia.\n'
          ' start "" /wait "Game.exe"\n'
          ' if not exist "Data\\sinnoh-experimental-compiled.txt" (\n'
          ' echo Barry ainda nao foi compilado; Novo Jogo SOMENTE no modo exploracao QA.\n'
          ' echo Batalha contra Barry bloqueada ate verificacao nativa.\n)\n'
          ')\nstart "" "Game.exe"\n',encoding="utf-8")
        (stage/"LEIA_ANTES_SINNOH.txt").write_text(
          "PILOTO EXPERIMENTAL SINNOH - SOMENTE COPIA PRIVADA\n"
          "Duplo clique INICIAR_SINNOH_EXPERIMENTAL.bat.\n"
          "Primeira execucao tenta compilar PBS Barry; sem compilacao, apenas exploracao QA.\n"
          "Mapas privados foram adicionados a esta copia; nunca ao seu game original.\n"
          "Coordenadas verificadas SOMENTE pelo modelo estatico, nao por Game.exe.\n"
          "R07/R08/R09 pendentes; nenhum teste nativo relatado pelo GitHub.\n",encoding="utf-8")
        # Proof only for what Python actually generated; no gameplay-ready marker.
        (stage/"sinnoh-experimental-copy-transaction.json").write_text(
            json.dumps({"schema":1,"mode":MODE,"qa_only":True,
                "original_game":str(base),"source_file_count":len(original),
                "map_ids":report["mapids"],"r07_independent":False,
                "native_qa_executed":0,"save_profile":report["save_profile"],
                "overlay_hashes":report["file_sha256"]},indent=2,ensure_ascii=False)+"\n",
            encoding="utf-8")
        if dest.exists():fail("OUTPUT_CREATED_CONCURRENTLY")
        stage.rename(dest)
    finally:
        if stage.exists():shutil.rmtree(stage)
    return dest

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game",type=Path,default=DEFAULT_GAME)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--install",action="store_true",help="Create the QA copy; never modify --game")
    args=parser.parse_args(argv)
    try:
        base=safe_path(args.game)
        project=safe_path(args.project)
        outputs,report=build_files(base,project)
        if args.install:
            dest=install_copy(base,outputs,report,project)
            report.update(installed_into_separate_qa_copy=True,
                          experimental_qa_directory=str(dest),
                          launch_file=str(dest/"INICIAR_SINNOH_EXPERIMENTAL.bat"))
        else:
            report.update(installed_into_separate_qa_copy=False,
                          experimental_qa_directory=None)
        print(json.dumps(report,indent=2,ensure_ascii=False))
        return 0
    except (OSError,ValueError,TypeError,KeyError,UnicodeError,OverflowError,
            struct.error,zlib.error) as exc:
        print("INSTALADOR_SINNOH_BLOQUEADO:"+str(exc),file=sys.stderr)
        return 2

if __name__=="__main__":raise SystemExit(main())
