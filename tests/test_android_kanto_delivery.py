"""Exercise the release gate against ZIPs with missing non-Cerulean maps."""
import json
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile
import zlib

from scripts.android.verify_kanto_cerulean import assert_delivery, EDGES, JOURNEY, KANTO_RUNTIME, KANTO_ATLAS, CERULEAN_DOORS
from scripts.regions.kanto_wall_atlas import render_wall_atlas
from scripts.regions.k03e_contract import MAPS, TRAINERS, MUSIC
from scripts.android.verify_kanto_cerulean import verify_k03e, k03e_audio_paths
from scripts.regions.k04_corridor import published_destinations
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

def city_fixture(mapping, missing_door=None, legacy_guard=None):
    def sym(value):
        raw = value.encode("ascii")
        return b":" + integer(len(raw)) + raw

    def obj(name, attrs):
        return b"o" + sym(name) + integer(len(attrs)) + b"".join(
            sym(k) + v for k, v in attrs.items())

    def arr(values):
        return b"[" + integer(len(values)) + b"".join(values)

    events = {}
    for event_id, (source, xy, landing) in CERULEAN_DOORS.items():
        if event_id == missing_door:
            continue
        op = obj("RPG::EventCommand", {
            "@code": dump(201), "@parameters": dump([0, mapping[source], *landing, 2, 0])})
        page = obj("RPG::Event::Page", {"@trigger": dump(1), "@list": arr([op])})
        events[event_id] = obj("RPG::Event", {
            "@x": dump(xy[0]), "@y": dump(xy[1]), "@pages": arr([page])})
    for event_id, active_index in ((13, 0), (25, 1)):
        pages = []
        for index in (0, 1):
            active = index == active_index
            ops = []
            if active:
                legacy = legacy_guard == event_id
                ops.append(obj("RPG::EventCommand", {
                    "@code": dump(355 if legacy else 101),
                    "@parameters": dump([RubyString(b"BlueKantoPilot.cerulean_police" if legacy else b"Police dialogue")])}))
            ops.append(obj("RPG::EventCommand", {"@code": dump(0), "@parameters": dump([])}))
            pages.append(obj("RPG::Event::Page", {
                "@trigger": dump(0), "@through": dump(not active),
                "@graphic": obj("RPG::Event::Page::Graphic", {"@character_name": dump(RubyString(b"guard" if active else b""))}),
                "@condition": obj("RPG::Event::Page::Condition", {
                    "@self_switch_valid": dump(bool(index)), "@self_switch_ch": dump(RubyString(b"A"))}),
                "@list": arr(ops)}))
        events[event_id] = obj("RPG::Event", {"@pages": arr(pages)})
    table = b"{" + integer(len(events)) + b"".join(dump(k) + v for k, v in events.items())
    return b"\x04\x08" + obj("RPG::Map", {"@events": table})


ROOT = Path(__file__).resolve().parents[1]


