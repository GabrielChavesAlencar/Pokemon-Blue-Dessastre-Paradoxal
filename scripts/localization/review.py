"""Audit author-time cache before final locale compilation; never edits game data."""
import argparse,json,re
from catalog import validate
RESIDUE=re.compile(r'ZXQ|XQZ|\{\d+(?::[^}]+)?\}[XZ](?![A-Za-z])')
def issues(source,target):
    reasons=[]
    try:validate(source,target)
    except ValueError:reasons.append('controls')
    if '\u2047' in target or '\ufffd' in target:reasons.append('unknown glyph')
    if RESIDUE.search(target) and not RESIDUE.search(source):reasons.append('copy marker residue')
    return reasons
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cache',required=True)
    parser.add_argument('--repair',action='store_true');args=parser.parse_args()
    from pathlib import Path
    path=Path(args.cache);data=json.loads(path.read_text(encoding='utf8'))
    bad={s:issues(s,t) for s,t in data.items() if issues(s,t)}
    report={'entries':len(data),'invalid':len(bad),'reasons':{reason:sum(reason in rows for rows in bad.values()) for reason in ['controls','unknown glyph','copy marker residue']}}
    if args.repair and bad:
        backup=path.with_name(path.stem+'-before-review.json')
        if not backup.exists():backup.write_bytes(path.read_bytes())
        path.write_text(json.dumps({s:t for s,t in data.items() if s not in bad},ensure_ascii=False),encoding='utf8')
        report['removedForRetranslation']=len(bad)
    print(json.dumps(report))
if __name__=='__main__':main()
