"""A09: synthetic Map001 transfer context; fail closed on ownership and runtime."""
from __future__ import annotations
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts/regions'))
from server.ruby_marshal import RubyObject, integer
import audit_unova_a04_mapids as a04
import audit_unova_a06_references as a06
import audit_unova_a07_reference_provenance as a07
import audit_unova_a08_readiness as a08
import audit_unova_a09_intro_and_claims as a09


def marshal(obj):
    def sym(x):
        raw=x.encode('utf-8');return b':'+integer(len(raw))+raw
    def value(x):
        if x is None:return b'0'
        if type(x) is bool:return b'T' if x else b'F'
        if type(x) is int:return b'i'+integer(x)
        if isinstance(x,bytes):return b'"'+integer(len(x))+x
        if isinstance(x,list):return b'['+integer(len(x))+b''.join(value(y) for y in x)
        if isinstance(x,dict):return b'{'+integer(len(x))+b''.join(value(k)+value(v) for k,v in x.items())
        if isinstance(x,RubyObject):return b'o'+sym(x.name)+integer(len(x.attrs))+b''.join(sym(k)+value(v) for k,v in x.attrs.items())
        raise TypeError(type(x).__name__)
    return b'\x04\x08'+value(obj)


def command(code,params=None):
    return RubyObject('RPG::EventCommand',{'@code':code,'@parameters':params or [],'@indent':0})


def mapp(with_two=True):
    cond=RubyObject('RPG::Event::Page::Condition',{'@switch1_valid':True,'@switch1_id':42,'@switch2_valid':False})
    intro_page=RubyObject('RPG::Event::Page',{'@trigger':3,'@condition':cond,
        '@list':[command(111,[0,42,0]),command(201,[0,3,5,6,2]),command(412),command(0)]})
    page2=RubyObject('RPG::Event::Page',{'@trigger':0,'@list':[command(0)]})
    quick=RubyObject('RPG::Event::Page',{'@trigger':0,
        '@list':[command(108,[b'init']),command(201,[0,3,7,8,2]),command(0)]})
    events={1:RubyObject('RPG::Event',{'@name':b'Intro','@pages':[intro_page,page2]})}
    if with_two:
        events[2]=RubyObject('RPG::Event',{'@name':b'Quick start intro','@pages':[quick,page2]})
    return marshal(RubyObject('RPG::Map',{'@events':events,'@width':20,'@height':20,'@tileset_id':1}))


def second_map():
    return marshal(RubyObject('RPG::Map',{'@events':{},'@width':20,'@height':20,'@tileset_id':1}))


