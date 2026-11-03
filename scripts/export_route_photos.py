"""Request/import the real Habitat Dex map renderer's per-location captures."""
from pathlib import Path
import argparse
import hashlib
import json
import struct
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server.ruby_marshal import loads,dumps_simple
ROOT=Path(__file__).resolve().parents[1]

def normalize(value):
    if isinstance(value,bytes):return value.decode('utf8')
    if isinstance(value,list):return [normalize(v) for v in value]
    return value

def prepare(root):
    areas=json.loads((root/'site/public/data/locations.json').read_text('utf8'))['locations']
    path=root/'game/Data/blue-route-captures-request.dat'
    path.write_bytes(dumps_simple([[a['id'],a['name']] for a in areas]))
    return len(areas)

def import_photos(root):
    data=normalize(loads((root/'game/Data/blue-route-captures.dat').read_bytes()))
    if not isinstance(data,list) or len(data)!=3 or data[0]!=1:raise ValueError('Invalid native route captures.')
    source=root/'game/Data/blue-route-captures';target=root/'site/public/assets/route-maps'
    regions=root/'site/public/data/region-points.json';manifest=json.loads(regions.read_text('utf8'))
    areas={a['id']:a for a in json.loads((root/'site/public/data/locations.json').read_text('utf8'))['locations']}
    images=manifest.setdefault('areaImages',{});seen=set();plans=[]
    for id,name,file,region,x,y,width,height in data[1]:
        if id in seen or id not in areas or file!=f'route-{id}.png':raise ValueError('Invalid capture identity.')
        raw=(source/file).read_bytes()
        if (width,height)!=(480,274) or len(raw)<24 or raw[:8]!=b'\x89PNG\r\n\x1a\n' or raw[12:16]!=b'IHDR' or struct.unpack('>II',raw[16:24])!=(width,height):raise ValueError('Invalid capture PNG.')
        seen.add(id);plans.append((file,raw))
        images[str(id)]={'src':'/assets/route-maps/'+file,'kind':'habitat-region-capture','name':name,
            'mapId':id,'region':region,'point':[x,y],'zoom':3,'highlightColor':'#ff3679','width':width,'height':height,
            'sha256':hashlib.sha256(raw).hexdigest()}
    missing={row[0] for row in data[2]}
    if seen & missing or seen|missing!=set(areas):raise ValueError('Native export does not cover every listed area.')
    # The user requested hiding removed legacy maps, without deleting their data.
    manifest['inactiveAreaIds']=sorted(missing)
    manifest['captureSource']='Local Habitat Dex renderer; regional map at 3x; selected area highlighted in pink; no player marker.'
    target.mkdir(parents=True,exist_ok=True)
    for file,raw in plans:(target/file).write_bytes(raw)
    regions.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf8')
    return len(seen),len(missing)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',action='store_true');args=parser.parse_args()
    print('Captures requested:',prepare(ROOT)) if args.prepare else print('Captured / hidden legacy:',import_photos(ROOT))
