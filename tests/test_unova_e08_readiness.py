"""U08/E08: reporting a blocker is not native Windows/JoiPlay approval."""
from __future__ import annotations
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_e08_readiness as readiness

FILES=(
    "data/regions/unova-u03-areas.json",
    "data/regions/unova-e06-e07-preparation.json",
    "data/regions/unova-e05-source-map-atlas.json",
    "site/public/data/regions.json",
    "docs/UNOVA_PESQUISA_FONTES_RMXP.md",
    "docs/UNOVA_PLANO_IMPORTACAO_REGIAO_32_FASES.md",
    "scripts/regions/audit_unova_source_detail.py",
)

class ReadinessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline=readiness.inspect(ROOT)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="unova-readiness-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        for relative in FILES:
            dst=self.root/relative
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/relative,dst)

    def test_01_baseline_stays_blocked(self):
        r=self.baseline
        self.assertEqual(r["bar_e"]["completed"],6)
        self.assertEqual(r["bar_e"]["total"],8)
        self.assertEqual(r["playable_phases_completed"],0)
        self.assertFalse(r["can_install"])
        self.assertFalse(r["game_exe_tested"])
        self.assertFalse(r["android_tested"])
        self.assertFalse(r["rights_verified"])
        self.assertEqual(len(r["blockers"]),2)
        self.assertTrue(r["source_e04_e05_audit_evidence_verified"])
        self.assertEqual(r["source_unova_event_containers"],0)
        self.assertEqual(r["source_unova_map_files_audited"],64)
        self.assertEqual(r["source_maps_20x15"],56)
        self.assertEqual(r["source_maps_larger"],8)
        self.assertTrue(r["symbolic_music_and_trainers_only"])

    def test_02_zip_filename_never_approves(self):
        folder=self.root/".blue-work/unova/sources"
        folder.mkdir(parents=True)
        (folder/"Pokemon_World_V18.zip").write_bytes(b"not a zip")
        r=readiness.inspect(self.root)
        self.assertTrue(r["donor_zip_present_not_audited"])
        self.assertFalse(r["can_install"])
        self.assertEqual(r["bar_e"]["completed"],4)

    def test_03_missing_research_blocks(self):
        (self.root/"docs/UNOVA_PESQUISA_FONTES_RMXP.md").unlink()
        with self.assertRaisesRegex(ValueError,"pesquisa|research"):
            readiness.inspect(self.root)

    def test_04_missing_deep_tool_blocks(self):
        (self.root/"scripts/regions/audit_unova_source_detail.py").unlink()
        with self.assertRaises(ValueError):
            readiness.inspect(self.root)

    def test_05_cannot_enable_unova_to_boost_progress(self):
        file=self.root/"site/public/data/regions.json"
        data=json.loads(file.read_text("utf-8"))
        data["regions"]["UNOVA"]["status"]="playable"
        file.write_text(json.dumps(data),encoding="utf-8")
        with self.assertRaises(ValueError):
            readiness.inspect(self.root)

    def test_06_missing_rights_matrix_blocks(self):
        file=self.root/"data/regions/unova-e06-e07-preparation.json"
        data=json.loads(file.read_text("utf-8"))
        data["rights_matrix"]=[]
        file.write_text(json.dumps(data),encoding="utf-8")
        with self.assertRaises(ValueError):
            readiness.inspect(self.root)

    def test_07_catalog_added_not_audio_installed(self):
        r=readiness.inspect(self.root)
        self.assertGreater(r["prepared_tooling"]["symbolic_music_cues"],50)
        self.assertFalse(r["rights_verified"])
        self.assertFalse(r["source_map_ids_verified"])


    def test_08_copy_real_snapshot_proves_only_E04_E05(self):
        source=ROOT/"data/regions/unova-e04-e05-observed-source.json"
        target=self.root/"data/regions/unova-e04-e05-observed-source.json"
        shutil.copy2(source,target)
        result=readiness.inspect(self.root)
        self.assertEqual(result["bar_e"]["completed"],6)
        self.assertEqual(result["source_unova_map_files_audited"],64)
        self.assertEqual(result["source_maps_20x15"],56)
        self.assertFalse(result["can_install"])
        self.assertFalse(result["rights_verified"])
        self.assertFalse(result["game_exe_tested"])
        self.assertEqual(result["playable_phases_completed"],0)

    def test_09_forged_source_observation_is_blocked(self):
        source=ROOT/"data/regions/unova-e04-e05-observed-source.json"
        target=self.root/"data/regions/unova-e04-e05-observed-source.json"
        shutil.copy2(source,target)
        doc=json.loads(target.read_text("utf-8"))
        doc["unova_parent_event_containers"]=999
        target.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaises(ValueError):
            readiness.inspect(self.root)

    def test_10_invalid_source_zip_hash_is_blocked(self):
        source=ROOT/"data/regions/unova-e04-e05-observed-source.json"
        target=self.root/"data/regions/unova-e04-e05-observed-source.json"
        shutil.copy2(source,target)
        doc=json.loads(target.read_text("utf-8"))
        doc["archive_sha256"]="0"*64
        target.write_text(json.dumps(doc),encoding="utf-8")
        with self.assertRaises(ValueError):
            readiness.inspect(self.root)

if __name__=="__main__":
    unittest.main()
