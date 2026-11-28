import unittest
from qa.kalos_mapids import ka02_candidates as audit

class MapIDConflictGuardTests(unittest.TestCase):
    def setUp(self):
        self.controls = audit.static_controls()
        self.fixture = {
            "occupied_or_declared_ids": [1,2,100],
            "source_proof": {"archive_sha256": audit.ANDROID_247_SHA256},
            "file_count": 3, "mapinfos_sha256": "a" * 64,
        }

    def test_fences_include_old_and_in_flight_revisions(self):
        denied = audit.protected(self.controls)
        self.assertTrue(set(range(276,280)) <= denied)
        self.assertTrue(set(range(442,1000)) <= denied)
        self.assertTrue(set(range(609,622)) <= denied)

    def test_merges_references_without_declaring_free_slots(self):
        out = audit.census(self.controls,self.fixture,{2,3},{4,5},7,11,3,2)
        self.assertEqual(out["unresolved_static_or_connection_destination_ids"], [3,4,5])
        self.assertFalse(out["may_allocate"])
        self.assertEqual(out["mapids_allocated"], 0)
        self.assertEqual(out["transfer_201_dynamic_count_not_resolved"], 7)

    def test_missing_maps_are_not_same_as_no_references(self):
        with self.assertRaisesRegex(ValueError,"Missing physical"):
            audit.census(self.controls,self.fixture,set(),set(),0,0,2,0)

    def test_loss_of_regional_fence_fails_closed(self):
        self.controls["protected"].pop("HOENN")
        with self.assertRaisesRegex(ValueError,"hold was removed"):
            audit.protected(self.controls)

    def test_connection_validation(self):
        self.assertEqual(audit.connection_ids(b"# comment\n19,North,0,20,South,-2\n"),({19,20},1))
        with self.assertRaisesRegex(ValueError,"Unsupported PBS"):
            audit.connection_ids(b"1,North,0,unknown,South,0")

if __name__ == "__main__":
    unittest.main()
