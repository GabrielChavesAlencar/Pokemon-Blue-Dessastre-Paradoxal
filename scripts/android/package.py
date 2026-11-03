"""Build a clean, precompiled JoiPlay game ZIP as a release asset, never a Git source file."""
from pathlib import Path
import argparse,hashlib,json,sys,zipfile,zlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/official_rules'))
from prepare_restore import Marshal,RubyString,dump

def fingerprint(game):
    digest=hashlib.sha256()
    for file in sorted((game/'Plugins').rglob('*')):
        if file.is_file() and file.suffix.lower() in ('.rb','.txt'):
            digest.update(file.relative_to(game).as_posix().encode());digest.update(file.read_bytes().replace(b'\r\n',b'\n'))
    return digest.hexdigest()

def request_compile(game):
    path=game/'Data/Scripts.rxdata';rows=Marshal(path.read_bytes()).read();found=False
    for row in rows:
        if row[1]!=b'Main':continue
        source=zlib.decompress(row[2]).decode('utf8')
        if '# BLUE_ANDROID_BUILD' not in source:
            needle='    Compiler.main'
            if source.count(needle)!=1:raise ValueError('Unknown Main compiler entry.')
            source=source.replace(needle,needle+"\n    # BLUE_ANDROID_BUILD\n    if File.file?('Data/blue-android-build-request.txt')\n      File.write('Data/blue-android-compiled.txt',File.read('Data/blue-android-build-request.txt'))\n      File.delete('Data/blue-android-build-request.txt')\n      exit\n    end")
            source=source.replace('    PluginManager.runPlugins',"    if File.file?('Data/blue-android-build-request.txt')\n      Object.send(:define_method,:pbPrintException) { |error| File.write('Data/blue-android-error.txt',error.to_s+\"\\n\"+Array(error.backtrace).join(\"\\n\"));exit! 1 }\n    end\n    PluginManager.runPlugins")
            row[2]=RubyString(zlib.compress(source.encode('utf8')))
        found=True
    if not found:raise ValueError('Main is missing.')
    path.write_bytes(b'\x04\x08'+dump(rows))
    for name in ['blue-battle-lab-request.txt','blue-android-compiled.txt']:
        file=game/'Data'/name
        if file.is_file():file.unlink()
    (game/'Data/blue-compile-request.txt').write_text('compile','ascii')
    (game/'Data/blue-android-build-request.txt').write_text(fingerprint(game),'ascii')

def allowed(path):
    parts=path.parts;name=path.name.lower()
    if not parts:return False
    if parts[0] in ('Audio','Fonts','Graphics','PBS','Plugins'):
        return not any(p in ('.git','__pycache__','BlueHub','Saves','saves') or p.lower().endswith('backup') for p in parts) and path.suffix.lower() not in ('.log','.pyc','.exe','.dll')
    if parts[0]=='Data':
        if name.startswith(('save','game.','game_','backup','lastsave')):return False
        return (name.endswith(('.dat','.rxdata')) and not name.startswith(('blue-mp','blue-route-captures','blue-campaign-reference','blue-')))
    return len(parts)==1 and name in ('game.exe','game.ini','mkxp.json','preload.rb','rgss104e.dll','x64-msvcrt-ruby310.dll','zlib1.dll','soundfont.sf2','credits.txt')

def build(game,output,revision):
    marker=game/'Data/blue-android-compiled.txt'
    if not marker.is_file() or marker.read_text()!=fingerprint(game):raise ValueError('The native compiler did not finish for the current plugins. No Android download can be published.')
    # Own runtime configuration/data are selected explicitly; logs, saves and machine paths are excluded.
    own=['blue-trainer-album.dat','blue-hub-presets.dat','blue-music.rxdata','blue-music-categories.rxdata','blue-official-rules.dat','blue-radical-ai.dat']
    plans={p.relative_to(game).as_posix():p for p in game.rglob('*') if p.is_file() and not p.is_symlink() and allowed(p.relative_to(game))}
    for name in own:
        file=game/'Data'/name
        if file.is_file():plans['Data/'+name]=file
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,file in sorted(plans.items()):archive.write(file,'Pokemon-Blue-Android/'+name)
        archive.writestr('Pokemon-Blue-Android/Data/blue-mobile.txt','experimental-v1\n')
        archive.writestr('Pokemon-Blue-Android/LEIA-ME-ANDROID.txt',
            'Versao experimental para JoiPlay + RPG Maker Plugin. Nao e um APK nativo.\n'
            'Instale os aplicativos de https://www.joiplay.net/ e extraia este ZIP por completo.\n'
            'Adicione Game.exe ao JoiPlay. Escolha Historia ou Hub offline na abertura.\n'
            'Use Times prontos para importar as equipes sem Python. Multiplayer e download de links requerem Windows.\n'
            'Ainda requer validacao em aparelhos Android reais.\nRevision: '+revision+'\n')
    digest=hashlib.sha256(output.read_bytes()).hexdigest();output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n','ascii')
    return {'revision':revision,'files':len(plans)+2,'bytes':output.stat().st_size,'sha256':digest}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game-dir',type=Path,default=ROOT/'game');parser.add_argument('--request-compile',action='store_true');parser.add_argument('--revision',default='local');parser.add_argument('--output',type=Path,default=ROOT/'dist/Blue-Android-JoiPlay.zip');a=parser.parse_args()
    if a.request_compile:request_compile(a.game_dir);print('Native Android compilation requested.')
    else:print(json.dumps(build(a.game_dir,a.output,a.revision)))
