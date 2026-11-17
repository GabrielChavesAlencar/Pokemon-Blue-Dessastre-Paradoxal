"""A10: read-only dynamic transfer diagnostics, status matrix and fail-closed gates."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
sys.path.insert(0,str(ROOT/"tests"))
from server.ruby_marshal import RubyObject
import test_unova_a09_intro_and_claims as fixture
import audit_unova_a04_mapids as a04
import audit_unova_a06_references as a06
import audit_unova_a07_reference_provenance as a07
import audit_unova_a08_readiness as a08
import audit_unova_a09_intro_and_claims as a09
import audit_unova_a10_dynamic_matrix as a10

class A10Tests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="unova-a10-")
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.game=self.root/"game";self.data=self.game/"Data"
        self.data.mkdir(parents=True)
        self.project=self.root/"project";self.project.mkdir()
        (self.data/"Map001.rxdata").write_bytes(fixture.mapp())
        (self.data/"Map002.rxdata").write_bytes(fixture.second_map())
        infos={i:RubyObject("RPG::MapInfo",{"@name":("Test "+str(i)).encode()}) for i in (1,2)}
        (self.data/"MapInfos.rxdata").write_bytes(fixture.marshal(infos))
        for rel in a08.PLANNING_FILES:
            target=self.project/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((ROOT/rel).read_bytes())
    def chain(self):
        a=a04.analyze(a04.scan_source(self.game,"DECADES",base=True),{})
        b=a06.audit(self.game,a)
        c=a07.audit(self.game,a,b)
        d=a08.audit(self.game,self.project,a,b,c)
        e=a09.audit(self.game,self.project,a,b,c,d)
        return a,b,c,d,e
    def run_a10(self):return a10.audit(self.game,self.project,*self.chain())
    def test_01_generates_exactly_82_ids_not_reserved(self):
        r=self.run_a10()
        self.assertEqual(r["mapids_reviewed"],82)
        self.assertEqual([x["map_id"] for x in r["mapid_matrix"]],list(range(518,600)))
        self.assertTrue(all(not x["approved_for_reservation"] for x in r["mapid_matrix"]))
        self.assertEqual(r["matrix_status_counts"]["OBSERVED_VACANT_NOT_RESERVED"],82)
        self.assertFalse(r["can_install"])
    def test_02_event_transfer_matches_a09_and_checks_page_gates(self):
        r=self.run_a10()
        intro=r["intro_transfer_analysis"]
        self.assertEqual(len(intro["mapid3_transfer_positions"]),2)
        self.assertTrue(intro["matches_a09_count"])
        page=intro["events"][0]["pages"][0]
        self.assertTrue(page["condition_flags"]["switch1_valid"])
        self.assertEqual(page["active_condition_inputs"]["switch1_id"],42)
        self.assertEqual(page["page_is_active_at_runtime"],"UNKNOWN")
        self.assertFalse(r["mapid3_destination_repaired"])
    def test_03_manifest_claim_numeric_string(self):
        (self.data/"blue-kanto-install.json").write_text('{"maps":{"5":"518"}}')
        r=self.run_a10()
        self.assertEqual(r["mapid_matrix"][0]["status"],"INSTALLER_MANIFEST_CLAIM_REVIEW")
        self.assertIn(518,r["installer_manifest_analysis"]["candidate_ids"])
    def test_04_manifest_nested_target(self):
        (self.data/"blue-hoenn-install.json").write_text(
            '{"nested":{"entries":[{"new_map_id":599}]}}')
        r=self.run_a10()
        self.assertEqual(r["mapid_matrix"][-1]["status"],"INSTALLER_MANIFEST_CLAIM_REVIEW")
    def test_05_json_unrelated_coordinates_not_destination(self):
        (self.data/"blue-johto-main-preview.json").write_text('{"x":518,"y":519,"maps":{"1":700}}')
        r=self.run_a10()
        self.assertEqual(r["installer_manifest_analysis"]["candidate_ids"],[])
    def test_06_occupied_id_highest_priority(self):
        (self.data/"Map518.rxdata").write_bytes(fixture.second_map())
        infos={i:RubyObject("RPG::MapInfo",{"@name":("Test "+str(i)).encode()})
               for i in (1,2,518)}
        (self.data/"MapInfos.rxdata").write_bytes(fixture.marshal(infos))
        r=self.run_a10()
        self.assertEqual(r["mapid_matrix"][0]["status"],"OCCUPIED_IN_CURRENT_SNAPSHOT")
        self.assertFalse(r["observed_snapshot_no_candidate_occupancy"])
    def test_07_dynamic_calls_preserve_provenance_without_running(self):
        raw=b"pbWarp($game_variables[33],2,2)\npbTeleport(518,2,2)\n"
        (self.data/"Scripts.rxdata").write_bytes(
            fixture.marshal([[1,b"Tester",zlib.compress(raw)]]))
        r=self.run_a10()
        dynamic=r["dynamic_script_references"]
        self.assertGreaterEqual(dynamic["reported_computed_count"],1)
        self.assertTrue(dynamic["unresolved_provenance"])
        self.assertFalse(dynamic["dynamic_targets_verified"])
        self.assertFalse(r["game_exe_tested"])
    def test_08_map001_changed_after_chain_denied(self):
        chain=self.chain()
        (self.data/"Map001.rxdata").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            a10.audit(self.game,self.project,*chain)
    def test_09_a09_missing_or_corrupt_denied(self):
        chain=list(self.chain())
        chain[4]["mapinfos_sha256"]="wrong"
        with self.assertRaises(ValueError):
            a10.audit(self.game,self.project,*chain)
    def test_10_report_immutable_does_not_touch_native(self):
        old={p.name:p.read_bytes() for p in self.data.iterdir()}
        r=self.run_a10()
        p=a10.save(self.project,r)
        self.assertEqual(p,a10.save(self.project,r))
        self.assertEqual(old,{p.name:p.read_bytes() for p in self.data.iterdir()})
        self.assertEqual(r["bar_a_completed"],0)
        self.assertEqual(r["bar_a_total"],8)
    def test_11_symlink_output_denied(self):
        outside=self.root/"outside";outside.mkdir()
        try:(self.project/".blue-work").symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest("Symlinks unavailable")
        with self.assertRaises(ValueError):a10.save(self.project,self.run_a10())
        self.assertFalse(list(outside.iterdir()))
    def test_12_invalid_manifest_not_silent_success(self):
        (self.data/"blue-hoenn-install.json").write_text("{broken")
        r=self.run_a10()
        statuses={x["name"]:x["status"] for x in r["installer_manifest_analysis"]["files"]}
        self.assertEqual(statuses["blue-hoenn-install.json"],"READ_ERROR")
        self.assertFalse(r["future_installer_ownership_verified"])
    def test_13_missing_event_2_not_claimed_safe(self):
        (self.data/"Map001.rxdata").write_bytes(fixture.mapp(False))
        r=self.run_a10()
        self.assertEqual(r["intro_transfer_analysis"]["events"][1]["status"],"MISSING")
        self.assertFalse(r["can_reserve_mapids"])
    def test_14_has_negative_safety_assertions(self):
        r=self.run_a10()
        self.assertFalse(r["mapids_allocated"])
        self.assertFalse(r["game_or_saves_modified"])
        self.assertFalse(r["source_maps_from_unova_verified"])
        self.assertFalse(r["future_installer_ownership_verified"])
        self.assertFalse(r["game_exe_intro_verified"])

if __name__=="__main__":unittest.main()
