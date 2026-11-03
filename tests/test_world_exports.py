import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest
from server.ruby_marshal import RubyObject, dumps_simple

ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/file)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result
catalog=module('album_catalog','scripts/battle_polish/trainer_album_catalog.py')
photos=module('route_photos','scripts/export_route_photos.py')
def command(code,args,indent=0):
    return RubyObject('RPG::EventCommand',{'@code':code,'@parameters':args,'@indent':indent})
def event(commands,name=b'Trainer NPC'):
    graphic=RubyObject('Graphic',{'@character_name':b'trainer_fisher','@direction':2})
    page=RubyObject('Page',{'@list':commands,'@graphic':graphic})
    return RubyObject('Event',{'@name':name,'@id':11,'@pages':[page]})

class TrainerCatalogTests(unittest.TestCase):
    def test_static_calls_are_deduplicated_and_dynamic_calls_ignored(self):
        calls=[command(111,[12,b'TrainerBattle.start(:FISHER,"Gaultier")']),
               command(355,[b'TrainerBattle.start(:FISHER,"Gaultier")']),
               command(355,[b'TrainerBattle.start(kind,name); dangerous()'])]
        self.assertEqual(catalog.identities(calls),[['FISHER','Gaultier']])
        row=catalog.event_row(event(calls))
        self.assertEqual(row[:5],[11,'Trainer NPC','FISHER','Gaultier','trainer_fisher'])
        self.assertEqual(row[8],[['FISHER','Gaultier']])
    def test_only_victory_branch_self_switches_count_as_old_wins(self):
        calls=[command(111,[12,b'TrainerBattle.start(:FISHER,"Gaultier")']),
               command(123,[b'A',0],1),command(411,[]),command(123,[b'B',0],1),
               command(412,[]),command(123,[b'C',0])]
        self.assertEqual(catalog.event_row(event(calls))[9],['A'])
        self.assertIsNone(catalog.event_row(event(calls,b'Story Mode Trainer Test')))
    def test_missing_game_maps_do_not_generate_an_empty_replacement(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            self.assertIsNone(catalog.build(root,root/'game'))

class RouteCaptureTests(unittest.TestCase):
    def fixture(self,root):
        for name in ['game/Data/blue-route-captures','site/public/data']:(root/name).mkdir(parents=True)
        (root/'site/public/data/locations.json').write_text(json.dumps({'locations':[{'id':86,'name':'Route 1'},{'id':5,'name':'Old Route 1'}]}))
        (root/'site/public/data/region-points.json').write_text(json.dumps({'regions':{'0':{'name':'Beatha'}}}))
        raw=b'\x89PNG\r\n\x1a\n'+struct.pack('>I',13)+b'IHDR'+struct.pack('>II',480,274)
        (root/'game/Data/blue-route-captures/route-86.png').write_bytes(raw)
        return [1,[[86,'Route 1','route-86.png',0,10,12,480,274]],[[5,'Old Route 1']]]
    def write_export(self,root,data):
        (root/'game/Data/blue-route-captures.dat').write_bytes(dumps_simple(data))
    def test_import_preserves_raw_area_data_and_hides_only_missing_maps(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);data=self.fixture(root);self.write_export(root,data)
            before=(root/'site/public/data/locations.json').read_bytes()
            self.assertEqual(photos.import_photos(root),(1,1))
            manifest=json.loads((root/'site/public/data/region-points.json').read_text())
            self.assertEqual(manifest['inactiveAreaIds'],[5])
            self.assertEqual(manifest['areaImages']['86']['src'],'/assets/route-maps/route-86.png')
            self.assertEqual(manifest['areaImages']['86']['point'],[10,12])
            self.assertEqual((root/'site/public/data/locations.json').read_bytes(),before)
            self.assertEqual(photos.prepare(root),2)
    def test_invalid_identity_coverage_or_png_never_writes_site_files(self):
        for case in ['path','duplicate','coverage','png','size']:
            with self.subTest(case=case),tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);data=self.fixture(root)
                if case=='path':data[1][0][2]='../route-86.png'
                if case=='duplicate':data[1].append(data[1][0].copy())
                if case=='coverage':data[2]=[]
                if case=='png':(root/'game/Data/blue-route-captures/route-86.png').write_bytes(b'bad')
                if case=='size':data[1][0][-1]=200
                self.write_export(root,data)
                before=(root/'site/public/data/region-points.json').read_bytes()
                with self.assertRaises(ValueError):photos.import_photos(root)
                self.assertFalse((root/'site/public/assets/route-maps').exists())
                self.assertEqual((root/'site/public/data/region-points.json').read_bytes(),before)

if __name__=='__main__':unittest.main()
