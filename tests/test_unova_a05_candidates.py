"""A05: historical candidate pool, B05 crosscheck and fail-closed A04 review."""
from __future__ import annotations
import contextlib
import copy
import io
import json
import hashlib
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from server.ruby_marshal import RubyObject
from stage import serialize
import audit_unova_a04_mapids as a04
import audit_unova_a05_candidates as a05

NEEDED=(
 "data/regions/unova-a05-mapid-candidates.json",
 "data/regions/sinnoh-b05-mapid-planning.json",
 "data/regions/sinnoh-b01-actual-native.json",
 "data/regions/sinnoh-b03-installer-evidence.json",
 "data/regions/unova-u03-areas.json",
)


class MapIDA05Tests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="unova-a05-")
        self.addCleanup(t.cleanup)
        self.root=Path(t.name)
        self.project=self.root/"Blue"
        self.project.mkdir()
        for name in NEEDED:
            src=ROOT/name
            dst=self.project/name
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(src,dst)
        self.game=self.root/"Decades/game/Data"
        self.game.mkdir(parents=True)
        info=serialize({
            1:RubyObject("RPG::MapInfo",{"@name":b"Start"}),
            518:RubyObject("RPG::MapInfo",{"@name":b"New untrusted map"})
        })
        (self.game/"MapInfos.rxdata").write_bytes(info)
        (self.game/"Map001.rxdata").write_bytes(b"dummy-map-1")
        (self.game/"Map518.rxdata").write_bytes(b"dummy-map-518")

    def source(self,name):
        return self.project/name

    def mutate(self,fn):
        p=self.source(NEEDED[0])
        j=json.loads(p.read_text())
        fn(j)
        p.write_text(json.dumps(j))
        with self.assertRaises(ValueError):
            a05.validate_plan(self.project)

    def make_a04(self):
        base=a04.scan_source(self.game,"DECADES",base=True)
        report=a04.analyze(base,{})
        path=a04.write_private(self.project,report)
        return path,report

    def test_01_snapshot_648_76_174_82(self):
        report=a05.audit(self.project)
        self.assertEqual(report["historical_occupied_count"],648)
        self.assertEqual(report["sinnoh_admin_hold_count"],76)
        self.assertEqual(report["historical_candidate_count"],174)
        self.assertEqual(report["preferred_candidate_count"],82)
        self.assertEqual(report["potential_expansion_count"],92)
        self.assertFalse(report["can_reserve_mapids"])
        self.assertFalse(report["can_install"])
        self.assertEqual(report["bar_a_completed"],0)
        self.assertIsNone(report["verified_free_mapids"])

    def test_02_preferred_block_and_no_sinnoh_overlap(self):
        r=a05.audit(self.project)
        candidates=set(r["historical_candidate_ids"])
        self.assertEqual(set(range(518,600))<=candidates,True)
        self.assertFalse(set(range(442,518)) & candidates)
        self.assertFalse(set(range(600,1000)) & candidates)
        self.assertNotIn(300,candidates)
        self.assertNotIn(1,candidates)
        self.assertNotIn(22,candidates)
        self.assertIn(2,candidates)

    def test_03_areas_not_assigned(self):
        r=a05.audit(self.project)
        self.assertEqual(r["symbolic_unova_area_count"],74)
        self.assertEqual(r["area_to_destination_map_id"],{})
        self.assertFalse(r["unova_maps_installed"])
        self.assertFalse(r["mapid_reservation_confirmed"])

    def test_04_legacy_short_ids_not_mistaken_for_free(self):
        r=a05.audit(self.project)
        self.assertEqual(r["historical_b04_legacy_omissions"],31)
        self.assertFalse(a05.LEGACY_OMITTED & set(r["historical_candidate_ids"]))

    def test_05_future_hoenn_space_protected(self):
        r=a05.audit(self.project)
        self.assertFalse(set(range(899,1000)) & set(r["historical_candidate_ids"]))
        self.assertFalse(r["future_region_reservations_verified"])

    def test_06_forged_mapid_assignment_rejected(self):
        self.mutate(lambda j:j["proposed_area_to_native_mapid"].update(
            UNOVA_NUVEMA_TOWN=518))

    def test_07_forged_install_ready_rejected(self):
        self.mutate(lambda j:j.update(can_install=True,can_reserve_mapids=True))

    def test_08_forged_game_exe_test_rejected(self):
        self.mutate(lambda j:j.update(game_exe_tested=True))

    def test_09_sinnoh_hold_changed_rejected(self):
        self.mutate(lambda j:j["sinnoh_administrative_hold"].update(end=518,count=77))

    def test_10_preferred_window_changed_rejected(self):
        self.mutate(lambda j:j["unova_preferred_candidate"].update(start=442))

    def test_11_hoenn_space_exposed_rejected(self):
        self.mutate(lambda j:j["protected_ranges"][1].update(end=898))

    def test_12_missing_31_short_mapids_rejected(self):
        self.mutate(lambda j:j["evidence"].update(b04_omitted_short_mapid_count=0))

    def test_13_fake_md_provenance_rejected(self):
        self.mutate(lambda j:j["evidence"].update(supplied_md_sha256="0"*64))

    def test_14_independent_manifest_rights_false_protected(self):
        self.mutate(lambda j:j["evidence"].update(
            original_manifest_hashes_independently_verified=True))

    def test_15_174_historical_count_recomputed_from_b05(self):
        p=self.source(NEEDED[1])
        j=json.loads(p.read_text())
        j["unova"]["candidate_ranges"][-1]["end"]=600
        j["unova"]["candidate_ranges"][-1]["count"]=83
        p.write_text(json.dumps(j))
        with self.assertRaises(ValueError):
            a05.validate_plan(self.project)

    def test_16_current_a04_new_occupation_detected_without_allocation(self):
        path,report=self.make_a04()
        review=a05.audit(self.project,path)
        self.assertEqual(review["status"],"A04_DIFFERENT_OR_CONFLICTING_NEEDS_REVIEW")
        self.assertIn(518,review["a04_observed_candidate_collisions"])
        self.assertFalse(review["a04_preferred_block_observed_vacant"])
        self.assertFalse(review["a04_snapshot_baseline_hash_matches_b05"])
        self.assertFalse(review["can_install"])
        self.assertFalse(review["can_reserve_mapids"])

    def test_17_a04_outside_private_directory_rejected(self):
        path,report=self.make_a04()
        outside=self.root/"a04-remote.json"
        shutil.copyfile(path,outside)
        with self.assertRaises(ValueError):
            a05.audit(self.project,outside)

    def test_18_a04_hash_mismatch_rejected(self):
        path,report=self.make_a04()
        changed=json.loads(path.read_text())
        changed["can_reserve_mapids"]=True
        path.write_text(json.dumps(changed))
        with self.assertRaises(ValueError):
            a05.audit(self.project,path)

    def test_19_a04_extra_flag_false_assumption_rejected(self):
        path,report=self.make_a04()
        report["game_exe_tested"]=True
        path.unlink()
        replaced=a04.write_private(self.project,report)
        with self.assertRaises(ValueError):
            a05.audit(self.project,replaced)

    def test_20_a04_duplicate_physical_map_id_rejected(self):
        path,report=self.make_a04()
        report["sources"]["DECADES"]["maps"].append(
            copy.deepcopy(report["sources"]["DECADES"]["maps"][0]))
        path.unlink()
        replacement=a04.write_private(self.project,report)
        with self.assertRaises(ValueError):
            a05.audit(self.project,replacement)

    def test_21_a04_false_declared_count_rejected(self):
        path,report=self.make_a04()
        report["sources"]["DECADES"]["mapinfos_declared_count"]=999
        path.unlink()
        new=a04.write_private(self.project,report)
        with self.assertRaises(ValueError):
            a05.audit(self.project,new)

    def test_22_a04_observed_ids_must_include_baseline(self):
        path,report=self.make_a04()
        report["observed_or_declared_occupied_map_ids"]=[1]
        report["observed_or_declared_occupied_count"]=1
        path.unlink()
        new=a04.write_private(self.project,report)
        with self.assertRaises(ValueError):
            a05.audit(self.project,new)

    def test_23_a04_future_short_mapids_not_certified_as_free(self):
        path,report=self.make_a04()
        review=a05.audit(self.project,path)
        self.assertIsNone(review["verified_free_mapids"])
        self.assertFalse(review["can_reserve_mapids"])
        self.assertEqual(review["bar_a_completed"],0)

    def test_24_report_save_content_addressed_idempotent(self):
        d=a05.audit(self.project)
        saved=a05.save(self.project,d)
        prior=saved.read_bytes()
        self.assertEqual(saved,a05.save(self.project,d))
        self.assertEqual(saved.read_bytes(),prior)
        other=a05.save(self.project,dict(d,status="not approved"))
        self.assertNotEqual(other,saved)
        self.assertEqual(saved.read_bytes(),prior)

    def test_25_symlink_private_report_directory_blocked(self):
        target=self.root/"external"
        target.mkdir()
        folder=self.project/".blue-work"
        try:
            folder.symlink_to(target,target_is_directory=True)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            a05.save(self.project,a05.audit(self.project))
        self.assertEqual(list(target.iterdir()),[])

    def test_26_cli_no_a04_succeeds_with_pending_status(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            code=a05.main(["--project",str(self.project),"--write"])
        self.assertEqual(code,0)
        body=json.loads(out.getvalue())
        self.assertEqual(body["status"],"HISTORICAL_SNAPSHOT_CANDIDATES_ONLY")
        self.assertFalse(body["a04_report_supplied"])
        self.assertIsNone(body["verified_free_mapids"])
        self.assertFalse((self.project/"game").exists())

    def test_27_cli_specific_A04_report_detects_new_collision(self):
        path,report=self.make_a04()
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            code=a05.main(["--project",str(self.project),"--a04-report",str(path)])
        self.assertEqual(code,0)
        self.assertIn(518,json.loads(out.getvalue())["a04_observed_candidate_collisions"])

    def test_28_a04_wrong_filename_blocked(self):
        path,report=self.make_a04()
        wrong=path.with_name("a04-mapids-"+"a"*16+".json")
        shutil.copyfile(path,wrong)
        with self.assertRaises(ValueError):
            a05.audit(self.project,wrong)

    def test_29_missing_B01_source_catalog_rejected(self):
        self.source(NEEDED[2]).unlink()
        with self.assertRaises(ValueError):
            a05.audit(self.project)

    def test_30_missing_unova_area_catalog_rejected(self):
        self.source(NEEDED[4]).unlink()
        with self.assertRaises(ValueError):
            a05.audit(self.project)

    def test_31_orphan_map_file_from_a04_is_not_certified(self):
        (self.game/"Map519.rxdata").write_bytes(b"other-orphan")
        path,report=self.make_a04()
        review=a05.audit(self.project,path)
        self.assertIn(519,review["a04_observed_candidate_collisions"])
        self.assertFalse(review["can_reserve_mapids"])

    def test_32_A04_no_protected_spaces_become_available(self):
        path,report=self.make_a04()
        review=a05.audit(self.project,path)
        candidates=set(review["historical_candidate_ids"])
        self.assertFalse(candidates&set(range(442,518)))
        self.assertFalse(candidates&set(range(600,1000)))
        self.assertFalse(review["mapid_reservation_confirmed"])


    def test_33_catalog_reference_uses_portable_posix_paths(self):
        """JSON references use '/' on both Linux and Windows."""
        source=json.loads(self.source(NEEDED[0]).read_text("utf-8"))
        self.assertEqual(source["unova_symbolic_area_catalog"],a05.U03.as_posix())
        self.assertEqual(source["evidence"]["cross_reference"],a05.B05.as_posix())
        # Both should run on WindowsPath without platform-dependent str(Path).
        self.assertNotIn("\\",source["unova_symbolic_area_catalog"])
        self.assertNotIn("\\",source["evidence"]["cross_reference"])
        self.assertEqual(a05.audit(self.project)["historical_candidate_count"],174)


if __name__=="__main__":
    unittest.main()
