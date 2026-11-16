"""CH10: isolated Sinnoh QA launcher/preflight guards — synthetic inputs only."""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

from install_sinnoh_qa_copy import (
    BARRY_READY, COMPILED, COMPILE_ERROR, COMPILE_REQUEST, ENGINE_REPORT,
    QA_META, PROBE_PLUGIN, START_PLUGIN, install, prepare, verify,
)
from launch_sinnoh_qa import preflight, run
from test_sinnoh_qa_install import fixture, simulate_native_report


def hash_tree(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob("*") if p.is_file()}


class SinnohCH10QALauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sinnoh-ch10-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.base, self.bundle, self.spec = fixture(self.root)
        self.base_hashes = hash_tree(self.base)
        self.qa = self.root / ".blue-work/game-sinnoh-qa-abcdef123456"
        self.report, self.blobs, self.native = prepare(
            self.base, self.bundle, self.spec, token="abcdef123456",
            project=self.root)
        install(self.root, self.base, self.qa,
                self.report, self.blobs, self.native)

    def safe(self):
        self.assertEqual(hash_tree(self.base), self.base_hashes)
        self.assertFalse((self.base / BARRY_READY).exists())
        self.assertFalse((self.base / COMPILED).exists())

    def native_proof(self):
        meta = json.loads((self.qa / QA_META).read_text("utf-8"))
        simulate_native_report(self.qa)
        # Existing test helper writes this report; do not use its return.
        self.assertTrue((self.qa / ENGINE_REPORT).is_file())
        (self.qa / COMPILED).write_text(
            meta["compile_token"] + "\n", encoding="ascii")
        (self.qa / COMPILE_REQUEST).unlink()
        return meta

    def test_initial_preflight_is_pending_never_gameplay_or_fallback(self):
        d = preflight(self.qa, project=self.root)
        self.assertEqual(d["requested_action"], "check")
        self.assertTrue(d["compile_request_pending"])
        self.assertTrue(d["required_launcher_assets_verified"])
        self.assertTrue(d["no_foreign_save_in_qa"])
        self.assertFalse(d["ready_to_launch_for_manual_testing"])
        self.assertFalse(d["gameplay_approved"])
        self.assertFalse(d["fallback_to_other_region"])
        d = run(self.qa, project=self.root)
        self.assertFalse(d["process_started"])
        self.safe()

    def test_compilation_is_explicit_and_only_launches_private_exe(self):
        with patch("launch_sinnoh_qa.subprocess.Popen") as popen:
            popen.return_value.pid = 12345
            result = run(self.qa, project=self.root, mode="compile")
            self.assertEqual(result["pid"], 12345)
            self.assertTrue(result["process_started"])
            self.assertFalse(result["gameplay_approved"])
            popen.assert_called_once_with(
                [str(self.qa / "Game.exe")], cwd=str(self.qa), shell=False)
        self.safe()

    def test_launch_requires_native_engine_report_and_never_falls_back(self):
        with patch("launch_sinnoh_qa.subprocess.Popen") as popen:
            with self.assertRaisesRegex(ValueError, "compilação"):
                run(self.qa, project=self.root, mode="launch")
            popen.assert_not_called()
        self.safe()

    def test_compiled_engine_report_enables_private_manual_test_only(self):
        meta = json.loads((self.qa / QA_META).read_text("utf-8"))
        simulate_native_report(self.qa)
        (self.qa / COMPILED).write_text(
            meta["compile_token"] + "\n", encoding="ascii")
        (self.qa / COMPILE_REQUEST).unlink()
        with patch("launch_sinnoh_qa.subprocess.Popen") as popen:
            popen.return_value.pid = 812
            report = run(self.qa, project=self.root, mode="launch")
            self.assertTrue(report["ready_to_launch_for_manual_testing"])
            self.assertFalse(report["gameplay_approved"])
            self.assertFalse(report["fallback_to_other_region"])
            popen.assert_called_once_with(
                [str(self.qa / "Game.exe")], cwd=str(self.qa), shell=False)
            with self.assertRaisesRegex(ValueError, "não está pendente"):
                run(self.qa, project=self.root, mode="compile")
            popen.assert_called_once()
        self.safe()

    def test_missing_runtime_executable_or_plugins_blocks(self):
        for rel in ("Game.exe", START_PLUGIN, PROBE_PLUGIN,
                    "Plugins/ZZZZZ Blue Sinnoh Intro/SinnohPilot.rb",
                    "Data/Scripts.rxdata"):
            with self.subTest(path=rel):
                file = self.qa / rel
                raw = file.read_bytes()
                file.unlink()
                with self.assertRaisesRegex(ValueError, "crítico|protegido"):
                    preflight(self.qa, project=self.root, mode="compile")
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(raw)
        self.safe()

    def test_tampered_runtime_scripts_config_and_binary_block(self):
        for rel in ("Game.exe", START_PLUGIN, PROBE_PLUGIN,
                    "mkxp.json", "Game.ini"):
            with self.subTest(path=rel):
                p = self.qa / rel
                original = p.read_bytes()
                p.write_bytes(original + b"\nCH10 tamper")
                with self.assertRaisesRegex(ValueError, "crítico|protegido"):
                    preflight(self.qa, project=self.root)
                p.write_bytes(original)
        self.safe()

    def test_removed_assets_fonts_graphics_audio_block(self):
        for name in ("Audio", "Graphics", "Fonts"):
            with self.subTest(name=name):
                directory = self.qa / name
                hidden = self.qa / ("CH10-" + name)
                directory.rename(hidden)
                with self.assertRaisesRegex(ValueError, "Assets"):
                    preflight(self.qa, project=self.root)
                hidden.rename(directory)
        self.safe()

    def test_foreign_region_save_cannot_be_inherited(self):
        for filename in ("Saves/Slot1.rxdata", "Savedata/Johto.sav",
                         "Save/Decades.sav", "Data/File A.rxdata"):
            with self.subTest(path=filename):
                p = self.qa / filename
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes(b"fake foreign save for isolated test")
                with self.assertRaisesRegex(ValueError, "Save incompatível"):
                    preflight(self.qa, project=self.root)
                p.unlink()
        self.safe()

    def test_transaction_cannot_claim_another_save_profile(self):
        txn = self.qa / "sinnoh-qa-transaction.json"
        original = txn.read_bytes()
        bad = json.loads(original)
        bad["save_isolation"]["dataPathApp"] = "Decades Main"
        txn.write_text(json.dumps(bad), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Perfil da transação"):
            preflight(self.qa, project=self.root)
        txn.write_bytes(original)
        self.safe()

    def test_missing_or_changed_install_proof_blocks_launch(self):
        file = self.qa / QA_META
        original = file.read_bytes()
        file.write_bytes(original + b"\n")
        with self.assertRaisesRegex(ValueError, "Prova de instalação"):
            preflight(self.qa, project=self.root)
        file.write_bytes(original)
        txn = self.qa / "sinnoh-qa-transaction.json"
        original = txn.read_bytes()
        forged = json.loads(original)
        forged.pop("qa_launch_sha256")
        txn.write_text(json.dumps(forged), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Manifesto do lançador"):
            preflight(self.qa, project=self.root)
        txn.write_bytes(original)
        self.safe()

    def test_invalid_compile_request_or_missing_request_fail_closed(self):
        request = self.qa / COMPILE_REQUEST
        old = request.read_bytes()
        request.write_text("0" * 64, encoding="ascii")
        with self.assertRaisesRegex(ValueError, "Pedido de compilação"):
            preflight(self.qa, project=self.root, mode="compile")
        request.unlink()
        with self.assertRaisesRegex(ValueError, "sem pedido"):
            preflight(self.qa, project=self.root)
        request.write_bytes(old)
        self.safe()

    def test_compiled_token_alone_cannot_start_qa(self):
        meta = json.loads((self.qa / QA_META).read_text("utf-8"))
        (self.qa / COMPILED).write_text(meta["compile_token"], encoding="ascii")
        (self.qa / COMPILE_REQUEST).unlink()
        with patch("launch_sinnoh_qa.subprocess.Popen") as popen:
            with self.assertRaisesRegex(ValueError, "sem relatório"):
                run(self.qa, project=self.root, mode="launch")
            popen.assert_not_called()
        self.safe()

    def test_qa_symlinked_game_and_paths_or_main_game_refused(self):
        with self.assertRaisesRegex(ValueError, "dentro"):
            preflight(self.base, project=self.root, mode="compile")
        link = self.qa / "Game.exe"
        contents = link.read_bytes()
        link.unlink()
        try:
            link.symlink_to(self.base / "Game.exe")
        except (OSError, NotImplementedError):
            link.write_bytes(contents)
            self.skipTest("Symlinks unavailable")
        with self.assertRaisesRegex(ValueError, "crítico|protegido"):
            preflight(self.qa, project=self.root)
        link.unlink()
        link.write_bytes(contents)
        self.safe()

    def test_atomic_install_failure_cleans_partial_directory(self):
        second = self.root / ".blue-work/game-sinnoh-qa-secondary"
        with patch("install_sinnoh_qa_copy.os.fsync",
                   side_effect=OSError("CH10 synthetic disk error")):
            with self.assertRaisesRegex(OSError, "CH10 synthetic disk error"):
                install(self.root, self.base, second,
                        self.report, self.blobs, self.native)
        self.assertFalse(second.exists())
        self.assertFalse(any(p.name.startswith(".sinnoh-qa-pending-")
                             for p in second.parent.iterdir()))
        self.safe()


if __name__ == "__main__":
    unittest.main()
