"""S24: testes positivos/negativos da matriz de 46 cenarios; sem audio."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/music"))
import audit_sinnoh_music_s24 as s24


class SinnohS24MusicCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(s24.FILES["matrix"].read_text(encoding="utf-8"))
        cls.catalog = json.loads(s24.FILES["catalog"].read_text(encoding="utf-8"))
        cls.document = s24.FILES["document"].read_text(encoding="utf-8")
        cls.blue = s24.FILES["blue"].read_text(encoding="utf-8")
        cls.adapter = s24.FILES["adapter"].read_text(encoding="utf-8")
        cls.regions = json.loads(s24.FILES["regions"].read_text(encoding="utf-8"))

    def check(self, matrix=None, source=None, document=None, blue=None, regions=None):
        return s24.audit(
            copy.deepcopy(self.matrix if matrix is None else matrix),
            copy.deepcopy(self.catalog if source is None else source),
            self.document if document is None else document,
            self.blue if blue is None else blue, self.adapter,
            copy.deepcopy(self.regions if regions is None else regions)
        )

    def changed_row(self, key, value, index=0):
        m = copy.deepcopy(self.matrix)
        m["scenarios"][index][key] = value
        return m

    def rejects(self, matrix):
        with self.assertRaisesRegex(ValueError, "SINNOH_S24_BLOCKED"):
            self.check(matrix=matrix)

    def test_01_coverage_46_cues_8_scopes(self):
        r = self.check()
        self.assertEqual(r["scenario_count"], 46)
        self.assertEqual(r["bgm_count"], 43)
        self.assertEqual(r["me_count"], 3)
        self.assertEqual(r["historical_source_keys"], 45)
        self.assertEqual(r["by_scope"], {
            "city": 14, "route": 6, "cave": 7, "scene": 4,
            "battle": 10, "transport": 1, "post_game": 1, "me": 3
        })
        self.assertFalse(r["install_allowed"])

    def test_02_cli_read_only(self):
        run = subprocess.run(
            [sys.executable, str(ROOT / "scripts/music/audit_sinnoh_music_s24.py")],
            cwd=ROOT, capture_output=True, text=True
        )
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("SINNOH_S24_CATALOG_OK_OFFLINE_ONLY", run.stdout)

    def test_03_missing_row(self):
        m = copy.deepcopy(self.matrix)
        m["scenarios"].pop()
        self.rejects(m)

    def test_04_duplicate_row(self):
        m = copy.deepcopy(self.matrix)
        m["scenarios"][-1] = m["scenarios"][0]
        self.rejects(m)

    def test_05_wrong_order(self):
        m = copy.deepcopy(self.matrix)
        m["scenarios"][0], m["scenarios"][1] = m["scenarios"][1], m["scenarios"][0]
        self.rejects(m)

    def test_06_fake_cue(self):
        self.rejects(self.changed_row("cue", "SINNOH_FAKE"))

    def test_07_fake_map_id(self):
        self.rejects(self.changed_row("physical_map_id", 800))

    def test_08_fake_event_id(self):
        self.rejects(self.changed_row("physical_event_id", 1))

    def test_09_unlicensed_file(self):
        self.rejects(self.changed_row("file", "Audio/BGM/official.ogg"))

    def test_10_fake_hash(self):
        self.rejects(self.changed_row("sha256", "a"*64))

    def test_11_fake_license(self):
        self.rejects(self.changed_row("license", "CC0"))

    def test_12_fake_permission(self):
        self.rejects(self.changed_row("redistribution_consent", True))

    def test_13_context_guard(self):
        self.rejects(self.changed_row("context", "MapId instalado"))
        self.rejects(self.changed_row("trigger_guard", "ALWAYS_PLAY"))

    def test_14_wrong_priority_fallback(self):
        self.rejects(self.changed_row("priority", -5))
        self.rejects(self.changed_row("fallback", "OVERRIDE"))

    def test_15_no_compiled_hook(self):
        self.rejects(self.changed_row("compiled_hook", True))
        self.rejects(self.changed_row("enabled", True))

    def test_16_cannot_claim_licensing_or_qa(self):
        for key, value in (
            ("licensed_recordings", 1), ("install_allowed", True),
            ("game_exe_tested", True), ("native_qa_approved", True),
            ("active_in_bluemusic", True), ("autoplay_enabled", True),
        ):
            m = copy.deepcopy(self.matrix)
            m[key] = value
            self.rejects(m)

    def test_17_ch16_audio_tampering_rejected(self):
        src = copy.deepcopy(self.catalog)
        src["cues"][0]["track_path"] = "Audio/BGM/fake.ogg"
        with self.assertRaisesRegex(ValueError, "SINNOH_CH16_BLOQUEADO"):
            self.check(source=src)

    def test_18_ch16_region_and_bluemusic_protected(self):
        regions = copy.deepcopy(self.regions)
        regions["regions"]["SINNOH"]["status"] = "playable"
        with self.assertRaisesRegex(ValueError, "SINNOH_CH16_BLOQUEADO"):
            self.check(regions=regions)
        with self.assertRaisesRegex(ValueError, "SINNOH_CH16_BLOQUEADO"):
            self.check(blue=self.blue + "\nSinnohMusicContracts.install\n")

    def test_19_only_s24_code_progresses(self):
        p = json.loads((ROOT / "data/regions/sinnoh-progress.json").read_text(encoding="utf-8"))
        self.assertEqual(next(t["status"] for t in p["tasks"] if t["id"]=="S24"), "done")
        self.assertEqual(next(t["status"] for t in p["tasks"] if t["id"]=="S25"), "pending")
        self.assertEqual((p["development"]["done"], p["development"]["partial"]), (25, 4))
        self.assertEqual(p["development"]["percent_complete"], 78)
        self.assertTrue(all(p["phase_gates"][k] == 0 for k in (
            "technically_approved", "playable_in_game_executable", "fully_tested_native"
        )))


if __name__ == "__main__":
    unittest.main()
