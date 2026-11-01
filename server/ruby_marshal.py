"""Read RPG Maker Marshal data; write only Blue's simple audio configuration.

Ruby classes are represented as inert data. No Ruby code is evaluated.
Original map files are never serialized or rewritten by the music editor.
"""
from dataclasses import dataclass,field
import struct

@dataclass
class RubyObject:
    name:str
    attrs:dict=field(default_factory=dict)

@dataclass
class RubyData:
    name:str
    data:bytes

def text(value):
    return value.decode('utf8',errors='replace') if isinstance(value,bytes) else str(value or '')

class Reader:
    def __init__(self,data):
        if not isinstance(data,bytes) or len(data)>32_000_000 or data[:2]!=b'\x04\x08':raise ValueError('Arquivo RPG Maker invalido.')
        self.data=data;self.i=2;self.objects=[];self.symbols=[];self.nodes=0
    def take(self,count):
        if count<0 or self.i+count>len(self.data):raise ValueError('Arquivo RPG Maker truncado.')
        result=self.data[self.i:self.i+count];self.i+=count;return result
    def number(self):
        n=int.from_bytes(self.take(1),'little',signed=True)
        if n==0:return 0
        if n>4:return n-5
        if n<-4:return n+5
        raw=int.from_bytes(self.take(abs(n)),'little')
        return raw if n>0 else raw-(1<<(abs(n)*8))
    def count(self):
        n=self.number()
        if not 0<=n<=1_000_000:raise ValueError('Colecao RPG Maker invalida.')
        return n
    def read(self,depth=0):
        self.nodes+=1
        if depth>128 or self.nodes>1_000_000:raise ValueError('Estrutura RPG Maker muito grande.')
        tag=self.take(1)
        child=lambda:self.read(depth+1)
        if tag==b'0':return None
        if tag==b'T':return True
        if tag==b'F':return False
        if tag==b'i':return self.number()
        if tag==b':':
            value=text(self.take(self.count()));self.symbols.append(value);return value
        if tag==b';':return self.symbols[self.count()]
        if tag==b'@':return self.objects[self.count()]
        if tag==b'"':
            value=self.take(self.count());self.objects.append(value);return value
        if tag==b'I':
            value=child()
            for _ in range(self.count()):child();child()
            return value
        if tag in (b'e',b'C'):
            child();return child()
        if tag==b'[':
            value=[];self.objects.append(value)
            for _ in range(self.count()):value.append(child())
            return value
        if tag in (b'{',b'}'):
            value={};self.objects.append(value)
            for _ in range(self.count()):
                key=child();value[key]=child()
            if tag==b'}':child()
            return value
        if tag in (b'o',b'S'):
            value=RubyObject(text(child()));self.objects.append(value)
            for _ in range(self.count()):
                key=text(child());value.attrs[key]=child()
            return value
        if tag==b'u':
            name=text(child());value=RubyData(name,self.take(self.count()));self.objects.append(value);return value
        if tag==b'U':
            value=RubyObject(text(child()));self.objects.append(value);value.attrs['marshal_load']=child();return value
        if tag==b'f':
            raw=self.take(self.count()).split(b'\0')[0]
            value=float(raw.replace(b'inf',b'Infinity').replace(b'nan',b'NaN'));self.objects.append(value);return value
        if tag==b'l':
            negative=self.take(1)==b'-';value=int.from_bytes(self.take(self.count()*2),'little')
            value=-value if negative else value;self.objects.append(value);return value
        if tag==b'/':
            value=RubyData('Regexp',self.take(self.count())+self.take(1));self.objects.append(value);return value
        if tag in (b'c',b'm',b'M'):
            value=RubyData('Class',self.take(self.count()));self.objects.append(value);return value
        raise ValueError('Tipo RPG Maker nao suportado: '+repr(tag))

def loads(data):
    reader=Reader(data)
    try:value=reader.read()
    except (IndexError,KeyError,TypeError,OverflowError) as error:raise ValueError('Referencias RPG Maker invalidas.') from error
    if reader.i!=len(data):raise ValueError('Dados RPG Maker extras.')
    return value

def integer(n):
    if n==0:return b'\0'
    if 0<n<123:return bytes([n+5])
    if -124<n<0:return bytes([(n-5)&255])
    size=next(i for i in range(1,5) if 0<=n<256**i or -256**i<=n<0)
    return bytes([size if n>0 else (-size&255)])+(n%(256**size)).to_bytes(size,'little')

def dumps_simple(value):
    def dump(v):
        if v is None:return b'0'
        if v is True:return b'T'
        if v is False:return b'F'
        if isinstance(v,int):return b'i'+integer(v)
        if isinstance(v,list):return b'['+integer(len(v))+b''.join(dump(x) for x in v)
        if isinstance(v,str):
            raw=v.encode('utf8');return b'I"'+integer(len(raw))+raw+integer(1)+b':'+integer(1)+b'E'+b'T'
        raise ValueError('Somente configuracoes simples podem ser gravadas.')
    return b'\x04\x08'+dump(value)
