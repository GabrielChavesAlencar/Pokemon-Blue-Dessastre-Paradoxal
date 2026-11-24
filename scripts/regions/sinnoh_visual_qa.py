"""Original pixel-art upgrade for the isolated Sinnoh pilot (no donor art).

New art is authored here; no official sprites, external pack or permission
claims. Historical J10/J11 receipts remain unchanged. Not native visual QA.
"""
import struct
import zlib
from audit_sinnoh_rxdata import read_marshal
from server.ruby_marshal import RubyData
from stage import serialize
from build_johto_events import EVENT_CLASSES
from compile_sinnoh_playable_j04 import passable_point

FIRST=384
COUNT=64
LAKE="SINNOH_LAKE_VERITY"
OUTSIDE={"SINNOH_TWINLEAF_TOWN","SINNOH_ROUTE_201","SINNOH_SANDGEM_TOWN",
         "SINNOH_ROUTE_202",LAKE}
# Each extra slot has a semantic parent; variants never change collision.
VARIANTS=(0,1,4,16,16,16,17,17,17,17,18,18,19,19,20,20,
          6,6,6,6,13,13,13,13,2,2,7,7,25,25,31,31)
BLOCKED={2,5,6,7,8,9,12,13,14,15,18,19,20,22,24,25,26,27,28,30,31}
NAMES=("floor","stone","wall","door","rug","shelf","bed","desk","chair",
       "pc","stairs","window","table","counter","machine","plant","grass",
       "path","water","shore","tree","flowers","rock","bridge","book","sofa",
       "sink","computer","pillow","lamp","lab","fence")

def parent(i):
    return VARIANTS[i-32] if i>=32 else i

def png(width,height,pixels):
    def chunk(name,data):
        b=name+data
        return struct.pack(">I",len(data))+b+struct.pack(">I",zlib.crc32(b)&0xffffffff)
    scan=b"".join(b"\0"+pixels[y*width*4:(y+1)*width*4] for y in range(height))
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",width,height,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(scan,9))+chunk(b"IEND",b"")

class Canvas:
    def __init__(self,w,h):
        self.w=w;self.h=h;self.raw=bytearray(w*h*4)
    def rect(self,x,y,w,h,color):
        c=bytes.fromhex(color)+b"\xff"
        for yy in range(max(0,y),min(self.h,y+h)):
            for xx in range(max(0,x),min(self.w,x+w)):
                p=4*(yy*self.w+xx);self.raw[p:p+4]=c
    def dot(self,x,y,color):
        self.rect(x,y,1,1,color)
    def ellipse(self,x,y,w,h,color):
        for yy in range(y,y+h):
            for xx in range(x,x+w):
                if ((xx-x+.5-w/2)/(w/2))**2+((yy-y+.5-h/2)/(h/2))**2<=1:
                    self.dot(xx,yy,color)
    def paste2(self,other,x,y):
        for yy in range(other.h):
            for xx in range(other.w):
                p=4*(yy*other.w+xx);c=other.raw[p:p+4]
                for dy in range(2):
                    for dx in range(2):
                        q=4*((y+2*yy+dy)*self.w+x+2*xx+dx)
                        self.raw[q:q+4]=c

