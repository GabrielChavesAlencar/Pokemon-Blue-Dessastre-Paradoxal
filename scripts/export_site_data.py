"""Export factual game data for the public Blue portal; no game assets or saves."""
from __future__ import annotations
import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import re

HEADER = re.compile(r'^\s*\[([^\]]+)\]\s*(?:#\s*(.*))?$')

def sections(path):
    result=[];current=None
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        match=HEADER.match(line)
        if match:
            current={'id':match[1].strip().upper(),'comment':match[2] or '', 'fields':{}}
            result.append(current)
        elif current is not None and '=' in line and not line.lstrip().startswith('#'):
            key,value=line.split('=',1);current['fields'][key.strip()]=value.split('#',1)[0].strip()
    return result

def values(raw):return [part.strip() for part in raw.split(',') if part.strip()]

def export(game,output):
    pbs=game/'PBS';output.mkdir(parents=True,exist_ok=True)
    species=[];forms=[];lookup={};details={}
    base_files=sorted(pbs.glob('pokemon*.txt'))
    base_files.sort(key=lambda p:(p.name!='pokemon.txt',p.name))
    for path in base_files:
        if path.name.startswith('pokemon_metrics'):continue
        for section in sections(path):
            key=section['id'];f=section['fields']
            if key in lookup:raise ValueError('Duplicate species: '+key)
            lookup[key]=f
            (forms if ',' in key else species).append((key,f,path.name))
    catalogue=[]
    for number,(key,f,source) in enumerate(species,1):
        stats=[int(n) for n in values(f.get('BaseStats','1,1,1,1,1,1'))]
        catalogue.append({'id':key,'number':number,'name':f.get('Name',key),
            'types':values(f.get('Types','NORMAL')),'stats':stats,'generation':int(f.get('Generation','1')),
            'flags':values(f.get('Flags','')),'height':float(f.get('Height','0')),'weight':float(f.get('Weight','0')),
            'forms':sum(1 for form,_,_ in forms if form.split(',')[0]==key)})
    for key,f,source in species+forms:
        moves=values(f.get('Moves',''))
        detail={'abilities':values(f.get('Abilities','')),'hidden':values(f.get('HiddenAbilities','')),
                'moves':[[int(moves[i]),moves[i+1]] for i in range(0,len(moves)-1,2)],
                'tutor':values(f.get('TutorMoves','')),'egg':values(f.get('EggMoves','')),
                'evolutions':[[x.strip() for x in f['Evolutions'].split(',')][i:i+3] for i in range(0,len(f.get('Evolutions','').split(',')),3)] if f.get('Evolutions') else [],
                'catchRate':int(f.get('CatchRate','0'))}
        if ',' in key:
            detail.update({'name':f.get('FormName','Forma '+key.split(',')[1]),'base':key.split(',')[0],
                           'form':int(key.split(',')[1]),'types':values(f.get('Types','')),
                           'stats':[int(n) for n in values(f.get('BaseStats',''))],
                           'megaStone':f.get('MegaStone'),'gmaxMove':f.get('GmaxMove'),
                           'exclusive':('gmax_megas' in source and key!='GRENINJA,3') or 'xd001' in source or key=='GRENINJA,4',
                           'own':[field for field in ['Abilities','HiddenAbilities','Moves','TutorMoves','EggMoves','Evolutions'] if field in f]})
        details[key]=detail
    moves={};abilities={};items={}
    for path in sorted(pbs.glob('moves*.txt')):
        for s in sections(path):
            f=s['fields'];moves[s['id']]={'name':f.get('Name',s['id']),'type':f.get('Type','NORMAL'),
                'power':int(f.get('Power','0')),'accuracy':int(f.get('Accuracy','0')),
                'pp':int(f.get('TotalPP','0')),'category':f.get('Category','Status')}
    for path in sorted(pbs.glob('abilities*.txt')):
        for s in sections(path):abilities[s['id']]=s['fields'].get('Name',s['id'])
    for path in sorted(pbs.glob('items*.txt')):
        for s in sections(path):items[s['id']]=s['fields'].get('Name',s['id'])
    metadata={int(s['id']):s['fields'] for s in sections(pbs/'map_metadata.txt')}
    locations={};current=None;method=None
    for raw in (pbs/'encounters.txt').read_text(encoding='utf-8-sig').splitlines():
        line=raw.split('#',1)[0].strip()
        if not line:continue
        match=HEADER.match(raw.strip())
        if match:
            parts=[int(n) for n in match[1].split(',')];map_id=parts[0];version=parts[1] if len(parts)>1 else 0
            fields=metadata.get(map_id,{})
            area=locations.setdefault(map_id,{'id':map_id,'name':fields.get('Name') or match[2] or f'Área {map_id}',
                 'outdoor':fields.get('Outdoor','false')=='true','position':values(fields.get('MapPosition','')),'versions':[]})
            current={'id':version,'methods':[]};area['versions'].append(current);method=None
        elif current is not None:
            row=next(csv.reader([line]))
            if not row[0].isdigit():
                method={'id':row[0],'rate':int(row[1]) if len(row)>1 else None,'slots':[]};current['methods'].append(method)
            elif method is not None:
                species_id=row[1].upper();low=int(row[2]);high=int(row[3]) if len(row)>3 else low
                method['slots'].append([species_id,low,high,int(row[0])])
    for area in locations.values():
        area['species']=sorted({slot[0] for v in area['versions'] for m in v['methods'] for slot in m['slots']})
    encounter_forms={}
    for area in locations.values():
        for key in area['species']:
            if key in details:continue
            base,_,form=key.rpartition('_')
            detail=details.get(base+','+form)
            if not detail:raise ValueError('Unknown encounter species: '+key)
            encounter_forms[key]={'base':base,'form':int(form),'name':detail['name']}
    generated=datetime.now(timezone.utc).isoformat()
    index={'updatedAt':generated,'species':catalogue,'counts':{'species':len(species),'forms':len(forms),
           'locations':len(locations),'moves':len(moves),'paradox':sum('Paradox' in x['flags'] for x in catalogue)},
           'encounterForms':encounter_forms,
           'basis':'Dados atuais do projeto, com referências da geração 9'}
    payloads={'catalog.json':index,'details.json':{'species':details,'moves':moves,'abilities':abilities,'items':items},
              'locations.json':{'updatedAt':generated,'locations':sorted(locations.values(),key=lambda x:x['id'])}}
    for name,data in payloads.items():
        path=output/name;path.write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8',newline='\n')
        print(name,path.stat().st_size)
    print(json.dumps(index['counts']))

if __name__=='__main__':
    project=Path(__file__).resolve().parents[1]
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game-dir',type=Path,default=project/'game')
    parser.add_argument('--output',type=Path,default=project/'site'/'public'/'data')
    args=parser.parse_args();export(args.game_dir,args.output)
