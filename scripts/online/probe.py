"""Opt-in native feasibility probe. Normal launchers never install this plugin."""
from pathlib import Path
import argparse,hashlib,importlib.util,json
ROOT=Path(__file__).resolve().parents[2]
PLUGIN='ZZZZZZ Blue Online Probe'
def finalize(project,game):
    if (game/'Data/blue-online-engine-request.txt').exists():raise ValueError('The requested native probe has not completed yet.')
    report=(game/'Data/blue-online-engine-validation.txt').read_text(encoding='utf8')
    if not report.rstrip().endswith('RESULT=PASS'):raise ValueError('Native probe failed. Read game/Data/blue-online-engine-validation.txt.')
    catalog=json.loads((game/'Data/blue-online-catalog.json').read_text(encoding='utf8'))
    files=[game/'Game.exe',game/'Data/Scripts.rxdata',*sorted((game/'Data').glob('*.dat'))]
    files += [p for p in sorted((game/'Plugins').rglob('*')) if p.is_file() and p.suffix in ('.rb','.txt') and PLUGIN not in p.parts]
    exported=min((game/'Data/blue-online-catalog.json').stat().st_mtime_ns,(game/'Data/blue-online-engine-validation.txt').stat().st_mtime_ns)
    if any(p.stat().st_mtime_ns>exported for p in files):raise ValueError('Engine files changed after export. Run the native probe again.')
    digest=hashlib.sha256()
    for file in files:
        digest.update(file.relative_to(game).as_posix().encode());digest.update(b'\0')
        raw=file.read_bytes()
        if file.suffix in ('.rb','.txt'):raw=raw.replace(b'\r\n',b'\n')
        digest.update(hashlib.sha256(raw).digest())
    catalog['engineFingerprint']=digest.hexdigest()
    output=project/'.blue-work/online/catalog.json';output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(catalog,sort_keys=True,ensure_ascii=True)+'\n',encoding='ascii')
    return output
def prepare(project,game,only=False):
    spec=importlib.util.spec_from_file_location('blue_online_lab_prepare',project/'scripts/battle_lab/launch.py');lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
    lab.install(project,game)
    destination=game/'Plugins'/PLUGIN;destination.mkdir(parents=True,exist_ok=True)
    # Only files owned by this explicit experiment are written here.
    lab.atomic_write(destination/'EngineProbe.rb',(project/'scripts/online/EngineProbe.rb').read_bytes())
    lab.atomic_write(destination/'meta.txt',b'Name = Blue Online Engine Probe\nVersion = 0.1\nEssentials = 21.1\nScripts = EngineProbe.rb\n')
    lab.prepare_request(game,True)
    (game/'Data/blue-online-engine-request.txt').write_text('probe-only' if only else 'probe',encoding='ascii')
def cleanup(game):
    target=(game/'Plugins'/PLUGIN).resolve()
    if not target.is_relative_to(game.resolve()) or target.name!=PLUGIN:raise ValueError('Invalid probe folder.')
    if target.exists():
        files=list(target.iterdir())
        if any(not p.is_file() or p.name not in ('EngineProbe.rb','meta.txt') for p in files):raise ValueError('Unexpected files in probe folder; nothing removed.')
        for file in files:file.unlink()
        target.rmdir()
    request=game/'Data/blue-online-engine-request.txt'
    if request.is_file():request.unlink()
def main():
    parser=argparse.ArgumentParser(description=__doc__);mode=parser.add_mutually_exclusive_group();mode.add_argument('--finalize',action='store_true');mode.add_argument('--cleanup',action='store_true');parser.add_argument('--only',action='store_true');args=parser.parse_args()
    if args.finalize:print(finalize(ROOT,ROOT/'game'))
    elif args.cleanup:cleanup(ROOT/'game');print('Plugin opcional removido. Atalhos offline preservados.')
    else:prepare(ROOT,ROOT/'game',args.only);print('Abra game/Game.exe nos proximos 120 segundos. Depois execute este script com --finalize.')
if __name__=='__main__':main()
