"""Install the author's special generation from a checked-in manifest and sprite bundle."""
from __future__ import annotations
import argparse,hashlib,importlib.util,io,json,os,re,shutil,sys,tarfile,tempfile
from datetime import datetime,timezone
from pathlib import Path
PROJECT=Path(__file__).resolve().parents[2]
OWN_PBS={'pokemon_dessastre_paradoxal.txt','pokemon_forms_dessastre_paradoxal.txt','pokemon_forms_future_eevee.txt','pokemon_metrics_dessastre_paradoxal.txt','items_dessastre_paradoxal.txt','abilities_dessastre_paradoxal.txt'}
ROLES={'front':'Front','front-shiny':'Front shiny','back':'Back','back-shiny':'Back shiny','icon':'Icons','icon-shiny':'Icons shiny','footprint':'Footprints'}
def future_module():
    spec=importlib.util.spec_from_file_location('blue_future_eevee',Path(__file__).with_name('future_eevee.py'))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

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
        data+=['GenderRatio = '+('Genderless' if 'paradox' in p['category'] else 'Female50Percent'),'GrowthRate = Medium','BaseExp = 150','EVs = HP,1','CatchRate = 45','Happiness = 50','EggGroups = '+('Undiscovered' if 'paradox' in p['category'] else 'Field'),'HatchSteps = 5120','Height = '+str(p.get('height') or 1.0),'Weight = '+str(p.get('weight') or 1.0),'Color = Blue','Shape = HeadArms','Category = Dessastre Paradoxal']
        evolutions=[]
        for target in entries:
            pre=target.get('preEvolution')
            if pre and pre[0]==p['id'] and not target['pending']:evolutions.extend([target['id'],pre[1],pre[2]])
        if evolutions:data+=['Evolutions = '+','.join(evolutions)]
    data+=['Pokedex = '+p.get('description','????'),'Generation = 0','Flags = '+','.join(flags)]
    return '\n'.join(data)+'\n'

def extra_assets(project,game):
    source=project/'data/fan-assets.json'
    if not source.is_file():return {}
    manifest=json.loads(source.read_text(encoding='utf8'))
    compressed=(project/'site/assets/fan-extras.tar.gz').read_bytes()
    if sha(compressed)!=manifest['archiveSha256']:raise ValueError('Pacote de cries e pedras corrompido.')
    expected={p['path']:p for p in manifest['files']};result={};seen=set()
    with tarfile.open(fileobj=io.BytesIO(compressed),mode='r:gz') as archive:
        for member in archive:
            if member.name not in expected or member.name in seen or not member.isfile() or member.size>2_000_000:raise ValueError('Asset autoral invalido.')
            entry=expected[member.name];data=archive.extractfile(member).read()
            if sha(data)!=entry['sha256']:raise ValueError('Hash de asset incorreto: '+member.name)
            target=entry['target']
            if not re.fullmatch(r'(?:Audio/SE/Cries/[A-Z0-9_]+\.wav|Graphics/Items/DP[A-Z0-9_]+\.png)',target):raise ValueError('Destino de asset invalido.')
            destination=(game/target).resolve()
            if not destination.is_relative_to(game.resolve()):raise ValueError('Destino de asset fora da instalacao.')
            result[destination]=data;seen.add(member.name)
    if seen!=set(expected):raise ValueError('Pacote autoral incompleto.')
    return result

def distribute(weights,total):
    exact=[w*total/sum(weights) for w in weights]
    result=[int(x) for x in exact]
    for i in sorted(range(len(result)),key=lambda i:(exact[i]-result[i],-i),reverse=True)[:total-sum(result)]:result[i]+=1
    if min(result)<1:raise ValueError('Quantidade de slots supera a precisao das chances.')
    return result

def update_encounters(text,entries,config=None):
    if config and config.get('version')==2:return spread_encounters(text,entries,config)
    config=config or {'authorPoolPercent':50,'areas':[{'mapId':156,'category':'past_paradox','method':'Land'},{'mapId':157,'category':'future_paradox','method':'Land'}]}
    pool=config['authorPoolPercent']
    if type(pool) is not int or not 1<=pool<=99:raise ValueError('Percentual de encontros invalido.')
    all_ids={p['id'] for p in entries if not p.get('base')}
    for area in config['areas']:
        map_id,category,method=area['mapId'],area['category'],area['method']
        if type(map_id) is not int or not re.fullmatch(r'[A-Za-z]+',method):raise ValueError('Area de encontro invalida.')
        fans=sorted(p['id'] for p in entries if p['category']==category and not p['pending'])
        if not fans:continue
        sections=parse_sections(text)
        section=next((s for s in sections if s[0]==str(map_id)),None)
        if not section:raise ValueError('Area Paradoxo nao encontrada: '+str(map_id))
        _,start,end=section;block=text[start:end]
        match=re.search(r'(?m)^'+re.escape(method)+r',\d+[^\r\n]*\r?\n((?:[ \t]+\d+,[^\r\n]+\r?\n)+)',block)
        if not match:raise ValueError('Tabela terrestre nao reconhecida: '+str(map_id))
        rows=[]
        for line in match[1].splitlines():
            cells=[s.strip() for s in line.split(',')]
            if cells[1] not in all_ids:rows.append(cells)
        if not rows:raise ValueError('Encontros originais ausentes.')
        originals=distribute([int(row[0]) for row in rows],100-pool)
        author=distribute([1]*len(fans),pool)
        newline='\r\n' if '\r\n' in block else '\n'
        lines=['    '+','.join([str(weight),*row[1:]]) for row,weight in zip(rows,originals)]
        low,high=rows[0][2],rows[0][3] if len(rows[0])>3 else None
        lines+=['    '+','.join([str(weight),id,low]+([high] if high else [])) for id,weight in zip(fans,author)]
        new=block[:match.start(1)]+newline.join(lines)+newline+block[match.end(1):]
        text=text[:start]+new+text[end:]
    return text

