"""Build a clean, precompiled JoiPlay game ZIP as a release asset, never a Git source file."""
from pathlib import Path
from datetime import datetime, timezone
import argparse,hashlib,json,sys,zipfile,zlib
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scripts/official_rules'))
from prepare_restore import Marshal,RubyString,dump
from server.ruby_marshal import loads
from scripts.android.build_manifest import installed_manifest, verify_manifest
from scripts.android.early_input import install as install_early_input, verify as verify_early_input
sys.path.insert(0,str(ROOT/'scripts/regions'))
import sinnoh_shared
from hoenn_catalog import (
    validate_manifest as validate_hoenn_manifest, verify_markers as verify_hoenn_markers,
)

MOBILE='Plugins/ZZZZ Blue Battle Lab/Mobile.rb'

# A multiregional Android ZIP must be the ACTUAL shared Decades build, not
# the independent Kanto/Hoenn pilots or a page pointing at the base ZIP.
KANTO_PLUGIN = "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb"
HOENN_PLUGIN = "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb"
REGION_START_PLUGIN = "Plugins/ZZZZ Blue Story and Presentation/RegionStart.rb"
REGION_TRAVEL_PLUGIN = "Plugins/ZZZZ Blue Story and Presentation/RegionTravel.rb"
JOHTO_QA_PROOF = "Data/blue-johto-main-preview.json"
JOHTO_QA_READY = "Data/blue-johto-preview-ready.txt"
JOHTO_QA_BOOT = "Plugins/ZZZZZ Blue Johto Main/Boot.rb"
JOHTO_QA_IDS = range(600,700)
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
    if any((game / name).is_file() for name in ("Kanto pilot.json", "Hoenn pilot.json",
                                               "Sinnoh pilot.json", "sinnoh-experimental-qa.json")):
        raise ValueError('The Android shared build cannot use isolated pilot save profiles.')
    sys.path.insert(0, str(ROOT / 'scripts/regions'))
    from install_kanto import verify_installed as kanto
    from install_hoenn import verify_installed as hoenn
    kp, hp = kanto(game), hoenn(game)
    if not kp.get("maps", 0) > 100:
        raise ValueError('Shared Kanto regional map count not verified.')
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


def verify_sinnoh(read, *, qa=False):
    proof = json.loads(read(sinnoh_shared.RECEIPT))
    sinnoh_shared.verify_files(proof, read, android=not qa, installed=True, qa=qa)
    compiled = read("Data/PluginScripts.rxdata")
    for rel in (sinnoh_shared.PLUGIN, REGION_START_PLUGIN, REGION_TRAVEL_PLUGIN):
        compiled_region(compiled, Path(rel).name, read(rel))


def verify_johto_qa(read):
    proof = json.loads(read(JOHTO_QA_PROOF))
    ready = read(JOHTO_QA_READY).strip()
    if (proof.get("region") != "JOHTO" or proof.get("status") != "EXPERIMENTAL_PRIVATE_UNVERIFIED"
            or proof.get("source_bundle_sha256") != "74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49"
            or proof.get("native_gameplay_verified") is not False or proof.get("map_ids") != list(JOHTO_QA_IDS)
            or ready != b"BLUE_JOHTO_PRIVATE_PREVIEW_V1,100,674,6,7,600,10,26,600,10,25"):
        raise ValueError("A matriz de viagens QA requer a prévia local de Johto com 100 mapas.")
    for rel in ("PBS/trainers_johto.txt", "PBS/trainer_types_johto.txt", "PBS/map_metadata_johto_main.txt",
                *(f"Data/Map{mid:03d}.rxdata" for mid in JOHTO_QA_IDS)):
        if not read(rel):
            raise ValueError("Arquivo Johto ausente no pacote de QA: " + rel)
    compiled_region(read("Data/PluginScripts.rxdata"),Path(JOHTO_QA_BOOT).name,read(JOHTO_QA_BOOT))


def compiled_mobile(cache,source):
    expected=source.replace(b'\r\n',b'\n')
    for plugin in loads(cache):
        for name,compressed in plugin[2]:
            if name==b'Mobile.rb' and zlib.decompress(compressed).replace(b'\r\n',b'\n')==expected:
                return hashlib.sha256(expected).hexdigest()
    raise ValueError('Compiled Mobile.rb differs from the Android source. Recompile before publishing.')

