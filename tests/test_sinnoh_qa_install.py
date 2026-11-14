"""Sinnoh private Windows QA installer: synthetic, no ROM, no actual Game.exe."""
from __future__ import annotations

import copy
import hashlib
import json
import shutil
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

from build_johto_events import ruby
from install_sinnoh_qa_copy import (
    BARRY_READY, COMPILED, COMPILE_REQUEST, QA_META, START_PLUGIN,
    compile_boot, install, jsonc, load_overlay, prepare, verify,
)
from prepare_sinnoh_pilot_bundle import build as build_overlay, publish as publish_overlay
from stage import serialize
from test_sinnoh_pilot_bundle import inputs
from server.ruby_marshal import loads
import johto_qa as qa

PROFILE = "abcdef123456"


def write(parent: Path, filename: str, data: bytes):
    path = parent / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def fixture(root: Path):
    geom, events, spec, draft, game = inputs(root)
    # Synthetic native game baseline. Compiled Main exists as a fixture,
    # NOT a real binary to be executed.
    write(game, "Data/System.rxdata",
          serialize(ruby("RPG::System", start_map_id=1, start_x=3,
                         start_y=4), qa.SYSTEM_CLASSES))
    native_script = (
        b"def main\n"
        b"    PluginManager.runPlugins\n"
        b"    Compiler.main\n"
        b"end\n"
    )
    write(game, "Data/Scripts.rxdata", b"\x04\x08" + qa.dump([
        [1, qa.RubyString(b"Main"),
         qa.RubyString(zlib.compress(native_script))],
    ]))
    write(game, "mkxp.json",
          b'{\n // Comment, URL in quotes must survive\n'
          b' "iconPath":"https://example.invalid/icon.png",\n'
          b' "dataPathApp": "Main Blue",\n'
          b' "dataPathOrg": "Main Org",\n}\n')
    write(game, "Game.ini", b"[Game]\nTitle=Main Blue\n")
    write(game, "Audio/Pokemon/placeholder.txt", b"test audio")
    write(game, "Fonts/placeholder.txt", b"test font")
    write(game, "Graphics/placeholder.txt", b"test graphics")
    write(game, "Plugins/ZZZZ Blue Story and Presentation/RegionStart.rb",
          b"# BlueRegionStart synthetic")
    write(game, "Plugins/ZZZZ Blue Story and Presentation/meta.txt",
          b"Name = Blue Battle Presentation and Story\n")
    write(game, "Data/File A.rxdata", b"MAIN SAVE SHOULD NOT COPY")
    write(game, "Saves/File A.rxdata", b"MAIN BACKUP SAVE")
    write(game, "Data/backup.tmp", b"should not copy")
    shutil.copyfile(ROOT / "scripts/regions/SinnohQAStart.rb",
                    write(root, "scripts/regions/SinnohQAStart.rb", b""))
    report, blobs = build_overlay(geom, events, spec, draft, game,
                                  project=root)
    root.joinpath(".blue-work").mkdir(exist_ok=True)
    output = root / ".blue-work/sinnoh-integration-v1"
    publish_overlay(root, output, report, blobs)
    return game, output, spec


class SinnohQAInstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sinnoh-isolated-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game, self.bundle, self.spec = fixture(self.root)

    def planned(self, spec=None, token=PROFILE):
        return prepare(self.game, self.bundle,
                       spec if spec is not None else self.spec,
                       token=token, project=self.root)

    def test_dry_run_has_unique_saves_and_does_not_create_copy(self):
        before = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in self.game.rglob("*") if p.is_file()}
        report, files, native = self.planned()
        self.assertEqual(report["mode"], "ISOLATED_QA_INSTALL_PLAN")
        self.assertFalse(report["runtime_playable"])
        self.assertFalse(report["ready_marker_created"])
        self.assertFalse(report["can_install_into_main_game"])
        self.assertFalse(report["current_main_game_or_saves_modified"])
        profile = report["save_isolation"]
        self.assertEqual(profile["dataPathApp"], "Sinnoh-QA-abcdef123456")
        self.assertEqual(profile["dataPathOrg"], "Dessastre-Sinnoh-QA-abcdef123456")
        self.assertNotEqual(profile["dataPathApp"], "Main Blue")
        self.assertIn(START_PLUGIN, files)
        self.assertIn(COMPILE_REQUEST, files)
        self.assertNotIn(COMPILED, files)
        self.assertNotIn(BARRY_READY, files)
        self.assertIn("Data/System.rxdata", files)
        self.assertIn("Data/Scripts.rxdata", files)
        system = loads(files["Data/System.rxdata"])
        self.assertEqual([system.attrs[f"@{k}"] for k in
                          ("start_map_id", "start_x", "start_y")],
                         [500, 10, 11])
        cfg = json.loads(files["mkxp.json"])
        self.assertEqual(cfg["dataPathApp"], profile["dataPathApp"])
        self.assertEqual(cfg["iconPath"], "https://example.invalid/icon.png")
        self.assertIn("Title=Sinnoh QA abcdef123456", files["Game.ini"].decode())
        self.assertNotIn("Data/File A.rxdata", native)
        self.assertNotIn("Saves/File A.rxdata", native)
        self.assertFalse((self.root / ".blue-work/game-sinnoh-qa-abcdef123456").exists())
        after = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in self.game.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_full_copy_preserves_decades_and_excludes_all_save_slots(self):
        report, blobs, native = self.planned()
        dest = self.root / ".blue-work/game-sinnoh-qa-abcdef123456"
        self.assertTrue(install(self.root, self.game, dest, report, blobs, native)["created"])
        self.assertTrue((dest / "Game.exe").is_file())
        self.assertEqual((dest / "Data/Map001.rxdata").read_bytes(),
                         b"Decades must stay unchanged")
        self.assertTrue((dest / "Data/Map500.rxdata").exists())
        self.assertTrue((dest / "Plugins/ZZZZZ Blue Sinnoh Intro/SinnohPilot.rb").exists())
        self.assertTrue((dest / START_PLUGIN).exists())
        self.assertFalse((dest / "Data/File A.rxdata").exists())
        self.assertFalse((dest / "Saves/File A.rxdata").exists())
        self.assertFalse((dest / BARRY_READY).exists())
        self.assertFalse((dest / COMPILED).exists())
        self.assertTrue((dest / COMPILE_REQUEST).exists())
        self.assertTrue((dest / "_sinnoh_qa_originals/Data/System.rxdata").exists())
        result = verify(dest, project=self.root)
        self.assertTrue(result["save_profile_isolated_in_config"])
        self.assertFalse(result["compiled_marker_present"])
        self.assertTrue(result["compile_request_pending"])
        self.assertFalse(result["ready_to_launch_for_manual_testing"])
        self.assertFalse(result["playable_approved"])
        with self.assertRaisesRegex(ValueError, "já existe"):
            install(self.root, self.game, dest, report, blobs, native)

    def test_native_compile_hook_only_generates_compiled_token_not_barry_ready(self):
        before = (self.game / "Data/Scripts.rxdata").read_bytes()
        after = compile_boot(before)
        from prepare_restore import Marshal
        rows = Marshal(after).read()
        src = zlib.decompress(rows[0][2]).decode("utf-8")
        self.assertIn("blue-sinnoh-qa-compiled.txt", src)
        self.assertIn("GameData::Trainer.exists?(:BLUE_SINNOH_RIVAL", src)
        self.assertNotIn("blue-sinnoh-rival-ready.txt", src)
        self.assertIn("PluginManager.runPlugins", src)
        self.assertEqual(before, (self.game / "Data/Scripts.rxdata").read_bytes())
        with self.assertRaisesRegex(ValueError, "limpo"):
            compile_boot(after)

    def test_compilation_proof_allows_static_verify_not_gameplay_approval(self):
        report, blobs, native = self.planned()
        dest = self.root / ".blue-work/game-sinnoh-qa-abcdef123456"
        install(self.root, self.game, dest, report, blobs, native)
        token = json.loads((dest / QA_META).read_text("utf-8"))["compile_token"]
        (dest / COMPILED).write_text(token + "\n", encoding="ascii")
        (dest / COMPILE_REQUEST).unlink()
        result = verify(dest, project=self.root)
        self.assertTrue(result["compiled_marker_present"])
        self.assertTrue(result["ready_to_launch_for_manual_testing"])
        self.assertFalse(result["playable_approved"])
        self.assertFalse(result["python_verified_trainer_battle"])
        self.assertFalse(result["android_verified"])

    def test_rejects_compiled_token_mismatch_and_barry_ready(self):
        report, blobs, native = self.planned()
        dest = self.root / ".blue-work/game-sinnoh-qa-abcdef123456"
        install(self.root, self.game, dest, report, blobs, native)
        (dest / COMPILED).write_text("0"*64, encoding="ascii")
        with self.assertRaisesRegex(ValueError, "não corresponde"):
            verify(dest, project=self.root)
        (dest / COMPILED).unlink()
        (dest / BARRY_READY).write_text("premature", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Marcador"):
            verify(dest, project=self.root)

    def test_rejects_wrong_native_start_or_unverified_spawn(self):
        bad = copy.deepcopy(self.spec)
        bad["start"]["passability_verified"] = False
        with self.assertRaisesRegex(ValueError, "Spawn"):
            self.planned(bad)
        bad = copy.deepcopy(self.spec)
        bad["start"]["map_id"] = 999
        with self.assertRaisesRegex(ValueError, "Spawn"):
            self.planned(bad)

    def test_rejects_legacy_or_overwritten_map(self):
        (self.game / "Data/Map500.rxdata").write_bytes(b"native collision")
        with self.assertRaisesRegex(ValueError, "MapID"):
            self.planned()

    def test_rejects_pilot_output_in_main_game(self):
        report, blobs, native = self.planned()
        with self.assertRaisesRegex(ValueError, "dentro"):
            install(self.root, self.game, self.game / "bad", report, blobs, native)

    def test_rejects_profile_override_in_mkxp(self):
        (self.game / "mkxp.json").write_text('{"customSavePath":"C:/other"}',
                                             encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "isolamento não provado"):
            self.planned()

    def test_rejects_modified_overlay_or_file_not_in_manifest(self):
        target = self.bundle / "PBS/trainers_sinnoh_barry.txt"
        target.write_bytes(target.read_bytes() + b"tampered")
        with self.assertRaisesRegex(ValueError, "adulterado"):
            self.planned()

    def test_rejects_symlink_into_game(self):
        shortcut = self.root / ".blue-work/malicious"
        try:
            shortcut.symlink_to(self.game, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("Symlink creation unavailable")
        report, files, native = self.planned()
        with self.assertRaisesRegex(ValueError, "link simbólico"):
            install(self.root, self.game, shortcut / "qa", report, files, native)

    def test_rejects_extra_overlay_payload(self):
        (self.bundle / "test-extra.bin").write_bytes(b"bad")
        with self.assertRaisesRegex(ValueError, "extras"):
            self.planned()


if __name__ == "__main__":
    unittest.main()
