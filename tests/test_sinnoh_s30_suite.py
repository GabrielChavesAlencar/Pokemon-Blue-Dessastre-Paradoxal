"""S30: negative-contract coverage of the offline Sinnoh regression matrix."""
from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.regions import audit_sinnoh_s30_suite as s30


class SinnohS30SuiteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for group in s30.REQUIRED.values():
            for rel in group:
                target = self.root / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(s30.ROOT / rel, target)

    def edit(self, rel, fn):
        target = self.root / rel
        data = json.loads(target.read_text(encoding="utf-8"))
        fn(data)
        target.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")

    def test_manifest_audits_python_ruby_portal_android_and_contracts(self):
        report = s30.collect(self.root)
        self.assertEqual(report["region"], "SINNOH")
        self.assertEqual(report["task"], "S30")
        self.assertEqual(report["scope"], "offline_contracts_only")
        self.assertEqual(report["status"], "ready_for_ci_not_native_verified")
        self.assertEqual(set(report["groups"]), set(s30.REQUIRED))
        for group, expected in s30.REQUIRED.items():
            self.assertEqual(report["groups"][group]["files"], len(expected))
            self.assertEqual(set(report["groups"][group]["sha256"]), set(expected))
            self.assertTrue(all(len(sha) == 64 for sha
                                in report["groups"][group]["sha256"].values()))
        self.assertEqual(report["development_counts"]["done"], 11)
        self.assertFalse(report["native_game_exe_tested"])
        self.assertFalse(report["joiplay_tested"])
        self.assertFalse(report["native_qa_approved"])
        self.assertFalse(report["ci_jobs_verified_by_manifest"])

    def test_manifest_deterministic_and_not_claiming_ci_execution(self):
        first = s30.collect(self.root)
        self.assertEqual(first, s30.collect(self.root))
        summary = s30.summary(first)
        self.assertIn("manifesto pronto para CI", summary)
        self.assertIn("NAO alteradas", summary)
        self.assertIn("NAO aprova gameplay", first["note"])

    def test_missing_python_or_portal_test_fails_closed(self):
        for rel in ("tests/test_sinnoh_progress.py",
                    "site/tests/sinnoh-s29-dynamic-levels.test.mjs"):
            original = (self.root / rel).read_bytes()
            (self.root / rel).unlink()
            with self.assertRaisesRegex(ValueError, "arquivo obrigatorio"):
                s30.collect(self.root)
            (self.root / rel).write_bytes(original)

    def test_missing_ruby_fixture_or_android_test_fails_closed(self):
        for rel in ("tests/sinnoh_story_ch14_runtime.rb",
                    "tests/test_sinnoh_android_ch20.py"):
            original = (self.root / rel).read_bytes()
            (self.root / rel).unlink()
            with self.assertRaisesRegex(ValueError, "arquivo obrigatorio"):
                s30.collect(self.root)
            (self.root / rel).write_bytes(original)

    def test_missing_job_or_essential_command_never_counts_as_s30(self):
        rel = ".github/workflows/sinnoh-s30.yml"
        original = (self.root / rel).read_text(encoding="utf-8")
        for token in ("S30 / Python", "S30 / Ruby", "S30 / Portal",
                      "S30 / Android estatico", "npm test", "sinnoh_ci_ch19.py"):
            (self.root / rel).write_text(original.replace(token, "DISABLED"),
                                         encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "gate obrigatorio"):
                s30.collect(self.root)
        (self.root / rel).write_text(original, encoding="utf-8")

    def test_false_native_gate_or_playtest_without_s31_rejected(self):
        rel = "data/regions/sinnoh-progress.json"
        original = (self.root / rel).read_text(encoding="utf-8")
        self.edit(rel, lambda j: j["phase_gates"].update(
            playable_in_game_executable=1))
        with self.assertRaisesRegex(ValueError, "aprovacao nativa"):
            s30.collect(self.root)
        (self.root / rel).write_text(original, encoding="utf-8")
        self.edit(rel, lambda j: j["native_playtest_workstream"].update(
            native_qa_approved=True))
        with self.assertRaisesRegex(ValueError, "playtest nativo"):
            s30.collect(self.root)

    def test_progress_s30_pending_or_wrong_counters_not_accepted(self):
        rel = "data/regions/sinnoh-progress.json"
        original = (self.root / rel).read_text(encoding="utf-8")
        self.edit(rel, lambda j: next(t for t in j["tasks"]
                                      if t["id"] == "S30").update(status="partial"))
        with self.assertRaisesRegex(ValueError, "contadores"):
            s30.collect(self.root)
        (self.root / rel).write_text(original, encoding="utf-8")
        def update_consistent(j):
            next(t for t in j["tasks"] if t["id"] == "S30").update(status="partial")
            j["development"].update(done=10, partial=7, percent_complete=31)
        self.edit(rel, update_consistent)
        with self.assertRaisesRegex(ValueError, "S30 deve ter evidencia"):
            s30.collect(self.root)

    def test_fake_playable_region_or_import_enabled_blocked(self):
        rel = "site/public/data/regions.json"
        original = (self.root / rel).read_text(encoding="utf-8")
        self.edit(rel, lambda j: j["regions"]["SINNOH"].update(status="playable"))
        with self.assertRaisesRegex(ValueError, "jogavel"):
            s30.collect(self.root)
        (self.root / rel).write_text(original, encoding="utf-8")
        self.edit("data/regions/sinnoh-source.json",
                  lambda j: j["import_control"].update(imports_enabled=True))
        with self.assertRaisesRegex(ValueError, "importacao"):
            s30.collect(self.root)

    def test_report_rejects_false_native_or_ci_certification(self):
        report = s30.collect(self.root)
        for key in ("native_game_exe_tested", "joiplay_tested",
                    "native_qa_approved", "ci_jobs_verified_by_manifest"):
            forged = copy.deepcopy(report)
            forged[key] = True
            with self.assertRaisesRegex(ValueError, "certificado falsamente"):
                s30.summary(forged)

    def test_output_is_private_nondestructive_and_no_overwrite(self):
        report = s30.collect(self.root)
        rel = Path(".blue-work/sinnoh-s30/report.json")
        s30.write_report(report, rel, self.root)
        self.assertTrue((self.root / rel).is_file())
        self.assertIn("suite automatizada offline",
                      (self.root / rel).with_suffix(".md").read_text("utf-8"))
        with self.assertRaisesRegex(ValueError, "sobrescrita"):
            s30.write_report(report, rel, self.root)
        with self.assertRaisesRegex(ValueError, "fora da pasta"):
            s30.write_report(report, Path("data/regions/unsafe.json"), self.root)

    def test_existing_markdown_is_not_overwritten(self):
        report = s30.collect(self.root)
        output = self.root / ".blue-work/sinnoh-s30/result.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.with_suffix(".md").write_text("PROTECTED", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "sobrescrita"):
            s30.write_report(report, output, self.root)
        self.assertEqual(output.with_suffix(".md").read_text("utf-8"), "PROTECTED")


if __name__ == "__main__":
    unittest.main()
