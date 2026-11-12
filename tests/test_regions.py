import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGIONS = ROOT / "scripts/regions"
sys.path.insert(0, str(REGIONS))
try:
    import audit
    import stage
    from runtime import plan
finally:
    sys.path.remove(str(REGIONS))
from server.ruby_marshal import RubyData, RubyObject, loads


class RegionsTest(unittest.TestCase):
    def test_unique_milestones_and_all_field_badges_reference_a_real_slot(self):
        registry = audit.json_file(audit.REGISTRY)
        self.assertEqual(len(set(registry["circuit"])), 10)
        self.assertEqual(set(registry["regions"]) - set(registry["circuit"]), {"HISUI"})
        for key, region in registry["regions"].items():
            self.assertEqual(len(set(region["milestones"])), 0 if key in ("HISUI", "DECADES") else 8, key)
            for rule in region["field"].values():
                if "badge" in rule:
                    area, badge = rule["badge"].split(":")
                    self.assertIn(badge, registry["regions"][area]["milestones"])

    def test_preview_writer_round_trip_preserves_tiles_and_rejects_event_code(self):
        terrain = RubyObject("RPG::Map", {"@width": 2, "@height": 2, "@data": RubyData("Table", b"\0"*28),
                                        "@events": {}})
        self.assertEqual(loads(stage.serialize(terrain)), terrain)
        terrain.attrs["@events"][1] = RubyObject("RPG::EventCommand", {"@code": 355})
        with self.assertRaises(ValueError):
            stage.serialize(terrain)

    @unittest.skipUnless(shutil.which("ruby"), "Ruby command not available")
    def test_regional_transport_rollback_and_single_save(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            files = plan(ROOT, target, target)
            data, contents = next(iter(files.items()))
            data.write_bytes(contents.replace(b"DECADES_VERIFIED = false", b"DECADES_VERIFIED = true"))
            args = ["ruby", str(ROOT/"tests/region_travel_runtime.rb"), str(data),
                    str(ROOT/"scripts/battle_polish/Regions.rb"),
                    str(ROOT/"scripts/battle_polish/RegionTravel.rb")]
            proc = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", timeout=20)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

    @unittest.skipUnless(shutil.which("ruby"), "Ruby command not available")
    def test_new_game_region_selection_and_legacy_save_safety(self):
        result = subprocess.run(
            ["ruby", str(ROOT / "tests/region_start_runtime.rb"),
             str(ROOT / "scripts/battle_polish/RegionStart.rb")],
            capture_output=True, text=True, encoding="utf-8", timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(shutil.which("ruby"), "Ruby command not available")
    def test_runtime_ring_old_saves_and_travel_rules(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            files = plan(ROOT, target, target)
            data, contents = next(iter(files.items()))
            data.write_bytes(contents.replace(b"DECADES_VERIFIED = false", b"DECADES_VERIFIED = true"))
            proc = subprocess.run(["ruby", str(ROOT/"tests/regions_runtime.rb"),
                                   str(data), str(ROOT/"scripts/battle_polish/Regions.rb")],
                                  capture_output=True, text=True, encoding="utf-8", timeout=20)
            self.assertEqual(proc.returncode, 0, proc.stdout+proc.stderr)


if __name__ == "__main__":
    unittest.main()
