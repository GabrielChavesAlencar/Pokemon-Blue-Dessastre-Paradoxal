"""Local importer transactions and classification, using only synthetic assets."""
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'server'));sys.path.insert(0,str(ROOT/'tests'))
from music_fixture import make_fixture,wav_bytes
from ruby_marshal import loads
from music_editor import MusicError,LIMIT,validate_audio
spec=importlib.util.spec_from_file_location('playlists',ROOT/'scripts/music/import_playlists.py')
playlists=importlib.util.module_from_spec(spec);spec.loader.exec_module(playlists)

class PlaylistTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.project=Path(self.tmp.name)/'project';self.game=self.project/'game';self.source=Path(self.tmp.name)/'source'
        make_fixture(self.game)
        plugins=self.project/'scripts/music';plugins.mkdir(parents=True)
        for name in ['BlueMusic.rb','RandomValidation.rb','meta.txt']:(plugins/name).write_bytes((ROOT/'scripts/music'/name).read_bytes())
        reference=self.project/'site/public/data';reference.mkdir(parents=True)
        (reference/'story-trainers.json').write_text(json.dumps({'masters':[{'name':'Marigold'}]}),encoding='utf8')
        (self.game/'PBS/trainer_types.txt').write_text('[LEADER_Test]\nName = Gym Leader\n[AROMALADY]\nName = Aroma Lady\n',encoding='utf8')
        (self.game/'PBS/trainers.txt').write_text('[AROMALADY,Marigold (1v1 Basic Power)]\nPokemon = TESTMON,5\n[AROMALADY,Jane]\nPokemon = TESTMON,5\n',encoding='utf8')
        for i,folder in enumerate(playlists.FOLDERS.values()):
            directory=self.source/folder;directory.mkdir(parents=True)
            (directory/'Musica.wav').write_bytes(wav_bytes(1600+i*200))
        self.config={'version':1,'global':{'wildVictory':{'mode':'mute','track':'','volume':60,'pitch':100}},'maps':{'1':{'mode':'custom','track':'Town.wav','volume':50,'pitch':100}}}
        (self.game/'Data/blue-music.json').write_text(json.dumps(self.config),encoding='utf8')
    def install(self,apply=True):return playlists.install(self.project,self.game,self.source,apply)
    def snapshot(self):return {p.relative_to(self.project):p.read_bytes() for p in self.project.rglob('*') if p.is_file() and '.blue-backups' not in p.parts}

    def test_import_preserves_originals_and_is_idempotent(self):
        before=self.snapshot();preview=self.install(False)
        self.assertFalse(preview['applied']);self.assertEqual(self.snapshot(),before)
        result=self.install();self.assertEqual(result['categories'],{'trainer':1,'wild':1,'gym':1})
        for p,raw in before.items():
            if p!=Path('game/Data/blue-music.json'):self.assertEqual((self.project/p).read_bytes(),raw)
        value=json.loads((self.game/'Data/blue-music.json').read_text())
        self.assertEqual(value['maps'],self.config['maps']);self.assertEqual(value['global']['wildVictory'],self.config['global']['wildVictory'])
        manifest=json.loads((self.project/'data/battle-music-playlists.json').read_text(encoding='utf8'))
        for category,tracks in manifest['categories'].items():
            self.assertEqual(value['global'][category]['mode'],'random')
            for track in tracks:self.assertEqual((self.game/'Audio/BGM'/track['file']).read_bytes(),(self.source/track['source']).read_bytes())
        categories=loads((self.game/'Data/blue-music-categories.rxdata').read_bytes())
        self.assertEqual(categories[1],[b'LEADER_Test'])
        self.assertEqual(categories[2],[[b'AROMALADY',b'Marigold']])
        self.assertEqual(len(categories[3]),3)
        self.assertEqual(self.install()['files'],0)

    def test_missing_or_invalid_source_does_not_partially_install(self):
        bad=self.source/'gym leader/Musica.wav';bad.unlink();before=self.snapshot()
        with self.assertRaises(ValueError):self.install()
        self.assertEqual(self.snapshot(),before)
        bad.write_bytes(b'not a valid wave')
        with self.assertRaises(MusicError):self.install()
        self.assertEqual(self.snapshot(),before)

    def test_failure_rolls_back_new_audio_and_existing_configuration(self):
        before=self.snapshot();original=playlists.atomic;failed=False
        def fail_once(path,raw):
            nonlocal failed
            if path==self.game/'Data/blue-music.rxdata' and not failed:
                failed=True;raise OSError('simulated disk failure')
            original(path,raw)
        with patch.object(playlists,'atomic',side_effect=fail_once),self.assertRaises(OSError):self.install()
        self.assertEqual(self.snapshot(),before)

    def test_local_import_accepts_valid_audio_above_web_upload_limit(self):
        raw=wav_bytes(LIMIT//2+1000)
        self.assertGreater(len(raw),LIMIT)
        with self.assertRaises(MusicError):validate_audio(raw,'.wav')
        (self.source/'gym leader/Musica.wav').write_bytes(raw)
        manifest,_=playlists.build_plan(self.project,self.game,self.source)
        self.assertEqual(manifest['categories']['gym'][0]['bytes'],len(raw))

if __name__=='__main__':unittest.main()
