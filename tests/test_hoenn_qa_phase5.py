"""QA05 synthetic test — source-informed story anchors and protected saves."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))

from build_johto_events import ruby,event_page
from pilot_hoenn import append_event
from hoenn_qa_phase5 import (
    STORY_EVENTS,GRUNT_GROUPS,STORY_KEYS,BOSS_PBS,SOURCE_SCOPE,
    verify_story_events,inventory_source,audit_generated,verify_copy,
)


class HoennQA5Tests(unittest.TestCase):
    def setUp(self):
        self.maps={}
        for mid,*_ in STORY_EVENTS:
            self.maps[mid]=ruby("RPG::Map",width=100,height=100,events={})
        for _handler,group in GRUNT_GROUPS:
            for mid,*_ in group:
                self.maps.setdefault(mid,ruby("RPG::Map",width=100,height=100,
                                              events={}))
        self.events={}
        for mid,x,y,name,handler,trigger in STORY_EVENTS:
            page=event_page(script=handler,touch=(trigger==1))
            eid=append_event(self.maps[mid],name,x,y,page)
            self.events[(mid,name)]=self.maps[mid].attrs["@events"][eid]
        for handler,group in GRUNT_GROUPS:
            for mid,x,y,version,_team in group:
                name=f"HN9_Grunt_{version}"
                page=event_page(script=f"BlueHoennPilot.{handler}({version})")
                append_event(self.maps[mid],name,x,y,page)

    def test_all_required_story_events_and_grunts_match(self):
        result=verify_story_events(self.maps)
        self.assertEqual(result["verified_story_events"],9)
        self.assertEqual(result["verified_grunt_event_bindings"],18)
        self.assertEqual(result["verified_grunts_by_group"],{
            "aqua_hideout_grunt":5,"magma_hideout_grunt":7,
            "pyre_aqua_grunt":4,"space_magma_grunt":2})
        self.assertTrue(result["groudon_auto_player_touch"])
        self.assertFalse(result["native_encounters_approved"])

    def test_groudon_invisible_story_must_auto_activate(self):
        key=(189,"HN9_Story_Groudon")
        scene=self.events[key]
        scene.attrs["@pages"][0].attrs["@trigger"]=0
        with self.assertRaisesRegex(ValueError,"trigger incorreto"):
            verify_story_events(self.maps)

    def test_donor_event_script_not_substitutable_for_blue_handler(self):
        scene=self.events[(236,"HN10_Boss_Archie")]
        scene.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"]=[
            b"pbTrainerBattle(:RSE_AQUALEADER_Archie)"
        ]
        with self.assertRaisesRegex(ValueError,"script"):
            verify_story_events(self.maps)

    def test_misplaced_kyogre_or_duplicate_story_fails(self):
        scene=self.events[(236,"HN10_Story_Kyogre")]
        scene.attrs["@x"]=24
        with self.assertRaisesRegex(ValueError,"fora da"):
            verify_story_events(self.maps)
        scene.attrs["@x"]=23
        other=event_page(script="BlueHoennPilot.seafloor_awakening",touch=True)
        append_event(self.maps[236],"HN10_Story_Kyogre",28,46,other)
        with self.assertRaisesRegex(ValueError,"duplicada"):
            verify_story_events(self.maps)

    def test_skipping_space_center_or_grunt_version_fails(self):
        scene=self.events[(81,"HN9_Boss_SpaceSteven")]
        del self.maps[81].attrs["@events"][scene.attrs["@id"]]
        with self.assertRaisesRegex(ValueError,"ausente"):
            verify_story_events(self.maps)
        # A wrong team/event mapping is never asserted as installed.

    def test_source_inventory_counts_only_name_candidates(self):
        sample={
            236:{
                1:ruby("RPG::Event",name=b"Archie",x=14,y=46,
                       pages=[event_page(script="pbTrainerBattle(:ARCHIE)")]),
                2:ruby("RPG::Event",name=b"Kyogre Event",x=23,y=46,
                       pages=[event_page(script="pbMessage('secret')")]),
                3:ruby("RPG::Event",name=b"Old Fisherman",x=4,y=7,
                       pages=[event_page(script="nil")]),
            },
            101:{1:ruby("RPG::Event",name=b"Aqua Grunt",x=3,y=4,
                         pages=[event_page(script="nil")])},
        }
        inv=inventory_source(sample)
        self.assertEqual(len(inv["source_story_candidates"]),2)
        self.assertEqual(inv["source_candidate_count_by_map"],{"236":2})
        self.assertFalse(inv["source_dialogues_or_scripts_redistributed"])
        self.assertIn(236,SOURCE_SCOPE)
        result=audit_generated(self.maps,sample)
        self.assertEqual(result["story_prerequisites"],list(STORY_KEYS))
        self.assertFalse(result["game_exe_tested"])
        self.assertFalse(result["seafloor_puzzles_native_approved"])

    def test_phase05_native_copy_requires_matching_rxdata_and_boss_teams(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)/".blue-work"
            copy=base/"hoenn-qa-fase05"
            (copy/"Data").mkdir(parents=True)
            (copy/"PBS").mkdir()
            mapping={str(i):700+i for i in range(1,200)}
            mapping.update({str(i):700+i for i in self.maps})
            manifest={
                "region":"HOENN","kind":"ISOLATED_HOENN_TEST",
                "save_profile":"Hoenn QA Fase05","maps":mapping,
                "qa5":{
                    **audit_generated(self.maps,{}),
                    "source_dialogues_or_scripts_redistributed":False,
                }
            }
            # A synthetic 199-map table with the required real source IDs.
            fixed={str(k):700+i for i,k in enumerate(
                sorted(set(map(int,mapping)))[:199])}
            # Fixed source IDs need unique, stable remapped test IDs.
            mapping={str(mid):700+i for i,mid in enumerate(
                sorted(set(map(int,mapping))))}
            self.assertEqual(len(mapping),199)
            manifest["maps"]=mapping
            (copy/"Hoenn pilot.json").write_text(json.dumps(manifest),
                                                  encoding="utf-8")
            for mid in self.maps:
                (copy/f"Data/Map{mapping[str(mid)]:03}.rxdata").write_bytes(
                    f"source:{mid}".encode())
            (copy/"PBS/trainers_hoenn_pilot.txt").write_text(
                "\n".join(BOSS_PBS)+"\n",encoding="utf-8")
            def fake_loads(data):
                mid=int(data.decode().split(":")[1])
                return self.maps[mid]
            with patch("hoenn_qa_phase1.require_private_path",side_effect=lambda p:p):
                with patch("hoenn_qa_phase5.loads",side_effect=fake_loads):
                    result=verify_copy(copy)
                    self.assertEqual(result["status"],
                                     "STORY_ANCHORS_STATICALLY_VERIFIED")
                    self.assertFalse(result["native_game_exe_approved"])
                    # Corrupt team registration; auditor refuses false positive.
                    (copy/"PBS/trainers_hoenn_pilot.txt").write_text(
                        BOSS_PBS[0],encoding="utf-8")
                    with self.assertRaisesRegex(ValueError,"Equipes PBS"):
                        verify_copy(copy)

    def test_source_inventory_does_not_expand_beyond_campaign_maps(self):
        src={999:{1:ruby("RPG::Event",name=b"Archie",x=0,y=0,
                          pages=[event_page(script="nil")])}}
        self.assertEqual(inventory_source(src)["source_story_candidates"],[])


if __name__=="__main__":
    unittest.main()
