"""Prepare/serve/test the opt-in native command bridge, separately from the Hub."""
from __future__ import annotations
import argparse,hashlib,importlib.util,json,secrets,shutil,threading,time,urllib.request,urllib.error
from pathlib import Path
try:from .rooms import Rooms
except ImportError:from rooms import Rooms
ROOT=Path(__file__).resolve().parents[2]
PLUGIN='ZZZZZZ Blue Native Turns'
OWNED={'EngineProbe.rb','TurnBridge.rb','meta.txt'}

def fingerprint(game):
    digest=hashlib.sha256()
    files=[game/'Game.exe',game/'Data/Scripts.rxdata',*sorted((game/'Data').glob('*.dat'))]
    files += [p for p in sorted((game/'Plugins').rglob('*')) if p.is_file() and p.suffix in ('.rb','.txt') and not any(part in (PLUGIN,'ZZZZZZ Blue Online Probe') for part in p.parts)]
    for p in files:
        digest.update(p.relative_to(game).as_posix().encode());raw=p.read_bytes()
        if p.suffix in ('.rb','.txt'):raw=raw.replace(b'\r\n',b'\n')
        digest.update(hashlib.sha256(raw).digest())
    return digest.hexdigest()

def roster(catalog,data=None):
    rooms=Rooms(catalog)
    if data is None:
        def team(species,ability,move):
            return [dict(species=species,ability=ability,item=None,nature='HARDY',moves=[move],ivs=[31]*6,evs=[0]*6,level=50) for _ in range(6)]
        data={'format':'double','teams':[team('PIKACHU','STATIC','THUNDERBOLT'),team('MAGIKARP','SWIFTSWIM','SPLASH')],'picks':[[0,1,2,3],[0,1,2,3]]}
    if set(data)!={'format','teams','picks'} or data['format'] not in ('single','double') or len(data['teams'])!=2 or len(data['picks'])!=2:raise ValueError('Use format, two teams of six and two selections of four.')
    lines=['BLUE_NATIVE_TURNS_1',data['format']]
    for side in range(2):
        team=rooms.validate_team(data['teams'][side]);picks=data['picks'][side]
        if not isinstance(picks,list) or len(picks)!=4 or any(type(i) is not int or not 0<=i<6 for i in picks) or len(set(picks))!=4:raise ValueError('Pick four different indexes between zero and five.')
        for i in picks:
            p=team[i]
            lines.append('\t'.join([str(side),p['species'],p['ability'],p['item'] or '-',p['nature'],','.join(p['moves']),','.join(map(str,p['ivs'])),','.join(map(str,p['evs']))]))
    return '\n'.join(lines)+'\n'

def prepare(project,game,catalog,teams=None):
    payload=roster(catalog,teams)
    spec=importlib.util.spec_from_file_location('blue_turns_lab',project/'scripts/battle_lab/launch.py');lab=importlib.util.module_from_spec(spec);spec.loader.exec_module(lab)
    lab.install(project,game)
    directory=game/'Data/blue-native-turns';directory.mkdir(exist_ok=True)
    known={'roster.tsv','state.json','state.json.tmp','command.tsv','command.tmp'}
    if any(p.is_symlink() or not p.is_file() or p.name not in known for p in directory.iterdir()):raise ValueError('Unexpected files in worker directory; preserve them before preparing another session.')
    backup=project/'.blue-backups'/('native-turns-'+secrets.token_hex(8));backup.mkdir(parents=True)
    for p in directory.iterdir():p.replace(backup/p.name)
    target=game/'Plugins'/PLUGIN;target.mkdir(parents=True,exist_ok=True)
    for name in OWNED-{'meta.txt'}:lab.atomic_write(target/name,(project/'scripts/online'/name).read_bytes())
    lab.atomic_write(target/'meta.txt',b'Name = Blue Native Turn Experiment\nVersion = 0.1\nEssentials = 21.1\nScripts = EngineProbe.rb,TurnBridge.rb\n')
    (directory/'roster.tsv').write_text(payload,encoding='ascii')
    session={'protocol':2,'directory':str(directory.resolve()),'compatibility':fingerprint(game),'tokens':[secrets.token_urlsafe(32),secrets.token_urlsafe(32)]}
    path=project/'.blue-work/online-turns/session.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(session),encoding='utf8')
    lab.prepare_request(game,True);(game/'Data/blue-native-turns-request.txt').write_text('turns',encoding='ascii')
    return path

