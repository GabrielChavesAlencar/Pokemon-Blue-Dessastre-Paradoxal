"""Phase 16: preflight is read-only, installed Johto is never assumed."""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "scripts/regions/install_johto.py"
SPEC = importlib.util.spec_from_file_location("johto_install_preflight", PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class JohtoReleaseTests(unittest.TestCase):
    def test_no_map_pack_no_pbs_no_hall_of_fame_means_no_real_release(self):
        report = AUDIT.audit(ROOT)
        self.assertEqual(report["schema"], 1)
        self.assertEqual(report["region"], "JOHTO")
        self.assertEqual(report["phase"], "16/16")
        self.assertEqual(report["status"], "BLOCKED_AWAITING_ASSETS")
        self.assertTrue(report["dry_run"])
        self.assertFalse(report["apply_supported"])
        self.assertEqual(report["game_files_modified"], 0)
        self.assertEqual(report["technical_full_acceptance"], 0)
        self.assertEqual(report["gameplay_full_acceptance"], 0)
        self.assertEqual(len(report["phases"]), 16)
        self.assertTrue(all(not row["real_gameplay_accepted"] for row in report["phases"]))
        self.assertTrue(all(not row["integrated_and_verified"]
                            for row in report["phases"]))
        self.assertGreaterEqual(len(report["blockers"]), 12)
        full_text = "\n".join(report["blockers"])
        self.assertIn("SHA-256", full_text)
        self.assertIn("MapIDs", full_text)
        self.assertIn("PBS", full_text)
        self.assertIn("direitos", full_text.lower())
        self.assertIn("Piloto", full_text)

    def test_missing_source_manifest_is_denied_not_accepted(self):
        original = AUDIT.read_json
        def unavailable(path):
            if path.name == "johto-source.json":
                return {"region": "JOHTO", "source": {}}
            return original(path)
        with mock.patch.object(AUDIT, "read_json", side_effect=unavailable):
            report = AUDIT.audit(ROOT)
        self.assertEqual(report["status"], "BLOCKED_AWAITING_ASSETS")
        self.assertGreaterEqual(len(report["blockers"]), 3)
        self.assertIsNone(report["source_archive_sha256"])

    def test_release_proof_requires_all_thirteen_real_criteria(self):
        start = (ROOT / "scripts/battle_polish/RegionStart.rb").read_text("utf-8")
        travel = (ROOT / "scripts/battle_polish/RegionTravel.rb").read_text("utf-8")
        for name in AUDIT.RELEASE_PROOFS:
            self.assertIn(name, start)
        self.assertEqual(len(AUDIT.RELEASE_PROOFS), 13)
        for line in (
            'data["status"] == "VERIFIED_PLAYABLE"',
            'Digest::SHA256.file(name).hexdigest == hash',
            'proof["travel_point"]',
            'proof["npc_point"]',
            'JOHTO_MARKER',
            "def self.johto_spawn",
        ):
            self.assertIn(line, start)
        for line in (
            "def self.johto_installed?",
            'when "JOHTO"',
            'state["leagues"].include?("JOHTO")',
            'BlueRegionStart.johto_town_point',
            'BlueRegionStart.johto_agent_point',
            "def self.attach_johto_agent",
            'BlueRegionTravel.attach_johto_agent(self)',
            "def self.free_storage_slots",
            "def self.perform",
        ):
            self.assertIn(line, travel)
        self.assertIn('"Data/blue-kanto-install.json"', travel)
        self.assertIn('state["current"] == "DECADES"', travel)

    def test_command_dry_run_works_and_strict_apply_refuse(self):
        base = [sys.executable, str(PATH), "--root", str(ROOT)]
        process = subprocess.run(base + ["--dry-run"], capture_output=True,
                                 text=True, encoding="utf-8", timeout=25)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertEqual(json.loads(process.stdout)["status"],
                         "BLOCKED_AWAITING_ASSETS")
        strict = subprocess.run(base + ["--strict"], capture_output=True,
                                text=True, encoding="utf-8", timeout=25)
        self.assertEqual(strict.returncode, 2)
        apply = subprocess.run(base + ["--apply"], capture_output=True,
                               text=True, encoding="utf-8", timeout=25)
        self.assertEqual(apply.returncode, 2)
        self.assertIn("BLOQUEADO", apply.stderr)
        self.assertIn('"game_files_modified": 0', apply.stdout)

    def test_report_can_only_be_new_file_inside_isolated_blue_work(self):
        report = {"status": "BLOCKED_AWAITING_ASSETS"}
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".blue-work").mkdir()
            target = root / ".blue-work" / "johto-audit.json"
            AUDIT.save_report(report, target, root)
            self.assertEqual(json.loads(target.read_text("utf-8")), report)
            with self.assertRaisesRegex(ValueError, "novo"):
                AUDIT.save_report(report, target, root)
            with self.assertRaises(ValueError):
                AUDIT.save_report(report, root / "game" / "Data" / "danger.json", root)

    def test_phase15_and_phase14_are_not_fake_acceptance_signals(self):
        preview = json.loads(
            (ROOT / "site/public/data/johto-preview.json").read_text("utf-8")
        )
        source = json.loads(
            (ROOT / "data/regions/johto-source.json").read_text("utf-8")
        )
        audio = json.loads(
            (ROOT / "data/johto-music.json").read_text("utf-8")
        )
        self.assertEqual(preview["maps_installed"], 0)
        self.assertEqual(preview["trainers_compiled"], 0)
        self.assertFalse(source["mapping_verified"])
        self.assertFalse(source["import_enabled"])
        self.assertIsNone(source["source"]["archive_sha256"])
        self.assertFalse(audio["license_verified"])
        self.assertEqual(audio["recordings"], [])


if __name__ == "__main__":
    unittest.main()
