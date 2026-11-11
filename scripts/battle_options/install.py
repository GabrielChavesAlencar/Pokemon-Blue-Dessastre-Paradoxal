"""Install only Blue's own Battle Mode / sprite quality plugin."""
from pathlib import Path
from datetime import datetime,timezone
import os,tempfile,shutil
FILES=['Rules.rb','ClassicStones.rb','Mechanics.rb','SpriteQuality.rb','ProceduralAnimation.rb','Menus.rb','Validation.rb','MechanicsValidation.rb','meta.txt']
def install(project,game):
    source=project/'scripts/battle_options';target=game/'Plugins/ZZZZ Blue Battle Options'
    plans={target/name:(source/name).read_bytes() for name in FILES}
    changed={p:b for p,b in plans.items() if not p.is_file() or p.read_bytes()!=b}
    backup=project/'.blue-backups'/('battle-options-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    previous={p:p.read_bytes() if p.is_file() else None for p in changed};written=[]
    for p,b in previous.items():
        if b is not None:backup.mkdir(parents=True,exist_ok=True);shutil.copy2(p,backup/p.name)
    def atomic(p,b):
        p.parent.mkdir(parents=True,exist_ok=True);fd,name=tempfile.mkstemp(dir=p.parent,prefix='.blue-options-')
        try:
            with os.fdopen(fd,'wb') as f:f.write(b);f.flush();os.fsync(f.fileno())
            os.replace(name,p)
        finally:
            if os.path.exists(name):os.unlink(name)
    try:
        for p,b in changed.items():atomic(p,b);written.append(p)
    except Exception:
        for p in reversed(written):
            if previous[p] is None:p.unlink()
            else:atomic(p,previous[p])
        raise
    return len(changed)
