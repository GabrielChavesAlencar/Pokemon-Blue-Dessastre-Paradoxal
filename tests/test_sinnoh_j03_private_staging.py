"""J03: synthetic data only, plus fail-closed inspection of real J02 catalog."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
from build_johto_events import ruby,EVENT_CLASSES
from server.ruby_marshal import RubyData,loads
from stage import serialize
from sinnoh_staging_transaction import preview,stage,rollback
import prepare_sinnoh_playable_j03 as j03

PNG=b"\x89PNG\r\n\x1a\n"+"test-owned-png-bytes".encode("ascii")
SHA=lambda payload:hashlib.sha256(payload).hexdigest()

def table(*,nonzero=True):
    w=h=3
    n=w*h*3
    data=([384]+[0]*(n-1)) if nonzero else [0]*n
    return RubyData("Table",struct.pack("<5I",3,w,h,3,n)+struct.pack(f"<{n}H",*data))

def write(root,rel,content):
    p=root/rel
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_bytes(content)
    return p

class TestJ03PrivateOverlay(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.source=self.root/"source"
        self.game=self.root/"game"/"Data"
        self.source.mkdir()
        self.game.mkdir(parents=True)
        self.source_info=serialize({
            209:ruby("RPG::MapInfo",name=b"Twinleaf"),
            227:ruby("RPG::MapInfo",name=b"Route 201"),
            210:ruby("RPG::MapInfo",name=b"Sandgem"),
            228:ruby("RPG::MapInfo",name=b"Route 202"),
        })
        write(self.source,"Data/MapInfos.rxdata",self.source_info)
        write(self.source,"Data/Tilesets.rxdata",serialize([
            None,ruby("RPG::Tileset",id=1,name=b"Source",tileset_name=b"Terrain",
                      autotile_names=[b"Water"],panorama_name=b"External Panorama",
                      battleback_name=b"External Battle",fog_name=b"Secret Fog")]))
        self.source_maps={}
        for sid in j03.SOURCE_IDS:
            evt=ruby("RPG::Event",pages=[ruby("RPG::Event::Page",list=[
                ruby("RPG::EventCommand",code=355,parameters=[b"system('DO_NOT_RUN')"])
            ])])
            payload=serialize(ruby("RPG::Map",tileset_id=1,width=3,height=3,
                data=table(),events={1:evt},autoplay_bgm=True,
                bgm=ruby("RPG::AudioFile",name=b"Third Party Music",volume=90,pitch=100)),
                EVENT_CLASSES)
            write(self.source,f"Data/Map{sid:03d}.rxdata",payload)
            self.source_maps[sid]=SHA(payload)
        write(self.source,"Graphics/Tilesets/Terrain.png",PNG)
        write(self.source,"Graphics/Autotiles/Water.png",PNG)
        write(self.game,"MapInfos.rxdata",serialize({
            1:ruby("RPG::MapInfo",name=b"Main Decades",order=1),
            2:ruby("RPG::MapInfo",name=b"Other Region",order=2),
        }))
        write(self.game,"Tilesets.rxdata",serialize([
            None,ruby("RPG::Tileset",id=1,name=b"Main",tileset_name=b"MainTerrain")
        ]))
        write(self.game,"Map001.rxdata",b"keep-game-map")
        write(self.root,"game/Save01.rxdata",b"keep-original-save")
        self.baseline=SHA((self.game/"MapInfos.rxdata").read_bytes())
        self.source_sha=SHA(self.source_info)
        self.catalog={
            "source_mapinfos_sha256":self.source_sha,
            "source_archive_sha256":"a"*64,
            "source_terrain_candidates":4,"source_maps_missing":5,
            "maps":[
                {"symbol":s,"source_id":sid,
                 "source_sha256":self.source_maps[sid],"source_dimensions":[3,3]}
                for s,sid in zip(j03.PILOT_SYMBOLS,j03.SOURCE_IDS)
            ],
        }
        self.bindings={
            "schema":1,"region":"SINNOH","mode":"J03_FOUR_TERRAIN_DRY_RUN",
            "baseline_mapinfos_sha256":self.baseline,
            "source_mapinfos_sha256":self.source_sha,
            "source_archive_sha256":None,
            "bindings":[
                {"symbol":sym,"source_id":sid,"destination_id":442+i,
                 "source_sha256":self.source_maps[sid],"width":3,"height":3}
                for i,(sym,sid) in enumerate(zip(j03.PILOT_SYMBOLS,j03.SOURCE_IDS))
            ]
        }
        self.reservations={
            "schema":1,"region":"SINNOH","mode":"LOCAL_RESERVATIONS_CANDIDATE",
            "baseline_mapinfos_sha256":self.baseline,"protected_ids":[3,600,700],
        }
        self.rights={
            "schema":1,"region":"SINNOH","mode":"J03_LOCAL_ASSET_REVIEW",
            "allowed_use":j03.RIGHTS_MODE,
            "source_mapinfos_sha256":self.source_sha,
            "source_archive_sha256":None,
            "reviewed_locally":True,
            "asset_sha256":{
                "Graphics/Tilesets/Terrain.png":SHA(PNG),
                "Graphics/Autotiles/Water.png":SHA(PNG),
            },
        }
        self._patch=patch.object(j03,"source_catalog",return_value=self.catalog)
        self._patch.start()
        self.addCleanup(self._patch.stop)

    def build(self):
        return j03.build_overlay(self.root,self.source,self.game,
                                 self.bindings,self.reservations,self.rights)

    def denied(self):
        with self.assertRaises(ValueError):self.build()

    def test_real_catalog_remains_four_of_nine_and_no_rights(self):
        real=j03.source_catalog(ROOT)
        self.assertEqual(real["source_terrain_candidates"],4)
        self.assertEqual(real["source_maps_missing"],5)
        self.assertFalse(real["source_rights_verified"])

    def test_four_synthetic_maps_staged_in_memory_without_game_writes(self):
        files,report=self.build()
        self.assertEqual(report["terrain_maps_in_memory"],4)
        self.assertEqual(report["missing_real_pilot_maps"],5)
        self.assertEqual(report["staged_graphics"],2)
        self.assertEqual(report["staged_tilesets"],1)
        self.assertEqual(len(files),8)  # 4 maps + 2 data copies + 2 graphics
        self.assertFalse(report["can_install"])
        self.assertFalse(report["native_playable"])
        self.assertFalse(report["asset_rights_independently_verified"])
        self.assertFalse((self.root/".blue-work").exists())
        self.assertEqual((self.game/"Map001.rxdata").read_bytes(),b"keep-game-map")
        self.assertEqual((self.root/"game/Save01.rxdata").read_bytes(),b"keep-original-save")

    def test_donor_events_music_and_script_dropped(self):
        files,report=self.build()
        for i in range(4):
            m=loads(files[f"Data/Map{442+i:03d}.rxdata"]).attrs
            self.assertEqual(m["@events"],{})
            self.assertEqual(m["@encounter_list"],[])
            self.assertEqual(m["@bgm"].attrs["@name"],b"")
            self.assertFalse(m["@autoplay_bgm"])
        self.assertEqual(report["donor_events_copied"],0)
        self.assertEqual(report["donor_scripts_copied"],0)
        self.assertEqual(report["donor_music_copied"],0)

    def test_preserve_native_mapinfos_tilesets_in_isolated_copies(self):
        files,_=self.build()
        infos=loads(files["Data/MapInfos.rxdata"])
        tiles=loads(files["Data/Tilesets.rxdata"])
        self.assertEqual(infos[1].attrs["@name"],b"Main Decades")
        self.assertEqual(tiles[1].attrs["@name"],b"Main")
        self.assertEqual(len(tiles),3)
        self.assertIn(442,infos)
        self.assertEqual(tiles[2].attrs["@panorama_name"],b"")
        self.assertEqual(tiles[2].attrs["@battleback_name"],b"")

    def test_dryrun_stage_verify_and_rollback_only_private_stage(self):
        files,report=self.build()
        before=SHA((self.game/"MapInfos.rxdata").read_bytes())
        dry=preview(self.root,"j03-owned",files)
        self.assertFalse((self.root/".blue-work").exists())
        r=stage(self.root,"j03-owned",files,dry["plan_sha256"])
        target=self.root/r["stage_relative_path"]
        self.assertTrue(target.is_dir())
        verified=j03.stage_verify(self.root,"j03-owned",dry["plan_sha256"])
        self.assertEqual(verified["files_verified"],8)
        self.assertFalse(verified["native_playable"])
        self.assertEqual(SHA((self.game/"MapInfos.rxdata").read_bytes()),before)
        back=rollback(self.root,"j03-owned",dry["plan_sha256"])
        self.assertTrue(back["removed_only_stage"])
        self.assertFalse(target.exists())
        self.assertEqual((self.root/"game/Save01.rxdata").read_bytes(),b"keep-original-save")

    def test_stage_plan_tamper_refused(self):
        files,_=self.build()
        p=preview(self.root,"j03-owned",files)
        with self.assertRaises(ValueError):
            stage(self.root,"j03-owned",files,"0"*64)
        self.assertFalse((self.root/".blue-work/sinnoh-stage").exists())

    def test_stage_modified_file_refuses_verification_and_rollback(self):
        files,_=self.build()
        p=preview(self.root,"j03-owned",files)
        stage(self.root,"j03-owned",files,p["plan_sha256"])
        target=self.root/".blue-work/sinnoh-stage"/f"j03-owned-{p['plan_sha256'][:16]}"
        (target/"Data/Map442.rxdata").write_bytes(b"changed")
        with self.assertRaises(ValueError):
            j03.stage_verify(self.root,"j03-owned",p["plan_sha256"])
        with self.assertRaises(ValueError):
            rollback(self.root,"j03-owned",p["plan_sha256"])
        self.assertTrue(target.exists())

    def test_stage_extra_files_refuses_verification_and_rollback(self):
        files,_=self.build()
        p=preview(self.root,"j03-owned",files)
        stage(self.root,"j03-owned",files,p["plan_sha256"])
        target=self.root/".blue-work/sinnoh-stage"/f"j03-owned-{p['plan_sha256'][:16]}"
        (target/"extra-private.bin").write_bytes(b"private")
        with self.assertRaises(ValueError):j03.stage_verify(self.root,"j03-owned",p["plan_sha256"])
        with self.assertRaises(ValueError):rollback(self.root,"j03-owned",p["plan_sha256"])

    def test_no_staging_from_no_inputs(self):
        report=j03.preview_only(ROOT)
        self.assertEqual(report["status"],"BLOCKED_REAL_SOURCE_AND_LOCAL_RIGHTS_NOT_PROVIDED")
        self.assertEqual(report["native_maps_installed"],0)
        self.assertFalse(report["can_install"])
        self.assertFalse(report["native_playable"])

    def test_plan_missing_row_denied(self):
        self.bindings["bindings"].pop()
        self.denied()

    def test_plan_extra_row_denied(self):
        self.bindings["bindings"].append(copy.deepcopy(self.bindings["bindings"][0]))
        self.denied()

    def test_invalid_plan_mode_denied(self):
        self.bindings["mode"]="APPROVED_FOR_INSTALL"
        self.denied()

    def test_missing_plan_field_denied(self):
        self.bindings.pop("source_archive_sha256")
        self.denied()

    def test_duplicate_destination_denied(self):
        self.bindings["bindings"][1]["destination_id"]=442
        self.denied()

    def test_wrong_region_mapid_denied(self):
        for invalid in (300,518,600,805,1000,-1,True,"443"):
            with self.subTest(id=invalid):
                self.bindings["bindings"][0]["destination_id"]=invalid
                self.denied()
        self.bindings["bindings"][0]["destination_id"]=442

    def test_occupied_native_mapid_denied(self):
        self.bindings["bindings"][0]["destination_id"]=1
        self.denied()

    def test_reserved_mapid_denied(self):
        self.reservations["protected_ids"].append(442)
        self.denied()

    def test_invalid_future_reservation_baseline_denied(self):
        self.reservations["baseline_mapinfos_sha256"]="a"*64
        self.denied()

    def test_duplicate_reservation_denied(self):
        self.reservations["protected_ids"]=[600,600]
        self.denied()

    def test_source_hash_mismatch_denied(self):
        self.bindings["bindings"][0]["source_sha256"]="f"*64
        self.denied()

    def test_source_map_file_changed_denied(self):
        target=self.source/"Data/Map209.rxdata"
        target.write_bytes(b"not-an-original-map")
        self.denied()

    def test_source_map_missing_denied(self):
        (self.source/"Data/Map209.rxdata").unlink()
        self.denied()

    def test_blank_source_map_denied(self):
        target=self.source/"Data/Map209.rxdata"
        v=loads(target.read_bytes())
        v.attrs["@data"]=table(nonzero=False)
        changed=serialize(v,EVENT_CLASSES)
        target.write_bytes(changed)
        # Independently confirm that empty terrain is blocked even if SHA is pinned.
        self.bindings["bindings"][0]["source_sha256"]=SHA(changed)
        self.catalog["maps"][0]["source_sha256"]=SHA(changed)
        self.denied()

    def test_bad_source_map_table_denied(self):
        target=self.source/"Data/Map209.rxdata"
        v=loads(target.read_bytes())
        v.attrs["@data"]=RubyData("Table",b"bad")
        changed=serialize(v,EVENT_CLASSES)
        target.write_bytes(changed)
        self.bindings["bindings"][0]["source_sha256"]=SHA(changed)
        self.catalog["maps"][0]["source_sha256"]=SHA(changed)
        self.denied()

    def test_missing_required_graphic_denied(self):
        (self.source/"Graphics/Tilesets/Terrain.png").unlink()
        self.denied()

    def test_graphic_sha_changed_denied(self):
        (self.source/"Graphics/Autotiles/Water.png").write_bytes(PNG+b"changed")
        self.denied()

    def test_rights_missing_review_denied(self):
        self.rights["reviewed_locally"]=False
        self.denied()

    def test_rights_not_for_distribution_denied(self):
        self.rights["allowed_use"]="FREE_PUBLIC_REDISTRIBUTION"
        self.denied()

    def test_rights_source_mapinfos_hash_wrong_denied(self):
        self.rights["source_mapinfos_sha256"]="f"*64
        self.denied()

    def test_rights_missing_one_graphic_denied(self):
        del self.rights["asset_sha256"]["Graphics/Autotiles/Water.png"]
        self.denied()

    def test_rights_extra_graphic_denied(self):
        self.rights["asset_sha256"]["Graphics/Tilesets/Secret.png"]="f"*64
        self.denied()

    def test_source_nested_with_main_game_denied(self):
        with self.assertRaises(ValueError):
            j03._safe_source(self.root,self.root/"game",self.game)

    def test_source_symlink_denied(self):
        link=self.root/"source-link"
        try:link.symlink_to(self.source,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            j03._safe_source(self.root,link,self.game)

    def test_invalid_native_game_data_denied(self):
        (self.game/"Tilesets.rxdata").unlink()
        self.denied()

    def test_invalid_native_mapinfos_sha_denied(self):
        (self.game/"MapInfos.rxdata").write_bytes(b"changed")
        self.denied()

    def test_read_only_main_cli_without_source_fails_closed(self):
        self.assertEqual(j03.main(["--project",str(ROOT)]),2)

    def test_cli_refuses_stage_without_source(self):
        self.assertEqual(j03.main(["--project",str(ROOT),"--stage"]),2)

    def test_cli_rejects_unsupported_flag(self):
        with self.assertRaises(SystemExit):
            j03.main(["--install-into-main-game"])

    def test_cli_roll_back_requires_exact_receipt(self):
        with self.assertRaises(ValueError):
            j03.stage_verify(self.root,"unrelated","f"*64)

    def test_source_rights_folder_escape_denied(self):
        with self.assertRaises(ValueError):
            j03._validate_rights({**self.rights,"asset_sha256":{"../private.png":"f"*64}},
                                 self.source_sha,None)

    def test_local_plan_must_remain_in_blue_work(self):
        with self.assertRaises(ValueError):
            j03.local_input(self.root,self.root/"fake.json")

if __name__=="__main__":unittest.main()
