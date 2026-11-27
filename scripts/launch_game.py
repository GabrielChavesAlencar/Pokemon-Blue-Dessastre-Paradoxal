"""Prepare the campaign without enabling the isolated battle laboratory."""
from pathlib import Path
import argparse,importlib.util,os,shutil,sys,zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/official_rules'))
sys.path.insert(0,str(ROOT/'scripts/regions'))
from sinnoh_legacy_plugin_guard import assert_no_legacy_sinnoh_shared
from prepare_restore import Marshal,RubyString,dump

def prepare(project,game):
    # Guard BEFORE lab.install or Scripts.rxdata/compile writes.
    assert_no_legacy_sinnoh_shared(game)
    recovery=game/'Data/.blue-sinnoh-install.json'
    if recovery.exists() or recovery.is_symlink():
        raise ValueError('Execute o instalador Blue-Story para recuperar a instalação interrompida de Sinnoh.')
    spec=importlib.util.spec_from_file_location('blue_campaign_plugins',project/'scripts/battle_lab/launch.py')
    lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
    lab.install(project,game)
    target=game/'Data/Scripts.rxdata';rows=Marshal(target.read_bytes()).read()
    marker='# BLUE_CAMPAIGN_COMPILE_REQUEST'
    local_sinnoh=(game/'Data/blue-sinnoh-shared-local.txt').is_file()
    protection='# BLUE_CAMPAIGN_PRESERVE_SINNOH_MAPS'
    changed=False
    for row in rows:
        if row[1]!=b'Main':continue
        code=zlib.decompress(row[2]).decode('utf8')
        updated=code
        if marker not in updated:
            needle='PluginManager.runPlugins'
            if updated.count(needle)!=1:raise ValueError('Bootstrap Main nao reconhecido.')
            prefix="if File.file?('Data/blue-compile-request.txt') "+marker+"\n      $DEBUG = true\n      File.delete('Data/blue-compile-request.txt')\n    end\n    "
            updated=updated.replace(needle,prefix+needle)
        if local_sinnoh and protection not in updated:
            needle='    Compiler.main'
            if updated.count(needle)!=1:raise ValueError('Compilador da campanha nao reconhecido.')
            # Invoke the installed compiler chain after all plugins have loaded.
            guard=f'''    blue_campaign_compile = proc do
{needle}
    end
    if defined?(BlueSinnohSharedEvents)
      BlueSinnohSharedEvents.preserve_authored_maps(&blue_campaign_compile)
    else
      blue_campaign_compile.call
    end {protection}'''
            updated=updated.replace(needle,guard)
        if updated==code:break
        row[2]=RubyString(zlib.compress(updated.encode('utf8')))
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
