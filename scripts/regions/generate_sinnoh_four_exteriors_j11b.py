#!/usr/bin/env python3
"""J11-B: four NEW programmatic exterior maps + nine original geometry candidates.

Author-created Python geometry/artwork, NOT traced Pokemon layouts or donor ZIP.
Never installs maps, reuses J10-A's five *originals*, not B00's 4 historical
references. Emits a nine-map private *design bundle* with two distinct PNGs.
No human review, rights grant, native MapIDs, actual RMXP Tilesets or QA.
"""
from __future__ import annotations
import argparse
from collections import deque
import hashlib
import json
import math
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import xml.sax.saxutils as xml
import zlib

ROOT=Path(__file__).resolve().parents[2]
for p in (ROOT,ROOT/"scripts/regions"):
    if str(p) not in sys.path:sys.path.insert(0,str(p))
import generate_sinnoh_original_j10a as five
import audit_sinnoh_playable_j11 as j11
from audit_sinnoh_playable_j09 import audit_map
from audit_sinnoh_twinleaf_events import MAPS
from author_sinnoh_playable_j10 import build_rxdata
from audit_sinnoh_rxdata import attrs,read_marshal
from server.ruby_marshal import RubyData

STAGE="J11-B"
OUTPUT="sinnoh-j11b-nine-original-designs"
EXTERIORS={
    "SINNOH_TWINLEAF_TOWN":(44,34),
    "SINNOH_ROUTE_201":(50,24),
    "SINNOH_SANDGEM_TOWN":(46,34),
    "SINNOH_ROUTE_202":(36,46),
}
# IDs remain 384..415, local to the *new standalone exterior tileset*.
G,P,W,S,T,F,R,B=five.GRASS,five.PATH,five.WATER,five.SHORE,five.TREE,five.FLOWERS,five.ROCK,five.BRIDGE
WALL,ROOF,DOOR,PLAZA,FENCE=five.WALL,five.BED,five.DOOR,five.FLOOR_ALT,five.FENCE
BLOCKED=frozenset(five.BLOCKS)|{W,S}
# Entirely fresh hand-coded exterior color scheme. No images downloaded.
COLORS=[
"#d4c49b","#b9a67c","#6b797e","#bb8058","#b88064","#9c7958","#b7846f","#9f7655",
"#7497ab","#8e775d","#d2caa3","#acd5cc","#b79b77","#c9b899","#83a7bd","#4c8067",
"#66a768","#d6c68d","#469ecb","#a6b9a1","#32784c","#f4d15c","#7d8980","#ac8864",
"#d8b584","#849caa","#a9c6bd","#76b9d0","#e7c4a4","#f1d981","#738b93","#708662",
]

def fail(message):
    raise ValueError("SINNOH_J11B_BLOCKED:"+message)

def sha(data:bytes)->str:
    return hashlib.sha256(data).hexdigest()

def scene(symbol):
    if symbol not in EXTERIORS:fail("UNKNOWN_FOUR_EXTERIOR_SYMBOL")
    w,h=EXTERIORS[symbol]
    m={"symbol":symbol,"width":w,"height":h,
       "layers":[[0]*(w*h) for _ in range(3)],
       "access":[],"landmarks":[],"edge_candidates":[],
       "kind":"ORIGINAL_PROGRAMMATIC_EXTERIOR_NOT_HUMAN_REVIEWED"}
    for y in range(h):
        for x in range(w):
            five.at(m,0,x,y,G)
            if (x*13+y*17)%23==0:five.at(m,2,x,y,F)
    return m

def draw(m,z,x,y,t):
    five.at(m,z,x,y,t)

def area(m,z,x1,y1,x2,y2,t):
    five.fill(m,z,x1,y1,x2,y2,t)

def path_tile(m,x,y,t=P):
    if 0<=x<m["width"] and 0<=y<m["height"]:
        draw(m,0,x,y,t)
        draw(m,1,x,y,0)
        draw(m,2,x,y,0)

def path_rect(m,x1,y1,x2,y2,t=P):
    for y in range(y1,y2+1):
        for x in range(x1,x2+1):path_tile(m,x,y,t)

def path_h(m,y,x1,x2,r=1):
    path_rect(m,x1,y-r,x2,y+r)

def path_v(m,x,y1,y2,r=1):
    path_rect(m,x-r,y1,x+r,y2)