class KantoDeliveryTests(unittest.TestCase):
    def fixture(self, channel, omit=None, short=None, omit_rival=False, omit_ticket=False, omit_bike=False, invalid_dig=False, atlas="authored", missing_door=None, legacy_guard=None, rock_fault=None):
        manifest = json.loads((ROOT / "data/regions/kanto-source.json").read_text("utf8"))
        mapping = {source: 700 + index for index, source in enumerate(manifest["maps"])}
        mapping.update(published_destinations())
        if rock_fault == "slots":
            mapping["90"], mapping["91"] = mapping["91"], mapping["90"]
        root, marker = (("Pokemon-Blue-Kanto-Android/", "Kanto pilot.json")
                        if channel == "kanto" else
                        ("Pokemon-Blue-Android/", "Data/blue-kanto-install.json"))
        source = (ROOT / "scripts/battle_polish/Journey.rb").read_bytes()
        travel = (ROOT / "scripts/battle_polish/RegionTravel.rb").read_bytes()
        rival = (ROOT / "scripts/regions/KantoPilot.rb").read_bytes()
        if rock_fault != "flash":
            field = (ROOT / "scripts/regions/KantoK04Field.rb").read_bytes()
            rival += b"\n" + field.strip() + b"\n"
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
                                     b"map" if original == short else (city_fixture(mapping, missing_door, legacy_guard) if original == "39" else b"m" * 128))
            edges = (*EDGES, ("64", "79"), ("39","86"))
            if rock_fault != "seam":
                edges += (("86","87"),)
            archive.writestr(root + "PBS/map_metadata_kanto.txt", "\n".join(
                f"[{mapping[i]}]\nName = Fixture" +
                ("\nDarkMap = true" if i in ("90","91") and not (i == "91" and rock_fault == "dark") else "")
                for i in published_destinations()))
            archive.writestr(root + "PBS/map_connections_kanto.txt", "\n".join(
                f"{mapping[a]},North,0,{mapping[b]},South,0" for a, b in edges))
            archive.writestr(root + "PBS/trainers_kanto.txt",
                             "[BLUE_KANTO_SWIMMER,Luis,0]\n[BLUE_KANTO_PICNICKER,Diana,0]\n[BLUE_KANTO_ROCKET,Grunt,6]\n" +
                             "\n".join(f"[BLUE_KANTO_RIVAL,Blue,{v}]" for v in (31, 32, 33)) + "\n" +
                             "\n".join(f"[BLUE_KANTO_{kind},{name},0]" for kind, name in TRAINERS.values()))
            if not omit_rival:
                archive.writestr(root + KANTO_RUNTIME, rival)
            if atlas is not None:
                archive.writestr(root + KANTO_ATLAS, render_wall_atlas() if atlas == "authored" else b"donor-or-invalid")
            archive.writestr(root + JOURNEY, source)
            archive.writestr(root + "Plugins/ZZZZ Blue Story and Presentation/RegionTravel.rb", travel)
            archive.writestr(root + "Data/PluginScripts.rxdata", cache)
            archive.writestr(root + "Data/items.dat", b"\x04\x08{\x00" if omit_ticket else ticket_catalog(omit_bike, invalid_dig))
            audio_paths = k03e_audio_paths()
            for path in set(audio_paths.values()):
                archive.writestr(root + path, b"synthetic audio fixture")
            by_name = {name: str(source) for source, name in MAPS.items()}
            selected = ["MAP\t{}\t{}\t100\t100".format(
                mapping[by_name[row["map"]]], audio_paths[row["track"]].removeprefix("Audio/BGM/"))
                for row in MUSIC]
            archive.writestr(root + "Data/blue-kanto-music.txt",
                             "MAP\tfixture\n" * 84 + "\n".join(selected))
        return target

    def test_all_maps_and_compiled_luis_guard_pass_in_both_channels(self):
        for channel in ("kanto", "multiregion"):
            with self.subTest(channel=channel):
                proof = assert_delivery(self.fixture(channel), channel)
                self.assertEqual(proof["kanto_maps"], 165)
                self.assertEqual(proof["cerulean_police_native_pages"], 2)

    def test_k04_zip_refuses_wrong_ids_missing_seam_darkness_or_flash(self):
        for fault, message in (("slots","stable K04 append"),("seam","connection absent"),
                              ("dark","darkness metadata"),("flash","Flash acquisition runtime")):
            with self.subTest(fault=fault):
                with self.assertRaisesRegex(ValueError,message):
                    assert_delivery(self.fixture("multiregion", rock_fault=fault),"multiregion")

    def test_promoted_k03e_requires_all_trainers_seam_and_music(self):
        mapping = {str(key): 600 + index for index, key in enumerate(MAPS)}
        mapping["64"] = 580
        pbs = "\n".join(f"[BLUE_KANTO_{kind},{name},0]" for kind, name in TRAINERS.values())
        edges = {frozenset((mapping["64"], mapping["79"]))}
        by_name = {name: source for source, name in MAPS.items()}
        audio_paths = k03e_audio_paths()
        track_names = {number: path.removeprefix("Audio/BGM/") for number, path in audio_paths.items()}
        music = [f"MAP\t{mapping[str(by_name[row['map']])]}\t{track_names[row['track']]}\t100\t100"
                 for row in MUSIC]
        files = set(audio_paths.values())
        verify_k03e(mapping, edges, pbs, music, files)
        with self.assertRaisesRegex(ValueError, "soundtrack missing"):
            verify_k03e(mapping, edges, pbs, music, set())
        for connection, trainers, tracks, error in (
            (set(), pbs, music, "connection absent"),
            (edges, pbs.replace("Dave", "Davi"), music, "trainer missing: Dave"),
            (edges, pbs, music[1:], "soundtrack missing"),
            (edges, pbs, music + [music[0]], "soundtrack missing"),
        ):
            with self.subTest(error=error), self.assertRaisesRegex(ValueError, error):
                verify_k03e(mapping, connection, trainers, tracks, files)

    def test_legacy_police_script_rejected_in_both_channels(self):
        for channel in ("kanto", "multiregion"):
            for guard in (13, 25):
                with self.subTest(channel=channel, guard=guard):
                    with self.assertRaisesRegex(ValueError, f"Cerulean police {guard}"):
                        assert_delivery(self.fixture(channel, legacy_guard=guard), channel)

    def test_missing_cerulean_door_is_rejected_even_with_all_maps_present(self):
        with self.assertRaisesRegex(ValueError, "Cerulean door 7 missing"):
            assert_delivery(self.fixture("multiregion", missing_door=7), "multiregion")

    def test_authored_atlas_required_in_both_channels(self):
        for channel in ("kanto", "multiregion"):
            for atlas in (None, "foreign"):
                with self.subTest(channel=channel, atlas=atlas):
                    with self.assertRaisesRegex(ValueError, "authored atlas"):
                        assert_delivery(self.fixture(channel, atlas=atlas), channel)

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
