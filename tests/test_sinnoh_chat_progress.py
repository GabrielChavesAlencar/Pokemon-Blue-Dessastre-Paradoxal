"""CH02: positive and tamper tests for the Sinnoh ChatGPT progress ledger."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.regions.validate_sinnoh_chat_progress import (
    LEDGER, MAP, PANEL, ROOT, validate,
)

SCRIPT = "scripts/regions/validate_sinnoh_chat_progress.py"


class SinnohChatProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        ledger = json.loads((ROOT / LEDGER).read_text(encoding="utf-8"))
        done_artifacts = [task["evidence_path"]
                          for task in ledger["chat_direct_workstream"]["tasks"]
                          if task["status"] == "done"]
        for relative in sorted(set((LEDGER, MAP, PANEL, SCRIPT, *done_artifacts))):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, destination)

    def read(self):
        return json.loads((self.root / LEDGER).read_text(encoding="utf-8"))

    def write(self, record):
        (self.root / LEDGER).write_text(
            json.dumps(record, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )

    def replace(self, path, old, new):
        file = self.root / path
        content = file.read_text(encoding="utf-8")
        self.assertIn(old, content)
        file.write_text(content.replace(old, new, 1), encoding="utf-8")

    def failed(self, piece):
        errors = validate(self.root)
        self.assertTrue(errors, "a alteração deveria ser rejeitada")
        self.assertTrue(any(piece in error for error in errors), errors)

    def test_actual_checkout_and_copied_files_validate(self):
        self.assertEqual(validate(ROOT), [])
        self.assertEqual(validate(self.root), [])

    def test_cli_accepts_valid_read_only_checkout(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / SCRIPT), "--root", str(self.root)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("SINNOH_CHAT_PROGRESS_OK", result.stdout)

    def test_rejects_wrong_status_counters(self):
        data = self.read()
        data["chat_direct_workstream"]["pending"] += 1
        self.write(data)
        self.failed("chat_direct_workstream.pending")

    def test_rejects_unknown_or_duplicate_ids(self):
        data = self.read()
        data["chat_direct_workstream"]["tasks"][3]["id"] = "CH02"
        self.write(data)
        self.failed("IDs CH01")
        data["chat_direct_workstream"]["tasks"][3]["id"] = "CH04"
        data["chat_direct_workstream"]["tasks"][3]["status"] = "ok"
        self.write(data)
        self.failed("status desconhecido")

    def test_rejects_wrong_percentage(self):
        data = self.read()
        data["chat_direct_workstream"]["percent_complete"] = 80
        self.write(data)
        self.failed("percent_complete")

    def test_rejects_missing_done_artifact_and_path_escape(self):
        data = self.read()
        data["chat_direct_workstream"]["tasks"][1]["evidence_path"] = "missing.py"
        self.write(data)
        self.failed("evidência ausente")
        data["chat_direct_workstream"]["tasks"][1]["evidence_path"] = "../../tmp/file.py"
        self.write(data)
        self.failed("fora do repositório")

    def test_rejects_missing_bar_and_wrong_fill(self):
        done = self.read()["chat_direct_workstream"]["done"]
        self.replace(PANEL, "█" * done + "░" * (20 - done),
                     "█" * (done - 1) + "░" * (21 - done))
        self.failed("preenchimento gráfico")

    def test_rejects_panel_counter_mismatch(self):
        pending = self.read()["chat_direct_workstream"]["pending"]
        self.replace(PANEL, f"- **Pendentes:** {pending}",
                     f"- **Pendentes:** {pending + 1}")
        self.failed("contador Pendentes")

    def test_rejects_mapping_counter_mismatch(self):
        pending = self.read()["chat_direct_workstream"]["pending"]
        self.replace(MAP, f"**{pending} pendentes**",
                     f"**{pending + 1} pendentes**")
        self.failed("mapeamento: contador pending")

    def test_rejects_missing_completed_marker(self):
        self.replace(MAP, "| P0 | **CH02** ✅ |", "| P0 | CH02 |")
        self.failed("marcador incorreto")

    def test_rejects_duplicate_mapping_row(self):
        content = (self.root / MAP).read_text(encoding="utf-8")
        row = next(line for line in content.splitlines()
                   if line.startswith("| P4 |") and "CH20" in line)
        self.replace(MAP, row, row.replace("CH20", "CH02", 1))
        self.failed("mapeamento: ID/prioridade")

    def test_rejects_changed_priorities(self):
        data = self.read()
        data["chat_direct_workstream"]["tasks"][2]["priority"] = "P4"
        self.write(data)
        self.failed("mapeamento: ID/prioridade")

    def test_rejects_changed_phase_gate_without_panel(self):
        data = self.read()
        data["phase_gates"]["fully_tested_native"] = 1
        self.write(data)
        self.failed("Barra D")

    def test_rejects_corrupted_ledger_and_missing_map(self):
        (self.root / LEDGER).write_text("{bad json", encoding="utf-8")
        self.failed("arquivos de progresso")
        self.write(json.loads((ROOT / LEDGER).read_text(encoding="utf-8")))
        (self.root / MAP).unlink()
        self.failed("arquivos de progresso")


if __name__ == "__main__":
    unittest.main()
