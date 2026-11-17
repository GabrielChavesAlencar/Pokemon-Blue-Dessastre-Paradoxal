"""S08 offline-only Sinnoh resources: maps, graphics, plugin deps and SHA."""
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))

import audit_sinnoh_s08_resources as s08
from install_sinnoh_qa_copy import verify
from sinnoh_s12_installer import execute
from stage import serialize
from server.ruby_marshal import RubyObject
from test_sinnoh_qa_install import fixture, PROFILE
from test_sinnoh_rxdata_audit import fixture_files


class S08IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="sinnoh-s08-")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.game, self.overlay, spec = fixture(self.root)
        self.spec = self.root / ".blue-work/sinnoh-qa-spec.json"
        self.spec.write_text(json.dumps(spec, ensure_ascii=False), encoding="utf-8")
        self.qa = self.root / ".blue-work" / ("game-sinnoh-qa-" + PROFILE)

    def hashes(self):
        return {f.relative_to(self.game).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
                for f in self.game.rglob("*") if f.is_file()}

    def audit(self, **kw):
        return s08.private_overlay_audit(
            self.root, kw.get("overlay", self.overlay),
            kw.get("spec", self.spec), token=PROFILE, qa=kw.get("qa"))

    def test_01_audits_all_nine_maps_scripts_graphics_and_dependencies_read_only(self):
        before = self.hashes()
        result = self.audit()
        self.assertEqual(result["status"], "STATIC_INTEGRITY_VERIFIED_NOT_NATIVE_GAMEPLAY")
        self.assertEqual(result["map_count"], 9)
        self.assertEqual(result["event_count"], 24)
        self.assertEqual(result["warps"], 16)
        self.assertTrue(result["plugin_dependencies_verified"])
        self.assertEqual(result["missing_graphics"], [])
        self.assertEqual(result["launcher_required_files"], sorted(s08.QA_LAUNCH_REQUIRED))
        self.assertGreater(result["overlay_file_count"], 9)
        self.assertFalse(result["native_gameplay_verified"])
        self.assertFalse(result["source_rights_verified"])
        self.assertFalse(result["import_allowed"])
        self.assertFalse(result["writes_to_main_game"])
        self.assertFalse(self.qa.exists())
        self.assertEqual(self.hashes(), before)

    def test_02_pinned_overlay_file_hashes_are_verified(self):
        original = self.audit()
        self.assertEqual(len(original["overlay_file_sha256"]),
                         original["overlay_file_count"])
        self.assertTrue(all(len(h) == 64 for h in original["overlay_file_sha256"].values()))

    def test_03_tampered_map_is_blocked_without_modifying_main(self):
        map_name = next(self.overlay.glob("Data/Map[0-9][0-9][0-9].rxdata"))
        map_name.write_bytes(map_name.read_bytes() + b"tampered")
        before = self.hashes()
        with self.assertRaisesRegex(ValueError, "adulterado"):
            self.audit()
        self.assertEqual(before, self.hashes())

    def test_04_missing_script_or_pbs_dependency_is_blocked(self):
        for rel in ("Plugins/ZZZZZ Blue Sinnoh Intro/meta.txt",
                    "PBS/trainers_sinnoh_barry.txt"):
            target = self.overlay / rel
            raw = target.read_bytes()
            target.unlink()
            with self.assertRaises(ValueError):
                self.audit()
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

    def test_05_plugin_name_and_required_dependency_must_match(self):
        _,output,basehashes = s08.prepare(self.game,self.overlay,
                    json.loads(self.spec.read_text("utf-8")),token=PROFILE,project=self.root)
        verified = s08.plugin_dependencies(output,self.game,basehashes)
        self.assertTrue(verified["plugin_dependencies_verified"])
        for rel in (s08.INTRO_META,s08.START_META,s08.PROBE_META):
            forged = dict(output)
            forged[rel] = forged[rel].replace(b"Requires = ", b"Needs = ")
            with self.assertRaisesRegex(ValueError, "dependencia"):
                s08.plugin_dependencies(forged,self.game,basehashes)

    def test_06_missing_base_plugin_is_rejected(self):
        target=self.game / s08.DEPENDENCY
        target.unlink()
        with self.assertRaises(ValueError):
            self.audit()

    def test_07_unresolved_tileset_image_is_blocked(self):
        blob=serialize([None,RubyObject("RPG::Tileset",
                        {"@tileset_name":b"MissingSinnoh"})])
        with self.assertRaisesRegex(ValueError,"graficos citados"):
            s08.graphic_inventory(blob, {}, self.game, {})
        png = bytes.fromhex(
            "89504e470d0a1a0a0000000d494844520000000100000001"
            "08060000001f15c4890000000049454e44ae426082")
        images={"Graphics/Tilesets/MissingSinnoh.png": png}
        good=s08.graphic_inventory(blob,images,self.game,{})
        self.assertEqual(good["referenced_graphics_count"],1)
        with self.assertRaisesRegex(ValueError,"PNG referenciado invalido"):
            s08.graphic_inventory(
                blob,{"Graphics/Tilesets/MissingSinnoh.png": b"invalid PNG"},
                self.game,{})

    def test_08_rejects_graphic_name_path_traversal(self):
        blob=serialize([None,RubyObject("RPG::Tileset",
                        {"@tileset_name":b"../game"})])
        with self.assertRaisesRegex(ValueError,"inseguro"):
            s08.graphic_inventory(blob,{},self.game,{})

    def test_09_missing_native_qa_premature_approval_never_passes(self):
        result=self.audit()
        for field in ("runtime_playable","native_qa_approved","import_allowed"):
            forged=dict(result)
            forged[field]=True
            with self.assertRaisesRegex(ValueError,"prova falsa"):
                s08.no_gameplay(forged)

    def test_10_integrated_qa_can_only_be_checked_after_private_install(self):
        self.assertFalse(self.qa.exists())
        with self.assertRaises(ValueError):
            self.audit(qa=self.qa)
        execute(self.root,overlay=self.overlay,spec=self.spec,
                do_install=True,token=PROFILE)
        status=verify(self.qa,project=self.root)
        self.assertFalse(status["playable_approved"])
        data=self.audit(qa=self.qa)
        self.assertTrue(data["qa_inspected"])
        self.assertFalse(data["native_gameplay_verified"])

    def test_11_source_rxdata_missing_graphics_maps_and_warps_are_blockers(self):
        donor = self.root / "donor"
        for rel,raw in fixture_files(include_graphics=True).items():
            target=donor/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw)
        result=s08.source_audit(donor)
        self.assertEqual(result["status"],"BLOCKED_SOURCE_INTEGRITY")
        self.assertIn("missing_map_files", result["findings"])
        self.assertIn("missing_graphics", result["findings"])
        self.assertIn("broken_static_transfers", result["findings"])
        self.assertFalse(result["rights_verified"])
        self.assertFalse(result["pilot_verified"])
        self.assertFalse(result["import_allowed"])
        self.assertEqual(result["script_commands_not_executed"],1)

    def test_12_source_assets_are_read_only(self):
        donor=self.root/"donor"
        for rel,raw in fixture_files(include_graphics=True).items():
            file=donor/rel
            file.parent.mkdir(parents=True,exist_ok=True)
            file.write_bytes(raw)
        before={p.relative_to(donor).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                for p in donor.rglob("*") if p.is_file()}
        s08.source_audit(donor)
        after={p.relative_to(donor).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
               for p in donor.rglob("*") if p.is_file()}
        self.assertEqual(before,after)

    def test_13_cli_incomplete_input_fails_closed(self):
        stream=io.StringIO()
        with contextlib.redirect_stderr(stream):
            with patch.object(sys,"argv",["s08","--overlay",str(self.overlay),
                              "--project",str(self.root)]):
                self.assertEqual(s08.main(),2)
        self.assertIn("SINNOH_S08_BLOQUEADO",stream.getvalue())

    def test_14_cli_private_overlay_prints_nonplayable_report(self):
        stream=io.StringIO()
        with contextlib.redirect_stdout(stream):
            with patch.object(sys,"argv",["s08","--overlay",str(self.overlay),
                 "--spec",str(self.spec),"--project",str(self.root)]):
                self.assertEqual(s08.main(),0)
        result=json.loads(stream.getvalue())
        self.assertEqual(result["mode"],"READ_ONLY_QA_RESOURCES")
        self.assertFalse(result["native_qa_approved"])

    def test_15_s12_reports_integrity_but_never_gameplay(self):
        before=self.hashes()
        plan=execute(self.root,overlay=self.overlay,spec=self.spec,
                     do_install=False,token=PROFILE)
        self.assertFalse(plan["created"])
        self.assertFalse(plan["native_gameplay_verified"])
        self.assertEqual(before,self.hashes())

    def test_16_no_cross_region_qa_or_symlink(self):
        fake=self.root/"game"
        with self.assertRaises(ValueError):
            self.audit(overlay=fake)
        link=self.root/".blue-work/unsafe-link"
        try:
            link.symlink_to(self.overlay,target_is_directory=True)
        except (NotImplementedError,OSError):
            self.skipTest("Symlinks indisponiveis")
        with self.assertRaises(ValueError):
            self.audit(overlay=link)


if __name__=="__main__":
    unittest.main()
