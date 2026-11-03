"""Network helper for the Hub's multiplayer. HTTP stays out of the game's render loop.

The game and this process talk through small atomic files in one private folder:
start.txt and cmd-N.txt go in; state.txt and sync-N.txt come out. Each line is key<TAB>base64.
"""
from __future__ import annotations
import argparse,base64,hashlib,json,os,socket,sys,time,urllib.error,urllib.request
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import mp_server
TICK=0.2
def write_kv(path,values):
    raw=''.join(f"{k}\t{base64.b64encode(str(v).encode('utf8')).decode('ascii')}\n" for k,v in values.items())
    temporary=path.with_name(path.name+'.tmp');temporary.write_text(raw,encoding='ascii')
    for attempt in range(25):
        try:os.replace(temporary,path);return
        except PermissionError:time.sleep(.02)  # Windows refuses while the game is reading it.
    raise PermissionError(f'{path} stayed locked')
def read_kv(path):
    result={}
    for line in path.read_text(encoding='ascii').splitlines():
        key,_,value=line.partition('\t')
        if key:result[key]=base64.b64decode(value).decode('utf8')
    return result
def fingerprint(game):
    # Source files only: compiled .dat bytes are not needed to detect a different game.
    digest=hashlib.sha256()
    files=[game/'Game.exe',game/'Data/Scripts.rxdata',*sorted((game/'PBS').glob('*.txt')),*sorted(p for p in (game/'Plugins').rglob('*') if p.is_file() and p.suffix in ('.rb','.txt','.py'))]
    for path in files:
        if not path.is_file():continue
        raw=path.read_bytes()
        if path.suffix in ('.rb','.txt','.py'):raw=raw.replace(b'\r\n',b'\n')
        digest.update(path.relative_to(game).as_posix().encode());digest.update(hashlib.sha256(raw).digest())
    return digest.hexdigest()
def addresses():
    found=[]
    try:found=[info[4][0] for info in socket.getaddrinfo(socket.gethostname(),None,socket.AF_INET)]
    except OSError:pass
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as probe:
            probe.connect(('10.255.255.255',1));found.insert(0,probe.getsockname()[0])
    except OSError:pass
    seen=[]
    for address in found:
        if address not in seen and not address.startswith('127.'):seen.append(address)
    return seen
def parent_alive(pid):
    if not pid:return True
    if os.name!='nt':
        try:os.kill(pid,0);return True
        except OSError:return False
    import ctypes
    kernel=ctypes.windll.kernel32
    handle=kernel.OpenProcess(0x1000,False,pid)   # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:return False
    code=ctypes.c_ulong();kernel.GetExitCodeProcess(handle,ctypes.byref(code));kernel.CloseHandle(handle)
    return code.value==259   # STILL_ACTIVE
class HttpError(Exception):
    def __init__(self,message,code=''):
        super().__init__(message);self.code=code
class Api:
    def __init__(self,url):
        self.url=url.rstrip('/');self.token=None;self.room=None
        self.http=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def call(self,method,path,data=None):
        headers={'Content-Type':'application/json'}
        if self.token:headers['Authorization']='Bearer '+self.token
        raw=None if data is None else json.dumps(data).encode()
        try:
            with self.http.open(urllib.request.Request(self.url+path,raw,headers,method=method),timeout=5) as response:
                return json.loads(response.read(1_000_001))
        except urllib.error.HTTPError as error:
            try:body=json.loads(error.read(65536))
            except ValueError:body={}
            raise HttpError(body.get('message','Erro do servidor.'),body.get('error','http')) from None
