"""MapInfos-only audit is robust to RMXP maps incompatible with the parser."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from server.ruby_marshal import RubyObject
from stage import serialize
import audit_unova_e05_mapinfos_only as index


class RealNamesFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads((ROOT/"data/regions/unova-u03-areas.json").read_text("utf-8"))

    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="unova-mapinfos-")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.src=self.root/".blue-work/unova/sources"
        self.src.mkdir(parents=True)
        self.zip=self.src/"Pokemon_World_V18.zip"

    def build(self,records=None,missing=None):
        if records is None:
            records={1:("Unova",0),2:("Nuvema Town",1),
                     3:("Route 1",1),4:("Pallet Town",0)}
        infos={
            key:RubyObject("RPG::MapInfo", {"@name":name.encode(), "@parent_id":parent})
            for key,(name,parent) in records.items()
        }
        with zipfile.ZipFile(self.zip,"w") as z:
            z.writestr("World/Data/MapInfos.rxdata",serialize(infos))
            z.writestr("World/Data/Tilesets.rxdata",b"not parsed")
            for mid in records:
                if mid == missing:
                    continue
                z.writestr(f"World/Data/Map{mid:03d}.rxdata",
                           b"Map binary bytes never parsed by this audit")
        return self.zip

    def test_01_parent_unova_and_nuvema_names(self):
        r=index.inspect(self.build(), self.catalog)
        self.assertEqual(r["whole_donor_project_map_count"],4)
        self.assertEqual(r["mapinfos_entry_count"],4)
        self.assertEqual(r["symbolic_areas"],74)
        self.assertEqual(r["clues"]["anchored_by_unova_parent_name"],3)
        child=next(x for x in r["maps"] if x["source_map_id"]==2)
        self.assertTrue(child["ancestor_unova_or_isshu_keyword"])
        self.assertEqual(child["ancestor_names"],["Nuvema Town","Unova"])
        self.assertFalse(child["identity_confirmed"])
        self.assertFalse(r["events_inspected"])
        self.assertFalse(r["can_install"])

    def test_02_route_generic_remains_unverified(self):
        r=index.inspect(self.build(),self.catalog)
        row=next(x for x in r["areas"] if x["area_key"]=="UNOVA_ROUTE_01")
        self.assertTrue(row["generic_name_unresolved"])
        self.assertFalse(row["manually_verified"])

    def test_03_fake_or_unsupported_map_bytes_do_not_abort(self):
        r=index.inspect(self.build(),self.catalog)
        self.assertEqual(r["mapinfos_entry_count"],4)
        self.assertFalse(r["events_inspected"])

    def test_04_missing_map_file_is_not_claimed_installed(self):
        r=index.inspect(self.build(missing=4),self.catalog)
        x=next(x for x in r["maps"] if x["source_map_id"]==4)
        self.assertFalse(x["source_map_file_in_zip"])

    def test_05_invalid_catalog_state_blocks(self):
        cat=dict(self.catalog,may_install=True)
        with self.assertRaises(ValueError):
            index.inspect(self.build(),cat)

    def test_06_duplicate_parent_cycle_blocks(self):
        records={1:("Unova",2),2:("Nuvema Town",1)}
        with self.assertRaises(ValueError):
            index.inspect(self.build(records),self.catalog)

    def test_07_mapinfos_corrupt_blocks(self):
        with zipfile.ZipFile(self.build(),"a") as z:
            # duplicate is already rejected at ZIP metadata gate
            z.writestr("world/data/mapinfos.rxdata",b"corrupt")
        with self.assertRaises(ValueError):
            index.inspect(self.zip,self.catalog)

    def test_08_map_id_parent_invalid_blocks(self):
        records={1:("Unova",-1),2:("Nuvema Town",1)}
        with self.assertRaises(ValueError):
            index.inspect(self.build(records),self.catalog)

    def test_09_name_missing_raises(self):
        records={1:("",0)}
        with self.assertRaises(ValueError):
            index.inspect(self.build(records),self.catalog)

    def test_10_source_mapids_are_not_target_ids(self):
        r=index.inspect(self.build(),self.catalog)
        self.assertTrue(all(x["destination_map_id"] is None for x in r["maps"]))
        self.assertFalse(r["native_mapids_checked"])
        self.assertFalse(r["rights_verified"])
        self.assertFalse(r["game_exe_tested"])

    def test_11_cli_missing_source_fail_closed(self):
        out=index.main(["--project",str(self.root),
                        "--catalog",str(ROOT/"data/regions/unova-u03-areas.json")])
        self.assertEqual(out,2)

    def test_12_report_only_under_ignored_workspace(self):
        self.build()
        with zipfile.ZipFile(self.zip,"r"): pass
        # inspect is side-effect free and leaves game/saves absent
        r=index.inspect(self.zip,self.catalog)
        self.assertFalse(r["game_or_saves_modified"])
        self.assertFalse((self.root/"game").exists())
        self.assertFalse((self.root/"saves").exists())


if __name__ == "__main__":
    unittest.main()
