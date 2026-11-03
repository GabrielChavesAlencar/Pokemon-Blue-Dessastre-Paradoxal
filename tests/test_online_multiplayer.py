import json,sys,tempfile,threading,time,unittest,urllib.error,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'/'battle_lab'))
import mp_client,mp_server
from mp_server import ProtocolError,Rooms,Server
MECHANICS={'mega':True,'zmove':False,'tera':True,'dynamax':False}
class Clock:
    now=0
    def __call__(self):return self.now
def form(name='A',size=6,compatibility='v1',**extra):
    return {'protocol':3,'compatibility':compatibility,'name':name,'team':[f'Pikachu{i}\n- Tackle' for i in range(size)],'preview':[f'Pikachu{i}' for i in range(size)],**extra}
def host(name='A',size=6,fmt='double',**extra):return form(name,size,format=fmt,mechanics=dict(MECHANICS),**extra)
def entry(n,label='turn',digest='h',choice='m0'):return {'n':n,'label':label,'hash':digest,'choice':choice}
class RoomTests(unittest.TestCase):
    def setUp(self):self.clock=Clock();self.rooms=Rooms(self.clock)
    def pair(self,fmt='single',size=3):
        a=self.rooms.create(host('A',size,fmt));b=self.rooms.join(a['room'],form('B',size));return a,b
    def advance(self,room,tokens,target):
        # Real helpers poll several times per second; the clock must not skip past them.
        while self.clock.now<target:
            self.clock.now=min(target,self.clock.now+10)
            if self.clock.now<target:
                for token in tokens:self.rooms.state(room,token)
    def test_single_room_starts_with_one_seed_for_both(self):
        a,b=self.pair()
        self.assertEqual(b['state'],'prepared')
        one,two=self.rooms.state(a['room'],a['token']),self.rooms.state(a['room'],b['token'])
        self.assertEqual(one['seed'],two['seed']);self.assertEqual(one['teams'],two['teams']);self.assertEqual((one['you'],two['you']),(0,1))
        self.assertEqual(two['mechanics'],MECHANICS)
    def test_third_player_and_different_game_version_cannot_enter(self):
        a=self.rooms.create(host('A',3,'single'))
        with self.assertRaises(ProtocolError) as error:self.rooms.join(a['room'],form('B',3,'other'))
        self.assertEqual(error.exception.code,'compatibility')
        self.rooms.join(a['room'],form('B',3))
        with self.assertRaises(ProtocolError) as error:self.rooms.join(a['room'],form('C',3))
        self.assertEqual(error.exception.code,'phase')
    def test_doubles_need_six_and_hide_benched_pokemon(self):
        with self.assertRaises(ProtocolError):self.rooms.create(host('A',3,'double'))
        a,b=self.pair('double',6)
        self.assertEqual(b['state'],'selecting');self.assertNotIn('teams',b);self.assertNotIn('seed',b)
        text=json.dumps(self.rooms.state(a['room'],b['token']))
        self.assertNotIn('Tackle',text);self.assertIn('Pikachu5',text)
        self.rooms.select(a['room'],a['token'],[5,1,0,3]);self.rooms.select(a['room'],b['token'],[4,3,2,1])
        view=self.rooms.state(a['room'],a['token'])
        self.assertEqual(view['state'],'prepared');self.assertEqual(view['previews'],[['Pikachu5','Pikachu1','Pikachu0','Pikachu3'],['Pikachu4','Pikachu3','Pikachu2','Pikachu1']])
        self.assertNotIn('Pikachu2\n',''.join(view['teams'][0]))
    def test_pick_timeout_uses_first_four_and_keeps_a_confirmed_choice(self):
        a,b=self.pair('double',6);self.rooms.select(a['room'],a['token'],[5,4,3,2]);self.advance(a['room'],[a['token'],b['token']],59.9)
        self.assertEqual(self.rooms.state(a['room'],a['token'])['state'],'selecting')
        self.rooms.state(a['room'],b['token']);self.clock.now=60
        view=self.rooms.state(a['room'],b['token'])
        self.assertEqual(view['state'],'prepared');self.assertEqual(view['picks'],[0,1,2,3]);self.assertTrue(view['timedOut'])
    def test_decision_stays_hidden_until_both_sides_reach_the_barrier(self):
        a,b=self.pair();room=a['room']
        first=self.rooms.sync(room,a['token'],entry(0,choice='secret'))
        self.assertFalse(first['ready']);self.assertNotIn('secret',json.dumps(first))
        self.assertNotIn('secret',json.dumps(self.rooms.wait(room,b['token'],0)))
        second=self.rooms.sync(room,b['token'],entry(0,choice='other'))
        self.assertTrue(second['ready']);self.assertEqual(second['choices'],['secret','other'])
        self.assertEqual(self.rooms.wait(room,a['token'],0)['choices'],['secret','other'])
    def test_retry_is_idempotent_but_a_confirmed_decision_cannot_change(self):
        a,b=self.pair();room=a['room']
        self.rooms.sync(room,a['token'],entry(0));self.rooms.sync(room,a['token'],entry(0))
        with self.assertRaises(ProtocolError) as error:self.rooms.sync(room,a['token'],entry(0,choice='changed'))
        self.assertEqual(error.exception.code,'replay')
        with self.assertRaises(ProtocolError) as error:self.rooms.sync(room,a['token'],entry(5))
        self.assertEqual(error.exception.code,'order')
    def test_different_state_hash_stops_the_match_without_a_winner(self):
        a,b=self.pair();room=a['room']
        self.rooms.sync(room,a['token'],entry(0,digest='one'))
        result=self.rooms.sync(room,b['token'],entry(0,digest='two'))
        self.assertFalse(result['ready']);self.assertEqual(result['reason'],'desync');self.assertIsNone(result['winner'])
        self.assertEqual(self.rooms.state(room,a['token'])['state'],'finished')
    def test_absent_player_loses_by_decision_timeout(self):
        a,b=self.pair();room=a['room'];self.rooms.sync(room,a['token'],entry(0))
        self.advance(room,[a['token'],b['token']],mp_server.DECISION_SECONDS-1)
        self.assertEqual(self.rooms.state(room,a['token'])['state'],'prepared')
        self.rooms.state(room,b['token']);self.clock.now=mp_server.DECISION_SECONDS
        view=self.rooms.state(room,a['token'])
        self.assertEqual((view['state'],view['reason'],view['winner']),('finished','timeout',0))
    def test_silent_helper_counts_as_disconnect_and_leaving_as_forfeit(self):
        a,b=self.pair();room=a['room'];self.clock.now=mp_server.DISCONNECT_SECONDS-1;self.rooms.state(room,a['token'])
        self.clock.now=mp_server.DISCONNECT_SECONDS
        view=self.rooms.state(room,a['token']);self.assertEqual((view['reason'],view['winner']),('disconnect',0))
        c,d=self.pair();self.rooms.leave(c['room'],d['token'])
        view=self.rooms.state(c['room'],c['token']);self.assertEqual((view['reason'],view['winner']),('forfeit',0))
    def test_end_barrier_closes_the_room_and_late_leave_changes_nothing(self):
        a,b=self.pair();room=a['room']
        self.rooms.sync(room,a['token'],entry(0,'end','r1',''));result=self.rooms.sync(room,b['token'],entry(0,'end','r1',''))
        self.assertTrue(result['ready']);self.assertEqual(result['reason'],'complete')
        self.rooms.leave(room,a['token'])
        self.assertTrue(self.rooms.wait(room,b['token'],0)['ready'])
        self.assertEqual(self.rooms.state(room,b['token'])['reason'],'complete')
    def test_invalid_fields_are_rejected(self):
        a,b=self.pair();room=a['room']
        for data in [{'n':0},{'n':True,'label':'t','hash':'h','choice':''},{'n':0,'label':'t','hash':'h','choice':'x'*513},{'n':0,'label':'t','hash':'','choice':''},{**entry(0),'winner':0}]:
            with self.subTest(data=data),self.assertRaises(ProtocolError):self.rooms.sync(room,a['token'],data)
        for name in ['','x'*25,'<b>']:
            with self.subTest(name=name),self.assertRaises(ProtocolError):self.rooms.create(host(name))
        with self.assertRaises(ProtocolError):self.rooms.state(room,'wrong')
