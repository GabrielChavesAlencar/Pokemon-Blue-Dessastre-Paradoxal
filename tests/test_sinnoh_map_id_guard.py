"""CH03: fail-closed Sinnoh-vs-Johto map-ID ownership contracts."""
from __future__ import annotations

import unittest

from scripts.regions.sinnoh_map_id_guard import (
    JOHTO_SHARED_PREVIEW_IDS,
    JOHTO_SINNOH_EXCLUSION,
    LEGACY_SINNOH_PILOT_IDS,
    assert_johto_shared_overlay_map_ids,
    assert_sinnoh_shared_destinations,
)


class SinnohJohtoMapIdGuardTests(unittest.TestCase):
    def test_legacy_and_protected_ranges_are_explicit(self):
        self.assertEqual(sorted(LEGACY_SINNOH_PILOT_IDS), list(range(800, 806)))
        self.assertTrue(LEGACY_SINNOH_PILOT_IDS.issubset(JOHTO_SINNOH_EXCLUSION))
        self.assertEqual(JOHTO_SHARED_PREVIEW_IDS, frozenset(range(600, 700)))

    def test_explicit_shared_sinnoh_candidates_must_be_below_600(self):
        self.assertIsNone(assert_sinnoh_shared_destinations([1, 500, 599]))
        for mid in (0, 600, 699, 700, 799, 806, 999, 1000, 1200):
            with self.subTest(mid=mid), self.assertRaisesRegex(
                ValueError, "limite conservador"
            ):
                assert_sinnoh_shared_destinations([mid])
        for mid in range(800, 806):
            with self.subTest(legacy_mid=mid), self.assertRaisesRegex(
                ValueError, "legado"
            ):
                assert_sinnoh_shared_destinations([mid])

    def test_sinnoh_ids_must_be_explicit_unique_ints(self):
        for case in ([500, 500], [True], [1.0], ["800"], "800", None, {}):
            with self.subTest(case=case), self.assertRaises(ValueError):
                assert_sinnoh_shared_destinations(case)

    def test_johto_staging_only_accepts_its_own_map_paths(self):
        found = assert_johto_shared_overlay_map_ids({
            "Data/Map600.rxdata": b"johto",
            "Data/Map699.rxdata": b"johto",
            "Data/MapInfos.rxdata": b"shared",
            "PBS/map_connections.txt": b"shared",
        })
        self.assertEqual(found, frozenset({600, 699}))

    def test_all_legacy_sinnoh_map_files_are_rejected_from_johto(self):
        for mid in sorted(LEGACY_SINNOH_PILOT_IDS):
            with self.subTest(mid=mid), self.assertRaisesRegex(
                ValueError, f"MapID {mid}.*Sinnoh"
            ):
                assert_johto_shared_overlay_map_ids({
                    "Data/Map600.rxdata": b"johto",
                    f"Data/Map{mid:03}.rxdata": b"sinnoh-legacy",
                })

    def test_other_region_ids_and_aliases_are_not_accepted(self):
        for name in ("Data/Map500.rxdata", "Data/Map700.rxdata",
                     "Data/Map999.rxdata", "Data/Map1000.rxdata"):
            with self.subTest(name=name), self.assertRaisesRegex(
                ValueError, "fora dos mapas"
            ):
                assert_johto_shared_overlay_map_ids({
                    "Data/Map600.rxdata": b"ok", name: b"not Johto",
                })
        for name in ("Data/Map0800.rxdata", "DATA/MAP800.RXDATA",
                     "Data/Map600.rxdata.bak", "Data\\Map800.rxdata"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                assert_johto_shared_overlay_map_ids({
                    "Data/Map600.rxdata": b"ok", name: b"foreign",
                })

    def test_rejects_duplicate_names_unknown_expected_range_and_empty_payload(self):
        for item in (
            {"Data/Map600.rxdata": b"a", "data/map600.RXDATA": b"b"},
            {"Data/Map600.rxdata": b"a", "Data/Map0600.rxdata": b"b"},
        ):
            with self.subTest(item=item), self.assertRaisesRegex(
                ValueError, "duplicad"
            ):
                assert_johto_shared_overlay_map_ids(item)
        with self.assertRaisesRegex(ValueError, "reserva"):
            assert_johto_shared_overlay_map_ids(
                {"Data/Map600.rxdata": b"a"}, allowed_ids=frozenset({800}))
        with self.assertRaisesRegex(ValueError, "nenhum mapa"):
            assert_johto_shared_overlay_map_ids({"Data/MapInfos.rxdata": b"x"})


if __name__ == "__main__":
    unittest.main()
