"""G03: regional MapID matrix must be conservative and fail closed."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_b05_mapid_planning as b05
import audit_sinnoh_g03_regional_mapids as g03


class SinnohG03RegionalMapIDsTests(unittest.TestCase):
    def inputs(self):
        return tuple(copy.deepcopy(b05.load(ROOT / path)) for path in
            (g03.B05, g03.B01, g03.B03, g03.UNOVA, g03.B07))

    def audited(self, changes=None):
        values = list(self.inputs())
        if changes is not None:
            changes(values)
        return g03.build_matrix(*values)

    def test_01_baseline_returns_no_native_approval(self):
        out = self.audited()
        self.assertEqual(out["status"], "STATIC_MATRIX_RECONCILED_FUTURE_RESERVATIONS_UNVERIFIED")
        self.assertFalse(out["r07_complete"])
        self.assertFalse(out["future_reservations_verified"])
        self.assertFalse(out["can_install_live_game"])
        self.assertFalse(out["game_exe_tested"])
        self.assertFalse(out["joiplay_tested"])
        for key in ("phase_b_approved", "phase_c_approved", "phase_d_approved"):
            self.assertEqual(out[key], 0)

    def test_02_all_648_occupied_ids_have_one_attributed_group(self):
        out = self.audited()
        claims = {v["scope"]:v["count"] for v in out["physical_claims"]}
        self.assertEqual(claims, {
            "BASE_OR_UNATTRIBUTED":207, "KANTO":142,"JOHTO":100,"HOENN":199
        })
        self.assertEqual(sum(claims.values()), 648)
        self.assertTrue(out["crosscheck"]["physical_region_claims_disjoint"])

    def test_03_sinnoh_54_geometry_and_22_placeholders_are_not_installed(self):
        out = self.audited()["sinnoh"]
        self.assertEqual(out["hold_range"], [442,517])
        self.assertEqual(out["hold_count"],76)
        self.assertEqual(out["geometry_staged_ids"],[{"start":442,"end":495,"count":54}])
        self.assertEqual(out["empty_placeholder_ids"],[{"start":496,"end":517,"count":22}])
        self.assertFalse(out["installed_in_live_game"])

    def test_04_unova_82_window_only_candidate(self):
        out = self.audited()["unova"]
        self.assertEqual(out["vacant_candidates_1_to_599"],174)
        self.assertEqual(out["preferred_window"],[518,599])
        self.assertEqual(out["preferred_window_size"],82)
        self.assertFalse(out["destination_mapids_approved"])
        self.assertFalse(out["installed_in_live_game"])

    def test_05_no_future_reservations_claimed(self):
        out = self.audited()
        self.assertEqual(set(out["unknown_future_reservations"]),
            {"SINNOH","UNOVA","KANTO","JOHTO","HOENN"})
        self.assertEqual(out["crosscheck"]["native_reserved_future_regions_approved"],[])
        self.assertFalse(out["baseline"]["native_game_reinspected_in_github_ci"])

    def test_06_legacy_sinnoh_800_805_must_stay_protected(self):
        out=self.audited()["other_protected"]
        self.assertTrue(out["legacy_sinnoh_800_to_805_within_native_hoenn_attribution"])
        self.assertFalse(out["four_digit_mapids_homologated"])
        self.assertEqual(out["hoenn_protected_not_observed_899_to_999"],101)

    def test_07_tampered_occupied_or_claim_fails(self):
        for change in (
            lambda x: x[0]["occupied"]["ranges"].pop(),
            lambda x: x[0]["occupied"]["identified_from_regional_manifests"]["KANTO"].update(count=143),
            lambda x: x[0]["sinnoh"]["administrative_planning_hold"].update(start=440),
        ):
            with self.subTest(change=repr(change)),self.assertRaises(ValueError):
                self.audited(change)

    def test_08_unova_candidate_changed_or_installed_fails(self):
        for change in (
            lambda x: x[0]["unova"]["candidate_ranges"].pop(),
            lambda x: x[3].update(may_install=True),
            lambda x: x[3]["areas"][0].update(destination_map_id=518),
        ):
            with self.subTest(change=repr(change)),self.assertRaises(ValueError):
                self.audited(change)

    def test_09_b07_staged_ids_or_placeholder_mutation_fails(self):
        for change in (
            lambda x: x[4]["candidate_terrain_destinations"].append(496),
            lambda x: x[4]["excluded_empty_destinations"].remove(517),
            lambda x: x[4]["candidate_terrain_destinations"].__setitem__(0, 300),
            lambda x: x[4].update(r07_complete=True),
            lambda x: x[4].update(can_install_into_game=True),
            lambda x: x[4].update(rights_per_asset_verified=True),
        ):
            with self.subTest(change=repr(change)),self.assertRaises(ValueError):
                self.audited(change)

    def test_10_unreconciled_future_reservations_do_not_become_approved(self):
        for change in (
            lambda x: x[2].update(future_reservations_reconciled=True),
            lambda x: x[2].update(confirmed_future_ids_kanto=[442]),
            lambda x: x[2].update(confirmed_future_ids_johto=[600]),
            lambda x: x[2].update(confirmed_future_ids_hoenn=[900]),
            lambda x: x[2].update(r07_complete=True),
        ):
            with self.subTest(change=repr(change)),self.assertRaises(ValueError):
                self.audited(change)

    def test_11_bad_b01_sha_or_count_fails(self):
        for change in (
            lambda x: x[1].update(mapinfos_sha256="0"*64),
            lambda x: x[1].update(native_occupied_map_count=647),
            lambda x: x[2].update(native_mapinfos_sha256="f"*64),
        ):
            with self.subTest(change=repr(change)),self.assertRaises(ValueError):
                self.audited(change)

    def test_12_ranges_are_sorted_consecutive_and_strict(self):
        self.assertEqual(g03.ranges({9,3,2,1,6,7}),
            [{"start":1,"end":3,"count":3},
             {"start":6,"end":7,"count":2},
             {"start":9,"end":9,"count":1}])
        for data in ({0},{1000},{True}):
            with self.assertRaises(ValueError):g03.ranges(data)

    def test_13_duplicate_and_bool_ids_cannot_pass(self):
        for data in ([442,442],[True],[-1],[1000],["442"]):
            with self.subTest(data=data),self.assertRaises(ValueError):
                g03.strict_ids(data,"test")

    def test_14_cli_is_read_only_and_json_is_machine_readable(self):
        p=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_sinnoh_g03_regional_mapids.py")],
            cwd=ROOT,capture_output=True,text=True,check=False)
        self.assertEqual(p.returncode,0,p.stderr)
        out=json.loads(p.stdout)
        self.assertEqual(out["stage"],"SINNOH_G03")
        self.assertFalse(out["r07_complete"])
        self.assertNotIn("report_path",out)

    def test_15_missing_or_wrong_stage_blocks(self):
        for change in (
            lambda x: x[4].update(stage="B08"),
            lambda x: x[4].pop("candidate_terrain_destinations"),
            lambda x: x[4].update(preserves_saves=False),
            lambda x: x[4].update(joiplay_tested=True),
        ):
            with self.subTest(change=repr(change)),self.assertRaises(ValueError):
                self.audited(change)

    def test_16_output_contains_no_user_or_private_game_paths(self):
        s=json.dumps(self.audited(),ensure_ascii=False)
        for forbidden in ("C:\\Users","/Users/","Game.exe","Save01.rxdata",
                          "username","PRIVATE_NATIVE_QA_CLONE_CREATED"):
            self.assertNotIn(forbidden,s)


if __name__=="__main__":unittest.main()
