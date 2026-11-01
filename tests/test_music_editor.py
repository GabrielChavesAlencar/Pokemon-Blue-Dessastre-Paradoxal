import base64,hashlib,json,sys,tempfile,threading,unittest,urllib.request,urllib.error
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'server'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import music_editor as music
from ruby_marshal import loads,dumps_simple,text
from main import atomic_write,backup_file,build_handler
from http.server import ThreadingHTTPServer
from music_fixture import make_fixture,wav_bytes

class MusicTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.game=Path(self.tmp.name)/'game';self.backups=Path(self.tmp.name)/'backups';make_fixture(self.game)
        self.lock=threading.Lock()
    def save(self,obj):return music.save_assignment(self.game,self.backups,obj,lock=self.lock,atomic_write=atomic_write,backup_file=backup_file)
    def upload(self,obj):return music.upload(self.game,self.backups,obj,lock=self.lock,atomic_write=atomic_write,backup_file=backup_file)
    def payload(self,**kw):return {'scope':'global','target':'wild','hash':music.config(self.game)[1],'mode':'custom','track':'Battle.wav','volume':73,'pitch':105,**kw}

    def test_catalog_and_original_map_are_read_without_executing_ruby(self):
        data=music.catalog(self.game)
        self.assertEqual(len(data['tracks']),2);self.assertEqual(data['maps'],[{'id':1,'name':'Fixture City'}])
        original=music.assignment(self.game,'map','1')['original']
        self.assertEqual(original,{'track':'Town','volume':80,'pitch':100,'enabled':True})

    def test_map_and_battle_assignments_preserve_all_original_game_files(self):
        before={p:p.read_bytes() for p in self.game.rglob('*') if p.is_file()}
        first=self.save(self.payload())
        self.save(self.payload(scope='map',target='1',hash=first['hash'],volume=61))
        config=music.config(self.game)[0]
        self.assertEqual(config['global']['wild']['track'],'Battle.wav');self.assertEqual(config['maps']['1']['volume'],61)
        self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))
        runtime=loads((self.game/'Data/blue-music.rxdata').read_bytes())
        self.assertEqual(runtime[0],1);self.assertEqual(runtime[1][0][0],b'wild');self.assertEqual(runtime[2][0][2],b'Battle.wav')

    def test_restore_original_removes_override_and_keeps_backup(self):
        self.save(self.payload(scope='map',target=1))
        old=(self.game/'Data/blue-music.json').read_bytes()
        self.save(self.payload(scope='map',target=1,mode='original'))
        self.assertNotIn('1',music.config(self.game)[0]['maps'])
        backups=list((self.backups/'Data/blue-music.json').glob('*.bak'))
        self.assertTrue(any(p.read_bytes()==old for p in backups))

    def test_random_pools_are_independent_and_encoded_as_native_arrays(self):
        self.save(self.payload(mode='random',tracks=['Town.wav','Battle.wav','Town.wav']))
        self.save(self.payload(target='gym',mode='random',tracks=['Battle.wav']))
        value=music.config(self.game)[0]['global']
        self.assertEqual(value['wild']['tracks'],['Town.wav','Battle.wav'])
        self.assertEqual(value['gym']['tracks'],['Battle.wav'])
        rows=loads((self.game/'Data/blue-music.rxdata').read_bytes())[1]
        self.assertEqual({r[0]:r[2] for r in rows},{b'gym':[b'Battle.wav'],b'wild':[b'Town.wav',b'Battle.wav']})
        self.save(self.payload(target='gym',mode='original'))
        self.assertNotIn('gym',music.config(self.game)[0]['global'])
        self.assertEqual(music.config(self.game)[0]['global']['wild'],value['wild'])

    def test_random_rejects_empty_unknown_and_unsupported_destinations(self):
        for changes in [{'tracks':[]},{'tracks':'Town.wav'},{'tracks':['../Town.wav']},{'tracks':['missing.wav']},{'tracks':[None]},{'tracks':['Town.wav']*257},{'target':'wildVictory'},{'target':'trainerVictory'},{'scope':'map','target':1}]:
            with self.subTest(changes=changes),self.assertRaises(music.MusicError):
                self.save(self.payload(**{'mode':'random','tracks':['Town.wav'],**changes}))
        self.assertFalse((self.game/'Data/blue-music.json').exists())

    def test_stale_configuration_hash_cannot_overwrite_other_assignment(self):
        request=self.payload();self.save(request);before=(self.game/'Data/blue-music.json').read_bytes()
        with self.assertRaises(music.MusicError) as error:self.save({**request,'target':'trainer'})
        self.assertEqual(error.exception.status,409);self.assertEqual((self.game/'Data/blue-music.json').read_bytes(),before)

    def test_invalid_scope_track_volume_and_pitch_are_rejected(self):
        for changes in [{'scope':'unknown'},{'scope':'map','target':999},{'target':'unknown'},{'track':'../secret.wav'},{'track':'missing.wav'},{'volume':101},{'volume':True},{'pitch':0}]:
            with self.subTest(changes=changes),self.assertRaises(music.MusicError):self.save(self.payload(**changes))
        self.assertFalse((self.game/'Data/blue-music.json').exists())

    def test_import_and_replace_require_expected_hash_and_keep_exact_backup(self):
        data=wav_bytes(3200)
        uploaded=self.upload({'filename':'Custom.wav','data':base64.b64encode(data).decode(),'mode':'create'})
        self.assertEqual((self.game/'Audio/BGM/Custom.wav').read_bytes(),data)
        with self.assertRaises(music.MusicError):self.upload({'filename':'Custom.wav','data':base64.b64encode(data).decode(),'mode':'create'})
        updated=wav_bytes(4000)
        self.upload({'filename':'Custom.wav','data':base64.b64encode(updated).decode(),'mode':'replace','hash':uploaded['hash']})
        self.assertEqual((self.game/'Audio/BGM/Custom.wav').read_bytes(),updated)
        self.assertEqual(next((self.backups/'Audio/BGM/Custom.wav').glob('*.bak')).read_bytes(),data)

    def test_import_rejects_bad_formats_and_path_traversal(self):
        for name,data in [('bad.wav',b'not audio'),('../out.wav',wav_bytes()),('x.exe',wav_bytes()),('CON.wav',wav_bytes()),('x.mid',b'not MIDI')]:
            with self.subTest(name=name),self.assertRaises(music.MusicError):self.upload({'filename':name,'data':base64.b64encode(data).decode(),'mode':'create'})
        self.assertEqual(len(music.catalog(self.game)['tracks']),2)

    def test_replace_nested_track_does_not_escape_music_folder(self):
        folder=self.game/'Audio/BGM/Sub';folder.mkdir();path=folder/'Town.wav';path.write_bytes(wav_bytes())
        self.upload({'filename':'Sub/Town.wav','data':base64.b64encode(wav_bytes(2000)).decode(),'mode':'replace','hash':music.file_sha(path)})
        self.assertEqual(path.read_bytes(),wav_bytes(2000))

    def test_failed_transaction_restores_prior_configuration(self):
        self.save(self.payload());before={p:p.read_bytes() for p in (self.game/'Data').iterdir() if p.is_file()}
        def fail(path,data):
            if path.name=='blue-music.rxdata':raise OSError('simulated failure')
            atomic_write(path,data)
        with self.assertRaises(OSError):
            music.save_assignment(self.game,self.backups,self.payload(target='trainer'),lock=self.lock,atomic_write=fail,backup_file=backup_file)
        self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))

    def test_audio_ranges(self):
        self.assertEqual(music.range_slice('bytes=2-8',20),(2,8,206))
        self.assertEqual(music.range_slice('bytes=-5',20),(15,19,206))
        self.assertEqual(music.range_slice('bytes=15-',20),(15,19,206))
        for header in ['bytes=99-100','bytes=5-2','bytes=0-1,3-4','bytes=-0']:
            with self.assertRaises(music.MusicError):music.range_slice(header,20)

    def test_marshal_configuration_and_malformed_input(self):
        self.assertEqual(loads(dumps_simple([1,'música',True,None,-999]))[:1],[1])
        self.assertEqual(text(loads(dumps_simple('música'))),'música')
        for raw in [b'',b'\x04\x08z',b'\x04\x08[\x06',b'\x04\x08@\x06']:
            with self.assertRaises(ValueError):loads(raw)

