"""Windows native-map recompilation is not the same as Johto missing.

Replay the integrated workflow with 100 valid Ruby Marshal maps, a changed
Map600 after Game.exe, installed Johto's original proof and no private ZIP.
Only the two New Bark maps may be patched; Kanto/Hoenn and saves stay intact.
"""
from __future__ import annotations
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "regions"))
from server.ruby_marshal import RubyObject
from stage import serialize
from test_johto_bedroom_hgss import fixtures, table
import johto_main_preview as preview
import auto_integrate_johto


class JohtoRuntimePreviewTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.root = Path(t.name)
        self.game = self.root / "game"
        for folder in ("Data", "Saves", "PBS", preview.PLUGIN):
            (self.game / folder).mkdir(parents=True, exist_ok=True)
        (self.root / ".blue-work").mkdir()
        self.write("Game.exe", b"existing game executable")
        self.write("Saves/File A.rxdata", b"existing user save")
        self.write("Data/Map410.rxdata", b"existing Kanto")
        self.write("Data/Map701.rxdata", b"existing Hoenn")
        self.write(preview.PLUGIN + "/Boot.rb", b"safe compiled Johto boot")
        self.write("PBS/map_metadata_johto_main.txt", b"[674]\n")
        self.write("PBS/map_connections.txt", b"regional connections")
        room, home, sets = fixtures()
        self.write("Data/Tilesets.rxdata", serialize(sets))
        infos = {}
        for mid in preview.PREVIEW_IDS:
            infos[mid] = RubyObject("RPG::MapInfo", {
                "@name": ("[Johto] " + str(mid)).encode("ascii"),
                "@parent_id": 0, "@order": mid})
            if mid == 674: obj = room
            elif mid == 675: obj = home
            else:
                obj = RubyObject("RPG::Map", {
                    "@width": 14, "@height": 11, "@tileset_id":1,
                    "@data": table(14,11,3),
                    "@events": {} })
            self.write(f"Data/Map{mid:03}.rxdata",
                       serialize(obj, preview.johto_qa.EVENT_CLASSES))
        self.write("Data/MapInfos.rxdata", serialize(infos))
        self.write(preview.READY, ("BLUE_JOHTO_PRIVATE_PREVIEW_V1,100," +
            ",".join(map(str, (*preview.START, *preview.TOWN[:3],
                               *preview.NPC[:3])))+"\n").encode("ascii"))
        names = [f"Data/Map{i:03}.rxdata" for i in sorted(preview.PREVIEW_IDS)]
        names += ["Data/Tilesets.rxdata","Data/MapInfos.rxdata",
                  "PBS/map_connections.txt","PBS/map_metadata_johto_main.txt",
                  preview.PLUGIN+"/Boot.rb"]
        proof = {"schema":1,"region":"JOHTO","status":preview.STATUS,
                 "source_bundle_sha256":preview.PINNED_SHA,
                 "map_ids":sorted(preview.PREVIEW_IDS),
                 "start":list(preview.START),"town":list(preview.TOWN),
                 "npc":list(preview.NPC),"file_hashes":{
                     name:preview.sha((self.game/name).read_bytes()) for name in names
                 }}
        self.write(preview.PROOF,preview.raw_json(proof))

    def write(self, relative, data):
        p=self.game/relative
        p.parent.mkdir(parents=True,exist_ok=True)
        p.write_bytes(data)

    def test_runtime_modified_map_detected_and_blue_story_keeps_johto_available(self):
        # Game.exe added a harmless real event to Map600 after installation.
        p=self.game/"Data/Map600.rxdata"
        modified=bytearray(p.read_bytes())
        # Use a legal RMXP edit, not arbitrary corruption.
        from server.ruby_marshal import loads
        map600=loads(bytes(modified))
        map600.attrs["@bgm"] = RubyObject("RPG::AudioFile", {
            "@name": b"104 New Bark Town", "@volume": 80,"@pitch":100})
        p.write_bytes(serialize(map600,preview.johto_qa.EVENT_CLASSES))
        original={x:(self.game/x).read_bytes() for x in (
            "Saves/File A.rxdata","Data/Map410.rxdata","Data/Map701.rxdata",
            "Data/Map600.rxdata", "Data/MapInfos.rxdata","Data/Tilesets.rxdata")}
        with self.assertRaisesRegex(ValueError,"Map600.rxdata"):
            preview.preview_proof(self.game)
        before=preview.runtime_semantic_preview(self.game)
        self.assertEqual(before["changed_map_ids"], [600])
        report=auto_integrate_johto.integrate(self.root,self.game)
        self.assertEqual(report["status"],
                         "experimental_installed_runtime_modified_not_native_tested")
        self.assertTrue(report["ready"])
        self.assertTrue(report["bedroom_changed"])
        self.assertFalse(report["native_qa"])
        self.assertEqual(report["runtime_modified_map_ids"], [600])
        after=preview.runtime_semantic_preview(self.game)
        self.assertEqual(after["changed_map_ids"], [600])
        self.assertEqual(serialize(loads((self.game/"Data/Map674.rxdata").read_bytes()),
                                   preview.johto_qa.EVENT_CLASSES),
                         (self.game/"Data/Map674.rxdata").read_bytes())
        for x,raw in original.items():
            self.assertEqual((self.game/x).read_bytes(),raw)

    def test_live_edited_bedroom_hash_and_return_event_are_preserved_as_installed(self):
        from server.ruby_marshal import loads
        room_path = self.game / "Data/Map674.rxdata"
        home_path = self.game / "Data/Map675.rxdata"
        room = loads(room_path.read_bytes())
        stairs = next(e for e in room.attrs["@events"].values()
                      if e.attrs["@name"] == b"JH_HOME2F_TO_1F")
        # Simulate a legitimate Johto Map Studio edit: the stair is moved
        # and the native Ruby Marshal bytes no longer match original proof.
        stairs.attrs["@x"], stairs.attrs["@y"] = 4, 4
        room_path.write_bytes(serialize(room,preview.johto_qa.EVENT_CLASSES))
        home = loads(home_path.read_bytes())
        warp = next(e for e in home.attrs["@events"].values()
                    if e.attrs["@name"] == b"JH_HOME1F_TO_2F")
        warp.attrs["@pages"][0].attrs["@list"][0].attrs["@parameters"][2:4] = [4, 5]
        home_path.write_bytes(serialize(home,preview.johto_qa.EVENT_CLASSES))
        snapshots = {name:(self.game/name).read_bytes() for name in (
            "Data/Map674.rxdata","Data/Map675.rxdata","Data/Map600.rxdata",
            "Data/Tilesets.rxdata","Data/MapInfos.rxdata",
            "Saves/File A.rxdata","Data/Map410.rxdata","Data/Map701.rxdata")}
        with self.assertRaisesRegex(ValueError,"Map674.rxdata"):
            preview.preview_proof(self.game)
        # The previous implementation called scoped_bedroom_proof unconditionally,
        # rejected the first changed hash and told Blue-Story Johto was missing.
        state = preview.runtime_semantic_preview(self.game)
        self.assertEqual(state["changed_map_ids"],[674,675])
        result = auto_integrate_johto.integrate(self.root,self.game)
        self.assertTrue(result["ready"],result)
        self.assertEqual(result["status"],
                         "experimental_installed_runtime_modified_not_native_tested")
        self.assertFalse(result["bedroom_changed"])
        self.assertIn("preserv",result["bedroom_reason"])
        self.assertEqual(result["runtime_modified_map_ids"],[674,675])
        for name,raw in snapshots.items():
            self.assertEqual((self.game/name).read_bytes(),raw,
                             "An existing Johto edit/other region/save was overwritten: "+name)

    def test_map_studio_published_edit_prevents_auto_stair_relayout(self):
        from server.ruby_marshal import loads
        room_path=self.game/"Data/Map674.rxdata"
        current=loads(room_path.read_bytes())
        stair = next(e for e in current.attrs["@events"].values()
                     if e.attrs["@name"]==b"JH_HOME2F_TO_1F")
        stair.attrs["@x"],stair.attrs["@y"]=5,5
        room_path.write_bytes(serialize(current,preview.johto_qa.EVENT_CLASSES))
        proof_path=self.game/preview.PROOF
        proof=json.loads(proof_path.read_text("utf-8"))
        proof["editor_map_patches"]={"674":"a"*64}
        proof_path.write_text(json.dumps(proof),encoding="utf-8")
        original=room_path.read_bytes()
        result=auto_integrate_johto.integrate(self.root,self.game)
        self.assertTrue(result["ready"],result)
        self.assertFalse(result["bedroom_changed"])
        self.assertIn("Map Studio",result["bedroom_reason"])
        self.assertEqual(room_path.read_bytes(),original)

    def test_private_hgss_tileset_is_accepted_only_when_manifest_marks_it(self):
        from server.ruby_marshal import loads
        from copy import deepcopy
        tiles=self.game/"Data/Tilesets.rxdata"
        room_path=self.game/"Data/Map674.rxdata"
        sets=loads(tiles.read_bytes())
        clone=deepcopy(sets[1])
        clone.attrs["@tileset_name"]=b"BLUE_JOHTO_HGSS_PRIVATE_1"
        sets.append(clone)
        tiles.write_bytes(serialize(sets))
        room=loads(room_path.read_bytes())
        room.attrs["@tileset_id"]=2
        room_path.write_bytes(serialize(room,preview.johto_qa.EVENT_CLASSES))
        with self.assertRaisesRegex(ValueError,"tileset de New Bark"):
            preview.runtime_semantic_preview(self.game)
        manifest=self.game/preview.PROOF
        contents=json.loads(manifest.read_text("utf-8"))
        contents["private_hgss"]={"status":"private_art_compiled",
                                  "maps":[674]}
        manifest.write_text(json.dumps(contents),encoding="utf-8")
        verified=preview.runtime_semantic_preview(self.game)
        self.assertEqual(verified["map_count"],100)
        self.assertIn(674,verified["changed_map_ids"])

    def test_missing_bedroom_file_is_not_treated_as_verified_johto(self):
        target=self.game/"Data/Map674.rxdata"
        target.unlink()
        result=auto_integrate_johto.integrate(self.root,self.game)
        self.assertFalse(result["ready"])
        self.assertEqual(result["status"],"existing_install_needs_review")
        self.assertFalse(target.exists())
        self.assertEqual((self.game/"Saves/File A.rxdata").read_bytes(),
                         b"existing user save")

    def test_conflicting_published_patch_is_reported_without_marking_johto_missing(self):
        from server.ruby_marshal import loads
        # The map changed since the GitHub patch was authored; never apply
        # the old before-tile over the player's newer local work.
        room = self.game/"Data/Map674.rxdata"
        original_room = room.read_bytes()
        map600 = self.game/"Data/Map600.rxdata"
        old = loads(map600.read_bytes())
        old.attrs["@bgm"] = RubyObject("RPG::AudioFile",
            {"@name": b"104 New Bark Town", "@volume":80,"@pitch":100})
        map600.write_bytes(serialize(old,preview.johto_qa.EVENT_CLASSES))
        patchdir=self.root/"data/regions/johto-map-edits"
        patchdir.mkdir(parents=True)
        patchdir.joinpath("Map674.json").write_text(json.dumps({
            "schema": 1, "map_id":674,
            "tileset":"BLUE_JOHTO_OPENING_INSIDE",
            "edits":[{"x":3,"y":3,"z":0,"before":900,"after":401}]
        }),encoding="utf-8")
        # Avoid bedroom patching itself by recording a previous editor
        # version; the intentionally conflicting new patch remains pending.
        proof=self.game/preview.PROOF
        data=json.loads(proof.read_text("utf-8"))
        data["editor_map_patches"]={"674":"a"*64}
        proof.write_text(json.dumps(data),encoding="utf-8")
        result=auto_integrate_johto.integrate(self.root,self.game)
        self.assertTrue(result["ready"],result)
        self.assertFalse(result["map_editor_changed"])
        self.assertIn("conflito",result["map_editor_warning"])
        self.assertEqual(room.read_bytes(),original_room)
        self.assertEqual((self.game/"Saves/File A.rxdata").read_bytes(),
                         b"existing user save")

    def test_corrupt_map_rejected_without_touching_saves(self):
        self.write("Data/Map600.rxdata", b"INVALID")
        original=self.game.joinpath("Data/Map674.rxdata").read_bytes()
        report=auto_integrate_johto.integrate(self.root,self.game)
        self.assertEqual(report["status"],"existing_install_needs_review")
        self.assertFalse(report["ready"])
        self.assertEqual((self.game/"Data/Map674.rxdata").read_bytes(),original)
        self.assertEqual((self.game/"Saves/File A.rxdata").read_bytes(),
                         b"existing user save")


class MissingPrivateSourceTests(unittest.TestCase):
    def test_base_only_inputs_are_identified_without_falsely_installing_johto(self):
        import zipfile
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary)
            game=root/"game"
            game.mkdir(parents=True)
            (root/".blue-work").mkdir()
            (game/"Game.exe").write_bytes(b"untouched Game.exe")
            filename=root/".blue-work/johto-pilot-inputs(1).zip"
            with zipfile.ZipFile(filename,"w") as archive:
                archive.writestr("johto-inputs-manifest.json",
                    json.dumps({"schema":2, "purpose":"PRIVATE_JOHTO_PILOT_INPUTS"}))
                archive.writestr("game/Graphics/Trainers/HGSS.png",b"some art")
            result=auto_integrate_johto.integrate(root,game)
            self.assertEqual(result["status"],"awaiting_johto_installable_release")
            self.assertFalse(result["ready"])
            self.assertIn("johto-pilot-inputs(1).zip",result["reason"])
            self.assertIn("Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip",
                          result["reason"])
            self.assertFalse((game/"Data"/"Map674.rxdata").exists())
            self.assertEqual((game/"Game.exe").read_bytes(),b"untouched Game.exe")


if __name__ == "__main__":
    unittest.main()
