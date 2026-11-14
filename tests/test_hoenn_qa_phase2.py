"""Hoenn QA 02/12: static 199-map and PBS checks, with synthetic RXDATA only."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))

from build_johto_events import ruby,command
import hoenn_qa_phase2 as qa


class HoennQAMapConnectionsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path=Path(self.tmp.name)
        self.mapping={old:700+i for i,old in enumerate(qa.SOURCE_MAPS)}
        self.maps={old:ruby("RPG::Map",width=1000,height=1000,events={})
                   for old in qa.SOURCE_MAPS}

    @staticmethod
    def event(event_id,name,x,y,*commands):
        page=ruby("RPG::Event::Page",list=list(commands))
        return ruby("RPG::Event",id=event_id,name=name.encode(),
                    x=x,y=y,pages=[page])

    def all_pbs(self):
        return "\n".join(
            f"{self.mapping[a]},{ea},{oa},{self.mapping[b]},{eb},{ob}"
            for a,ea,oa,b,eb,ob in qa.ALL_BORDERS
        )+"\n"

    def test_199_maps_and_all_pbs_borders_accepted(self):
        self.assertEqual(len(qa.SOURCE_MAPS),199)
        result=qa.inspect_connections(self.all_pbs(),self.mapping,self.maps)
        self.assertEqual(result["verified_border_records"],len(qa.ALL_BORDERS))
        self.assertFalse(result["field_moves_tested_in_engine"])

    def test_missing_border_fails_closed(self):
        rows=self.all_pbs().splitlines()
        with self.assertRaisesRegex(ValueError,"Faltam"):
            qa.inspect_connections("\n".join(rows[1:]),self.mapping,self.maps)

    def test_duplicate_border_fails_closed(self):
        s=self.all_pbs().splitlines()[0]
        with self.assertRaisesRegex(ValueError,"duplicada"):
            qa.inspect_connections(self.all_pbs()+s+"\n",self.mapping,self.maps)

    def test_unexpected_native_map_reference_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"inesperado"):
            qa.inspect_connections(
                self.all_pbs()+"700,North,0,441,South,0\n",
                self.mapping,self.maps)

    def test_inverted_or_unknown_border_is_rejected(self):
        rows=self.all_pbs().splitlines()
        fields=rows[0].split(",")
        fields[4]=fields[1]  # the two sides must face one another
        rows[0]=",".join(fields)
        with self.assertRaisesRegex(ValueError,"Direções"):
            qa.inspect_connections("\n".join(rows),self.mapping,self.maps)

    def test_border_offset_is_bounded_by_real_geometry(self):
        rows=self.all_pbs().splitlines()
        fields=rows[0].split(",")
        fields[2]="1001"
        rows[0]=",".join(fields)
        with self.assertRaisesRegex(ValueError,"fora das dimensões"):
            qa.inspect_connections("\n".join(rows),self.mapping,self.maps)

    def test_native_rmxp_warp_is_mapped_into_199_pilot_ids(self):
        first=83
        dest=238
        self.maps[first].attrs["@events"]={
            1:self.event(1,"Door",10,10,command(201,0,self.mapping[dest],14,15,0))
        }
        report=qa.audit_map(first,self.maps[first],self.maps,self.mapping)
        self.assertEqual(report["direct_warps"],
                         [(first,10,10,dest,14,15,"native_201")])

    def test_native_warp_to_non_hoenn_map_is_rejected(self):
        self.maps[83].attrs["@events"]={
            1:self.event(1,"Broken",10,10,command(201,0,441,14,15,0))
        }
        with self.assertRaisesRegex(ValueError,"fora do piloto"):
            qa.audit_map(83,self.maps[83],self.maps,self.mapping)

    def test_blue_script_warp_checks_original_source_id_and_landing(self):
        self.maps[83].attrs["@events"]={
            1:self.event(1,"WarpScript",10,10,
                command(355,b"BlueHoennPilot.stage10_transfer(83,238,12,13)"))
        }
        r=qa.audit_map(83,self.maps[83],self.maps,self.mapping)
        self.assertEqual(r["script_warps"],
                         [(83,10,10,238,12,13,"stage10_transfer")])
        self.maps[83].attrs["@events"][1]=self.event(
            1,"WrongSource",10,10,
            command(355,b"BlueHoennPilot.stage10_transfer(94,238,12,13)"))
        with self.assertRaisesRegex(ValueError,"divergente"):
            qa.audit_map(83,self.maps[83],self.maps,self.mapping)

    def test_script_warp_to_invalid_cell_is_rejected(self):
        self.maps[83].attrs["@events"]={
            1:self.event(1,"BadWarp",10,10,
                command(355,b"BlueHoennPilot.stage10_transfer(83,238,9999,3)"))
        }
        with self.assertRaisesRegex(ValueError,"fora de limites"):
            qa.audit_map(83,self.maps[83],self.maps,self.mapping)

    def test_event_indices_footprints_and_bounds(self):
        self.maps[83].attrs["@events"]={
            1:self.event(1,"A",10,10,command(0)),
            2:self.event(2,"B",10,10,command(0)),
        }
        with self.assertRaisesRegex(ValueError,"sobrepostos"):
            qa.audit_map(83,self.maps[83],self.maps,self.mapping)
        self.maps[83].attrs["@events"]={
            1:self.event(2,"WrongId",10,10,command(0)),
        }
        with self.assertRaisesRegex(ValueError,"divergentes"):
            qa.audit_map(83,self.maps[83],self.maps,self.mapping)
        self.maps[83].attrs["@events"]={
            1:self.event(1,"Outside",1001,10,command(0)),
        }
        with self.assertRaisesRegex(ValueError,"fora dos limites"):
            qa.audit_map(83,self.maps[83],self.maps,self.mapping)

    def test_marker_has_exact_physical_map_remap(self):
        copy=self.path
        (copy/"Data").mkdir()
        records={str(a):b for a,b in self.mapping.items()}
        (copy/"Hoenn pilot.json").write_text(json.dumps({
            "region":"HOENN","kind":"ISOLATED_HOENN_TEST",
            "source_commit":qa.UPSTREAM,"maps":records}),encoding="utf-8")
        (copy/"Data/blue-hoenn-pilot.txt").write_text(
            "BLUE_HOENN_PILOT_V1\n708,25,6\n"
            + "".join(f"{a},{b}\n" for a,b in self.mapping.items()),encoding="ascii")
        parsed,_=qa.read_marker(copy)
        self.assertEqual(parsed,self.mapping)
        broken=self.path/"Data/blue-hoenn-pilot.txt"
        broken.write_text(broken.read_text("ascii").replace("83,","84,",1),
                          encoding="ascii")
        with self.assertRaisesRegex(ValueError,"Marcador"):
            qa.read_marker(copy)


if __name__ == "__main__":
    unittest.main()
