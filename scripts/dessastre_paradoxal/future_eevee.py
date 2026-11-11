"""Install Eevee's nine regional forms from the site's verified atlas.

Only Python standard library is required. Never overwrites official form data
or source graphics; all authored files are placed in dedicated PBS/graphics paths.
"""
from __future__ import annotations
import hashlib
import json
import re
import struct
import zlib
from pathlib import Path

FORM=50
ROLES=("front","front-shiny","back","back-shiny","icon","icon-shiny","footprint")
GRAPHICS=("Front","Front shiny","Back","Back shiny","Icons","Icons shiny","Footprints")
TYPE_NAMES={"GHOST":"Fantasma","POISON":"Veneno","STEEL":"Aco","GROUND":"Terra",
            "DRAGON":"Dragao","BUG":"Inseto","ROCK":"Pedra","FLYING":"Voador",
            "FIGHTING":"Lutador"}
SIGNATURE=b"\x89PNG\r\n\x1a\n"
def load_manifest(project):
    data=json.loads((project/"site/public/data/future-eevee.json").read_text("utf8"))
    forms=data["forms"]
    expected={"EEVEE","VAPOREON","JOLTEON","FLAREON","ESPEON","UMBREON","LEAFEON","GLACEON","SYLVEON"}
    if len(forms)!=9 or {f["card"]["base"] for f in forms}!=expected:
        raise ValueError("Manifesto Eevee regional incompleto")
    if any(f["card"]["form"]!=FORM or f["card"]["id"]!=f["card"]["base"]+",50" for f in forms):
        raise ValueError("Numero de forma regional inesperado")
    return data

def _chunks(blob):
    if not blob.startswith(SIGNATURE):raise ValueError("Atlas PNG invalido")
    p=len(SIGNATURE)
    while p<len(blob):
        length=struct.unpack_from(">I",blob,p)[0]
        kind=blob[p+4:p+8]
        data=blob[p+8:p+8+length]
        crc=struct.unpack_from(">I",blob,p+8+length)[0]
        if zlib.crc32(kind+data)&0xffffffff!=crc:raise ValueError("Atlas PNG com CRC invalido")
        yield kind,data
        p+=length+12
        if kind==b"IEND":break

def rgba_atlas(blob):
    """Decode indexed/RGB/RGBA PNG (8 bpc, noninterlaced) without Pillow."""
    ihdr=None;palette=None;alpha=b"";compressed=[]
    for kind,data in _chunks(blob):
        if kind==b"IHDR":ihdr=struct.unpack(">IIBBBBB",data)
        elif kind==b"PLTE":palette=[tuple(data[i:i+3]) for i in range(0,len(data),3)]
        elif kind==b"tRNS":alpha=data
        elif kind==b"IDAT":compressed.append(data)
    if not ihdr:raise ValueError("IHDR ausente")
    w,h,depth,color,compression,filter_method,interlace=ihdr
    if (w,h)!=(896,1152) or depth!=8 or color not in (2,3,6) or compression or filter_method or interlace:
        raise ValueError("Atlas requer PNG de 896x1152 com 8 bits nao intercalados")
    bpp={2:3,3:1,6:4}[color]
    data=zlib.decompress(b"".join(compressed))
    width=w*bpp;offset=0;previous=bytearray(width);out=[]
    for row_index in range(h):
        kind=data[offset];offset+=1
        line=bytearray(data[offset:offset+width]);offset+=width
        if len(line)!=width:raise ValueError("PNG incompleto")
        for i in range(width):
            left=line[i-bpp] if i>=bpp else 0
            above=previous[i]
            upper_left=previous[i-bpp] if i>=bpp else 0
            if kind==0:predictor=0
            elif kind==1:predictor=left
            elif kind==2:predictor=above
            elif kind==3:predictor=(left+above)//2
            elif kind==4:
                p=left+above-upper_left
                da,db,dc=abs(p-left),abs(p-above),abs(p-upper_left)
                predictor=left if da<=db and da<=dc else above if db<=dc else upper_left
            else:raise ValueError("Filtro PNG invalido")
            line[i]=(line[i]+predictor)&255
        if color==3:
            if not palette:raise ValueError("Paleta PNG ausente")
            out.append(b"".join(bytes((*palette[v],alpha[v] if v<len(alpha) else 255)) for v in line))
        elif color==2:
            out.append(b"".join(bytes((line[i],line[i+1],line[i+2],255)) for i in range(0,len(line),3)))
        else:out.append(bytes(line))
        previous=line
    if offset!=len(data):raise ValueError("Dados PNG excedentes")
    return out

