"""G07.3: offline transaction, immutable backups, full-state CAS and rollback."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts/regions"))
import audit_unova_g07_transaction as tx
import audit_unova_g07_incremental_manifest as g72

class UnovaG073Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit = tx.audit_contract()
        cls.contract = g72.j(ROOT, tx.CONTRACT_PATH)
        cls.board = g72.j(ROOT, g72.TRACKER)
        cls.registry = g72.j(ROOT, g72.REGISTRY)

    def bundle(self):
        pkg, manifest, old, new = tx.multi_file_fixture()
        state = tx.base_fixture(pkg, manifest, old)
        return state, pkg, manifest, old, new

    def preview(self, *, state=None, package=None, manifest=None, old=None, new=None,
                generation=None, etag=None, **options):
        base, pkg, origin, before, after = self.bundle()
        state = base if state is None else state
        pkg = pkg if package is None else package
        origin = origin if manifest is None else manifest
        before = before if old is None else old
        after = after if new is None else new
        gen = state["generation"] if generation is None else generation
        digest = tx.state_etag(state) if etag is None else etag
        return tx.transact(state, pkg, origin, before, after,
                           expected_generation=gen, expected_snapshot_sha256=digest,
                           **options)

    def test_001_phase(self):
        self.assertEqual(self.audit["phase"], "G07.3")
    def test_002_only_memory(self):
        self.assertEqual(self.audit["scope"], tx.SCOPE)
    def test_003_cannot_install(self):
        self.assertFalse(self.audit["can_install"])
    def test_004_no_real_download(self):
        self.assertFalse(self.audit["blue_story_invoked"])
    def test_005_no_game_exe(self):
        self.assertFalse(self.audit["game_exe_invoked"])
    def test_006_no_joiplay(self):
        self.assertFalse(self.audit["joiplay_invoked"])
    def test_007_no_native_files(self):
        self.assertEqual(self.audit["native_files_written"], 0)
    def test_008_no_saves_touched(self):
        self.assertFalse(self.audit["native_saves_modified"])
    def test_009_release_not_allowed(self):
        self.assertFalse(self.audit["can_release"])
    def test_010_previous_G072_done(self):
        self.assertEqual(self.board["groups"][6]["tasks"][1]["status"], "done")
    def test_011_G073_registered(self):
        self.assertEqual(self.board["groups"][6]["tasks"][2]["id"], "G07.3")
    def test_012_planned_unova(self):
        self.assertEqual(self.registry["regions"]["UNOVA"]["status"], "planned")
    def test_013_technical_zero(self):
        self.assertEqual(self.board["native_technical_bar"]["completed"], 0)
    def test_014_playable_zero(self):
        self.assertEqual(self.board["native_playable_bar"]["completed"], 0)
    def test_015_no_native_rollout(self):
        self.assertFalse(self.contract["can_install"])
        self.assertFalse(self.contract["release_allowed"])
    def test_016_exact_guards(self):
        self.assertEqual(self.contract["guardrails"], tx.GUARDS)
    def test_017_failpoints_listed(self):
        self.assertEqual(self.contract["fault_points"], list(tx.FAULTS))
    def test_018_predecessor_still_strict(self):
        self.assertFalse(g72.j(ROOT, g72.CONTRACT_PATH)["can_install"])
    def test_019_contract_no_Android(self):
        self.assertFalse(self.contract["guardrails"]["android_supported"])
    def test_020_valid_two_file_bundle(self):
        _, pkg, origin, old, new = self.bundle()
        self.assertEqual(g72.validate_package(pkg, origin, old, new)["files_checked"], 2)
    def test_021_fixture_has_only_docs_bytes(self):
        state, pkg, _, old, new = self.bundle()
        self.assertEqual(state["files"], old)
        self.assertTrue(all(g72.path_ok(name) for name in new))
    def test_022_baseline_etag_is_SHA256(self):
        self.assertRegex(tx.state_etag(self.bundle()[0]),r"^[a-f0-9]{64}$")
    def test_023_etag_deterministic(self):
        state = self.bundle()[0]
        self.assertEqual(tx.state_etag(state),tx.state_etag(copy.deepcopy(state)))
    def test_024_two_file_atomic_commit(self):
        result = self.preview()
        self.assertEqual(result["status"],"SIMULATED_ATOMIC_COMMIT_NOT_INSTALLED")
        self.assertEqual(result["changed_files"],2)
    def test_025_payload_written_to_new_state_only(self):
        state, _, _, _, new = self.bundle()
        result = self.preview(state=state)
        self.assertEqual(result["state"]["files"],new)
    def test_026_original_state_is_unmodified(self):
        state=self.bundle()[0];baseline=copy.deepcopy(state)
        self.preview(state=state)
        self.assertEqual(state,baseline)
    def test_027_protected_unchanged_on_commit(self):
        state=self.bundle()[0]
        self.assertEqual(self.preview(state=state)["state"]["protected"],state["protected"])
    def test_028_version_bumps_in_synthetic_snapshot(self):
        state=self.bundle()[0];result=self.preview(state=state)
        self.assertEqual(result["state"]["package_version"],"0.0.1-planned")
    def test_029_revision_bumps_in_synthetic_snapshot(self):
        _,pkg,*_=self.bundle()
        self.assertEqual(self.preview()["state"]["revision"],pkg["source"]["target_revision"])
    def test_030_generation_bumps_exactly_once(self):
        state=self.bundle()[0]
        self.assertEqual(self.preview()["state"]["generation"],state["generation"]+1)
    def test_031_next_origin_manifest_is_synthetic(self):
        state=self.bundle()[0];new=self.preview()["state"]
        self.assertNotEqual(state["source_manifest_sha256"],new["source_manifest_sha256"])
    def test_032_new_etag_matches_returned_snapshot(self):
        result=self.preview()
        self.assertEqual(result["snapshot_sha256"],tx.state_etag(result["state"]))
    def test_033_no_disk_file_written(self):
        result=self.preview()
        self.assertEqual(result["native_files_written"],0)
        self.assertEqual(result["bytes_written"],0)
    def test_034_backup_contains_two_source_digests(self):
        state,*_=self.bundle();result=self.preview()
        self.assertEqual(set(result["backup_manifest"]),set(state["files"]))
        for key,row in result["backup_manifest"].items():
            self.assertEqual(row["sha256"],g72.digest(state["files"][key]))
            self.assertEqual(row["size"],len(state["files"][key]))
            self.assertTrue(row["memory_only"])
    def test_035_stage_visible_only_as_trace(self):
        result=self.preview()
        self.assertIn("PAYLOAD_STAGED_IN_MEMORY",result["trace"])
        self.assertIn("FULL_CANDIDATE_BUILT_NOT_PUBLISHED",result["trace"])
    def test_036_two_CAS_checks_in_trace(self):
        result=self.preview()
        self.assertIn("FINAL_FULL_STATE_CAS_MATCHED",result["trace"])
        self.assertIn("PREPUBLISH_CAS_RECHECKED",result["trace"])
    def test_037_noop_result_does_not_claim_native_install(self):
        result=self.preview()
        self.assertFalse(result["can_install"])
        self.assertFalse(result["release_allowed"])
    def test_038_baseline_state_strict(self):
        self.assertEqual(tx.validate_state(self.bundle()[0])["generation"],0)
    def test_039_demo_rollbacks_all(self):
        d=tx.demo()
        self.assertTrue(d["all_rollbacks_restored"])
        self.assertEqual(d["rollback_points"],len(tx.FAULTS))
    def test_040_demo_concurrent_save_protected(self):
        self.assertTrue(tx.demo()["concurrent_protected_save_blocked"])
    def test_041_demo_never_writes(self):
        self.assertEqual(tx.demo()["native_files_written"],0)
    def test_042_cli_check(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g07_transaction.py"),"--check"],
                         capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertFalse(json.loads(p.stdout)["can_install"])
    def test_043_cli_demo(self):
        p=subprocess.run([sys.executable,str(ROOT/"scripts/regions/audit_unova_g07_transaction.py"),"--simulate-demo"],
                         capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(json.loads(p.stdout)["fixture_files"],2)
    def test_044_invalid_failpoint_blocks(self):
        with self.assertRaises(ValueError):
            self.preview(fail_at="delete_real_game")
    def test_045_invalid_cas_etag_blocks(self):
        with self.assertRaises(ValueError):
            self.preview(etag="deadbeef")
    def test_046_invalid_cas_generation_type_blocks(self):
        with self.assertRaises(ValueError):
            self.preview(generation=True)
    def test_047_stale_generation_conflicts(self):
        out=self.preview(generation=7)
        self.assertEqual(out["status"],"CONFLICT_CAS_GENERATION")
    def test_048_stale_snapshot_etag_conflicts(self):
        out=self.preview(etag="c"*64)
        self.assertEqual(out["status"],"CONFLICT_CAS_SNAPSHOT")
    def test_049_concurrent_edit_detected_before_commit(self):
        state,*_=self.bundle()
        other=copy.deepcopy(state)
        other["generation"]+=1
        out=self.preview(state=state,observed_after_staging=other)
        self.assertEqual(out["status"],"CONFLICT_CAS_CONCURRENT_EDIT")
    def test_050_concurrent_edit_detected_prepublication(self):
        state,*_=self.bundle()
        other=copy.deepcopy(state);other["generation"]+=1
        out=self.preview(state=state,observed_before_publish=other)
        self.assertEqual(out["status"],"CONFLICT_CAS_CONCURRENT_EDIT")
    def test_051_concurrent_edit_no_partial_state(self):
        state,*_=self.bundle()
        other=copy.deepcopy(state);other["protected"]["saves"]["FIXTURE_SAVES_LEDGER"]="FIXTURE_CHANGED"
        result=self.preview(state=state,observed_after_staging=other)
        self.assertEqual(result["state"],state)
    def test_052_state_digest_covers_protected_changes(self):
        state=self.bundle()[0]
        other=copy.deepcopy(state)
        other["protected"]["key_items"]["FIXTURE_KEY_ITEMS_LEDGER"]="FIXTURE_CHANGED"
        self.assertNotEqual(tx.state_etag(state),tx.state_etag(other))
    def test_053_state_digest_covers_files(self):
        state=self.bundle()[0];other=copy.deepcopy(state)
        k=next(iter(other["files"]));other["files"][k]=b"changed"
        self.assertNotEqual(tx.state_etag(state),tx.state_etag(other))
    def test_054_state_digest_covers_revision(self):
        state=self.bundle()[0];other=copy.deepcopy(state)
        other["revision"]="c"*40
        self.assertNotEqual(tx.state_etag(state),tx.state_etag(other))
    def test_055_source_revision_mismatch_conflicts(self):
        state=self.bundle()[0];state["revision"]="c"*40
        self.assertEqual(self.preview(state=state)["status"],"CONFLICT_SOURCE_REVISION")
    def test_056_source_manifest_mismatch_conflicts(self):
        state=self.bundle()[0];state["source_manifest_sha256"]="c"*64
        self.assertEqual(self.preview(state=state)["status"],"CONFLICT_SOURCE_MANIFEST")
    def test_057_local_source_file_changed_blocks(self):
        state=self.bundle()[0];key=next(iter(state["files"]))
        state["files"][key]=b"changed"
        self.assertEqual(self.preview(state=state)["status"],"CONFLICT_SOURCE_BYTES")
    def test_058_one_step_baseline_only(self):
        state=self.bundle()[0];state["package_version"]="0.0.1-planned"
        self.assertEqual(self.preview(state=state)["status"],"CONFLICT_UNSUPPORTED_VERSION_CHAIN")
    def test_059_preview_never_mutates_source_manifest(self):
        state,pkg,manifest,old,new=self.bundle()
        baseline=(copy.deepcopy(state),copy.deepcopy(pkg),manifest,copy.deepcopy(old),copy.deepcopy(new))
        self.preview(state=state,package=pkg,manifest=manifest,old=old,new=new)
        self.assertEqual((state,pkg,manifest,old,new),baseline)
    def test_060_rejects_source_duplicate_license_injected(self):
        state,pkg,manifest,old,new=self.bundle()
        pkg["rights"].pop("license_id")
        pkg["package_sha256"]=g72.package_digest(pkg)
        with self.assertRaises(ValueError):
            self.preview(state=state,package=pkg,manifest=manifest,old=old,new=new)
    def test_061_rejects_corrupt_payload(self):
        state,pkg,manifest,old,new=self.bundle()
        key=next(iter(new));new[key]=b"corrupt"
        with self.assertRaises(ValueError):
            self.preview(state=state,package=pkg,manifest=manifest,old=old,new=new)
    def test_062_rejects_native_map_payload(self):
        state,pkg,manifest,old,new=self.bundle()
        pkg["files"][0]["path"]="Data/Map518.rxdata"
        pkg["package_sha256"]=g72.package_digest(pkg)
        with self.assertRaises(ValueError):
            self.preview(state=state,package=pkg,manifest=manifest,old=old,new=new)

# All seven failure points must restore the exact original state; backups never
# expose actual game files. The first candidate write is intentionally tested
# on a two-file patch so a half-committed fixture would be detected.
for _name in tx.FAULTS:
    def _failure(self, point=_name):
        state=self.bundle()[0];original=copy.deepcopy(state)
        result=self.preview(state=state,fail_at=point)
        self.assertEqual(result["status"],"SIMULATED_ROLLBACK_COMPLETE")
        self.assertEqual(result["state"],original)
        self.assertEqual(state,original)
        self.assertEqual(result["snapshot_sha256"],tx.state_etag(original))
        self.assertEqual(result["native_files_written"],0)
        self.assertEqual(result["bytes_written"],0)
        self.assertFalse(result["can_install"])
        self.assertFalse(result["native_saves_modified"])
    setattr(UnovaG073Tests,"test_injected_rollback_"+_name,_failure)

# Every protection namespace participates in BOTH CAS checks and must be
# byte-for-byte (synthetic-value-for-synthetic-value) unchanged on success.
for _name in tx.PROTECTED:
    def _untouched(self,namespace=_name):
        base=self.bundle()[0]
        res=self.preview(state=base)
        self.assertEqual(res["state"]["protected"][namespace],base["protected"][namespace])
    setattr(UnovaG073Tests,"test_protected_success_"+_name,_untouched)

    def _conflict(self,namespace=_name):
        base=self.bundle()[0]
        concurrent=copy.deepcopy(base)
        key=next(iter(concurrent["protected"][namespace]))
        concurrent["protected"][namespace][key]="FIXTURE_EXTERNAL_EDIT"
        early=self.preview(state=base,observed_after_staging=concurrent)
        late=self.preview(state=base,observed_before_publish=concurrent)
        for result in (early,late):
            self.assertEqual(result["status"],"CONFLICT_CAS_CONCURRENT_EDIT")
            self.assertEqual(result["state"],base)
            self.assertFalse(result["can_install"])
    setattr(UnovaG073Tests,"test_protected_conflict_"+_name,_conflict)

# Invalid root state, real asset paths, tampered protected keys, wrong
# generation and memory limits are rejected before staging.
_BAD_STATES={
    "unknown_field":lambda s:s.update(physical_disk_write=True),
    "wrong_scope":lambda s:s.update(scope="NATIVE_SAVE"),
    "wrong_region":lambda s:s.update(region="KANTO"),
    "wrong_channel":lambda s:s.update(channel="android"),
    "invalid_revision":lambda s:s.update(revision="short"),
    "unknown_version":lambda s:s.update(package_version="native-1.0"),
    "negative_generation":lambda s:s.update(generation=-1),
    "boolean_generation":lambda s:s.update(generation=True),
    "manifest_sha_short":lambda s:s.update(source_manifest_sha256="deadbeef"),
    "unknown_protected_region":lambda s:s["protected"].update(galar={}),
    "missing_save_snapshot":lambda s:s["protected"].pop("saves"),
    "empty_other_region":lambda s:s["protected"].update(kanto={}),
    "real_save_key":lambda s:s["protected"]["saves"].update({"File A.rxdata":"FIXTURE_X"}),
    "real_path_value":lambda s:s["protected"]["saves"].update(FIXTURE_SAVE="Game.exe"),
    "non_ascii_protected":lambda s:s["protected"]["saves"].update(FIXTURE_Á="FIXTURE_X"),
    "wrong_protected_payload":lambda s:s["protected"].update(checkpoints=["FIXTURE_X"]),
    "actual_map_path":lambda s:s["files"].update({"Data/Map518.rxdata":b"bad"}),
    "actual_save_path":lambda s:s["files"].update({"saves/File A.rxdata":b"save"}),
    "windows_traversal":lambda s:s["files"].update({"docs/unova-package-fixtures/../saves/a.txt":b"a"}),
    "symlink_not_bytes":lambda s:s["files"].update({next(iter(s["files"])):"/tmp/game"}),
    "empty_documentation":lambda s:s["files"].update({next(iter(s["files"])):b""}),
    "missing_files":lambda s:s["files"].clear(),
    "too_large_file":lambda s:s["files"].update({next(iter(s["files"])):b"A"*(g72.MAX_BYTES+1)}),
}
for _name,_mutator in _BAD_STATES.items():
    def _invalid(self,mutate=_mutator):
        state=self.bundle()[0];mutate(state)
        with self.assertRaises(ValueError):
            tx.validate_state(state)
    setattr(UnovaG073Tests,"test_invalid_state_"+_name,_invalid)

# The G07.2 validator is a strict dependency; bypasses and malformed
# metadata still fail before any staged/backup memory is prepared.
_BAD_PACKAGES={
    "native_status":lambda p:p.update(status="PLAYABLE"),
    "native_payload":lambda p:p.update(native_payload_approved=True),
    "release":lambda p:p.update(release_allowed=True),
    "Android":lambda p:p["compatibility"].update(android="supported"),
    "Windows":lambda p:p["compatibility"].update(windows="installed"),
    "JoiPlay":lambda p:p["compatibility"].update(joiplay="supported"),
    "wrong_protocol":lambda p:p["compatibility"].update(protocol_version=2),
    "no_source_manifest":lambda p:p["source"].pop("manifest_sha256"),
    "wrong_source_revision":lambda p:p["source"].update(origin_revision="invalid"),
    "same_revision":lambda p:p["source"].update(target_revision=p["source"]["origin_revision"]),
    "tamper_package_digest":lambda p:p.update(package_sha256="a"*64),
    "missing_license":lambda p:p["files"][0]["rights"].pop("license_id"),
    "false_rights":lambda p:p["rights"].update(redistribution_approved=True),
    "bad_file_hash":lambda p:p["files"][0].update(sha256="c"*64),
    "wrong_source_hash":lambda p:p["files"][0].update(source_sha256="d"*64),
    "wrong_native_path":lambda p:p["files"][0].update(path="game/Data/Map518.rxdata"),
    "unknown_field":lambda p:p.update(unova_ready=True),
}
for _name,_mutator in _BAD_PACKAGES.items():
    def _invalid(self,mutate=_mutator):
        state,pkg,manifest,old,new=self.bundle()
        mutate(pkg)
        if _name != "tamper_package_digest":
            pkg["package_sha256"]=g72.package_digest(pkg)
        with self.assertRaises(ValueError):
            self.preview(state=state,package=pkg,manifest=manifest,old=old,new=new)
    setattr(UnovaG073Tests,"test_invalid_package_"+_name,_invalid)

if __name__=="__main__":
    unittest.main()
