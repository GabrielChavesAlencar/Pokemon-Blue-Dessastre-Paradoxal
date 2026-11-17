"""S13: genuine CH06 integration, no fictional events, badges or MapIDs."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_s13_intro as s13

class SinnohS13Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=json.loads(s13.MANIFEST.read_text("utf-8"))
        cls.events=json.loads(s13.TEMPLATE.read_text("utf-8"))
        cls.schema=json.loads(s13.SCHEMA.read_text("utf-8"))
        cls.pilot=s13.PILOT.read_text("utf-8")
        cls.bridge=s13.BRIDGE.read_text("utf-8")

    def check(self,m=None,events=None,pilot=None,bridge=None):
        return s13.audit(copy.deepcopy(self.m if m is None else m),
                         copy.deepcopy(self.events if events is None else events),
                         copy.deepcopy(self.schema),
                         self.pilot if pilot is None else pilot,
                         self.bridge if bridge is None else bridge)

    def corrupt(self,key,value,index=None):
        m=copy.deepcopy(self.m)
        if index is None:m[key]=value
        else:m["steps"][index][key]=value
        with self.assertRaisesRegex(ValueError,"SINNOH_S13_BLOCKED"):
            self.check(m=m)

    def test_01_reference_checkpoints_and_trio(self):
        r=self.check()
        self.assertEqual(r["story_checkpoints"],6)
        self.assertFalse(r["can_install"])
        self.assertEqual([x["flag"] for x in self.m["steps"]],
                         s13.FLAGS)
        balls=self.m["steps"][3]["physical_balls"]
        self.assertEqual({x["species"] for x in balls},
                         {"TURTWIG","CHIMCHAR","PIPLUP"})

    def test_02_cli(self):
        p=subprocess.run([sys.executable,str(s13.ROOT/"scripts/regions/audit_sinnoh_s13_intro.py")],
                         capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("SINNOH_S13_INTRO_CONTRACT_OK_OFFLINE",p.stdout)

    def test_03_out_of_order(self):self.corrupt("flag","pokedex_received",2)
    def test_04_forged_map_id(self):self.corrupt("native_map_id",800,0)
    def test_05_forged_event_id(self):self.corrupt("native_event_id",22,0)
    def test_06_forged_barry_battle(self):self.corrupt("native_callback_verified",True,4)
    def test_07_forged_player_interaction(self):self.corrupt("player_interaction_verified",True,0)
    def test_08_forged_game_exe(self):self.corrupt("game_exe_verified",True,5)
    def test_09_forged_android(self):self.corrupt("joiplay_verified",True,5)
    def test_10_forged_barry_pbs(self):self.corrupt("native_barry_pbs_compiled",True)
    def test_11_forged_compiled_maps(self):self.corrupt("native_maps_compiled",9)
    def test_12_forged_native_handlers(self):self.corrupt("native_handlers_verified",5)
    def test_13_forged_gameplay(self):
        for key in ("can_install","gameplay_approved","native_qa_approved","global_hooks_installed"):
            with self.subTest(key=key):self.corrupt(key,True)
    def test_14_forged_start_position(self):
        events=copy.deepcopy(self.events)
        events["start"]["map_id"]=500
        with self.assertRaises(ValueError):self.check(events=events)
    def test_15_forged_starter_species(self):
        m=copy.deepcopy(self.m)
        m["steps"][3]["physical_balls"][0]["species"]="PIKACHU"
        with self.assertRaisesRegex(ValueError,"SINNOH_S13_BLOCKED"):self.check(m=m)
    def test_16_forged_rival_event(self):self.corrupt("event","SN_NPC_ROWAN_BRIEFCASE",4)
    def test_17_forged_story_requirement(self):self.corrupt("needs",[],5)
    def test_18_runtime_unknown_flags_guard(self):
        with self.assertRaisesRegex(ValueError,"SINNOH_S13_BLOCKED"):
            self.check(pilot=self.pilot.replace("return false unless flags.keys.all?",
                                                "return true unless flags.keys.all?"))
    def test_19_runtime_reentrant_proof(self):
        with self.assertRaisesRegex(ValueError,"SINNOH_S13_BLOCKED"):
            self.check(pilot=self.pilot.replace("return false if key == \"rival_fought\" && !@rival_battle_in_progress","pass"))
    def test_20_no_bridge_hooks(self):
        with self.assertRaisesRegex(ValueError,"SINNOH_S13_BLOCKED"):
            self.check(bridge=self.bridge+"\nEventHandlers.add(:fake,:fake,proc {})")
    def test_21_progress_distinguishes_native(self):
        p=json.loads((ROOT/"data/regions/sinnoh-progress.json").read_text("utf-8"))
        # Completion of S13 must survive later S14/S31 engineering work.
        self.assertGreaterEqual(p["development"]["done"],30)
        self.assertEqual(p["development"]["done"],
                         sum(t["status"]=="done" for t in p["tasks"]))
        self.assertEqual(p["development"]["partial"],
                         sum(t["status"]=="partial" for t in p["tasks"]))
        self.assertEqual(p["development"]["pending"],
                         sum(t["status"]=="pending" for t in p["tasks"]))
        self.assertEqual(p["development"]["percent_complete"],
                         100*p["development"]["done"]//p["development"]["total"])
        self.assertEqual(next(x["status"] for x in p["tasks"] if x["id"]=="S13"),"done")
        self.assertIn(next(x["status"] for x in p["tasks"] if x["id"]=="S14"),("partial","done"))
        self.assertEqual((p["intro_workstream"]["complete"],p["intro_workstream"]["total"]),(5,8))
        self.assertFalse(p["intro_workstream"]["native_verified"])
        self.assertEqual(p["phase_gates"]["playable_in_game_executable"],0)
        self.assertEqual(p["phase_gates"]["fully_tested_native"],0)
if __name__=="__main__":unittest.main()
