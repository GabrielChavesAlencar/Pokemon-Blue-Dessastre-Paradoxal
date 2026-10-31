"""Install and launch Blue's opt-in battle sandbox using the local game."""
from __future__ import annotations
import argparse
from datetime import datetime
import os
from pathlib import Path
import shutil
import subprocess
import time
import sys
import zlib
import tempfile


def atomic_write(path: Path, data: bytes):
    fd,temp=tempfile.mkstemp(prefix='.blue-lab-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:
            stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)


def install(project: Path, game: Path) -> Path:
    game=game.resolve()
    for relative in ['Game.exe','Data/Scripts.rxdata']:
        if not (game/relative).is_file():
            raise RuntimeError(f'Base local incompleta: {game/relative}. Execute BAIXAR_BASE_DECADES.bat primeiro.')
    source=project/'scripts'/'battle_lab'
    plugin=game/'Plugins'/'ZZZZ Blue Battle Lab'
    plugin.mkdir(parents=True,exist_ok=True)
    backup=project/'.blue-backups'/'battle-lab'/datetime.now().strftime('%Y%m%dT%H%M%S%f')
    for name in ['BlueBattleLab.rb','meta.txt']:
        data=(source/name).read_bytes();target=plugin/name
        if target.is_file() and target.read_bytes()==data:continue
        if target.is_file():
            backup.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup/name)
        atomic_write(target,data)
    patch_bootstrap(project,game,backup)
    return game


def patch_bootstrap(project: Path, game: Path, backup: Path):
    sys.path.insert(0,str(project/'scripts'/'official_rules'))
    from prepare_restore import Marshal, RubyString, dump
    target=game/'Data'/'Scripts.rxdata'
    scripts=Marshal(target.read_bytes()).read()
    found=False
    for script in scripts:
        if script[1]!=b'Main':continue
        code=zlib.decompress(script[2]).decode('utf8')
        if '# BLUE_LAB_EARLY_DEBUG' in code:return
        already_installed='# BLUE_BATTLE_LAB_BOOTSTRAP' in code
        needle='PluginManager.runPlugins'
        if code.count(needle)!=1:raise RuntimeError('Bootstrap Main nao reconhecido. Nenhum script foi substituido.')
        hook = needle + "\n    # BLUE_BATTLE_LAB_BOOTSTRAP: opt-in; no campaign side effects\n    if File.file?('Data/blue-battle-lab-request.txt') && !defined?(BlueBattleLab)\n      load 'Plugins/ZZZZ Blue Battle Lab/BlueBattleLab.rb'\n    end"
        early="$DEBUG = true if File.file?('Data/blue-battle-lab-request.txt') && Time.now - File.mtime('Data/blue-battle-lab-request.txt') < 120 && ['play','smoke'].include?(File.read('Data/blue-battle-lab-request.txt').strip) # BLUE_LAB_EARLY_DEBUG\n    "
        replacement=early+(needle if already_installed else hook)
        script[2]=RubyString(zlib.compress(code.replace(needle,replacement).encode('utf8')))
        found=True
    if not found:raise RuntimeError('Main nao encontrado na base local.')
    backup.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup/'Scripts.rxdata')
    atomic_write(target,b'\x04\x08'+dump(scripts))


def prepare_request(game: Path, smoke: bool=False):
    (game/'Data'/'blue-battle-lab-request.txt').write_text('smoke' if smoke else 'play',encoding='ascii')


def launch(project: Path, game: Path, smoke: bool=False, timeout: float=120) -> int:
    game=install(project,game)
    log=game/'Data'/'blue-battle-lab.log'
    before=log.stat().st_size if log.exists() else 0
    env=os.environ.copy();env['BLUE_BATTLE_LAB']='1'
    if smoke:env['BLUE_BATTLE_LAB_SMOKE']='1'
    else:env.pop('BLUE_BATTLE_LAB_SMOKE',None)
    print('Abrindo a batalha real do jogo. O laboratorio nao carrega nem salva a campanha.',flush=True)
    print('Na primeira abertura, aguarde a compilacao dos plugins/PBS em modo debug.',flush=True)
    prepare_request(game,smoke)
    process=subprocess.Popen([str(game/'Game.exe'),'debug'],cwd=game,env=env)
    if not smoke:return 0
    deadline=time.monotonic()+timeout
    while process.poll() is None and time.monotonic()<deadline:time.sleep(.5)
    if process.poll() is None:
        process.terminate();process.wait(timeout=10)
        raise RuntimeError(f'Teste excedeu {timeout}s. Confira {log}.')
    output=log.read_bytes()[before:].decode('utf8',errors='replace') if log.exists() else ''
    print(output)
    if 'SMOKE=PASS' not in output:raise RuntimeError('O runtime nao confirmou as batalhas. Veja o log e mensagens do jogo.')
    return 0


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    project=Path(__file__).resolve().parents[2]
    parser.add_argument('--game-dir',type=Path,default=Path(os.environ.get('BLUE_GAME_DIR',project/'game')))
    parser.add_argument('--install-only',action='store_true')
    parser.add_argument('--prepare-only',action='store_true',help='Preparar uma abertura pelo Game.exe nos proximos 120 segundos.')
    parser.add_argument('--smoke-test',action='store_true')
    parser.add_argument('--timeout',type=float,default=120)
    args=parser.parse_args(argv)
    try:
        if args.install_only:install(project,args.game_dir);print('Plugin instalado.');return 0
        if args.prepare_only:
            game=install(project,args.game_dir);prepare_request(game,args.smoke_test);print('Pronto para abrir Game.exe.');return 0
        return launch(project,args.game_dir,args.smoke_test,args.timeout)
    except (OSError,RuntimeError) as error:
        print(f'[ERRO] {error}');return 1

if __name__=='__main__':raise SystemExit(main())
