"""A08 regression: synthetic maps, inactive-only diagnostic, no reservations."""
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
from server.ruby_marshal import RubyObject
import test_unova_a06_references as fixture
import audit_unova_a04_mapids as a04
import audit_unova_a06_references as a06
import audit_unova_a07_reference_provenance as a07
import audit_unova_a08_readiness as a08

PLANNING=(
 "data/regions/unova-a05-mapid-candidates.json",
 "data/regions/sinnoh-b05-mapid-planning.json",
 "data/regions/sinnoh-b03-installer-evidence.json",
)

def map1(with_two=True):
    condition=RubyObject("RPG::Event::Page::Condition",{
        "@switch1_valid":True,"@switch1_id":12,
        "@self_switch_valid":False})
    page1=RubyObject("RPG::Event::Page",{
        "@condition":condition,"@trigger":0,
        "@list":[fixture.command(201,[0,3,7,4,2]),
                 fixture.command(355,[b"pbWarp(current_map_id, 4, 5)"])]})
    page2=RubyObject("RPG::Event::Page",{
        "@trigger":1,"@list":[fixture.command(201,[0,3,8,4,2])]})
    events={1:RubyObject("RPG::Event",{
        "@name":b"Start Warp","@x":2,"@y":5,"@pages":[page1]})}
    if with_two:
        events[2]=RubyObject("RPG::Event",{
            "@name":b"Second Warp","@x":9,"@y":6,"@pages":[page2]})
    return fixture._tiny_ruby_marshal(RubyObject("RPG::Map",{
        "@events":events,"@width":20,"@height":15,"@tileset_id":1}))

class A08Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="unova-a08-")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.game=self.root/"game";self.data=self.game/"Data"
        self.data.mkdir(parents=True)
        self.project=self.root/"repo";self.project.mkdir()
        self.data.joinpath("Map001.rxdata").write_bytes(map1())
        self.data.joinpath("Map002.rxdata").write_bytes(fixture.mapblob([]))
        self.data.joinpath("MapInfos.rxdata").write_bytes(fixture.mapinfos([1,2]))
        for relative in PLANNING:
            target=self.project/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,target)
    def reports(self):
        a=a04.analyze(a04.scan_source(self.game,"DECADES",base=True),{})
        b=a06.audit(self.game,a)
        c=a07.audit(self.game,a,b)
        return a,b,c
    def run_a08(self):
        return a08.audit(self.game,self.project,*self.reports())
    def test_01_mapid3_two_sources_provenance(self):
        r=self.run_a08()
        self.assertTrue(r["mapid3_referenced_but_not_found"])
        self.assertTrue(r["mapid3_transfers_reconciled_with_a07"])
        self.assertEqual([v["event_id"] for v in r["map001_event_context"]],[1,2])
        self.assertFalse(r["can_reserve_mapids"])
    def test_02_page_switch_conditions_are_metadata_not_activated(self):
        r=self.run_a08()
        page=r["map001_event_context"][0]["pages"][0]
        self.assertTrue(page["conditions_active_flags"]["switch1_valid"])
        self.assertEqual(page["condition_inputs"]["switch1_id"],12)
        self.assertFalse(page["activation_verified_at_runtime"])
    def test_03_unknown_installer_manifests_are_not_ok(self):
        r=self.run_a08()
        self.assertTrue(r["local_region_manifests"]["manifest_coverage_incomplete"])
        self.assertFalse(r["blue_story_future_claims_certified"])
        self.assertFalse(r["can_install"])
    def test_04_explicit_local_manifest_collision(self):
        (self.data/"blue-kanto-install.json").write_text('{"maps":{"123":518}}')
        r=self.run_a08()
        self.assertEqual(r["local_region_manifests"]["observed_candidate_overlaps"],[518])
        self.assertEqual(r["status"],"BLOCKED_CANDIDATE_CONFLICT_REVIEW")
    def test_05_unrelated_numeric_values_do_not_become_claims(self):
        (self.data/"blue-hoenn-install.json").write_text(
            '{"x":518,"y":519,"maps":{"22":720}}')
        r=self.run_a08()
        self.assertEqual(r["local_region_manifests"]["observed_candidate_overlaps"],[])
        self.assertFalse(r["can_reserve_mapids"])
    def test_06_occupied_candidate_never_approved(self):
        self.data.joinpath("Map518.rxdata").write_bytes(fixture.mapblob([]))
        self.data.joinpath("MapInfos.rxdata").write_bytes(fixture.mapinfos([1,2,518]))
        r=self.run_a08()
        self.assertIn(518,r["candidate_518_599_occupied_ids"])
        self.assertFalse(r["candidate_518_599_observed_vacant"])
        self.assertFalse(r["can_reserve_mapids"])
    def test_07_changed_map001_since_a04_denied(self):
        a,b,c=self.reports()
        self.data.joinpath("Map001.rxdata").write_bytes(b"modified")
        with self.assertRaises(ValueError):
            a08.audit(self.game,self.project,a,b,c)
    def test_08_corrupt_a07_coherence_denied(self):
        a,b,c=self.reports()
        c["mapinfos_sha256"]="f"*64
        with self.assertRaises(ValueError):
            a08.audit(self.game,self.project,a,b,c)
    def test_09_script_indicators_not_certification(self):
        self.data.joinpath("Scripts.rxdata").write_bytes(
            fixture._tiny_ruby_marshal([[1,b"Test",
                zlib.compress(b"pbTransferPlayer(map_id, x, y)")]]))
        r=self.run_a08()
        self.assertGreater(r["additional_script_indicators"]["transfer_api_name_occurrences"],0)
        self.assertFalse(r["additional_script_indicators"]["computed_mapids_resolved"])
    def test_10_missing_event_is_pending_not_silent(self):
        self.data.joinpath("Map001.rxdata").write_bytes(map1(False))
        r=self.run_a08()
        self.assertEqual(r["map001_target_events_missing"],[2])
        self.assertFalse(r["can_reserve_mapids"])
    def test_11_save_immutable_and_read_only(self):
        before={p.name:p.read_bytes() for p in self.data.iterdir()}
        r=self.run_a08()
        first=a08.save(self.project,r)
        self.assertEqual(first,a08.save(self.project,r))
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.data.iterdir()})
        self.assertEqual(r["bar_a_completed"],0)
    def test_12_symlink_cache_rejected(self):
        outside=self.root/"outside";outside.mkdir()
        try:
            (self.project/".blue-work").symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest("Symlinks unavailable")
        with self.assertRaises(ValueError):
            a08.save(self.project,self.run_a08())
        self.assertEqual(list(outside.iterdir()),[])
    def test_13_planning_missing_is_not_approved(self):
        (self.project/PLANNING[0]).unlink()
        r=self.run_a08()
        self.assertGreater(r["review_problems_count"],0)
        self.assertFalse(r["can_install"])
    def test_14_does_not_make_game_exe_playable_claim(self):
        r=self.run_a08()
        self.assertFalse(r["game_exe_tested"])
        self.assertFalse(r["android_tested"])
        self.assertFalse(r["region_source_rights_verified"])
        self.assertEqual(r["bar_a_total"],8)

if __name__=="__main__":
    unittest.main()