def verify_archive(output,revision,source_sha=None,channel='decades',*,sinnoh_qa=False):
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
            for name in REGIONAL_FILES:
                if not archive.getinfo(base+name).file_size:
                    raise ValueError('Empty Android region runtime: '+name)
            def read_region(name):
                return archive.read(base + name)
            kanto = json.loads(read_region("Data/blue-kanto-install.json"))
            kanto_maps = kanto.get("maps", {})
            if len(kanto_maps) <= 100:
                raise ValueError("Android ZIP does not contain a verified Kanto mapping.")
            hoenn = json.loads(read_region("Data/blue-hoenn-install.json"))
            destinations = set(validate_hoenn_manifest(hoenn).values())
            verify_hoenn_markers(read_region, hoenn)
            infos = loads(read_region("Data/MapInfos.rxdata"))
            if not isinstance(infos, dict) or not destinations <= infos.keys():
                raise ValueError("Android ZIP is missing Hoenn entries in MapInfos.")
            if destinations.intersection(kanto_maps.values()):
                raise ValueError("Kanto and Hoenn claim the same map ID in the Android ZIP.")
            members = {info.filename for info in archive.infolist() if info.file_size}
            missing = [f"Data/Map{dest:03}.rxdata" for dest in sorted(destinations)
                       if f"{base}Data/Map{dest:03}.rxdata" not in members]
            if missing:
                raise ValueError(f"Android ZIP is missing a Hoenn map file: {missing[0]}")
            cache=archive.read(base+'Data/PluginScripts.rxdata')
            for name in (KANTO_PLUGIN,HOENN_PLUGIN,REGION_START_PLUGIN):
                compiled_region(cache,Path(name).name,archive.read(base+name))
        if (base+sinnoh_shared.QA_MARKER in archive.namelist()) != sinnoh_qa:
            raise ValueError('O perfil Android QA de Sinnoh não é um pacote de distribuição.')
        if any(base+name in archive.namelist() for name in (sinnoh_shared.RECEIPT, sinnoh_shared.START, sinnoh_shared.PLUGIN)):
            if channel != 'multiregion':
                raise ValueError('Sinnoh requires the shared Android channel.')
            verify_sinnoh(lambda rel: archive.read(base+rel),qa=sinnoh_qa)
        elif sinnoh_qa:
            raise ValueError('Pacote Android QA sem arquivos de Sinnoh.')
        if sinnoh_qa:
            verify_johto_qa(lambda rel: archive.read(base+rel))
        elif any(base+rel in archive.namelist() for rel in (JOHTO_QA_PROOF,JOHTO_QA_READY)):
            raise ValueError("A prévia privada de Johto só pode integrar o pacote local de QA.")
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

