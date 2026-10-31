"""Prepare a bounded restoration of canonical species/moves and battle rules.

References: Essentials v21.1 and Caruban's unmodified Generation 9 Pack v3.3.3.
No maps, events, encounters, trainer teams, graphics or audio are replaced.
"""
from pathlib import Path
import os
import collections
import hashlib
import json
import re
import zlib

CODE = Path(__file__).resolve().parent
PROJECT = CODE.parents[1]
ROOT = Path(os.environ.get("BLUE_RESTORE_WORK_DIR", str(PROJECT / ".blue-work" / "official-rules"))).resolve()
GAME = Path(os.environ.get("BLUE_GAME_DIR", str(PROJECT / "game"))).resolve()
STAGE = ROOT / "staged"
GEN9 = ROOT / "gen9-reference"
ESS = ROOT / "essentials-reference"
PLAN = []

class RubyString(bytes):
    pass

class Symbol(bytes):
    pass

class Marshal:
    def __init__(self, raw):
        assert raw[:2] == b"\x04\x08"
        self.raw, self.i, self.objects, self.symbols = raw, 2, [], []

    def number(self):
        n = int.from_bytes(self.raw[self.i:self.i+1], "little", signed=True)
        self.i += 1
        if n == 0: return 0
        if n > 4: return n-5
        if n < -4: return n+5
        size = abs(n)
        v = int.from_bytes(self.raw[self.i:self.i+size], "little")
        self.i += size
        return v if n > 0 else v - (1 << (size*8))

    def read(self):
        t = chr(self.raw[self.i]); self.i += 1
        if t == "[":
            a = []; self.objects.append(a)
            for _ in range(self.number()): a.append(self.read())
            return a
        if t == "i": return self.number()
        if t in ('"', ':'):
            n = self.number()
            v = (RubyString if t == '"' else Symbol)(self.raw[self.i:self.i+n])
            self.i += n
            (self.objects if t == '"' else self.symbols).append(v)
            return v
        if t == 'I':
            v = self.read()
            v.ivars = [(self.read(), self.read()) for _ in range(self.number())]
            return v
        if t == '@': return self.objects[self.number()]
        if t == ';': return self.symbols[self.number()]
        if t == 'T': return True
        if t == 'F': return False
        if t == '0': return None
        raise ValueError(f"Unsupported Marshal tag {t!r} at {self.i}")

def integer(n):
    if n == 0: return b'\x00'
    if 0 < n < 123: return bytes([n+5])
    if -124 < n < 0: return bytes([(n-5) & 255])
    size = next(s for s in range(1, 5) if (0 <= n < 256**s) or (-256**s <= n < 0))
    return bytes([size if n > 0 else (-size & 255)]) + (n % 256**size).to_bytes(size, 'little')

def dump(v):
    if v is None: return b'0'
    if v is True: return b'T'
    if v is False: return b'F'
    if isinstance(v, int): return b'i' + integer(v)
    if isinstance(v, list): return b'[' + integer(len(v)) + b''.join(dump(x) for x in v)
    if isinstance(v, Symbol): return b':' + integer(len(v)) + bytes(v)
    if isinstance(v, bytes):
        raw = b'"' + integer(len(v)) + bytes(v)
        attrs = getattr(v, 'ivars', None)
        if attrs: raw = b'I' + raw + integer(len(attrs)) + b''.join(dump(k)+dump(x) for k,x in attrs)
        return raw
    raise TypeError(type(v))

def digest(data): return hashlib.sha256(data).hexdigest()

def stage(relative, data, reason):
    if isinstance(data, str): data = data.encode('utf-8')
    target = GAME / relative
    previous = target.read_bytes() if target.is_file() else None
    if previous == data: return
    output = STAGE / relative
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    PLAN.append(dict(path=relative.replace('\\','/'), reason=reason,
                     before=digest(previous) if previous is not None else None,
                     after=digest(data), size=len(data)))

HEADER = re.compile(r'^[ \t]*\[([^\]\r\n]+)\][ \t]*(?:#.*)?$', re.M)

