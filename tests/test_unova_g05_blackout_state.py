"""G05.4: deterministic regional Center/blackout and shared state regression."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g05_blackout_state as mod

class UnovaG054Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data,cls.registry,cls.report=mod.load_project()
        cls.sources=cls.data["sources"]
        cls.prior=[mod.load(ROOT,cls.sources[x]) for x in ("items","specials","travel")]
        cls.board=mod.load(ROOT,cls.sources["tracker"])
        cls.ruby={x:mod.read(ROOT,cls.sources[x]) for x in mod.RUBY}

    def state(self):
        return mod.fixture(self.registry)

    def run_blackout(self,state=None,**kw):
        return mod.blackout(self.state() if state is None else state,self.registry,**kw)

    def assert_bad(self,mutator):
        state=self.state();mutator(state)
        with self.assertRaises(ValueError):
            mod.validate_state(state,self.registry)

    def assert_bad_catalog(self,mutator):
        doc=copy.deepcopy(self.data)
        mutator(doc)
        with self.assertRaises(ValueError):
            mod.validate_catalog(doc,self.registry,self.prior,self.board,self.ruby)

    def test_001_phase(self):
        self.assertEqual(self.report["phase"],"G05.4")
    def test_002_four_supported_regions(self):
        self.assertEqual(tuple(self.data["runtime_regions"]),mod.REGIONS)
    def test_003_unova_planned(self):
        self.assertEqual(self.registry["regions"]["UNOVA"]["status"],"planned")
    def test_004_source_evidence_null(self):
        self.assertTrue(all(v is None for v in self.data["native_evidence"].values()))
    def test_005_no_native_centers_installed(self):
        self.assertFalse(self.data["native_center_installed"])
    def test_006_no_game_exe_claim(self):
        self.assertFalse(self.data["game_exe_tested"])
    def test_007_no_joiplay_claim(self):
        self.assertFalse(self.data["android_tested"])
    def test_008_no_save_mutation(self):
        self.assertFalse(self.data["native_saves_modified"])
    def test_009_no_native_badge_mutation(self):
        self.assertFalse(self.data["native_badges_modified"])
    def test_010_no_installer(self):
        self.assertFalse(self.data["can_install"])
    def test_011_technical_bar_remains_zero(self):
        self.assertEqual(self.board["native_technical_bar"]["completed"],0)
    def test_012_playable_bar_remains_zero(self):
        self.assertEqual(self.board["native_playable_bar"]["completed"],0)
    def test_013_ruby_hook_before_native(self):
        self.assertIn("BlueRegionalRespawn.before_blackout!",self.ruby["respawn"])
    def test_014_source_real_center_gate(self):
        self.assertIn("def self.real_center?(region, id)",self.ruby["respawn"])
    def test_015_source_native_engine_super(self):
        self.assertIn("def pbStartOver(*args, &block)",self.ruby["respawn"])
    def test_016_ruby_no_valid_candidate_risk(self):
        self.assertIn("return unless valid?(candidate)",self.ruby["respawn"])
        self.assertTrue(self.data["policy"]["native_no_fallback_may_leave_stale_checkpoint"])
    def test_017_ruby_owner_bypass_risk(self):
        self.assertIn("return if valid?(native) && (owner == current ||",self.ruby["respawn"])
        self.assertTrue(self.data["policy"]["native_owner_only_check_may_accept_foreign_point"])
    def test_018_source_money_metadata(self):
        self.assertIn("$player.money",self.ruby["economy"])
    def test_019_fixture_is_synthetic(self):
        self.assertEqual(self.state()["scope"],mod.SIM["scope"])
    def test_020_fixture_valid(self):
        self.assertEqual(mod.validate_state(self.state(),self.registry)["current"],"KANTO")
    def test_021_stale_decades_checkpoint_corrected(self):
        result=self.run_blackout()
        self.assertEqual(result["checkpoint_source"],"REMEMBERED_LOCAL_CENTER")
        self.assertEqual(result["fixture"]["native_checkpoint"],"FIXTURE_KANTO_CERULEAN_CENTER")
    def test_022_owner_corrected_to_current(self):
        self.assertEqual(self.run_blackout()["fixture"]["checkpoint_owner"],"KANTO")
    def test_023_blackout_position_corrected(self):
        self.assertEqual(self.run_blackout()["fixture"]["position"],"FIXTURE_KANTO_CERULEAN_CENTER")
    def test_024_native_checkpoint_local_preferred(self):
        s=self.state();s["native_checkpoint"]="FIXTURE_KANTO_VIRIDIAN_CENTER"
        s["checkpoint_owner"]="KANTO"
        self.assertEqual(self.run_blackout(s)["checkpoint_source"],"CURRENT_LOCAL_CHECKPOINT")
    def test_025_owner_unknown_but_local_checkpoint_preferred(self):
        s=self.state();s["native_checkpoint"]="FIXTURE_KANTO_VIRIDIAN_CENTER"
        s["checkpoint_owner"]=None
        self.assertEqual(self.run_blackout(s)["checkpoint_source"],"CURRENT_LOCAL_CHECKPOINT")
    def test_026_owner_from_foreign_region_rejected_even_when_center_local(self):
        s=self.state();s["native_checkpoint"]="FIXTURE_KANTO_VIRIDIAN_CENTER"
        s["checkpoint_owner"]="DECADES"
        self.assertEqual(self.run_blackout(s)["checkpoint_source"],"REMEMBERED_LOCAL_CENTER")
    def test_027_unsafe_forged_owner_does_not_authorize_foreign_map(self):
        s=self.state();s["checkpoint_owner"]="KANTO"
        self.assertEqual(self.run_blackout(s)["checkpoint_source"],"REMEMBERED_LOCAL_CENTER")
    def test_028_remembered_missing_uses_fallback(self):
        s=self.state();s["remembered"].pop("KANTO")
        self.assertEqual(self.run_blackout(s)["checkpoint_source"],"VERIFIED_LOCAL_FALLBACK")
    def test_029_remembered_invalid_uses_fallback(self):
        s=self.state();s["remembered"]["KANTO"]="FIXTURE_FAKE_CENTER"
        self.assertEqual(self.run_blackout(s)["checkpoint_source"],"VERIFIED_LOCAL_FALLBACK")
    def test_030_no_safe_center_blocks(self):
        s=self.state();s["verified_centers"]["KANTO"]=[]
        s["fallbacks"]["KANTO"]=None
        self.assertEqual(self.run_blackout(s)["status"],"BLOCKED_NO_VERIFIED_LOCAL_CENTER")
    def test_031_no_safe_center_preserves_checkpoint(self):
        s=self.state();s["verified_centers"]["KANTO"]=[]
        s["fallbacks"]["KANTO"]=None
        self.assertEqual(self.run_blackout(s)["fixture"],s)
    def test_032_no_safe_center_does_not_call_engine(self):
        s=self.state();s["verified_centers"]["KANTO"]=[]
        s["fallbacks"]["KANTO"]=None
        self.assertFalse(self.run_blackout(s)["native_engine_invoked"])
    def test_033_cross_region_no_fallback_into_decades(self):
        s=self.state();s["verified_centers"]["KANTO"]=[]
        s["fallbacks"]["KANTO"]=None
        self.assertNotEqual(self.run_blackout(s)["fixture"]["native_checkpoint"],
                            "FIXTURE_KANTO_VIRIDIAN_CENTER")
    def test_034_blackout_in_unova_not_approved(self):
        s=self.state();s["current"]="UNOVA"
        s["bag"]["current"]="UNOVA";s["party"]["current"]="UNOVA"
        self.assertEqual(self.run_blackout(s)["status"],"PLANNED_REGION_RESPAWN_UNVERIFIED")
    def test_035_unova_does_not_write_native_center(self):
        s=self.state();s["current"]="UNOVA"
        s["bag"]["current"]="UNOVA";s["party"]["current"]="UNOVA"
        self.assertFalse(self.run_blackout(s)["native_engine_invoked"])
    def test_036_blackout_heals_once_in_fixture(self):
        before=self.state();after=self.run_blackout(before)["fixture"]
        self.assertEqual(after["heals"],before["heals"]+1)
    def test_037_blackout_engine_called_once_in_fixture(self):
        before=self.state();after=self.run_blackout(before)["fixture"]
        self.assertEqual(after["blackouts"],before["blackouts"]+1)
    def test_038_native_engine_not_actually_called(self):
        self.assertFalse(self.run_blackout()["native_engine_invoked"])
    def test_039_blackout_no_source_mutation(self):
        src=self.state();copy0=copy.deepcopy(src)
        self.run_blackout(src)
        self.assertEqual(src,copy0)
    def test_040_two_blackouts_mean_two_fixture_calls(self):
        base=self.state();once=self.run_blackout(base)["fixture"]
        twice=self.run_blackout(once)["fixture"]
        self.assertEqual(twice["heals"],base["heals"]+2)
        self.assertEqual(twice["blackouts"],base["blackouts"]+2)
    def test_041_legacy_decades_has_no_snapshot_adapter(self):
        self.assertTrue(self.data["policy"]["legacy_decades_does_not_migrate"])
    def test_042_current_center_remembered(self):
        s=self.state();s["native_checkpoint"]="FIXTURE_KANTO_CERULEAN_CENTER"
        s["nurse_map"]=s["native_checkpoint"]
        result=mod.remember(s,self.registry)
        self.assertEqual(result["status"],"SYNTHETIC_LOCAL_CENTER_RECORDED")
        self.assertEqual(result["fixture"]["checkpoint_owner"],"KANTO")
    def test_043_nurse_does_not_overwrite_foreign_region_memory(self):
        s=self.state();old=s["remembered"]["DECADES"]
        s["native_checkpoint"]="FIXTURE_KANTO_CERULEAN_CENTER";s["nurse_map"]=s["native_checkpoint"]
        self.assertEqual(mod.remember(s,self.registry)["fixture"]["remembered"]["DECADES"],old)
    def test_044_fake_nurse_on_route_does_not_remember(self):
        s=self.state();s["nurse_map"]="FIXTURE_KANTO_ROUTE"
        self.assertEqual(mod.remember(s,self.registry)["status"],"UNVERIFIED_NURSE_NO_RECORD")
    def test_045_nurse_in_other_region_does_not_remember(self):
        s=self.state();s["nurse_map"]="FIXTURE_DECADES_CHERRYHILL_CENTER"
        self.assertEqual(mod.remember(s,self.registry)["status"],"UNVERIFIED_NURSE_NO_RECORD")
    def test_046_nurse_does_not_edit_input(self):
        s=self.state();before=copy.deepcopy(s)
        mod.remember(s,self.registry)
        self.assertEqual(s,before)
    def test_047_no_double_heal_with_center_registration(self):
        s=self.state();s["native_checkpoint"]="FIXTURE_KANTO_CERULEAN_CENTER"
        s["nurse_map"]=s["native_checkpoint"]
        self.assertEqual(mod.remember(s,self.registry)["fixture"]["heals"],s["heals"])
    def test_048_no_center_record_in_unova(self):
        s=self.state();s["current"]="UNOVA"
        s["bag"]["current"]="UNOVA";s["party"]["current"]="UNOVA"
        self.assertEqual(mod.remember(s,self.registry)["status"],"UNVERIFIED_NURSE_NO_RECORD")
    def test_049_rollback_on_after_checkpoint(self):
        st=self.state();res=self.run_blackout(st,fail_at="after_checkpoint")
        self.assertEqual(res["status"],"SYNTHETIC_FAILURE_ROLLED_BACK")
        self.assertEqual(res["fixture"],st)
    def test_050_rollback_on_after_owner(self):
        st=self.state();self.assertEqual(self.run_blackout(st,fail_at="after_owner")["fixture"],st)
    def test_051_rollback_on_after_heal(self):
        st=self.state();self.assertEqual(self.run_blackout(st,fail_at="after_heal")["fixture"],st)
    def test_052_rollback_on_after_transfer(self):
        st=self.state();self.assertEqual(self.run_blackout(st,fail_at="after_transfer")["fixture"],st)
    def test_053_rollback_preserves_source(self):
        st=self.state();copy0=copy.deepcopy(st)
        self.run_blackout(st,fail_at="after_transfer")
        self.assertEqual(st,copy0)
    def test_054_failed_blackout_does_not_call_native(self):
        self.assertFalse(self.run_blackout(fail_at="after_transfer")["native_engine_invoked"])
    def test_055_unknown_failure_name_blocked(self):
        with self.assertRaises(ValueError):self.run_blackout(fail_at="delete_real_save")
    def test_056_no_native_money_penalty_implied(self):
        self.assertTrue(self.data["simulation"]["no_real_economy_logic"])
    def test_057_native_respawn_ruby_unchanged_by_contract(self):
        self.assertIn("Object.prepend(NativeCheckpoints)",self.ruby["respawn"])
    def test_058_demo_corrected_foreign_center(self):
        self.assertEqual(mod.demo(self.data,self.registry)["source"],"REMEMBERED_LOCAL_CENTER")
    def test_059_demo_records_native_risk(self):
        self.assertEqual(mod.demo(self.data,self.registry)["no_safe_center"],"BLOCKED_NO_VERIFIED_LOCAL_CENTER")
    def test_060_demo_blocks_unova(self):
        self.assertEqual(mod.demo(self.data,self.registry)["unova_not_native"],"PLANNED_REGION_RESPAWN_UNVERIFIED")
    def test_061_demo_rollback(self):
        self.assertTrue(mod.demo(self.data,self.registry)["rollback_preserved"])
    def test_062_demo_money_and_boxes_preserved(self):
        d=mod.demo(self.data,self.registry)
        self.assertTrue(d["money_preserved"] and d["coins_preserved"] and d["boxes_preserved"])
    def test_063_cli_check(self):
        ret=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g05_blackout_state.py"),"--check"],
               text=True,capture_output=True)
        self.assertEqual(ret.returncode,0,ret.stdout+ret.stderr)
        self.assertEqual(json.loads(ret.stdout)["native_unova_centers"],0)
    def test_064_cli_demo(self):
        ret=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g05_blackout_state.py"),"--simulate-demo"],
               text=True,capture_output=True)
        self.assertEqual(ret.returncode,0,ret.stdout+ret.stderr)
        self.assertTrue(json.loads(ret.stdout)["healed_exactly_once"])

# Preserve EVERY shared datum, including both currency balances, without
# duplicating 17 almost identical unittest functions.
_PRESERVED=("money","coins","bag","party","boxes","native_badges",
    "leagues","field_events","mechanics_by_region","active_mechanics",
    "current","version","scope","remembered","verified_centers","fallbacks")
for _name in _PRESERVED:
    def _test(self,field=_name):
        src=self.state()
        dst=self.run_blackout(src)["fixture"]
        self.assertEqual(dst[field],src[field])
    setattr(UnovaG054Tests,"test_preserve_"+_name,_test)

_NEGATIVE={
 "wrong_scope":lambda s:s.update(scope="NATIVE_SAVE"),
 "wrong_version":lambda s:s.update(version=2),
 "unknown_region":lambda s:s.update(current="UNKNOWN"),
 "native_mapid_position":lambda s:s.update(position=77),
 "native_mapid_checkpoint":lambda s:s.update(native_checkpoint=518),
 "foreign_owner":lambda s:s.update(checkpoint_owner="UNKNOWN"),
 "missing_verified_set":lambda s:s["verified_centers"].pop("KANTO"),
 "invented_unova_map":lambda s:s["verified_centers"].update(UNOVA=["FIXTURE_UNOVA_CENTER"]),
 "same_center_two_regions":lambda s:s["verified_centers"]["JOHTO"].append("FIXTURE_KANTO_VIRIDIAN_CENTER"),
 "invalid_fallback":lambda s:s["fallbacks"].update(KANTO="FIXTURE_NOT_VERIFIED"),
 "foreign_fallback":lambda s:s["fallbacks"].update(KANTO="FIXTURE_DECADES_CHERRYHILL_CENTER"),
 "real_nurse_map":lambda s:s.update(nurse_map="Map077"),
 "unknown_remembered_region":lambda s:s["remembered"].update(UNOVA="FIXTURE_FAKE"),
 "wrong_money_type":lambda s:s.update(money=True),
 "negative_money":lambda s:s.update(money=-1),
 "negative_coins":lambda s:s.update(coins=-1),
 "float_coins":lambda s:s.update(coins=12.0),
 "negative_heals":lambda s:s.update(heals=-1),
 "bad_blackout_counter":lambda s:s.update(blackouts="2"),
 "bag_region_mismatch":lambda s:s["bag"].update(current="HOENN"),
 "party_region_mismatch":lambda s:s["party"].update(current="JOHTO"),
 "extra_pokemon_party_box":lambda s:s["boxes"].update(FIXTURE_BOX_TEST="FIXTURE_NORMAL"),
 "duplicate_boxed_pokemon":lambda s:s["boxes"].update(FIXTURE_BOX_TEST="FIXTURE_BOXED_MON"),
 "real_box_slot":lambda s:s["boxes"].update(BOX1="FIXTURE_OTHER"),
 "native_badge_int":lambda s:s.update(native_badges=[1]),
 "duplicate_league":lambda s:s["leagues"].append("KANTO"),
 "unknown_league":lambda s:s["leagues"].append("MOON"),
 "unknown_field_region":lambda s:s["field_events"].update(UNRELEASED=["FIXTURE_X"]),
 "non_synthetic_event":lambda s:s["field_events"]["KANTO"].append("CUT"),
 "nonboolean_mechanics":lambda s:s["active_mechanics"].update(FIXTURE_DYNAMAX=1),
 "foreign_mechanics_region":lambda s:s["mechanics_by_region"].update(UNKNOWN={}),
 "unknown_root_field":lambda s:s.update(native_save_path="/app/game"),
}
for _name,_edit in _NEGATIVE.items():
    def _test(self,change=_edit):
        self.assert_bad(change)
    setattr(UnovaG054Tests,"test_invalid_"+_name,_test)

_CONTRACT_ATTACKS={
 "fake_installed":lambda d:d.update(native_center_installed=True),
 "fake_game_qa":lambda d:d.update(game_exe_tested=True),
 "fake_android_qa":lambda d:d.update(android_tested=True),
 "fake_unova_mapid":lambda d:d["native_evidence"].update(unova_center_mapids=[518]),
 "fake_native_save_edit":lambda d:d.update(native_saves_modified=True),
 "misstate_rollback":lambda d:d["policy"].update(rollback_failure_before_commit=False),
 "hide_native_fallback_risk":lambda d:d["policy"].update(native_no_fallback_may_leave_stale_checkpoint=False),
 "hide_native_owner_risk":lambda d:d["policy"].update(native_owner_only_check_may_accept_foreign_point=False),
 "fake_unova_enabled":lambda d:d.update(can_install=True),
 "false_region_allowlist":lambda d:d["runtime_regions"].append("UNOVA"),
}
for _name,_edit in _CONTRACT_ATTACKS.items():
    def _test(self,change=_edit):
        self.assert_bad_catalog(change)
    setattr(UnovaG054Tests,"test_contract_reject_"+_name,_test)

if __name__=="__main__":
    unittest.main()
