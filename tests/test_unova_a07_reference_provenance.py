"""A07 read-only provenance of MapID 3 and 518..599 with synthetic scripts."""
from __future__ import annotations
import shutil
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
sys.path.insert(0,str(ROOT/"tests"))
import test_unova_a06_references as fixtures
from server.ruby_marshal import RubyObject
import audit_unova_a04_mapids as a04
import audit_unova_a06_references as a06
import audit_unova_a07_reference_provenance as a07

class A07Tests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="unova-a07-")
        self.addCleanup(t.cleanup)
        self.root=Path(t.name);self.game=self.root/"game";self.data=self.game/"Data"
        self.data.mkdir(parents=True)
        self.project=self.root/"project";self.project.mkdir()
        cmd=fixtures.command
        self.data.joinpath("Map001.rxdata").write_bytes(fixtures.mapblob([
            cmd(201,[0,3,1,2,2]),cmd(201,[0,2,0,0,2]),
            cmd(355,[b"$game_player.reserve_transfer(518, 4, 4)"]),
            cmd(655,[b"pbWarp(3, 2, 2)"])]))
        self.data.joinpath("Map002.rxdata").write_bytes(fixtures.mapblob([
            cmd(201,[0,1,0,0,2])]))
        self.data.joinpath("MapInfos.rxdata").write_bytes(fixtures.mapinfos([1,2]))
    def before(self):
        manifest=a04.analyze(a04.scan_source(self.game,"DECADES",base=True),{})
        summary=a06.audit(self.game,manifest)
        self.assertEqual(summary["map_files_parsed"],2)
        return manifest,summary
    def test_01_origin_of_missing_mapid_three(self):
        a,b=self.before()
        r=a07.audit(self.game,a,b)
        self.assertEqual(r["mapid_3_static_reference_count"],1)
        self.assertEqual(r["static_interest_references"][0]["source_map_id"],1)
        self.assertEqual(r["static_interest_references"][0]["event_id"],1)
        self.assertEqual(r["static_interest_references"][0]["page_index"],1)
        self.assertEqual(r["static_interest_references"][0]["destination_map_id"],3)
        self.assertFalse(r["can_reserve_mapids"])
    def test_02_script_api_hints_only(self):
        a,b=self.before();r=a07.audit(self.game,a,b)
        ids={x["target_literal"] for x in r["script_literal_hints"]}
        self.assertEqual(ids,{3,518})
        self.assertFalse(r["script_scan_exhaustive"])
        self.assertFalse(r["all_mapid_references_certified"])
    def test_03_static_candidate_reference_not_counted_as_free(self):
        a,b=self.before();r=a07.audit(self.game,a,b)
        self.assertEqual(r["unova_518_599_static_reference_count"],0)
        self.assertFalse(r["can_reserve_mapids"])
    def test_04_common_events_scanned_when_present(self):
        ev=RubyObject("RPG::CommonEvent",{"@list":[fixtures.command(201,[0,518,1,1,0])]})
        self.data.joinpath("CommonEvents.rxdata").write_bytes(
            fixtures._tiny_ruby_marshal([None,ev]))
        a,b=self.before();r=a07.audit(self.game,a,b)
        self.assertEqual(r["common_events"]["status"],"READ_ONLY_INSPECTED")
        self.assertEqual(r["unova_518_599_static_reference_count"],1)
        self.assertTrue(any(x["source_type"]=="COMMON_EVENT" for x in r["static_interest_references"]))
    def test_05_scripts_zlib_scan_literal(self):
        payload=zlib.compress(b"$game_player.reserve_transfer(519, 3, 3)")
        self.data.joinpath("Scripts.rxdata").write_bytes(
            fixtures._tiny_ruby_marshal([[1,b"TestScript",payload]]))
        a,b=self.before();r=a07.audit(self.game,a,b)
        self.assertEqual(r["scripts_rxdata"]["status"],"TEXT_SCANNED_INERT")
        self.assertIn(519,[x["target_literal"] for x in r["script_literal_hints"]])
    def test_06_corrupt_scripts_are_reported_not_approved(self):
        self.data.joinpath("Scripts.rxdata").write_bytes(b"invalid script bundle")
        a,b=self.before();r=a07.audit(self.game,a,b)
        self.assertEqual(r["scripts_rxdata"]["status"],"PARSE_FAILED")
        self.assertGreater(r["review_errors_count"],0)
        self.assertFalse(r["all_mapid_references_certified"])
    def test_07_source_map_changes_after_a04_become_findings(self):
        a,b=self.before()
        self.data.joinpath("Map001.rxdata").write_bytes(b"tampered")
        r=a07.audit(self.game,a,b)
        self.assertLess(r["map_files_parsed"],2)
        self.assertGreater(r["review_errors_count"],0)
        self.assertFalse(r["can_install"])
    def test_08_invalid_a06_rejected(self):
        a,b=self.before();b["mapinfos_sha256"]="f"*64
        with self.assertRaises(ValueError):
            a07.audit(self.game,a,b)
    def test_09_immutable_private_reports(self):
        a,b=self.before();r=a07.audit(self.game,a,b)
        first=a07.save(self.project,r);old=first.read_bytes()
        self.assertEqual(first,a07.save(self.project,r))
        self.assertEqual(first.read_bytes(),old)
        self.assertFalse((self.project/"game").exists())
    def test_10_symlink_report_path_rejected(self):
        a,b=self.before();r=a07.audit(self.game,a,b)
        outside=self.root/"outside";outside.mkdir()
        try:
            (self.project/".blue-work").symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest("symlinks not supported")
        with self.assertRaises(ValueError):
            a07.save(self.project,r)
        self.assertFalse(list(outside.iterdir()))
    def test_11_game_files_unmodified(self):
        a,b=self.before()
        old={x.name:x.read_bytes() for x in self.data.iterdir()}
        a07.audit(self.game,a,b)
        self.assertEqual(old,{x.name:x.read_bytes() for x in self.data.iterdir()})
    def test_12_full_coverage_remains_not_approved(self):
        a,b=self.before();r=a07.audit(self.game,a,b)
        self.assertEqual(r["map_files_parsed"],2)
        self.assertFalse(r["installer_manifests_examined"])
        self.assertEqual(r["bar_a_completed"],0)
        self.assertEqual(r["bar_a_total"],8)

if __name__=="__main__":
    unittest.main()
