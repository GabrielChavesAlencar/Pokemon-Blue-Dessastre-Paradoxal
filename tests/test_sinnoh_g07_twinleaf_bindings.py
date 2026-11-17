"""G07: Twinleaf physical-binding readiness, using only public offline contracts."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
import audit_sinnoh_g07_twinleaf_bindings as g07


class SinnohG07BindingTests(unittest.TestCase):
    def source(self):
        return {key: copy.deepcopy(g07.load_public(ROOT / path))
                for key, path in g07.FILES.items()}

    def audited(self, changes=None):
        sources=self.source()
        if changes:
            changes(sources)
        return g07.audit(**sources)

    def test_01_report_is_static_not_playable(self):
        out=self.audited()
        self.assertEqual(out["status"],
            "TWINLEAF_SYMBOLIC_BINDING_MATRIX_ONLY_NATIVE_EVIDENCE_PENDING")
        self.assertEqual(out["mode"],"READ_ONLY_GITHUB_STATIC_CONTRACTS")
        for field in ("asset_rights_verified","real_native_map_evidence_inspected_on_github",
                      "game_exe_tested","joiplay_tested","r07_complete",
                      "r08_complete","r09_complete","can_install_live_game",
                      "gameplay_approved"):
            self.assertIs(out[field],False)
        for key in ("phase_b_approved","phase_c_approved","phase_d_approved"):
            self.assertIs(type(out[key]),int)
            self.assertEqual(out[key],0)

    def test_02_counts_match_existing_9_map_24_event_plan(self):
        counts=self.audited()["counts"]
        expected={
            "symbolic_maps":9,"planned_events":24,"planned_warps":16,
            "reciprocal_pairs":8,"planned_handlers":5,
            "planned_physical_starter_balls":3,"story_checkpoints":6,
            "physically_bound_maps":0,"physically_bound_events":0,
            "native_transfers_verified":0,"physical_starter_balls_verified":0,
        }
        self.assertEqual(counts,expected)

    def test_03_map_rows_are_all_unbound_even_with_54_terrain_candidates(self):
        out=self.audited()
        self.assertEqual([m["symbol"] for m in out["maps"]],list(g07.MAPS))
        self.assertEqual(out["terrain_stage"]["terrain_candidate_count"],54)
        self.assertEqual(out["terrain_stage"]["empty_placeholders_not_installed"],22)
        self.assertEqual(out["terrain_stage"]["clone_map_count_declared_by_b09_contract"],702)
        self.assertFalse(out["terrain_stage"]["symbol_to_terrain_map_link_proven"])
        self.assertFalse(out["terrain_stage"]["donor_events_present_in_private_geometry"])
        for m in out["maps"]:
            self.assertIsNone(m["native_map_id"])
            self.assertIsNone(m["map_sha256"])
            self.assertFalse(m["candidate_terrain_mapping_verified"])
            self.assertFalse(m["passability_verified"])
            self.assertEqual(m["status"],"PENDING_REAL_MAP_IDENTIFICATION")

    def test_04_eight_pairs_have_correct_return_event_keys(self):
        out=self.audited()
        planned={(m["symbol"],e["destination_symbol"]):e["key"]
                 for m in out["maps"] for e in m["planned_events"]
                 if e["kind"]=="warp"}
        self.assertEqual(len(planned),16)
        pairs=out["reciprocal_pairs"]
        self.assertEqual(len(pairs),8)
        for row in pairs:
            a,b=row["source_symbol"],row["destination_symbol"]
            self.assertEqual(row["forward_event_key"],planned[(a,b)])
            self.assertEqual(row["return_event_key"],planned[(b,a)])
            self.assertIsNone(row["forward_native_event_id"])
            self.assertFalse(row["arrival_passability_verified"])

    def test_05_nine_maps_reachable_from_bedroom(self):
        out=self.audited()
        graph={m["symbol"]:set() for m in out["maps"]}
        for row in out["reciprocal_pairs"]:
            a,b=row["source_symbol"],row["destination_symbol"]
            graph[a].add(b)
            graph[b].add(a)
        reached={"SINNOH_PLAYER_BEDROOM"}
        pending=list(reached)
        while pending:
            current=pending.pop()
            for neighbor in graph[current]-reached:
                reached.add(neighbor)
                pending.append(neighbor)
        self.assertEqual(reached,set(g07.MAPS))

    def test_06_starter_balls_are_physical_and_on_lake_verity(self):
        balls=self.audited()["starter_balls"]
        self.assertEqual([b["species"] for b in balls],
                         ["TURTWIG","CHIMCHAR","PIPLUP"])
        self.assertEqual([b["barry_counter_species"] for b in balls],
                         ["CHIMCHAR","PIPLUP","TURTWIG"])
        self.assertEqual([b["barry_pbs_version"] for b in balls],[0,1,2])
        for b in balls:
            self.assertEqual(b["map_symbol"],"SINNOH_LAKE_VERITY")
            self.assertEqual(b["trigger"],"action")
            self.assertIsNone(b["native_map_id"])
            self.assertIsNone(b["sprite"])

    def test_07_story_order_and_deps_follow_S13(self):
        steps=self.audited()["story_checkpoints"]
        self.assertEqual([s["flag"] for s in steps],list(g07.INTRO_FLAGS))
        self.assertEqual([s["needs"] for s in steps],
                         [[]]+[[f] for f in g07.INTRO_FLAGS[:-1]])
        self.assertEqual(steps[3]["physical_starter_ball_keys"],
                         ["SN_BALL_TURTWIG","SN_BALL_CHIMCHAR","SN_BALL_PIPLUP"])
        self.assertEqual(steps[3]["map"],"SINNOH_LAKE_VERITY")
        self.assertEqual(steps[5]["map"],"SINNOH_PROFESSOR_ROWAN_LABORATORY")
        self.assertTrue(all(s["native_handler_verified"] is False for s in steps))

    def test_08_spawn_must_remain_unverified_in_bedroom(self):
        self.assertEqual(self.audited()["start_spawn"],{
            "symbol":"SINNOH_PLAYER_BEDROOM","native_map_id":None,
            "x":None,"y":None,"passability_verified":False,
            "native_spawn_verified":False,
        })

    def test_09_forged_map_id_or_sprite_fails(self):
        for mutator in (
            lambda x: x["events"]["maps"][0].update(map_id=442),
            lambda x: x["events"]["maps"][0].update(map_sha256="a"*64),
            lambda x: x["events"]["maps"][0]["events"][0].update(x=4),
            lambda x: x["events"]["maps"][5]["events"][1].update(
                sprite="Invented",verified_sprite=True),
            lambda x: x["events"]["start"].update(passability_verified=True),
        ):
            with self.subTest(mutator=repr(mutator)),self.assertRaises(ValueError):
                self.audited(mutator)

    def test_10_wrong_transfer_or_reciprocity_fails(self):
        for mutator in (
            lambda x: x["events"]["maps"][0]["events"][0].update(
                destination="SINNOH_ROUTE_201"),
            lambda x: x["events"]["maps"][1]["events"][1].update(
                arrival_x=0),
            lambda x: x["events"]["maps"][2]["events"][2].update(
                destination="SINNOH_PLAYER_HOUSE_1F"),
            lambda x: x["events"]["maps"][0]["events"].append(
                copy.deepcopy(x["events"]["maps"][0]["events"][0])),
        ):
            with self.subTest(mutator=repr(mutator)),self.assertRaises(ValueError):
                self.audited(mutator)

    def test_11_wrong_npc_handler_or_starter_species_fails(self):
        for mutator in (
            lambda x: x["events"]["maps"][1]["events"][0].update(
                handler="barry_intro"),
            lambda x: x["events"]["maps"][5]["events"][1].update(species="PIPLUP"),
            lambda x: x["events"].update(starter_selection="ROWAN_DIALOG"),
        ):
            with self.subTest(mutator=repr(mutator)),self.assertRaises(ValueError):
                self.audited(mutator)

    def test_12_s13_story_drift_rejected(self):
        mutators=(
            lambda x:x["intro"]["steps"][1].update(needs=[]),
            lambda x:x["intro"]["steps"][2].update(map="SINNOH_TWINLEAF_TOWN"),
            lambda x:x["intro"]["steps"][0].update(event="SN_NPC_ROWAN_POKEDEX"),
            lambda x:x["intro"]["steps"][3].update(physical_balls=[]),
            lambda x:x["intro"]["steps"][4].update(native_callback_verified=True),
            lambda x:x["intro"]["steps"][1].update(native_map_id=442),
            lambda x:x["intro"].update(native_barry_pbs_compiled=True),
            lambda x:x["intro"].update(native_handlers_verified=1),
        )
        for f in mutators:
            with self.subTest(mutation=repr(f)),self.assertRaisesRegex(
                    ValueError,"SINNOH_G07_BLOCKED"):
                self.audited(f)

    def test_13_s14_starter_drift_rejected(self):
        mutators=(
            lambda x:x["starters"]["balls"][0].update(
                rival_pbs_version=2),
            lambda x:x["starters"]["balls"][1].update(
                event_key="SN_BALL_PIPLUP"),
            lambda x:x["starters"]["balls"][2].update(
                event_compiled=True),
            lambda x:x["starters"]["balls"][0].update(
                native_event_id=3),
            lambda x:x["starters"]["balls"][0].update(
                verified_position=True),
            lambda x:x["starters"].update(native_verified_starter_balls=3),
            lambda x:x["starters"].update(starter_selection_playable=True),
            lambda x:x["starters"].update(verified_native_sources={"TURTWIG":442}),
        )
        for f in mutators:
            with self.subTest(mutation=repr(f)),self.assertRaisesRegex(
                    ValueError,"SINNOH_G07_BLOCKED"):
                self.audited(f)

    def test_14_b07_fake_terrain_or_donor_events_rejected(self):
        mutators=(
            lambda x:x["b07"]["candidate_terrain_destinations"].remove(442),
            lambda x:x["b07"]["excluded_empty_destinations"].append(442),
            lambda x:x["b07"].update(imports_donor_events=True),
            lambda x:x["b07"].update(imports_donor_scripts=True),
            lambda x:x["b07"].update(rights_per_asset_verified=True),
            lambda x:x["b07"].update(preserves_saves=False),
        )
        for f in mutators:
            with self.subTest(mutation=repr(f)),self.assertRaisesRegex(
                    ValueError,"SINNOH_G07_BLOCKED"):
                self.audited(f)

    def test_15_b08_b09_forged_gate_or_ids_rejected(self):
        mutators=(
            lambda x:x["b08"]["expected_staged_terrain_ids"].append(496),
            lambda x:x["b08"].update(can_install=True),
            lambda x:x["b08"].update(has_live_stage_evidence=True),
            lambda x:x["b09"].update(expected_qa_clone_map_count=703),
            lambda x:x["b09"]["candidate_installed_sinnoh_ids"].pop(),
            lambda x:x["b09"].update(runtime_save_isolation_verified=True),
            lambda x:x["b09"].update(third_party_asset_rights_verified=True),
            lambda x:x["b09"].update(phase_b_approved=1),
            lambda x:x["b09"].update(game_exe_tested=True),
        )
        for f in mutators:
            with self.subTest(mutation=repr(f)),self.assertRaisesRegex(
                    ValueError,"SINNOH_G07_BLOCKED"):
                self.audited(f)

    def test_16_missing_or_extra_map_fails_closed(self):
        for mutate in (
            lambda x:x["events"]["maps"].pop(),
            lambda x:x["events"]["maps"].append(
                copy.deepcopy(x["events"]["maps"][0])),
            lambda x:x["events"]["maps"].reverse(),
        ):
            with self.subTest(mutation=repr(mutate)),self.assertRaises(ValueError):
                self.audited(mutate)

    def test_17_public_output_contains_no_private_paths_or_runtime_assets(self):
        report=json.dumps(self.audited(),ensure_ascii=False)
        for forbidden in ("C:\\Users\\","AppData","Save01.rxdata",
                          "private-baseline.json","Game.exe.exe",
                          '"native_map_id": 442', '"map_sha256": "'):
            self.assertNotIn(forbidden,report)
        self.assertNotIn('"playable": true',report.lower())

    def test_18_cli_emits_only_metadata_json(self):
        process=subprocess.run(
            [sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_g07_twinleaf_bindings.py")],
            cwd=ROOT,capture_output=True,text=True,check=False
        )
        self.assertEqual(process.returncode,0,process.stderr)
        body=json.loads(process.stdout)
        self.assertEqual(body["stage"],"G07")
        self.assertEqual(body["counts"]["physically_bound_maps"],0)
        self.assertFalse(body["game_exe_tested"])

    def test_19_untrusted_cli_input_is_blocked(self):
        process=subprocess.run(
            [sys.executable,str(ROOT/"scripts/regions/audit_sinnoh_g07_twinleaf_bindings.py"),
             "--source","C:\\Private\\Save01.rxdata"],
            cwd=ROOT,capture_output=True,text=True,check=False
        )
        self.assertEqual(process.returncode,2)
        self.assertIn("SINNOH_G07_BLOCKED",process.stderr)
        self.assertNotIn("C:\\Private",process.stderr)

    def test_20_report_does_not_reinterpret_terrain_as_events(self):
        report=self.audited()
        self.assertFalse(report["terrain_stage"]["donor_events_present_in_private_geometry"])
        self.assertEqual(report["counts"]["native_transfers_verified"],0)
        for m in report["maps"]:
            for event in m["planned_events"]:
                self.assertFalse(event["physical_binding_verified"])
                self.assertIsNone(event["native_event_id"])
                if event["kind"]=="warp":
                    self.assertFalse(event["native_transfer_verified"])
                    self.assertIsNone(event["arrival_position"])


if __name__ == "__main__":
    unittest.main()
