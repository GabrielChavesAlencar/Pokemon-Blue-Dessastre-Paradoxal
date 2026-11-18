"""G08.2: join real G01-G07 metadata; run only offline G01-G07 fixtures.

No real game files, saved games, network operations, ZIP operations, or installs.
"""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g08_integrated as mod
import audit_unova_g01_chapter_machine as chapter
import audit_unova_g02_gym_story as gym
import audit_unova_g02_elite_finale as elite
import audit_unova_g03_rivals_plasma as rival
import audit_unova_g04_encounter_validation as encounter
import audit_unova_g05_blackout_state as blackout
import audit_unova_g05_travel as travel
import audit_unova_g05_regional_items as items
import audit_unova_g07_incremental_manifest as g72
import audit_unova_g07_transaction as g73
import audit_unova_g07_platform_compat as g74

class UnovaG082Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources=mod.source_state()
        cls.result=mod.audit_contract()
        cls.board=cls.sources["board"]
        cls.root_contract=g72.j(ROOT,mod.FILE)

    def tamper(self,fn):
        source=copy.deepcopy(self.sources)
        fn(source)
        with self.assertRaises(ValueError):
            mod.validate_links(source)

    def transaction(self,platform="windows"):
        pkg,manifest,old,new=g73.multi_file_fixture()
        state=g73.base_fixture(pkg,manifest,old)
        req=g74.fixture_request(platform,pkg,state)
        return pkg,manifest,old,new,state,req

    def test_001_status_not_native(self):
        self.assertEqual(self.result["status"],"ALL_G01_TO_G07_SOURCE_CONTRACTS_VERIFIED_OFFLINE")
    def test_002_coverage_all_contracts(self):
        self.assertEqual(self.result["coverage"],22)
        self.assertEqual(len(self.root_contract["coverage"]),22)
    def test_003_sources_and_contracts_join(self):
        self.assertEqual(self.root_contract["source_contracts"],mod.SOURCES)
    def test_004_guards_immutable(self):
        self.assertEqual(self.root_contract["constraints"],mod.CONSTRAINTS)
    def test_005_unova_not_installed(self):
        self.assertFalse(self.result["can_install"])
    def test_006_native_technical_unchanged(self):
        self.assertEqual(self.board["native_technical_bar"]["completed"],0)
    def test_007_native_playable_unchanged(self):
        self.assertEqual(self.board["native_playable_bar"]["completed"],0)
    def test_008_native_files_not_written(self):
        self.assertEqual(self.result["native_files_written"],0)
    def test_009_saves_not_modified(self):
        self.assertFalse(self.result["native_saves_modified"])
    def test_010_rights_no_approval(self):
        self.assertTrue(all(v is None for v in self.root_contract["evidence"].values()))
    def test_011_region_not_playable(self):
        self.assertEqual(self.sources["registry"]["regions"]["UNOVA"]["status"],"planned")
    def test_012_regions_board_not_playable(self):
        self.assertEqual(self.board["status"],"PLANNED_NOT_NATIVE_PLAYABLE")
    def test_013_74_areas_joined(self):
        self.assertEqual(self.result["areas_joined"],74)
    def test_014_12_chapters_joined(self):
        self.assertEqual(self.result["chapters_joined"],12)
    def test_015_12_missions_linked(self):
        self.assertEqual(self.result["mission_gates_joined"],12)
    def test_016_8_gyms_linked(self):
        self.assertEqual(self.result["gyms_joined"],8)
    def test_017_4_elite_joined(self):
        self.assertEqual(self.result["elite_members"],4)
    def test_018_15_rivals_encounters(self):
        self.assertEqual(self.result["rival_events"],15)
    def test_019_no_native_encounters(self):
        self.assertEqual(self.result["native_tables_verified"],0)
    def test_020_no_real_teams(self):
        self.assertEqual(self.result["native_teams_verified"],0)
    def test_021_g01_entry_to_first_chapter(self):
        self.assertEqual(self.sources["transitions"]["transitions"][0]["to"],
                         self.sources["chapters"]["chapters"][1]["key"])
    def test_022_g01_gate_from_first_gym(self):
        g=self.sources["gyms"]["gyms"][0]
        self.assertEqual(g["mission_key"],self.sources["chapters"]["missions"][1]["key"])
    def test_023_white_final_gym_iris(self):
        self.assertEqual(self.sources["gyms"]["gyms"][-1]["leader_key"],"IRIS")
    def test_024_elite_order_white(self):
        self.assertEqual([x["member_name"] for x in self.sources["finale"]["elite_members"]],
                         ["SHAUNTAL","GRIMSLEY","CAITLIN","MARSHAL"])
    def test_025_g03_read_only_linked_events(self):
        self.assertEqual(self.sources["rivals"]["canonical_linked_receipts"],
                         "READ_ONLY_G01_G02_NO_DUPLICATION")
    def test_026_plasma_teams_not_native(self):
        self.assertFalse(self.sources["rivals"]["trainer_pbs_compiled"])
    def test_027_g04_wild_rate_unknown(self):
        self.assertTrue(all(row["native_encounter_rate"] is None
                            for row in self.sources["encounter_validation"]["areas"]))
    def test_028_g04_native_species_unknown(self):
        self.assertTrue(all(row["native_species"] is None
                            for row in self.sources["encounter_validation"]["areas"]))
    def test_029_g05_unova_region_not_routable(self):
        self.assertNotIn("UNOVA",travel.ROUTABLE)
    def test_030_g05_hm_and_keys_region_local(self):
        self.assertEqual(items.LOCAL_KINDS,("HM","KEY_ITEM"))
    def test_031_g05_tm_globally_shared(self):
        self.assertIn("TM",items.GLOBAL_KINDS)
    def test_032_g05_special_badge_threshold(self):
        self.assertFalse(self.sources["badges_specials"]["can_install"])
    def test_033_blackout_source_preserves_shared_money(self):
        reg=self.sources["registry"];st=blackout.fixture(reg)
        changed=blackout.blackout(st,reg)
        self.assertEqual(changed["fixture"]["money"],st["money"])
    def test_034_blackout_preserves_boxes(self):
        reg=self.sources["registry"];st=blackout.fixture(reg)
        changed=blackout.blackout(st,reg)
        self.assertEqual(changed["fixture"]["boxes"],st["boxes"])
    def test_035_blackout_preserves_TMs(self):
        reg=self.sources["registry"];st=blackout.fixture(reg)
        changed=blackout.blackout(st,reg)
        self.assertEqual(changed["fixture"]["bag"],st["bag"])
    def test_036_blackout_preserves_mechanics(self):
        reg=self.sources["registry"];st=blackout.fixture(reg)
        changed=blackout.blackout(st,reg)
        self.assertEqual(changed["fixture"]["mechanics_by_region"],st["mechanics_by_region"])
    def test_037_blackout_respects_current_region(self):
        reg=self.sources["registry"];st=blackout.fixture(reg)
        changed=blackout.blackout(st,reg)
        self.assertIn(changed["fixture"]["position"],st["verified_centers"]["KANTO"])
    def test_038_blackout_does_not_override_original(self):
        reg=self.sources["registry"];st=blackout.fixture(reg);before=copy.deepcopy(st)
        blackout.blackout(st,reg)
        self.assertEqual(st,before)
    def test_039_predecessor_package_not_installable(self):
        self.assertFalse(self.sources["incremental"]["can_install"])
    def test_040_transaction_not_installable(self):
        self.assertFalse(self.sources["transaction"]["can_install"])
    def test_041_platform_not_installable(self):
        self.assertFalse(self.sources["platform"]["can_install"])
    def test_042_platform_does_not_approve_windows_or_android(self):
        for row in self.sources["platform"]["platforms"].values():
            self.assertFalse(row["native_patch_supported"])
    def test_043_g072_demo_package_validated(self):
        pkg,m,old,new=g72.demo_package()
        self.assertEqual(g72.validate_package(pkg,m,old,new)["files_checked"],1)
    def test_044_g073_two_files_validated(self):
        pkg,m,old,new=g73.multi_file_fixture()
        self.assertEqual(g72.validate_package(pkg,m,old,new)["files_checked"],2)
    def test_045_g074_contract_preview_only(self):
        for p in g74.PLATFORMS:
            pkg,m,old,new,st,req=self.transaction(p)
            response=g74.preview(p,req,pkg,m,old,new,st)
            self.assertEqual(response["status"],"PLATFORM_DOCS_PREVIEW_NOT_INSTALLABLE")
    def test_046_g074_no_native_files(self):
        for p in g74.PLATFORMS:
            pkg,m,old,new,st,req=self.transaction(p)
            response=g74.preview(p,req,pkg,m,old,new,st)
            self.assertEqual(response["native_files_written"],0)
    def test_047_G072_protection_strict(self):
        self.assertEqual(self.sources["incremental"]["allowed_prefix"],g72.PREFIX)
    def test_048_G073_snapshot_protects_user_data(self):
        self.assertEqual(set(g73.PROTECTED),set(self.sources["transaction"]["protected_namespaces"]))
    def test_049_G074_channels_no_unova(self):
        self.assertNotIn("unova",self.sources["platform"]["platforms"]["android"]["existing_update_channels"])
    def test_050_validation_read_only(self):
        before=copy.deepcopy(self.sources)
        mod.validate_links(self.sources)
        self.assertEqual(self.sources,before)
    def test_051_tracker_G08_2_pending_or_done(self):
        t=next(x for x in self.board["groups"] if x["id"]=="G08")
        self.assertIn(t["tasks"][1]["status"],("pending","done"))
    def test_052_demo_g01_to_g07(self):
        result=mod.synthetic_chain()
        self.assertEqual(result["status"],"CROSS_CONTRACT_SYNTHETIC_ONLY_NOT_GAMEPLAY")
    def test_053_demo_badges(self):
        self.assertEqual(mod.synthetic_chain()["gym_badges_simulated"],8)
    def test_054_demo_elite_four(self):
        self.assertEqual(mod.synthetic_chain()["elite_four_simulated"],4)
    def test_055_demo_rivals_plasma(self):
        self.assertEqual(mod.synthetic_chain()["plasma_rival_battles_simulated"],9)
    def test_056_demo_wild_not_installed(self):
        self.assertEqual(mod.synthetic_chain()["native_encounter_tables"],0)
    def test_057_demo_master_scaled(self):
        self.assertEqual(mod.synthetic_chain()["synthetic_master_scaled_level"],36)
    def test_058_demo_HM_roundtrip(self):
        self.assertTrue(mod.synthetic_chain()["regional_hm_restored"])
    def test_059_demo_money_preserved(self):
        self.assertTrue(mod.synthetic_chain()["blackout_money_preserved"])
    def test_060_demo_boxes_preserved(self):
        self.assertTrue(mod.synthetic_chain()["blackout_boxes_preserved"])
    def test_061_demo_cas_platforms(self):
        self.assertEqual(set(mod.synthetic_chain()["platform_dry_runs"]),{"windows","android"})
    def test_062_demo_injected_rollbacks_per_platform(self):
        self.assertTrue(all(info["faults_rolled_back"]==7
           for info in mod.synthetic_chain()["platform_dry_runs"].values()))
    def test_063_cli_contract_check(self):
        output=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g08_integrated.py"),"--check"],
          capture_output=True,text=True)
        self.assertEqual(output.returncode,0,output.stdout+output.stderr)
        self.assertFalse(json.loads(output.stdout)["can_install"])
    def test_064_cli_simulation(self):
        output=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g08_integrated.py"),"--simulate-demo"],
          capture_output=True,text=True)
        self.assertEqual(output.returncode,0,output.stdout+output.stderr)
        self.assertFalse(json.loads(output.stdout)["can_install"])
    def test_065_G01_serialization_not_save(self):
        self.assertFalse(self.sources["chapters"]["native_game_files_modified"])
    def test_066_G05_no_UnoVa_center_installed(self):
        self.assertFalse(self.sources["blackout"]["native_center_installed"])
    def test_067_G07_rights_declared_missing(self):
        self.assertEqual(self.sources["incremental"]["rights_status"],
                         "FIXTURE_ONLY_NOT_DISTRIBUTABLE")
    def test_068_game_exe_qa_not_verified(self):
        self.assertFalse(self.sources["chapters"]["game_exe_tested"])
    def test_069_portal_links_use_symbolic_area_keys(self):
        self.assertTrue(all(a["key"].startswith("UNOVA_") for a in self.sources["areas"]["areas"]))
    def test_070_no_unova_native_release(self):
        self.assertIsNone(self.sources["platform"]["native_evidence"]["unova_release_signature"])

