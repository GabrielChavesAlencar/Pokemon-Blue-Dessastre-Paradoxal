"""B03 audit: real B00/B01 snapshot + installer code claims, no approval."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_sinnoh_b03_installer_evidence as b03

class B03Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=b03.read(b03.B03)
        cls.templates=b03.read(b03.TEMPLATES)
        cls.b00=b03.read(b03.B00)
        cls.b01=b03.read(b03.B01)
        cls.b02=b03.read(b03.B02)
        cls.ch05=b03.read(b03.CH05)

    def check(self,manifest=None,templates=None,b00=None,b01=None,b02=None,ch05=None):
        return b03.audit(
          copy.deepcopy(self.manifest if manifest is None else manifest),
          copy.deepcopy(self.templates if templates is None else templates),
          copy.deepcopy(self.b00 if b00 is None else b00),
          copy.deepcopy(self.b01 if b01 is None else b01),
          copy.deepcopy(self.b02 if b02 is None else b02),
          copy.deepcopy(self.ch05 if ch05 is None else ch05))

    def mutate(self,key,value):
        m=copy.deepcopy(self.manifest);m[key]=value
        with self.assertRaisesRegex(ValueError,"SINNOH_B03_BLOCKED"):
            self.check(manifest=m)

    def test_01_valid_inputs_have_no_install_approval(self):
        result=self.check()
        self.assertEqual(result["source_installer_evidence_files"],4)
        self.assertEqual(result["future_reservation_manifests_verified"],0)
        self.assertFalse(result["can_apply_mapping"])
        self.assertFalse(result["can_install"])
        self.assertFalse(result["r07_complete"])

    def test_02_cli_preflight_success(self):
        proc=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_b03_installer_evidence.py")],
                            cwd=ROOT,encoding="utf-8",capture_output=True)
        self.assertEqual(proc.returncode,0,proc.stderr)
        self.assertIn("SINNOH_B03_SOURCE_CLAIMS_AND_TILESET_PLAN_OK_OFFLINE",proc.stdout)

    def test_03_hypothetical_window_is_not_reserved(self):
        win=self.manifest["illustrative_contiguous_window"]
        self.assertEqual((win["start"],win["end"],win["length"]),(442,517,76))
        self.assertFalse(win["selected_as_destinations"])
        self.assertFalse(win["future_claims_checked"])
        self.assertEqual(self.manifest["destination_mapping"],{})

    def test_04_no_fake_kanto_reservations(self):
        self.assertEqual(self.manifest["confirmed_future_ids_kanto"],[])
        self.mutate("confirmed_future_ids_kanto",[442])

    def test_05_no_fake_johto_reservations(self):
        self.mutate("confirmed_future_ids_johto",[518])

    def test_06_no_fake_hoenn_reservations(self):
        self.mutate("confirmed_future_ids_hoenn",[550])

    def test_07_cannot_claim_approved_window(self):
        m=copy.deepcopy(self.manifest)
        m["illustrative_contiguous_window"]["selected_as_destinations"]=True
        with self.assertRaisesRegex(ValueError,"SINNOH_B03_BLOCKED"):
            self.check(manifest=m)

    def test_08_cannot_assign_a_native_tileset_id(self):
        m=copy.deepcopy(self.manifest)
        m["tileset_strategy"]["donor_tile_ids"][1]["new_native_id"]=70
        with self.assertRaisesRegex(ValueError,"SINNOH_B03_BLOCKED"):
            self.check(manifest=m)

    def test_09_cannot_copy_tileset_31_as_native_31(self):
        m=copy.deepcopy(self.manifest)
        m["tileset_strategy"]["donor_to_native_index_mapping"]={"31":31}
        with self.assertRaisesRegex(ValueError,"SINNOH_B03_BLOCKED"):
            self.check(manifest=m)

    def test_10_must_keep_autotile_validation(self):
        m=copy.deepcopy(self.manifest)
        m["tileset_strategy"]["must_verify_autotile_names_and_files"]=False
        with self.assertRaisesRegex(ValueError,"SINNOH_B03_BLOCKED"):
            self.check(manifest=m)

    def test_11_must_not_modify_native_tilesets(self):
        m=copy.deepcopy(self.manifest)
        m["tileset_strategy"]["must_preserve_existing_native_tilesets"]=False
        with self.assertRaisesRegex(ValueError,"SINNOH_B03_BLOCKED"):
            self.check(manifest=m)

    def test_12_templates_are_not_r07_proof(self):
        t=self.templates
        self.assertFalse(t["can_use_as_r07_evidence"])
        self.assertEqual(set(t["records"]),{"KANTO","JOHTO","HOENN"})
        self.assertEqual(t["baseline_mapinfos_sha256"],self.b01["mapinfos_sha256"])
        self.assertTrue(all(not row["reviewed_locally"] and not row["future_reserved_map_ids"]
                            for row in t["records"].values()))

    def test_13_forged_local_review_rejected(self):
        t=copy.deepcopy(self.templates)
        t["records"]["KANTO"]["reviewed_locally"]=True
        with self.assertRaisesRegex(ValueError,"SINNOH_B03_BLOCKED"):
            self.check(templates=t)

    def test_14_forged_future_array_rejected(self):
        t=copy.deepcopy(self.templates)
        t["records"]["JOHTO"]["future_reserved_map_ids"]=[500]
        with self.assertRaisesRegex(ValueError,"SINNOH_B03_BLOCKED"):
            self.check(templates=t)

    def test_15_forged_baseline_hash_rejected(self):
        t=copy.deepcopy(self.templates)
        t["baseline_mapinfos_sha256"]="f"*64
        with self.assertRaisesRegex(ValueError,"SINNOH_B03_BLOCKED"):
            self.check(templates=t)

    def test_16_spoofed_installer_evidence_rejected(self):
        m=copy.deepcopy(self.manifest)
        m["code_evidence"][2]["entries"]=["if True: allow_sinnoh"]
        with self.assertRaisesRegex(ValueError,"SINNOH_B03_BLOCKED"):
            self.check(manifest=m)

    def test_17_b02_collision_count_cannot_be_faked(self):
        b=copy.deepcopy(self.b02)
        b["sinnoh_original_collision_count"]=0
        with self.assertRaisesRegex(ValueError,"SINNOH_B03_BLOCKED"):
            self.check(b02=b)

    def test_18_native_tileset_index_is_not_an_approved_slot(self):
        self.assertEqual(self.manifest["tileset_strategy"]["native_tileset_table_reported_length"],70)
        self.assertFalse(self.manifest["tileset_strategy"]["rights_cleared"])
        self.assertEqual(self.manifest["tileset_strategy"]["materialized_new_tilesets"],0)
        self.mutate("can_generate_installable_remap",True)

    def test_19_sibling_regions_remain_excluded(self):
        self.assertEqual(self.manifest["code_protected_ranges"],[
          {"region":"JOHTO","start":600,"end":699,"kind":"PREVIEW_CODE_CLAIM"},
          {"region":"HOENN","start":700,"end":999,"kind":"INSTALLER_CODE_RANGE"}
        ])
        self.mutate("protect_other_regions",False)

    def test_20_bars_and_runtime_remain_unapproved(self):
        for key in ("r07_complete","r08_complete","r09_complete",
                    "native_game_exe_tested","joiplay_tested",
                    "can_install","can_mark_playable","game_or_saves_modified"):
            with self.subTest(key=key):self.mutate(key,True)
        for key in ("phase_b_approved","phase_c_approved","phase_d_approved"):
            with self.subTest(key=key):self.mutate(key,1)

if __name__=="__main__":unittest.main()
