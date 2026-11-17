"""S20 negative tests: no fake Spear Pillar maps, Cyrus outcomes or Giratina."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_s20_distortion import (
    CONTRACT, STORY, COVERAGE, RUBY, STORY_RUBY, WALKTHROUGH, FIXTURE,
    IDS, OUTCOMES, RESTRICTIONS, audit,
)


class SinnohS20DistortionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text("utf-8"))
        cls.story = json.loads(STORY.read_text("utf-8"))
        cls.coverage = json.loads(COVERAGE.read_text("utf-8"))
        cls.ruby = RUBY.read_text("utf-8")
        cls.story_ruby = STORY_RUBY.read_text("utf-8")
        cls.walkthrough = WALKTHROUGH.read_text("utf-8")
        cls.fixture = FIXTURE.read_text("utf-8")

    def check(self, contract=None, story=None, coverage=None, ruby=None,
              story_ruby=None, walkthrough=None, fixture=None):
        return audit(
            copy.deepcopy(self.contract if contract is None else contract),
            copy.deepcopy(self.story if story is None else story),
            copy.deepcopy(self.coverage if coverage is None else coverage),
            self.ruby if ruby is None else ruby,
            self.story_ruby if story_ruby is None else story_ruby,
            self.walkthrough if walkthrough is None else walkthrough,
            self.fixture if fixture is None else fixture,
        )

    def test_01_nine_phase_8_steps_keep_all_native_approvals_false(self):
        result = self.check()
        self.assertEqual(result["checkpoint_count"], 9)
        self.assertEqual(result["phase"], 8)
        self.assertEqual(result["native_map_ids"], 0)
        self.assertEqual(result["native_callbacks"], 0)
        self.assertEqual(result["native_battles_verified"], 0)
        self.assertEqual(result["native_teleports_verified"], 0)
        self.assertFalse(result["native_giratina_encounter_verified"])
        self.assertFalse(result["game_exe_and_joiplay_tested"])
        self.assertFalse(result["gameplay_certified"])
        self.assertEqual([s["id"] for s in self.contract["steps"]], list(IDS))
        self.assertEqual([s["outcome"] for s in self.contract["steps"]],
                         list(OUTCOMES))

    def test_02_forged_native_or_approval_flags_rejected(self):
        for field in ("game_exe_executed", "joiplay_executed",
                      "events_native_installed", "gameplay_verified",
                      "can_install"):
            with self.subTest(field=field):
                altered = copy.deepcopy(self.contract)
                altered[field] = True
                with self.assertRaisesRegex(ValueError, "prova nativa"):
                    self.check(contract=altered)

    def test_03_no_map_ids_pbs_teleport_or_callbacks_fabricated(self):
        for field, data in (
            ("native_verified_source_registry", ["real?"]),
            ("installed_map_ids", [801]),
            ("installed_native_pbs", ["trainers.txt"]),
            ("native_teleport_points", [[800, 10, 10]]),
        ):
            with self.subTest(field=field):
                altered = copy.deepcopy(self.contract)
                altered[field] = data
                with self.assertRaisesRegex(ValueError, "inventados"):
                    self.check(contract=altered)

    def test_04_every_checkpoint_cannot_claim_rewards_and_maps(self):
        for field, data in (
            ("native_map_id", 811), ("native_callback_installed", True),
            ("native_callback_verified", True), ("native_battle_verified", True),
            ("native_puzzle_verified", True),
            ("native_giratina_resolution_verified", True),
            ("native_return_verified", True), ("grants_badge", True),
            ("grants_item", True), ("grants_species", True),
            ("teleport_destination", [801, 3, 9]), ("reference_only", False),
        ):
            with self.subTest(field=field):
                altered = copy.deepcopy(self.contract)
                altered["steps"][6][field] = data
                with self.assertRaisesRegex(ValueError, "forjado"):
                    self.check(contract=altered)

    def test_05_missing_reordered_and_duplicate_cyrus_steps_rejected(self):
        for mutation in ("removed", "swapped", "duplicate"):
            altered = copy.deepcopy(self.contract)
            if mutation == "removed":
                altered["steps"].pop(1)
            elif mutation == "swapped":
                altered["steps"][0], altered["steps"][1] = (
                    altered["steps"][1], altered["steps"][0])
            else:
                altered["steps"][4] = altered["steps"][0]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.check(contract=altered)

    def test_06_wrong_battle_and_puzzle_results_must_fail(self):
        for index, outcome in (
            (0, "talked"), (1, "scene_completed"), (2, "lost"),
            (3, "approached"), (4, "battle_won"),
            (5, "scene_completed"), (6, "scene_completed"),
            (7, "captured"), (8, "encounter_resolved"),
        ):
            altered = copy.deepcopy(self.contract)
            altered["steps"][index]["outcome"] = outcome
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, "forjado"):
                self.check(contract=altered)

    def test_07_mine_and_icicle_are_both_required_for_first_cyrus(self):
        for badges in ([], ["MINE"], ["ICICLE"], ["FOREST"], ["MINE", "FOREST"]):
            altered = copy.deepcopy(self.contract)
            altered["steps"][0]["requires_local_badges"] = badges
            with self.subTest(badges=badges), self.assertRaisesRegex(ValueError, "forjado"):
                self.check(contract=altered)

    def test_08_no_giratina_grant_or_forced_capture(self):
        for key in ("giratina_resolution_is_not_forced_capture",
                    "no_giratina_grant", "requires_explicit_safe_return",
                    "requires_distortion_puzzles_solved"):
            altered = copy.deepcopy(self.contract)
            altered["restrictions"][key] = False
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "protecao S20"):
                self.check(contract=altered)
        self.assertEqual(self.contract["steps"][7]["outcome"], "encounter_resolved")
        self.assertFalse(self.contract["steps"][7]["grants_species"])

    def test_09_ch14_cannot_be_declared_installed_or_shifted(self):
        for key in ("native_events_installed", "can_install", "gameplay_verified"):
            altered = copy.deepcopy(self.story)
            altered[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "CH14"):
                self.check(story=altered)
        altered = copy.deepcopy(self.story)
        altered["steps"][11]["prerequisite_event"] = "P08_COMMANDER_MARS"
        with self.assertRaisesRegex(ValueError, "checkpoint S20"):
            self.check(story=altered)

    def test_10_coverage_phase_8_must_keep_events_unverified(self):
        altered = copy.deepcopy(self.coverage)
        phase = next(p for p in altered["phases"] if p["phase"] == 8)
        target = next(e for e in phase["events"] if e["key"] == IDS[0])
        target["verified"] = True
        with self.assertRaisesRegex(ValueError, "cobertura"):
            self.check(coverage=altered)
        altered = copy.deepcopy(self.coverage)
        phase = next(p for p in altered["phases"] if p["phase"] == 8)
        phase["events"] = [e for e in phase["events"] if e["key"] != IDS[0]]
        with self.assertRaisesRegex(ValueError, "fase 8"):
            self.check(coverage=altered)

    def test_11_ch14_s39_cyrus_final_reference_must_exist(self):
        broken = self.walkthrough.replace("### S39 ", "### UNKNOWN ")
        with self.assertRaisesRegex(ValueError, "S39"):
            self.check(walkthrough=broken)

    def test_12_native_callback_registry_must_stay_empty_and_private(self):
        broken = self.ruby.replace("VERIFIED_NATIVE_SOURCES = {}.freeze",
                                   "VERIFIED_NATIVE_SOURCES = {1 => 800}.freeze")
        with self.assertRaisesRegex(ValueError, "guardas"):
            self.check(ruby=broken)
        broken = self.ruby.replace("private_class_method :record_with_sources", "")
        with self.assertRaisesRegex(ValueError, "guardas"):
            self.check(ruby=broken)

    def test_13_source_order_and_CH14_save_protection_must_remain(self):
        broken = self.ruby.replace("P08_COMMANDER_SATURN", "P08_GIRATINA_ENCOUNTER", 1)
        with self.assertRaisesRegex(ValueError, "sequencia"):
            self.check(ruby=broken)
        broken = self.story_ruby.replace("events == STEPS.first(events.length)", "")
        with self.assertRaisesRegex(ValueError, "CH14"):
            self.check(story_ruby=broken)

    def test_14_runtime_fixture_must_verify_safe_return_native_block(self):
        for token in (
            "SINNOH_S20_DISTORTION_PUZZLES_GIRATINA_SAFE_RETURN_OFFLINE_OK",
            "record_from_native(", "send(:record_with_sources,",
            "P08_SAFE_RETURN_FROM_DISTORTION_WORLD",
        ):
            with self.subTest(token=token):
                with self.assertRaisesRegex(ValueError, "runtime S20"):
                    self.check(fixture=self.fixture.replace(token, ""))

    def test_15_only_existing_ch14_ledger_may_be_used(self):
        altered = copy.deepcopy(self.contract)
        altered["ch14_save_key"] = "sinnoh_s20_redundant"
        with self.assertRaisesRegex(ValueError, "protecao S20"):
            self.check(contract=altered)
        altered = copy.deepcopy(self.contract)
        altered["next_after_s20"] = "P09_HALL_OF_FAME"
        with self.assertRaisesRegex(ValueError, "protecao S20"):
            self.check(contract=altered)

    def test_16_missing_fields_and_extra_native_certificates_rejected(self):
        altered = copy.deepcopy(self.contract)
        altered["native_approved"] = True
        with self.assertRaisesRegex(ValueError, "campos desconhecidos"):
            self.check(contract=altered)
        altered = copy.deepcopy(self.contract)
        altered.pop("restrictions")
        with self.assertRaisesRegex(ValueError, "campos desconhecidos"):
            self.check(contract=altered)


if __name__ == "__main__":
    unittest.main()
