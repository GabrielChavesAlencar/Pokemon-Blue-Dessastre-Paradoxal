"""Synthetic music/map fixtures; contains no assets from the installed game."""
from pathlib import Path
import io,wave,sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'server'))
from ruby_marshal import RubyObject,RubyData,integer

def wav_bytes(frames=1600):
    buffer=io.BytesIO()
    with wave.open(buffer,'wb') as sound:
        sound.setnchannels(1);sound.setsampwidth(2);sound.setframerate(8000)
        sound.writeframes(b'\xd0\x07\x30\xf8'*(frames//2))
    return buffer.getvalue()

def marshal_fixture(value):
    def symbol(s):
        raw=s.encode();return b':'+integer(len(raw))+raw
    def dump(v):
        if v is None:return b'0'
        if v is True:return b'T'
        if v is False:return b'F'
        if isinstance(v,int):return b'i'+integer(v)
        if isinstance(v,str):v=v.encode('utf8')
        if isinstance(v,bytes):return b'"'+integer(len(v))+v
        if isinstance(v,list):return b'['+integer(len(v))+b''.join(dump(x) for x in v)
        if isinstance(v,dict):return b'{'+integer(len(v))+b''.join(dump(k)+dump(x) for k,x in v.items())
        if isinstance(v,RubyObject):return b'o'+symbol(v.name)+integer(len(v.attrs))+b''.join(symbol(k)+dump(x) for k,x in v.attrs.items())
        if isinstance(v,RubyData):return b'u'+symbol(v.name)+integer(len(v.data))+v.data
        raise TypeError(type(v))
    return b'\x04\x08'+dump(value)

def make_fixture(game):
    (game/'PBS').mkdir(parents=True,exist_ok=True);(game/'Data').mkdir(exist_ok=True);(game/'Audio/BGM').mkdir(parents=True,exist_ok=True)
    (game/'PBS/metadata.txt').write_text('[0]\nWildBattleBGM = Town\nTrainerBattleBGM = Battle\n',encoding='utf8')
    (game/'PBS/pokemon.txt').write_text('[TESTMON]\nName = Testmon\n',encoding='utf8')
    for name,frames in [('Town.wav',1600),('Battle.wav',2400)]: (game/'Audio/BGM'/name).write_bytes(wav_bytes(frames))
    audio=RubyObject('RPG::AudioFile',{'@name':'Town','@volume':80,'@pitch':100})
    event=RubyObject('RPG::Event',{'@id':7,'@name':'Fixture event','@pages':[RubyObject('RPG::Event::Page',{'@list':[1,2,3]})]})
    record=RubyObject('RPG::Map',{'@bgm':audio,'@autoplay_bgm':True,'@events':{7:event},'@data':RubyData('Table',b'opaque synthetic tile bytes')})
    (game/'Data/Map001.rxdata').write_bytes(marshal_fixture(record))
    (game/'Data/MapInfos.rxdata').write_bytes(marshal_fixture({1:RubyObject('RPG::MapInfo',{'@name':'Fixture City','@parent_id':0})}))

if __name__=='__main__':
    import sys
    make_fixture(Path(sys.argv[1]))
