"""B10: fail-closed Windows Sandbox config and B09 clone provenance tests."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"scripts/regions"),str(ROOT/"tests")]
import prepare_sinnoh_b10_save_isolation as b10
import build_sinnoh_b09_native_qa as b09
from audit_sinnoh_b05_mapid_planning import expand
from test_sinnoh_b09_native_qa import B09Tests

class B10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=b10.load(b10.CONTRACT)
        cls.c09=b10.load(b10.B09)
        cls.c08=b10.load(b10.B08)
        cls.c07=b10.load(b10.B07)
        cls.c06=b10.load(b10.B06)
        cls.b00=b10.load(b10.B00)
        cls.b01=b10.load(b10.B01)
        cls.b04=b10.load(b10.B04)
        cls.b05=b10.load(b10.B05)

    def fixture(self):
        helper=B09Tests("test_01_b09_metadata_safe")
        self.addCleanup(helper.doCleanups)
        project,game,files,infos,tiles,dry,rows,report=helper.fixture()
        occupied=expand(self.b05["occupied"]["ranges"],limit=999)
        for map_id in sorted(occupied-{1}):
            (game/"Data"/f"Map{map_id:03d}.rxdata").write_bytes(
                b"synthetic-native-map-"+str(map_id).encode())
        native,_=b09.scan_native_game(project,game)
        plan=b09.plan_clone(native,files,dry["plan_sha256"])
        result=b09.clone_private(project,game,files,plan,plan["plan_sha256"])
        modified=copy.deepcopy(self.b01)
        modified["mapinfos_sha256"]=b10.sha(infos)
        modified["tilesets_sha256"]=b10.sha(tiles)
        return project,game,files,dry,plan,result,modified

    def audit_fixture(self):
        project,game,files,dry,plan,result,native_b01=self.fixture()
        folder=project/result["relative_path"]
        proof=b10.audit_clone(project,folder,plan["plan_sha256"],
                              self.c,self.c09,native_b01,self.b05)
        return project,game,files,dry,plan,result,native_b01,proof

    def test_01_metadata_preflight_with_unapproved_B09(self):
        terrain=b10.check_contract(self.c,self.c09,self.c08,self.c07,
                                   self.c06,self.b00,self.b01,self.b04,self.b05)
        self.assertEqual(len(terrain),54)
        self.assertEqual(self.c["expected_clone_maps"],702)
        self.assertFalse(self.c["host_saves_runtime_isolation_tested"])

    def test_02_cli_is_readonly_with_no_args(self):
        import subprocess
        proc=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/prepare_sinnoh_b10_save_isolation.py")],
            capture_output=True,text=True,cwd=ROOT)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn("B10_READY_AWAITING_B09_CLONE",proc.stdout)
        self.assertFalse(self.c["guest_game_tested"])

    def test_03_WSB_has_only_two_read_only_mappings(self):
        xml=ET.fromstring(b10.xml_wsb(r"C:\Private\Clone",r"C:\Private\Tools"))
        folders=xml.findall("./MappedFolders/MappedFolder")
        self.assertEqual(len(folders),2)
        self.assertEqual([f.findtext("ReadOnly") for f in folders],["true","true"])
        self.assertEqual([f.findtext("SandboxFolder") for f in folders],
                         [b10.GUEST_SOURCE,b10.GUEST_TOOLS])
        self.assertEqual([f.findtext("HostFolder") for f in folders],
                         [r"C:\Private\Clone",r"C:\Private\Tools"])

    def test_04_WSB_blocks_network_clipboard_and_autostart(self):
        xml=ET.fromstring(b10.xml_wsb(r"C:\A",r"C:\B"))
        for tag in ("vGPU","Networking","AudioInput","VideoInput",
                    "PrinterRedirection","ClipboardRedirection"):
            self.assertEqual(xml.findtext(tag),"Disable",tag)
        self.assertEqual(xml.findtext("ProtectedClient"),"Enable")
        self.assertIsNone(xml.find("LogonCommand"))

    def test_05_WSB_xml_escapes_windows_special_characters(self):
        xml=ET.fromstring(b10.xml_wsb(r"C:\QA & Maps\Clone",r"C:\Helpers > QA"))
        self.assertEqual(xml.findtext("./MappedFolders/MappedFolder/HostFolder"),
                         r"C:\QA & Maps\Clone")

    def test_06_non_windows_sandbox_is_rejected(self):
        with patch.object(b10.platform,"system",return_value="Linux"):
            out=b10.probe_windows_sandbox()
        self.assertFalse(out["supported"])
        self.assertEqual(out["reason"],"NOT_WINDOWS")

    def test_07_windows_home_is_rejected(self):
        class Key:
            def __enter__(self):return self
            def __exit__(self,*args):pass
        fake=types.SimpleNamespace(
            HKEY_LOCAL_MACHINE=214,
            OpenKey=lambda a,b:Key(),
            QueryValueEx=lambda k,v:("CoreSingleLanguage",1))
        with patch.object(b10.platform,"system",return_value="Windows"):
            with patch.dict(sys.modules,{"winreg":fake}):
                result=b10.probe_windows_sandbox()
        self.assertFalse(result["supported"])
        self.assertEqual(result["reason"],"WINDOWS_EDITION_UNSUPPORTED")

    def test_08_supported_windows_with_feature_disabled_is_rejected(self):
        class Key:
            def __enter__(self):return self
            def __exit__(self,*args):pass
        fake=types.SimpleNamespace(HKEY_LOCAL_MACHINE=214,OpenKey=lambda *a:Key(),
            QueryValueEx=lambda *a:("Professional",1))
        p=types.SimpleNamespace(returncode=0,stdout="Disabled\n")
        with patch.object(b10.platform,"system",return_value="Windows"):
            with patch.dict(sys.modules,{"winreg":fake}):
                with patch.object(b10.subprocess,"run",return_value=p):
                    result=b10.probe_windows_sandbox()
        self.assertFalse(result["supported"])
        self.assertEqual(result["reason"],"SANDBOX_FEATURE_NOT_ENABLED")

    def test_09_supported_windows_enabled_feature_is_detected(self):
        class Key:
            def __enter__(self):return self
            def __exit__(self,*args):pass
        fake=types.SimpleNamespace(HKEY_LOCAL_MACHINE=214,OpenKey=lambda *a:Key(),
            QueryValueEx=lambda *a:("Professional",1))
        p=types.SimpleNamespace(returncode=0,stdout="Enabled\n")
        with patch.object(b10.platform,"system",return_value="Windows"):
            with patch.dict(sys.modules,{"winreg":fake}):
                with patch.object(b10.subprocess,"run",return_value=p):
                    result=b10.probe_windows_sandbox()
        self.assertTrue(result["supported"])
        self.assertTrue(result["feature_enabled"])

    def test_10_safe_relative_filename_denies_traversal_ads(self):
        for bad in ("../Saves/Save01.rxdata",r"X:\users\save",
                    "Data/../../Foo","Data/Map442.rxdata:secret",
                    "Data/CON.txt","Data/Map442.rxdata.",
                    "\\\\server\\share\\evil","Graphics/Sinnoh "):
            with self.subTest(name=bad),self.assertRaisesRegex(ValueError,"SINNOH_B10_BLOCKED"):
                b10.safe_rel(bad)

    def test_11_clone_full_648_plus_54_map_ids_audited(self):
        *_,proof=self.audit_fixture()
        self.assertEqual(proof["native_map_ids_confirmed"],648)
        self.assertEqual(proof["sinnoh_map_ids_confirmed"],54)
        self.assertEqual(proof["clone_total_map_ids"],702)

    def test_12_clone_cannot_contain_saves(self):
        project,game,files,dry,plan,result,native_b01,proof=self.audit_fixture()
        clone=project/result["relative_path"]
        (clone/"Save01.rxdata").write_bytes(b"private data")
        with self.assertRaisesRegex(ValueError,"SINNOH_B10_BLOCKED"):
            b10.audit_clone(project,clone,plan["plan_sha256"],
                            self.c,self.c09,native_b01,self.b05)

    def test_13_tampered_terrain_map_blocks(self):
        project,game,files,dry,plan,result,native_b01,proof=self.audit_fixture()
        clone=project/result["relative_path"]
        (clone/"Data/Map442.rxdata").write_bytes(b"corrupt")
        with self.assertRaisesRegex(ValueError,"SINNOH_B10_BLOCKED"):
            b10.audit_clone(project,clone,plan["plan_sha256"],
                            self.c,self.c09,native_b01,self.b05)

    def test_14_fake_playability_in_B09_manifest_blocks(self):
        project,game,files,dry,plan,result,native_b01,proof=self.audit_fixture()
        clone=project/result["relative_path"]
        mfile=clone/"B09_PRIVATE_QA_MANIFEST.json"
        m=json.loads(mfile.read_text("utf-8"))
        m["save_isolation_verified"]=True
        mfile.write_text(json.dumps(m),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"SINNOH_B10_BLOCKED"):
            b10.audit_clone(project,clone,plan["plan_sha256"],
                            self.c,self.c09,native_b01,self.b05)

    def test_15_clone_missing_native_map_blocks(self):
        project,game,files,dry,plan,result,native_b01,proof=self.audit_fixture()
        clone=project/result["relative_path"]
        (clone/"Data/Map002.rxdata").unlink(missing_ok=True)
        # Map002 is not occupied; remove an occupied ID instead.
        (clone/"Data/Map076.rxdata").unlink()
        with self.assertRaisesRegex(ValueError,"SINNOH_B10_BLOCKED"):
            b10.audit_clone(project,clone,plan["plan_sha256"],
                            self.c,self.c09,native_b01,self.b05)

    def test_16_prepare_requires_supported_sandbox(self):
        project,game,files,dry,plan,result,native_b01,proof=self.audit_fixture()
        clone=project/result["relative_path"]
        with self.assertRaisesRegex(ValueError,"SINNOH_B10_BLOCKED"):
            b10.prepare_session(project,clone,plan["plan_sha256"],proof,
                {"supported":False,"feature_enabled":False})
        self.assertFalse((project/".blue-work/sinnoh-b10-sandbox").exists())

    def test_17_session_writes_only_private_WSB_and_guest_CMD(self):
        project,game,files,dry,plan,result,native_b01,proof=self.audit_fixture()
        clone=project/result["relative_path"]
        before=b10.sha((game/"Game.exe").read_bytes())
        out=b10.prepare_session(project,clone,plan["plan_sha256"],proof,
                                {"supported":True,"feature_enabled":True})
        self.assertFalse(out["sandbox_session_started"])
        self.assertFalse(out["game_exe_started"])
        cfg=project/out["config_relative_path"]
        self.assertEqual(cfg.suffix.lower(),".wsb")
        xml=ET.fromstring(cfg.read_text("utf-8"))
        mapped=xml.findall("./MappedFolders/MappedFolder")
        self.assertEqual(mapped[0].findtext("HostFolder"),str(clone))
        for m in mapped:
            self.assertEqual(m.findtext("ReadOnly"),"true")
        self.assertFalse((clone/"B10_ISOLAMENTO.wsb").exists())
        self.assertEqual(b10.sha((game/"Game.exe").read_bytes()),before)

    def test_18_duplicate_session_not_overwritten(self):
        project,game,files,dry,plan,result,native_b01,proof=self.audit_fixture()
        clone=project/result["relative_path"]
        host={"supported":True,"feature_enabled":True}
        b10.prepare_session(project,clone,plan["plan_sha256"],proof,host)
        with self.assertRaisesRegex(ValueError,"SINNOH_B10_BLOCKED"):
            b10.prepare_session(project,clone,plan["plan_sha256"],proof,host)

    def test_19_guest_CMD_never_auto_runs_Game_EXE(self):
        s=b10.GUEST_CMD
        self.assertIn("robocopy",s)
        self.assertIn("C:\\SinnohB10Game",s)
        self.assertIn("if errorlevel 8 goto :failed",s)
        self.assertNotIn("start Game.exe",s)
        self.assertNotIn("call Game.exe",s)

    def test_20_unsupported_rights_or_progress_forgery_rejected(self):
        for field in ("host_saves_runtime_isolation_tested",
                      "guest_game_tested","asset_rights_verified",
                      "future_regional_reservations_verified","r07_complete",
                      "r08_complete","r09_complete"):
            with self.subTest(field=field):
                c=copy.deepcopy(self.c);c[field]=True
                with self.assertRaisesRegex(ValueError,"SINNOH_B10_BLOCKED"):
                    b10.check_contract(c,self.c09,self.c08,self.c07,self.c06,
                        self.b00,self.b01,self.b04,self.b05)

if __name__=="__main__":unittest.main()