class Session:
    def __init__(self,directory,game,parent=0):
        self.dir=directory;self.game=game;self.parent=parent;self.api=None;self.server=None;self.done=False
        self.next_cmd=1;self.pending={};self.delivered=set();self.status={'link':'connecting'};self.last=None
    def publish(self,**changes):
        self.status.update(changes)
        current=dict(self.status)
        if current!=self.last:write_kv(self.dir/'state.txt',current);self.last=current
    def enter(self,start):
        form={'protocol':mp_server.PROTOCOL,'compatibility':fingerprint(self.game),'name':start['name'],
              'team':start['team'].split('\n\n'),'preview':start['preview'].split('\n')}
        port=int(start.get('port') or mp_server.PORT)
        if start['mode']=='host':
            # The previous room stays open a few seconds so its opponent can read the result.
            for attempt in range(10):
                try:self.server=mp_server.start('0.0.0.0',port);break
                except OSError:time.sleep(1)
            else:raise HttpError(f'A porta {port} ja esta em uso. Feche outra sala aberta neste PC.')
            self.api=Api(f'http://127.0.0.1:{port}')
            form['format']=start['format']
            form['mechanics']={key:key in start.get('mechanics','').split(',') for key in mp_server.MECHANICS}
            view=self.api.call('POST','/v3/rooms',form)
            self.publish(addresses='\n'.join(addresses()),port=port)
        else:
            address=start['address'].strip()
            if ':' in address:address,port=address.rsplit(':',1);port=int(port)
            self.api=Api(f'http://{address}:{port}')
            hello=self.api.call('GET','/v3/hello')
            if hello.get('protocol')!=mp_server.PROTOCOL:raise HttpError('O servidor usa outra versao do multiplayer.')
            view=self.api.call('POST',f"/v3/rooms/{start['code'].strip().upper()}/join",form)
        self.api.token=view.pop('token');self.api.room=view['room'];self.take(view)
    def take(self,view):
        changes={'link':'up','room':view['room'],'state':view['state'],'you':view['you'],'format':view['format'],
                 'mechanics':','.join(k for k,v in view['mechanics'].items() if v),
                 'seconds':'' if view['secondsRemaining'] is None else int(view['secondsRemaining']+.999),
                 'reason':view.get('reason') or '','winner':'' if view.get('winner') is None else view['winner'],'picks':','.join(map(str,view['picks'] or []))}
        for i,player in enumerate(view['players']):
            changes.update({f'name{i}':player['name'],f'connected{i}':int(player['connected']),f'ready{i}':int(player['ready']),f'preview{i}':'\n'.join(player['preview'])})
        changes['players']=len(view['players'])
        if 'seed' in view:
            changes['seed']=view['seed']
            for i in range(2):changes[f'team{i}']='\n\n'.join(view['teams'][i])
        self.publish(**changes)
    def commands(self):
        while True:
            path=self.dir/f'cmd-{self.next_cmd}.txt'
            if not path.is_file():return
            command=read_kv(path);path.unlink();self.next_cmd+=1
            if command['op']=='select':
                self.take(self.api.call('POST',f'/v3/rooms/{self.api.room}/select',{'picks':[int(n) for n in command['picks'].split(',')]}))
            elif command['op']=='sync':
                entry={'n':int(command['n']),'label':command['label'],'hash':command['hash'],'choice':command.get('choice','')}
                self.pending[entry['n']]=entry
            elif command['op']=='leave':
                self.leave();self.done=True;return
    def leave(self):
        if self.api and self.api.token:
            try:self.api.call('POST',f'/v3/rooms/{self.api.room}/leave',{})
            except (OSError,HttpError,ValueError):pass
    def deliver(self,n,result):
        if result.get('ready'):
            write_kv(self.dir/f'sync-{n}.txt',{'a':result['choices'][0],'b':result['choices'][1]})
            self.pending.pop(n,None);self.delivered.add(n)
    def syncs(self):
        for n,entry in sorted(self.pending.items()):
            if not entry.get('sent'):
                self.deliver(n,self.api.call('POST',f'/v3/rooms/{self.api.room}/sync',{k:entry[k] for k in ('n','label','hash','choice')}));entry['sent']=True
            else:
                self.deliver(n,self.api.call('GET',f'/v3/rooms/{self.api.room}/sync/{n}'))
    def run(self):
        start=read_kv(self.dir/'start.txt')
        try:self.enter(start)
        except (OSError,HttpError,ValueError,KeyError) as error:
            detail=str(error) if isinstance(error,HttpError) else 'Nao foi possivel conectar. Confira o endereco, o firewall e se a sala esta aberta.'
            self.publish(link='failed',error=detail);return 1
        while not self.done:
            if not parent_alive(self.parent):self.leave();break
            try:
                self.commands()
                if self.done:break
                self.syncs()
                self.take(self.api.call('GET',f'/v3/rooms/{self.api.room}'))
            except HttpError as error:
                self.publish(error=str(error),errorCode=error.code)
                if error.code in ('room','auth'):
                    self.publish(link='failed');break
            except (OSError,ValueError):
                self.publish(link='down')
            time.sleep(TICK)
        if self.server:
            # Keep the room open long enough for the opponent to read the final state.
            time.sleep(5)
            self.server.shutdown();self.server.server_close()
        return 0
def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--dir',type=Path,required=True);parser.add_argument('--game',type=Path,required=True);parser.add_argument('--parent',type=int,default=0);args=parser.parse_args(argv)
    return Session(args.dir,args.game,args.parent).run()
if __name__=='__main__':raise SystemExit(main())
