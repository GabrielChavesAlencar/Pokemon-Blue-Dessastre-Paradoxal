"""Sinnoh B07: isolated fixture stage; never writes to user's native Decades."""
from __future__ import annotations
import copy
import hashlib
import io
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import build_sinnoh_b07_private_stage as b07
from server.ruby_marshal import RubyObject,RubyData,loads
from stage import serialize
from sinnoh_staging_transaction import preview,stage,rollback

def tile_table():
    return RubyData("Table",struct.pack("<5I",3,2,2,3,12)
                    +struct.pack("<12H",*[1,0,0,0]*3))

def tile(id,name):
    return RubyObject("RPG::Tileset",{
       "@id":id,"@name":name.encode(),
       "@tileset_name":name.encode(),
       "@autotile_names":[b"Wave"],
       "@passages":RubyData("Table",struct.pack("<5I",1,384,1,1,384)
                            +struct.pack("<384H",*[0]*384)),
       "@priorities":[],"@terrain_tags":[],
       "@panorama_name":b"Other panorama","@fog_name":b"Fog",
       "@battleback_name":b"Other battleback",
    })

class B07Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=b07.load(b07.CONTRACT)
        cls.b00=b07.load(b07.B00)
        cls.b01=b07.load(b07.B01)
        cls.b04=b07.load(b07.B04)
        cls.b05=b07.load(b07.B05)
        cls.b06=b07.load(b07.B06)

    def test_01_metadata_preflight_never_marks_gameplay(self):
        rows=b07.check_contract(self.c,self.b06,self.b00,
                                 self.b01,self.b04,self.b05)
        self.assertEqual(len(rows),54)
        self.assertEqual(rows[0]["candidate_destination_map_id"],442)
        self.assertEqual(rows[-1]["candidate_destination_map_id"],495)
        self.assertFalse(self.c["can_install_into_game"])
        self.assertFalse(self.c["r07_complete"])

    def test_02_cli_without_private_zip_does_not_write(self):
        run=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/build_sinnoh_b07_private_stage.py")],
            cwd=ROOT,text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertIn("B07_PREFLIGHT_METADATA_READY_NOT_STAGED",run.stdout)

    def test_03_cannot_forge_future_or_rights_approval(self):
        for key,value in (("rights_per_asset_verified",True),
                          ("r07_complete",True),("r08_complete",True),
                          ("can_install_into_game",True),
                          ("redistribution_approved",True),
                          ("phase_b_approved",1)):
            altered=copy.deepcopy(self.c);altered[key]=value
            with self.subTest(key=key),self.assertRaisesRegex(
                ValueError,"SINNOH_B07_BLOCKED"):
                b07.check_contract(altered,self.b06,self.b00,
                                   self.b01,self.b04,self.b05)

    def test_04_placeholder_b06_not_promoted_to_terrain(self):
        altered=copy.deepcopy(self.b06)
        altered["remap_preview"][54]["category"]="TERRAIN"
        with self.assertRaises(ValueError):
            b07.check_contract(self.c,altered,self.b00,
                               self.b01,self.b04,self.b05)

    def fixture(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        project=Path(tmp.name)
        source=project/"synthetic-source.zip"
        infos={i:RubyObject("RPG::MapInfo",{"@name":("map"+str(i)).encode()})
               for i in range(100,154)}
        t=[None,tile(1,"TerrainA")]
        while len(t)<31:t.append(None)
        t.append(tile(31,"TerrainB"))
        rows=[]
        with ZipFile(source,"w",ZIP_DEFLATED) as z:
            z.writestr("Synthetic/Data/MapInfos.rxdata",serialize(infos))
            z.writestr("Synthetic/Data/Tilesets.rxdata",serialize(t))
            for folder,name in (("Tilesets","TerrainA"),("Tilesets","TerrainB"),
                                ("Autotiles","Wave")):
                z.writestr(f"Synthetic/Graphics/{folder}/{name}.png",
                           b"\x89PNG\r\n\x1a\n" + b"synthetic")
            for i in range(54):
                sid=100+i;dst=442+i
                rows.append({"source_map_id":sid,
                             "candidate_destination_map_id":dst,
                             "category":"TERRAIN"})
                attrs={"@tileset_id":31 if i<53 else 1,
                       "@width":2,"@height":2,"@data":tile_table(),
                       "@events":{7:RubyObject("RPG::Event",{"@id":7})},
                       "@autoplay_bgm":True}
                data=serialize(RubyObject("RPG::Map",attrs),
                               extra_classes=("RPG::Event",))
                z.writestr(f"Synthetic/Data/Map{sid:03d}.rxdata",data)
        native_infos=serialize({
            1:RubyObject("RPG::MapInfo",{
               "@name":b"Decades original","@order":1})})
        native_tiles=serialize([None,tile(1,"NativeA")])
        return project,source,rows,native_infos,native_tiles

    def test_05_synthetic_all_54_maps_staged_in_memory(self):
        root,src,rows,infos,tiles=self.fixture()
        files,report=b07.build_files(src,infos,tiles,rows,source_root="Synthetic")
        self.assertEqual(report["source_terrain_maps_prepared"],54)
        self.assertEqual(report["empty_placeholders_excluded"],22)
        self.assertEqual(len([k for k in files if k.startswith("Data/Map") and k.endswith(".rxdata")])-1,54)
        self.assertEqual(report["private_png_count"],3)
        self.assertEqual(report["donor_tileset_to_new_private_index"],{"1":3,"31":2})
        self.assertFalse((root/".blue-work").exists())

    def test_06_strip_events_audio_and_preserve_native_files(self):
        root,src,rows,infos,tiles=self.fixture()
        files,_=b07.build_files(src,infos,tiles,rows,source_root="Synthetic")
        data=loads(files["Data/Map442.rxdata"]).attrs
        self.assertEqual(data["@events"],{})
        self.assertEqual(data["@encounter_list"],[])
        self.assertFalse(data["@autoplay_bgm"])
        self.assertEqual(data["@bgm"].attrs["@name"],b"")
        self.assertEqual(data["@tileset_id"],2)
        out_info=loads(files["Data/MapInfos.rxdata"])
        out_tiles=loads(files["Data/Tilesets.rxdata"])
        self.assertEqual(out_info[1].attrs["@name"],b"Decades original")
        self.assertEqual(out_tiles[1].attrs["@name"],b"NativeA")
        self.assertEqual(out_tiles[2].attrs["@tileset_name"][:6],b"SN_B07")
        self.assertEqual(out_tiles[2].attrs["@panorama_name"],b"")
        self.assertEqual(out_tiles[2].attrs["@fog_name"],b"")
        self.assertEqual(out_tiles[2].attrs["@battleback_name"],b"")
        self.assertEqual(loads(files["Data/Map495.rxdata"]).attrs["@tileset_id"],3)
        self.assertNotIn("Data/Map496.rxdata",files)
        self.assertEqual(len([k for k in files if k.startswith("Graphics/")]),3)

    def test_07_private_stage_and_rollback_preserve_native(self):
        root,src,rows,infos,tiles=self.fixture()
        game=root/"game"/"Data";game.mkdir(parents=True)
        (game/"MapInfos.rxdata").write_bytes(infos)
        (game/"Tilesets.rxdata").write_bytes(tiles)
        (game/"Map001.rxdata").write_bytes(b"original Map")
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                for p in game.iterdir()}
        files,_=b07.build_files(src,infos,tiles,rows,source_root="Synthetic")
        dry=preview(root,"privateb07",files)
        self.assertEqual(dry["mode"],"DRY_RUN_NO_WRITES")
        self.assertFalse((root/".blue-work").exists())
        done=stage(root,"privateb07",files,dry["plan_sha256"])
        self.assertEqual(done["mode"],"LOCAL_STAGE_ONLY")
        path=root/done["stage_relative_path"]
        self.assertTrue((path/"Data/Map442.rxdata").exists())
        self.assertTrue((path/"Graphics/Tilesets").is_dir())
        self.assertEqual({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in game.iterdir()},before)
        self.assertTrue(rollback(root,"privateb07",dry["plan_sha256"])
                        ["removed_only_stage"])
        self.assertFalse(path.exists())
        self.assertEqual({p.name:hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in game.iterdir()},before)

    def test_08_stage_wont_accept_wrong_preview_hash(self):
        root,src,rows,infos,tiles=self.fixture()
        files,_=b07.build_files(src,infos,tiles,rows,source_root="Synthetic")
        with self.assertRaisesRegex(ValueError,"dry-run"):
            stage(root,"privateb07",files,"0"*64)
        self.assertFalse((root/".blue-work"/"sinnoh-stage").exists())

    def test_09_missing_private_png_fail_closed(self):
        root,src,rows,infos,tiles=self.fixture()
        broken=root/"missing-png.zip"
        with ZipFile(src) as z,ZipFile(broken,"w",ZIP_DEFLATED) as dst:
            for name in z.namelist():
                if name!="Synthetic/Graphics/Autotiles/Wave.png":
                    dst.writestr(name,z.read(name))
        with self.assertRaisesRegex(ValueError,"ausente/duplicado"):
            b07.build_files(broken,infos,tiles,rows,source_root="Synthetic")
        self.assertFalse((root/".blue-work").exists())

    def test_10_invalid_map_terrain_rejected(self):
        root,src,rows,infos,tiles=self.fixture()
        bad=root/"bad-map.zip"
        with ZipFile(src) as z,ZipFile(bad,"w",ZIP_DEFLATED) as dst:
            for name in z.namelist():
                raw=z.read(name)
                if name=="Synthetic/Data/Map100.rxdata":
                    m=loads(raw);m.attrs["@data"]=RubyData("Table",b"corrupt")
                    raw=serialize(m,extra_classes=("RPG::Event",))
                dst.writestr(name,raw)
        with self.assertRaisesRegex(ValueError,"geometria/tileset"):
            b07.build_files(bad,infos,tiles,rows,source_root="Synthetic")

    def test_11_unverified_game_data_snapshot_is_blocked(self):
        root,src,rows,infos,tiles=self.fixture()
        game=root/"game"/"Data";game.mkdir(parents=True)
        (game/"MapInfos.rxdata").write_bytes(infos)
        (game/"Tilesets.rxdata").write_bytes(tiles)
        (game/"Map001.rxdata").write_bytes(b"original Map")
        inventory={"mapinfos_sha256":hashlib.sha256(infos).hexdigest(),
                   "tilesets_sha256":hashlib.sha256(tiles).hexdigest()}
        self.assertTrue(b07.check_current_game(game,inventory,[1])
                        ["actual_game_data_verified_against_b01"])
        (game/"Map442.rxdata").write_bytes(b"new collision")
        with self.assertRaisesRegex(ValueError,"MapIDs"):
            b07.check_current_game(game,inventory,[1])

    def test_12_game_data_changes_block_stage(self):
        root,src,rows,infos,tiles=self.fixture()
        game=root/"game"/"Data";game.mkdir(parents=True)
        (game/"MapInfos.rxdata").write_bytes(infos)
        (game/"Tilesets.rxdata").write_bytes(tiles)
        inventory={"mapinfos_sha256":hashlib.sha256(infos).hexdigest(),
                   "tilesets_sha256":hashlib.sha256(tiles).hexdigest()}
        (game/"MapInfos.rxdata").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError,"baseline local mudou"):
            b07.check_current_game(game,inventory,[])

    def test_13_rollbacks_refuse_tampered_private_stage(self):
        root,src,rows,infos,tiles=self.fixture()
        files,_=b07.build_files(src,infos,tiles,rows,source_root="Synthetic")
        dry=preview(root,"privateb07",files)
        stage(root,"privateb07",files,dry["plan_sha256"])
        p=root/dry["stage_relative_path"]/"Data/Map442.rxdata"
        p.write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError,"hash divergente"):
            rollback(root,"privateb07",dry["plan_sha256"])
        self.assertTrue(p.exists())

    def test_14_unsafe_png_names_rejected(self):
        root,src,rows,infos,tiles=self.fixture()
        rows2=copy.deepcopy(rows);rows2[0]["candidate_destination_map_id"]=300
        badinfos=serialize({300:RubyObject("RPG::MapInfo",{"@name":b"occupied"})})
        with self.assertRaisesRegex(ValueError,"colide"):
            b07.build_files(src,badinfos,tiles,rows2,source_root="Synthetic")

if __name__=="__main__":unittest.main()
