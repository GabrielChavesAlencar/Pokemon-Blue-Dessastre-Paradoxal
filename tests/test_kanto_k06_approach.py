"""Verify only exact original approaches can enter the disposable test graph."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts/regions"))
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
