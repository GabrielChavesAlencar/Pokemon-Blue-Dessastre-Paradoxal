"""Install the original music adapter without touching maps or music assets."""
from pathlib import Path
from datetime import datetime,timezone
import os,tempfile,shutil

def install(project,game):
    source=project/'scripts/music';plugin=game/'Plugins/ZZZZ Blue Music'
    plan={plugin/name:(source/name).read_bytes() for name in ['BlueMusic.rb','meta.txt']}
    changed={p:b for p,b in plan.items() if not p.is_file() or p.read_bytes()!=b}
    backup=project/'.blue-backups'/('music-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    for path,raw in changed.items():
        if path.is_file():backup.mkdir(parents=True,exist_ok=True);shutil.copy2(path,backup/path.name)
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
