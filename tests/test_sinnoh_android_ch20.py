"""CH20: regressao negativa do pre-voo JoiPlay e checklist de 44 casos."""
from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import stat
import tempfile
import unittest
from zipfile import ZipFile, ZipInfo

from scripts.regions.audit_sinnoh_android_ch20 import (
    ROOT, LEDGER, TEMPLATE, EXPECTED_COUNTS,
    audit, checklist, inspect_package, safe_output, write_report,
)


class SinnohAndroidCH20Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sinnoh-ch20-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for relative in (TEMPLATE, LEDGER):
            destination = self.root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes((ROOT / relative).read_bytes())

    def modify(self, relative, change):
        file = self.root / relative
        data = json.loads(file.read_text("utf-8"))
        change(data)
        file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    def makezip(self, names=None):
        names = names or (
            "Data/MapInfos.rxdata", "Data/System.rxdata",
            "Data/Scripts.rxdata", "Game.ini",
        )
        path = self.root / "sinnoh-android.zip"
        with ZipFile(path, "w") as archive:
            for name in names:
                archive.writestr(name, b"synthetic fixture, not a game")
        return path

    def test_44_cases_derive_from_original_template_not_fake_map_ids(self):
        report = audit(root=self.root)
        self.assertEqual(report["checklist_total"], 44)
        self.assertEqual(report["by_kind"], EXPECTED_COUNTS)
        self.assertEqual(report["completed_native_cases"], 0)
        self.assertEqual(report["package"]["status"], "NOT_PROVIDED")
        self.assertTrue(all(c["native_status"] == "pending" and c["evidence"] is None
                            for c in report["cases"]))
        self.assertFalse(report["joiplay_tested"])
        self.assertFalse(report["native_gameplay_verified"])
        self.assertFalse(report["ready_marker_created"])

    def test_same_44_case_ids_as_native_auditor_without_installed_coordinates(self):
        from scripts.regions.audit_sinnoh_android_ch20 import STARTERS, REGIONS
        cases = checklist(self.root)
        self.assertEqual(len({x["id"] for x in cases}), 44)
        for starter in STARTERS:
            self.assertIn("ball-" + starter, [x["id"] for x in cases])
            self.assertIn("save-reload-" + starter, [x["id"] for x in cases])
        for region in REGIONS:
            self.assertIn("regression-" + region, [x["id"] for x in cases])
        self.assertEqual(sum(c["id"].startswith("warp-") for c in cases), 16)
        self.assertEqual(sum(c["id"].startswith("npc-") for c in cases), 5)
        self.assertIn("android-joi-play", [x["id"] for x in cases])

    def test_clean_zip_is_not_claimed_compatible_with_joiplay(self):
        report = audit(root=self.root, package=self.makezip())
        self.assertEqual(report["package"]["status"], "STRUCTURE_PRESENT_UNVERIFIED")
        self.assertEqual(report["package"]["structural_checks"], "METADATA_ONLY")
        self.assertEqual(len(report["package"]["sha256"]), 64)
        self.assertFalse(report["joiplay_tested"])
        self.assertEqual(report["completed_native_cases"], 0)

    def test_wrapped_zip_is_detected_without_extraction(self):
        package = self.makezip([
            "wrapped/Data/MapInfos.rxdata",
            "wrapped/Data/System.rxdata",
            "wrapped/Data/Scripts.rxdata",
        ])
        result = inspect_package(package)
        self.assertEqual(result["source_root"], "wrapped")
        self.assertFalse((self.root / "wrapped").exists())

    def test_missing_structure_fails_closed_as_blocked(self):
        result = inspect_package(self.makezip(["Data/MapInfos.rxdata"]))
        self.assertEqual(result["status"], "BLOCKED")
        self.assertNotEqual(result["status"], "STRUCTURE_PRESENT_UNVERIFIED")

    def test_duplicate_entries_differing_only_by_case_rejected(self):
        package = self.makezip(["Data/System.rxdata", "data/system.rxdata"])
        with self.assertRaisesRegex(ValueError, "duplicadas"):
            inspect_package(package)

    def test_zip_slip_and_windows_style_paths_rejected(self):
        for name in ("../game/save.dat", "Data\\Scripts.rxdata", "/Data/file",
                     "C:/Data/Scripts.rxdata", "Data/../game/file"):
            package = self.makezip([name])
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "inseguro"):
                inspect_package(package)

    def test_archive_symlink_rejected(self):
        package = self.root / "symlink.zip"
        with ZipFile(package, "w") as archive:
            member = ZipInfo("Data/scripts.rb")
            member.create_system = 3
            member.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(member, "target.rb")
        with self.assertRaisesRegex(ValueError, "symlink"):
            inspect_package(package)

    def test_legacy_ids_are_warning_not_unverified_gameplay_proof(self):
        package = self.makezip([
            "Data/MapInfos.rxdata", "Data/System.rxdata", "Data/Scripts.rxdata",
            "Data/Map800.rxdata", "Data/Map805.rxdata",
        ])
        report = audit(root=self.root, package=package)
        self.assertEqual(report["package"]["legacy_map_id_800_805_files"], [800, 805])
        self.assertFalse(report["native_gameplay_verified"])

    def test_rejects_fake_map_id_and_coordinates_in_source_template(self):
        self.modify(TEMPLATE, lambda j: j["maps"][0].update(map_id=802))
        with self.assertRaisesRegex(ValueError, "MapID"):
            checklist(self.root)
        self.modify(TEMPLATE, lambda j: j["maps"][0].update(map_id=None))
        self.modify(TEMPLATE, lambda j: j["maps"][0]["events"][0].update(arrival_x=12))
        with self.assertRaisesRegex(ValueError, "coordenadas"):
            checklist(self.root)

    def test_rejects_fake_playable_status_and_native_evidence(self):
        self.modify(TEMPLATE, lambda j: j.update(approved_for_install=True))
        with self.assertRaisesRegex(ValueError, "jogavel"):
            checklist(self.root)
        self.modify(TEMPLATE, lambda j: j.update(approved_for_install=False))
        self.modify(LEDGER, lambda j: j["native_playtest_workstream"].update(android_joi_play_tested=True))
        with self.assertRaisesRegex(ValueError, "Ledger"):
            checklist(self.root)

    def test_rejects_unrecognized_handler_or_warp_and_duplicate_key(self):
        self.modify(TEMPLATE, lambda j: j["maps"][0]["events"][0].update(destination="UNKNOWN"))
        with self.assertRaisesRegex(ValueError, "destino"):
            checklist(self.root)
        self.modify(TEMPLATE, lambda j: j["maps"][0]["events"][0].update(destination="SINNOH_PLAYER_HOUSE_1F"))
        self.modify(TEMPLATE, lambda j: j["maps"][0]["events"].append(
            copy.deepcopy(j["maps"][0]["events"][0])))
        with self.assertRaisesRegex(ValueError, "44 casos"):
            checklist(self.root)

    def test_write_json_only_in_blue_work_and_never_overwrite(self):
        report = audit(root=self.root)
        target = self.root / ".blue-work/reports/ch20.json"
        write_report(self.root, report, target)
        loaded = json.loads(target.read_text("utf-8"))
        self.assertEqual(loaded["checklist_total"], 44)
        self.assertFalse(loaded["game_exe_tested"])
        with self.assertRaisesRegex(ValueError, "sobrescrever"):
            write_report(self.root, report, target)
        with self.assertRaisesRegex(ValueError, "somente dentro"):
            safe_output(self.root, self.root / "game/overwrite.json")

    def test_output_directory_symlink_rejected(self):
        outside = self.root / "outside"
        outside.mkdir()
        work = self.root / ".blue-work"
        work.mkdir()
        (work / "linked").symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlinks"):
            write_report(self.root, audit(root=self.root),
                         work / "linked/report.json")


if __name__ == "__main__":
    unittest.main()