def spread_encounters(text,entries,config):
    """Replace rare slots deterministically, including migration from both grottos."""
    chance=config.get('chancePerSpecies')
    if type(chance) is not int or not 1<=chance<100:raise ValueError('Chance por especie invalida.')
    known={p['id']:p for p in entries};author={p['id'] for p in entries if not p.get('base')}
    plans={};found=set()
    for area in config['areas']:
        key=(area['mapId'],area['method']);ids=area['species']
        if type(key[0]) is not int or not re.fullmatch(r'[A-Za-z]+',key[1]) or key in plans:raise ValueError('Area de encontro invalida ou duplicada.')
        if not ids or len(ids)!=len(set(ids)) or len(ids)*chance>=100:raise ValueError('Distribuicao de encontros invalida.')
        for id in ids:
            p=known.get(id)
            if not p or p.get('base') or p['pending'] or p['category'] not in ('past_paradox','future_paradox'):raise ValueError('Paradoxo nao liberado: '+id)
        plans[key]=ids
    pattern=re.compile(r'(?m)^([A-Za-z]+),\d+[^\r\n]*\r?\n((?:[ \t]+\d+,[^\r\n]+(?:\r?\n|$))+)')
    for header,start,end in reversed(parse_sections(text)):
        map_id=int(header.split(',')[0]);block=text[start:end]
        def replace(match):
            key=(map_id,match[1]);ids=plans.get(key,[])
            cells=[[s.strip() for s in line.split(',')] for line in match[2].splitlines() if line.strip()]
            base=[row for row in cells if row[1] not in author]
            if not ids and len(base)==len(cells):return match[0]
            if not base:raise ValueError('Encontros originais ausentes: '+str(key))
            weights=distribute([int(row[0]) for row in base],100-len(ids)*chance)
            newline='\r\n' if '\r\n' in match[0] else '\n'
            rows=['    '+','.join([str(w),*row[1:]]) for row,w in zip(base,weights)]
            rows+=['    '+','.join([str(chance),id,*base[0][2:]]) for id in ids]
            if ids:found.add(key)
            return match[0][:match.start(2)-match.start()]+newline.join(rows)+newline
        block=pattern.sub(replace,block);text=text[:start]+block+text[end:]
    if found!=set(plans):raise ValueError('Tabelas de encontro ausentes: '+str(sorted(set(plans)-found)))
    return text

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
    metrics='# Metricas de batalha da geracao autoral; frente 2x e costas 1x.\n'
    # The Decades engine's default FRONT_BATTLER_SPRITE_SCALE is 2.
    # An explicit scale of 1 shrank every author sprite relative to native Pokemon.
    # Do not change back sprite scale or any source PNGs.
    for p in ready:metrics+=f"#-------------------------------\n[{p['id']}]\nFrontSprite = 0,0,2\nBackSprite = 0,0,1\nShadowSprite = 0,0,2\n"
    future=future_module()
    future_manifest=future.load_manifest(project)
    form_pbs,skipped_moves,skipped_abilities=future.build_forms(future_manifest,known_moves,known_abilities)
    if skipped_abilities:raise ValueError('Regional Eevee abilities missing from engine: '+','.join(skipped_abilities))
    put('PBS/pokemon_forms_future_eevee.txt',form_pbs)
    for entry in future_manifest['forms']:
        p=entry['card']
        metrics+=f"#-------------------------------\n[{p['base']},50]\nFrontSprite = 0,0,2\nBackSprite = 0,0,1\nShadowSprite = 0,0,2\n"
    put('PBS/pokemon_metrics_dessastre_paradoxal.txt',metrics)
    put('Data/blue-future-eevee-compatibility.txt',
        'Golpes do estudo que nao existem neste PBS (nao compilados):\n'+
        ('\n'.join(skipped_moves) if skipped_moves else 'Nenhum')+'\n')
    for graphic,blob in future.extract_sprites(project,future_manifest).items():
        put(graphic,blob)
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
    for name in ['Generation.rb','FutureEevee.rb','RuntimeChecks.rb','meta.txt']:
        put('Plugins/ZZZ Dessastre Paradoxal/'+name,(project/'scripts/dessastre_paradoxal'/name).read_bytes())
    for path,data in extra_assets(project,game).items():plans[path]=data
    encounters=game/'PBS/encounters.txt'
    encounter_text=encounters.read_bytes().decode('utf8')
    if (project/'data/fan-encounters.json').is_file():
        config=json.loads((project/'data/fan-encounters.json').read_text(encoding='utf8'))
        encounter_text=update_encounters(encounter_text,entries,config)
    regional_config=json.loads((project/'data/eevee-regional-encounters.json').read_text(encoding='utf8'))
    paradox_ids={p['id'] for p in entries if p['category'] in ('past_paradox','future_paradox')}
    put('PBS/encounters.txt',future.regional_encounters(encounter_text,regional_config,paradox_ids))
    trainer_file=game/'PBS/trainers_story_mode.txt'
    if trainer_file.is_file():
        trainer_config=json.loads((project/'data/eevee-regional-trainers.json').read_text(encoding='utf8'))
        changed_trainers,number_added=future.patch_trainers(trainer_file.read_text(encoding='utf-8-sig'),trainer_config)
        if number_added:put('PBS/trainers_story_mode.txt',changed_trainers)
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
