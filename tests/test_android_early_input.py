"""Regression: user screenshot shows Input line 28 missing mouse_in_window on JoiPlay.

The compatibility shim must run *inside the first Input script*, before the
late Mobile.rb plugin and only for the Android distribution.
"""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
import zlib
from pathlib import Path

from scripts.android import early_input
from scripts.official_rules.prepare_restore import Marshal, RubyString, dump


class EarlyInputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.game = Path(self.tmp.name)
        data = self.game / "Data"
        data.mkdir()
        self.input = b"module Input\n  def self.touch; Input.mouse_in_window; end\nend\n"
        self.other = b"$no_change = 42\n"
        rows = [
            [1, RubyString(b"Other"), RubyString(zlib.compress(self.other))],
            [2, RubyString(b"Input"), RubyString(zlib.compress(self.input))],
        ]
        (data / "Scripts.rxdata").write_bytes(b"\x04\x08" + dump(rows))

    def patched_script(self):
        rows = Marshal((self.game / "Data/Scripts.rxdata").read_bytes()).read()
        self.assertEqual(zlib.decompress(rows[0][2]), self.other)
        return zlib.decompress(rows[1][2]).decode("utf8")

    def test_injects_before_original_input_and_is_idempotent(self):
        before = self.patched_script()
        self.assertIn("mouse_in_window", before)
        self.assertNotIn(early_input.MARKER, before)
        self.assertTrue(early_input.install(self.game))
        packed = (self.game / "Data/Scripts.rxdata").read_bytes()
        self.assertTrue(self.patched_script().startswith(early_input.EARLY_BOOTSTRAP))
        self.assertEqual(self.patched_script().count(early_input.MARKER), 1)
        early_input.verify(packed)
        self.assertFalse(early_input.install(self.game))
        self.assertEqual((self.game / "Data/Scripts.rxdata").read_bytes(), packed)

    def test_refuses_missing_input_and_prevents_unfixed_release(self):
        with self.assertRaisesRegex(ValueError, "pre-plugin"):
            early_input.verify((self.game / "Data/Scripts.rxdata").read_bytes())
        rows = Marshal((self.game / "Data/Scripts.rxdata").read_bytes()).read()
        rows[1][1] = RubyString(b"NotInput")
        (self.game / "Data/Scripts.rxdata").write_bytes(b"\x04\x08" + dump(rows))
        with self.assertRaisesRegex(ValueError, "exactly one"):
            early_input.install(self.game)

    def test_early_call_works_on_mobile_and_does_not_change_windows(self):
        ruby = shutil.which("ruby")
        if not ruby:
            self.skipTest("Ruby unavailable in local Python environment")
        early_input.install(self.game)
        script = self.patched_script()
        for platform in ("android", "windows"):
            with self.subTest(platform=platform):
                marker = self.game / "Data/blue-mobile.txt"
                if platform == "android":
                    marker.write_text("experimental-v1")
                else:
                    marker.unlink(missing_ok=True)
                snippet = (
                    script +
                    "\nif File.file?('Data/blue-mobile.txt')\n"
                    "  raise 'JoiPlay touch failed before plugins load' unless Input.touch == true\n"
                    "else\n"
                    "  raise 'Windows received the Android shim' if Input.respond_to?(:mouse_in_window)\n"
                    "end\n"
                )
                executed = subprocess.run(
                    [ruby, "-e", snippet], cwd=self.game, text=True, capture_output=True,
                )
                self.assertEqual(executed.returncode, 0, executed.stderr)


if __name__ == "__main__":
    unittest.main()
