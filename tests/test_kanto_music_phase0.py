"""Kanto phase-zero baseline: inspect only; never edit original audio or saves."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.music import audit_kanto_phase0 as phase0

ROOT = Path(__file__).resolve().parents[1]


class PhaseZeroMusicTests(unittest.TestCase):
    def fake_integrity(self):
        return {"files": 64, "BGM": 50, "ME": 14,
                "bytes": 135_768_381}

    def test_existing_repo_baseline_has_142_source_maps_45_previews(self):
        # Avoid rereading all 135 MB in each unit test; the workflow separately
        # runs the real CLI with hashes verified for ALL 64 assets.
        with patch.object(phase0.install_kanto_music, "audit",
                          return_value=self.fake_integrity()):
            report = phase0.inspect(ROOT)
        self.assertEqual(report["result"], "PASS_STATIC_BASELINE")
        self.assertEqual(report["phase"], 0)
        self.assertEqual(report["audio_catalog"]["tracks_verified_by_git_blob_sha"], 64)
        self.assertEqual(report["audio_catalog"]["BGM"], 50)
        self.assertEqual(report["audio_catalog"]["ME"], 14)
        self.assertEqual(report["source_maps"]["source_count"], 142)
        self.assertEqual(report["source_maps"]["preview_only"], 45)
        self.assertFalse(report["source_maps"]["compiled_map_ids_audited"])
        self.assertEqual(report["integration"]["map_music_bindings_added"], 0)
        self.assertEqual(report["integration"]["event_music_bindings_added"], 0)
        self.assertFalse(report["audio_catalog"]["playback_tested"])
        self.assertEqual(report["local_game"]["status"], "not_checked")

    def test_only_real_source_groups_reported_not_invented(self):
        with patch.object(phase0.install_kanto_music, "audit",
                          return_value=self.fake_integrity()):
            report = phase0.inspect(ROOT)
        group = report["source_maps"]["groups"]
        self.assertEqual(group["pallet"]["source_count"], 2)
        self.assertEqual(group["pallet"]["source_map_ids_only"][0]["source_id"], 5)
        self.assertEqual(group["mt_moon"]["source_count"], 3)
        self.assertEqual(group["silph"]["source_count"], 12)
        self.assertGreaterEqual(group["gyms"]["source_count"], 8)
        self.assertEqual(group["lavender"]["source_count"], 0)
        self.assertEqual(group["lavender"]["status"], "absent_from_pilot_manifest")
        self.assertEqual(group["sevii"]["source_count"], 0)
        self.assertEqual(group["rocket_hideout"]["source_count"], 0)
        self.assertIn("preview_only", {
            item["status"] for area in group.values()
            for item in area["source_map_ids_only"]
        })

    def test_plugin_hooks_are_not_fake_audio_playback(self):
        plugin=(ROOT/"scripts/music/BlueMusic.rb").read_text(encoding="utf-8")
        result=phase0.inspect_runtime(plugin)
        self.assertEqual(result["map_bgm_hook"], "present_static")
        self.assertEqual(result["wild_battle_bgm_hook"], "present_static")
        self.assertEqual(result["trainer_battle_bgm_hook"], "present_static")
        self.assertEqual(result["trainer_victory_bgm_hook"], "present_static")
        self.assertEqual(result["me_event_playback_hook"], "not_implemented")
        # Fase 0 remains a historical baseline, but F1 now adds the guard.
        self.assertEqual(result["kanto_region_guard"], "present_static")
        self.assertEqual(result["gym_victory_separate_hook"], "not_implemented")
        self.assertEqual(result["global_battle_config"], "present_static")
        self.assertFalse(result["native_audio_decoder_tested"])
        with self.assertRaisesRegex(ValueError,"hook BlueMusic"):
            phase0.inspect_runtime("module BlueMusic;end")

    def test_mutated_source_manifest_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            for name in ("data/kanto-music.json", "data/regions/kanto-source.json",
                         "scripts/music/BlueMusic.rb"):
                destination=root/name
                destination.parent.mkdir(parents=True,exist_ok=True)
                destination.write_bytes((ROOT/name).read_bytes())
            manifest=root/"data/regions/kanto-source.json"
            data=json.loads(manifest.read_text(encoding="utf-8"))
            del data["maps"]["5"]
            manifest.write_text(json.dumps(data),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"142 mapas"):
                phase0.inspect(root,check_audio_bytes=False)

    def test_game_scan_is_read_only_and_distinguishes_missing(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/"Game.exe").write_bytes(b"test runner fixture")
            (root/"Audio/BGM/Kanto").mkdir(parents=True)
            tracks=[
                {"game_path":"Audio/BGM/Kanto/sample.mp3",
                 "bytes":len(b"fake-music"), "git_blob_sha":"not-real"},
                {"game_path":"Audio/ME/Kanto/absent.mp3",
                 "bytes":1, "git_blob_sha":"does-not-exist"},
            ]
            (root/"Audio/BGM/Kanto/sample.mp3").write_bytes(b"fake-music")
            status=phase0.inspect_game(root,tracks)
            self.assertEqual(status["status"],"incomplete")
            self.assertEqual(status["matched"],0)
            self.assertEqual(status["missing"],1)
            self.assertEqual(status["conflicting"],["Audio/BGM/Kanto/sample.mp3"])
            self.assertFalse(status["tested_playback"])
            self.assertEqual(len(list(root.rglob("*"))),5)

    def test_report_rejects_paths_outside_ignored_workspace(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(SystemExit) as exit_error:
                phase0.main(["--output",str(Path(temp)/"unsafe-report.json")])
            self.assertEqual(exit_error.exception.code,2)
            self.assertFalse((Path(temp)/"unsafe-report.json").exists())


if __name__ == "__main__":
    unittest.main()
