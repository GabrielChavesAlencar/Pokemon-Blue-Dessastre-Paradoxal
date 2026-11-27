"""Verify the authored maps and reciprocal portal locations before remapping."""

from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/regions"))
import unova_original_opening as opening
from audit_sinnoh_playable_j09 import audit_map


class OriginalOpeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files, cls.receipt = opening.generate()

    def test_regular_rmxp_geometry_with_unique_checksums(self):
        maps = self.receipt["maps"]
        self.assertEqual(len(maps), 7)
        self.assertEqual(len({row["sha256"] for row in maps.values()}), len(maps))
        for symbol, row in maps.items():
            with self.subTest(symbol=symbol):
                content = self.files[row["file"]]
                decoded = audit_map(content)
                self.assertEqual([decoded["width"], decoded["height"]], row["size"])
                self.assertEqual(opening.checksum(content), row["sha256"])
                self.assertGreater(row["reachable_cells"], 100)
                self.assertIsNone(row["map_id"])
        self.assertFalse(self.receipt["runtime_verified"])

    def test_complete_reciprocal_corridor(self):
        maps = self.receipt["maps"]
        for source, row in maps.items():
            for door in row["candidate_doors"]:
                reverse, = [p for p in maps[door["destination"]]["candidate_doors"]
                            if p["destination"] == source]
                self.assertNotEqual(reverse["threshold"], door["arrival"])
                self.assertEqual(sum(abs(a - b) for a, b in
                                     zip(reverse["threshold"], door["arrival"])), 1)
        reached = {opening.BEDROOM}
        pending = [opening.BEDROOM]
        while pending:
            for door in maps[pending.pop()]["candidate_doors"]:
                if door["destination"] not in reached:
                    reached.add(door["destination"])
                    pending.append(door["destination"])
        self.assertEqual(reached, set(maps))
        self.assertEqual(sum(len(row["candidate_doors"]) for row in maps.values()), 12)

    def test_private_export_keeps_the_first_build(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.assertEqual(opening.build(root), self.receipt)
            result = root / opening.OUTPUT
            self.assertEqual((result / "manifest.json").read_bytes(), self.files["manifest.json"])
            with self.assertRaisesRegex(ValueError, "Já existe"):
                opening.build(root)
            self.assertEqual(sorted(p.name for p in root.iterdir()), [".blue-work"])
