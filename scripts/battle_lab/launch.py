"""Install and launch Blue's native Battle Hub using the local game."""
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
import importlib.util

PLUGIN_FILES = ['BlueBattleLab.rb', 'Interface.rb', 'Teams.rb', 'HubData.rb', 'HubUI.rb', 'TeamPreview.rb', 'HubValidation.rb', 'Validation.rb', 'pokepaste.py', 'meta.txt']


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
            raise RuntimeError(f'Base local incompleta: {game/relative}. Execute INSTALAR_HUB.bat ou INSTALAR_JOGO.bat primeiro.')
    source=project/'scripts'/'battle_lab'
    plugin=game/'Plugins'/'ZZZZ Blue Battle Lab'
    plugin.mkdir(parents=True,exist_ok=True)
    backup=project/'.blue-backups'/'battle-lab'/datetime.now().strftime('%Y%m%dT%H%M%S%f')
    for name in PLUGIN_FILES:
        data=(source/name).read_bytes();target=plugin/name
        if target.is_file() and target.read_bytes()==data:continue
        if target.is_file():
            backup.mkdir(parents=True,exist_ok=True);shutil.copy2(target,backup/name)
        atomic_write(target,data)
    patch_bootstrap(project,game,backup)
    interpreter=Path(sys.executable).with_name('pythonw.exe')
    if not interpreter.is_file():interpreter=Path(sys.executable)
    config=(str(interpreter.resolve())+'\n').encode('utf8')
    config_path=game/'Data/blue-hub-python.txt'
    if not config_path.is_file() or config_path.read_bytes()!=config:atomic_write(config_path,config)
    options_installer=project/'scripts'/'battle_options'/'install.py'
    if options_installer.is_file():
        spec=importlib.util.spec_from_file_location('blue_battle_options_install',options_installer)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.install(project,game)
    ai_installer=project/'scripts'/'radical_ai'/'install.py'
    if ai_installer.is_file():
        spec=importlib.util.spec_from_file_location('blue_radical_ai_install',ai_installer)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.install(project,game,True)
    music_installer=project/'scripts'/'music'/'install.py'
    if music_installer.is_file():
        spec=importlib.util.spec_from_file_location('blue_music_install',music_installer)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.install(project,game)
    presentation_installer=project/'scripts'/'battle_polish'/'install.py'
    if presentation_installer.is_file():
        spec=importlib.util.spec_from_file_location('blue_presentation_install',presentation_installer)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.install(project,game)
    za_installer=project/'scripts'/'za_megas'/'install.py'
    if za_installer.is_file():
        spec=importlib.util.spec_from_file_location('blue_za_install',za_installer)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        module.install(project,game)
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


def read_log_since(path: Path, offset: int) -> str:
    if not path.is_file():return ''
    with path.open('rb') as stream:
        stream.seek(offset)
        return stream.read().decode('utf8',errors='replace')


def native_startup_error(path: Path, offset: int):
    # This native failure happens before Ruby starts. Do not confuse rescued
    # plugin warnings (such as require 'set') with a fatal engine failure.
    for line in read_log_since(path,offset).replace('\x00','').splitlines():
        if 'Error initializing PhysFS' in line:return line.strip()
    return None


def launch(project: Path, game: Path, smoke: bool=False, timeout: float=240) -> int:
    game=install(project,game)
    log=game/'Data'/'blue-battle-lab.log'
    before=log.stat().st_size if log.exists() else 0
    env=os.environ.copy();env['BLUE_BATTLE_LAB']='1'
    if smoke:env['BLUE_BATTLE_LAB_SMOKE']='1'
    else:env.pop('BLUE_BATTLE_LAB_SMOKE',None)
    print('Abrindo o Hub de Batalha. O Hub nao carrega nem salva a campanha.',flush=True)
    print('Na primeira abertura, aguarde a compilacao dos plugins/PBS em modo debug.',flush=True)
    prepare_request(game,smoke)
    engine_log=game/'Data'/'blue-battle-launcher.log'
    # Detach the GUI from the double-clicked CMD and retain startup diagnostics.
    flags=(subprocess.DETACHED_PROCESS|subprocess.CREATE_NEW_PROCESS_GROUP) if os.name=='nt' else 0
    with engine_log.open('ab') as stream:
        stream.write(f'\nBLUE LAUNCH | {datetime.now().isoformat()} | {sys.executable}\n'.encode('utf8'));stream.flush()
        engine_start=stream.tell()
        # The request enables Ruby's compiler/debug flag inside Main. Passing the
        # executable's separate 'debug' argument also creates a native console,
        # whose closure terminates the game and can obscure its actual window.
        process=subprocess.Popen([str(game/'Game.exe')],cwd=game,env=env,creationflags=flags,
                                 stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT)
        stream.write(f'PROCESS_ID={process.pid}\n'.encode('ascii'));stream.flush()
    deadline=time.monotonic()+timeout
    while process.poll() is None and time.monotonic()<deadline:
        fatal=native_startup_error(engine_log,engine_start)
        if fatal:
            process.terminate();process.wait(timeout=10)
            raise RuntimeError(f'O motor nao conseguiu inicializar o sistema de arquivos: {fatal}. Veja {engine_log}.')
        output=read_log_since(log,before)
        if not smoke and 'MENU_READY' in output:
            print('Hub aberto. Mantenha este CMD aberto enquanto joga; voce pode minimiza-lo.',flush=True)
            # Explorer/terminal launchers can put the process tree in a job
            # object. Detaching the GUI does not break that lifetime relation.
            # Retain the launcher until the user actually closes the game.
            status=process.wait()
            with engine_log.open('ab') as stream:stream.write(f'PROCESS_EXIT={status} HEX=0x{status & 0xffffffff:08X}\n'.encode('ascii'))
            if status!=0:raise RuntimeError(f'O jogo encerrou com codigo {status}. Veja {engine_log} e {log}.')
            return 0
        time.sleep(.5)
    if not smoke:
        output=read_log_since(log,before)
        if 'MENU_READY' in output:raise RuntimeError(f'O laboratorio iniciou e encerrou durante a abertura. Veja {log}.')
        raise RuntimeError(f'O jogo nao confirmou a abertura do laboratorio (saida={process.poll()}). Veja {engine_log} e {log}.')
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
    parser.add_argument('--export-campaign-reference',action='store_true',help='Exportar os perfis reais dos lideres durante a verificacao nativa.')
    parser.add_argument('--timeout',type=float,default=240)
    args=parser.parse_args(argv)
    try:
        if args.export_campaign_reference:
            if not args.smoke_test:raise ValueError('A exportacao requer --smoke-test para usar dados temporarios, sem carregar a campanha.')
            game=install(project,args.game_dir)
            atomic_write(game/'Data/blue-reference-export-request.txt',b'Export current Full Doubles campaign profiles.\n')
        if args.install_only:install(project,args.game_dir);print('Plugin instalado.');return 0
        if args.prepare_only:
            game=install(project,args.game_dir);prepare_request(game,args.smoke_test);print('Pronto para abrir Game.exe.');return 0
        return launch(project,args.game_dir,args.smoke_test,args.timeout)
    except (OSError,RuntimeError,ValueError) as error:
        print(f'[ERRO] {error}');return 1

if __name__=='__main__':raise SystemExit(main())
