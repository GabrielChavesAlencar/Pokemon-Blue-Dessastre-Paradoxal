"""Cache user-selected public PokéPastes as inert text, grouped by game/regulation."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
from pathlib import Path
import re
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from pokepaste import download
ROOT=Path(__file__).resolve().parents[2]

def catalogue(markdown):
    rows=[];game=regulation=None
    for line in markdown.splitlines():
        heading=re.match(r'## Pokémon (Scarlet/Violet|Champions) — Regulamento ([A-Z-]+)',line)
        if heading:game,regulation=heading.groups()
        entry=re.match(r'\d+\. \*\*(.+?)\*\* — (https://pokepast\.es/[a-f0-9]{16})\s*$',line)
        if entry and game:
            title,url=entry.groups()
            rows.append({'game':game,'regulation':regulation,'title':title,'url':url,
                         'format':'champions' if game=='Champions' else 'classic'})
    if not rows:raise ValueError('No direct PokéPaste entries found.')
    return rows

def fetch(entry):
    result=dict(entry)
    try:
        raw=download(entry['url'])
        # Download success does not claim tournament legality or complete spreads.
        headers=[b for b in re.split(r'\n\s*\n',raw.strip()) if b.strip() and not b.startswith('===')]
        if len(headers)!=6:raise ValueError('O texto nao contem seis blocos de Pokemon.')
        result.update(text=raw,available=True)
    except Exception as error:result.update(text='',available=False,error=str(error)[:240])
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('markdown',type=Path)
    args=parser.parse_args();rows=catalogue(args.markdown.read_text('utf-8-sig'))
    results=[None]*len(rows)
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(fetch,row):i for i,row in enumerate(rows)}
        for future in as_completed(futures):results[futures[future]]=future.result()
    target=ROOT/'data/preset-teams.json'
    target.write_text(json.dumps({'version':1,'source':'User-supplied PokéPaste catalogue; cached public text; legality/spreads not independently certified.','teams':results},ensure_ascii=False,indent=2)+'\n','utf8')
    print(json.dumps({'total':len(results),'available':sum(row['available'] for row in results),
                      'unavailable':[(row['regulation'],row['url'],row['error']) for row in results if not row['available']]},ensure_ascii=True))
if __name__=='__main__':main()
