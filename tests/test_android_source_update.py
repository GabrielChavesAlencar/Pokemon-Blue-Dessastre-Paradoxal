import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.android.source_update import preflight, clone_verified_install, commit_local, atomic_file, manifest_row
from unittest.mock import patch
from scripts.android.update_client import MARKER, read_installed


class AndroidPinnedSourceUpdateTests(unittest.TestCase):
    def make(self,root):
        data=root/"Data"
        data.mkdir()
        content=b"synthetic native file"
        regions={"kanto":{str(i):mid for i,mid in enumerate(range(300,465),10)},
                 "hoenn":{str(i):mid for i,mid in enumerate(range(700,899),10)}}
        installed={"schema":1,"channel":"multiregion","revision":"a"*40,"files":{}}
        for region,ids in regions.items():
            (data/f"blue-{region}-install.json").write_text(json.dumps({"maps":ids}))
            for mid in ids.values():
                path=f"Data/Map{mid:03d}.rxdata"
                (root/path).write_bytes(content)
                installed["files"][path]={"sha256":hashlib.sha256(content).hexdigest()}
        (root/MARKER).write_text(json.dumps(installed))
        save=root/"saves"/"Game.rxdata"
        save.parent.mkdir()
        save.write_bytes(b"not a real save; do not inspect")
        return save

    def test_preflight_is_read_only_and_keeps_hoenn_and_save(self):
        with TemporaryDirectory() as work:
            root=Path(work)
            saved=self.make(root)
            before={p:p.read_bytes() for p in root.rglob("*") if p.is_file()}
            proof=preflight(root)
            self.assertEqual(proof["hoenn_maps"],199)
            self.assertEqual(proof["kanto_maps"],165)
            self.assertFalse(proof["updated"])
            self.assertFalse(proof["compile_verified"])
            self.assertEqual({p:p.read_bytes() for p in root.rglob("*") if p.is_file()},before)
            self.assertIn(saved,before)

    def test_reject_missing_modified_or_colliding_map_before_download(self):
        with TemporaryDirectory() as work:
            root=Path(work)
            self.make(root)
            hoenn=root/"Data/Map700.rxdata"
            before=hoenn.read_bytes()
            hoenn.write_bytes(b"owner edit")
            with self.assertRaisesRegex(ValueError,"Map700"):
                preflight(root)
            self.assertEqual(hoenn.read_bytes(),b"owner edit")
            hoenn.write_bytes(before)
            (root/"Data/Map609.rxdata").write_bytes(b"other region")
            with self.assertRaisesRegex(ValueError,"609"):
                preflight(root)

    def test_clone_only_verified_runtime_and_rolls_back_bad_copy(self):
        with TemporaryDirectory() as folder:
            parent=Path(folder).resolve()
            root=parent/"installed"
            root.mkdir()
            save=self.make(root)
            manifest=read_installed(root)
            stage=parent/"stage"
            for meta in manifest["files"].values():
                meta["size"]=len(b"synthetic native file")
            clone_verified_install(root,stage,manifest)
            self.assertTrue((stage/"Data/Map700.rxdata").is_file())
            self.assertFalse((stage/save.relative_to(root)).exists())
            self.assertEqual(save.read_bytes(),b"not a real save; do not inspect")
            bad=parent/"bad"
            (root/"Data/Game.rxdata").write_bytes(b"private")
            manifest["files"]["Data/Game.rxdata"]={"size":7,"sha256":hashlib.sha256(b"private").hexdigest()}
            with self.assertRaisesRegex(ValueError,"Caminho não permitido"):
                clone_verified_install(root,bad,manifest)
            self.assertFalse(bad.exists())
            self.assertEqual((root/"Data/Game.rxdata").read_bytes(),b"private")

    def test_apply_fault_rolls_back_and_leaves_revision_unchanged(self):
        with TemporaryDirectory() as folder:
            parent=Path(folder).resolve()
            root,stage=parent/"installed",parent/"stage"
            root.mkdir()
            save=self.make(root)
            names=["Data/Map609.rxdata","Data/Map610.rxdata"]
            (stage/"Data").mkdir(parents=True)
            (root/names[0]).write_bytes(b"old tile")
            for name in names:
                (stage/name).write_bytes(b"local new tile")
            changes={name:manifest_row(stage/name) for name in names}
            revision=(root/MARKER).read_bytes()
            def limited(path,data):
                if path==root/names[1]:
                    raise OSError("simulated I/O failure")
                return atomic_file(path,data)
            with patch("scripts.android.source_update.atomic_file",side_effect=limited):
                with self.assertRaisesRegex(OSError,"simulated"):
                    commit_local(root,stage,changes,b"new revision",parent/"recovery")
            self.assertEqual((root/MARKER).read_bytes(),revision)
            self.assertEqual((root/names[0]).read_bytes(),b"old tile")
            self.assertFalse((root/names[1]).exists())
            self.assertEqual(save.read_bytes(),b"not a real save; do not inspect")
