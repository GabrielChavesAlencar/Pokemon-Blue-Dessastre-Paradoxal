"""Version the maintainer's supplied playlists and additional tracks for every install."""
from pathlib import Path
import argparse,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'server'))
from server.music_editor import validate_audio

def publish(root,extra):
    old=json.loads((root/'data/battle-music-playlists.json').read_text('utf8'))
    config=json.loads((root/'game/Data/blue-music.json').read_text('utf8'))
    categories={key:list(rows) for key,rows in old['categories'].items()}
    for key,folder in {'trainer':'treinador','wild':'pokemons selvagens','gym':'lider ginasio'}.items():
        for path in sorted((extra/folder).iterdir()):
            if path.suffix.lower() not in ('.mp3','.ogg','.wav'):continue
            raw=path.read_bytes();validate_audio(raw,path.suffix.lower(),max_size=128_000_000)
            sha=hashlib.sha256(raw).hexdigest()
            if any(r['sha256']==sha for r in categories[key]):continue
            relative='BlueRandom/'+key+'/'+sha[:24]+path.suffix.lower()
            categories[key].append({'source':folder+'/'+path.name,'file':relative,'title':path.stem,'bytes':len(raw),'sha256':sha,'extraSource':str(path)})
    files=[]
    for key,rows in categories.items():
        for row in rows:
            source=Path(row.pop('extraSource')) if 'extraSource' in row else root/'game/Audio/BGM'/row['file']
            raw=source.read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256']
            asset='assets/music/'+row['sha256']+source.suffix.lower();destination=root/asset
            destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
            entry={'path':row['file'],'asset':asset,'title':row['title'],'bytes':len(raw),'sha256':row['sha256']}
            if len(raw)>6_000_000:
                entry['chunks']=[]
                for i,offset in enumerate(range(0,len(raw),1_000_000)):
                    part=asset+'.part-'+str(i).zfill(2);(root/part).write_bytes(raw[offset:offset+1_000_000]);entry['chunks'].append(part)
            files.append(entry)
        prior=config['global'].get(key,{})
        config['global'][key]={'mode':'random','track':'','tracks':[r['file'] for r in rows],'volume':prior.get('volume',100),'pitch':prior.get('pitch',100)}
    old['categories']=categories
    shared={'version':1,'files':files,'config':config,'gymTrainerTypes':old['gymTrainerTypes'],'gymTrainers':old['gymTrainers']}
    for path,data in [(root/'data/battle-music-playlists.json',old),(root/'data/shared-music.json',shared)]:
        path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n','utf8')
    return {'categories':{k:len(v) for k,v in categories.items()},'bytes':sum(r['bytes'] for r in files)}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--extra-source',type=Path,required=True)
    print(publish(ROOT,parser.parse_args().extra_source))
