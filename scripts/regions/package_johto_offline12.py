"""Audita e empacota Johto 12/12 SEM instalar em game/ e SEM executar Game.exe.

O ZIP privado é uma prévia auditável, NÃO um instalador. Reúne dados das
etapas 07–11, PBS de Silver, conexões (incluindo duas inferidas) e gráficos
nativos que os eventos citam. Repara em cópia separada dois nomes de sprites
que já existem na exportação Blue; nada sobrescreve os RXDATA originais.

Uso:
 python scripts/regions/package_johto_offline12.py --stage ... --game game \
   --rival .blue-work/johto-rival-pbs09-linked --connections ... \
   --output .blue-work/johto-offline12-preview.zip

Proteções: event allowlist, SHA do estágio, hashes PBS, MapIDs, não escrever
game/, negação de links simbólicos, nenhuma instalação/ready marker/saves.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import io
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

from audit_johto import ROOT, checksum, read_map_data
from build_johto_events import EVENT_CLASSES
from stage import serialize
from server.ruby_marshal import RubyObject, loads, text

MAP_IDS = set(range(600, 682))
RIVAL_PBS = ("trainer_types_johto.txt", "trainers_johto.txt")
STAGE_PBS = (
    "encounters_johto_routes.txt", "trainers_johto_routes.txt",
    "trainer_types_johto_violet.txt", "trainers_johto_violet.txt",
)
RUNTIME = ("JohtoPilot.rb", "JohtoRouteTrainers.rb", "JohtoViolet.rb")
ALLOWED_RUNTIME_PREFIXES = (
    "BlueJohtoPilot.", "BlueJohtoRouteTrainers.", "BlueJohtoViolet.",
)
PATCH_SPRITES = {
    "JH_SPROUT_ELDER_LI": ("NPC_HGSS_Elder_Li", "NPC_HGSS_Elder"),
    "JH_VIOLET_CENTER_CLERK": ("NPC_HGSS_Nurse", "NPC_DPP_PokeCenter_Nurse"),
}
PNG=b"\x89PNG\r\n\x1a\n"
SHA=re.compile(r"^[0-9a-f]{64}$")
GRAPHIC=re.compile(r"^[A-Za-z0-9_ \-]{1,90}$")
REQUIRED_BORDER={
    "600,West,13,625,East,0",
    "601,East,12,625,West,0",
    "602,East,6,627,West,0",
}
NOT_INSTALLABLE=(
    "JOHTO OFFLINE 12/12 - NAO INSTALAR EM game/\n"
    "Este ZIP contem mapas e arquivos PBS para AUDITORIA PRIVADA apenas.\n"
    "Nao existem validacao Game.exe, teste de saves, compilacao Essentials,\n"
    "liberacao de recursos de terceiros nem instalador Blue-Story.exe pronto.\n"
    "O progresso OFFLINE 12/12 nao equivale a Johto jogavel.\n"
)


def fail(message: str):
    raise ValueError("[JOHTO][OFFLINE 12] "+message)


def digest(blob:bytes)->str:
    return hashlib.sha256(blob).hexdigest()


def read_json(path:Path)->dict:
    if path.is_symlink() or not path.is_file():
        fail("Manifesto ausente/symlink: "+str(path))
    value=json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict):
        fail("JSON esperado: "+str(path))
    return value


def verify_locations(root:Path,stage:Path,game:Path,rival:Path,
                     connections:Path,output:Path)->None:
    root=root.resolve()
    work=(root/".blue-work")
    if work.is_symlink():fail(".blue-work não pode ser symlink")
    work=work.resolve()
    stage,game,rival,connections,output=[p.absolute() for p in
                                        (stage,game,rival,connections,output)]
    for p in (stage,rival,connections):
        if p.is_symlink() or not p.resolve().is_relative_to(work):
            fail("Entradas privadas precisam estar em .blue-work")
    if (output.is_symlink() or output.exists() or output.resolve()==work or
        not output.resolve().is_relative_to(work) or
        output.resolve().is_relative_to(stage.resolve()) or
        output.resolve().is_relative_to(rival.resolve())):
        fail("ZIP novo deve estar dentro de .blue-work e não sobrescrever nada")
    if game.is_symlink() or not game.is_dir() or game.resolve().is_relative_to(work):
        fail("game/ nativo deve ser somente leitura, fora de .blue-work")
    for directory in (stage,rival):
        if not directory.is_dir() or any(p.is_symlink() for p in directory.rglob("*")):
            fail("Staging com symlinks, incompleto ou ausente")


def expected_events(root:Path)->tuple[dict[str,tuple[str,tuple[int,int],str]],dict[str,tuple[int,int,int]]]:
    """Map event name -> (map symbol, xy, exact handler/wrap key)."""
    warps={}
    actions={}
    for name in ("johto-stage07-warps.json", "johto-stage11-violet.json"):
        doc=read_json(root/"data/regions"/name)
        for w in doc["warps"]:
            key=w["key"]
            if key in warps:fail("Warp duplicado nos contratos: "+key)
            source=w["source"]
            destination=w.get("target")
            arrival=w.get("arrival") or [w.get("arrival_x"),w.get("arrival_y")]
            warps[key]=(source,(w["x"],w["y"]),destination,tuple(arrival),w.get("reverse",w.get("reverse_key")))
    story=read_json(root/"data/regions/johto-stage08-story.json")
    route=read_json(root/"data/regions/johto-stage10-routes.json")
    violet=read_json(root/"data/regions/johto-stage11-violet.json")
    for row in story["npcs"]:
        actions[row["key"]]=(row["symbol"],(row["x"],row["y"]),
                              "BlueJohtoPilot."+row["handler"])
    for row in story["starter_balls"]:
        actions[row["key"]]=(row["symbol"],(row["x"],row["y"]),
                   "BlueJohtoPilot.choose_starter_from_ball(:"+row["species"]+")")
    for row in route["trainers"]:
        actions[row["key"]]=(row["symbol"],(row["x"],row["y"]),
                             "BlueJohtoRouteTrainers.battle(:"+row["key"]+")")
    for row in violet["npcs"]:
        actions[row["key"]]=(row["source"],(row["x"],row["y"]),row["handler"])
    if len(warps)!=16 or len(actions)!=16 or set(warps)&set(actions):
        fail("Contrato precisa ter 16 transferências + 16 ações exclusivas")
    for key,(_,_,destination,_,reverse_key) in warps.items():
        counterpart=warps.get(reverse_key)
        if not counterpart or counterpart[4]!=key or counterpart[2]!=warps[key][0]:
            fail("Warp sem retorno pareado: "+key)
    return actions,warps


def merge_connections(path:Path)->tuple[bytes,dict]:
    if path.is_symlink() or not path.is_file():
        fail("Arquivo de conexões da etapa 04 ausente")
    raw=path.read_text(encoding="utf-8-sig").splitlines()
    items=[]
    seen=set()
    pattern=re.compile(r"^(\d+),(North|South|West|East),(\d+),(\d+),(North|South|West|East),(\d+)$")
    for line in raw:
        line=line.split("#",1)[0].strip().replace(" ","")
        if not line:continue
        m=pattern.fullmatch(line)
        if not m or int(m[1]) not in MAP_IDS or int(m[4]) not in MAP_IDS:
            fail("Conexão inválida/fora de Johto: "+line)
        reverse=",".join((m[4],m[5],m[6],m[1],m[2],m[3]))
        if line in seen or reverse in seen:
            fail("Conexão repetida/oposta: "+line)
        items.append(line);seen.add(line)
    inferred=("601,East,12,625,West,0","602,East,6,627,West,0")
    for line in inferred:
        if line not in seen:
            items.append(line);seen.add(line)
    if not REQUIRED_BORDER<=seen:
        fail("Faltam conexões New Bark–Violet")
    if len(items)!=44:
        fail(f"Esperadas 42 conexões nativas + 2 inferidas; obtidas {len(items)}")
    return ("\n".join(items)+"\n").encode("utf8"),{
        "original_connections":42,"new_inferred_connections":2,
        "total":len(items),"inferred_engine_verified":False}


def trainer_blocks(raw:bytes)->dict[str,list[str]]:
    blocks={}
    key=None
    for line in raw.decode("utf-8-sig").splitlines():
        line=line.strip()
        if not line or line.startswith("#"):continue
        if line.startswith("[") and "]" in line:
            key=line[1:line.index("]")]
            if key in blocks:fail("PBS seção duplicada: "+key)
            blocks[key]=[];continue
        if key is None:fail("PBS sem seção inicial")
        blocks[key].append(line)
    return blocks


def inspect_pbs(stage:Path,rival:Path)->tuple[dict[str,bytes],dict]:
    blobs={}
    for name in STAGE_PBS:
        file=stage/"PBS"/name
        if not file.is_file() or file.is_symlink():fail("PBS etapa 10/11 ausente: "+name)
        blobs[name]=file.read_bytes()
    for name in RIVAL_PBS:
        file=rival/"PBS"/name
        if not file.is_file() or file.is_symlink():fail("PBS Silver etapa 09 ausente: "+name)
        blobs[name]=file.read_bytes()
    types={}
    headers={}
    for name,blob in blobs.items():
        parts=trainer_blocks(blob)
        if name.startswith("trainer_types_"):
            for ident in parts:
                if ident in types:fail("Tipo de treinador duplicado: "+ident)
                types[ident]=name
        elif name.startswith("trainers_"):
            for ident,lines in parts.items():
                if ident in headers:fail("Treinador PBS duplicado: "+ident)
                headers[ident]=lines
    expected_types={"BLUE_JOHTO_RIVAL","BLUE_JOHTO_FALKNER",
                    "BLUE_JOHTO_ELDER","BLUE_JOHTO_SAGE"}
    if set(types)!=expected_types or len(headers)!=3+10+8:
        fail(f"PBS incompletos: tipos={len(types)}, equipes={len(headers)}; esperado 4 e 21")
    for name,lines in headers.items():
        parts=name.split(",")
        if len(parts)!=3 or parts[-1] not in ("0","1","2"):
            fail("Header de batalha inválido: "+name)
        expected=4 if parts[-1]=="1" and parts[0]!="BLUE_JOHTO_RIVAL" else (
            2 if parts[0]!="BLUE_JOHTO_RIVAL" else 1)
        if sum(line.startswith("Pokemon =") for line in lines)!=expected:
            fail("Tamanho da equipe errado: "+name)
    wild=trainer_blocks(blobs["encounters_johto_routes.txt"])
    if set(wild)!={"625","626","627"}:fail("Faltam encontros das Rotas 29–31")
    for key,lines in wild.items():
        slots={}
        method=None
        for line in lines:
            if line.startswith("Land,") or line.startswith("LandNight,"):
                method=line.split(",")[0];slots[method]=0
            elif method and re.fullmatch(r"\d+,[A-Z0-9_]+,\d+,\d+",line):
                slots[method]+=int(line.split(",")[0])
            else:fail("Encontro PBS inválido: "+key+":"+line)
        if slots!={"Land":100,"LandNight":100}:
            fail("Encontro diurno/noturno não soma 100%: "+key)
    return blobs,{"trainer_types":len(types),"trainer_profiles":len(headers),
                   "wild_tables":6,"sha256":{n:digest(b) for n,b in blobs.items()},
                   "pbs_compiled_in_engine":False}


def audit(stage:Path,rival:Path,connections:Path,game:Path,
          *,root:Path=ROOT)->tuple[dict,dict[str,bytes]]:
    """Strict offline integrity audit and in-memory PATCH; no writes."""
    root=root.resolve()
    stage=stage.absolute();rival=rival.absolute();game=game.absolute()
    manifest=read_json(stage/"johto-stage.json")
    violet=read_json(stage/"johto-violet11-report.json")
    story=read_json(stage/"johto-story-preview.json")
    routes=read_json(stage/"johto-routes10-report.json")
    if ((manifest.get("schema"),manifest.get("region"),manifest.get("status"),
         manifest.get("can_install"),manifest.get("not_playable")) !=
        (1,"JOHTO","BLUE_VIOLET_STAGE11_PREVIEW_ONLY_NOT_PLAYABLE",False,True)):
        fail("Entrada não é stage 11 original, ou afirma estar jogável")
    if ((violet.get("status"),violet.get("can_install"),violet.get("tested_in_game"),
         violet.get("warps_created"),violet.get("npcs_created"),
         violet.get("new_map_ids"),violet.get("old_maps_preserved")) !=
        ("VIOLET_SPROUT_GYM_PRIVATE_STAGE11_NOT_ENGINE_TESTED",False,False,
         10,5,[677,678,679,680,681],76)):
        fail("Prova Violet 11 inconsistente")
    if (story.get("original_warps_preserved"),story.get("story_events_added"),
         story.get("starter_ball_events"))!=(6,6,3):
        fail("Eventos de New Bark/3 Poké Bolas não comprovados")
    if (routes.get("trainer_events_added"),routes.get("wild_tables"),
         routes.get("pbs_compiled"))!=(5,6,False):
        fail("Eventos/encounters das Rotas 29–31 não comprovados")
    rows=manifest.get("maps")
    if (not isinstance(rows,list) or len(rows)!=82 or
        {x.get("destination_id") for x in rows}!=MAP_IDS or
        len({x.get("symbol") for x in rows})!=82 or
        any(x.get("events_imported")!=0 for x in rows)):
        fail("Esperados 82 mapas exclusivos sem eventos importados")
    mids={x["symbol"]:x["destination_id"] for x in rows}
    infos=read_map_data(stage/"Data/MapInfos.rxdata")
    tiles=read_map_data(stage/"Data/Tilesets.rxdata")
    if not isinstance(infos,dict) or not isinstance(tiles,list):
        fail("MapInfos/Tilesets RXDATA ilegíveis")
    if (not MAP_IDS<=set(infos) or
        checksum(stage/"Data/Tilesets.rxdata") != violet["tilesets_preserved_sha256"] or
        checksum(stage/"Data/MapInfos.rxdata") != violet["new_mapinfos_sha256"]):
        fail("MapInfos/tilesets mudaram desde a auditoria Violet")
    actions,warps=expected_events(root)
    expected=set(actions)|set(warps)
    present=set()
    source={}
    changes={}
    graphic_names=set()
    for mid in sorted(MAP_IDS):
        path=stage/"Data"/f"Map{mid:03d}.rxdata"
        if path.is_symlink() or not path.is_file():fail("MapNNN ausente/symlink")
        obj=read_map_data(path)
        if not isinstance(obj,RubyObject) or obj.name!="RPG::Map":
            fail("Mapa não é RPG::Map: "+str(mid))
        w,h=obj.attrs.get("@width"),obj.attrs.get("@height")
        if type(w) is not int or type(h) is not int or w<5 or h<5:
            fail("Dimensão inválida Map"+str(mid))
        events=obj.attrs.get("@events")
        if not isinstance(events,dict):fail("Map event hash inválido")
        edited=copy.deepcopy(obj)
        for eid,e in edited.attrs["@events"].items():
            if type(eid) is not int or not isinstance(e,RubyObject) or e.name!="RPG::Event":
                fail("RPG::Event inválido Map"+str(mid))
            name=text(e.attrs.get("@name"))
            if name not in expected or name in present:
                fail("Evento inesperado/repetido: "+name)
            present.add(name)
            rows_e=e.attrs.get("@pages")
            if not isinstance(rows_e,list) or len(rows_e)!=1:fail("Evento com páginas não auditadas")
            page=rows_e[0]
            cmd=page.attrs.get("@list")
            if (not isinstance(cmd,list) or len(cmd)!=2 or
                cmd[-1].attrs.get("@code")!=0):
                fail("Evento com comandos extra: "+name)
            x,y=e.attrs.get("@x"),e.attrs.get("@y")
            if not (type(x) is int and type(y) is int and 0<=x<w and 0<=y<h):
                fail("Evento fora do mapa: "+name)
            if name in actions:
                sym,xy,script=actions[name]
                if (mids[sym] != mid or (x,y)!=xy or cmd[0].attrs.get("@code")!=355
                    or text(cmd[0].attrs.get("@parameters",[None])[0])!=script or
                    not script.startswith(ALLOWED_RUNTIME_PREFIXES)):
                    fail("Handler/posição inesperados: "+name)
            else:
                sym,xy,dest,arrival,reverse=warps[name]
                param=cmd[0].attrs.get("@parameters")
                if (mids[sym]!=mid or (x,y)!=xy or cmd[0].attrs.get("@code")!=201
                    or not isinstance(param,list) or len(param)!=6
                    or param[:4]!=[0,mids[dest],*arrival]):
                    fail("Warp não corresponde ao contrato: "+name)
                target_file=stage/"Data"/f"Map{mids[dest]:03d}.rxdata"
                if not target_file.is_file():fail("Destino de warp ausente")
            graphic=page.attrs.get("@graphic")
            if not isinstance(graphic,RubyObject):fail("Sprite de evento inválido")
            sprite=text(graphic.attrs.get("@character_name"))
            if name in PATCH_SPRITES:
                old,new=PATCH_SPRITES[name]
                if sprite not in (old,new):
                    fail("Sprite de Li/atendente mudou inesperadamente")
                if sprite==old:
                    graphic.attrs["@character_name"]=new.encode("ascii")
                    sprite=new
                    source[name]={"from":old,"to":new,"map_id":mid}
            if sprite:
                if not GRAPHIC.fullmatch(sprite):fail("Nome de sprite perigoso: "+sprite)
                graphic_names.add(sprite)
        if any(x["map_id"]==mid and x["after_sha256"]!=checksum(path)
               for x in routes.get("map_changes",[])):
            fail("Stage11 alterou mapa de treinador da etapa 10")
        recorded=violet.get("map_sha256",{}).get(str(mid))
        if recorded and recorded!=checksum(path):
            fail("Mapa Violet difere do SHA-256 da etapa 11")
        if any(x.get("map_id")==mid and x.get("map_sha256")!=checksum(path)
               for x in story.get("checks",[])
               if mid not in (625,675)):
            fail("Dados da etapa 08 não foram preservados")
        if any(n["map_id"]==mid for n in source.values()):
            binary=serialize(edited,EVENT_CLASSES)
            reloaded=loads(binary)
            if not isinstance(reloaded,RubyObject) or len(reloaded.attrs["@events"])!=len(events):
                fail("Roundtrip dos sprites Violet falhou")
            changes[mid]=binary
    if present!=expected:fail("Eventos faltando: "+",".join(sorted(expected-present)))
    if len(present)!=32 or len(changes)!=2:
        fail("Esperados 32 eventos e 2 ajustes de sprite na cópia")
    if any((stage/"Data"/m).exists() for m in
           ("blue-johto-rival-ready.txt","blue-johto-routes-ready.txt",
            "blue-johto-violet-ready.txt","blue-johto-start.txt")):
        fail("Stage não deve conter marcadores de gameplay")
    payloads,pbs=inspect_pbs(stage,rival)
    conns,cinfo=merge_connections(connections)
    graphics={}
    missing=[]
    # Every used tileset/autotile must be present in the private archive,
    # even when stage11 relied on Blue's own installed Inside.png resources.
    used_tilesets=set()
    for mid in sorted(MAP_IDS):
        room=read_map_data(stage/"Data"/f"Map{mid:03d}.rxdata")
        used_tilesets.add(room.attrs.get("@tileset_id"))
    tile_graphics={}
    tile_missing=[]
    graphic_label=re.compile(r"^[A-Za-z0-9_ ().\\-]{1,130}$")
    for tid in sorted(used_tilesets):
        if type(tid) is not int or not 0<tid<len(tiles):
            fail("Tileset inválido referenciado por Johto: "+str(tid))
        sheet=tiles[tid]
        if not isinstance(sheet,RubyObject) or sheet.name!="RPG::Tileset":
            fail("RPG::Tileset ausente: "+str(tid))
        names=[("Tilesets",text(sheet.attrs.get("@tileset_name")))]
        names += [("Autotiles",text(name)) for name in
                  sheet.attrs.get("@autotile_names",[]) if text(name)]
        for folder,name in names:
            if not name:continue
            if not graphic_label.fullmatch(name):
                fail("Nome de recurso de tileset perigoso: "+name)
            relative=f"Graphics/{folder}/{name}.png"
            if relative in tile_graphics:continue
            file=stage/relative
            if not file.is_file():file=game/relative
            if not file.is_file() or file.is_symlink() or file.read_bytes()[:8]!=PNG:
                tile_missing.append(relative)
            else:
                tile_graphics[relative]=file.read_bytes()
    if tile_missing:
        fail("Tilesets/autotiles exigidos ausentes: "+", ".join(sorted(tile_missing)))
    for name in sorted(graphic_names):
        target=f"Graphics/Characters/{name}.png"
        path=stage/target
        if not path.is_file():
            path=game/target
        if not path.is_file() or path.is_symlink() or path.read_bytes()[:8]!=PNG:
            missing.append(name)
        else:
            graphics[target]=path.read_bytes()
    # Graphics/Trainers sprites and real game moves still require native QA.
    blockers=[
        "PBS não compilados pelo Pokémon Essentials / Game.exe",
        "Não existe marcador de batalha pronta pós-QA",
        "Gráficos de batalha dos trainer types BLUE_JOHTO_* não certificados",
        "Centro Pokémon de Violet ainda não cura",
        "Conexões novas Route29–Cherrygrove/Route31–Violet não testadas no motor",
        "Níveis compartilhados por esmeraldas e Master ainda não testados no motor",
        "Instalação automática Blue-Story.exe / rollback real não implementados",
        "Licenças de distribuição de mapas, sprites e música não aprovadas",
        "Game.exe Windows/JoiPlay, saves e troca de regiões não testados",
    ]
    if missing:blockers.append("Sprites NPC ausentes: "+", ".join(missing))
    report={
        "schema":1,"region":"JOHTO","milestone":"OFFLINE_12_OF_12",
        "status":"OFFLINE_INTEGRITY_AUDITED_INSTALL_BLOCKED",
        "offline_audit_complete":True,"gameplay_playable":False,
        "tested_in_game":False,"can_install":False,
        "blue_story_exe_installed":False,
        "stage11_status":manifest["status"],"map_count":82,
        "maps_sha256":{str(i):checksum(stage/"Data"/f"Map{i:03d}.rxdata")
                       for i in sorted(MAP_IDS)},
        "stage11_mapinfos_sha256":checksum(stage/"Data/MapInfos.rxdata"),
        "stage11_tilesets_sha256":checksum(stage/"Data/Tilesets.rxdata"),
        "events_total":len(present),"warps":len(warps),
        "story_and_trainer_events":len(actions),
        "sprite_name_corrections":source,
        "referenced_character_graphics":len(graphic_names),
        "referenced_tilesets":len(used_tilesets),
        "tile_and_autotile_graphics":len(tile_graphics),
        "character_sprites_missing":missing,
        "pbs":pbs,"connections":cinfo,
        "source_archive_sha256":manifest["source_archive_sha256"],
        "rights_approved":False,"engine_pbs_compiled":False,
        "install_blockers":blockers,
    }
    return report,{"map_fixes":changes,"sprites":graphics,
                   "tile_resources":tile_graphics,"pbs":payloads,"connections":conns}


def pack(stage:Path,rival:Path,connections:Path,game:Path,output:Path,
         *,root:Path=ROOT)->dict:
    verify_locations(root,stage,game,rival,connections,output)
    report,extra=audit(stage,rival,connections,game,root=root)
    safe={}
    # Snapshot only approved file kinds: no EXE, save, script from outside.
    for src in sorted(stage.rglob("*")):
        if not src.is_file():continue
        rel=src.relative_to(stage).as_posix()
        if (rel.startswith("Data/Map") and rel.endswith(".rxdata") or
            rel=="Data/Tilesets.rxdata" or
            rel.startswith("Graphics/Tilesets/") and rel.endswith(".png") or
            rel.startswith("Graphics/Autotiles/") and rel.endswith(".png") or
            rel.startswith("PBS/") and rel.endswith(".txt") or
            rel.startswith("johto-") and rel.endswith(".json")):
            safe["stage/"+rel]=src.read_bytes()
    for mid,blob in extra["map_fixes"].items():
        safe[f"stage/Data/Map{mid:03d}.rxdata"]=blob
    for rel,data in extra["sprites"].items():
        safe["stage/"+rel]=data
    for rel,data in extra["tile_resources"].items():
        safe["stage/"+rel]=data
    for name,data in extra["pbs"].items():
        safe["stage/PBS/"+name]=data
    safe["stage/PBS/map_connections_johto_offline12.txt"]=extra["connections"]
    # Source scripts are included for REVIEW, never auto-loaded in the game.
    for name in RUNTIME:
        src=root/"scripts/regions"/name
        if not src.is_file() or src.is_symlink():
            fail("Runtime original ausente para revisão: "+name)
        safe["review_only/Ruby/"+name]=src.read_bytes()
    revised=read_json(stage/"johto-stage.json")
    revised["status"]="BLUE_OFFLINE12_PREVIEW_ONLY_NOT_INSTALLABLE"
    revised["not_playable"]=True;revised["can_install"]=False
    revised["offline12"]={
        "sprite_fixes":report["sprite_name_corrections"],
        "new_connections_inferred":2,
        "pbs_source_count":6,"engine_verified":False,"gameplay_ready":False}
    safe["stage/johto-stage.json"]=(json.dumps(revised,ensure_ascii=False,indent=2)+"\n").encode()
    report["packaged_map_sha256"]={
        str(i):digest(safe[f"stage/Data/Map{i:03d}.rxdata"])
        for i in sorted(MAP_IDS)}
    report["packaged_file_count"]=len(safe)+2
    safe["OFFLINE_ONLY_NOT_INSTALLABLE.txt"]=NOT_INSTALLABLE.encode("utf8")
    safe["johto-offline12-audit.json"]=(json.dumps(report,ensure_ascii=False,indent=2)+"\n").encode()
    output.parent.mkdir(parents=True,exist_ok=True)
    try:
        with output.open("xb") as target:
            with zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
                for rel,blob in sorted(safe.items()):
                    if rel.startswith("/") or ".." in Path(rel).parts:
                        fail("Path traversal bloqueado")
                    archive.writestr(rel,blob)
        with zipfile.ZipFile(output) as archive:
            bad=archive.testzip()
            if bad or len(archive.namelist())!=len(safe):
                fail("ZIP privado incompleto/CRC incorreto")
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return report


def main(argv=None)->int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root",type=Path,default=ROOT)
    p.add_argument("--stage",type=Path,default=ROOT/".blue-work/johto-staging-violet-v1")
    p.add_argument("--game",type=Path,default=ROOT/"game")
    p.add_argument("--rival",type=Path,default=ROOT/".blue-work/johto-rival-pbs09-linked")
    p.add_argument("--connections",type=Path,default=ROOT/".blue-work/johto-connections-preview.txt")
    p.add_argument("--output",type=Path,default=ROOT/".blue-work/johto-offline12-preview.zip")
    args=p.parse_args(argv)
    try:
        value=pack(args.stage,args.rival,args.connections,args.game,args.output,
                   root=args.root)
    except (ValueError,OSError,KeyError,TypeError,IndexError,json.JSONDecodeError) as exc:
        print("[JOHTO][BLOQUEADO]",exc,file=sys.stderr)
        return 2
    print("[JOHTO] 12/12 OFFLINE auditados: 82 MapNNN, 32 eventos, 44 conexões, 21 equipes PBS.")
    print("[JOHTO] ZIP PRIVADO para auditoria, NÃO instalar no Blue-Story.exe ou game/.")
    print("[JOHTO] Bloqueios de jogabilidade:",len(value["install_blockers"]))
    print("[JOHTO] Nenhum Game.exe executado; jogáveis/testados permanecem 0/13.")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
