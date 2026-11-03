"""Open two real game windows, let them fight each other over the local server and compare every turn.

Windows only, with the game installed (the Python test suite does not need this). Usage:
    python tests/multiplayer_e2e.py --format single --seeds 1 2 3
"""
from __future__ import annotations
import argparse,os,shutil,subprocess,sys,tempfile,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GAME=ROOT/'game'
sys.path.insert(0,str(ROOT/'scripts'/'battle_lab'))
SINGLE_A="""Charizard @ Charizardite Y
Ability: Blaze
Level: 50
EVs: 252 SpA / 4 SpD / 252 Spe
Timid Nature
- Flamethrower
- Air Slash
- Solar Beam
- Roost

Gengar @ Life Orb
Ability: Cursed Body
Level: 50
EVs: 252 SpA / 252 Spe
Timid Nature
- Shadow Ball
- Sludge Bomb
- Thunderbolt
- Hypnosis

Corviknight @ Leftovers
Ability: Pressure
Level: 50
EVs: 252 HP / 252 Def
Impish Nature
- Brave Bird
- U-turn
- Roost
- Iron Defense
"""
SINGLE_B="""Pikachu @ Light Ball
Ability: Static
Level: 50
EVs: 252 SpA / 252 Spe
Timid Nature
- Thunderbolt
- Volt Switch
- Surf
- Fake Out

Garchomp @ Choice Scarf
Ability: Rough Skin
Level: 50
EVs: 252 Atk / 252 Spe
Jolly Nature
- Earthquake
- Dragon Claw
- Stone Edge
- Fire Fang

Blissey @ Leftovers
Ability: Natural Cure
Level: 50
EVs: 252 HP / 252 SpD
Calm Nature
- Seismic Toss
- Soft-Boiled
- Thunder Wave
- Toxic
"""
DOUBLE_A=SINGLE_A+"""
Tyranitar @ Assault Vest
Ability: Sand Stream
Level: 50
EVs: 252 HP / 252 Atk
Adamant Nature
- Rock Slide
- Crunch
- Earthquake
- Fire Punch

Rotom-Wash @ Sitrus Berry
Ability: Levitate
Level: 50
EVs: 252 HP / 252 SpA
Modest Nature
- Hydro Pump
- Discharge
- Will-O-Wisp
- Protect

Whimsicott @ Focus Sash
Ability: Prankster
Level: 50
EVs: 252 HP / 252 Spe
Timid Nature
- Tailwind
- Moonblast
- Encore
- Helping Hand
"""
DOUBLE_B=SINGLE_B+"""
Incineroar @ Sitrus Berry
Ability: Intimidate
Level: 50
EVs: 252 HP / 252 Atk
Adamant Nature
- Flare Blitz
- Fake Out
- Knock Off
- Parting Shot

Gyarados @ Gyaradosite
Ability: Moxie
Level: 50
EVs: 252 Atk / 252 Spe
Jolly Nature
- Waterfall
- Dragon Dance
- Thunder Wave
- Protect

Amoonguss @ Rocky Helmet
Ability: Regenerator
Level: 50
EVs: 252 HP / 252 Def
Bold Nature
- Spore
- Rage Powder
- Sludge Bomb
- Protect
"""
def launch(role,folder,form,seed,anims,scenario=''):
    env={**os.environ,'BLUE_MP_TEST_SCENARIO':scenario,'BLUE_BATTLE_LAB':'1','BLUE_MP_TEST':role,'BLUE_MP_TEST_DIR':str(folder),'BLUE_MP_TEST_FORMAT':form,'BLUE_MP_TEST_SEED':str(seed),'BLUE_MP_TEST_ANIMS':'1' if anims else '0'}
    env.pop('BLUE_BATTLE_LAB_SMOKE',None)
    with (folder/f'console-{role}.txt').open('ab') as console:
        return subprocess.Popen([str(GAME/'Game.exe')],cwd=GAME,env=env,stdin=subprocess.DEVNULL,stdout=console,stderr=subprocess.STDOUT)
def dialogs(pids):
    # An engine error stops the game behind a message box; show what it says.
    import ctypes
    from ctypes import wintypes as w
    user=ctypes.windll.user32;found=[]
    callback=ctypes.WINFUNCTYPE(ctypes.c_bool,w.HWND,w.LPARAM)
    def text(handle):
        buffer=ctypes.create_unicode_buffer(4000);user.GetWindowTextW(handle,buffer,4000);return buffer.value
    def window(handle,_):
        owner=w.DWORD();user.GetWindowThreadProcessId(handle,ctypes.byref(owner))
        name=ctypes.create_unicode_buffer(64);user.GetClassNameW(handle,name,64)
        if owner.value in pids and user.IsWindowVisible(handle) and name.value!='SDL_app':
            parts=[text(handle)]
            def child(inner,_):
                parts.append(text(inner));return True
            user.EnumChildWindows(handle,callback(child),0)
            found.append(' / '.join(part for part in parts if part))
        return True
    user.EnumWindows(callback(window),0)
    return found
