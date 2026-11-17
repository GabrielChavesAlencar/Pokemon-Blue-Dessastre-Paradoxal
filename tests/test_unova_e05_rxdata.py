"""Synthetic checks: inert Unova source inspection never approves maps or rights."""
from __future__ import annotations
import io
import json
import sys
import tempfile
import unittest
import zipfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from stage import serialize
from server.ruby_marshal import RubyObject
import audit_unova_source_detail as detail
import audit_unova_u02 as metadata


class UnovaDeepSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json.loads((ROOT/"data/regions/unova-u03-areas.json").read_text("utf-8"))

    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="unova-deep-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.folder=self.root/".blue-work/unova/sources"
        self.folder.mkdir(parents=True)
        self.source=self.folder/"Pokemon_World_V18.zip"

    def sample(self, *, name=b"Nuvema Town", commands=None, corrupt=False, route=False):
        if commands is None:
            commands=[RubyObject("RPG::EventCommand",{
                "@code":201,"@parameters":[0,2,4,5]}),
                RubyObject("RPG::EventCommand",{
                "@code":355,"@parameters":[b"raise 'would break if executed'"]})]
        page=RubyObject("RPG::Event::Page",{"@list":commands})
        event=RubyObject("RPG::Event",{"@pages":[page]})
        info={
            1:RubyObject("RPG::MapInfo",{"@name":b"Route 1" if route else name}),
            2:RubyObject("RPG::MapInfo",{"@name":b"Another Town"})}
        m1=RubyObject("RPG::Map",{"@width":20,"@height":15,"@events":{1:event}})
        m2=RubyObject("RPG::Map",{"@width":16,"@height":14,"@events":{}})
        extra=("RPG::Event","RPG::Event::Page","RPG::EventCommand")
        with zipfile.ZipFile(self.source,"w") as z:
            z.writestr("World/Data/MapInfos.rxdata",serialize(info))
            z.writestr("World/Data/Tilesets.rxdata",b"Not needed for metadata-only test")
            z.writestr("World/Data/Map001.rxdata",b"corrupt" if corrupt else serialize(m1,extra))
            z.writestr("World/Data/Map002.rxdata",serialize(m2))
        return self.source

    def test_01_parses_real_marshal_without_any_installation(self):
        result=detail.inspect(self.sample(),self.catalog)
        self.assertEqual(result["all_regions_source_map_count"],2)
        row=result["maps"][0]
        self.assertEqual(row["name"],"Nuvema Town")
        self.assertEqual(row["event_count"],1)
        self.assertEqual(row["event_pages"],1)
        self.assertEqual(row["static_transfer_target_ids"],[2])
        self.assertEqual(row["untrusted_script_commands_not_executed"],1)
        self.assertIn("UNOVA_NUVEMA_TOWN",result["candidate_unova_area_keys"])
        self.assertFalse(row["candidate_confirmed_as_unova"])
        self.assertIsNone(result["confirmed_unova_map_count"])
        self.assertIsNone(row["destination_map_id"])
        self.assertFalse(result["can_install"])
        self.assertFalse(result["game_or_saves_modified"])
        self.assertFalse((self.root/"game").exists())

    def test_02_script_as_text_not_executed(self):
        report=detail.inspect(self.sample(),self.catalog)
        self.assertEqual(report["total_untrusted_script_commands_not_executed"],1)

    def test_03_route_name_alone_is_ambiguous(self):
        result=detail.inspect(self.sample(route=True),self.catalog)
        self.assertNotIn("UNOVA_ROUTE_01",result["candidate_unova_area_keys"])

    def test_04_corrupt_map_marshal_is_rejected(self):
        with self.assertRaises(ValueError):
            detail.inspect(self.sample(corrupt=True),self.catalog)

    def test_05_dynamic_transfer_is_reported_not_automapped(self):
        cmd=[RubyObject("RPG::EventCommand",{"@code":201,"@parameters":[1,1,1,1]})]
        result=detail.inspect(self.sample(commands=cmd),self.catalog)
        self.assertEqual(result["maps"][0]["dynamic_transfer_commands"],1)
        self.assertEqual(result["maps"][0]["static_transfer_target_ids"],[])

    def test_06_unresolved_static_target_reported(self):
        cmd=[RubyObject("RPG::EventCommand",{"@code":201,"@parameters":[0,999,1,1]})]
        result=detail.inspect(self.sample(commands=cmd),self.catalog)
        self.assertEqual(result["unresolved_transfer_ids"],[999])
        self.assertFalse(result["can_install"])

    def test_07_source_no_rights_even_with_name_match(self):
        result=detail.inspect(self.sample(),self.catalog)
        self.assertFalse(result["rights_verified"])
        self.assertFalse(result["native_mapinfos_verified"])
        self.assertFalse(result["game_exe_tested"])
        self.assertFalse(result["android_tested"])

    def test_08_catalog_claiming_install_is_rejected(self):
        cat=dict(self.catalog,may_install=True)
        with self.assertRaises(ValueError):
            detail.inspect(self.sample(),cat)

    def test_09_cli_missing_zip_fails_closed(self):
        buf=io.StringIO()
        with redirect_stdout(buf):
            code=detail.main(["--project",str(self.root),"--catalog",
                str(ROOT/"data/regions/unova-u03-areas.json")])
        self.assertEqual(code,2)
        self.assertFalse((self.root/"game").exists())

    def test_10_duplicate_src_zip_rejected_by_metadata_guard(self):
        self.sample()
        with zipfile.ZipFile(self.source,"a") as z:
            z.writestr("world/data/map001.rxdata",b"duplicate")
        with self.assertRaises(ValueError):
            detail.inspect(self.source,self.catalog)

if __name__=="__main__":
    unittest.main()
