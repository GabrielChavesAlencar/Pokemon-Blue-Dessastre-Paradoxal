"""Verify only exact original approaches can enter the disposable test graph."""
from pathlib import Path
import sys
import json
from unittest.mock import patch
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts/regions"))
from audit_k06_rocket import audit_conditions, selectors
from k06_windows_approach import activation_enabled, RELEASE_FLAG
from k06_approach_migration import require_hashes, sha_bytes, verify_k05_android_predecessor
from build_k06_approach import APPROACH, EXACT_SEAMS, TEMP_GATES, TRANSFERS, planned_connections, verify_source


class K06ApproachTests(unittest.TestCase):
    def test_boundary_and_guard_contract(self):
        slots={i:300+i for i in (*APPROACH,93,87,114,83)}
        stale=[f"{slots[107]},East,35,{slots[83]},West,0",
               f"{slots[114]},East,0,{slots[111]},West,0"]
        keep=f"{slots[93]},North,0,{slots[87]},South,0"
        next,removed=planned_connections("\n".join([keep,*stale]),slots)
        self.assertEqual(removed,stale)
        self.assertEqual(next.splitlines(),[keep,*[",".join(map(str,(slots[a],d,o,slots[b],p,q)))
                                                           for a,d,o,b,p,q in EXACT_SEAMS]])
        self.assertEqual({k for k,v in TRANSFERS.items() if v[1]==168},TEMP_GATES)

    def test_bad_source_warp_rejected(self):
        report={"connections":list(EXACT_SEAMS),"warps":[
            dict(source=s,event=e,at=at,destination=d,xy=xy,direction=f)
            for (s,e),(at,d,xy,f) in TRANSFERS.items()]}
        verify_source(report)
        report["warps"][0]["direction"]=6
        with self.assertRaisesRegex(ValueError,"Original Route 8"):
            verify_source(report)

    def test_source_progression_records_do_not_copy_messages_or_ruby(self):
        self.assertEqual(selectors({"code":111,"parameters":[12,"donor Ruby"]}),{})
        self.assertEqual(selectors({"code":102,"parameters":[["dialogue","another string"],0]}),{"option_count":2})
        self.assertEqual(selectors({"code":121,"parameters":[58,58,0]}),{"numeric_control":[58,58,0]})
        self.assertEqual(selectors({"code":123,"parameters":["A",0]}),{"self_switch":["A",0]})
        self.assertEqual(audit_conditions({"@switch1_valid":True,"@switch1_id":58,
                                           "@switch2_valid":False,"@switch2_id":99}),{"@switch1_id":58})


    def test_installed_plan_rejects_unowned_or_modified_baseline(self):
        with TemporaryDirectory() as temp:
            root=Path(temp).resolve()
            rel="Map107.rxdata"
            path=root/rel
            path.write_bytes(b"owned")
            require_hashes(root,[rel],{rel:sha_bytes(b"owned")})
            with self.assertRaisesRegex(ValueError,"not the recorded baseline"):
                require_hashes(root,[rel],{rel:sha_bytes(b"edited")})
            self.assertEqual(path.read_bytes(),b"owned")

    def test_android_predecessor_requires_actual_source_inventory_digest(self):
        from scripts.android.source_update import PRODUCT_REVISION, installed_provenance
        from scripts.android.update_client import MARKER
        recipe="4bda388e0f6d07763c95cfd9877ce337e61f9cb9"
        with TemporaryDirectory() as temp:
            root=Path(temp).resolve()
            path=root/MARKER
            path.parent.mkdir()
            mark={"schema":1,"revision":PRODUCT_REVISION,"channel":"multiregion",
                  "files":{"Data/Map373.rxdata":{"size":2,"sha256":"a"*64}}}
            mark["source_update"]=installed_provenance(mark["files"],recipe)
            path.write_text(json.dumps(mark),encoding="utf8")
            maps={"kanto":dict(enumerate(range(178))),"hoenn":dict(enumerate(range(199)))}
            with patch("scripts.android.source_update.protected_map_inventory",return_value=(maps,{})) as check:
                self.assertEqual(verify_k05_android_predecessor(root)[0],mark)
                check.assert_called_once()
                mark["files"]["Data/Map373.rxdata"]["size"]=3
                path.write_text(json.dumps(mark),encoding="utf8")
                with self.assertRaisesRegex(ValueError,"verified source-built K05"):
                    verify_k05_android_predecessor(root)
                self.assertEqual(check.call_count,1)

    def test_windows_product_flag_has_exact_source_maps(self):
        with TemporaryDirectory() as folder:
            root=Path(folder).resolve()
            self.assertFalse(activation_enabled(root))
            flag=root/RELEASE_FLAG
            flag.parent.mkdir(parents=True)
            record={"schema":1,"stage":"K06_APPROACH","source_maps":list(range(107,114))}
            flag.write_text(json.dumps(record),encoding="utf8")
            self.assertTrue(activation_enabled(root))
            record["source_maps"].append(114)
            flag.write_text(json.dumps(record),encoding="utf8")
            with self.assertRaisesRegex(ValueError,"revisão autorizada"):
                activation_enabled(root)
