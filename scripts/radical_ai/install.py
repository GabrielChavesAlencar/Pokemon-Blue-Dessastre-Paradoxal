"""Install Blue's original CFRU-inspired policy without editing base AI or PBS."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile

PROJECT = Path(__file__).resolve().parents[2]
FILES = ['Policy.rb', 'Snapshot.rb', 'Scores.rb', 'Switches.rb', 'Integration.rb', 'Validation.rb', 'meta.txt']

def atomic(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.blue-ai-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data); stream.flush(); os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name): os.unlink(name)

def validate(config):
    if config.get('version') != 1: raise ValueError('Versao de configuracao desconhecida.')
    profiles = config.get('profiles', {})
    if set(profiles) != {'engine', 'normal', 'radical'} or config.get('defaultProfile') not in profiles:
        raise ValueError('Perfis de IA invalidos.')
    if not isinstance(config.get('trace'), bool): raise ValueError('trace deve ser booleano.')
    for profile in profiles.values():
        if not isinstance(profile.get('label'), str) or not profile['label']: raise ValueError('Perfil sem nome.')
        if type(profile.get('skill')) is not int or not 0 <= profile['skill'] <= 255: raise ValueError('Skill invalida.')
        if type(profile.get('strength')) not in (int, float) or not 0 <= profile['strength'] <= 1: raise ValueError('Forca invalida.')
        if not isinstance(profile.get('antiLoop'), bool): raise ValueError('antiLoop invalido.')
    expected={'ko','resistAll','revenge','wall','twoHit','faster','weak','faints','faintsButFaster'}
    weights=config.get('switchWeights', {})
    if set(weights) != expected or any(type(n) is not int or not -100 <= n <= 100 for n in weights.values()):
        raise ValueError('Pesos de troca invalidos.')
    return config

def ruby(value):
    if isinstance(value, dict): return '{'+', '.join(ruby(k)+' => '+ruby(v) for k,v in value.items())+'}'
    if isinstance(value, str): return "'"+value.replace('\\','\\\\').replace("'","\\'")+"'"
    if isinstance(value, bool): return 'true' if value else 'false'
    if isinstance(value, (int,float)): return str(value)
    raise ValueError('Tipo de configuracao nao suportado.')

def install(project: Path, game: Path, apply=False):
    project=project.resolve(); game=game.resolve()
    if not (game/'Data/Scripts.rxdata').is_file(): raise ValueError('Base local incompleta.')
    config=validate(json.loads((project/'data/radical-ai.json').read_text(encoding='utf8')))
    source=project/'scripts/radical_ai'; plugin=game/'Plugins/ZZZZZ Blue Radical AI'
    plan={plugin/name:(source/name).read_bytes() for name in FILES}
    generated='# Generated from data/radical-ai.json by the Blue installer.\nmodule BlueRadicalAI\n  CONFIG = '+ruby(config)+'\nend\n'
    plan[plugin/'000_Config.rb']=generated.encode('utf8')
    changed={p:b for p,b in plan.items() if not p.is_file() or p.read_bytes()!=b}
    result={'profile':config['defaultProfile'],'files':len(changed),'applied':False}
    if not apply or not changed: return result
    backup=project/'.blue-backups'/('radical-ai-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    before={p:p.read_bytes() if p.is_file() else None for p in changed}
    for p,old in before.items():
        if old is not None: atomic(backup/p.relative_to(game),old)
    cache=game/'Data/PluginScripts.rxdata'
    if cache.is_file():
        backup.mkdir(parents=True,exist_ok=True);shutil.copy2(cache,backup/cache.name)
    written=[]
    try:
        for p,data in changed.items(): atomic(p,data);written.append(p)
    except Exception:
        for p in reversed(written):
            if before[p] is None: p.unlink()
            else: atomic(p,before[p])
        raise
    return {**result,'applied':True,'backup':str(backup)}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir',type=Path,default=PROJECT/'game')
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    try: print(json.dumps(install(PROJECT,args.game_dir,args.apply),ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,KeyError) as error: print('[ERRO]',error);return 1

if __name__=='__main__': raise SystemExit(main())
