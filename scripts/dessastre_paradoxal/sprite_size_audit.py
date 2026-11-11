"""Read-only audit of all Dessastre Paradoxal front/back PNGs.

The normalized art bundle is the authoritative source. No Pillow dependency:
decode the alpha channel using Python's PNG/zlib standard library support.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import math
import struct
import tarfile
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SIGNATURE=b'\x89PNG\r\n\x1a\n'
ROLES=('front','front-shiny','back','back-shiny')

def png_bounds(blob, threshold=16):
    """Return width,height,alpha bounds (x0,y0,x1,y1), frame count, per-frame boxes."""
    if not blob.startswith(SIGNATURE):
        raise ValueError('Not a PNG')
    p=8;parts=[];header=None;palette=None;transparency=b''
    while p<len(blob):
        if p+12>len(blob):raise ValueError('Incomplete PNG chunk')
        n=struct.unpack_from('>I',blob,p)[0]
        tag=blob[p+4:p+8]
        if p+n+12>len(blob):raise ValueError('Oversized PNG chunk')
        data=blob[p+8:p+8+n]
        crc=struct.unpack_from('>I',blob,p+8+n)[0]
        if zlib.crc32(tag+data)&0xffffffff!=crc:raise ValueError('PNG CRC error')
        if tag==b'IHDR':header=struct.unpack('>IIBBBBB',data)
        elif tag==b'PLTE':palette=data
        elif tag==b'tRNS':transparency=data
        elif tag==b'IDAT':parts.append(data)
        elif tag==b'IEND':break
        p+=12+n
    if header is None:raise ValueError('PNG missing IHDR')
    width,height,depth,color,compression,filter_method,interlaced=header
    if not 1<=width<=8192 or not 1<=height<=8192 or compression or filter_method or interlaced:
        raise ValueError(f'Unsupported size or interlaced PNG {width}x{height}')
    channels={0:1,2:3,3:1,4:2,6:4}.get(color)
    if channels is None or depth not in (1,2,4,8,16):
        raise ValueError(f'Unsupported PNG color {color} depth {depth}')
    if color in (2,4,6) and depth<8:raise ValueError('Unsupported packed truecolor')
    stride=(width*channels*depth+7)//8
    pixel_step=max(1,(channels*depth+7)//8)
    data=zlib.decompress(b''.join(parts))
    pos=0;previous=bytearray(stride);points=[]
    if color==3 and not palette:raise ValueError('Palette missing')
    transparent_rgb=tuple(transparency[i:i+2] for i in range(0,6,2)) if color==2 and len(transparency)>=6 else None
    transparent_gray=transparency[:2] if color==0 and len(transparency)>=2 else None
    for y in range(height):
        if pos+stride+1>len(data):raise ValueError('PNG data truncated')
        kind=data[pos];pos+=1
        row=bytearray(data[pos:pos+stride]);pos+=stride
        for k in range(stride):
            left=row[k-pixel_step] if k>=pixel_step else 0
            above=previous[k]
            upper=previous[k-pixel_step] if k>=pixel_step else 0
            if kind==0:f=0
            elif kind==1:f=left
            elif kind==2:f=above
            elif kind==3:f=(left+above)//2
            elif kind==4:
                p0=left+above-upper
                a,b,c=abs(p0-left),abs(p0-above),abs(p0-upper)
                f=left if a<=b and a<=c else above if b<=c else upper
            else:raise ValueError('PNG filter invalid')
            row[k]=(row[k]+f)&255
        previous=row
        for x in range(width):
            if depth<8:
                offset=x*depth
                sample=(row[offset//8]>>(8-depth-offset%8))&((1<<depth)-1)
                if color==3: alpha=transparency[sample] if sample<len(transparency) else 255
                else:alpha=0 if transparent_gray and sample==int.from_bytes(transparent_gray,'big') else 255
            elif depth==8:
                off=x*channels
                if color==6:alpha=row[off+3]
                elif color==4:alpha=row[off+1]
                elif color==3:alpha=transparency[row[off]] if row[off]<len(transparency) else 255
                elif color==2 and transparent_rgb:
                    alpha=0 if all(row[off+i]==transparent_rgb[i][1] for i in range(3)) else 255
                elif color==0 and transparent_gray:
                    alpha=0 if row[off]==transparent_gray[1] else 255
                else:alpha=255
            else:
                off=x*channels*2
                if color==6:alpha=row[off+6]
                elif color==4:alpha=row[off+2]
                elif color==2 and transparent_rgb:
                    alpha=0 if all(bytes(row[off+2*i:off+2*i+2])==transparent_rgb[i] for i in range(3)) else 255
                elif color==0 and transparent_gray:
                    alpha=0 if bytes(row[off:off+2])==transparent_gray else 255
                else:alpha=255
            if alpha>=threshold:points.append((x,y))
    if pos!=len(data):raise ValueError('PNG excess data')
    frame_width=height if width>height*2 and width%height==0 else width
    frames=width//frame_width
    boxes=[]
    for frame in range(frames):
        fragment=[(x-frame*frame_width,y) for x,y in points if frame*frame_width<=x<(frame+1)*frame_width]
        if fragment:
            boxes.append((min(x for x,y in fragment),min(y for x,y in fragment),
                          max(x for x,y in fragment)+1,max(y for x,y in fragment)+1))
        else:boxes.append(None)
    box=(min(x for x,y in points),min(y for x,y in points),
         max(x for x,y in points)+1,max(y for x,y in points)+1) if points else None
    return {'width':width,'height':height,'frames':frames,'frameWidth':frame_width,
            'bbox':box,'frameBoxes':boxes,'alphaPixels':len(points)}

def analyze(project=ROOT):
    manifest=json.loads((project/'data/dessastre-paradoxal.json').read_text('utf8'))
    archive=(project/'site/assets/fan-pokemon.tar.gz').read_bytes()
    if hashlib.sha256(archive).hexdigest()!=manifest['assetsSha256']:
        raise ValueError('Sprite bundle hash mismatch')
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tar:
        members={p.name:p for p in tar if p.isfile()}
        entries=[]
        for pokemon in manifest['entries']:
            summary={'id':pokemon['id'],'fileId':pokemon['fileId'],'name':pokemon['name'],
                     'base':pokemon.get('base'),'pending':pokemon['pending'],'sides':{}}
            for role in ROLES:
                source=pokemon['sprites'].get(role)
                if not source:continue
                member=members.get(source['path'])
                if not member:raise ValueError('Missing sprite '+pokemon['id']+' '+role)
                raw=tar.extractfile(member).read()
                if hashlib.sha256(raw).hexdigest()!=source['sha256']:
                    raise ValueError('Sprite checksum mismatch '+pokemon['id']+' '+role)
                summary['sides'][role]=png_bounds(raw)
            entries.append(summary)
    return entries

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    rows=analyze()
    if args.json:print(json.dumps(rows,ensure_ascii=False));return
    for row in rows:
        front=row['sides'].get('front');back=row['sides'].get('back')
        def describe(img):
            if not img:return 'MISSING'
            box=img['frameBoxes'][0]
            if not box:return 'EMPTY'
            return f"{img['frameWidth']}x{img['height']} art={box[2]-box[0]}x{box[3]-box[1]} origin={box[0]},{box[1]} n={img['frames']}"
        print(f"AUDIT {row['id']:<20s} FRONT {describe(front):<38s} BACK {describe(back)}")
    print('AUDIT_COUNT',len(rows))
if __name__=='__main__':main()
