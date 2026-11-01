"""Import local battle music pools. Audio stays local; only metadata is versioned."""
from __future__ import annotations
import argparse,hashlib,json,os,re,sys,tempfile
from pathlib import Path
from datetime import datetime,timezone
PROJECT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(PROJECT/'server'))
from ruby_marshal import dumps_simple
from music_editor import validate_audio,MusicError,EXTENSIONS
FOLDERS={'trainer':'batalha treinador','wild':'encontros selvagens','gym':'gym leader'}
MAX_FILE=128_000_000

def atomic(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    descriptor,name=tempfile.mkstemp(prefix='.blue-music-',dir=path.parent)
    try:
        with os.fdopen(descriptor,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)

def sections(raw):
    matches=list(re.finditer(r'^\[([^\]\r\n]+)\]',raw,re.M))
    return [(m[1],raw[m.end():matches[i+1].start() if i+1<len(matches) else len(raw)]) for i,m in enumerate(matches)]

def gym_categories(project,game):
    types=[]
    for file in sorted((game/'PBS').glob('trainer_types*.txt')):
        for id,body in sections(file.read_text(encoding='utf-8-sig')):
            name=re.search(r'^Name\s*=\s*([^\r\n]+)',body,re.M)
            if name and re.search(r'\bgym\s+leader\b',name[1],re.I):types.append(id)
    reference=project/'site/public/data/story-trainers.json'
    if not reference.is_file():raise ValueError('Referencia dos Mestres de Tipo ausente: '+str(reference))
    masters={row['name'] for row in json.loads(reference.read_text(encoding='utf8'))['masters']}
    pairs=set()
    for file in sorted((game/'PBS').glob('trainers*.txt')):
        for header,_ in sections(file.read_text(encoding='utf-8-sig')):
            if ',' not in header:continue
            id,name=header.split(',',1)
            name=re.sub(r'\s*\([^()]*\)\s*$','',name).strip()
            if name in masters:pairs.add((id.strip(),name))
    return sorted(set(types)),[list(row) for row in sorted(pairs)]

def build_plan(project,game,source):
    project=project.resolve();game=game.resolve();source=source.resolve()
    manifest={'version':1,'categories':{}}
    plans={}
    for category,folder in FOLDERS.items():
        directory=source/folder
        if not directory.is_dir():raise ValueError('Pasta de musicas ausente: '+str(directory))
        tracks=[]
        for file in sorted(directory.iterdir(),key=lambda p:p.name.casefold()):
            if not file.is_file():continue
            extension=file.suffix.lower()
            if extension not in EXTENSIONS:continue
            if not 0<file.stat().st_size<=MAX_FILE:raise ValueError('Arquivo vazio ou maior que 128 MB: '+file.name)
            raw=file.read_bytes()
            # Validation of the supplied MP3 headers is independent of web upload's
            # 20 MB limit. Files are copied without conversion or resampling.
            validate_audio(raw,extension,max_size=MAX_FILE)
            digest=hashlib.sha256(raw).hexdigest()
            relative=f'BlueRandom/{category}/{digest[:24]}{extension}'
            destination=(game/'Audio/BGM'/relative).resolve()
            if not destination.is_relative_to(game):raise ValueError('Destino de audio invalido.')
            plans[destination]=raw
            tracks.append({'source':folder+'/'+file.name,'file':relative,'title':file.stem,'bytes':len(raw),'sha256':digest})
        if not tracks:raise ValueError('Nenhuma musica compativel na pasta: '+folder)
        manifest['categories'][category]=tracks
    types,pairs=gym_categories(project,game)
    manifest['gymTrainerTypes']=types;manifest['gymTrainers']=pairs
    config_path=game/'Data/blue-music.json'
    config=json.loads(config_path.read_text(encoding='utf8')) if config_path.is_file() else {'version':1,'global':{},'maps':{}}
    if config.get('version')!=1 or not isinstance(config.get('global'),dict) or not isinstance(config.get('maps'),dict):raise ValueError('Configuracao de musicas invalida.')
    for category,tracks in manifest['categories'].items():
        previous=config['global'].get(category,{})
        volume=previous.get('volume',100);pitch=previous.get('pitch',100)
        if type(volume) is not int or not 0<=volume<=100 or type(pitch) is not int or not 50<=pitch<=150:raise ValueError('Volume/tom invalido na configuracao anterior.')
        config['global'][category]={'mode':'random','track':'','tracks':list(dict.fromkeys(row['file'] for row in tracks)),'volume':volume,'pitch':pitch}
    rows=lambda entries:[[key,v['mode'],v.get('tracks',[]) if v['mode']=='random' else v['track'],v['volume'],v['pitch']] for key,v in sorted(entries.items())]
    json_bytes=lambda obj:(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    plans[config_path]=json_bytes(config)
    plans[game/'Data/blue-music.rxdata']=dumps_simple([1,rows(config['global']),rows(config['maps'])])
    references=[[category,[row['file'] for row in tracks]] for category,tracks in manifest['categories'].items()]
    plans[game/'Data/blue-music-categories.rxdata']=dumps_simple([1,types,pairs,references])
    plans[game/'Data/blue-music-playlists.json']=json_bytes(manifest)
    plans[project/'data/battle-music-playlists.json']=json_bytes(manifest)
    for name in ['BlueMusic.rb','RandomValidation.rb','meta.txt']:
        plans[game/'Plugins/ZZZZ Blue Music'/name]=(project/'scripts/music'/name).read_bytes()
    return manifest,{p:b for p,b in plans.items() if not p.is_file() or p.read_bytes()!=b}

def install(project,game,source,apply=False):
    project=project.resolve();game=game.resolve()
    manifest,plans=build_plan(project,game,source)
    result={'categories':{k:len(v) for k,v in manifest['categories'].items()},'files':len(plans),'gymTypes':len(manifest['gymTrainerTypes']),'gymCharacters':len({p[1] for p in manifest['gymTrainers']}),'applied':False}
    if not apply or not plans:return result
    backup=project/'.blue-backups'/('random-music-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    previous={p:p.read_bytes() if p.is_file() else None for p in plans};written=[]
    for path,raw in previous.items():
        if raw is None:continue
        if path.is_relative_to(game):relative=Path('game')/path.relative_to(game)
        elif path.is_relative_to(project):relative=Path('project')/path.relative_to(project)
        else:raise ValueError('Destino fora do projeto e do jogo.')
        atomic(backup/relative,raw)
    try:
        for path,raw in plans.items():atomic(path,raw);written.append(path)
    except Exception:
        for path in reversed(written):
            if previous[path] is None:path.unlink()
            else:atomic(path,previous[path])
        raise
    return {**result,'applied':True,'backup':str(backup)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,default=Path.home()/'Downloads'/'musicas de pokemon')
    parser.add_argument('--game-dir',type=Path,default=PROJECT/'game')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    try:print(json.dumps(install(PROJECT,args.game_dir,args.source_dir,args.apply),ensure_ascii=True,indent=2));return 0
    except (ValueError,MusicError,OSError) as error:print('[ERRO]',error);return 1

if __name__=='__main__':raise SystemExit(main())
