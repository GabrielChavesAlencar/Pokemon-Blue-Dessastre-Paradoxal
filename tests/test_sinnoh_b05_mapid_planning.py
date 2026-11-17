"""B05 tests: real B01/B04 aggregate, planning holds, future reservations blocked."""
from __future__ import annotations
import copy
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_b05_mapid_planning as b05

class B05MapidPlanningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=b05.load(b05.CATALOG)
        cls.b01=b05.load(b05.B01)
        cls.b03=b05.load(b05.B03)
        cls.unova=b05.load(b05.UNOVA)

    def check(self,catalog=None,b01=None,b03=None,unova=None):
        return b05.audit(
          copy.deepcopy(self.catalog if catalog is None else catalog),
          copy.deepcopy(self.b01 if b01 is None else b01),
          copy.deepcopy(self.b03 if b03 is None else b03),
          copy.deepcopy(self.unova if unova is None else unova)
        )
    def reject(self,mutator):
        d=copy.deepcopy(self.catalog)
        mutator(d)
        with self.assertRaisesRegex(ValueError,"SINNOH_B05_BLOCKED"):
            self.check(catalog=d)

    def test_01_offline_report_is_not_native_approval(self):
        x=self.check()
        self.assertEqual(x["occupied_count"],648)
        self.assertEqual(x["sinnoh_admin_hold_count"],76)
        self.assertEqual(x["unova_physical_candidates_count"],174)
        self.assertFalse(x["r07_complete"])
        self.assertFalse(x["can_install"])
        self.assertFalse(x["unova_allocated"])

    def test_02_cli_runs(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_b05_mapid_planning.py")],
            cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("SINNOH_B05_UNOVA_MAPID_PLANNING_OK_NOT_NATIVE_APPROVED",p.stdout)

    def test_03_occupied_ranges_have_exact_648_ids(self):
        used=b05.expand(self.catalog["occupied"]["ranges"])
        self.assertEqual(len(used),648)
        self.assertIn(1,used)
        self.assertIn(22,used)
        self.assertIn(48,used)
        self.assertIn(76,used)
        self.assertIn(898,used)
        self.assertNotIn(442,used)

    def test_04_installed_regions_are_nonoverlapping(self):
        regs=self.catalog["occupied"]["identified_from_regional_manifests"]
        sets={k:b05.expand(v["ranges"]) for k,v in regs.items()}
        self.assertTrue(sets["KANTO"].isdisjoint(sets["JOHTO"]))
        self.assertTrue(sets["JOHTO"].isdisjoint(sets["HOENN"]))
        self.assertEqual(sum(map(len,sets.values())),441)

    def test_05_base_207_maps_stay_protected(self):
        self.assertEqual(self.catalog["occupied"]["base_or_other_manifest_unattributed"]["count"],207)
        self.reject(lambda x:x["occupied"]["base_or_other_manifest_unattributed"].update({"count":206}))

    def test_06_sinnoh_76_planning_hold_is_not_native_allocation(self):
        d=self.catalog["sinnoh"]
        self.assertEqual(d["administrative_planning_hold"],{"start":442,"end":517,"count":76})
        self.assertFalse(d["native_reserved_or_allocated"])
        self.reject(lambda x:x["sinnoh"].update({"native_reserved_or_allocated":True}))

    def test_07_sinnoh_hold_cannot_overlap_kanto(self):
        self.reject(lambda x:x["sinnoh"]["administrative_planning_hold"].update({"start":400,"end":475}))

    def test_08_sinnoh_source_map_mapping_still_empty(self):
        self.reject(lambda x:x["sinnoh"].update({"source_to_destination_mapping_done":True}))

    def test_09_unova_only_gets_174_physical_candidates(self):
        candidates=b05.expand(self.catalog["unova"]["candidate_ranges"])
        self.assertEqual(len(candidates),174)
        self.assertEqual(len(candidates & set(range(442,518))),0)
        self.assertEqual(len(candidates & set(range(600,1000))),0)

    def test_10_unova_large_block_518_to_599_exact(self):
        d=self.catalog["unova"]["preferred_contiguous_candidate"]
        self.assertEqual(d,{"start":518,"end":599,"count":82})
        self.assertTrue(set(range(518,600))<=b05.expand(self.catalog["unova"]["candidate_ranges"]))

    def test_11_unova_cannot_use_sinnoh_held_id(self):
        self.reject(lambda x:x["unova"]["candidate_ranges"].append({"start":442,"end":442,"count":1}))

    def test_12_unova_cannot_claim_hoenn_899_to_999(self):
        self.reject(lambda x:x["unova"]["candidate_ranges"].append({"start":899,"end":899,"count":1}))

    def test_13_future_reservations_not_proved(self):
        self.reject(lambda x:x["sinnoh"].update({"future_region_reservations_verified":True}))

    def test_14_unova_cannot_claim_installed_or_reserved(self):
        for field in ("already_allocated_shared_map_ids","reservation_confirmed","can_install"):
            with self.subTest(field=field):
                self.reject(lambda x,f=field:x["unova"].update({f:True}))

    def test_15_old_b04_missing_ids_must_be_visible(self):
        omit=self.catalog["evidence"]["b04_unreported_b01_map_ids"]
        self.assertEqual(len(omit),31)
        self.assertEqual(omit[:7],[1,22,32,33,42,43,48])
        self.assertEqual(omit[-1],99)
        self.reject(lambda x:x["evidence"].update({"b04_reported_physical_count":648}))

    def test_16_fake_b04_manifest_hash_rejected(self):
        self.reject(lambda x:x["occupied"]["identified_from_regional_manifests"]
                    ["JOHTO"].update({"manifest_sha256":"f"*64}))

    def test_17_mapinfos_hash_drift_rejected(self):
        self.reject(lambda x:x["evidence"].update({"mapinfos_sha256":"0"*64}))

    def test_18_r07_not_complete_even_with_hold(self):
        self.reject(lambda x:x["constraints"].update({"r07_complete":True}))

    def test_19_hoenn_entire_700_to_999_remains_protected(self):
        self.assertEqual(self.catalog["excluded"]["hoenn_protected"],
                         {"start":700,"end":999,"count":300,"currently_occupied":199})
        self.reject(lambda x:x["excluded"]["hoenn_protected"].update({"end":898}))

    def test_20_do_not_pretend_unova_game_maps_are_imported(self):
        u=copy.deepcopy(self.unova)
        u["areas"][0]["destination_map_id"]=518
        with self.assertRaisesRegex(ValueError,"SINNOH_B05_BLOCKED"):
            self.check(unova=u)

    def test_21_reject_intervals_with_overlap_or_wrong_count(self):
        self.reject(lambda x:x["occupied"]["ranges"][1].update({"end":23,"count":2}))
        self.reject(lambda x:x["occupied"]["ranges"][0].update({"count":2}))

    def test_22_reject_false_gameplay_or_phase_gates(self):
        for field in ("b_approved","c_approved","d_approved"):
            with self.subTest(field=field):
                self.reject(lambda x,f=field:x["constraints"].update({f:1}))
        self.reject(lambda x:x["constraints"].update({"no_native_gameplay_test":False}))

if __name__=="__main__":unittest.main()
