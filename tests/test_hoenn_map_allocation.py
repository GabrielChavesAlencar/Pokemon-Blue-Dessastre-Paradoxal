"""Hoenn MapKey migration fixtures without map assets or a personal install."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/regions"))

from hoenn_catalog import CATALOG, LEGACY_SOURCE_IDS
from pilot_hoenn import SOURCE_MAPS, allocate_hoenn_map_ids, plan_hoenn_map_ids, validate_pilot_mapping


class HoennMapAllocationTests(unittest.TestCase):
    def test_existing_pairs_are_stable_when_a_source_is_added(self):
        previous = {7: 705, 8: 702}
        reserved = {700, 702, 703, 705}
        self.assertEqual(plan_hoenn_map_ids((7, 8, 107), reserved, previous, foreign={701}),
                         {7: 705, 8: 702, 107: 704})
        self.assertEqual(plan_hoenn_map_ids((7, 8), reserved, previous), previous)

    def test_exhaustion_does_not_allocate_four_digit_ids(self):
        previous = {7: 700}
        with self.assertRaisesRegex(ValueError, "abaixo de 1000"):
            plan_hoenn_map_ids((7, 8), range(700, 1000), previous)

    def test_missing_or_competing_legacy_claim_refuses_migration(self):
        with self.assertRaisesRegex(ValueError, "legado de Hoenn ausente"):
            plan_hoenn_map_ids((7, 8), {710}, {7: 700})
        with self.assertRaisesRegex(ValueError, "também pertence"):
            plan_hoenn_map_ids((7, 8), {700}, {7: 700}, foreign={700})

    def test_real_scan_reserves_pbs_foreign_manifest_and_unindexed_map(self):
        with tempfile.TemporaryDirectory() as directory:
            game = Path(directory)
            (game / "Data").mkdir()
            (game / "PBS").mkdir()
            (game / "Data/Map702.rxdata").write_bytes(b"legacy")
            (game / "Data/Map703.rxdata").write_bytes(b"orphan")
            (game / "Data/blue-kanto-install.json").write_text(
                json.dumps({"maps": {"1": 705}}), encoding="utf-8")
            (game / "PBS/map_metadata_other.txt").write_text("[701]\n", encoding="utf-8")
            (game / "PBS/map_connections_other.txt").write_text(
                "704,North,0,112,South,0\n", encoding="utf-8")
            infos = {700: object(), 702: object()}
            self.assertEqual(allocate_hoenn_map_ids(game, (7, 8), {7: 702}, native_infos=infos),
                             {7: 702, 8: 706})
            with self.assertRaisesRegex(ValueError, "sem arquivo ou registro"):
                allocate_hoenn_map_ids(game, (7, 8), {7: 703}, native_infos=infos)
            # A differently padded filename claims the same ID.
            (game / "Data/Map0703.rxdata").write_bytes(b"alias")
            with self.assertRaisesRegex(ValueError, "nomes de arquivo conflitantes"):
                allocate_hoenn_map_ids(game, (7, 8), {7: 702}, native_infos=infos)

    def test_private_pilot_requires_exact_keys_for_its_recorded_revision(self):
        legacy = {mid: 700+i for i, mid in enumerate(sorted(LEGACY_SOURCE_IDS))}
        false_map = dict(legacy)
        false_map[999] = false_map.pop(7)
        with self.assertRaisesRegex(ValueError, "inválido"):
            validate_pilot_mapping({"maps": false_map})
        with patch.dict(CATALOG["revisions"], {"2": [*LEGACY_SOURCE_IDS, 107]}), \
             patch.dict(SOURCE_MAPS, {107: "mapa sintético de teste"}):
            larger = {**legacy, 107: 899}
            self.assertEqual(validate_pilot_mapping({"maps": larger, "catalog_revision": 2}), larger)
            with self.assertRaisesRegex(ValueError, "inválido"):
                validate_pilot_mapping({"maps": legacy, "catalog_revision": 2})
            self.assertEqual(validate_pilot_mapping({"maps": legacy}), legacy)


if __name__ == "__main__":
    unittest.main()
