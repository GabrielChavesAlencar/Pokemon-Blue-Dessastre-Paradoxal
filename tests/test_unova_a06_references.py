"""A06: inert static transfer inventory, no game writes, no false reservations."""
from __future__ import annotations

import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from stage import serialize
from server.ruby_marshal import RubyObject, integer
import audit_unova_a04_mapids as a04
import audit_unova_a06_references as a06

def command(code,parameters):
    return RubyObject("RPG::EventCommand",{"@code":code,"@parameters":parameters})

def _tiny_ruby_marshal(v):
    """Test-only minimal Ruby Marshal serializer for nested RPG::Map events."""
    def sym(s):
        raw=s.encode("utf-8")
        return b":" + integer(len(raw)) + raw
    def raw(x):
        if x is None:
            return b"0"
        if type(x) is int:
            return b"i" + integer(x)
        if isinstance(x,bytes):
            return b'"' + integer(len(x)) + x
        if isinstance(x,list):
            return b"[" + integer(len(x)) + b"".join(raw(y) for y in x)
        if isinstance(x,dict):
            return (b"{" + integer(len(x))
                    + b"".join(raw(k)+raw(y) for k,y in x.items()))
        if isinstance(x,RubyObject):
            return (b"o" + sym(x.name) + integer(len(x.attrs))
                    + b"".join(sym(key)+raw(val) for key,val in x.attrs.items()))
        raise TypeError(type(x).__name__)
    return b"\x04\x08" + raw(v)


def mapblob(commands):
    page=RubyObject("RPG::Event::Page",{"@list":commands})
    ev=RubyObject("RPG::Event",{"@pages":[page]})
    return _tiny_ruby_marshal(RubyObject("RPG::Map",{"@events":{1:ev},"@width":20,"@height":15,"@tileset_id":1}))

def mapinfos(items):
    return serialize({i:RubyObject("RPG::MapInfo",{"@name":("Map "+str(i)).encode()})
                      for i in items})

