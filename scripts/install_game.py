"""Install the Blue modifications from a ZIP or checkout; the base is fetched separately."""
from pathlib import Path
import argparse,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/regions'))
from sinnoh_legacy_plugin_guard import assert_no_legacy_sinnoh_shared
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

def install(project,game,hub_only=False,allow_kanto_missing=False,skip_kanto=False):
    # CH04: do not modify a shared game containing standalone Sinnoh boot files.
    game=Path(game).resolve()
    assert_no_legacy_sinnoh_shared(game)
    # Even an older self-updating Blue-Story.exe downloads this Python entry
    # point from main. Install the editor shortcuts into the managed project
    # before game preparation (which can fail for unrelated region sources).
    if not hub_only:
        # O Blue-Story prepara a publicacao sem pedir PowerShell, BAT de login ou Git.
        # Falha de rede nao deve impedir de jogar/editar mapas localmente.
        try:
            from scripts.windows.github_cli import ensure_cli
            github_cli = ensure_cli(project)
            print('[JOHTO GITHUB] CLI pronta para publicar:', github_cli, flush=True)
        except (OSError, ValueError, RuntimeError, ImportError) as error:
            print('[JOHTO GITHUB] Publicacao indisponivel temporariamente:', error, flush=True)
        try:
            from scripts.windows.install_johto_editor import install as install_editor
            origin=os.environ.get('BLUE_STORY_LAUNCHER_DIR')
            editor=install_editor(project,Path(origin) if origin else None)
            print('[JOHTO EDITOR] Atalhos e codigo atualizados:',editor['installed'],flush=True)
            for issue in editor['warnings']:
                print('[JOHTO EDITOR] Pasta opcional indisponivel:',issue['directory'],issue['reason'],flush=True)
        except (OSError,ValueError,ImportError,KeyError) as error:
            print('[JOHTO EDITOR] Aviso: editor nao instalado:',error,flush=True)
    game=game.resolve();ensure_base(project,game)
    assert_no_legacy_sinnoh_shared(game)
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
    if hub_only:
        run([sys.executable,'scripts/battle_lab/launch.py','--game-dir',game,'--install-only'],project,env)
        print('[OK] Hub instalado. Abra HUB_DE_BATALHA.bat para jogar contra a IA.')
    else:
        # The website's Blue-Story.exe invokes this same installer after every
        # online update. First prepare Blue plugins so the Kanto map builder
        # can safely compile against the native Decades game.
        run([sys.executable,'scripts/launch_game.py','--game-dir',game,'--prepare-only'],project,env)
        import importlib.util
        kanto_path=project/'scripts/regions/auto_integrate_kanto.py'
        if skip_kanto:
            print('[KANTO AUTO] Ignorado apenas por --skip-kanto (QA/CI).',flush=True)
        elif kanto_path.is_file():
            spec=importlib.util.spec_from_file_location('blue_auto_integrate_kanto',kanto_path)
            auto=importlib.util.module_from_spec(spec);spec.loader.exec_module(auto)
            result=auto.integrate(project,game)
            print('[KANTO AUTO] Resultado:',result['status'],flush=True)
            if not result.get('ready') and not allow_kanto_missing:
                reason=result.get('reason','Consulte o relatorio da instalacao.')
                raise RuntimeError(
                    'KANTO NAO INSTALADO: '+reason+
                    '. O inicializador nao abrira o jogo como se a instalacao '
                    'estivesse completa. O diagnostico foi salvo em .blue-work/'
                    'kanto-install-status.json e kanto-install.log. '
                    'Feche o jogo e abra o Blue-Story.exe para tentar novamente.')
            if result['changed']:
                # Rebuild/merge the new regional PBS/plugin and reviewed pt-BR
                # overlay after the importer has committed its marker LAST.
                run([sys.executable,'scripts/launch_game.py','--game-dir',game,'--prepare-only'],project,env)
        else:
            if not allow_kanto_missing:
                raise RuntimeError('Modulo automatico de Kanto nao foi baixado pela revisao atual.')
            print('[KANTO AUTO] Modulo regional ausente. Iniciando apenas Decades.',flush=True)
        # Hoenn is an OPTIONAL local, audited import. Never prevent Decades/Kanto
        # startup when the private donor ZIP is absent, incompatible or unverified.
        # Build the 199 Hoenn maps against the CURRENT (possibly Kanto-integrated)
        # MapInfos/Tilesets, rather than copying an isolated QA game's save profile.
        if skip_kanto:
            print('[HOENN AUTO] Ignorado na preparação de QA/CI.',flush=True)
        else:
            hoenn_path=project/'scripts/regions/auto_integrate_hoenn.py'
            if hoenn_path.is_file():
                spec=importlib.util.spec_from_file_location('blue_auto_integrate_hoenn',hoenn_path)
                hoenn=importlib.util.module_from_spec(spec);spec.loader.exec_module(hoenn)
                result=hoenn.integrate(project,game)
                print('[HOENN AUTO] Resultado:',result['status'],flush=True)
                if not result['ready']:
                    print('[HOENN AUTO] Acesso no Game.exe principal permanece bloqueado:',result['reason'],flush=True)
                if result['changed']:
                    run([sys.executable,'scripts/launch_game.py','--game-dir',game,'--prepare-only'],project,env)
        # Johto: the local private OFFLINE12 source is NEVER copied raw.
        # A transactional experimental installer repairs its map data and
        # rebases into unused 600-699 IDs (700+ belongs to Hoenn). This is a
        # shared-save EARLY ACCESS build, not the final native-QA release.
        if not skip_kanto:
            johto_path=project/'scripts/regions/auto_integrate_johto.py'
            if johto_path.is_file():
                spec=importlib.util.spec_from_file_location('blue_auto_integrate_johto',johto_path)
                johto=importlib.util.module_from_spec(spec);spec.loader.exec_module(johto)
                result=johto.integrate(project,game)
                print('[JOHTO AUTO] Resultado:',result['status'],flush=True)
                if result.get('verification') == 'semantic_runtime_map_validation_not_native_gameplay_qa':
                    print('[JOHTO AUTO] 100 mapas estruturais verificados; edicoes do jogador preservadas. Game.exe nao testado.',flush=True)
                if result.get('bedroom_reason'):
                    print('[JOHTO EDITOR] Quarto:',result['bedroom_reason'],flush=True)
                if result.get('map_editor_warning'):
                    print('[JOHTO EDITOR] ATENCAO:',result['map_editor_warning'],flush=True)
                if not result['ready']:
                    print('[JOHTO AUTO] Johto ainda não inicia neste Game.exe:',result['reason'],
                          'Detalhes: .blue-work/johto-main-install-status.json',flush=True)
                elif result.get('native_qa') is False:
                    print('[JOHTO AUTO] Prévia Johto instalada: 100 mapas, não validada em gameplay real.',flush=True)
                    installed_hgss = result.get('hgss_status') == 'private_art_compiled'
                    changed_hgss = result.get('hgss_changed')
                    if installed_hgss or changed_hgss:
                        print('[JOHTO HGSS] Tilesets reais de autores aplicados em:',
                              result.get('hgss_maps', []),flush=True)
                    else:
                        print('[JOHTO HGSS] Novo visual de interiores ainda não aplicado:',
                              result.get('hgss_reason','PNGs/manifesto privados dos autores não disponíveis'),
                              'Veja docs/JOHTO_HGSS_INTERIORES_PRIVADOS.md',flush=True)
                if result.get('changed'):
                    # New Ruby plugin and regional PBS must be compiled by the
                    # native Game.exe before trainer battles can be tested.
                    run([sys.executable,'scripts/launch_game.py','--game-dir',game,'--prepare-only'],project,env)
        if not skip_kanto:
            from sinnoh_shared import integrate as integrate_sinnoh
            try:
                result = integrate_sinnoh(project, game)
                print('[SINNOH] Instalação compartilhada:', result['status'], flush=True)
            except (OSError, ValueError, KeyError, TypeError) as error:
                print('[SINNOH] Integração bloqueada:', error, flush=True)
            else:
                if result['changed']:
                    run([sys.executable,'scripts/launch_game.py','--game-dir',game,'--prepare-only'],project,env)
        print('[OK] Instalado. Abra ABRIR_JOGO.bat para a campanha ou HUB_DE_BATALHA.bat para o Hub.')
    print('As listas de musica compartilhadas do projeto foram aplicadas; cada batalha sorteia uma faixa da categoria.')

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game-dir',type=Path,default=ROOT/'game');parser.add_argument('--apply',action='store_true');parser.add_argument('--hub-only',action='store_true');parser.add_argument('--allow-kanto-missing',action='store_true',help='Permitir jogar apenas Decades quando Kanto falhar');parser.add_argument('--skip-kanto',action='store_true',help='Usar apenas ao preparar ambiente de QA/CI');args=parser.parse_args()
    if not args.apply:
        print('Plano: baixar base Decades '+BASE_COMMIT+', restaurar regras oficiais, importar Dessastre Paradoxal e instalar plugins Blue.');print('Use --apply para instalar. Saves e backups existentes sao preservados.');return 0
    try:install(ROOT,args.game_dir,args.hub_only,args.allow_kanto_missing,args.skip_kanto);return 0
    except (OSError,ValueError,RuntimeError,subprocess.CalledProcessError) as error:print('[ERRO]',error);print('A instalacao parou. Corrija a causa e execute novamente; os backups ficam em .blue-backups.');return 1
if __name__=='__main__':raise SystemExit(main())