def _png_chunk(tag,data):
    return struct.pack(">I",len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data)&0xffffffff)

def encode_rgba(rows):
    width=len(rows[0])//4;height=len(rows)
    raw=b"".join(b"\0"+line for line in rows)
    header=struct.pack(">IIBBBBB",width,height,8,6,0,0,0)
    return SIGNATURE+_png_chunk(b"IHDR",header)+_png_chunk(b"IDAT",zlib.compress(raw,9))+_png_chunk(b"IEND",b"")

def extract_sprites(project,manifest):
    src=project/"site/public/assets/future-eevee/sprites-atlas.png"
    atlas=rgba_atlas(src.read_bytes())
    assets={}
    for row,entry in enumerate(manifest["forms"]):
        base=entry["card"]["base"]
        for col,(role,folder) in enumerate(zip(ROLES,GRAPHICS)):
            size=128 if col<4 else 64 if col<6 else 48
            # The site atlas has 128-pixel cells; nearest-neighbor preserves
            # hard-edged pixel art for the smaller icon/footprint roles.
            image=[]
            for y in range(size):
                source_y=row*128+(y*128//size)
                atlas_line=atlas[source_y]
                image.append(b"".join(
                    atlas_line[4*(col*128+(x*128//size)):4*(col*128+(x*128//size)+1)]
                    for x in range(size)
                ))
            assets[f"Graphics/Pokemon/{folder}/{base}_{FORM}.png"]=encode_rgba(image)
    return assets

def build_forms(manifest,known_moves,known_abilities):
    blocks=[];missing_moves=set();missing_abilities=set()
    for entry in manifest["forms"]:
        card=entry["card"];data=entry["details"];base=card["base"]
        abilities=[a for a in data["abilities"] if a in known_abilities]
        hidden=[a for a in data.get("hidden",[]) if a in known_abilities]
        missing_abilities.update(set(data["abilities"]+data.get("hidden",[]))-known_abilities)
        if not abilities:raise ValueError("Nenhuma habilidade legal para "+base)
        level=[(int(l),m) for l,m in data["moves"] if m in known_moves]
        missing_moves.update(m for l,m in data["moves"] if m not in known_moves)
        if not level:raise ValueError("Nenhum golpe legal para "+base)
        tutors=[m for m in dict.fromkeys(data.get("tm",[])+data.get("tutor",[])) if m in known_moves]
        eggs=[m for m in dict.fromkeys(data.get("egg",[])) if m in known_moves]
        missing_moves.update(set(data.get("tm",[])+data.get("tutor",[])+data.get("egg",[]))-known_moves)
        lines=[f"[{base},{FORM}]",
               "FormName = Regional "+TYPE_NAMES[card["types"][0]],
               "Types = "+",".join(card["types"]),
               "BaseStats = "+",".join(map(str,card["stats"])),
               "Abilities = "+",".join(abilities),
               "Moves = "+",".join(str(v) for l,m in level for v in (l,m)),
               "TutorMoves = "+",".join(tutors),
               "Flags = DessastreParadoxal,RegionalEevee"]
        if hidden:lines.append("HiddenAbilities = "+",".join(hidden))
        if eggs:lines.append("EggMoves = "+",".join(eggs))
        if base=="EEVEE":
            evolved=[f"{name},{rule['methodId']},{rule['minLevel']}" for name,rule in manifest["evolutions"].items()]
            lines.append("Evolutions = "+",".join(evolved))
        lines.append("Pokedex = Forma regional do Eevee de Dessastre Paradoxal.")
        blocks.append("\n".join(lines))
    return "# Formas regionais do Eevee - geracao Dessastre Paradoxal\n#-------------------------------\n"+"\n#-------------------------------\n".join(blocks)+"\n",sorted(missing_moves),sorted(missing_abilities)

def distribute(weights,total):
    if not weights or total<len(weights):raise ValueError("Nao ha espaco para manter todos os encontros")
    portions=[w*total/sum(weights) for w in weights]
    result=[int(x) for x in portions]
    for index in sorted(range(len(result)),key=lambda i:(portions[i]-result[i],-i),reverse=True)[:total-sum(result)]:
        result[index]+=1
    if min(result)<1:raise ValueError("Chance insuficiente para preservar especies nativas")
    return result

def regional_encounters(text,config,paradox_ids):
    entries={(a["mapId"],a["method"]):a for a in config["areas"]}
    if len(entries)!=9 or len({a["species"] for a in config["areas"]})!=9:
        raise ValueError("Cada forma regional precisa de uma area unica")
    if {a["percent"] for a in config["areas"] if a["species"]=="EEVEE_50"}!={20}:
        raise ValueError("Eevee regional exige 20%")
    if any(a["percent"]!=5 for a in config["areas"] if a["species"]!="EEVEE_50"):
        raise ValueError("Eeveelutions regionais exigem 5%")
    form_ids={a["species"] for a in config["areas"]}
    sections=list(re.finditer(r"^\[([^\]\r\n]+)\][^\r\n]*(?:\r?\n|$)",text,re.M))
    found=set()
    table_pattern=re.compile(r"(?m)^([A-Za-z]+),\d+[^\r\n]*\r?\n((?:[ \t]+\d+,[^\r\n]+(?:\r?\n|$))+)") 
    for i in range(len(sections)-1,-1,-1):
        m=sections[i];start=m.start();end=sections[i+1].start() if i+1<len(sections) else len(text)
        map_id=int(m[1].split(",")[0]);block=text[start:end]
        def rewrite(match):
            key=(map_id,match[1]);area=entries.get(key)
            rows=[[part.strip() for part in line.split(",")] for line in match[2].splitlines() if line.strip()]
            local=[r for r in rows if r[1] not in form_ids]
            if not area:return match[0]
            if not local:raise ValueError("Sem encontros originais em "+str(key))
            fixed=[r for r in local if r[1] in paradox_ids]
            normal=[r for r in local if r[1] not in paradox_ids]
            remainder=100-int(area["percent"])-sum(int(r[0]) for r in fixed)
            weights=distribute([int(r[0]) for r in normal],remainder)
            newline="\r\n" if "\r\n" in match[0] else "\n"
            result=["    "+",".join([str(weight),*r[1:]]) for weight,r in zip(weights,normal)]
            result+=["    "+",".join(r) for r in fixed]
            # Level range comes from existing encounter table, never guessed.
            result+=["    "+",".join([str(area["percent"]),area["species"],*normal[0][2:]])]
            found.add(key)
            return match[0][:match.start(2)-match.start()]+newline.join(result)+newline
        block=table_pattern.sub(rewrite,block)
        text=text[:start]+block+text[end:]
    missing=set(entries)-found
    if missing:raise ValueError("Area ou metodo sem encontro PBS: "+str(sorted(missing)))
    return text

def patch_trainers(text,config):
    headers=list(re.finditer(r"(?m)^\[([^,\]\r\n]+),([^\]\r\n]+)\][^\r\n]*\r?\n",text))
    target={(x["trainerType"],x["name"]):x for x in config["trainers"]}
    updated=0
    for i in range(len(headers)-1,-1,-1):
        m=headers[i];key=(m[1].strip(),m[2].strip());entry=target.get(key)
        if not entry:continue
        stop=headers[i+1].start() if i+1<len(headers) else len(text)
        original=text[m.end():stop]
        blocks=re.findall(r"(?m)^\s*Pokemon\s*=\s*([A-Z0-9_]+)\s*,\s*(\d+)",original)
        if any(mon==entry["species"] and re.search(r"(?m)^\s*Form\s*=\s*50\s*$",original) for mon,level in blocks):
            continue
        if not blocks or len(blocks)>=6:continue
        level=max(int(level) for mon,level in blocks)
        newline="\r\n" if "\r\n" in original else "\n"
        new="Pokemon = "+entry["species"]+","+str(level)+newline+"    Form = 50"+newline
        pos=original.find("#-------------------------------")
        if pos<0:pos=len(original)
        text=text[:m.end()+pos]+new+text[m.end()+pos:]
        updated+=1
    return text,updated
