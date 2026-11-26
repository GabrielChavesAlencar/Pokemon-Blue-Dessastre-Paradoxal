"""Exercise the release gate against ZIPs with missing non-Cerulean maps."""
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import zlib

from scripts.android.verify_kanto_cerulean import assert_delivery, EDGES, JOURNEY, KANTO_RUNTIME
from scripts.official_rules.prepare_restore import RubyString, dump
from server.ruby_marshal import integer


def ticket_catalog(omit_bike=False, invalid_dig=False):
    # Minimal inert Ruby Marshal fixture matching native GameData::Item.
    def sym(value):
        raw = value.encode("ascii")
        return b":" + integer(len(raw)) + raw
    ids = ["BLUE_KANTO_SSTICKET", "BIKEVOUCHER", "TM28"]
    if not omit_bike:
        ids.append("BICYCLE")
    records = []
    for key in ids:
        attrs = {"@id": sym(key), "@pocket": dump(8),
                 "@price": dump(0), "@consumable": dump(False),
                 "@flags": dump([RubyString(b"KeyItem")])}
        if key == "TM28":
            attrs = {"@id": sym(key), "@pocket": dump(9), "@price": dump(2000),
                     "@consumable": dump(True), "@flags": dump([RubyString(b"Fling_80")]),
                     "@field_use": dump(5), "@move": sym("CUT" if invalid_dig else "DIG")}
        record = b"o" + sym("GameData::Item") + integer(len(attrs)) + b"".join(
            sym(name) + value for name, value in attrs.items())
        records.append(sym(key) + record)
    return b"\x04\x08{" + integer(len(records)) + b"".join(records)

ROOT = Path(__file__).resolve().parents[1]


class KantoDeliveryTests(unittest.TestCase):
    def fixture(self, channel, omit=None, short=None, omit_rival=False, omit_ticket=False, omit_bike=False, invalid_dig=False):
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
                             "[BLUE_KANTO_SWIMMER,Luis,0]\n[BLUE_KANTO_PICNICKER,Diana,0]\n[BLUE_KANTO_ROCKET,Grunt,6]\n" +
                             "\n".join(f"[BLUE_KANTO_RIVAL,Blue,{v}]" for v in (31, 32, 33)))
            if not omit_rival:
                archive.writestr(root + KANTO_RUNTIME, rival)
            archive.writestr(root + JOURNEY, source)
            archive.writestr(root + "Plugins/ZZZZ Blue Story and Presentation/RegionTravel.rb", travel)
            archive.writestr(root + "Data/PluginScripts.rxdata", cache)
            archive.writestr(root + "Data/items.dat", b"\x04\x08{\x00" if omit_ticket else ticket_catalog(omit_bike, invalid_dig))
            archive.writestr(root + "Data/blue-kanto-music.txt", "MAP\tfixture\n" * 83)
        return target

    def test_all_maps_and_compiled_luis_guard_pass_in_both_channels(self):
        for channel in ("kanto", "multiregion"):
            with self.subTest(channel=channel):
                self.assertEqual(assert_delivery(self.fixture(channel), channel)["kanto_maps"], 151)

    def test_gary_runtime_cannot_be_omitted(self):
        for channel in ("kanto", "multiregion"):
            with self.subTest(channel=channel):
                with self.assertRaisesRegex(ValueError, "Gary runtime missing"):
                    assert_delivery(self.fixture(channel, omit_rival=True), channel)

    def test_missing_compiled_ticket_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Compiled Kanto S.S. Ticket"):
            assert_delivery(self.fixture("multiregion", omit_ticket=True), "multiregion")

    def test_missing_compiled_bicycle_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Compiled Cerulean key item missing or invalid: BICYCLE"):
            assert_delivery(self.fixture("multiregion", omit_bike=True), "multiregion")

    def test_wrong_compiled_dig_machine_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "TM28/DIG machine"):
            assert_delivery(self.fixture("multiregion", invalid_dig=True), "multiregion")

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