def records(text):
    headers = list(HEADER.finditer(text))
    return [(m.group(1).strip().upper(), text[m.start():headers[i+1].start() if i+1<len(headers) else len(text)])
            for i,m in enumerate(headers)]

def catalog(paths):
    result = {}
    for path in paths:
        for key, raw in records(path.read_text(encoding='utf-8-sig')):
            if key in result and result[key] != raw: raise ValueError(f'Duplicate reference: {key}')
            result[key] = raw
    return result

def fields(text):
    return {m.group(1):m.group(2).split('#',1)[0].strip()
            for m in re.finditer(r'^[ \t]*(\w+)[ \t]*=[ \t]*(.*)$',text,re.M)}

def restore_records(path, canonical):
    text = path.read_text(encoding='utf-8-sig')
    blocks = records(text)
    prefix = text[:HEADER.search(text).start()] if blocks else text
    changed = matched = 0
    updated = []
    for key, raw in blocks:
        new = canonical.get(key, raw)
        if key in canonical:
            # The campaign distributes universal Mega Stones. Preserve that
            # resource binding while restoring the form's canonical battle data.
            current=fields(raw)
            if ',' in key and current.get('MegaStone'):
                stone='MegaStone = '+current['MegaStone']
                if re.search(r'(?m)^MegaStone\s*=',new):
                    new=re.sub(r'(?m)^MegaStone\s*=.*$',stone,new)
                else:new=new.rstrip()+'\n'+stone+'\n'
            matched += 1
            if fields(new) != fields(raw): changed += 1
        updated.append(new.rstrip()+'\n#-------------------------------\n')
    result = prefix + ''.join(updated)
    assert [k for k,_ in records(result)] == [k for k,_ in blocks]
    for key,raw in records(result):
        if key in canonical:
            expected=fields(canonical[key]);actual=fields(raw)
            if ',' in key and fields(dict(blocks)[key]).get('MegaStone'):
                expected['MegaStone']=fields(dict(blocks)[key])['MegaStone']
            assert actual==expected,(path.name,key)
    if changed: stage(str(path.relative_to(GAME)), result, f'{changed} canonical records restored; {matched} matched')
    return dict(file=path.name, changed=changed, matched=matched, exclusive=len(blocks)-matched)

def preserve_extra_classes(canonical, local):
    class_re = re.compile(r'^class ([A-Za-z0-9_:]+)(?:[^\r\n]*)$',re.M)
    known = {m.group(1) for m in class_re.finditer(canonical)}
    starts = list(class_re.finditer(local))
    extras = [local[m.start():starts[i+1].start() if i+1<len(starts) else len(local)]
              for i,m in enumerate(starts) if m.group(1) not in known]
    return canonical.rstrip()+'\n\n'+ '\n'.join(extras) if extras else canonical

