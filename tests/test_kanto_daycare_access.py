"""One-cell, source-guarded Route 5 Day Care approach adaptation."""
import copy
import struct
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "scripts/regions"))
from pilot import restore_route5_daycare_walkway
from server.ruby_marshal import RubyObject, RubyData


class DaycareAccessTest(unittest.TestCase):
    def fixture(self):
        w,h,d=40,40,3
        cells=[0]*(w*h*d)
        def put(x,y,stack):
            for z,v in enumerate(stack):
                cells[x+w*(y+h*z)]=v
        for x in range(20,27):
            put(x,27,(385,1212,0))
        put(23,25,(434,1954,0))
        put(23,26,(442,0,0))
        put(23,28,(385,0,0))
        raw=struct.pack("<5I",3,w,h,d,len(cells))+struct.pack(f"<{len(cells)}H",*cells)
        return RubyObject("RPG::Map",{"@data":RubyData("Table",raw),
            "@events":{1:RubyObject("RPG::Event",{"@x":23,"@y":25})}})

    def test_exact_single_cell_and_donor_preserved(self):
        donor=self.fixture()
        stage=copy.deepcopy(donor)
        original=donor.attrs["@data"].data
        restore_route5_daycare_walkway(stage,donor)
        after=stage.attrs["@data"].data
        before_cells=struct.unpack_from("<4800H",original,20)
        after_cells=struct.unpack_from("<4800H",after,20)
        self.assertEqual([(i,a,b) for i,(a,b) in enumerate(zip(before_cells,after_cells)) if a!=b],
                         [(23+40*(27+40),1212,0)])
        self.assertEqual(donor.attrs["@data"].data,original)

    def test_rejects_changed_source_or_event(self):
        donor=self.fixture()
        stage=copy.deepcopy(donor)
        donor.attrs["@events"][1].attrs["@x"]=22
        with self.assertRaisesRegex(ValueError,"entrance changed"):
            restore_route5_daycare_walkway(stage,donor)
        donor=self.fixture()
        stage=copy.deepcopy(donor)
        stage.attrs["@data"].data=stage.attrs["@data"].data[:-2]+b"\x01\x00"
        with self.assertRaisesRegex(ValueError,"differs from source"):
            restore_route5_daycare_walkway(stage,donor)


if __name__=="__main__":
    unittest.main()
