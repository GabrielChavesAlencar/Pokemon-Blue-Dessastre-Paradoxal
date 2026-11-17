"""Unova sprite packs: metadata-only synthetic ZIP and Decades reference tests."""
from __future__ import annotations

import hashlib
import json
import stat
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_sprite_pack as audit


def chunk(name: bytes, payload: bytes) -> bytes:
    return (struct.pack(">I",len(payload))+name+payload+
            struct.pack(">I",zlib.crc32(name+payload)&0xffffffff))


def png(w=128,h=128,rgba=True,apng_frames=0):
    color=6 if rgba else 2
    ihdr=struct.pack(">IIBBBBB",w,h,8,color,0,0,0)
    channels=4 if rgba else 3
    raw=(b"\0"+bytes(channels*w))*h if w*h<=300_000 else b"\0\0"
    result=b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR",ihdr)
    if apng_frames:
        result+=chunk(b"acTL",struct.pack(">II",apng_frames,0))
    result+=chunk(b"IDAT",zlib.compress(raw))+chunk(b"IEND",b"")
    return result


def gif(frames=2):
    header=(b"GIF89a"+struct.pack("<HHBBB",1,1,0x80,0,0)+
            b"\x00\x00\x00\xff\xff\xff")
    image=b"\x2c"+struct.pack("<HHHHB",0,0,1,1,0)+b"\x02\x02\x44\x01\x00"
    gce=b"\x21\xf9\x04\x01\x05\x00\x00\x00"
    return header+(gce+image)*frames+b"\x3b"


