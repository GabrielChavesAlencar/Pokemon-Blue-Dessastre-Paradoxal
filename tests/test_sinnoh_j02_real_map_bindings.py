"""Tests J02: real-source binder validation, fail-closed negative cases, no native claims."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import bind_sinnoh_playable_j02 as j02

A = "a" * 64
B = "b" * 64
C = "c" * 64

class J02BindingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = j02.source_catalog()

    def setUp(self):
        self.plan = {
            "schema": 1, "region": "SINNOH",
            "mode": "J02_LOCAL_BINDING_CANDIDATE",
            "baseline_mapinfos_sha256": A,
            "source_mapinfos_sha256": B,
            "source_archive_sha256": C,
            "bindings": [],
        }
        self.map_data = {}
        self.metadata = {"source_mapinfos_sha256": B,
                         "source_archive_sha256": C,
                         "source_tilesets_sha256": A}
        chosen_missing = iter(range(901, 906))  # TEST FIXTURE ONLY. Never real MapIDs.
        for i, row in enumerate(self.catalog["maps"]):
            sid = row["source_id"] if row["source_id"] is not None else next(chosen_missing)
            digest = row["source_sha256"] if row["source_sha256"] else hashlib.sha256(str(sid).encode()).hexdigest()
            width, height = row["source_dimensions"] if row["source_dimensions"] else [20, 15]
            self.plan["bindings"].append({
                "symbol": row["symbol"], "source_id": sid, "destination_id": 442 + i,
                "source_sha256": digest, "width": width, "height": height,
            })
            self.map_data[sid] = {
                "sha256": digest, "width": width, "height": height,
                "tileset_id": 31, "nonempty_terrain": True,
            }
        self.reservations = {
            "schema": 1, "region": "SINNOH", "mode": "LOCAL_RESERVATIONS_CANDIDATE",
            "baseline_mapinfos_sha256": A, "protected_ids": [1, 600, 700],
        }

    def run_validation(self, plan=None, reservation=True):
        return j02.validate_candidate(plan or self.plan, self.catalog, A,
                                      {1, 22, 600, 700}, self.metadata, self.map_data,
                                      self.reservations if reservation else None)

    def assert_blocked(self, plan=None, reservation=True):
        with self.assertRaises(ValueError):
            self.run_validation(plan, reservation=reservation)

    def test_catalog_has_four_specific_nonempty_references(self):
        c = self.catalog
        self.assertEqual(c["source_terrain_candidates"], 4)
        self.assertEqual(c["source_maps_missing"], 5)
        present = {r["symbol"]: r["source_id"] for r in c["maps"] if r["source_id"] is not None}
        self.assertEqual(present, {
            "SINNOH_TWINLEAF_TOWN": 209,
            "SINNOH_SANDGEM_TOWN": 210,
            "SINNOH_ROUTE_201": 227,
            "SINNOH_ROUTE_202": 228
        })

    def test_missing_lake_and_interiors_never_fill_with_placeholders(self):
        missing = j02.original_metadata_view()["missing_symbols"]
        self.assertIn("SINNOH_LAKE_VERITY", missing)
        self.assertIn("SINNOH_PLAYER_BEDROOM", missing)
        self.assertIn("SINNOH_PLAYER_HOUSE_1F", missing)
        self.assertIn("SINNOH_BARRY_HOUSE", missing)
        self.assertIn("SINNOH_PROFESSOR_ROWAN_LABORATORY", missing)
        self.assertEqual(len(missing),5)

    def test_no_source_does_not_install(self):
        state = j02.original_metadata_view()
        self.assertEqual(state["status"], "SOURCE_REFS_4_OF_9_MISSING_LOCAL_INPUTS")
        self.assertEqual(state["candidate_destination_ids_verified"], 0)
        self.assertEqual(state["native_maps_installed"], 0)
        self.assertFalse(state["r07_complete"])
        self.assertFalse(state["can_install"])

    def test_synthetic_nine_bindings_are_candidates_only(self):
        out = self.run_validation()
        self.assertEqual(out["candidate_map_count"],9)
        self.assertFalse(out["can_install"])
        self.assertFalse(out["native_playable"])
        self.assertFalse(out["rights_verified"])
        self.assertFalse(out["r07_complete"])
        self.assertEqual(out["new_source_maps_required_and_checked"],5)
        self.assertTrue(out["future_reservations_supplied_as_local_claim"])
        self.assertFalse(out["future_reservations_complete_verified"])

    def test_no_future_reservations_claim_still_rejected_for_global_approval(self):
        out = self.run_validation(reservation=False)
        self.assertFalse(out["future_reservations_supplied_as_local_claim"])
        self.assertFalse(out["r07_complete"])

    def test_output_does_not_include_private_paths_or_user_saves(self):
        out = json.dumps(self.run_validation())
        self.assertNotIn("C:\\",out)
        self.assertNotIn("/Users/",out)
        self.assertNotIn("Save01.rxdata",out)
        self.assertNotIn("Game.exe",out)

    def test_wrong_header_denied(self):
        for key, value in (("schema",2),("region","KANTO"),
                           ("mode","NATIVE_APPROVED")):
            with self.subTest(key=key):
                obj=copy.deepcopy(self.plan);obj[key]=value
                self.assert_blocked(obj)

    def test_unknown_or_extra_schema_field_denied(self):
        obj=copy.deepcopy(self.plan);obj["approval"]=True;self.assert_blocked(obj)
        obj=copy.deepcopy(self.plan);del obj["bindings"];self.assert_blocked(obj)

    def test_baseline_sha_tampering_denied(self):
        obj=copy.deepcopy(self.plan);obj["baseline_mapinfos_sha256"]=C
        self.assert_blocked(obj)

    def test_source_mapinfos_sha_tampering_denied(self):
        obj=copy.deepcopy(self.plan);obj["source_mapinfos_sha256"]=A
        self.assert_blocked(obj)

    def test_source_archive_sha_tampering_denied(self):
        obj=copy.deepcopy(self.plan);obj["source_archive_sha256"]=B
        self.assert_blocked(obj)

    def test_nine_bindings_required(self):
        obj=copy.deepcopy(self.plan);obj["bindings"].pop()
        self.assert_blocked(obj)

    def test_duplicate_symbol_denied(self):
        obj=copy.deepcopy(self.plan)
        obj["bindings"][1]["symbol"]=obj["bindings"][0]["symbol"]
        self.assert_blocked(obj)

    def test_swapped_symbol_order_denied(self):
        obj=copy.deepcopy(self.plan);obj["bindings"][0],obj["bindings"][1]=obj["bindings"][1],obj["bindings"][0]
        self.assert_blocked(obj)

    def test_invalid_non_dict_entry_denied(self):
        obj=copy.deepcopy(self.plan);obj["bindings"][0]="fake"
        self.assert_blocked(obj)

    def test_forged_row_approval_denied(self):
        obj=copy.deepcopy(self.plan);obj["bindings"][0]["approved"]=True
        self.assert_blocked(obj)

    def test_duplicate_source_id_denied(self):
        obj=copy.deepcopy(self.plan);obj["bindings"][1]["source_id"]=obj["bindings"][0]["source_id"]
        self.assert_blocked(obj)

    def test_duplicate_destination_id_denied(self):
        obj=copy.deepcopy(self.plan);obj["bindings"][1]["destination_id"]=obj["bindings"][0]["destination_id"]
        self.assert_blocked(obj)

    def test_outside_sinnoh_range_denied(self):
        for dest in (0,441,518,800,805,1000,True,"445",-5):
            with self.subTest(dest=dest):
                obj=copy.deepcopy(self.plan);obj["bindings"][0]["destination_id"]=dest
                self.assert_blocked(obj)

    def test_native_id_collision_denied(self):
        obj=copy.deepcopy(self.plan);obj["bindings"][0]["destination_id"]=600
        self.assert_blocked(obj)

    def test_collision_inside_sinnoh_candidate_range_denied(self):
        obj=copy.deepcopy(self.plan)
        with self.assertRaises(ValueError):
            j02.validate_candidate(obj,self.catalog,A,{442},self.metadata,self.map_data,self.reservations)

    def test_future_reservation_collision_denied(self):
        obj=copy.deepcopy(self.reservations);obj["protected_ids"].append(442)
        with self.assertRaises(ValueError):
            j02.validate_candidate(self.plan,self.catalog,A,set(),self.metadata,self.map_data,obj)

    def test_future_reservation_baseline_mismatch_denied(self):
        obj=copy.deepcopy(self.reservations);obj["baseline_mapinfos_sha256"]=B
        with self.assertRaises(ValueError):
            j02.validate_candidate(self.plan,self.catalog,A,set(),self.metadata,self.map_data,obj)

    def test_future_reservation_duplicates_denied(self):
        obj=copy.deepcopy(self.reservations);obj["protected_ids"]=[600,600]
        with self.assertRaises(ValueError):
            j02.validate_candidate(self.plan,self.catalog,A,set(),self.metadata,self.map_data,obj)

    def test_future_reservation_bad_schema_denied(self):
        obj=copy.deepcopy(self.reservations);obj["reviewer"]="unknown"
        with self.assertRaises(ValueError):
            j02.validate_candidate(self.plan,self.catalog,A,set(),self.metadata,self.map_data,obj)

    def test_missing_source_map_denied(self):
        key=self.plan["bindings"][0]["source_id"]
        original=self.map_data.pop(key)
        try:self.assert_blocked()
        finally:self.map_data[key]=original

    def test_source_hash_mismatch_denied(self):
        obj=copy.deepcopy(self.plan);obj["bindings"][0]["source_sha256"]=A
        self.assert_blocked(obj)

    def test_historical_hash_changed_even_if_manifest_matches_denied(self):
        obj=copy.deepcopy(self.plan)
        index=next(i for i,r in enumerate(obj["bindings"]) if r["symbol"]=="SINNOH_TWINLEAF_TOWN")
        sid=obj["bindings"][index]["source_id"]
        obj["bindings"][index]["source_sha256"]=A
        original=copy.deepcopy(self.map_data[sid])
        self.map_data[sid]["sha256"]=A
        try:self.assert_blocked(obj)
        finally:self.map_data[sid]=original

    def test_historical_source_reassigned_denied(self):
        obj=copy.deepcopy(self.plan)
        index=next(i for i,r in enumerate(obj["bindings"]) if r["symbol"]=="SINNOH_ROUTE_201")
        obj["bindings"][index]["source_id"]=800
        self.map_data[800]=copy.deepcopy(self.map_data[227])
        try:self.assert_blocked(obj)
        finally:del self.map_data[800]

    def test_missing_source_terrain_denied(self):
        sid=self.plan["bindings"][0]["source_id"]
        original=self.map_data[sid]["nonempty_terrain"]
        self.map_data[sid]["nonempty_terrain"]=False
        try:self.assert_blocked()
        finally:self.map_data[sid]["nonempty_terrain"]=original

    def test_mismatched_source_dimensions_denied(self):
        obj=copy.deepcopy(self.plan);obj["bindings"][0]["height"]+=1
        self.assert_blocked(obj)

    def test_bad_source_id_types_denied(self):
        for sid in (None,False,0,-1,"209",10000):
            with self.subTest(sid=sid):
                obj=copy.deepcopy(self.plan);obj["bindings"][0]["source_id"]=sid
                self.assert_blocked(obj)

    def test_invalid_map_sha_denied(self):
        obj=copy.deepcopy(self.plan);obj["bindings"][0]["source_sha256"]="ab"
        self.assert_blocked(obj)

    def test_output_opt_in_exclusive_mode(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p)
            j02.local_report(root,self.run_validation())
            out=root/".blue-work"/"sinnoh-jogavel"/"j02-map-bindings.json"
            self.assertTrue(out.is_file())
            with self.assertRaises(FileExistsError):j02.local_report(root,self.run_validation())

    def test_input_file_outside_workspace_denied(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p);source=root/"bindings.json";source.write_text("{}")
            with self.assertRaises(ValueError):j02.local_input(root,source)

    def test_input_file_symlink_denied(self):
        with tempfile.TemporaryDirectory() as p:
            root=Path(p);w=root/".blue-work";w.mkdir()
            real=w/"real.json";real.write_text("{}")
            link=w/"alias.json"
            try:link.symlink_to(real)
            except (OSError,NotImplementedError):self.skipTest("Symlink unavailable")
            with self.assertRaises(ValueError):j02.local_input(root,link)

    def test_audit_does_not_upgrade_documentary_catalog(self):
        c=copy.deepcopy(self.catalog);c["source_rights_verified"]=True
        with patch.object(j02,"object_json",side_effect=[c, j02.object_json(ROOT/"data/regions/sinnoh-b00-actual-source.json")]):
            with self.assertRaises(ValueError):j02.source_catalog()

    def test_cli_no_args_blocked_but_sanitized(self):
        self.assertEqual(j02.main(["--project",str(ROOT)]),2)

    def test_cli_cannot_inject_execute_game(self):
        with self.assertRaises(SystemExit):j02.main(["--execute-game"])

    def test_catalog_mapping_remains_uninstalled(self):
        self.assertTrue(all(r["destination_map_id"] is None and not r["installed"]
                            for r in self.catalog["maps"]))

if __name__=="__main__":
    unittest.main()
