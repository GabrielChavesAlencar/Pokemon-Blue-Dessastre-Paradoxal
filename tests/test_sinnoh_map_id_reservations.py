"""CH05: documented reservations, unknown occupancy and negative tamper tests."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.regions.audit_region_map_id_reservations import (
    EVIDENCE, LEGACY_EVIDENCE, MANIFEST, ROOT, inspect_id, native_report,
    report, validate,
)


def original():
    return json.loads((ROOT / MANIFEST).read_text(encoding="utf-8"))


class SinnohMapIdReservationsTests(unittest.TestCase):
    def test_main_manifest_is_checked_against_actual_source_lines(self):
        data = original()
        validate(data, ROOT)
        self.assertEqual(set(data["regions"]), set(EVIDENCE))
        self.assertIsNone(data["native_snapshot"]["occupied_ids"])
        self.assertIsNone(data["allocation"]["confirmed_free_ids"])
        self.assertFalse(data["allocation"]["can_allocate"])
        self.assertFalse(data["allocation"]["can_install"])

    def test_reserved_not_physically_occupied_is_distinguished(self):
        data = original()
        rows = {r["map_id"]: r for r in report(data)["classified"]}
        for i, owner in ((600, "JOHTO"), (699, "JOHTO"),
                         (700, "HOENN"), (800, "HOENN"),
                         (805, "HOENN"), (999, "HOENN")):
            with self.subTest(i=i):
                self.assertEqual(rows[i]["documented_reservation_owners"], [owner])
                self.assertEqual(rows[i]["physical_observation"], "NO_LOCAL_REPORT")
                self.assertIsNone(rows[i]["physical_owner"])
                self.assertFalse(rows[i]["free_to_allocate"])
        self.assertTrue(rows[800]["legacy_sinnoh_standalone_candidate"])
        self.assertTrue(rows[805]["legacy_sinnoh_standalone_candidate"])
        self.assertFalse(rows[700]["legacy_sinnoh_standalone_candidate"])

    def test_unknown_destinations_are_never_assumed_available(self):
        data = original()
        for i in (1, 500, 599, 1000, 5000):
            with self.subTest(i=i):
                row = inspect_id(i, data)
                self.assertFalse(row["reserved_by_code"])
                self.assertEqual(row["documented_reservation_owners"], [])
                self.assertFalse(row["free_to_allocate"])
                self.assertIsNone(row["physical_owner"])
                self.assertEqual(row["physical_observation"], "NO_LOCAL_REPORT")

    def test_even_absent_from_real_report_does_not_become_free(self):
        data = original()
        snapshot = {"schema": 1, "region": "SINNOH",
                    "mode": "READ_ONLY_INERT_RMXP", "import_allowed": False,
                    "native": {"status": "LOCAL_READ_ONLY",
                               "occupied_ids": [1, 800]}}
        observed = native_report(snapshot)
        row = inspect_id(800, data, observed=observed)
        self.assertEqual(row["physical_observation"], "REPORTED_OCCUPIED_UNATTRIBUTED")
        self.assertEqual(row["documented_reservation_owners"], ["HOENN"])
        self.assertIsNone(row["physical_owner"])
        missing = inspect_id(2, data, observed=observed)
        self.assertEqual(missing["physical_observation"],
                         "NOT_REPORTED_OCCUPIED_NOT_PROOF_FREE")
        self.assertFalse(missing["free_to_allocate"])
        self.assertFalse(report(data, observed=observed)["can_install"])

    def test_rejects_spoofed_native_reports(self):
        valid = {"schema": 1, "region": "SINNOH",
                 "mode": "READ_ONLY_INERT_RMXP", "import_allowed": False,
                 "native": {"status": "LOCAL_READ_ONLY", "occupied_ids": [1, 2]}}
        for change in (
            {"mode": "CAPACITY_ONLY_NO_ALLOCATION"},
            {"import_allowed": True},
            {"native": {"status": "NOT_CHECKED", "occupied_ids": [1, 2]}},
            {"native": {"status": "LOCAL_READ_ONLY", "occupied_ids": [1, 1]}},
            {"native": {"status": "LOCAL_READ_ONLY", "occupied_ids": [True]}},
            {"native": {"status": "LOCAL_READ_ONLY", "occupied_ids": ["800"]}},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                native_report({**valid, **change})

    def test_rejects_false_approval_and_mislabelled_occupation(self):
        for field, value in (
            ("can_allocate", True), ("can_install", True),
            ("safe_to_merge", True), ("confirmed_free_ids", [500]),
            ("confirmed_free_status", "VERIFIED"),
        ):
            with self.subTest(field=field):
                d = original()
                d["allocation"][field] = value
                with self.assertRaisesRegex(ValueError, "liberar"):
                    validate(d, ROOT)
        d = original()
        d["regions"]["KANTO"]["physical_occupied_ids"] = [500]
        with self.assertRaisesRegex(ValueError, "ocupação"):
            validate(d, ROOT)
        d = original()
        d["native_snapshot"]["status"] = "LOCAL_READ_ONLY"
        with self.assertRaisesRegex(ValueError, "ocupação"):
            validate(d, ROOT)

    def test_rejects_conflicting_or_fabricated_claims(self):
        for owner, bad_start, err in (
            ("JOHTO", 599, "faixa"),
            ("JOHTO", 700, "faixa"),
            ("HOENN", 600, "faixa"),
        ):
            with self.subTest(owner=owner, start=bad_start):
                d = original()
                row = next(x for x in d["documented_shared_reservations"]
                           if x["owner"] == owner)
                row["start"] = bad_start
                with self.assertRaisesRegex(ValueError, err):
                    validate(d, ROOT)
        d = original()
        d["documented_shared_reservations"][1]["owner"] = "JOHTO"
        with self.assertRaisesRegex(ValueError, "repetido"):
            validate(d, ROOT)
        d = original()
        d["legacy_standalone"]["mode"] = "SHARED_INSTALL"
        with self.assertRaisesRegex(ValueError, "piloto"):
            validate(d, ROOT)

    def test_rejects_unknown_region_and_unverified_sinnoh_range(self):
        d = original()
        d["regions"]["PALDEA"] = {"physical_occupied_ids": None}
        with self.assertRaisesRegex(ValueError, "regiões"):
            validate(d, ROOT)
        d = original()
        d["sinnoh_shared_exclusion"]["start"] = 700
        with self.assertRaisesRegex(ValueError, "faixa proibida"):
            validate(d, ROOT)
        d = original()
        d["regions"]["SINNOH"]["known_shared_destinations"] = [501]
        with self.assertRaisesRegex(ValueError, "destinos"):
            validate(d, ROOT)

    def test_rejects_removed_evidence_or_source_drift(self):
        d = original()
        d["regions"]["HOENN"]["evidence"][0]["contains"] = "unverified marker"
        with self.assertRaisesRegex(ValueError, "fonte"):
            validate(d, ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for path, _ in (*EVIDENCE.values(), LEGACY_EVIDENCE):
                dest = root / path
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text("altered contract", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "contrato alterado"):
                validate(original(), root)

    def test_rejects_invalid_queries(self):
        data = original()
        for value in (True, 0, -1, "600", 2.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                inspect_id(value, data)
        with self.assertRaisesRegex(ValueError, "duplicados"):
            report(data, query_ids=[600, 600])

    def test_cli_read_only(self):
        command = [sys.executable,
                   str(ROOT / "scripts/regions/audit_region_map_id_reservations.py"),
                   "--id", "599", "--id", "800", "--id", "1000"]
        response = subprocess.run(command, text=True, capture_output=True, check=False)
        self.assertEqual(response.returncode, 0, response.stderr)
        output = json.loads(response.stdout)
        self.assertFalse(output["can_allocate"])
        self.assertEqual([x["map_id"] for x in output["classified"]],
                         [599, 800, 1000])
        self.assertFalse(output["shared_installation_verified"])


if __name__ == "__main__":
    unittest.main()
