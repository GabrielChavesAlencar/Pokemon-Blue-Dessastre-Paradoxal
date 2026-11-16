"""Map Studio: real RMXP tile mapping, safety, rollback, direct main API."""
from __future__ import annotations

import json
import struct
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "scripts/regions"))

from server.ruby_marshal import RubyData, loads
from build_johto_elm_lab_v1 import table_values
from stage import serialize
from test_johto_bedroom_hgss import fixtures
from johto_map_editor import (details, save_changes, publish, Session,
                              EditorError, catalog, sha)
import johto_map_editor as editor
import johto_map_patches as patcher
import johto_qa


class JohtoMapStudioTests(unittest.TestCase):
    def setUp(self):
        folder=tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root=Path(folder.name)
        self.game=self.root/"game"
        (self.game/"Data").mkdir(parents=True)
        (self.game/"Saves").mkdir()
        (self.root/".blue-backups").mkdir()
        (self.root/"data/regions/johto-map-edits").mkdir(parents=True)
        room, home, tilesets=fixtures()
        self.room,self.home,self.tilesets=room,home,tilesets
        self.write("Game.exe",b"native game stays untouched")
        self.write("Saves/File.rxdata",b"the user's private save")
        self.write("Data/Map674.rxdata",serialize(room,johto_qa.EVENT_CLASSES))
        self.write("Data/Map675.rxdata",serialize(home,johto_qa.EVENT_CLASSES))
        self.write("Data/Tilesets.rxdata",serialize(tilesets))
        self.write("Data/Map600.rxdata",b"unrelated map left untouched")
        self.original=self.game.joinpath("Data/Map674.rxdata").read_bytes()

    def write(self,relative,data):
        path=self.game/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

    def test_save_writes_native_map_and_json_patch_but_not_events_or_saves(self):
        before=details(self.root,self.game,674)
        self.assertEqual(before["width"],14)
        self.assertEqual(before["height"],11)
        original_events=loads(self.original).attrs["@events"]
        operations=[{"x":4,"y":5,"z":1,"from":0,"to":400},
                    {"x":5,"y":5,"z":1,"from":0,"to":401}]
        report=save_changes(self.root,self.game,{
            "map_id":674,"map_hash":before["map_hash"],"patch_hash":None,
            "changes":operations})
        self.assertTrue(report["saved"])
        self.assertEqual(report["count"],2)
        self.assertTrue(Path(report["backup"]).exists())
        map_updated=loads((self.game/"Data/Map674.rxdata").read_bytes())
        (shape,cells)=table_values(map_updated.attrs["@data"].data,3)
        self.assertEqual(shape,(14,11,3))
        self.assertEqual(cells[4+14*(5+11)],400)
        self.assertEqual(cells[5+14*(5+11)],401)
        self.assertEqual(map_updated.attrs["@events"],original_events)
        self.assertEqual((self.game/"Saves/File.rxdata").read_bytes(),
                         b"the user's private save")
        self.assertEqual((self.game/"Data/Map600.rxdata").read_bytes(),
                         b"unrelated map left untouched")
        p=patcher.read_patch(self.root,674)
        self.assertEqual(len(p["edits"]),2)
        self.assertEqual(p["tileset"],"BLUE_JOHTO_OPENING_INSIDE")

        # This published patch also reproduces the exact cells in a fresh
        # staged Johto map without copying private RXDATA into the repository.
        blank,_,sets=fixtures()
        self.assertEqual(patcher.apply_patch(blank,sets,674,p),2)
        self.assertEqual(patcher.apply_patch(blank,sets,674,p),0)

        next_map=details(self.root,self.game,674)
        undo=save_changes(self.root,self.game,{
            "map_id":674,"map_hash":next_map["map_hash"],
            "patch_hash":next_map["patch_hash"],
            "changes":[{"x":4,"y":5,"z":1,"from":400,"to":0}]})
        self.assertTrue(undo["saved"])
        self.assertEqual(len(patcher.read_patch(self.root,674)["edits"]),1)

    def test_invalid_foreign_map_and_stale_write_are_rejected(self):
        with self.assertRaisesRegex(ValueError,"600"):
            patcher.map_id(700)
        current=details(self.root,self.game,674)
        with self.assertRaisesRegex(EditorError,"Mapa alterado"):
            save_changes(self.root,self.game,{
                "map_id":674,"map_hash":"0"*64,"patch_hash":None,
                "changes":[{"x":1,"y":2,"z":0,"from":0,"to":399}]})
        self.assertEqual((self.game/"Data/Map674.rxdata").read_bytes(),self.original)
        self.assertEqual(catalog(self.game)[0]["id"],600)

    def test_solid_tile_cannot_cover_event_or_spawn(self):
        # Mark tile 401 impassable; painting it under the staircase event
        # must not succeed or mutate the original RXDATA.
        from server.ruby_marshal import RubyData
        original=self.tilesets[1].attrs["@passages"].data
        raw=bytearray(original)
        struct.pack_into("<H",raw,20+401*2,15)
        self.tilesets[1].attrs["@passages"]=RubyData("Table",bytes(raw))
        self.write("Data/Tilesets.rxdata",serialize(self.tilesets))
        d=details(self.root,self.game,674)
        with self.assertRaisesRegex(ValueError,"bloquearia spawn/evento"):
            save_changes(self.root,self.game,{
                "map_id":674,"map_hash":d["map_hash"],"patch_hash":None,
                "changes":[{"x":9,"y":8,"z":2,"from":0,"to":401}]})
        self.assertEqual((self.game/"Data/Map674.rxdata").read_bytes(),self.original)

    def test_sync_applies_main_patch_to_existing_game_without_saves(self):
        before=details(self.root,self.game,674)
        save_changes(self.root,self.game,{
            "map_id":674,"map_hash":before["map_hash"],"patch_hash":None,
            "changes":[{"x":4,"y":5,"z":1,"from":0,"to":400}]})
        # Simulate a previous install (old map) receiving the JSON patch
        # through Blue-Story's source update.
        self.write("Data/Map674.rxdata",self.original)
        self.write("Data/blue-johto-main-preview.json",
                   json.dumps({"region":"JOHTO","file_hashes":{
                        "Data/Map674.rxdata":sha(self.original)}}).encode())
        result=patcher.sync_installed(self.root,self.game)
        self.assertTrue(result["changed"])
        self.assertEqual(result["maps"],[674])
        self.assertEqual((self.game/"Saves/File.rxdata").read_bytes(),
                         b"the user's private save")
        self.assertEqual((self.game/"Data/Map675.rxdata").read_bytes(),
                         serialize(self.home,johto_qa.EVENT_CLASSES))
        self.assertFalse(patcher.sync_installed(self.root,self.game)["changed"])

    def test_publish_uses_main_branch_and_never_sends_rpdata_or_saves(self):
        before=details(self.root,self.game,674)
        result=save_changes(self.root,self.game,{
            "map_id":674,"map_hash":before["map_hash"],"patch_hash":None,
            "changes":[{"x":3,"y":6,"z":1,"from":0,"to":405}]})
        session=Session(self.root,self.game)
        session.publish_baseline[674]={"sha":None,"in_sync":True}
        with patch.object(editor,"github_authenticated",return_value=True),\
             patch.object(editor,"remote",return_value={"sha":None,"in_sync":True}),\
             patch.object(editor,"_gh",return_value={
                "commit":{"html_url":"https://github.com/example/commit/test"},
                "content":{"sha":"abc123"}}) as client:
            published=publish(session,674,None,result["patch_hash"])
            self.assertTrue(published["published"])
            args,kwargs=client.call_args
            body=json.loads(kwargs["body"])
            self.assertEqual(body["branch"],"main")
            self.assertIn("johto-map-edits/Map674.json",args[1][-3])
            import base64
            uploaded=base64.b64decode(body["content"])
            self.assertIn(b'"map_id": 674',uploaded)
            self.assertNotIn(b"private save",uploaded)
            self.assertFalse(uploaded.startswith(b"\x04\x08"))
        self.assertEqual(session.publish_baseline[674]["sha"],"abc123")

    def test_first_publish_without_remote_file_needs_no_manual_verification(self):
        before=details(self.root,self.game,674)
        saved=save_changes(self.root,self.game,{
            "map_id":674,"map_hash":before["map_hash"],"patch_hash":None,
            "changes":[{"x":3,"y":6,"z":1,"from":0,"to":405}]})
        session=Session(self.root,self.game)
        # The UI did not request /api/remote beforehand (e.g. offline at startup).
        with patch.object(editor,"github_authenticated",return_value=True),\
             patch.object(editor,"remote",return_value={
                 "exists":False,"sha":None,"in_sync":True}),\
             patch.object(editor,"_gh",return_value={
                 "commit":{"html_url":"https://github.com/example/commit/new"},
                 "content":{"sha":"new"}}):
            result=publish(session,674,None,saved["patch_hash"])
        self.assertTrue(result["published"])
        self.assertEqual(result["branch"],"main")
        self.assertEqual(session.publish_baseline[674]["sha"],"new")

    def test_real_remote_conflict_never_overwrites_main(self):
        before=details(self.root,self.game,674)
        saved=save_changes(self.root,self.game,{
            "map_id":674,"map_hash":before["map_hash"],"patch_hash":None,
            "changes":[{"x":3,"y":6,"z":1,"from":0,"to":405}]})
        session=Session(self.root,self.game)
        session.publish_baseline[674]={"sha":"old","in_sync":True}
        with patch.object(editor,"github_authenticated",return_value=True),\
             patch.object(editor,"remote",return_value={
                 "exists":True,"sha":"new","in_sync":False}),\
             patch.object(editor,"_gh") as client:
            with self.assertRaisesRegex(EditorError,"Outro commit"):
                publish(session,674,"old",saved["patch_hash"])
            client.assert_not_called()

    def test_unauthenticated_publishing_requests_browser_authorization(self):
        before=details(self.root,self.game,674)
        saved=save_changes(self.root,self.game,{
            "map_id":674,"map_hash":before["map_hash"],"patch_hash":None,
            "changes":[{"x":3,"y":6,"z":1,"from":0,"to":405}]})
        session=Session(self.root,self.game)
        with patch.object(editor,"github_authenticated",return_value=False),\
             patch.object(editor,"remote") as remote:
            with self.assertRaisesRegex(EditorError,"GITHUB_AUTH_REQUIRED") as ctx:
                publish(session,674,None,saved["patch_hash"])
            self.assertEqual(ctx.exception.code,401)
            remote.assert_not_called()

    def test_move_staircase_event_and_edit_return_warp_without_touching_scripts(self):
        before=details(self.root,self.game,674)
        stair=next(e for e in before["events"] if e["name"]=="JH_HOME2F_TO_1F")
        event_change={
            "id":stair["id"],"name":stair["name"],
            "before":[stair["x"],stair["y"]],"after":[4,4],
            "warp_before":[stair["warp"]["map"],stair["warp"]["x"],stair["warp"]["y"]],
            "warp_after":[stair["warp"]["map"],stair["warp"]["x"],stair["warp"]["y"]],
        }
        result=save_changes(self.root,self.game,{
            "map_id":674,"map_hash":before["map_hash"],"patch_hash":None,
            "changes":[],"event_changes":[event_change]})
        self.assertEqual(result["count"],1)
        updated=details(self.root,self.game,674)
        moved=next(e for e in updated["events"] if e["name"]=="JH_HOME2F_TO_1F")
        self.assertEqual((moved["x"],moved["y"]),(4,4))
        patch674=patcher.read_patch(self.root,674)
        self.assertEqual(len(patch674["events"]),1)
        self.assertEqual(patch674["events"][0]["before"],[9,8])

        # The downstairs event may use a sound and fade before code 201;
        # only the transfer coordinates change, never the rest of its script.
        downstairs=details(self.root,self.game,675)
        back=next(e for e in downstairs["events"] if e["name"]=="JH_HOME1F_TO_2F")
        move={
            "id":back["id"],"name":back["name"],
            "before":[back["x"],back["y"]],
            "after":[back["x"],back["y"]],
            "warp_before":[674,9,7],"warp_after":[674,4,5]}
        report=save_changes(self.root,self.game,{
            "map_id":675,"map_hash":downstairs["map_hash"],"patch_hash":None,
            "changes":[],"event_changes":[move]})
        self.assertEqual(report["count"],1)
        changed=details(self.root,self.game,675)
        ret=next(e for e in changed["events"] if e["name"]=="JH_HOME1F_TO_2F")
        self.assertEqual(ret["warp"],{"map":674,"x":4,"y":5})
        # No source characters/MapInfos/tilesets or saves were replaced.
        self.assertEqual((self.game/"Saves/File.rxdata").read_bytes(),
                         b"the user's private save")

        fresh, home, sets=fixtures()
        self.assertEqual(patcher.apply_patch(fresh,sets,674,patch674),1)
        self.assertEqual(patcher.apply_patch(fresh,sets,674,patch674),0)
        self.assertEqual(fresh.attrs["@events"][1].attrs["@x"],4)
        self.assertEqual(patcher.apply_patch(home,sets,675,patcher.read_patch(self.root,675)),1)
        self.assertEqual(home.attrs["@events"][1].attrs["@pages"][0].attrs["@list"][0]
                         .attrs["@parameters"][2:4],[4,5])

    def test_profile_initialization_event_cannot_be_moved(self):
        before=details(self.root,self.game,674)
        profile=next(e for e in before["events"] if e["name"]=="JH_NEW_GAME_PROFILE")
        movement={"id":profile["id"],"name":profile["name"],
                  "before":[6,7],"after":[6,8],
                  "warp_before":[674,6,7],"warp_after":[674,6,7]}
        with self.assertRaisesRegex(ValueError,"Não mover"):
            save_changes(self.root,self.game,{
                "map_id":674,"map_hash":before["map_hash"],"patch_hash":None,
                "changes":[],"event_changes":[movement]})
        self.assertEqual((self.game/"Data/Map674.rxdata").read_bytes(),self.original)

    def test_unknown_old_tile_blocks_published_patch_without_overwriting_events(self):
        old,_,sets=fixtures()
        p={"schema":1,"map_id":674,"tileset":"BLUE_JOHTO_OPENING_INSIDE",
           "edits":[{"x":5,"y":5,"z":1,"before":499,"after":401}]}
        with self.assertRaisesRegex(ValueError,"conflito"):
            patcher.apply_patch(old,sets,674,p)
        self.assertEqual(old.attrs["@events"],self.room.attrs["@events"])


if __name__=="__main__":
    unittest.main()
