"""Offline regression of the Android JoiPlay cache patch for map transitions.

No proprietary archives, executable, actual maps, saves, or network.
"""
import shutil
import subprocess
import unittest
import zlib
from pathlib import Path

from scripts.android.repack_multiregion_hotfix import replace_compiled_travel, TRAVEL
from server.ruby_marshal import loads

SOURCE = Path(__file__).resolve().parents[1] / "scripts/battle_polish/RegionTravel.rb"


def fixture(*names, unrecognized=False):
    ruby = r'''
require "zlib"
entries = ARGV.map do |name|
  old = name == "RegionTravel.rb" ?
    (ENV["BAD_TRAVEL"] ? "module Unrelated; end" : "module BlueRegionTravel; end") : "keep"
  [name, Zlib::Deflate.deflate(old)]
end
STDOUT.binmode.write(Marshal.dump([["Blue presentation", 1, entries]]))
'''
    env = None
    if unrecognized:
        import os
        env = dict(os.environ, BAD_TRAVEL="1")
    return subprocess.run(["ruby", "-e", ruby, *names],
                          env=env, check=True, capture_output=True).stdout


@unittest.skipUnless(shutil.which("ruby"), "Ruby runtime required for cache serializer")
class AndroidMapTransitionPackaging(unittest.TestCase):
    def test_region_travel_path_matches_real_plugin_install(self):
        self.assertEqual(TRAVEL, "Plugins/ZZZZ Blue Story and Presentation/RegionTravel.rb")
        source = SOURCE.read_bytes()
        self.assertIn(b"def self.agent_map_id(region)", source)
        self.assertIn(b"def self.attach_agents(map)", source)

    def test_exact_cache_entry_patched_without_touching_other_plugins(self):
        old = fixture("RegionTravel.rb", "Unchanged.rb")
        replacement = SOURCE.read_bytes()
        result = replace_compiled_travel(old, replacement)
        decoded = loads(result)
        entries = decoded[0][2]
        self.assertEqual(zlib.decompress(entries[0][1]), replacement)
        self.assertEqual(zlib.decompress(entries[1][1]), b"keep")
        self.assertNotEqual(result, old)

    def test_missing_or_duplicate_compiled_entry_fails_closed(self):
        for names in [("Unchanged.rb",),
                      ("RegionTravel.rb", "RegionTravel.rb")]:
            with self.subTest(entries=names):
                with self.assertRaisesRegex(ValueError, "exactly one compiled RegionTravel"):
                    replace_compiled_travel(fixture(*names), SOURCE.read_bytes())

    def test_unknown_plugin_content_is_never_overwritten(self):
        old = fixture("RegionTravel.rb", unrecognized=True)
        with self.assertRaisesRegex(ValueError, "Unknown compiled BlueRegionTravel"):
            replace_compiled_travel(old, SOURCE.read_bytes())


if __name__ == "__main__":
    unittest.main()
