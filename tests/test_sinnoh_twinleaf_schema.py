"""CH06: negative tests for authored Twinleaf schema, graph and map bounds."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from scripts.regions.audit_sinnoh_twinleaf_events import (
    ROOT, SCHEMA, SPEC, audit, read_json, validate_schema,
)

SCRIPT = ROOT / "scripts/regions/audit_sinnoh_twinleaf_events.py"


class TwinleafSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.template = read_json(SPEC)
        cls.schema = read_json(SCHEMA)

    def draft(self):
        return copy.deepcopy(self.template)

    def filled(self):
        d = self.draft()
        sizes = {m["symbol"]: [32, 32] for m in d["maps"]}
        for mid, m in enumerate(d["maps"], start=500):
            m["map_id"], m["map_sha256"] = mid, "b" * 64
            for i, event in enumerate(m["events"]):
                event["x"], event["y"] = i + 2, 4
                event["verified_position"] = True
                if event["kind"] == "warp":
                    event["arrival_x"], event["arrival_y"] = 10, 11
                    event["verified_arrival"] = True
                else:
                    event["sprite"] = "OriginalSyntheticSprite"
                    event["verified_sprite"] = True
        d["start"].update(map_id=500, x=12, y=12,
                          verified_position=True, passability_verified=True)
        return d, sizes

    def blocked(self, draft, reason, *, sizes=None):
        with self.assertRaisesRegex(ValueError, reason):
            audit(draft, self.schema, dimensions=sizes)

    def test_actual_draft_is_structurally_valid_not_playable(self):
        status = audit(self.template, self.schema)
        self.assertEqual((status["maps"], status["events"], status["warps"]),
                         (9, 24, 16))
        self.assertEqual(status["bidirectional_pairs"], 8)
        self.assertTrue(status["all_maps_reachable_from_bedroom"])
        self.assertEqual(status["coordinates_mode"], "NULL_UNVERIFIED_TEMPLATE")
        self.assertFalse(status["can_install"])
        self.assertFalse(status["native_game_verified"])

    def test_cli_reads_only_and_reports_no_gameplay_proof(self):
        proc = subprocess.run([sys.executable, str(SCRIPT)], text=True,
                              capture_output=True, check=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertFalse(data["game_modified"])
        self.assertFalse(data["actual_geometry_verified"])

    def test_schema_metadata_and_supported_contracts(self):
        validate_schema(self.template, self.schema)
        self.assertEqual(self.schema["$schema"],
                         "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(set(self.schema["$defs"]),
                         {"start", "map", "warp", "handler", "starter_ball"})

    def test_missing_fields_and_extra_commands_rejected(self):
        for target, field in (
            ("start", "passability_verified"),
            ("map", "events"),
            ("warp", "verified_arrival"),
            ("ball", "species"),
        ):
            with self.subTest(target=target):
                d = self.draft()
                node = {"start": d["start"], "map": d["maps"][0],
                        "warp": d["maps"][0]["events"][0],
                        "ball": d["maps"][5]["events"][1]}[target]
                node.pop(field)
                self.blocked(d, "obrigat|contrato")
        d = self.draft()
        d["maps"][0]["events"][0]["ruby_script"] = "Kernel.system('rm -rf /')"
        self.blocked(d, "contrato")

    def test_invalid_kind_trigger_and_types_are_rejected(self):
        d = self.draft()
        d["maps"][0]["events"][0]["kind"] = "unsafe"
        self.blocked(d, "contrato")
        d = self.draft()
        d["maps"][0]["events"][0]["trigger"] = "action"
        self.blocked(d, "contrato")
        d = self.draft()
        d["maps"][0]["events"][0]["verified_arrival"] = "true"
        self.blocked(d, "contrato")
        d = self.draft()
        d["maps"][0]["map_id"] = True
        self.blocked(d, "contrato")
        for field in ("approved_for_install", "gameplay_verified"):
            d = self.draft()
            d[field] = True
            self.blocked(d, "valor fixo")

    def test_missing_duplicate_or_unlisted_maps_rejected(self):
        d = self.draft()
        d["maps"].pop()
        self.blocked(d, "mínimo")
        d = self.draft()
        d["maps"][0]["symbol"] = d["maps"][1]["symbol"]
        self.blocked(d, "duplicados")
        d = self.draft()
        d["maps"][1]["symbol"] = "SINNOH_UNKNOWN_MAP"
        self.blocked(d, "lista permitida")

    def test_duplicate_event_id_wrong_handler_and_wrong_ball_rejected(self):
        d = self.draft()
        d["maps"][0]["events"][0]["key"] = d["maps"][1]["events"][1]["key"]
        self.blocked(d, "duplicado")
        d = self.draft()
        d["maps"][1]["events"][0]["handler"] = "barry_intro"
        self.blocked(d, "handler")
        d = self.draft()
        d["maps"][5]["events"][1]["species"] = "PIPLUP"
        self.blocked(d, "Poké Bola")
        d = self.draft()
        d["maps"][5]["events"][1]["key"] = "SN_BALL_FAKE"
        self.blocked(d, "Poké Bola")

    def test_orphan_transfer_and_self_cycle_rejected(self):
        d = self.draft()
        d["maps"][0]["events"][0]["destination"] = "SINNOH_NOT_DEFINED"
        self.blocked(d, "contrato")
        d = self.draft()
        d["maps"][0]["events"][0]["destination"] = "SINNOH_PLAYER_BEDROOM"
        self.blocked(d, "próprio mapa")

    def test_missing_return_warp_or_topology_change_rejected(self):
        d = self.draft()
        d["maps"][0]["events"][0]["destination"] = "SINNOH_ROUTE_201"
        self.blocked(d, "sem retorno|topologia")
        d = self.draft()
        d["maps"][0]["events"].append(copy.deepcopy(d["maps"][0]["events"][0]))
        d["maps"][0]["events"][-1]["key"] = "SN_EXTRA_WARP"
        self.blocked(d, "duplicado|24 eventos")

    def test_unverified_coordinates_and_spawn_cannot_be_pretended(self):
        d = self.draft()
        d["maps"][0]["map_id"] = 500
        self.blocked(d, "sem dimensões")
        d = self.draft()
        d["maps"][0]["events"][0]["x"] = 2
        self.blocked(d, "null/false")
        d = self.draft()
        d["start"]["passability_verified"] = True
        self.blocked(d, "spawn")

    def test_synthetic_dimensions_can_check_bounds_but_do_not_unlock_game(self):
        d, dims = self.filled()
        result = audit(d, self.schema, dimensions=dims)
        self.assertEqual(result["coordinates_mode"], "BOUNDS_FROM_SUPPLIED_DIMENSIONS_ONLY")
        self.assertFalse(result["native_game_verified"])
        self.assertFalse(result["can_install"])

    def test_out_of_bounds_event_arrival_spawn_are_rejected(self):
        d, dim = self.filled()
        d["maps"][5]["events"][0]["x"] = 32
        self.blocked(d, "fora dos limites", sizes=dim)
        d, dim = self.filled()
        d["maps"][0]["events"][0]["arrival_y"] = 32
        self.blocked(d, "fora dos limites", sizes=dim)
        d, dim = self.filled()
        d["start"]["x"] = -1
        self.blocked(d, "contrato|fora dos limites", sizes=dim)

    def test_duplicate_positions_and_map_ids_rejected(self):
        d, dim = self.filled()
        d["maps"][5]["events"][1]["x"] = d["maps"][5]["events"][0]["x"]
        self.blocked(d, "mesma coordenada", sizes=dim)
        d, dim = self.filled()
        d["maps"][1]["map_id"] = d["maps"][0]["map_id"]
        self.blocked(d, "MapIDs", sizes=dim)

    def test_missing_sprite_arrival_and_bad_dimensions_rejected(self):
        d, dim = self.filled()
        d["maps"][5]["events"][1]["verified_sprite"] = False
        self.blocked(d, "sprite", sizes=dim)
        d, dim = self.filled()
        d["maps"][0]["events"][0]["verified_arrival"] = False
        self.blocked(d, "chegada", sizes=dim)
        d, dim = self.filled()
        dim.pop("SINNOH_ROUTE_202")
        self.blocked(d, "exatamente", sizes=dim)
        d, dim = self.filled()
        dim["SINNOH_ROUTE_202"] = [True, 32]
        self.blocked(d, "dimensões inválidas", sizes=dim)

    def test_wrong_spawn_map_rejected(self):
        d, dim = self.filled()
        d["start"]["map_id"] = 501
        self.blocked(d, "outro mapa", sizes=dim)


if __name__ == "__main__":
    unittest.main()
