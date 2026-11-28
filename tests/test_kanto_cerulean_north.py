"""Source-pinned Cerulean north contracts, without Game.exe or saves.

CI without the private FRLG source checks stable IDs and authored callbacks.
Kanto's source-present runner additionally checks real Map039/053/054/055
coordinates. Nothing is taken from guessed MapIDs or donor Ruby scripts.
"""
import json
import struct
import zlib
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit import stable_source_order, allocate_kanto_ids, load
from pilot import TRAINERS
from kanto_wall_atlas import render_wall_atlas, PLACES, PROVENANCE
from kanto_overworld import CERULEAN_FURNITURE, source_cerulean_furniture
from server.ruby_marshal import RubyObject

SOURCE = ROOT / ".blue-work/frlg-source/Essentials FRLG"
MANIFEST = ROOT / "data/regions/kanto-source.json"
RUNTIME = ROOT / "scripts/regions/KantoPilot.rb"
BUILDER = ROOT / "scripts/regions/pilot.py"
VERIFIER = ROOT / "scripts/regions/verify_pilot.py"


class CeruleanNorthContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text("utf-8"))
        from k05_contract import MAPS as lavender
        cls.ids = {int(i) for i in cls.manifest["maps"]} - lavender.keys()

    def test_01_legacy_map_ids_cannot_shift(self):
        corridor = {23,79,81,82}
        active = bool(self.ids & corridor)
        rock = {86,87,88,90,91} & self.ids
        prior = self.ids - corridor - rock - {43,44,45,46,47,48,53,54,55,58,68,69,70,71}
        self.assertEqual(len(prior), 142)
        self.assertEqual(len(self.ids), (160 if active else 156) + len(rock))
        old_order = stable_source_order(prior)
        upgraded = stable_source_order(self.ids)
        self.assertEqual(upgraded[:142], old_order)
        self.assertEqual(upgraded[142:145], [53, 54, 55])
        self.assertEqual(upgraded[145:151], [43,44,45,46,47,48])
        self.assertEqual(upgraded[151:152], [58])
        self.assertEqual(upgraded[152:156], [68,69,70,71])
        self.assertEqual(upgraded[156:160], sorted(corridor) if active else [])
        self.assertEqual(upgraded[160:], sorted(rock))
        self.assertIn(rock, (set(), {86,87,88,90,91}))
        self.assertEqual(self.manifest["maps"]["53"], "ROUTE_24")
        self.assertEqual(self.manifest["maps"]["54"], "ROUTE_25")
        self.assertEqual(self.manifest["maps"]["55"], "BILL_COTTAGE")

    def test_cerulean_interiors_append_without_shifting_145_existing_slots(self):
        extra = {43, 44, 45, 46, 47, 48}
        historical = self.ids - {23,58,68,69,70,71,79,81,82,86,87,88,90,91}
        before = stable_source_order(historical - extra)
        expanded = stable_source_order(historical)
        self.assertEqual(expanded[:145], before)
        self.assertEqual(expanded[145:], sorted(extra))
        existing = {sid: 300+i for i, sid in enumerate(before)}
        occupied = set(existing.values()) | {700, 800}
        upgraded = allocate_kanto_ids(historical, occupied, existing)
        self.assertEqual({sid: upgraded[sid] for sid in existing}, existing)
        self.assertEqual([upgraded[sid] for sid in sorted(extra)], list(range(801, 807)))

    def test_optional_cerulean_callbacks_are_local_and_source_anchored(self):
        runtime = RUNTIME.read_text("utf-8")
        builder = BUILDER.read_text("utf-8")
        for source in ('(44,1): "cerulean_badge_guide"', '(46,2): "cerulean_jynx_trade"',
                       '(46,5): "cerulean_wall_map"', '(47,4): "cerulean_wall_map"'):
            self.assertIn(source, builder)
        self.assertIn('!progress["pilot_cerulean_jynx_trade"]', runtime)
        self.assertIn('pbStartTrade(index, received, "Zynx", "Dontae", 0)', runtime)
        self.assertIn('KantoWallMap.png', runtime)
        self.assertNotIn('pbChoosePokemonForTrade(1, 2', runtime)

    def test_authored_wall_atlas_is_deterministic_valid_and_complete(self):
        image = render_wall_atlas()
        self.assertEqual(image, render_wall_atlas())
        self.assertEqual(image[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(struct.unpack(">II", image[16:24]), (480, 320))
        self.assertIn(PROVENANCE, image)
        self.assertEqual(len({name for name, *_ in PLACES}), 11)
        pos, data = 8, b""
        while pos < len(image):
            size = struct.unpack(">I", image[pos:pos+4])[0]
            kind = image[pos+4:pos+8]
            chunk = image[pos+8:pos+8+size]
            crc = struct.unpack(">I", image[pos+8+size:pos+12+size])[0]
            self.assertEqual(crc, zlib.crc32(kind+chunk) & 0xffffffff)
            if kind == b"IDAT":
                data += chunk
            pos += 12+size
        self.assertEqual(pos, len(image))
        raw = zlib.decompress(data)
        self.assertEqual(len(raw), 320*(1+480*3))
        self.assertGreater(len(set(raw)), 8)

    def test_native_message_fixture_restores_underlying_method_with_prepend(self):
        ruby = shutil.which("ruby")
        if not ruby:
            self.skipTest("Ruby runtime unavailable")
        native = ROOT / "scripts/regions/KantoNativeCheck.rb"
        code = """
module LocaleWrapper
  def pbMessage(message,*args,&block)
    super(message,*args,&block)
  end
end
Object.prepend(LocaleWrapper)
Object.send(:define_method,:pbMessage) { |*args| args[1].is_a?(Array) ? 0 : nil }
load ARGV.fetch(0)
module Probe
  def self.choose
    pbMessage("choose",["yes","no"])
  end
end
raise "initial fixture broken" unless Probe.choose == 0
KantoNativeCheck.with_native_message_fixture(proc { |*args| 1 }) do
  raise "scoped fixture broken" unless Probe.choose == 1
end
raise "restore broken" unless Probe.choose == 0
begin
  KantoNativeCheck.with_native_message_fixture(proc { |*args| 1 }) { raise "test exception" }
rescue RuntimeError => e
  raise unless e.message == "test exception"
end
raise "restore after exception broken" unless Probe.choose == 0
puts "KANTO_K02C_MESSAGE_PREPEND_RESTORE_OK"
"""
        run = subprocess.run([ruby, "-e", code, str(native)], capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertIn("KANTO_K02C_MESSAGE_PREPEND_RESTORE_OK", run.stdout)

    def test_furniture_allowlist_rejects_foreign_scripts_and_coordinates(self):
        def obj(**attrs):
            return RubyObject("fixture", {"@" + k: v for k, v in attrs.items()})
        for (source, eid), (name, x, y) in CERULEAN_FURNITURE.items():
            event = obj(name=name, x=x, y=y, pages=[obj(
                condition=obj(self_switch_valid=False), trigger=0,
                graphic=obj(character_name=b"", tile_id=0),
                list=[obj(code=101, indent=0, parameters=[b"Furniture"]),
                      obj(code=0, indent=0, parameters=[])])])
            self.assertIsNotNone(source_cerulean_furniture(event, source, eid))
            self.assertIsNone(source_cerulean_furniture(event, source, 999))
            event.attrs["@x"] += 1
            self.assertIsNone(source_cerulean_furniture(event, source, eid))
            event.attrs["@x"] -= 1
            event.attrs["@pages"][0].attrs["@list"][0].attrs["@code"] = 355
            self.assertIsNone(source_cerulean_furniture(event, source, eid))

    def test_cerulean_police_gate_rejects_legacy_script_on_either_page(self):
        from cerulean_doors import verify_cerulean_police
        def obj(**attrs):
            return RubyObject("fixture", {"@" + k: v for k, v in attrs.items()})
        events = {}
        for eid, active_index in ((13, 0), (25, 1)):
            pages = []
            for index in (0, 1):
                active = index == active_index
                pages.append(obj(trigger=0, through=not active,
                    graphic=obj(character_name=b"guard" if active else b""),
                    condition=obj(self_switch_valid=bool(index), self_switch_ch=b"A"),
                    list=([obj(code=101, parameters=[b"Police"])] if active else []) +
                         [obj(code=0, parameters=[])]))
            events[eid] = obj(pages=pages)
        verify_cerulean_police(events)
        for eid, index in ((13, 0), (25, 1)):
            command = events[eid].attrs["@pages"][index].attrs["@list"][0]
            command.attrs["@code"] = 355
            with self.assertRaisesRegex(ValueError, "police"):
                verify_cerulean_police(events)
            command.attrs["@code"] = 101
        verify_cerulean_police(events)

    def test_02_source_trainer_bindings_are_local_and_unique(self):
        self.assertEqual(len(TRAINERS[53]), 6)
        self.assertEqual(len(TRAINERS[54]), 9)
        self.assertEqual(TRAINERS[53][1][:2], ("CAMPER", "Ethan"))
        self.assertEqual(TRAINERS[53][5][:2], ("BUGCATCHER", "Cale"))
        self.assertEqual(TRAINERS[54][11][:2], ("PICNICKER", "Kelsey"))
        self.assertNotIn(6, TRAINERS[53])  # Rocket's prize/battle is atomic.
        keys = [f"KANTO_{mid:03d}_{eid:03d}"
                for mid in (53, 54) for eid in TRAINERS[mid]]
        self.assertEqual(len(keys), len(set(keys)))

    def test_03_native_story_replaces_foreign_switch_scripts(self):
        runtime = RUNTIME.read_text("utf-8")
        builder = BUILDER.read_text("utf-8")
        verifier = VERIFIER.read_text("utf-8")
        for callback in (
            "BlueKantoPilot.cerulean_rival",
            "BlueKantoPilot.nugget_bridge_rocket",
            "BlueKantoPilot.bill_request",
            "BlueKantoPilot.bill_computer",
            "BlueKantoPilot.bill_reward",
        ):
            self.assertIn(callback, builder)
            self.assertIn(callback, verifier)
        self.assertIn("pilot_cerulean_rival", runtime)
        self.assertIn("pilot_nugget_bridge_awarded", runtime)
        self.assertIn("pilot_bill_helped", runtime)
        self.assertIn("pilot_bill_ticket", runtime)
        self.assertNotIn("pbSetSelfSwitch(31", builder)
        self.assertNotIn("TrainerBattle.start(:RIVAL1", builder)

    def test_04_android_ready_gate_accepts_only_verified_old_and_new_registry(self):
        source = (ROOT / "scripts/battle_polish/RegionStart.rb").read_text("utf-8")
        self.assertIn('["142", "145", "151", "152", "156", "160", "165", "178", "182"].include?(fields[1])', source)
        self.assertIn('[142, 145, 151, 152, 156, 160, 165, 178, 182].include?(expected_count)', source)
        self.assertIn('if expected_count >= 160', source)
        self.assertIn('if expected_count >= 178', source)
        self.assertIn('if expected_count == 182', source)
        self.assertIn('{"125"=>276, "126"=>277, "127"=>278, "128"=>279}', source)
        self.assertIn('K06_CELADON_SERVICES', source)
        self.assertIn('lavender.all? { |source,id| maps[source]==id }', source)
        self.assertIn('rock_slots.all? { |source, id| maps[source] == id }', source)
        self.assertIn('["23","79","81","82"].all?', source)
        self.assertIn('maps[source].is_a?(Integer) && !(452..595).include?(maps[source])', source)
        self.assertIn('pairs.length == expected_count', source)
        self.assertIn('maps.values.uniq.length == expected_count', source)
        self.assertIn('["53", "54", "55"].all?', source)
        self.assertIn('expected_count >= 152 && !maps["58"].is_a?(Integer)', source)
        self.assertIn('(68..71).all?', source)
        self.assertIn('(452..595).include?(maps[source.to_s])', source)
        self.assertIn('pbRgssExists?(sprintf("Data/Map%03d.rxdata", id))', source)

    @unittest.skipUnless((SOURCE / "Data/MapInfos.rxdata").is_file(),
                         "Original pinned FRLG source unavailable in fixture CI")
    def test_04_real_source_coordinates_and_event_id(self):
        expected = {39: (48, 40), 53: (36, 44), 54: (69, 44),
                    55: (20, 15)}
        for mid, dims in expected.items():
            item = load(SOURCE / f"Data/Map{mid:03d}.rxdata")
            attrs = item.attrs
            self.assertEqual((attrs["@width"], attrs["@height"]), dims)
        def event(mid, eid):
            return load(SOURCE / f"Data/Map{mid:03d}.rxdata").attrs["@events"][eid].attrs
        self.assertEqual([event(39, i)["@x"] for i in (15, 32, 34)],
                         [22, 23, 24])
        self.assertEqual([event(39, i)["@y"] for i in (15, 32, 34)],
                         [6, 6, 6])
        self.assertEqual((event(53, 6)["@x"], event(53, 6)["@y"]), (24, 19))
        self.assertEqual((event(54, 18)["@x"], event(54, 18)["@y"]), (51, 8))
        self.assertEqual((event(55, 8)["@x"], event(55, 8)["@y"]), (7, 6))

    @unittest.skipUnless((SOURCE / "PBS/map_connections.txt").is_file(),
                         "Source map connections unavailable in fixture CI")
    def test_05_real_source_connections(self):
        rows = {
            line.split("#", 1)[0].strip()
            for line in (SOURCE / "PBS/map_connections.txt").read_text(
                encoding="utf-8-sig").splitlines()
        }
        self.assertTrue({"53,South,0,39,North,0",
                         "54,South,0,39,North,36",
                         "54,West,0,53,East,0"} <= rows)


if __name__ == "__main__":
    unittest.main()
