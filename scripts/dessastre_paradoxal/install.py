"""Install the author's special generation from a checked-in manifest and sprite bundle."""
from __future__ import annotations
import argparse,hashlib,io,json,os,re,shutil,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[2]
OWN_PBS={'pokemon_dessastre_paradoxal.txt','pokemon_forms_dessastre_paradoxal.txt','pokemon_metrics_dessastre_paradoxal.txt','items_dessastre_paradoxal.txt','abilities_dessastre_paradoxal.txt'}
ROLES={'front':'Front','front-shiny':'Front shiny','back':'Back','back-shiny':'Back shiny','icon':'Icons','icon-shiny':'Icons shiny','footprint':'Footprints'}
def sha(data):return hashlib.sha256(data).hexdigest()
def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,temp=tempfile.mkstemp(prefix='.blue-dp-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        os.replace(temp,path)
    finally:
        if os.path.exists(temp):os.unlink(temp)

def parse_sections(text):
    matches=list(re.finditer(r'^\[([^\]\r\n]+)\][^\r\n]*',text,re.M))
    return [(m[1].strip().upper(),m.start(),matches[i+1].start() if i+1<len(matches) else len(text)) for i,m in enumerate(matches)]
def field(text,key,default=''):
    m=re.search(r'^'+re.escape(key)+r'\s*=\s*([^\r\n]*)',text,re.M);return m[1].strip() if m else default

def append_evolution(text,id,evolution):
    section=next((s for s in parse_sections(text) if s[0]==id),None)
    if not section:raise ValueError('Missing base species: '+id)
    _,start,end=section;block=text[start:end];old=field(block,'Evolutions')
    parts=old.split(',') if old else []
    if evolution in [parts[i:i+3] for i in range(0,len(parts),3)]:return text
    value=','.join(parts+evolution);newline='\r\n' if '\r\n' in text else '\n'
    line='Evolutions = '+value
    if re.search(r'^Evolutions\s*=',block,re.M):block=re.sub(r'^Evolutions\s*=[^\r\n]*',lambda m:line,block,flags=re.M)
    else:block=block.rstrip('\r\n')+newline+line+newline
    return text[:start]+block+text[end:]

def pbs_entry(p,entries):
    mega=bool(p.get('base'));flags=['DessastreParadoxal']
    if p['category'] in ['past_paradox','future_paradox']:flags.append('Paradox')
    if mega:flags.append('MegaEvolution')
    data=[f"[{p['id']}]",('FormName' if mega else 'Name')+' = '+p['name'],'Types = '+','.join(p['types']),'BaseStats = '+','.join(map(str,p['stats'])),'Abilities = '+','.join(p['abilities'][:2])]
    if mega:data+=['HiddenAbilities = '+','.join(p['abilities'][:2]),'MegaStone = '+p['megaStone']]
    elif len(p['abilities'])>2:data+=['HiddenAbilities = '+','.join(p['abilities'][2:])]
    level=p['learnset']['level'];data+=['Moves = '+','.join(str(v) for m in level for v in [m['level'],m['id']])]
    tutors=list(dict.fromkeys(m['id'] for kind in ['tm','tutor'] for m in p['learnset'][kind]));eggs=list(dict.fromkeys(m['id'] for m in p['learnset']['egg']))
    if tutors:data+=['TutorMoves = '+','.join(tutors)]
    if eggs:data+=['EggMoves = '+','.join(eggs)]
    if not mega:
        data+=['GenderRatio = '+('Genderless' if 'paradox' in p['category'] else 'Female50Percent'),'GrowthRate = Medium','BaseExp = 150','EVs = HP,1','CatchRate = 45','Happiness = 50','EggGroups = '+('Undiscovered' if 'paradox' in p['category'] else 'Field'),'HatchSteps = 5120','Height = 1.0','Weight = 1.0','Color = Blue','Shape = HeadArms','Category = Dessastre Paradoxal']
        evolutions=[]
        for target in entries:
            pre=target.get('preEvolution')
            if pre and pre[0]==p['id'] and not target['pending']:evolutions.extend([target['id'],pre[1],pre[2]])
        if evolutions:data+=['Evolutions = '+','.join(evolutions)]
    data+=['Pokedex = ????','Generation = 0','Flags = '+','.join(flags)]
    return '\n'.join(data)+'\n'

def make_plan(project,game):
    game=game.resolve()
    if not (game/'Data/Scripts.rxdata').is_file():raise ValueError('Instale a base local do jogo antes de importar.')
    manifest=json.loads((project/'data/dessastre-paradoxal.json').read_text(encoding='utf8'));entries=manifest['entries']
    archive=(project/'site/assets/fan-pokemon.tar.gz').read_bytes()
    if sha(archive)!=manifest['assetsSha256']:raise ValueError('O pacote de sprites nao corresponde ao manifesto.')
    blobs={}
    with tarfile.open(fileobj=io.BytesIO(archive),mode='r:gz') as tar:
        for member in tar:
            if not member.isfile() or not re.fullmatch(r'[A-Z][A-Z0-9_]*/[a-z-]+\.png',member.name) or member.size>2_000_000:raise ValueError('Entrada de sprite invalida.')
            blobs[member.name]=tar.extractfile(member).read()
    official={};existing=set();known_moves=set();known_abilities={'MEGASOL'}
    for path in (game/'PBS').glob('*.txt'):
        if path.name in OWN_PBS:continue
        text=path.read_text(encoding='utf-8-sig')
        for id,start,end in parse_sections(text):
            if path.name.startswith('pokemon') and not path.name.startswith('pokemon_metrics'):
                if id in existing:raise ValueError('Duplicated PBS ID: '+id)
                existing.add(id)
                if ',' not in id:official[id]=path
            if path.name.startswith('moves'):known_moves.add(id)
            if path.name.startswith('abilities'):known_abilities.add(id)
    plans={};ready=[p for p in entries if not p['pending']]
    for p in ready:
        if p['id'] in existing:raise ValueError('ID ja usado fora da geracao especial: '+p['id'])
        if not all(isinstance(n,int) and 1<=n<=255 for n in p['stats']):raise ValueError('Invalid stats: '+p['id'])
        if p.get('base') not in official and p.get('base'):raise ValueError('Missing mega base')
        if any(a not in known_abilities for a in p['abilities']):raise ValueError('Unknown ability: '+p['id'])
        if any(not isinstance(m['level'],int) or not 0<=m['level']<=100 for m in p['learnset']['level']):raise ValueError('Invalid move level: '+p['id'])
        for group in p['learnset'].values():
            if any(m['id'] not in known_moves for m in group):raise ValueError('Unknown move: '+p['id'])
    def put(path,data):
        target=(game/path).resolve()
        if not target.is_relative_to(game):raise ValueError('Unsafe target')
        plans[target]=data.encode('utf8') if isinstance(data,str) else data
    for mega,name in [(False,'pokemon_dessastre_paradoxal.txt'),(True,'pokemon_forms_dessastre_paradoxal.txt')]:
        put('PBS/'+name,'# Geracao especial autoral. Descricoes pendentes: ????\n#-------------------------------\n'+'#-------------------------------\n'.join(pbs_entry(p,ready) for p in ready if bool(p.get('base'))==mega))
    metrics='# Metricas de sprites estaticos normalizados; escala 1.\n'
    for p in ready:metrics+=f"#-------------------------------\n[{p['id']}]\nFrontSprite = 0,0,1\nBackSprite = 0,0,1\nShadowSprite = 0,0,2\n"
    put('PBS/pokemon_metrics_dessastre_paradoxal.txt',metrics)
    items='# Pedras das Mega Evolucoes autorais.\n'
    for p in ready:
        if p.get('megaStone'):items+=f"#-------------------------------\n[{p['megaStone']}]\nName = {p['base'].title()}ita DP\nNamePlural = {p['base'].title()}itas DP\nPocket = 6\nPrice = 0\nFlags = MegaStone,Fling_80\nDescription = Permite a Mega Evolucao de {p['base'].title()} em sua forma de Dessastre Paradoxal.\n"
    items+='#-------------------------------\n[DPSILICASCALE]\nName = Escama de Silica\nNamePlural = Escamas de Silica\nPocket = 1\nPrice = 0\nFieldUse = OnPokemon\nFlags = EvolutionStone\nDescription = Escama usada na evolucao de Spinedra quando seus dados de batalha estiverem definidos.\n'
    put('PBS/items_dessastre_paradoxal.txt',items)
    put('PBS/abilities_dessastre_paradoxal.txt','[MEGASOL]\nName = Mega Sol\nDescription = Seus golpes consideram sol intenso, sem mudar o clima ou beneficiar outros Pokemon.\n')
    # Preserve every existing branch while adding the author's new evolution routes.
    updated={}
    new_ids={p['id'] for p in ready}
    for p in ready:
        pre=p.get('preEvolution')
        if not pre or pre[0] in new_ids:continue
        if pre[0] not in official:raise ValueError('Missing evolutionary base: '+pre[0])
        path=official[pre[0]]
        if path not in updated:updated[path]=path.read_bytes().decode('utf8')
        updated[path]=append_evolution(updated[path],pre[0],[p['id'],pre[1],pre[2]])
    for path,text in updated.items():put(path.relative_to(game),text)
    for p in entries:
        for role,info in p['sprites'].items():
            if not info:continue
            blob=blobs.get(info['path'])
            if blob is None or sha(blob)!=info['sha256']:raise ValueError('Sprite hash mismatch: '+p['id'])
            # Draft sprites can be installed, but draft species are never compiled or battle-selectable.
            put('Graphics/Pokemon/'+ROLES[role]+'/'+p['fileId']+'.png',blob)
    for name in ['Generation.rb','RuntimeChecks.rb','meta.txt']:
        put('Plugins/ZZZ Dessastre Paradoxal/'+name,(project/'scripts/dessastre_paradoxal'/name).read_bytes())
    changed={p:b for p,b in plans.items() if not p.is_file() or p.read_bytes()!=b}
    return manifest,changed

def install(project,game,apply=False):
    manifest,plan=make_plan(project,game)
    result={'species':sum(not p.get('base') and not p['pending'] for p in manifest['entries']),'megaForms':sum(bool(p.get('base')) for p in manifest['entries']),'pending':sum(p['pending'] for p in manifest['entries']),'files':len(plan),'applied':False}
    if not apply or not plan:return result
    backup=project/'.blue-backups'/('dessastre-paradoxal-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));backup.mkdir(parents=True)
    previous={};applied=[]
    for target in plan:
        previous[target]=target.read_bytes() if target.is_file() else None
        if previous[target] is not None:atomic(backup/target.relative_to(game.resolve()),previous[target])
    for target in (game/'Data').glob('*.dat'):shutil.copy2(target,backup/target.name)
    cache=game/'Data/PluginScripts.rxdata'
    if cache.is_file():shutil.copy2(cache,backup/'PluginScripts.rxdata')
    report={**result,'targets':[str(p.relative_to(game.resolve())) for p in plan]};atomic(backup/'manifest.json',json.dumps(report,indent=2).encode())
    try:
        for target,data in plan.items():atomic(target,data);applied.append(target)
    except Exception:
        for target in reversed(applied):
            if previous[target] is not None:atomic(target,previous[target])
            else:target.unlink()
        raise
    return {**result,'applied':True,'backup':str(backup)}

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game-dir',type=Path,default=Path(os.environ.get('BLUE_GAME_DIR',PROJECT/'game')));parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    try:print(json.dumps(install(PROJECT,args.game_dir,args.apply),ensure_ascii=False,indent=2));return 0
    except (OSError,ValueError,KeyError,tarfile.TarError) as error:print('[ERRO]',error);return 1
if __name__=='__main__':raise SystemExit(main())
