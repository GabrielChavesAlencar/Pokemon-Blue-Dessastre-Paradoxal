"""Local audio library and reversible runtime music overrides for Essentials."""
from __future__ import annotations
import base64,binascii,hashlib,io,json,re,wave
from pathlib import Path
from ruby_marshal import loads,dumps_simple,text,RubyObject

ROOT=Path(__file__).resolve().parents[1]
EXTENSIONS={'.wav':('audio/wav',True),'.ogg':('audio/ogg',True),'.mp3':('audio/mpeg',True),'.mid':('audio/midi',False),'.midi':('audio/midi',False)}
GLOBALS={'wild':'Batalhas selvagens','trainer':'Batalhas contra treinadores','wildVictory':'Vitória selvagem','trainerVictory':'Vitória contra treinadores'}
FIELDS={'wild':'WildBattleBGM','trainer':'TrainerBattleBGM','wildVictory':'WildVictoryBGM','trainerVictory':'TrainerVictoryBGM'}
LIMIT=20_000_000

class MusicError(Exception):
    def __init__(self,message,status=400):super().__init__(message);self.status=status

def sha(raw):return hashlib.sha256(raw).hexdigest()

def file_sha(path):
    digest=hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda:stream.read(65536),b''):digest.update(block)
    return digest.hexdigest()

def game_file(game,relative):
    base=game.resolve();target=(base/relative).resolve()
    if not target.is_relative_to(base):raise MusicError('Destino fora da pasta do jogo.')
    return target

def track_path(game,name,exists=True):
    if not isinstance(name,str) or not name or '\\' in name or ':' in name or name.startswith('/') or any(p in ('','..','.') for p in name.split('/')):
        raise MusicError('Nome de faixa inválido.')
    base=game_file(game,'Audio/BGM');target=(base/name).resolve()
    if not target.is_relative_to(base) or target.suffix.lower() not in EXTENSIONS:raise MusicError('Faixa inválida.')
    if exists and not target.is_file():raise MusicError('Faixa não encontrada.',404)
    return target

def config(game):
    path=game_file(game,'Data/blue-music.json');raw=path.read_bytes() if path.is_file() else b''
    if len(raw)>300_000:raise MusicError('Configuração de músicas muito grande.')
    value=json.loads(raw) if raw else {'version':1,'global':{},'maps':{}}
    if value.get('version')!=1 or not isinstance(value.get('global'),dict) or not isinstance(value.get('maps'),dict):raise MusicError('Configuração de músicas inválida.')
    return value,sha(raw)

def attrs(value):return value.attrs if isinstance(value,RubyObject) else {}

def metadata(game):
    p=game/'PBS/metadata.txt'
    if not p.is_file():return {}
    raw=p.read_text(encoding='utf-8-sig');block=re.search(r'(?ms)^\[0\][^\n]*\n(.*?)(?=^\[|\Z)',raw)
    return dict(re.findall(r'^([A-Za-z]+)\s*=\s*([^\r\n#]+)',block[1],re.M)) if block else {}

def catalog(game):
    value,digest=config(game);base=game_file(game,'Audio/BGM');tracks=[]
    if base.is_dir():
        for path in base.rglob('*'):
            if not path.is_file() or path.suffix.lower() not in EXTENSIONS:continue
            name=path.relative_to(base).as_posix()
            try:track_path(game,name)
            except MusicError:continue
            tracks.append({'id':name,'name':path.stem,'size':path.stat().st_size,'preview':EXTENSIONS[path.suffix.lower()][1]})
    info={};mapinfo=game_file(game,'Data/MapInfos.rxdata')
    if mapinfo.is_file():
        parsed=loads(mapinfo.read_bytes())
        if isinstance(parsed,dict):info={i:text(attrs(v).get('@name')) for i,v in parsed.items() if isinstance(i,int)}
    maps=[]
    for path in (game/'Data').glob('Map[0-9]*.rxdata'):
        match=re.fullmatch(r'Map(\d+)\.rxdata',path.name)
        if match:maps.append({'id':int(match[1]),'name':info.get(int(match[1])) or 'Mapa '+match[1]})
    defaults=metadata(game)
    return {'tracks':sorted(tracks,key=lambda e:e['id'].casefold()),'maps':sorted(maps,key=lambda e:(e['name'].casefold(),e['id'])),
            'global':[{'id':k,'name':label,'original':defaults.get(FIELDS[k],'').strip()} for k,label in GLOBALS.items()],
            'assignments':value,'hash':digest}

def target_key(game,scope,target):
    if scope=='global' and target in GLOBALS:return target
    if scope=='map':
        try:number=int(target)
        except (ValueError,TypeError):raise MusicError('Mapa inválido.')
        if not 1<=number<=99999 or not game_file(game,f'Data/Map{number:03d}.rxdata').is_file():raise MusicError('Mapa não encontrado.',404)
        return str(number)
    raise MusicError('Destino de música inválido.')

def assignment(game,scope,target):
    key=target_key(game,scope,target);value,digest=config(game)
    if scope=='map':
        record=loads(game_file(game,f'Data/Map{int(key):03d}.rxdata').read_bytes())
        data=attrs(record);audio=attrs(data.get('@bgm'))
        original={'track':text(audio.get('@name')),'volume':audio.get('@volume',100),'pitch':audio.get('@pitch',100),'enabled':bool(data.get('@autoplay_bgm'))}
    else:original={'track':metadata(game).get(FIELDS[key],''),'volume':100,'pitch':100,'enabled':True}
    return {'scope':scope,'target':key,'original':original,'value':value['maps' if scope=='map' else 'global'].get(key),'hash':digest}

