"""Testa a checagem de prontidao do piloto sem usar dados de terceiros."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from inspect_johto_pilot_readiness import assess, EXPECTED_TOPOLOGY


def fixture(*, complete=False, with_connections=False):
    symbols = sorted({x[0] for x in EXPECTED_TOPOLOGY.values()} |
                     {x[2] for x in EXPECTED_TOPOLOGY.values()
                      if x[1] == "warp"})
    ids = {sym: 601 + index for index, sym in enumerate(symbols)}
    stage = {"schema": 1, "region": "JOHTO", "status": "GEOMETRY_PREVIEW_ONLY",
             "can_install": False, "not_playable": True,
             "maps": [{"symbol": k, "destination_id": v, "events_imported": 0}
                      for k, v in ids.items()]}
    rooms = {k: {"sha256": f"{i+1:064x}", "width": 20, "height": 20}
             for i, k in enumerate(symbols)}
    spec = {"schema": 1, "region": "JOHTO",
            "status": "EVENT_COORDINATES_REQUIRE_REAL_AUDIT",
            "maps": [{"symbol": k, "map_id": ids[k], "map_sha256": rooms[k]["sha256"],
                      "events": []} for k in symbols],
            "start": {"symbol": "JOHTO_NEW_BARK_PLAYER_HOME_2F", "x": None,
                      "y": None, "verified_position": False,
                      "passability_verified": False}}
    lookup = {row["symbol"]: row for row in spec["maps"]}
    for index, (key, (symbol, kind, destination)) in enumerate(EXPECTED_TOPOLOGY.items()):
        event = {"key": key, "kind": kind,
                 "x": index % 10 + 1 if complete else None, "y": 1 if complete else None,
                 "verified_position": complete}
        if kind == "warp":
            event.update(destination=destination,
                         arrival_x=2 if complete else None,
                         arrival_y=2 if complete else None)
        else:
            event.update(handler=destination,
                         sprite="Test_Character" if complete else None)
        lookup[symbol]["events"].append(event)
    if complete:
        spec["start"].update(x=3, y=3, verified_position=True,
                             passability_verified=True)
    conn = "{},West,13,{},East,0\n".format(
        ids["JOHTO_NEW_BARK_TOWN"], ids["JOHTO_ROUTE_29"])
    return stage, spec, rooms, {"Test_Character"}, conn


class FirstPlayableReadinessTest(unittest.TestCase):
    def test_unverified_template_reports_missing_event_positions(self):
        stage, spec, rooms, sprites, conn = fixture()
        report = assess(stage, spec, rooms, sprites)
        self.assertEqual(report["events_total"], 12)
        self.assertFalse(report["ready_for_isolated_assembly"])
        self.assertEqual(report["events_ready"], 0)
        self.assertFalse(report["gameplay_playable"])
        self.assertFalse(report["gameplay_tested"])
        self.assertTrue(any(e["problem"] == "SPAWN_XY_AUSENTE"
                            for e in report["outstanding"]))
        self.assertTrue(any(e["problem"] == "CHEGADA_XY_AUSENTE"
                            for e in report["outstanding"]))

    def test_fully_reviewed_coordinates_allow_only_isolated_assembly(self):
        stage, spec, rooms, sprites, conn = fixture(complete=True)
        report = assess(stage, spec, rooms, sprites)
        self.assertEqual(report["status"], "READY_FOR_ISOLATED_ASSEMBLY_NOT_PLAYABLE")
        self.assertEqual(report["events_ready"], 12)
        self.assertTrue(report["ready_for_isolated_assembly"])
        self.assertFalse(report["gameplay_playable"])
        self.assertFalse(report["can_install"])

    def test_border_connection_can_replace_only_its_two_warps(self):
        stage, spec, rooms, sprites, conn = fixture(complete=True)
        for row in spec["maps"]:
            for e in row["events"]:
                if e["key"] in ("JH_TOWN_TO_ROUTE29", "JH_ROUTE29_TO_NEW_BARK"):
                    e.update(x=None, y=None, arrival_x=None, arrival_y=None,
                             verified_position=False)
        without_pbs = assess(stage, spec, rooms, sprites)
        self.assertFalse(without_pbs["ready_for_isolated_assembly"])
        with_pbs = assess(stage, spec, rooms, sprites,
                          with_connections=True, connections=conn)
        self.assertTrue(with_pbs["ready_for_isolated_assembly"])
        self.assertEqual(with_pbs["events_ready"], 12)
        bad_pbs = assess(stage, spec, rooms, sprites, with_connections=True,
                         connections="602,West,13,603,East,0\n")
        self.assertFalse(bad_pbs["ready_for_isolated_assembly"])
        self.assertIn("LIGACAO_NEW_BARK_ROUTE29_NAO_UNICA",
                      bad_pbs["border_issues"])
        duplicate = assess(stage, spec, rooms, sprites, with_connections=True,
                           connections=conn + conn)
        self.assertFalse(duplicate["ready_for_isolated_assembly"])

    def test_rejects_swapped_handlers_missing_stage_and_stale_sha(self):
        stage, spec, rooms, sprites, conn = fixture(complete=True)
        corrupt = copy.deepcopy(spec)
        corrupt["maps"][0]["map_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            assess(stage, corrupt, rooms, sprites)
        corrupt = copy.deepcopy(spec)
        e = next(e for row in corrupt["maps"] for e in row["events"]
                 if e["key"] == "JH_NPC_ELM")
        e["handler"] = "mother"
        with self.assertRaisesRegex(ValueError, "Topologia"):
            assess(stage, corrupt, rooms, sprites)
        corrupt_stage = copy.deepcopy(stage)
        corrupt_stage["maps"] = corrupt_stage["maps"][:-1]
        with self.assertRaisesRegex(ValueError, "cinco mapas"):
            assess(corrupt_stage, spec, rooms, sprites)

    def test_rejects_coordinate_collision_and_absent_sprite(self):
        stage, spec, rooms, sprites, conn = fixture(complete=True)
        elm = next(row for row in spec["maps"]
                   if row["symbol"] == "JOHTO_NEW_BARK_ELM_LAB")
        elm["events"][1]["x"], elm["events"][1]["y"] = (
            elm["events"][0]["x"], elm["events"][0]["y"])
        result = assess(stage, spec, rooms, set())
        self.assertFalse(result["ready_for_isolated_assembly"])
        self.assertTrue(any(e["problem"] == "COORDENADA_OCUPADA"
                            for e in result["outstanding"]))
        self.assertTrue(any(e["problem"] == "SPRITE_PNG_NAO_ENCONTRADO"
                            for e in result["outstanding"]))


if __name__ == "__main__":
    unittest.main()
