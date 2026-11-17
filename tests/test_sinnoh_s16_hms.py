"""S16: negative tests for HM pickup receipts, region/field isolation."""
from __future__ import annotations
import copy,json,sys,subprocess,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_s16_hms as s16

class SinnohS16Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        d={k:p.read_text("utf-8") for k,p in s16.FILES.items()}
        cls.data={k:json.loads(d[k]) for k in ("s16","ch11","s15","teams","registry")}
        cls.text={k:d[k] for k in ("campaign","regions","policy","travel","gyms_adapter","adapter")}
    def check(self,**kwargs):
        z={**copy.deepcopy(self.data),**self.text,**kwargs}
        return s16.audit(*[z[k] for k in ("s16","ch11","s15","teams","registry","campaign","regions","policy","travel","gyms_adapter","adapter")])
    def blocked(self,key,val,index=None):
        v=copy.deepcopy(self.data["s16"])
        if index is None:v[key]=val
        else:v["hms"][index][key]=val
        with self.assertRaisesRegex(ValueError,"SINNOH_S16_BLOCKED"):self.check(s16=v)
    def test_01_all_eight_pairs_ch11_order(self):
        d=self.check()
        self.assertEqual(d["hm_contracts"],8)
        self.assertFalse(d["can_install"])
        self.assertEqual([h["badge"] for h in self.data["s16"]["hms"]],
                         ["COAL","FOREST","COBBLE","RELIC","FEN","MINE","ICICLE","BEACON"])
    def test_02_read_only_cli(self):
        r=subprocess.run([sys.executable,str(s16.ROOT/"scripts/regions/audit_sinnoh_s16_hms.py")],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("SINNOH_S16_LOCAL_HM_CONTRACT_OK_OFFLINE",r.stdout)
    def test_03_missing_row(self):
        v=copy.deepcopy(self.data["s16"]);v["hms"].pop()
        with self.assertRaisesRegex(ValueError,"SINNOH_S16_BLOCKED"):self.check(s16=v)
    def test_04_swap_hm_pair(self):
        v=copy.deepcopy(self.data["s16"]);v["hms"][2],v["hms"][3]=v["hms"][3],v["hms"][2]
        with self.assertRaisesRegex(ValueError,"SINNOH_S16_BLOCKED"):self.check(s16=v)
    def test_05_foreign_hm(self):self.blocked("hm_item","HM01",2)
    def test_06_foreign_badge(self):self.blocked("badge","BOULDER",0)
    def test_07_forged_map_id(self):self.blocked("physical_map_id",900,0)
    def test_08_forged_event_id(self):self.blocked("physical_event_id",99,0)
    def test_09_forged_callback(self):self.blocked("verified_source_id","fake",0)
    def test_10_forged_source_hash(self):self.blocked("source_hash_sha256","a"*64,0)
    def test_11_forged_pickup(self):self.blocked("pickup_event_verified",True,0)
    def test_12_forged_receipt(self):self.blocked("local_receipt_verified",True,0)
    def test_13_forged_enabled(self):self.blocked("enabled",True,0)
    def test_14_forged_compilation(self):self.blocked("handler_compiled",True,0)
    def test_15_forged_native_qa(self):
        for key in ("can_grant_hm","native_qa_approved","game_exe_tested","joiplay_tested","approved_for_install","can_change_native_saves"):
            with self.subTest(key=key):self.blocked(key,True)
    def test_16_fake_sources_registry(self):self.blocked("verified_native_sources",{"ROCK_SMASH":"bad"})
    def test_17_fake_pickup_counter(self):self.blocked("native_pickups_installed",1)
    def test_18_no_global_hook(self):
        with self.assertRaisesRegex(ValueError,"SINNOH_S16_BLOCKED"):
            self.check(adapter=self.text["adapter"]+"\nEventHandlers.add(:fake,:fake,proc {})\n")
    def test_19_runtime_proof_required(self):
        # CH11 runs first and is expected to reject a removed native pickup guard.
        with self.assertRaisesRegex(ValueError,r"SINNOH CH11"):
            self.check(regions=self.text["regions"].replace("pickup_confirmed == true","pickup_confirmed != false"))
    def test_20_no_cross_region_field_bypass(self):
        # Preserve CH11's earlier, stricter rejection of cross-region access.
        with self.assertRaisesRegex(ValueError,r"SINNOH CH11"):
            self.check(policy=self.text["policy"].replace('local_proof = current["current"] == "SINNOH"',"local_proof = false"))
    def test_21_no_key_item_cross_region(self):
        with self.assertRaisesRegex(ValueError,"SINNOH_S16_BLOCKED"):
            self.check(travel=self.text["travel"].replace("def self.stage_local_bag(state, destination)","def self.stage_shared_bag(state, destination)"))
    def test_22_corrupt_ch11(self):
        x=copy.deepcopy(self.data["ch11"]);x["rules"][0]["hm_item"]="HM01"
        with self.assertRaisesRegex(ValueError,"SINNOH CH11"):self.check(ch11=x)
    def test_23_corrupt_s15(self):
        x=copy.deepcopy(self.data["s15"]);x["gyms"][0]["hm_item"]="HM01"
        with self.assertRaisesRegex(ValueError,"SINNOH_S15_BLOCKED"):self.check(s15=x)
    def test_24_progress_code_only(self):
        p=json.loads((ROOT/"data/regions/sinnoh-progress.json").read_text("utf-8"))
        self.assertEqual(p["development"]["done"],28)
        self.assertEqual(p["development"]["partial"],4)
        self.assertEqual(p["development"]["pending"],0)
        self.assertEqual(p["development"]["percent_complete"],87)
        self.assertEqual(next(x["status"] for x in p["tasks"] if x["id"]=="S16"),"done")
        self.assertEqual(p["phase_gates"]["playable_in_game_executable"],0)
        self.assertEqual(p["phase_gates"]["fully_tested_native"],0)

if __name__=="__main__":unittest.main()