def tile_art(slot,exterior):
    i=parent(slot);v=slot-32 if slot>=32 else 0
    c=Canvas(16,16);r=c.rect;e=c.ellipse
    if i in (0,1):
        r(0,0,16,16,"d4b890" if i==0 else "c7c3b3")
        for y in (0,5,10,15):
            r(0,y,16,1,"aa8965" if i==0 else "a2a59e")
            r((y*3+v*5)%15,y,1,5,"b39774" if i==0 else "b1b4ab")
        for y in (2,7,12):r((y*5+v)%10,y,5,1,"e3cba6" if i==0 else "e2dfcf")
    elif i==16:
        r(0,0,16,16,"86b963")
        for j in range(12):
            x=(j*7+slot*3)%16;y=(j*11+slot)%16
            c.dot(x,y,"6b9e4e");c.dot(x+1,y-1,"a3ce78")
    elif i==17:
        r(0,0,16,16,"dcc397")
        for j in range(8):c.dot((j*7+v)%16,(j*3+v*2)%16,"c6a979")
        if 38<=slot<=41:
            if slot==38:r(0,0,16,2,"86b963")
            if slot==39:r(14,0,2,16,"86b963")
            if slot==40:r(0,14,16,2,"86b963")
            if slot==41:r(0,0,2,16,"86b963")
    elif i==18:
        r(0,0,16,16,"508fb2")
        for y in (3,9,14):
            x=(y+v*3)%9;r(x,y,7,1,"77c2d7");r(x+2,y+1,4,1,"397b9d")
    elif i==19:
        r(0,0,16,16,"89b96b");r(0,6,16,10,"75b8c5")
        r(0,5,16,1,"c2d4a1");r(1,8,9,1,"a4d7d7")
        # Shore variant mirrors the edge for the opposite water direction.
        if slot==45:
            c.raw=bytearray(b"".join(c.raw[y*64:(y+1)*64] for y in range(15,-1,-1)))
    elif i==20:
        e(1,11,14,5,"526f4d");r(7,10,3,6,"795238")
        e(0,0,16,13,"345e43");e(1,0,13,10,"4f854c");e(3,1,9,6,"78a85a")
        e(7,5,7,5,"63974f");r(4,4,3,1,"a3c779")
    elif i==21:
        for x,y in ((4,8),(10,4),(12,12)):
            r(x,y,1,3,"547d49");e(x-2,y-2,5,5,"f1ce75");c.dot(x,y,"d88754")
    elif i==22:
        e(1,5,14,10,"69766d");e(2,3,12,10,"8e9b90");r(4,5,6,2,"b8c1b0");r(7,12,6,1,"54635d")
    elif i==31:
        for x in (2,12):r(x,3,3,13,"7b6247");r(x,3,1,12,"c1a77a")
        for y in (6,10):r(0,y,16,2,"aa8e66")
    elif i==2:
        r(0,0,16,16,"b6aa94" if exterior else "657a86")
        for y in (0,6,12):
            r(0,y,16,1,"897c6d" if exterior else "465c69")
            r((y//6%2)*8,y,1,6,"897c6d" if exterior else "465c69")
        r(0,0,16,2,"d8cbb2" if exterior else "a3b4b7")
    elif exterior and i in (6,13):
        r(0,0,16,16,"a86155" if i==6 else "677e9d")
        for y in (0,4,8,12):
            r(0,y,16,1,"684d4c");r(0,y+1,16,1,"d3977d" if i==6 else "9aabc5")
            for x in range((y%8)*2//2,16,8):r(x,y,1,4,"78565a")
        if slot in (48,52):r(0,0,16,2,"e5c5ab")
        if slot in (49,53):r(0,14,16,2,"574b4e")
        if slot in (50,54):r(0,0,2,16,"574b4e")
        if slot in (51,55):r(14,0,2,16,"574b4e")
    elif i==3:
        r(0,0,16,16,"c0a385");r(3,1,10,15,"684b3e");r(4,2,8,14,"a67751")
        r(5,3,6,5,"d5b18a");r(5,9,6,5,"8f5f43");c.dot(10,10,"f2d18d")
    elif i==4:
        r(0,0,16,16,"ac645e");r(0,0,16,2,"e4be9b");r(0,14,16,2,"e4be9b")
        for x in (2,13):r(x,2,1,12,"d39982")
        for x,y in ((5,5),(9,9)):e(x,y,4,4,"dca789")
    elif i==6:
        r(1,0,14,16,"644c47");r(2,1,12,14,"ad795f")
        r(3,2,10,4,"f2e5cf");r(3,6,10,8,"80a5b4");r(3,10,10,2,"557c93")
        if slot==48:r(3,1,10,5,"f2e5cf")
        if slot==49:r(3,0,10,14,"80a5b4")
    elif i==10:
        r(0,0,16,16,"997a5c")
        for y in (1,5,9,13):r(1,y,14,2,"ddbe90");r(1,y+2,14,1,"715b49")
    elif i==11:
        r(1,1,14,14,"7c6554");r(2,2,12,10,"b4d6dc");r(3,3,10,8,"7cacc3")
        r(7,2,2,10,"ebe4cc");r(2,6,12,2,"ebe4cc")
    elif i in (9,14,27):
        r(2,1,12,13,"687d86");r(3,2,10,8,"334f64");r(4,3,8,6,"8fc3cb")
        r(4,11,8,2,"dde2d4");r(6,14,4,2,"53616a")
    elif i in (15,):
        r(5,10,6,6,"a67454");e(1,0,14,12,"3f7350");e(4,1,8,7,"82b96c")
    elif i in (5,7,8,12,13,24,25,26,28,29,30):
        colors={5:"a17b56",7:"a47b59",8:"b78b64",12:"b99165",13:"b6b6a4",
                24:"c18c64",25:"778f9f",26:"b0c4c6",28:"eee3cf",29:"f0d38a",30:"b7c7c4"}
        base=colors[i]
        r(2,4,12,11,"69594c");r(1,2,14,11,base);r(2,2,12,2,"ead7b7")
        if i==5:
            for y in (5,9):
                r(2,y,12,1,"674e40")
                for x in (3,6,9):r(x,y-3,2,3,"8bafaa" if x==6 else "b56854")
        elif i==25:r(2,4,12,4,"a2b9b8");r(3,9,10,3,"526f83")
        elif i==29:e(3,1,10,8,"f8e2a3");r(7,9,2,5,"a98b63")
        elif i==26:e(4,4,8,5,"6b8d9a");r(7,2,2,4,"dce7e4")
        elif i==28:e(2,3,12,8,"f7eede")
        else:r(3,6,10,1,"8f7962");r(4,13,2,3,"6b5140");r(10,13,2,3,"6b5140")
    elif i==23:
        r(0,0,16,16,"aa865b")
        for y in (0,4,8,12):r(0,y,16,1,"6e583f");r(0,y+1,16,1,"d3b183")
    return c

def atlas(exterior):
    c=Canvas(256,256)
    for i in range(COUNT):c.paste2(tile_art(i,exterior),(i%8)*32,(i//8)*32)
    return png(c.w,c.h,bytes(c.raw))

def npc(name):
    # 4 directions x 4 steps; original hand-authored palette/pose.
    colors={"MOTHER":("785346","bb7784"),"BARRY":("d7ad54","d88847"),
            "ROWAN":("d7d7c9","7d8b9c")}
    hair,coat=colors[name];c=Canvas(128,128)
    for d in range(4):
        for step in range(4):
            f=Canvas(16,16);r=f.rect;e=f.ellipse
            e(3,12,10,4,"536064");r(5,9,6,5,coat)
            r(4,9,2,4,coat);r(10,9,2,4,coat)
            e(3,1,10,9,hair);e(4,3,8,7,"e4b995")
            r(4,2,8,2,hair)
            if d==3:r(4,3,8,6,hair)
            elif d in (1,2):f.dot(6 if d==1 else 10,6,"3b4148")
            else:
                f.dot(6,6,"3b4148");f.dot(9,6,"3b4148")
            r(7,10,2,3,"e6d5b5")
            r(5,13-(step==1),2,3,"455268");r(9,13-(step==3),2,3,"455268")
            c.paste2(f,step*32,d*32)
    return png(c.w,c.h,bytes(c.raw))

def remap_cells(cells,w,h,outside):
    result=list(cells);area=w*h
    def get(z,x,y):
        return cells[z*area+y*w+x]-FIRST if 0<=x<w and 0<=y<h else -1
    for z in range(3):
        for y in range(h):
            for x in range(w):
                n=z*area+y*w+x;i=cells[n]-FIRST
                if cells[n]==0:continue
                if not 0<=i<32:raise ValueError("SINNOH_VISUAL_UNEXPECTED_SOURCE_TILE")
                k=i
                if i in (0,1,4) and (x+3*y)%3==0:k={0:32,1:33,4:34}[i]
                elif i==16:k=35+(x+2*y)%3
                elif i==17:
                    edges=[get(z,x,y-1),get(z,x+1,y),get(z,x,y+1),get(z,x-1,y)]
                    k=next((38+j for j,a in enumerate(edges) if a==16),17)
                elif i==18:k=42+(x+y)%2
                elif i==19:k=45 if get(z,x,y-1)==18 else 44
                elif i==20:k=46+(x+y)%2
                elif i in (6,13):
                    edges=[get(z,x,y-1),get(z,x,y+1),get(z,x-1,y),get(z,x+1,y)]
                    k=next(((48 if i==6 else 52)+j for j,a in enumerate(edges) if a!=i),i)
                result[n]=FIRST+k
    return result

def upgrade(blobs,mapping,tile_ids,events,start):
    """Recompile three layers, preserve semantic collision and event positions."""
    from prepare_sinnoh_nine_original_j11c import table1,GRAPHIC
    out=dict(blobs)
    tiles=read_marshal(out["Data/Tilesets.rxdata"],"VISUAL_TILES")
    for group,tid in tile_ids.items():
        outside=group=="J11B_EXTERIORS"
        a=tiles[tid].attrs
        p=[0]+[15]*(FIRST-1);pr=[0]*FIRST;tags=[0]*FIRST
        for k in range(COUNT):
            i=parent(k);blocked=i in BLOCKED
            p.append(15 if blocked else 0)
            pr.append(1 if blocked and i not in (18,19) else 0)
            # Rock and ordinary water are standard Essentials tags; no new
            # wild encounters, Surf authorization or tall-grass claims here.
            tags.append(4 if outside and i==22 else 6 if outside and i==18 else 0)
        a["@passages"]=table1(p);a["@priorities"]=table1(pr);a["@terrain_tags"]=table1(tags)
        out["Graphics/Tilesets/"+GRAPHIC[group][1]+".png"]=atlas(outside)
    out["Data/Tilesets.rxdata"]=serialize(tiles)
    for symbol,mid in mapping.items():
        path="Data/Map%03d.rxdata"%mid
        m=read_marshal(out[path],"VISUAL_MAP");a=m.attrs
        w,h=a["@width"],a["@height"];raw=a["@data"];n=w*h*3
        cells=struct.unpack_from("<"+str(n)+"H",raw.data,20)
        new=remap_cells(cells,w,h,symbol in OUTSIDE)
        a["@tileset_id"]=tile_ids["J11B_EXTERIORS" if symbol in OUTSIDE else "J10A_INTERIORS"]
        a["@data"]=RubyData("Table",raw.data[:20]+struct.pack("<"+str(n)+"H",*new))
        for event in events:
            if event["map"]==symbol:passable_point(m,tiles,*event["position"])
            if event.get("destination")==symbol:passable_point(m,tiles,*event["arrival"])
        if symbol=="SINNOH_PLAYER_BEDROOM":passable_point(m,tiles,*start)
        out[path]=serialize(m,EVENT_CLASSES)
    for name in ("MOTHER","BARRY","ROWAN"):
        out["Graphics/Characters/SNQA_"+name+".png"]=npc(name)
    return out
