"""R07 synthetic-only diagnostic of installed and future regional MapIDs."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_r07_reservations as r07
from server.ruby_marshal import RubyObject
from stage import serialize


class SinnohR07ReservationsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="sinnoh-r07-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.work=self.root/".blue-work"
        self.work.mkdir()
        self.data=self.root/"game/Data"
        self.data.mkdir(parents=True)
        raw=serialize({1:RubyObject("RPG::MapInfo",{"@name":b"Decades"})})
        (self.data/"MapInfos.rxdata").write_bytes(raw)
        (self.data/"Map001.rxdata").write_bytes(b"NOT AN ACTUAL GAME MAP")
        self.sha=hashlib.sha256(raw).hexdigest()

    def manifest(self,region,ids):
        folder=self.work/"sinnoh-reservations"
        folder.mkdir(exist_ok=True)
        file=folder/(region.lower()+".json")
        file.write_text(json.dumps({
            "schema":1,"region":region,"kind":"LOCAL_FUTURE_MAP_ID_RESERVATIONS",
            "baseline_mapinfos_sha256":self.sha,
            "future_reserved_map_ids":ids,"ownership_evidence":"Local manifest reviewed",
            "reviewed_locally":True,"read_only":True
        }),encoding="utf-8")
        return file

    def all_manifests(self):
        self.manifest("KANTO",[200])
        self.manifest("JOHTO",[600,601])
        self.manifest("HOENN",[300])

    @staticmethod
    def plan(*values):
        return {"schema":1,"region":"SINNOH","mode":"REMAP_CANDIDATE_ONLY",
                "can_install":False,"may_stage_real_map_data":False,
                "mapping":{str(i+7):mid for i,mid in enumerate(values)}}

    def test_01_missing_manifests_and_plan_block_without_fabricating_evidence(self):
        report=r07.audit(self.root)
        self.assertEqual(report["status"],"BLOCKED_MISSING_NATIVE_RESERVATION_EVIDENCE")
        self.assertEqual(report["future_regions_with_evidence"],0)
        self.assertFalse(report["r07_complete"])
        self.assertFalse(report["r08_real_maps_imported"])
        self.assertFalse(report["r09_game_exe_joiplay_tested"])
        self.assertFalse(report["native_gameplay_verified"])
        self.assertFalse(report["may_apply_to_main_game"])

    def test_02_all_regions_and_noncolliding_candidate_still_need_native_signoff(self):
        self.all_manifests()
        report=r07.audit(self.root,plan=self.plan(500,501))
        self.assertEqual(report["status"],"CANDIDATE_READY_FOR_MANUAL_REVIEW_NOT_APPROVED")
        self.assertEqual(report["future_regions_with_evidence"],3)
        self.assertTrue(report["candidate_safety_reviewable"])
        self.assertEqual(report["blockers"],[])
        self.assertFalse(report["r07_complete"])
        self.assertFalse(report["rights_verified"])
        self.assertFalse(report["native_gameplay_verified"])
        self.assertFalse(report["game_or_saves_modified"])

    def test_03_candidate_conflicts_with_installed_decades(self):
        self.all_manifests()
        report=r07.audit(self.root,plan=self.plan(1))
        self.assertIn({"id":1,"reason":"OCCUPIED_IN_NATIVE_BASE"},report["collisions"])
        self.assertFalse(report["candidate_safety_reviewable"])

    def test_04_candidate_conflicts_with_planned_kanto_hoenn_ids(self):
        self.all_manifests()
        report=r07.audit(self.root,plan=self.plan(200,300))
        self.assertEqual(len(report["collisions"]),2)
        self.assertIn({"id":200,"reason":"FUTURE_RESERVED_KANTO"},report["collisions"])
        self.assertIn({"id":300,"reason":"FUTURE_RESERVED_HOENN"},report["collisions"])

    def test_05_future_reservations_from_two_regions_cannot_overlap(self):
        self.all_manifests()
        self.manifest("HOENN",[200,300])
        result=r07.audit(self.root,plan=self.plan(501))
        self.assertIn("reserva compartilhada em conflito: 200",result["blockers"])
        self.assertFalse(result["candidate_safety_reviewable"])

    def test_06_missing_native_game_data_does_not_approve(self):
        self.all_manifests()
        (self.data/"MapInfos.rxdata").unlink()
        (self.data/"Map001.rxdata").unlink()
        self.data.rmdir()
        result=r07.audit(self.root,plan=self.plan(500))
        self.assertFalse(result["native_snapshot_present"])
        self.assertIsNone(result["native_mapinfos_sha256"])
        self.assertFalse(result["candidate_safety_reviewable"])

    def test_07_invalid_baseline_sha_and_unknown_region_are_rejected(self):
        self.all_manifests()
        file=self.work/"sinnoh-reservations/kanto.json"
        obj=json.loads(file.read_text("utf-8"))
        obj["baseline_mapinfos_sha256"]="f"*64
        file.write_text(json.dumps(obj),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"baseline"):
            r07.audit(self.root,plan=self.plan(500))
        obj["baseline_mapinfos_sha256"]=self.sha
        obj["region"]="SINNOH"
        file.write_text(json.dumps(obj),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"baseline"):
            r07.audit(self.root,plan=self.plan(500))

    def test_08_unreviewed_and_unidentified_future_reservations_rejected(self):
        self.all_manifests()
        file=self.work/"sinnoh-reservations/johto.json"
        orig=json.loads(file.read_text("utf-8"))
        for bad in [
            {**orig,"reviewed_locally":False},
            {**orig,"ownership_evidence":""},
            {**orig,"future_reserved_map_ids":[500,500]},
            {**orig,"future_reserved_map_ids":[-1]},
            {**orig,"future_reserved_map_ids":["500"]},
            {**orig,"native_gameplay_verified":True}
        ]:
            file.write_text(json.dumps(bad),encoding="utf-8")
            with self.assertRaises(ValueError):
                r07.audit(self.root,plan=self.plan(501))

    def test_09_bad_plan_cannot_claim_install_or_use_johto_range(self):
        self.all_manifests()
        for candidate in [
            {**self.plan(500),"can_install":True},
            self.plan(600),
            self.plan(1000),
            self.plan(0),
            self.plan(500,500),
            {**self.plan(500),"region":"HOENN"},
            {**self.plan(500),"mapping":{"00":500}},
        ]:
            with self.assertRaises(ValueError):
                r07.audit(self.root,plan=candidate)

    def test_10_report_writes_only_diagnostics_and_keeps_main_hashes(self):
        self.all_manifests()
        before=hashlib.sha256((self.data/"MapInfos.rxdata").read_bytes()).hexdigest()
        report=r07.audit(self.root,plan=self.plan(501))
        path=r07.write_report(self.root,report)
        self.assertEqual(path,self.work/"sinnoh-diagnostics/r07-reservations.json")
        saved=json.loads(path.read_text("utf-8"))
        self.assertFalse(saved["r07_complete"])
        self.assertEqual(before,hashlib.sha256((self.data/"MapInfos.rxdata").read_bytes()).hexdigest())

    def test_11_report_refuses_false_signoff(self):
        result=r07.audit(self.root)
        result["r07_complete"]=True
        with self.assertRaisesRegex(ValueError,"adulterado"):
            r07.write_report(self.root,result)

    def test_12_symlink_manifest_and_game_path_rejected(self):
        self.all_manifests()
        kanto=self.work/"sinnoh-reservations/kanto.json"
        link=self.work/"sinnoh-reservations/temp.json"
        try:
            link.symlink_to(kanto)
        except (NotImplementedError,OSError):
            self.skipTest("symlink unavailable")
        kanto.unlink()
        kanto.symlink_to(link)
        with self.assertRaises(ValueError):
            r07.audit(self.root,plan=self.plan(500))

    def test_13_cli_missing_plan_is_blocked_but_can_write_diagnostics(self):
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            rc=r07.main(["--project",str(self.root),"--write"])
        self.assertEqual(rc,2)
        obj=json.loads(out.getvalue())
        self.assertFalse(obj["candidate_safety_reviewable"])
        self.assertTrue((self.work/"sinnoh-diagnostics/r07-reservations.json").is_file())

    def test_14_cli_valid_candidate_reports_only_review_ready(self):
        self.all_manifests()
        plan_path=self.work/"sinnoh-r07-candidate.json"
        plan_path.write_text(json.dumps(self.plan(501)),encoding="utf-8")
        out=io.StringIO()
        with contextlib.redirect_stdout(out):
            rc=r07.main(["--project",str(self.root),"--plan",str(plan_path)])
        self.assertEqual(rc,0)
        result=json.loads(out.getvalue())
        self.assertEqual(result["status"],"CANDIDATE_READY_FOR_MANUAL_REVIEW_NOT_APPROVED")
        self.assertFalse(result["r07_complete"])
        self.assertFalse((self.work/"sinnoh-diagnostics").exists())

    def test_15_cli_plan_outside_workspace_not_read(self):
        self.all_manifests()
        path=self.root/"untrusted.json"
        path.write_text(json.dumps(self.plan(501)),encoding="utf-8")
        err=io.StringIO()
        with contextlib.redirect_stderr(err):
            rc=r07.main(["--project",str(self.root),"--plan",str(path)])
        self.assertEqual(rc,2)
        self.assertIn("SINNOH_R07_BLOQUEADO",err.getvalue())

    def test_16_static_auditor_never_modifies_main_or_other_regions(self):
        bat=(ROOT/"SINNOH_DIAGNOSTICAR_PENDENCIAS.bat").read_text("utf-8")
        self.assertIn('cd /d "%~dp0"',bat)
        self.assertIn('audit_sinnoh_r07_reservations.py',bat)
        self.assertIn("--write",bat)
        self.assertNotIn("powershell",bat.lower())
        self.assertNotIn("start game.exe",bat.lower())
        self.assertNotIn("rmdir ",bat.lower())
        self.all_manifests()
        original={
            str(p.relative_to(self.root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in self.root.rglob("*") if p.is_file()
        }
        for _ in range(3):
            report=r07.audit(self.root,plan=self.plan(501))
            self.assertFalse(report["game_or_saves_modified"])
        after={
            str(p.relative_to(self.root)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in self.root.rglob("*") if p.is_file()
        }
        self.assertEqual(after,original)


if __name__=="__main__":
    unittest.main()
