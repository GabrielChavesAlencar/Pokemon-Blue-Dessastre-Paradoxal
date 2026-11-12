"""Pure graph and guard tests for the read-only Kanto pilot audit."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

REGIONS = Path(__file__).resolve().parents[1] / "scripts" / "regions"
sys.path.insert(0, str(REGIONS))
try:
    from verify_pilot import reachable
    from pilot import PILOT_META, build_signature, pilot_is_current
    from audit import PILOT_V1_SOURCE_IDS, stable_source_order
finally:
    sys.path.remove(str(REGIONS))


class KantoPilotAuditTests(unittest.TestCase):
    def test_functional_interiors_append_without_shifting_previous_101_map_slots(self):
        root = REGIONS.parents[1]
        manifest = json.loads((root / "data/regions/kanto-source.json").read_text("utf-8"))
        order = stable_source_order({int(k) for k in manifest["maps"]})
        self.assertEqual(len(order), 109)
        self.assertEqual(tuple(order[:13]), PILOT_V1_SOURCE_IDS)
        self.assertEqual(len(set(order)), 109)
        self.assertEqual(order[13:25], [26,27,32,33,34,36,37,38,39,40,41,42])
        self.assertEqual(order[25:40], [56,59,60,61,63,64,65,66,67,72,74,75,76,77,78])
        self.assertEqual(order[40:51], [111,114,115,117,118,119,120,121,122,123,124])
        self.assertEqual(order[51:71], [141,142,143,144,145,146,147,152,153,155,
                                      156,157,158,159,160,161,162,163,164,165])
        self.assertEqual(order[71:100], [57,62,107,108,109,110,112,113,168,169,170,171,
                                     172,174,175,176,177,178,179,180,181,182,183,
                                     184,185,186,187,188,189])
        self.assertEqual(order[100:101], [173])
        self.assertEqual(order[101:], [8,14,15,21,22,29,30,31])
        self.assertEqual(manifest["preview_only"], sorted([
            111,117,118,119,120,121,122,123,
            141,142,143,152,155,156,157,158,159,
            160,161,162,163,164,165,
            57,62,107,108,109,110,112,113,168,169,170,171,172,
            173,174,175,176,177,178,179,180,181,182,183,184,185,186,187,188,189]))
        self.assertIn(42, order[13:])
        self.assertEqual(len(manifest["preview_only"]), 53)
        self.assertTrue({114, 115, 124, 144, 145, 146, 147, 153}.isdisjoint(manifest["preview_only"]))

    def test_portal_matches_audited_cerulean_roster(self):
        root = REGIONS.parents[1]
        data = json.loads((root / "site/public/data/kanto.json").read_text("utf-8"))
        self.assertEqual(len(data["locations"]), 109)
        self.assertEqual(len(data["trainers"]), 69)
        for slug in ("kanto-rivals-house", "kanto-viridian-house-north",
                     "kanto-viridian-house-south", "kanto-route2-secret-gatehouse",
                     "kanto-route2-hidden-house", "kanto-pewter-museum",
                     "kanto-pewter-house-north", "kanto-pewter-house-south"):
            self.assertTrue(any(row["id"] == slug for row in data["locations"]),
                            "Missing functional interior in portal: " + slug)
        misty = next(t for t in data["trainers"] if t["id"] == "kanto-misty")
        self.assertTrue(misty["leader"])
        self.assertEqual(misty["location"], "kanto-cerulean-gym")
        self.assertEqual(
            [(p["species"], p["level"]) for p in misty["variants"][0]["team"]],
            [("STARYU", 18), ("STARMIE", 21)]
        )
        # Stage 09 opens ONLY the three core maps for adapted gameplay.
        # Route 7 and all seven department-store floors stay geometry-only.
        preview = [x for x in data["locations"] if x["id"].startswith(
            ("kanto-celadon-dept-", "kanto-route-7"))]
        self.assertEqual(len(preview), 8)
        self.assertTrue(all(not x["methods"] and not x["trainers"] for x in preview))
        erika = next(t for t in data["trainers"] if t["id"] == "kanto-erika")
        self.assertTrue(erika["leader"])
        self.assertEqual(erika["location"], "kanto-celadon-gym")
        self.assertEqual([(p["species"], p["level"]) for p in erika["variants"][0]["team"]],
                         [("VICTREEBEL", 29), ("TANGELA", 24), ("VILEPLUME", 29)])
        gym = next(x for x in data["locations"] if x["id"] == "kanto-celadon-gym")
        self.assertEqual(len(gym["trainers"]), 8)
        self.assertTrue(all(x in {t["id"] for t in data["trainers"]}
                            for x in gym["trainers"]))
        # Koga + six gym trainers must appear only in Fuchsia Gym.
        koga = next(t for t in data["trainers"] if t["id"] == "kanto-koga")
        self.assertTrue(koga["leader"])
        self.assertEqual(koga["location"], "kanto-fuchsia-gym")
        self.assertEqual(
            [(p["species"], p["level"]) for p in koga["variants"][0]["team"]],
            [("KOFFING", 37), ("MUK", 39), ("KOFFING", 37), ("WEEZING", 43)])
        fgym = next(x for x in data["locations"] if x["id"] == "kanto-fuchsia-gym")
        self.assertEqual(len(fgym["trainers"]), 7)
        self.assertTrue(all(x in {t["id"] for t in data["trainers"]}
                            for x in fgym["trainers"]))
        for slug in ("kanto-fuchsia-city", "kanto-fuchsia-center",
                     "kanto-fuchsia-mart", "kanto-fuchsia-safari-gate"):
            row = next(x for x in data["locations"] if x["id"] == slug)
            self.assertEqual(row["methods"], [])
            self.assertEqual(row["trainers"], [])
        for slug in ("kanto-fuchsia-warden-house", "kanto-safari-south",
                     "kanto-safari-north", "kanto-safari-west",
                     "kanto-safari-secret-house"):
            preview_row = next(x for x in data["locations"] if x["id"] == slug)
            self.assertFalse(preview_row["methods"])
            self.assertFalse(preview_row["trainers"])

        for slug in ("kanto-celadon-city", "kanto-celadon-center"):
            city = next(x for x in data["locations"] if x["id"] == slug)
            self.assertEqual(city["methods"], [])
            self.assertEqual(city["trainers"], [])
        phase10 = [x for x in data["locations"] if x["id"].startswith(
            ("kanto-fuchsia-", "kanto-safari-", "kanto-route-15",
             "kanto-route-18"))]
        self.assertEqual(len(phase10), 20)
        active_fuchsia = {"kanto-fuchsia-city", "kanto-fuchsia-center",
                          "kanto-fuchsia-mart", "kanto-fuchsia-gym",
                          "kanto-fuchsia-safari-gate"}
        protected_fuchsia = [x for x in phase10 if x["id"] not in active_fuchsia]
        self.assertEqual(len(protected_fuchsia), 15)
        self.assertTrue(all(not x["methods"] and not x["trainers"]
                            for x in protected_fuchsia))
        self.assertEqual(sum(t["name"] == "Koga" for t in data["trainers"]), 1)
        phase11 = [x for x in data["locations"] if x["id"].startswith(
            ("kanto-saffron-", "kanto-silph-", "kanto-route-8",
             "kanto-underground-route"))]
        self.assertEqual(len(phase11), 30)
        self.assertTrue(all(not x["methods"] and not x["trainers"] for x in phase11))
        self.assertFalse(any("Sabrina" in trainer["name"] for trainer in data["trainers"]))
        surge = next(t for t in data["trainers"] if t["id"] == "kanto-lt. surge")
        self.assertTrue(surge["leader"])
        self.assertEqual(surge["location"], "kanto-vermilion-gym")
        self.assertEqual(
            [(p["species"], p["level"]) for p in surge["variants"][0]["team"]],
            [("VOLTORB", 21), ("PIKACHU", 18), ("RAICHU", 24)]
        )

    def test_reachability_follows_bidirectional_corridor(self):
        graph = {300: {301}, 301: {300, 302}, 302: {301}}
        self.assertEqual(reachable(graph, 300), {300, 301, 302})

    def test_isolated_map_is_not_silently_accepted(self):
        graph = {300: {301}, 301: {300}, 302: set()}
        self.assertEqual(reachable(graph, 300), {300, 301})
        self.assertNotEqual(reachable(graph, 300), set(graph))

    def test_one_way_transfer_does_not_create_a_fictitious_return_route(self):
        graph = {300: {301}, 301: {302}, 302: set()}
        self.assertEqual(reachable(graph, 300), {300, 301, 302})
        # The reverse direction is not automatically available:
        self.assertEqual(reachable(graph, 302), {302})

    def test_explicit_return_transfer_restores_bidirectional_access(self):
        graph = {300: {301}, 301: {302}, 302: {300}}
        self.assertEqual(reachable(graph, 302), {300, 301, 302})

    def test_pilot_signature_detects_obsolete_build_without_deleting_it(self):
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            marker = folder / PILOT_META
            self.assertFalse(pilot_is_current(folder))
            marker.write_text(json.dumps({"build_signature": build_signature()}), encoding="utf-8")
            self.assertTrue(pilot_is_current(folder))
            marker.write_text(json.dumps({"build_signature": "old-release"}), encoding="utf-8")
            self.assertFalse(pilot_is_current(folder))


if __name__ == "__main__":
    unittest.main()
