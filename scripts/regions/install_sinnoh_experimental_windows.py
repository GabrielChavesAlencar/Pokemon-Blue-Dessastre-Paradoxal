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

def plan_events(blobs:dict,mapping:dict):
    """Model-verified coordinates. NEVER claim human or native verification."""
    scenes=all_scenes()
    draft=json.loads((ROOT/"data/regions/sinnoh-twinleaf-events.json").read_text("utf-8"))
    if [row["symbol"] for row in draft["maps"]]!=list(MAPS):
        fail("CH06_SYMBOL_ORDER_MISMATCH")
    chars={}
    for symbol,scene in scenes.items():
        chars[symbol]=component(scene)
    positions={}
    local_used={}
    all_keys=set()
    for row in draft["maps"]:
        symbol=row["symbol"];used=set();chosen={}
        world=read_marshal(blobs["Data/Map%03d.rxdata"%mapping[symbol]],"QA_MAP")
        tiles=read_marshal(blobs["Data/Tilesets.rxdata"],"QA_TILES")
        for event in row["events"]:
            key=event["key"];anchor=ANCHORS.get(key)
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

def compile_events(blobs,mapping):
    records,start=plan_events(blobs,mapping)
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

def patch_bootstrap(raw:bytes,token:str,map_ids=()):
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
    if map_ids and (len(map_ids)!=9 or len(set(map_ids))!=9 or
                    any(type(n) is not int or not 442<=n<=517 for n in map_ids)):
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
    # Essentials normalizes transfer events (door SFX/fades) during PBS
    # compilation and rewrites their maps. These authored QA files are pinned
    # byte-for-byte by the title/supervisor. Preserve their verified input bytes
    # only across this compiler call, without accepting new hashes or touching
    # other maps, trainer output, the source game or a later gameplay session.
    protected=[f"Data/Map{mid:03d}.rxdata" for mid in map_ids]
    protected += ["Data/MapInfos.rxdata","Data/Tilesets.rxdata"] if map_ids else []
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
          File.binwrite(path, original) if File.binread(path) != original
        end
      end
    end
"""
    guarded=guarded.replace("__QA_PROTECTED__"," ".join(protected))
    code=code.replace(anchor,hook+anchor).replace(compiler,guarded+verify)
    code=code.replace("__QA_SCOPE__",scope)
    main[2]=RubyString(zlib.compress(code.encode("utf-8")))
    return b"\x04\x08"+dump(rows)

def experiment_plugin(start,token):
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
    return code.encode("utf-8")

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
    token=secrets.token_hex(6)
    config,game_ini,profile=runtime_config(base,token)
    # This is an isolated copy, never the installed game:
    final=dict(maps)
    final.update(barry_files)
    final.update({
        "Graphics/Characters/SNQA_NPC.png":sprite_png("NPC"),
        "Graphics/Characters/SNQA_BALL.png":sprite_png("BALL"),
        "Data/System.rxdata":None,
        "Data/Scripts.rxdata":patch_bootstrap((base/"Data/Scripts.rxdata").read_bytes(),token,ids),
        "mkxp.json":config,"Game.ini":game_ini,
        # Only inside the NEW private QA copy. Blue-Story source-only sync
        # cannot update the installed main-game title when Kanto is 142/145.
        # Refresh the title plugin in QA so Testar Sinnoh routes to local
        # New Game instead of searching for the legacy Sinnoh pilot.json.
        QA_TITLE_PLUGIN:(project/"scripts/battle_polish/TitleKanto.rb").read_bytes(),
        f"{INTRO_PLUGIN}/SinnohPilot.rb":(project/"scripts/regions/SinnohPilot.rb").read_bytes(),
        f"{INTRO_PLUGIN}/meta.txt":b"Name = Blue Sinnoh Intro\nVersion = 0.1\nEssentials = 21.1\nScripts = SinnohPilot.rb\n",
        f"{EXPERIMENT_PLUGIN}/SinnohExperimentalStart.rb":experiment_plugin(
                  [mapping["SINNOH_PLAYER_BEDROOM"],*start],token),
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
    proof=sha(("SinnohExperimental:"+token+sha(final["Data/MapInfos.rxdata"])).encode())
    final["Data/sinnoh-experimental-compile-request.txt"]=proof.encode("ascii")
    # These hashes do not claim human rights approval, or native gameplay acceptance.
    report={"schema":1,"region":"SINNOH","mode":MODE,
        "maps_prepared":9,"static_events_placed":len(events),
        "static_warps":16,"static_handlers":5,"static_starter_balls":3,
        "local_reserved_qa_only":True,"independent_r07_approved":False,
        "independent_r08_approved":False,"r09_native_qa_executed":0,
        "game_exe_executed":False,"runtime_playable_verified":False,
        "main_game_modified":False,"personal_saves_copied":False,
        "save_profile":profile,"profile_token":token,
        "mapids":mapping,"start":[mapping["SINNOH_PLAYER_BEDROOM"],*start],
        "coordinates_provenance":"ORIGINAL_GENERATED_GEOMETRY_AND_MODEL_PASSABILITY_ONLY",
        "visual_revision":"SINNOH_ORIGINAL_PIXEL_ART_V2",
        "visual_native_reviewed":False,
        "human_positions_reviewed":False,"native_collision_verified":False,
        "compile_token":proof,
        "file_sha256":{path:sha(content) for path,content in final.items()},
        "base_mapinfos_sha256":sha((base/"Data/MapInfos.rxdata").read_bytes())}
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
        if not isinstance(rel,str) or "\\" in rel or ".." in PurePosixPath(rel).parts:
            fail("UNSAFE_OUTPUT_PATH")
        if rel.startswith("Data/Map") and re.fullmatch(r"Data/Map\d{3}\.rxdata",rel):
            if rel in original:fail("WOULD_OVERWRITE_NATIVE_MAP")
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
          "Nove mapas foram adicionados a esta copia; nunca ao seu game original.\n"
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