def frame(m):
    w,h=m["width"],m["height"]
    for y in range(h):
        for x in range(w):
            if x<2 or y<2 or x>w-3 or y>h-3:
                if m["layers"][0][y*w+x]!=P:
                    draw(m,1,x,y,T)
                    draw(m,2,x,y,0)

def house(m,x,y,w,h,style=0):
    if w<5 or h<5:fail("HOUSE_TOO_SMALL")
    # Roof silhouette is a bespoke arrangement, not a Nintendo building.
    area(m,1,x,y,x+w-1,y+h-2,WALL)
    area(m,2,x+1,y+1,x+w-2,y+h-3,ROOF if not style else five.COUNTER)
    for gx in range(x+2,x+w-2,3):
        draw(m,2,gx,y+1,five.LAMP)
    cx=x+w//2
    draw(m,1,cx,y+h-2,DOOR)
    draw(m,2,cx,y+h-2,0)
    return (cx,y+h-1)  # APPROACH candidate, NOT native warp/event.

def town_twinleaf():
    m=scene("SINNOH_TWINLEAF_TOWN")
    # Original four-way garden neighborhood with two off-axis courtyards.
    path_v(m,21,0,33,2)
    path_h(m,18,0,43,2)
    path_rect(m,16,13,26,23,PLAZA)
    path_h(m,18,0,43,2);path_v(m,21,0,33,2)
    entries=[]
    for x,y,w,h,style in ((5,5,10,9,0),(29,5,10,9,1),
                          (6,24,9,7,1),(30,24,9,7,0)):
        entries.append(house(m,x,y,w,h,style))
    for i,(x,y) in enumerate(entries):
        if i<2:path_v(m,x,y,16,1)
        else:path_v(m,x,21,y,1)
    path_h(m,17,10,34,1)
    path_h(m,21,10,34,1)
    for x,y in ((4,18),(38,18),(13,21),(29,21),(11,4),(38,4),
                (4,28),(40,29)):
        draw(m,1,x,y,five.PLANT)
    draw(m,1,24,23,five.ROCK)
    m["access"]=[[21,32]]
    m["edge_candidates"]=[[21,1],[1,18],[42,18]]
    m["landmarks"]=[[21,18],[21,8],[10,17],[34,17],[21,27]]
    frame(m)
    return m

def trail_y(x,w,base,amp=3):
    return int(round(base+amp*math.sin(x*.15)+2*math.sin(x*.31)))

def route_201():
    m=scene("SINNOH_ROUTE_201")
    w,h=m["width"],m["height"]
    for x in range(w):
        y=trail_y(x,w,12,2)
        for yy in range(y-2,y+3):path_tile(m,x,yy)
    # Independent grove with a northern pond.
    for y in range(3,7):
        for x in range(13,21):
            q=((x-16.5)/4.5)**2+((y-4.5)/2.8)**2
            if q<.6:draw(m,0,x,y,W)
            elif q<1.1:draw(m,0,x,y,S)
    for y in range(3,h-3):
        for x in range(3,w-3):
            if (x*7+y*11)%41==0 and m["layers"][0][y*w+x]==G:
                draw(m,1,x,y,T)
            elif (x*19+y*13)%83==0 and m["layers"][0][y*w+x]==G:
                draw(m,1,x,y,R)
    # A separate 8th authored tile type avoids trivial repeated route geometry.
    draw(m,1,25,trail_y(25,w,12,2),B)
    m["access"]=[[2,trail_y(2,w,12,2)]]
    m["edge_candidates"]=[[w-3,trail_y(w-3,w,12,2)]]
    m["landmarks"]=[[12,trail_y(12,w,12,2)],[26,trail_y(26,w,12,2)],
                    [39,trail_y(39,w,12,2)]]
    frame(m)
    return m

def town_sandgem():
    m=scene("SINNOH_SANDGEM_TOWN")
    path_v(m,23,0,33,2);path_h(m,21,0,45,2)
    path_rect(m,17,13,29,24,PLAZA)
    # Repaint primary movement corridors through the new public square.
    path_v(m,23,0,33,2);path_h(m,21,0,45,2)
    for x,y,w,h,style in ((4,5,11,10,1),(32,5,11,10,0),
                          (5,26,10,6,0),(33,26,9,6,1)):
        door=house(m,x,y,w,h,style)
        if y<20:path_v(m,door[0],door[1],19,1)
        else:path_v(m,door[0],23,door[1],1)
    path_h(m,19,10,35,1)
    for x,y in ((18,14),(28,14),(18,25),(28,25)):
        draw(m,1,x,y,five.PLANT)
    # A stepped obelisk, unlike any official Sinnoh town layout.
    draw(m,1,18,16,R);draw(m,2,18,16,five.LAMP)
    m["access"]=[[23,32]]
    m["edge_candidates"]=[[23,1],[1,21],[44,21]]
    m["landmarks"]=[[23,19],[12,19],[36,19],[23,29]]
    frame(m)
    return m

