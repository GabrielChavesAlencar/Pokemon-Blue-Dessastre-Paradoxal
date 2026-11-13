"""Add New Bark story NPCs and 3 individual starter-ball events to stage07.

Writes ONLY a NEW .blue-work preview. Preserves all six preexisting code-201
warps, removes the 3 static ball graphics from the tilemap, and uses explicit
BlueJohtoPilot.choose_starter_from_ball(:SPECIES) action events. Game.exe,
game/, saves, legacy Johto test contracts, Kanto and Decades stay untouched.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path

from audit_johto import ROOT, checksum, read_map_data
from build_johto_elm_lab_v1 import table_values
from build_johto_events import EVENT_CLASSES, event_page, ruby
from stage import serialize
from server.ruby_marshal import RubyData, RubyObject, loads, text

DEFAULT_SPEC = ROOT / "data/regions/johto-stage08-story.json"
DEFAULT_PREVIEW = ROOT / ".blue-work/johto-staging-warps-v1"
DEFAULT_OUTPUT = ROOT / ".blue-work/johto-staging-story-v1"
DEFAULT_SPRITES = ROOT / "game/Graphics/Characters"

WARP_KEYS = (
    "JH_HOME2F_TO_1F", "JH_HOME1F_TO_2F", "JH_HOME1F_TO_TOWN",
    "JH_TOWN_TO_HOME1F", "JH_TOWN_TO_ELM_LAB", "JH_LAB_TO_TOWN",
)
REQUIRED_NPCS = {
    "JH_NPC_MOTHER": ("JOHTO_NEW_BARK_PLAYER_HOME_1F", 6, 8, "NPC_GSC_Mom", "mother"),
    "JH_NPC_ELM": ("JOHTO_NEW_BARK_ELM_LAB", 10, 4, "NPC_HGSS_Professor_Elm", "elm"),
    "JH_ROUTE29_NPC_RIVAL": ("JOHTO_ROUTE_29", 71, 17, "NPC_HGSS_Silver", "rival"),
}
REQUIRED_BALLS = {
    "JH_STARTER_CHIKORITA": (7, 7, 7, 6, 5328, "CHIKORITA"),
    "JH_STARTER_CYNDAQUIL": (10, 7, 10, 6, 5329, "CYNDAQUIL"),
    "JH_STARTER_TOTODILE": (13, 7, 13, 6, 5330, "TOTODILE"),
}
LAB = "JOHTO_NEW_BARK_ELM_LAB"
SHA = re.compile(r"[0-9a-f]{64}\Z")
PNG = b"\x89PNG\r\n\x1a\n"


def fail(message: str):
    raise ValueError("[JOHTO][OFFLINE 08] " + message)


def read_json(path: Path) -> dict:
    if path.is_symlink() or not path.is_file():
        fail("JSON ausente/symlink: " + str(path))
    data = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict):
        fail("JSON não contém objeto")
    return data


def validate_spec(spec: dict) -> tuple[list[dict], list[dict]]:
    if ((spec.get("schema"), spec.get("region"), spec.get("status"),
         spec.get("requires_stage_status"), spec.get("requires_existing_warps")) !=
        (1, "JOHTO", "STORY_EVENT_COORDINATES_STATIC_ONLY_NOT_GAMEPLAY_TESTED",
         "BLUE_WARP_PREVIEW_ONLY_NOT_PLAYABLE", 6)):
        fail("Contrato de etapa 08 desconhecido")
    if spec.get("requires_warp_keys") != list(WARP_KEYS):
        fail("Não apagar/mudar os seis warps de 07/12")
    approval = spec.get("approval", {})
    if not isinstance(approval, dict) or approval != {
        "can_install": False, "gameplay_playable": False,
        "tested_in_game": False, "installer_integrated": False
    }:
        fail("Etapa 08 não pode certificar execução/instalação")
    npcs, balls = spec.get("npcs"), spec.get("starter_balls")
    if not isinstance(npcs, list) or len(npcs) != 3 or not isinstance(balls, list) or len(balls) != 3:
        fail("Exigir mãe, Elm, Silver e exatamente três Poké Bolas")
    keys = [row.get("key") for row in npcs + balls if isinstance(row, dict)]
    if len(keys) != 6 or len(set(keys)) != 6 or set(keys) != set(REQUIRED_NPCS) | set(REQUIRED_BALLS):
        fail("Chaves de NPC/Bola ausentes ou duplicadas")
    for item in npcs:
        if not isinstance(item, dict):
            fail("NPC inválido")
        key = item["key"]
        expected = REQUIRED_NPCS[key]
        if ((item.get("symbol"), item.get("x"), item.get("y"),
             item.get("sprite"), item.get("handler")) != expected
            or item.get("trigger") != "action" or item.get("engine_verified") is not False):
            fail("Posição/handler de NPC inesperado: " + key)
    for item in balls:
        if not isinstance(item, dict):
            fail("Bola inválida")
        key = item["key"]
        x, y, sx, sy, number, species = REQUIRED_BALLS[key]
        if (item.get("symbol") != LAB or item.get("sprite") != "Object_Ball"
                or item.get("handler") != "choose_starter_from_ball"
                or item.get("species") != species or
                any(type(item.get(n)) is not int for n in
                    ("x","y","static_tile_x","static_tile_y","static_tile_id",
                     "interact_from_x","interact_from_y"))
                or (item["x"], item["y"], item["static_tile_x"],
                    item["static_tile_y"], item["static_tile_id"]) !=
                    (x,y,sx,sy,number)
                or (item["interact_from_x"], item["interact_from_y"]) != (x,y+1)
                or item.get("engine_verified") is not False):
            fail("Poké Bola/posição/espécie adulterada: " + key)
    return npcs, balls


def load_map(preview: Path, tiles: list, mid: int) -> tuple[RubyObject, dict]:
    path = preview / "Data" / f"Map{mid:03d}.rxdata"
    if path.is_symlink() or not path.is_file():
        fail("Mapa ausente/ligado: " + path.name)
    obj = read_map_data(path)
    if not isinstance(obj, RubyObject) or obj.name != "RPG::Map":
        fail("RPG::Map inválido: " + path.name)
    a = obj.attrs
    w, h, tid = a.get("@width"), a.get("@height"), a.get("@tileset_id")
    if (any(type(i) is not int for i in (w,h,tid))
            or not 5 <= w <= 500 or not 5 <= h <= 500
            or not 0 < tid < len(tiles)):
        fail("Mapa com tamanho/tileset inválido: " + path.name)
    table = a.get("@data")
    t = tiles[tid]
    passage = t.attrs.get("@passages") if isinstance(t, RubyObject) else None
    if (not isinstance(table, RubyData) or table.name != "Table" or
            not isinstance(passage, RubyData) or passage.name != "Table"):
        fail("Mapa sem tabela RMXP")
    shape, cells = table_values(table.data, dimension=3)
    pshape, flags = table_values(passage.data, dimension=1)
    if shape != (w,h,3) or pshape[1:] != (1,1) or max(cells, default=0) >= len(flags):
        fail("Passabilidade/tabela inconsistentes")
    return obj, {"w":w, "h":h, "cells":list(cells), "flags":flags}


def walkable(grid: dict, x: int, y: int, *, cells: list[int] | None = None) -> bool:
    w,h = grid["w"],grid["h"]
    if type(x) is not int or type(y) is not int or not 0 <= x < w or not 0 <= y < h:
        return False
    values = grid["cells"] if cells is None else cells
    for z in range(3):
        tid = values[x+w*(y+h*z)]
        if tid >= len(grid["flags"]) or grid["flags"][tid] & 0x0F:
            return False
    return True


def audit_existing_warps(stage: dict, preview: Path, ids: dict, rooms: dict) -> list[dict]:
    path = preview / "johto-warp-preview.json"
    report = read_json(path)
    if ((report.get("schema"), report.get("region"), report.get("status"),
         report.get("can_install"), report.get("tested_in_game")) !=
        (1,"JOHTO","SIX_BLUE_WARPS_STATIC_AUDIT_NOT_ENGINE_TESTED",False,False)):
        fail("Prova da etapa 07 ausente ou inválida")
    rows = report.get("warps")
    if not isinstance(rows,list) or len(rows)!=6:
        fail("Etapa 07 precisa ter exatamente 6 warps")
    actual = {}
    for sym, (world, _) in rooms.items():
        events = world.attrs.get("@events")
        if not isinstance(events,dict):
            fail("Eventos RMXP malformados: " + sym)
        for eid, ev in events.items():
            if type(eid) is not int or not isinstance(ev,RubyObject) or ev.name != "RPG::Event":
                fail("Evento não-confiável antes da etapa 08")
            name = text(ev.attrs.get("@name"))
            if name in actual:
                fail("Evento duplicado: " + name)
            if name not in WARP_KEYS:
                fail("Evento externo/desconhecido antes da etapa 08: " + name)
            pages = ev.attrs.get("@pages")
            if not isinstance(pages,list) or len(pages)!=1:
                fail("Warp tem páginas não auditadas")
            commands = pages[0].attrs.get("@list")
            if not isinstance(commands,list) or [c.attrs.get("@code") for c in commands] != [201,0]:
                fail("Warp sem comando 201 único")
            actual[name] = (sym, ev, commands[0])
    if set(actual) != set(WARP_KEYS):
        fail("Etapa 07 foi alterada: faltam/excedem warps")
    checked = {}
    for row in rows:
        key,source,target = row.get("key"), row.get("source"), row.get("target")
        if key not in WARP_KEYS or source not in ids or target not in ids or key in checked:
            fail("Warp inesperado na prova anterior")
        sym,ev,cmd = actual[key]
        if (sym!=source or row.get("source_id")!=ids[source] or
                row.get("destination_id")!=ids[target] or
                (ev.attrs.get("@x"), ev.attrs.get("@y")) != (row.get("x"),row.get("y")) or
                cmd.attrs.get("@parameters")[:4]!=[
                    0,ids[target],row.get("arrival_x"),row.get("arrival_y")
                ]):
            fail("Warp da etapa 07 adulterado: " + key)
        checked[key] = row
    digests = report.get("warped_map_sha256", {})
    for sym,(world,_) in rooms.items():
        mid = ids[sym]
        if sym not in ("JOHTO_NEW_BARK_TOWN", "JOHTO_NEW_BARK_PLAYER_HOME_2F",
                       "JOHTO_NEW_BARK_PLAYER_HOME_1F", LAB):
            continue
        digest = digests.get(str(mid),digests.get(f"Map{mid:03d}.rxdata"))
        if not isinstance(digest,str) or not SHA.fullmatch(digest):
            fail("Hash da etapa 07 ausente: " + sym)
        if digest != checksum(preview / "Data" / f"Map{mid:03d}.rxdata"):
            fail("O mapa da etapa 07 mudou: " + sym)
    return rows


def compile_story(spec: dict, preview: Path, sprites: Path) -> tuple[dict, dict[int,bytes]]:
    npcs, balls = validate_spec(spec)
    stage = read_json(preview / "johto-stage.json")
    if ((stage.get("schema"),stage.get("region"),stage.get("status"),
         stage.get("not_playable"),stage.get("can_install")) !=
        (1,"JOHTO","BLUE_WARP_PREVIEW_ONLY_NOT_PLAYABLE",True,False)):
        fail("Prévia de entrada não é a etapa 07")
    rows = stage.get("maps",[])
    if len(rows) != 77 or any(not isinstance(x,dict) or x.get("events_imported")!=0 for x in rows):
        fail("Mapa estrangeiro/contagem não conferida")
    ids={r["symbol"]:r["destination_id"] for r in rows}
    if len(ids)!=77 or len(set(ids.values()))!=77:
        fail("MapIDs duplicados")
    if any(type(x) is not int or not 600<=x<=999 for x in ids.values()):
        fail("MapIDs fora do namespace")
    required = {LAB,"JOHTO_NEW_BARK_PLAYER_HOME_2F","JOHTO_NEW_BARK_PLAYER_HOME_1F",
                "JOHTO_NEW_BARK_TOWN","JOHTO_ROUTE_29"}
    if not required<=ids.keys():
        fail("Mapas obrigatórios ausentes")
    tiles = read_map_data(preview / "Data/Tilesets.rxdata")
    if not isinstance(tiles,list):
        fail("Tilesets de Johto não são array RMXP")
    rooms = {}
    for sym in sorted(required):
        rooms[sym]=load_map(preview,tiles,ids[sym])
    old_warps = audit_existing_warps(stage,preview,ids,rooms)
    if not sprites.is_dir() or sprites.is_symlink():
        fail("Graphics/Characters nativo ausente/ligado")
    for sprite in ("NPC_GSC_Mom","NPC_HGSS_Professor_Elm","NPC_HGSS_Silver","Object_Ball"):
        src=sprites / f"{sprite}.png"
        if src.is_symlink() or not src.is_file() or src.open("rb").read(8)!=PNG:
            fail("Sprite PNG nativo ausente: "+sprite)
    new_positions={}
    for row in npcs+balls:
        sym,x,y=row["symbol"],row["x"],row["y"]
        world,grid = rooms[sym]
        if not 0<=x<grid["w"] or not 0<=y<grid["h"]:
            fail("NPC/Bola fora do mapa: "+row["key"])
        occupied = {(ev.attrs["@x"],ev.attrs["@y"])
                    for ev in world.attrs["@events"].values()}
        if (x,y) in occupied or (x,y) in new_positions.setdefault(sym,set()):
            fail("NPC/Bola em cima de warp/outro NPC: "+row["key"])
        new_positions[sym].add((x,y))
        if row in npcs:
            if not walkable(grid,x,y):
                fail("NPC sobre tile bloqueado: "+row["key"])
            if not any(walkable(grid,xx,yy)
                       for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))):
                fail("NPC sem aproximação possível: "+row["key"])
        else:
            if (abs(row["interact_from_x"]-x)+abs(row["interact_from_y"]-y)!=1
                    or not walkable(grid,row["interact_from_x"],row["interact_from_y"])):
                fail("Poké Bola não pode ser alcançada para clicar: "+row["key"])
            sx,sy=row["static_tile_x"],row["static_tile_y"]
            cell=sx+grid["w"]*(sy+grid["h"]*2)
            if grid["cells"][cell]!=row["static_tile_id"]:
                fail("Poké Bola estática não existe ou já foi removida: "+row["key"])
    lab,lab_grid=rooms[LAB]
    old_static=sum(1 for number in lab_grid["cells"] if number in (5328,5329,5330))
    if old_static != 3:
        fail("Expected exactly 3 static Poké Ball tiles before replacement")

    result={}
    source_digest={}
    preserved_count=0
    for sym in sorted({row["symbol"] for row in npcs+balls}):
        world,grid=rooms[sym]
        updated=copy.deepcopy(world)
        events=updated.attrs["@events"]
        if not isinstance(events,dict):
            fail("Mapa com eventos inválidos")
        before=copy.deepcopy(events)
        next_id=max(events.keys(),default=0)+1
        for row in [x for x in npcs+balls if x["symbol"]==sym]:
            key=row["key"]
            if row in npcs:
                script="BlueJohtoPilot."+row["handler"]
            else:
                script="BlueJohtoPilot.choose_starter_from_ball(:"+row["species"]+")"
            event=ruby("RPG::Event",id=next_id,name=key.encode("ascii"),
                       x=row["x"],y=row["y"],
                       pages=[event_page(script=script,sprite=row["sprite"])])
            events[next_id]=event
            next_id+=1
        if sym==LAB:
            raw=updated.attrs["@data"]
            shape,cells=table_values(raw.data,dimension=3)
            data=list(cells)
            for row in balls:
                cell=row["static_tile_x"]+grid["w"]*(row["static_tile_y"]+grid["h"]*2)
                data[cell]=0
            import struct
            raw.data=struct.pack("<5I",3,*shape,len(data))+struct.pack(f"<{len(data)}H",*data)
            if any(x in (5328,5329,5330) for x in data):
                fail("Poké Bola estática não removida da geometria")
        binary=serialize(updated,EVENT_CLASSES)
        saved=loads(binary)
        output_events=saved.attrs.get("@events")
        if not isinstance(output_events,dict) or len(output_events)!=len(events):
            fail("Roundtrip Marshal descartou evento")
        for eid,prior in before.items():
            if output_events.get(eid)!=prior:
                fail("Warp da etapa 07 modificado durante compilação")
        for ev in output_events.values():
            name=text(ev.attrs.get("@name"))
            if name in WARP_KEYS:
                continue
            cmds=ev.attrs["@pages"][0].attrs["@list"]
            expected_script=("BlueJohtoPilot.choose_starter_from_ball(:"+name[len("JH_STARTER_"):]+")"
                             if name.startswith("JH_STARTER_") else
                             "BlueJohtoPilot."+next(row["handler"] for row in npcs if row["key"]==name))
            if ([x.attrs["@code"] for x in cmds]!=[355,0] or
                cmds[0].attrs["@parameters"][0]!=expected_script.encode("ascii")):
                fail("Evento de história não passou na verificação de script")
        mid=ids[sym]
        result[mid]=binary
        source_digest[str(mid)]=checksum(preview/"Data"/f"Map{mid:03d}.rxdata")
    if len(result)!=3:
        fail("Somente três mapas podem receber NPCs nesta etapa")
    report={
      "schema":1,"region":"JOHTO","status":"STORY_EVENTS_COMPILED_OFFLINE_NOT_PLAYABLE",
      "can_install":False,"not_playable":True,"tested_in_game":False,
      "gameplay_playable":False,"installer_integrated":False,
      "original_warps_preserved":len(old_warps),
      "story_events_added":len(npcs)+len(balls),
      "starter_ball_events":3,"static_starter_ball_tiles_removed":3,
      "new_bark_maps_modified":sorted(result),
      "other_maps_preserved":len(rows)-len(result),
      "source_archive_sha256":stage["source_archive_sha256"],
      "before_map_sha256":source_digest,
      "after_map_sha256":{str(i):hashlib.sha256(v).hexdigest() for i,v in result.items()},
      "npc_placements":npcs,"starter_ball_placements":balls,
      "warnings":[
         "Poké Bolas são eventos individuais de ação; ainda requerem QA em Game.exe",
         "IDs, eventos e sprites estão em preview privado; não há instalador automático",
         "A batalha de Silver exige PBS de rival da etapa 09, não é certificada aqui",
      ]
    }
    return report,result


def build(*,root:Path=ROOT,preview:Path|None=None,output:Path|None=None,
          spec_path:Path|None=None,sprites:Path|None=None)->dict:
    root=root.resolve()
    work=(root/".blue-work").resolve()
    preview=(preview or root/".blue-work/johto-staging-warps-v1").absolute()
    output=(output or root/".blue-work/johto-staging-story-v1").absolute()
    spec_path=(spec_path or root/"data/regions/johto-stage08-story.json").absolute()
    sprites=(sprites or root/"game/Graphics/Characters").absolute()
    if (work.is_symlink() or preview.is_symlink() or output.is_symlink() or
        output.exists() or preview.resolve()==work or output.resolve()==work or
        not preview.resolve().is_relative_to(work) or
        not output.resolve().is_relative_to(work) or
        preview.resolve()==output.resolve() or
        output.resolve().is_relative_to(preview.resolve()) or
        preview.resolve().is_relative_to(output.resolve())):
        fail("Só é permitido novo destino distinto em .blue-work")
    # No symlink dereferencing when copying private assets.
    if any(p.is_symlink() for p in preview.rglob("*")):
        fail("Stage contém links simbólicos; cópia recusada")
    if sprites.is_symlink() or not sprites.resolve().is_relative_to(root):
        fail("Graphics/Characters fora da instalação do projeto")
    spec=read_json(spec_path)
    report,blobs=compile_story(spec,preview,sprites)
    stage=read_json(preview/"johto-stage.json")
    modified=set(blobs)
    edited=copy.deepcopy(stage)
    edited["status"]="BLUE_STORY_PREVIEW_ONLY_NOT_PLAYABLE"
    edited["story_preview"]={
        "manifest":"johto-story-preview.json","added_events":report["story_events_added"],
        "static_balls_removed":report["static_starter_ball_tiles_removed"],
        "gameplay_playable":False,"tested_in_game":False,"can_install":False
    }
    edited["warnings"].append("Etapa 08: seis eventos próprios; Ruby do piloto requer testes no EXE e PBS rival")
    for row in edited["maps"]:
        if row["destination_id"] in modified:
            row["blue_authored_story_events"]={
                675:1,676:4,625:1
            }[row["destination_id"]]
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".johto-story-",dir=output.parent) as tmp:
        dest=Path(tmp)/"stage"
        shutil.copytree(preview,dest)
        for mid,binary in blobs.items():
            (dest/"Data"/f"Map{mid:03d}.rxdata").write_bytes(binary)
        (dest/"johto-story-preview.json").write_text(
            json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        (dest/"johto-stage.json").write_text(
            json.dumps(edited,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
        for path in ("MapInfos.rxdata","Tilesets.rxdata"):
            if checksum(preview/"Data"/path)!=checksum(dest/"Data"/path):
                fail("Metadados RMXP nativos foram alterados")
        for row in stage["maps"]:
            mid=row["destination_id"]
            if mid not in modified and checksum(preview/"Data"/f"Map{mid:03d}.rxdata") != (
                  checksum(dest/"Data"/f"Map{mid:03d}.rxdata")):
                fail("Mapa fora da lista de NPCs alterado")
        if output.exists() or output.is_symlink():
            fail("Destino passou a existir durante compilação")
        dest.rename(output)
    return report


def main(argv=None)->int:
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root",type=Path,default=ROOT)
    cli.add_argument("--preview",type=Path)
    cli.add_argument("--output",type=Path)
    cli.add_argument("--spec",type=Path)
    cli.add_argument("--sprites",type=Path)
    args=cli.parse_args(argv)
    try:
        p=build(root=args.root,preview=args.preview,output=args.output,
                spec_path=args.spec,sprites=args.sprites)
    except (OSError,ValueError,KeyError,TypeError,StopIteration,json.JSONDecodeError) as error:
        print("[JOHTO][BLOQUEADO]",error,file=sys.stderr)
        return 2
    print("[JOHTO] 6 eventos de história criados (3 NPCs + 3 Poké Bolas).")
    print("[JOHTO] 6 warps preservados; 3 desenhos antigos de bolas removidos.")
    print("[JOHTO] 0/13 jogáveis; 0/13 testadas - EXE não executado.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
