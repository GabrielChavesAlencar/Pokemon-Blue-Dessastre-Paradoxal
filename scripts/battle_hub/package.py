"""Build a standalone Hub source package; never include the base game or saves."""
from pathlib import Path
import argparse,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parents[2]
SCRIPT_DIRS=['official_rules','dessastre_paradoxal','battle_lab','battle_options','battle_polish','radical_ai','music','za_megas']
REQUIRED=['HUB_DE_BATALHA.bat','TESTAR_BATALHA.bat','INSTALAR_HUB.bat','scripts/install_game.py',
          'server/prepare_game.py','server/music_editor.py','server/ruby_marshal.py',
          'data/dessastre-paradoxal.json','data/fan-assets.json','data/national-species.json','data/radical-ai.json','data/za-megas.json',
          'site/assets/fan-pokemon.tar.gz','site/assets/fan-pokemon.sha256',
          'site/assets/fan-extras.tar.gz','site/assets/fan-extras.sha256','site/assets/fan-extras.manifest.json',
          'site/public/data/story-trainers.json','docs/HUB_BATALHA.md','docs/ROADMAP_HUB.md']
def files(project):
    selected=set(REQUIRED)
    for directory in SCRIPT_DIRS:
        for file in (project/'scripts'/directory).iterdir():
            if file.is_file() and file.suffix in ('.py','.rb','.txt'):selected.add(file.relative_to(project).as_posix())
    plans={}
    for name in sorted(selected):
        candidate=project/name;path=candidate.resolve()
        if not path.is_relative_to(project.resolve()) or candidate.is_symlink():raise ValueError('Invalid package source: '+name)
        raw=path.read_bytes()
        if path.suffix in ('.py','.rb','.md','.txt','.json','.bat','.sha256'):raw=raw.replace(b'\r\n',b'\n')
        plans[name]=raw
    plans['LEIA-ME.md']=plans['docs/HUB_BATALHA.md']
    return plans
def build(project,output,revision='local'):
    plans=files(project)
    manifest={'version':1,'product':'Blue Hub de Batalha','revision':revision,'baseIncluded':False,
              'files':[{'path':p,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()} for p,raw in sorted(plans.items())]}
    plans['hub-manifest.json']=(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for path,raw in sorted(plans.items()):
            info=zipfile.ZipInfo('Blue-Battle-Hub/'+path,date_time=(2026,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=0o644<<16;archive.writestr(info,raw)
    digest=hashlib.sha256(output.read_bytes()).hexdigest()
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n',encoding='ascii')
    return {'path':str(output),'files':len(plans),'bytes':output.stat().st_size,'sha256':digest}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'dist/Blue-Battle-Hub.zip');parser.add_argument('--revision',default='local');args=parser.parse_args()
    print(json.dumps(build(ROOT,args.output,args.revision),indent=2))
if __name__=='__main__':main()
