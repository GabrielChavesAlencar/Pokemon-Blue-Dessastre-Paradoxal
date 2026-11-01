"""Isolated, in-memory preparation protocol. No battle result is accepted from clients."""
from __future__ import annotations
import copy,hashlib,json,re,secrets,threading,time
PROTOCOL=1
RULES={'format':'double-pick4','teamSize':6,'pickedSize':4,'level':50,'selectionSeconds':60,'mechanics':{'mega':True,'zmove':True,'tera':True,'dynamax':True}}
class ProtocolError(Exception):
    def __init__(self,code,message,status=400):
        super().__init__(message);self.code=code;self.status=status
def reject(code,message,status=400):raise ProtocolError(code,message,status)
def integer(value,low,high):return type(value) is int and low<=value<=high
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode()).hexdigest()

class Rooms:
    def __init__(self,catalog,clock=time.monotonic,max_rooms=64):
        if catalog.get('schema')!=1 or not re.fullmatch('[a-f0-9]{64}',catalog.get('engineFingerprint','')):
            raise ValueError('Export a native catalog with probe.py before starting the server.')
        self.catalog=copy.deepcopy(catalog);self.clock=clock;self.max_rooms=max_rooms
        self.fingerprint=digest({'protocol':PROTOCOL,'rules':RULES,'catalog':catalog})
        self.rooms={};self.lock=threading.RLock()
    def hello(self):
        return {'protocol':PROTOCOL,'compatibility':self.fingerprint,'rules':copy.deepcopy(RULES),'capabilities':['rooms','team-preview','pick-four','reconnect'],'battleAvailable':False}
    def validate_team(self,team):
        if not isinstance(team,list) or len(team)!=6:reject('team','Envie exatamente seis Pokemon.')
        result=[]
        for row in team:
            if not isinstance(row,dict):reject('team','Pokemon invalido.')
            expected={'species','ability','item','nature','moves','evs','ivs','level'}
            if set(row)!=expected:reject('team','Campos de Pokemon invalidos para o protocolo 1.')
            species=self.catalog['species'].get(row['species']) if isinstance(row['species'],str) else None
            if not species or species['mega']:reject('species','Use uma especie/forma base registrada, nunca a forma Mega inicial.')
            if row['ability'] not in species['abilities']:reject('ability','Habilidade incompativel.')
            if row['item'] is not None and row['item'] not in self.catalog['items']:reject('item','Item desconhecido.')
            if row['nature'] not in self.catalog['natures']:reject('nature','Nature desconhecida.')
            if not integer(row['level'],50,50):reject('level','O nivel online deve ser 50.')
            moves=row['moves']
            if not isinstance(moves,list) or not 1<=len(moves)<=4 or not all(isinstance(m,str) and m in self.catalog['moves'] for m in moves) or len(set(moves))!=len(moves):reject('moves','Use de um a quatro golpes registrados, sem repeticao.')
            for key,maximum in [('evs',252),('ivs',31)]:
                values=row[key]
                if not isinstance(values,list) or len(values)!=6 or not all(integer(v,0,maximum) for v in values):reject(key,'Atributos invalidos: '+key)
            if sum(row['evs'])>510:reject('evs','O total de EVs excede 510.')
            result.append(copy.deepcopy(row))
        return result
    def _request(self,data):
        if not isinstance(data,dict) or data.get('protocol')!=PROTOCOL or type(data.get('protocol')) is not int:reject('protocol','Versao de protocolo incompativel.',409)
        if set(data)!={'protocol','compatibility','name','team'}:reject('request','Campos desconhecidos na inscricao.')
        if data.get('compatibility')!=self.fingerprint:reject('compatibility','Engine, catalogo ou regras diferentes. Atualize ambos os clientes.',409)
        name=data.get('name')
        if not isinstance(name,str) or not 1<=len(name.strip())<=24 or any(ord(c)<32 or c in '<>&' for c in name):reject('name','Nome invalido.')
        return {'name':name.strip(),'team':self.validate_team(data.get('team')),'token':secrets.token_urlsafe(32),'picks':None,'timeout':False,'seen':self.clock()}
    def _advance(self,room):
        now=self.clock()
        if room['state']=='selecting' and now>=room['deadline']:
            for player in room['players']:
                if player['picks'] is None:player['picks']=[0,1,2,3];player['timeout']=True
            room['state']='prepared'
        if room['state'] in ('waiting','selecting','prepared') and (now-room['created']>=1800 or now-max(p['seen'] for p in room['players'])>=600):room['state']='expired'
    def sweep(self):
        with self.lock:
            for code,room in list(self.rooms.items()):
                self._advance(room)
                if room['state'] in ('expired','cancelled'):
                    room.setdefault('closed',self.clock())
                    if self.clock()-room['closed']>=60:del self.rooms[code]
    def _room(self,code):
        room=self.rooms.get(code)
        if room is None:reject('room','Sala inexistente.',404)
        self._advance(room);return room
    def _auth(self,room,token):
        if not isinstance(token,str) or len(token)>128:reject('auth','Token invalido.',401)
        for i,p in enumerate(room['players']):
            if secrets.compare_digest(p['token'],token):return i,p
        reject('auth','Token invalido.',401)
    def _view(self,code,room,index):
        own=room['players'][index]
        return {'room':code,'state':room['state'],'you':index,'rules':copy.deepcopy(RULES),'battleAvailable':False,
                'secondsRemaining':max(0,room['deadline']-self.clock()) if room['deadline'] is not None else None,
                'picks':copy.deepcopy(own['picks']),'timedOut':own['timeout'],
                'players':[{'name':p['name'],'connected':self.clock()-p['seen']<30,'ready':p['picks'] is not None,'species':[m['species'] for m in p['team']]} for p in room['players']]}
    def create(self,data):
        with self.lock:
            self.sweep()
            if len(self.rooms)>=self.max_rooms:reject('capacity','Limite temporario de salas atingido.',503)
            player=self._request(data)
            while True:
                code=''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
                if code not in self.rooms:break
            room={'players':[player],'created':self.clock(),'state':'waiting','deadline':None};self.rooms[code]=room
            return {**self._view(code,room,0),'token':player['token']}
    def join(self,code,data):
        with self.lock:
            room=self._room(code)
            if room['state']!='waiting' or len(room['players'])!=1:reject('phase','Esta sala nao aceita mais participantes.',409)
            player=self._request(data);room['players'].append(player);room['state']='selecting';room['deadline']=self.clock()+60
            return {**self._view(code,room,1),'token':player['token']}
    def state(self,code,token):
        with self.lock:
            room=self._room(code);i,p=self._auth(room,token)
            if room['state'] not in ('expired','cancelled'):p['seen']=self.clock()
            return self._view(code,room,i)
    def select(self,code,token,picks):
        with self.lock:
            room=self._room(code);i,p=self._auth(room,token)
            if not isinstance(picks,list) or len(picks)!=4 or not all(integer(n,0,5) for n in picks) or len(set(picks))!=4:reject('picks','Escolha quatro indices diferentes de 0 a 5.')
            if room['state'] in ('selecting','prepared') and p['picks']==picks:return self._view(code,room,i)
            if room['state']!='selecting' or p['picks'] is not None:reject('phase','Selecao encerrada ou ja confirmada.',409)
            p['picks']=list(picks);p['seen']=self.clock()
            if all(x['picks'] is not None for x in room['players']):room['state']='prepared'
            return self._view(code,room,i)
    def leave(self,code,token):
        with self.lock:
            room=self._room(code);i,_=self._auth(room,token)
            if room['state']!='expired':room['state']='cancelled';room.setdefault('closed',self.clock())
            return self._view(code,room,i)
