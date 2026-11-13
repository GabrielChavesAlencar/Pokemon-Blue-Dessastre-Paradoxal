"""Sinnoh map remap plans use real audited IDs only and NEVER install assets."""
from __future__ import annotations

import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from plan_sinnoh_remap import make_plan


def audited():
    return {
        "schema": 1, "region": "SINNOH", "mode": "READ_ONLY_INERT_RMXP",
        "import_allowed": False, "source_map_ids": [7, 8],
        "source_zip_sha256": "f" * 64,
        "mapinfos_sha256": "c" * 64,
        "tilesets_sha256": "d" * 64,
        "native": {"status": "LOCAL_READ_ONLY",
                   "occupied_ids": [1, 2, 10, 600, 681, 999]},
        "maps": [
            {"source_id": 7, "name": "Sample start", "sha256": "a" * 64,
             "transfer_targets": [8]},
            {"source_id": 8, "name": "Sample interior", "sha256": "b" * 64,
             "transfer_targets": [7]},
        ],
        "missing_map_files": [], "orphan_map_files": [],
        "unresolved_static_transfer_ids": [], "missing_graphics": [],
        "invalid_graphic_names": [],
        "dynamic_transfer_commands": 1,
        "untrusted_script_commands_not_executed": 2,
    }


def request():
    return {
        "schema": 1, "region": "SINNOH",
        "source_zip_sha256": "f" * 64,
        "source_mapinfos_sha256": "c" * 64,
        "source_tilesets_sha256": "d" * 64,
        "source_map_hashes": {"7": "a" * 64, "8": "b" * 64},
        "mapping": {"7": 500, "8": 501},
        "symbols": {"7": "SINNOH_SAMPLE_START", "8": "SINNOH_SAMPLE_ROOM"},
    }


class SinnohRemapTests(unittest.TestCase):
    def test_plan_uses_explicit_ids_and_only_proposes_static_rewrites(self):
        plan = make_plan(audited(), request(),
                         reserved={"schema": 1, "region": "SINNOH",
                                   "protected_ids": [3, 4, 580]})
        self.assertEqual(plan["mode"], "REMAP_CANDIDATE_ONLY")
        self.assertEqual(plan["mapping"], {"7": 500, "8": 501})
        self.assertEqual(plan["source_map_hashes"]["7"], "a" * 64)
        self.assertEqual(plan["proposed_static_transfer_rewrites"], [
            {"from_source_id": 7, "to_source_id": 8, "from_candidate_id": 500,
             "to_candidate_id": 501, "mode": "STATIC_REFERENCE_PROPOSAL"},
            {"from_source_id": 8, "to_source_id": 7, "from_candidate_id": 501,
             "to_candidate_id": 500, "mode": "STATIC_REFERENCE_PROPOSAL"},
        ])
        self.assertEqual(plan["protected_johto_range"], [600, 999])
        self.assertFalse(plan["can_install"])
        self.assertFalse(plan["may_stage_real_map_data"])
        self.assertFalse(plan["game_or_saves_modified"])
        self.assertFalse(plan["other_region_reservations_fully_verified"])
        self.assertEqual(plan["dynamic_transfer_commands_for_manual_review"], 1)
        self.assertEqual(len(plan["plan_sha256"]), 64)
        self.assertEqual(plan, make_plan(audited(), request(),
                                       reserved={"schema": 1, "region": "SINNOH",
                                                 "protected_ids": [3, 4, 580]}))

    def test_no_native_snapshot_is_not_an_allocation(self):
        report = audited()
        report["native"]["status"] = "NOT_CHECKED"
        with self.assertRaisesRegex(ValueError, "game/Data"):
            make_plan(report, request())
        report = audited()
        report["native"]["occupied_ids"] = None
        with self.assertRaisesRegex(ValueError, "MapIDs ocupados"):
            make_plan(report, request())

    def test_rejects_occupied_johto_four_digit_and_duplicates(self):
        for target, expected in [(1, "ocupado"), (600, "limite conservador"),
                                 (999, "limite conservador"),
                                 (1000, "limite conservador"), (0, "limite conservador")]:
            with self.subTest(target=target):
                bad = request()
                bad["mapping"]["7"] = target
                with self.assertRaisesRegex(ValueError, expected):
                    make_plan(audited(), bad)
        duplicate = request()
        duplicate["mapping"]["8"] = 500
        with self.assertRaisesRegex(ValueError, "duplicado"):
            make_plan(audited(), duplicate)

    def test_declared_other_region_reservations_block_destinations(self):
        with self.assertRaisesRegex(ValueError, "reserva"):
            make_plan(audited(), request(),
                      reserved={"schema": 1, "region": "SINNOH",
                                "protected_ids": [501]})
        with self.assertRaisesRegex(ValueError, "outra região"):
            make_plan(audited(), request(),
                      reserved={"schema": 1, "region": "HOENN",
                                "protected_ids": []})

    def test_rejects_missing_map_and_dangling_warp(self):
        report = audited()
        report["unresolved_static_transfer_ids"] = [99]
        with self.assertRaisesRegex(ValueError, "unresolved_static_transfer_ids"):
            make_plan(report, request())
        report = audited()
        report["missing_map_files"] = [11]
        with self.assertRaisesRegex(ValueError, "missing_map_files"):
            make_plan(report, request())

    def test_rejects_hash_changes_and_partial_selection(self):
        bad = request()
        bad["source_zip_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "ZIP original"):
            make_plan(audited(), bad)
        bad = request()
        bad["source_map_hashes"]["7"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash diverge"):
            make_plan(audited(), bad)
        bad = request()
        del bad["mapping"]["8"]
        with self.assertRaisesRegex(ValueError, "Todos os mapas"):
            make_plan(audited(), bad)

    def test_old_destinations_symbols_hashes_cannot_be_reassigned(self):
        prior = make_plan(audited(), request())
        new = request()
        self.assertEqual(make_plan(audited(), new, prior=prior)["mapping"],
                         prior["mapping"])
        new["mapping"]["7"] = 505
        with self.assertRaisesRegex(ValueError, "preservado"):
            make_plan(audited(), new, prior=prior)
        new = request()
        new["symbols"]["7"] = "SINNOH_DIFFERENT"
        with self.assertRaisesRegex(ValueError, "migração"):
            make_plan(audited(), new, prior=prior)
        new = request()
        prior_bad = copy.deepcopy(prior)
        prior_bad["source_map_hashes"]["8"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "migração"):
            make_plan(audited(), new, prior=prior_bad)

    def test_must_not_mutate_the_input(self):
        original_report, original_request = audited(), request()
        old_report = copy.deepcopy(original_report)
        old_request = copy.deepcopy(original_request)
        result = make_plan(original_report, original_request)
        self.assertEqual(original_report, old_report)
        self.assertEqual(original_request, old_request)
        self.assertNotIn("Data/Map007.rxdata", json.dumps(result))
        self.assertFalse(result["can_install"])
        self.assertFalse(result["may_stage_real_map_data"])
        self.assertFalse(result["game_or_saves_modified"])

    def test_rejects_invalid_symbols_and_unverified_report(self):
        bad = request()
        bad["symbols"]["7"] = "JOHTO_FIRST"
        with self.assertRaisesRegex(ValueError, "Símbolo"):
            make_plan(audited(), bad)
        report = audited()
        report["mode"] = "LOCAL_STAGE_ONLY"
        with self.assertRaisesRegex(ValueError, "Auditoria RXDATA"):
            make_plan(report, request())


if __name__ == "__main__":
    unittest.main()
