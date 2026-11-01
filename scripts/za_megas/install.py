"""Apply the supplied ZA catalogue to the campaign and the native Battle Hub."""
from pathlib import Path
import importlib.util,json,re,sys
FILES=['Megas.rb','Validation.rb','meta.txt']
ORDER=['HP','ATTACK','DEFENSE','SPEED','SPECIAL_ATTACK','SPECIAL_DEFENSE']
ABILITIES={
 'DRAGONIZE':('Dragonize','Normal moves become Dragon type and gain 20% power.'),
 'PIERCINGDRILL':('Piercing Drill','Contact moves bypass protection, dealing one quarter of normal damage.'),
 'EELEVATE':('Eelevate','Floats above the ground and raises its highest stat after a knockout.'),
 'FIREMANE':('Fire Mane','Powers up Fire-type attacks by 50%.'),
 'AURAGUARD':('Aura Guard','Halves damage taken from contact moves.'),
 'SPICYSPRAY':('Spicy Spray','Burns the attacker when damaged by a move.')}

def field(block,key,default=''):
    m=re.search(r'^'+re.escape(key)+r'\s*=\s*([^\r\n]*)',block,re.M)
    return m[1].strip() if m else default
def set_field(block,key,value):
    line=key+' = '+value
    if re.search(r'^'+re.escape(key)+r'\s*=',block,re.M):
        return re.sub(r'^'+re.escape(key)+r'\s*=[^\r\n]*',lambda m:line,block,flags=re.M)
    return block.rstrip()+'\n'+line+'\n'
def apply_catalog(text,entries):
    wanted={f"{e['species']},{form}":e for e in entries for form in e['forms']}
    seen=set()
    def replace(match):
        key,block=match[1],match[0]
        if key not in wanted:return block
        seen.add(key);e=wanted[key]
        block=set_field(block,'BaseStats',','.join(str(e['stats'][s]) for s in ORDER))
        block=set_field(block,'Types',','.join(e['types']))
        block=set_field(block,'MegaStone',e['stone'])
        if e['ability']:
            block=set_field(block,'Abilities',e['ability'])
            block=set_field(block,'HiddenAbilities',e['ability'])
        else:
            flags=[f for f in field(block,'Flags').split(',') if f]
            if 'BlueZAProvisionalAbility' not in flags:flags.append('BlueZAProvisionalAbility')
            block=set_field(block,'Flags',','.join(flags))
        return block
    result=re.sub(r'^\[([^\]\r\n]+)\][\s\S]*?(?=^\[|\Z)',replace,text,flags=re.M)
    if seen!=set(wanted):raise ValueError('Base ZA incompleta: '+', '.join(sorted(set(wanted)-seen)))
    return result

def install(project,game):
    # Reuse the transaction/backup implementation shared by our other plugins.
    spec=importlib.util.spec_from_file_location('blue_za_atomic',project/'scripts/battle_polish/install.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    catalog=json.loads((project/'data/za-megas.json').read_text(encoding='utf8'))
    entries=catalog['entries'];pbs=game/'PBS/pokemon_forms_PLZA_megas.txt'
    if not pbs.is_file():raise ValueError('Formas PLZA ausentes na base instalada.')
    plans={pbs:apply_catalog(pbs.read_text(encoding='utf-8-sig'),entries).encode('utf8')}
    stones={e['stone']:e for e in entries}
    lines=[]
    for id,e in stones.items():
        lines.extend([f'[{id}]','Name = '+e['stoneName'],'NamePlural = '+e['stoneName']+'s','Pocket = 6','Price = 0','BPPrice = 50','Flags = MegaStone,Fling_80','Description = Enables '+e['name'].split(' (')[0]+' when held by its compatible Pokemon.','#-------------------------------'])
        # Existing fangame art stays local. Distinct item IDs work even when
        # only the base's generic Mega Stone icon is available.
        icon=game/'Graphics/Items'/f'{id}.png'
        fallback=game/'Graphics/Items/MEGAITE.png'
        if not icon.is_file() and fallback.is_file():plans[icon]=fallback.read_bytes()
    plans[game/'PBS/items_blue_za.txt']=('\n'.join(lines)+'\n').encode('utf8')
    abilities=[]
    for id,(name,description) in ABILITIES.items():
        abilities.extend([f'[{id}]','Name = '+name,'Description = '+description,'#-------------------------------'])
    plans[game/'PBS/abilities_blue_za.txt']=('\n'.join(abilities)+'\n').encode('utf8')
    plugin=game/'Plugins/ZZZZ Blue ZA Megas'
    for name in FILES:plans[plugin/name]=(project/'scripts/za_megas'/name).read_bytes()
    plans[plugin/'catalog.json']=(json.dumps(catalog,ensure_ascii=True)+'\n').encode('ascii')
    records=[]
    for e in entries:
        for form in e['forms']:
            records.append('{species: :'+e['species']+', form: '+str(form)+', stats: ['+','.join(str(e['stats'][s]) for s in ORDER)+'], types: [:'+ ', :'.join(e['types'])+'], stone: :'+e['stone']+', ability: '+(':'+e['ability'] if e['ability'] else 'nil')+'}')
    plans[plugin/'Catalog.rb']=('module BlueZAMegas\n  CATALOG = [\n    '+',\n    '.join(records)+'\n  ].freeze\nend\n').encode('ascii')
    changed={p:b for p,b in plans.items() if not p.is_file() or p.read_bytes()!=b}
    from datetime import datetime,timezone
    backup=project/'.blue-backups'/('za-megas-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    previous={p:p.read_bytes() if p.is_file() else None for p in changed};written=[]
    for p,b in previous.items():
        if b is not None:module.atomic(backup/p.relative_to(game),b)
    try:
        for p,b in changed.items():module.atomic(p,b);written.append(p)
    except Exception:
        for p in reversed(written):
            if previous[p] is None:p.unlink()
            else:module.atomic(p,previous[p])
        raise
    return len(changed)
if __name__=='__main__':
    root=Path(__file__).resolve().parents[2]
    print('Arquivos ZA atualizados:',install(root,root/'game'))
