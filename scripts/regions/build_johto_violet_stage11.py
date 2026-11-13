"""Johto offline 11/12: author Violet gym, 3 Sprout floors and Center.

Reads the private stage10 (77 existing maps) plus Blue's installed Inside
tileset/PBS, adds 5 NEW maps IDs 677–681, ten reversible warp events and
five story NPCs in an isolated .blue-work copy. No Game.exe, no installed
game/ writes, no badge in advance, no native or third-party binary commits.

Interior artwork is an ORIGINAL provisional layout, NOT a faithful HGSS
room or a proof of engine passability. Missing trainer/Nurse sprites remain
explicit blockers; nothing creates a battle-ready marker.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import shutil
import struct
import sys
import tempfile
from pathlib import Path

from audit_johto import ROOT, checksum, read_map_data
from build_johto_bedroom_v1 import tile
from build_johto_elm_lab_v1 import table_values
from build_johto_events import EVENT_CLASSES, event_page, ruby
from build_johto_routes_stage10 import learn_moves
from pbs import catalogue, read_blocks
from stage import serialize
from server.ruby_marshal import RubyData, RubyObject, loads, text

DEFAULT_SPEC = ROOT / "data/regions/johto-stage11-violet.json"
DEFAULT_STAGE = ROOT / ".blue-work/johto-staging-routes-v1"
DEFAULT_OUTPUT = ROOT / ".blue-work/johto-staging-violet-v1"
CITY = "JOHTO_VIOLET_CITY"
SOURCE_CITY_ID = 602
NEW_IDS = set(range(677, 682))
EXPECTED_WARP_COUNT = 10
EXPECTED_NPC_COUNT = 5
EXPECTED_TRAINER_NAMES = {
    ("BLUE_JOHTO_FALKNER", "Falkner"),
    ("BLUE_JOHTO_ELDER", "Li"),
    ("BLUE_JOHTO_SAGE", "Nico"),
    ("BLUE_JOHTO_SAGE", "Troy"),
}
EXPECTED_SYMBOLS = {
    "JOHTO_VIOLET_GYM":677, "JOHTO_SPROUT_TOWER":678,
    "JOHTO_SPROUT_TOWER_2F":679, "JOHTO_SPROUT_TOWER_3F":680,
    "JOHTO_VIOLET_POKEMON_CENTER":681,
}
PNG = b"\x89PNG\r\n\x1a\n"


def fail(message: str):
    raise ValueError("[JOHTO][OFFLINE 11] " + message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        fail("Contrato/manifesto ausente ou symlink: " + str(path))
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        fail("Contrato deve ser um objeto JSON")
    return value


def validate_contract(spec: dict) -> None:
    if ((spec.get("schema"),spec.get("region"),spec.get("stage"),spec.get("status"),
         spec.get("requires_previous_stage"),spec.get("source_violet_id")) !=
        (1,"JOHTO","OFFLINE_11_VIOLET_SPROUT_FALKNER",
         "PROPOSED_PRIVATE_GEOMETRY_AND_PBS_NOT_GAMEPLAY_VERIFIED",
         "BLUE_ROUTE10_PREVIEW_ONLY_NOT_PLAYABLE",602)):
        fail("Contrato da etapa 11 não autorizado")
    rows = spec.get("interiors")
    if (not isinstance(rows,list) or len(rows)!=5 or
        {r.get("symbol"):r.get("id") for r in rows} != EXPECTED_SYMBOLS or
        any(type(r.get("id")) is not int or r.get("width")!=20 or
            r.get("height")!=16 or r.get("kind") not in ("gym","tower","center")
            for r in rows)):
        fail("Cinco interiores e IDs 677–681 são obrigatórios")
    if {r["parent_id"] for r in rows} - {602,678,679}:
        fail("Parent MapInfo de Violet inválido")
    warps = spec.get("warps")
    npcs = spec.get("npcs")
    if (not isinstance(warps,list) or len(warps)!=10 or
        not isinstance(npcs,list) or len(npcs)!=5):
        fail("A etapa 11 exige 10 warps e 5 NPCs")
    wkeys={r.get("key") for r in warps}
    nkeys={r.get("key") for r in npcs}
    if len(wkeys)!=10 or len(nkeys)!=5 or wkeys & nkeys:
        fail("Chaves dos eventos duplicadas")
    all_symbols=set(EXPECTED_SYMBOLS)|{CITY}
    for w in warps:
        if (w.get("source") not in all_symbols or w.get("target") not in all_symbols
                or not isinstance(w.get("reverse"),str)
                or not isinstance(w.get("key"),str)
                or type(w.get("x")) is not int or type(w.get("y")) is not int
                or not isinstance(w.get("arrival"),list) or len(w["arrival"])!=2
                or any(type(x) is not int for x in w["arrival"])):
            fail("Transição com símbolo/coord inválida")
        inverse=next((r for r in warps if r.get("key")==w["reverse"]),None)
        if not inverse or inverse.get("reverse")!=w["key"] or (
                inverse.get("source"),inverse.get("target"))!=(w["target"],w["source"]):
            fail("Falta retorno do warp " + w["key"])
    allowed_handlers={
        "BlueJohtoViolet.falkner", "BlueJohtoViolet.sprout_elder",
        "BlueJohtoViolet.sprout_sage(:JH_SPROUT_SAGE_NICO)",
        "BlueJohtoViolet.sprout_sage(:JH_SPROUT_SAGE_TROY)",
        "BlueJohtoViolet.center_clerk"
    }
    if {r.get("handler") for r in npcs} != allowed_handlers:
        fail("Handler Ruby de Violet desconhecido")
    for r in npcs:
        if (r.get("source") not in all_symbols or
            type(r.get("x")) is not int or type(r.get("y")) is not int or
            not isinstance(r.get("sprite"),str) or not r["sprite"].startswith("NPC_HGSS_")):
            fail("NPC inválido/sem sprite simbólico")
    trainers=spec.get("trainers")
    if (not isinstance(trainers,list) or len(trainers)!=4 or
        {(t.get("type"),t.get("name")) for t in trainers} != EXPECTED_TRAINER_NAMES):
        fail("Faltam Falkner, Li e dois sages")
    for t in trainers:
        if t.get("base_type") not in ("BIRDKEEPER","GENTLEMAN"):
            fail("Trainer type de origem não validado")
        for variant,n in (("normal",2),("master",4)):
            team=t.get(variant)
            if (not isinstance(team,list) or len(team)!=n or
                any(not isinstance(x,list) or len(x)!=2 or
                    not isinstance(x[0],str) or type(x[1]) is not int or
                    not 1<=x[1]<=100 for x in team)):
                fail("Time normal/Master incompleto")
    rules=spec.get("rules")
    if not isinstance(rules,dict) or rules != {
        "badge":"ZEPHYR","source":"BlueRegions.award","region":"JOHTO",
        "max_awards_per_save":1,"master_team_size":4,"normal_team_size":2,
        "normal_level_ratio":0.7,"master_level_ratio":0.9,
        "wild_level_ratio":0.45,"badge_in_sprout_elder":False,
        "gameplay_playable":False,"tested_in_engine":False,
        "pbs_compiled":False,"installer_integrated":False,
        "trainer_sprites_audited":False
    }:
        fail("Não alterar balanceamento global nem conceder Zephyr antes de vitória")


def room_grid(kind: str, passages: tuple[int,...], w:int=20,h:int=16):
    """Original, simple interior geometry; never clone native map layout."""
    values=[0]*(w*h*3)
    if kind not in ("gym","tower","center"):
        fail("Tipo de interior desconhecido")
    def put(x,y,z,n):
        if not 0<=x<w or not 0<=y<h or not 0<=n<len(passages):
            fail("Tile fora dos limites do Inside")
        values[x+w*(y+h*z)]=n
    for y in range(1,h-1):
        for x in range(1,w-1):
            put(x,y,0,tile(88,(x+y)%2))
    for x in range(1,w-1):
        put(x,0,0,tile(190,3))
        put(x,1,1,tile(191,3))
        put(x,h-1,0,tile(190,0))
    for y in range(h):
        put(0,y,0,tile(190,0))
        put(w-1,y,0,tile(190,0))
    # Decorative fixtures only at side walls: leave all warp / NPC anchors free.
    furniture={"gym":[(2,3,280,0),(17,3,280,4),(2,7,275,4),(17,7,275,4)],
               "tower":[(2,3,275,4),(17,3,275,4),(2,9,275,4),(17,9,275,4)],
               "center":[(3,3,257,0),(15,3,257,0),(2,8,267,0),(17,8,267,0)]}
    for x,y,row,col in furniture[kind]:
        put(x,y,2,tile(row,col))
    raw=struct.pack("<5I",3,w,h,3,len(values))+struct.pack(f"<{len(values)}H",*values)
    return raw


def passage_grid(room: RubyObject, tilesets:list):
    w,h,tid=(room.attrs.get("@width"),room.attrs.get("@height"),
             room.attrs.get("@tileset_id"))
    if (any(type(x) is not int for x in (w,h,tid)) or
        not 5<=w<=500 or not 5<=h<=500 or not 0<tid<len(tilesets)):
        fail("Dimensão/tileset de mapa inválidos")
    raw=room.attrs.get("@data")
    p=tilesets[tid].attrs.get("@passages")
    if not isinstance(raw,RubyData) or not isinstance(p,RubyData):
        fail("RPG::Map / Tileset sem tabelas")
    shape,cells=table_values(raw.data,dimension=3)
    pshape,flags=table_values(p.data,dimension=1)
    if shape!=(w,h,3) or pshape[1:]!=(1,1) or max(cells)>=len(flags):
        fail("Tabela de tiles/passagens inconsistente")
    def walk(x,y):
        return (type(x) is int and type(y) is int and 0<=x<w and 0<=y<h
                and all(not(flags[cells[x+w*(y+h*z)]]&15) for z in range(3)))
    def connected(points):
        pts=set(points)
        if not pts or any(not walk(*point) for point in pts):
            fail("Spawn/warp/NPC em tile estático bloqueado")
        seen={min(pts)}
        queue=[min(pts)]
        for x,y in queue:
            for point in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if point not in seen and walk(*point):
                    seen.add(point);queue.append(point)
        if not pts<=seen:
            fail("Transições/NPCs do mapa não compartilham caminho estático")
        return len(seen)
    return walk,connected


def build_pbs(spec:dict,game:Path)->tuple[dict[str,bytes],dict]:
    validate_contract(spec)
    pbs=game/"PBS"
    needed={p:pbs/p for p in ("trainer_types.txt","pokemon.txt","moves.txt")}
    if not pbs.is_dir() or pbs.is_symlink() or any(
        not p.is_file() or p.is_symlink() for p in needed.values()):
        fail("PBS nativo ausente ou symlink")
    types=read_blocks(needed["trainer_types.txt"])
    if not {"BIRDKEEPER","GENTLEMAN"}<=set(types):
        fail("Trainer types BirdKeeper/Gentleman ausentes")
    reserved={t["type"] for t in spec["trainers"]}
    if any(key in read_blocks(p) for p in pbs.glob("trainer_types*.txt") for key in reserved):
        fail("Trainer type de Violet já existe, prevenir colisão")
    expected={(t["type"],t["name"]) for t in spec["trainers"]}
    for path in pbs.glob("trainers*.txt"):
        if path.is_symlink():fail("Trainer PBS em symlink")
        for header in read_blocks(path):
            parts=header.split(",")
            if len(parts)>=2 and (parts[0],parts[1]) in expected:
                fail("Treinador Violet já existe no PBS nativo")
    names={poke for t in spec["trainers"] for variant in ("normal","master")
           for poke,_ in t[variant]}
    available=catalogue(game,"pokemon")
    moves=catalogue(game,"moves")
    if not names<=available or not moves:
        fail("Espécies/moves não encontrados na base Blue")
    sections=read_blocks(needed["pokemon.txt"],names)
    if set(sections)!=names:
        fail("Learnset da espécie ausente do PBS")
    learnsets={}
    for species,lines in sections.items():
        pairs=[line.partition("=") for line in lines]
        found=[v.strip() for k,sep,v in pairs if sep and k.strip()=="Moves"]
        if len(found)!=1:fail("Movimentos ausentes/duplicados para "+species)
        learnsets[species]=found[0]
    new_types=[]
    used=set()
    for t in spec["trainers"]:
        if t["type"] in used:continue
        used.add(t["type"])
        new_types.append("["+t["type"]+"]")
        new_types.extend("Name = "+({"BLUE_JOHTO_FALKNER":"Leader",
                  "BLUE_JOHTO_ELDER":"Elder","BLUE_JOHTO_SAGE":"Sage"}[t["type"]])
                  if line.strip().startswith("Name =") else line
                  for line in types[t["base_type"]])
        new_types.append("")
    trainers=[]
    roster=[]
    for t in spec["trainers"]:
        for version,kind in ((0,"normal"),(1,"master")):
            trainers.append(f"[{t['type']},{t['name']},{version}]")
            team=[]
            for species,level in t[kind]:
                legal=learn_moves(learnsets[species],moves,level)
                trainers += [f"Pokemon = {species},{level}",
                             "    Moves = "+",".join(legal)]
                team.append({"species":species,"level":level,"moves":legal})
            roster.append({"type":t["type"],"name":t["name"],
                           "version":version,"team":team})
            trainers.append("")
    payloads={
       "PBS/trainer_types_johto_violet.txt":("\n".join(new_types)+"\n").encode(),
       "PBS/trainers_johto_violet.txt":("\n".join(trainers)+"\n").encode()
    }
    return payloads,{
       "trainer_entries":len(roster),"trainer_profiles":roster,
       "native_pbs_sha256":{k:checksum(v) for k,v in needed.items()},
       "pbs_sha256":{n:sha(v) for n,v in payloads.items()},
       "trainer_sprites_verified":False,"pbs_compiled":False,
       "trainer_ready_marker_created":False
    }


def compile_preview(spec:dict,preview:Path,game:Path,payloads:dict,report:dict):
    stage=read_json(preview/"johto-stage.json")
    if ((stage.get("schema"),stage.get("region"),stage.get("status"),
         stage.get("not_playable"),stage.get("can_install")) !=
        (1,"JOHTO","BLUE_ROUTE10_PREVIEW_ONLY_NOT_PLAYABLE",True,False)):
        fail("Entrada deve ser estágio real da etapa 10")
    if len(stage.get("maps",[]))!=77:
        fail("Etapa 10 precisa ter 77 mapas")
    existing={x["symbol"]:x["destination_id"] for x in stage["maps"]}
    if existing.get(CITY)!=602 or len(set(existing.values()))!=77:
        fail("Violet City Map602 não encontrado")
    if NEW_IDS & set(existing.values()):
        fail("IDs 677–681 já utilizados; impedir overwrite")
    infos=read_map_data(preview/"Data/MapInfos.rxdata")
    tiles=read_map_data(preview/"Data/Tilesets.rxdata")
    if not isinstance(infos,dict) or not isinstance(tiles,list):
        fail("MapInfos/Tilesets de origem inválidos")
    if NEW_IDS & set(infos):
        fail("MapInfos já contém IDs novos de Violet")
    template=read_map_data(preview/"Data/Map675.rxdata")
    city=read_map_data(preview/"Data/Map602.rxdata")
    if (not isinstance(template,RubyObject) or template.name!="RPG::Map"
        or not isinstance(city,RubyObject) or city.name!="RPG::Map"
        or not isinstance(city.attrs.get("@events"),dict) or city.attrs["@events"]):
        fail("Template de casa ou cidade Violet não auditados")
    tid=template.attrs.get("@tileset_id")
    if not isinstance(tid,int) or not 0<tid<len(tiles):
        fail("Inside tileset não encontrado")
    info_template=infos.get(675)
    if not isinstance(info_template,RubyObject) or info_template.name!="RPG::MapInfo":
        fail("MapInfo de interiores anteriores ausente")
    old_infos=copy.deepcopy(infos)
    stages={CITY:copy.deepcopy(city)}
    stage_ids=dict(existing)
    order=max((m.attrs.get("@order",0) for m in infos.values()
               if isinstance(m,RubyObject)),default=0)
    passages=tiles[tid].attrs.get("@passages")
    if not isinstance(passages,RubyData):fail("Tileset Inside sem passabilidade")
    _,flags=table_values(passages.data,dimension=1)
    for row in spec["interiors"]:
        mid=row["id"];symbol=row["symbol"]
        if (preview/"Data"/f"Map{mid:03d}.rxdata").exists():
            fail("MapNNN novo já existe")
        room=copy.deepcopy(template)
        room.attrs["@width"],room.attrs["@height"]=row["width"],row["height"]
        room.attrs["@data"]=RubyData("Table",room_grid(row["kind"],flags,row["width"],row["height"]))
        room.attrs["@events"]={}
        room.attrs["@encounter_list"]=[]
        room.attrs["@autoplay_bgm"]=room.attrs["@autoplay_bgs"]=False
        for f in ("@bgm","@bgs"):
            song=room.attrs.get(f)
            if isinstance(song,RubyObject):song.attrs["@name"]=b""
        stages[symbol]=room
        stage_ids[symbol]=mid
        info=copy.deepcopy(info_template)
        info.attrs["@name"]=row["name"].encode("utf-8")
        info.attrs["@parent_id"]=row["parent_id"]
        order+=1;info.attrs["@order"]=order
        infos[mid]=info
    if any(infos[k]!=v for k,v in old_infos.items()):
        fail("Informações dos mapas anteriores foram alteradas")
    placed={sym:set() for sym in stages}
    trigger_by_map={sym:set() for sym in stages}
    arrival_by_map={sym:set() for sym in stages}
    for w in spec["warps"]:
        source,target=w["source"],w["target"]
        xy=(w["x"],w["y"])
        arrive=tuple(w["arrival"])
        trigger_by_map[source].add(xy)
        arrival_by_map[target].add(arrive)
        if xy in placed[source]:fail("Eventos sobrepostos no mesmo tile")
        placed[source].add(xy)
        room=stages[source];events=room.attrs["@events"]
        eid=max(events.keys(),default=0)+1
        page=event_page(warp=(stage_ids[target],*arrive),touch=True)
        events[eid]=ruby("RPG::Event",id=eid,name=w["key"].encode("ascii"),
                         x=xy[0],y=xy[1],pages=[page])
    for npc in spec["npcs"]:
        source=npc["source"];xy=(npc["x"],npc["y"])
        if xy in placed[source]:fail("NPC sobre warp/outro NPC")
        placed[source].add(xy)
        room=stages[source];events=room.attrs["@events"]
        eid=max(events.keys(),default=0)+1
        page=event_page(script=npc["handler"],sprite=npc["sprite"])
        events[eid]=ruby("RPG::Event",id=eid,name=npc["key"].encode("ascii"),
                         x=xy[0],y=xy[1],pages=[page])
    for sym,room in stages.items():
        if trigger_by_map[sym] & arrival_by_map[sym]:
            fail("Chegada sobre gatilho de warp; risco de loop: "+sym)
        _,connected=passage_grid(room,tiles)
        report.setdefault("static_reachable_tiles",{})[sym]=connected(
            trigger_by_map[sym]|arrival_by_map[sym]|
            {(x["x"],x["y"]) for x in spec["npcs"] if x["source"]==sym})
    sprites=game/"Graphics/Characters"
    missing=[]
    for npc in spec["npcs"]:
        filename=sprites/(npc["sprite"]+".png")
        if (not filename.is_file() or filename.is_symlink()
                or filename.read_bytes()[:8]!=PNG):
            missing.append(npc["sprite"]+".png")
    report["missing_native_character_sprites"]=sorted(set(missing))
    report["character_sprites_proven"]=not missing
    if len(stages)!=6 or len(infos)!=len(old_infos)+5:
        fail("Cinco novas salas e Violet City são exigidos")
    blobs={}
    for sym,room in stages.items():
        binary=serialize(room,EVENT_CLASSES)
        parsed=loads(binary)
        if not isinstance(parsed,RubyObject) or (
            len(parsed.attrs.get("@events",{})) != len(room.attrs["@events"])):
            fail("Ruby Marshal perdeu eventos: "+sym)
        blobs[stage_ids[sym]]=binary
    info_blob=serialize(infos)
    actual=loads(info_blob)
    if not isinstance(actual,dict) or any(actual.get(k)!=v for k,v in old_infos.items()):
        fail("Roundtrip mudou MapInfos anteriores")
    report.update({
        "schema":1,"region":"JOHTO",
        "status":"VIOLET_SPROUT_GYM_PRIVATE_STAGE11_NOT_ENGINE_TESTED",
        "can_install":False,"not_playable":True,"gameplay_playable":False,
        "tested_in_game":False,"installer_integrated":False,
        "original_map_count":77,"new_map_ids":sorted(NEW_IDS),
        "existing_map_modified":[602],"old_maps_preserved":76,
        "map_infos_appended":5,"warps_created":10,"npcs_created":5,
        "map_sha256":{str(i):sha(blob) for i,blob in blobs.items()},
        "source_manifest_sha256":checksum(preview/"johto-stage.json"),
        "source_mapinfos_sha256":checksum(preview/"Data/MapInfos.rxdata"),
        "new_mapinfos_sha256":sha(info_blob),
        "tilesets_preserved_sha256":checksum(preview/"Data/Tilesets.rxdata"),
        "zephyr_rule":"BlueRegions.award only AFTER a verified victory; Elder must NEVER grant badge",
        "blockers":spec["missing_before_gameplay"]
    })
    manifest=copy.deepcopy(stage)
    manifest["status"]="BLUE_VIOLET_STAGE11_PREVIEW_ONLY_NOT_PLAYABLE"
    manifest["not_playable"]=True;manifest["can_install"]=False
    for row in spec["interiors"]:
        manifest["maps"].append({
            "symbol":row["symbol"],"source_id":None,
            "destination_id":row["id"],"origin":"BLUE_AUTHORED_OFFLINE_VIOLET_11",
            "events_imported":0,"layout_is_hgss_verified":False
        })
    manifest["violet11_offline_preview"]={
        "maps_new":5,"warps":10,"npcs":5,"trainer_profiles":4,
        "pbs_compiled":False,"tested_in_game":False,"can_install":False
    }
    manifest.setdefault("warnings",[]).append(
        "Violet interior layouts, trainer graphics, PBS and entrance identity "
        "not yet engine-tested; do not install as playable")
    return blobs,info_blob,manifest,report


def publish(spec_path:Path,game:Path,preview:Path,output:Path,*,root:Path=ROOT):
    root=root.resolve();work=(root/".blue-work").resolve()
    game=game.absolute();preview=preview.absolute();output=output.absolute()
    if (work.is_symlink() or game.is_symlink() or preview.is_symlink()
        or output.is_symlink() or output.exists()
        or not preview.resolve().is_relative_to(work)
        or not output.resolve().is_relative_to(work)
        or output.resolve()==work or preview.resolve()==work
        or output.resolve()==preview.resolve()
        or output.resolve().is_relative_to(preview.resolve())
        or preview.resolve().is_relative_to(output.resolve())
        or game.resolve().is_relative_to(work)
        or not game.is_dir()):
        fail("Exigir cópia nova sob .blue-work e game/ somente leitura")
    if any(p.is_symlink() for p in preview.rglob("*")):
        fail("Stage privado contém symlinks")
    spec=read_json(spec_path)
    validate_contract(spec)
    payloads,report=build_pbs(spec,game)
    maps,infos,manifest,report=compile_preview(spec,preview,game,payloads,report)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-violet11-",dir=output.parent) as tmp:
        target=Path(tmp)/"stage"
        shutil.copytree(preview,target)
        for mid,blob in maps.items():
            (target/"Data"/f"Map{mid:03d}.rxdata").write_bytes(blob)
        (target/"Data/MapInfos.rxdata").write_bytes(infos)
        for name,blob in payloads.items():
            p=target/name
            if p.exists():fail("PBS Violet já existe, impedir overwrite")
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(blob)
        (target/"johto-stage.json").write_text(
            json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        (target/"johto-violet11-report.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        if checksum(preview/"Data/Tilesets.rxdata") != checksum(target/"Data/Tilesets.rxdata"):
            fail("Tilesets originais alterados")
        for row in manifest["maps"][:77]:
            mid=row["destination_id"]
            if mid!=602 and checksum(preview/"Data"/f"Map{mid:03d}.rxdata") != (
               checksum(target/"Data"/f"Map{mid:03d}.rxdata")):
                fail("Mapas 600–676 fora de Violet foram alterados")
        if output.exists() or output.is_symlink():fail("Destino criou-se durante build")
        target.rename(output)
    return report


def main(argv=None):
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root",type=Path,default=ROOT)
    cli.add_argument("--spec",type=Path,default=DEFAULT_SPEC)
    cli.add_argument("--game",type=Path,default=ROOT/"game")
    cli.add_argument("--preview",type=Path,default=DEFAULT_STAGE)
    cli.add_argument("--output",type=Path,default=DEFAULT_OUTPUT)
    args=cli.parse_args(argv)
    try:
        result=publish(args.spec,args.game,args.preview,args.output,root=args.root)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as error:
        print("[JOHTO][BLOQUEADO]",error,file=sys.stderr)
        return 2
    print("[JOHTO] Violet Map602, 5 interiores 677–681, 10 warps, 5 NPCs.")
    print("[JOHTO] 8 rosters PBS normal/master em PREVIA ISOLADA; BADGE NAO OUTORGADA.")
    print("[JOHTO] Sprites pendentes:",result["missing_native_character_sprites"])
    print("[JOHTO] Sem Game.exe, sem Blue-Story.exe instalado, gameplay 0/13.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
