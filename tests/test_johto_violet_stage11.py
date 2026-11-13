"""Stage 11 regression: Violet map, five new interiors, 10 two-way warps and PBS.

No Game.exe, no native sprites, no installation. Source maps/PBS synthetic.
"""
from __future__ import annotations

import copy
import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
sys.path.insert(0,str(ROOT/"tests"))
from build_johto_violet_stage11 import (
    validate_contract,room_grid,build_pbs,publish,
    NEW_IDS,EXPECTED_SYMBOLS,passage_grid
)
from build_johto_elm_lab_v1 import table_values
from test_johto_routes_stage10 import fixture,make_story_preview
from audit_johto import checksum,read_map_data
from stage import serialize
from server.ruby_marshal import RubyObject

SPEC=json.loads((ROOT/"data/regions/johto-stage11-violet.json").read_text(encoding="utf8"))


def sample(root):
    game=fixture(root)
    pbs=game/"PBS"
    old=(pbs/"trainer_types.txt").read_text(encoding="utf8")
    (pbs/"trainer_types.txt").write_text(old+
        "[BIRDKEEPER]\nName = Bird Keeper\nGender = Male\nBaseMoney = 24\n"
        "[GENTLEMAN]\nName = Gentleman\nGender = Male\nBaseMoney = 32\n",
        encoding="utf8")
    for name in ("PIDGEOTTO","SPEAROW","HOPPIP"):
        with (pbs/"pokemon.txt").open("a",encoding="utf8") as out:
            out.write(f"\n[{name}]\nName = {name}\n"
                      "Types = NORMAL\nBaseStats = 50,50,50,50,50,50\n"
                      "Abilities = OVERGROW\nMoves = 1,TACKLE,3,GROWL,5,QUICKATTACK,9,PECK\n")
    stage=make_story_preview(root)
    manifest=stage/"johto-stage.json"
    d=json.loads(manifest.read_text("utf8"))
    d["status"]="BLUE_ROUTE10_PREVIEW_ONLY_NOT_PLAYABLE"
    for entry in d["maps"]:
        if entry["destination_id"]==602:
            entry["symbol"]="JOHTO_VIOLET_CITY"
    manifest.write_text(json.dumps(d),encoding="utf8")
    info=RubyObject("RPG::MapInfo",{
        "@name":b"Johto template","@parent_id":0,"@order":210,
        "@expanded":False,"@scroll_x":0,"@scroll_y":0
    })
    (stage/"Data/MapInfos.rxdata").write_bytes(serialize({675:info}))
    return game,stage


