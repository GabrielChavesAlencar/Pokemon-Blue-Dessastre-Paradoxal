"""J10 SYNTHETIC ONLY: human-drawn source pipeline, never maps/rights/QA for real."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import author_sinnoh_playable_j10 as j10
from audit_sinnoh_playable_j09 import authored_five

def chunk(name:bytes,raw:bytes):
    return struct.pack(">I",len(raw))+name+raw+struct.pack(">I",zlib.crc32(name+raw)&0xffffffff)
def fake_png():
    row=b"\0"+(b"\x10\x22\x33\xff"*256)
    content=row*96
    return b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",struct.pack(">IIBBBBB",256,96,8,6,0,0,0))+chunk(b"IDAT",zlib.compress(content))+chunk(b"IEND",b"")
def make_obj(tmp,symbol,n,sha,*,w=12,h=10):
    ground=[384+(x+y+n)%4 for y in range(h) for x in range(w)]
    upper=[0]*(w*h)
    for i in range(5):upper[(i+1)*w+(i*2+n)%(w-2)+1]=394+(i%2)
    third=[0]*(w*h)
    return {"schema":1,"region":"SINNOH","stage":"J10","symbol":symbol,
            "kind":j10.KIND,"width":w,"height":h,
            "tileset_id":1,"tileset_png":"OwnApproved.png",
            "tileset_sha256":sha,
            "tileset_permission_reference":"SYNTHETIC_TEST_OWN_GRAPHICS_NOT_A_LICENSE",
            "author_reference":"SYNTHETIC_TEST_MAP_AUTHOR_NO_REAL_RIGHTS",
            "authored_by_user":True,"geometry_reviewed_locally":True,
            "layers":[ground,upper,third],"events":[],
            "destination_map_id":None,"native_gameplay_verified":False}
class SinnohJ10MapAuthorTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="j10-fixture-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        src=json.loads((ROOT/"data/regions/sinnoh-j02-map-source-catalog.json").read_text())
        cat=self.root/"data/regions/sinnoh-j02-map-source-catalog.json"
        cat.parent.mkdir(parents=True)
        cat.write_text(json.dumps(src))
        self.symbols=[r["symbol"] for r in src["maps"] if r["source_id"] is None]
        # Synthetic fixture: J02 real provenance validation belongs to its own regression suite.
        self.catalog_patcher=patch.object(j10,"source_catalog",return_value=src)
        self.catalog_patcher.start()
        self.addCleanup(self.catalog_patcher.stop)
        self.work=self.root/".blue-work"
        self.drafts=self.work/j10.DRAFT_DIR
        self.tiles=self.work/j10.TILESET_DIR
        self.drafts.mkdir(parents=True)
        self.tiles.mkdir()
        self.png=self.tiles/"OwnApproved.png"
        self.png.write_bytes(fake_png())
        self.sha=hashlib.sha256(self.png.read_bytes()).hexdigest()
        self.objects={}
        for n,s in enumerate(self.symbols):
            obj=make_obj(self.root,s,n,self.sha)
            self.objects[s]=obj
            self.write(s)
        self.fakegame=self.root/"game/Data/Map099.rxdata"
        self.fakegame.parent.mkdir(parents=True)
        self.fakegame.write_bytes(b"SYNTHETIC_MAIN_GAME_DO_NOT_CHANGE")
        self.save=self.root/"game/Saves/private.sav"
        self.save.parent.mkdir(parents=True)
        self.save.write_bytes(b"SYNTHETIC_SAVE_DO_NOT_CHANGE")
    def write(self,s):
        (self.drafts/(s+".json")).write_text(json.dumps(self.objects[s]))
    def first(self):
        return self.symbols[0]
    def reject(self,part=None):
        if part:
            with self.assertRaisesRegex((ValueError,OSError),part):
                j10.preflight(self.root)
        else:
            with self.assertRaises((ValueError,OSError,KeyError,TypeError)):
                j10.preflight(self.root)
        self.assertFalse((self.work/j10.STAGE_DIR).exists())
    def test_01_five_synthetic_drafts_validate_but_no_native_approval(self):
        blobs,r=j10.preflight(self.root)
        self.assertEqual(len(blobs),5)
        self.assertFalse(r["can_install"])
        self.assertFalse(r["can_publish"])
        self.assertFalse(r["permissions_independently_approved"])
        self.assertEqual(r["native_qa_cases_passed"],0)
        self.assertEqual(r["native_maps_installed"],0)
    def test_02_atomic_build_produces_five_rxdata_sources_only(self):
        r=j10.private_build(self.root)
        folder=self.work/j10.STAGE_DIR
        self.assertTrue(folder.is_dir())
        self.assertEqual(len(list(folder.iterdir())),5)
        checked=authored_five(self.root,folder,json.loads((self.root/j10.CATALOG).read_text()) if hasattr(j10,"CATALOG") else j10.source_catalog(self.root))
        self.assertEqual(len(checked),5)
        self.assertEqual(r["actual_original_map_files_written"],5)
        self.assertFalse(r["can_install"])
        self.assertFalse((self.root/"game/Data/Map442.rxdata").exists())
        self.assertEqual(self.fakegame.read_bytes(),b"SYNTHETIC_MAIN_GAME_DO_NOT_CHANGE")
        self.assertEqual(self.save.read_bytes(),b"SYNTHETIC_SAVE_DO_NOT_CHANGE")
    def test_03_rebuild_refuses_overwriting_real_scenes(self):
        j10.private_build(self.root)
        with self.assertRaisesRegex(ValueError,"AUTHORED_MAPS_ALREADY_EXIST"):
            j10.private_build(self.root)
    def test_04_missing_one_map_no_output(self):
        (self.drafts/(self.first()+".json")).unlink()
        self.reject()
    def test_05_no_drawn_tiles_rejected(self):
        s=self.first();self.objects[s]["layers"]=[[0]*120 for _ in range(3)];self.write(s)
        self.reject("DRAFT_HAS_NO_MEANINGFUL")
    def test_06_plain_one_tile_filler_rejected(self):
        s=self.first();self.objects[s]["layers"]=[[384]*120,[0]*120,[0]*120];self.write(s)
        self.reject("DRAFT_HAS_NO_MEANINGFUL")
    def test_07_duplicated_scenes_failclosed(self):
        a,b=self.symbols[:2]
        self.objects[b]["layers"]=copy.deepcopy(self.objects[a]["layers"])
        self.write(b)
        self.reject("FIVE_SCENES_ARE_DUPLICATE")
    def test_08_different_symbol_in_filename_rejected(self):
        s=self.first();self.objects[s]["symbol"]="SINNOH_FAKE";self.write(s)
        self.reject("DRAFT_MUST_BE_ORIGINALLY")
    def test_09_malformed_json_rejected(self):
        (self.drafts/(self.first()+".json")).write_text("{",encoding="utf-8")
        self.reject("DRAFT_NOT_JSON")
    def test_10_false_author_attribution_rejected(self):
        s=self.first();self.objects[s]["authored_by_user"]=False;self.write(s)
        self.reject("DRAFT_MUST_BE_ORIGINALLY")
    def test_11_unreviewed_geometry_rejected(self):
        s=self.first();self.objects[s]["geometry_reviewed_locally"]=False;self.write(s)
        self.reject("DRAFT_MUST_BE_ORIGINALLY")
    def test_12_fake_claim_native_test_rejected(self):
        s=self.first();self.objects[s]["native_gameplay_verified"]=True;self.write(s)
        self.reject("DRAFT_MUST_BE_ORIGINALLY")
    def test_13_event_script_import_blocked(self):
        s=self.first();self.objects[s]["events"]=[{"script":"donor"}];self.write(s)
        self.reject("DRAFT_MUST_BE_ORIGINALLY")
    def test_14_fabricated_destination_mapid_rejected(self):
        s=self.first();self.objects[s]["destination_map_id"]=442;self.write(s)
        self.reject("DRAFT_MUST_BE_ORIGINALLY")
    def test_15_sha_tampering_rejected(self):
        s=self.first();self.objects[s]["tileset_sha256"]="0"*64;self.write(s)
        self.reject("TILESET_CHANGED")
    def test_16_png_mutation_detected(self):
        self.png.write_bytes(self.png.read_bytes()+b"J10_TAMPER")
        self.reject("TILESET_CHANGED")
    def test_17_tileset_not_available_rejected(self):
        self.png.unlink()
        self.reject()
    def test_18_broken_png_header_rejected_even_sha_updated(self):
        self.png.write_bytes(b"NOTPNG"*40)
        for s in self.symbols:
            self.objects[s]["tileset_sha256"]=hashlib.sha256(self.png.read_bytes()).hexdigest()
            self.write(s)
        self.reject("LOCAL_TILESET_PNG_INVALID")
    def test_19_png_crc_invalid_rejected(self):
        data=bytearray(self.png.read_bytes());data[29]^=0xff
        self.png.write_bytes(data)
        for s in self.symbols:
            self.objects[s]["tileset_sha256"]=hashlib.sha256(self.png.read_bytes()).hexdigest()
            self.write(s)
        self.reject("LOCAL_TILESET_PNG_HEADER_CRC")
    def test_20_wrong_layer_count_rejected(self):
        s=self.first();self.objects[s]["layers"]=[[384]*120];self.write(s)
        self.reject("EXACTLY_THREE")
    def test_21_wrong_layer_shape_rejected(self):
        s=self.first();self.objects[s]["layers"][0].pop();self.write(s)
        self.reject("FULL_EXPLICIT")
    def test_22_negative_tile_rejected(self):
        s=self.first();self.objects[s]["layers"][0][0]=-1;self.write(s)
        self.reject("TILE_OUT_OF")
    def test_23_id_exceeds_png_range_rejected(self):
        s=self.first();self.objects[s]["layers"][0][0]=65535;self.write(s)
        self.reject("TILE_OUT_OF")
    def test_24_autotile_without_assets_rejected(self):
        s=self.first();self.objects[s]["layers"][0][0]=48;self.write(s)
        self.reject("TILE_OUT_OF")
    def test_25_too_small_map_rejected(self):
        s=self.first();self.objects[s]["width"]=4;self.write(s)
        self.reject("MAP_SIZE_OR_TILESET")
    def test_26_bad_tileset_id_rejected(self):
        s=self.first();self.objects[s]["tileset_id"]=0;self.write(s)
        self.reject("MAP_SIZE_OR_TILESET")
    def test_27_tile_image_path_traversal_rejected(self):
        s=self.first();self.objects[s]["tileset_png"]="../evil.png";self.write(s)
        self.reject("INVALID_TILESET_PNG")
    def test_28_tileset_symlink_refused(self):
        real=self.tiles/"actual.png";self.png.rename(real)
        try:self.png.symlink_to(real)
        except OSError:self.skipTest("symlink not permitted")
        self.reject()
    def test_29_no_user_author_approval_rejected(self):
        s=self.first();self.objects[s]["author_reference"]="x";self.write(s)
        self.reject("DRAFT_MUST_BE_ORIGINALLY")
    def test_30_rights_reference_missing_rejected(self):
        s=self.first();self.objects[s]["tileset_permission_reference"]="";self.write(s)
        self.reject("DRAFT_MUST_BE_ORIGINALLY")
    def test_31_no_script_or_event_in_generated_map(self):
        draft,blob,info=j10.validate_draft(self.root,self.first())
        result=j10.build_rxdata(draft,blob)
        j09=sys.modules["audit_sinnoh_playable_j09"]
        audit=j09.audit_map(result)
        self.assertEqual(audit["foreign_events_not_imported"],0)
        self.assertTrue(audit["nonempty_terrain"])
        self.assertGreater(audit["nonzero_tiles"],60)
    def test_32_no_editor_inputs_on_clean_checkout(self):
        self.assertEqual(j10.main(["--project",str(ROOT)]),2)
    def test_33_map_symbols_must_be_from_j02(self):
        with self.assertRaisesRegex(ValueError,"NON_MISSING_MAP_SYMBOL"):
            j10.validate_draft(self.root,"SINNOH_TWINLEAF_TOWN")
    def test_34_export_writes_only_in_blue_work(self):
        result=j10.private_build(self.root)
        self.assertTrue(Path(result["private_source_directory"]).is_relative_to(self.work))
        self.assertFalse((self.root/"game/Data/Map442.rxdata").exists())
        self.assertEqual(self.fakegame.read_bytes(),b"SYNTHETIC_MAIN_GAME_DO_NOT_CHANGE")
    def test_35_no_duplicate_temp_directory_left_after_build(self):
        j10.private_build(self.root)
        self.assertFalse(any(x.name.startswith(".sinnoh-j10-atomic-")
                             for x in self.work.iterdir()))
if __name__=="__main__":unittest.main()
