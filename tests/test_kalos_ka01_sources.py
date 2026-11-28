import json
import unittest
from unittest.mock import patch
from qa.kalos_sources import ka01_source_audit as gate

class KalosSourcePolicyTest(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(gate.POLICY.read_text("utf8"))

    def test_opening_has_bidirectional_spine_and_center_branch(self):
        self.assertEqual(gate.validate_policy(self.policy), (11, 10))

    def test_permission_or_assignment_is_rejected(self):
        for field in ("destination_mapids", "external_install_permissions", "external_redistribution_permissions"):
            self.policy[field] = ["not authorized"]
            with self.assertRaisesRegex(ValueError, "must not approve"):
                gate.validate_policy(self.policy)
            self.policy[field] = []

    def test_wrong_hash_is_rejected_before_parsing(self):
        with patch.object(gate, "loads") as parser, self.assertRaisesRegex(ValueError, "not the pinned"):
            gate.validate(self.policy, b"wrong donor")
        parser.assert_not_called()

    def test_scope_cannot_open_next_route(self):
        self.policy["opening_spine"].insert(8, ["ROUTE_04", None])
        with self.assertRaisesRegex(ValueError, "crosses"):
            gate.validate_policy(self.policy)

    def test_existing_tiles_are_not_automatically_license_granted(self):
        self.policy["tiles"] = "APPROVED_TO_REDISTRIBUTE"
        with self.assertRaisesRegex(ValueError, "not a license"):
            gate.validate_policy(self.policy)
