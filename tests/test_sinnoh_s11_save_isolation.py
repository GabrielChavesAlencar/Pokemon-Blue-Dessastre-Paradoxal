"""S11: the Sinnoh pilot must never read or overwrite other regions' saves.

Fixtures create synthetic Game.exe bytes; no real executable, save or AppData
is accessed. The runtime reload must still be verified in Windows/JoiPlay.
"""
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

from sinnoh_save_isolation import namespace, validate_namespace
from install_sinnoh_qa_copy import prepare, install, verify
from launch_sinnoh_qa import preflight
from test_sinnoh_qa_install import fixture, simulate_native_report, PROFILE


class S11SaveNamespaceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sinnoh-s11-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / ".blue-work").mkdir()
        self.qa = self.root / ".blue-work/game-sinnoh-qa-abcdef123456"
        self.qa.mkdir()
        self.profile = namespace("abcdef123456")
        self.ini = "[Game]\nTitle=" + self.profile["title"] + "\n"
        self.config = {"windowTitle": self.profile["title"],
                       "dataPathApp": self.profile["dataPathApp"],
                       "dataPathOrg": self.profile["dataPathOrg"]}

    def check(self, profile=None, cfg=None, ini=None, qa=None, main=None):
        return validate_namespace(
            self.qa if qa is None else qa,
            self.profile if profile is None else profile,
            self.config if cfg is None else cfg,
            self.ini if ini is None else ini,
            project=self.root, main_config=main)

    def test_private_token_produces_unique_namespace_without_absolute_paths(self):
        other = namespace("000000000001")
        self.assertNotEqual(self.profile["dataPathApp"], other["dataPathApp"])
        self.assertNotEqual(self.profile["dataPathOrg"], other["dataPathOrg"])
        self.assertNotIn("/", self.profile["dataPathApp"])
        self.assertNotIn("\\", self.profile["dataPathOrg"])
        self.assertTrue(self.check()["save_namespace_verified"])
        self.assertFalse(self.check()["native_save_reload_verified"])

    def test_rejects_bad_or_path_injection_tokens(self):
        for value in ("", "ABCDEF123456", "abcdef12345", "abcdef1234567",
                      "../game", "abcdef123456/../game", "g"*12, None):
            with self.subTest(token=value), self.assertRaises(ValueError):
                namespace(value)

    def test_qa_profile_must_match_folder_token_exactly(self):
        for value in (
            dict(self.profile, dataPathApp="Decades"),
            dict(self.profile, dataPathOrg="Dessastre-Johto"),
            dict(self.profile, title="Main Blue"),
            dict(self.profile, title="Sinnoh QA 000000000001"),
            {**self.profile, "legacySave": True},
        ):
            with self.subTest(profile=value), self.assertRaisesRegex(ValueError,"namespace"):
                self.check(profile=value)

    def test_rejects_foreign_or_shared_mkxp_paths(self):
        for change in (
            {"dataPathApp": "Main Blue"},
            {"dataPathOrg": "Pokemon-Blue"},
            {"windowTitle": "Johto"},
            {"savePath": "C:/Users/example/AppData/Blue"},
            {"userDataDir": "../game"},
            {"customSavePath": "/tmp/other"},
        ):
            cfg = {**self.config, **change}
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.check(cfg=cfg)

    def test_rejects_game_ini_mismatch_and_duplicate_title(self):
        for ini in (
            "[Game]\nTitle=Decades\n",
            "[Game]\nTitle=" + self.profile["title"] * 0 + "\n",
            self.ini + "Title=" + self.profile["title"] + "\n",
        ):
            with self.subTest(ini=ini), self.assertRaisesRegex(ValueError,"Game.ini"):
                self.check(ini=ini)

    def test_rejects_qa_directory_outside_blue_work(self):
        with self.assertRaisesRegex(ValueError, "pasta QA"):
            self.check(qa=self.root / "game")
        with self.assertRaisesRegex(ValueError, "pasta QA"):
            self.check(qa=self.root / ".blue-work/johto-test")
        with self.assertRaisesRegex(ValueError, "namespace"):
            self.check(qa=self.root / ".blue-work/game-sinnoh-qa-000000000001")

    def test_rejects_qa_namespace_colliding_with_original_main(self):
        main={"dataPathApp": self.profile["dataPathApp"], "dataPathOrg":"Main Org"}
        with self.assertRaisesRegex(ValueError, "coincide"):
            self.check(main=main)
        main={"dataPathApp":"Main App","dataPathOrg":self.profile["dataPathOrg"]}
        with self.assertRaisesRegex(ValueError, "coincide"):
            self.check(main=main)

    def test_rejects_symlinked_qa_and_work_root(self):
        alias = self.root / ".blue-work/game-sinnoh-qa-000000000001"
        try:
            alias.symlink_to(self.qa, target_is_directory=True)
        except (OSError,NotImplementedError):
            self.skipTest("symlink indisponivel")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.check(qa=alias)

    def test_read_only_namespace_check_does_not_touch_files(self):
        save = self.root / "game/Saves/File A.rxdata"
        save.parent.mkdir(parents=True)
        save.write_bytes(b"FOREIGN USER SAVE - MUST NOT TOUCH")
        before=hashlib.sha256(save.read_bytes()).hexdigest()
        for _ in range(3):
            self.assertTrue(self.check()["save_namespace_verified"])
        self.assertEqual(hashlib.sha256(save.read_bytes()).hexdigest(),before)


