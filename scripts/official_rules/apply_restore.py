"""Apply the reviewed staging manifest, with bounded paths and a full Data backup."""
import argparse
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from prepare_restore import ROOT, GAME, STAGE

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def atomic(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix='.blue-restore-',dir=path.parent)
    try:
        with os.fdopen(fd,'wb') as file:file.write(data);file.flush();os.fsync(file.fileno())
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)

def protected():
    paths=list((GAME/'Data').glob('Map*.rxdata'))
    paths += [GAME/'Data'/n for n in ['CommonEvents.rxdata','System.rxdata','Tilesets.rxdata']]
    paths += [p for p in (GAME/'PBS').glob('*.txt') if not p.name.startswith(('pokemon','moves','abilities','types'))]
    return {str(p.relative_to(GAME)).replace('\\','/'):sha(p) for p in paths if p.is_file()}

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args(argv)
    plan=json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))
    assert json.loads((ROOT/'static-validation.json').read_text())['result']=='PASS'
    for entry in plan['files']:
        rel=Path(entry['path']);target=GAME/rel
        assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] in ('PBS','Data','Plugins')
        assert target.resolve().is_relative_to(GAME.resolve())
        assert sha(STAGE/rel)==entry['after']
        assert (sha(target) if target.is_file() else None)==entry['before'],entry['path']
    if not args.apply:print(f"READY: {len(plan['files'])} verified target files; no files changed.");return
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    backup=GAME.parent/'.blue-backups'/('official-rules-'+stamp)
    backup.mkdir(parents=True,exist_ok=False)
    baseline=protected()
    # Recompilation can refresh all .dat files. Preserve the complete Data folder.
    shutil.copytree(GAME/'Data',backup/'Data')
    for entry in plan['files']:
        path=GAME/entry['path']
        if path.is_file() and not entry['path'].startswith('Data/'):
            dest=backup/entry['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest)
    manifest={**plan,'backup':str(backup),'protected':baseline,'applied':[]}
    atomic(backup/'manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
    try:
        for entry in plan['files']:
            atomic(GAME/entry['path'],(STAGE/entry['path']).read_bytes())
            manifest['applied'].append(entry['path'])
        assert protected()==baseline,'Protected campaign files changed'
    except Exception:
        for rel in reversed(manifest['applied']):
            old=backup/rel
            if old.is_file():atomic(GAME/rel,old.read_bytes())
            elif (GAME/rel).is_file():(GAME/rel).unlink()
        raise
    atomic(backup/'manifest.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
    atomic(ROOT/'applied.json',json.dumps(manifest,ensure_ascii=False,indent=2).encode('utf-8'))
    print(json.dumps({'applied':len(manifest['applied']),'backup':str(backup),'campaign_files_verified':len(baseline)},ensure_ascii=False))

if __name__=='__main__':main()
