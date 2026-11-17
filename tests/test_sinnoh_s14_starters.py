"""S14: contracts & real synthetic map compiler tests, no native approval."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_s14_starters as s14
from build_sinnoh_twinleaf_events import compile_events
from test_sinnoh_twinleaf_events import fixture

class S14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=[json.loads(x.read_text("utf-8")) for x in
                  (s14.MANIFEST,s14.EVENTS,s14.SCHEMA,s14.S13)]
        cls.files=[x.read_text("utf-8") for x in
                   (s14.PILOT,s14.INTRO,s14.COMPILER,s14.BRIDGE)]
    def check(self,ball=None,events=None,pilot=None,compiler=None,bridge=None):
        a=copy.deepcopy(self.base)
        b=list(self.files)
        if ball is not None:a[0]=ball
        if events is not None:a[1]=events
        if pilot is not None:b[0]=pilot
        if compiler is not None:b[2]=compiler
        if bridge is not None:b[3]=bridge
        return s14.audit(*a,*b)
    def reject(self,key,value,index=None):
        spec=copy.deepcopy(self.base[0])
        if index is None:spec[key]=value
        else:spec["balls"][index][key]=value
        with self.assertRaisesRegex(ValueError,"SINNOH_S14_BLOCKED"):
            self.check(ball=spec)

    def test_01_three_physical_balls_ch06(self):
        result=self.check()
        self.assertEqual(result["physical_starter_events"],3)
        self.assertFalse(result["can_install"])
        self.assertEqual([x["species"] for x in self.base[0]["balls"]],
                         ["TURTWIG","CHIMCHAR","PIPLUP"])
        self.assertTrue(all(x["trigger"]=="action" for x in self.base[0]["balls"]))

    def test_02_cli(self):
        r=subprocess.run([sys.executable,str(s14.ROOT/"scripts/regions/audit_sinnoh_s14_starters.py")],
                         cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn("SINNOH_S14_PHYSICAL_STARTERS_OK_OFFLINE",r.stdout)
    def test_03_unknown_starter(self):self.reject("species","PIKACHU",0)
    def test_04_swapped_starter_event(self):self.reject("event_key","SN_BALL_CHIMCHAR",0)
    def test_05_wrong_rival(self):self.reject("rival_species","TURTWIG",1)
    def test_06_wrong_rival_version(self):self.reject("rival_pbs_version",2,1)
    def test_07_fake_native_map(self):self.reject("native_map_id",500,0)
    def test_08_fake_native_event(self):self.reject("native_event_id",2,0)
    def test_09_fake_position(self):self.reject("verified_position",True,0)
    def test_10_fake_sprite(self):self.reject("verified_sprite","BallSprite",0)
    def test_11_fake_callback(self):self.reject("verified_native_callback","forged",0)
    def test_12_fake_compiled(self):self.reject("event_compiled",True,0)
    def test_13_fake_playtest(self):self.reject("grant_tested_in_game",True,0)
    def test_14_fake_source_registry(self):self.reject("verified_native_sources",{"SN_BALL_TURTWIG":"fake"})
    def test_15_fake_approval(self):
        for k in ("approved_for_install","starter_selection_playable","game_exe_verified",
                  "joiplay_verified","native_qa_approved","source_assets_verified",
                  "compiled_pbs_barry_verified","can_write_game"):
            with self.subTest(k=k):self.reject(k,True)
    def test_16_wrong_trigger(self):self.reject("trigger","touch",0)
    def test_17_reordered_ball(self):
        obj=copy.deepcopy(self.base[0])
        obj["balls"][0],obj["balls"][1]=obj["balls"][1],obj["balls"][0]
        with self.assertRaisesRegex(ValueError,"SINNOH_S14_BLOCKED"):
            self.check(ball=obj)
    def test_18_ch06_template_mutation_denied(self):
        obj=copy.deepcopy(self.base[1])
        for e in obj["maps"][5]["events"]:
            if e["kind"]=="starter_ball" and e["species"]=="TURTWIG":
                e["species"]="CHIMCHAR"
                break
        with self.assertRaises(ValueError):self.check(events=obj)
    def test_19_compiler_missing_ch06_guards(self):
        obj=self.files[2].replace('STATIC_BALLS.get(key) != (symbol, species)',"False")
        with self.assertRaisesRegex(ValueError,"SINNOH_S14_BLOCKED"):self.check(compiler=obj)
    def test_20_compiler_missing_manual_action_guard(self):
        obj=self.files[2].replace('if trigger != "action" or','if False or')
        with self.assertRaisesRegex(ValueError,"SINNOH_S14_BLOCKED"):self.check(compiler=obj)
    def test_21_pilot_missing_reentrancy(self):
        obj=self.files[0].replace("return false if @starter_grant_in_progress","return true")
        with self.assertRaisesRegex(ValueError,"SINNOH_S14_BLOCKED"):self.check(pilot=obj)
    def test_22_bridge_injects_grant(self):
        obj=self.files[3]+"\nBlueSinnohPilot.choose_starter_from_ball(:TURTWIG)\n"
        with self.assertRaisesRegex(ValueError,"SINNOH_S14_BLOCKED"):self.check(bridge=obj)
    def test_23_compiler_end_to_end_three_ball_scripts(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            folder,source=fixture(root)
            report,files=compile_events(folder,source,project=root)
            self.assertEqual(report["starter_balls"],["CHIMCHAR","PIPLUP","TURTWIG"])
            self.assertEqual(len(files),9)
            original=(root/"game/Data/Map001.rxdata").read_bytes()
            self.assertEqual(original,b"Decades must stay unchanged")
            # A walk-on starter would grant without explicit player choice.
            tamper=copy.deepcopy(source)
            for e in tamper["maps"][5]["events"]:
                if e["kind"]=="starter_ball":
                    e["trigger"]="touch"
                    break
            with self.assertRaisesRegex(ValueError,"Poké Bola exige interação"):
                compile_events(folder,tamper,project=root)
            self.assertEqual((root/"game/Data/Map001.rxdata").read_bytes(),original)

    def test_24_progress_only_offline(self):
        p=json.loads((ROOT/"data/regions/sinnoh-progress.json").read_text("utf-8"))
        self.assertEqual((p["development"]["done"],p["development"]["partial"],
                          p["development"]["pending"],p["development"]["percent_complete"]),
                         (31,1,0,96))
        self.assertEqual(next(t["status"] for t in p["tasks"] if t["id"]=="S14"),"done")
        self.assertEqual(next(t["status"] for t in p["tasks"] if t["id"]=="S31"),"partial")
        self.assertEqual((p["intro_workstream"]["complete"],p["intro_workstream"]["total"]),(5,8))
        self.assertFalse(p["intro_workstream"]["native_verified"])
        self.assertEqual(p["phase_gates"]["playable_in_game_executable"],0)
        self.assertEqual(p["phase_gates"]["fully_tested_native"],0)
if __name__=="__main__":unittest.main()
