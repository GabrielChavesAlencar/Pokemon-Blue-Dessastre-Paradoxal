"""Blue-Story one-click Sinnoh QA supervisor, wholly synthetic fixtures.

No actual Game.exe execution, no private saves, no native gameplay claims.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from scripts.windows import sinnoh_qa_supervisor as supervisor


class SinnohSupervisorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sinnoh-supervisor-fixture-")
        self.addCleanup(self.tmp.cleanup)
        self.project = Path(self.tmp.name)
        self.qa = self.project / ".blue-work" / "game-sinnoh-experimental-012345abcdef"
        self.qa.mkdir(parents=True)
        self.game = self.project / "game"
        self.game.mkdir()
        (self.game / "Game.exe").write_bytes(b"main game is never launched")
        (self.qa / "Game.exe").write_bytes(b"synthetic non-executable fixture")
        profile = {
            "title": "Sinnoh QA 012345abcdef",
            "dataPathApp": "Sinnoh-QA-012345abcdef",
            "dataPathOrg": "Dessastre-Sinnoh-QA-012345abcdef",
        }
        self.write("mkxp.json", json.dumps({
            **profile, "windowTitle": profile["title"]}))
        self.write("Game.ini", "Title=" + profile["title"] + "\n")
        self.maps = {"SINNOH_PLAYER_BEDROOM": 442}
        self.maps.update({"MAP%d" % i: 443+i for i in range(8)})
        files = ["Data/MapInfos.rxdata", supervisor.TILESETS] + [
            "Data/Map%03d.rxdata" % n for n in self.maps.values()]
        self.hashes = {}
        for rel in files:
            data = ("synthetic:" + rel).encode()
            self.write(rel, data)
            self.hashes[rel] = hashlib.sha256(data).hexdigest()
        pristine_bytes = (self.qa / supervisor.TILESETS).read_bytes()
        self.write(supervisor.PRISTINE, pristine_bytes)
        self.hashes[supervisor.PRISTINE] = self.hashes[supervisor.TILESETS]
        self.manifest = {
            "schema": 1, "region": "SINNOH",
            "mode": supervisor.installer.MODE,
            "profile_token": "012345abcdef",
            "main_game_modified": False, "personal_saves_copied": False,
            "runtime_playable_verified": False, "r09_native_qa_executed": 0,
            "save_profile": profile, "mapids": self.maps,
            "start": [442, 10, 8], "file_sha256": self.hashes,
        }
        self.write("sinnoh-experimental-qa.json", json.dumps(self.manifest))
        self.base_sha = hashlib.sha256((self.game / "Game.exe").read_bytes()).hexdigest()

    def write(self, rel, raw):
        path = self.qa / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw.encode() if isinstance(raw, str) else raw)

    def run(self, fake):
        result = supervisor.supervise(self.project, self.qa, fake)
        self.assertEqual(hashlib.sha256((self.game / "Game.exe").read_bytes()).hexdigest(), self.base_sha)
        self.assertFalse((self.qa / supervisor.ENABLED).exists())
        self.assertFalse((self.qa / supervisor.REQUEST).exists())
        return result

    def test_01_clean_one_click_launch(self):
        calls=[]
        self.assertEqual(self.run(lambda exe, cwd: calls.append((exe,cwd)) or 0),0)
        self.assertEqual(calls,[(self.qa/"Game.exe",self.qa)])

    def test_02_initial_compilation_mutates_tilesets_then_recovers(self):
        self.write(supervisor.COMPILE_REQUEST, "synthetic token")
        calls=[]
        def fake(exe, cwd):
            calls.append((exe,cwd))
            if len(calls)==1:
                self.write(supervisor.TILESETS, "compiler rewrote tile data")
                (self.qa / supervisor.COMPILE_REQUEST).unlink()
            return 0
        self.assertEqual(self.run(fake),0)
        self.assertEqual(len(calls),2)
        self.assertEqual((self.qa/supervisor.TILESETS).read_bytes(),
                         (self.qa/supervisor.PRISTINE).read_bytes())

    def test_03_runtime_verified_repair_restarts_same_copy_once(self):
        calls=[]
        def fake(exe,cwd):
            calls.append((exe,cwd))
            if len(calls)==1:
                self.write(supervisor.TILESETS, "rewritten on title boot")
                self.write(supervisor.TILESETS,
                           (self.qa/supervisor.PRISTINE).read_bytes())
                self.write(supervisor.REQUEST,
                           "012345abcdef\n"+self.hashes[supervisor.TILESETS]+"\n")
            return 0
        self.assertEqual(self.run(fake),0)
        self.assertEqual(calls,[(self.qa/"Game.exe",self.qa)]*2)

    def test_04_wrong_marker_cannot_request_restart(self):
        def fake(exe,cwd):
            self.write(supervisor.REQUEST,"forged restart")
            return 0
        with self.assertRaisesRegex(ValueError,"UNVERIFIED_RESTART_REQUEST"):
            self.run(fake)

    def test_05_no_restart_loop_allowed(self):
        calls=[]
        def fake(exe,cwd):
            calls.append(1)
            self.write(supervisor.REQUEST,
                       "012345abcdef\n"+self.hashes[supervisor.TILESETS]+"\n")
            return 0
        with self.assertRaisesRegex(ValueError,"ONE_RESTART_LIMIT"):
            self.run(fake)
        self.assertEqual(len(calls),2)

    def test_06_adulterated_pristine_cannot_restore(self):
        self.write(supervisor.TILESETS,"modified")
        self.write(supervisor.PRISTINE,"forged")
        calls=[]
        with self.assertRaisesRegex(ValueError,"PRISTINE_FILE_TAMPERED"):
            self.run(lambda *_:calls.append(1) or 0)
        self.assertEqual(calls,[])

    def test_07_map_tampering_blocks_before_execution(self):
        self.write("Data/Map442.rxdata","forged")
        calls=[]
        with self.assertRaisesRegex(ValueError,"MAP_OR_INDEX_SHA256_MISMATCH"):
            self.run(lambda *_:calls.append(1) or 0)
        self.assertEqual(calls,[])

    def test_08_foreign_qa_path_not_authorized(self):
        foreign=self.project/"game-sinnoh-experimental-012345abcdef"
        foreign.mkdir()
        with self.assertRaisesRegex(ValueError,"NOT_EXACT_PRIVATE_QA_DIRECTORY"):
            supervisor.supervise(self.project,foreign,lambda *_:0)

    def test_09_original_save_namespace_not_modified(self):
        self.manifest["save_profile"]["dataPathApp"]="OTHER"
        self.write("sinnoh-experimental-qa.json",json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError,"INVALID_PRIVATE_SAVE_NAMESPACE"):
            self.run(lambda *_:0)

    def test_10_stale_marker_blocks_before_execution(self):
        self.write(supervisor.REQUEST,"untrusted")
        with self.assertRaisesRegex(ValueError,"UNEXPECTED_SUPERVISOR_MARKER"):
            self.run(lambda *_:0)

    def test_11_compiler_request_remaining_blocks_secondary_boot(self):
        self.write(supervisor.COMPILE_REQUEST,"synthetic pending")
        calls=[]
        with self.assertRaisesRegex(ValueError,"NATIVE_COMPILER_REQUEST_STILL_PENDING"):
            self.run(lambda *_:calls.append(1) or 0)
        self.assertEqual(len(calls),1)


if __name__ == "__main__":
    unittest.main()
