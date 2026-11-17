"""A04 read-only multi-region MapID audit with synthetic RPG Maker snapshots."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import shutil
import stat
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "scripts/regions"))
from server.ruby_marshal import RubyObject
from stage import serialize
import audit_unova_a04_mapids as a04


def infos(names):
    return serialize({mid: RubyObject("RPG::MapInfo",{"@name":name.encode("utf-8")})
                      for mid,name in names.items()})


class UnovaMapIDTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="unova-a04-mapids-")
        self.addCleanup(temp.cleanup)
        self.work=Path(temp.name)
        self.project=self.work/"repo"
        self.project.mkdir()
        self.game=self.work/"PokemonBlue/Game"
        self.native=self.game/"Data"
        self.native.mkdir(parents=True)
        self.populate(self.native,{1:b"A"*64,2:b"B"*65,3:b"C"*66},
                      {1:"Decades Town",2:"Route 1",3:"Unknown Map"})
        self.overlays={}

    def populate(self,path,maps,declared=None,zeropad=3):
        path.mkdir(parents=True,exist_ok=True)
        for mid,payload in maps.items():
            (path/("Map"+str(mid).zfill(zeropad)+".rxdata")).write_bytes(payload)
        if declared is not None:
            (path/"MapInfos.rxdata").write_bytes(infos(declared))
        return path

    def overlay(self,label,maps,declared=None):
        folder=self.work/("overlay-"+label)/"Data"
        self.overlays[label]=self.populate(folder,maps,declared)
        return self.overlays[label]

    def zip_overlay(self,label,maps,declared=None,wrapper="Package/Data"):
        out=self.work/("snapshot-"+label+".zip")
        with zipfile.ZipFile(out,"w") as z:
            if declared is not None:
                z.writestr(wrapper+"/MapInfos.rxdata",infos(declared))
            for mid,payload in maps.items():
                z.writestr(wrapper+("/Map%03d.rxdata"%mid),payload)
        return out

    def test_01_no_native_data_is_blocked_not_apparently_safe(self):
        report=a04.missing_base()
        self.assertEqual(report["status"],"BLOCKED_NATIVE_DECADES_MAPINFOS_NOT_PROVIDED")
        self.assertIsNone(report["observed_or_declared_occupied_map_ids"])
        self.assertIsNone(report["available_map_ids_certified"])
        self.assertFalse(report["can_reserve_mapids"])
        self.assertEqual(report["bar_a_completed"],0)

    def test_02_read_real_mapinfos_and_real_map_files(self):
        doc=a04.scan_source(self.game,"DECADES",base=True)
        self.assertEqual(doc["map_ids_occupied_or_declared"],[1,2,3])
        self.assertEqual(doc["file_count"],3)
        self.assertTrue(doc["mapinfos_present"])
        self.assertEqual(doc["maps"][0]["mapinfo_name"],"Decades Town")
        self.assertEqual(doc["maps"][0]["sha256"],hashlib.sha256(b"A"*64).hexdigest())
        self.assertFalse(doc["map_payloads_parsed"])
        self.assertFalse(doc["region_identity_verified"])
        self.assertFalse(doc["native_game_exe_tested"])

    def test_03_empty_overlays_cannot_certify_free_ids(self):
        result=a04.analyze(a04.scan_dir(self.game,"DECADES",base=True),{})
        self.assertEqual(result["observed_or_declared_occupied_count"],3)
        self.assertEqual(result["status"],"PARTIAL_SNAPSHOTS_NO_FREE_MAPID_CERTIFICATION")
        self.assertEqual(result["region_overlay_snapshots_missing"],list(a04.REGIONS))
        self.assertIsNone(result["available_map_ids_certified"])
        self.assertFalse(result["can_reserve_mapids"])
        self.assertFalse(result["unova_destination_mapids_allocated"])
        self.assertFalse(result["can_install"])

    def test_04_different_map_bytes_same_id_flagged(self):
        k=a04.scan_dir(self.overlay("KANTO",{2:b"Kanto-new"}),"KANTO")
        result=a04.analyze(a04.scan_dir(self.native,"DECADES",base=True),{"KANTO":k})
        overlap=result["overlaps"][0]
        self.assertEqual(overlap["map_id"],2)
        self.assertEqual(overlap["classification"],
                         "DIFFERENT_OR_UNBACKED_MAPID_OVERLAP_REVIEW")
        self.assertEqual(overlap["declared_by"],["DECADES","KANTO"])
        self.assertFalse(overlap["safe_to_allocate"])
        self.assertEqual(result["status"],"OVERLAPPING_MAPIDS_REQUIRE_REVIEW")

    def test_05_identical_map_bytes_still_occupied_and_review(self):
        k=a04.scan_dir(self.overlay("KANTO",{2:b"B"*65}),"KANTO")
        result=a04.analyze(a04.scan_dir(self.native,"DECADES",base=True),{"KANTO":k})
        self.assertEqual(result["overlaps"][0]["classification"],
                         "SAME_MAP_BYTES_MULTIPLE_SNAPSHOTS_REVIEW")
        self.assertFalse(result["can_reserve_mapids"])

    def test_06_missing_file_declared_in_mapinfos_is_reserved(self):
        self.populate(self.native,{}, {1:"Decades Town",2:"Route 1",3:"Unknown Map",500:"Planned"})
        result=a04.scan_dir(self.native,"DECADES",base=True)
        self.assertIn(500,result["map_ids_occupied_or_declared"])
        self.assertEqual(result["missing_map_file_ids"],[500])
        self.assertEqual(result["mapinfos_declared_count"],4)

    def test_07_orphan_map_file_is_not_assumed_region(self):
        (self.native/"Map999.rxdata").write_bytes(b"orphan")
        result=a04.scan_dir(self.native,"DECADES",base=True)
        self.assertEqual(result["orphan_map_file_ids"],[999])
        self.assertEqual(result["maps"][-1]["mapinfo_name"],None)

    def test_08_missing_base_mapinfos_blocks(self):
        (self.native/"MapInfos.rxdata").unlink()
        with self.assertRaises(ValueError):
            a04.scan_dir(self.native,"DECADES",base=True)

    def test_09_nonmapinfos_overlay_allowed_but_cannot_prove_ownership(self):
        k=a04.scan_dir(self.overlay("KANTO",{451:b"Kanto"}),"KANTO")
        self.assertFalse(k["mapinfos_present"])
        self.assertIsNone(k["orphan_map_file_ids"])
        self.assertFalse(k["region_identity_verified"])
        result=a04.analyze(a04.scan_dir(self.native,"DECADES",base=True),{"KANTO":k})
        self.assertIn(451,result["observed_or_declared_occupied_map_ids"])
        self.assertFalse(result["all_installed_overlays_proven_complete"])

    def test_10_four_overlays_does_not_prove_completeness(self):
        snapshots={}
        for i,region in enumerate(a04.REGIONS,100):
            snapshots[region]=a04.scan_dir(self.overlay(region,{i:b"data"}),region)
        result=a04.analyze(a04.scan_dir(self.native,"DECADES",base=True),snapshots)
        self.assertEqual(result["region_overlay_snapshots_missing"],[])
        self.assertEqual(result["status"],"SNAPSHOTS_SCANNED_OWNERSHIP_UNVERIFIED")
        self.assertFalse(result["region_ownership_verified"])
        self.assertFalse(result["all_installed_overlays_proven_complete"])
        self.assertIsNone(result["available_map_ids_certified"])
        self.assertFalse(result["can_install"])

    def test_11_zip_overlay_nested_data(self):
        path=self.zip_overlay("SINNOH",{506:b"sinnoh-map"}, {506:"Twinleaf"})
        result=a04.scan_zip(path,"SINNOH")
        self.assertEqual(result["map_ids_occupied_or_declared"],[506])
        self.assertEqual(result["source_kind"],"ZIP")
        self.assertEqual(result["maps"][0]["mapinfo_name"],"Twinleaf")
        self.assertEqual(result["archive_sha256"],a04.sha256_file(path))

    def test_12_zip_base_with_valid_mapinfos(self):
        path=self.zip_overlay("DECADES",{1:b"base-map"},{1:"Origin"})
        item=a04.scan_zip(path,"DECADES",base=True)
        self.assertTrue(item["mapinfos_present"])
        self.assertEqual(item["file_count"],1)

    def test_13_zip_base_missing_mapinfos_blocks(self):
        path=self.zip_overlay("DECADES",{1:b"base-map"})
        with self.assertRaises(ValueError):
            a04.scan_zip(path,"DECADES",base=True)

    def test_14_zip_traversal_rejected(self):
        path=self.zip_overlay("HOENN",{205:b"hoenn"})
        with zipfile.ZipFile(path,"a") as z:
            z.writestr("../Game/Data/Map999.rxdata",b"malicious")
        with self.assertRaises(ValueError):
            a04.scan_zip(path,"HOENN")

    def test_15_zip_duplicate_names_casefold_rejected(self):
        path=self.zip_overlay("JOHTO",{300:b"j"})
        with zipfile.ZipFile(path,"a") as z:
            z.writestr("package/data/map300.rxdata",b"duplicate")
        with self.assertRaises(ValueError):
            a04.scan_zip(path,"JOHTO")

    def test_16_zip_symlink_member_rejected(self):
        path=self.zip_overlay("HOENN",{200:b"H"})
        with zipfile.ZipFile(path,"a") as z:
            item=zipfile.ZipInfo("Package/Data/Link")
            item.create_system=3
            item.external_attr=(stat.S_IFLNK|0o777)<<16
            z.writestr(item,b"/Game/Data")
        with self.assertRaises(ValueError):
            a04.scan_zip(path,"HOENN")

    def test_17_zip_multiple_data_roots_rejected(self):
        path=self.zip_overlay("KANTO",{3:b"K"})
        with zipfile.ZipFile(path,"a") as z:
            z.writestr("Other/Data/Map009.rxdata",b"other region")
        with self.assertRaises(ValueError):
            a04.scan_zip(path,"KANTO")

    def test_18_inconsistent_zero_padding_same_id_dir_blocks(self):
        (self.native/"Map1.rxdata").write_bytes(b"another")
        with self.assertRaises(ValueError):
            a04.scan_dir(self.native,"DECADES",base=True)

    def test_19_invalid_marshal_mapinfos_blocks(self):
        (self.native/"MapInfos.rxdata").write_bytes(b"not ruby data")
        with self.assertRaises(ValueError):
            a04.scan_dir(self.native,"DECADES",base=True)

    def test_20_zip_source_symlink_rejected(self):
        real=self.zip_overlay("KANTO",{10:b"K"})
        target=self.work/"linked.zip"
        try:
            target.symlink_to(real)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            a04.scan_zip(target,"KANTO")

    def test_21_native_dir_symlink_rejected(self):
        alias=self.work/"alias"
        try:
            alias.symlink_to(self.game,target_is_directory=True)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            a04.scan_dir(alias,"DECADES",base=True)

    def test_22_map_file_symlink_rejected(self):
        file=self.native/"Map002.rxdata"
        original=self.work/"map-copy"
        shutil.copyfile(file,original)
        file.unlink()
        try:
            file.symlink_to(original)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            a04.scan_dir(self.native,"DECADES",base=True)

    def test_23_invalid_overlay_label_rejected(self):
        with self.assertRaises(ValueError):
            a04.overlay_args(["UNOVA=/tmp/game/Data"])

    def test_24_duplicate_overlay_label_rejected(self):
        with self.assertRaises(ValueError):
            a04.overlay_args(["KANTO=one","kanto=two"])

    def test_25_report_content_addressed_idempotent(self):
        doc=a04.analyze(a04.scan_dir(self.native,"DECADES",base=True),{})
        output=a04.write_private(self.project,doc)
        before=output.read_bytes()
        same=a04.write_private(self.project,doc)
        self.assertEqual(output,same)
        self.assertEqual(before,same.read_bytes())
        second=a04.write_private(self.project,dict(doc,status="WRONG"))
        self.assertNotEqual(output,second)
        self.assertEqual(before,output.read_bytes())
        self.assertFalse((self.project/"game").exists())

    def test_26_report_directory_symlink_rejected(self):
        outside=self.work/"outside"
        outside.mkdir()
        work=self.project/".blue-work"
        try:
            work.symlink_to(outside,target_is_directory=True)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            a04.write_private(self.project,a04.missing_base())
        self.assertFalse((outside/"unova").exists())

    def test_27_cli_no_base_fails_closed_and_writes_blocked_evidence(self):
        output=io.StringIO()
        with contextlib.redirect_stdout(output):
            code=a04.main(["--project",str(self.project),"--write"])
        self.assertEqual(code,2)
        report=json.loads(output.getvalue())
        self.assertEqual(report["status"],"BLOCKED_NATIVE_DECADES_MAPINFOS_NOT_PROVIDED")
        self.assertTrue(list((self.project/a04.REPORT_DIR).glob("a04-mapids-*.json")))

    def test_28_cli_base_only_inspects_without_changes(self):
        before=(self.native/"MapInfos.rxdata").read_bytes()
        output=io.StringIO()
        with contextlib.redirect_stdout(output),contextlib.redirect_stderr(io.StringIO()):
            code=a04.main(["--project",str(self.project),"--base-data",str(self.game),"--write"])
        self.assertEqual(code,0)
        summary=json.loads(output.getvalue())
        self.assertEqual(summary["observed_or_declared_occupied_count"],3)
        self.assertFalse(summary["can_install"])
        self.assertFalse(summary["can_reserve_mapids"])
        self.assertEqual(before,(self.native/"MapInfos.rxdata").read_bytes())

    def test_29_cli_four_region_overlays_including_zip(self):
        k=self.overlay("KANTO",{100:b"K"})
        j=self.overlay("JOHTO",{200:b"J"})
        h=self.zip_overlay("HOENN",{300:b"H"})
        s=self.overlay("SINNOH",{400:b"S"})
        args=["--project",str(self.project),"--base-data",str(self.native)]
        args+=["--overlay",f"KANTO={k}","--overlay",f"JOHTO={j}",
               "--overlay",f"HOENN={h}","--overlay",f"SINNOH={s}"]
        with contextlib.redirect_stdout(io.StringIO()):
            code=a04.main(args)
        self.assertEqual(code,0)
        self.assertEqual((self.native/"Map001.rxdata").read_bytes(),b"A"*64)

    def test_30_base_mapinfos_map_id_must_be_positive(self):
        self.populate(self.native,{}, {0:"Invalid",1:"Decades"})
        with self.assertRaises(ValueError):
            a04.scan_dir(self.native,"DECADES",base=True)

    def test_31_mapinfos_does_not_prove_map_payload_integrity(self):
        self.native.joinpath("Map001.rxdata").write_bytes(b"not marshal")
        doc=a04.scan_dir(self.native,"DECADES",base=True)
        self.assertFalse(doc["map_payloads_parsed"])
        self.assertFalse(doc["native_game_exe_tested"])
        self.assertFalse(doc["region_identity_verified"])

    def test_32_untracked_regions_cannot_be_automatically_assigned(self):
        k=a04.scan_dir(self.overlay("KANTO",{450:b"maybe"}),"KANTO")
        doc=a04.analyze(a04.scan_dir(self.native,"DECADES",base=True),{"KANTO":k})
        self.assertFalse(doc["region_ownership_verified"])
        self.assertFalse(doc["unova_destination_mapids_allocated"])
        self.assertIsNone(doc["available_map_ids_certified"])
        self.assertEqual(doc["bar_a_completed"],0)


if __name__=="__main__":
    unittest.main()