# Fail-closed independent cross-contract mutations. All join logic runs against
# copies of the real audited G01-G07 sources, never fabricated MapIDs or data.
_TAMPERS={
 "orphan_mission_area":lambda d:d["chapters"]["missions"][0].update(reference_area_key="UNOVA_FAKE_MAP"),
 "orphan_mission_chapter":lambda d:d["chapters"]["missions"][0].update(chapter_key="UNKNOWN"),
 "mission_installed":lambda d:d["chapters"]["missions"][0].update(real_event_id=518),
 "mission_not_planned":lambda d:d["chapters"]["missions"][0].update(planned_only=False),
 "duplicate_mission":lambda d:d["chapters"]["missions"][1].update(key=d["chapters"]["missions"][0]["key"]),
 "remove_mission":lambda d:d["chapters"]["missions"].pop(),
 "reorder_chapters":lambda d:d["chapters"]["chapters"][1].update(index=9),
 "chapter_native_map":lambda d:d["chapters"]["chapters"][1].update(map_id=518),
 "chapter_false_qa":lambda d:d["chapters"]["chapters"][1].update(game_exe_verified=True),
 "transition_skip":lambda d:d["transitions"]["transitions"][1].update(to="UNOVA_CH10_LEAGUE"),
 "transition_source":lambda d:d["transitions"]["transitions"][0].update(**{"from":"UNOVA_CH03_NACRENE"}),
 "transition_fake_gate":lambda d:d["transitions"]["transitions"][2].update(required_mission_key="BAD"),
 "gym_native_badge":lambda d:d["gyms"]["gyms"][0].update(native_badge_item_id=1),
 "gym_native_switch":lambda d:d["gyms"]["gyms"][0].update(native_badge_switch_id=200),
 "gym_native_team":lambda d:d["gyms"]["gyms"][0].update(trainer_party=["Snivy"]),
 "gym_native_levels":lambda d:d["gyms"]["gyms"][0].update(trainer_levels=[15]),
 "gym_fake_approved":lambda d:d["gyms"]["gyms"][0].update(challenge_status="NATIVE_PLAYABLE"),
 "gym_wrong_chapter":lambda d:d["gyms"]["gyms"][0].update(chapter_key="INVALID"),
 "gym_wrong_area":lambda d:d["gyms"]["gyms"][0].update(gym_area_key="MAP518"),
 "gym_unknown_mission":lambda d:d["gyms"]["gyms"][0].update(mission_key="BAD"),
 "gym_duplicate_index":lambda d:d["gyms"]["gyms"][1].update(index=1),
 "gym_native_event":lambda d:d["gyms"]["gyms"][0]["events"][0].update(native_event_id=42),
 "gym_native_map":lambda d:d["gyms"]["gyms"][0]["events"][0].update(source_map_id=518),
 "gym_real_trainer_id":lambda d:d["gyms"]["gyms"][0]["events"][0].update(trainer_id=22),
 "elite_name_forged":lambda d:d["finale"]["elite_members"][0].update(member_name="FAKE"),
 "elite_native_team":lambda d:d["finale"]["elite_members"][0].update(team=["FAKE"]),
 "elite_native_levels":lambda d:d["finale"]["elite_members"][0].update(levels=[70]),
 "elite_native_trainer":lambda d:d["finale"]["elite_members"][0].update(native_trainer_id=9),
 "elite_orphan_area":lambda d:d["finale"]["elite_members"][0].update(area_key="MAP518"),
 "rival_native_team":lambda d:d["rivals"]["encounters"][0].update(canonical_team=["FAKE"]),
 "rival_native_level":lambda d:d["rivals"]["encounters"][0].update(canonical_levels=[12]),
 "rival_native_event":lambda d:d["rivals"]["encounters"][0].update(native_event_id=100),
 "rival_native_map":lambda d:d["rivals"]["encounters"][0].update(native_map_id=518),
 "rival_orphan_area":lambda d:d["rivals"]["encounters"][0].update(reference_area_key="NOPE"),
 "rival_orphan_chapter":lambda d:d["rivals"]["encounters"][0].update(chapter_key="NOPE"),
 "g04_missing_area":lambda d:d["encounter_validation"]["areas"].pop(),
 "g04_native_map":lambda d:d["encounter_validation"]["areas"][0].update(native_map_id=518),
 "g04_species_invented":lambda d:d["encounter_validation"]["areas"][0].update(native_species="PIKACHU"),
 "g04_rate_invented":lambda d:d["encounter_validation"]["areas"][0].update(native_encounter_rate=20),
 "g04_native_pbs":lambda d:d["encounter_validation"]["areas"][0].update(native_pbs_verified=True),
 "g04_installed":lambda d:d["encounter_validation"]["areas"][0].update(installable=True),
 "g04_duplicate_area":lambda d:d["encounter_validation"]["areas"][1].update(area_key=d["encounter_validation"]["areas"][0]["area_key"]),
 "g04_methods_missing_area":lambda d:d["encounter_methods"]["areas"].pop(),
 "g04_scaling_missing_area":lambda d:d["wild_scaling"]["areas"].pop(),
 "area_native_map":lambda d:d["areas"]["areas"][0].update(source_map_id=518),
 "area_native_destination":lambda d:d["areas"]["areas"][0].update(destination_map_id=518),
 "area_playable":lambda d:d["areas"]["areas"][0].update(state="playable"),
 "area_duplicate_key":lambda d:d["areas"]["areas"][1].update(key=d["areas"]["areas"][0]["key"]),
 "native_registry_promotion":lambda d:d["registry"]["regions"]["UNOVA"].update(status="playable"),
 "board_technical_one":lambda d:d["board"]["native_technical_bar"].update(completed=1),
 "board_playable_one":lambda d:d["board"]["native_playable_bar"].update(completed=1),
 "board_false_status":lambda d:d["board"].update(status="PLAYABLE"),
 "item_native_approved":lambda d:d["regional_items"].update(can_install=True),
 "special_native_approved":lambda d:d["badges_specials"].update(can_install=True),
 "travel_native_approved":lambda d:d["travel"].update(can_install=True),
 "blackout_native_approved":lambda d:d["blackout"].update(can_install=True),
 "g07_package_native":lambda d:d["incremental"].update(can_install=True),
 "g07_transaction_native":lambda d:d["transaction"].update(can_install=True),
 "g07_platform_native":lambda d:d["platform"].update(can_install=True),
 "g07_package_rights":lambda d:d["incremental"].update(release_allowed=True),
 "g07_transaction_rights":lambda d:d["transaction"].update(release_allowed=True),
 "g07_platform_rights":lambda d:d["platform"].update(can_release=True),
 "foreign_region":lambda d:d["postgame"].update(region="HOENN"),
 "rival_game_qa":lambda d:d["rivals"].update(game_exe_tested=True),
 "blackout_game_qa":lambda d:d["blackout"].update(game_exe_tested=True),
}
for _name,_edit in _TAMPERS.items():
    def _test(self,mutation=_edit):
        self.tamper(mutation)
    setattr(UnovaG082Tests,"test_refuse_cross_"+_name,_test)

