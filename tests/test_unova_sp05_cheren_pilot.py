"""SP05 isolated Cheren QA: synthetic sprite sheets, hashes and safety gates."""
from __future__ import annotations
import argparse
import hashlib
import json
import shutil
import struct
import sys
import tempfile
import unittest
import zipfile
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_sprite_pack as sprite
import audit_unova_sp04_npcs as npc
import unova_sp05_cheren_pilot as pilot

PROJECT_FILES=(
    "data/regions/unova-sp05-cheren-pilot.json",
    "data/regions/unova-sp04-npcs.json",
    "data/regions/unova-u03-areas.json",
    "data/regions/unova-e06-e07-preparation.json",
    "site/public/data/regions.json",
)
MEMBER="Graphics/Characters/Cheren.png"


def chunk(name: bytes,payload:bytes)->bytes:
    return (struct.pack(">I",len(payload))+name+payload+
            struct.pack(">I",zlib.crc32(name+payload)&0xffffffff))


def png_sheet(size=128, body_w=13,body_h=24,blank=None,opaque=True,variant=0):
    """Synthetic RGBA8 sprite; every 4x4 cell has a silhouette, not a Pokemon asset."""
    width=height=size
    cell=size//4
    raw=bytearray()
    for y in range(height):
        row=bytearray([0])
        fr=y//cell
        yy=y%cell
        for x in range(width):
            col=x//cell
            xx=x%cell
            visible=(fr,col)!=blank and (2<=yy<2+body_h) and (3<=xx<3+body_w)
            alpha=255 if visible and opaque else 0
            row.extend([30+variant%100,100,150,alpha])
        raw.extend(row)
    return (b"\x89PNG\r\n\x1a\n"
            +chunk(b"IHDR",struct.pack(">IIBBBBB",width,height,8,6,0,0,0))
            +chunk(b"IDAT",zlib.compress(bytes(raw)))
            +chunk(b"IEND",b""))


def cmd_args(test,**updates):
    a=dict(project=test.project,zip=test.zip,member=MEMBER,sp03=test.sp03,
           sp04=test.sp04,reference_sprite=test.ref,rights_evidence=test.rights,
           rights_holder="Example creator for QA",source_url="https://eeveeexpo.com/resources/25/")
    a.update(updates)
    return argparse.Namespace(**a)


class CherenPilotTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="unova-sp05-")
        self.addCleanup(tmp.cleanup)
        self.tmp=Path(tmp.name)
        self.project=self.tmp/"project"
        self.project.mkdir()
        for f in PROJECT_FILES:
            dest=self.project/f
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/f,dest)
        self.zip=self.tmp/"Gen5OW.zip"
        self.ref=self.tmp/"Decades/Graphics/Characters/reference.png"
        self.ref.parent.mkdir(parents=True)
        self.ref.write_bytes(png_sheet())
        self.rights=self.tmp/"rights-note.txt"
        self.rights.write_text(
            "This is SYNTHETIC test evidence only; NOT a real sprite use authorization.",
            encoding="utf-8")
        self.create()

    def create(self, png=None, name=MEMBER, additional=None):
        if png is None:
            png=png_sheet()
        with zipfile.ZipFile(self.zip,"w",zipfile.ZIP_DEFLATED) as z:
            z.writestr(name,png)
            if additional:
                for n,v in additional.items():
                    z.writestr(n,v)
        self.sp03=sprite.save_report(self.project,sprite.audit(self.zip))
        report=npc.merge(
            npc.read_json(self.project/PROJECT_FILES[1]),
            npc.read_json(self.project/PROJECT_FILES[2]),
            npc.read_json(self.project/PROJECT_FILES[3]),
            npc.read_json(self.project/PROJECT_FILES[4]),
            npc.read_sp03(self.project,self.sp03)
        )
        self.sp04=npc.save(self.project,report)
        return report

    def test_01_plan_is_blocked_without_source_or_rights(self):
        p=pilot.plan(self.project)
        self.assertEqual(p["status"],"BLOCKED_MISSING_AUTHOR_SOURCE_AND_NATIVE_QA")
        self.assertFalse(p["can_install"])
        self.assertFalse(p["sprite_selected"])
        self.assertFalse(p["game_exe_tested"])
        self.assertFalse(p["android_tested"])

    def test_02_local_qa_stage_matches_sp03_sp04_and_reference(self):
        r=pilot.stage(cmd_args(self))
        self.assertEqual(r["phase"],"SP05")
        self.assertEqual(r["status"],"LOCAL_QA_ASSET_STAGED_PENDING_MANUAL_SIGNOFF")
        self.assertEqual(r["visible_height_ratio"],1.0)
        self.assertEqual(r["visible_width_ratio"],1.0)
        self.assertEqual(r["sprite_metrics"]["frame_count"],16)
        self.assertEqual(len(r["sprite_metrics"]["direction_row_metrics"]),4)
        self.assertTrue(r["rights_evidence_present_not_authenticated"])
        self.assertFalse(r["rights_verified"])
        self.assertFalse(r["redistribution_approved"])
        self.assertFalse(r["can_install"])
        self.assertFalse(r["directions_visually_verified"])
        self.assertFalse(r["game_exe_tested"])
        self.assertFalse(r["android_tested"])
        staged=self.project/r["private_qa_directory"]/pilot.DEST
        self.assertEqual(staged.read_bytes(),png_sheet())
        self.assertEqual(self.ref.read_bytes(),png_sheet())
        self.assertFalse((self.project/"game").exists())
        self.assertFalse((self.project/"Graphics").exists())

    def test_03_idempotent_private_staging(self):
        first=pilot.stage(cmd_args(self))
        second=pilot.stage(cmd_args(self))
        self.assertEqual(first,second)
        self.assertTrue((self.project/first["private_qa_directory"]/"sp05-cheren-qa.json").exists())

    def test_04_missing_rights_document_blocks(self):
        self.rights.unlink()
        with self.assertRaises(ValueError):
            pilot.stage(cmd_args(self))
        self.assertFalse((self.project/"game").exists())

    def test_05_short_rights_document_blocks(self):
        self.rights.write_text("OK")
        with self.assertRaisesRegex(ValueError,"insuficiente"):
            pilot.stage(cmd_args(self))

    def test_06_missing_decades_reference_blocks(self):
        self.ref.unlink()
        with self.assertRaises(ValueError):
            pilot.stage(cmd_args(self))

    def test_07_scale_height_too_large_is_blocked(self):
        self.ref.write_bytes(png_sheet(body_w=13,body_h=10))
        with self.assertRaisesRegex(ValueError,"altura visível"):
            pilot.stage(cmd_args(self))

    def test_08_scale_width_too_large_is_blocked(self):
        self.ref.write_bytes(png_sheet(body_w=5,body_h=24))
        with self.assertRaisesRegex(ValueError,"largura visível"):
            pilot.stage(cmd_args(self))

    def test_09_missing_frame_in_down_direction_blocks(self):
        self.create(png_sheet(blank=(0,2)))
        with self.assertRaisesRegex(ValueError,"quadro invisível"):
            pilot.stage(cmd_args(self))

    def test_10_all_transparent_frames_block(self):
        self.create(png_sheet(opaque=False))
        with self.assertRaisesRegex(ValueError,"quadro invisível"):
            pilot.stage(cmd_args(self))

    def test_11_wrong_sheet_not_multiple_of_four_blocks(self):
        with self.assertRaises(ValueError):
            pilot.rgba_pixels(png_sheet(size=132)[:-12])

    def test_12_png_invalid_CRC_blocks(self):
        a=bytearray(png_sheet())
        a[16]^=1
        with self.assertRaises(ValueError):
            pilot.measure_sheet(bytes(a))

    def test_13_sp03_zip_hash_mismatch_blocks(self):
        self.create(png_sheet(variant=22))
        # Recreate another ZIP with same name, different content, leaving audits old.
        with zipfile.ZipFile(self.zip,"w") as z:
            z.writestr(MEMBER,png_sheet(variant=42))
        with self.assertRaises(ValueError):
            pilot.stage(cmd_args(self))

    def test_14_member_must_be_cheren_candidate(self):
        self.create(additional={"Graphics/Characters/Bianca.png":png_sheet(variant=2)})
        with self.assertRaises(ValueError):
            pilot.stage(cmd_args(self,member="Graphics/Characters/Bianca.png"))

    def test_15_tampered_sp04_report_blocks(self):
        data=json.loads(self.sp04.read_text("utf-8"))
        data["npcs"][0]["game_exe_tested"]=True
        self.sp04.write_text(json.dumps(data),encoding="utf-8")
        with self.assertRaises(ValueError):
            pilot.stage(cmd_args(self))

    def test_16_sp04_report_cannot_be_outside_private_workspace(self):
        elsewhere=self.tmp/"fake.json"
        elsewhere.write_bytes(self.sp04.read_bytes())
        with self.assertRaises(ValueError):
            pilot.stage(cmd_args(self,sp04=elsewhere))

    def test_17_bad_source_url_blocks(self):
        with self.assertRaisesRegex(ValueError,"HTTPS"):
            pilot.stage(cmd_args(self,source_url="http://untrusted.local"))

    def test_18_missing_rights_holder_blocks(self):
        with self.assertRaises(ValueError):
            pilot.stage(cmd_args(self,rights_holder=""))

    def test_19_reject_non_PNG_member(self):
        with self.assertRaises(ValueError):
            pilot.stage(cmd_args(self,member="Characters/Cheren.gif"))

    def test_20_rgba_decoder_preserves_16_frame_geometry(self):
        info=pilot.measure_sheet(png_sheet())
        self.assertEqual(info["cell_width"],32)
        self.assertEqual(info["cell_height"],32)
        self.assertEqual(info["visible_height_median"],24)
        self.assertEqual(info["visible_width_median"],13)
        self.assertEqual(len(info["frame_metrics"]),16)

    def test_21_missing_roster_blocked(self):
        (self.project/PROJECT_FILES[1]).unlink()
        with self.assertRaises(ValueError):
            pilot.plan(self.project)

    def test_22_do_not_overwrite_existing_qa_file(self):
        r=pilot.stage(cmd_args(self))
        image=self.project/r["private_qa_directory"]/pilot.DEST
        image.write_bytes(b"existing precious user content")
        with self.assertRaises(ValueError):
            pilot.stage(cmd_args(self))
        self.assertEqual(image.read_bytes(),b"existing precious user content")

    def test_23_do_not_follow_private_qa_symlink(self):
        work=self.project/".blue-work"
        outside=self.tmp/"outside"
        outside.mkdir()
        # Remove empty workspace and replace it with symlink.
        shutil.rmtree(work)
        try:
            work.symlink_to(outside,target_is_directory=True)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaises(ValueError):
            pilot.private_stage_dir(self.project,"a"*64)
        self.assertFalse((outside/"unova").exists())

    def test_24_reference_image_never_modified(self):
        before=self.ref.read_bytes()
        pilot.stage(cmd_args(self))
        self.assertEqual(before,self.ref.read_bytes())

    def test_25_no_member_path_traversal(self):
        with self.assertRaises(ValueError):
            pilot.stage(cmd_args(self,member="../game/data/Cheren.png"))

    def test_26_no_entitlements_from_rights_note(self):
        result=pilot.stage(cmd_args(self))
        # Synthetic "rights note" is not proof of actual author consent.
        self.assertFalse(result["rights_verified"])
        self.assertFalse(result["native_scale_verified"])
        self.assertFalse(result["npc_event_installed"])
        self.assertFalse(result["map_id_assigned"])

    def test_27_bad_policy_cannot_enable_install(self):
        p=self.project/PROJECT_FILES[0]
        doc=json.loads(p.read_text("utf-8"))
        doc["can_install"]=True
        p.write_text(json.dumps(doc))
        with self.assertRaises(ValueError):
            pilot.plan(self.project)

    def test_28_bad_policy_cannot_disable_visual_review(self):
        p=self.project/PROJECT_FILES[0]
        doc=json.loads(p.read_text("utf-8"))
        doc["scale_policy"]["visual_signoff_required"]=False
        p.write_text(json.dumps(doc))
        with self.assertRaises(ValueError):
            pilot.plan(self.project)

    def test_29_cli_plan_succeeds_without_pack_or_install(self):
        import contextlib,io
        stdout=io.StringIO()
        with contextlib.redirect_stdout(stdout):
            ret=pilot.main(["--project",str(self.project)])
        self.assertEqual(ret,0)
        self.assertIn("BLOCKED_MISSING_AUTHOR_SOURCE_AND_NATIVE_QA",stdout.getvalue())
        self.assertFalse((self.project/"Graphics").exists())

    def test_30_cli_stage_no_args_fails_closed(self):
        import contextlib,io
        with contextlib.redirect_stderr(io.StringIO()):
            ret=pilot.main(["--project",str(self.project),"--stage"])
        self.assertEqual(ret,2)

if __name__=="__main__":
    unittest.main()
