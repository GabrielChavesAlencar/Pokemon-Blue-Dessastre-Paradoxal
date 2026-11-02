"""Extract translation text without rewriting original maps, messages or game data."""
from pathlib import Path
import argparse,collections,json,re,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from server.ruby_marshal import loads,text
PROTECTED_TYPES={1,4,5,7,8,10,14,27,28,29,30}
CONTROL=re.compile(r'#\{[^{}]*\}|<[^>]+>|(?:[A-Z]:[\\/]|(?:Graphics|Audio|Data|Plugins|Fonts|PBS)/)[^\s"<>]+|\\(?:[a-zA-Z]+\[[^\]]*\]|\[[0-9a-f]{8}\]|POG|PN|PM|PG|TN|TE|CN|WTNP|WT|OP|CL|WU|WM|WD|PT|TS|[Gnbrmlf0-9.!^|><])|\{\d+(?::[^}]+)?\}|%\d*\$?[sdif]|\n',re.I)
def extract(project=ROOT):
    keys=set();protected=set();maps=set()
    for filename in ['messages_core.dat','messages_game.dat']:
        data=loads((project/'game/Data'/filename).read_bytes())
        for kind,values in enumerate(data):
            if kind in PROTECTED_TYPES:
                if isinstance(values,dict):protected.update(text(k) for k in values)
                continue
            if kind==0:
                for group in values:
                    if isinstance(group,dict):maps.update(text(k) for k in group)
            elif isinstance(values,dict):keys.update(text(k) for k in values)
    keys.update(maps)
    protected.update({'Pokémon','Pokemon','Pokédex','Pokedex','Blue','Dessastre Paradoxal','EV','EVs','IV','IVs','EXP','PP','HP'})
    # Compiled map text is supplemented by the source events, so recently added
    # or uncompiled dialogue is included too. Script conditions are never read
    # as dialogue and are never modified by the localization layer.
    def events(commands):
        current=[]
        for c in commands:
            code=c.attrs['@code'];params=c.attrs['@parameters']
            if code in (101,401):current.append(text(params[0]));continue
            if current:
                maps.add(' '.join(current));current=[]
            if code==102:keys.update(text(v) for v in params[0])
        if current:maps.add(' '.join(current))
    for p in sorted((project/'game/Data').glob('Map[0-9][0-9][0-9].rxdata')):
        for event in loads(p.read_bytes()).attrs['@events'].values():
            for page in event.attrs['@pages']:events(page.attrs['@list'])
    for event in loads((project/'game/Data/CommonEvents.rxdata').read_bytes()):
        if event:events(event.attrs['@list'])
    keys.update(maps)
    protected={s for s in protected if s and not s.isdigit()}
    keys={s for s in keys if s.strip() and s not in protected and re.search('[A-Za-z]',CONTROL.sub('',s))}
    return {'version':1,'strings':sorted(keys),'mapStrings':sorted(maps & keys),'protected':sorted(protected,key=lambda s:(-len(s),s))}
def controls(value):return collections.Counter(CONTROL.findall(value))
def validate(source,target):
    if not isinstance(target,str) or not target.strip():raise ValueError('Empty translation')
    if controls(source)!=controls(target):raise ValueError('Message controls/placeholders changed: '+source[:100])
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    data=extract();args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'strings':len(data['strings']),'mapStrings':len(data['mapStrings']),'protected':len(data['protected']),'words':sum(len(s.split()) for s in data['strings'])}))
if __name__=='__main__':main()
