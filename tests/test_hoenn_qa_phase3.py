"""QA 03/12: pinned default encounters, original presets and conservative source events."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))

from build_johto_events import ruby,command,event_page
from hoenn_qa_phase3 import (
    parse_reference_encounters,assemble_encounters,parse_compiled_encounters,
    _safe_events,
)
from pilot_hoenn import append_event,LAND_ENCOUNTERS,CAVE_ENCOUNTERS,SOURCE_MAPS


class HoennQA3Tests(unittest.TestCase):
    def test_default_and_special_swarms_ignored(self):
        profiles,report=parse_reference_encounters(
            "[101] # Rota 101\n"
            "Land,11\n    70,WURMPLE,2,3\n    30,POOCHYENA,2\n"
            "[101,1] # SURSKIT SWARM\nLand,11\n    150,SURSKIT,3\n"
            "[83]\nWater,2\n    100,MAGIKARP,5,35\n",
            {101,83},
        )
        self.assertEqual(profiles[101]["Land"]["rows"],
                         [(70,"WURMPLE",2,3),(30,"POOCHYENA",2,2)])
        self.assertEqual(profiles[83]["Water"]["rows"],
                         [(100,"MAGIKARP",5,35)])
        self.assertEqual(report["alternate_profiles_not_activated"],
                         [{"source_map_id":101,"version":1}])
        self.assertFalse(report["normalized_weights"])

    def test_200_and_95_percent_source_weights_are_normalized_deterministically(self):
        profiles,report=parse_reference_encounters(
            "[250]\nCave,5\n    75,GOLBAT,36\n    75,HARIYAMA,38\n"
            "    50,ZUBAT,35\n"
            "[132]\nLand,11\n    50,ROSELIA,13\n    45,MARILL,13\n",
            {132,250})
        self.assertEqual(sum(row[0] for row in profiles[250]["Cave"]["rows"]),100)
        self.assertEqual(sum(row[0] for row in profiles[132]["Land"]["rows"]),100)
        self.assertEqual([(n["map_id"],n["source_total"]) for n in
                          report["normalized_weights"]],[(250,200),(132,95)])
        self.assertEqual(parse_reference_encounters(
            "[250]\nCave,5\n    75,GOLBAT,36\n    75,HARIYAMA,38\n    50,ZUBAT,35\n",
            {250})[0][250]["Cave"]["rows"],profiles[250]["Cave"]["rows"])

    def test_malformed_or_duplicate_source_encounters_are_blocked(self):
        sources=[
            "[101]\nLand,11\n    0,POOCHYENA,3\n",
            "[101]\nLand,11\n    100,UNKNOWN BAD,3\n",
            "[101]\nUnknown,4\n    100,ZIGZAGOON,3\n",
            "[101]\nLand,11\n    100,ZIGZAGOON,12,4\n",
            "[101]\nLand,11\n    100,ZIGZAGOON,3\nLand,11\n    100,ZIGZAGOON,3\n",
            "[101]\nLand,11\n    100,ZIGZAGOON,3\n[101]\nWater,2\n    100,MAGIKARP,5\n",
        ]
        for sample in sources:
            with self.subTest(sample=sample):
                with self.assertRaises(ValueError):
                    parse_reference_encounters(sample,{101})

    def test_blue_land_cave_presets_win_and_new_methods_are_added(self):
        profiles,report=parse_reference_encounters(
            "[101]\nLand,11\n    100,PIKACHU,5\n"
            "Water,2\n    100,MARILL,5,35\n"
            "OldRod\n    70,MAGIKARP,5,10\n    30,GOLDEEN,5,10\n"
            "[250]\nCave,5\n    100,GOLBAT,38,40\n"
            "RockSmash,11\n    100,GEODUDE,20,40\n", {101,250})
        mapping={101:700,250:701}
        original_land={101:((100,"ZIGZAGOON",2,3),)}
        original_cave={250:((100,"ZUBAT",30,32),)}
        encoded,merged=assemble_encounters(profiles,mapping,original_land,original_cave)
        body=encoded.decode()
        self.assertIn("[700]\nLand,21\n    100,ZIGZAGOON,2,3\n",body)
        self.assertIn("[701]\nCave,5\n    100,ZUBAT,30,32\n",body)
        self.assertNotIn("PIKACHU",body)
        self.assertIn("Water,2\n    100,MARILL,5,35",body)
        self.assertIn("RockSmash,11\n    100,GEODUDE,20,40",body)
        self.assertEqual(merged["authored_method_profiles_preserved"],2)
        self.assertEqual(merged["new_default_profiles_installed"],3)
        self.assertEqual(parse_compiled_encounters(body,{700,701}),
                         {700:{"Land":1,"Water":1,"OldRod":2},
                          701:{"Cave":1,"RockSmash":1}})

    def test_duplicate_output_mapids_and_bad_authored_weights_refused(self):
        with self.assertRaisesRegex(ValueError,"duplicado"):
            assemble_encounters({}, {101:700,102:700}, {},{})
        with self.assertRaisesRegex(ValueError,"100%"):
            assemble_encounters({}, {101:700},{101:((70,"ZIGZAGOON",2,3),)},{})

    def test_merged_pbs_rejects_duplicate_map_or_method_and_wrong_weights(self):
        bad=[
            "[700]\nLand,11\n    50,ZIGZAGOON,2,3\n",
            "[700]\nWater,2\n    100,MARILL,5,30\n[700]\nCave,5\n    100,ZUBAT,20,30\n",
            "[700]\nLand,11\n    100,ZIGZAGOON,2,3\nLand,11\n    100,POOCHYENA,2,3\n",
            "[700]\nWater,2\n    100,MARILL,35,5\n",
        ]
        for b in bad:
            with self.subTest(b=b):
                with self.assertRaises(ValueError):
                    parse_compiled_encounters(b,{700})

    @staticmethod
    def synthetic_event(name,x,y,cmds=(),has_condition=False):
        page=event_page(script="nil")
        page.attrs["@list"]=list(cmds)
        if has_condition:
            page.attrs["@condition"].attrs["@switch1_valid"]=True
        return ruby("RPG::Event",id=1,name=name.encode(),x=x,y=y,pages=[page])

    def test_only_unconditional_unoccupied_pinned_pickups_reauthored(self):
        source_events={
            101:{
                1:self.synthetic_event("Item",4,5,(
                    command(355,b"pbItemBall(:POTION)"),)),
                2:self.synthetic_event("HiddenItem",7,8,(
                    command(355,b"pbHiddenItemBall(:RARECANDY)"),)),
            },
        }
        donor={101:ruby("RPG::Map",width=30,height=30,events=source_events[101])}
        authored={101:ruby("RPG::Map",width=30,height=30,events={})}
        report=_safe_events(source_events,donor,authored,append_event,
                            event_page,command,ruby)
        self.assertEqual(report["source_event_counts"]["source_items_newly_authored"],2)
        self.assertEqual(len(authored[101].attrs["@events"]),2)
        names=[ev.attrs["@name"] for ev in authored[101].attrs["@events"].values()]
        self.assertIn(b"HN_QA3_Pickup_101_4_5",names)
        for ev in authored[101].attrs["@events"].values():
            self.assertEqual(len(ev.attrs["@pages"]),2)
            self.assertEqual(ev.attrs["@pages"][0].attrs["@list"][0].attrs["@code"],355)
            self.assertTrue(ev.attrs["@pages"][1].attrs["@condition"].attrs["@self_switch_valid"])

    def test_do_not_duplicate_existing_event_or_conditional_item(self):
        source={
            101:{
                1:self.synthetic_event("Item",4,5,(command(355,b"pbItemBall(:POTION)"),)),
                2:self.synthetic_event("Item",9,9,(command(355,b"pbItemBall(:MASTERBALL)"),),True),
            },
        }
        donor={101:ruby("RPG::Map",width=30,height=30,events=source[101])}
        authored={101:ruby("RPG::Map",width=30,height=30,events={
            1:self.synthetic_event("HN_Existing",4,5)})}
        report=_safe_events(source,donor,authored,append_event,
                            event_page,command,ruby)
        self.assertEqual(report["source_event_counts"]["position_already_authored"],1)
        self.assertEqual(report["source_event_counts"]["items_need_manual_review"],1)
        self.assertEqual(len(authored[101].attrs["@events"]),1)

    def test_unknown_script_item_without_item_id_needs_manual_review(self):
        events={101:{
            1:self.synthetic_event("HiddenItem",8,8,
                                   (command(355,b"pbCommonEvent(99)"),))}}
        donor={101:ruby("RPG::Map",width=40,height=40,events=events[101])}
        authored={101:ruby("RPG::Map",width=40,height=40,events={})}
        report=_safe_events(events,donor,authored,append_event,event_page,command,ruby)
        self.assertEqual(report["source_event_counts"]["items_need_manual_review"],1)
        self.assertEqual(len(authored[101].attrs["@events"]),0)

    def test_named_trainer_sign_and_dialogue_are_catalogued_but_not_copied(self):
        src={101:{
            1:self.synthetic_event("Youngster Ben",1,2),
            2:self.synthetic_event("Route Sign",3,4),
            3:self.synthetic_event("Old Lady",5,6,(command(101,b"Talk"),))
        }}
        donor={101:ruby("RPG::Map",width=20,height=20,events=src[101])}
        out={101:ruby("RPG::Map",width=20,height=20,events={})}
        audit=_safe_events(src,donor,out,append_event,event_page,command,ruby)
        counts=audit["source_event_counts"]
        self.assertEqual(counts["pending_trainer"],1)
        self.assertEqual(counts["pending_sign"],1)
        self.assertEqual(counts["pending_npc_or_dialog"],1)
        self.assertEqual(len(audit["unimplemented_source_event_candidates"]),3)
        self.assertEqual(out[101].attrs["@events"],{})
        self.assertFalse(audit["trainer_npc_sign_cleared_for_playable"])

    def test_pilot_has_199_maps_and_authoring_presets_are_not_overwritten(self):
        self.assertEqual(len(SOURCE_MAPS),199)
        data,counts=assemble_encounters({}, {mid:700+i for i,mid in enumerate(SOURCE_MAPS)},
                                        LAND_ENCOUNTERS,CAVE_ENCOUNTERS)
        self.assertGreater(counts["authored_method_profiles_preserved"],10)
        self.assertEqual(counts["new_default_profiles_installed"],0)
        self.assertTrue(data.startswith(b"["))


if __name__=="__main__":
    unittest.main()