def trail_x(y,h):
    return int(round(18+3*math.sin(y*.19)+2*math.sin(y*.37)))

def route_202():
    m=scene("SINNOH_ROUTE_202")
    w,h=m["width"],m["height"]
    for y in range(h):
        x=trail_x(y,h)
        for xx in range(x-2,x+3):path_tile(m,xx,y)
    for y in range(17,26):
        for x in range(4,12):
            q=((x-7.5)/4.5)**2+((y-21)/5)**2
            if q<.6:draw(m,0,x,y,W)
            elif q<1.05:draw(m,0,x,y,S)
    for y in range(3,h-3):
        for x in range(3,w-3):
            if (x*11+y*7)%37==0 and m["layers"][0][y*w+x]==G:
                draw(m,1,x,y,T)
            elif (x*7+y*5)%71==0 and m["layers"][0][y*w+x]==G:
                draw(m,1,x,y,R)
    for y in (10,29,37):
        x=trail_x(y,h)
        for xx in range(x+4,min(w-3,x+9)):draw(m,1,xx,y,FENCE)
    m["access"]=[[trail_x(44,h),44]]
    m["edge_candidates"]=[[trail_x(1,h),1]]
    m["landmarks"]=[[trail_x(8,h),8],[trail_x(20,h),20],
                    [trail_x(32,h),32]]
    frame(m)
    return m

def reachable(m):
    w,h=m["width"],m["height"]
    def safe(x,y):
        if not(0<=x<w and 0<=y<h):return False
        index=y*w+x
        return m["layers"][0][index] not in (W,S) and m["layers"][1][index] not in BLOCKED
    candidates=m["access"]+m["edge_candidates"]+m["landmarks"]
    if any(len(point)!=2 or any(type(v)!=int for v in point) or not safe(*point) for point in candidates):
        fail("EXTERIOR_CANDIDATE_BLOCKED")
    start=tuple(m["access"][0]);q=deque([start]);seen={start}
    while q:
        x,y=q.popleft()
        for dx,dy in ((0,1),(0,-1),(1,0),(-1,0)):
            nxt=(x+dx,y+dy)
            if nxt not in seen and safe(*nxt):
                seen.add(nxt);q.append(nxt)
    if len(seen)<w*h//8 or any(tuple(pt) not in seen for pt in candidates):
        fail("EXTERIOR_MAIN_PATH_DISCONNECTED")
    return len(seen)

def scenes():
    layouts=(town_twinleaf(),route_201(),town_sandgem(),route_202())
    if {s["symbol"] for s in layouts}!=set(EXTERIORS):fail("EXTERIOR_COUNT")
    for s in layouts:
        five.validate_scene(s)
        s["reachable_potential"]=reachable(s)
    return layouts

