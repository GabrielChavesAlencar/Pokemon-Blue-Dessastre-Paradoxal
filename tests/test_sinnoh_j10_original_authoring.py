"""J10 private original geometry: synthetic-only coverage; no licensed assets or native game."""
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
import audit_sinnoh_playable_j09 as j09

SYMBOLS=[
    "SINNOH_PLAYER_BEDROOM","SINNOH_PLAYER_HOUSE_1F","SINNOH_BARRY_HOUSE",
    "SINNOH_LAKE_VERITY","SINNOH_PROFESSOR_ROWAN_LABORATORY",
]

def chunk(kind,data):
    payload=kind+data
    return struct.pack(">I",len(data))+payload+struct.pack(">I",zlib.crc32(payload)&0xffffffff)

def fake_png(width=256,height=128):
    ihdr=struct.pack(">IIBBBBB",width,height,8,6,0,0,0)
    pixels=b"".join(b"\\x00"+b"\\x00"*(width*4) for _ in range(height))
    return b"\\x89PNG\\r\\n\\x1a\\n"+chunk(b"IHDR",ihdr)+chunk(b"IDAT",zlib.compress(pixels))+chunk(b"IEND",b"")

class J10SyntheticAuthoringTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="sinnoh-j10-synthetic-")
        self.addCleanup(tmp.cleanup)
        self.project=Path(tmp.name)
        self.root=self.project/".blue-work"
        self.drafts=self.root/j10.DRAFT_DIR
        self.images=self.root/j10.TILESET_DIR
        self.drafts.mkdir(parents=True)
        self.images.mkdir()
        self.png=fake_png()
        self.pngfile=self.images/"SYNTHETIC_CI_ONLY.png"
        self.pngfile.write_bytes(self.png)
        self.catalog={"maps":[{"symbol":s,"source_id":None} for s in SYMBOLS]+[
            {"symbol":"SINNOH_TWINLEAF_TOWN","source_id":209},
            {"symbol":"SINNOH_ROUTE_201","source_id":227},
            {"symbol":"SINNOH_SANDGEM_TOWN","source_id":210},
            {"symbol":"SINNOH_ROUTE_202","source_id":228},
        ]}
        self.patcher=patch.object(j10,"source_catalog",return_value=self.catalog)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.maps={}
        for i,symbol in enumerate(SYMBOLS):
            lower=[384+(j+i)%7 for j in range(300)]
            middle=[0]*300;middle[10+i]=390+i;middle[20+i]=387
            self.maps[symbol]={
                "schema":1,"region":"SINNOH","stage":"J10","symbol":symbol,
                "kind":j10.KIND,"width":20,"height":15,"tileset_id":1,
                "tileset_png":self.pngfile.name,"tileset_sha256":j10.digest(self.png),
                "tileset_permission_reference":"SYNTHETIC_CI_NO_REAL_PERMISSION",
                "author_reference":"SYNTHETIC_CI_NOT_ORIGINAL_AUTHOR",
                "authored_by_user":True,"geometry_reviewed_locally":True,
                "layers":[lower,middle,[0]*300],
                "events":[],"destination_map_id":None,"native_gameplay_verified":False,
            }
            self.write(symbol)

    def write(self,symbol):
        (self.drafts/(symbol+".json")).write_text(json.dumps(self.maps[symbol]),encoding="utf-8")

    def mutate(self,field,value,symbol=SYMBOLS[0]):
        self.maps[symbol][field]=value
        self.write(symbol)

    def rejects(self,pattern=None):
        with self.assertRaisesRegex(ValueError,pattern or "BLOCKED"):
            j10.preflight(self.project)

    def test_01_valid_private_five_are_geometry_only(self):
        files,report=j10.preflight(self.project)
        self.assertEqual(len(files),5)
        self.assertEqual(report["native_maps_installed"],0)
        self.assertFalse(report["can_publish"])
        self.assertFalse(report["r07_mapids_approved"])
        self.assertFalse(report["r08_full_asset_rights_approved"])
        self.assertFalse(report["r09_game_exe_or_joiplay_tested"])

    def test_02_explicit_private_build_round_trips_j09_and_no_events(self):
        result=j10.private_build(self.project)
        folder=self.root/j09.STAGE_DIR
        self.assertEqual(result["actual_original_map_files_written"],5)
        self.assertEqual(len(j09.authored_five(self.project,folder,self.catalog)),5)
        for symbol in SYMBOLS:
            self.assertEqual(j09.audit_map((folder/(symbol+".rxdata")).read_bytes())["foreign_events_not_imported"],0)
        self.assertFalse(result["can_install"])

    def test_03_build_never_overwrites_existing_stage(self):
        j10.private_build(self.project)
        before={p.name:p.read_bytes() for p in (self.root/j09.STAGE_DIR).iterdir()}
        with self.assertRaisesRegex(ValueError,"NEVER_OVERWRITE"):
            j10.private_build(self.project)
        self.assertEqual(before,{p.name:p.read_bytes() for p in (self.root/j09.STAGE_DIR).iterdir()})

    def test_04_missing_draft_refused(self):
        (self.drafts/(SYMBOLS[0]+".json")).unlink()
        with self.assertRaises((OSError,ValueError)):j10.preflight(self.project)

    def test_05_missing_tileset_refused(self):
        self.pngfile.unlink()
        with self.assertRaises((OSError,ValueError)):j10.preflight(self.project)

    def test_06_mismatched_tileset_hash_refused(self):
        self.mutate("tileset_sha256","0"*64)
        self.rejects("TILESET_CHANGED")

    def test_07_wrong_png_width_refused(self):
        raw=fake_png(width=128)
        self.pngfile.write_bytes(raw)
        for symbol in SYMBOLS:
            self.maps[symbol]["tileset_sha256"]=j10.digest(raw);self.write(symbol)
        self.rejects("NOT_RMXP")

    def test_08_png_crc_tamper_refused(self):
        b=bytearray(self.png);b[29]^=0x1;self.pngfile.write_bytes(b)
        self.mutate("tileset_sha256",j10.digest(bytes(b)))
        self.rejects("HEADER_CRC")

    def test_09_png_must_not_be_random_data(self):
        raw=b"bogus"*40;self.pngfile.write_bytes(raw)
        self.mutate("tileset_sha256",j10.digest(raw))
        self.rejects("LOCAL_TILESET_PNG_INVALID")

    def test_10_nonmissing_symbol_refused(self):
        with self.assertRaisesRegex(ValueError,"NON_MISSING_MAP_SYMBOL"):
            j10.validate_draft(self.project,"SINNOH_TWINLEAF_TOWN")

    def test_11_extra_schema_field_refused(self):
        self.mutate("pretend_rights_granted",True)
        self.rejects("DRAFT_MUST")

    def test_12_forged_native_true_refused(self):
        self.mutate("native_gameplay_verified",True)
        self.rejects("DRAFT_MUST")

    def test_13_claimed_mapid_refused(self):
        self.mutate("destination_map_id",442)
        self.rejects("DRAFT_MUST")

    def test_14_foreign_event_refused(self):
        self.mutate("events",[{"id":1}])
        self.rejects("DRAFT_MUST")

    def test_15_no_author_attestation_refused(self):
        self.mutate("authored_by_user",False)
        self.rejects("DRAFT_MUST")

    def test_16_no_review_attestation_refused(self):
        self.mutate("geometry_reviewed_locally",False)
        self.rejects("DRAFT_MUST")

    def test_17_empty_permission_refused(self):
        self.mutate("tileset_permission_reference","")
        self.rejects("DRAFT_MUST")

    def test_18_html_injected_author_refused(self):
        self.mutate("author_reference","REF <script>evil</script>")
        self.rejects("DRAFT_MUST")

    def test_19_unreasonable_width_refused(self):
        self.mutate("width",500)
        self.rejects("MAP_SIZE")

    def test_20_boolean_width_refused(self):
        self.mutate("width",True)
        self.rejects("MAP_SIZE")

    def test_21_untrusted_image_path_refused(self):
        self.mutate("tileset_png","../outside.png")
        self.rejects("INVALID_TILESET_PNG")

    def test_22_invalid_tileset_id_refused(self):
        self.mutate("tileset_id",0)
        self.rejects("MAP_SIZE")

    def test_23_missing_third_layer_refused(self):
        self.mutate("layers",self.maps[SYMBOLS[0]]["layers"][:2])
        self.rejects("EXACTLY_THREE")

    def test_24_truncated_tile_array_refused(self):
        self.maps[SYMBOLS[0]]["layers"][0].pop()
        self.write(SYMBOLS[0]);self.rejects("FULL_EXPLICIT")

    def test_25_negative_tile_id_refused(self):
        self.maps[SYMBOLS[0]]["layers"][0][0]=-1
        self.write(SYMBOLS[0]);self.rejects("TILE_OUT_OF")

    def test_26_png_out_of_range_tile_refused(self):
        self.maps[SYMBOLS[0]]["layers"][0][0]=500
        self.write(SYMBOLS[0]);self.rejects("TILE_OUT_OF")

    def test_27_boolean_tile_refused(self):
        self.maps[SYMBOLS[0]]["layers"][0][0]=True
        self.write(SYMBOLS[0]);self.rejects("TILE_OUT_OF")

    def test_28_blank_placeholder_refused(self):
        self.mutate("layers",[[0]*300 for _ in range(3)])
        self.rejects("NO_MEANINGFUL")

    def test_29_sparse_terrain_refused(self):
        self.maps[SYMBOLS[0]]["layers"][0]=[384]*100+[0]*200
        self.write(SYMBOLS[0]);self.rejects("NO_MEANINGFUL")

    def test_30_no_upper_layers_refused(self):
        self.maps[SYMBOLS[0]]["layers"][1]=[0]*300
        self.write(SYMBOLS[0]);self.rejects("NO_MEANINGFUL")

    def test_31_no_distinct_tiles_refused(self):
        self.maps[SYMBOLS[0]]["layers"]=[[384]*300,[384]*300,[0]*300]
        self.write(SYMBOLS[0]);self.rejects("NO_MEANINGFUL")

    def test_32_duplicate_scenes_refused(self):
        other=copy.deepcopy(self.maps[SYMBOLS[0]])
        other["symbol"]=SYMBOLS[1];self.maps[SYMBOLS[1]]=other;self.write(SYMBOLS[1])
        self.rejects("DUPLICATE_COPIES")

    def test_33_private_output_already_symlink_blocked(self):
        folder=self.root/j09.STAGE_DIR
        try:folder.symlink_to(self.drafts,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(ValueError,"NEVER_OVERWRITE"):j10.private_build(self.project)

    def test_34_private_draft_symlink_refused(self):
        p=self.drafts/(SYMBOLS[0]+".json")
        p.unlink()
        try:p.symlink_to(self.drafts/(SYMBOLS[1]+".json"))
        except (OSError,NotImplementedError):self.skipTest("symlinks unavailable")
        self.rejects("PRIVATE_")

    def test_35_private_work_symlink_refused(self):
        self.drafts.rename(self.project/"drafts-private")
        self.root.rename(self.project/"real-work")
        try:self.root.symlink_to(self.project/"real-work",target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("symlinks unavailable")
        self.rejects("PROJECT_WORKSPACE_INVALID")

    def test_36_failed_batch_writes_no_partial_five(self):
        self.mutate("authored_by_user",False,SYMBOLS[-1])
        with self.assertRaises(ValueError):j10.private_build(self.project)
        self.assertFalse((self.root/j09.STAGE_DIR).exists())

    def test_37_catalog_changes_block_five_assumption(self):
        self.catalog["maps"][0]["source_id"]=500
        self.rejects("J02_FIVE_MISSING")

    def test_38_wrong_json_root_refused(self):
        (self.drafts/(SYMBOLS[0]+".json")).write_text("[]",encoding="utf-8")
        self.rejects("DRAFT_MUST")

    def test_39_editor_is_source_only_without_remote_upload(self):
        html=(ROOT/"site/public/sinnoh-j10-editor.html").read_text(encoding="utf-8")
        for name in SYMBOLS:self.assertIn(name,html)
        self.assertIn('destination_map_id:null',html)
        self.assertIn('native_gameplay_verified:false',html)
        self.assertNotIn("fetch(",html)
        self.assertNotIn("XMLHttpRequest",html)
        self.assertNotIn("localStorage",html)
        self.assertNotIn("game/Game.exe",html)

if __name__=="__main__":unittest.main()
