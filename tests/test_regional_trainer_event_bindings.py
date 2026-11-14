"""Read-only source and private file tests for region trainer event bindings."""
from __future__ import annotations

import copy
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from verify_trainer_event_bindings import (  # noqa: E402
    BINDINGS, audit_sources, extract_events, inspect_private_copy,
    native_map_id, read_json, trainer_headers,
)
from build_johto_events import EVENT_CLASSES, event_page, ruby  # noqa: E402
from stage import serialize  # noqa: E402


class RegionalTrainerBindingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = read_json(ROOT / BINDINGS)
        cls.report = audit_sources(ROOT)

    def test_early_source_contains_13_unique_trainer_events(self):
        records = self.registry["records"]
        self.assertEqual(len(records), 13)
        self.assertEqual(self.report["source_count"], {"HOENN": 4, "JOHTO": 9})
        self.assertEqual(len({x["id"] for x in records}), 13)
        self.assertTrue(all(x["gameplay_verified"] is False for x in records))
        self.assertFalse(self.report["native_copy_inspected"])

    def test_maps_are_only_donor_or_offline_stage_ids(self):
        hoenn = [x for x in self.registry["records"] if x["region"] == "HOENN"]
        self.assertEqual({x["map_source_id"] for x in hoenn}, {102})
        self.assertTrue(all(x["map_stage_id"] is None for x in hoenn))
        johto = [x for x in self.registry["records"] if x["region"] == "JOHTO"]
        self.assertEqual({x["map_stage_id"] for x in johto}, {625, 626, 627, 677, 678, 679, 680})
        self.assertTrue(all(x["status"] == "STAGED_OFFLINE_NOT_COMPILED" for x in johto))
        self.assertEqual(len(self.registry["missing_event_candidates"]), 1)
        self.assertEqual(self.registry["missing_event_candidates"][0]["id"], "HOENN_ROUTE103_RIVAL")

    def test_johto_versions_and_no_npc_overlap(self):
        johto = [x for x in self.registry["records"] if x["region"] == "JOHTO"]
        self.assertTrue(all(x["versions"] == [0, 1] for x in johto))
        self.assertEqual(len({(x["map_stage_id"], x["x"], x["y"]) for x in johto}), len(johto))

    def test_private_audit_checks_actual_map_event_and_pbs_headers_without_compiling(self):
        sample = next(x for x in self.registry["records"] if x["id"] == "JH_ROUTE29_MIKE")
        with tempfile.TemporaryDirectory() as folder:
            copy_dir = Path(folder)
            (copy_dir / "Data").mkdir()
            (copy_dir / "PBS").mkdir()
            event = ruby("RPG::Event",id=1,name=sample["event_key"].encode(),
                         x=sample["x"],y=sample["y"],pages=[event_page(script=sample["script_call"])])
            map_blob = serialize(ruby("RPG::Map", events={1: event}),EVENT_CLASSES)
            (copy_dir / "Data/Map625.rxdata").write_bytes(map_blob)
            (copy_dir / "PBS/trainers_johto_routes.txt").write_text(
                f"[{sample['trainer_type']},{sample['trainer_name']},0]\n"
                "Pokemon = RATTATA,5\n"
                f"[{sample['trainer_type']},{sample['trainer_name']},1]\n"
                "Pokemon = RATTATA,5\n",encoding="utf-8",
            )
            self.assertEqual(len(extract_events(copy_dir / "Data/Map625.rxdata")),1)
            self.assertEqual(len(trainer_headers(copy_dir)),2)
            result = inspect_private_copy(copy.deepcopy(self.report),self.registry,copy_dir)
            item = next(x for x in result["entries"] if x["id"] == sample["id"])
            self.assertTrue(item["event_verified_in_copy"])
            self.assertTrue(item["pbs_headers_verified_in_copy"])
            self.assertFalse(item["native_compilation_verified"])
            self.assertFalse(item["gameplay_verified"])
            self.assertEqual(result["byte_level_bindings_found"],1)
            # No misleading promotion even if all source tests pass.
            self.assertEqual(result["status"],"PRIVATE_MAP_AND_PBS_AUDIT_ONLY_NO_GAMEPLAY_PROOF")

    def test_hoenn_remap_requires_real_private_marker(self):
        hoenn = next(x for x in self.registry["records"] if x["id"]=="HOENN_ROUTE102_CALVIN")
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            self.assertIsNone(native_map_id(hoenn,directory))
            (directory/"Hoenn pilot.json").write_text(
                json.dumps({"region":"HOENN","kind":"ISOLATED_HOENN_TEST",
                            "maps":{"102":742}}),encoding="utf-8")
            self.assertEqual(native_map_id(hoenn,directory),742)
            (directory/"Hoenn pilot.json").write_text(
                json.dumps({"region":"HOENN","kind":"UNKNOWN",
                            "maps":{"102":742}}),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Invalid Hoenn pilot"):
                native_map_id(hoenn,directory)

    def test_modified_stage_manifest_fails_closed(self):
        files = [
            BINDINGS, "data/regions/johto-stage10-routes.json",
            "data/regions/johto-stage11-violet.json",
            "scripts/regions/pilot_hoenn.py",
            "scripts/regions/build_johto_routes_stage10.py",
            "scripts/regions/build_johto_violet_stage11.py",
            "scripts/regions/HoennPilot.rb",
            "scripts/regions/JohtoRouteTrainers.rb",
            "scripts/regions/JohtoViolet.rb",
        ]
        with tempfile.TemporaryDirectory() as folder:
            staging = Path(folder)
            for relative in files:
                dst = staging / relative
                dst.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(ROOT / relative,dst)
            original = audit_sources(staging)
            self.assertEqual(original["authored_npc_bindings"],13)
            location = staging/"data/regions/johto-stage10-routes.json"
            contract = json.loads(location.read_text(encoding="utf-8"))
            contract["trainers"][0]["x"] += 1
            location.write_text(json.dumps(contract),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"Johto Route trainer drift"):
                audit_sources(staging)


if __name__ == "__main__":
    unittest.main()
