"""F03 offline contract tests; original archives are checked separately."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
import struct

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"scripts/regions")]
import audit_sinnoh_expansion_f03 as f
from server.ruby_marshal import RubyData

class ExpansionF03(unittest.TestCase):
    def test_catalog_and_baseline(self):
        rows=f.reconcile(f.catalog(),[])
        self.assertEqual(len(rows),133)
        self.assertEqual(sum(r["prepared_in_pilot"] for r in rows),10)
        self.assertEqual(sum(r["category"]=="Cidades e vilarejos" for r in rows),14)
        self.assertEqual(sum(r["category"]=="Rotas" for r in rows),30)
        self.assertTrue(all(r["destination_map_id"] is None and not r["import_approved"] for r in rows))
    def test_candidate_statuses(self):
        rows=[{"symbol":"SINNOH_ROUTE_203","label":"Route 203","category":"Rotas"}]
        m={"source_id":12,"name":"Route 203","issues":[]}
        self.assertEqual(f.reconcile(rows,[m])[0]["source_status"],"unique_candidate")
        self.assertEqual(f.reconcile(rows,[m,{**m,"source_id":13}])[0]["source_status"],"ambiguous")
        self.assertEqual(f.reconcile(rows,[{**m,"issues":["empty_geometry"]}])[0]["source_status"],"blocked_candidate")
        self.assertEqual(f.reconcile(rows,[{**m,"name":"Route 203 East"}])[0]["source_status"],"no_exact_match")
    def test_invalid_zip_names(self):
        for names in (["A.png","a.PNG"],["../x"],["/x"],["C:/x"],["a\\x"]):
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/"bad.zip"
                with zipfile.ZipFile(p,"w") as z:
                    for n in names:z.writestr(n,b"x")
                with zipfile.ZipFile(p) as z,self.assertRaises(ValueError):f.index(z)
    def test_table_shape(self):
        raw=RubyData("Table",struct.pack("<5I2H",1,2,1,1,2,0,15))
        self.assertEqual(f.table1(raw),(0,15))
        with self.assertRaises(ValueError):f.table(raw,(3,2,1,1))
    def test_capacity_checks_existing_mapping(self):
        mapping={k:442+i for i,k in enumerate(sorted(f.PREPARED))}
        with tempfile.TemporaryDirectory() as d:
            base=Path(d);(base/"Data").mkdir()
            (base/"Data/MapInfos.rxdata").write_bytes(b"fixture")
            with patch.object(f,"read_marshal",return_value={2:None}),patch("install_sinnoh_experimental_windows.native_map_ids",return_value={2,452}):
                out=f.local_capacity(base,mapping)
                self.assertEqual(out["unallocated_qa_capacity"],65)
                self.assertTrue(out["f04_twelve_city_capacity"])
                self.assertFalse(out["allocated"])
            with patch.object(f,"read_marshal",return_value={442:None}),patch("install_sinnoh_experimental_windows.native_map_ids",return_value=set()):
                with self.assertRaises(ValueError):f.local_capacity(base,mapping)
if __name__=="__main__":unittest.main()
