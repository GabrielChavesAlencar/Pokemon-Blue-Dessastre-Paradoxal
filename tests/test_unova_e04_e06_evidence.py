"""End-to-end synthetic cross-report checks, without launching any donor code."""
from __future__ import annotations
import copy
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts/regions"))
from server.ruby_marshal import RubyObject
from stage import serialize
import unova_e04_intake as intake
import audit_unova_u02 as zipaudit
import audit_unova_source_detail as source_detail
import audit_unova_e05_crosswalk as crosswalk
import audit_unova_e06_rights_inventory as rights
import audit_unova_e04_e06_evidence as gate


class EvidenceConsistencyTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="unova-evidence-")
        self.addCleanup(tmp.cleanup)
        self.base=Path(tmp.name)
        self.project=self.base/"project"
        self.project.mkdir()
        self.origin=self.base/"donor.zip"
        self.credits=self.base/"Credits.txt"
        self.credits.write_text("Artist credited, no permission granted.\n",encoding="utf-8")
        meta={1:RubyObject("RPG::MapInfo",{"@name":b"Nuvema Town"}),
              2:RubyObject("RPG::MapInfo",{"@name":b"Route 1"})}
        map1=RubyObject("RPG::Map",{"@width":16,"@height":15,"@events":{}})
        map2=RubyObject("RPG::Map",{"@width":12,"@height":12,"@events":{}})
        with zipfile.ZipFile(self.origin,"w") as z:
            z.writestr("World/Data/MapInfos.rxdata",serialize(meta))
            z.writestr("World/Data/Tilesets.rxdata",b"untested")
            z.writestr("World/Data/Map001.rxdata",serialize(map1))
            z.writestr("World/Data/Map002.rxdata",serialize(map2))
            z.writestr("World/Graphics/Tilesets/City.png",b"asset")
        self.catalog=json.loads((ROOT/"data/regions/unova-u03-areas.json").read_text("utf-8"))

    def build(self):
        intake.intake(self.project,self.origin,self.credits)
        p=self.project/".blue-work/unova/sources/Pokemon_World_V18.zip"
        za=zipaudit.audit_zip(p)
        zipaudit.write_report(self.project,za)
        raw=source_detail.inspect(p,self.catalog)
        local=self.project/".blue-work/unova/audit"
        (local/"u02-rxdata-detail.json").write_text(json.dumps(raw),encoding="utf-8")
        cw=crosswalk.classify(raw,self.catalog)
        crosswalk.save(self.project,local/"e05-crosswalk.json",cw)
        report=rights.inspect(self.project,p)
        rights.save(self.project,report)
        return local

    def read(self,loc,name):
        return json.loads((loc/name).read_text("utf-8"))

    def write(self,loc,name,obj):
        (loc/name).write_text(json.dumps(obj),encoding="utf-8")

    def test_01_missing_source_does_not_approve_e04(self):
        report=gate.evidence(self.project)
        self.assertEqual(report["status"],"BLOCKED_MISSING_SOURCE_EVIDENCE")
        self.assertEqual(len(report["missing_reports"]),5)
        self.assertEqual(report["bar_e_completed"],4)
        self.assertFalse(report["can_install"])

    def test_02_consistent_private_reports_are_still_not_licensed(self):
        self.build()
        r=gate.evidence(self.project)
        self.assertEqual(r["status"],"CONSISTENT_PRIVATE_REPORTS_NOT_LICENSED_OR_INSTALLED")
        self.assertTrue(r["matched_source_hashes"])
        self.assertEqual(r["whole_donor_project_map_count"],2)
        self.assertEqual(r["symbolic_area_count"],74)
        self.assertEqual(r["source_name_candidate_area_count"],2)
        self.assertFalse(r["map_identity_confirmed"])
        self.assertFalse(r["rights_cleared"])
        self.assertFalse(r["can_install"])
        self.assertFalse(r["game_or_saves_modified"])
        self.assertFalse((self.project/"game").exists())

    def test_03_tampered_report_zip_hash_blocks(self):
        loc=self.build()
        v=self.read(loc,"e05-crosswalk.json")
        v["source_zip_sha256"]="f"*64
        self.write(loc,"e05-crosswalk.json",v)
        with self.assertRaisesRegex(ValueError,"diferentes"):
            gate.evidence(self.project)

    def test_04_tampered_mapinfos_hash_blocks(self):
        loc=self.build()
        v=self.read(loc,"e05-crosswalk.json")
        v["source_mapinfos_sha256"]="f"*64
        self.write(loc,"e05-crosswalk.json",v)
        with self.assertRaisesRegex(ValueError,"MapInfos"):
            gate.evidence(self.project)

    def test_05_fake_destination_mapid_is_rejected(self):
        loc=self.build()
        v=self.read(loc,"e05-crosswalk.json")
        v["areas"][0]["destination_map_id"]=900
        self.write(loc,"e05-crosswalk.json",v)
        with self.assertRaises(ValueError):
            gate.evidence(self.project)

    def test_06_false_license_is_rejected(self):
        loc=self.build()
        v=self.read(loc,"e06-rights-inventory.json")
        v["assets"][0]["can_redistribute"]=True
        self.write(loc,"e06-rights-inventory.json",v)
        with self.assertRaises(ValueError):
            gate.evidence(self.project)

    def test_07_credit_file_mismatch_is_rejected(self):
        loc=self.build()
        v=self.read(loc,"e06-rights-inventory.json")
        v["credits"]["credits_sha256"]="f"*64
        self.write(loc,"e06-rights-inventory.json",v)
        with self.assertRaises(ValueError):
            gate.evidence(self.project)

    def test_08_source_mapid_not_present_is_rejected(self):
        loc=self.build()
        v=self.read(loc,"e05-crosswalk.json")
        v["areas"][0]["candidate_source_map_ids"]=[500]
        self.write(loc,"e05-crosswalk.json",v)
        with self.assertRaises(ValueError):
            gate.evidence(self.project)

    def test_09_private_report_write_is_idempotent(self):
        self.build()
        r=gate.evidence(self.project)
        dest=gate.save(self.project,r)
        original=dest.read_bytes()
        gate.save(self.project,r)
        self.assertEqual(original,dest.read_bytes())
        with self.assertRaises(ValueError):
            gate.save(self.project,dict(r,status="PLAYABLE"))
        self.assertEqual(original,dest.read_bytes())

    def test_10_no_source_gate_exit_code_is_blocking(self):
        ret=gate.main(["--project",str(self.project)])
        self.assertEqual(ret,2)
        self.assertFalse((self.project/"game").exists())


if __name__=="__main__":
    unittest.main()
