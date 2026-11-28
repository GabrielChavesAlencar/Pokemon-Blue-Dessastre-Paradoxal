import contextlib
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from scripts.android import build_source_bootstrap, source_bootstrap, world_source_update as updater


class AndroidWorldSourceTests(unittest.TestCase):
    def test_zip_contains_only_launcher_and_guide(self):
        with TemporaryDirectory() as work:
            output = Path(work) / "install.zip"
            build_source_bootstrap.build(output)
            with ZipFile(output) as archive:
                self.assertEqual(archive.namelist(), ["ATUALIZAR-ANDROID.py", "LEIA-ME.md"])
                self.assertEqual(archive.read("ATUALIZAR-ANDROID.py"),
                                 Path(source_bootstrap.__file__).read_bytes())
            self.assertTrue(output.with_suffix(".zip.sha256").is_file())

    def test_discovers_only_matching_world_release_refs(self):
        refs = "\n".join([f"{'a'*40}\trefs/tags/android-source-world-10-aaaaaaa",
                          f"{'b'*40}\trefs/tags/android-source-world-11-aaaaaaa",
                          f"{'b'*40}\trefs/tags/android-k05-source-12-bbbbbbb",
                          f"{'b'*40}\trefs/tags/android-source-world-9-bbbbbbb"])
        self.assertEqual(source_bootstrap.release_revisions(refs), {9: "b"*40, 10: "a"*40})
        with self.assertRaisesRegex(ValueError, "mesma versão"):
            source_bootstrap.release_revisions(refs + f"\n{'b'*40}\trefs/tags/android-source-world-10-bbbbbbb")

    def staging_files(self, content):
        def assemble(root, staged, previous):
            (staged / "mkxp.json").write_text("{}", encoding="utf8")
            (staged / "Game.ini").write_text("[Game]", encoding="ascii")
            (staged / "Game.exe").write_bytes(b"engine")
            data = staged / "Data"
            data.mkdir()
            for region, maps in (("kanto", {"7": 301}), ("hoenn", {"1": 700})):
                (data / f"blue-{region}-install.json").write_text(json.dumps({"maps": maps}))
            if previous is None:
                (data / "retired.dat").write_bytes(b"old managed file")
            (data / "Map700.rxdata").write_bytes(content)
            (data / "PluginScripts.rxdata").write_bytes(content)
            scripts = staged / updater.package.MOBILE
            scripts.parent.mkdir(parents=True)
            scripts.write_bytes(content)
        return assemble

    def test_new_install_then_transactional_update_keeps_same_save(self):
        with TemporaryDirectory() as work, contextlib.redirect_stdout(io.StringIO()), \
                patch.object(updater.package, "request_compile"), patch.object(updater.package, "verify_regions"), \
                patch.object(updater.package, "compiled_mobile", return_value="c"*64):
            root = Path(work).resolve() / "Blue"
            holder = root.with_name("Blue-Compilar-Fontes")
            staged = holder / "game"
            for release, revision, content in ((1, "a"*40, b"first"), (2, "b"*40, b"second")):
                with patch.object(updater, "assemble", self.staging_files(content)):
                    updater.workflow(root, release, revision)
                self.assertEqual(root.exists(), release == 2)
                (staged / updater.COMPILED).write_text(updater.package.fingerprint(staged), encoding="ascii")
                updater.workflow(root, release, revision)
                self.assertEqual((root / "Data/Map700.rxdata").read_bytes(), content)
                self.assertEqual((root / "Data/retired.dat").is_file(), release == 1)
                self.assertFalse(holder.exists())
                self.assertFalse((root / updater.COMPILED).exists())
                self.assertEqual(updater.current_install(root)["revision"], revision)
                self.assertEqual((root / "mkxp.json").read_text(), "{}")
                save = root / "File G.rxdata"
                if release == 1:
                    save.write_bytes(b"player")
                self.assertEqual(save.read_bytes(), b"player")
                updater.workflow(root, release, revision)
            with self.assertRaisesRegex(ValueError, "anterior"):
                updater.workflow(root, 1, "a"*40)

    def test_rejects_legacy_install_without_writing_to_it(self):
        with TemporaryDirectory() as work:
            root = Path(work).resolve()
            updater.put_json(root / updater.MARKER, {"schema": 1, "channel": "multiregion",
                                                    "revision": "a"*40, "files": {}})
            before = sorted(root.rglob("*"))
            with self.assertRaisesRegex(ValueError, "outra edição"):
                updater.workflow(root, 1, "b"*40)
            self.assertEqual(sorted(root.rglob("*")), before)

    def test_world_inventory_keeps_celadon_receipt_not_saves(self):
        with TemporaryDirectory() as work:
            game = Path(work).resolve()
            data = game / "Data"
            data.mkdir()
            receipt = data / "blue-kanto-k06-services.json"
            receipt.write_text("{}")
            (data / "File G.rxdata").write_bytes(b"user")
            self.assertEqual(updater.source_inventory(game),
                             {"Data/blue-kanto-k06-services.json": receipt})

    def test_non_windows_kanto_overlay_requires_exact_world_ownership(self):
        from k06_approach_migration import managed_world_assembly
        with TemporaryDirectory() as work:
            root = Path(work).resolve()
            project, target = root / "recipe", root / "Blue"
            game = project / "game"
            game.mkdir(parents=True)
            owner = project / ".blue-work/android-source-owner.json"
            with patch.dict("os.environ", {"BLUE_KANTO_WORLD_TARGET": str(target)}):
                self.assertFalse(managed_world_assembly(project, game))
                owner.parent.mkdir()
                updater.put_json(owner, {"game": str(game), "target": str(target)})
                self.assertTrue(managed_world_assembly(project, game))
                self.assertFalse(managed_world_assembly(project, target))
                updater.put_json(owner, {"game": str(game), "target": str(root / "Other")})
                self.assertFalse(managed_world_assembly(project, game))
