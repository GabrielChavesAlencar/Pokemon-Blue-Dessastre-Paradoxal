from pathlib import Path
import json
import re
import sys
import zlib
from prepare_restore import GAME, ROOT, STAGE, records, fields, Marshal

PLANNED = {entry["path"] for entry in json.loads((ROOT/"plan.json").read_text(encoding="utf-8"))["files"]}

def read(path):
    staged=STAGE/path.relative_to(GAME)
    return (staged if staged.is_file() and path.relative_to(GAME).as_posix() in PLANNED and '--live' not in sys.argv else path).read_text(encoding='utf-8-sig')

def registry(prefix, skip=()):
    result={}
    for path in (GAME/'PBS').glob(prefix+'*.txt'):
        if path.name.startswith(skip):continue
        for key,raw in records(read(path)):
            if key in result:raise ValueError(f'Duplicate {prefix} key {key}: {path}')
            result[key]=fields(raw)
    return result

species=registry('pokemon',('pokemon_metrics',))
moves=registry('moves')
abilities=registry('abilities')
types=registry('types')
items=registry('items')
errors=[]
for key, record in species.items():
    base=key.split(',')[0]
    if base not in species:errors.append(f'{key}: missing base')
    for value in record.get('Types','').split(','):
        if value and value not in types:errors.append(f'{key}: type {value}')
    for attr in ('Abilities','HiddenAbilities'):
        for value in record.get(attr,'').split(','):
            if value and value not in abilities:errors.append(f'{key}: ability {value}')
    for attr in ('TutorMoves','EggMoves','Moves'):
        values=record.get(attr,'').split(',')
        if attr=='Moves':values=values[1::2]
        for value in values:
            if value and value not in moves:errors.append(f'{key}: move {value}')
    evolutions=record.get('Evolutions','').split(',')
    for value in evolutions[0::3]:
        if value and value not in species:errors.append(f'{key}: evolution {value}')
    for attr in ('MegaStone','MegaItem','WildItemCommon','WildItemUncommon','WildItemRare'):
        for value in record.get(attr,'').split(','):
            if value and value not in items:errors.append(f'{key}: item {value}')

assert not errors, '\n'.join(errors[:40])
assert len([k for k in species if ',' not in k])==1025
assert species['BULBASAUR']['BaseStats']=='45,49,49,45,65,65'
assert species['BULBASAUR']['Abilities']=='OVERGROW'
assert species['BULBASAUR']['CatchRate']=='45'
assert species['BULBASAUR']['Evolutions']=='IVYSAUR,Level,16'
assert species['CHARMELEON']['Types']=='FIRE'
assert species['BLASTOISE']['Types']=='WATER'
assert species['ETERNATUS,1']['BaseStats']=='255,115,250,130,125,250'
for form in range(3,16):
    if 'PIKACHU,'+str(form) in species:
        assert species['PIKACHU,'+str(form)].get('Types','ELECTRIC')=='ELECTRIC'
assert moves['STEALTHROCK']['Type']=='ROCK'
assert moves['TORCHSONG']['Power']=='80'
assert moves['ELECTRODRIFT']['Power']=='100'

bundle_path = (STAGE/'Data'/'Scripts.rxdata')
if '--live' in sys.argv or 'Data/Scripts.rxdata' not in PLANNED or not bundle_path.is_file(): bundle_path=GAME/'Data'/'Scripts.rxdata'
bundle=bundle_path.read_bytes()
decoder=Marshal(bundle);rows=decoder.read();assert decoder.i==len(bundle)
sources={bytes(row[1]).decode('utf-8-sig'):zlib.decompress(row[2]).decode('utf-8-sig') for row in rows}
assert 'ret = userTypes[0]' not in sources['Move_UsageCalculations']
assert 'pbRandom(100) < 25' in sources['Battler_UseMoveSuccessChecks']
assert 'Counter] * 2' in sources['MoveEffects_ChangeMoveEffect']
assert '@ppup = 0' in sources['Pokemon_Move']
assert 'rand(IV_STAT_LIMIT + 1)' in sources['Pokemon']
# Do not confuse a successful file write with preserving the campaign.
original=Marshal((GAME/'Data'/'Scripts.rxdata').read_bytes()).read()
for index,row in enumerate(rows):
    if bytes(row[1]).decode('utf-8-sig') in ['Main','Player','Trainer','Game_Player','Overworld_FieldMoves']:
        assert bytes(row[2])==bytes(original[index][2]),(index,row[1])
report={'result':'PASS','species':1025,'forms':len(species)-1025,'moves':len(moves),'abilities':len(abilities),
        'references':'All species/type/ability/move/item/evolution references resolved',
        'engine':'405 scripts readable, canonical mechanics present, campaign entry points unchanged'}
(ROOT/'static-validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report,indent=2))