class A09Tests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix='unova-a09-');self.addCleanup(t.cleanup)
        self.root=Path(t.name);self.game=self.root/'game';self.data=self.game/'Data';self.data.mkdir(parents=True)
        self.project=self.root/'repo';self.project.mkdir()
        (self.data/'Map001.rxdata').write_bytes(mapp())
        (self.data/'Map002.rxdata').write_bytes(second_map())
        infos={i:RubyObject('RPG::MapInfo',{'@name':('Test '+str(i)).encode()}) for i in (1,2)}
        (self.data/'MapInfos.rxdata').write_bytes(marshal(infos))
        for n in a08.PLANNING_FILES:
            dest=self.project/n;dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes((ROOT/n).read_bytes())
    def chain(self):
        a=a04.analyze(a04.scan_source(self.game,'DECADES',base=True),{})
        b=a06.audit(self.game,a);c=a07.audit(self.game,a,b);d=a08.audit(self.game,self.project,a,b,c)
        return a,b,c,d
    def run_it(self):return a09.audit(self.game,self.project,*self.chain())
    def test_01_reconcile_mapid3_and_context(self):
        report=self.run_it();i=report['intro_event_evidence']
        self.assertTrue(i['mapid3_origin_matches_a07'])
        self.assertEqual(i['static_transfer_to_mapid3_count'],2)
        self.assertEqual([e['event_name'] for e in i['events']],['Intro','Quick start intro'])
        self.assertFalse(report['runtime_intro_proven_safe'])
        self.assertFalse(report['can_reserve_mapids'])
    def test_02_trigger_and_branch_context(self):
        page=self.run_it()['intro_event_evidence']['events'][0]['pages'][0]
        self.assertEqual(page['trigger_label'],'AUTORUN')
        self.assertTrue(page['condition_flags']['switch1_valid'])
        self.assertEqual(page['condition_ids']['switch1_id'],42)
        self.assertEqual(page['branch_like_command_count'],2)
        self.assertTrue(any(x['kind']=='TRANSFER_PLAYER' for x in page['transfer_evidence'][0]['surrounding_codes']))
    def test_03_script_call_definition_vs_symbolic(self):
        scripts=b'def pbWarp(x,y,z)\nend\npbWarp(variable_map_id, 4, 5)\npbTeleport(518,1,1)\n'
        (self.data/'Scripts.rxdata').write_bytes(marshal([[1,b'Test',zlib.compress(scripts)]]))
        triage=self.run_it()['script_transfer_triage']
        kinds=triage['classification_counts']
        self.assertEqual(kinds['DEFINITION'],1)
        self.assertEqual(kinds['SYMBOLIC_OR_COMPUTED'],1)
        self.assertEqual(kinds['LITERAL_UNOVA_CANDIDATE'],1)
        self.assertFalse(triage['all_dynamic_destinations_covered'])
    def test_04_installer_overlap(self):
        (self.data/'blue-kanto-install.json').write_text('{"maps":{"22":518}}')
        report=self.run_it()
        self.assertEqual(report['manifest_provenance']['observed_candidate_collisions'],[518])
        self.assertIn('INSTALLER_MANIFEST_OVERLAP_CANDIDATES',report['followup_review_flags'])
    def test_05_missing_manifest_not_safe(self):
        report=self.run_it()
        self.assertTrue(report['manifest_provenance']['missing_or_unrecognized_coverage'])
        self.assertFalse(report['future_installer_claims_certified'])
    def test_06_map_changed_after_a04(self):
        previous=self.chain();(self.data/'Map001.rxdata').write_bytes(b'bad')
        with self.assertRaises(ValueError):a09.audit(self.game,self.project,*previous)
    def test_07_a08_missing_block(self):
        previous=list(self.chain());previous[3]['mapinfos_sha256']='deadbeef'
        with self.assertRaises(ValueError):a09.audit(self.game,self.project,*previous)
    def test_08_empty_intro_event_yields_pending(self):
        (self.data/'Map001.rxdata').write_bytes(mapp(False))
        report=self.run_it();self.assertIn('EVENT_2_NOT_FOUND',report['followup_review_flags'])
        self.assertFalse(report['can_install'])
    def test_09_report_immutable_and_game_untouched(self):
        before={x.name:x.read_bytes() for x in self.data.iterdir()}
        report=self.run_it();path=a09.save(self.project,report)
        self.assertEqual(path,a09.save(self.project,report))
        self.assertEqual(before,{x.name:x.read_bytes() for x in self.data.iterdir()})
        self.assertEqual(report['bar_a_completed'],0)
    def test_10_symlink_reports_blocked(self):
        outside=self.root/'outside';outside.mkdir()
        try:(self.project/'.blue-work').symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest('symlink unavailable')
        with self.assertRaises(ValueError):a09.save(self.project,self.run_it())
        self.assertEqual(list(outside.iterdir()),[])
    def test_11_no_blind_game_repair(self):
        report=self.run_it()
        self.assertFalse(report['mapid3_repaired'])
        self.assertFalse(report['game_exe_tested'])
        self.assertFalse(report['game_or_saves_modified'])
        self.assertIn('MAPID_3_UNRESOLVED_INTRO_DESTINATION',report['followup_review_flags'])
    def test_12_source_status_never_certifies(self):
        report=self.run_it()
        self.assertEqual(report['status'],'REVIEW_REQUIRED_NO_RESERVATION')
        self.assertFalse(report['all_mapid_references_certified'])
        self.assertFalse(report['mapids_allocated'])


if __name__=='__main__':unittest.main()
