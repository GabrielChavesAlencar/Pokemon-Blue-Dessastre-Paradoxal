"""B01 synthetic-only inventory: no gameplay or native allocation."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from audit_sinnoh_b01_inventory import compare,unpack
from server.ruby_marshal import RubyObject
from stage import serialize

class B01Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.file=Path(self.temp.name)/"inventory.zip"
        self.info=serialize({
          1:RubyObject("RPG::MapInfo",{"@name":b"Decades"}),
          209:RubyObject("RPG::MapInfo",{"@name":b"Kanto"}),
          400:RubyObject("RPG::MapInfo",{"@name":b"Hoenn"})})
        self.tiles=serialize([])
    def make(self,ids=None,mutate=None,extra=None,infos=None):
        ids=[1,209,400] if ids is None else ids
        inf=self.info if infos is None else infos
        report={
          "schema":1,"mode":"DECADES_LOCAL_MAPID_INVENTORY_READ_ONLY",
          "project":"Pokemon Blue Dessastre Paradoxal / Decades",
          "mapinfos_sha256":hashlib.sha256(inf).hexdigest(),
          "tilesets_sha256":hashlib.sha256(self.tiles).hexdigest(),
          "physical_map_file_count":len(ids),"physical_map_ids":ids,
          "scan_only":True,"game_or_saves_modified":False,
          "future_region_reservations_verified":False,
          "manually_executed_native_qa":False,"full_local_path_exported":False
        }
        if mutate:mutate(report)
        content={"native_inventory.json":json.dumps(report).encode(),
                 "MapInfos.rxdata":inf,"Tilesets.rxdata":self.tiles}
        if extra:content.update(extra)
        with zipfile.ZipFile(self.file,"w",zipfile.ZIP_DEFLATED) as z:
            for name,raw in content.items():z.writestr(name,raw)
    def test_01_snapshot_compares_without_installation(self):
        self.make()
        x=compare(self.file)
        self.assertIn(209,x["sinnoh_original_ids_colliding_with_decades"])
        self.assertEqual(x["sinnoh_source_map_count"],76)
        self.assertEqual(x["conservative_unoccupied_1_to_599_count"],596)
        self.assertFalse(x["can_install"])
        self.assertFalse(x["can_select_destinations"])
        self.assertEqual(x["phase_b_approved"],0)
    def test_02_missing_file_rejected(self):
        with self.assertRaisesRegex(ValueError,"ausente"):compare(self.file)
    def test_03_extra_file_is_not_accepted(self):
        self.make(extra={"Game.exe":b"no"})
        with self.assertRaisesRegex(ValueError,"extra"):compare(self.file)
    def test_04_hash_must_match(self):
        self.make(mutate=lambda x:x.update(mapinfos_sha256="0"*64))
        with self.assertRaisesRegex(ValueError,"hash"):compare(self.file)
    def test_05_forged_native_approval_rejected(self):
        for key in ("future_region_reservations_verified","game_or_saves_modified",
                    "manually_executed_native_qa","full_local_path_exported"):
            with self.subTest(key=key):
                self.make(mutate=lambda x,k=key:x.update({k:True}))
                with self.assertRaisesRegex(ValueError,"conclusao falsa"):compare(self.file)
    def test_06_duplicates_rejected(self):
        self.make(ids=[1,1,209])
        with self.assertRaisesRegex(ValueError,"MapIDs fisicos"):compare(self.file)
    def test_07_index_file_discrepancies_reported(self):
        self.make(ids=[1,209,500])
        x=compare(self.file)
        self.assertEqual(x["native_indexed_maps_missing_files"],[400])
        self.assertEqual(x["native_physical_maps_missing_index"],[500])
    def test_08_invalid_marshal_rejected(self):
        self.make(infos=b"not marshal")
        with self.assertRaises(ValueError):compare(self.file)
    def test_09_out_of_range_sinnoh_ids_never_destinations(self):
        self.make()
        x=compare(self.file)
        self.assertIn(906,x["sinnoh_original_ids_outside_conservative_destination_band"])
        self.assertFalse(x["other_region_future_reservations_verified"])
    def test_10_never_modify_source_zip(self):
        self.make()
        before=hashlib.sha256(self.file.read_bytes()).hexdigest()
        compare(self.file)
        self.assertEqual(hashlib.sha256(self.file.read_bytes()).hexdigest(),before)
    def test_11_forged_donor_receipt_rejected(self):
        self.make()
        source=json.loads((ROOT/"data/regions/sinnoh-b00-actual-source.json").read_text())
        source["sinnoh_map_count"]=75
        tmp=Path(self.temp.name)/"receipt.json"
        tmp.write_text(json.dumps(source))
        with self.assertRaisesRegex(ValueError,"recibo"):compare(self.file,source=tmp)
    def test_12_archive_unpack_shape(self):
        self.make()
        item,_=unpack(self.file)
        self.assertEqual(item["physical_map_file_count"],3)

if __name__=="__main__":unittest.main()
