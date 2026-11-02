"""Install Blue's original presentation/story plugin, with a local backup."""
from pathlib import Path
import importlib.util,os,tempfile
FILES=['Presentation.rb','Title.rb','Story.rb','Campaign.rb','Economy.rb','Balance.rb','IVSelectors.rb','items_blue_iv.txt','Shop.rb','Journey.rb','JourneyValidation.rb','Playability.rb','Locale.rb','UIValidation.rb','CampaignValidation.rb','FullPowerValidation.rb','Validation.rb','meta.txt']
SUPPORT=['leaders.py','leaders_full_power.json','champions.py']
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
    plans={(game/'PBS'/name if name.startswith('items_') else target/name):(source/name).read_bytes() for name in FILES}
    spec=importlib.util.spec_from_file_location('blue_leader_patch',source/'leaders.py')
    patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
    trainer_plan=patch.plan(project,game)
    plans.update(trainer_plan)
    if trainer_plan:plans[target/'leader-teams.tsv']=patch.validation_rows(patch.manifest(project))
    spec=importlib.util.spec_from_file_location('blue_champions_patch',source/'champions.py')
    champions=importlib.util.module_from_spec(spec);spec.loader.exec_module(champions)
    plans.update(champions.plan(project,game))
    locale=project/'scripts/localization/install.py'
    if locale.is_file():
        spec=importlib.util.spec_from_file_location('blue_locale_install',locale)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        plans.update(module.plan(project,game))
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
