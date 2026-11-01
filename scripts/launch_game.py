"""Prepare the campaign without enabling the isolated battle laboratory."""
from pathlib import Path
import argparse,importlib.util,os,shutil,sys,zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/official_rules'))
from prepare_restore import Marshal,RubyString,dump

def prepare(project,game):
    spec=importlib.util.spec_from_file_location('blue_campaign_plugins',project/'scripts/battle_lab/launch.py')
    lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
    lab.install(project,game)
    target=game/'Data/Scripts.rxdata';rows=Marshal(target.read_bytes()).read()
    marker='# BLUE_CAMPAIGN_COMPILE_REQUEST'
    changed=False
    for row in rows:
        if row[1]!=b'Main':continue
        code=zlib.decompress(row[2]).decode('utf8')
        if marker in code:break
        needle='PluginManager.runPlugins'
        if code.count(needle)!=1:raise ValueError('Bootstrap Main nao reconhecido.')
        prefix="if File.file?('Data/blue-compile-request.txt') "+marker+"\n      $DEBUG = true\n      File.delete('Data/blue-compile-request.txt')\n    end\n    "
        row[2]=RubyString(zlib.compress(code.replace(needle,prefix+needle).encode('utf8')))
        from datetime import datetime,timezone
        backup=project/'.blue-backups'/('campaign-launch-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
        backup.mkdir(parents=True);shutil.copy2(target,backup/target.name)
        lab.atomic_write(target,b'\x04\x08'+dump(rows));changed=True;break
    else:raise ValueError('Main ausente.')
    cache=game/'Data/PluginScripts.rxdata';stamp=cache.stat().st_mtime if cache.is_file() else 0
    needs_plugins=any(p.stat().st_mtime>stamp for p in (game/'Plugins').rglob('*') if p.is_file() and p.suffix in ('.rb','.txt'))
    data=game/'Data/species.dat';data_stamp=data.stat().st_mtime if data.is_file() else 0
    needs_pbs=any(p.stat().st_mtime>data_stamp for p in (game/'PBS').glob('*.txt'))
    if changed or needs_plugins or needs_pbs:
        (game/'Data/blue-compile-request.txt').write_text('compile',encoding='ascii')
    # Opening the campaign explicitly cancels a pending, unconsumed lab request.
    request=game/'Data/blue-battle-lab-request.txt'
    if request.is_file():request.unlink()
    return {'compileRequested':changed or needs_plugins or needs_pbs,'game':str(game/'Game.exe')}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game-dir',type=Path,default=ROOT/'game');parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args()
    try:
        result=prepare(ROOT,args.game_dir.resolve());print('Campanha preparada. Aguarde a compilacao se for a primeira abertura.')
        if not args.prepare_only:
            if os.name!='nt':raise RuntimeError('Game.exe requer Windows.')
            os.startfile(result['game'])
        return 0
    except (OSError,RuntimeError,ValueError) as error:print('[ERRO]',error);return 1
if __name__=='__main__':raise SystemExit(main())
