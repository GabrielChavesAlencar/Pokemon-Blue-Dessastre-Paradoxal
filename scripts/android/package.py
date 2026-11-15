"""Build a clean, precompiled JoiPlay game ZIP as a release asset, never a Git source file."""
from pathlib import Path
import argparse,hashlib,json,sys,zipfile,zlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scripts/official_rules'))
from prepare_restore import Marshal,RubyString,dump
from server.ruby_marshal import loads
from scripts.android.build_manifest import installed_manifest, verify_manifest
from scripts.android.early_input import install as install_early_input, verify as verify_early_input

MOBILE='Plugins/ZZZZ Blue Battle Lab/Mobile.rb'

# A multiregional Android ZIP must be the ACTUAL shared Decades build, not
# the independent Kanto/Hoenn pilots or a page pointing at the base ZIP.
KANTO_PLUGIN = "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb"
HOENN_PLUGIN = "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb"
REGION_START_PLUGIN = "Plugins/ZZZZ Blue Story and Presentation/RegionStart.rb"
REGIONAL_FILES = (
    "Data/blue-kanto-install.json", "Data/blue-kanto-start.txt",
    "Data/blue-kanto-ready.txt", "Data/blue-kanto-music.txt",
    "Data/blue-kanto-locale.dat", "Data/blue-kanto-npc-dialogues.dat",
    "Data/blue-kanto-pewter-route3-gate.txt",
    "Data/blue-kanto-pewter-mom-sprite.txt",
    "Data/blue-kanto-viridian-route2-line.txt",
    "Data/blue-kanto-silph-floors.txt",
    "Data/blue-hoenn-install.json", "Data/blue-hoenn-start.txt",
    "Data/blue-hoenn-ready.txt", "Data/blue-hoenn-pilot.txt",
)

def compiled_region(cache, name, source):
    expected = source.replace(b'\r\n', b'\n')
    for plugin in loads(cache):
        for item_name, compressed in plugin[2]:
            if item_name == name.encode('ascii') and zlib.decompress(compressed).replace(b'\r\n', b'\n') == expected:
                return hashlib.sha256(expected).hexdigest()
    raise ValueError('Regional script is missing or stale in Android plugin cache: '+str(name))

def verify_regions(game):
    # install_hoenn.safe_file validates absolute paths; the Android CLI
    # normally passes --game-dir game (relative to the checkout).
    game = Path(game).resolve()
    if any((game / name).is_file() for name in ("Kanto pilot.json", "Hoenn pilot.json")):
        raise ValueError('The Android shared build cannot use isolated pilot save profiles.')
    sys.path.insert(0, str(ROOT / 'scripts/regions'))
    from install_kanto import verify_installed as kanto
    from install_hoenn import verify_installed as hoenn
    kp, hp = kanto(game), hoenn(game)
    if not kp.get("maps", 0) > 100 or hp.get("maps") != 199:
        raise ValueError('Shared Kanto/Hoenn regional map counts not verified.')
    for name in REGIONAL_FILES:
        p = game / name
        if not p.is_file() or p.is_symlink() or p.stat().st_size == 0:
            raise ValueError('Missing mandatory Android shared region file: '+name)
    compiled = (game/'Data/PluginScripts.rxdata').read_bytes()
    # Regression for the real Android crash: the package must contain the
    # updated RegionStart.rb in BOTH the files and compiled plugin scripts.
    for item in (KANTO_PLUGIN, HOENN_PLUGIN, REGION_START_PLUGIN):
        file = game / item
        if not file.is_file() or file.is_symlink():
            raise ValueError("Missing Android regional boot script: " + item)
        compiled_region(compiled, Path(item).name, file.read_bytes())
    return kp, hp


def compiled_mobile(cache,source):
    expected=source.replace(b'\r\n',b'\n')
    for plugin in loads(cache):
        for name,compressed in plugin[2]:
            if name==b'Mobile.rb' and zlib.decompress(compressed).replace(b'\r\n',b'\n')==expected:
                return hashlib.sha256(expected).hexdigest()
    raise ValueError('Compiled Mobile.rb differs from the Android source. Recompile before publishing.')