# G07.3's seven fault points are tested through the platform adapter, NOT a
# mock that could accidentally claim native rollback.
for _platform in g74.PLATFORMS:
    for _point in g73.FAULTS:
        def _test(self,p=_platform,f=_point):
            pkg,m,old,new,st,req=self.transaction(p)
            baseline=copy.deepcopy(st)
            out=g74.preview(p,req,pkg,m,old,new,st,fail_at=f)
            self.assertEqual(out["transaction_status"],"SIMULATED_ROLLBACK_COMPLETE")
            self.assertEqual(out["state"],baseline)
            self.assertEqual(st,baseline)
            self.assertFalse(out["install_allowed"])
            self.assertEqual(out["native_files_written"],0)
        setattr(UnovaG082Tests,"test_platform_rollback_"+_platform+"_"+_point,_test)

for _namespace in g73.PROTECTED:
    for _platform in g74.PLATFORMS:
        def _test(self,p=_platform,scope=_namespace):
            pkg,m,old,new,st,req=self.transaction(p)
            concurrent=copy.deepcopy(st)
            key=next(iter(concurrent["protected"][scope]))
            concurrent["protected"][scope][key]="FIXTURE_CHANGED_EXTERNALLY"
            for where in ("observed_after_staging","observed_before_publish"):
                out=g74.preview(p,req,pkg,m,old,new,st,**{where:concurrent})
                self.assertEqual(out["transaction_status"],"CONFLICT_CAS_CONCURRENT_EDIT")
                self.assertEqual(out["state"],st)
        setattr(UnovaG082Tests,"test_cross_region_conflict_"+_platform+"_"+_namespace,_test)

if __name__=="__main__":unittest.main()