def cleanup(game):
    target=(game/'Plugins'/PLUGIN).resolve()
    if not target.is_relative_to(game.resolve()) or target.name!=PLUGIN:raise ValueError('Invalid worker path.')
    if target.exists():
        files=list(target.iterdir())
        if any(p.is_symlink() or not p.is_file() or p.name not in OWNED for p in files):raise ValueError('Unexpected files in optional worker plugin.')
        for p in files:p.unlink()
        target.rmdir()
    request=game/'Data/blue-native-turns-request.txt'
    if request.exists():request.unlink()
    # Essentials can retain a removed plugin in its compiled cache. Preserve the cache,
    # then force one clean rebuild rather than leaving the experiment in offline startup.
    cache=game/'Data/PluginScripts.rxdata'
    if cache.exists():
        backup=game.parent/'.blue-backups'/('native-turns-cache-'+secrets.token_hex(8));backup.mkdir(parents=True)
        cache.replace(backup/cache.name)

class Client:
    def __init__(self,url,token,compatibility):self.url=url;self.token=token;self.compatibility=compatibility
    def call(self,path,data=None):
        raw=None if data is None else json.dumps(data).encode()
        request=urllib.request.Request(self.url+path,data=raw,headers={'Authorization':'Bearer '+self.token,'X-Blue-Compatibility':self.compatibility,'Content-Type':'application/json'})
        with urllib.request.urlopen(request,timeout=5) as response:return json.load(response)

def demo(session_path):
    try:from .turn_service import Turns,TurnServer
    except ImportError:from turn_service import Turns,TurnServer
    session=json.loads(session_path.read_text(encoding='utf8'));turns=Turns(session['directory'],session['compatibility'],session['tokens'])
    with TurnServer(('127.0.0.1',0),turns) as server:
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        clients=[Client(f'http://127.0.0.1:{server.server_port}',token,session['compatibility']) for token in session['tokens']]
        counts=[0,0];switched=False;deadline=time.monotonic()+170;seen=set();result=None
        print('Dois clientes HTTP aguardando a engine. Abra game/Game.exe agora.',flush=True)
        try:
            while time.monotonic()<deadline:
                for side,client in enumerate(clients):
                    state=client.call('/v2/state')
                    if state['state']=='failed':raise RuntimeError(state['error'])
                    if state['state']=='finished':result=state;break
                    r=state.get('request')
                    if not r or r['seq'] in seen:continue
                    option=0
                    if side==0 and not switched and r['kind']=='action':
                        choices=[i for i,o in enumerate(r['options']) if o['kind']=='switch']
                        if choices:option=choices[0];switched=True
                    command={'seq':r['seq'],'option':option}
                    client.call('/v2/command',command)
                    retry=client.call('/v2/command',command)
                    if not retry['replayed']:raise RuntimeError('Retry was not idempotent.')
                    seen.add(r['seq']);counts[side]+=1
                if result:break
                time.sleep(.015)
            if not result:raise RuntimeError('Native match did not finish before deadline.')
            if not all(counts) or not switched or result.get('winner')!=0:raise RuntimeError('Both clients, a voluntary switch and native victory must be observed.')
            report={'result':'PASS','winner':result['winner'],'turns':result['turn'],'httpCommands':counts,'nativeCommands':len(result['commands']),'voluntarySwitch':switched,'replacement':any(c['kind']=='replace' for c in result['commands'])}
            (session_path.parent/'http-validation.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report),flush=True)
            return report
        finally:server.shutdown();thread.join(timeout=5)

def main():
    p=argparse.ArgumentParser(description=__doc__);m=p.add_mutually_exclusive_group(required=True);m.add_argument('--prepare',action='store_true');m.add_argument('--cleanup',action='store_true');m.add_argument('--demo',action='store_true');p.add_argument('--catalog',type=Path,default=ROOT/'.blue-work/online/catalog.json');p.add_argument('--teams',type=Path);p.add_argument('--session',type=Path,default=ROOT/'.blue-work/online-turns/session.json');a=p.parse_args()
    if a.cleanup:cleanup(ROOT/'game');print('Worker opcional removido; cache anterior preservado para recompilação limpa.')
    elif a.demo:demo(a.session)
    else:
        catalog=json.loads(a.catalog.read_text(encoding='utf8'));data=json.loads(a.teams.read_text(encoding='utf8')) if a.teams else None
        print(prepare(ROOT,ROOT/'game',catalog,data));print('Inicie --demo e abra game/Game.exe em até 120 segundos. Nenhum atalho offline instala este worker.')
if __name__=='__main__':main()
