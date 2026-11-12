"""Install the original music adapter without touching maps or music assets."""
from pathlib import Path
from datetime import datetime,timezone
import os,tempfile,shutil,json,hashlib,sys

def shared_plan(project,game):
    path=project/'data/shared-music.json'
    if not path.is_file():return {}
    raw=path.read_bytes();digest=hashlib.sha256(raw).hexdigest();marker=game/'Data/blue-shared-music.sha256'
    if marker.is_file() and marker.read_text('ascii')==digest:return {}
    # A first install may create defaults, but an existing user configuration
    # always wins over later shared-music releases and regional add-ons.
    if (game/'Data/blue-music.json').is_file() or (game/'Data/blue-music.rxdata').is_file():return {}
    data=json.loads(raw);plan={}
    if data.get('version')!=1:raise ValueError('Invalid shared music version.')
    for row in data['files']:
        sources=[(project/name).resolve() for name in row.get('chunks',[row['asset']])];target=(game/'Audio/BGM'/row['path']).resolve()
        if not sources or not all(p.is_relative_to((project/'assets/music').resolve()) for p in sources) or not target.is_relative_to((game/'Audio/BGM').resolve()):raise ValueError('Invalid shared music path.')
        audio=b''.join(source.read_bytes() for source in sources)
        if hashlib.sha256(audio).hexdigest()!=row['sha256']:raise ValueError('Shared music checksum failed: '+row['asset'])
        plan[target]=audio
    sys.path.insert(0,str(project))
    from server.ruby_marshal import dumps_simple
    config=data['config'];rows=lambda entries:[[key,v['mode'],v.get('tracks',[]) if v['mode']=='random' else v.get('track',''),v['volume'],v['pitch']] for key,v in sorted(entries.items())]
    plan[game/'Data/blue-music.json']=(json.dumps(config,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    plan[game/'Data/blue-music.rxdata']=dumps_simple([1,rows(config['global']),rows(config['maps'])])
    pools=[[key,value.get('tracks',[])] for key,value in config['global'].items() if key in ('trainer','wild','gym')]
    plan[game/'Data/blue-music-categories.rxdata']=dumps_simple([1,data['gymTrainerTypes'],data['gymTrainers'],pools])
    plan[marker]=digest.encode('ascii')
    return plan

def install(project,game):
    source=project/'scripts/music';plugin=game/'Plugins/ZZZZ Blue Music'
    plan={plugin/name:(source/name).read_bytes() for name in ['BlueMusic.rb','RandomValidation.rb','meta.txt']}
    plan.update(shared_plan(project,game))
    # Recompile only the regional mapping for an already-integrated Kanto.
    # The generated file is separate from blue-music.json/rxdata.
    import importlib.util
    spec=importlib.util.spec_from_file_location('blue_kanto_music_compile',source/'compile_kanto_music.py')
    regional=importlib.util.module_from_spec(spec);spec.loader.exec_module(regional)
    plan.update(regional.plan_installed(project,game))
    changed={p:b for p,b in plan.items() if not p.is_file() or p.read_bytes()!=b}
    backup=project/'.blue-backups'/('music-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    for path,raw in changed.items():
        if path.is_file():
            old=backup/path.relative_to(game);old.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,old)
        path.parent.mkdir(parents=True,exist_ok=True)
        fd,name=tempfile.mkstemp(dir=path.parent,prefix='.blue-music-')
        try:
            with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
            os.replace(name,path)
        finally:
            if os.path.exists(name):os.unlink(name)
    return len(changed)

if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]
    print('Arquivos de musica atualizados:',install(root,root/'game'))
