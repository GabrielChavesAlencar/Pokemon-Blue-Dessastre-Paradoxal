"""CH19: testes negativos do relatorio isolado e dos gates offline."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.regions import sinnoh_ci_ch19 as ci


class SinnohCIChapter19Tests(unittest.TestCase):
    def test_python_suite_is_scoped_to_sinnoh(self):
        names = [name for name, _ in ci.PYTHON_CHECKS]
        self.assertIn("sinnoh-python-unit", names)
        unit = next(cmd for name, cmd in ci.PYTHON_CHECKS if name == "sinnoh-python-unit")
        self.assertIn("test_sinnoh_*.py", unit)
        self.assertNotIn("test_*.py", unit)
        self.assertTrue(all(name.startswith("sinnoh-") for name in names))

    def test_ruby_suite_has_real_fixtures_not_native_game(self):
        names = [name for name, _ in ci.RUBY_CHECKS]
        for required in ("sinnoh-pilot", "sinnoh-barry-ch08", "sinnoh-evolution",
                         "sinnoh-story", "sinnoh-music", "sinnoh-engine-fixture"):
            self.assertIn(required, names)
        self.assertTrue(all("Game.exe" not in " ".join(cmd) for _, cmd in ci.RUBY_CHECKS))
        self.assertTrue(all("joiplay" not in " ".join(cmd).lower() for _, cmd in ci.RUBY_CHECKS))
        self.assertFalse(any(name.startswith("kanto-") or name.startswith("johto-")
                             for name in names))

    def test_failure_is_not_swallowed(self):
        with tempfile.TemporaryDirectory() as d:
            result = ci.run_check("sinnoh-intentional-failure",
                                  [sys.executable, "-c", "import sys;sys.exit(7)"], Path(d))
        self.assertEqual(result["status"], "failed")
        self.assertEqual(result["returncode"], 7)
        summary = ci.summarize("python", [result])
        self.assertEqual(summary["status"], "failed")
        self.assertFalse(summary["native_qa_approved"])

    def test_runner_missing_blocks_instead_of_passing(self):
        with tempfile.TemporaryDirectory() as d:
            result = ci.run_check("sinnoh-missing", ["__sinnoh_ch19_no_such_runner__"], Path(d))
        self.assertEqual(result["status"], "blocked")
        self.assertEqual(ci.summarize("ruby", [result])["status"], "blocked")

    def test_success_is_explicit_and_never_native_evidence(self):
        with tempfile.TemporaryDirectory() as d:
            result = ci.run_check("sinnoh-synthetic-success",
                                  [sys.executable, "-c", "print('ok')"], Path(d))
        self.assertEqual(result["status"], "passed")
        summary = ci.summarize("python", [result])
        self.assertEqual(summary["status"], "passed")
        self.assertEqual(summary["evidence_level"], "offline_synthetic")
        self.assertTrue(all(summary[field] is False for field in ci.NATIVE_FIELDS))
        self.assertEqual(summary["external_subsystems"]["kanto"], "not_run")

    def test_mixed_pass_fail_never_passes(self):
        rows = [{"status": "passed", "id": "a", "returncode": 0, "command": [], "tail": ""},
                {"status": "failed", "id": "b", "returncode": 1, "command": [], "tail": ""}]
        self.assertEqual(ci.summarize("ruby", rows)["status"], "failed")

    def test_all_blocked_never_passes(self):
        rows = [{"status": "blocked", "id": "x", "returncode": None, "command": [], "tail": ""}]
        self.assertEqual(ci.summarize("python", rows)["status"], "blocked")

    def test_empty_or_unknown_suite_fails_closed(self):
        with self.assertRaises(ValueError):
            ci.summarize("python", [])
        with self.assertRaises(ValueError):
            ci.summarize("kanto", [{"status": "passed"}])
        with self.assertRaises(ValueError):
            ci.summarize("python", [{"status": "success"}])

    def test_rejects_falsely_passing_exit_code(self):
        rows = [{"id": "sinnoh-forged", "status": "passed", "returncode": 7,
                 "command": ["python", "--bad"], "tail": ""}]
        with self.assertRaisesRegex(ValueError, "exit code 0"):
            ci.summarize("python", rows)

    def test_rejects_falsely_blocked_with_process_exit(self):
        rows = [{"id": "sinnoh-forged", "status": "blocked", "returncode": 0,
                 "command": ["python"], "tail": ""}]
        with self.assertRaisesRegex(ValueError, "blocked"):
            ci.summarize("ruby", rows)

    def test_timeout_is_failed_not_certified(self):
        with tempfile.TemporaryDirectory() as d:
            result = ci.run_check("sinnoh-intentional-timeout",
                                  [sys.executable, "-c", "import time;time.sleep(2)"],
                                  Path(d), timeout=1)
        self.assertEqual(result["status"], "failed")
        self.assertIsNone(result["returncode"])
        self.assertEqual(ci.summarize("python", [result])["status"], "failed")

    def test_reports_are_machine_readable_and_never_claim_native_pass(self):
        sample = {"id": "sinnoh-offline", "command": [sys.executable], "status": "passed",
                  "returncode": 0, "tail": ""}
        report = ci.summarize("ruby", [sample])
        with tempfile.TemporaryDirectory() as d:
            ci.save_report(report, Path(d))
            loaded = json.loads((Path(d) / "sinnoh-ch19-ruby.json").read_text("utf-8"))
            md = (Path(d) / "sinnoh-ch19-ruby.md").read_text("utf-8")
        self.assertEqual(loaded["region"], "sinnoh")
        self.assertFalse(loaded["gameplay_certified"])
        self.assertIn("não certifica Game.exe/JoiPlay", md)
        self.assertIn("Kanto/Johto/Hoenn não executados", md)


if __name__ == "__main__":
    unittest.main()
