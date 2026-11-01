import copy,json,os,tempfile,threading,unittest,urllib.error,urllib.request
from pathlib import Path
from scripts.online.rooms import Rooms,ProtocolError
from scripts.online.server import Server
from scripts.online.client import Client
from scripts.online.demo import run
from scripts.online.probe import cleanup,finalize,PLUGIN
CATALOG={'schema':1,'engineFingerprint':'a'*64,'species':{'PIKACHU':{'mega':False,'abilities':['STATIC']},'MAGIKARP':{'mega':False,'abilities':['SWIFTSWIM']},'RAICHU_3':{'mega':True,'abilities':['NOGUARD']}},'items':['RAICHUNITEY'],'moves':['TACKLE','SPLASH'],'natures':['HARDY']}
def team():return [dict(species='PIKACHU',ability='STATIC',item=None,nature='HARDY',moves=['TACKLE'],evs=[0]*6,ivs=[31]*6,level=50) for _ in range(6)]
class Clock:
    now=0
    def __call__(self):return self.now
class RoomTests(unittest.TestCase):
    def setUp(self):self.clock=Clock();self.rooms=Rooms(CATALOG,self.clock)
    def request(self,name='Player'):
        return {'protocol':1,'compatibility':self.rooms.fingerprint,'name':name,'team':team()}
    def pair(self):
        a=self.rooms.create(self.request('A'));b=self.rooms.join(a['room'],self.request('B'));return a,b
    def test_two_people_prepare_four_in_their_own_order_without_claiming_a_battle(self):
        a,b=self.pair();self.rooms.select(a['room'],a['token'],[5,1,0,3]);self.rooms.select(b['room'],b['token'],[4,3,2,1])
        state=self.rooms.state(a['room'],a['token'])
        self.assertEqual(state['state'],'prepared');self.assertEqual(state['picks'],[5,1,0,3]);self.assertFalse(state['battleAvailable'])
        self.assertEqual(len(self.rooms.rooms[a['room']]['players'][0]['team']),6)
    def test_tokens_and_opponent_private_fields_are_not_in_state(self):
        a,b=self.pair();self.rooms.select(a['room'],a['token'],[5,1,0,3]);state=self.rooms.state(b['room'],b['token']);text=json.dumps(state)
        for secret in [a['token'],b['token'],'STATIC','TACKLE','ivs','evs','item']:self.assertNotIn(secret,text)
        self.assertIsNone(state['picks']);self.assertTrue(state['players'][0]['ready'])
        with self.assertRaises(ProtocolError) as error:self.rooms.state(a['room'],'invalid')
        self.assertEqual(error.exception.status,401)
    def test_timeout_is_exactly_sixty_and_polling_cannot_extend_it(self):
        a,b=self.pair();self.clock.now=59.999
        self.assertEqual(self.rooms.state(a['room'],a['token'])['state'],'selecting')
        self.clock.now=60
        state=self.rooms.state(b['room'],b['token']);self.assertEqual(state['state'],'prepared');self.assertTrue(state['timedOut']);self.assertEqual(state['picks'],[0,1,2,3])
    def test_timeout_keeps_a_confirmed_opponent_selection(self):
        a,b=self.pair();self.rooms.select(a['room'],a['token'],[5,4,3,2]);self.clock.now=61
        self.assertEqual(self.rooms.state(a['room'],a['token'])['picks'],[5,4,3,2]);self.assertFalse(self.rooms.state(a['room'],a['token'])['timedOut'])
        self.assertEqual(self.rooms.state(b['room'],b['token'])['picks'],[0,1,2,3])
    def test_confirm_is_idempotent_but_cannot_change_after_commit(self):
        a,b=self.pair();first=self.rooms.select(a['room'],a['token'],[5,4,3,2]);self.assertEqual(first,self.rooms.select(a['room'],a['token'],[5,4,3,2]))
        with self.assertRaises(ProtocolError):self.rooms.select(a['room'],a['token'],[0,1,2,3])
    def test_invalid_indices_never_commit(self):
        a,b=self.pair()
        for bad in [[0,0,1,2],[0,1,2,6],[True,1,2,3],[0,1,2],None,'0123']:
            with self.assertRaises(ProtocolError):self.rooms.select(a['room'],a['token'],bad)
            self.assertIsNone(self.rooms.state(a['room'],a['token'])['picks'])
    def test_versions_and_catalogue_changes_rejected_before_join(self):
        a=self.rooms.create(self.request())
        for field,value in [('protocol',2),('protocol',True),('compatibility','b'*64)]:
            data=self.request();data[field]=value
            with self.assertRaises(ProtocolError):self.rooms.join(a['room'],data)
        self.assertEqual(len(self.rooms.rooms[a['room']]['players']),1)
        changed=copy.deepcopy(CATALOG);changed['moves'].append('PROTECT');self.assertNotEqual(Rooms(changed).fingerprint,self.rooms.fingerprint)
    def test_invalid_rosters_do_not_create_rooms(self):
        samples=[]
        for field,value in [('species','RAICHU_3'),('species',{}),('ability','SWIFTSWIM'),('item','UNKNOWN'),('nature','UNKNOWN'),('level',100),('level',True),('moves',['TACKLE','TACKLE']),('moves',[]),('evs',[252]*6),('ivs',[True]*6),('evs',[253,0,0,0,0,0])]:
            data=self.request();data['team'][0][field]=value;samples.append(data)
        data=self.request();data['team'].pop();samples.append(data)
        for data in samples:
            with self.assertRaises(ProtocolError):self.rooms.create(data)
        self.assertFalse(self.rooms.rooms)
    def test_reconnect_preserves_seat_and_deadline_and_leave_cancels_both(self):
        a,b=self.pair();self.clock.now=31
        state=self.rooms.state(a['room'],a['token']);self.assertEqual(state['you'],0);self.assertEqual(state['secondsRemaining'],29);self.assertFalse(state['players'][1]['connected'])
        self.rooms.leave(b['room'],b['token']);self.assertEqual(self.rooms.state(a['room'],a['token'])['state'],'cancelled')
        with self.assertRaises(ProtocolError):self.rooms.select(a['room'],a['token'],[0,1,2,3])
    def test_room_capacity_expiry_and_cleanup_are_bounded(self):
        self.rooms.max_rooms=1;a=self.rooms.create(self.request())
        with self.assertRaises(ProtocolError):self.rooms.create(self.request())
        self.clock.now=600;self.rooms.sweep();self.assertEqual(self.rooms.state(a['room'],a['token'])['state'],'expired')
        self.clock.now=660;self.rooms.sweep();self.assertFalse(self.rooms.rooms)
    def test_simultaneous_third_player_cannot_take_a_second_seat(self):
        a=self.rooms.create(self.request());barrier=threading.Barrier(3);out=[]
        def join():
            barrier.wait()
            try:self.rooms.join(a['room'],self.request());out.append('joined')
            except ProtocolError:out.append('rejected')
        threads=[threading.Thread(target=join) for _ in range(2)]
        for thread in threads:thread.start()
        barrier.wait()
        for thread in threads:thread.join(5)
        self.assertCountEqual(out,['joined','rejected'])
