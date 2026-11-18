"""G07.2: fail-closed synthetic package, hashes, provenance, paths, rights.

No network, archives, native saves, Game.exe or installer execution.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_unova_g07_incremental_manifest as mod


class UnovaG072Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = mod.validate_catalog()
        cls.registry = mod.j(ROOT, mod.REGISTRY)
        cls.board = mod.j(ROOT, mod.TRACKER)
        cls.contract = mod.j(ROOT, mod.CONTRACT_PATH)
        cls.schema = mod.j(ROOT, mod.SCHEMA_PATH)

    def fixture(self):
        return mod.demo_package()

    def passes(self, change=None, origin_change=None, payload_change=None):
        p, origin, old, new = self.fixture()
        if change:
            change(p)
            p["package_sha256"] = mod.package_digest(p)
        if origin_change:
            d = json.loads(origin)
            origin_change(d)
            origin = mod.canonical(d)
            p["source"]["manifest_sha256"] = mod.digest(origin)
            p["source"]["manifest_size"] = len(origin)
            p["package_sha256"] = mod.package_digest(p)
        if payload_change:
            payload_change(old, new)
        return mod.validate_package(p, origin, old, new)

    def fails(self, change=None, origin_change=None, payload_change=None):
        with self.assertRaises(ValueError):
            self.passes(change, origin_change, payload_change)

    def test_001_valid_fixture_preview_only(self):
        self.assertEqual(self.passes()["status"], "SYNTHETIC_DOCS_UPDATE_VALIDATED_NOT_INSTALLABLE")

    def test_002_no_installed_game_files(self):
        self.assertEqual(self.passes()["native_files_written"], 0)

    def test_003_no_bytes_written(self):
        self.assertEqual(self.passes()["bytes_written"], 0)

    def test_004_one_hash_approved_fixture(self):
        self.assertTrue(self.passes()["sha256_verified"])

    def test_005_not_license_verification(self):
        self.assertFalse(self.passes()["license_verified"])

    def test_006_not_provenance_signature(self):
        self.assertFalse(self.passes()["provenance_authenticated"])

    def test_007_no_release_status(self):
        self.assertFalse(self.passes()["release_allowed"])

    def test_008_no_native_payload(self):
        self.assertFalse(self.passes()["native_payload_approved"])

    def test_009_dry_run_check_catalog(self):
        self.assertEqual(self.report["phase"], "G07.2")

    def test_010_technical_bar_zero(self):
        self.assertEqual(self.board["native_technical_bar"]["completed"], 0)

    def test_011_playable_bar_zero(self):
        self.assertEqual(self.board["native_playable_bar"]["completed"], 0)

    def test_012_unova_planned(self):
        self.assertEqual(self.registry["regions"]["UNOVA"]["status"], "planned")

    def test_013_no_blue_story_installer(self):
        self.assertFalse(self.contract["installer_implemented"])

    def test_014_no_android_compatibility(self):
        self.assertFalse(self.contract["android_supported"])

    def test_015_no_game_exe_QA(self):
        self.assertFalse(self.contract["game_exe_tested"])

    def test_016_no_saves_modified(self):
        self.assertFalse(self.contract["saves_modified"])

    def test_017_schema_draft_2020_12(self):
        self.assertEqual(self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema")

    def test_018_schema_disallows_extra_fields(self):
        self.assertIs(self.schema["additionalProperties"], False)

    def test_019_source_identity_is_sha40(self):
        p, *_ = self.fixture()
        self.assertEqual(len(p["source"]["origin_revision"]), 40)
        self.assertEqual(len(p["source"]["target_revision"]), 40)

    def test_020_package_digest_is_canonical(self):
        p, *_ = self.fixture()
        self.assertEqual(p["package_sha256"], mod.package_digest(p))

    def test_021_origin_manifest_size_checked(self):
        p, origin, *_ = self.fixture()
        self.assertEqual(p["source"]["manifest_size"], len(origin))

    def test_022_packed_filenames_are_synthetic(self):
        p, *_ = self.fixture()
        self.assertTrue(all(mod.path_ok(x["path"]) for x in p["files"]))

    def test_023_demo_blocks_Map518(self):
        self.assertTrue(mod.demo()["unsafe_native_map_path_blocked"])

    def test_024_cli_check(self):
        out = subprocess.run([sys.executable, str(ROOT / "scripts/regions/audit_unova_g07_incremental_manifest.py"), "--check"],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertFalse(json.loads(out.stdout)["can_install"])

    def test_025_cli_simulate(self):
        out = subprocess.run([sys.executable, str(ROOT / "scripts/regions/audit_unova_g07_incremental_manifest.py"), "--simulate-demo"],
                             capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertEqual(json.loads(out.stdout)["files_checked"], 1)

    def test_026_not_same_source_and_target(self):
        self.fails(lambda p: p["source"].update(target_revision="a" * 40))

    def test_027_origin_digest_checked_against_actual_bytes(self):
        p, o, src, dest = self.fixture()
        p["source"]["manifest_sha256"] = "c" * 64
        p["package_sha256"] = mod.package_digest(p)
        with self.assertRaises(ValueError):
            mod.validate_package(p, o, src, dest)

    def test_028_package_digest_checked_against_actual_metadata(self):
        p, o, src, dest = self.fixture()
        p["source"]["target_revision"] = "c" * 40
        with self.assertRaises(ValueError):
            mod.validate_package(p, o, src, dest)

    def test_029_destination_bytes_are_hashed_not_names(self):
        self.fails(payload_change=lambda old, new: new.update({mod.PREFIX + "g07-2-note.txt": b"xyz"}))

    def test_030_source_bytes_are_hashed_not_names(self):
        self.fails(payload_change=lambda old, new: old.update({mod.PREFIX + "g07-2-note.txt": b"xyz"}))

    def test_031_payload_does_not_mutate_input_buffers(self):
        p, o, src, dest = self.fixture()
        saved = (copy.deepcopy(p), o, copy.deepcopy(src), copy.deepcopy(dest))
        mod.validate_package(p, o, src, dest)
        self.assertEqual((p, o, src, dest), saved)

    def test_032_bad_json_duplicate_keys(self):
        p, o, src, dest = self.fixture()
        raw = o[:-1] + b',"region":"UNOVA"}'
        p["source"]["manifest_size"] = len(raw)
        p["source"]["manifest_sha256"] = mod.digest(raw)
        p["package_sha256"] = mod.package_digest(p)
        with self.assertRaises(ValueError):
            mod.validate_package(p, raw, src, dest)

    def test_033_noncanonical_origin(self):
        p, o, src, dest = self.fixture()
        raw = json.dumps(json.loads(o), indent=2).encode("utf-8")
        p["source"]["manifest_size"] = len(raw)
        p["source"]["manifest_sha256"] = mod.digest(raw)
        p["package_sha256"] = mod.package_digest(p)
        with self.assertRaises(ValueError):
            mod.validate_package(p, raw, src, dest)

    def test_034_corrupted_origin_manifest(self):
        p, o, src, dest = self.fixture()
        raw = b"{" + o[1:]
        p["source"]["manifest_size"] = len(raw)
        p["source"]["manifest_sha256"] = mod.digest(raw)
        p["package_sha256"] = mod.package_digest(p)
        with self.assertRaises(ValueError):
            mod.validate_package(p, raw, src, dest)

    def test_035_wrong_hash_format(self):
        self.fails(lambda p: p["files"][0].update(sha256="0x" + "a" * 64))

    def test_036_unknown_payload_files(self):
        self.fails(payload_change=lambda old, new: new.update({"docs/unova-package-fixtures/extra.txt": b"x"}))

    def test_037_missing_source_bytes(self):
        self.fails(payload_change=lambda old, new: old.clear())

    def test_038_missing_destination_bytes(self):
        self.fails(payload_change=lambda old, new: new.clear())

    def test_039_extra_origin_inventory(self):
        self.fails(origin_change=lambda doc: doc["files"].append({
            "path": "docs/unova-package-fixtures/extra.txt", "sha256": "a" * 64, "size": 3,
        }))

    def test_040_empty_destination_is_invalid(self):
        self.fails(payload_change=lambda old, new: new.update({mod.PREFIX + "g07-2-note.txt": b""}))

    def test_041_noop_increment_is_invalid(self):
        def mutation(p):
            p["files"][0]["sha256"] = p["files"][0]["source_sha256"]
        self.fails(change=mutation, payload_change=lambda old, new: new.update(old))

    def test_042_changed_valid_docs_fixture(self):
        p, origin, old, new = self.fixture()
        name = next(iter(new))
        new[name] = b"next"
        p["files"][0]["sha256"] = mod.digest(new[name])
        p["files"][0]["size"] = len(new[name])
        p["package_sha256"] = mod.package_digest(p)
        self.assertEqual(mod.validate_package(p, origin, old, new)["files_checked"], 1)

    def test_043_cannot_forge_source_revision_in_origin(self):
        self.fails(origin_change=lambda doc: doc.update(revision="c" * 40))

    def test_044_cannot_fake_source_manifest_version(self):
        self.fails(origin_change=lambda doc: doc.update(package_version="2.3.4"))

    def test_045_prevent_unknown_source_inventory_field(self):
        self.fails(origin_change=lambda doc: doc["files"][0].update(approved=True))

    def test_046_prevent_source_manifest_nonfixture(self):
        self.fails(origin_change=lambda doc: doc.update(fixture_only=False))

    def test_047_status_must_stay_planned(self):
        self.fails(lambda p: p.update(status="PLAYABLE"))

    def test_048_travel_G05_predecessor_not_install_proof(self):
        self.assertEqual(mod.j(ROOT, mod.PREDECESSOR)["can_install"], False)

    def test_049_package_version_monotonic_fixture(self):
        self.assertEqual(self.passes(lambda p: p.update(package_version="0.0.2-planned"))["files_checked"], 1)

    def test_050_package_compatible_contract_only(self):
        self.assertEqual(self.passes()["status"], "SYNTHETIC_DOCS_UPDATE_VALIDATED_NOT_INSTALLABLE")


# Dynamically generate independent negative cases with descriptive test names.
_ROOT_TAMPER = {
    "unknown_field": lambda p: p.update(native_map_id=518),
    "schema_version": lambda p: p.update(schema_version=2),
    "schema_version_bool": lambda p: p.update(schema_version=True),
    "foreign_region": lambda p: p.update(region="JOHTO"),
    "unknown_campaign": lambda p: p.update(campaign="BLACK_2"),
    "wrong_channel": lambda p: p.update(channel="android-multiregion"),
    "release_flag": lambda p: p.update(release_allowed=True),
    "native_payload": lambda p: p.update(native_payload_approved=True),
    "executable_mode": lambda p: p.update(mode="apply"),
    "real_game_qa": lambda p: p.update(game_exe_tested=True),
    "save_write_claim": lambda p: p.update(saves_modified=True),
    "unsigned_license": lambda p: p["rights"].update(redistribution_approved=True),
    "missing_rights": lambda p: p.pop("rights"),
    "missing_file_rights": lambda p: p["files"][0].pop("rights"),
    "file_license_forged": lambda p: p["files"][0]["rights"].update(license_id="CC-BY"),
    "file_license_omitted": lambda p: p["files"][0]["rights"].pop("license_id"),
    "rights_proof_forged": lambda p: p["rights"].update(evidence_path="licenses/release.pdf"),
    "unknown_package_id": lambda p: p.update(package_id="UNOVA-NATIVE-READY"),
    "wrong_protocol": lambda p: p["compatibility"].update(protocol_version=2),
    "protocol_bool": lambda p: p["compatibility"].update(protocol_version=True),
    "android_enabled": lambda p: p["compatibility"].update(android="supported"),
    "joiplay_enabled": lambda p: p["compatibility"].update(joiplay="supported"),
    "windows_enabled": lambda p: p["compatibility"].update(windows="native_ready"),
    "installer_claim": lambda p: p["compatibility"].update(installer_adapter_implemented=True),
    "foreign_client": lambda p: p["compatibility"].update(client="JoiPlay"),
    "unknown_client_field": lambda p: p["compatibility"].update(native_maps=True),
    "downgrade": lambda p: p.update(package_version="0.0.0"),
    "real_semver": lambda p: p.update(package_version="1.0.0"),
    "bad_version_suffix": lambda p: p.update(package_version="0.0.2-release"),
    "wrong_source_repository": lambda p: p["source"].update(repository="fake/repo"),
    "wrong_source_path": lambda p: p["source"].update(manifest_path="game/Data/Map518.rxdata"),
    "origin_rev_short": lambda p: p["source"].update(origin_revision="a" * 39),
    "target_rev_uppercase": lambda p: p["source"].update(target_revision="B" * 40),
    "source_field_injection": lambda p: p["source"].update(unova_installed=True),
    "extra_file_field": lambda p: p["files"][0].update(map_id=518),
    "kind_native_map": lambda p: p["files"][0].update(kind="map"),
    "kind_native_script": lambda p: p["files"][0].update(kind="ruby_runtime"),
    "empty_files": lambda p: p.update(files=[]),
    "wrong_file_size": lambda p: p["files"][0].update(size=4),
    "wrong_origin_size": lambda p: p["files"][0].update(source_size=4),
    "file_size_bool": lambda p: p["files"][0].update(size=True),
    "wrong_source_sha": lambda p: p["files"][0].update(source_sha256="e" * 64),
    "wrong_dest_sha": lambda p: p["files"][0].update(sha256="f" * 64),
    "missing_source_manifest_sha": lambda p: p["source"].pop("manifest_sha256"),
}
for _name, _mutate in _ROOT_TAMPER.items():
    def _test(self, change=_mutate):
        self.fails(change=change)
    setattr(UnovaG072Tests, "test_reject_" + _name, _test)

_PATH_ATTACKS = {
    "parent_escape": "../game/Data/Map518.rxdata",
    "inside_escape": "docs/unova-package-fixtures/../game/Data/Map518.rxdata",
    "absolute": "/game/Data/Map518.rxdata",
    "windows_absolute": "C:\\game\\Data\\Map518.rxdata",
    "windows_backslash": "docs\\unova-package-fixtures\\hello.txt",
    "drive": "docs/unova-package-fixtures/C:evil.txt",
    "url_encoded_escape": "docs/unova-package-fixtures/%2e%2e/game.txt",
    "outside_documentation": "game/Data/Map518.rxdata",
    "native_script": "scripts/battle_polish/RegionTravel.rb",
    "save_path": "saves/Save01.rxdata",
    "android_data": "Data/Map518.rxdata",
    "joiplay": "Graphics/Characters/Player.png",
    "installer": "scripts/install_game.py",
    "root_only": "docs/unova-package-fixtures/",
    "source_manifest": "docs/unova-package-fixtures/origin-manifest.json",
    "mixed_case": "docs/unova-package-fixtures/Map518.txt",
    "unicode_confusable": "docs/unova-package-fixtures/caf\u00e9.txt",
    "hidden_segment": "docs/unova-package-fixtures/.hidden/file.txt",
    "multiple_slashes": "docs/unova-package-fixtures/other//file.txt",
    "explicit_dot": "docs/unova-package-fixtures/./file.txt",
    "script_extension": "docs/unova-package-fixtures/tool.py",
    "executable": "docs/unova-package-fixtures/tool.exe",
    "zip_archive": "docs/unova-package-fixtures/map.zip",
    "rxdata": "docs/unova-package-fixtures/Map518.rxdata",
    "colon": "docs/unova-package-fixtures/name:evil.txt",
    "percent_question": "docs/unova-package-fixtures/note?.txt",
    "null": "docs/unova-package-fixtures/file\x00.txt",
    "doubled_dot": "docs/unova-package-fixtures/file..txt",
}
for _name, _path in _PATH_ATTACKS.items():
    def _test(self, name=_path):
        self.assertFalse(mod.path_ok(name))
        self.fails(lambda p: p["files"][0].update(path=name))
    setattr(UnovaG072Tests, "test_path_block_" + _name, _test)


if __name__ == "__main__":
    unittest.main()
