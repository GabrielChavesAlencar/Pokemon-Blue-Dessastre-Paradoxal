"""Install Blue's original presentation/story plugin, with a local backup."""
from pathlib import Path
import os,tempfile
FILES=['Presentation.rb','Title.rb','Story.rb','Campaign.rb','Economy.rb','Shop.rb','CampaignValidation.rb','Validation.rb','meta.txt']
def atomic(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='.blue-polish-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)
def install(project,game):
    from datetime import datetime,timezone
    source=project/'scripts/battle_polish';target=game/'Plugins/ZZZZ Blue Story and Presentation'
    plans={target/name:(source/name).read_bytes() for name in FILES}
    changed={p:b for p,b in plans.items() if not p.is_file() or p.read_bytes()!=b}
    backup=project/'.blue-backups'/('story-presentation-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    previous={p:p.read_bytes() if p.is_file() else None for p in changed};written=[]
    for p,b in previous.items():
        if b is not None:atomic(backup/p.name,b)
    try:
        for p,b in changed.items():atomic(p,b);written.append(p)
    except Exception:
        for p in reversed(written):
            if previous[p] is None:p.unlink()
            else:atomic(p,previous[p])
        raise
    return len(changed)
if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]
    print('Arquivos atualizados:',install(root,root/'game'))
