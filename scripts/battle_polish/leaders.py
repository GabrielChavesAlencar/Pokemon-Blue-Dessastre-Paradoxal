"""Patch only the requested Pokemon slots in Story 2v2 Full Power; never rewrite other teams."""
from pathlib import Path
import json,re
STATS=['HP','ATTACK','DEFENSE','SPEED','SPECIAL_ATTACK','SPECIAL_DEFENSE'] # Essentials PBS order, not Showdown order.
HEADER=re.compile(r'^\[([^\]\r\n]+)\][^\r\n]*(?:\r?\n|$)',re.M)
POKEMON=re.compile(r'^([ \t]*Pokemon[ \t]*=[ \t]*)([A-Z0-9_]+)([ \t]*,[ \t]*)(\d+)([^\r\n]*)(?:\r?\n|$)',re.M)

def manifest(project):
    data=json.loads((project/'scripts/battle_polish/leaders_full_power.json').read_text(encoding='utf8'))
    rows=data['replacements']
    if data.get('version')!=1 or data.get('variant')!='2v2 Full Power' or len(rows)!=18 or len({r['leader'] for r in rows})!=18:raise ValueError('Invalid full-power leader manifest.')
    for row in rows:
        if len(row['moves'])!=4 or len(set(row['moves']))!=4 or not row['evs'] or set(row['evs'])-set(STATS):raise ValueError('Invalid leader moves/EV fields.')
        if any(type(n) is not int or not 0<=n<=252 for n in row['evs'].values()) or sum(row['evs'].values())>510:raise ValueError('Invalid EV distribution.')
    return data

def field(block,key,value,newline):
    pattern=re.compile(r'^([ \t]*)'+re.escape(key)+r'[ \t]*=[^\r\n]*(?:\r?\n|$)',re.M)
    found=list(pattern.finditer(block))
    if len(found)>1:raise ValueError('Duplicate Pokemon field: '+key)
    if found:
        m=found[0];return block[:m.start()]+m[1]+key+' = '+str(value)+newline+block[m.end():]
    # Insert after the Pokemon line, before trailing section comments/blank lines.
    first=POKEMON.match(block)
    if not first:raise ValueError('Invalid Pokemon slot.')
    return block[:first.end()]+'\t\t'+key+' = '+str(value)+newline+block[first.end():]

def transform(text,data):
    headers=list(HEADER.finditer(text));changes=[];seen=set()
    for pos,h in enumerate(headers):
        end=headers[pos+1].start() if pos+1<len(headers) else len(text)
        trainer=h[1].split(',',1)[-1].strip()
        rows=[r for r in data['replacements'] if trainer==r['leader']+' ('+data['variant']+')']
        if not rows:continue
        row=rows[0]
        if row['leader'] in seen:raise ValueError('Duplicate requested trainer: '+trainer)
        seen.add(row['leader']);body=text[h.end():end];newline='\r\n' if '\r\n' in body else '\n'
        slots=list(POKEMON.finditer(body));edits=[]
        candidates=[i for i,m in enumerate(slots) if m[2] in (row['from'],row['species'])]
        if len(candidates)!=1:raise ValueError('Expected one source or updated Pokemon in '+trainer)
        tasks=[(candidates[0],row)]
        for extra in data['extraItems']:
            if extra['leader']!=row['leader']:continue
            indexes=[i for i,m in enumerate(slots) if m[2]==extra['species']]
            if len(indexes)!=1:raise ValueError('Expected one '+extra['species']+' in '+trainer)
            tasks.append((indexes[0],extra))
        for index,edit in tasks:
            start=slots[index].start();stop=slots[index+1].start() if index+1<len(slots) else len(body)
            block=body[start:stop]
            if 'from' in edit:
                first=POKEMON.match(block)
                block=first[1]+edit['species']+first[3]+first[4]+first[5]+newline+block[first.end():]
                values={'Form':0,'Moves':','.join(edit['moves']),'Nature':edit['nature'],'AbilityIndex':edit['abilityIndex'],
                    'EV':','.join(str(edit['evs'].get(s,0)) for s in STATS),'Item':edit['item']}
                # Full-power defaults: keep offensive IVs usable after replacing a special/physical slot.
                ivs={s:31 for s in STATS}
                if edit['nature'] in ('QUIET','BRAVE','SASSY'):ivs['SPEED']=0
                if edit['nature'] in ('QUIET','MODEST','BOLD') and not any(m in edit['moves'] for m in ('FAKEOUT','UTURN')):ivs['ATTACK']=0
                values['IV']=','.join(str(ivs[s]) for s in STATS)
                for key,value in values.items():block=field(block,key,value,newline)
            else:block=field(block,'Item',edit['item'],newline)
            edits.append((start,stop,block))
        for start,stop,block in sorted(edits,reverse=True):body=body[:start]+block+body[stop:]
        changes.append((h.end(),end,body))
    missing={r['leader'] for r in data['replacements']}-seen
    if missing:raise ValueError('Missing full-power trainers: '+', '.join(sorted(missing)))
    for start,end,body in reversed(changes):text=text[:start]+body+text[end:]
    return text

def plan(project,game):
    path=game/'PBS/trainers_story_mode.txt'
    if not path.is_file():return {}
    original=path.read_bytes();bom=b'\xef\xbb\xbf' if original.startswith(b'\xef\xbb\xbf') else b''
    updated=transform(original.decode('utf-8-sig'),manifest(project))
    return {path:bom+updated.encode('utf8')}

def validation_rows(data):
    rows=[]
    for r in data['replacements']:
        ivs={s:31 for s in STATS}
        if r['nature'] in ('QUIET','BRAVE','SASSY'):ivs['SPEED']=0
        if r['nature'] in ('QUIET','MODEST','BOLD') and not any(m in r['moves'] for m in ('FAKEOUT','UTURN')):ivs['ATTACK']=0
        rows.append('\t'.join([r['leader'],r['species'],r['nature'],str(r['abilityIndex']),r['item'],
            ','.join(str(r['evs'].get(s,0)) for s in STATS),','.join(str(ivs[s]) for s in STATS),','.join(r['moves']),r['from']]))
    return ('\n'.join(rows)+'\n').encode('utf8')
