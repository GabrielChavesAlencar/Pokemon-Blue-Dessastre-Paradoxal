"""Read trainer-event identities without executing event scripts or editing maps."""
from pathlib import Path
import hashlib
import json
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from server.ruby_marshal import loads,text,dumps_simple

CALL=re.compile(r'''TrainerBattle\.start\(\s*:([A-Z][A-Z0-9_]*)\s*,\s*(["'])((?:\\.|(?!\2).)*?)\2''')
GYMS=set('Marigold Reva Keegan Quinn Luis Luna Galen Christopher Atlas Sophia Hermes Cethin Keiko Roho Belinda Gohar Eira Azure Danny'.split())

def identities(commands):
    found=[]
    for command in commands:
        if command.attrs.get('@code') not in (111,355,655):continue
        for value in command.attrs.get('@parameters',[]):
            if not isinstance(value,bytes):continue
            for kind,quote,name in CALL.findall(text(value)):
                name=re.sub(r'\\([\\"\'])',r'\1',name)
                pair=[kind,name]
                if pair not in found:found.append(pair)
    return found

def event_row(event):
    name=text(event.attrs.get('@name'))
    if not re.match(r'Trainer\s*NPC\b',name,re.I):return None
    pages=event.attrs.get('@pages',[]);keys=[];graphic=None;switches=[]
    for page in pages:
        commands=page.attrs.get('@list',[])
        pairs=identities(commands)
        for pair in pairs:
            if pair[1].split(' (')[0] not in GYMS and pair not in keys:keys.append(pair)
        if pairs and graphic is None:graphic=page.attrs.get('@graphic')
        # Only import self-switches explicitly enabled in a victory's true branch.
        for i,command in enumerate(commands):
            if command.attrs.get('@code')!=111 or not identities([command]):continue
            depth=command.attrs.get('@indent',0)
            for child in commands[i+1:]:
                if child.attrs.get('@indent',0)<=depth:break
                args=child.attrs.get('@parameters',[])
                if child.attrs.get('@code')==123 and len(args)>1 and args[1]==0:
                    switch=text(args[0])
                    if switch in 'ABCD' and switch not in switches:switches.append(switch)
    if not keys:return None
    g=graphic.attrs if graphic else {}
    return [event.attrs['@id'],name,keys[0][0],keys[0][1],text(g.get('@character_name')),g.get('@character_hue',0),
            g.get('@direction',2),g.get('@pattern',0),keys,switches]

def load_data(path):return loads(path.read_bytes())

def build(project,game):
    info=game/'Data/MapInfos.rxdata'
    if not info.is_file():return None
    maps=sorted((game/'Data').glob('Map[0-9][0-9][0-9].rxdata'))
    signature=hashlib.sha256(Path(__file__).read_bytes())
    for path in [info,*maps]:
        stat=path.stat();signature.update(f'{path.name}:{stat.st_mtime_ns}:{stat.st_size}\n'.encode())
    key=signature.hexdigest();cache=project/'.blue-work/trainer-album-catalog.json'
    if cache.is_file():
        saved=json.loads(cache.read_text('utf8'))
        if saved.get('key')==key:return dumps_simple(saved['data'])
    infos=load_data(info);areas=[]
    for path in maps:
        map_id=int(path.stem[3:]);map_info=infos.get(map_id)
        if map_info is None:continue
        data=load_data(path)
        rows=[row for event in data.attrs.get('@events',{}).values() if (row:=event_row(event))]
        if rows:areas.append([map_id,text(map_info.attrs.get('@name')),sorted(rows,key=lambda r:r[0])])
    result=[1,areas];cache.parent.mkdir(parents=True,exist_ok=True)
    cache.write_text(json.dumps({'key':key,'data':result},ensure_ascii=False),'utf8')
    return dumps_simple(result)
