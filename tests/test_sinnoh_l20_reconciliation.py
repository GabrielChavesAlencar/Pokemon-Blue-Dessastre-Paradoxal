"""L20 public-only metadata reconciliation: fail-closed negative regression suite."""
from __future__ import annotations
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_l20_reconciliation as l20

def load(path):
    return json.loads((ROOT / path).read_text("utf8"))

class SinnohL20ReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = load(l20.REPORT)
        cls.mirror = load(l20.MIRROR)
        cls.source = load(l20.SOURCE)
        cls.trusted = l20.l19.expected_report(load(l20.l19.SOURCE))

    def audited(self, mutation=None):
        p = copy.deepcopy(self.report)
        m = copy.deepcopy(self.mirror)
        s = copy.deepcopy(self.source)
        t = copy.deepcopy(self.trusted)
        if mutation:
            mutation(p,m,s,t)
        return l20.audit(p,m,s,t)

    def rejected(self, mutation):
        with self.assertRaises(ValueError):
            self.audited(mutation)

    def test_success_88_public_only(self):
        d = self.audited()
        self.assertEqual(d["status"], "PUBLIC_METADATA_RECONCILIATION_AUDITED_ALL_BLOCKED")
        self.assertEqual((d["requests_matched"],d["gaps_open"],d["gaps_closed"]),(88,88,0))
        self.assertEqual((d["links"],d["anonymous_unassigned"]),(1084,18))
        self.assertFalse(d["sinnoh_playable"])

    def test_exact_mirror_bytes(self):
        self.assertEqual((ROOT/l20.REPORT).read_bytes(),(ROOT/l20.MIRROR).read_bytes())

    def test_immutable_l19_git_anchor(self):
        self.assertTrue(l20.check_l19_git_blobs(ROOT))
        self.assertEqual(l20.L19_BLOB,"ff9f86e14cd28f7960331580d85e2b10d99b8240")

    def test_full_parent_contract(self):
        self.assertEqual(l20.run(ROOT)["status"],
            "PUBLIC_METADATA_RECONCILIATION_AUDITED_ALL_BLOCKED")

    def test_never_accept_arbitrary_cli_paths(self):
        self.assertEqual(l20.main(["--root","/private"]),2)

    def test_git_blob_changes_when_bytes_change(self):
        original=(ROOT/l20.SOURCE).read_bytes()
        self.assertEqual(l20.blob_sha(original),l20.L19_BLOB)
        self.assertNotEqual(l20.blob_sha(original+b" " ),l20.L19_BLOB)

    def test_explicit_platform_separation(self):
        part={r["platform"]:r for r in self.report["platform_partition"]}
        self.assertEqual((len(part["windows"]["case_ids"]),len(part["android"]["case_ids"])),(43,1))
        self.assertTrue(part["windows"]["requires_windows_b10_b11"])
        self.assertFalse(part["android"]["requires_windows_b10_b11"])
        self.assertEqual(self.report["global_r09"]["case_ids"],[])
        self.assertEqual(self.report["global_r09"]["documentary_dependency_request_ids"],[])

# Each one becomes a separate discoverable unittest, not a shared subtest.
# Object mutation is applied independently to a fresh 4-document snapshot.
def replace(path, value, doc=0):
    def mutation(*docs):
        item=docs[doc]
        for key in path[:-1]:
            item=item[key]
        item[path[-1]]=value
    return mutation