class S11InstalledPilotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sinnoh-s11-copy-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game,self.overlay,self.spec = fixture(self.root)
        report, files, native = prepare(
            self.game, self.overlay, self.spec, token=PROFILE, project=self.root)
        self.qa = self.root / ".blue-work/game-sinnoh-qa-abcdef123456"
        install(self.root, self.game, self.qa, report, files, native)

    def test_private_install_uses_exact_token_and_does_not_inherit_foreign_saves(self):
        proof=json.loads((self.qa/"Sinnoh qa.json").read_text("utf-8"))
        self.assertEqual(proof["profile"],namespace(PROFILE))
        state=verify(self.qa,project=self.root)
        self.assertTrue(state["save_namespace_verified"])
        self.assertFalse(state["foreign_save_inherited"])
        self.assertFalse(state["native_save_reload_verified"])
        self.assertFalse(state["playable_approved"])
        self.assertFalse((self.qa/"Saves/File A.rxdata").exists())
        self.assertFalse((self.qa/"Data/File A.rxdata").exists())
        self.assertEqual((self.game/"Saves/File A.rxdata").read_bytes(),
                         b"MAIN BACKUP SAVE")

    def test_modified_qa_profile_rejected_before_launch_without_touching_main(self):
        file=self.qa/"mkxp.json"
        cfg=json.loads(file.read_text("utf-8"))
        cfg["dataPathApp"]="Decades Main"
        file.write_text(json.dumps(cfg),encoding="utf-8")
        with self.assertRaises(ValueError):
            verify(self.qa,project=self.root)
        with self.assertRaises(ValueError):
            preflight(self.qa,project=self.root,mode="compile")
        self.assertEqual((self.game/"Saves/File A.rxdata").read_bytes(),
                         b"MAIN BACKUP SAVE")

    def test_injected_foreign_save_file_is_rejected_and_not_removed(self):
        foreign=self.qa/"Saves/File A.rxdata"
        foreign.parent.mkdir()
        foreign.write_bytes(b"DO NOT USE FOREIGN SAVE")
        with self.assertRaisesRegex(ValueError,"incompatível"):
            verify(self.qa,project=self.root)
        self.assertEqual(foreign.read_bytes(), b"DO NOT USE FOREIGN SAVE")

    def test_independent_copy_token_does_not_match_first_copy_metadata(self):
        fake=self.root/".blue-work/game-sinnoh-qa-000000000001"
        fake.mkdir()
        with self.assertRaises(ValueError):
            validate_namespace(fake,namespace(PROFILE),self._mkxp(),
                               self._ini(),project=self.root)

    def _mkxp(self):
        return json.loads((self.qa/"mkxp.json").read_text("utf-8"))

    def _ini(self):
        return (self.qa/"Game.ini").read_text("utf-8")


if __name__ == "__main__":
    unittest.main()
