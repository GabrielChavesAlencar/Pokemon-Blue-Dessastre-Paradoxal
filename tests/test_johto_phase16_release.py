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
        self.assertRegex(report["source_archive_sha256"], r"^[a-f0-9]{64}$")
        self.assertNotIn("SHA-256 da fonte não fixado", full_text)
        self.assertNotIn("MapIDs e warps reais de Johto não auditados", full_text)
        self.assertIn("Instalação local game/Data/MapInfos.rxdata", full_text)
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
        self.assertTrue(source["mapping_verified"])
        self.assertEqual(len(source["maps"]), 74)
        self.assertFalse(source["import_enabled"])
        self.assertFalse(source["source"]["distribution_approved"])
        self.assertRegex(source["source"]["archive_sha256"], r"^[a-f0-9]{64}$")
        self.assertFalse(audio["license_verified"])
        self.assertEqual(audio["recordings"], [])


class JohtoReleaseIntegrityTests(unittest.TestCase):
    """Byte-for-byte pilot gates; mocks NEVER certify real gameplay."""

    @staticmethod
    def synthetic_pilot(root: Path):
        import hashlib
        source_path = root / "data/regions/johto-source.json"
        source_path.parent.mkdir(parents=True)
        source_hash = "a" * 64
        source_path.write_text(json.dumps({
            "schema": 1, "region": "JOHTO",
            "source": {"archive_sha256": source_hash}
        }), encoding="utf-8")
        pilot = root / ".blue-work/johto-pilot"
        data = pilot / "Data"
        data.mkdir(parents=True)
        files = {}
        for name in ("MapInfos.rxdata", "Tilesets.rxdata",
                     "Map700.rxdata", "Map701.rxdata"):
            raw = f"synthetic-only-not-gameplay:{name}".encode()
            (data / name).write_bytes(raw)
            files[f"Data/{name}"] = hashlib.sha256(raw).hexdigest()
        proof = {
            "schema": 1, "region": "JOHTO", "status": "VERIFIED_PLAYABLE",
            "source_archive_sha256": source_hash,
            "checks": {k: True for k in AUDIT.RELEASE_PROOFS},
            "start": [700, 4, 6, 2],
            "travel_point": [701, 10, 11, 2],
            "npc_point": [701, 11, 11, 4],
            "file_hashes": files,
        }
        manifest = data / "blue-johto-install.json"
        manifest.write_text(json.dumps(proof), encoding="utf-8")
        (data / "blue-johto-start.txt").write_text(
            "BLUE_JOHTO_START_V1,JOHTO,700,4,6\n", encoding="utf-8")
        return pilot, proof, manifest

    def test_pilot_hashes_have_to_match_all_real_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pilot, _, _ = self.synthetic_pilot(root)
            # Passing checks validates only file integrity, never gameplay QA.
            self.assertEqual(AUDIT.verify_pilot_package(root, pilot), [])
            (pilot / "Data/Map701.rxdata").write_bytes(b"modified")
            blockers = AUDIT.verify_pilot_package(root, pilot)
            self.assertTrue(any("modificado" in x for x in blockers), blockers)

    def test_rejects_fake_checks_source_hash_and_wrong_spawn(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pilot, proof, manifest = self.synthetic_pilot(root)
            proof["checks"]["windows_gameplay"] = False
            manifest.write_text(json.dumps(proof), encoding="utf-8")
            self.assertTrue(any("13 comprovantes" in x for x in
                                AUDIT.verify_pilot_package(root, pilot)))
            proof["checks"]["windows_gameplay"] = True
            proof["source_archive_sha256"] = "b" * 64
            manifest.write_text(json.dumps(proof), encoding="utf-8")
            self.assertTrue(any("fonte" in x for x in
                                AUDIT.verify_pilot_package(root, pilot)))
            proof["source_archive_sha256"] = "a" * 64
            proof["travel_point"] = [700, 4, 6, 2]
            manifest.write_text(json.dumps(proof), encoding="utf-8")
            self.assertTrue(any("pontos seguros" in x for x in
                                AUDIT.verify_pilot_package(root, pilot)))
            proof["travel_point"] = [701, 10, 11, 2]
            manifest.write_text(json.dumps(proof), encoding="utf-8")
            (pilot / "Data/blue-johto-start.txt").write_text(
                "BLUE_JOHTO_START_V1,JOHTO,700,999,6\n",
                encoding="utf-8")
            self.assertTrue(any("marcador" in x for x in
                                AUDIT.verify_pilot_package(root, pilot)))

    def test_cannot_approve_non_johto_mapids_or_symlinked_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pilot, proof, manifest = self.synthetic_pilot(root)
            proof["file_hashes"]["Data/Map005.rxdata"] = "a" * 64
            manifest.write_text(json.dumps(proof), encoding="utf-8")
            self.assertTrue(any("sobrescrever outra região" in x for x in
                                AUDIT.verify_pilot_package(root, pilot)))
            proof["file_hashes"].pop("Data/Map005.rxdata")
            manifest.write_text(json.dumps(proof), encoding="utf-8")
            physical = pilot / "Data/Map701.rxdata"
            physical.unlink()
            physical.symlink_to("Map700.rxdata")
            self.assertTrue(any("symlink" in x for x in
                                AUDIT.verify_pilot_package(root, pilot)))

    def test_cannot_redirect_report_through_symlink_or_apply(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "game/Data").mkdir(parents=True)
            (root / ".blue-work").symlink_to(root / "game", target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                AUDIT.save_report({}, root / ".blue-work/Data/unsafe.json", root)
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".blue-work").mkdir()
            unsafe = root / ".blue-work" / "should-not-exist.json"
            result = subprocess.run([
                sys.executable, str(PATH), "--root", str(root),
                "--apply", "--report", str(unsafe)
            ], capture_output=True, text=True, encoding="utf-8", timeout=20)
            self.assertEqual(result.returncode, 2)
            self.assertFalse(unsafe.exists(), "--apply wrote a report despite refusal")
            self.assertIn("BLOQUEADO", result.stderr)


if __name__ == "__main__":
    unittest.main()