NEGATIVE_MUTATIONS = {
    "wrong_stage":replace(["stage"],"L21"),
    "wrong_schema":replace(["schema"],2),
    "false_schema_zero":replace(["schema"],False),
    "wrong_region":replace(["region"],"UNOVA"),
    "wrong_version":replace(["version"],99),
    "wrong_status":replace(["status"],"READY"),
    "wrong_mode":replace(["mode"],"NATIVE_QA"),
    "untrusted_l19_sha":replace(["source","git_blob_sha1"],"0"*40),
    "untrusted_l19_commit":replace(["baseline_commits","L19"],"1"*40),
    "break_l18_history":replace(["baseline_commits","L18"],"2"*40),
    "remove_public_source":replace(["public_sources"],[]),
    "change_open_gaps":replace(["counts","open_gaps"],87),
    "close_a_gap":replace(["counts","closed_gaps"],1),
    "fake_human_review":replace(["counts","human_approved"],1),
    "fake_native_run":replace(["counts","native_executed"],1),
    "fake_native_pass":replace(["counts","native_approved"],1),
    "fake_local_report":replace(["counts","local_reports_received"],1),
    "fake_bcd_completed":replace(["counts","phase_bcd_completed"],1),
    "drop_1084_link":replace(["counts","documentary_links"],1083),
    "drop_846_case_criterion":replace(["edge_summary","case_to_criterion"],845),
    "drop_218_case_blocker":replace(["edge_summary","case_to_blocker"],217),
    "drop_20_criterion_blocker":replace(["edge_summary","criterion_to_blocker"],19),
    "anonymous_assigned":replace(["counts","anonymous_unassigned"],17),
    "alter_priority_count":replace(["priority_summary",4,"open"],43),
    "alter_priority_label":replace(["records",0,"priority_label"],"P4_NATIVE_QA_UNAUTHORIZED"),
    "alter_priority":replace(["records",0,"priority"],4),
    "alter_request_id":replace(["records",0,"request_id"],"FAKE"),
    "alter_subject_id":replace(["records",0,"subject_id"],"FAKE"),
    "alter_platform":replace(["records",0,"platform"],"android"),
    "alter_kind":replace(["records",0,"kind"],"NATIVE_CASE"),
    "alter_order":replace(["records",0,"order"],88),
    "alter_gap_types":replace(["records",0,"gap_types"],[]),
    "alter_l04_links":replace(["records",0,"linked_l04_criterion_ids"],[]),
    "invent_dependency":replace(["records",0,"documentary_dependency_request_ids"],["FAKE"]),
    "alter_edge_count":replace(["records",0,"documentary_dependency_count"],1),
    "fake_ready":replace(["records",0,"readiness"],"READY"),
    "fake_approved":replace(["records",0,"status"],"APPROVED"),
    "fake_review_state":replace(["records",0,"review_state"],"APPROVED"),
    "close_record_gap":replace(["records",0,"gap_open"],False),
    "alter_gap_status":replace(["records",0,"review_gap_status"],"CLOSED"),
    "fake_review_approval":replace(["records",0,"independent_review_approved"],True),
    "fake_exit_criterion":replace(["records",0,"exit_criteria_met"],True),
    "fake_native_test":replace(["records",0,"native_qa_executed"],True),
    "fake_physical_evidence":replace(["records",0,"physical_evidence_accepted"],True),
    "fake_named_reviewer":replace(["records",0,"assigned_reviewer"],True),
    "fake_anonymous_identity":replace(["records",0,"anonymous_identity_assigned"],True),
    "falsify_correspondence":replace(["records",0,"correspondence"],"PHYSICAL_VERIFIED"),
    "invent_r09_case":replace(["global_r09","case_ids"],["case-001"]),
    "approve_r07":replace(["gates","r07"],"APPROVED"),
    "approve_r08":replace(["gates","r08"],"APPROVED"),
    "approve_r09":replace(["gates","r09"],"APPROVED"),
    "allow_game_exe":replace(["policy","no_game_exe"],False),
    "allow_joiplay":replace(["policy","no_joiplay"],False),
    "allow_saves":replace(["policy","no_saves"],False),
    "allow_private_upload":replace(["policy","no_private_uploads"],False),
    "mark_playable":replace(["policy","sinnoh_playable"],True),
    "android_inherits_windows":replace(["platform_partition",1,"requires_windows_b10_b11"],True),
    "mirror_fake_approval":replace(["records",0,"independent_review_approved"],True,1),
    "mirror_fake_count":replace(["counts","open_gaps"],87,1),
    "tamper_source":replace(["records",0,"status"],"APPROVED",2),
    "tamper_trusted_source":replace(["records",0,"status"],"APPROVED",3),
}
for name, mutation in NEGATIVE_MUTATIONS.items():
    def test(self, mutation=mutation):
        self.rejected(mutation)
    setattr(SinnohL20ReconciliationTests,"test_negative_"+name,test)

if __name__ == "__main__":
    unittest.main()
