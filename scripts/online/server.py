"""Experimental local room server; intentionally separate from the game and website."""
from __future__ import annotations
import argparse,json,re,threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
try:from .rooms import Rooms,ProtocolError
except ImportError:from rooms import Rooms,ProtocolError

class Server(ThreadingHTTPServer):
    daemon_threads=True
    def __init__(self,address,rooms):
        self.rooms=rooms;self.slots=threading.BoundedSemaphore(16);super().__init__(address,Handler)
    def process_request(self,request,client_address):
        if not self.slots.acquire(blocking=False):request.close();return
        try:super().process_request(request,client_address)
        except BaseException:self.slots.release();raise
    def process_request_thread(self,request,client_address):
        try:super().process_request_thread(request,client_address)
        finally:self.slots.release()
    def service_actions(self):self.rooms.sweep()
class Handler(BaseHTTPRequestHandler):
    server_version='BlueOnlineExperiment/1';sys_version=''
    def setup(self):super().setup();self.connection.settimeout(5)
    def log_message(self,*args):pass  # Never write bearer tokens or private team payloads to logs.
    def reply(self,status,value):
        raw=json.dumps(value,ensure_ascii=True,separators=(',',':')).encode()
        self.send_response(status);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(raw)
    def dispatch(self):
        try:
            if self.headers.get('Origin') is not None:raise ProtocolError('origin','Esta API experimental nao aceita chamadas de paginas web.',403)
            if self.command=='GET' and self.path=='/v1/hello':return self.reply(200,self.server.rooms.hello())
            match=re.fullmatch(r'/v1/rooms(?:/([A-Z2-9]{8})(?:/(join|select|leave))?)?',self.path)
            if not match:raise ProtocolError('route','Rota desconhecida.',404)
            code,action=match.groups();data={}
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
            elif self.command=='POST' and action=='join':value=rooms.join(code,data)
            elif self.command=='GET' and code and action is None:value=rooms.state(code,token)
            elif self.command=='POST' and action=='select':value=rooms.select(code,token,data.get('picks'))
            elif self.command=='POST' and action=='leave':value=rooms.leave(code,token)
            else:raise ProtocolError('route','Operacao indisponivel.',404)
            self.reply(200,value)
        except ProtocolError as error:self.reply(error.status,{'error':error.code,'message':str(error)})
        except (ValueError,TypeError,KeyError):self.reply(400,{'error':'request','message':'Dados invalidos.'})
    do_GET=dispatch;do_POST=dispatch
def main():
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--catalog',type=Path,required=True);parser.add_argument('--host',default='127.0.0.1');parser.add_argument('--port',type=int,default=8791);parser.add_argument('--lan',action='store_true');args=parser.parse_args()
    if args.host not in ('127.0.0.1','localhost','::1') and not args.lan:parser.error('Use --lan explicitamente para escutar fora do computador local.')
    if args.catalog.stat().st_size>8_000_000:parser.error('Catalogo muito grande.')
    rooms=Rooms(json.loads(args.catalog.read_text(encoding='utf8')))
    with Server((args.host,args.port),rooms) as server:
        print(f'Blue online experimental: http://{args.host}:{server.server_port}; apenas salas/selecao, batalha PvP ainda indisponivel.',flush=True)
        try:server.serve_forever(poll_interval=0.25)
        except KeyboardInterrupt:pass
if __name__=='__main__':main()
