"""Install the Blue modifications from a ZIP or checkout; the base is fetched separately."""
from pathlib import Path
import argparse,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
BASE_URL='https://github.com/HazyCrazy/Pokemon-Decades.git'
BASE_COMMIT='ff6091b23603b3298ad72a7584b02a51e1d01c0e'
def run(command,root,env=None):
    print('>', ' '.join(map(str,command)),flush=True)
    subprocess.run([str(x) for x in command],cwd=root,env=env,check=True)

def ensure_base(project,game):
    if (game/'Game.exe').is_file() and (game/'PBS/pokemon.txt').is_file():return
    git=shutil.which('git')
    if not git:raise RuntimeError('Instale Git para Windows e abra INSTALAR_JOGO.bat novamente.')
    marker=project/'.blue-work/base-download.json'
    if game.exists() and any(game.iterdir()):
        if not marker.is_file() or json.loads(marker.read_text())!={'target':str(game),'commit':BASE_COMMIT}:
            raise RuntimeError('Pasta game parcial/desconhecida. Preserve seus arquivos e instale em uma pasta nova.')
    marker.parent.mkdir(parents=True,exist_ok=True)
    marker.write_text(json.dumps({'target':str(game),'commit':BASE_COMMIT}),encoding='utf8')
    game.mkdir(parents=True,exist_ok=True)
    if not (game/'.git').exists():
        run([git,'init',game],project)
        run([git,'-C',game,'remote','add','origin',BASE_URL],project)
    run([git,'-C',game,'fetch','--depth','1','origin',BASE_COMMIT],project)
    run([git,'-C',game,'checkout','--detach',BASE_COMMIT],project)
    if not (game/'Game.exe').is_file():raise RuntimeError('O download da base nao contem Game.exe.')

def install(project,game):
    game=game.resolve();ensure_base(project,game)
    state_path=project/'.blue-work/installation.json'
    state=json.loads(state_path.read_text(encoding='utf8')) if state_path.is_file() else {}
    if state and state.get('game')!=str(game):raise ValueError('Estado de instalacao pertence a outra pasta do jogo.')
    state.setdefault('game',str(game))
    env={**os.environ,'BLUE_GAME_DIR':str(game),'PYTHONUTF8':'1'}
    # A completed rules restoration is not repeated over user-edited PBS.
    if not state.get('officialRules'):
        run([sys.executable,'scripts/official_rules/restore.py','--game-dir',game,'--apply'],project,env)
        state['officialRules']=True;state_path.parent.mkdir(parents=True,exist_ok=True)
        state_path.write_text(json.dumps(state,indent=2),encoding='utf8')
    run([sys.executable,'scripts/dessastre_paradoxal/install.py','--game-dir',game,'--apply'],project,env)
    run([sys.executable,'server/prepare_game.py'],project,env)
    run([sys.executable,'scripts/launch_game.py','--game-dir',game,'--prepare-only'],project,env)
    print('[OK] Instalado. Abra ABRIR_JOGO.bat para a campanha ou TESTAR_BATALHA.bat para o laboratorio.')
    print('Musicas MP3 particulares nao fazem parte do download. O jogo usa a trilha da base ate voce importar suas listas.')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game-dir',type=Path,default=ROOT/'game');parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    if not args.apply:
        print('Plano: baixar base Decades '+BASE_COMMIT+', restaurar regras oficiais, importar Dessastre Paradoxal e instalar plugins Blue.');print('Use --apply para instalar. Saves e backups existentes sao preservados.');return 0
    try:install(ROOT,args.game_dir);return 0
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError) as error:print('[ERRO]',error);print('A instalacao parou. Corrija a causa e execute novamente; os backups ficam em .blue-backups.');return 1
if __name__=='__main__':raise SystemExit(main())
