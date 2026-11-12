"""Kanto music: unchanged-bytes audit, correct target folders and safe local copies.

All test MP3s are synthetic bytes and never reproduce soundtrack recordings.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.music import install_kanto_music as music


class KantoMusicInstallerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game = self.root / "game"
        (self.game / "Audio").mkdir(parents=True)
        (self.game / "Game.exe").write_bytes(b"fake test-only game")
        self.entries = []
        kinds = {1,9,14,22,23,29,31,42,43,44,49,51,54,58}
        self.payload_bytes = 0
        for n in [*range(1,61),70,71,72,73]:
            name = f"1-{n:02d}. Example.mp3"
            kind = "ME" if n in kinds else "BGM"
            raw = f"ID3-synthetic-audio-{n}".encode("ascii")
            path = self.root / "assets" / "music" / "kanto" / kind / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
            self.payload_bytes += len(raw)
            self.entries.append({
                "number":n, "title":f"Example {n}", "filename":name, "kind":kind,
                "usage":"synthetic fixture", "bytes":len(raw),
                "git_blob_sha":music.git_blob_sha(path),
                "repo_path":f"assets/music/kanto/{kind}/{name}",
                "game_path":f"Audio/{kind}/Kanto/{name}",
            })
        self.manifest = self.root / "data/kanto-music.json"
        self.manifest.parent.mkdir()
        self.manifest.write_text(json.dumps({
            "schema":1, "region":"KANTO", "files":self.entries,
            "total_bytes":self.payload_bytes,
        }),encoding="utf-8")
        self.p1=patch.object(music,"ROOT",self.root)
        self.p2=patch.object(music,"EXPECTED_BYTES",self.payload_bytes)
        self.p1.start();self.p2.start()
        self.addCleanup(self.p1.stop);self.addCleanup(self.p2.stop)

    def run_import(self, apply=False):
        return music.install(self.game,apply=apply,
                             manifest_path=self.manifest,base=self.root)

    def test_audits_all_64_with_exact_source_git_blobs(self):
        result=music.audit(self.manifest,self.root)
        self.assertEqual(result["files"],64)
        self.assertEqual(result["BGM"],50)
        self.assertEqual(result["ME"],14)
        self.assertEqual(result["bytes"],self.payload_bytes)

    def test_preview_does_not_write_and_apply_is_idempotent(self):
        preview=self.run_import()
        self.assertEqual(preview["new"],64)
        self.assertFalse(preview["writes"])
        self.assertFalse((self.game/"Audio/BGM/Kanto").exists())
        applied=self.run_import(apply=True)
        self.assertEqual(applied["new"],64)
        self.assertTrue(applied["writes"])
        self.assertEqual(len(list((self.game/"Audio/BGM/Kanto").glob("*.mp3"))),50)
        self.assertEqual(len(list((self.game/"Audio/ME/Kanto").glob("*.mp3"))),14)
        again=self.run_import(apply=True)
        self.assertEqual(again["new"],0)
        self.assertEqual(again["unchanged"],64)
        self.assertFalse(again["writes"])

    def test_conflict_aborts_without_overwriting_any_track(self):
        target=self.game/self.entries[17]["game_path"]
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(b"KEEP ORIGINAL")
        with self.assertRaisesRegex(ValueError,"Conflito"):
            self.run_import(apply=True)
        self.assertEqual(target.read_bytes(),b"KEEP ORIGINAL")
        self.assertFalse((self.game/"Audio/ME/Kanto").exists())

    def test_missing_or_modified_asset_rejected(self):
        source=self.root/self.entries[0]["repo_path"]
        source.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError,"corrompido"):
            music.audit(self.manifest,self.root)
        source.unlink()
        with self.assertRaisesRegex(ValueError,"ausente"):
            music.audit(self.manifest,self.root)

    def test_bad_manifest_paths_cannot_escape_assets(self):
        rows=json.loads(self.manifest.read_text("utf-8"))
        rows["files"][0]["repo_path"]="../../outside.mp3"
        self.manifest.write_text(json.dumps(rows),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"Destinos divergentes"):
            self.run_import()

    def test_rejects_game_outside_repo(self):
        music.audit(self.manifest,self.root)
        outside=Path(self.tmp.name).parent/"not-the-game"
        with self.assertRaisesRegex(ValueError,"Destinos permitidos"):
            music.safe_target_game(outside)


if __name__=="__main__":
    unittest.main()
