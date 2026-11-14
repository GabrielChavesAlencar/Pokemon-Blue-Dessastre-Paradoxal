"""Hoenn QA04 — conservative source obstacle recognition and isolated-copy guards."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))

from build_johto_events import ruby,command,event_page
from hoenn_qa_phase4 import (
    classify_obstacle,categorize_source_events,
    install_simple_obstacles,verify_copy,
    REGIONAL_BADGES, UNDERWATER, WATERFALL_ENTRANCE,
)


def source_event(event_id,name,x,y,script=None,conditional=False,multi=False):
    page=event_page(script="nil")
    page.attrs["@list"]=[command(355,(script or "nil").encode("ascii"))]
    if conditional:
        page.attrs["@condition"].attrs["@switch1_valid"]=True
    pages=[page]
    if multi:pages.append(event_page(script="nil"))
    return ruby("RPG::Event",id=event_id,name=name.encode("ascii"),
                x=x,y=y,pages=pages)


class FieldMoveQA4Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base=Path(self.tmp.name)
        self.game=self.base/"game"
        self.donor={250:ruby("RPG::Map",width=25,height=30,events={})}
        self.authored={250:ruby("RPG::Map",width=25,height=30,events={})}

    def events(self,*events):
        self.donor[250].attrs["@events"]={v.attrs["@id"]:v for v in events}
        return {250:self.donor[250].attrs["@events"]}

    def sprites(self,*names):
        for n in names:
            p=self.game/"Graphics/Characters"/f"{n}.png"
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(b"\x89PNG\r\n\x1a\nfixture")

    def test_mapping_all_field_moves_to_hoenn_only_badges(self):
        self.assertEqual(REGIONAL_BADGES,{
            "CUT":"STONE","FLASH":"KNUCKLE","ROCKSMASH":"DYNAMO",
            "STRENGTH":"HEAT","SURF":"BALANCE","DIVE":"MIND",
            "WATERFALL":"RAIN",
        })
        self.assertEqual(WATERFALL_ENTRANCE,(91,322))
        self.assertIn(255,UNDERWATER)
        self.assertNotIn(83,UNDERWATER)

    def test_exact_rock_and_strength_events_are_recognized(self):
        self.assertEqual(classify_obstacle("RockSmashRock"),"rock_smash")
        self.assertEqual(classify_obstacle("StrengthBoulder"),"strength")
        self.assertEqual(classify_obstacle("Thin Ice"),"ice")
        self.assertEqual(classify_obstacle("PB", "pbRockSmash()"),"rock_smash")
        self.assertEqual(classify_obstacle("Current", "pbDive()"),"dive")
        self.assertIsNone(classify_obstacle("Nurse Joy"))
        self.assertEqual(classify_obstacle("Waterfall Sign"),"manual_field_review")

    def test_pinned_event_inventory_counts_without_executing_scripts(self):
        events=self.events(
            source_event(1,"RockSmashRock",3,4,"pbRockSmash"),
            source_event(2,"StrengthBoulder",5,6,"pbStrength"),
            source_event(3,"Thin Ice",7,8),
            source_event(4,"Nurse",9,10),
        )
        result=categorize_source_events(events,self.donor)
        self.assertEqual(result["source_obstacles_by_type"],{
            "ice":1,"rock_smash":1,"strength":1,
        })
        self.assertFalse(result["source_ruby_scripts_executed"])
        self.assertEqual(len(result["source_obstacle_candidates"]),3)

    def test_obstacles_use_native_sprites_and_only_author_owned_scripts(self):
        self.sprites("Object_Rock","Object_Boulder")
        events=self.events(
            source_event(1,"RockSmashRock",3,4,"pbRockSmash"),
            source_event(2,"StrengthBoulder",5,6,"pbStrength"),
        )
        report=install_simple_obstacles(events,self.donor,self.authored,self.game)
        self.assertEqual(report["new_safe_obstacles_by_type"],{
            "rock_smash":1,"strength":1,
        })
        self.assertEqual(len(report["new_safe_obstacles"]),2)
        generated=list(self.authored[250].attrs["@events"].values())
        self.assertEqual(len(generated),2)
        rock,stone=generated
        rcmd=rock.attrs["@pages"][0].attrs["@list"][0]
        scmd=stone.attrs["@pages"][0].attrs["@list"][0]
        self.assertIn(b"BlueHoennPilot.rock_smash_obstacle(",rcmd.attrs["@parameters"][0])
        self.assertIn(b"BlueHoennPilot.strength_boulder(",scmd.attrs["@parameters"][0])
        self.assertEqual(len(rock.attrs["@pages"]),2)
        self.assertEqual(len(stone.attrs["@pages"]),1)
        self.assertTrue(rock.attrs["@pages"][1].attrs["@condition"].attrs["@self_switch_valid"])
        self.assertFalse(report["native_field_move_handlers_untested"] is False)

    def test_known_event_overlap_skips_obstacle_without_removing_existing(self):
        self.sprites("Object_Rock")
        original=self.events(source_event(1,"RockSmashRock",3,4))
        self.authored[250].attrs["@events"]={1:source_event(1,"HN_Trainer",3,4)}
        report=install_simple_obstacles(original,self.donor,self.authored,self.game)
        self.assertEqual(len(report["new_safe_obstacles"]),0)
        self.assertEqual(report["source_obstacles_needing_review"][0][-1],"already_authored")
        self.assertEqual(len(self.authored[250].attrs["@events"]),1)

    def test_missing_sprite_conditional_and_multi_page_skip(self):
        events=self.events(
            source_event(1,"StrengthBoulder",3,4,conditional=True),
            source_event(2,"RockSmashRock",5,6,multi=True),
            source_event(3,"RockSmashRock",7,8),
        )
        result=install_simple_obstacles(events,self.donor,self.authored,self.game)
        self.assertEqual(len(result["new_safe_obstacles"]),0)
        reasons={x[-1] for x in result["source_obstacles_needing_review"]}
        self.assertEqual(reasons,{"conditional_original","ambiguous_or_multipage",
                                  "no_native_sprite"})

    def test_script_only_identifiers_not_automatically_reauthored(self):
        self.sprites("Object_Rock","Object_Boulder")
        events=self.events(source_event(1,"Gym Controller",3,4,"pbRockSmash"),
                           source_event(2,"Stone Room",4,5,"pbStrength"))
        result=install_simple_obstacles(events,self.donor,self.authored,self.game)
        self.assertFalse(result["new_safe_obstacles"])
        self.assertTrue(all(x[-1]=="not_exact_obstacle_name"
                            for x in result["source_obstacles_needing_review"]))

    def test_copy_report_has_no_false_native_approval(self):
        with tempfile.TemporaryDirectory() as work:
            base=Path(work)/".blue-work"
            folder=base/"hoenn-qa-fase04"
            folder.mkdir(parents=True)
            (folder/"Hoenn pilot.json").write_text(json.dumps({
                "kind":"ISOLATED_HOENN_TEST",
                "maps":{str(i):700+i for i in range(199)},
                "qa4":{
                    "source_obstacles_by_type":{"strength":1},
                    "source_obstacle_candidates":[{"source_map_id":250}],
                    "new_safe_obstacles":[],
                    "source_obstacles_needing_review":[],
                    "native_field_move_handlers_untested":True,
                    "source_ruby_scripts_executed":False,
                },
            }),encoding="utf-8")
            with patch("hoenn_qa_phase1.require_private_path",side_effect=lambda p:p):
                report=verify_copy(folder)
                self.assertEqual(report["status"],"FIELD_OBSTACLE_CONTRACT_PREPARED")
                self.assertFalse(report["game_exe_tested"])
                self.assertFalse(report["puzzles_and_ice_floor_approved"])
                data=json.loads((folder/"Hoenn pilot.json").read_text("utf-8"))
                data["qa4"]["native_field_move_handlers_untested"]=False
                (folder/"Hoenn pilot.json").write_text(json.dumps(data),encoding="utf-8")
                with self.assertRaises(ValueError):
                    verify_copy(folder)


if __name__=="__main__":
    unittest.main()
