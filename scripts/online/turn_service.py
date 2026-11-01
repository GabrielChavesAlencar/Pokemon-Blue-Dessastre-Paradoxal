"""Opt-in command transport to ONE local authoritative native battle worker.

No client can submit damage, HP or a winner. This is an experimental API, not a Hub UI.
"""
from __future__ import annotations
import copy,json,secrets,threading,time
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
try:from .rooms import ProtocolError
except ImportError:from rooms import ProtocolError

def atomic(path,raw):
    tmp=path.with_suffix('.tmp');tmp.write_bytes(raw.encode('utf8'));tmp.replace(path)

class Turns:
    def __init__(self,directory,compatibility,tokens=None):
        self.directory=Path(directory);self.compatibility=compatibility
        self.tokens=tokens or [secrets.token_urlsafe(32),secrets.token_urlsafe(32)]
        self.lock=threading.RLock();self.accepted={}
    def auth(self,token,compatibility):
        if compatibility!=self.compatibility:raise ProtocolError('version','Engine/regras incompatíveis.',409)
        for side,known in enumerate(self.tokens):
            if secrets.compare_digest(str(token),known):return side
        raise ProtocolError('auth','Token inválido.',401)
    def read(self):
        path=self.directory/'state.json'
        if not path.exists():return {'state':'waiting-engine','protocol':2}
        if path.stat().st_size>1_000_000:raise ProtocolError('worker','Estado da engine inválido.',503)
        return json.loads(path.read_text(encoding='utf8'))
    def state(self,side):
        with self.lock:
            state=copy.deepcopy(self.read())
            request=state.get('request')
            if request and request['side']!=side:state['request']=None
            elif request:
                # Show only this side's pending legal choices, never the other side's move list.
                request['submitted']=request['seq'] in self.accepted
            return state
    def submit(self,side,data):
        with self.lock:
            if not isinstance(data,dict) or set(data)!={'seq','option'} or any(type(data[k]) is not int for k in data):
                raise ProtocolError('command','Envie apenas seq e option inteiros.')
            seq,option=data['seq'],data['option']
            previous=self.accepted.get(seq)
            if previous is not None:
                if previous!=(side,option):raise ProtocolError('replay','Comando já confirmado.',409)
                return {'accepted':seq,'replayed':True}
            state=self.read();request=state.get('request')
            if state.get('state')!='choosing' or not request or request['seq']!=seq:raise ProtocolError('phase','Pedido de comando expirado.',409)
            if request['side']!=side:raise ProtocolError('owner','Este Pokémon pertence ao outro jogador.',403)
            options=request['options']
            if not 0<=option<len(options):raise ProtocolError('option','Escolha uma opção legal da engine.')
            choice=options[option]
            atomic(self.directory/'command.tsv',f"{seq}\t{choice['kind']}\t{choice['slot']}\t{choice['target']}\n")
            self.accepted[seq]=(side,option)
            return {'accepted':seq,'replayed':False}

class TurnServer(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,turns):
        self.turns=turns;self.slots=threading.BoundedSemaphore(16);super().__init__(address,Handler)
    def process_request(self,request,address):
        if not self.slots.acquire(blocking=False):request.close();return
        try:super().process_request(request,address)
        except BaseException:self.slots.release();raise
    def process_request_thread(self,request,address):
        try:super().process_request_thread(request,address)
        finally:self.slots.release()

class Handler(BaseHTTPRequestHandler):
    server_version='BlueNativeTurns/2';sys_version=''
    def setup(self):super().setup();self.connection.settimeout(5)
    def log_message(self,*args):pass
    def reply(self,status,value):
        raw=json.dumps(value,ensure_ascii=True).encode();self.send_response(status)
        self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)))
        self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(raw)
    def dispatch(self):
        try:
            if self.path=='/v2/hello' and self.command=='GET':
                return self.reply(200,{'protocol':2,'compatibility':self.server.turns.compatibility,'experimental':True,'nativeCommands':True,'hubUI':False,'mechanics':False})
            side=self.server.turns.auth(self.headers.get('Authorization','').removeprefix('Bearer '),self.headers.get('X-Blue-Compatibility'))
            if self.path=='/v2/state' and self.command=='GET':return self.reply(200,self.server.turns.state(side))
            if self.path!='/v2/command' or self.command!='POST':raise ProtocolError('route','Rota indisponível.',404)
            length=self.headers.get('Content-Length','')
            if not length.isdecimal() or not 0<int(length)<=2048 or self.headers.get_content_type()!='application/json':raise ProtocolError('body','JSON limitado a 2048 bytes.',413)
            self.reply(200,self.server.turns.submit(side,json.loads(self.rfile.read(int(length)))))
        except ProtocolError as error:self.reply(error.status,{'error':error.code,'message':str(error)})
        except (ValueError,KeyError,TypeError):self.reply(400,{'error':'request'})
    do_GET=dispatch;do_POST=dispatch

def main():
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--session',type=Path,required=True);p.add_argument('--host',default='127.0.0.1');p.add_argument('--port',type=int,default=8792);p.add_argument('--lan',action='store_true');args=p.parse_args()
    if args.host not in ('127.0.0.1','localhost','::1') and not args.lan:p.error('Use --lan explicitamente para acesso fora do computador local.')
    session=json.loads(args.session.read_text(encoding='utf8'));turns=Turns(session['directory'],session['compatibility'],session['tokens'])
    with TurnServer((args.host,args.port),turns) as server:
        print(f'Native turns: http://{args.host}:{server.server_port}; API experimental, sem interface PvP no Hub.',flush=True)
        try:server.serve_forever(.1)
        except KeyboardInterrupt:pass
if __name__=='__main__':main()
