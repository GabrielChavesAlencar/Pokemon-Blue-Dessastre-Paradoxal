"""G06: synthetic-only PNG integrity and public Sinnoh rendering metadata."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_g06_render_static as g06


def chunk(tag, payload=b""):
    return (struct.pack(">I",len(payload))+tag+payload+
            struct.pack(">I",zlib.crc32(tag+payload)&0xffffffff))


def png(width=1,height=1,*,depth=8,colour=2,interlace=0,
        idat=None,filtered_rows=None,palette=None,extra_before=(),extra_after=()):
    header=struct.pack(">IIBBBBB",width,height,depth,colour,0,0,interlace)
    channels=g06.COLOUR_CHANNELS[colour]
    pass_rows=g06._passes(width,height,channels,depth,interlace)
    if idat is None and filtered_rows is None:
        packed=[]
        compressor=zlib.compressobj(level=6)
        for row_len,rows in pass_rows:
            row=b"\0"*row_len
            for _ in range(rows):
                packed.append(compressor.compress(row))
        packed.append(compressor.flush())
        idat=b"".join(packed)
    elif idat is None:
        idat=zlib.compress(filtered_rows)
    if idat is None:
        raise AssertionError("missing compressed stream")
    return (g06.PNG+chunk(b"IHDR",header)
            + (chunk(b"PLTE",palette) if palette is not None else b"")
            + b"".join(chunk(tag,raw) for tag,raw in extra_before)
            + chunk(b"IDAT",idat)
            + b"".join(chunk(tag,raw) for tag,raw in extra_after)
            +chunk(b"IEND"))


class SinnohG06RenderStaticTests(unittest.TestCase):
    def manifests(self):
        return [copy.deepcopy(g06.load_public(ROOT/"data/regions"/path))
                for path in ("sinnoh-b01-actual-native.json",
                             "sinnoh-b06-technical-candidate.json",
                             "sinnoh-b07-private-stage.json",
                             "sinnoh-b08-private-qa.json")]

    def test_01_baseline_does_not_claim_graphics_native_approval(self):
        result=g06.run()
        self.assertEqual(result["status"],
            "STATIC_RENDER_METADATA_RECONCILED_PNG_BYTES_NOT_AVAILABLE")
        self.assertEqual(result["real_png_bytes_inspected_on_github"],0)
        self.assertEqual(result["expected_private_png_count"],14)
        for field in ("real_png_crc_zlib_verified_on_github",
                      "real_png_references_checked_against_bytes_on_github",
                      "rendering_in_Game_exe_verified","android_joiplay_verified",
                      "rights_per_asset_verified","r07_complete",
                      "r08_complete","r09_complete","can_install_live_game"):
            self.assertIs(result[field],False)

    def test_02_private_tileset_indices_are_conditional_not_proven(self):
        report=g06.run()
        self.assertEqual(report["baseline_native_tileset_record_count"],70)
        self.assertEqual(report["source_tileset_ids"],[1,31])
        self.assertEqual(report["expected_private_tileset_indices_if_zero_slot_present"],[71,72])
        self.assertFalse(report["private_tileset_indices_verified_against_native_serialized_table"])
        self.assertEqual(report["expected_geometry_map_count"],54)

    def test_03_tall_textures_risk_estimation_is_not_runtime_test(self):
        report=g06.run()
        a,b=report["tall_png_render_risks"]
        self.assertEqual((a["width"],a["height"]),(256,50000))
        self.assertEqual((b["width"],b["height"]),(256,70000))
        self.assertEqual(a["pixels"],12800000)
        self.assertEqual(b["pixels"],17920000)
        self.assertTrue(a["height_exceeds_conservative_16384_side_check"])
        self.assertTrue(b["height_exceeds_conservative_16384_side_check"])
        self.assertFalse(a["gpu_runtime_compatibility_confirmed"])
        self.assertFalse(b["gpu_runtime_compatibility_confirmed"])

    def test_04_missing_png_count_or_tampered_tileset_mapping_rejected(self):
        changes=(
            lambda x:x[3].update(expected_pngs=13),
            lambda x:x[0].update(native_tileset_count=69),
            lambda x:x[1].update(source_tileset_references=[31,1]),
            lambda x:x[2].update(required_source_tilesets=[1,2]),
            lambda x:x[0].update(donor_tilesets={"1":"Fake","31":"Fake"}),
            lambda x:x[3].update(native_tilesets_sha256="0"*64),
        )
        for change in changes:
            vals=self.manifests();change(vals)
            with self.subTest(change=str(change)),self.assertRaisesRegex(ValueError,"SINNOH_G06_BLOCKED"):
                g06.audit_metadata(*vals)

    def test_05_false_gameplay_and_rights_claims_blocked(self):
        for i,field in ((2,"rights_per_asset_verified"),(2,"r07_complete"),
                        (2,"can_install_into_game"),(3,"rights_per_asset_verified"),
                        (3,"can_install"),(3,"can_mark_gameplay"),(3,"has_live_stage_evidence")):
            vals=self.manifests();vals[i][field]=True
            with self.subTest(field=field),self.assertRaises(ValueError):
                g06.audit_metadata(*vals)

    def test_06_fourteen_synthetic_pngs_have_crc_and_raster(self):
        results=[]
        for i in range(14):
            result=g06.inspect_png(png(i+1,12))
            self.assertTrue(result["crc_and_zlib_valid"])
            self.assertFalse(result["game_exe_rendered"])
            results.append(result)
        self.assertEqual(len(results),14)
        self.assertEqual(results[-1]["width"],14)

    def test_07_huge_tileset_dimensions_are_structurally_possible(self):
        for height in (50000,70000):
            with self.subTest(height=height):
                result=g06.inspect_png(png(256,height))
                self.assertEqual(result["height"],height)
                self.assertTrue(result["crc_and_zlib_valid"])
                self.assertTrue(result["high_texture_side_risk"])
                self.assertFalse(result["game_exe_rendered"])

    def test_08_corrupt_crc_is_rejected(self):
        data=bytearray(png())
        data[30] ^= 1
        with self.assertRaisesRegex(ValueError,"CRC"):
            g06.inspect_png(bytes(data))

    def test_09_missing_iend_or_idat_is_rejected(self):
        raw=png()
        with self.assertRaisesRegex(ValueError,"incompleto"):
            g06.inspect_png(raw[:-12])
        ihdr=chunk(b"IHDR",struct.pack(">IIBBBBB",1,1,8,2,0,0,0))
        with self.assertRaisesRegex(ValueError,"IEND"):
            g06.inspect_png(g06.PNG+ihdr+chunk(b"IEND"))

    def test_10_idat_zlib_stream_corrupted_even_with_valid_crc(self):
        raw=png(idat=b"not a deflate stream")
        with self.assertRaisesRegex(ValueError,"zlib"):
            g06.inspect_png(raw)

    def test_11_wrong_row_length_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"raster"):
            g06.inspect_png(png(1,1,filtered_rows=b"\0\xff\x00"))
        with self.assertRaisesRegex(ValueError,"mais bytes"):
            g06.inspect_png(png(1,1,filtered_rows=b"\0\x00\x00\x00\xff"))

    def test_12_invalid_scanline_filter_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"filtro"):
            g06.inspect_png(png(1,1,filtered_rows=b"\x05\x00\x00\x00"))

    def test_13_decompression_bomb_exceeds_header_dimensions(self):
        with self.assertRaisesRegex(ValueError,"mais bytes"):
            g06.inspect_png(png(1,1,filtered_rows=b"\0"*65537))

    def test_14_indexed_png_needs_a_valid_palette(self):
        with self.assertRaisesRegex(ValueError,"indexado"):
            g06.inspect_png(png(2,2,depth=2,colour=3))
        ok=g06.inspect_png(png(2,2,depth=2,colour=3,palette=b"\0\0\0"))
        self.assertEqual(ok["colour_type"],3)
        with self.assertRaisesRegex(ValueError,"paleta"):
            g06.inspect_png(png(2,2,depth=1,colour=3,palette=b"\0"*9))

    def test_15_illegal_color_depth_combination_rejected(self):
        for depth,colour in ((1,2),(4,6),(16,3)):
            with self.subTest(depth=depth,colour=colour),self.assertRaisesRegex(ValueError,"profundidade"):
                g06.inspect_png(png(1,1,depth=depth,colour=colour))

    def test_16_duplicate_ihdr_or_unknown_critical_chunk(self):
        raw=png()
        extra=chunk(b"IHDR",struct.pack(">IIBBBBB",1,1,8,2,0,0,0))
        with self.assertRaisesRegex(ValueError,"IHDR"):
            g06.inspect_png(raw[:33]+extra+raw[33:])
        with self.assertRaisesRegex(ValueError,"critico"):
            g06.inspect_png(raw[:33]+chunk(b"ABCD")+raw[33:])

    def test_17_idat_not_contiguous_is_rejected(self):
        original=png()
        ihdr=original[:33]
        compressed=zlib.compress(b"\0\0\0\0")
        broken=(ihdr+chunk(b"IDAT",compressed[:4])
                +chunk(b"tEXt",b"k\0v")
                +chunk(b"IDAT",compressed[4:])+chunk(b"IEND"))
        with self.assertRaisesRegex(ValueError,"IDAT"):
            g06.inspect_png(broken)

    def test_18_extra_trailing_bytes_not_allowed(self):
        with self.assertRaisesRegex(ValueError,"IEND"):
            g06.inspect_png(png()+b"host-data")

    def test_19_valid_split_idat_and_adam7_structure(self):
        raw=png()
        original=raw[33:-12]
        compressed=original[8:-4]
        split=(raw[:33]+chunk(b"IDAT",compressed[:3])
               +chunk(b"IDAT",compressed[3:])+chunk(b"IEND"))
        self.assertTrue(g06.inspect_png(split)["crc_and_zlib_valid"])
        interlaced=g06.inspect_png(png(1,1,interlace=1))
        self.assertTrue(interlaced["interlaced"])

    def test_20_missing_or_invalid_chunk_format_rejected(self):
        raw=png()
        with self.assertRaisesRegex(ValueError,"nao canonico"):
            g06.inspect_png(raw[:8]+raw[8:12]+b"aC1D"+raw[16:])
        with self.assertRaisesRegex(ValueError,"nao canonico"):
            g06.inspect_png(raw[:8]+raw[8:12]+b"AbcD"+raw[16:])

    def test_21_cli_emits_only_json_metadata_and_no_binary_assets(self):
        proc=subprocess.run([sys.executable,
            str(ROOT/"scripts/regions/audit_sinnoh_g06_render_static.py")],
            cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(proc.returncode,0,proc.stderr)
        out=json.loads(proc.stdout)
        self.assertEqual(out["stage"],"G06")
        self.assertEqual(out["phase_b_approved"],0)
        self.assertEqual(out["phase_c_approved"],0)
        self.assertEqual(out["phase_d_approved"],0)
        self.assertNotIn("png_dimensions_verified",out)
        self.assertNotIn("asset_bytes",out)


if __name__=="__main__":unittest.main()
