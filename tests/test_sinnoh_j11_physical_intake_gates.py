"""J11 read-only regression: never imply geometry QA equals native QA or rights."""
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

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/"scripts/regions")]
import audit_sinnoh_playable_j11 as j11
import generate_sinnoh_original_j10a as j10a

class J11PhysicalIntakeGates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files,cls.manifest=j10a.generate()
        cls.scenes=j10a.scenes()
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix="sinnoh-j11-synthetic-only-")
        self.addCleanup(tmp.cleanup)
        self.project=Path(tmp.name)
        for f in ("data/regions/sinnoh-j02-map-source-catalog.json",
                  "data/regions/sinnoh-twinleaf-events.json",
                  "data/regions/sinnoh-twinleaf-events.schema.json"):
            path=self.project/f
            path.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/f,path)
        game=self.project/"game/Data";game.mkdir(parents=True)
        (game/"Map209.rxdata").write_bytes(b"protected map not touched")
        saves=self.project/"game/Saves";saves.mkdir()
        (saves/"personal.sav").write_bytes(b"protected save fixture")
        self.original=(game/"Map209.rxdata").read_bytes(),(saves/"personal.sav").read_bytes()
    def payload(self):
        return copy.deepcopy(self.files),copy.deepcopy(self.manifest)
    def scenes_copy(self):
        return copy.deepcopy(self.scenes)
    def assert_blocked(self,call):
        with self.assertRaises((ValueError,KeyError,TypeError)):
            call()
    def review_path(self,name,value):
        folder=self.project/".blue-work/sinnoh-j11-reviews"
        folder.mkdir(parents=True,exist_ok=True)
        p=folder/name
        p.write_text(json.dumps(value))
        return p
    def r07(self):
        return {"schema":1,"region":"SINNOH","stage":"J09",
                "mode":"LOCAL_R07_RESERVATIONS_NOT_NATIVE_APPROVAL",
                "baseline_mapinfos_sha256":"a"*64,
                "occupied_ids":[209,210],
                "candidate_sinnoh_ids":list(range(442,451)),
                "reserved_by_region":{region:[] for region in j11.REGIONS},
                "locally_reviewed":True,
                "review_reference":"SYNTHETIC_TEST_EVIDENCE_NOT_AUTHORIZED"}

    def test_01_actual_five_generated_maps_reaudited(self):
        report=j11.original_audit(ROOT)
        self.assertEqual(report["count"],5)
        self.assertEqual(set(report["maps"]),set(j10a.SYMBOLS))
        self.assertTrue(all(v["rxdata"]["layers"]==3 for v in report["maps"].values()))
    def test_02_full_png_checksum_pixels_and_nontrivial_tiles(self):
        report=j11.verify_png(self.files["OriginalJ10A.png"])
        self.assertEqual(report["sha256"],self.manifest["tileset_sha256"])
        self.assertGreaterEqual(report["unique_drawn_tile_count"],24)
        self.assertFalse(report["rpg_maker_passages_checked"])
    def test_03_all_five_actual_svg_previews_checked(self):
        for scene in self.scenes:
            svg=self.files["previews/"+scene["symbol"]+".svg"]
            report=j11.verify_svg(svg,scene)
            self.assertEqual(report["cell_count"],scene["width"]*scene["height"])
            self.assertFalse(report["external_content"])
    def test_04_all_rxdata_byte_equal_three_layer_scene_grids(self):
        for scene in self.scenes:
            info=j11.verify_rxdata(self.files[scene["symbol"]+".rxdata"],scene,
                                   self.manifest["tileset_sha256"])
            self.assertEqual(info["layers"],3)
            self.assertFalse(info["native_tileset_registered"])
    def test_05_potential_collision_reachability_explicitly_non_native(self):
        for scene in self.scenes:
            info=j11.potential_walkability(scene)
            self.assertGreater(info["potential_reachable_cells"],20)
            self.assertFalse(info["directional_passages_checked"])
    def test_06_nine_symbolic_maps_four_sources_pending(self):
        report=j11.audit(ROOT)
        self.assertEqual(report["nine_map_symbolic_slots"],9)
        self.assertEqual(sum(x["origin"]=="B00_HISTORICAL_PRIVATE_DONOR"
                             for x in report["nine_map_source_plan"].values()),4)
        self.assertEqual(sum(x["origin"]=="J10A_PROCEDURAL_ORIGINAL"
                             for x in report["nine_map_source_plan"].values()),5)
        self.assertFalse(report["historical_donor_verified"])
    def test_07_16_warps_five_npc_three_balls_without_coordinates(self):
        events=j11.verify_contracts(ROOT)
        self.assertEqual((events["directional_warps"],events["npc_handlers"],
                          events["starter_balls"]),(16,5,3))
        self.assertFalse(events["compilation_j04_allowed"])
    def test_08_no_native_or_rights_promotion(self):
        report=j11.audit(ROOT)
        self.assertFalse(report["can_install"])
        self.assertFalse(report["can_stage_j03_j04_j06"])
        self.assertFalse(report["can_promote_to_j09"])
        self.assertFalse(report["r07"]["r07_independent_approval"])
        self.assertFalse(report["r08"]["r08_independently_approved"])
        self.assertEqual(report["native_maps_installed"],0)
        self.assertEqual(report["native_qa_cases_executed"],0)
    def test_09_no_access_to_main_game_or_personal_saves(self):
        j11.audit(self.project)
        self.assertEqual((self.project/"game/Data/Map209.rxdata").read_bytes(),self.original[0])
        self.assertEqual((self.project/"game/Saves/personal.sav").read_bytes(),self.original[1])
        self.assertFalse((self.project/".blue-work").exists())
    def test_10_write_only_inert_noninstallable_private_json(self):
        report=j11.private_plan(self.project)
        path=self.project/".blue-work"/j11.PLAN
        self.assertTrue(path.is_file())
        self.assertFalse(report["can_install"])
        self.assertEqual(json.loads(path.read_text())["native_maps_installed"],0)
        self.assertEqual(len(list(path.parent.rglob("*"))),1)
        self.assertEqual((self.project/"game/Saves/personal.sav").read_bytes(),self.original[1])
    def test_11_refuse_overwrite_private_receipt(self):
        j11.private_plan(self.project)
        self.assert_blocked(lambda:j11.private_plan(self.project))
    def test_12_generate_audit_reproducible_hashes(self):
        a=j11.original_audit(ROOT);b=j11.original_audit(ROOT)
        self.assertEqual({k:v["rxdata"]["sha256"] for k,v in a["maps"].items()},
                         {k:v["rxdata"]["sha256"] for k,v in b["maps"].items()})

    def test_13_reject_missing_original_rxdata(self):
        f,m=self.payload();f.pop(j10a.SYMBOLS[0]+".rxdata")
        self.assert_blocked(lambda:j11.original_audit(ROOT,payload=(f,m)))
    def test_14_reject_extra_foreign_asset(self):
        f,m=self.payload();f["map.exe"]=b"\x00"
        self.assert_blocked(lambda:j11.original_audit(ROOT,payload=(f,m)))
    def test_15_reject_modified_map_even_with_valid_other_maps(self):
        f,m=self.payload();n=j10a.SYMBOLS[2]+".rxdata";f[n]+=b"modified"
        self.assert_blocked(lambda:j11.original_audit(ROOT,payload=(f,m)))
    def test_16_reject_forged_source_manifest_checksum(self):
        f,m=self.payload();m["map_sources"][j10a.SYMBOLS[0]]["rxdata_sha256"]="0"*64
        self.assert_blocked(lambda:j11.original_audit(ROOT,payload=(f,m)))
    def test_17_reject_forged_manifest_tileset_hash(self):
        f,m=self.payload();m["tileset_sha256"]="f"*64
        self.assert_blocked(lambda:j11.original_audit(ROOT,payload=(f,m)))
    def test_18_reject_bad_png_crc(self):
        image=bytearray(self.files["OriginalJ10A.png"]);image[29]^=1
        self.assert_blocked(lambda:j11.verify_png(bytes(image)))
    def test_19_reject_empty_or_invalid_png_signature(self):
        self.assert_blocked(lambda:j11.verify_png(b"\x00"*32))
    def test_20_reject_png_external_chunk(self):
        blob=self.files["OriginalJ10A.png"]
        name=b"tEXt";content=b"copyright=no"
        part=struct.pack(">I",len(content))+name+content
        import zlib
        part+=struct.pack(">I",zlib.crc32(name+content)&0xffffffff)
        modified=blob[:33]+part+blob[33:]
        self.assert_blocked(lambda:j11.verify_png(modified))
    def test_21_reject_svg_script_injection(self):
        sc=self.scenes[0]
        raw=self.files["previews/"+sc["symbol"]+".svg"]
        self.assert_blocked(lambda:j11.verify_svg(raw.replace(b"</svg>",b"<script>alert(1)</script></svg>"),sc))
    def test_22_reject_svg_external_image(self):
        sc=self.scenes[0];raw=self.files["previews/"+sc["symbol"]+".svg"]
        self.assert_blocked(lambda:j11.verify_svg(raw.replace(b"</svg>",b'<image href="http://unsafe"/>\n</svg>'),sc))
    def test_23_reject_doctype_in_svg(self):
        sc=self.scenes[0]
        self.assert_blocked(lambda:j11.verify_svg(b'<!DOCTYPE foo>'+self.files["previews/"+sc["symbol"]+".svg"],sc))
    def test_24_reject_svg_missing_render_cell(self):
        sc=self.scenes[0];raw=self.files["previews/"+sc["symbol"]+".svg"]
        start=raw.find(b"<rect ")
        end=raw.find(b"/>",start)
        self.assertGreater(end,start)
        tampered=raw[:start]+raw[end+2:]
        self.assert_blocked(lambda:j11.verify_svg(tampered,sc))
    def test_25_reject_rxdata_corruption(self):
        sc=self.scenes[0]
        self.assert_blocked(lambda:j11.verify_rxdata(b"\x00"*200,sc,self.manifest["tileset_sha256"]))
    def test_26_reject_layout_changed_from_serialized_layers(self):
        sc=copy.deepcopy(self.scenes[0]);sc["layers"][0][50]=j10a.RUG
        self.assert_blocked(lambda:j11.verify_rxdata(self.files[sc["symbol"]+".rxdata"],sc,
                                    self.manifest["tileset_sha256"]))
    def test_27_reject_passability_blocked_entrance(self):
        sc=copy.deepcopy(self.scenes[0])
        x,y=sc["access"][0];j10a.at(sc,1,x,y,j10a.WALL)
        self.assert_blocked(lambda:j11.potential_walkability(sc))
    def test_28_reject_disconnected_landmark(self):
        sc=copy.deepcopy(self.scenes[1]);x,y=sc["landmarks"][0]
        for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):j10a.at(sc,1,x+dx,y+dy,j10a.WALL)
        self.assert_blocked(lambda:j11.potential_walkability(sc))
    def test_29_reject_fake_nine_map_catalog_approval(self):
        path=self.project/"data/regions/sinnoh-j02-map-source-catalog.json"
        meta=json.loads(path.read_text());meta["source_rights_verified"]=True
        path.write_text(json.dumps(meta))
        self.assert_blocked(lambda:j11.original_audit(self.project))
    def test_30_reject_missing_symbol_from_source_catalog(self):
        path=self.project/"data/regions/sinnoh-j02-map-source-catalog.json"
        meta=json.loads(path.read_text());meta["maps"].pop()
        path.write_text(json.dumps(meta))
        self.assert_blocked(lambda:j11.original_audit(self.project))
    def test_31_reject_event_coordinates_without_review(self):
        path=self.project/"data/regions/sinnoh-twinleaf-events.json"
        meta=json.loads(path.read_text());meta["maps"][0]["events"][0]["x"]=7
        path.write_text(json.dumps(meta))
        self.assert_blocked(lambda:j11.verify_contracts(self.project))
    def test_32_reject_event_warp_graph_change(self):
        path=self.project/"data/regions/sinnoh-twinleaf-events.json"
        meta=json.loads(path.read_text())
        meta["maps"][0]["events"][0]["destination"]=j10a.SYMBOLS[3]
        path.write_text(json.dumps(meta))
        self.assert_blocked(lambda:j11.verify_contracts(self.project))
    def test_33_reject_fake_event_install_approval(self):
        path=self.project/"data/regions/sinnoh-twinleaf-events.json"
        meta=json.loads(path.read_text());meta["approved_for_install"]=True
        path.write_text(json.dumps(meta))
        self.assert_blocked(lambda:j11.verify_contracts(self.project))
    def test_34_reject_private_inputs_not_in_workspace(self):
        p=self.project/"fake-source.zip";p.write_bytes(b"not a source")
        self.assert_blocked(lambda:j11.audit(self.project,donor_zip=p))
    def test_35_reject_baseline_without_review(self):
        self.assert_blocked(lambda:j11.audit(self.project,baseline_dir=self.project/"game/Data"))
    def test_36_reject_review_without_baseline(self):
        self.assert_blocked(lambda:j11.audit(self.project,review_dir=self.project/"game"))
    def test_37_reject_missing_r07_mapinfos(self):
        path=self.project/".blue-work/sinnoh-j11-baseline/Data";path.mkdir(parents=True)
        self.assert_blocked(lambda:j11._baseline(self.project,path))
    def test_38_reject_baseline_r07_outside_isolation(self):
        self.assert_blocked(lambda:j11._baseline(self.project,self.project/"game/Data"))
    def test_39_r07_reject_stale_mapinfos_sha(self):
        row=self.r07();row["baseline_mapinfos_sha256"]="b"*64
        p=self.review_path("r07.json",row)
        with patch.object(j11,"_baseline",return_value=("a"*64,{209,210})):
            self.assert_blocked(lambda:j11.check_r07(self.project,self.project/"game/Data",p))
    def test_40_r07_reject_collision_with_other_region(self):
        row=self.r07();row["reserved_by_region"]["KANTO"]=[442]
        p=self.review_path("r07.json",row)
        with patch.object(j11,"_baseline",return_value=("a"*64,{209,210})):
            self.assert_blocked(lambda:j11.check_r07(self.project,self.project/"game/Data",p))
    def test_41_r07_reject_duplicate_destination_mapid(self):
        row=self.r07();row["candidate_sinnoh_ids"][1]=442
        p=self.review_path("r07.json",row)
        with patch.object(j11,"_baseline",return_value=("a"*64,{209,210})):
            self.assert_blocked(lambda:j11.check_r07(self.project,self.project/"game/Data",p))
    def test_42_r07_synthetic_local_assertion_never_independent_approval(self):
        p=self.review_path("r07.json",self.r07())
        with patch.object(j11,"_baseline",return_value=("a"*64,{209,210})):
            report=j11.check_r07(self.project,self.project/"game/Data",p)
        self.assertFalse(report["r07_independent_approval"])
        self.assertEqual(report["local_candidates_checked_no_collision"],9)
    def test_43_r08_requires_four_real_historical_hashes(self):
        self.assert_blocked(lambda:j11.check_r08(self.project,self.project/".blue-work/sinnoh-j11-reviews",
                                                 {"original_four":{}},j11.original_audit(ROOT)))
    def test_44_no_symlink_workspace_allowed(self):
        outside=self.project/"outside";outside.mkdir()
        link=self.project/".blue-work"
        try:link.symlink_to(outside,target_is_directory=True)
        except (OSError,NotImplementedError):self.skipTest("symlinks not supported")
        self.assert_blocked(lambda:j11.private_plan(self.project))
    def test_45_review_dir_must_be_explicit_private_path(self):
        path=self.project/"game";path.mkdir(exist_ok=True)
        self.assert_blocked(lambda:j11.audit(self.project,
                             baseline_dir=self.project/".blue-work/sinnoh-j11-baseline/Data",
                             review_dir=path))
    def test_46_reject_forged_native_promotion_in_generator_manifest(self):
        files,meta=self.payload();meta["native_maps_installed"]=5
        self.assert_blocked(lambda:j11.original_audit(ROOT,payload=(files,meta)))
    def test_47_reject_false_human_authorship_in_generator_manifest(self):
        files,meta=self.payload();meta["actual_human_authorship_attested"]=True
        self.assert_blocked(lambda:j11.original_audit(ROOT,payload=(files,meta)))
    def test_48_preserve_public_nine_installed_zero(self):
        p=json.loads((ROOT/"data/regions/sinnoh-playable-progress.json").read_text())
        site=json.loads((ROOT/"site/public/data/sinnoh-playable-progress.json").read_text())
        self.assertEqual(p,site)
        self.assertEqual(p["status"],"PILOT_NOT_INSTALLED_NOT_PLAYABLE")
        self.assertEqual(p["stages_native_validated"],0)
        self.assertEqual((p["native_windows_cases_executed"],p["native_android_cases_executed"]),(0,0))
        self.assertFalse(p["main_game_modified"])
        self.assertFalse(p["game_exe_tested"] or p["joiplay_tested"])
    def test_49_cli_check_does_not_write(self):
        self.assertEqual(j11.main(["--project",str(self.project)]),0)
        self.assertFalse((self.project/".blue-work").exists())
    def test_50_reject_duplicate_write_plan_when_integration_blocked(self):
        j11.private_plan(self.project)
        target=self.project/".blue-work"/j11.PLAN
        original=target.read_bytes()
        self.assert_blocked(lambda:j11.private_plan(self.project))
        self.assertEqual(target.read_bytes(),original)

if __name__=="__main__":
    unittest.main()