def verify_archive(output,revision,source_sha=None,channel='decades'):
    with zipfile.ZipFile(output) as archive:
        base='Pokemon-Blue-Android/'
        info=dict(line.split(': ',1) for line in archive.read(base+'Data/blue-mobile-build.txt').decode('utf8').splitlines() if ': ' in line)
        if info.get('Revision')!=revision:raise ValueError('Android ZIP revision does not match the requested commit.')
        source=archive.read(base+MOBILE)
        actual=compiled_mobile(archive.read(base+'Data/PluginScripts.rxdata'),source)
        if info.get('Mobile-SHA256')!=actual or (source_sha and source_sha!=actual):raise ValueError('Android ZIP compatibility source checksum mismatch.')
        if 'Revision: '+revision+'\n' not in archive.read(base+'LEIA-ME-ANDROID.txt').decode('utf8'):raise ValueError('Android README revision mismatch.')
        verify_manifest(archive,base,channel,revision)
        verify_early_input(archive.read(base+'Data/Scripts.rxdata'))
        if channel == 'multiregion':
            kanto=json.loads(archive.read(base+'Data/blue-kanto-install.json'))
            hoenn=json.loads(archive.read(base+'Data/blue-hoenn-install.json'))
            if len(kanto.get('maps',{}))<=100 or len(hoenn.get('maps',{}))!=199:
                raise ValueError('Android ZIP does not contain both verified regional mappings.')
            for name in REGIONAL_FILES:
                if not archive.getinfo(base+name).file_size:
                    raise ValueError('Empty Android region runtime: '+name)
            cache=archive.read(base+'Data/PluginScripts.rxdata')
            for name in (KANTO_PLUGIN,HOENN_PLUGIN,REGION_START_PLUGIN):
                compiled_region(cache,Path(name).name,archive.read(base+name))
    return {'revision':revision,'mobileSha256':actual}

def fingerprint(game):
    digest=hashlib.sha256()
    for file in sorted((game/'Plugins').rglob('*')):
        if file.is_file() and file.suffix.lower() in ('.rb','.txt'):
            digest.update(file.relative_to(game).as_posix().encode());digest.update(file.read_bytes().replace(b'\r\n',b'\n'))
    return digest.hexdigest()

def request_compile(game):
    # Input is loaded before plugin Mobile.rb. Fix JoiPlay touch at its source
    # instead of depending on a late plugin callback (Input line 28 crash).
    install_early_input(game)
    path=game/'Data/Scripts.rxdata';rows=Marshal(path.read_bytes()).read();found=False
    for row in rows:
        if row[1]!=b'Main':continue
        source=zlib.decompress(row[2]).decode('utf8')
        if '# BLUE_ANDROID_BUILD' not in source:
            needle='    Compiler.main'
            if source.count(needle)!=1:raise ValueError('Unknown Main compiler entry.')
            source=source.replace(needle,"    File.write('Data/blue-android-stage.txt','compiler') if File.file?('Data/blue-android-build-request.txt')\n"+needle+"\n    # BLUE_ANDROID_BUILD\n    if File.file?('Data/blue-android-build-request.txt')\n      File.write('Data/blue-android-compiled.txt',File.read('Data/blue-android-build-request.txt'))\n      File.delete('Data/blue-android-build-request.txt')\n      exit\n    end")
            source=source.replace('    PluginManager.runPlugins',"    if File.file?('Data/blue-android-build-request.txt')\n      File.write('Data/blue-android-stage.txt','plugins')\n      Object.send(:define_method,:pbPrintException) { |error| File.write('Data/blue-android-error.txt',error.to_s+\"\\n\"+Array(error.backtrace).join(\"\\n\"));exit! 1 }\n    end\n    PluginManager.runPlugins")
        if '# BLUE_ANDROID_DEBUG' not in source:
            source=source.replace('    PluginManager.runPlugins',"    $DEBUG = true if File.file?('Data/blue-android-build-request.txt') # BLUE_ANDROID_DEBUG\n    PluginManager.runPlugins")
        row[2]=RubyString(zlib.compress(source.encode('utf8')))
        found=True
    if not found:raise ValueError('Main is missing.')
    path.write_bytes(b'\x04\x08'+dump(rows))
    for name in ['blue-battle-lab-request.txt','blue-android-compiled.txt','blue-android-error.txt','blue-android-stage.txt']:
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

