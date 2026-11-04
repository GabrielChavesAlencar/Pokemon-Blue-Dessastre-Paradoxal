"""Reproduce Blue's canonical rules restoration using pinned local references."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
from html.parser import HTMLParser
from urllib.request import Request, urlopen
import zipfile

ESSENTIALS_SHA256 = '1bea20fbf6e96a3d7a74eea15ee343533ec73f3e91e88af5eed6704b0b0f617d'
GEN9_SHA256 = '1a12e96a48f790ac082b06e119c3422b00e7a12e59d5de218a02d67331881e85'
ESSENTIALS_URL = 'https://codeload.github.com/Maruno17/pokemon-essentials/zip/refs/tags/v21.1'
GEN9_URL = 'https://eeveeexpo.com/resources/1101/version/3285/download'
GEN9_DOWNLOAD_PAGE = 'https://www.mediafire.com/file/3clyiys8mrkerbx/Generation_9_Pack_v3.3.3.rar/file'

def sha256(path):
    value = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''): value.update(chunk)
    return value.hexdigest()

def download(url, path):
    partial=path.with_name(path.name+'.part')
    try:
        for attempt in range(3):
            try:
                with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=90) as source, partial.open('wb') as target:
                    shutil.copyfileobj(source, target)
                os.replace(partial,path);return
            except OSError:
                if attempt==2:raise
                time.sleep(attempt+1)
    finally:
        if partial.exists():partial.unlink()

class DownloadLink(HTMLParser):
    url = None
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'a' and values.get('id') == 'downloadButton': self.url = values.get('href')

def gen9_download_url():
    # The second page is the public destination of the original version's redirect.
    # Keep the pinned archive hash below; never substitute another pack/version.
    for page_url in (GEN9_URL,GEN9_DOWNLOAD_PAGE):
        for attempt in range(3):
            try:
                with urlopen(Request(page_url,headers={'User-Agent':'Mozilla/5.0'}),timeout=60) as page:
                    parser=DownloadLink();parser.feed(page.read().decode('utf8',errors='replace'))
                if parser.url and parser.url.startswith('https://'):return parser.url
            except OSError:
                pass
            if attempt<2:time.sleep(attempt+1)
    raise ValueError('Download link unavailable after retries; supply --gen9-rar.')

def references(work, essentials_zip=None, gen9_rar=None):
    expected = {'essentials': ESSENTIALS_SHA256, 'gen9': GEN9_SHA256}
    marker = work / 'references.json'
    if marker.is_file() and json.loads(marker.read_text()) == expected:
        if (work/'essentials-reference').is_dir() and (work/'gen9-reference'/'Plugins').is_dir(): return
    work.mkdir(parents=True, exist_ok=True)
    essential = Path(essentials_zip).resolve() if essentials_zip else work / 'essentials-v21.1.zip'
    gen9 = Path(gen9_rar).resolve() if gen9_rar else work / 'gen9-v3.3.3.rar'
    if not essential.is_file() or (not essentials_zip and sha256(essential)!=ESSENTIALS_SHA256):
        print('Downloading Essentials v21.1 reference...')
        download(ESSENTIALS_URL, essential)
    if sha256(essential) != ESSENTIALS_SHA256: raise ValueError('Essentials archive SHA-256 mismatch.')
    if not gen9.is_file() or (not gen9_rar and sha256(gen9)!=GEN9_SHA256):
        print('Downloading original Gen 9 Pack v3.3.3 reference...')
        download(gen9_download_url(), gen9)
    if sha256(gen9) != GEN9_SHA256: raise ValueError('Gen 9 archive SHA-256 mismatch.')
    essential_root = work/'essentials-reference'
    with zipfile.ZipFile(essential) as archive:
        for name in archive.namelist():
            if '/Data/Scripts/' not in name or not name.endswith('.rb'): continue
            target = essential_root/name.split('/Data/Scripts/', 1)[1]
            if not target.resolve().is_relative_to(essential_root.resolve()): raise ValueError('Invalid archive path.')
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(archive.read(name))
    tar = shutil.which('tar')
    if not tar: raise RuntimeError('Windows tar is required to extract the RAR reference.')
    gen9_root = work/'gen9-reference'; gen9_root.mkdir(exist_ok=True)
    subprocess.run([tar, '-xf', str(gen9), '-C', str(gen9_root), 'Plugins', 'PBS'], check=True)
    marker.write_text(json.dumps(expected, indent=2), encoding='utf-8')

def main():
    project = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir', type=Path, default=Path(os.environ.get('BLUE_GAME_DIR', project/'game')))
    parser.add_argument('--work-dir', type=Path, default=project/'.blue-work'/'official-rules')
    parser.add_argument('--essentials-zip', type=Path, help='Use an already downloaded, hash-verified archive.')
    parser.add_argument('--gen9-rar', type=Path, help='Use an already downloaded, hash-verified archive.')
    parser.add_argument('--apply', action='store_true', help='Apply the validated plan with backups; default only prepares.')
    args = parser.parse_args()
    if not (args.game_dir/'PBS'/'pokemon.txt').is_file(): parser.error('Install the local Decades base first.')
    os.environ['BLUE_GAME_DIR'] = str(args.game_dir.resolve())
    os.environ['BLUE_RESTORE_WORK_DIR'] = str(args.work_dir.resolve())
    references(args.work_dir.resolve(), args.essentials_zip, args.gen9_rar)
    import prepare_restore
    prepare_restore.prepare()
    import verify_stage  # Runs the independent staging integrity checks.
    import apply_restore
    apply_restore.main(['--apply'] if args.apply else [])
    if args.apply:
        print('Applied. Launch Game.exe debug to compile and run the one-time engine checks.')
        print('Check game/Data/blue-official-validation.txt for RESULT=PASS, then launch normally.')
    else: print('Reviewed plan is ready. Re-run with --apply to modify the local game.')

if __name__ == '__main__':
    main()