class SpritePackTests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(prefix="unova-sprites-")
        self.addCleanup(t.cleanup)
        self.base=Path(t.name)
        self.project=self.base/"project"
        self.project.mkdir()
        self.source=self.base/"Gen5_Overworld_Pack.zip"

    def pack(self, entries=None):
        if entries is None:
            entries={
                "Gen5/Graphics/Characters/Cheren.png":png(128,128),
                "Gen5/Graphics/Characters/Bianca.png":png(120,128),
                "Gen5/Graphics/Characters/N.png":png(128,128),
                "Gen5/Graphics/Characters/Team_Plasma.gif":gif(3),
                "Gen5/Readme.txt":b"Please verify licensing before use",
            }
        with zipfile.ZipFile(self.source,"w",compression=zipfile.ZIP_DEFLATED) as f:
            for name,body in entries.items():
                f.writestr(name,body)
        return self.source

    def test_01_identifies_characters_png_gif_and_animations(self):
        r=audit.audit(self.pack())
        self.assertEqual(r["supported_images"],4)
        self.assertEqual(r["invalid_images"],[])
        self.assertEqual(r["status"],"SPRITES_AUDITED_NOT_LICENSED_OR_INSTALLED")
        self.assertIn("CHEREN",r["characters_by_filename_candidates"])
        self.assertIn("BIANCA",r["characters_by_filename_candidates"])
        self.assertIn("N",r["characters_by_filename_candidates"])
        self.assertIn("TEAM_PLASMA",r["characters_by_filename_candidates"])
        gif_row=next(x for x in r["images"] if x["format"]=="GIF")
        self.assertEqual(gif_row["animation_frames_declared"],3)
        self.assertEqual(gif_row["delays_ms_declared"],[50,50,50])
        self.assertFalse(gif_row["animation_decoded"])
        self.assertEqual(r["reference_status"],"NOT_PROVIDED")
        self.assertFalse(r["can_install"])
        self.assertFalse(r["rights_verified"])
        self.assertFalse(r["game_or_saves_modified"])
        self.assertFalse((self.project/"game").exists())

    def test_02_rmxp_four_by_four_candidate(self):
        r=audit.audit(self.pack({"Characters/Juniper.png":png(128,128)}))
        guesses=r["images"][0]["sheet_layout_candidates"]
        self.assertEqual(len(guesses),1)
        self.assertEqual(guesses[0]["columns"],4)
        self.assertEqual(guesses[0]["cell_height"],32)
        self.assertFalse(r["images"][0]["native_four_direction_layout_verified"])

    def test_03_sheet_can_be_ambiguous_3x4_or_4x4(self):
        r=audit.audit(self.pack({"Characters/Chili.png":png(120,128)}))
        guesses=r["images"][0]["sheet_layout_candidates"]
        self.assertEqual(len(guesses),2)
        self.assertIn("LAYOUT_AMBIGUOUS_4X4_VS_3X4",r["images"][0]["warnings"])

    def test_04_n_only_exact_filename_not_within_another_word(self):
        r=audit.audit(self.pack({
            "Characters/N.png":png(),
            "Characters/Neptune.png":png(),
            "Characters/Marnie.png":png(),
        }))
        self.assertEqual(r["characters_by_filename_candidates"]["N"],["Characters/N.png"])

    def test_05_duplicate_bytes_different_filenames_are_flagged(self):
        b=png()
        r=audit.audit(self.pack({"A/Cheren.png":b,"B/Bianca.png":b}))
        self.assertEqual(len(r["duplicate_content_groups"]),1)
        self.assertEqual(len(r["duplicate_content_groups"][0]["paths"]),2)

    def test_06_same_basename_different_bytes_flagged(self):
        r=audit.audit(self.pack({"A/Cheren.png":png(64,64),"B/Cheren.png":png(128,128)}))
        self.assertEqual(len(r["same_basename_collisions"]),1)
        self.assertEqual(r["same_basename_collisions"][0]["basename_casefold"],"cheren")

    def test_07_same_full_path_different_case_rejected(self):
        with zipfile.ZipFile(self.source,"w") as z:
            z.writestr("Characters/CHEREN.png",png())
            z.writestr("characters/cheren.PNG",png())
        with self.assertRaisesRegex(ValueError,"duplicacao"):
            audit.audit(self.source)

    def test_08_zip_traversal_rejected(self):
        with self.assertRaises(ValueError):
            audit.audit(self.pack({"../game/Data/Map001.rxdata":b"x","A/N.png":png()}))

    def test_09_absolute_windows_path_rejected(self):
        with self.assertRaises(ValueError):
            audit.audit(self.pack({"C:/Windows/evil.png":png()}))

    def test_10_embedded_symlink_member_rejected(self):
        with zipfile.ZipFile(self.source,"w") as z:
            info=zipfile.ZipInfo("Characters/N.png")
            info.create_system=3
            info.external_attr=(stat.S_IFLNK|0o777)<<16
            z.writestr(info,b"../../game")
        with self.assertRaisesRegex(ValueError,"link simbolico"):
            audit.audit(self.source)

    def test_11_corrupt_png_blocked_not_installed(self):
        broken=png()[:-2]+b"\x00\x00"
        r=audit.audit(self.pack({"Characters/Cheren.png":broken,"Characters/Bianca.png":png()}))
        self.assertEqual(r["supported_images"],1)
        self.assertEqual(len(r["invalid_images"]),1)
        self.assertEqual(r["status"],"SPRITES_WITH_INVALID_FILES_NEED_REVIEW")
        self.assertFalse(r["can_install"])
        self.assertFalse((self.project/"game").exists())

    def test_12_no_valid_image_rejected(self):
        with self.assertRaises(ValueError):
            audit.audit(self.pack({"Characters/N.png":b"not png"}))

    def test_13_png_truncated_rejected(self):
        with self.assertRaises(ValueError):
            audit.inspect_png(png()[:-8])

    def test_14_png_oversize_dimensions_rejected(self):
        with self.assertRaises(ValueError):
            audit.inspect_png(png(8193,64))

    def test_15_png_apng_declared_frames(self):
        r=audit.audit(self.pack({"Characters/N.png":png(128,128,apng_frames=5)}))
        x=r["images"][0]
        self.assertEqual(x["format"],"APNG")
        self.assertEqual(x["animation_frames_declared"],5)
        self.assertEqual(x["sheet_layout_candidates"],[])
        self.assertFalse(x["native_animation_playback_verified"])

    def test_16_gif_two_frames_detected(self):
        r=audit.audit(self.pack({"Characters/Team_Plasma.gif":gif(2)}))
        self.assertEqual(r["images"][0]["animation_frames_declared"],2)
        self.assertEqual(r["images"][0]["delays_ms_declared"],[50,50])

    def test_17_gif_truncated_rejected(self):
        with self.assertRaises(ValueError):
            audit.inspect_gif(gif()[:-1])

    def test_18_unsupported_images_not_converted_or_extracted(self):
        r=audit.audit(self.pack({"Characters/N.png":png(),"Characters/Trainer.webp":b"webp"}))
        self.assertEqual(r["supported_images"],1)
        self.assertEqual(r["unsupported_image_paths"],["Characters/Trainer.webp"])

    def test_19_baseline_name_collision_and_scale_warning(self):
        ref=self.base/"Decades/Graphics/Characters"
        ref.mkdir(parents=True)
        (ref/"Cheren.png").write_bytes(png(64,64))
        r=audit.audit(self.pack({"Characters/Cheren.png":png(128,128)}),ref)
        x=r["images"][0]
        self.assertEqual(r["reference_status"],"SCANNED_READ_ONLY")
        self.assertEqual(x["decades_same_basename_matches"],1)
        self.assertIn("EXISTING_DECADES_BASENAME_COLLISION_DO_NOT_OVERWRITE",x["warnings"])
        self.assertIn("POTENTIAL_DIMENSION_MISMATCH",x["warnings"])
        self.assertIn("POTENTIAL_FRAME_SCALE_MISMATCH",x["warnings"])
        self.assertEqual(x["candidate_cell_height_ratio_to_first_decades_match"],2)
        self.assertFalse(x["installable"])
        self.assertEqual((ref/"Cheren.png").read_bytes(),png(64,64))

    def test_20_baseline_no_match_does_not_claim_native_compatibility(self):
        ref=self.base/"Decades/Graphics/Characters"
        ref.mkdir(parents=True)
        (ref/"NPC.png").write_bytes(png(128,128))
        r=audit.audit(self.pack({"Characters/Bianca.png":png(128,128)}),ref)
        x=r["images"][0]
        self.assertEqual(x["decades_same_basename_matches"],0)
        self.assertFalse(x["native_four_direction_layout_verified"])

    def test_21_symlink_baseline_rejected(self):
        ref=self.base/"ref"
        ref.mkdir()
        link=self.base/"link"
        try:
            link.symlink_to(ref,target_is_directory=True)
        except OSError:
            self.skipTest("symlinks not supported")
        with self.assertRaises(ValueError):
            audit.audit(self.pack(),link)

    def test_22_untrusted_baseline_sprite_symlink_rejected(self):
        ref=self.base/"ref"
        ref.mkdir()
        external=self.base/"external.png"
        external.write_bytes(png())
        try:
            (ref/"NPC.png").symlink_to(external)
        except OSError:
            self.skipTest("symlinks not supported")
        with self.assertRaises(ValueError):
            audit.audit(self.pack(),ref)

    def test_23_report_only_in_private_directory_and_idempotent(self):
        r=audit.audit(self.pack())
        path=audit.save_report(self.project,r)
        self.assertTrue(path.is_relative_to(self.project/".blue-work/unova/audit/sprite-packs"))
        first=path.read_bytes()
        audit.save_report(self.project,r)
        self.assertEqual(first,path.read_bytes())
        with self.assertRaises(ValueError):
            audit.save_report(self.project,dict(r,status="INSTALLED"))
        self.assertEqual(first,path.read_bytes())
        self.assertFalse((self.project/"game").exists())

    def test_24_symlink_output_directory_rejected(self):
        (self.project/".blue-work/unova/audit").mkdir(parents=True)
        external=self.base/"ex"
        external.mkdir()
        try:
            (self.project/".blue-work/unova/audit/sprite-packs").symlink_to(
                external,target_is_directory=True)
        except OSError:
            self.skipTest("symlinks not supported")
        with self.assertRaises(ValueError):
            audit.save_report(self.project,audit.audit(self.pack()))

    def test_25_missing_zip_blocked(self):
        with self.assertRaises(ValueError):
            audit.audit(self.source)

    def test_26_zip_with_only_txt_files_blocked(self):
        with self.assertRaises(ValueError):
            audit.audit(self.pack({"readme.txt":b"no images"}))

    def test_27_gif_transparency_metadata_in_report(self):
        x=audit.audit(self.pack({"Characters/Plasma.gif":gif()}))["images"][0]
        self.assertTrue(x["transparency_possible"])
        self.assertFalse(x["rights_verified"])

    def test_28_optional_reference_not_provided_is_explicit(self):
        r=audit.audit(self.pack())
        self.assertFalse(r["reference_files_scanned"])
        self.assertEqual(r["reference_status"],"NOT_PROVIDED")
        self.assertIsNone(r["reference_typical_4x4_cell_height"])

if __name__=="__main__":
    unittest.main()
