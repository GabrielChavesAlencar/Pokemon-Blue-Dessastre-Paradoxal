#!/usr/bin/env python3
"""J10-A: deterministically draw five ORIGINAL Sinnoh-inspired pilot scenes.

Produces original tile artwork + map geometry, not Nintendo layouts or donor
assets. NO human authorship/rights/MapID/passability/native-QA claims.
Only --build writes, exclusively to a new ignored .blue-work directory.
The J11 independent human review must precede any J09 intake/promotion.
"""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import xml.sax.saxutils as xml
import zlib

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts/regions")]
from author_sinnoh_playable_j10 import build_rxdata, parse_png
from audit_sinnoh_playable_j09 import audit_map, authored_five, source_catalog

OUTPUT = "sinnoh-j10a-original"
SYMBOLS = (
    "SINNOH_PLAYER_BEDROOM",
    "SINNOH_PLAYER_HOUSE_1F",
    "SINNOH_BARRY_HOUSE",
    "SINNOH_LAKE_VERITY",
    "SINNOH_PROFESSOR_ROWAN_LABORATORY",
)
# Only in this tool's standalone generated tileset. NOT IDs in a real game.
FLOOR, FLOOR_ALT, WALL, DOOR, RUG, SHELF, BED, DESK = range(384, 392)
CHAIR, PC, STAIR, WINDOW, TABLE, COUNTER, MACHINE, PLANT = range(392, 400)
GRASS, PATH, WATER, SHORE, TREE, FLOWERS, ROCK, BRIDGE = range(400, 408)
BOOK, SOFA, SINK, COMPUTER, PILLOW, LAMP, LAB_BENCH, FENCE = range(408, 416)
TILE_NAMES = (
    "floor", "floor_alt", "wall", "door", "rug", "shelf", "bed", "desk",
    "chair", "pc", "stairs", "window", "table", "counter", "machine", "plant",
    "grass", "path", "water", "shore", "tree", "flowers", "rock", "bridge",
    "book", "sofa", "sink", "computer", "pillow", "lamp", "lab_bench", "fence",
)
PALETTE = [
    "#bcae92", "#cbbba0", "#59647a", "#aa7959", "#aa6d69", "#7c5b46", "#537ea8", "#8b654f",
    "#9b7859", "#b2bfc0", "#c3a875", "#75a8ba", "#9b6d55", "#c4bba6", "#869fbb", "#387a61",
    "#6c9e69", "#d5bf8b", "#4a90bc", "#9caa83", "#305e43", "#e6c966", "#82877b", "#9b7256",
    "#c9ac72", "#8a94a4", "#a4bac7", "#729bb4", "#dce4ed", "#eccd82", "#668591", "#647660",
]
BLOCKS = {WALL, SHELF, BED, DESK, CHAIR, PC, TABLE, COUNTER, MACHINE, PLANT,
          TREE, ROCK, BOOK, SOFA, SINK, COMPUTER, PILLOW, LAB_BENCH, FENCE}
SIZES = {
    SYMBOLS[0]: (20, 15),
    SYMBOLS[1]: (25, 19),
    SYMBOLS[2]: (23, 18),
    SYMBOLS[3]: (38, 27),
    SYMBOLS[4]: (29, 21),
}

def fail(reason):
    raise ValueError("SINNOH_J10A_BLOCKED:" + reason)

def checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def base_map(symbol):
    w, h = SIZES[symbol]
    return {"symbol": symbol, "width": w, "height": h,
            "layers": [[0] * (w * h) for _ in range(3)],
            "access": [], "landmarks": [], "kind": ""}

def at(m, z, x, y, tile):
    if not (0 <= z < 3 and 0 <= x < m["width"] and 0 <= y < m["height"]):
        fail("DRAW_OUTSIDE_MAP")
    m["layers"][z][y*m["width"]+x] = tile

def fill(m, z, x1, y1, x2, y2, tile):
    for y in range(y1, y2+1):
        for x in range(x1, x2+1):
            at(m, z, x, y, tile)

def box(m, x1, y1, x2, y2, tile):
    for x in range(x1, x2+1):
        at(m, 1, x, y1, tile)
        at(m, 1, x, y2, tile)
    for y in range(y1, y2+1):
        at(m, 1, x1, y, tile)
        at(m, 1, x2, y, tile)