class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.rooms=Rooms(CATALOG);self.server=Server(('127.0.0.1',0),self.rooms)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start();self.url='http://127.0.0.1:'+str(self.server.server_port)
    def tearDown(self):self.server.shutdown();self.server.server_close();self.thread.join(5)
    def test_real_two_client_roundtrip_and_server_disallows_a_third_client(self):
        a=Client(self.url,self.rooms.fingerprint);b=Client(self.url,self.rooms.fingerprint);c=Client(self.url,self.rooms.fingerprint)
        state=a.enter('A',team());b.enter('B',team(),state['room'])
        with self.assertRaises(urllib.error.HTTPError) as error:c.enter('C',team(),state['room'])
        self.assertEqual(error.exception.code,409)
        a.select([5,0,2,3]);b.select([4,1,3,2]);self.assertEqual(a.state()['state'],'prepared');self.assertEqual(b.state()['picks'],[4,1,3,2])
        a.leave();self.assertEqual(b.state()['state'],'cancelled')
    def test_client_refuses_engine_mismatch_and_browser_origin(self):
        with self.assertRaises(ValueError):Client(self.url,'b'*64)
        request=urllib.request.Request(self.url+'/v1/hello',headers={'Origin':'https://evil.example'})
        with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(request,timeout=3)
        self.assertEqual(error.exception.code,403)
    def test_bad_payload_and_unimplemented_battle_route_do_not_change_rooms(self):
        for path,raw,content_type in [('/v1/rooms',b'[]','application/json'),('/v1/rooms',b'{oops','application/json'),('/v1/rooms',b'{}','text/plain'),('/v1/rooms/ABCDEFGH/battle',b'{"winner":0}','application/json')]:
            request=urllib.request.Request(self.url+path,raw,{'Content-Type':content_type})
            with self.assertRaises(urllib.error.HTTPError):urllib.request.urlopen(request,timeout=3)
        self.assertFalse(self.rooms.rooms)
    def test_demonstration_uses_two_http_clients(self):self.assertEqual(run(CATALOG)['clients'],2)
class ProbeFileTests(unittest.TestCase):
    def test_cleanup_removes_only_owned_plugin_and_preserves_offline_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp);owned=game/'Plugins'/PLUGIN;owned.mkdir(parents=True)
            for name in ('EngineProbe.rb','meta.txt'):(owned/name).write_text('probe')
            offline=game/'Plugins/Blue Battle Hub/HubUI.rb';offline.parent.mkdir();offline.write_bytes(b'offline untouched')
            cleanup(game);self.assertFalse(owned.exists());self.assertEqual(offline.read_bytes(),b'offline untouched')
    def test_cleanup_refuses_an_unexpected_file_without_removing_anything(self):
        with tempfile.TemporaryDirectory() as tmp:
            game=Path(tmp);owned=game/'Plugins'/PLUGIN;owned.mkdir(parents=True);(owned/'unknown.txt').write_text('keep');(owned/'EngineProbe.rb').write_text('probe')
            with self.assertRaises(ValueError):cleanup(game)
            self.assertEqual(len(list(owned.iterdir())),2)
    def test_export_rejects_pending_probes_and_changed_engine_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            project=Path(tmp);game=project/'game';(game/'Data').mkdir(parents=True);(game/'Plugins').mkdir()
            exe=game/'Game.exe';exe.write_bytes(b'fixture');(game/'Data/Scripts.rxdata').write_bytes(b'scripts')
            (game/'Data/blue-online-catalog.json').write_text(json.dumps(CATALOG));(game/'Data/blue-online-engine-validation.txt').write_text('RESULT=PASS\n')
            request=game/'Data/blue-online-engine-request.txt';request.write_text('pending')
            with self.assertRaises(ValueError):finalize(project,game)
            request.unlink();output=finalize(project,game)
            self.assertEqual(json.loads(output.read_text())['schema'],1)
            changed=(game/'Data/blue-online-catalog.json').stat().st_mtime+2;os.utime(exe,(changed,changed))
            with self.assertRaises(ValueError):finalize(project,game)