class JohtoVioletOfflineStage11Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix="johto-violet11-")
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.game,self.stage=sample(self.root)

    def test_spec_five_interiors_and_ten_paired_transfers(self):
        validate_contract(copy.deepcopy(SPEC))
        self.assertEqual({r["id"] for r in SPEC["interiors"]}, NEW_IDS)
        self.assertEqual({r["symbol"]:r["id"] for r in SPEC["interiors"]},EXPECTED_SYMBOLS)
        self.assertEqual(len(SPEC["warps"]),10)
        self.assertEqual(len(SPEC["npcs"]),5)
        self.assertEqual(len(SPEC["trainers"]),4)

    def test_violet_zephyr_rules_are_exclusively_region_scoped(self):
        self.assertEqual(SPEC["rules"]["badge"],"ZEPHYR")
        self.assertEqual(SPEC["rules"]["source"],"BlueRegions.award")
        self.assertFalse(SPEC["rules"]["badge_in_sprout_elder"])
        self.assertEqual(SPEC["rules"]["max_awards_per_save"],1)
        self.assertFalse(SPEC["rules"]["pbs_compiled"])
        self.assertFalse(SPEC["rules"]["gameplay_playable"])

    def test_bad_master_team_length_rejected(self):
        s=copy.deepcopy(SPEC);s["trainers"][0]["master"].pop()
        with self.assertRaisesRegex(ValueError,"Time normal/Master"):
            validate_contract(s)

    def test_missing_reverse_warp_rejected(self):
        s=copy.deepcopy(SPEC)
        s["warps"][0]["reverse"]="JH_TOWER3_TO_2"
        with self.assertRaisesRegex(ValueError,"retorno"):
            validate_contract(s)

    def test_bad_badge_policy_rejected(self):
        s=copy.deepcopy(SPEC);s["rules"]["max_awards_per_save"]=2
        with self.assertRaisesRegex(ValueError,"Zephyr"):
            validate_contract(s)

    def test_private_interior_geometry_is_original_rmxp_table(self):
        flags=tuple([0]*6000)
        for kind in ("gym","tower","center"):
            raw=room_grid(kind,flags)
            dims,tiles=table_values(raw,dimension=3)
            self.assertEqual(dims,(20,16,3))
            self.assertEqual(len(tiles),20*16*3)
            self.assertNotEqual(raw, b"")

    def test_pbs_eight_normal_and_master_profiles_from_native_learnsets(self):
        files,proof=build_pbs(SPEC,self.game)
        self.assertEqual(proof["trainer_entries"],8)
        self.assertEqual(len(proof["trainer_profiles"]),8)
        self.assertEqual(sum(len(x["team"]) for x in proof["trainer_profiles"]),24)
        self.assertEqual(len(files),2)
        self.assertFalse(proof["pbs_compiled"])
        self.assertFalse(proof["trainer_ready_marker_created"])
        text=files["PBS/trainers_johto_violet.txt"].decode()
        self.assertIn("[BLUE_JOHTO_FALKNER,Falkner,1]",text)
        self.assertIn("[BLUE_JOHTO_ELDER,Li,0]",text)
        self.assertIn("[BLUE_JOHTO_SAGE,Troy,1]",text)

    def test_missing_pidgeotto_rejected(self):
        file=self.game/"PBS/pokemon.txt"
        file.write_text(file.read_text(encoding="utf8").replace(
            "[PIDGEOTTO]","[NOTPIDGEOTTO]"),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"Espécies"):
            build_pbs(SPEC,self.game)

    def test_build_stage_preserves_76_old_maps_and_adds_only_five_mapinfos(self):
        output=self.root/".blue-work/johto-staging-violet-v1"
        previous={i:checksum(self.stage/"Data"/f"Map{i:03d}.rxdata")
                  for i in range(600,677)}
        results=publish(ROOT/"data/regions/johto-stage11-violet.json",
                        self.game,self.stage,output,root=self.root)
        self.assertEqual(results["new_map_ids"],[677,678,679,680,681])
        self.assertEqual(results["existing_map_modified"],[602])
        self.assertEqual(results["warps_created"],10)
        self.assertEqual(results["npcs_created"],5)
        self.assertEqual(results["old_maps_preserved"],76)
        self.assertFalse(results["tested_in_game"])
        self.assertFalse(results["can_install"])
        self.assertTrue(all(checksum(output/"Data"/f"Map{i:03d}.rxdata")==digest
                            for i,digest in previous.items() if i!=602))
        self.assertNotEqual(checksum(output/"Data/Map602.rxdata"),previous[602])
        self.assertEqual(checksum(output/"Data/Tilesets.rxdata"),
                         checksum(self.stage/"Data/Tilesets.rxdata"))
        infos=read_map_data(output/"Data/MapInfos.rxdata")
        self.assertEqual(set(infos),{675,677,678,679,680,681})
        self.assertEqual(infos[675],read_map_data(self.stage/"Data/MapInfos.rxdata")[675])
        self.assertFalse((output/"Data/blue-johto-violet-ready.txt").exists())
        self.assertFalse(results["character_sprites_proven"])
        self.assertEqual(len(results["missing_native_character_sprites"]),4)
        with self.assertRaisesRegex(ValueError,"cópia nova"):
            publish(ROOT/"data/regions/johto-stage11-violet.json",
                    self.game,self.stage,output,root=self.root)

    def test_city_portal_cannot_land_on_own_trigger(self):
        broken=copy.deepcopy(SPEC)
        w=next(w for w in broken["warps"] if w["key"]=="JH_GYM_TO_VIOLET")
        w["arrival"]=[43,30]
        outfile=self.root/"broken.json"
        outfile.write_text(json.dumps(broken),encoding="utf8")
        with self.assertRaisesRegex(ValueError,"Chegada sobre gatilho"):
            publish(outfile,self.game,self.stage,
                    self.root/".blue-work/violated-output",root=self.root)


if __name__=="__main__":
    unittest.main()
