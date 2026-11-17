"""Unova SP04: rigorous synthetic NPC roster & safe SP03 sprite-report join."""
from __future__ import annotations
import copy
import hashlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout,redirect_stderr
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_sp04_npcs as sp04

FILES=("data/regions/unova-sp04-npcs.json",
       "data/regions/unova-u03-areas.json",
       "data/regions/unova-e06-e07-preparation.json",
       "site/public/data/regions.json")


class UnovaNPCCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=sp04.read_json(ROOT/FILES[0])
        cls.areas=sp04.read_json(ROOT/FILES[1])
        cls.trainers=sp04.read_json(ROOT/FILES[2])
        cls.regions=sp04.read_json(ROOT/FILES[3])

    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="unova-sp04-npcs-")
        self.addCleanup(tmp.cleanup)
        self.project=Path(tmp.name)
        for relative in FILES:
            dest=self.project/relative
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/relative,dest)
        self.sp03_dir=self.project/sp04.SP03_DIR
        self.sp03_dir.mkdir(parents=True)
        self.archive_sha="a"*64
        self.source=self.sp03_dir/("sprites-"+self.archive_sha[:16]+".json")

    def roster(self):
        return copy.deepcopy(self.catalog)

    def base_report(self,imgs):
        return {
            "schema":1,"region":"UNOVA","phase":"SPRITE_AUDIT_SP03",
            "mode":"PRIVATE_SPRITE_PACK_METADATA_INSPECTION_NO_EXTRACTION",
            "status":"SPRITES_AUDITED_NOT_LICENSED_OR_INSTALLED",
            "archive_sha256":self.archive_sha,
            "supported_images":len(imgs),"images":imgs,"invalid_images":[],
            "rights_verified":False,"may_redistribute":False,
            "game_exe_tested":False,"android_tested":False,
            "game_or_saves_modified":False,"can_install":False,
        }

    def img(self,path,chars=None,kind="OVERWORLD_SHEET_CANDIDATE",width=128,height=128):
        return {
            "path":path,"sha256":hashlib.sha256(path.encode()).hexdigest(),
            "format":"PNG","width":width,"height":height,
            "animation_frames_declared":1,
            "sprite_kind_candidate":kind,
            "sheet_layout_candidates":[{
                "layout_candidate":"RMXP_4_COLUMNS_4_DIRECTIONS_CANDIDATE",
                "columns":4,"direction_rows":4,
                "cell_width":width//4,"cell_height":height//4}],
            "character_name_candidates":chars or [],
            "warnings":[],
            "decades_same_basename_matches":0,
            "native_four_direction_layout_verified":False,
            "native_animation_playback_verified":False,
            "rights_verified":False,"installable":False,
        }

    def write_audit(self,imgs):
        self.source.write_text(json.dumps(self.base_report(imgs)),encoding="utf-8")
        return self.source

    def joined(self,report=None,roster=None):
        return sp04.merge(roster or self.roster(),self.areas,self.trainers,self.regions,report)

    def person(self,result,key):
        return next(x for x in result["npcs"] if x["npc_key"]=="UNOVA_NPC_"+key)

    def invalid_roster(self,change):
        c=self.roster()
        change(c)
        with self.assertRaises(ValueError):
            self.joined(roster=c)

    def test_01_catalog_73_planned_and_19_trainer_refs(self):
        r=self.joined()
        self.assertEqual(r["roster_entries"],73)
        self.assertEqual(len(r["npcs"]),73)
        self.assertEqual(sum(bool(row["trainer_reference_key"]) for row in r["npcs"]),19)
        self.assertEqual(r["status_counts"],{"NO_PACK_AUDIT":73})
        self.assertEqual(r["candidate_npcs_count"],0)
        self.assertIsNone(r["source_sprite_report_sha256"])
        self.assertFalse(r["can_install"])
        self.assertFalse(r["rights_verified"])

    def test_02_white_iris_black_drayden_protected(self):
        self.assertEqual(self.person(self.joined(),"IRIS")["role"],"GYM_LEADER")
        self.assertEqual(self.person(self.joined(),"DRAYDEN")["story_scope"],
                         "BLACK_ONLY_VARIANT")
        self.invalid_roster(lambda c: next(x for x in c["characters"]
              if x["key"]=="UNOVA_NPC_DRAYDEN").update(role="GYM_LEADER"))

    def test_03_npc_name_exact_from_sp03(self):
        doc=self.base_report([self.img("Graphics/Characters/Cheren.png",["CHEREN"])])
        r=self.joined(doc)
        ch=self.person(r,"CHEREN")
        self.assertEqual(ch["candidate_count"],1)
        self.assertEqual(ch["status"],"SINGLE_CANDIDATE_MANUAL_REVIEW")
        self.assertFalse(ch["sprite_selection_approved"])
        self.assertFalse(ch["license_verified"])
        self.assertFalse(ch["npc_installed"])
        self.assertFalse(r["can_install"])

    def test_04_alias_matches_named_sage_not_recognized_by_sp03(self):
        doc=self.base_report([self.img("Overworld/Rood.png")])
        r=self.joined(doc)
        self.assertEqual(self.person(r,"ROOD")["candidate_count"],1)

    def test_05_n_token_only_explicit(self):
        doc=self.base_report([self.img("Characters/N.png",["N"]),
                              self.img("Characters/Neptune.png",[])])
        r=self.joined(doc)
        self.assertEqual(self.person(r,"N")["candidate_count"],1)
        self.assertEqual(self.person(r,"N")["sprite_candidates"][0]["source_path_candidate"],
                         "Characters/N.png")

    def test_06_battler_and_icon_ignored(self):
        doc=self.base_report([self.img("Battlers/Cheren.png",["CHEREN"],
                                      "BATTLE_SPRITE_CANDIDATE"),
                              self.img("Icons/Cheren.png",["CHEREN"],"ICON_CANDIDATE")])
        r=self.joined(doc)
        self.assertEqual(self.person(r,"CHEREN")["candidate_count"],0)

    def test_07_multiple_candidate_ambiguity(self):
        doc=self.base_report([self.img("A/Cheren.png",["CHEREN"]),
                              self.img("B/Cheren.png",["CHEREN"])])
        r=self.joined(doc)
        self.assertEqual(self.person(r,"CHEREN")["status"],
                         "MULTIPLE_CANDIDATES_MANUAL_REVIEW")
        self.assertEqual(self.person(r,"CHEREN")["candidate_count"],2)

    def test_08_pack_report_wrong_sha_filename(self):
        doc=self.write_audit([self.img("Characters/Cheren.png",["CHEREN"])])
        value=json.loads(doc.read_text())
        value["archive_sha256"]="b"*64
        doc.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            sp04.read_sp03(self.project,doc)

    def test_09_rejects_sp03_falsely_licensed(self):
        doc=self.write_audit([self.img("Characters/Cheren.png",["CHEREN"])])
        value=json.loads(doc.read_text())
        value["rights_verified"]=True
        doc.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            sp04.read_sp03(self.project,doc)

    def test_10_rejects_sp03_corrupted_images(self):
        doc=self.write_audit([self.img("Characters/Cheren.png",["CHEREN"])])
        value=json.loads(doc.read_text())
        value["invalid_images"]=[{"path":"broken.png","error":"invalid"}]
        doc.write_text(json.dumps(value))
        with self.assertRaises(ValueError):
            sp04.read_sp03(self.project,doc)

    def test_11_cannot_assign_unlicensed_sprite_to_roster(self):
        self.invalid_roster(lambda c:c["characters"][0].update(
            sprite_source_path="Graphics/Characters/Hilbert.png",installed=True))

    def test_12_cannot_forge_license(self):
        self.invalid_roster(lambda c:c["characters"][0].update(
            redistribution_allowed=True,license_evidence_url="https://fake.test"))

    def test_13_cannot_forge_native_qa(self):
        self.invalid_roster(lambda c:c["characters"][0].update(
            game_exe_tested=True,android_tested=True))

    def test_14_duplicate_key_blocked(self):
        self.invalid_roster(lambda c:c["characters"][1].update(
            key=c["characters"][0]["key"]))

    def test_15_dropped_critical_npc_blocked(self):
        self.invalid_roster(lambda c:c["characters"].remove(next(
            x for x in c["characters"] if x["key"]=="UNOVA_NPC_IRIS")))

    def test_16_wrong_story_phase_blocked(self):
        self.invalid_roster(lambda c:c["characters"][0].update(planned_phase="U32"))

    def test_17_fake_area_blocked(self):
        self.invalid_roster(lambda c:c["characters"][0].update(
            primary_area_key="UNOVA_NONEXISTENT"))

    def test_18_trainer_reference_cannot_be_rewired(self):
        self.invalid_roster(lambda c:next(x for x in c["characters"]
                 if x["key"]=="UNOVA_NPC_CHEREN").update(
                 trainer_reference_key="UNOVA_TRAINER_BIANCA"))

    def test_19_duplicate_alias_blocked(self):
        self.invalid_roster(lambda c:c["characters"][0].update(
            filename_alias_candidates=["hilda","HILDA"]))

    def test_20_report_in_other_folder_blocked(self):
        fake=self.project/"game/sprites-"+self.archive_sha[:16]+".json"
        fake.parent.mkdir(parents=True)
        fake.write_text(json.dumps(self.base_report([self.img("NPC/Cheren.png")])))
        with self.assertRaises(ValueError):
            sp04.read_sp03(self.project,fake)

    def test_21_symlink_report_blocked(self):
        doc=self.write_audit([self.img("Characters/Cheren.png")])
        external=self.project/"outside.json"
        external.write_bytes(doc.read_bytes())
        doc.unlink()
        try:
            doc.symlink_to(external)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            sp04.read_sp03(self.project,doc)

    def test_22_file_paths_inside_sp03_must_be_unique(self):
        doc=self.write_audit([self.img("A/Cheren.png"),
                              self.img("a/cheren.PNG")])
        with self.assertRaises(ValueError):
            sp04.read_sp03(self.project,doc)

    def test_23_readme_no_zip_does_not_fake_candidates(self):
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            code=sp04.main(["--project",str(self.project)])
        self.assertEqual(code,0)
        self.assertFalse((self.project/"game").exists())

    def test_24_default_latest_uses_real_private_SP03_only(self):
        doc=self.write_audit([self.img("Graphics/Characters/Bianca.png",["BIANCA"])])
        with redirect_stdout(io.StringIO()) as buff:
            code=sp04.main(["--project",str(self.project),"--latest","--write"])
        self.assertEqual(code,0)
        report=self.project/sp04.SP04_DIR/("npc-sp04-"+self.archive_sha[:16]+".json")
        self.assertTrue(report.is_file())
        output=json.loads(report.read_text())
        self.assertEqual(self.person(output,"BIANCA")["candidate_count"],1)
        self.assertFalse(output["game_exe_tested"])

    def test_25_report_writer_is_idempotent_and_no_overwrite(self):
        report=self.joined()
        dst=sp04.save(self.project,report)
        before=dst.read_bytes()
        sp04.save(self.project,report)
        self.assertEqual(dst.read_bytes(),before)
        with self.assertRaises(ValueError):
            sp04.save(self.project,dict(report,status="INSTALLED"))
        self.assertEqual(dst.read_bytes(),before)

    def test_26_output_symlink_blocked(self):
        folder=self.project/sp04.SP04_DIR
        folder.mkdir(parents=True)
        target=folder/"npc-sp04-planned-only.json"
        outside=self.project/"outside.json"
        outside.write_text("{}")
        try:
            target.symlink_to(outside)
        except OSError:
            self.skipTest("symlink unavailable")
        with self.assertRaises(ValueError):
            sp04.save(self.project,self.joined())

    def test_27_missing_existing_catalog_fails_closed(self):
        (self.project/FILES[0]).unlink()
        with redirect_stderr(io.StringIO()):
            code=sp04.main(["--project",str(self.project)])
        self.assertEqual(code,2)

    def test_28_unknown_file_extension_not_report_accepted(self):
        path=self.sp03_dir/"sprites-"+self.archive_sha[:16]+".txt"
        path.write_text("{}")
        with self.assertRaises(ValueError):
            sp04.read_sp03(self.project,path)

if __name__=="__main__":
    unittest.main()