class A06ReferencesTests(unittest.TestCase):
    def setUp(self):
        context=tempfile.TemporaryDirectory(prefix="unova-a06-")
        self.addCleanup(context.cleanup)
        self.root=Path(context.name)
        self.project=self.root/"project"
        self.project.mkdir()
        self.game=self.root/"game"
        self.data=self.game/"Data"
        self.data.mkdir(parents=True)
        self.write_map(1,[command(201,[0,2,10,10,2]),
                          command(201,[0,518,4,4,2]),
                          command(355,[b"some unknown Ruby"])])
        self.write_map(2,[command(201,[0,1,3,3,2]),
                          command(201,[1,5,4,4,2])])
        self.update_infos()
    def write_map(self,mid,cmds):
        (self.data/("Map%03d.rxdata"%mid)).write_bytes(mapblob(cmds))
    def update_infos(self):
        ids=[int(p.stem[3:]) for p in self.data.glob("Map*.rxdata")
             if p.name!="MapInfos.rxdata"]
        (self.data/"MapInfos.rxdata").write_bytes(mapinfos(ids))
    def baseline(self):
        return a04.analyze(a04.scan_source(self.game,"DECADES",base=True),{})
    def test_01_reads_literal_destination(self):
        result=a06.audit(self.game,self.baseline())
        self.assertEqual(result["map_files_parsed"],2)
        self.assertEqual(result["static_transfer_command_count"],3)
        self.assertEqual(result["static_destination_mapids"],[1,2,518])
        self.assertEqual(result["candidate_unova_518_599_referenced"],[518])
        self.assertEqual(result["static_unresolved_destination_ids"],[518])
    def test_02_dynamic_and_scripts_not_certified(self):
        result=a06.audit(self.game,self.baseline())
        self.assertEqual(result["dynamic_transfer_commands"],1)
        self.assertEqual(result["event_script_commands_not_executed"],1)
        self.assertFalse(result["all_mapid_references_certified"])
        self.assertFalse(result["script_assets_examined"])
        self.assertFalse(result["can_reserve_mapids"])
    def test_03_no_install_or_rights_claim(self):
        result=a06.audit(self.game,self.baseline())
        for flag in ("mapids_allocated","can_install","can_reserve_mapids",
                     "game_exe_tested","android_tested","game_or_saves_modified"):
            self.assertIs(result[flag],False)
    def test_04_mapinfos_hash_matches_a04(self):
        a04_report=self.baseline()
        result=a06.audit(self.game,a04_report)
        self.assertEqual(result["mapinfos_sha256"],
                         a04_report["sources"]["DECADES"]["mapinfos_sha256"])
    def test_05_modified_map_after_a04_fails_partial_without_hiding(self):
        baseline=self.baseline()
        self.write_map(2,[command(201,[0,4,0,0,0])])
        result=a06.audit(self.game,baseline)
        self.assertEqual(result["status"],"PARTIAL_MAP_PARSE_REVIEW_REQUIRED")
        self.assertEqual(result["map_files_parsed"],1)
        self.assertEqual(len(result["map_read_failures"]),1)
        self.assertEqual(result["map_read_failures"][0]["source_map_id"],2)
        self.assertFalse(result["can_reserve_mapids"])
    def test_06_map_object_type_invalid_is_partial(self):
        baseline=self.baseline()
        (self.data/"Map002.rxdata").write_bytes(serialize([1,2,3]))
        # Align hash as if A04 read it to verify A06 catches object type.
        baseline=a04.analyze(a04.scan_source(self.game,"DECADES",base=True),{})
        result=a06.audit(self.game,baseline)
        self.assertEqual(result["map_files_parsed"],1)
        self.assertEqual(len(result["map_read_failures"]),1)
    def test_07_not_a_real_a04_report_blocked(self):
        with self.assertRaises(ValueError):
            a06.audit(self.game,{"phase":"A06"})
    def test_08_dangling_ids_detected(self):
        self.write_map(3,[command(201,[0,999,1,1,2])])
        self.update_infos()
        result=a06.audit(self.game,self.baseline())
        self.assertIn(999,result["static_unresolved_destination_ids"])
    def test_09_protected_sinnoh_reference_detected(self):
        self.write_map(3,[command(201,[0,442,1,1,2])])
        self.update_infos()
        result=a06.audit(self.game,self.baseline())
        self.assertEqual(result["sinnoh_442_517_referenced"],[442])
    def test_10_invalid_target_is_dynamic_not_homologated(self):
        self.write_map(3,[command(201,[0,0,1,1,2])])
        self.update_infos()
        result=a06.audit(self.game,self.baseline())
        self.assertGreater(result["dynamic_transfer_commands"],1)
    def test_11_empty_events_still_parse_not_certified(self):
        self.write_map(3,[])
        self.update_infos()
        result=a06.audit(self.game,self.baseline())
        self.assertEqual(result["map_files_parsed"],3)
        self.assertFalse(result["all_mapid_references_certified"])
    def test_12_save_private_idempotent(self):
        report=a06.audit(self.game,self.baseline())
        a=a06.save(self.project,report)
        before=a.read_bytes()
        b=a06.save(self.project,report)
        self.assertEqual(a,b)
        self.assertEqual(a.read_bytes(),before)
        self.assertFalse((self.project/"game").exists())
    def test_13_private_symlink_does_not_escape(self):
        outside=self.root/"outside"
        outside.mkdir()
        try:
            (self.project/".blue-work").symlink_to(outside,target_is_directory=True)
        except OSError:
            self.skipTest("symlinks unsupported")
        with self.assertRaises(ValueError):
            a06.save(self.project,a06.audit(self.game,self.baseline()))
        self.assertEqual(list(outside.iterdir()),[])
    def test_14_read_only_mapinfos_and_maps(self):
        a=self.baseline()
        before={p.name:p.read_bytes() for p in self.data.iterdir()}
        a06.audit(self.game,a)
        after={p.name:p.read_bytes() for p in self.data.iterdir()}
        self.assertEqual(before,after)
    def test_15_hash_change_cannot_hide_other_observed_refs(self):
        a=self.baseline()
        (self.data/"Map002.rxdata").write_bytes(b"corrupt")
        report=a06.audit(self.game,a)
        self.assertIn(518,report["candidate_unova_518_599_referenced"])
        self.assertEqual(report["map_files_expected"],2)
        self.assertFalse(report["all_mapid_references_certified"])

if __name__=="__main__":
    unittest.main()
