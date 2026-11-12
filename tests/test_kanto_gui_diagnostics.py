"""OS-independent checks for the Kanto Windows boot diagnostics."""
import sys
import unittest
from pathlib import Path

REGIONS = Path(__file__).resolve().parents[1] / "scripts" / "regions"
sys.path.insert(0, str(REGIONS))
try:
    from gui_diagnostics import classify
finally:
    sys.path.remove(str(REGIONS))


class KantoGuiDiagnosticsTest(unittest.TestCase):
    def test_physfs_error_takes_priority_over_generic_failure(self):
        self.assertEqual(classify(False, 1, "PhysFS initialization failed", ""), "physfs_error")

    def test_visible_window_is_not_treated_as_full_gameplay_validation(self):
        self.assertEqual(classify(True, None, "", ""), "window_observed_not_gameplay_verified")

    def test_game_process_early_exit_is_reported(self):
        self.assertEqual(classify(False, 1, "", ""), "process_failed")
        self.assertEqual(classify(False, 0, "", ""), "process_exited_without_visible_window")

    def test_headless_environment_is_inconclusive(self):
        self.assertEqual(classify(False, None, "", ""), "no_visible_window")


if __name__ == "__main__":
    unittest.main()
