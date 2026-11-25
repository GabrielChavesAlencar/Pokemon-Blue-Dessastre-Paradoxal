"""VIS01–VIS07: optional, hash-pinned local map/overworld import for Sinnoh QA.

Only data from the two user-supplied archives is read. No archive extraction,
network, Ruby execution, redistribution, donor events or campaign writes.
"""
from __future__ import annotations
from collections import deque
import copy
import hashlib
import io
import os
import re
from pathlib import Path
import struct
import zipfile
import zlib
from audit_sinnoh_rxdata import read_marshal
from server.ruby_marshal import RubyData
from stage import serialize
from prepare_sinnoh_nine_original_j11c import table1
from sinnoh_visual_qa import png

PACKS = {
    "maps": ("Sinnoh Maps.zip", "79a7a4e4d176039daa9d3a2866540ced4daad4c9043a9a82378dae45a60e9e26"),
    "overworlds": ("Ultimate Gen 4 Overworlds Pack.zip", "e9d240918b62460c76d56ec9e5d4067a4ee853979d16a6657c05917d9bfd2b99"),
}
DONOR = {
    "SINNOH_TWINLEAF_TOWN": (194, b"Twinleaf Town", (36,36)),
    "SINNOH_ROUTE_201": (193, b"Route 201", (64,30)),
    "SINNOH_SANDGEM_TOWN": (192, b"Sandgem Town", (38,32)),
    "SINNOH_ROUTE_202": (191, b"Route 202", (46,31)),
    "SINNOH_LAKE_VERITY": (196, b"Lake Verity", (62,50)),
}
# Candidate anchors from the supplied map geometry, not Nintendo coordinates
# or native QA. Lakefront (195) is not in the existing nine-map pilot.
ANCHORS = {
    "SN_TOWN_TO_HOME": (13,22), "SN_TOWN_TO_BARRY_HOME": (23,12),
    "SN_TOWN_TO_ROUTE201": (18,1), "SN_ROUTE201_TO_TOWN": (16,28),
    "SN_ROUTE201_TO_LAKE": (1,17), "SN_ROUTE201_TO_SANDGEM": (62,8),
    "SN_LAKE_TO_ROUTE201": (44,43), "SN_NPC_ROWAN_BRIEFCASE": (45,40),
    "SN_BALL_TURTWIG": (44,38), "SN_BALL_CHIMCHAR": (45,38),
    "SN_BALL_PIPLUP": (46,38), "SN_NPC_BARRY_BATTLE": (47,35),
    "SN_SANDGEM_TO_ROUTE201": (1,13), "SN_SANDGEM_TO_ROWAN_LAB": (9,10),
    "SN_SANDGEM_TO_ROUTE202": (26,1), "SN_ROUTE202_TO_SANDGEM": (31,29),
}
SEEDS = {
    "SINNOH_TWINLEAF_TOWN": (18,1), "SINNOH_ROUTE_201": (16,28),
    "SINNOH_SANDGEM_TOWN": (1,13), "SINNOH_ROUTE_202": (31,29),
    "SINNOH_LAKE_VERITY": (44,43),
}
SPRITES = {"MOTHER": "NPC_126_Mom", "BARRY": "NPC_140_Barry", "ROWAN": "NPC_138_Prof_Rowan"}
PLAYER = {"LUCAS": "NPC_199_Lucas", "DAWN": "NPC_202_Dawn"}
MAP_ROOT = "Sinnoh Maps/"
OW_ROOT = "Ultimate Gen 4 Overworlds Pack/All Official Overworlds/"
TILESET = "SNQA_Private_Outdoors"
CREDITS = "PhantomFae; Game Freak; original map/tileset contributors; PurpleZaffre (overworlds). Local use only; R08 not approved."


def fail(reason):
    raise ValueError("SINNOH_PRIVATE_VISUAL:" + reason)


def discover(project):
    # The archive stays in the user's folder, outside source control.
    dirs = [project / ".blue-work" / "sinnoh-private-input", project]
    launcher = os.environ.get("BLUE_STORY_LAUNCHER_DIR")
    if launcher:
        dirs.append(Path(launcher))
    dirs.append(Path.home() / "Downloads")
    found = {}
    for kind, (name, expected) in PACKS.items():
        for folder in dirs:
            path = folder / name
            if not path.exists():
                continue
            if path.is_symlink() or not path.is_file() or path.stat().st_size > 120_000_000:
                fail("UNSAFE_ARCHIVE:" + name)
            with path.open("rb") as f:
                actual = hashlib.file_digest(f, "sha256").hexdigest()
            if actual != expected:
                fail("ARCHIVE_SHA256_MISMATCH:" + name)
            found[kind] = path
            break
    return found


def verified_archive(path, kind):
    """Read the exact approved input bytes, then open them inertly in memory."""
    path=Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size>120_000_000:
        fail("UNSAFE_ARCHIVE:"+kind)
    with path.open("rb") as f:
        raw=f.read(120_000_001)
    if len(raw)>120_000_000 or hashlib.sha256(raw).hexdigest()!=PACKS[kind][1]:
        fail("ARCHIVE_SHA256_MISMATCH:"+kind)
    return zipfile.ZipFile(io.BytesIO(raw))


def member(archive, name, max_bytes=32_000_000):
    matches = [i for i in archive.infolist() if i.filename.casefold() == name.casefold()]
    if len(matches) != 1 or matches[0].filename != name or matches[0].is_dir():
        fail("MISSING_OR_DUPLICATE_MEMBER:" + name)
    info = matches[0]
    if info.file_size > max_bytes or ((info.external_attr >> 16) & 0o170000) == 0o120000:
        fail("UNSAFE_MEMBER:" + name)
    with archive.open(info) as f:
        raw = f.read(max_bytes + 1)
    if len(raw) != info.file_size:
        fail("MEMBER_SIZE:" + name)
    return raw


def dims(raw):
    if len(raw) < 33 or raw[:8] != b"\x89PNG\r\n\x1a\n" or raw[12:16] != b"IHDR":
        fail("PNG_HEADER")
    return struct.unpack_from(">II", raw, 16)


