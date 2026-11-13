import importlib.util,json,sys,tempfile,unittest,zipfile,zlib,hashlib,subprocess,shutil
import io
from unittest.mock import patch
from urllib.error import URLError
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/official_rules'))
from prepare_restore import Marshal,RubyString,dump
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
android=load('blue_android_package','scripts/android/package.py')
music=load('blue_shared_music','scripts/music/install.py')
presets=load('blue_preset_catalog','scripts/battle_lab/import_presets.py')
restore=load('blue_reference_downloads','scripts/official_rules/restore.py')
class DistributionTests(unittest.TestCase):
    def test_reference_download_retries_atomically_and_keeps_existing_files_on_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'reference.rar';target.write_bytes(b'original')
            with patch.object(restore,'urlopen',side_effect=[URLError('timeout'),io.BytesIO(b'complete')]),patch.object(restore.time,'sleep'):
                restore.download('https://example.invalid/reference.rar',target)
            self.assertEqual(target.read_bytes(),b'complete')
            with patch.object(restore,'urlopen',side_effect=URLError('timeout')),patch.object(restore.time,'sleep'):
                with self.assertRaises(URLError):restore.download('https://example.invalid/reference.rar',target)
            self.assertEqual(target.read_bytes(),b'complete');self.assertFalse(target.with_name(target.name+'.part').exists())
    def test_reference_landing_page_uses_the_original_public_destination_after_retries(self):
        pages=[io.BytesIO(b'no link') for _ in range(3)]+[io.BytesIO(b'<a id="downloadButton" href="https://example.invalid/pinned.rar">Download</a>')]
        with patch.object(restore,'urlopen',side_effect=pages) as opening,patch.object(restore.time,'sleep'):
            self.assertEqual(restore.gen9_download_url(),'https://example.invalid/pinned.rar')
        self.assertEqual(opening.call_args_list[-1].args[0].full_url,restore.GEN9_DOWNLOAD_PAGE)
    def test_shared_helpers_win_over_the_standalone_online_server_on_embedded_search_path(self):
        code="import sys;sys.path[:0]=[sys.argv[1],sys.argv[2]];import server.ruby_marshal;assert server.ruby_marshal.dumps_simple([1]).startswith(b'\\x04\\x08')"
        subprocess.run([sys.executable,'-I','-c',code,str(ROOT),str(ROOT/'scripts/online')],check=True,capture_output=True)
    def game(self,root):
        game=root/'game';(game/'Data').mkdir(parents=True);(game/'Plugins/Blue').mkdir(parents=True)
        (game/'Plugins/Blue/main.rb').write_text('original own plugin')
        mobile=game/android.MOBILE;mobile.parent.mkdir(parents=True);mobile.write_bytes(b'module BlueMobile; end')
        (game/'Data/PluginScripts.rxdata').write_bytes(b'\x04\x08'+dump([[RubyString(b'Blue Battle Lab'),None,[[RubyString(b'Mobile.rb'),RubyString(zlib.compress(mobile.read_bytes()))]]]]))
        rows=[
            [1,RubyString(b'Main'),RubyString(zlib.compress(b'    PluginManager.runPlugins\n    Compiler.main\n    Game.initialize'))],
            [2,RubyString(b'Input'),RubyString(zlib.compress(b'module Input\n  def self.touch; Input.mouse_in_window; end\nend\n'))]
        ]
        (game/'Data/Scripts.rxdata').write_bytes(b'\x04\x08'+dump(rows))
        return game
    def test_android_compiler_hook_is_opt_in_idempotent_and_does_not_touch_saves(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=self.game(Path(tmp));save=game/'Game.rxdata';save.write_bytes(b'private save')
            android.request_compile(game);first=(game/'Data/Scripts.rxdata').read_bytes();android.request_compile(game)
            self.assertEqual((game/'Data/Scripts.rxdata').read_bytes(),first)
            source=zlib.decompress(Marshal(first).read()[0][2]).decode()
            self.assertEqual(source.count('# BLUE_ANDROID_BUILD'),1);self.assertIn("exit! 1",source)
            self.assertEqual(source.count('# BLUE_ANDROID_DEBUG'),1)
            self.assertIn("$DEBUG = true if File.file?('Data/blue-android-build-request.txt')",source)
            self.assertEqual(save.read_bytes(),b'private save')
    def test_android_title_is_safe_when_joiplay_calls_it_with_nil_receiver(self):
        source=(ROOT/'scripts/battle_lab/Mobile.rb').read_text(encoding='utf-8')
        self.assertIn('BlueMobile.title_selected=true',source)
        self.assertNotIn('@blue_mobile_selected',source)
        ruby=shutil.which('ruby')
        if not ruby:
            self.skipTest('Ruby is not installed; static check passed')
        runner="""
module Input
end
module BlueBattleLab
  ACTIVE = false
  @calls = 0
  def self.choose(*args); @calls += 1; 0; end
  def self.calls; @calls; end
end
class Object
  def pbCallTitle; :story; end
end
load ARGV.fetch(0)
raise 'title callback failed with nil' unless nil.pbCallTitle == :story
raise 'subsequent title callback failed' unless nil.pbCallTitle == :story
raise 'mobile menu appeared more than once' unless BlueBattleLab.calls == 1
"""
        with tempfile.TemporaryDirectory() as tmp:
            marker=Path(tmp)/'Data/blue-mobile.txt'
            marker.parent.mkdir(parents=True);marker.write_text('experimental-v1')
            result=subprocess.run([ruby,'-e',runner,str(ROOT/'scripts/battle_lab/Mobile.rb')],cwd=tmp,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+' '+result.stderr)
    def test_android_joiplay_touch_shim_works_without_mouse_in_window(self):
        ruby=shutil.which('ruby')
        source=(ROOT/'scripts/battle_lab/Mobile.rb').read_text(encoding='utf-8')
        self.assertIn('Input.define_singleton_method(:mouse_in_window)',source)
        self.assertIn('BlueMobile.install_input_compatibility',source)
        if not ruby:
            self.skipTest('Ruby is not installed; static check passed')
        runner="""
module Input
end
module BlueBattleLab
  ACTIVE = false
end
class Object
  def pbCallTitle; :story; end
end
mode=ARGV.fetch(1)
if mode=='system'
  module System
    def self.mouse_in_window; false; end
  end
elsif mode=='existing'
  def Input.mouse_in_window; :original; end
end
load ARGV.fetch(0)
case mode
when 'touch'
  raise 'Android click compatibility missing' unless Input.respond_to?(:mouse_in_window) && Input.mouse_in_window==true
when 'system'
  raise 'Android touch must not depend on physical mouse state' unless Input.mouse_in_window==true
when 'existing'
  raise 'Native Input implementation was replaced' unless Input.mouse_in_window==:original
when 'desktop'
  raise 'Android shim was installed on Windows' if Input.respond_to?(:mouse_in_window)
end
"""
        with tempfile.TemporaryDirectory() as tmp:
            for mode in ('touch','system','existing','desktop'):
                folder=Path(tmp)/mode
                folder.mkdir()
                if mode!='desktop':
                    marker=folder/'Data/blue-mobile.txt'
                    marker.parent.mkdir();marker.write_text('experimental-v1')
                result=subprocess.run([ruby,'-e',runner,str(ROOT/'scripts/battle_lab/Mobile.rb'),mode],
                                      cwd=folder,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,f'{mode}: {result.stdout} {result.stderr}')
    def test_android_event_error_logs_real_cause_without_suppressing_exception(self):
        ruby=shutil.which('ruby')
        source=(ROOT/'scripts/battle_lab/Mobile.rb').read_text(encoding='utf-8')
        self.assertIn('blue-android-event-error.txt',source)
        self.assertIn('Interpreter.prepend(EventDiagnostics)',source)
        if not ruby:
            self.skipTest('Ruby is not installed; static check passed')
        runner="""
module Input
  def self.mouse_in_window; true; end
end
module BlueBattleLab
  ACTIVE = false
end
class Object
  def pbCallTitle; :story; end
end
class Interpreter
  def execute_script(script)
    raise RuntimeError, 'Original starter script problem' if script=='choose starters'
    :ok
  end
end
load ARGV.fetch(0)
i=Interpreter.new
raise 'normal interpreter execution changed' unless i.execute_script('ok') == :ok
begin
  i.execute_script('choose starters')
  raise 'original failure was swallowed'
rescue RuntimeError => e
  raise unless e.message=='Original starter script problem'
end
log=File.read('Data/blue-android-event-error.txt')
raise 'missing underlying error' unless log.include?('RuntimeError: Original starter script problem')
raise 'missing event script' unless log.include?("Full script:\\nchoose starters")
"""
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp);(game/'Data').mkdir()
            (game/'Data/blue-mobile.txt').write_text('experimental-v1')
            result=subprocess.run([ruby,'-e',runner,str(ROOT/'scripts/battle_lab/Mobile.rb')],
                                  cwd=tmp,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+' '+result.stderr)
    def test_android_bundle_requires_a_current_native_compile_and_excludes_private_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.game(root);output=root/'out.zip'
            with self.assertRaises(ValueError):android.build(game,output,'test')
            for name in ['Game.exe','Game.ini','Data/Map001.rxdata','Data/blue-hub-presets.dat','Data/blue-pt-br.dat','Game.rxdata','Data/Game.rxdata','Data/blue-hub-python.txt','BlueHub/private-team.txt']:
                p=game/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b'synthetic data')
            (game/'Data/blue-android-compiled.txt').write_text(android.fingerprint(game))
            android.build(game,output,'test')
            with zipfile.ZipFile(output) as z:
                names=z.namelist();self.assertIn('Pokemon-Blue-Android/Game.exe',names)
                self.assertIn('Pokemon-Blue-Android/Data/blue-hub-presets.dat',names)
                self.assertIn('Pokemon-Blue-Android/Data/blue-pt-br.dat',names)
                self.assertIn('Pokemon-Blue-Android/Data/blue-mobile-build.txt',names)
                self.assertFalse(any('Game.rxdata' in n or 'python.txt' in n or 'private-team' in n for n in names))
            (game/'Plugins/Blue/main.rb').write_text('changed own plugin')
            with self.assertRaises(ValueError):android.build(game,root/'stale.zip','test')
            with self.assertRaisesRegex(ValueError,'revision'):android.verify_archive(output,'wrong-commit')
    def test_android_records_original_event_error_before_interpreter_wraps_it(self):
        ruby=shutil.which('ruby')
        if not ruby:self.skipTest('Ruby is required for runtime compatibility fixtures')
        runner=r"""
module Input; end
module BlueBattleLab; ACTIVE=false; end
class EventScriptError < StandardError; end
class Object
  def pbCallTitle; :story; end
  def pbGetExceptionMessage(error); error.message; end
end
class Interpreter
  def initialize;@map_id=1;@event_id=7;@index=177;end
  def execute_script(script)
    eval(script)
  rescue StandardError => error
    pbGetExceptionMessage(error)
    raise EventScriptError,'opaque wrapper'
  end
end
load ARGV.fetch(0)
Thread.current[:blue_mobile_event]=:previous
begin
  Interpreter.new.execute_script('Input.missing_starter_api')
  raise 'error was swallowed'
rescue EventScriptError => error
  raise unless error.message=='opaque wrapper'
end
raise 'event context leaked' unless Thread.current[:blue_mobile_event]==:previous
log=File.read('Data/blue-android-event-error.txt')
raise 'original cause lost' unless log.include?('NoMethodError') && log.include?('missing_starter_api')
raise 'logged wrapper instead of original error' if log.include?('opaque wrapper')
raise 'event coordinates lost' unless log.include?('Map: 1 | Event: 7 | Command: 177')
raise 'build revision missing' unless log.include?('Revision: test-device')
class << File
  alias blue_real_open open
  def open(path,*args,&block)
    raise Errno::EACCES if path=='Data/blue-android-event-error.txt'
    blue_real_open(path,*args,&block)
  end
end
begin
  Interpreter.new.execute_script('Input.another_missing_api')
rescue EventScriptError => error
  raise unless error.message=='opaque wrapper'
end
raise 'write failure leaked context' unless Thread.current[:blue_mobile_event]==:previous
"""
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'Data').mkdir()
            (folder/'Data/blue-mobile.txt').write_text('experimental-v1')
            (folder/'Data/blue-mobile-build.txt').write_text('Revision: test-device\n')
            result=subprocess.run([ruby,'-e',runner,str(ROOT/'scripts/battle_lab/Mobile.rb')],cwd=tmp,capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stdout+' '+result.stderr)
    def test_android_refuses_stale_compiled_mobile_even_with_a_current_plugin_marker(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.game(root)
            (game/android.MOBILE).write_text('module BlueMobile; VERSION=2; end')
            (game/'Data/blue-android-compiled.txt').write_text(android.fingerprint(game))
            with self.assertRaisesRegex(ValueError,'Compiled Mobile.rb differs'):android.build(game,root/'bad.zip','test')
    def test_shared_music_checksum_failure_prevents_all_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir();(root/'assets/music').mkdir(parents=True);(root/'assets/music/test.mp3').write_bytes(b'changed')
            (root/'data/shared-music.json').write_text(json.dumps({'version':1,'files':[{'asset':'assets/music/test.mp3','path':'BlueRandom/test.mp3','sha256':'0'*64}]}))
            with self.assertRaisesRegex(ValueError,'checksum'):music.shared_plan(root,root/'game')
            self.assertFalse((root/'game').exists())
    def test_preset_groups_are_read_without_treating_document_text_as_code(self):
        rows=presets.catalogue('## Pokémon Scarlet/Violet — Regulamento A\n1. **Example** — https://pokepast.es/0123456789abcdef\nignore me\n## Pokémon Champions — Regulamento M-C\n1. **Other** — https://pokepast.es/abcdef0123456789\n')
        self.assertEqual([r['format'] for r in rows],['classic','champions'])
        self.assertEqual(rows[1]['regulation'],'M-C')
    def test_split_audio_is_reassembled_and_verified_before_installing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'data').mkdir();(root/'assets/music').mkdir(parents=True)
            (root/'assets/music/part0').write_bytes(b'first');(root/'assets/music/part1').write_bytes(b'second')
            audio=b'firstsecond';row={'asset':'assets/music/not-required.mp3','path':'BlueRandom/song.mp3','chunks':['assets/music/part0','assets/music/part1'],'sha256':hashlib.sha256(audio).hexdigest()}
            data={'version':1,'files':[row],'config':{'global':{},'maps':{}},'gymTrainerTypes':[],'gymTrainers':[]}
            (root/'data/shared-music.json').write_text(json.dumps(data))
            plan=music.shared_plan(root,root/'game');self.assertEqual(plan[(root/'game/Audio/BGM/BlueRandom/song.mp3').resolve()],audio)
if __name__=='__main__':unittest.main()