def prepare():
    vanilla = GEN9/'PBS'/'Gen 9 backup'/'Vanilla PBS Files (with updates)'
    species = catalog([vanilla/'pokemon.txt', vanilla/'pokemon_forms.txt',
                       GEN9/'PBS'/'pokemon_base_Gen_9_Pack.txt',GEN9/'PBS'/'pokemon_forms_Gen_9_Pack.txt'])
    stock = GAME/'[0] Mods (Use if you are RetroNC and want Vanilla Gen 9)'/'Basic Vanilla Gen 9 Patch'/'[4] Stock Vanilla PBS'/'PBS'
    for name in ['pokemon_forms_gmax.txt','pokemon_forms_pikachu_caps.txt','pokemon_forms_pikachu_cosplay.txt']:
        species.update(catalog([stock/name]))
    moves = catalog([vanilla/'moves.txt',GEN9/'PBS'/'moves_Gen_9_Pack.txt'])
    abilities = catalog([vanilla/'abilities.txt',GEN9/'PBS'/'abilities_Gen_9_Pack.txt'])
    types = catalog([next((GAME/'[0] Mods (Use if you are RetroNC and want Vanilla Gen 9)').rglob('[[]2] Vanilla Type Matchups PBS/PBS/types.txt'))])
    summaries=[]
    for path in sorted((GAME/'PBS').glob('*.txt')):
        name=path.name
        if name.startswith('pokemon') and not name.startswith('pokemon_metrics'): ref=species
        elif name.startswith('moves'): ref=moves
        elif name.startswith('abilities'): ref=abilities
        elif name=='types.txt': ref=types
        else: continue
        summaries.append(restore_records(path,ref))

    # Use the same engine version, restoring battle mechanics without replacing
    # story scripts, maps, event data, UI, audio, sprites, or the plugin framework.
    raw=(GAME/'Data'/'Scripts.rxdata').read_bytes(); decoder=Marshal(raw); rows=decoder.read()
    assert decoder.i == len(raw)
    by_name={bytes(row[1]).decode('utf-8-sig'):row for row in rows}
    engine_changes=[]
    for ref in ESS.rglob('*.rb'):
        relative=ref.relative_to(ESS).as_posix()
        name=re.sub(r'^\d+_','',ref.stem)
        allowed=any(relative.startswith(p) for p in ('011_Battle/001_Battle/','011_Battle/002_Battler/',
                   '011_Battle/003_Move/','011_Battle/007_Other battle code/'))
        allowed |= name in {'Pokemon','Pokemon_Move','FormHandlers'}
        if not allowed or name not in by_name:continue
        row=by_name[name]
        original=zlib.decompress(row[2]).decode('utf-8-sig').replace('\r\n','\n')
        canon=ref.read_text(encoding='utf-8-sig')
        canon=preserve_extra_classes(canon,original) if name.startswith('MoveEffects_') else canon
        if original.rstrip()==canon.rstrip():continue
        compressed=RubyString(zlib.compress(canon.encode('utf-8')))
        if hasattr(row[2],'ivars'):compressed.ivars=row[2].ivars
        row[2]=compressed
        engine_changes.append(name)
    # Restore only biological odds in Settings; keep the campaign's configuration.
    row=by_name['Settings'];text=zlib.decompress(row[2]).decode('utf-8-sig').replace('\r\n','\n')
    text=re.sub(r'(?m)^(\s*SHINY_POKEMON_CHANCE\s*=).*$',r'\1 (MECHANICS_GENERATION >= 6) ? 16 : 8',text)
    text=re.sub(r'(?m)^(\s*POKERUS_CHANCE\s*=).*$',r'\1 3',text)
    compressed=RubyString(zlib.compress(text.encode('utf-8')))
    if hasattr(row[2],'ivars'):compressed.ivars=row[2].ivars
    row[2]=compressed;engine_changes.append('Settings: shiny/Pokerus odds only')
    bundle=b'\x04\x08'+dump(rows)
    check=Marshal(bundle);reread=check.read();assert check.i==len(bundle) and reread==rows
    assert len(reread)==405
    for row in reread:zlib.decompress(row[2])
    stage('Data/Scripts.rxdata',bundle,'Restore canonical battle engine while retaining custom move classes')

    # Clean source from the very same installed plugin release. Preserve two
    # local compatibility fixes unrelated to balance (Z-A files).
    keep={'[006] Z-A Battle Function.rb','[003] Z-A Moves.rb'}
    plugin_changes=[]
    for ref in (GEN9/'Plugins'/'Generation 9 Pack Scripts').rglob('*.rb'):
        if ref.name in keep:continue
        relative=Path('Plugins')/ref.relative_to(GEN9/'Plugins')
        current=GAME/relative
        if not current.is_file():continue
        a=ref.read_text(encoding='utf-8-sig');b=current.read_text(encoding='utf-8-sig')
        if a.rstrip()!=b.rstrip():
            stage(str(relative),a,'Restore original Gen 9 Pack 3.3.3 behavior')
            plugin_changes.append(str(relative))

    # Preserve the allocator screen, using separate official EVs and limits.
    ev='Plugins/Level Based Mixed EV System and Allocator/'
    fundamental='''# Blue: canonical EV limits; retain allocator UI and trainer metadata.\nclass Pokemon\n  attr_accessor :trainerevs\n  EV_LIMIT = 510\n  EV_STAT_LIMIT = 252\nend\n'''
    stage(ev+'Fundamentals.rb',fundamental,'Official EV limits without attack/special-attack mirroring')
    stage(ev+'No Non Allocator EV Gain.rb','# Blue: use the canonical EV gain and level-up methods restored in the core.\n',
          'Restore EV gain; remove automatic EV injection on level-up')
    path=GAME/ev/'Settings.rb';text=path.read_text(encoding='utf-8-sig')
    stage(ev+'Settings.rb',re.sub(r'PURIST_MODE\s*=\s*false','PURIST_MODE = true',text),'Keep physical and special EVs independent')
    for name in ['Summary.rb','Trainers.rb']:
        text=(GAME/ev/name).read_text(encoding='utf-8-sig')
        text=re.sub(r'evpool\s*=\s*472\s*\+\s*(?:self\.|pkmn\.)?level\s*\*\s*8','evpool=510',text)
        text=re.sub(r'evcap\s*=\s*236\s*\+\s*(?:self\.|pkmn\.|pkmn_data\[:)?level(?:\])?\s*\*\s*4','evcap=252',text)
        text=text.replace('512','510').replace('256','252')
        if name=='Trainers.rb' and 'total = pkmn.ev.values.sum' not in text:
            # Clamp existing authored NPC allocations without rewriting any team.
            text=text.replace('pkmn.calc_stats', '''GameData::Stat.each_main { |s| pkmn.ev[s.id] = pkmn.ev[s.id].clamp(0, Pokemon::EV_STAT_LIMIT) }\n        total = pkmn.ev.values.sum\n        if total > Pokemon::EV_LIMIT\n          scale = Pokemon::EV_LIMIT.to_f / total\n          GameData::Stat.each_main { |s| pkmn.ev[s.id] = (pkmn.ev[s.id] * scale).floor }\n        end\n        pkmn.calc_stats''')
        stage(ev+name,text,'Keep allocator/trainer resources within official EV limits')
    # This optional mod changes ordinary held type boosters into status consumables.
    stage('Plugins/Super Yellow Scripts/[004] Type Enhance Item Effects Overhaul.rb',
          '# Blue: canonical held-item battle handlers are restored in the core.\n',
          'Remove the noncanonical status-item conversion; keep item IDs and campaign assets')

    stage('Plugins/[ZZZ] Blue Official Rules/meta.txt',
          'Name = Blue Official Rules\nVersion = 1.0\nEssentials = 21.1\nRequires = Generation 9 Pack,3.3.3\nRequires = Super Yellow Pack,3.0.0\nRequires = Level Based Mixed EV System and Allocator,1.0.5\nCredits = Gabriel Chaves Alencar\n',
          'Runtime verification after canonical rules and all dependency plugins load')
    stage('Plugins/[ZZZ] Blue Official Rules/Verify.rb',(CODE/'runtime_verify.rb').read_bytes(),
          'Opt-in runtime verification with no save-game writes')
    stage('Data/blue-verify-request.txt','Verify compiled canonical rules once.\n','Request one runtime verification, without loading a save')

    # DBK must normalize LF before splitting/replacing property values.
    compiler='Plugins/[DBK_000] Deluxe Battle Kit/[000] Essentials Patches/[000] Compiler.rb'
    code=(GAME/compiler).read_text(encoding='utf-8-sig')
    old='        line += "\\r\\n" if !line.include?("\\r\\n")'
    new='        line = line.sub(/\\r?\\n\\z/, "") + "\\r\\n"'
    if old in code: stage(compiler,code.replace(old,new),'DBK compiler LF/CRLF compatibility')
    elif new not in code: raise ValueError('Unsupported DBK compiler version.')

    result=dict(reference='Essentials v21.1 + original Generation 9 Pack v3.3.3',
                files=PLAN,pbs=summaries,engine=engine_changes,plugins=plugin_changes,
                note='Canonical counterpart restored by symbolic ID; exclusive noncanonical records retained for campaign compatibility.')
    (ROOT/'plan.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'files':len(PLAN),'changed_records':sum(x['changed'] for x in summaries),
                      'engine_scripts':len(engine_changes),'pbs':summaries},ensure_ascii=False,indent=2))

if __name__=='__main__':prepare()
