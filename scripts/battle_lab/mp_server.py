"""Multiplayer rooms and lockstep barrier (protocol 3). Runs inside the host's helper or standalone.

Both games simulate the same battle from one seed. The server never computes damage: it hides
each decision until both sides reached the same sync point and compares the two state hashes.
"""
from __future__ import annotations
import argparse,copy,json,os,re,secrets,threading,time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
PROTOCOL=3
PORT=8793
PICK_SECONDS=60
DECISION_SECONDS=180
DISCONNECT_SECONDS=45
ALPHABET='ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
MECHANICS=('mega','zmove','tera','dynamax')
class ProtocolError(Exception):
    def __init__(self,code,message,status=400):
        super().__init__(message);self.code=code;self.status=status
def reject(code,message,status=400):raise ProtocolError(code,message,status)
def short_text(value,limit):return isinstance(value,str) and 0<len(value)<=limit

class Rooms:
    def __init__(self,clock=time.monotonic,max_rooms=64):
        self.clock=clock;self.max_rooms=max_rooms;self.rooms={};self.lock=threading.RLock()
    def hello(self):return {'protocol':PROTOCOL,'name':'Blue multiplayer'}
    def _player(self,data):
        if not isinstance(data,dict) or data.get('protocol')!=PROTOCOL or type(data.get('protocol')) is not int:reject('protocol','Versao de protocolo incompativel. Atualize o Hub.',409)
        name=data.get('name')
        if not short_text(name,24) or not name.strip() or any(ord(c)<32 or c in '<>&' for c in name):reject('name','Nome invalido.')
        team,preview=data.get('team'),data.get('preview')
        if not isinstance(team,list) or not 1<=len(team)<=6 or not all(short_text(m,2048) for m in team):reject('team','Envie de 1 a 6 Pokemon.')
        if not isinstance(preview,list) or len(preview)!=len(team) or not all(short_text(s,64) for s in preview):reject('team','Previa do time invalida.')
        if not short_text(data.get('compatibility'),64):reject('compatibility','Versao do jogo ausente.')
        return {'name':name.strip(),'team':list(team),'preview':list(preview),'token':secrets.token_urlsafe(32),'picks':None,'timeout':False,'seen':self.clock(),'next':0,'compatibility':data['compatibility']}
    def _finish(self,room,reason,winner=None):
        room.update(state='finished',reason=reason,winner=winner);room.setdefault('closed',self.clock())
    def _prepare(self,room):
        room.update(state='prepared',seed=secrets.randbits(63),deadline=None)
    def _advance(self,room):
        now=self.clock()
        if room['state']=='selecting' and now>=room['deadline']:
            for player in room['players']:
                if player['picks'] is None:player['picks']=[0,1,2,3];player['timeout']=True
            self._prepare(room)
        if room['state']=='prepared':
            for slot in room['syncs'].values():
                if slot['first'] is not None and sum(e is not None for e in slot['entries'])==1 and now-slot['first']>=DECISION_SECONDS:
                    return self._finish(room,'timeout',0 if slot['entries'][0] else 1)
            gone=[i for i,p in enumerate(room['players']) if now-p['seen']>=DISCONNECT_SECONDS]
            if len(gone)==1:return self._finish(room,'disconnect',1-gone[0])
            if gone:return self._finish(room,'disconnect')
        idle=now-max(p['seen'] for p in room['players'])
        if room['state'] in ('waiting','selecting') and (now-room['created']>=1800 or idle>=600):room['state']='expired';room.setdefault('closed',now)
    def sweep(self):
        with self.lock:
            for code,room in list(self.rooms.items()):
                self._advance(room)
                if 'closed' in room and self.clock()-room['closed']>=120:del self.rooms[code]
    def _room(self,code):
        room=self.rooms.get(code)
        if room is None:reject('room','Sala inexistente. Confira o codigo.',404)
        self._advance(room);return room
    def _auth(self,room,token):
        if not isinstance(token,str) or len(token)>128:reject('auth','Token invalido.',401)
        for i,player in enumerate(room['players']):
            if secrets.compare_digest(player['token'],token):return i,player
        reject('auth','Token invalido.',401)
    def _view(self,code,room,index):
        own=room['players'][index];now=self.clock()
        view={'room':code,'state':room['state'],'you':index,'format':room['format'],'mechanics':copy.deepcopy(room['mechanics']),
              'secondsRemaining':max(0,room['deadline']-now) if room['deadline'] is not None else None,'picks':copy.deepcopy(own['picks']),'timedOut':own['timeout'],
              'reason':room.get('reason'),'winner':room.get('winner'),
              'players':[{'name':p['name'],'connected':now-p['seen']<15,'ready':p['picks'] is not None,'preview':list(p['preview'])} for p in room['players']]}
        if room.get('seed') is not None:
            # Lockstep needs the chosen Pokemon on both machines, but never the benched ones.
            view['seed']=room['seed']
            view['teams']=[[p['team'][i] for i in p['picks']] if p['picks'] is not None else list(p['team']) for p in room['players']]
            view['previews']=[[p['preview'][i] for i in p['picks']] if p['picks'] is not None else list(p['preview']) for p in room['players']]
        return view
    def create(self,data):
        with self.lock:
            self.sweep()
            if len(self.rooms)>=self.max_rooms:reject('capacity','Limite temporario de salas atingido.',503)
            player=self._player(data)
            form=data.get('format');mechanics=data.get('mechanics')
            if form not in ('single','double'):reject('format','Formato desconhecido.')
            if not isinstance(mechanics,dict) or set(mechanics)!=set(MECHANICS) or any(type(v) is not bool for v in mechanics.values()):reject('mechanics','Mecanicas invalidas.')
            if form=='double' and len(player['team'])!=6:reject('team','Duplas exigem seis Pokemon.')
            while True:
                code=''.join(secrets.choice(ALPHABET) for _ in range(6))
                if code not in self.rooms:break
            room={'players':[player],'created':self.clock(),'state':'waiting','deadline':None,'format':form,'mechanics':dict(mechanics),'syncs':{}}
            self.rooms[code]=room
            return {**self._view(code,room,0),'token':player['token']}
    def join(self,code,data):
        with self.lock:
            room=self._room(code)
            if room['state']!='waiting' or len(room['players'])!=1:reject('phase','Esta sala nao aceita mais participantes.',409)
            player=self._player(data)
            if player['compatibility']!=room['players'][0]['compatibility']:reject('compatibility','Os dois jogos tem versoes diferentes. Atualizem o Hub e tentem de novo.',409)
            if room['format']=='double' and len(player['team'])!=6:reject('team','Esta sala e de duplas: prepare seis Pokemon.')
            room['players'].append(player)
            if room['format']=='double':room.update(state='selecting',deadline=self.clock()+PICK_SECONDS)
            else:self._prepare(room)
            return {**self._view(code,room,1),'token':player['token']}
    def state(self,code,token):
        with self.lock:
            room=self._room(code);i,player=self._auth(room,token)
            player['seen']=self.clock()
            return self._view(code,room,i)
    def select(self,code,token,picks):
        with self.lock:
            room=self._room(code);i,player=self._auth(room,token)
            if not isinstance(picks,list) or len(picks)!=4 or any(type(n) is not int or not 0<=n<=5 for n in picks) or len(set(picks))!=4:reject('picks','Escolha quatro indices diferentes de 0 a 5.')
            if player['picks']==picks:return self._view(code,room,i)
            if room['state']!='selecting' or player['picks'] is not None:reject('phase','Selecao encerrada ou ja confirmada.',409)
            player['picks']=list(picks)
            if all(p['picks'] is not None for p in room['players']):self._prepare(room)
            return self._view(code,room,i)
    def sync(self,code,token,data):
        with self.lock:
            room=self._room(code);i,player=self._auth(room,token)
            if not isinstance(data,dict) or set(data)!={'n','label','hash','choice'}:reject('sync','Campos invalidos.')
            n,label,digest,choice=data['n'],data['label'],data['hash'],data['choice']
            if type(n) is not int or not 0<=n<=20000 or not short_text(label,32) or not short_text(digest,64) or not isinstance(choice,str) or len(choice)>512:reject('sync','Valores invalidos.')
            entry={'label':label,'hash':digest,'choice':choice}
            slot=room['syncs'].get(n)
            if slot and slot['entries'][i] is not None:
                if slot['entries'][i]!=entry:reject('replay','Decisao ja confirmada.',409)
                return self._result(room,n,i)
            if n!=player['next']:reject('order','Fora de ordem.',409)
            if room['state']!='prepared':return self._result(room,n,i)
            slot=room['syncs'].setdefault(n,{'entries':[None,None],'first':self.clock()})
            slot['entries'][i]=entry;player['next']=n+1
            if all(slot['entries']):
                a,b=slot['entries']
                if a['label']!=b['label'] or a['hash']!=b['hash']:
                    room['desync']={'n':n,'labels':[a['label'],b['label']],'hashes':[a['hash'],b['hash']]}
                    self._finish(room,'desync')
                elif label=='end':self._finish(room,'complete')
            return self._result(room,n,i)
    def _result(self,room,n,index):
        slot=room['syncs'].get(n)
        value={'n':n,'state':room['state'],'reason':room.get('reason'),'winner':room.get('winner'),'ready':False}
        if room.get('desync'):value['desync']=copy.deepcopy(room['desync'])
        if slot and all(slot['entries']) and not room.get('desync'):
            value.update(ready=True,choices=[e['choice'] for e in slot['entries']])
        return value
    def wait(self,code,token,n):
        with self.lock:
            room=self._room(code);i,player=self._auth(room,token)
            player['seen']=self.clock()
            return self._result(room,n,i)
    def leave(self,code,token):
        with self.lock:
            room=self._room(code);i,_=self._auth(room,token)
            if room['state']=='prepared':self._finish(room,'forfeit',1-i)
            elif room['state'] in ('waiting','selecting'):room['state']='cancelled';room.setdefault('closed',self.clock())
            return self._view(code,room,i)

