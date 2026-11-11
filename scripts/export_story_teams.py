"""Atualiza equipes da página História a partir do PBS local do Blue.

Não altere as equipes no navegador; execute após salvar treinadores no Blue Studio.
Sem game/PBS/trainers_story_mode.txt não substitui os dados de referência.
"""
from __future__ import annotations
import json
import sys
import zlib
from pathlib import Path
import re

ENTRY = re.compile(r'^\[([^,\]\n]+),([^\]\n]+)\]', re.M)
START_POKEMON = re.compile(r'^\s*Pokemon\s*=\s*([^,\r\n]+)\s*,\s*(\d+)', re.I)
FIELD = re.compile(r'^\s*(Moves|Item|Form|AbilityIndex|TeraType|Nature|IV|EV|DynamaxLv)\s*=\s*([^#\r\n]+)')
KEYS = {'Moves':'moves','Item':'item','Form':'form','AbilityIndex':'abilityIndex',
        'TeraType':'teraType','Nature':'nature','IV':'ivs','EV':'evs','DynamaxLv':'dynamaxLv'}

def campaign_rules_crc() -> int:
    root=Path(__file__).resolve().parent/'battle_polish'
    return zlib.crc32(b''.join((root/name).read_bytes() for name in ['Story.rb','Balance.rb','Campaign.rb']))

def campaign_profiles(game: Path, roster: dict, source: bytes) -> bool:
    """Only publish native profiles belonging to the same current PBS source."""
    crc=zlib.crc32(source);rules_crc=campaign_rules_crc()
    reference=game/'Data/blue-campaign-reference.dat'
    data=None
    if reference.is_file():
        sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
        from server.ruby_marshal import loads
        def normalize(value):
            if isinstance(value,bytes):return value.decode('utf8')
            if isinstance(value,dict):return {normalize(k):normalize(v) for k,v in value.items()}
            if isinstance(value,list):return [normalize(v) for v in value]
            return value
        candidate=normalize(loads(reference.read_bytes()))
        if candidate.get('version')==1 and candidate.get('sourceCRC')==crc and candidate.get('rulesCRC')==rules_crc:
            data=candidate
    if data:
        masters=data.get('masters',{})
        expected={'beginner','intermediate','advanced','master'}
        if len(masters)!=18 or any(len(v)!=4 or {p.get('id') for p in v}!=expected or
            any(p.get('origin')!='blue-engine' or len(p.get('team',[]))!=6 for p in v) for v in masters.values()):
            raise ValueError('Invalid native Full Doubles campaign reference.')
        for trainer in roster.get('masters',[]):
            if trainer['name'] not in masters:raise ValueError('Missing native leader: '+trainer['name'])
            trainer['campaignVariants']=masters[trainer['name']]
        roster['campaignSourceCRC']=crc
        roster['campaignRulesCRC']=rules_crc
        roster['campaignProfiles']='blue-engine-full-doubles'
        return True
    if roster.get('campaignSourceCRC') not in (None,crc) or roster.get('campaignRulesCRC') not in (None,rules_crc):
        for trainer in roster.get('masters',[]):trainer.pop('campaignVariants',None)
        roster.pop('campaignSourceCRC',None);roster.pop('campaignRulesCRC',None);roster.pop('campaignProfiles',None)
        print('Perfis de campanha antigos removidos: reexporte pela engine após alterar o PBS.')
        return True
    return False

def parse_teams(raw: str) -> dict[tuple[str, str], list[dict]]:
    found = list(ENTRY.finditer(raw))
    teams: dict[tuple[str, str], list[dict]] = {}
    for i, match in enumerate(found):
        body=raw[match.end():(found[i+1].start() if i+1<len(found) else len(raw))]
        team=[]
        for line in body.splitlines():
            if line.strip().startswith('#----------------'): break
            pokemon=START_POKEMON.match(line)
            if pokemon:
                team.append({'species':pokemon.group(1).strip().upper(),'level':int(pokemon.group(2))})
                continue
            field=FIELD.match(line)
            if field and team:
                value=field.group(2).strip()
                key=field.group(1)
                parsed=([x.strip() for x in value.split(',')] if key=='Moves'
                        else int(value) if key in ('Form','AbilityIndex','DynamaxLv') and value.isdigit()
                        else value)
                team[-1][KEYS[key]]=parsed
        if team: teams[(match.group(1).strip(),match.group(2).strip())]=team
    return teams


