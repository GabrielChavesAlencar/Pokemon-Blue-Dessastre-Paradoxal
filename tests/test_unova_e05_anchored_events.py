"""E05: synthetic tests of inert per-map event counting with safe fallback."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from stage import serialize
from server.ruby_marshal import RubyObject
import audit_unova_e05_anchored_events as ev


def fixture_map(commands=None):
    if commands is None:
        commands=[
            RubyObject("RPG::EventCommand",{"@code":101,"@parameters":[b"first line"]}),
            RubyObject("RPG::EventCommand",{"@code":401,"@parameters":[b"text"]}),
            RubyObject("RPG::EventCommand",{"@code":201,"@parameters":[0,3,1,2]}),
            RubyObject("RPG::EventCommand",{"@code":355,"@parameters":[b"raise 'never called'"]}),
        ]
    page=RubyObject("RPG::Event::Page",{"@list":commands})
    event=RubyObject("RPG::Event",{"@name":b"Test NPC","@pages":[page]})
    game_map=RubyObject("RPG::Map",{"@width":30,"@height":24,"@events":{1:event}})
    return serialize(game_map,{"RPG::Event","RPG::Event::Page","RPG::EventCommand"})


class EventAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads((ROOT/"data/regions/unova-u03-areas.json").read_text("utf-8"))

    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="unova-events-")
        self.addCleanup(tmp.cleanup)
        self.root=Path(tmp.name)
        self.src=self.root/".blue-work/unova/sources"
        self.src.mkdir(parents=True)
        self.zip=self.src/"Pokemon_World_V18.zip"

    def create(self,corrupt=False,unova=True):
        records={1:("Unova" if unova else "Johto",0),2:("Nuvema Town",1),
                 3:("Route 1",1),4:("Pallet Town",0)}
        infos={k:RubyObject("RPG::MapInfo",{"@name":name.encode(),"@parent_id":parent})
               for k,(name,parent) in records.items()}
        with zipfile.ZipFile(self.zip,"w") as z:
            z.writestr("World/Data/MapInfos.rxdata",serialize(infos))
            z.writestr("World/Data/Tilesets.rxdata",b"not loaded")
            z.writestr("World/Data/Map001.rxdata",fixture_map())
            z.writestr("World/Data/Map002.rxdata",b"broken-map" if corrupt else fixture_map())
            z.writestr("World/Data/Map003.rxdata",fixture_map())
            z.writestr("World/Data/Map004.rxdata",b"not parsed")
        return self.zip

    def test_01_event_counts_and_transfer(self):
        result=ev.inspect_one_map(fixture_map(),2,"Nuvema Town",["Nuvema Town","Unova"])
        self.assertEqual(result["event_containers"],1)
        self.assertEqual(result["event_pages"],1)
        self.assertEqual(result["command_counts"]["message_line"],1)
        self.assertEqual(result["command_counts"]["ruby_script"],1)
        self.assertEqual(result["static_transfer_target_source_ids"],[3])
        self.assertEqual(result["event_names_first_30"],["Test NPC"])
        self.assertFalse(result["events_gameplay_verified"])
        self.assertFalse(result["source_rights_verified"])

    def test_02_untrusted_script_text_never_executed(self):
        result=ev.inspect_one_map(fixture_map(),2,"Map",["Map"])
        self.assertEqual(result["command_counts"]["ruby_script"],1)
        self.assertFalse(result["game_exe_tested"])

    def test_03_one_bad_map_does_not_erase_good_maps(self):
        report=ev.inspect(self.create(corrupt=True),self.catalog)
        self.assertEqual(report["unova_parent_context_map_files"],3)
        self.assertEqual(report["parsed_map_count"],2)
        self.assertEqual(report["unparsed_map_count"],1)
        self.assertEqual(report["total_event_containers_parsed"],2)
        bad=next(x for x in report["maps"] if x["source_map_id"]==2)
        self.assertEqual(bad["parse_status"],"BLOCKED_MAP_PARSER_INCOMPATIBLE")
        self.assertIsNone(bad["destination_map_id"])
        self.assertFalse(report["can_install"])

    def test_04_no_unova_parent_no_events_from_foreign_branch(self):
        report=ev.inspect(self.create(unova=False),self.catalog)
        self.assertEqual(report["unova_parent_context_map_files"],0)
        self.assertEqual(report["total_event_containers_parsed"],0)

    def test_05_invalid_catalog_state_block(self):
        self.create()
        bad=dict(self.catalog,state="PLAYABLE")
        with self.assertRaises(ValueError):
            ev.inspect(self.zip,bad)

    def test_06_no_fake_installer_or_windows_qa(self):
        report=ev.inspect(self.create(),self.catalog)
        self.assertFalse(report["gameplay_approved"])
        self.assertFalse(report["native_mapids_audited"])
        self.assertFalse(report["copyright_rights_verified"])
        self.assertFalse(report["game_exe_tested"])
        self.assertFalse(report["android_tested"])

    def test_07_no_write_to_game_from_inspect(self):
        ev.inspect(self.create(),self.catalog)
        self.assertFalse((self.root/"game").exists())
        self.assertFalse((self.root/"saves").exists())

    def test_08_static_transfer_with_dynamic_pointers_not_counted_as_native(self):
        cmd=[RubyObject("RPG::EventCommand",{"@code":201,"@parameters":[1,7,7]})]
        data=ev.inspect_one_map(fixture_map(cmd),2,"Name",["Name"])
        self.assertEqual(data["command_counts"]["transfer"],1)
        self.assertEqual(data["static_transfer_target_source_ids"],[])

    def test_09_zero_event_map_is_allowed_and_not_playable(self):
        game_map=RubyObject("RPG::Map",{"@width":10,"@height":10,"@events":{}})
        parsed=ev.inspect_one_map(serialize(game_map),4,"Empty",["Empty"])
        self.assertEqual(parsed["event_containers"],0)
        self.assertFalse(parsed["installed"])

    def test_10_source_map_name_not_confirmed_by_text(self):
        report=ev.inspect(self.create(),self.catalog)
        self.assertTrue(report["region_context_assumed_from_parent_name_only"])
        self.assertFalse(report["gameplay_approved"])
        self.assertTrue(all(x["destination_map_id"] is None for x in report["maps"]))

if __name__=="__main__":
    unittest.main()
