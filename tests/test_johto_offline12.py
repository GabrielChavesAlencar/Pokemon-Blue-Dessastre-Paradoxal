"""Stage12 offline gate regression; synthetic fixtures, NEVER Game.exe."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from package_johto_offline12 import (
    MAP_IDS,NOT_INSTALLABLE,expected_events,merge_connections,
    trainer_blocks,inspect_pbs,verify_locations,audit
)


def connections(root:Path)->Path:
    work=root/".blue-work";work.mkdir(exist_ok=True)
    result=work/"johto-connections-preview.txt"
    lines=["600,West,13,625,East,0"] + [
        f"{600+i},East,0,{601+i},West,0" for i in range(41)]
    result.write_text("\n".join(lines)+"\n",encoding="utf8")
    return result


def mock_pbs(root:Path):
    stage=root/".blue-work/stage"
    rival=root/".blue-work/rival"
    for p in (stage/"PBS",rival/"PBS"):p.mkdir(parents=True,exist_ok=True)
    types=(
        "trainer_types_johto.txt","[BLUE_JOHTO_RIVAL]\nName = Rival\n")
    (rival/"PBS"/types[0]).write_text(types[1],encoding="utf8")
    (stage/"PBS/trainer_types_johto_violet.txt").write_text(
        "[BLUE_JOHTO_FALKNER]\nName = Leader\n"
        "[BLUE_JOHTO_ELDER]\nName = Elder\n"
        "[BLUE_JOHTO_SAGE]\nName = Sage\n",encoding="utf8")
    trainer=lambda kind,name,version,count:(
        f"[{kind},{name},{version}]\n"+
        "".join("Pokemon = PIDGEY,5\n    Moves = TACKLE\n"
                for _ in range(count))+"\n")
    (rival/"PBS/trainers_johto.txt").write_text(
        "".join(trainer("BLUE_JOHTO_RIVAL","Rival",v,1) for v in range(3)),
        encoding="utf8")
    (stage/"PBS/trainers_johto_routes.txt").write_text(
        "".join(trainer("YOUNGSTER",f"Johto Test{i}",v,4 if v==1 else 2)
                for i in range(5) for v in (0,1)),encoding="utf8")
    (stage/"PBS/trainers_johto_violet.txt").write_text(
        "".join(trainer(kind,name,v,4 if v==1 else 2)
                for kind,name in (
                    ("BLUE_JOHTO_FALKNER","Falkner"),
                    ("BLUE_JOHTO_ELDER","Li"),
                    ("BLUE_JOHTO_SAGE","Nico"),
                    ("BLUE_JOHTO_SAGE","Troy")
                ) for v in (0,1)),encoding="utf8")
    encounter=""
    for n in (625,626,627):
        encounter+=f"[{n}]\nLand,21\n    60,PIDGEY,2,4\n    40,SENTRET,2,4\n"
        encounter+="LandNight,21\n    70,HOOTHOOT,2,4\n    30,RATTATA,2,4\n\n"
    (stage/"PBS/encounters_johto_routes.txt").write_text(encounter,encoding="utf8")
    return stage,rival


class JohtoOffline12Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="johto-offline12-")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.root.joinpath(".blue-work").mkdir()
        self.root.joinpath("game").mkdir()

    def test_has_82_reserved_mapids_and_noninstallable_warning(self):
        self.assertEqual(MAP_IDS,set(range(600,682)))
        self.assertIn("NAO INSTALAR",NOT_INSTALLABLE)
        self.assertIn("OFFLINE",NOT_INSTALLABLE)

    def test_event_contracts_require_sixteen_warps_and_sixteen_actions(self):
        actions,warps=expected_events(ROOT)
        self.assertEqual(len(actions),16)
        self.assertEqual(len(warps),16)
        self.assertIn("JH_STARTER_CHIKORITA",actions)
        self.assertIn("JH_ROUTE29_NPC_RIVAL",actions)
        self.assertIn("JH_VIOLET_FALKNER",actions)
        self.assertIn("JH_TOWER3_TO_2",warps)
        self.assertEqual(set(actions)&set(warps),set())

    def test_forty_two_original_connections_plus_two_inferred(self):
        raw=connections(self.root)
        merged,proof=merge_connections(raw)
        rows=merged.decode().splitlines()
        self.assertEqual(len(rows),44)
        self.assertEqual(proof["new_inferred_connections"],2)
        self.assertFalse(proof["inferred_engine_verified"])
        self.assertEqual(sum("601,East,12,625,West,0"==x for x in rows),1)

    def test_duplicate_connection_rejected(self):
        p=connections(self.root)
        p.write_text(p.read_text()+"600,West,13,625,East,0\n",encoding="utf8")
        with self.assertRaisesRegex(ValueError,"repetida"):
            merge_connections(p)

    def test_malformed_connection_rejected(self):
        p=connections(self.root)
        p.write_text(p.read_text()+"DROP TABLE users\n",encoding="utf8")
        with self.assertRaisesRegex(ValueError,"inválida"):
            merge_connections(p)

    def test_rival_and_route_and_violet_pbs_are_unique(self):
        stage,rival=mock_pbs(self.root)
        payload,proof=inspect_pbs(stage,rival)
        self.assertEqual(proof["trainer_types"],4)
        self.assertEqual(proof["trainer_profiles"],21)
        self.assertEqual(proof["wild_tables"],6)
        self.assertFalse(proof["pbs_compiled_in_engine"])
        self.assertEqual(len(payload),6)

    def test_detect_duplicate_pbs_type(self):
        stage,rival=mock_pbs(self.root)
        p=stage/"PBS/trainer_types_johto_violet.txt"
        p.write_text(p.read_text()+"[BLUE_JOHTO_RIVAL]\nName = Conflict\n")
        with self.assertRaisesRegex(ValueError,"duplicado"):
            inspect_pbs(stage,rival)

    def test_detect_invalid_team_size(self):
        stage,rival=mock_pbs(self.root)
        p=stage/"PBS/trainers_johto_violet.txt"
        text=p.read_text()
        text=text.replace("[BLUE_JOHTO_FALKNER,Falkner,1]\n",
                          "[BLUE_JOHTO_FALKNER,Falkner,1]\nPokemon = PIDGEY,5\n",1)
        p.write_text(text)
        with self.assertRaisesRegex(ValueError,"equipe errado"):
            inspect_pbs(stage,rival)

    def test_detect_bad_night_encounter_weight(self):
        stage,rival=mock_pbs(self.root)
        p=stage/"PBS/encounters_johto_routes.txt"
        p.write_text(p.read_text().replace("70,HOOTHOOT","60,HOOTHOOT",1))
        with self.assertRaisesRegex(ValueError,"100%"):
            inspect_pbs(stage,rival)

    def test_path_safety_rejects_output_outside_blue_work(self):
        stage,rival=mock_pbs(self.root)
        conn=connections(self.root)
        with self.assertRaisesRegex(ValueError,"ZIP novo"):
            verify_locations(self.root,stage,self.root/"game",rival,conn,
                             self.root/"game/overwrite.zip")

    def test_path_safety_rejects_existing_output(self):
        stage,rival=mock_pbs(self.root)
        conn=connections(self.root)
        out=self.root/".blue-work/old.zip"
        out.write_bytes(b"old")
        with self.assertRaisesRegex(ValueError,"ZIP novo"):
            verify_locations(self.root,stage,self.root/"game",rival,conn,out)

    def test_missing_stage11_manifest_fails_closed(self):
        stage,rival=mock_pbs(self.root)
        conn=connections(self.root)
        with self.assertRaisesRegex(ValueError,"Manifesto"):
            audit(stage,rival,conn,self.root/"game",root=self.root)

    def test_pbs_duplicate_section_rejected(self):
        with self.assertRaisesRegex(ValueError,"duplicada"):
            trainer_blocks(b"[RIVAL]\nName = A\n[RIVAL]\nName = B\n")


if __name__=="__main__":
    unittest.main()