class Player:
    """Plays the game's side of the file bridge."""
    def __init__(self,root,name,**start):
        self.dir=root/name;self.dir.mkdir();self.cmd=0
        team='\n\n'.join(f'Pikachu{i}\n- Tackle' for i in range(3))
        mp_client.write_kv(self.dir/'start.txt',{'name':name,'team':team,'preview':'\n'.join(f'Pikachu{i}' for i in range(3)),**start})
        self.session=mp_client.Session(self.dir,root/'game')
        self.thread=threading.Thread(target=self.session.run,daemon=True);self.thread.start()
    def state(self):
        path=self.dir/'state.txt'
        return mp_client.read_kv(path) if path.is_file() else {}
    def wait(self,test,seconds=15):
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            state=self.state()
            if test(state):return state
            time.sleep(.02)
        raise AssertionError(f'Timeout; last state: {self.state()}')
    def send(self,**values):
        self.cmd+=1;mp_client.write_kv(self.dir/f'cmd-{self.cmd}.txt',values)
class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        game=self.root/'game';(game/'Data').mkdir(parents=True);(game/'Plugins').mkdir();(game/'PBS').mkdir()
        (game/'Game.exe').write_bytes(b'exe');(game/'Data/Scripts.rxdata').write_bytes(b'scripts')
        with Server(('127.0.0.1',0),Rooms()) as probe:self.port=probe.server_port
    def host(self):
        return Player(self.root,'Host',mode='host',format='single',mechanics='mega,tera',port=self.port)
    def test_two_helpers_play_through_the_files_with_the_embedded_server(self):
        one=self.host()
        room=one.wait(lambda s:s.get('room'))['room']
        two=Player(self.root,'Guest',mode='join',address='127.0.0.1',code=room,port=self.port)
        for player in (one,two):
            state=player.wait(lambda s:s.get('state')=='prepared' and s.get('seed'))
            self.assertEqual(state['mechanics'],'mega,tera')
        self.assertEqual(one.state()['seed'],two.state()['seed'])
        self.assertEqual(one.state()['team0'],two.state()['team0'])
        self.assertEqual(one.state()['you'],'0');self.assertEqual(two.state()['you'],'1')
        one.send(op='sync',n=0,label='turn1',hash='abc',choice='m0.-1')
        time.sleep(.5);self.assertFalse((one.dir/'sync-0.txt').exists())
        two.send(op='sync',n=0,label='turn1',hash='abc',choice='s2')
        for player in (one,two):
            player.wait(lambda s:(player.dir/'sync-0.txt').exists())
            self.assertEqual(mp_client.read_kv(player.dir/'sync-0.txt'),{'a':'m0.-1','b':'s2'})
        two.send(op='leave');two.thread.join(10)
        self.assertEqual(one.wait(lambda s:s.get('reason')=='forfeit')['winner'],'0')
        one.send(op='leave')
    def test_wrong_room_shows_a_readable_error(self):
        one=self.host();one.wait(lambda s:s.get('room'))
        two=Player(self.root,'Guest',mode='join',address='127.0.0.1',code='AAAAAA',port=self.port)
        state=two.wait(lambda s:s.get('link')=='failed')
        self.assertIn('Sala inexistente',state['error'])
        one.send(op='leave')
    def test_unreachable_host_explains_how_to_fix_it(self):
        two=Player(self.root,'Guest',mode='join',address='127.0.0.1',code='AAAAAA',port=self.port)
        state=two.wait(lambda s:s.get('link')=='failed')
        self.assertIn('firewall',state['error'])
    def test_fingerprint_ignores_line_endings_but_sees_real_changes(self):
        game=self.root/'game';plugin=game/'Plugins/a.rb';plugin.write_bytes(b'x=1\n');first=mp_client.fingerprint(game)
        plugin.write_bytes(b'x=1\r\n');self.assertEqual(mp_client.fingerprint(game),first)
        plugin.write_bytes(b'x=2\n');self.assertNotEqual(mp_client.fingerprint(game),first)
if __name__=='__main__':unittest.main()