class MusicAPITests(unittest.TestCase):
    payload=MusicTests.payload
    def setUp(self):
        MusicTests.setUp(self)
        self.server=ThreadingHTTPServer(('127.0.0.1',0),build_handler(self.game,self.backups,0))
        self.server.RequestHandlerClass=build_handler(self.game,self.backups,self.server.server_port)
        thread=threading.Thread(target=self.server.serve_forever,daemon=True);thread.start()
        self.addCleanup(self.server.server_close);self.addCleanup(self.server.shutdown)
        self.base='http://127.0.0.1:'+str(self.server.server_port)
    def test_http_preview_range_and_assignment(self):
        request=urllib.request.Request(self.base+'/api/music/audio?id=Town.wav',headers={'Range':'bytes=0-11'})
        with urllib.request.urlopen(request) as response:
            self.assertEqual(response.status,206);self.assertEqual(len(response.read()),12)
            self.assertEqual(response.headers['Content-Range'],'bytes 0-11/'+str((self.game/'Audio/BGM/Town.wav').stat().st_size))
        body=json.dumps(self.payload()).encode()
        request=urllib.request.Request(self.base+'/api/music/assignment',data=body,headers={'Content-Type':'application/json','X-Blue-Studio':'1'})
        with urllib.request.urlopen(request) as response:self.assertTrue(json.load(response)['ok'])
        request=urllib.request.Request(self.base+'/api/music/assignment',data=body,headers={'Content-Type':'application/json'})
        with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(request)
        self.assertEqual(error.exception.code,403)

if __name__=='__main__':unittest.main()
