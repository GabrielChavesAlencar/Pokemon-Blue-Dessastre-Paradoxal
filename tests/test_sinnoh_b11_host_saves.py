"""B11 synthetic host-save before/after fingerprints and VM-only diagnostic."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"scripts/regions"),str(ROOT/"tests")]
import audit_sinnoh_b11_host_saves as b11
import prepare_sinnoh_b10_save_isolation as b10
from test_sinnoh_b10_save_isolation import B10Tests

class B11Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=b11.load(b11.CONTRACT)
        cls.c10=b11.load(b10.CONTRACT)
        cls.c09=b11.load(b11.b09.CONTRACT)

    def fixture(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        project=Path(tmp.name)/"project"
        project.mkdir()
        root=Path(tmp.name)/"user_save_dir"
        root.mkdir()
        (root/"Save01.rxdata").write_bytes(b"synthetic save 1")
        return project,root

    def prepare(self,project,root):
        with patch.object(b11,"b10_session",return_value=None):
            return b11.prepare_before(project,"a"*64,[root])

    def test_01_contract_metadata_no_false_approval(self):
        b11.check_contract(self.c,self.c10,self.c09)
        self.assertFalse(self.c["game_exe_tested"])
        self.assertFalse(self.c["host_saves_unchanged_after_native_test_confirmed"])

    def test_02_no_arg_preflight_readonly(self):
        result=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_sinnoh_b11_host_saves.py")],
            cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn("B11_CODE_READY_NO_WINDOWS_EVIDENCE",result.stdout)

    def test_03_default_scopes_only_project_named_locations(self):
        scopes=b11.default_scopes({"APPDATA":r"C:\Users\tester\AppData\Roaming",
            "LOCALAPPDATA":r"C:\Users\tester\AppData\Local",
            "USERPROFILE":r"C:\Users\tester"})
        self.assertEqual(len(scopes),4)
        self.assertTrue(all(x.name=="PokemonBlueDessastreParadoxal" for x in scopes))

    def test_04_snapshot_and_after_unchanged(self):
        project,root=self.fixture()
        before=self.prepare(project,root)
        after=b11.inspect_after(project,before["watch_id"],"not_run")
        self.assertTrue(after["watch_unchanged"])
        self.assertEqual(after["files_added"],0)
        self.assertEqual(after["files_removed"],0)
        self.assertEqual(after["files_changed"],0)
        self.assertFalse(after["host_saves_globally_isolated_proven"])
        self.assertFalse(after["guest_vm_execution_independently_verified"])

    def test_05_modified_host_save_is_detected(self):
        project,root=self.fixture()
        snap=self.prepare(project,root)
        (root/"Save01.rxdata").write_bytes(b"modified synthetic save")
        result=b11.inspect_after(project,snap["watch_id"],"save_inside_vm")
        self.assertEqual(result["files_changed"],1)
        self.assertEqual(result["status"],"HOST_WATCHED_FILES_CHANGED_REVIEW_REQUIRED")
        self.assertFalse(result["host_saves_globally_isolated_proven"])

    def test_06_new_and_deleted_host_save_are_detected(self):
        project,root=self.fixture()
        snap=self.prepare(project,root)
        (root/"Save01.rxdata").unlink()
        (root/"Save02.rxdata").write_bytes(b"test newly added")
        result=b11.inspect_after(project,snap["watch_id"],"rendered_map")
        self.assertEqual(result["files_removed"],1)
        self.assertEqual(result["files_added"],1)
        self.assertFalse(result["watch_unchanged"])

    def test_07_shared_summary_contains_no_personal_paths_or_save_bytes(self):
        project,root=self.fixture()
        before=self.prepare(project,root)
        after=b11.inspect_after(project,before["watch_id"],"launch_failed")
        printed=json.dumps({"before":before,"after":after})
        self.assertNotIn(str(root),printed)
        self.assertNotIn("Save01.rxdata",printed)
        self.assertNotIn("synthetic save 1",printed)
        self.assertFalse(before["paths_names_and_saves_in_report"])
        self.assertFalse(after["paths_names_and_saves_in_report"])

    def test_08_private_baseline_contains_only_hmac_ids_not_filenames(self):
        project,root=self.fixture()
        before=self.prepare(project,root)
        snapshot=project/".blue-work/sinnoh-b11-save-audit"/(
            "watch-"+before["watch_id"])/"private-baseline.json"
        data=json.loads(snapshot.read_text("utf-8"))
        self.assertEqual(len(data["baseline"]),1)
        self.assertEqual(len(next(iter(data["baseline"]))),64)
        self.assertNotIn("Save01.rxdata",json.dumps(data["baseline"]))

    def test_09_modified_baseline_cannot_be_trusted(self):
        project,root=self.fixture()
        before=self.prepare(project,root)
        path=project/".blue-work/sinnoh-b11-save-audit"/(
            "watch-"+before["watch_id"])/"private-baseline.json"
        obj=json.loads(path.read_text("utf-8"))
        obj["baseline"]={}
        path.write_text(json.dumps(obj),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"SINNOH_B11_BLOCKED"):
            b11.inspect_after(project,before["watch_id"],"not_run")

    def test_10_after_invalid_identifier_is_rejected(self):
        project,root=self.fixture()
        with self.assertRaisesRegex(ValueError,"SINNOH_B11_BLOCKED"):
            b11.inspect_after(project,"../../my-saves","not_run")

    def test_11_symlink_in_save_scope_is_rejected(self):
        project,root=self.fixture()
        target=root/"Save01.rxdata"
        alias=root/"shadow-save.rxdata"
        try:
            alias.symlink_to(target)
        except (OSError,NotImplementedError):
            self.skipTest("symlink not available on this filesystem")
        with patch.object(b11,"b10_session",return_value=None):
            with self.assertRaisesRegex(ValueError,"SINNOH_B11_BLOCKED"):
                b11.prepare_before(project,"a"*64,[root])

    def test_12_overlapping_save_scopes_are_rejected(self):
        project,root=self.fixture()
        sub=root/"other";sub.mkdir()
        with self.assertRaisesRegex(ValueError,"SINNOH_B11_BLOCKED"):
            b11.checked_roots([root,sub])

    def test_13_guest_observation_cannot_approve_gameplay(self):
        project,root=self.fixture()
        before=self.prepare(project,root)
        for kind in ("not_run","launched","rendered_map","save_inside_vm"):
            result=b11.inspect_after(project,before["watch_id"],kind)
            self.assertFalse(result["gameplay_approved"])
            self.assertFalse(result["R07_R08_R09_approved"])
            self.assertEqual(result["phase_b_approved"],0)

    def test_14_guest_status_is_restricted(self):
        project,root=self.fixture()
        before=self.prepare(project,root)
        with self.assertRaisesRegex(ValueError,"SINNOH_B11_BLOCKED"):
            b11.inspect_after(project,before["watch_id"],"officially_approved")

    def test_15_wsb_maps_exactly_two_readonly_folders_and_no_autoexec(self):
        project,root=self.fixture()
        before=self.prepare(project,root)
        wsb=project/before["config_relative_path"]
        tree=ET.fromstring(wsb.read_text("utf-8"))
        maps=tree.findall("./MappedFolders/MappedFolder")
        self.assertEqual(len(maps),2)
        self.assertTrue(all(m.findtext("ReadOnly")=="true" for m in maps))
        self.assertEqual(tree.findtext("Networking"),"Disable")
        self.assertEqual(tree.findtext("ClipboardRedirection"),"Disable")
        self.assertIsNone(tree.find("LogonCommand"))

    def test_16_guest_diagnostic_does_not_auto_launch_exe(self):
        self.assertIn("Map442.rxdata",b11.GUEST_DIAG)
        self.assertIn("Map495.rxdata",b11.GUEST_DIAG)
        self.assertNotIn("start Game.exe",b11.GUEST_DIAG)
        self.assertNotIn("call Game.exe",b11.GUEST_DIAG)

    def test_17_source_b10_session_integrity(self):
        helper=B10Tests("test_01_metadata_preflight_with_unapproved_B09")
        self.addCleanup(helper.doCleanups)
        project,game,files,dry,plan,result,base_b01,proof=helper.audit_fixture()
        clone=project/result["relative_path"]
        b10.prepare_session(project,clone,plan["plan_sha256"],proof,
                           {"supported":True,"feature_enabled":True})
        folder=b11.b10_session(project,plan["plan_sha256"])
        self.assertTrue((folder/"B10_ISOLAMENTO.wsb").exists())

    def test_18_tampered_b10_config_blocks_snapshots(self):
        helper=B10Tests("test_01_metadata_preflight_with_unapproved_B09")
        self.addCleanup(helper.doCleanups)
        project,game,files,dry,plan,result,base_b01,proof=helper.audit_fixture()
        clone=project/result["relative_path"]
        b10.prepare_session(project,clone,plan["plan_sha256"],proof,
                           {"supported":True,"feature_enabled":True})
        path=b10.session_root(project)/(
            f"session-{plan['plan_sha256'][:16]}")/"B10_ISOLAMENTO.wsb"
        path.write_text("<Configuration><Networking>Enable</Networking></Configuration>")
        with self.assertRaisesRegex(ValueError,"SINNOH_B11_BLOCKED"):
            b11.b10_session(project,plan["plan_sha256"])

    def test_19_false_approval_flags_in_contract_blocked(self):
        for field in ("sandbox_runtime_save_path_verified",
                      "host_saves_unchanged_after_native_test_confirmed",
                      "game_exe_tested",
                      "rendering_50000_70000_tilesets_verified",
                      "r07_complete","r08_complete","r09_complete"):
            c=copy.deepcopy(self.c);c[field]=True
            with self.subTest(field=field),self.assertRaisesRegex(
                    ValueError,"SINNOH_B11_BLOCKED"):
                b11.check_contract(c,self.c10,self.c09)

if __name__=="__main__":unittest.main()