def original_pixels():
    raw=bytearray(256*256*4)
    def col(h):return bytes.fromhex(h.strip("#"))+b"\xff"
    def rect(x,y,w,h,c):
        v=col(c)
        for yy in range(max(0,y),min(256,y+h)):
            for xx in range(max(0,x),min(256,x+w)):
                off=(yy*256+xx)*4;raw[off:off+4]=v
    for i,main in enumerate(COLORS):
        x,y=(i%8)*32,(i//8)*32
        rect(x,y,32,32,main)
        for dx in range(3,30,7):
            oy=(i*11+dx*5)%26
            rect(x+dx,y+oy,2+((i+dx)%3),2,"#f6e7c6" if i%3==0 else "#294e53")
        if i in (16,17,18,19,20,21,22,23):
            # Landscape tile textures: leaves, water lines, stones, bridges.
            for yy in (7,15,23):
                rect(x+4,y+yy,23-(i%4)*2,2,"#a8d4b2" if i%2==0 else "#e3ba70")
        if i in (2,3,6,7,13,14,30,31):
            rect(x+3,y+4,26,4,"#314d5d")
            rect(x+3,y+24,26,3,"#ebd2a4")
        if i==20:
            rect(x+8,y+5,16,20,"#2b673b")
            rect(x+13,y+22,5,7,"#5f4c39")
        if i==18:
            for yy in (5,13,21):rect(x+4,y+yy,24,2,"#a4d9f0")
    return bytes(raw)

def original_png():
    image=original_pixels()
    scan=b"".join(b"\x00"+image[i*256*4:(i+1)*256*4] for i in range(256))
    def chunk(name,content):
        part=name+content
        return struct.pack(">I",len(content))+part+struct.pack(">I",zlib.crc32(part)&0xffffffff)
    png=b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",256,256,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(scan,9))+chunk(b"IEND",b"")
    if j11.verify_png(png)["authored_tile_count"]!=32:fail("EXTERIOR_ART_NOT_VALID")
    return png

def svg_preview(m):
    w,h=m["width"],m["height"]
    result=[]
    for y in range(h):
        for x in range(w):
            idx=y*w+x
            t=next((m["layers"][z][idx] for z in (2,1,0) if m["layers"][z][idx]),0)
            color=COLORS[t-384] if t>=384 else "#152d34"
            result.append(f'<rect x="{x*12}" y="{y*12}" width="12" height="12" fill="{color}"/>')
    for x,y in m["access"]:
        result.append(f'<circle cx="{x*12+6}" cy="{y*12+6}" r="5" fill="#ffffff"/>')
    for x,y in m["edge_candidates"]:
        result.append(f'<circle cx="{x*12+6}" cy="{y*12+6}" r="4" fill="#5de0d7"/>')
    for x,y in m["landmarks"]:
        result.append(f'<circle cx="{x*12+6}" cy="{y*12+6}" r="3" fill="#ffe8a2"/>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w*12}" height="{h*12+30}" '
            f'viewBox="0 0 {w*12} {h*12+30}" role="img" '
            f'aria-label="{xml.escape(m["symbol"])}">\n'
            f'<rect width="100%" height="100%" fill="#152d34"/>'
            f'<text x="6" y="20" fill="white" font-size="12">{xml.escape(m["symbol"])}</text>'
            '<g transform="translate(0 30)">'+''.join(result)+'</g></svg>\n')

def proposed_tilesets(original_pngs):
    # A proposal, NOT RPG::Tileset and NOT an authoritative passage table.
    rows={}
    for name,png in original_pngs.items():
        proposed=[]
        for i,label in enumerate(five.TILE_NAMES):
            tile_id=384+i
            blocked=tile_id in BLOCKED
            proposed.append({"tile_id":tile_id,"label":label,
                             "hypothetical_passages":15 if blocked else 0,
                             "hypothetical_priority":1 if blocked else 0,
                             "verified_in_engine":False})
        rows[name]={"png_sha256":sha(png),"pixels":[256,256],
                    "tile_size":32,"candidate_tileset_id":None,
                    "existing_native_tile_id":None,
                    "human_reviewed":False,"license_independently_approved":False,
                    "native_passages_reviewed":False,
                    "native_priorities_reviewed":False,
                    "proposed_tiles":proposed}
    if len(rows)!=2:fail("TWO_DISTINCT_PNGS_REQUIRED")
    return {"mode":"PROPOSED_ONLY_NOT_RPG_TILESET","native_tilesets_rxdata_generated":False,
            "two_images_require_two_distinct_native_tileset_assignments":True,
            "can_install":False,"tilesets":rows}

def audit_nine(orig_files,orig_manifest,ex_scenes,ex_png,ex_files):
    five_audit=j11.original_audit(ROOT,payload=(orig_files,orig_manifest))
    if five_audit["count"]!=5:fail("J11_FIVE_BASELINE_NOT_VERIFIED")
    original_hashes={symbol:five_audit["maps"][symbol]["rxdata"]["sha256"]
                     for symbol in five.SYMBOLS}
    info={}
    for sc in ex_scenes:
        symbol=sc["symbol"]
        raw=ex_files[symbol+".rxdata"]
        result=audit_map(raw)
        if (result["width"],result["height"])!=(sc["width"],sc["height"]):
            fail("NEW_EXTERIOR_GEOMETRY_OR_DIMENSIONS")
        table=attrs(read_marshal(raw,"J11B_EXTERIOR")).get("@data")
        if not isinstance(table,RubyData) or table.name!="Table" or len(table.data)!=20+sc["width"]*sc["height"]*6:
            fail("NATIVE_RMXP_THREE_LAYERS")
        count=sc["width"]*sc["height"]
        actual=struct.unpack_from("<"+str(3*count)+"H",table.data,20)
        if any(list(actual[z*count:(z+1)*count])!=sc["layers"][z] for z in range(3)):
            fail("RXDATA_NOT_SAME_AS_DRAWN_SOURCE")
        if result["foreign_events_not_imported"]!=0:fail("DONOR_EVENTS_NOT_ALLOWED")
        if ex_files["previews/"+symbol+".svg"]!=svg_preview(sc).encode():fail("EXTERIOR_SVG_CHANGED")
        root=j11.ET.fromstring(ex_files["previews/"+symbol+".svg"])
        if root.tag!="{http://www.w3.org/2000/svg}svg" or len(list(root.iter()))<count:
            fail("EXTERIOR_SVG_CELLS_INVALID")
        info[symbol]={"sha256":sha(raw),"width":sc["width"],"height":sc["height"],
                      "three_layers":True,"source":"J11B_PROGRAMMATIC_ORIGINAL",
                      "potential_reachable_cells":sc["reachable_potential"],
                      "edge_candidates_not_warps":sc["edge_candidates"],
                      "native_tileset_id":None,"rights_approved":False}
    all_hash={**original_hashes,**{k:v["sha256"] for k,v in info.items()}}
    if len(all_hash)!=9 or set(all_hash)!=set(MAPS) or len(set(all_hash.values()))!=9:
        fail("NINE_DISTINCT_ORIGINAL_MAPS_REQUIRED")
    catalog=j11.source_catalog(ROOT)
    if [row["symbol"] for row in catalog["maps"]]!=list(MAPS):fail("J02_SYMBOL_ORDER_CHANGED")
    contract=j11.verify_contracts(ROOT)
    return {"five":five_audit["maps"],"four":info,"hashes":all_hash,"events":contract}

def generate():
    j10_files,j10_manifest=five.generate()
    ex_scenes=scenes()
    exterior=original_png()
    files={name:raw for name,raw in j10_files.items() if name!="manifest.json"}
    files["ExteriorJ11B.png"]=exterior
    for scene in ex_scenes:
        symbol=scene["symbol"]
        draft={"width":scene["width"],"height":scene["height"],"tileset_id":1,"layers":scene["layers"]}
        raw=build_rxdata(draft,exterior)
        files[symbol+".rxdata"]=raw
        files["previews/"+symbol+".svg"]=svg_preview(scene).encode()
    audited=audit_nine(j10_files,j10_manifest,ex_scenes,exterior,files)
    registries=proposed_tilesets({"J10A_INTERIORS":files["OriginalJ10A.png"],
                                  "J11B_EXTERIORS":exterior})
    files["tileset-registration-proposal.json"]=(json.dumps(registries,sort_keys=True,indent=2)+"\n").encode()
    source_rows=[]
    for symbol in MAPS:
        name="J10A_INTERIORS" if symbol in five.SYMBOLS else "J11B_EXTERIORS"
        d=audited["five"][symbol]["rxdata"] if symbol in five.SYMBOLS else audited["four"][symbol]
        source_rows.append({"symbol":symbol,"source":"ORIGINAL_GENERATOR",
                            "source_phase":"J10-A" if name=="J10A_INTERIORS" else "J11-B",
                            "rxdata_sha256":audited["hashes"][symbol],
                            "dimensions":[d["width"],d["height"]],
                            "tileset_group":name,"provisional_embedded_tileset_id":1,
                            "native_tileset_id":None,"destination_mapid":None,
                            "r07_approved":False,"r08_approved":False,
                            "native_passability_validated":False,"human_reviewed":False,
                            "installed":False})
    symbolic={"schema":1,"region":"SINNOH","stage":STAGE,
              "mode":"NINE_ORIGINAL_GEOMETRIES_PROPOSAL_NOT_INSTALLABLE",
              "nine_map_symbols_ordered":list(MAPS),"maps":source_rows,
              "historical_source_maps_used":0,
              "donor_assets_used":False,
              "mapinfos_baseline_checked":False,"mapid_reservations_approved":False,
              "real_tilesets_registered":False,"native_geometry_integrated":False,
              "rights_reviewed":False,"event_contract_counts":{"warps":16,"npcs":5,"starter_balls":3},
              "event_coordinates_reviewed":False,
              "native_maps_installed":0,"windows_native_qa":0,"android_native_qa":0,
              "can_stage_j03_j04_j06":False,"can_install":False,"can_publish":False}
    files["nine-map-source-plan.json"]=(json.dumps(symbolic,sort_keys=True,indent=2)+"\n").encode()
    report={"schema":1,"region":"SINNOH","stage":STAGE,
            "status":"NINE_ORIGINAL_MAP_GEOMETRIES_GENERATED_NOT_NATIVE_APPROVED",
            "five_existing_originals":5,"four_new_original_exteriors":4,
            "nine_distinct_rxdata_count":9,"previews_svg_count":9,
            "tilesets_png_count":2,"source_authorship":"PROGRAMMATIC_NOT_HUMAN_ATTESTED",
            "r07_approved":False,"r08_approved":False,"r09_approved":False,
            "actual_rmxp_tileset_passability_checked":False,
            "mapinfos_baseline_verified":False,"mapids_assigned":0,
            "native_maps_installed":0,"native_qa_cases_executed":0,
            "can_install":False,"can_publish_game":False,
            "next":"INDEPENDENT_HUMAN_REVIEW_THEN_R07_R08_RMXP_TILESETS_J04_AND_NATIVE_QA",
            "files_sha256":{name:sha(blob) for name,blob in sorted(files.items())}}
    files["manifest.json"]=(json.dumps(report,sort_keys=True,indent=2)+"\n").encode()
    return files,report

def r07_optional(root:Path,baseline:Path|None,review:Path|None):
    if (baseline is None)!=(review is None):fail("R07_BASELINE_AND_REVIEW_REQUIRED_TOGETHER")
    if baseline is None:
        return {"checked":False,"reason":"REAL_PRIVATE_MAPINFOS_AND_REGIONAL_RESERVATIONS_MISSING",
                "independently_approved":False}
    result=j11.check_r07(root,baseline,review)
    return {"checked_locally":True,"result":result,"independently_approved":False}

def private_build(project:Path):
    project=Path(project).absolute()
    work=project/".blue-work";target=work/OUTPUT
    if (not project.is_dir() or project.is_symlink() or work.is_symlink()
        or target.exists() or target.is_symlink()
        or not (project/"scripts/regions/generate_sinnoh_original_j10a.py").is_file()):
        fail("PRIVATE_PROJECT_OR_OUTPUT_UNSAFE")
    files,report=generate()
    work.mkdir(exist_ok=True)
    if work.is_symlink():fail("PRIVATE_SYMLINK_WORKSPACE")
    staging=Path(tempfile.mkdtemp(prefix=".j11b-atomic-",dir=work))
    try:
        for name,blob in files.items():
            path=staging/name
            path.parent.mkdir(parents=True,exist_ok=True)
            with path.open("xb") as f:f.write(blob)
        if any(sha((staging/name).read_bytes())!=sha(blob) for name,blob in files.items()):
            fail("PRIVATE_BUNDLE_HASH_MISMATCH")
        if target.exists():fail("PRIVATE_TARGET_CONCURRENTLY_CREATED")
        staging.rename(target)
    finally:
        if staging.exists():shutil.rmtree(staging)
    return {**report,"private_directory":str(target),"private_bundle_created":True}

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--project",type=Path,default=ROOT)
    p.add_argument("--build",action="store_true",
                   help="Write only a NEW ignored .blue-work design folder; never install")
    p.add_argument("--r07-baseline",type=Path,
                   help="Only .blue-work/sinnoh-j11-baseline/Data from isolated QA")
    p.add_argument("--r07-review",type=Path,
                   help="Only .blue-work private R07 JSON; not independent approval")
    args=p.parse_args(argv)
    try:
        if args.build and (args.r07_baseline or args.r07_review):
            fail("BUILD_CANNOT_COMBINE_WITH_PRIVATE_R07_INPUTS")
        out=private_build(args.project) if args.build else generate()[1]
        out["r07_local_validation"]=r07_optional(args.project,args.r07_baseline,args.r07_review)
    except (ValueError,OSError,TypeError,KeyError,IndexError,OverflowError,struct.error,zlib.error) as exc:
        print("J11B_BLOQUEADO:"+str(exc),file=sys.stderr)
        return 2
    print(json.dumps(out,sort_keys=True,indent=2,ensure_ascii=False))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