def sync_regular_trainers(raw: str, output: Path, roster: dict) -> int:
    """Synchronize regular trainer teams from the LOCAL game PBS when available.

    Preserve identities, locations and fallback data for entries not in the
    local file; do not replace the Gym/Master roster. The static JSON source
    is committed separately so the website also works without game assets.
    """
    import unicodedata
    target=output/'regular-trainers.json'
    if not target.is_file():
        return 0
    data=json.loads(target.read_text(encoding='utf8'))
    if not isinstance(data.get('trainers'),list):
        raise ValueError('Invalid regular trainer manifest.')
    parsed=parse_teams(raw)
    current={(t['trainerType'],t['name']):t for t in data['trainers']}
    protected={t['name'] for t in roster.get('masters',[])+roster.get('bosses',[])}
    changes=0
    for trainer in data['trainers']:
        team=parsed.pop((trainer['trainerType'],trainer['name']),None)
        if team is None:
            continue
        if team!=trainer['team'] or trainer.get('teamOrigin')!='blue-pbs':
            trainer['team']=team
            trainer['teamOrigin']='blue-pbs'
            changes+=1
    # New trainers authored directly in Blue Studio also appear in this tab.
    used={t['id'] for t in data['trainers']}
    for (category,name),team in sorted(parsed.items()):
        base=name.split(' (',1)[0]
        if base in protected or re.search(r'\((?:1v1|2v2|3v3)\s+(?:Basic|Full)\s+Power\)',name,re.I):
            continue
        safe=unicodedata.normalize('NFKD',category+'-'+name)
        safe=''.join(ch for ch in safe if not unicodedata.combining(ch))
        slug=re.sub(r'[^a-z0-9]+','-',safe.lower()).strip('-')
        if not slug:
            continue
        ident=slug
        suffix=2
        while ident in used:
            ident=f'{slug}-{suffix}'
            suffix+=1
        used.add(ident)
        trainer_class=' '.join(category.split('_')[2:]).replace('_',' ').title() or category
        data['trainers'].append({
            'id':ident,'name':name,'trainerType':category,
            'trainerClass':trainer_class,'location':'Local não informado',
            'team':team,'teamOrigin':'blue-pbs'
        })
        changes+=1
    if changes:
        data['basis']='Registros locais do Blue Studio onde teamOrigin=blue-pbs; demais preservados do PBS Decades'
        data['sourceCRC']=zlib.crc32(raw.encode('utf8'))
        target.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    return changes

def update_story_teams(game: Path, output: Path) -> int:
    source=game/'PBS'/'trainers_story_mode.txt'
    target=output/'story-trainers.json'
    if not source.is_file() or not target.is_file():
        print('story-trainers.json: PBS de treinadores ausente; mantida referência original')
        return 0
    roster=json.loads(target.read_text(encoding='utf-8'))
    rows=parse_teams(source.read_text(encoding='utf-8-sig'))
    count=0
    for trainer in roster.get('masters',[])+roster.get('bosses',[]):
        for variant in trainer.get('variants',[]):
            wanted=trainer['name']+' ('+variant['label']+')'
            possible=[(category,team) for (category,name),team in rows.items() if name==wanted]
            if len(possible)==1:
                variant['team']=possible[0][1]
                variant['origin']='blue-pbs'
                count+=1
    sync_regular_trainers(source.read_text(encoding='utf-8-sig'),output,roster)
    profiles_updated=campaign_profiles(game,roster,source.read_bytes())
    if count or profiles_updated:
        roster['version']='blue-pbs-with-reference-fallback'
        roster['basis']='Equipes sincronizadas com Blue Studio onde origin=blue-pbs; outras herdadas do Pokémon Decades'
        roster['syncedTeams']=count
        # Level-dependent native move series add many records; keep the portal's
        # shared payload compact rather than tripling it with indentation.
        options={'ensure_ascii':False}
        if roster.get('campaignProfiles'):options['separators']=(',',':')
        else:options['indent']=2
        target.write_text(json.dumps(roster,**options)+'\n',encoding='utf-8')
    print(f'story-trainers.json: {count} variantes sincronizadas do Blue Studio')
    return count

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    update_story_teams(root/'game',root/'site'/'public'/'data')
