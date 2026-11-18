"""G08.3 six-region offline integration: native entry denied, CAS and full rollback."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g08_multiregional as reg
import audit_unova_g08_integrated as g82
import audit_unova_g05_travel as travel
import audit_unova_g05_regional_items as items
import audit_unova_g05_badges_specials as special
import audit_unova_g05_blackout_state as faint
import audit_unova_g07_incremental_manifest as g72
import audit_unova_g07_transaction as g73
import audit_unova_g07_platform_compat as g74

class UnovaG083Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract,cls.registry=reg.load()
        cls.audit=reg.audit_contract()
        cls.tc,cls.r,cls.ic,cls.sc,_=travel.load_project()

    def world(self):
        return reg.fixture(self.r)
    def at(self,region):
        state=self.world()
        for target in reg.ROUTE[1:]:
            if state["current"]==region:break
            out=reg.travel_step(state,target,self.r,self.tc,self.ic,self.sc,
                 expected_snapshot_sha256=reg.etag(state,self.r))
            self.assertEqual(out["status"],"SYNTHETIC_TRAVEL_COMMIT_NOT_INSTALLED")
            state=out["state"]
        self.assertEqual(state["current"],region)
        return state
    def step(self,state,target,**kw):
        return reg.travel_step(state,target,self.r,self.tc,self.ic,self.sc,
                  expected_snapshot_sha256=reg.etag(state,self.r),**kw)
    def bad_claim(self,edit):
        d=copy.deepcopy(self.contract);edit(d)
        with self.assertRaises(ValueError):
            reg.validate_claims(d,self.registry)
    def bad_world(self,edit):
        world=self.world()
        edit(world)
        with self.assertRaises((ValueError,TypeError,KeyError)):
            reg.validate_world(world,self.r)
    def test_001_status(self):
        self.assertEqual(self.audit["status"],"SIX_REGION_FIXTURES_AUDITED_NOT_NATIVE")
    def test_002_six_profiles(self):
        self.assertEqual(self.audit["regions"],list(reg.REGIONS))
    def test_003_G082_dependency(self):
        self.assertEqual(g82.audit_contract()["coverage"],22)
    def test_004_original_contracts_are_sources(self):
        self.assertEqual(self.contract["sources"],reg.SOURCES)
    def test_005_native_technical_zero(self):
        self.assertEqual(self.audit["native_technical_completed"],0)
    def test_006_native_playable_zero(self):
        self.assertEqual(self.audit["native_playable_completed"],0)
    def test_007_not_installable(self):
        self.assertFalse(self.audit["can_install"])
    def test_008_no_real_save_read(self):
        self.assertFalse(self.contract["can_read_user_saves"])
    def test_009_no_runtime_execution(self):
        self.assertFalse(self.audit["game_exe_invoked"])
        self.assertFalse(self.audit["joiplay_invoked"])
    def test_010_source_registry_statuses(self):
        self.assertEqual({k:self.r["regions"][k]["status"] for k in reg.REGIONS},reg.STATUSES)
    def test_011_routable_fixture_only_four(self):
        self.assertEqual(reg.ROUTE,("KANTO","HOENN","JOHTO","DECADES","KANTO"))
        self.assertEqual(reg.travel.ROUTABLE,("DECADES","KANTO","JOHTO","HOENN"))
    def test_012_blocked_planned_regions(self):
        self.assertEqual(reg.BLOCKED,("SINNOH","UNOVA"))
    def test_013_profile_status_not_real_installation(self):
        self.assertFalse(any(p["native_qa_from_this_suite"] for p in self.contract["regional_profiles"]))
    def test_014_no_native_mapid_evidence(self):
        self.assertTrue(all(v is None for v in self.contract["runtime_evidence"].values()))
    def test_015_mandatory_fail_points(self):
        self.assertEqual(self.contract["failure_points"],reg.FAULTS)
    def test_016_immutable_policy(self):
        self.assertEqual(self.contract["policy"],reg.POLICY)
    def test_017_no_true_install_contract(self):
        for k in ("can_install","can_execute_real_travel","can_read_user_saves","release_allowed"):
            self.assertIs(self.contract[k],False)
    def test_018_no_writes(self):
        self.assertEqual(self.audit["native_files_written"],0)
    def test_019_Barra_G_task_registered(self):
        board=g72.j(ROOT,reg.SOURCES["tracker"])
        task=next(t for group in board["groups"] if group["id"]=="G08" for t in group["tasks"] if t["id"]=="G08.3")
        self.assertIn(task["status"],("pending","done"))
        self.assertEqual(board["native_playable_bar"]["completed"],0)
    def test_020_fixture_valid(self):
        self.assertEqual(reg.validate_world(self.world(),self.r)["current"],"KANTO")
    def test_021_etag_stable(self):
        s=self.world()
        self.assertEqual(reg.etag(s,self.r),reg.etag(copy.deepcopy(s),self.r))
    def test_022_etag_sha(self):
        self.assertRegex(reg.etag(self.world(),self.r),r"^[a-f0-9]{64}$")
    def test_023_no_unova_center(self):
        self.assertIsNone(self.world()["checkpoints"]["UNOVA"])
    def test_024_no_sinnoh_center(self):
        self.assertIsNone(self.world()["checkpoints"]["SINNOH"])
    def test_025_start_has_global_TM(self):
        self.assertIn("FIXTURE_TM_GLOBAL",self.world()["shared"]["tm_ledger"])
    def test_026_KANTO_to_HOENN(self):
        out=self.step(self.world(),"HOENN")
        self.assertEqual(out["status"],"SYNTHETIC_TRAVEL_COMMIT_NOT_INSTALLED")
    def test_027_HOENN_to_JOHTO(self):
        out=self.step(self.at("HOENN"),"JOHTO")
        self.assertEqual(out["status"],"SYNTHETIC_TRAVEL_COMMIT_NOT_INSTALLED")
    def test_028_JOHTO_to_DECADES(self):
        out=self.step(self.at("JOHTO"),"DECADES")
        self.assertEqual(out["status"],"SYNTHETIC_TRAVEL_COMMIT_NOT_INSTALLED")
    def test_029_DECADES_to_KANTO(self):
        out=self.step(self.at("DECADES"),"KANTO")
        self.assertEqual(out["status"],"SYNTHETIC_TRAVEL_COMMIT_NOT_INSTALLED")
    def test_030_roundtrip_KANTO_HM(self):
        s=self.at("DECADES")
        arrived=self.step(s,"KANTO")["state"]
        self.assertTrue(any(x["id"]=="FIXTURE_KANTO_HM" for x in arrived["travel_state"]["bag_state"]["bag"]))
    def test_031_roundtrip_KANTO_local_PC(self):
        arrived=self.step(self.at("DECADES"),"KANTO")["state"]
        self.assertTrue(any(x["id"]=="FIXTURE_KANTO_PC_KEY" for x in arrived["travel_state"]["bag_state"]["pc"]))
    def test_032_TM_preserved_for_all_hops(self):
        for key in ("KANTO","HOENN","JOHTO","DECADES"):
            s=self.at(key)
            self.assertTrue(any(x["id"]=="FIXTURE_TM_GLOBAL" for x in s["travel_state"]["bag_state"]["bag"]))
    def test_033_money_unchanged(self):
        self.assertEqual(self.at("DECADES")["shared"]["money"],4500)
    def test_034_coins_unchanged(self):
        self.assertEqual(self.at("DECADES")["shared"]["coins"],125)
    def test_035_boxes_outside_party_preserved(self):
        self.assertEqual(self.at("DECADES")["shared"]["global_boxes"],self.world()["shared"]["global_boxes"])
    def test_036_special_box_preserved(self):
        self.assertEqual(self.at("DECADES")["shared"]["special_storage"],self.world()["shared"]["special_storage"])
    def test_037_world_progress_preserved(self):
        self.assertEqual(self.at("DECADES")["shared"]["world_progress"],self.world()["shared"]["world_progress"])
    def test_038_achievements_per_region(self):
        self.assertEqual(self.at("DECADES")["travel_state"]["party_state"]["achievements"],
                         self.world()["travel_state"]["party_state"]["achievements"])
    def test_039_KANTO_mechanics_restored(self):
        before=self.world()["travel_state"]["current_mechanics"]
        arrived=self.step(self.at("DECADES"),"KANTO")["state"]
        self.assertEqual(arrived["travel_state"]["current_mechanics"],before)
    def test_040_boxed_legendary_after_HOENN(self):
        arrived=self.at("HOENN")
        self.assertIn("FIXTURE_LEGEND",arrived["travel_state"]["pc_boxes"].values())
    def test_041_special_not_in_party_after_HOENN(self):
        p=self.at("HOENN")["travel_state"]["party_state"]["party"]
        self.assertNotIn("FIXTURE_LEGEND",[row["id"] for row in p])
    def test_042_special_no_duplicate_box(self):
        s=self.at("DECADES")
        self.assertEqual(list(s["travel_state"]["pc_boxes"].values()).count("FIXTURE_LEGEND"),1)
    def test_043_special_unlock_local_badges(self):
        p=self.world()["travel_state"]["party_state"]
        self.assertFalse(special.allow_specials(p,self.r,"HOENN"))
    def test_044_native_specials_not_approved(self):
        self.assertFalse(self.contract["can_install"])
        self.assertFalse(self.tc["can_install"])
    def test_045_foreign_checkpoint_never_used(self):
        k=reg.blackout_step(self.world(),"KANTO",self.r)
        self.assertNotEqual(k["after"]["position"],k["before"]["native_checkpoint"])
        self.assertEqual(k["after"]["checkpoint_owner"],"KANTO")
    def test_046_all_existing_centers_from_correct_region(self):
        for key in travel.ROUTABLE:
            result=reg.blackout_step(self.world(),key,self.r)
            self.assertIn(result["after"]["position"],result["before"]["verified_centers"][key])
    def test_047_money_preserved_after_each_blackout(self):
        for key in travel.ROUTABLE:
            result=reg.blackout_step(self.world(),key,self.r)
            self.assertEqual(result["before"]["money"],result["after"]["money"])
    def test_048_boxes_preserved_after_each_blackout(self):
        for key in travel.ROUTABLE:
            result=reg.blackout_step(self.world(),key,self.r)
            self.assertEqual(result["before"]["boxes"],result["after"]["boxes"])
    def test_049_registered_local_HMs_preserved(self):
        for key in travel.ROUTABLE:
            result=reg.blackout_step(self.world(),key,self.r)
            self.assertEqual(result["before"]["bag"],result["after"]["bag"])
    def test_050_badge_flags_preserved(self):
        for key in travel.ROUTABLE:
            result=reg.blackout_step(self.world(),key,self.r)
            self.assertEqual(result["before"]["native_badges"],result["after"]["native_badges"])
    def test_051_blackout_progress_preserved(self):
        for key in travel.ROUTABLE:
            result=reg.blackout_step(self.world(),key,self.r)
            self.assertEqual(result["before"]["leagues"],result["after"]["leagues"])
    def test_052_blackout_mechanics_preserved(self):
        for key in travel.ROUTABLE:
            result=reg.blackout_step(self.world(),key,self.r)
            self.assertEqual(result["before"]["mechanics_by_region"],result["after"]["mechanics_by_region"])
    def test_053_blackout_planned_sinnoh_no_center(self):
        result=reg.blackout_step(self.world(),"SINNOH",self.r)
        self.assertEqual(result["status"],"PLANNED_REGION_RESPAWN_UNVERIFIED")
    def test_054_blackout_planned_unova_no_center(self):
        result=reg.blackout_step(self.world(),"UNOVA",self.r)
        self.assertEqual(result["status"],"PLANNED_REGION_RESPAWN_UNVERIFIED")
    def test_055_unova_travel_blocked(self):
        result=self.step(self.world(),"UNOVA")
        self.assertEqual(result["status"],"DESTINATION_NOT_INSTALLED_OR_SUPPORTED")
    def test_056_sinnoh_travel_blocked(self):
        result=self.step(self.world(),"SINNOH")
        self.assertEqual(result["status"],"DESTINATION_NOT_INSTALLED_OR_SUPPORTED")
    def test_057_source_not_mutated(self):
        original=self.world();snapshot=copy.deepcopy(original)
        self.step(original,"HOENN")
        self.assertEqual(snapshot,original)
    def test_058_bad_world_CAS(self):
        current=self.world()
        r=reg.travel_step(current,"HOENN",self.r,self.tc,self.ic,self.sc,
            expected_snapshot_sha256="b"*64)
        self.assertEqual(r["status"],"CONFLICT_WORLD_CAS_STALE")
    def test_059_concurrent_money_detected(self):
        current=self.world();other=copy.deepcopy(current)
        other["shared"]["money"]=1
        result=self.step(current,"HOENN",observed_after_staging=other)
        self.assertEqual(result["status"],"CONFLICT_WORLD_CAS_CONCURRENT_EDIT")
        self.assertEqual(result["state"],current)
    def test_060_concurrent_box_detected(self):
        current=self.world();other=copy.deepcopy(current)
        other["shared"]["global_boxes"]["FIXTURE_GLOBAL_BOX"]="FIXTURE_DIFFERENT_MON"
        result=self.step(current,"HOENN",observed_after_staging=other)
        self.assertEqual(result["status"],"CONFLICT_WORLD_CAS_CONCURRENT_EDIT")
    def test_061_concurrent_checkpoint_refused(self):
        current=self.world();other=copy.deepcopy(current)
        other["checkpoints"]["UNOVA"]="FIXTURE_UNOVA_FAKE_CENTER"
        with self.assertRaises(ValueError):
            self.step(current,"HOENN",observed_after_staging=other)
    def test_062_concurrent_history_detected(self):
        current=self.world();other=copy.deepcopy(current)
        other["shared"]["world_progress"]["FIXTURE_DECADES_PROGRESS"]="FIXTURE_EXTERNAL_EDIT"
        result=self.step(current,"HOENN",observed_after_staging=other)
        self.assertEqual(result["status"],"CONFLICT_WORLD_CAS_CONCURRENT_EDIT")
    def test_063_native_file_writes_zero(self):
        self.assertEqual(self.audit["native_files_written"],0)
    def test_064_G073_full_rollback(self):
        p,m,old,new=g73.multi_file_fixture()
        state=g73.base_fixture(p,m,old)
        out=g73.transact(state,p,m,old,new,expected_generation=state["generation"],
            expected_snapshot_sha256=g73.state_etag(state),fail_at="after_first_candidate_write")
        self.assertEqual(out["status"],"SIMULATED_ROLLBACK_COMPLETE")
        self.assertEqual(out["state"],state)
    def test_065_G074_windows_and_android_never_installed(self):
        d=g74.demo()
        self.assertFalse(d["can_install"])
        self.assertEqual(set(d["platforms"]),{"windows","android"})
    def test_066_G082_end_to_end_chain(self):
        self.assertFalse(g82.synthetic_chain()["can_install"])
    def test_067_cli_check(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g08_multiregional.py"),"--check"],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(len(json.loads(p.stdout)["regions"]),6)
    def test_068_cli_demo(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g08_multiregional.py"),"--simulate-demo"],capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(len(json.loads(p.stdout)["hops"]),4)
    def test_069_demo_preserves_regional_HM(self):
        self.assertTrue(reg.demo()["regional_hm_restored"])
    def test_070_demo_does_not_claim_real_game(self):
        d=reg.demo()
        self.assertFalse(d["game_exe_tested"])
        self.assertFalse(d["unova_playable"])

# Contract mutation checks: never invent native QA/rights, real MapIDs or
# real installation through a changed progress tracker.
_BAD_CONTRACT={
 "wrong_phase":lambda d:d.update(phase="NATIVE_LIVE"),
 "wrong_region":lambda d:d.update(region="SINNOH"),
 "fake_can_install":lambda d:d.update(can_install=True),
 "fake_release":lambda d:d.update(release_allowed=True),
 "read_real_saves":lambda d:d.update(can_read_user_saves=True),
 "perform_real_travel":lambda d:d.update(can_execute_real_travel=True),
 "native_technical":lambda d:d.update(native_technical_completed=1),
 "native_playable":lambda d:d.update(native_playable_completed=32),
 "false_windows_QA":lambda d:d["runtime_evidence"].update(unova_runtime_windows="PASS"),
 "false_android_QA":lambda d:d["runtime_evidence"].update(unova_runtime_android="PASS"),
 "invent_mapids":lambda d:d["runtime_evidence"].update(unova_mapids=[518]),
 "falsify_rights":lambda d:d["runtime_evidence"].update(rights_approved=True),
 "false_unova_installed":lambda d:d["runtime_evidence"].update(unova_installed=True),
 "false_sinnoh_installed":lambda d:d["runtime_evidence"].update(sinnoh_installed=True),
 "add_unova_routable":lambda d:d["regional_profiles"][5].update(runtime_fixture_routable=True),
 "sinnoh_playable":lambda d:d["regional_profiles"][4].update(registry_status="playable"),
 "johto_native":lambda d:d["regional_profiles"][2].update(native_qa_from_this_suite=True),
 "force_blocked_to_route":lambda d:d["allowed_fixture_route"].insert(1,"UNOVA"),
 "unblock_sinnoh":lambda d:d["blocked_native_destinations"].remove("SINNOH"),
 "remove_KANTO_from_routes":lambda d:d["allowed_fixture_route"].pop(),
 "no_rollback":lambda d:d["policy"].update(full_rollback_on_failure=False),
 "world_save_written":lambda d:d["policy"].update(no_save_reads_or_writes=False),
 "disable_checkpoint_check":lambda d:d["policy"].update(center_requires_verified_region_ownership=False),
 "miss_money":lambda d:d["covered_resources"].remove("money"),
 "miss_HMs":lambda d:d["covered_resources"].remove("regional_HMs"),
 "miss_specials":lambda d:d["covered_resources"].remove("restricted_legendaries_mythicals_UB_paradox"),
 "drop_faultpoint":lambda d:d["failure_points"]["travel"].pop(),
 "cross_module_ref":lambda d:d["sources"].update(travel="data/regions/other-game.json"),
 "missing_limitations":lambda d:d.update(limitations=[]),
 "missing_policies":lambda d:d["policy"].pop("blocked_sinnoh_unova"),
 "extra_unknown":lambda d:d.update(native_support_proven=True),
}
for _name,_edit in _BAD_CONTRACT.items():
    def _invalid(self,mutation=_edit):
        self.bad_claim(mutation)
    setattr(UnovaG083Tests,"test_reject_claim_"+_name,_invalid)

_BAD_WORLD={
 "native_scope":lambda s:s.update(scope="NATIVE_SAVE"),
 "wrong_version":lambda s:s.update(version=2),
 "native_region":lambda s:s.update(current="UNOVA"),
 "wrong_active":lambda s:s["travel_state"].update(current="HOENN"),
 "invalid_checkpoint_unova":lambda s:s["checkpoints"].update(UNOVA="FIXTURE_UNOVA_FAKE_CENTER"),
 "invalid_checkpoint_kanto":lambda s:s["checkpoints"].update(KANTO="FIXTURE_JOHTO_CHERRYGROVE_CENTER"),
 "remove_sinnoh_checkpoint":lambda s:s["checkpoints"].pop("SINNOH"),
 "missing_shared":lambda s:s.pop("shared"),
 "negative_money":lambda s:s["shared"].update(money=-1),
 "boolean_money":lambda s:s["shared"].update(money=True),
 "duplicate_TM":lambda s:s["shared"].update(tm_ledger=["FIXTURE_TM_GLOBAL","FIXTURE_TM_GLOBAL"]),
 "real_save_name":lambda s:s["shared"]["global_boxes"].update(**{"File A.rxdata":"FIXTURE_MON"}),
 "real_pokemon_id":lambda s:s["shared"]["global_boxes"].update(FIXTURE_X="PIKACHU"),
 "foreign_g07_scope":lambda s:s["protected"].pop("saves"),
 "native_g07_path":lambda s:s["protected"]["saves"].update({"Game.exe":"FIXTURE_X"}),
 "unknown_region_proof":lambda s:s["travel_state"]["install_proofs"].update(UNOVA=True),
 "missing_hm":lambda s:s["travel_state"]["bag_state"].update(scope="real-save"),
 "native_coord":lambda s:s["travel_state"].update(position="518"),
 "unsafe_decades_return":lambda s:s["travel_state"].update(decades_return="FIXTURE_DECADES_INTRO"),
 "unverified_destination":lambda s:s["travel_state"]["arrival_proofs"].update(HOENN="yes"),
}
for _name,_edit in _BAD_WORLD.items():
    def _bad(self,mutation=_edit):
        self.bad_world(mutation)
    setattr(UnovaG083Tests,"test_reject_world_"+_name,_bad)

for _region in reg.BLOCKED:
    for _origin in travel.ROUTABLE:
        def _blocked(self,dest=_region,src=_origin):
            world=self.at(src)
            original=copy.deepcopy(world)
            out=self.step(world,dest)
            self.assertEqual(out["status"],"DESTINATION_NOT_INSTALLED_OR_SUPPORTED")
            self.assertEqual(out["state"],original)
            self.assertEqual(world,original)
        setattr(UnovaG083Tests,"test_blocked_"+_origin+"_to_"+_region,_blocked)

for _point in travel.FAIL_POINTS:
    for _origin,_dest in (("KANTO","HOENN"),("HOENN","JOHTO")):
        def _failure(self,f=_point,source=_origin,destination=_dest):
            world=self.at(source)
            original=copy.deepcopy(world)
            out=self.step(world,destination,fail_at=f)
            self.assertEqual(out["status"],"SIMULATED_TRANSFER_FAILED_ROLLED_BACK")
            self.assertEqual(out["state"],original)
            self.assertEqual(world,original)
        setattr(UnovaG083Tests,"test_travel_rollback_"+_origin+"_"+_point,_failure)

for _region in travel.ROUTABLE:
    for _point in faint.FAULTS:
        def _blackout(self,region=_region,point=_point):
            result=reg.blackout_step(self.world(),region,self.r,fail_at=point)
            self.assertEqual(result["status"],"SYNTHETIC_FAILURE_ROLLED_BACK")
            self.assertEqual(result["before"],result["after"])
        setattr(UnovaG083Tests,"test_blackout_rollback_"+_region+"_"+_point,_blackout)

for _namespace in g73.PROTECTED:
    def _cas(self,scope=_namespace):
        state=self.world()
        observed=copy.deepcopy(state)
        key=next(iter(observed["protected"][scope]))
        observed["protected"][scope][key]="FIXTURE_CONCURRENT_EDIT"
        out=self.step(state,"HOENN",observed_after_staging=observed)
        self.assertEqual(out["status"],"CONFLICT_WORLD_CAS_CONCURRENT_EDIT")
        self.assertEqual(out["state"],state)
    setattr(UnovaG083Tests,"test_concurrent_protected_"+_namespace,_cas)

for _point in g73.FAULTS:
    for _profile in g74.PLATFORMS:
        def _rollback(self,point=_point,profile=_profile):
            p,m,old,new=g73.multi_file_fixture()
            state=g73.base_fixture(p,m,old)
            req=g74.fixture_request(profile,p,state)
            out=g74.preview(profile,req,p,m,old,new,state,fail_at=point)
            self.assertEqual(out["transaction_status"],"SIMULATED_ROLLBACK_COMPLETE")
            self.assertEqual(out["state"],state)
            self.assertFalse(out["install_allowed"])
        setattr(UnovaG083Tests,"test_update_rollback_"+_profile+"_"+_point,_rollback)

if __name__=="__main__":
    unittest.main()
