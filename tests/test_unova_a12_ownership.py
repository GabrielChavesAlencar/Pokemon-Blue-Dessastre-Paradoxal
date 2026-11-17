"""A12 source/manifest ownership audit synthetic negative tests. Never execute installer code."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
sys.path.insert(0,str(ROOT/"tests"))
from server.ruby_marshal import RubyObject
import test_unova_a09_intro_and_claims as fx
import audit_unova_a04_mapids as a04
import audit_unova_a06_references as a06
import audit_unova_a07_reference_provenance as a07
import audit_unova_a08_readiness as a08
import audit_unova_a09_intro_and_claims as a09
import audit_unova_a10_dynamic_matrix as a10
import audit_unova_a11_intro_preflight as a11
import audit_unova_a12_ownership as a12


class A12Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="unova-a12-")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.game=self.root/"game"
        self.data=self.game/"Data"
        self.data.mkdir(parents=True)
        self.project=self.root/"repo"
        self.project.mkdir()
        (self.data/"Map001.rxdata").write_bytes(fx.mapp())
        (self.data/"Map002.rxdata").write_bytes(fx.second_map())
        infos={i:RubyObject("RPG::MapInfo",{"@name":f"Test {i}".encode()})
               for i in (1,2)}
        (self.data/"MapInfos.rxdata").write_bytes(fx.marshal(infos))
        for rel in (*a08.PLANNING_FILES,*a12.SOURCE_FILES):
            target=self.project/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes((ROOT/rel).read_bytes())
    def chain(self):
        x=a04.analyze(a04.scan_source(self.game,"DECADES",base=True),{})
        b=a06.audit(self.game,x)
        c=a07.audit(self.game,x,b)
        d=a08.audit(self.game,self.project,x,b,c)
        e=a09.audit(self.game,self.project,x,b,c,d)
        f=a10.audit(self.game,self.project,x,b,c,d,e)
        g=a11.audit(self.game,self.project,x,b,c,d,e,f)
        return x,b,c,d,e,f,g
    def check(self):return a12.audit(self.game,self.project,*self.chain())

    def test_01_all_installer_code_sources_parsed_without_execution(self):
        r=self.check();src=r["installer_source_review"]
        self.assertEqual(src["sources_expected"],8)
        self.assertEqual(src["sources_parsed"],8)
        self.assertTrue(src["all_source_snapshots_read"])
        self.assertFalse(src["sources_executed"])
        self.assertTrue(all(x["sha256"] for x in src["files"]))
        self.assertTrue(all(x["anchor_found"] for x in src["code_anchors"]))
    def test_02_correct_literal_regions_do_not_overlap_unova(self):
        r=self.check()
        bands=r["installer_source_review"]["observed_literal_bands"]
        self.assertIn([600,681],[x["range"] for x in bands])
        self.assertIn([600,699],[x["range"] for x in bands])
        self.assertIn([700,999],[x["range"] for x in bands])
        self.assertTrue(r["known_literal_bands_do_not_intersect_candidate_interval"])
        self.assertFalse(r["complete_future_code_and_manifest_ownership_proven"])
    def test_03_kanto_dynamic_mapping_unverified(self):
        r=self.check()
        k=next(x for x in r["installer_source_review"]["code_anchors"] if x["region"]=="KANTO")
        self.assertTrue(k["anchor_found"])
        self.assertIsNone(k["known_destination_interval"])
        self.assertFalse(k["destination_ids_complete"])
    def test_04_82_id_in_memory_plan_is_nonoperative(self):
        r=self.check();plan=r["isolated_install_preparation"]
        self.assertEqual(plan["candidate_count"],82)
        self.assertEqual(plan["target_rows"][0]["map_id"],518)
        self.assertEqual(plan["target_rows"][-1]["map_id"],599)
        self.assertEqual(plan["observed_snapshot_conflicts"],0)
        self.assertFalse(plan["isolated_game_copy_created"])
        self.assertFalse(plan["ready_to_install"])
        self.assertTrue(all(not x["write_allowed"] for x in plan["target_rows"]))
    def test_05_negative_scenarios_synthetic_only(self):
        cases=self.check()["isolated_install_preparation"]["synthetic_cases"]
        self.assertEqual(len(cases),3)
        self.assertTrue(all(x["would_block"] and x["synthetic"] for x in cases))
        self.assertTrue(all(not x["native_files_created"] for x in cases))
    def test_06_computed_reference_shapes_never_resolved(self):
        r=self.check();shapes=r["dynamic_reference_prioritization"]
        self.assertEqual(shapes["total_observed"],0)
        self.assertFalse(shapes["all_destinations_known"])
        self.assertFalse(shapes["dynamic_calls_executed"])
    def test_07_local_manifest_claim_518_blocks_preflight(self):
        (self.data/"blue-kanto-install.json").write_text('{"maps":{"1":518}}')
        r=self.check();plan=r["isolated_install_preparation"]
        self.assertEqual(plan["observed_snapshot_conflicts"],1)
        self.assertIn("LOCAL_CANDIDATE_COLLISION_OBSERVED",r["review_flags"])
        self.assertFalse(plan["target_rows"][0]["write_allowed"])
    def test_08_occupied_599_detected(self):
        (self.data/"Map599.rxdata").write_bytes(fx.second_map())
        info={i:RubyObject("RPG::MapInfo",{"@name":f"Test {i}".encode()})
              for i in (1,2,599)}
        (self.data/"MapInfos.rxdata").write_bytes(fx.marshal(info))
        r=self.check()
        self.assertEqual(r["isolated_install_preparation"]["observed_snapshot_conflicts"],1)
        self.assertFalse(r["isolated_install_preparation"]["target_rows"][-1]["write_allowed"])
    def test_09_missing_installer_source_produces_audit_warning(self):
        (self.project/a12.SOURCE_FILES[2]).unlink()
        r=self.check()
        self.assertEqual(r["installer_source_review"]["sources_parsed"],7)
        self.assertIn("INSTALLER_SOURCE_SNAPSHOT_INCOMPLETE",r["review_flags"])
    def test_10_invalid_installer_source_never_executed(self):
        p=self.project/a12.SOURCE_FILES[0]
        p.write_text("def broken(:\n")
        r=self.check()
        self.assertEqual(r["installer_source_review"]["files"][0]["status"],"SOURCE_PARSE_ERROR")
        self.assertFalse(r["can_install"])
    def test_11_mapinfos_sha_changed_denied(self):
        chain=self.chain()
        (self.data/"MapInfos.rxdata").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            a12.audit(self.game,self.project,*chain)
    def test_12_map001_sha_changed_denied(self):
        chain=self.chain()
        (self.data/"Map001.rxdata").write_bytes(b"tampered")
        with self.assertRaises(ValueError):
            a12.audit(self.game,self.project,*chain)
    def test_13_forged_A11_reservation_denied(self):
        chain=list(self.chain())
        chain[-1]["reservation_preflight"]["candidate_matrix"][0]["reserved"]=True
        with self.assertRaises(ValueError):
            a12.audit(self.game,self.project,*chain)
    def test_14_missing_or_broken_A11_phase_denied(self):
        chain=list(self.chain())
        chain[-1]["phase"]="FAKE"
        with self.assertRaises(ValueError):
            a12.audit(self.game,self.project,*chain)
    def test_15_report_immutable_and_no_native_writes(self):
        before={p.name:p.read_bytes() for p in self.data.iterdir()}
        r=self.check()
        path=a12.save(self.project,r)
        self.assertEqual(path,a12.save(self.project,r))
        self.assertEqual(before,{p.name:p.read_bytes() for p in self.data.iterdir()})
        self.assertFalse(r["game_or_saves_modified"])
        self.assertFalse(r["mapids_allocated"])
        self.assertEqual(r["bar_a_completed"],0)
    def test_16_symlink_output_is_rejected(self):
        outside=self.root/"outside";outside.mkdir()
        try:(self.project/".blue-work").symlink_to(outside,target_is_directory=True)
        except OSError:self.skipTest("Symlink not available")
        with self.assertRaises(ValueError):a12.save(self.project,self.check())
        self.assertEqual(list(outside.iterdir()),[])
    def test_17_actual_game_exe_not_launched(self):
        r=self.check()
        self.assertFalse(r["game_exe_tested"])
        self.assertFalse(r["android_tested"])
        self.assertFalse(r["can_reserve_mapids"])
        self.assertFalse(r["can_install"])
        self.assertFalse(r["isolated_install_preparation"]["game_exe_started"])
    def test_18_computed_shapes_different_a09_stay_unknown(self):
        chain=list(self.chain())
        chain[-1]["computed_reference_review"]["counts_match_a09"]=False
        r=a12.audit(self.game,self.project,*chain)
        self.assertIn("COMPUTED_SHAPE_COUNT_MISMATCH_A09",r["review_flags"])
        self.assertFalse(r["full_source_remap_approved"])

if __name__=="__main__":
    unittest.main()
