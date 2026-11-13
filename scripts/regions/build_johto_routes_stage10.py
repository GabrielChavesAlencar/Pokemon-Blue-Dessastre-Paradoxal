"""Johto OFFLINE 10/12: encounters + trainers for Route 29, 30 and 31.

Creates 2 PBS drafts and 5 map NPC events in an isolated .blue-work stage.
The Johto map pack has NO canonical route encounters/trainers: this is an
explicit proposal validated against native Blue species/moves and tile flags.
NO Game.exe, installed game/PBS, saves, trainer-ready marker or Kanto edits.
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
from build_johto_elm_lab_v1 import table_values
from build_johto_events import EVENT_CLASSES, event_page, ruby
from pbs import catalogue, read_blocks
from stage import serialize
from server.ruby_marshal import RubyData, RubyObject, loads, text

SPEC = ROOT / "data/regions/johto-stage10-routes.json"
STAGE = ROOT / ".blue-work/johto-staging-story-v1"
OUTPUT = ROOT / ".blue-work/johto-staging-routes-v1"
ROUTE_IDS = {"JOHTO_ROUTE_29":625, "JOHTO_ROUTE_30":626, "JOHTO_ROUTE_31":627}
TRAINER_TYPES = {"YOUNGSTER","BUGCATCHER"}
SPRITES = {"NPC_HGSS_Youngster","NPC_HGSS_Bug_Catcher"}
PNG=b"\x89PNG\r\n\x1a\n"


def fail(msg):
    raise ValueError("[JOHTO][OFFLINE 10] " + str(msg))


def checksum_bytes(blob):
    return hashlib.sha256(blob).hexdigest()


def load_contract(path:Path)->dict:
    if path.is_symlink() or not path.is_file():
        fail("Especificação ausente/symlink")
    s=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(s,dict):
        fail("Contrato não é objeto JSON")
    return s


def validate_contract(s:dict)->None:
    if ((s.get("schema"),s.get("region"),s.get("status"),s.get("requires_stage_status"),
          s.get("gameplay_ready"),s.get("installer_integrated")) !=
        (1,"JOHTO","OFFLINE_10_ROUTE29_31_PROPOSED_ENCOUNTERS_NOT_ENGINE_TESTED",
         "BLUE_STORY_PREVIEW_ONLY_NOT_PLAYABLE",False,False)):
        fail("Estado/especificação não autorizados")
    policy=s.get("balance_policy")
    if (not isinstance(policy,dict) or
        [policy.get(k) for k in ("trainer_normal_ratio","trainer_master_ratio","wild_ratio","master_stage","master_team_size","runtime_scaling_verified")] !=
        [0.7,0.9,0.45,3,4,False]):
        fail("Balanceamento alterado: usar BlueCampaign/BlueStory nativos")
    routes=s.get("routes");trainers=s.get("trainers")
    if not isinstance(routes,list) or len(routes)!=3 or not isinstance(trainers,list) or len(trainers)!=5:
        fail("Esperados três mapas e cinco treinadores")
    if {r.get("symbol") for r in routes}!=set(ROUTE_IDS):
        fail("Símbolos das rotas inválidos")
    for r in routes:
        if ((r.get("map_id"),r.get("source_id"),r.get("encounter_rate")) !=
            (ROUTE_IDS[r["symbol"]],ROUTE_IDS[r["symbol"]]-521,21)):
            # IDs source 104,105,106 -> targets 625,626,627 (offset 521)
            fail("MapID origem/destino ou taxa diferente do staging")
        for key in ("land","night"):
            rows=r.get(key)
            if not isinstance(rows,list) or len(rows)<2 or sum(x[0] for x in rows if isinstance(x,list) and len(x)==4)!=100:
                fail("Slots de encontro não somam 100%: "+r["symbol"]+"/"+key)
            for entry in rows:
                if (not isinstance(entry,list) or len(entry)!=4 or
                    any(type(v) is not int for v in (entry[0],entry[2],entry[3])) or
                    not 1<=entry[0]<=100 or not 1<=entry[2]<=entry[3]<=100 or
                    not isinstance(entry[1],str) or not entry[1].isupper()):
                    fail("Slot de encontro inválido")
    keys=set();names=set();coords=set()
    for t in trainers:
        k=t.get("key")
        if (not isinstance(k,str) or not k.startswith("JH_ROUTE") or
            k in keys or t.get("symbol") not in ROUTE_IDS or
            t.get("map_id")!=ROUTE_IDS[t["symbol"]] or
            t.get("trainer_type") not in TRAINER_TYPES or
            t.get("sprite") not in SPRITES or
            t.get("engine_verified") is not False):
            fail("Treinador, tipo, mapa ou nome duplicado")
        if (type(t.get("x")) is not int or type(t.get("y")) is not int or
            not isinstance(t.get("name"),str) or not t["name"].startswith("Johto ")):
            fail("Coordenada/nome de treinador inválidos")
        keys.add(k)
        unique=(t["trainer_type"],t["name"])
        where=(t["map_id"],t["x"],t["y"])
        if unique in names or where in coords:
            fail("Treinador PBS/posição duplicados")
        names.add(unique);coords.add(where)
        for variant,length in (("normal",2),("master",4)):
            roster=t.get(variant)
            if not isinstance(roster,list) or len(roster)!=length:
                fail("Cada treinador precisa de 2 normais ou 4 no Master")
            for entry in roster:
                if (not isinstance(entry,list) or len(entry)!=2 or
                    not isinstance(entry[0],str) or not entry[0].isupper() or
                    type(entry[1]) is not int or not 1<=entry[1]<=100):
                    fail("Equipe/nível de treinador inválidos")
    if len(keys)!=5:
        fail("Treinadores de Johto ausentes")


def learn_moves(raw:str,known:set[str],level:int)->list[str]:
    pairs=[part.strip() for part in raw.split(",")]
    if not raw or len(pairs)%2 or any(not p for p in pairs):
        fail("Learnset inválido em pokemon.txt")
    result=[]
    for lv,move in zip(pairs[::2],pairs[1::2]):
        if not lv.isdecimal() or not 0<=int(lv)<=100 or move not in known:
            fail("Nível/move desconhecido no learnset Blue: "+str((lv,move)))
        if int(lv)<=level:
            if move in result:
                result.remove(move)
            result.append(move)
    if not result:
        fail("Pokémon sem golpe válido até nível "+str(level))
    return result[-4:]


def build_pbs(spec:dict,game:Path)->tuple[dict[str,bytes],dict]:
    validate_contract(spec)
    pbs=game/"PBS"
    if not pbs.is_dir() or pbs.is_symlink() or game.is_symlink():
        fail("PBS nativos ausentes/symlink")
    types_file=pbs/"trainer_types.txt";pokemon_file=pbs/"pokemon.txt";moves_file=pbs/"moves.txt"
    if any(not p.is_file() or p.is_symlink() for p in (types_file,pokemon_file,moves_file)):
        fail("PBS base trainer_types/pokemon/moves ausentes")
    types=read_blocks(types_file)
    if not TRAINER_TYPES<=set(types):
        fail("Tipo YOUNGSTER/BUGCATCHER ausente na base Blue")
    for filepath in sorted(pbs.glob("trainers*.txt")):
        if filepath.is_symlink():
            fail("trainers*.txt vinculado por symlink")
        for key in read_blocks(filepath):
            fields=key.split(",")
            if len(fields)>=2 and (fields[0],fields[1]) in {
                (x["trainer_type"],x["name"]) for x in spec["trainers"]
            }:
                fail("Nome de treinador de Johto colide com PBS instalado")
    known_species=catalogue(game,"pokemon");known_moves=catalogue(game,"moves")
    species=set()
    for route in spec["routes"]:
        species.update(slot[1] for key in ("land","night") for slot in route[key])
    for t in spec["trainers"]:
        species.update(row[0] for kind in ("normal","master") for row in t[kind])
    if not species<=known_species:
        fail("Pokémon ausentes do PBS Blue: "+",".join(sorted(species-known_species)))
    pokemon=read_blocks(pokemon_file,species)
    if set(pokemon)!=species:
        fail("Espécies ausentes do pokemon.txt nativo")
    learnsets={}
    for ident,lines in pokemon.items():
        info={}
        for line in lines:
            key,sep,value=line.partition("=")
            if sep:
                info[key.strip()]=value.strip()
        if not info.get("Moves"):
            fail("Pokémon sem Moves: "+ident)
        learnsets[ident]=info["Moves"]
    encounters=[]
    for route in spec["routes"]:
        encounters.append(f"[{route['map_id']:03d}] # JOHTO {route['symbol']}")
        for section,method in (("land","Land"),("night","LandNight")):
            encounters.append(f"{method},{route['encounter_rate']}")
            encounters.extend(f"    {weight},{mon},{low},{high}"
                              for weight,mon,low,high in route[section])
        encounters.append("")
    trainers=[]
    details=[]
    for t in spec["trainers"]:
        for version,kind in ((0,"normal"),(1,"master")):
            trainers.append(f"[{t['trainer_type']},{t['name']},{version}]")
            team=[]
            for pokemon_id,level in t[kind]:
                moves=learn_moves(learnsets[pokemon_id],known_moves,level)
                trainers.append(f"Pokemon = {pokemon_id},{level}")
                trainers.append("    Moves = "+",".join(moves))
                team.append({"species":pokemon_id,"level":level,"moves":moves})
            trainers.append("")
            details.append({"key":t["key"],"type":t["trainer_type"],"name":t["name"],
                            "version":version,"team":team})
    payloads={
        "PBS/encounters_johto_routes.txt":("\n".join(encounters)+"\n").encode("utf-8"),
        "PBS/trainers_johto_routes.txt":("\n".join(trainers)+"\n").encode("utf-8")
    }
    report={
        "schema":1,"region":"JOHTO",
        "status":"ROUTES_29_31_PBS_DRAFT_AND_NPC_STAGE_NOT_TESTED",
        "source_policy":spec["source_policy"],
        "can_install":False,"gameplay_playable":False,
        "tested_in_game":False,"pbs_compiled":False,
        "trainer_battles_verified":False,"master_level_scaling_verified":False,
        "gameplay_ready_marker_created":False,
        "route_maps":[x["map_id"] for x in spec["routes"]],
        "wild_tables":len(spec["routes"])*2,"trainers":details,
        "master_team_size":4,"normal_team_size":2,
        "native_pbs_sha256":{str(p.relative_to(game)):checksum(p)
                             for p in (types_file,pokemon_file,moves_file)},
        "output_sha256":{n:checksum_bytes(blob) for n,blob in payloads.items()},
        "requirements_before_gameplay":[
            "Confirmar horários Land/LandNight na engine Blue",
            "Integrar os dois PBS na cópia isolada com compilação Essentials",
            "Verificar que a engine usa BlueCampaign 70/90 trainer e 45 wild e as esmeraldas globais",
            "Habilitar os NPCs somente após validar todas as versões em batalha real",
            "Verificar permissões dos mapas/tilesets e instalação automática Blue-Story.exe"
        ]
    }
    return payloads,report


def grid_for_map(map_obj:RubyObject,tilesets:list):
    w,h,tid=(map_obj.attrs.get("@width"),map_obj.attrs.get("@height"),
             map_obj.attrs.get("@tileset_id"))
    if (any(type(v) is not int for v in (w,h,tid)) or
        not 0<tid<len(tilesets) or not 5<=w<=500 or not 5<=h<=500):
        fail("Mapa/tileset nativo inválido")
    table=map_obj.attrs.get("@data");tile=tilesets[tid]
    flags=tile.attrs.get("@passages") if isinstance(tile,RubyObject) else None
    if not isinstance(table,RubyData) or not isinstance(flags,RubyData):
        fail("Map/tileset sem RGSS Table")
    dims,cells=table_values(table.data,dimension=3)
    fdims,passages=table_values(flags.data,dimension=1)
    if dims!=(w,h,3) or fdims[1:]!=(1,1) or max(cells)>=len(passages):
        fail("Tabelas RGSS incompatíveis")
    def walk(x,y):
        return (0<=x<w and 0<=y<h and all(
            (passages[cells[x+w*(y+h*z)]]&0x0F)==0 for z in range(3)))
    return w,h,walk


def compile_stage(spec:dict,preview:Path,game:Path,payloads:dict,report:dict)->tuple[dict[int,bytes],dict]:
    if preview.is_symlink() or not preview.is_dir() or any(p.is_symlink() for p in preview.rglob("*")):
        fail("Preview da etapa 08 ausente/contém symlinks")
    manifest=preview/"johto-stage.json"
    previous=json.loads(manifest.read_text(encoding="utf-8"))
    if ((previous.get("schema"),previous.get("region"),previous.get("status"),
         previous.get("not_playable"),previous.get("can_install"))!=
        (1,"JOHTO","BLUE_STORY_PREVIEW_ONLY_NOT_PLAYABLE",True,False)):
        fail("A preview precisa da etapa 08 de Johto, sem aprovação da engine")
    rows=previous.get("maps")
    if not isinstance(rows,list) or len(rows)!=77:
        fail("Mapa preliminar precisa ter 77 MapNNN")
    mapping={r["symbol"]:r["destination_id"] for r in rows}
    if len(mapping)!=77 or any(mapping.get(k)!=v for k,v in ROUTE_IDS.items()):
        fail("MapIDs de Johto não coincidem com source→stage validado")
    proof=json.loads((preview/"johto-story-preview.json").read_text(encoding="utf-8"))
    if (proof.get("status"),proof.get("original_warps_preserved"),
        proof.get("story_events_added"),proof.get("can_install"))!=(
        "STORY_EVENTS_COMPILED_OFFLINE_NOT_PLAYABLE",6,6,False):
        fail("Falta prova dos 6 warps e 6 eventos de história")
    tiles=read_map_data(preview/"Data/Tilesets.rxdata")
    if not isinstance(tiles,list):
        fail("Tilesets RMXP ausentes")
    npc_names={x["sprite"] for x in spec["trainers"]}
    for name in npc_names:
        sprite=game/"Graphics/Characters"/(name+".png")
        if sprite.is_symlink() or not sprite.is_file() or sprite.open("rb").read(8)!=PNG:
            fail("Sprite NPC do Blue ausente: "+name)
    changes={}
    audit=[]
    for route in spec["routes"]:
        sym=route["symbol"];mid=route["map_id"]
        src=preview/"Data"/f"Map{mid:03d}.rxdata"
        if src.is_symlink() or not src.is_file():
            fail("Mapa real ausente: "+src.name)
        original=read_map_data(src)
        if not isinstance(original,RubyObject) or original.name!="RPG::Map":
            fail("RPG::Map inválido: "+src.name)
        w,h,walk=grid_for_map(original,tiles)
        existing=original.attrs.get("@events")
        if not isinstance(existing,dict):
            fail("Eventos do mapa não são hash")
        names={text(e.attrs.get("@name")) for e in existing.values()}
        if sym=="JOHTO_ROUTE_29":
            if names!={"JH_ROUTE29_NPC_RIVAL"}:
                fail("Silver perdido ou evento não reconhecido na Route29")
        elif existing:
            fail("Route30/31 já possuem eventos; prevenir overwrite")
        updated=copy.deepcopy(original)
        events=updated.attrs["@events"]
        occupied={(e.attrs["@x"],e.attrs["@y"]) for e in events.values()}
        mid_trainers=[t for t in spec["trainers"] if t["map_id"]==mid]
        if len(mid_trainers)!={625:1,626:2,627:2}[mid]:
            fail("Cinco treinadores não distribuídos nas três rotas")
        points=[]
        for t in mid_trainers:
            x,y=t["x"],t["y"]
            if (x,y) in occupied or not walk(x,y):
                fail("NPC sobre evento/colisão no mapa "+str(mid))
            if sum(walk(a,b) for a,b in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)))<2:
                fail("NPC sem aproximação por pelo menos dois lados")
            points.append((x,y));occupied.add((x,y))
            eid=max(events,default=0)+1
            script=f"BlueJohtoRouteTrainers.battle(:{t['key']})"
            events[eid]=ruby("RPG::Event",id=eid,name=t["key"].encode("ascii"),
                x=x,y=y,pages=[event_page(script=script,sprite=t["sprite"])])
        # Both Route30 trainers and both Route31 trainers must inhabit
        # the same traversable component; never strand an NPC on an island.
        reachable={points[0]};todo=[points[0]]
        while todo:
            x,y=todo.pop()
            for next_pt in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if next_pt not in reachable and walk(*next_pt):
                    reachable.add(next_pt);todo.append(next_pt)
        if any(pos not in reachable for pos in points) or len(reachable)<40:
            fail("Treinador desconectado do corredor principal da rota "+str(mid))
        blob=serialize(updated,EVENT_CLASSES)
        roundtrip=loads(blob)
        if not isinstance(roundtrip,RubyObject) or len(roundtrip.attrs.get("@events",{}))!=len(events):
            fail("Falha no roundtrip Ruby Marshal: "+str(mid))
        for old_eid,old_evt in existing.items():
            if roundtrip.attrs["@events"].get(old_eid)!=old_evt:
                fail("Evento de Silver/evento de origem alterado: "+str(mid))
        changes[mid]=blob
        audit.append({"map_id":mid,"source_sha256":checksum(src),"after_sha256":checksum_bytes(blob),
                      "events_added":len(mid_trainers),"component_static_tiles":len(reachable),
                      "positions":[{"key":t["key"],"x":t["x"],"y":t["y"]}
                                   for t in mid_trainers]})
    report["stage08_manifest_sha256"]=checksum(manifest)
    report["map_changes"]=audit
    report["map_count_preserved"]=77-len(changes)
    report["native_mapinfos_sha256"]=checksum(preview/"Data/MapInfos.rxdata")
    report["native_tilesets_sha256"]=checksum(preview/"Data/Tilesets.rxdata")
    report["map_events_in_game"]=False
    return changes,report


def publish(spec_path:Path,game:Path,preview:Path,output:Path,*,root:Path=ROOT)->dict:
    root=root.resolve();work=(root/".blue-work").resolve()
    output=output.absolute();preview=preview.absolute();game=game.absolute()
    if (work.is_symlink() or output.is_symlink() or preview.is_symlink() or
        output.exists() or output.resolve()==work or
        not output.resolve().is_relative_to(work) or
        not preview.resolve().is_relative_to(work) or
        output.resolve()==preview.resolve() or
        output.resolve().is_relative_to(preview.resolve()) or
        preview.resolve().is_relative_to(output.resolve()) or
        game.is_symlink() or game.resolve().is_relative_to(work)):
        fail("Apenas nova pasta .blue-work; game/ é fonte somente leitura")
    spec=load_contract(spec_path)
    payloads,report=build_pbs(spec,game)
    changes,report=compile_stage(spec,preview,game,payloads,report)
    copied=json.loads((preview/"johto-stage.json").read_text(encoding="utf-8"))
    copied["status"]="BLUE_ROUTE10_PREVIEW_ONLY_NOT_PLAYABLE"
    copied["not_playable"]=True;copied["can_install"]=False
    copied["route10_offline_preview"]={"maps_modified":sorted(changes),
        "trainer_events_added":sum(x["events_added"] for x in report["map_changes"]),
        "wild_tables_prepared":report["wild_tables"],
        "pbs_compiled":False,"gameplay_playable":False,"tested_in_game":False}
    copied["warnings"].append("Routes29–31: encontros e treinadores são propostas baseadas no PBS Blue; engine e level cap não testados")
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-routes10-",dir=output.parent) as tmp:
        dest=Path(tmp)/"stage"
        shutil.copytree(preview,dest)
        for mid,blob in changes.items():
            (dest/"Data"/f"Map{mid:03d}.rxdata").write_bytes(blob)
        for name,blob in payloads.items():
            path=dest/name
            if path.exists():fail("PBS já existe na preview; não sobrescrever")
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(blob)
        (dest/"johto-stage.json").write_text(json.dumps(copied,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        (dest/"johto-routes10-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        for immutable in ("MapInfos.rxdata","Tilesets.rxdata"):
            if checksum(preview/"Data"/immutable)!=checksum(dest/"Data"/immutable):
                fail("Metadados RMXP originais alterados")
        for row in copied["maps"]:
            mid=row["destination_id"]
            if mid not in changes and checksum(preview/"Data"/f"Map{mid:03d}.rxdata") != checksum(dest/"Data"/f"Map{mid:03d}.rxdata"):
                fail("Mapa fora de 625–627 alterado")
        if output.exists():fail("Output criada durante stage; recusar overwrite")
        dest.rename(output)
    return report


def main(argv=None)->int:
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root",type=Path,default=ROOT)
    cli.add_argument("--game",type=Path,default=ROOT/"game")
    cli.add_argument("--spec",type=Path,default=SPEC)
    cli.add_argument("--preview",type=Path,default=STAGE)
    cli.add_argument("--output",type=Path,default=OUTPUT)
    a=cli.parse_args(argv)
    try:
        report=publish(a.spec,a.game,a.preview,a.output,root=a.root)
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError) as e:
        print("[JOHTO][BLOQUEADO]",e,file=sys.stderr)
        return 2
    print("[JOHTO] 3 rotas, 6 tabelas selvagens, 5 NPCs, 10 equipes PBS (5 Master com 4).")
    print("[JOHTO] Stage privado / sem Game.exe, PBS compilado=False, instalador pendente.")
    print("[JOHTO] SHA:",report["output_sha256"])
    return 0


if __name__=="__main__":
    raise SystemExit(main())
