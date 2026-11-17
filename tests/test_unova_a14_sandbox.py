"""A14 Windows Sandbox preflight tests. Never start native Game.exe."""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_a13_private_qa as a13
import audit_unova_a14_sandbox as a14

class A14Tests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="unova-a14-")
        self.addCleanup(t.cleanup)
        root=Path(t.name)
        self.local=root/"AppData"/"Local"
        self.local.mkdir(parents=True)
        self.game=root/"game"
        self.game.mkdir()
        data=self.game/"Data"
        data.mkdir()
        (self.game/"Game.exe").write_bytes(b"synthetic not executable")
        (self.game/"Game.ini").write_text("[Game]\nTitle=Pokemon Blue\n")
        (self.game/"mkxp.json").write_text(
            '{"windowTitle":"Pokemon","dataPathApp":"Decades","dataPathOrg":"Studio"}')
        for name in ("MapInfos.rxdata","Map001.rxdata","Scripts.rxdata","System.rxdata"):
            (data/name).write_bytes(name.encode())
        a04={"phase":"A04","sources":{"DECADES":{
            "mapinfos_sha256":a13.hash_file(data/"MapInfos.rxdata"),
            "maps":[{"id":1,"source_filename":"Map001.rxdata",
                     "sha256":a13.hash_file(data/"Map001.rxdata")}]}}}
        a12={"phase":"A12","status":"A12_SOURCE_REVIEW_DONE_ISOLATED_QA_NOT_CREATED",
             "mapinfos_sha256":a04["sources"]["DECADES"]["mapinfos_sha256"],
             "can_install":False,"can_reserve_mapids":False}
        self.a13=a13.clone(self.game,
            self.local/a14.ROOT_NAME/"qa-copies",a04,a12)
        self.qa=Path(self.a13["path"])
    def prepare(self):
        return a14.prepare(self.qa,self.a13,self.local)

    def test_01_wsb_written_without_running_game(self):
        r=self.prepare()
        self.assertEqual(r["status"],a14.STATUS)
        self.assertTrue(Path(r["wsb_configuration_path"]).is_file())
        self.assertFalse(r["sandbox_game_started"])
        self.assertFalse(r["host_game_started"])
        self.assertFalse(r["qa_runtime_save_path_verified"])
        self.assertFalse(r["gameplay_approved"])
    def test_02_windows_sandbox_config_disables_network_and_redirection(self):
        r=self.prepare()
        root=ET.parse(r["wsb_configuration_path"]).getroot()
        self.assertEqual(root.tag,"Configuration")
        for tag in ("Networking","VGpu","ClipboardRedirection",
                    "PrinterRedirection","AudioInput","VideoInput"):
            self.assertEqual(root.findtext(tag),"Disable")
    def test_03_only_reports_mapping_is_writable(self):
        r=self.prepare()
        root=ET.parse(r["wsb_configuration_path"]).getroot()
        m=root.find("MappedFolders").findall("MappedFolder")
        self.assertEqual(len(m),3)
        self.assertEqual([x.findtext("ReadOnly") for x in m],
                         ["true","true","false"])
        self.assertEqual(Path(m[0].findtext("HostFolder")),self.qa)
        self.assertEqual(m[0].findtext("SandboxFolder"),r"C:\UNOVA_A14_RO")
        self.assertTrue(m[2].findtext("HostFolder").endswith("reports"))
    def test_04_logon_command_targets_isolated_launcher_only(self):
        r=self.prepare()
        root=ET.parse(r["wsb_configuration_path"]).getroot()
        self.assertEqual(root.findtext("LogonCommand/Command"),
                         r"cmd.exe /c C:\UNOVA_A14_TOOLS\RUN_SANDBOX_QA.cmd")
        self.assertNotIn(str(self.game),root.findtext("LogonCommand/Command"))
    def test_05_batch_copies_inside_sandbox_then_requests_consent(self):
        r=self.prepare()
        cmd=Path(r["sandbox_script_path"]).read_text("utf-8")
        self.assertIn('robocopy "%QA_SRC%" "%QA_DST%"',cmd)
        self.assertIn('choice /C NS',cmd)
        self.assertIn('start "" /wait "%QA_DST%\\Game.exe"',cmd)
        self.assertNotIn(str(self.game),cmd)
        self.assertNotIn("powershell",cmd.lower())
    def test_06_runtime_result_not_forged_by_preflight(self):
        r=self.prepare()
        self.assertFalse(Path(r["runtime_log_expected"]).exists())
        self.assertIsNone(r["sandbox_binary_found_in_path"])
        self.assertEqual(r["sandbox_feature_enabled_and_usable"],"UNKNOWN_NOT_TESTED")
        self.assertEqual(r["bar_a_completed"],0)
    def test_07_reexecution_preserves_wsb_and_logs(self):
        first=self.prepare()
        report=Path(first["sandbox_reports_folder"])/"A14_SANDBOX_RUNTIME.txt"
        report.write_text("test only")
        second=self.prepare()
        self.assertEqual(first["wsb_configuration_path"],second["wsb_configuration_path"])
        self.assertEqual(report.read_text(),"test only")
    def test_08_tampered_wsb_rejected_without_overwrite(self):
        r=self.prepare()
        p=Path(r["wsb_configuration_path"])
        p.write_text("tampered")
        with self.assertRaises(ValueError):self.prepare()
        self.assertEqual(p.read_text(),"tampered")
    def test_09_tampered_launcher_rejected(self):
        r=self.prepare()
        p=Path(r["sandbox_script_path"])
        p.write_text("not our launcher")
        with self.assertRaises(ValueError):self.prepare()
    def test_10_original_game_and_clone_not_modified(self):
        before={p.relative_to(self.qa).as_posix():a13.hash_file(p)
                for p in self.qa.rglob("*") if p.is_file()}
        self.prepare()
        after={p.relative_to(self.qa).as_posix():a13.hash_file(p)
               for p in self.qa.rglob("*") if p.is_file()}
        self.assertEqual(before,after)
        self.assertEqual((self.game/"Game.exe").read_bytes(),b"synthetic not executable")
    def test_11_wrong_qa_parent_rejected(self):
        other=self.local/"other"
        other.mkdir()
        with self.assertRaises(ValueError):
            a14.prepare(other,self.a13,self.local)
    def test_12_forged_a13_status_rejected(self):
        self.a13["status"]="PLAYABLE"
        with self.assertRaises(ValueError):self.prepare()
    def test_13_forged_a13_path_rejected(self):
        self.a13["path"]=str(self.game)
        with self.assertRaises(ValueError):self.prepare()
    def test_14_tampered_game_exe_detected(self):
        (self.qa/"Game.exe").write_bytes(b"evil")
        with self.assertRaises(ValueError):self.prepare()
    def test_15_tampered_mapinfos_detected(self):
        (self.qa/"Data/MapInfos.rxdata").write_bytes(b"changed")
        with self.assertRaises(ValueError):self.prepare()
    def test_16_tampered_scripts_detected(self):
        (self.qa/"Data/Scripts.rxdata").write_bytes(b"changed")
        with self.assertRaises(ValueError):self.prepare()
    def test_17_missing_a13_evidence_rejected(self):
        (self.qa/a13.INVENTORY_FILE).unlink()
        with self.assertRaises(ValueError):self.prepare()
    def test_18_profile_mismatch_rejected(self):
        (self.qa/"mkxp.json").write_text('{"dataPathApp":"NormalGame"}')
        with self.assertRaises(ValueError):self.prepare()
    def test_19_custom_save_override_rejected(self):
        (self.qa/"mkxp.json").write_text(
            '{"custom":{"savePath":"C:/saves"}}')
        with self.assertRaises(ValueError):self.prepare()
    def test_20_missing_ini_rejected(self):
        (self.qa/"Game.ini").unlink()
        with self.assertRaises(ValueError):self.prepare()
    def test_21_save_file_in_clone_rejected(self):
        (self.qa/"Data/File1.rxdata").write_bytes(b"PRIVATE")
        with self.assertRaises(ValueError):self.prepare()
    def test_22_symlink_destination_rejected(self):
        r=self.prepare()
        f=Path(r["sandbox_script_path"])
        f.unlink()
        try:f.symlink_to(self.qa/"Game.ini")
        except OSError:self.skipTest("symlink not supported")
        with self.assertRaises(ValueError):self.prepare()
    def test_23_report_is_immutable(self):
        report=self.prepare()
        work=self.local/"reportproject"
        work.mkdir()
        path=a14.save(work,report)
        self.assertEqual(a14.save(work,report),path)
        self.assertEqual(json.loads(path.read_text()),report)
    def test_24_test_does_not_spawn_external_process(self):
        with patch.object(a14.shutil,"which",return_value=None):
            r=self.prepare()
        self.assertFalse(r["sandbox_game_started"])
        self.assertEqual(r["next_manual_step"],
                         "DOUBLE_CLICK_WSB_ONLY_IF_WINDOWS_SANDBOX_IS_SUPPORTED")
    def test_25_report_directory_is_private_scope(self):
        r=self.prepare()
        report=Path(r["sandbox_reports_folder"])
        self.assertTrue(report.is_relative_to(self.local/a14.ROOT_NAME))
        self.assertFalse(report.is_relative_to(self.qa))
        self.assertTrue(Path(r["wsb_configuration_path"]).is_relative_to(self.local/a14.ROOT_NAME))
    def test_26_a13_profile_flags_do_not_mark_native_save_test_passed(self):
        r=self.prepare()
        self.assertFalse(r["qa_runtime_save_path_verified"])
        self.assertFalse(r["gameplay_approved"])
        self.assertFalse(r["can_reserve_mapids"])
        self.assertFalse(r["unova_maps_installed"])
    def test_27_wsb_does_not_map_main_installed_game(self):
        r=self.prepare()
        xml=Path(r["wsb_configuration_path"]).read_text()
        self.assertNotIn(str(self.game),xml)
        self.assertIn(str(self.qa),xml)
    def test_28_large_or_invalid_evidence_fail_closed(self):
        (self.qa/a13.INVENTORY_FILE).write_bytes(b"x"*(a14.MAX_METADATA+1))
        with self.assertRaises(ValueError):self.prepare()

if __name__=="__main__":
    unittest.main()
