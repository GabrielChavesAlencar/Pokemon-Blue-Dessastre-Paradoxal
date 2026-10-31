"""Atualiza equipes da página História a partir do PBS local do Blue.

Não altere as equipes no navegador; execute após salvar treinadores no Blue Studio.
Sem game/PBS/trainers_story_mode.txt não substitui os dados de referência.
"""
from __future__ import annotations
import json
from pathlib import Path
import re

ENTRY = re.compile(r'^\[([^,\]\n]+),([^\]\n]+)\]', re.M)
START_POKEMON = re.compile(r'^\s*Pokemon\s*=\s*([^,\r\n]+)\s*,\s*(\d+)', re.I)
FIELD = re.compile(r'^\s*(Moves|Item|Form|AbilityIndex|TeraType|Nature|IV|EV|DynamaxLv)\s*=\s*([^#\r\n]+)')
KEYS = {'Moves':'moves','Item':'item','Form':'form','AbilityIndex':'abilityIndex',
        'TeraType':'teraType','Nature':'nature','IV':'ivs','EV':'evs','DynamaxLv':'dynamaxLv'}

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
                team[-1][KEYS[field.group(1)]]=[x.strip() for x in value.split(',')] if field.group(1)=='Moves' else value
        if team: teams[(match.group(1).strip(),match.group(2).strip())]=team
    return teams

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
    if count:
        roster['version']='blue-pbs-with-reference-fallback'
        roster['basis']='Equipes sincronizadas com Blue Studio onde origin=blue-pbs; outras herdadas do Pokémon Decades'
        roster['syncedTeams']=count
        target.write_text(json.dumps(roster,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'story-trainers.json: {count} variantes sincronizadas do Blue Studio')
    return count

if __name__=='__main__':
    root=Path(__file__).resolve().parents[1]
    update_story_teams(root/'game',root/'site'/'public'/'data')
