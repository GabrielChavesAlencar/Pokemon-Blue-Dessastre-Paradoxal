import copy,json,tempfile,threading,unittest,urllib.error
from pathlib import Path
from scripts.online.rooms import ProtocolError
from scripts.online.turn_service import Turns,TurnServer
from scripts.online.turns import Client,roster,cleanup,PLUGIN
from tests.test_online_rooms import CATALOG,team

class TurnTransportTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        self.turns=Turns(self.root,'version',['player-a','player-b'])
        self.worker={'protocol':2,'state':'choosing','turn':0,'messages':['Public event'],
          'request':{'seq':1,'side':0,'battler':0,'kind':'action','options':[{'kind':'move','slot':0,'target':1,'move':'TACKLE','pp':35},{'kind':'switch','slot':2,'target':-1}]}}
        self.write(self.worker)
    def write(self,value):(self.root/'state.json').write_text(json.dumps(value),encoding='utf8')
    def test_opponent_cannot_see_private_legal_move_list(self):
        self.assertIsNone(self.turns.state(1)['request']);self.assertNotIn('TACKLE',json.dumps(self.turns.state(1)))
        self.assertEqual(self.turns.state(0)['request']['options'][0]['move'],'TACKLE')
        self.assertNotIn('player-a',json.dumps(self.turns.state(0)))
    def test_owner_and_engine_version_are_required(self):
        for token,version in [('wrong','version'),('player-a','different')]:
            with self.assertRaises(ProtocolError):self.turns.auth(token,version)
        with self.assertRaises(ProtocolError):self.turns.submit(1,{'seq':1,'option':0})
    def test_command_is_one_native_legal_option_and_retry_is_idempotent(self):
        first=self.turns.submit(0,{'seq':1,'option':1});raw=(self.root/'command.tsv').read_bytes()
        self.assertEqual(raw,b'1\tswitch\t2\t-1\n');self.assertFalse(first['replayed'])
        self.assertTrue(self.turns.submit(0,{'seq':1,'option':1})['replayed'])
        self.assertEqual((self.root/'command.tsv').read_bytes(),raw)
        with self.assertRaises(ProtocolError):self.turns.submit(0,{'seq':1,'option':0})
    def test_invalid_indexes_damage_winner_and_boolean_values_are_rejected(self):
        for data in [{'seq':1,'option':-1},{'seq':1,'option':99},{'seq':True,'option':0},
                     {'seq':1,'option':0,'damage':999},{'winner':0},{'seq':1,'option':'0'}]:
            with self.subTest(data=data),self.assertRaises(ProtocolError):self.turns.submit(0,data)
        self.assertFalse((self.root/'command.tsv').exists())
    def test_old_turns_cannot_overwrite_current_choice(self):
        self.worker['request']['seq']=2;self.write(self.worker)
        with self.assertRaises(ProtocolError):self.turns.submit(0,{'seq':1,'option':0})
        self.turns.submit(0,{'seq':2,'option':0})
        self.assertTrue((self.root/'command.tsv').read_text().startswith('2\t'))
    def test_finished_result_only_comes_from_worker(self):
        self.write({'protocol':2,'state':'finished','winner':1,'result':2})
        self.assertEqual(self.turns.state(0)['winner'],1)
        with self.assertRaises(ProtocolError):self.turns.submit(0,{'seq':1,'option':0})
    def test_concurrent_different_commands_accept_exactly_one(self):
        barrier=threading.Barrier(2);answers=[]
        def submit(option):
            barrier.wait()
            try:self.turns.submit(0,{'seq':1,'option':option});answers.append('ok')
            except ProtocolError:answers.append('conflict')
        threads=[threading.Thread(target=submit,args=(i,)) for i in range(2)]
        for t in threads:t.start()
        for t in threads:t.join()
        self.assertCountEqual(answers,['ok','conflict'])
    def test_two_http_clients_observe_their_own_side_and_send_real_requests(self):
        with TurnServer(('127.0.0.1',0),self.turns) as server:
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                clients=[Client('http://127.0.0.1:'+str(server.server_port),token,'version') for token in self.turns.tokens]
                self.assertIsNone(clients[1].call('/v2/state')['request'])
                self.assertEqual(clients[0].call('/v2/command',{'seq':1,'option':0})['accepted'],1)
                self.worker['request'].update(seq=2,side=1,battler=1);self.write(self.worker)
                self.assertEqual(clients[1].call('/v2/command',{'seq':2,'option':0})['accepted'],2)
                with self.assertRaises(urllib.error.HTTPError):clients[0].call('/v2/command',{'seq':2,'option':0})
            finally:server.shutdown();thread.join(timeout=5)
    def test_roster_preserves_pick_order_and_validates_native_catalog(self):
        data={'format':'double','teams':[team(),team()],'picks':[[5,1,0,3],[4,3,2,1]]}
        raw=roster(CATALOG,data);self.assertEqual(len(raw.splitlines()),10)
        data['teams'][0][5]['ability']='IMPOSSIBLE'
        with self.assertRaises(ProtocolError):roster(CATALOG,data)
    def test_cleanup_rejects_unknown_files_and_keeps_offline_sources(self):
        game=self.root/'game';target=game/'Plugins'/PLUGIN;target.mkdir(parents=True)
        (target/'user-file.txt').write_text('keep')
        with self.assertRaises(ValueError):cleanup(game)
        self.assertTrue((target/'user-file.txt').exists())
if __name__=='__main__':unittest.main()
