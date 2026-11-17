"""S25: regressao negativa do adapter BlueMusic sem efeitos colaterais."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/music"))
import audit_sinnoh_music_s25 as s25
import audit_sinnoh_music_s24 as s24

class SinnohS25Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads(s25.MANIFEST.read_text("utf-8"))
        cls.matrix=json.loads(s24.FILES["matrix"].read_text("utf-8"))
        cls.catalog=json.loads(s24.FILES["catalog"].read_text("utf-8"))
        cls.doc=s24.FILES["document"].read_text("utf-8")
        cls.blue=s24.FILES["blue"].read_text("utf-8")
        cls.adapter=s24.FILES["adapter"].read_text("utf-8")
        cls.regions=json.loads(s24.FILES["regions"].read_text("utf-8"))
        cls.bridge=s25.BRIDGE.read_text("utf-8")

    def check(self,m=None,matrix=None,catalog=None,blue=None,bridge=None):
        return s25.audit(
            copy.deepcopy(self.manifest if m is None else m),
            copy.deepcopy(self.matrix if matrix is None else matrix),
            copy.deepcopy(self.catalog if catalog is None else catalog),
            self.doc,self.blue if blue is None else blue,self.adapter,
            copy.deepcopy(self.regions),self.bridge if bridge is None else bridge)

    def blocked(self,key,value):
        m=copy.deepcopy(self.manifest)
        m[key]=value
        with self.assertRaisesRegex(ValueError,"SINNOH_S25_BLOCKED"):
            self.check(m=m)

    def test_01_clean_offline(self):
        self.assertEqual(self.check()["cues"],46)
        self.assertFalse(self.check()["music_installed"])

    def test_02_cli(self):
        p=subprocess.run([sys.executable,str(s25.ROOT/"scripts/music/audit_sinnoh_music_s25.py")],
                         cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertIn("SINNOH_S25_BRIDGE_OK_OFFLINE",p.stdout)

    def test_03_forged_enabled(self): self.blocked("enabled",True)
    def test_04_forged_native(self): self.blocked("installed",True)
    def test_05_forged_hook(self): self.blocked("autoplay",True)
    def test_06_fake_audio(self): self.blocked("approved_tracks",["fake.mp3"])
    def test_07_fake_license(self): self.blocked("licensed_sources",["fake"])
    def test_08_fake_map(self): self.blocked("native_maps",[800])
    def test_09_fake_event(self): self.blocked("native_events",[1])
    def test_10_fake_binding(self): self.blocked("compiled_bindings",["fake"])
    def test_11_claimed_audio_copy(self): self.blocked("audio_copied",True)
    def test_12_claimed_game_exe(self): self.blocked("game_exe_tested",True)
    def test_13_claimed_joiplay(self): self.blocked("joiplay_tested",True)
    def test_14_claimed_qa(self): self.blocked("native_qa_approved",True)

    def test_15_priority_locked(self):
        self.blocked("priority",list(reversed(s25.PRIORITY)))

    def test_16_policy_locked(self):
        m=copy.deepcopy(self.manifest)
        m["policies"]["preserve_mute"]=False
        with self.assertRaisesRegex(ValueError,"SINNOH_S25_BLOCKED"):
            self.check(m=m)

    def test_17_no_audio_function(self):
        with self.assertRaisesRegex(ValueError,"SINNOH_S25_BLOCKED"):
            self.check(bridge=self.bridge+"\npbBGMPlay('bad')\n")

    def test_18_ch16_sources_cannot_activate(self):
        c=copy.deepcopy(self.catalog)
        c["cues"][0]["enabled"]=True
        with self.assertRaisesRegex(ValueError,"SINNOH_CH16_BLOQUEADO"):
            self.check(catalog=c)

    def test_19_s24_no_fake_map(self):
        matrix=copy.deepcopy(self.matrix)
        matrix["scenarios"][0]["physical_map_id"]=800
        with self.assertRaisesRegex(ValueError,"SINNOH_S24_BLOCKED"):
            self.check(matrix=matrix)

    def test_20_no_global_bluemusic_modification(self):
        with self.assertRaisesRegex(ValueError,"SINNOH_CH16_BLOQUEADO"):
            self.check(blue=self.blue+"\nSinnohMusicContracts\n")

    def test_21_progress_26_only(self):
        p=json.loads((ROOT/"data/regions/sinnoh-progress.json").read_text("utf-8"))
        # S25 completion remains valid when later unrelated tasks progress.
        self.assertGreaterEqual(p["development"]["done"],26)
        self.assertEqual(p["development"]["done"],
                         sum(t["status"]=="done" for t in p["tasks"]))
        self.assertEqual(p["development"]["partial"],
                         sum(t["status"]=="partial" for t in p["tasks"]))
        self.assertEqual(p["development"]["pending"],
                         sum(t["status"]=="pending" for t in p["tasks"]))
        self.assertEqual(p["development"]["percent_complete"],
                         100*p["development"]["done"]//p["development"]["total"])
        self.assertFalse(self.manifest["installed"])
        self.assertFalse(self.manifest["enabled"])
        self.assertEqual(self.manifest["approved_tracks"],[])
        self.assertEqual(next(x["status"] for x in p["tasks"] if x["id"]=="S25"),"done")
        self.assertEqual(p["phase_gates"]["playable_in_game_executable"],0)
        self.assertEqual(p["phase_gates"]["fully_tested_native"],0)

if __name__=="__main__":
    unittest.main()