def build(game,output,revision,channel='decades'):
    if channel not in ('decades','multiregion'):raise ValueError('Unknown Android History build channel.')
    if channel=='multiregion':verify_regions(game)
    marker=game/'Data/blue-android-compiled.txt'
    if not marker.is_file():raise ValueError('The native compiler did not produce its completion marker. No Android download can be published.')
    if marker.read_text()!=fingerprint(game):raise ValueError('The native compiler completion marker is stale for the current plugins. No Android download can be published.')
    mobile_sha=compiled_mobile((game/'Data/PluginScripts.rxdata').read_bytes(),(game/MOBILE).read_bytes())
    # Own runtime configuration/data are selected explicitly; logs, saves and machine paths are excluded.
    own=['blue-trainer-album.dat','blue-hub-presets.dat','blue-pt-br.dat','blue-music.rxdata','blue-music-categories.rxdata','blue-official-rules.dat','blue-radical-ai.dat']
    plans={p.relative_to(game).as_posix():p for p in game.rglob('*') if p.is_file() and not p.is_symlink() and allowed(p.relative_to(game))}
    for name in own:
        file=game/'Data'/name
        if file.is_file():plans['Data/'+name]=file
    if channel=='multiregion':
        # Package the proof files the generic Decades filter intentionally
        # excludes (blue-*.json/txt/dat), or Hoenn stays "em preparação".
        for name in REGIONAL_FILES:
            plans[name]=game/name
    output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,file in sorted(plans.items()):archive.write(file,'Pokemon-Blue-Android/'+name)
        archive.writestr('Pokemon-Blue-Android/Data/blue-mobile.txt','experimental-v1\n')
        archive.writestr('Pokemon-Blue-Android/Data/blue-mobile-build.txt','Compatibility: 2\nRevision: '+revision+'\nMobile-SHA256: '+mobile_sha+'\nPlugins-SHA256: '+fingerprint(game)+'\n')
        readme = (
            'Versao experimental para JoiPlay + RPG Maker Plugin. Nao e um APK nativo.\n'
            'Instale os aplicativos de https://www.joiplay.net/ e extraia este ZIP por completo.\n'
            'Adicione Game.exe ao JoiPlay. Escolha Historia ou Hub offline na abertura.\n'
            'Use Times prontos para importar as equipes sem Python. Multiplayer e download de links requerem Windows.\n'
            'Atualizacoes: feche o JoiPlay e execute ATUALIZAR-ANDROID.py no Termux com Python.\n'
            'Verifique primeiro com: python ATUALIZAR-ANDROID.py\n'
            'Para baixar e instalar: python ATUALIZAR-ANDROID.py --update\n'
            'Se nao houver patch, Termux instala o ZIP inteiro com backup dos saves.\n'
            'Guia: docs/ANDROID_ATUALIZACOES_INCREMENTAIS.md no GitHub.\n'
            'Ainda requer validacao em aparelhos Android reais.\nRevision: '+revision+'\n')
        if channel == 'multiregion':
            readme += (
                'EDICAO MULTIRREGIONAL: DECADES + KANTO + HOENN no mesmo jogo e perfil de saves.\n'
                'Correcao JoiPlay: Novo Jogo sem biblioteca JSON, sem travar RegionStart.rb.\n'
                'Pacote separado do Decades puro; nao instale patch do canal decades.\n'
                'A disponibilidade da viagem depende tambem do progresso no jogo.\n'
                'Nao instale sobre os arquivos de outro canal sem backup dos saves.\n')
        archive.writestr('Pokemon-Blue-Android/LEIA-ME-ANDROID.txt', readme)
        # Inventory is checked by the release publisher and the Android updater.
        extras={
            'Data/blue-mobile.txt': b'experimental-v1\n',
            'Data/blue-mobile-build.txt': (
                'Compatibility: 2\nRevision: '+revision+'\nMobile-SHA256: '+mobile_sha+
                '\nPlugins-SHA256: '+fingerprint(game)+'\n').encode('utf8')
        }
        archive.writestr('Pokemon-Blue-Android/Data/blue-update.json',
                         installed_manifest(channel,revision,{**plans,**extras,
                                                               'ATUALIZAR-ANDROID.py':
                                                               (ROOT/'scripts/android/update_client.py').read_bytes(),
                                                               'LEIA-ME-ANDROID.txt': readme.encode('utf8')}))
        archive.writestr('Pokemon-Blue-Android/ATUALIZAR-ANDROID.py',
                         (ROOT/'scripts/android/update_client.py').read_bytes())
    verify_archive(output,revision,mobile_sha,channel)
    with output.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n','ascii')
    return {'revision':revision,'mobileSha256':mobile_sha,'files':len(plans)+3,'bytes':output.stat().st_size,'sha256':digest}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--game-dir',type=Path,default=ROOT/'game');parser.add_argument('--request-compile',action='store_true');parser.add_argument('--verify',action='store_true');parser.add_argument('--revision',default='local');parser.add_argument('--channel',choices=('decades','multiregion'),default='decades');parser.add_argument('--output',type=Path,default=ROOT/'dist/Blue-Android-JoiPlay.zip');a=parser.parse_args()
    if a.request_compile:request_compile(a.game_dir);print('Native Android compilation requested.')
    elif a.verify:
        source_sha=hashlib.sha256((ROOT/'scripts/battle_lab/Mobile.rb').read_bytes().replace(b'\r\n',b'\n')).hexdigest()
        print(json.dumps(verify_archive(a.output,a.revision,source_sha,channel=a.channel)))
    else:print(json.dumps(build(a.game_dir,a.output,a.revision,a.channel)))
