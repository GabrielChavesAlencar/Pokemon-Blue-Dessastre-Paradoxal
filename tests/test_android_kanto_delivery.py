"""Exercise the release gate against ZIPs with missing non-Cerulean maps."""
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import zlib

from scripts.android.verify_kanto_cerulean import assert_delivery, EDGES, JOURNEY, KANTO_RUNTIME
from scripts.official_rules.prepare_restore import RubyString, dump

ROOT = Path(__file__).resolve().parents[1]


class KantoDeliveryTests(unittest.TestCase):
    def fixture(self, channel, omit=None, short=None, omit_rival=False):
        manifest = json.loads((ROOT / "data/regions/kanto-source.json").read_text("utf8"))
        mapping = {source: 600 + index for index, source in enumerate(manifest["maps"])}
        root, marker = (("Pokemon-Blue-Kanto-Android/", "Kanto pilot.json")
                        if channel == "kanto" else
                        ("Pokemon-Blue-Android/", "Data/blue-kanto-install.json"))
        source = (ROOT / "scripts/battle_polish/Journey.rb").read_bytes()
        travel = (ROOT / "scripts/battle_polish/RegionTravel.rb").read_bytes()
        rival = (ROOT / "scripts/regions/KantoPilot.rb").read_bytes()
        scripts = [[RubyString(b"Journey.rb"), RubyString(zlib.compress(source))],
                   [RubyString(b"RegionTravel.rb"), RubyString(zlib.compress(travel))],
                   [RubyString(b"KantoPilot.rb"), RubyString(zlib.compress(rival))]]
        cache = b"\x04\x08" + dump([[RubyString(b"Story"), None, scripts]])
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        target = Path(directory.name) / "android.zip"
        with ZipFile(target, "w") as archive:
            archive.writestr(root + marker, json.dumps({"maps": mapping}))
            for original, destination in mapping.items():
                if original != omit:
                    archive.writestr(root + f"Data/Map{destination:03}.rxdata",
                                     b"map" if original == short else b"m" * 128)
            archive.writestr(root + "PBS/map_connections_kanto.txt", "\n".join(
                f"{mapping[a]},North,0,{mapping[b]},South,0" for a, b in EDGES))
            archive.writestr(root + "PBS/trainers_kanto.txt",
                             "[BLUE_KANTO_SWIMMER,Luis,0]\n[BLUE_KANTO_PICNICKER,Diana,0]\n" +
                             "\n".join(f"[BLUE_KANTO_RIVAL,Blue,{v}]" for v in (31, 32, 33)))
            if not omit_rival:
                archive.writestr(root + KANTO_RUNTIME, rival)
            archive.writestr(root + JOURNEY, source)
            archive.writestr(root + "Plugins/ZZZZ Blue Story and Presentation/RegionTravel.rb", travel)
            archive.writestr(root + "Data/PluginScripts.rxdata", cache)
            archive.writestr(root + "Data/blue-kanto-music.txt", "MAP\tfixture\n" * 77)
        return target

    def test_all_maps_and_compiled_luis_guard_pass_in_both_channels(self):
        for channel in ("kanto", "multiregion"):
            with self.subTest(channel=channel):
                self.assertEqual(assert_delivery(self.fixture(channel), channel)["kanto_maps"], 145)

    def test_gary_runtime_cannot_be_omitted(self):
        for channel in ("kanto", "multiregion"):
            with self.subTest(channel=channel):
                with self.assertRaisesRegex(ValueError, "Gary runtime missing"):
                    assert_delivery(self.fixture(channel, omit_rival=True), channel)

    def test_missing_pallet_map_is_rejected_even_with_cerulean_present(self):
        for channel in ("kanto", "multiregion"):
            with self.subTest(channel=channel):
                with self.assertRaisesRegex(ValueError, "Map5 was not compiled"):
                    assert_delivery(self.fixture(channel, omit="5"), channel)

    def test_truncated_non_cerulean_map_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Map24 was not compiled"):
            assert_delivery(self.fixture("kanto", short="24"), "kanto")


if __name__ == "__main__":
    unittest.main()