def compile_plugins(timeout=420):
    # A debug request makes one game recompile changed plugins; two at once would fight over the cache.
    subprocess.run([sys.executable,'-X','utf8',str(ROOT/'scripts/battle_lab/launch.py'),'--prepare-only'],check=True,stdout=subprocess.DEVNULL)
    with tempfile.TemporaryDirectory(prefix='blue-mp-compile-') as temporary:
        process=launch('compile',Path(temporary),'single',0,False)
        try:process.wait(timeout)
        except subprocess.TimeoutExpired:process.kill();raise SystemExit('A compilacao dos plugins excedeu o limite.')
def leaving(form,scenario,timeout):
    # The host gives up or closes the game on turn 2; the other player must get the win and a message.
    with tempfile.TemporaryDirectory(prefix='blue-mp-e2e-') as temporary:
        folder=Path(temporary);one,two=(SINGLE_A,SINGLE_B) if form=='single' else (DOUBLE_A,DOUBLE_B)
        (folder/'team-host.txt').write_text(one,encoding='utf8');(folder/'team-join.txt').write_text(two,encoding='utf8')
        processes=[launch(role,folder,form,1,False,scenario) for role in ('host','join')]
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline and processes[1].poll() is None:time.sleep(.5)
        for process in processes:
            if process.poll() is None:process.kill();process.wait(10)
        read=lambda role:(folder/f'result-{role}.txt').read_text(encoding='utf8').strip() if (folder/f'result-{role}.txt').is_file() else ''
        host,join=read('host'),read('join')
        print(f'{scenario}: host={host!r} join={join!r}',flush=True)
        passed=join.startswith('OK Vitoria') and (scenario=='quit' or host.startswith('OK Derrota'))
        if not passed:print('FALHOU:',scenario,flush=True)
        return passed
def match(form,seed,anims,timeout):
    with tempfile.TemporaryDirectory(prefix='blue-mp-e2e-') as temporary:
        folder=Path(temporary)
        one,two=(SINGLE_A,SINGLE_B) if form=='single' else (DOUBLE_A,DOUBLE_B)
        (folder/'team-host.txt').write_text(one,encoding='utf8');(folder/'team-join.txt').write_text(two,encoding='utf8')
        processes=[launch('host',folder,form,seed,anims),launch('join',folder,form,seed,anims)]
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline and any(p.poll() is None for p in processes):time.sleep(.5)
        for message in dialogs({p.pid for p in processes}):print('DIALOGO:',message[:1600],flush=True)
        for process in processes:
            if process.poll() is None:process.kill();process.wait(10)
        results={role:(folder/f'result-{role}.txt').read_text(encoding='utf8') if (folder/f'result-{role}.txt').is_file() else '(sem resultado)' for role in ('host','join')}
        traces={role:(folder/f'trace-{role}.txt').read_text(encoding='utf8').splitlines() if (folder/f'trace-{role}.txt').is_file() else [] for role in ('host','join')}
        problems=[]
        if not all(text.startswith('OK') for text in results.values()):problems.append(f'resultado: {results}')
        if not traces['host'] or len(traces['host'])!=len(traces['join']):problems.append(f"traces de tamanho {len(traces['host'])} e {len(traces['join'])}")
        for a,b in zip(traces['host'],traces['join']):  # Also useful when a match hit the time limit.
            if a!=b:
                problems.append(f'primeira diferenca:\n  host {a}\n  join {b}');break
        wins={role:text for role,text in results.items()}
        if not problems and ('Vitoria' in wins['host'])==('Vitoria' in wins['join']) and 'Empate' not in wins['host']+wins['join']:
            problems.append(f'os dois jogos discordam do vencedor: {wins}')
        joined=' '.join(traces['host'])
        seen=[name for name,mark in (('Mega',':CHARIZARD:2:'),('Mega',':CHARIZARD:3:'),('Mega',':GYARADOS:1:')) if mark in joined]
        print(f"{form} semente {seed}: {sorted(set(seen))} {len(traces['host'])} sincronizacoes; host={results['host'].strip()[:80]!r} join={results['join'].strip()[:80]!r}",flush=True)
        if problems:
            kept=Path(tempfile.gettempdir())/f'blue-mp-fail-{form}-{seed}'
            shutil.rmtree(kept,ignore_errors=True);shutil.copytree(folder,kept)
            print('FALHOU:','\n'.join(problems),f'\nArquivos em {kept}',flush=True)
        return not problems
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--format',choices=['single','double'],default='single');parser.add_argument('--seeds',type=int,nargs='+',default=[1]);parser.add_argument('--anims',action='store_true');parser.add_argument('--timeout',type=float,default=280);parser.add_argument('--leaving',action='store_true',help='Testar desistencia e jogo fechado no meio da partida.');args=parser.parse_args()
    if not (GAME/'Game.exe').is_file():parser.error('Instale o jogo primeiro (INSTALAR_HUB.bat).')
    compile_plugins()
    passed=[leaving(args.format,scenario,args.timeout) for scenario in ('forfeit','quit')] if args.leaving else [match(args.format,seed,args.anims,args.timeout) for seed in args.seeds]
    print('RESULT='+('PASS' if all(passed) else 'FAIL'),f'{sum(passed)}/{len(passed)}',flush=True)
    return 0 if all(passed) else 1
if __name__=='__main__':raise SystemExit(main())
