"""S15: contracts and negative tests for 8 Sinnoh Gyms. No Game.exe."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_s15_gyms as s15

class SinnohS15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=json.loads(s15.GYMS.read_text("utf-8"))
        cls.teams=json.loads(s15.TRAINERS.read_text("utf-8"))
        cls.hm=json.loads(s15.BADGES.read_text("utf-8"))
        cls.registry=json.loads(s15.REGISTRY.read_text("utf-8"))
        cls.campaign=s15.CAMPAIGN.read_text("utf-8")
        cls.runtime=s15.REGIONS.read_text("utf-8")
        cls.adapter=s15.RUBY.read_text("utf-8")

    def check(self,spec=None,teams=None,hm=None,registry=None,campaign=None,
              runtime=None,adapter=None):
        return s15.audit(
            copy.deepcopy(self.spec if spec is None else spec),
            copy.deepcopy(self.teams if teams is None else teams),
            copy.deepcopy(self.hm if hm is None else hm),
            copy.deepcopy(self.registry if registry is None else registry),
            self.campaign if campaign is None else campaign,
            self.runtime if runtime is None else runtime,
            self.adapter if adapter is None else adapter)

    def fail_spec(self,key,val,index=None):
        obj=copy.deepcopy(self.spec)
        if index is None: obj[key]=val
        else: obj["gyms"][index][key]=val
        with self.assertRaisesRegex(ValueError,"SINNOH_S15_BLOCKED"):
            self.check(spec=obj)

    def test_01_eight_gym_order_and_ch11_hms(self):
        result=self.check()
        self.assertEqual(result["gyms"],8)
        self.assertEqual(result["historical_order"],list(s15.ORDER))
        self.assertFalse(result["can_install"])
        self.assertEqual((self.spec["gyms"][2]["badge"],self.spec["gyms"][3]["badge"]),("RELIC","COBBLE"))
        self.assertEqual([g["badge"] for g in self.spec["gyms"]],
                         ["COAL","FOREST","RELIC","COBBLE","FEN","MINE","ICICLE","BEACON"])

    def test_02_cli(self):
        r=subprocess.run([sys.executable,str(s15.ROOT/"scripts/regions/audit_sinnoh_s15_gyms.py")],
                         capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("SINNOH_S15_GYMS_OK_OFFLINE_ONLY",r.stdout)

    def test_03_missing_gym(self):
        v=copy.deepcopy(self.spec);v["gyms"].pop()
        with self.assertRaisesRegex(ValueError,"SINNOH_S15_BLOCKED"):self.check(spec=v)

    def test_04_reordered_gym(self):
        v=copy.deepcopy(self.spec);v["gyms"][2],v["gyms"][3]=v["gyms"][3],v["gyms"][2]
        with self.assertRaisesRegex(ValueError,"SINNOH_S15_BLOCKED"):self.check(spec=v)

    def test_05_wrong_badge(self):self.fail_spec("badge","BOULDER",2)
    def test_06_wrong_hm(self):self.fail_spec("hm_item","HM01",2)
    def test_07_wrong_prior_badges(self):self.fail_spec("prerequisite_badges",[],3)
    def test_08_fake_map_id(self):self.fail_spec("physical_map_id",800,0)
    def test_09_fake_event_id(self):self.fail_spec("physical_event_id",1,0)
    def test_10_fake_pbs(self):self.fail_spec("trainer_type","BLUE_SINNOH_ROARK",0)
    def test_11_fake_source_hash(self):self.fail_spec("source_sha256","0"*64,0)
    def test_12_fake_npc(self):self.fail_spec("physical_event_installed",True,0)
    def test_13_fake_battle_win(self):self.fail_spec("battle_victory_verified",True,0)
    def test_14_fake_badge_award(self):self.fail_spec("badge_award_verified",True,0)
    def test_15_fake_native_source(self):self.fail_spec("verified_native_sources",{"ROARK":"test"})
    def test_16_fake_gameplay(self):
        for key in ("battles_playable","approved_for_install","native_badges_awardable",
                    "native_pbs_compiled","game_exe_tested","joiplay_tested",
                    "native_qa_approved","can_write_game"):
            with self.subTest(key=key):self.fail_spec(key,True)

    def test_17_legacy_hm_catalog_untouched(self):
        x=copy.deepcopy(self.hm)
        x["rules"][2]["badge"]="RELIC"
        with self.assertRaisesRegex(ValueError,"SINNOH_S15_BLOCKED"):self.check(hm=x)

    def test_18_roster_fraud(self):
        x=copy.deepcopy(self.teams)
        x["trainers"][2]["badge"]="COBBLE"
        with self.assertRaisesRegex(ValueError,"SINNOH_S15_BLOCKED"):self.check(teams=x)

    def test_19_playable_registry_fraud(self):
        x=copy.deepcopy(self.registry)
        x["regions"]["SINNOH"]["status"]="playable"
        with self.assertRaisesRegex(ValueError,"SINNOH_S15_BLOCKED"):self.check(registry=x)

    def test_20_no_global_hook_or_native_badges(self):
        with self.assertRaisesRegex(ValueError,"SINNOH_S15_BLOCKED"):
            self.check(adapter=self.adapter+"\nEventHandlers.add(:on_start_battle,:fake,proc {})\n")
        with self.assertRaisesRegex(ValueError,"SINNOH_S15_BLOCKED"):
            self.check(runtime=self.runtime.replace("def self.award(state, region, key)","def bad_award"))

    def test_21_balance_does_not_drift(self):
        with self.assertRaisesRegex(ValueError,"SINNOH_S15_BLOCKED"):
            self.check(campaign=self.campaign.replace("master? ? 90 : 70","master? ? 100 : 100"))

    def test_22_progress_only_code(self):
        p=json.loads((ROOT/"data/regions/sinnoh-progress.json").read_text("utf-8"))
        # S15 remains complete as later S16 work progresses.
        self.assertGreaterEqual(p["development"]["done"],27)
        self.assertEqual(p["development"]["done"],
                         sum(x["status"]=="done" for x in p["tasks"]))
        self.assertEqual(p["development"]["percent_complete"],
                         100*p["development"]["done"]//p["development"]["total"])
        self.assertEqual(next(t["status"] for t in p["tasks"] if t["id"]=="S15"),"done")
        self.assertIn(next(t["status"] for t in p["tasks"] if t["id"]=="S16"),
                      ("pending","done"))
        self.assertEqual(p["phase_gates"]["playable_in_game_executable"],0)
        self.assertEqual(p["phase_gates"]["fully_tested_native"],0)

if __name__=="__main__":unittest.main()