def rgba_rows(raw):
    # The pinned outdoors sheet is non-interlaced 8-bit RGBA.
    w,h=dims(raw)
    if (w,h)!=(256,29984) or raw[24:29]!=bytes((8,6,0,0,0)):
        fail("OUTDOOR_PNG_FORMAT")
    off=8;chunks=[];end=False
    while off+12<=len(raw):
        n=struct.unpack_from(">I",raw,off)[0]
        if off+12+n>len(raw):
            fail("PNG_CHUNK_LENGTH")
        tag=raw[off+4:off+8];body=raw[off+8:off+8+n]
        if zlib.crc32(tag+body)&0xffffffff!=struct.unpack_from(">I",raw,off+8+n)[0]:
            fail("PNG_CRC")
        if tag==b"IDAT":chunks.append(body)
        off+=12+n
        if tag==b"IEND":end=True;break
    if not end or off!=len(raw):
        fail("PNG_TRAILING_DATA")
    stride=w*4;limit=h*(stride+1)
    dec=zlib.decompressobj()
    data=dec.decompress(b"".join(chunks),limit+1)
    if len(data)!=limit or not dec.eof or dec.unused_data:
        fail("PNG_DECOMPRESSED_LENGTH")
    previous=bytearray(stride)
    for y in range(h):
        i=y*(stride+1);mode=data[i];row=bytearray(data[i+1:i+1+stride])
        if mode==1:
            for x in range(4,stride):row[x]=(row[x]+row[x-4])&255
        elif mode==2:
            row=bytearray((a+b)&255 for a,b in zip(row,previous))
        elif mode==3:
            for x in range(stride):
                a=row[x-4] if x>=4 else 0
                row[x]=(row[x]+((a+previous[x])//2))&255
        elif mode==4:
            for x in range(stride):
                a=row[x-4] if x>=4 else 0;b=previous[x];c=previous[x-4] if x>=4 else 0
                p=a+b-c;pa=abs(p-a);pb=abs(p-b);pc=abs(p-c)
                row[x]=(row[x]+(a if pa<=pb and pa<=pc else b if pb<=pc else c))&255
        elif mode!=0:fail("PNG_FILTER")
        yield row
        previous=row


def compact_atlas(raw, ids):
    if not ids or any(t<384 or t>=7880 for t in ids):
        fail("TILE_OUT_OF_SOURCE_RANGE")
    remap={t:384+i for i,t in enumerate(sorted(ids))}
    height=((len(ids)+7)//8)*32
    if height>4096:
        fail("COMPACT_ATLAS_TOO_TALL")
    result=bytearray(256*height*4)
    groups={}
    for src,dst in remap.items():
        old=src-384;new=dst-384
        groups.setdefault(old//8,[]).append((old%8,new%8,new//8))
    for y,row in enumerate(rgba_rows(raw)):
        for x,nx,ny in groups.get(y//32,()):
            pos=((ny*32+y%32)*256+nx*32)*4
            result[pos:pos+128]=row[x*128:x*128+128]
    return png(256,height,bytes(result)),remap


def table(raw, expected):
    if not isinstance(raw,RubyData) or raw.name!="Table" or len(raw.data)!=20+2*expected:
        fail("INVALID_SOURCE_TABLE")
    if struct.unpack_from("<5I",raw.data)!=(1,expected,1,1,expected):
        fail("INVALID_SOURCE_TABLE_HEADER")
    return struct.unpack_from("<%dH"%expected,raw.data,20)


def map_cells(map_obj, size):
    a=map_obj.attrs;w,h=size
    if (a["@width"],a["@height"],a["@tileset_id"])!=(w,h,24):
        fail("SOURCE_MAP_DIMENSIONS_OR_TILESET")
    raw=a["@data"];n=w*h*3
    if not isinstance(raw,RubyData) or raw.name!="Table" or len(raw.data)!=20+2*n:
        fail("SOURCE_MAP_TABLE")
    if struct.unpack_from("<5I",raw.data)!=(3,w,h,3,n):
        fail("SOURCE_MAP_TABLE_HEADER")
    cells=struct.unpack_from("<%dH"%n,raw.data,20)
    if any(t and not 384<=t<7880 for t in cells):
        fail("SOURCE_MAP_TILE_RANGE")
    return cells


def connected(cells,w,h,passages,seed):
    free=set()
    for y in range(h):
        for x in range(w):
            i=y*w+x;ts=[cells[i+l*w*h] for l in range(3) if cells[i+l*w*h]]
            if ts and all(not (passages[t]&15) for t in ts):free.add((x,y))
    if seed not in free:fail("DONOR_SEED_BLOCKED")
    seen={seed};queue=deque([seed])
    while queue:
        x,y=queue.popleft()
        for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if q in free and q not in seen:
                seen.add(q);queue.append(q)
    return seen



# Authored four-room geometry using actual donor interior tiles (not copied
# maps). Source slot 25 was inspected; no specific Sinnoh interiors exist.
INTERIOR_SIZES={"SINNOH_PLAYER_BEDROOM":(12,10),"SINNOH_PLAYER_HOUSE_1F":(16,12),
                "SINNOH_BARRY_HOUSE":(14,12),"SINNOH_PROFESSOR_ROWAN_LABORATORY":(18,13)}
INTERIOR_ANCHORS={"SN_BEDROOM_TO_1F":(10,8),"SN_1F_TO_BEDROOM":(13,3),
                  "SN_1F_TO_TWINLEAF":(8,11),"SN_NPC_MOTHER":(8,7),
                  "SN_BARRY_HOME_TO_TOWN":(7,11),"SN_NPC_BARRY_INTRO":(7,7),
                  "SN_ROWAN_LAB_TO_TOWN":(9,12),"SN_NPC_ROWAN_POKEDEX":(9,5)}
INTERIOR_TILESET="SNQA_Private_Indoors"


def interior_cells(symbol):
    w,h=INTERIOR_SIZES[symbol]
    lab=symbol.endswith("LABORATORY");bedroom=symbol.endswith("BEDROOM")
    area=w*h;cells=[0]*(area*3)
    def put(x,y,t,z=1):
        if not (0<=x<w and 0<=y<h):fail("INTERIOR_COORDINATE")
        cells[z*area+y*w+x]=t
    def patch(x,y,rows,z=1):
        for dy,row in enumerate(rows):
            for dx,t in enumerate(row):
                if t:put(x+dx,y+dy,t,z)
    for y in range(h):
        for x in range(w):
            put(x,y,(1795,1796,1797)[x%3] if lab else (1355,1356,1357)[(x+y)%3],0)
    for x in range(w):
        put(x,0,1608 if lab else 1371);put(x,1,1616 if lab else 1379)
    for y in range(2,h):
        put(0,y,1617 if lab else 1378);put(w-1,y,1617 if lab else 1380)
    for x in range(1,w-1):
        if bedroom or x!=w//2:put(x,h-1,1616 if lab else 1379)
    def rug(x,y,width,height,top,mid,bottom):
        for yy in range(height):
            row=top if yy==0 else bottom if yy==height-1 else mid
            for xx in range(width):
                put(x+xx,y+yy,row[0 if xx==0 else 2 if xx==width-1 else 1],0)
    def shelf(x,y):
        patch(x,y,[[1464,1465,1466],[1472,1473,1474],[1480,1481,1482]])
    def plant(x,y):
        put(x,y,1084,2);put(x,y+1,1092)
    if bedroom:
        patch(1,2,[[1288,1289],[1296,1297]])
        patch(7,2,[[1504,1505,1506],[1512,1513,1514],[1520,1521,1522]])
        put(8,2,1488,2);shelf(1,5);plant(10,2)
        rug(4,4,4,3,[1096,1097,1098],[1104,1105,1106],[1112,1113,1114])
        put(10,8,1637,0)
    elif lab:
        for x in (2,12):
            patch(x,2,[[1144,1145,1146,1145],[1152,1153,1154,1153],[1160,1161,1162,1161]])
            put(x+1,3,1488,2);put(x+2,3,1489,2)
        patch(2,7,[[1564,1565,1566],[1572,1573,1574]])
        patch(13,7,[[1309,1310,1311],[1317,1318,1319]])
        shelf(7,2);plant(16,9)
        rug(7,7,4,4,[1771,1772,1773],[1779,1780,1781],[1787,1788,1789])
    else:
        shelf(1,2);plant(w-2,2)
        patch(5,2,[[1256,1257,1258],[1264,1265,1266]])
        rug(4,5,5,4,[1099,1100,1101],[1107,1108,1109],[1115,1116,1117])
        if w>=16:
            patch(11,5,[[1504,1505,1506],[1512,1513,1514],[1520,1521,1522]])
            put(13,3,1638,0)
        else:
            patch(10,5,[[1504,1505],[1512,1513],[1520,1521]])
    return cells


def apply_interiors(out,mapping,archive,components,imported):
    source=read_marshal(member(archive,MAP_ROOT+"Data/Tilesets.rxdata"),"PRIVATE_INTERIOR_TILESETS")[25]
    if source.attrs["@tileset_name"]!=b"indoors" or any(source.attrs["@autotile_names"]):
        fail("INTERIOR_SOURCE_TILESET")
    tables={k:table(source.attrs[k],7880) for k in ("@passages","@priorities","@terrain_tags")}
    layers={symbol:interior_cells(symbol) for symbol in INTERIOR_SIZES}
    used={t for cells in layers.values() for t in cells if t}
    atlas,remap=compact_atlas(member(archive,MAP_ROOT+"Graphics/Tilesets/indoors.png"),used)
    tiles=read_marshal(out["Data/Tilesets.rxdata"],"QA_INTERIOR_TILESETS")
    tid=len(tiles)
    if tid>=5000:fail("QA_INTERIOR_TILESET_CAPACITY")
    candidate=copy.deepcopy(source);a=candidate.attrs
    a.update({"@id":tid,"@name":b"Sinnoh private interiors QA","@tileset_name":INTERIOR_TILESET.encode()})
    total=384+((len(remap)+7)//8)*8
    for key,values in tables.items():
        entries=list(values[:384])+[15 if key=="@passages" else 0]*(total-384)
        for old,new in remap.items():entries[new]=values[old]
        a[key]=table1(entries)
    tiles.append(candidate);out["Data/Tilesets.rxdata"]=serialize(tiles)
    out["Graphics/Tilesets/"+INTERIOR_TILESET+".png"]=atlas
    for symbol,(w,h) in INTERIOR_SIZES.items():
        cells=layers[symbol];n=w*h*3
        components[symbol]=connected(cells,w,h,tables["@passages"],(w//2,h-2))
        target="Data/Map%03d.rxdata"%mapping[symbol]
        m=read_marshal(out[target],"QA_INTERIOR_MAP")
        m.attrs.update({"@width":w,"@height":h,"@tileset_id":tid,"@events":{},
                        "@data":RubyData("Table",struct.pack("<5I",3,w,h,3,n)+
                              struct.pack("<%dH"%n,*(remap[t] if t else 0 for t in cells)))})
        out[target]=serialize(m)
        imported[symbol]={"source_id":None,"target_id":mapping[symbol],"source_tileset_id":25,
                          "target_tileset_id":tid,"width":w,"height":h,"authored_layout":True,
                          "model_connected_cells":len(components[symbol])}


LAKEFRONT="SINNOH_VERITY_LAKEFRONT"
LAKEFRONT_SOURCE=(195,b"Verity Lakefront",(26,22))


def donor_maps(mapping):
    return {**DONOR,**({LAKEFRONT:LAKEFRONT_SOURCE} if LAKEFRONT in mapping else {})}


def apply_maps(blobs,mapping,path):
    out=dict(blobs);components={};imported={}
    with verified_archive(path,"maps") as z:
        infos=read_marshal(member(z,MAP_ROOT+"Data/MapInfos.rxdata"),"PRIVATE_INFOS")
        source=read_marshal(member(z,MAP_ROOT+"Data/Tilesets.rxdata"),"PRIVATE_TILESETS")[24]
        if source.attrs["@tileset_name"]!=b"outdoors":fail("SOURCE_TILESET_NAME")
        tables={k:table(source.attrs[k],7880) for k in ("@passages","@priorities","@terrain_tags")}
        used=set();source_cells={}
        for symbol,(mid,name,size) in donor_maps(mapping).items():
            if infos[mid].attrs["@name"]!=name:fail("SOURCE_MAP_NAME:"+symbol)
            m=read_marshal(member(z,MAP_ROOT+"Data/Map%03d.rxdata"%mid),"PRIVATE_MAP")
            cells=map_cells(m,size)
            source_cells[symbol]=cells;used.update(t for t in cells if t)
            components[symbol]=connected(cells,*size,tables["@passages"],(25,13) if symbol==LAKEFRONT else SEEDS[symbol])
        atlas,remap=compact_atlas(member(z,MAP_ROOT+"Graphics/Tilesets/outdoors.png"),used)
        tiles=read_marshal(out["Data/Tilesets.rxdata"],"QA_TILESETS")
        tid=len(tiles)
        if tid>=5000:fail("QA_TILESET_CAPACITY")
        candidate=copy.deepcopy(source)
        a=candidate.attrs;a["@id"]=tid;a["@name"]=b"Sinnoh private outdoors QA";a["@tileset_name"]=TILESET.encode()
        # These five source maps contain zero autotile IDs. Preserve all seven
        # slots and referenced sheets anyway, with collision-free names.
        names=[]
        for i,name in enumerate(a["@autotile_names"]):
            if not name:names.append(b"");continue
            target="SNQA_Private_Auto_%d"%(i+1)
            raw=member(z,MAP_ROOT+"Graphics/Autotiles/"+name.decode("ascii")+".png")
            dims(raw);out["Graphics/Autotiles/"+target+".png"]=raw;names.append(target.encode())
        a["@autotile_names"]=names
        total=384+((len(remap)+7)//8)*8
        for key,values in tables.items():
            entries=list(values[:384])+[0]*(total-384)
            if key=="@passages":
                entries[384:]=[15]*(total-384)
            for old,new in remap.items():entries[new]=values[old]
            a[key]=table1(entries)
        tiles.append(candidate)
        out["Data/Tilesets.rxdata"]=serialize(tiles)
        out["Graphics/Tilesets/"+TILESET+".png"]=atlas
        for symbol,(mid,name,size) in donor_maps(mapping).items():
            target="Data/Map%03d.rxdata"%mapping[symbol]
            template=target if symbol!=LAKEFRONT else "Data/Map%03d.rxdata"%mapping["SINNOH_LAKE_VERITY"]
            m=read_marshal(out[template],"QA_DONOR_DESTINATION");w,h=size;n=w*h*3
            cells=source_cells[symbol]
            m.attrs.update({"@width":w,"@height":h,"@tileset_id":tid,"@events":{},
                            "@data":RubyData("Table",struct.pack("<5I",3,w,h,3,n)+
                                  struct.pack("<%dH"%n,*(remap[t] if t else 0 for t in cells)))})
            out[target]=serialize(m)
            imported[symbol]={"source_id":mid,"target_id":mapping[symbol],"source_tileset_id":24,
                              "target_tileset_id":tid,"width":w,"height":h,
                              "model_connected_cells":len(components[symbol])}
        apply_interiors(out,mapping,z,components,imported)
        if LAKEFRONT in mapping:
            idx=read_marshal(out["Data/MapInfos.rxdata"],"QA_EXTRA_MAPINFO")
            mid=mapping[LAKEFRONT]
            if mid in idx:fail("LAKEFRONT_ID_COLLISION")
            info=copy.deepcopy(idx[mapping["SINNOH_LAKE_VERITY"]]);info.attrs["@name"]=b"Verity Lakefront";info.attrs["@order"]=max(i.attrs["@order"] for i in idx.values())+1
            idx[mid]=info;out["Data/MapInfos.rxdata"]=serialize(idx)
    # Only the pilot's generated events are rebuilt. No donor event or global
    # source file is ever copied into the destination.
    for symbol in mapping:
        target="Data/Map%03d.rxdata"%mapping[symbol]
        m=read_marshal(out[target],"QA_RESET_EVENTS")
        m.attrs["@events"]={}
        out[target]=serialize(m)
    return out,components,imported


def apply_sprites(blobs,path):
    out=dict(blobs)
    with verified_archive(path,"overworlds") as z:
        for role,name in SPRITES.items():
            raw=member(z,OW_ROOT+name+".png",1_000_000)
            if dims(raw)!=(256,256):fail("SPRITE_DIMENSIONS:"+role)
            out["Graphics/Characters/SNQA_"+role+".png"]=raw
        for role in ("YOUNGSTER","LASS"):
            candidates=[i.filename for i in z.infolist() if re.fullmatch(re.escape(OW_ROOT)+r"NPC_\d+_"+role+r"\.png",i.filename,re.I)]
            if len(candidates)==1:
                raw=member(z,candidates[0],1_000_000)
                if dims(raw)==(256,256):out["Graphics/Characters/SNQA_"+role+".png"]=raw
        # The native Decades database already includes Platinum Lucas/Dawn
        # (metadata IDs 9/10). Keep its existing walking/running/bike/Surf/
        # fishing states; these optional sheets are local reference only.
    return out


def has_platinum_player(base, player_id=9):
    """Use the native Platinum player registration, not a global sprite overwrite."""
    names={9:"PLAYER_TRAINER_PL_Lucas",10:"PLAYER_TRAINER_PL_Dawn"}
    if player_id not in names:fail("INVALID_PLATINUM_PLAYER_ID")
    metadata=base/"PBS/metadata.txt"
    if not metadata.is_file() or metadata.is_symlink():
        return False
    raw=metadata.read_text("utf-8-sig")
    block=re.search(r"(?m)^\["+str(player_id)+r"\][ \t]*(?:#[^\n]*)?\n([\s\S]*?)(?=^\[\d+\]|\Z)",raw)
    if not block:
        return False
    fields={}
    for line in block.group(1).splitlines():
        line=line.split("#",1)[0]
        if "=" in line:
            k,v=line.split("=",1);fields[k.strip()]=v.strip()
    if fields.get("TrainerType")!=names[player_id]:
        return False
    # Selection only requires the native walking sheet. Optional movement
    # animations may have a different canvas size; do not hide the profile.
    for key in ("WalkCharset",):
        name=fields.get(key,"")
        if not re.fullmatch(r"[A-Za-z0-9_]+",name):
            return False
        path=base/"Graphics/Characters"/(name+".png")
        if not path.is_file() or path.is_symlink():
            return False
        if dims(path.read_bytes())!=(256,256):
            return False
    return True


# Actual connections in the pinned donor PBS. Only the three pairs whose
# two endpoints are present and have reachable common edge tiles are used.
# Lake Verity has no walkable shared boundary in this source; retain its
# authored warp. Jubilife and Verity Lakefront are not in this nine-map QA.
CONTINUOUS = (
    ("SINNOH_TWINLEAF_TOWN","N",2,"SINNOH_ROUTE_201","S",0,
     "SN_TOWN_TO_ROUTE201","SN_ROUTE201_TO_TOWN"),
    ("SINNOH_ROUTE_201","E",0,"SINNOH_SANDGEM_TOWN","W",4,
     "SN_ROUTE201_TO_SANDGEM","SN_SANDGEM_TO_ROUTE201"),
    ("SINNOH_SANDGEM_TOWN","N",0,"SINNOH_ROUTE_202","S",6,
     "SN_SANDGEM_TO_ROUTE202","SN_ROUTE202_TO_SANDGEM"),
)
DIRECTIONS={"N":"N","North":"N","S":"S","South":"S","E":"E","East":"E","W":"W","West":"W"}
AUDIO = {
    "Twinleaf":("DPPT 006 Twinleaf Town",True),
    "Route201":("DPPT 008 Route 201",True),
    "Lake":("DPPT 009 Lake",False),
    "Sandgem":("DPPT 016 Sandgem Town",True),
}
MAP_MUSIC = {
    "SINNOH_PLAYER_BEDROOM":"Twinleaf","SINNOH_PLAYER_HOUSE_1F":"Twinleaf",
    "SINNOH_TWINLEAF_TOWN":"Twinleaf","SINNOH_BARRY_HOUSE":"Twinleaf",
    "SINNOH_ROUTE_201":"Route201","SINNOH_ROUTE_202":"Route201",
    "SINNOH_LAKE_VERITY":"Lake","SINNOH_SANDGEM_TOWN":"Sandgem",
    "SINNOH_PROFESSOR_ROWAN_LABORATORY":"Sandgem",
}


def parse_connections(raw):
    rows=[]
    for line in raw.decode("utf-8-sig").splitlines():
        text=line.split("#",1)[0].strip()
        if not text:continue
        cols=[v.strip() for v in text.split(",")]
        if len(cols)!=6 or cols[1] not in DIRECTIONS or cols[4] not in DIRECTIONS:
            fail("SOURCE_CONNECTION_FORMAT")
        rows.append((int(cols[0]),DIRECTIONS[cols[1]],int(cols[2]),
                     int(cols[3]),DIRECTIONS[cols[4]],int(cols[5])))
    return rows


def edge_axis(points,size,direction,offset):
    w,h=size
    if direction=="N":return {x-offset for x,y in points if y==0}
    if direction=="S":return {x-offset for x,y in points if y==h-1}
    if direction=="W":return {y-offset for x,y in points if x==0}
    if direction=="E":return {y-offset for x,y in points if x==w-1}
    fail("SOURCE_EDGE_DIRECTION")


def connection_plan(mapping,components,source_rows):
    result=[]
    donors=donor_maps(mapping)
    pairs=CONTINUOUS+(((LAKEFRONT,"E",0,"SINNOH_ROUTE_201","W",4,"SN_ROUTE201_TO_LAKE",None),) if LAKEFRONT in mapping else ())
    for a,da,oa,b,db,ob,wa,wb in pairs:
        source=(donors[a][0],da,oa,donors[b][0],db,ob)
        reverse=(source[3],db,ob,source[0],da,oa)
        if source_rows.count(source)+source_rows.count(reverse)!=1:
            fail("SOURCE_CONNECTION_MISSING_OR_DUPLICATE")
        shared=edge_axis(components[a],donors[a][2],da,oa)&edge_axis(components[b],donors[b][2],db,ob)
        if not shared:fail("SOURCE_CONNECTION_NO_REACHABLE_SEAM")
        result.append({"record":[mapping[a],da,oa,mapping[b],db,ob],
                       "source_ids":[source[0],source[3]],"reachable_seam_tiles":len(shared),
                       "warp_keys":[k for k in (wa,wb) if k]})
    # The donor also aligns the two forest/water borders visually. Neither
    # border has a traversable common cell; actual lake access uses portals.
    if LAKEFRONT in mapping:
        for a,da,oa,b,db,ob in (("SINNOH_LAKE_VERITY","S",36,LAKEFRONT,"N",0),
                                 ("SINNOH_LAKE_VERITY","E",46,"SINNOH_ROUTE_201","W",0)):
            source=(donors[a][0],da,oa,donors[b][0],db,ob)
            reverse=(source[3],db,ob,source[0],da,oa)
            if source_rows.count(source)+source_rows.count(reverse)!=1:
                fail("SOURCE_VISUAL_CONNECTION_MISSING")
            if edge_axis(components[a],donors[a][2],da,oa)&edge_axis(components[b],donors[b][2],db,ob):
                fail("SOURCE_VISUAL_CONNECTION_UNEXPECTED_WALKABLE_EDGE")
            result.append({"record":[mapping[a],da,oa,mapping[b],db,ob],
                           "source_ids":[source[0],source[3]],"reachable_seam_tiles":0,
                           "warp_keys":[],"visual_only":True})
    return result


def merge_connections(base,plans,mapping):
    # Preserve every baseline compiled record; append only private QA IDs.
    from install_sinnoh_experimental_windows import regular
    data_path=base/"Data/map_connections.dat";pbs_path=base/"PBS/map_connections.txt"
    regular(data_path);regular(pbs_path)
    original=read_marshal(data_path.read_bytes(),"BASE_CONNECTIONS")
    if not isinstance(original,list):fail("BASE_CONNECTIONS_NOT_ARRAY")
    ids=set(mapping.values())
    for row in original:
        if (not isinstance(row,list) or len(row)!=6 or
            any(type(row[i]) is not int for i in (0,2,3,5)) or
            any(row[i] not in (b"N",b"S",b"E",b"W") for i in (1,4))):
            fail("BASE_CONNECTION_RECORD_UNSUPPORTED")
        if row[0] in ids or row[3] in ids:fail("BASE_CONNECTION_ID_COLLISION")
    pbs=pbs_path.read_bytes()
    if any(row[0] in ids or row[3] in ids for row in parse_connections(pbs)):
        fail("BASE_PBS_CONNECTION_ID_COLLISION")
    # Forest-only connections are source evidence, not traversable links.
    # Never let MapFactory choose the lake as an alternate seam destination.
    records=[p["record"] for p in plans if not p.get("visual_only")]
    rows=[[r[0],r[1].encode("ascii"),r[2],r[3],r[4].encode("ascii"),r[5]] for r in records]
    addition=("\n# Blue Sinnoh private QA - native seamless connections\n"+
              "\n".join(",".join(map(str,r)) for r in records)+"\n").encode("ascii")
    return {"Data/map_connections.dat":serialize(original+rows),
            "PBS/map_connections.txt":pbs+addition}


def bind_audio_and_connections(blobs,mapping,components,path,base):
    """Use actual donor BGM, day/night variants, and verified continuous seams."""
    from build_johto_events import EVENT_CLASSES,ruby
    from install_sinnoh_experimental_windows import regular
    out=dict(blobs)
    with verified_archive(path,"maps") as z:
        plans=connection_plan(mapping,components,parse_connections(member(z,MAP_ROOT+"PBS/map_connections.txt")))
        audio_files=[]
        for key,(name,night) in AUDIO.items():
            for suffix in ("","_n") if night else ("",):
                raw=member(z,MAP_ROOT+"Audio/BGM/"+name+suffix+".ogg")
                if not raw.startswith(b"OggS") or b"\x01vorbis" not in raw[:4096]:
                    fail("SOURCE_BGM_NOT_VORBIS:"+key)
                rel="Audio/BGM/SNQA_"+key+suffix+".ogg"
                out[rel]=raw;audio_files.append(rel)
    out.update(merge_connections(base,plans,mapping))
    # Metadata enables the native map system's outdoor/day/night behavior.
    # Only unoccupied private map IDs are appended; no other region is changed.
    pbs_path=base/"PBS/map_metadata.txt";regular(pbs_path)
    old=pbs_path.read_bytes()
    existing={int(m) for m in re.findall(rb"(?m)^\s*\[(\d+)\]",old)}
    if existing & set(mapping.values()):fail("BASE_MAP_METADATA_ID_COLLISION")
    meta=[]
    for symbol,mid in mapping.items():
        outside=symbol in donor_maps(mapping)
        area_name=donor_maps(mapping)[symbol][1].decode("ascii") if outside else {"SINNOH_PLAYER_BEDROOM":"Twinleaf Town","SINNOH_PLAYER_HOUSE_1F":"Twinleaf Town","SINNOH_BARRY_HOUSE":"Twinleaf Town","SINNOH_PROFESSOR_ROWAN_LABORATORY":"Sandgem Town"}[symbol]
        lines=["[%03d]"%mid, "Name = "+area_name, "Outdoor = "+("true" if outside else "false"),
               "ShowArea = "+("true" if outside else "false")]
        if outside:lines.append("Bicycle = true")
        if not outside or symbol=="SINNOH_LAKE_VERITY":lines.append("SnapEdges = true")
        meta.append("\n".join(lines))
    out["PBS/map_metadata.txt"]=old+b"\n# Blue Sinnoh private QA\n"+("\n#-------------------------------\n".join(meta)+"\n").encode("ascii")
    obsolete={key for plan in plans for key in plan["warp_keys"]}
    removed=set()
    for symbol,mid in mapping.items():
        rel="Data/Map%03d.rxdata"%mid
        m=read_marshal(out[rel],"QA_BGM_MAP")
        a=m.attrs
        a["@autoplay_bgm"]=True
        a["@bgm"]=ruby("RPG::AudioFile",name=("SNQA_"+("Route201" if symbol==LAKEFRONT else MAP_MUSIC[symbol])).encode("ascii"),volume=100,pitch=100)
        # Retain the authored event IDs/names, but retire their transfer pages:
        # otherwise touch warps jump before the seamless map boundary.
        for event in a["@events"].values():
            key=event.attrs["@name"].decode("ascii")
            if key not in obsolete:continue
            pages=event.attrs["@pages"]
            if len(pages)!=1 or not any(c.attrs["@code"]==201 for c in pages[0].attrs["@list"]):
                fail("EXPECTED_SEAM_WARP_NOT_FOUND:"+key)
            page=pages[0].attrs
            page["@list"]=[ruby("RPG::EventCommand",code=0,indent=0,parameters=[])]
            page["@trigger"]=0
            page["@through"]=True
            removed.add(key)
        out[rel]=serialize(m,EVENT_CLASSES)
    if removed!=obsolete:fail("SEAM_WARP_KEYS_INCOMPLETE")
    return out,{"connections":plans,"retired_warp_keys":sorted(removed),
                "audio_files":sorted(audio_files),"map_music":{**MAP_MUSIC,**({LAKEFRONT:"Route201"} if LAKEFRONT in mapping else {})},
                "native_reviewed":False}


def route201_encounters(base,mapping):
    """Authored early-route roster, using native Essentials 21.1 Land PBS."""
    from install_sinnoh_experimental_windows import regular
    path=base/"PBS/encounters.txt";regular(path)
    raw=path.read_bytes()
    mid=mapping["SINNOH_ROUTE_201"]
    occupied={int(m) for m in re.findall(rb"(?m)^\s*\[(\d+)(?:,\d+)?\]",raw)}
    if occupied & set(mapping.values()):fail("BASE_ENCOUNTER_ID_COLLISION")
    # DPPt-style introductory table; levels remain subject to existing runtime scaling.
    block=f"\n# Blue Sinnoh private QA\n[{mid:03d}] # Route 201\nLand,21\n    50,STARLY,2,3\n    50,BIDOOF,2,3\n"
    return raw+block.encode("ascii")


# Early-game Platinum roster. Route 201 keeps the Blue pilot's existing
# balance; Route 202 includes the morning/night Kricketot variation.
# Surf/fishing tables are prepared but their access remains HM/item gated.
LAND_ROSTER={
    "SINNOH_ROUTE_201":{"Land":((50,"STARLY",2,3),(50,"BIDOOF",2,3))},
    "SINNOH_ROUTE_202":{
        "Land":((20,"STARLY",2,4),(50,"BIDOOF",2,4),(30,"SHINX",3,4)),
        "LandMorning":((20,"STARLY",2,4),(40,"BIDOOF",2,4),(30,"SHINX",3,4),(10,"KRICKETOT",4,4)),
        "LandNight":((10,"STARLY",2,4),(50,"BIDOOF",2,4),(30,"SHINX",3,4),(10,"KRICKETOT",4,4))},
    "SINNOH_LAKE_VERITY":{"Land":((50,"STARLY",2,4),(50,"BIDOOF",2,4))},
}
WATER_ROSTER={
    "Water":((90,"PSYDUCK",20,30),(10,"GOLDUCK",20,40)),
    "OldRod":((100,"MAGIKARP",3,15),),
    "GoodRod":((65,"MAGIKARP",10,25),(35,"GOLDEEN",10,25)),
    "SuperRod":((65,"GYARADOS",30,55),(35,"SEAKING",30,55)),
}
# All first-visit trainer battles in the ten-map early-story scope.
ROUTE202_TRAINERS=(
    ("TRISTAN","YOUNGSTER","Tristan","STARLY"),
    ("NATALIE","LASS","Natalie","BIDOOF"),
    ("LOGAN","YOUNGSTER","Logan","BURMY"),
)
TRAINER_VERSION=202


def coverage_encounters(base,mapping,masks):
    from install_sinnoh_experimental_windows import regular
    from pbs import catalogue
    route201_encounters(base,mapping) # checks allocated IDs against baseline
    raw=(base/"PBS/encounters.txt").read_bytes()
    roster={k:dict(v) for k,v in LAND_ROSTER.items()}
    for sym in ("SINNOH_TWINLEAF_TOWN","SINNOH_LAKE_VERITY"):
        roster.setdefault(sym,{}).update(WATER_ROSTER)
    report={}
    species=set()
    blocks=[]
    for sym,mid in mapping.items():
        rows=masks.get(mid,[])
        grass=sum(row.count("g") for row in rows)
        methods=roster.get(sym,{})
        if grass and "Land" not in methods:
            fail("UNCOVERED_GRASS_MAP:"+sym)
        if "Land" in methods and not grass:
            fail("LAND_ROSTER_WITHOUT_GRASS:"+sym)
        report[sym]={"grass_cells":grass,"methods":sorted(methods),
                     "water_access_not_verified":bool("Water" in methods)}
        if not methods:continue
        blocks.append("[%03d] # %s"%(mid,sym))
        for method,entries in methods.items():
            if sum(e[0] for e in entries)!=100:fail("ENCOUNTER_WEIGHT_TOTAL")
            blocks.append(method+(",21" if method.startswith("Land") else ",2" if method=="Water" else ""))
            for weight,mon,lo,hi in entries:
                species.add(mon)
                blocks.append("    %d,%s,%d,%d"%(weight,mon,lo,hi))
    if not species<=catalogue(base,"pokemon"):fail("ENCOUNTER_SPECIES_MISSING")
    return raw+("\n# Blue Sinnoh coverage\n"+"\n".join(blocks)+"\n").encode("ascii"),report


def route202_trainer_pbs(base):
    from pbs import catalogue,read_blocks
    from install_sinnoh_experimental_windows import regular
    types=catalogue(base,"trainer_types")
    mons=catalogue(base,"pokemon")
    existing=set()
    for p in (base/"PBS").glob("trainers*.txt"):
        regular(p)
        existing.update(read_blocks(p))
    lines=[]
    for key,kind,name,mon in ROUTE202_TRAINERS:
        section=f"{kind},{name},{TRAINER_VERSION}"
        if kind not in types or mon not in mons:fail("ROUTE202_TRAINER_DATABASE_MISSING:"+key)
        if section in existing:fail("ROUTE202_TRAINER_ID_COLLISION:"+key)
        lines.extend(("["+section+"]",f"Pokemon = {mon},5",""))
    return ("\n".join(lines)+"\n").encode("ascii")


def route202_trainer_events(blobs,mapping,components):
    """Place three authored NPCs on verified ground; preserve every old ID.

    Select positions progressively north from Sandgem's entry using graph
    distance. Removing the three NPC cells must leave all remaining
    reachable cells connected, so the player cannot be trapped by an NPC.
    """
    from build_johto_events import EVENT_CLASSES,ruby,event_page
    from compile_sinnoh_playable_j04 import passable_point
    sym="SINNOH_ROUTE_202";mid=mapping[sym]
    rel="Data/Map%03d.rxdata"%mid
    out=dict(blobs)
    m=read_marshal(out[rel],"TRAINER_MAP")
    tiles=read_marshal(out["Data/Tilesets.rxdata"],"TRAINER_TILES")
    rows=movement_masks(out,mapping)[mid]
    points=components[sym]
    seed=SEEDS[sym]
    def distances(blocked):
        seen={seed:0};queue=deque([seed])
        while queue:
            x,y=queue.popleft()
            for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if q in points and q not in blocked and q not in seen:
                    seen[q]=seen[(x,y)]+1;queue.append(q)
        return seen
    dist=distances(set())
    events=m.attrs["@events"]
    used={(e.attrs["@x"],e.attrs["@y"]) for e in events.values()}
    chosen=set();positions=[]
    extent=max(dist.values())
    for (key,kind,name,mon),fraction in zip(ROUTE202_TRAINERS,(0.30,0.55,0.80)):
        candidates=sorted((q for q in dist if q not in used|chosen and
                           1<=q[0]<len(rows[0])-1 and 1<=q[1]<len(rows)-1 and
                           rows[q[1]][q[0]]=="." and all(abs(q[0]-x)+abs(q[1]-y)>=4 for x,y in chosen)),
                          key=lambda q:(abs(dist[q]-extent*fraction),q[1],q[0]))
        xy=next((q for q in candidates if len(distances(chosen|{q}))==len(dist)-len(chosen)-1),None)
        if xy is None:fail("NO_SAFE_ROUTE202_TRAINER_POSITION:"+key)
        passable_point(m,tiles,*xy)
        chosen.add(xy)
        eid=max(events,default=0)+1
        page=event_page(script=f'BlueSinnohPilot.route_trainer("{key}")',sprite="SNQA_"+kind)
        # Action interaction plus native sight trigger. Once defeated, the
        # empty sight-name condition is handled by the native self switch.
        page.attrs["@trigger"]=2
        finished=event_page(script=f'BlueSinnohPilot.route_trainer("{key}")',sprite="SNQA_"+kind)
        finished.attrs["@condition"].attrs.update({"@self_switch_valid":True,"@self_switch_ch":b"A"})
        events[eid]=ruby("RPG::Event",id=eid,name=("Trainer(3) SN_ROUTE202_"+key).encode("ascii"),
                         x=xy[0],y=xy[1],pages=[page,finished])
        positions.append({"key":key,"map_id":mid,"event_id":eid,"position":list(xy),"species":mon,"type":kind})
    out[rel]=serialize(m,EVENT_CLASSES)
    return out,positions


def movement_masks(blobs,mapping,extra_symbols=()):
    """Derive conservative ground collision and tall-grass masks from actual maps."""
    tiles=read_marshal(blobs["Data/Tilesets.rxdata"],"MOVEMENT_TILES")
    result={}
    for sym in sorted(set(donor_maps(mapping))|set(extra_symbols)):
        mid=mapping[sym]
        m=read_marshal(blobs["Data/Map%03d.rxdata"%mid],"MOVEMENT_MAP").attrs
        w,h=m["@width"],m["@height"]
        attrs=tiles[m["@tileset_id"]].attrs
        passages=attrs["@passages"].data[20:]
        tags=attrs["@terrain_tags"].data[20:]
        p=struct.unpack("<%dH"%(len(passages)//2),passages)
        t=struct.unpack("<%dH"%(len(tags)//2),tags)
        cells=struct.unpack_from("<%dH"%(w*h*3),m["@data"].data,20)
        rows=[]
        for y in range(h):
            row=[]
            for x in range(w):
                stack=[cells[z*w*h+y*w+x] for z in range(3) if cells[z*w*h+y*w+x]]
                if not stack or any(p[i]&15 for i in stack):row.append("#")
                elif any(t[i]==2 for i in stack):row.append("g")
                else:row.append(".")
            rows.append("".join(row))
        result[mid]=rows
    return result


def safe_grassless_component(rows,seed):
    w,h=len(rows[0]),len(rows)
    if not (0<=seed[0]<w and 0<=seed[1]<h and rows[seed[1]][seed[0]]=="."):
        fail("SAFE_START_BLOCKED")
    seen={seed};queue=deque([seed])
    while queue:
        x,y=queue.popleft()
        for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=xx<w and 0<=yy<h and rows[yy][xx]=="." and (xx,yy) not in seen:
                seen.add((xx,yy));queue.append((xx,yy))
    return seen


def verify_starter_corridor(masks,mapping):
    route=masks[mapping["SINNOH_ROUTE_201"]]
    front=masks[mapping[LAKEFRONT]]
    lake=masks[mapping["SINNOH_LAKE_VERITY"]]
    r=safe_grassless_component(route,(16,28))
    f=safe_grassless_component(front,(25,13))
    if not any((0,y) in r and (25,y-4) in f for y in range(4,26)):
        fail("NO_GRASSLESS_ROUTE_TO_LAKEFRONT")
    if not {(10,2),(11,2)}<=f:fail("NO_GRASSLESS_LAKEFRONT_PORTAL")
    for seed in ((44,42),(45,42)):
        l=safe_grassless_component(lake,seed)
        if not {(44,43),(45,43),(45,40)}<=l:
            fail("NO_GRASSLESS_LAKE_RETURN_OR_ROWAN")
        for x in (44,45,46):
            if not any(q in l for q in ((x,37),(x,39),(x-1,38),(x+1,38))):
                fail("NO_GRASSLESS_STARTER_ACCESS")


def movement_plugin(masks,route202=None):
    # Embedded immutable rows from verified local RXDATA. No assets published.
    # Scope is the isolated QA and its allocated map IDs, not global gameplay.
    import json
    rows="{"+",".join(str(mid)+"=>"+json.dumps(grid) for mid,grid in sorted(masks.items()))+"}"
    return ("""module BlueSinnohSafeMovement
  MASKS = __ROWS__.freeze
  ROUTE202 = __ROUTE202__
  def self.cell(id,x,y)
    rows=MASKS[id]
    return nil unless rows && x.is_a?(Integer) && y.is_a?(Integer) &&
      y>=0 && y<rows.length && x>=0 && x<rows[y].length
    rows[y][x,1]
  end

  def self.has_pokemon?
    $player && $player.respond_to?(:party) && $player.party.any? { |p|
      p && (!p.respond_to?(:egg?) || !p.egg?)
    }
  end

  module PlayerMovement
    def move_generic(dir,*args,&block)
      if BlueSinnohExperimental.private_copy? && $game_map &&
         BlueSinnohSafeMovement::MASKS.key?($game_map.map_id) &&
         [2,4,6,8].include?(dir)
        facing = $map_factory && $map_factory.getFacingTile(dir,self)
        if facing && BlueSinnohSafeMovement::MASKS.key?(facing[0])
          if BlueSinnohSafeMovement::ROUTE202 && facing[0]==BlueSinnohSafeMovement::ROUTE202 &&
             $game_map.map_id!=BlueSinnohSafeMovement::ROUTE202 && !BlueSinnohPilot.route202_allowed?
            unless @blue_sinnoh_lab_warning
              @blue_sinnoh_lab_warning=true
              pbMessage(_INTL("Antes de seguir, visite Rowan no laboratorio de Sandgem e receba a Pokedex e cinco Poke Bolas."))
            end
            return
          end
          cell=BlueSinnohSafeMovement.cell(*facing)
          return if cell.nil?
          if defined?(BlueSinnohF12DIntegrated)
            current=[$game_map.map_id,x,y]
            origin=BlueSinnohF12DIntegrated.surf_route_mode(current)
            target=BlueSinnohF12DIntegrated.surf_route_mode(facing)
            if origin=="surf" || target=="surf"
              return unless BlueSinnohF12DIntegrated.runtime_surf_step_allowed?(current,facing)
              # Only the verified water edge may bypass the conservative
              # dry mask. Never override native passable?, jump or walls.
              return if cell=="#" && target!="surf"
            elsif cell=="#"
              return
            end
          elsif cell=="#"
            return
          end
          if cell=="g" && !BlueSinnohSafeMovement.has_pokemon?
            unless @blue_sinnoh_grass_warning
              @blue_sinnoh_grass_warning=true
              pbMessage(_INTL("E perigoso entrar na grama alta sem um Pokemon!"))
            end
            return
          end
        elsif !facing || !BlueSinnohSafeMovement::MASKS.key?(facing[0])
          # Outdoor map edges cannot escape the isolated pilot.
          return
        end
        @blue_sinnoh_grass_warning=false
        @blue_sinnoh_lab_warning=false
      end
      super(dir,*args,&block)
    end
  end

  def self.install!
    return unless BlueSinnohExperimental.private_copy?
    raise "Sinnoh QA: API de movimento ausente" unless defined?(Game_Player) &&
      Game_Player.method_defined?(:move_generic)
    Game_Player.prepend(PlayerMovement) unless Game_Player.ancestors.include?(PlayerMovement)
  end
end
""").replace("__ROWS__",rows).replace("__ROUTE202__",str(route202) if route202 is not None else "nil").encode("utf-8")


def extend_lake_story(blobs,mapping,components):
    """Add original authored story scenes; never import donor scripts."""
    from build_johto_events import EVENT_CLASSES,ruby,event_page,command
    from compile_sinnoh_playable_j04 import passable_point
    if LAKEFRONT not in mapping:fail("STORY_REQUIRES_LAKEFRONT")
    out=dict(blobs)
    tiles=read_marshal(out["Data/Tilesets.rxdata"],"STORY_TILES")
    worlds={sym:read_marshal(out["Data/Map%03d.rxdata"%mid],"STORY_MAP") for sym,mid in mapping.items()}
    lake="SINNOH_LAKE_VERITY"
    def world(sym):return worlds[sym].attrs["@events"]
    def point(sym,xy):
        if xy not in components[sym]:fail("STORY_POINT_NOT_REACHABLE:"+sym)
        passable_point(worlds[sym],tiles,*xy)
    def event(sym,key,xy,page,existing=None,pages=None):
        point(sym,xy);events=world(sym)
        eid=existing if existing is not None else max(events,default=0)+1
        if any((e.attrs["@x"],e.attrs["@y"])==xy and i!=eid for i,e in events.items()):
            fail("STORY_EVENT_POSITION_COLLISION:"+key)
        events[eid]=ruby("RPG::Event",id=eid,name=key.encode("ascii"),
                         x=xy[0],y=xy[1],pages=pages or [page])
    # Use the donor's actual reciprocal portal coordinates, not a warp
    # invented from nearest generic terrain. The two entry lanes match.
    old_exit=[i for i,e in world(lake).items() if e.attrs["@name"]==b"SN_LAKE_TO_ROUTE201"]
    if len(old_exit)!=1:fail("STORY_OLD_LAKE_WARP_MISSING")
    # The lake entrance is story-gated; exit is always available.
    def entry_page(dest,xy):
        p=event_page(warp=(mapping[dest],*xy),touch=True)
        ops=p.attrs["@list"]
        test=command(111,12,b"BlueSinnohPilot.lake_entry_allowed?")
        transfer=ops[0];transfer.attrs["@indent"]=1;transfer.attrs["@parameters"][4]=8
        ending=command(0);ending.attrs["@indent"]=1
        p.attrs["@list"]=[test,transfer,ending,command(412),command(0)]
        return p
    for lane in range(2):
        a=(10+lane,2);b=(44+lane,43)
        point(lake,(44+lane,42));point(LAKEFRONT,(10+lane,3))
        event(LAKEFRONT,"SN_LAKEFRONT_TO_LAKE_"+str(lane+1),a,entry_page(lake,(44+lane,42)))
        event(lake,"SN_LAKE_TO_LAKEFRONT_"+str(lane+1),b,
              event_page(warp=(mapping[LAKEFRONT],10+lane,3),touch=True),
              existing=old_exit[0] if lane==0 else None)
    # The profile autorun must release the interpreter even if the native
    # name screen fails. The bedroom exit retries setup before transferring;
    # neither cancellation nor a failed API call can grant completion.
    bedroom="SINNOH_PLAYER_BEDROOM"
    exits=[e for e in world(bedroom).values() if e.attrs["@name"]==b"SN_BEDROOM_TO_1F"]
    if len(exits)!=1:fail("PROFILE_BEDROOM_EXIT_MISSING")
    exit_page=exits[0].attrs["@pages"][0].attrs
    transfer=exit_page["@list"][0]
    if transfer.attrs["@code"]!=201:fail("PROFILE_BEDROOM_EXIT_NOT_WARP")
    transfer.attrs["@indent"]=1
    ending=command(0);ending.attrs["@indent"]=1
    exit_page["@list"]=[command(111,12,b"defined?(BlueSinnohPilot) && BlueSinnohPilot.respond_to?(:setup_profile) && BlueSinnohPilot.setup_profile"),transfer,ending,command(412),command(0)]

    # A one-time autorun on entering each map, with a self switch and a
    # blank second page, avoids looping and leaves action NPCs available.
    scenes=(
        ("SINNOH_PLAYER_BEDROOM","SN_PROFILE_SETUP","BlueSinnohPilot.setup_profile"),
        ("SINNOH_PLAYER_HOUSE_1F","SN_MOTHER_SCENE","BlueSinnohPilot.mother"),
        ("SINNOH_BARRY_HOUSE","SN_BARRY_SCENE","BlueSinnohPilot.barry_intro"),
        (lake,"SN_ROWAN_SCENE","BlueSinnohPilot.rowan_briefcase"),
        ("SINNOH_PROFESSOR_ROWAN_LABORATORY","SN_DEX_SCENE","BlueSinnohPilot.lab_reward"),
    )
    for sym,key,script in scenes:
        used={(e.attrs["@x"],e.attrs["@y"]) for e in world(sym).values()}
        xy=min(components[sym]-used,key=lambda p:(p[1],p[0]))
        active=event_page(script=script)
        active.attrs["@trigger"]=3
        active.attrs["@through"]=True
        active.attrs["@list"]=[command(355,script.encode("ascii")),command(123,b"A",0),command(0)]
        if key=="SN_PROFILE_SETUP":
            # A means the initial attempt ran, not profile completion.
            # The saved profile flag is the authority; stairs retry if false.
            # The inline rescue catches failures before the handler is entered
            # (e.g. a missing compiled plugin), without losing the cause.
            code=('begin; BlueSinnohPilot.setup_profile; rescue StandardError => e; '
                  'begin; File.open("sinnoh-profile-error.txt","wb"){|f| f.write("PROFILE_EVENT_DISPATCH\\n"+e.class.to_s+": "+e.message.to_s+"\\n"+Array(e.backtrace).first(12).join("\\n"))}; rescue StandardError; end; '
                  'begin; pbMessage("Sinnoh QA: erro ao iniciar perfil. Consulte sinnoh-profile-error.txt."); rescue StandardError; end; end')
            active.attrs["@list"][0]=command(355,code.encode("ascii"))
        finished=copy.deepcopy(active)
        finished.attrs["@trigger"]=0
        finished.attrs["@condition"].attrs.update({"@self_switch_valid":True,"@self_switch_ch":b"A"})
        finished.attrs["@list"]=[command(0)]
        event(sym,key,xy,active,pages=[active,finished])
    for e in world("SINNOH_PROFESSOR_ROWAN_LABORATORY").values():
        if e.attrs["@name"]==b"SN_NPC_ROWAN_POKEDEX":
            for op in e.attrs["@pages"][0].attrs["@list"]:
                if op.attrs["@code"]==355:
                    op.attrs["@parameters"][0]=b"BlueSinnohPilot.lab_reward"
    for e in world(lake).values():
        key=e.attrs["@name"]
        if not key.startswith(b"SN_BALL_"):continue
        page=e.attrs["@pages"][0].attrs
        for op in page["@list"]:
            if op.attrs["@code"]==355:
                script=op.attrs["@parameters"][0]
                if not script.startswith(b"BlueSinnohPilot.choose_starter_from_ball("):
                    fail("STORY_STARTER_HANDLER_UNEXPECTED")
                op.attrs["@parameters"][0]=script.replace(b"choose_starter_from_ball",b"choose_starter_scene")
        hidden=event_page(script="nil")
        hidden.attrs["@list"]=[command(0)]
        hidden.attrs["@through"]=True
        hidden.attrs["@condition"].attrs.update({"@self_switch_valid":True,"@self_switch_ch":b"B"})
        e.attrs["@pages"].append(hidden)
    for sym,mid in mapping.items():
        out["Data/Map%03d.rxdata"%mid]=serialize(worlds[sym],EVENT_CLASSES)
    return out,{"portal_pairs":2,"autoruns":len(scenes),"extra_event_count":8,
                "native_reviewed":False}
