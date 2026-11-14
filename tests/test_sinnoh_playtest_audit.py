"""Offline 44-case Sinnoh playtest evidence: no real game, only fake fixtures."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_playtest import audit, new_plan, write_new_plan
from install_sinnoh_qa_copy import COMPILED, COMPILE_REQUEST, install, prepare
from test_sinnoh_qa_install import fixture, simulate_native_report


class SinnohManualPlaytestAuditTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix="sinnoh-manual-qa-")
        self.addCleanup(tmp.cleanup)
        self.project = Path(tmp.name)
        self.game, self.overlay, self.spec = fixture(self.project)
        report, blobs, native = prepare(self.game, self.overlay, self.spec,
                                        token="123456abcdef", project=self.project)
        self.qa = self.project / ".blue-work/game-sinnoh-qa-123456abcdef"
        install(self.project, self.game, self.qa, report, blobs, native)
        meta = simulate_native_report(self.qa)
        (self.qa / COMPILED).write_text(meta["compile_token"], encoding="ascii")
        (self.qa / COMPILE_REQUEST).unlink()
        self.file = write_new_plan(self.qa, project=self.project)

    def save(self, plan):
        self.file.write_text(json.dumps(plan, ensure_ascii=False), encoding="utf-8")

    def attach(self, case, observation, *, filename=None):
        stem = filename or case["id"]
        folder = self.qa / "qa-evidence"
        folder.mkdir(exist_ok=True)
        file = folder / (stem + ".txt")
        content = (case["id"] + "\n") .encode("utf-8")
        file.write_bytes(content)
        case["evidence"] = {
            "path": "qa-evidence/" + file.name,
            "sha256": hashlib.sha256(content).hexdigest(),
        }
        case["observation"] = {"platform": "windows", "pass": True, **observation}

    def test_plan_has_every_battle_path_warp_and_regional_regression(self):
        before = {str(p.relative_to(self.project)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.game.rglob("*") if p.is_file()}
        plan = new_plan(self.qa, project=self.project)
        self.assertEqual(plan["origin"], "REAL_QA_OBSERVATIONS_REQUIRED")
        self.assertEqual(len(plan["cases"]), 44)
        self.assertEqual(len({x["id"] for x in plan["cases"]}), 44)
        self.assertEqual(sum(x["kind"] == "barry" for x in plan["cases"]), 12)
        self.assertEqual(sum(x["kind"] == "warp" for x in plan["cases"]), 16)
        self.assertEqual(sum(x["kind"] == "starter" for x in plan["cases"]), 3)
        self.assertEqual(sum(x["kind"] == "save_reload" for x in plan["cases"]), 3)
        self.assertEqual(sum(x["kind"] == "npc" for x in plan["cases"]), 5)
        self.assertEqual(sum(x["kind"] == "regression" for x in plan["cases"]), 4)
        self.assertEqual(sum(x["kind"] == "android" for x in plan["cases"]), 1)
        self.assertFalse(plan["may_approve_gameplay"])
        self.assertFalse(plan["may_create_barry_ready_marker"])
        self.assertTrue(all(c["observation"] is None and c["evidence"] is None
                            for c in plan["cases"]))
        after = {str(p.relative_to(self.project)): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.game.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        with self.assertRaisesRegex(ValueError, "já existe"):
            write_new_plan(self.qa, project=self.project)

    def test_empty_evidence_is_pending_not_native_success(self):
        report = audit(self.qa, project=self.project)
        self.assertEqual(report["status"], "INCOMPLETE")
        self.assertEqual((report["completed"], report["total"]), (0, 44))
        self.assertFalse(report["automatically_approved_gameplay"])
        self.assertFalse(report["native_game_executed_independently_proven"])
        self.assertFalse(report["may_create_barry_ready_marker"])

    def test_normal_and_master_levels_checked_from_observed_party(self):
        plan = json.loads(self.file.read_text("utf-8"))
        for row in plan["cases"]:
            if row["id"] in ("barry-PIPLUP-normal-win", "barry-CHIMCHAR-master-loss"):
                self.attach(row, {
                    "species": row["opponent"], "version": row["version"],
                    "outcome": row["outcome"], "highest_party_level": 50,
                    "growth_rate_max_level": 100,
                    "enemy_level": 35 if row["mode"] == "normal" else 45,
                    "enemy_party_size": 1 if row["mode"] == "normal" else 4,
                })
        self.save(plan)
        report = audit(self.qa, project=self.project)
        self.assertEqual(report["completed"], 2)
        self.assertEqual(report["by_kind"]["barry"]["complete"], 2)
        self.assertFalse(report["automatically_approved_gameplay"])

    def test_wrong_observed_level_is_rejected(self):
        plan = json.loads(self.file.read_text("utf-8"))
        row = next(c for c in plan["cases"] if c["id"] == "barry-TURTWIG-master-win")
        self.attach(row, {
            "species": "CHIMCHAR", "version": 0, "outcome": "win",
            "highest_party_level": 70, "enemy_level": 49,
            "growth_rate_max_level": 100, "enemy_party_size": 4,
        })
        self.save(plan)
        with self.assertRaisesRegex(ValueError, "90%"):
            audit(self.qa, project=self.project)

    def test_wrong_counter_type_or_master_party_size_rejected(self):
        plan = json.loads(self.file.read_text("utf-8"))
        row = next(c for c in plan["cases"] if c["id"] == "barry-TURTWIG-master-loss")
        self.attach(row, {
            "species": "PIPLUP", "version": 0, "outcome": "loss",
            "highest_party_level": 50, "enemy_level": 45,
            "growth_rate_max_level": 100, "enemy_party_size": 1,
        })
        self.save(plan)
        with self.assertRaisesRegex(ValueError, "contra-inicial"):
            audit(self.qa, project=self.project)
        row["observation"]["species"] = "CHIMCHAR"
        self.save(plan)
        with self.assertRaisesRegex(ValueError, "menor"):
            audit(self.qa, project=self.project)

    def test_warp_coordinates_must_match_real_spec(self):
        plan = json.loads(self.file.read_text("utf-8"))
        row = next(c for c in plan["cases"] if c["kind"] == "warp")
        self.attach(row, {
            "destination_map_id": row["destination_map_id"],
            "arrival_x": row["arrival_x"], "arrival_y": row["arrival_y"] + 1,
        })
        self.save(plan)
        with self.assertRaisesRegex(ValueError, "Warp"):
            audit(self.qa, project=self.project)
        row["observation"]["arrival_y"] = row["arrival_y"]
        self.save(plan)
        self.assertEqual(audit(self.qa, project=self.project)["completed"], 1)

    def test_save_reload_requires_same_profile_party_and_dex(self):
        plan = json.loads(self.file.read_text("utf-8"))
        row = next(c for c in plan["cases"] if c["id"] == "save-reload-TURTWIG")
        self.attach(row, {
            "starter_before": "TURTWIG", "starter_after": "TURTWIG",
            "same_profile_after_reload": True, "same_party_after_reload": False,
            "pokedex_kept_after_reload": True,
        })
        self.save(plan)
        with self.assertRaisesRegex(ValueError, "Save/load"):
            audit(self.qa, project=self.project)
        row["observation"]["same_party_after_reload"] = True
        self.save(plan)
        self.assertEqual(audit(self.qa, project=self.project)["completed"], 1)

    def test_screenshot_tamper_and_escape_are_rejected(self):
        plan = json.loads(self.file.read_text("utf-8"))
        row = next(c for c in plan["cases"] if c["kind"] == "starter")
        self.attach(row, {"species": row["starter"], "second_ball_denied": True})
        self.save(plan)
        self.assertEqual(audit(self.qa, project=self.project)["completed"], 1)
        (self.qa / row["evidence"]["path"]).write_bytes(b"altered log")
        with self.assertRaisesRegex(ValueError, "alterado"):
            audit(self.qa, project=self.project)
        row["evidence"]["path"] = "../game/save.dat"
        self.save(plan)
        with self.assertRaisesRegex(ValueError, "qa-evidence"):
            audit(self.qa, project=self.project)

    def test_wrong_token_or_reordered_cases_are_rejected(self):
        plan = json.loads(self.file.read_text("utf-8"))
        plan["compile_token"] = "0"*64
        self.save(plan)
        with self.assertRaisesRegex(ValueError, "compilação"):
            audit(self.qa, project=self.project)
        plan = new_plan(self.qa, project=self.project)
        plan["cases"][0], plan["cases"][1] = plan["cases"][1], plan["cases"][0]
        self.save(plan)
        with self.assertRaisesRegex(ValueError, "reordenado"):
            audit(self.qa, project=self.project)

    def test_fake_android_observation_not_accepted_as_windows(self):
        plan = json.loads(self.file.read_text("utf-8"))
        row = next(c for c in plan["cases"] if c["kind"] == "android")
        self.attach(row, {
            "joi_play_session": True, "independent_save_profile": True,
            "starter_and_warp_tested": True
        })
        self.save(plan)
        with self.assertRaisesRegex(ValueError, "Android"):
            audit(self.qa, project=self.project)
        row["observation"]["platform"] = "android"
        self.save(plan)
        self.assertEqual(audit(self.qa, project=self.project)["completed"], 1)

    def test_one_case_cannot_be_accepted_without_screenshot(self):
        plan = json.loads(self.file.read_text("utf-8"))
        plan["cases"][0]["observation"] = {
            "platform": "windows", "pass": True, "species": "TURTWIG",
            "second_ball_denied": True,
        }
        self.save(plan)
        with self.assertRaisesRegex(ValueError, "sem captura"):
            audit(self.qa, project=self.project)

    def test_no_copy_or_generation_before_native_probe(self):
        (self.qa / "Data/blue-sinnoh-qa-engine-check.json").unlink()
        with self.assertRaisesRegex(ValueError, "sem relatório"):
            new_plan(self.qa, project=self.project)


if __name__ == "__main__":
    unittest.main()