class Server(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=os.name!='nt'  # On Windows this would let two rooms share the port silently.
    def __init__(self,address,rooms):
        self.rooms=rooms;self.slots=threading.BoundedSemaphore(32);super().__init__(address,Handler)
    def process_request(self,request,client_address):
        if not self.slots.acquire(blocking=False):request.close();return
        try:super().process_request(request,client_address)
        except BaseException:self.slots.release();raise
    def process_request_thread(self,request,client_address):
        try:super().process_request_thread(request,client_address)
        finally:self.slots.release()
    def service_actions(self):self.rooms.sweep()
class Handler(BaseHTTPRequestHandler):
    server_version='BlueMultiplayer/3';sys_version=''
    def setup(self):super().setup();self.connection.settimeout(5)
    def log_message(self,*args):pass  # Never write bearer tokens or private team payloads to logs.
    def reply(self,status,value):
        raw=json.dumps(value,ensure_ascii=True,separators=(',',':')).encode()
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
    def dispatch(self):
        try:
            if self.headers.get('Origin') is not None:raise ProtocolError('origin','Esta API nao aceita chamadas de paginas web.',403)
            if self.command=='GET' and self.path=='/v3/hello':return self.reply(200,self.server.rooms.hello())
            match=re.fullmatch(r'/v3/rooms(?:/([A-Z2-9]{6})(?:/(join|select|sync|leave)(?:/(\d{1,5}))?)?)?',self.path)
            if not match:raise ProtocolError('route','Rota desconhecida.',404)
            code,action,number=match.groups();data={}
            if self.command=='POST':
                length=self.headers.get('Content-Length','')
                if not length.isdigit() or not 0<int(length)<=32768:raise ProtocolError('size','Corpo ausente ou maior que 32 KB.',413)
                if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Type','').split(';')[0]!='application/json':raise ProtocolError('encoding','Use JSON com tamanho definido.',415)
                try:data=json.loads(self.rfile.read(int(length)))
                except (ValueError,UnicodeError):raise ProtocolError('json','JSON invalido.')
                if not isinstance(data,dict):raise ProtocolError('json','Envie um objeto JSON.')
            token=self.headers.get('Authorization','').removeprefix('Bearer ')
            rooms=self.server.rooms
            if self.command=='POST' and code is None:value=rooms.create(data)
            elif self.command=='POST' and action=='join' and number is None:value=rooms.join(code,data)
            elif self.command=='GET' and code and action is None:value=rooms.state(code,token)
            elif self.command=='POST' and action=='select' and number is None:value=rooms.select(code,token,data.get('picks'))
            elif self.command=='POST' and action=='sync' and number is None:value=rooms.sync(code,token,data)
            elif self.command=='GET' and action=='sync' and number is not None:value=rooms.wait(code,token,int(number))
            elif self.command=='POST' and action=='leave' and number is None:value=rooms.leave(code,token)
            else:raise ProtocolError('route','Operacao indisponivel.',404)
            self.reply(200,value)
        except ProtocolError as error:self.reply(error.status,{'error':error.code,'message':str(error)})
        except (ValueError,TypeError,KeyError):self.reply(400,{'error':'request','message':'Dados invalidos.'})
    do_GET=dispatch;do_POST=dispatch
def start(host='0.0.0.0',port=PORT):
    server=Server((host,port),Rooms())
    thread=threading.Thread(target=lambda:server.serve_forever(poll_interval=0.25),daemon=True);thread.start()
    return server
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--host',default='0.0.0.0');parser.add_argument('--port',type=int,default=PORT);args=parser.parse_args()
    with Server((args.host,args.port),Rooms()) as server:
        print(f'Servidor multiplayer do Blue em {args.host}:{server.server_port}. Ctrl+C encerra.',flush=True)
        try:server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:pass
if __name__=='__main__':main()
