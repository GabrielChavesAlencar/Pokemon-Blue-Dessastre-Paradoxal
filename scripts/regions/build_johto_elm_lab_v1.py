"""Generate Elm's own lab with three visible Poké Balls, without Game.exe.

All third-party graphics stay in the private .blue-work preview. No game/
updates, no executable scripts/events, no claims of runtime collision QA.
Requires only Python stdlib and the Blue/Decades installation data.
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
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SYMBOL = "JOHTO_NEW_BARK_ELM_LAB"
WIDTH, HEIGHT = 20, 16
TILESET_NAME = "BLUE_JOHTO_ELM_INSIDE"
STARTERS = ("CHIKORITA", "CYNDAQUIL", "TOTODILE")
BALLS = ((7, 6), (10, 6), (13, 6))
APPROACH = ((7, 8), (10, 8), (13, 8))
ELM = (10, 4)
DOOR = (9, 12)
FROM_TOWN = (10, 11)
PNG_HEADER = b"\x89PNG\r\n\x1a\n"


def tile(row: int, col: int) -> int:
    if type(row) is not int or type(col) is not int or not 0 <= row < 618 or not 0 <= col < 8:
        raise ValueError("Invalid native Inside tileset index")
    return 384 + 8 * row + col


def table_values(raw: bytes, dimension: int | None = None):
    if not isinstance(raw, bytes) or len(raw) < 20:
        raise ValueError("Truncated RPG Maker XP table")
    d, w, h, z, n = struct.unpack_from("<5I", raw)
    if ((dimension is not None and d != dimension) or d not in (1, 3)
            or not 1 <= w <= 65536 or not 1 <= h <= 5000 or not 1 <= z <= 3
            or n != w*h*z or len(raw) != 20+2*n):
        raise ValueError("Invalid RPG Maker XP table shape")
    return (w, h, z), struct.unpack_from(f"<{n}H", raw, 20)


def extend_table(raw: bytes, *, ball_flag: int = 0) -> bytes:
    shape, values = table_values(raw, dimension=1)
    if shape[1:] != (1, 1) or shape[0] != tile(617, 7)+1:
        raise ValueError("Unexpected native Inside table length")
    new_values = (*values, *(ball_flag for _ in range(3)), *(0 for _ in range(5)))
    return struct.pack("<5I", 1, len(new_values), 1, 1, len(new_values)) + struct.pack(f"<{len(new_values)}H", *new_values)


def _png_chunk(label: bytes, data: bytes) -> bytes:
    return (struct.pack(">I", len(data)) + label + data +
            struct.pack(">I", zlib.crc32(label+data) & 0xffffffff))


def decode_png(raw: bytes, *, expected_width: int | None = None, max_height: int = 20000):
    """Strict 8-bit RGBA PNG reader for the two installed known assets."""
    if not raw.startswith(PNG_HEADER) or len(raw) > 32_000_000:
        raise ValueError("Not a supported PNG")
    pos, idat, shape, end = len(PNG_HEADER), bytearray(), None, False
    while pos + 12 <= len(raw):
        count = struct.unpack_from(">I", raw, pos)[0]
        if count > 32_000_000 or pos + count + 12 > len(raw):
            raise ValueError("Unsafe PNG chunk size")
        kind = raw[pos+4:pos+8]
        data = raw[pos+8:pos+8+count]
        crc = struct.unpack_from(">I", raw, pos+8+count)[0]
        if zlib.crc32(kind+data) & 0xffffffff != crc:
            raise ValueError("Corrupt PNG CRC")
        pos += count + 12
        if kind == b"IHDR":
            if shape is not None or len(data) != 13:
                raise ValueError("PNG header repeated/invalid")
            w, h, bits, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", data)
            if ((expected_width is not None and w != expected_width) or
                    not 1 <= w <= 512 or not 1 <= h <= max_height or
                    (bits, color, compression, filtering, interlace) != (8, 6, 0, 0, 0)):
                raise ValueError("PNG must be noninterlaced 8-bit RGBA")
            shape = (w, h)
        elif kind == b"IDAT":
            idat.extend(data)
            if len(idat) > 32_000_000:
                raise ValueError("Oversized PNG IDAT")
        elif kind == b"IEND":
            end = True
            break
        elif kind[0] & 32 == 0 and kind not in (b"PLTE",):
            raise ValueError("Unexpected PNG critical chunk")
    if not end or shape is None or pos != len(raw):
        raise ValueError("Missing PNG end")
    w, h = shape
    stride = w*4
    decoder = zlib.decompressobj()
    packed = decoder.decompress(bytes(idat), h*(stride+1)+1)
    packed += decoder.flush()
    if not decoder.eof or decoder.unused_data or len(packed) != h*(stride+1):
        raise ValueError("Unexpected PNG decompressed size")
    rows = []
    prev = bytes(stride)
    for y in range(h):
        offset = y*(stride+1)
        filt = packed[offset]
        src = packed[offset+1:offset+1+stride]
        if filt not in range(5):
            raise ValueError("Unexpected PNG filter")
        out = bytearray(stride)
        if filt == 0:
            out[:] = src
        else:
            for i, value in enumerate(src):
                a = out[i-4] if i >= 4 else 0
                b = prev[i]
                c = prev[i-4] if i >= 4 else 0
                if filt == 1: predict = a
                elif filt == 2: predict = b
                elif filt == 3: predict = (a+b)//2
                else:
                    p = a+b-c
                    pa, pb, pc = abs(p-a), abs(p-b), abs(p-c)
                    predict = a if pa <= pb and pa <= pc else b if pb <= pc else c
                out[i] = (value + predict) & 255
        rows.append(bytes(out))
        prev = out
    return w, h, rows


def encode_png(width: int, rows: list[bytes]) -> bytes:
    if width < 1 or width > 512 or not rows or any(len(x) != width*4 for x in rows):
        raise ValueError("Bad generated PNG rows")
    data = b"".join(b"\x00"+r for r in rows)
    return (PNG_HEADER + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width,len(rows),8,6,0,0,0))+
            _png_chunk(b"IDAT", zlib.compress(data, 7)) + _png_chunk(b"IEND", b""))


def lab_tileset_png(inside: bytes, obj_ball: bytes) -> bytes:
    w, h, rows = decode_png(inside, expected_width=256)
    if h != 618*32:
        raise ValueError("Native Inside tile atlas differs from audited 618 rows")
    bw, bh, brows = decode_png(obj_ball, expected_width=128, max_height=128)
    if (bw, bh) != (128, 128):
        raise ValueError("Object_Ball sprite atlas mismatch")
    # First 32x32 frame, with three independent copies in the new final row.
    appended = []
    for sy in range(32):
        ball = brows[sy][:32*4]
        out = bytearray(w*4)
        for sx in (0, 1, 2):
            out[sx*32*4:(sx+1)*32*4] = ball
        appended.append(bytes(out))
    generated = encode_png(w, rows+appended)
    rw,rh,_ = decode_png(generated, expected_width=256)
    if (rw,rh)!=(256,h+32):
        raise ValueError("Generated Elm PNG invalid")
    return generated


def blueprint(passages: tuple[int,...]):
    """Actual table with 3 Poké Ball tiles, not imaginary event placeholders."""
    if len(passages) < tile(617,7)+9:
        raise ValueError("Inside tileset has not been extended with physical balls")
    cells = [0]*(WIDTH*HEIGHT*3)
    reserved = set()
    furniture=[]
    def put(x,y,z,tid,label):
        if not (0 <= x < WIDTH and 0 <= y < HEIGHT and 0 <= z < 3) or not 0 <= tid < len(passages):
            raise ValueError("Invalid tile position: "+label)
        key=(x,y,z)
        if key in reserved:
            raise ValueError("Overlapping lab geometry: "+label)
        reserved.add(key)
        cells[x+WIDTH*(y+HEIGHT*z)]=tid
    for y in range(1,HEIGHT-1):
        for x in range(1,WIDTH-1):
            put(x,y,0,tile(85, 2),"tile floor")
    for x in range(1,WIDTH-1):
        put(x,0,0,tile(190,3),"upper wall")
        put(x,1,1,tile(191,3),"wall face")
        put(x,HEIGHT-1,0,tile(190,0),"lower wall")
    for y in range(HEIGHT):
        put(0,y,0,tile(190,0),"left wall")
        put(WIDTH-1,y,0,tile(190,0),"right wall")

    def decoration(name,x,y,row,col,w,h,z=2):
        for dy in range(h):
            for dx in range(w):
                put(x+dx,y+dy,z,tile(row+dy,col+dx),name)
        furniture.append({'name':name,'x':x,'y':y,'width':w,'height':h,'layer':z})

    decoration('research_bookshelf',2,3,251,4,4,3)
    decoration('diagnostics_computer',14,3,257,0,4,3)
    decoration('lab_scanner',16,8,266,6,1,3)
    decoration('desk_console',2,9,264,0,3,2)
    decoration('entry_door',9,13,200,4,2,2)
    decoration('research_poster',11,1,201,7,1,1)
    # Three matching laboratory desks, with physical Poké Balls drawn above them.
    for starter, (bx,by), col in zip(STARTERS,BALLS,range(3)):
        decoration('starter_pedestal_'+starter.lower(),bx,by,283,0,2,2,z=1)
        put(bx,by,2,tile(617,7)+1+col,'pokeball_'+starter)
    proposal={'elm':ELM,'entry_door_approach':DOOR,'arrival_from_town':FROM_TOWN}
    proposal.update({'approach_'+name.lower():p for name,p in zip(STARTERS,APPROACH)})

    def walkable(x,y):
        return (0 <= x < WIDTH and 0 <= y < HEIGHT and
                all(not (passages[cells[x+WIDTH*(y+HEIGHT*z)]] & 15)
                    for z in range(3)))
    for label,point in proposal.items():
        if not walkable(*point):
            raise ValueError('Blocked Elm lab proposed coordinate: '+label)
    seen={DOOR};stack=[DOOR]
    while stack:
        x,y=stack.pop()
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if (1<=nx<WIDTH-1 and 2<=ny<HEIGHT-1 and
                    (nx,ny) not in seen and walkable(nx,ny)):
                seen.add((nx,ny));stack.append((nx,ny))
    if len(seen)<55 or any(p not in seen for p in proposal.values()):
        raise ValueError('Elm or starter interaction aisle unreachable')
    table=struct.pack('<5I',3,WIDTH,HEIGHT,3,len(cells))+struct.pack(f'<{len(cells)}H',*cells)
    return table,{
        'schema':1,'region':'JOHTO','symbol':SYMBOL,
        'status':'AUTHORED_ELM_LAB_OFFLINE_NOT_PLAYABLE',
        'size':[WIDTH,HEIGHT],'furniture':furniture,
        'starter_balls':[{'starter':name,'x':bx,'y':by,'tile_id':tile(617,7)+1+i,
                           'event_installed':False,'remove_static_tile_when_event_added':True}
                         for i,(name,(bx,by)) in enumerate(zip(STARTERS,BALLS))],
        'proposed_positions':{key:{'x':value[0],'y':value[1],
                                   'static_passability_checked':True,'verified_in_game':False}
                              for key,value in proposal.items()},
        'static_reachable_tiles':len(seen),
        'passability':'STATIC_TILE_FLAGS_ONLY','events_installed':0,
        'engine_warps_installed':False,'native_game_modified':False,
        'gameplay_playable':False,'tested_in_game':False,
    }


def build(*,root:Path=ROOT, preview:Path|None=None, output:Path|None=None):
    from audit_johto import checksum,read_map_data
    from stage import serialize
    from verify_johto import inspect
    from server.ruby_marshal import RubyData,RubyObject,text
    root=root.resolve(); work=root/'.blue-work'; game=root/'game'
    preview=(preview or work/'johto-staging-home1f-v1').absolute()
    output=(output or work/'johto-staging-elm-lab-v1').absolute()
    if (work.is_symlink() or game.is_symlink() or preview.is_symlink() or output.is_symlink() or
            output.exists() or not preview.resolve().is_relative_to(work.resolve()) or
            not output.resolve().is_relative_to(work.resolve()) or
            output.resolve() in (work.resolve(),preview.resolve()) or
            output.resolve().is_relative_to(preview.resolve()) or
            preview.resolve().is_relative_to(output.resolve())):
        raise ValueError('Use two separate .blue-work previews and no overwriting')
    if inspect(preview,game,root=root).get('status')!='STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE':
        raise ValueError('Prior stage not validated')
    stage=json.loads((preview/'johto-stage.json').read_text(encoding='utf-8'))
    entries={r['symbol']:r for r in stage['maps']}
    if (entries.get('JOHTO_NEW_BARK_PLAYER_HOME_2F',{}).get('origin')!='BLUE_AUTHORED_OFFLINE_BEDROOM_V1' or
            entries.get('JOHTO_NEW_BARK_PLAYER_HOME_1F',{}).get('origin')!='BLUE_AUTHORED_OFFLINE_HOME1F_V1' or
            entries.get(SYMBOL,{}).get('origin')!='BLUE_NATIVE_INTERIOR_TEMPLATE'):
        raise ValueError('Required 4/12 and 5/12 or lab already authored')
    labid=entries[SYMBOL]['destination_id']
    if type(labid) is not int or not 600<=labid<=999:
        raise ValueError('Lab MapID invalid')
    mapfile=preview/'Data'/f'Map{labid:03d}.rxdata'
    room=read_map_data(mapfile); tiles=read_map_data(preview/'Data/Tilesets.rxdata')
    if not isinstance(room,RubyObject) or room.name!='RPG::Map' or not isinstance(tiles,list):
        raise ValueError('Expected RMXP map and tilesets')
    donor_id=room.attrs.get('@tileset_id')
    if (type(donor_id) is not int or not 0<donor_id<len(tiles) or
            not isinstance(tiles[donor_id],RubyObject) or
            text(tiles[donor_id].attrs.get('@tileset_name')).casefold()!='inside'):
        raise ValueError('Lab must derive the installed native Inside tileset')
    inside=game/'Graphics/Tilesets/Inside.png'
    ball=game/'Graphics/Characters/Object_Ball.png'
    if any(not f.is_file() or f.is_symlink() for f in (inside,ball)):
        raise ValueError('Native Inside.png or Object_Ball.png not installed')
    png=lab_tileset_png(inside.read_bytes(),ball.read_bytes())
    t=copy.deepcopy(tiles[donor_id]);new_id=len(tiles)
    t.attrs['@id']=new_id;t.attrs['@name']=b'Blue Johto Elm Lab Inside'
    t.attrs['@tileset_name']=TILESET_NAME.encode('ascii')
    for field,ball_flag in (('@passages',15),('@priorities',0),('@terrain_tags',0)):
        val=t.attrs.get(field)
        if not isinstance(val,RubyData) or val.name!='Table':
            raise ValueError('Native Inside tileset table absent: '+field)
        val.data=extend_table(val.data,ball_flag=ball_flag)
    _,flags=table_values(t.attrs['@passages'].data,dimension=1)
    grid,proof=blueprint(flags)
    replacement=copy.deepcopy(room)
    replacement.attrs.update({'@width':WIDTH,'@height':HEIGHT,'@tileset_id':new_id,
                              '@data':RubyData('Table',grid),'@events':{},
                              '@encounter_list':[],'@autoplay_bgm':False,'@autoplay_bgs':False})
    for sound in ('@bgm','@bgs'):
        audio=replacement.attrs.get(sound)
        if isinstance(audio,RubyObject): audio.attrs['@name']=b''
    finalmap=serialize(replacement)
    proof.update({'map_id':labid,'tileset_id':new_id,'map_sha256':hashlib.sha256(finalmap).hexdigest(),
                  'input_map_sha256':checksum(mapfile),'tileset_png_sha256':hashlib.sha256(png).hexdigest(),
                  'source_archive_sha256':stage['source_archive_sha256']})
    edited=copy.deepcopy(stage);entry=next(r for r in edited['maps'] if r['symbol']==SYMBOL)
    entry.update({'origin':'BLUE_AUTHORED_OFFLINE_ELM_LAB_V1','elm_lab_authored_geometry':True,
                  'events_imported':0,'tileset_id':new_id,'layout_is_hgss_verified':False})
    edited['elm_lab_offline_preview']=proof
    edited['warnings'].append('Elm lab physical balls are STATIC tiles; stage 08 must swap to interactive starter events')
    tiles.append(t)
    destination_img=f'Graphics/Tilesets/{TILESET_NAME}.png'
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.johto-elm-',dir=output.parent) as tmp:
        target=Path(tmp)/'staging';shutil.copytree(preview,target)
        (target/'Data'/f'Map{labid:03d}.rxdata').write_bytes(finalmap)
        (target/'Data/Tilesets.rxdata').write_bytes(serialize(tiles))
        graphic=target/destination_img
        if graphic.exists():raise ValueError('Johto Elm graphic collides with private stage')
        graphic.parent.mkdir(parents=True,exist_ok=True);graphic.write_bytes(png)
        (target/'johto-stage.json').write_text(json.dumps(edited,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        if inspect(target,game,root=root).get('status')!='STRUCTURAL_PREVIEW_VALIDATED_NOT_PLAYABLE':
            raise ValueError('Final Elm stage failed geometry check')
        if output.exists() or output.is_symlink():raise ValueError('Output already exists')
        target.rename(output)
    return proof


def main(argv=None):
    cli=argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--root',type=Path,default=ROOT)
    cli.add_argument('--preview',type=Path)
    cli.add_argument('--output',type=Path)
    a=cli.parse_args(argv)
    try: proof=build(root=a.root,preview=a.preview,output=a.output)
    except (OSError,ValueError,KeyError,TypeError,zlib.error) as exc:
        print('[JOHTO][BLOQUEADO]',exc,file=sys.stderr)
        return 2
    print('[JOHTO] Elm laboratory',proof['map_id'],proof['size'],'3 visible static Poké Balls')
    print('[JOHTO] No Game.exe, no native game changes and no events installed')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