def track_info(game,name):
    p=track_path(game,name)
    return {'id':name,'hash':file_sha(p),'size':p.stat().st_size,'preview':EXTENSIONS[p.suffix.lower()][1]}

def transaction(game,backups,plans,atomic_write,backup_file):
    previous={p:p.read_bytes() if p.is_file() else None for p in plans};written=[]
    for p,raw in previous.items():
        if raw is not None:backup_file(backups,p.relative_to(game.resolve()).as_posix(),raw)
    try:
        for p,raw in plans.items():p.parent.mkdir(parents=True,exist_ok=True);atomic_write(p,raw);written.append(p)
    except Exception:
        for p in reversed(written):
            if previous[p] is None:p.unlink()
            else:atomic_write(p,previous[p])
        raise

def save_assignment(game,backups,obj,*,lock,atomic_write,backup_file):
    key=target_key(game,obj.get('scope'),obj.get('target'))
    mode=obj.get('mode','custom')
    if mode not in ('original','custom','mute'):raise MusicError('Modo de música inválido.')
    volume=obj.get('volume',100);pitch=obj.get('pitch',100)
    if type(volume) is not int or not 0<=volume<=100 or type(pitch) is not int or not 50<=pitch<=150:raise MusicError('Volume ou velocidade inválidos.')
    name=obj.get('track','')
    if mode=='custom':track_path(game,name)
    selected={'mode':mode,'track':name if mode=='custom' else '', 'volume':volume,'pitch':pitch}
    with lock:
        value,digest=config(game)
        if obj.get('hash')!=digest:raise MusicError('As músicas foram alteradas. Atualize antes de salvar.',409)
        section=value['maps' if obj['scope']=='map' else 'global']
        if mode=='original':section.pop(key,None)
        else:section[key]=selected
        rows=lambda source:[[k,v['mode'],v['track'],v['volume'],v['pitch']] for k,v in sorted(source.items())]
        raw=(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf8')
        plans={game_file(game,'Data/blue-music.json'):raw,game_file(game,'Data/blue-music.rxdata'):dumps_simple([1,rows(value['global']),rows(value['maps'])])}
        for file in ['BlueMusic.rb','meta.txt']:
            plans[game_file(game,'Plugins/ZZZZ Blue Music/'+file)]=(ROOT/'scripts/music'/file).read_bytes()
        plans={p:b for p,b in plans.items() if not p.is_file() or p.read_bytes()!=b}
        transaction(game,backups,plans,atomic_write,backup_file)
    return {'ok':True,'hash':sha(raw),'value':None if mode=='original' else selected,'message':'Música salva. Reabra o jogo para aplicar a configuração atual.'}

def validate_audio(raw,extension):
    if not raw or len(raw)>LIMIT:raise MusicError('Áudio vazio ou maior que 20 MB.',413)
    try:
        if extension=='.wav':
            with wave.open(io.BytesIO(raw),'rb') as sound:
                if sound.getnframes()==0:raise ValueError('WAV vazio')
        elif extension=='.ogg':
            if len(raw)<27 or not raw.startswith(b'OggS'):raise ValueError('OGG inválido')
        elif extension=='.mp3':
            if len(raw)<128 or not (raw.startswith(b'ID3') or (raw[0]==255 and raw[1]&224==224)):raise ValueError('MP3 inválido')
        elif extension in ('.mid','.midi'):
            if len(raw)<14 or not raw.startswith(b'MThd') or int.from_bytes(raw[4:8],'big')!=6:raise ValueError('MIDI inválido')
        else:raise ValueError('Formato não suportado')
    except (ValueError,wave.Error,EOFError) as error:raise MusicError(str(error)) from error

def upload(game,backups,obj,*,lock,atomic_write,backup_file):
    name=obj.get('filename','')
    parts=name.split('/') if isinstance(name,str) and obj.get('mode')=='replace' else [name]
    reserved={'CON','PRN','AUX','NUL',*[f'COM{i}' for i in range(1,10)],*[f'LPT{i}' for i in range(1,10)]}
    if not isinstance(name,str) or len(name)>200 or any(not isinstance(p,str) or not re.fullmatch(r"[\w .()'-]+",p) or p.rstrip(' .')!=p or p.split('.')[0].upper() in reserved for p in parts):raise MusicError('Nome do áudio inválido.')
    target=track_path(game,name,False)
    encoded=obj.get('data','')
    if not isinstance(encoded,str) or len(encoded)>27_000_000:raise MusicError('Áudio maior que 20 MB.',413)
    try:raw=base64.b64decode(encoded,validate=True)
    except (binascii.Error,ValueError) as error:raise MusicError('Áudio base64 inválido.') from error
    validate_audio(raw,target.suffix.lower())
    with lock:
        exists=target.is_file()
        if exists and (obj.get('mode')!='replace' or obj.get('hash')!=file_sha(target)):raise MusicError('Arquivo existente. Selecione substituir e recarregue a faixa.',409)
        if not exists and obj.get('mode')=='replace':raise MusicError('Arquivo a substituir não encontrado.',409)
        transaction(game,backups,{target:raw},atomic_write,backup_file)
    return {'ok':True,'id':name,'hash':sha(raw),'replaced':exists}

def range_slice(header,size):
    if not header:return 0,size-1,200
    match=re.fullmatch(r'bytes=(\d*)-(\d*)',header)
    if not match or not any(match.groups()) or size<=0:raise MusicError('Intervalo de áudio inválido.',416)
    if match[1]:start=int(match[1]);end=min(int(match[2]) if match[2] else size-1,size-1)
    else:start=max(0,size-int(match[2]));end=size-1
    if start<0 or start>=size or end<start:raise MusicError('Intervalo fora do áudio.',416)
    return start,end,206
