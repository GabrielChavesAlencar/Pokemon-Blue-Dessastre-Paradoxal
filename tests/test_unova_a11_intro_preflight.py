"""A11 synthetic QA: intro preflight, dynamic argument shapes and safe rollback plan."""
from __future__ import annotations
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
import audit_unova_a11_intro_preflight as a11

class A11Tests(unittest.TestCase):
    def setUp(self):
        td=tempfile.TemporaryDirectory(prefix="unova-a11-")
        self.addCleanup(td.cleanup)
        self.root=Path(td.name);self.game=self.root/"game"
        self.data=self.game/"Data";self.data.mkdir(parents=True)
        self.project=self.root/"repo";self.project.mkdir()
        (self.data/"Map001.rxdata").write_bytes(fixture.mapp())
        (self.data/"Map002.rxdata").write_bytes(fixture.second_map())
        infos={i:RubyObject("RPG::MapInfo",{"@name":("Test "+str(i)).encode()})
               for i in (1,2)}
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
        f=a10.audit(self.game,self.project,a,b,c,d,e)
        return a,b,c,d,e,f
    def run_a11(self):return a11.audit(self.game,self.project,*self.chain())
    def test_01_intro_routes_preserved_but_not_claimed_playable(self):
        r=self.run_a11()
        intro=r["intro_route_review"]
        self.assertEqual(intro["transfer_count"],2)
        self.assertTrue(intro["matches_a10_positions"])
        self.assertFalse(intro["runtime_input_and_switches_verified"])
        self.assertIsNone(intro["safe_replacement_map_id"])
        self.assertFalse(r["mapid3_repaired"])
    def test_02_active_gate_has_switch_id_only(self):
        r=self.run_a11()
        p=r["intro_route_review"]["sensitive_transfers"][0]
        self.assertEqual(p["enabled_condition_inputs"]["switch1_id"],42)
        self.assertEqual(p["page_is_active_at_runtime"],"UNKNOWN")
        self.assertTrue(p["higher_indexed_page_exists"])
        self.assertFalse(p["automatic_replacement_allowed"])
    def test_03_82_candidate_matrix_is_nonoperative(self):
        r=self.run_a11();m=r["reservation_preflight"]
        self.assertEqual(m["count"],82)
        self.assertEqual(m["status_counts"]["OBSERVED_VACANT_NOT_RESERVED"],82)
        self.assertEqual(m["status_counts"]["OCCUPIED_IN_CURRENT_SNAPSHOT"],0)
        self.assertEqual(m["candidate_matrix"][0]["map_id"],518)
        self.assertEqual(m["candidate_matrix"][-1]["map_id"],599)
        self.assertTrue(all(not x["reserved"] and not x["safe_to_write"] for x in m["candidate_matrix"]))
        self.assertFalse(m["reservation_approved"])
    def test_04_rollback_is_documented_not_implemented(self):
        protocol=self.run_a11()["reservation_preflight"]["rollback_protocol"]
        self.assertEqual(protocol["status"],"DRAFT_ONLY_NOT_EXECUTED")
        self.assertFalse(protocol["installer_or_backup_created"])
        self.assertFalse(protocol["may_touch_user_game"])
        self.assertGreaterEqual(len(protocol["requires_separate_backups"]),5)
    def test_05_dynamic_arguments_classified_without_source_code(self):
        text=b"def pbWarp(a,b,c)\nend\npbWarp($game_variables[33],1,1)\npbTeleport(route_map_id,2,2)\n"
        (self.data/"Scripts.rxdata").write_bytes(
            fixture.marshal([[1,b"Test",zlib.compress(text)]]))
        r=self.run_a11();p=r["computed_reference_review"]
        self.assertEqual(p["computed_shape_observed"],2)
        self.assertTrue(p["counts_match_a09"])
        self.assertIn("INDEXED_VARIABLE",p["shape_histogram"])
        self.assertIn("VARIABLE_OR_SYMBOL",p["shape_histogram"])
        self.assertEqual(len(p["unresolved_calls"]),2)
        self.assertFalse(p["all_dynamic_targets_resolved"])
        self.assertNotIn("argument_text",p["unresolved_calls"][0])
    def test_06_manifest_claim_blocks_write(self):
        (self.data/"blue-kanto-install.json").write_text('{"maps":{"3":518}}')
        r=self.run_a11()
        self.assertEqual(r["reservation_preflight"]["status_counts"]["INSTALLER_MANIFEST_CLAIM_REVIEW"],1)
        self.assertFalse(r["reservation_preflight"]["candidate_matrix"][0]["safe_to_write"])
        self.assertIn("CANDIDATE_MAPID_CONFLICTS_OBSERVED",r["review_flags"])
    def test_07_native_occupied_candidate_preserved(self):
        (self.data/"Map519.rxdata").write_bytes(fixture.second_map())
        infos={i:RubyObject("RPG::MapInfo",{"@name":("Test "+str(i)).encode()})
               for i in (1,2,519)}
        (self.data/"MapInfos.rxdata").write_bytes(fixture.marshal(infos))
        r=self.run_a11()
        m=r["reservation_preflight"]
        self.assertEqual(m["status_counts"]["OCCUPIED_IN_CURRENT_SNAPSHOT"],1)
        self.assertFalse(m["candidate_matrix"][1]["eligible_for_provisional_design"])
    def test_08_forged_a10_reservation_denied(self):
        chain=list(self.chain())
        chain[-1]["mapid_matrix"][0]["approved_for_reservation"]=True
        with self.assertRaises(ValueError):a11.audit(self.game,self.project,*chain)
    def test_09_a10_inconsistent_sha_denied(self):
        chain=list(self.chain())
        chain[-1]["mapinfos_sha256"]="bad"
        with self.assertRaises(ValueError):a11.audit(self.game,self.project,*chain)
    def test_10_map_changed_after_A04_denied(self):
        chain=self.chain()
        (self.data/"Map001.rxdata").write_bytes(b"tampered")
        with self.assertRaises(ValueError):a11.audit(self.game,self.project,*chain)
    def test_11_missing_event_not_certified(self):
        (self.data/"Map001.rxdata").write_bytes(fixture.mapp(False))
        r=self.run_a11()
        self.assertEqual(r["intro_route_review"]["missing_events"],[2])
        self.assertIn("INTRO_A10_COHERENCE_OR_EVENT_MISSING",r["review_flags"])
    def test_12_game_files_and_saves_never_mutated(self):
        before={p.name:p.read_bytes() for p in self.data.iterdir()}
        r=self.run_a11();path=a11.save(self.project,r)
        self.assertEqual(path,a11.save(self.project,r))
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.data.iterdir()})
        self.assertFalse(r["game_or_saves_modified"])
        self.assertEqual(r["bar_a_completed"],0)
    def test_13_reports_symlink_denied(self):
        outside=self.root/"outside";outside.mkdir()
        try:(self.project/".blue-work").symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest("no symlink support")
        with self.assertRaises(ValueError):a11.save(self.project,self.run_a11())
        self.assertEqual(list(outside.iterdir()),[])
    def test_14_unknown_manifest_coverage_never_approved(self):
        r=self.run_a11()
        self.assertIn("blue-unova-install.json",r["regional_manifest_missing_or_partial"])
        self.assertFalse(r["future_installer_claims_verified"])
        self.assertFalse(r["can_reserve_mapids"])
        self.assertFalse(r["can_install"])
        self.assertFalse(r["game_exe_tested"])
        self.assertFalse(r["android_tested"])
    def test_15_corrupt_script_blocks_upstream_provenance(self):
        (self.data/"Scripts.rxdata").write_bytes(b"\x00invalid")
        # A07/A08 must reject the source before A11 can imply a clean scan.
        with self.assertRaises(ValueError):
            self.run_a11()
    def test_16_all_matrix_categories_get_explicit_zero_counts(self):
        r=self.run_a11();counts=r["reservation_preflight"]["status_counts"]
        self.assertEqual(set(counts),set(a11.KNOWN_STATUSES))
        self.assertEqual(sum(counts.values()),82)

if __name__=="__main__":
    unittest.main()
