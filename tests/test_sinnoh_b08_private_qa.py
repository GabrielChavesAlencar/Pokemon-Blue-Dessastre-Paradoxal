"""Sinnoh B08: synthetic 54-map B07 stage, PNG references and private QA overlay."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
import zipfile
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
sys.path.insert(0,str(ROOT/"tests"))
import audit_sinnoh_b08_private_qa as b08
import build_sinnoh_b07_private_stage as b07
from sinnoh_staging_transaction import preview,stage
from stage import serialize
from server.ruby_marshal import loads
from test_sinnoh_b07_private_stage import B07Tests

def png(width=1,height=1):
    def chunk(kind,content):
        return (struct.pack(">I",len(content))+kind+content+
                struct.pack(">I",zlib.crc32(kind+content)&0xffffffff))
    header=struct.pack(">IIBBBBB",width,height,8,2,0,0,0)
    pixel=zlib.compress(b"\0\xff\0\0")
    return b08.PNG+chunk(b"IHDR",header)+chunk(b"IDAT",pixel)+chunk(b"IEND",b"")

class B08Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=b08.load(b08.CONTRACT)
        cls.c07=b08.load(b08.B07)
        cls.b06=b08.load(b08.B06)
        cls.b00=b08.load(b08.B00)
        cls.b01=b08.load(b08.B01)
        cls.b04=b08.load(b08.B04)
        cls.b05=b08.load(b08.B05)

    def fixture(self,stage_it=True):
        helper=B07Tests("test_01_metadata_preflight_never_marks_gameplay")
        self.addCleanup(helper.doCleanups)
        root,source,rows,infos,tiles=helper.fixture()
        valid=root/"source-valid-png.zip"
        with zipfile.ZipFile(source) as old,zipfile.ZipFile(valid,"w",zipfile.ZIP_DEFLATED) as new:
            for filename in old.namelist():
                raw=png() if filename.endswith(".png") else old.read(filename)
                new.writestr(filename,raw)
        files,_=b07.build_files(valid,infos,tiles,rows,source_root="Synthetic")
        dry=preview(root,b08.STAGE_LABEL,files)
        if stage_it:stage(root,b08.STAGE_LABEL,files,dry["plan_sha256"])
        return root,files,infos,tiles,dry,rows

    def check(self,files,infos,tiles,rows,**kwargs):
        return b08.audit_files(files,infos,tiles,
            [r["candidate_destination_map_id"] for r in rows],
            expected_png_count=kwargs.get("pngs",3),
            expected_cells=kwargs.get("cells",162))

    def test_01_frozen_contract_is_safe(self):
        rows=b08.check_contract(self.c,self.c07,self.b06,
                                self.b00,self.b01,self.b04,self.b05)
        self.assertEqual(len(rows),54)
        self.assertFalse(self.c["can_install"])
        self.assertFalse(self.c["has_live_stage_evidence"])

    def test_02_cli_without_stage_reports_pending(self):
        proc=subprocess.run([sys.executable,
          str(ROOT/"scripts/regions/audit_sinnoh_b08_private_qa.py")],
          cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn("B08_READY_AWAITING_LOCAL_B07_STAGE",proc.stdout)

    def test_03_54_maps_and_tileset_refs_are_audited(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        result=self.check(files,infos,tiles,rows)
        self.assertEqual(result["maps_validated"],54)
        self.assertEqual(result["nonzero_terrain_cells"],162)
        self.assertEqual(result["pngs_verified"],3)
        self.assertEqual(result["new_private_tileset_ids"],[2,3])
        self.assertEqual(sorted(result["tile_usage_by_private_id"].values()),[1,53])
        self.assertTrue(result["all_png_references_resolved"])
        self.assertFalse(result["playable"])

    def test_04_stage_manifest_matches_every_file_sha(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        original,receipt=b08.read_stage(root,b08.STAGE_LABEL,dry["plan_sha256"])
        self.assertEqual(set(original),set(files))
        self.assertEqual(receipt["plan_sha256"],dry["plan_sha256"])

    def test_05_stage_with_modified_map_is_rejected(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        path=root/dry["stage_relative_path"]/"Data/Map442.rxdata"
        path.write_bytes(b"tampered map")
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            b08.read_stage(root,b08.STAGE_LABEL,dry["plan_sha256"])

    def test_06_stage_with_extra_script_is_rejected(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        (root/dry["stage_relative_path"]/"EVIL.RB").write_text("evil")
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            b08.read_stage(root,b08.STAGE_LABEL,dry["plan_sha256"])

    def test_07_forged_stage_receipt_rejected(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        manifest=root/dry["stage_relative_path"]/"stage-manifest.json"
        obj=json.loads(manifest.read_text("utf-8"))
        obj["may_install_into_game"]=True
        manifest.write_text(json.dumps(obj),encoding="utf-8")
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            b08.read_stage(root,b08.STAGE_LABEL,dry["plan_sha256"])

    def test_08_corrupt_png_crc_rejected(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        changed=copy.copy(files)
        key=next(k for k in files if k.endswith(".png"))
        raw=bytearray(files[key]);raw[-8]^=1
        changed[key]=bytes(raw)
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            self.check(changed,infos,tiles,rows)

    def test_09_true_sinnoh_tall_tileset_height_is_supported(self):
        # Some actual source PNGs are 256x50000 and 256x70000.
        self.assertEqual(b08.png_geometry(png(256,70000)),(256,70000))
        self.assertEqual(b08.png_geometry(png(256,50000)),(256,50000))

    def test_10_missing_png_reference_rejected(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        altered=copy.copy(files)
        changed=loads(files["Data/Tilesets.rxdata"])
        changed[2].attrs["@tileset_name"]=b"Nonexistent"
        altered["Data/Tilesets.rxdata"]=serialize(changed)
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            self.check(altered,infos,tiles,rows)

    def test_11_extra_unused_png_rejected(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        extra=copy.copy(files);raw=png(2,2)
        extra[f"Graphics/Tilesets/SN_B07_{b08.sha(raw)[:16]}_Unused.png"]=raw
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            self.check(extra,infos,tiles,rows,pngs=4)

    def test_12_native_tileset_cannot_be_overwritten(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        altered=copy.copy(files)
        collection=loads(files["Data/Tilesets.rxdata"])
        collection[1].attrs["@name"]=b"changed-native"
        altered["Data/Tilesets.rxdata"]=serialize(collection)
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            self.check(altered,infos,tiles,rows)

    def test_13_map_with_events_rejected(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        altered=copy.copy(files)
        value=loads(files["Data/Map442.rxdata"])
        value.attrs["@events"]={1:b"donor"}
        altered["Data/Map442.rxdata"]=serialize(value)
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            self.check(altered,infos,tiles,rows)

    def test_14_wrong_terrain_count_rejected(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            self.check(files,infos,tiles,rows,cells=999)

    def test_15_invalid_tile_id_rejected(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        altered=copy.copy(files)
        obj=loads(files["Data/Map442.rxdata"])
        obj.attrs["@tileset_id"]=31
        altered["Data/Map442.rxdata"]=serialize(obj)
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            self.check(altered,infos,tiles,rows)

    def test_16_qa_overlay_requires_verified_live_baseline(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        result=self.check(files,infos,tiles,rows)
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            b08.prepare_qa(root,dry["plan_sha256"],files,result)
        self.assertFalse((root/".blue-work/sinnoh-b08-qa").exists())

    def test_17_create_private_overlay_and_preserve_live_game(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        data=root/"game"/"Data";data.mkdir(parents=True)
        (data/"MapInfos.rxdata").write_bytes(infos)
        (data/"Tilesets.rxdata").write_bytes(tiles)
        (data/"Map001.rxdata").write_bytes(b"native map")
        before={x.name:hashlib.sha256(x.read_bytes()).hexdigest()
                for x in data.iterdir() if x.is_file()}
        snap={"mapinfos_sha256":b08.sha(infos),"tilesets_sha256":b08.sha(tiles)}
        verified=b07.check_current_game(data,snap,[1])
        result=self.check(files,infos,tiles,rows)
        receipt=b08.prepare_qa(root,dry["plan_sha256"],files,result,
                               live_game_verified=verified["actual_game_data_verified_against_b01"])
        self.assertEqual(receipt["files_copied"],len(files))
        output=root/receipt["relative_path"]
        self.assertEqual((output/"Data/Map442.rxdata").read_bytes(),
                         files["Data/Map442.rxdata"])
        self.assertFalse((output/"Game.exe").exists())
        self.assertFalse((output/"Save01.rxdata").exists())
        manifest=json.loads((output/"qa-overlay-manifest.json").read_text("utf-8"))
        self.assertFalse(manifest["may_copy_into_live_game"])
        self.assertFalse(manifest["rights_verified"])
        self.assertEqual({x.name:hashlib.sha256(x.read_bytes()).hexdigest()
                          for x in data.iterdir() if x.is_file()},before)

    def test_18_duplicate_qa_overlay_cannot_overwrite(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        info=self.check(files,infos,tiles,rows)
        b08.prepare_qa(root,dry["plan_sha256"],files,info,
                       live_game_verified=True)
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            b08.prepare_qa(root,dry["plan_sha256"],files,info,
                           live_game_verified=True)

    def test_19_stale_live_game_data_rejected(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        data=root/"game"/"Data";data.mkdir(parents=True)
        (data/"MapInfos.rxdata").write_bytes(b"changed")
        (data/"Tilesets.rxdata").write_bytes(tiles)
        with self.assertRaises(ValueError):
            b07.check_current_game(data,{"mapinfos_sha256":b08.sha(infos),
                          "tilesets_sha256":b08.sha(tiles)},[])

    def test_20_missing_stage_prevents_qa(self):
        root,files,infos,tiles,dry,rows=self.fixture(stage_it=False)
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            b08.latest_stage(root,b08.STAGE_LABEL)

    def test_21_false_rights_approval_in_contract_blocked(self):
        m=copy.deepcopy(self.c);m["r07_complete"]=True
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            b08.check_contract(m,self.c07,self.b06,self.b00,
                               self.b01,self.b04,self.b05)

    def test_22_unexpected_staged_map_id_rejected(self):
        root,files,infos,tiles,dry,rows=self.fixture()
        altered=copy.copy(files)
        altered["Data/Map496.rxdata"]=files["Data/Map495.rxdata"]
        with self.assertRaisesRegex(ValueError,"SINNOH_B08_BLOCKED"):
            self.check(altered,infos,tiles,rows)

if __name__=="__main__":unittest.main()
