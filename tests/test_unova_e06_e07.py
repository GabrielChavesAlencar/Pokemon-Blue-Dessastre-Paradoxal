"""Guard Unova E06/E07 symbolic catalogs against false asset/game approvals."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_e06_e07 as audit

class UnovaRightsAndMusicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template=json.loads(audit.DATA.read_text("utf-8"))
        cls.areas=json.loads(audit.AREAS.read_text("utf-8"))
        cls.region=json.loads(audit.REGISTRY.read_text("utf-8"))["regions"]["UNOVA"]

    def invalid(self,change):
        row=copy.deepcopy(self.template)
        area=copy.deepcopy(self.areas)
        region=copy.deepcopy(self.region)
        change(row,area,region)
        with self.assertRaises(ValueError):
            audit.validate(row,area,region)

    def test_01_all_prepared_uninstalled(self):
        result=audit.validate(self.template,self.areas,self.region)
        self.assertEqual(result["music_cues"],69)
        self.assertEqual(result["trainer_references"],19)
        self.assertEqual(result["rights_groups_unverified"],14)
        self.assertFalse(result["rights_cleared"])
        self.assertFalse(result["music_installed"])
        self.assertFalse(result["can_install"])

    def test_02_catalog_cannot_enable_region(self):
        self.invalid(lambda d,a,r:r.update(status="playable"))

    def test_03_unlicensed_distribution_is_blocked(self):
        self.invalid(lambda d,a,r:d["rights_matrix"][0].update(redistribution_allowed=True))

    def test_04_cannot_forge_rights_owner_or_license(self):
        self.invalid(lambda d,a,r:d["rights_matrix"][3].update(rights_owner="Someone",license="MIT"))

    def test_05_cannot_claim_audio_bytes(self):
        self.invalid(lambda d,a,r:d.update(audio_bytes_added=1000))

    def test_06_cannot_install_fake_music_file(self):
        self.invalid(lambda d,a,r:d["music_cues"][0].update(source_track="Music.ogg"))

    def test_07_cannot_set_fake_map_id(self):
        self.invalid(lambda d,a,r:d["music_cues"][0].update(physical_map_id=500))

    def test_08_cannot_forge_compiled_binding(self):
        self.invalid(lambda d,a,r:d["music_cues"][0].update(compiled_binding_verified=True))

    def test_09_cannot_forge_trainer_team(self):
        self.invalid(lambda d,a,r:d["trainer_references"][0].update(team=["LILLIPUP"]))

    def test_10_cannot_forge_trainer_level_or_PBS_id(self):
        self.invalid(lambda d,a,r:d["trainer_references"][1].update(level_reference=20,pbs_trainer_id=12))

    def test_11_missing_leader_is_rejected(self):
        self.invalid(lambda d,a,r:d["trainer_references"].remove(next(x for x in d["trainer_references"] if x["key"]=="UNOVA_TRAINER_IRIS")))

    def test_12_battle_cue_missing_is_rejected(self):
        self.invalid(lambda d,a,r:d["music_cues"].remove(next(x for x in d["music_cues"] if x["key"]=="UNOVA_BATTLE_N")))

    def test_13_missing_wrong_audio_fallback(self):
        self.invalid(lambda d,a,r:d["music_cues"][0].update(fallback="STOP_EVERYTHING"))

    def test_14_cannot_fake_native_gameplay(self):
        self.invalid(lambda d,a,r:d.update(game_exe_tested=True))

    def test_15_missing_area_reference_is_rejected(self):
        self.invalid(lambda d,a,r:d["music_cues"][0].update(target_area_key="UNOVA_FAKE"))

    def test_16_duplicate_music_cue_is_rejected(self):
        self.invalid(lambda d,a,r:d["music_cues"].append(copy.deepcopy(d["music_cues"][0])))

if __name__=="__main__":
    unittest.main()
