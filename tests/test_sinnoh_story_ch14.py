"""CH14 Sinnoh: negatives for ordering, reward spoofing and fake post-game travel."""
from __future__ import annotations

import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_story_ch14 import (
    CONTRACT, COVERAGE, WALKTHROUGH, RUNTIME, REGIONS, TRAVEL,
    audit, read, IDS,
)


class SinnohStoryCH14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(read(CONTRACT))
        cls.coverage = json.loads(read(COVERAGE))
        cls.walkthrough = read(WALKTHROUGH)
        cls.runtime = read(RUNTIME)
        cls.regions = read(REGIONS)
        cls.travel = read(TRAVEL)

    def check(self, contract=None, coverage=None, walkthrough=None,
              runtime=None, regions=None, travel=None):
        return audit(
            copy.deepcopy(self.contract if contract is None else contract),
            copy.deepcopy(self.coverage if coverage is None else coverage),
            self.walkthrough if walkthrough is None else walkthrough,
            self.runtime if runtime is None else runtime,
            self.regions if regions is None else regions,
            self.travel if travel is None else travel,
        )

    def rejects(self, reason, **changes):
        with self.assertRaisesRegex(ValueError, reason):
            self.check(**changes)

    def test_positive_22_ordered_milestones(self):
        report = self.check()
        self.assertEqual(report["checkpoints"], 22)
        self.assertEqual(report["native_hooks_installed"], 0)
        self.assertFalse(report["gameplay_verified"])
        self.assertFalse(report["can_install"])

    def test_cli_reports_read_only(self):
        p = subprocess.run(
            [sys.executable, str(ROOT / "scripts/regions/audit_sinnoh_story_ch14.py")],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(json.loads(p.stdout)["planned_native_hooks"], 22)

    def test_missing_or_extra_fields_block(self):
        for field in ("source", "runtime", "steps", "can_install"):
            with self.subTest(field=field):
                c = copy.deepcopy(self.contract)
                c.pop(field)
                self.rejects("Campos", contract=c)
        c = copy.deepcopy(self.contract)
        c["map_id"] = 801
        self.rejects("Campos", contract=c)

    def test_milestone_missing_duplicate_or_wrong_order(self):
        c = copy.deepcopy(self.contract)
        c["steps"].pop()
        self.rejects("incompleta", contract=c)
        c = copy.deepcopy(self.contract)
        c["steps"][4]["id"] = c["steps"][3]["id"]
        self.rejects("fora de ordem", contract=c)
        c = copy.deepcopy(self.contract)
        c["steps"][16], c["steps"][17] = c["steps"][17], c["steps"][16]
        self.rejects("fora de ordem", contract=c)

    def test_cynthia_cannot_be_declared_hall_of_fame(self):
        c = copy.deepcopy(self.contract)
        c["steps"][20]["proof_kind"] = "ENGINE_HALL_OF_FAME_CONFIRMED"
        self.rejects("fora de ordem", contract=c)
        c = copy.deepcopy(self.contract)
        c["steps"][21]["proof_kind"] = "TRUSTED_NATIVE_EVENT_CONFIRMED"
        self.rejects("fora de ordem", contract=c)

    def test_cyrus_distortion_and_double_battle_cannot_swap(self):
        c = copy.deepcopy(self.contract)
        c["steps"][5]["id"] = "SINNOH_DISTORTION_CYRUS_FINAL"
        self.rejects("fora de ordem", contract=c)
        c = copy.deepcopy(self.contract)
        c["steps"][9]["id"] = "P08_DISTORTION_WORLD_PUZZLES"
        self.rejects("fora de ordem", contract=c)

    def test_invalid_badge_gate_or_phase_rejected(self):
        c = copy.deepcopy(self.contract)
        c["steps"][15]["requires_local_badges"].pop()
        self.rejects("fora de ordem", contract=c)
        c = copy.deepcopy(self.contract)
        c["steps"][14]["requires_local_badges"] = ["KANTO:EARTH"]
        self.rejects("fora de ordem", contract=c)
        c = copy.deepcopy(self.contract)
        c["steps"][5]["phase"] = 9
        self.rejects("fora de ordem", contract=c)

    def test_forged_native_approval_and_prizes_rejected(self):
        for k in ("can_install", "native_events_installed",
                  "gameplay_verified", "native_hall_of_fame_verified"):
            with self.subTest(flag=k):
                c = copy.deepcopy(self.contract)
                c[k] = True
                self.rejects("falsificadas", contract=c)
        for k in ("grants_item", "grants_badge", "grants_map",
                  "native_event_installed", "native_event_verified"):
            with self.subTest(step_flag=k):
                c = copy.deepcopy(self.contract)
                c["steps"][0][k] = True
                self.rejects("fora de ordem", contract=c)

    def test_no_map_ids_or_installation_in_steps(self):
        c = copy.deepcopy(self.contract)
        c["steps"][0]["destination_map_id"] = 500
        self.rejects("Campos do checkpoint", contract=c)
        c = copy.deepcopy(self.contract)
        c["steps"][1]["prerequisite_event"] = None
        self.rejects("fora de ordem", contract=c)

    def test_hoenn_unova_or_npc_forged_unlock(self):
        for value in (["HOENN"], ["HOENN", "UNOVA", "JOHTO"], []):
            with self.subTest(value=value):
                c = copy.deepcopy(self.contract)
                c["destinations_post_cynthia"] = value
                self.rejects("falsificadas", contract=c)
        c = copy.deepcopy(self.contract)
        c["travel_without_verified_npc_context"] = True
        self.rejects("falsificadas", contract=c)

    def test_unverified_coverage_events_block(self):
        coverage = copy.deepcopy(self.coverage)
        for phase in coverage["phases"]:
            for row in phase["events"]:
                if row["key"] == "P09_HALL_OF_FAME":
                    row["verified"] = True
        self.rejects("duplicado ou declarado nativo", coverage=coverage)
        coverage = copy.deepcopy(self.coverage)
        for phase in coverage["phases"]:
            if phase["phase"] == 9:
                phase["events"] = [
                    row for row in phase["events"]
                    if row["key"] != "P09_AARON_BATTLE"
                ]
        self.rejects("não existe", coverage=coverage)

    def test_chapter_references_must_exist(self):
        text = self.walkthrough.replace("### S39", "### X39")
        self.rejects("Referência narrativa", walkthrough=text)
        text = self.walkthrough.replace("### S42", "### X42")
        self.rejects("Referência narrativa", walkthrough=text)

    def test_runtime_step_list_cannot_skip_sinnoh_hall_of_fame(self):
        s = self.runtime.replace("P09_CYNTHIA_BATTLE P09_HALL_OF_FAME",
                                 "P09_CYNTHIA_BATTLE P09_FAKE_POSTGAME")
        self.rejects("sequência", runtime=s)
        s = self.runtime.replace("hall_of_fame_verified.equal?(true)",
                                 "true")
        self.rejects("Guarda Ruby", runtime=s)
        s = self.runtime.replace("BlueRegions.complete_league(state, \"SINNOH\")",
                                 "state[\"leagues\"] << \"SINNOH\"")
        self.rejects("Guarda Ruby", runtime=s)

    def test_unsafe_travel_without_actual_source_or_arrival_rejected(self):
        s = self.runtime.replace("BlueRegionTravel.destination(state, destination)",
                                 "[500, 1, 1, 2]")
        self.rejects("Guarda Ruby", runtime=s)
        s = self.runtime.replace("BlueRegionTravel.source_valid?(state)",
                                 "true")
        self.rejects("Guarda Ruby", runtime=s)
        s = self.runtime.replace("BlueRegionTravel.available?(state)",
                                 "true")
        self.rejects("Guarda Ruby", runtime=s)

    def test_missing_battle_coverage_reference_rejected(self):
        cover = copy.deepcopy(self.coverage)
        for phase in cover["phases"]:
            if phase["phase"] == 9:
                phase["events"] = [
                    row for row in phase["events"]
                    if row["key"] != "P09_CYNTHIA_BATTLE"
                ]
        self.rejects("não existe", coverage=cover)


if __name__ == "__main__":
    unittest.main()