def interior(symbol):
    m = base_map(symbol)
    w, h = m["width"], m["height"]
    m["kind"] = "ORIGINAL_INTERIOR"
    for y in range(h):
        for x in range(w):
            at(m, 0, x, y, FLOOR_ALT if (x//2+y//2)%2 else FLOOR)
    box(m, 0, 0, w-1, h-1, WALL)
    fill(m, 1, 0, 1, w-1, 1, WALL)
    # Do NOT infer actual game portals; these are proposed door approach tiles.
    at(m, 1, w//2, h-1, DOOR)
    at(m, 1, w//2, h-2, 0)
    for x in (4, w-5):
        at(m, 2, x, 1, WINDOW)
    m["access"] = [[w//2, h-2]]
    return m

def decorate_bedroom():
    m = interior(SYMBOLS[0]); w, h = m["width"], m["height"]
    fill(m, 0, 8, 6, 12, 9, RUG)
    fill(m, 1, 3, 3, 5, 5, BED)
    at(m, 2, 4, 3, PILLOW)
    fill(m, 1, 14, 4, 16, 4, DESK)
    at(m, 2, 15, 4, COMPUTER)
    at(m, 1, 15, 5, CHAIR)
    at(m, 1, 3, 9, SHELF)
    at(m, 2, 3, 9, BOOK)
    at(m, 1, 17, 9, PLANT)
    at(m, 1, 5, 11, STAIR)
    for x in (7, 8, 12, 13):at(m, 2, x, 1, LAMP)
    m["landmarks"] = [[10, 8], [6, 11], [14, 7]]
    return m

def decorate_house():
    m = interior(SYMBOLS[1]); w, h = m["width"], m["height"]
    fill(m, 0, 4, 7, 10, 12, RUG)
    fill(m, 1, 5, 5, 8, 5, SOFA)
    at(m, 1, 7, 8, TABLE)
    at(m, 2, 7, 8, BOOK)
    fill(m, 1, 17, 3, 21, 3, COUNTER)
    at(m, 1, 20, 4, SINK)
    at(m, 2, 18, 3, LAMP)
    at(m, 1, 19, 8, TABLE)
    at(m, 1, 17, 9, CHAIR)
    at(m, 1, 21, 9, CHAIR)
    at(m, 1, 4, 15, STAIR)
    at(m, 1, 3, 4, PLANT)
    m["landmarks"] = [[7, 11], [15, 11], [5, 14], [19, 11]]
    return m

def decorate_barry_house():
    m = interior(SYMBOLS[2]); w, h=m["width"],m["height"]
    fill(m, 0, 5, 9, 12, 12, RUG)
    at(m, 1, 4, 4, STAIR)
    fill(m, 1, 7, 5, 10, 5, SOFA)
    at(m, 1, 8, 9, TABLE)
    at(m, 1, 15, 5, DESK)
    at(m, 2, 15, 5, PC)
    at(m, 1, 16, 6, CHAIR)
    at(m, 1, 18, 11, SHELF)
    at(m, 2, 18, 11, BOOK)
    at(m, 1, 3, 13, PLANT)
    at(m, 2, 13, 1, LAMP)
    m["landmarks"] = [[11, 11], [5, 5], [13, 8]]
    return m

def decorate_lake():
    m=base_map(SYMBOLS[3]);w,h=m["width"],m["height"]
    m["kind"]="ORIGINAL_FOREST_LAKE"
    for y in range(h):
        for x in range(w):
            at(m,0,x,y,GRASS)
            if (x+y*3)%11==0:at(m,2,x,y,FLOWERS)
    # Stylized original pond (not a traced or copied official route).
    for y in range(5,20):
        for x in range(13,34):
            q=((x-23)/10)**2+((y-12)/7)**2
            if q<=0.76:at(m,0,x,y,WATER)
            elif q<=1.03:at(m,0,x,y,SHORE)
    # Public-facing walkway from the south edge, then west around the lake.
    for y in range(17,h):
        for x in range(6,10):at(m,0,x,y,PATH);at(m,2,x,y,0)
    for y in range(17,22):
        for x in range(8,14):at(m,0,x,y,PATH);at(m,2,x,y,0)
    for x in range(8,15):
        at(m,0,x,20,PATH);at(m,2,x,20,0)
    # Deterministic forest boundary; gap at southwestern access.
    for y in range(h):
        for x in range(w):
            if x in (0,1,w-2,w-1) or y in (0,1,h-2,h-1):
                if not (6<=x<=9 and y>=h-2):
                    at(m,1,x,y,TREE);at(m,2,x,y,0)
    for x,y in ((3,5),(5,8),(4,13),(8,5),(10,10),(11,16),
                (32,21),(35,16),(34,3),(26,23),(2,19)):
        at(m,1,x,y,TREE)
    for x,y in ((10,8),(12,21),(30,23),(5,22)):
        at(m,1,x,y,ROCK)
    at(m,1,13,20,BRIDGE)
    m["access"]=[[8,h-2]]
    m["landmarks"]=[[8,20],[12,20],[15,20],[8,17]]
    return m

def decorate_lab():
    m=interior(SYMBOLS[4]);w,h=m["width"],m["height"]
    fill(m,0,12,4,16,16,RUG)
    fill(m,1,4,5,9,5,LAB_BENCH)
    fill(m,1,19,5,24,5,LAB_BENCH)
    for x in (5,7,9,20,22,24):
        at(m,2,x,5,MACHINE)
    fill(m,1,5,11,9,11,LAB_BENCH)
    fill(m,1,19,11,23,11,LAB_BENCH)
    for x in (6,8,20,22):
        at(m,2,x,11,COMPUTER)
    fill(m,1,12,3,16,3,DESK)
    at(m,2,14,3,COMPUTER)
    at(m,1,14,5,CHAIR)
    for x in (4,24):at(m,1,x,16,PLANT)
    for x in (10,18):at(m,2,x,1,LAMP)
    m["landmarks"]=[[14,7],[14,13],[10,10],[18,10]]
    return m

def scenes():
    result=[decorate_bedroom(),decorate_house(),decorate_barry_house(),
            decorate_lake(),decorate_lab()]
    if tuple(x["symbol"] for x in result)!=SYMBOLS:fail("SCENE_SYMBOL_ORDER")
    for scene in result:validate_scene(scene)
    return result

def walkable(scene, x, y):
    w,h=scene["width"],scene["height"]
    if not (0<=x<w and 0<=y<h):return False
    idx=y*w+x
    bottom,upper=scene["layers"][0][idx],scene["layers"][1][idx]
    return bottom!=WATER and bottom!=SHORE and upper not in BLOCKS

def validate_scene(scene):
    w,h=scene["width"],scene["height"]
    if not (12<=w<=120 and 10<=h<=120 and w*h<=14400):fail("DIMENSIONS")
    layers=scene["layers"]
    if len(layers)!=3 or any(len(z)!=w*h for z in layers):fail("THREE_FULL_LAYERS")
    if any(type(t)!=int or not 0<=t<=415 for z in layers for t in z):fail("TILE_RANGE")
    distinct={t for z in layers for t in z if t}
    if len(distinct)<8 or sum(t>0 for t in layers[1])<8:
        fail("TRIVIAL_OR_PLACEHOLDER_LAYOUT")
    if sum(t!=0 for t in layers[0])!=w*h:fail("BASE_LAYER_INCOMPLETE")
    for x,y in scene["access"]+scene["landmarks"]:
        if not walkable(scene,x,y):fail("ACCESS_OR_LANDMARK_BLOCKED")
    start=tuple(scene["access"][0]);seen={start};queue=deque([start])
    while queue:
        x,y=queue.popleft()
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
            nxt=(x+dx,y+dy)
            if nxt not in seen and walkable(scene,*nxt):
                seen.add(nxt);queue.append(nxt)
    if not all(tuple(p) in seen for p in scene["landmarks"]):
        fail("POTENTIAL_WALKABILITY_DISCONNECTED")
    scene["walkable_reachable"]=len(seen)
    scene["potential_terrain_walkability_only"]=True
    scene["actual_rmxp_tileset_passability_checked"]=False
    return scene

def rgba_artwork():
    """Original 8x8 tile palette with hand-coded simple geometries, no imports."""
    size=256
    raw=bytearray(size*size*4)
    def rgb(h):
        return tuple(bytes.fromhex(h.lstrip("#")))+(255,)
    def rect(x,y,w,h,c):
        color=rgb(c)
        for yy in range(max(0,y),min(size,y+h)):
            for xx in range(max(0,x),min(size,x+w)):
                raw[(yy*size+xx)*4:(yy*size+xx)*4+4]=bytes(color)
    for i,main in enumerate(PALETTE):
        x,y=i%8*32,i//8*32
        rect(x,y,32,32,main)
        dark="#24394b"; light="#f3e4bb"
        if i in (2,5,7,12,13,14,26,30,31):
            rect(x+2,y+3,28,3,dark);rect(x+2,y+25,28,3,dark)
        if i in (0,1,4,16,17):
            for px in (4,14,25):rect(x+px,y+((i+px)*7)%24,3,3,light)
        if i in (3,10,23):
            rect(x+7,y+2,18,28,"#f5ddac")
            rect(x+12,y+13,4,4,dark)
        if i in (6,25,28):
            rect(x+4,y+4,24,24,"#dce2d8")
            rect(x+5,y+23,22,4,dark)
        if i in (8,9,27):
            rect(x+8,y+6,16,16,dark);rect(x+11,y+8,10,9,"#95cede")
        if i in (11,18):
            for k in range(3):rect(x+3+k*9,y+8+k%2*5,7,2,"#c1e6f5")
        if i in (15,20):
            rect(x+13,y+17,6,13,"#654c36")
            for xx,yy in ((3,5),(13,1),(18,8),(7,12)):
                rect(x+xx,y+yy,12,13,"#44774f")
        if i in (21,24,29):
            for px in (6,16,23):rect(x+px,y+7+px%9,3,4,"#f8dca3")
        if i==19:
            rect(x+3,y+3,26,4,"#d6cfa0");rect(x+3,y+25,26,4,"#dde2ba")
        if i==22:
            rect(x+5,y+15,21,11,"#4b5b68");rect(x+9,y+11,15,6,"#acb8b5")
    return bytes(raw)

def png_bytes():
    img=rgba_artwork()
    scan=b"".join(b"\x00"+img[y*256*4:(y+1)*256*4] for y in range(256))
    def chunk(name,data):
        blob=name+data
        return struct.pack(">I",len(data))+blob+struct.pack(">I",zlib.crc32(blob)&0xffffffff)
    out=(b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",256,256,8,6,0,0,0))
         +chunk(b"IDAT",zlib.compress(scan,9))+chunk(b"IEND",b""))
    if parse_png(out)!=(256,256):fail("ORIGINAL_TILESET_PNG_INVALID")
    return out

def svg_preview(scene):
    w,h=scene["width"],scene["height"]
    rectangles=[]
    for y in range(h):
        for x in range(w):
            idx=y*w+x
            tiles=[scene["layers"][z][idx] for z in range(3)]
            visible=next((v for v in reversed(tiles) if v),0)
            color=PALETTE[visible-384] if visible>=384 else "#0e1929"
            rectangles.append(f'<rect x="{x*14}" y="{y*14}" width="14" height="14" fill="{color}"/>')
    for ax,ay in scene["access"]:
        rectangles.append(f'<circle cx="{ax*14+7}" cy="{ay*14+7}" r="5" fill="#ffffff" stroke="#172639" stroke-width="2"/>')
    for lx,ly in scene["landmarks"]:
        rectangles.append(f'<circle cx="{lx*14+7}" cy="{ly*14+7}" r="3" fill="#eecb41" stroke="#172639"/>')
    title=xml.escape(scene["symbol"])
    return ('<svg xmlns="http://www.w3.org/2000/svg" width="'+str(w*14)+'" height="'+str(h*14+32)+
            '" viewBox="0 0 '+str(w*14)+' '+str(h*14+32)+'" role="img" aria-label="'+title+'">\n'
            '<rect width="100%" height="100%" fill="#172639"/><text x="8" y="21" '
            'font-family="sans-serif" font-size="13" fill="white">'+title+'</text>'
            '<g transform="translate(0 32)">'+''.join(rectangles)+'</g></svg>\n')

def generate():
    png=png_bytes()
    output={}
    info={}
    for sc in scenes():
        symbol=sc["symbol"]
        draft={"width":sc["width"],"height":sc["height"],"tileset_id":1,"layers":sc["layers"]}
        raw=build_rxdata(draft,png)
        checked=audit_map(raw)
        if checked["foreign_events_not_imported"]!=0 or checked["width"]!=sc["width"]:
            fail("J09_MARSHAL_COMPATIBILITY")
        output[symbol+".rxdata"]=raw
        output["previews/"+symbol+".svg"]=svg_preview(sc).encode("utf-8")
        info[symbol]={"width":sc["width"],"height":sc["height"],
            "three_layers":True,"source_kind":"PROGRAMMATIC_ORIGINAL_NOT_HUMAN_ATTESTED",
            "rxdata_sha256":checksum(raw),"nonzero_tiles":checked["nonzero_tiles"],
            "reachable_potential_walkable_cells":sc["walkable_reachable"],
            "entry_candidates_not_native_portals":sc["access"],
            "landmarks_not_native_event_coordinates":sc["landmarks"],
            "r07_destination_mapid":None,"r08_independent_asset_review":False,
            "j11_real_tileset_passability_verified":False}
    if len({v["rxdata_sha256"] for v in info.values()})!=5:fail("DUPLICATE_SCENES")
    output["OriginalJ10A.png"]=png
    report={"schema":1,"region":"SINNOH","stage":"J10-A",
        "status":"FIVE_ORIGINAL_PROGRAMMATIC_GEOMETRIES_GENERATED_UNREVIEWED",
        "tileset_sha256":checksum(png),
        "tileset_description":"New 32x32 procedural tile palette, stdlib only; no donor images",
        "map_count":5,"map_sources":info,"generated_by":"Python procedural design, not human map drawings",
        "actual_human_authorship_attested":False,
        "r07_approved":False,"r08_approved":False,"r09_native_verified":False,
        "real_game_tileset_compatibility_verified":False,
        "native_maps_installed":0,"native_windows_cases_executed":0,
        "native_android_cases_executed":0,"can_install":False,"can_publish_game":False,
        "next":"J11 requires real human geometry review, permission approval, MapInfos and tileset passability",
        "output_checksums":{name:checksum(raw) for name,raw in sorted(output.items())}}
    output["manifest.json"]=(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n").encode()
    return output,report

def build_private(root:Path):
    root=Path(root).absolute()
    work=root/".blue-work"
    target=work/OUTPUT
    if not root.is_dir() or root.is_symlink() or work.is_symlink() or target.exists() or target.is_symlink():
        fail("OUTPUT_MUST_BE_NEW_PRIVATE_DIRECTORY")
    if not (root/"scripts/regions/author_sinnoh_playable_j10.py").is_file():
        fail("REPOSITORY_ROOT_NOT_FOUND")
    files,report=generate()
    work.mkdir(exist_ok=True)
    if work.is_symlink():fail("PRIVATE_SYMLINK")
    temp=Path(tempfile.mkdtemp(dir=work,prefix=".j10a-atomic-"))
    try:
        for name,content in files.items():
            path=temp/name
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("xb") as handle:handle.write(content)
        if any(checksum((temp/name).read_bytes())!=checksum(raw) for name,raw in files.items()):
            fail("ATOMIC_OUTPUT_SHA_CHANGED")
        if target.exists() or target.is_symlink():fail("OUTPUT_CONCURRENTLY_CREATED")
        temp.rename(target)
    finally:
        if temp.exists():shutil.rmtree(temp)
    return {**report,"private_output":str(target),"private_generated_rxdata_count":5}

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project",type=Path,default=ROOT)
    parser.add_argument("--build",action="store_true",
                        help="Write to NEW .blue-work/sinnoh-j10a-original only (never install)")
    args=parser.parse_args(argv)
    try:
        _,report=generate() if not args.build else (None,build_private(args.project))
    except (ValueError,OSError,KeyError,TypeError) as err:
        print("J10A_BLOCKED:"+str(err),file=sys.stderr)
        return 2
    print(json.dumps(report,indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
