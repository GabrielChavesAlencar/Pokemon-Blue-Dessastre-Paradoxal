"""Pure graph and guard tests for the read-only Kanto pilot audit."""
import sys
import unittest
from pathlib import Path

REGIONS = Path(__file__).resolve().parents[1] / "scripts" / "regions"
sys.path.insert(0, str(REGIONS))
try:
    from verify_pilot import reachable
finally:
    sys.path.remove(str(REGIONS))


class KantoPilotAuditTests(unittest.TestCase):
    def test_reachability_follows_bidirectional_corridor(self):
        graph = {300: {301}, 301: {300, 302}, 302: {301}}
        self.assertEqual(reachable(graph, 300), {300, 301, 302})

    def test_isolated_map_is_not_silently_accepted(self):
        graph = {300: {301}, 301: {300}, 302: set()}
        self.assertEqual(reachable(graph, 300), {300, 301})
        self.assertNotEqual(reachable(graph, 300), set(graph))


if __name__ == "__main__":
    unittest.main()
