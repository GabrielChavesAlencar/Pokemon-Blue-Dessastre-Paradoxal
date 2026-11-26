"""Original project-authored 4x4 overworld sheets, no donor extraction."""
import struct
import zlib
import sinnoh_f10c_npcs as npc

def psyduck_sheet():
    size=128;raw=bytearray(size*size*4)
    ink=(111,80,41);gold=(245,201,75);shade=(218,161,45);bill=(246,221,158);eye=(38,38,42)
    for direction in range(4):
        for frame in range(4):
            ox,oy=frame*32,direction*32
            bob=frame%2
            def ellipse(cx,cy,rx,ry,color):
                for y in range(max(0,cy-ry),min(32,cy+ry+1)):
                    for x in range(max(0,cx-rx),min(32,cx+rx+1)):
                        if (x-cx)**2*ry**2+(y-cy)**2*rx**2<=rx**2*ry**2:
                            n=((oy+y)*size+ox+x)*4;raw[n:n+4]=bytes((*color,255))
            ellipse(16,21+bob,9,8,ink);ellipse(16,20+bob,8,7,shade)
            ellipse(11,27,4,2,ink);ellipse(21,27,4,2,ink)
            ellipse(11,26,3,2,bill);ellipse(21,26,3,2,bill)
            ellipse(16,13+bob,10,9,ink);ellipse(16,13+bob,9,8,gold)
            for x in (13,16,19):
                ellipse(x,4+bob,1,3,ink)
            if direction!=3:
                dx=-3 if direction==1 else 3 if direction==2 else 0
                ellipse(16+dx,17+bob,7,4,ink);ellipse(16+dx,17+bob,6,3,bill)
                if direction!=2:ellipse(12+dx,12+bob,1,2,eye)
                if direction!=1:ellipse(20+dx,12+bob,1,2,eye)
            else:
                ellipse(16,22+bob,4,3,gold)
            ellipse(8,18+bob,2,3,gold);ellipse(24,18+bob,2,3,gold)
    def chunk(tag,data):
        return struct.pack(">I",len(data))+tag+data+struct.pack(">I",zlib.crc32(tag+data)&0xffffffff)
    scan=b"".join(b"\0"+raw[y*size*4:(y+1)*size*4] for y in range(size))
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",size,size,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(scan,9))+chunk(b"IEND",b"")

def build():
    prefix="Graphics/Characters/SNQA_F12D_"
    return {prefix+"CYNTHIA.png":npc.authored_sheet("f12d_cynthia"),
        prefix+"PSYDUCK.png":psyduck_sheet(),
        prefix+"VALOR.png":npc.authored_sheet("galactic_saturn"),
        prefix+"VERITY.png":npc.authored_sheet("galactic_mars"),
        prefix+"ACUITY.png":npc.authored_sheet("galactic_jupiter")}
