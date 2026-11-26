"""Source-pinned Cerulean north contracts, without Game.exe or saves.

CI without the private FRLG source checks stable IDs and authored callbacks.
Kanto's source-present runner additionally checks real Map039/053/054/055
coordinates. Nothing is taken from guessed MapIDs or donor Ruby scripts.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit import stable_source_order, allocate_kanto_ids, load
from pilot import TRAINERS

SOURCE = ROOT / ".blue-work/frlg-source/Essentials FRLG"
MANIFEST = ROOT / "data/regions/kanto-source.json"
RUNTIME = ROOT / "scripts/regions/KantoPilot.rb"
BUILDER = ROOT / "scripts/regions/pilot.py"
VERIFIER = ROOT / "scripts/regions/verify_pilot.py"


class CeruleanNorthContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = json.loads(MANIFEST.read_text("utf-8"))
        cls.ids = {int(i) for i in cls.manifest["maps"]}

    def test_01_legacy_map_ids_cannot_shift(self):
        prior = self.ids - {53, 54, 55}
        self.assertEqual(len(prior), 142)
        self.assertEqual(len(self.ids), 145)
        old_order = stable_source_order(prior)
        upgraded = stable_source_order(self.ids)
        self.assertEqual(upgraded[:142], old_order)
        self.assertEqual(upgraded[-3:], [53, 54, 55])
        self.assertEqual(self.manifest["maps"]["53"], "ROUTE_24")
        self.assertEqual(self.manifest["maps"]["54"], "ROUTE_25")
        self.assertEqual(self.manifest["maps"]["55"], "BILL_COTTAGE")

    def test_cerulean_interiors_append_without_shifting_145_existing_slots(self):
        extra = {43, 44, 45, 46, 47, 48}
        before = stable_source_order(self.ids)
        expanded = stable_source_order(self.ids | extra)
        self.assertEqual(expanded[:145], before)
        self.assertEqual(expanded[145:], sorted(extra))
        existing = {sid: 300+i for i, sid in enumerate(before)}
        occupied = set(existing.values()) | {700, 800}
        upgraded = allocate_kanto_ids(self.ids | extra, occupied, existing)
        self.assertEqual({sid: upgraded[sid] for sid in existing}, existing)
        self.assertEqual([upgraded[sid] for sid in sorted(extra)], list(range(801, 807)))

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
        self.assertIn('["142", "145"].include?(fields[1])', source)
        self.assertIn('pairs.length == expected_count', source)
        self.assertIn('maps.values.uniq.length == expected_count', source)
        self.assertIn('["53", "54", "55"].all?', source)
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