def build(game,output,revision,channel='decades',*,sinnoh_qa=False):
    if channel not in ('decades','multiregion'):raise ValueError('Unknown Android History build channel.')
    game,output = game.resolve(),output.resolve()
    recovery = sinnoh_shared.safe_file(game,sinnoh_shared.INSTALL_JOURNAL)
    if recovery.exists():
        raise ValueError('A instalação interrompida de Sinnoh precisa ser recuperada antes de empacotar.')
    qa_marker = game/sinnoh_shared.QA_MARKER
    if (qa_marker.exists() or qa_marker.is_symlink()) != sinnoh_qa:
        raise ValueError('A cópia de QA de Sinnoh exige empacotamento QA explícito.')
    if sinnoh_qa and (channel != 'multiregion' or
                      game.parts[-3:] != ('.blue-work','sinnoh-shared-qa','game') or
                      output != game.parent/'Blue-Android-Sinnoh-QA.zip'):
        raise ValueError('O ZIP QA de Sinnoh deve permanecer na cópia descartável.')
    if channel=='multiregion':verify_regions(game)
    has_sinnoh = any((game/name).exists() or (game/name).is_symlink() for name in
        (sinnoh_shared.RECEIPT, sinnoh_shared.START, sinnoh_shared.PLUGIN))
    if has_sinnoh:
        if channel != 'multiregion':raise ValueError('Sinnoh exige o canal compartilhado no Android.')
        verify_sinnoh(lambda rel: sinnoh_shared.safe_file(game,rel).read_bytes(),qa=sinnoh_qa)
    if sinnoh_qa:
        verify_johto_qa(lambda rel: sinnoh_shared.safe_file(game,rel).read_bytes())
    elif any((game/rel).exists() or (game/rel).is_symlink() for rel in (JOHTO_QA_PROOF,JOHTO_QA_READY)):
        raise ValueError("A base contém a prévia privada de Johto. Use uma base de distribuição aprovada.")
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
        if has_sinnoh:
            for name in (sinnoh_shared.RECEIPT,sinnoh_shared.START):
                plans[name]=game/name
        if sinnoh_qa:
            plans[sinnoh_shared.QA_MARKER]=qa_marker
            for name in (JOHTO_QA_PROOF,JOHTO_QA_READY):
                plans[name]=game/name
    output.parent.mkdir(parents=True,exist_ok=True)
    build_utc=datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00","Z")
    build_info=('Compatibility: 2\nRevision: '+revision+'\nBuild-UTC: '+build_utc+
                '\nMobile-SHA256: '+mobile_sha+'\nPlugins-SHA256: '+fingerprint(game)+'\n')
    with zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for name,file in sorted(plans.items()):archive.write(file,'Pokemon-Blue-Android/'+name)
        archive.writestr('Pokemon-Blue-Android/Data/blue-mobile.txt','experimental-v1\n')
        archive.writestr('Pokemon-Blue-Android/Data/blue-mobile-build.txt',build_info)
        readme = (
            'Versao experimental para JoiPlay + RPG Maker Plugin. Nao e um APK nativo.\n'
            'Instale os aplicativos de https://www.joiplay.net/ e extraia este ZIP por completo.\n'
            'Adicione Game.exe ao JoiPlay. Escolha Historia ou Hub offline na abertura.\n'
            'Use Times prontos para importar as equipes sem Python. Multiplayer e download de links requerem Windows.\n'
            'Atualizacoes: feche o JoiPlay e execute ATUALIZAR-ANDROID.py no Termux com Python.\n'
            'Verifique primeiro com: python ATUALIZAR-ANDROID.py\n'
            'Para baixar e instalar: python ATUALIZAR-ANDROID.py --update\n'
            'Sem patch compativel, o Termux NAO baixa o ZIP completo automaticamente.\n'
            'Use --full --update somente se quiser o ZIP inteiro sem backup.\n'
            'Guia: docs/ANDROID_ATUALIZACOES_INCREMENTAIS.md no GitHub.\n'
            'Ainda requer validacao em aparelhos Android reais.\nRevision: '+revision+'\n')
        if channel == 'multiregion':
            readme += (
                'EDICAO MULTIRREGIONAL: DECADES + KANTO + HOENN no mesmo jogo e perfil de saves.\n'
                'Correcao JoiPlay: Novo Jogo sem biblioteca JSON, sem travar RegionStart.rb.\n'
                'Pacote separado do Decades puro; nao instale patch do canal decades.\n'
                'A disponibilidade da viagem depende tambem do progresso no jogo.\n'
                'Nao instale sobre os arquivos de outro canal sem backup dos saves.\n')
        if has_sinnoh:
            readme += 'SINNOH: selecione Novo Jogo ou use o Agente de Transporte Regional no mesmo save.\n'
        if sinnoh_qa:
            readme = ('Copia local de QA de Sinnoh e da previa privada de Johto. Use apenas saves de teste.\n'
                      'Use este ZIP em pasta separada. O atualizador estavel recusa a copia de QA.\n' + readme)
        archive.writestr('Pokemon-Blue-Android/LEIA-ME-ANDROID.txt', readme)
        # Inventory is checked by the release publisher and the Android updater.
        extras={
            'Data/blue-mobile.txt': b'experimental-v1\n',
            'Data/blue-mobile-build.txt': build_info.encode('utf8')
        }
        archive.writestr('Pokemon-Blue-Android/Data/blue-update.json',
                         installed_manifest(channel,revision,{**plans,**extras,
                                                               'ATUALIZAR-ANDROID.py':
                                                               (ROOT/'scripts/android/update_client.py').read_bytes(),
                                                               'LEIA-ME-ANDROID.txt': readme.encode('utf8')}))
        archive.writestr('Pokemon-Blue-Android/ATUALIZAR-ANDROID.py',
                         (ROOT/'scripts/android/update_client.py').read_bytes())
    verify_archive(output,revision,mobile_sha,channel,sinnoh_qa=sinnoh_qa)
    with output.open('rb') as stream:digest=hashlib.file_digest(stream,'sha256').hexdigest()
    output.with_suffix('.zip.sha256').write_text(digest+'  '+output.name+'\n','ascii')
    return {'revision':revision,'mobileSha256':mobile_sha,'files':len(plans)+3,'bytes':output.stat().st_size,'sha256':digest}
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-dir',type=Path,default=ROOT/'game')
    parser.add_argument('--request-compile',action='store_true')
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--revision',default='local')
    parser.add_argument('--channel',choices=('decades','multiregion'),default='decades')
    parser.add_argument('--output',type=Path)
    parser.add_argument('--sinnoh-qa',action='store_true')
    a=parser.parse_args()
    output = a.output or (a.game_dir.parent/'Blue-Android-Sinnoh-QA.zip' if a.sinnoh_qa else
                          ROOT/'dist/Blue-Android-JoiPlay.zip')
    if a.request_compile:request_compile(a.game_dir);print('Native Android compilation requested.')
    elif a.verify:
        source_sha=hashlib.sha256((ROOT/'scripts/battle_lab/Mobile.rb').read_bytes().replace(b'\r\n',b'\n')).hexdigest()
        print(json.dumps(verify_archive(output,a.revision,source_sha,channel=a.channel,sinnoh_qa=a.sinnoh_qa)))
    else:print(json.dumps(build(a.game_dir,output,a.revision,a.channel,sinnoh_qa=a.sinnoh_qa)))
