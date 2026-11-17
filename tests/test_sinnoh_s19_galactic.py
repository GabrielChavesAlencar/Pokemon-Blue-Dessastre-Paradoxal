"""S19 Galactic — reject fake maps, battles, progression and native proof."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_s19_galactic import (
    CONTRACT, STORY, COVERAGE, RUBY, STORY_RUBY, FIXTURE, audit, IDS,
)


class SinnohS19GalacticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contract = json.loads(CONTRACT.read_text("utf-8"))
        cls.story = json.loads(STORY.read_text("utf-8"))
        cls.coverage = json.loads(COVERAGE.read_text("utf-8"))
        cls.ruby = RUBY.read_text("utf-8")
        cls.story_ruby = STORY_RUBY.read_text("utf-8")
        cls.fixture = FIXTURE.read_text("utf-8")

    def check(self, *, contract=None, story=None, coverage=None,
              ruby=None, story_ruby=None, fixture=None):
        return audit(
            copy.deepcopy(self.contract if contract is None else contract),
            copy.deepcopy(self.story if story is None else story),
            copy.deepcopy(self.coverage if coverage is None else coverage),
            self.ruby if ruby is None else ruby,
            self.story_ruby if story_ruby is None else story_ruby,
            self.fixture if fixture is None else fixture,
        )

    def test_01_exact_five_checkpoints_are_planned_without_native_hooks(self):
        r = self.check()
        self.assertEqual(r["planned_steps"], 5)
        self.assertEqual(r["reference_phases"], [5, 6, 7])
        self.assertEqual([x["id"] for x in self.contract["steps"]], list(IDS))
        self.assertEqual(r["native_event_handlers_installed"], 0)
        self.assertEqual(r["physical_map_ids_verified"], 0)
        self.assertFalse(r["auto_rewards_or_map_travel"])
        self.assertFalse(r["game_exe_or_joiplay_tested"])
        self.assertFalse(r["gameplay_certified"])

    def test_02_fake_game_exe_joiplay_playable_or_install_flag_rejected(self):
        for key in ("native_runtime_verified", "game_exe_tested",
                    "joiplay_tested", "can_install", "gameplay_verified"):
            c = copy.deepcopy(self.contract)
            c[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "aprovação"):
                self.check(contract=c)

    def test_03_false_map_ids_source_installations_and_pbs_rejected(self):
        for name, inserted in (
            ("already_verified_native_sources", ["FAKE"]),
            ("physical_map_ids", [800]),
            ("spawned_trainers", ["MARS"]),
            ("native_pbs_files", ["PBS/trainers.txt"]),
        ):
            c = copy.deepcopy(self.contract)
            c[name] = inserted
            with self.subTest(key=name), self.assertRaisesRegex(ValueError, "inventados"):
                self.check(contract=c)

    def test_04_rewards_warps_and_badges_cannot_be_published_as_native(self):
        for key, fake in (
            ("map_id", 700), ("native_event_installed", True),
            ("native_event_verified", True), ("compiled_battle_verified", True),
            ("reward_items", ["MASTERBALL"]),
            ("reward_badges", ["FOREST"]),
            ("teleport_destination", [999, 5, 4]),
            ("reference_only", False),
        ):
            c = copy.deepcopy(self.contract)
            c["steps"][1][key] = fake
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.check(contract=c)

    def test_05_out_of_order_or_missing_checkpoint_rejected(self):
        for change in ("swap", "skip", "duplicate"):
            c = copy.deepcopy(self.contract)
            if change == "swap":
                c["steps"][0], c["steps"][1] = c["steps"][1], c["steps"][0]
            elif change == "skip":
                c["steps"].pop(1)
            else:
                c["steps"][1] = copy.deepcopy(c["steps"][0])
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.check(contract=c)

    def test_06_jupiter_requires_forest_but_mars_does_not(self):
        for index, badge in ((1, ["FOREST"]), (2, [])):
            c = copy.deepcopy(self.contract)
            c["steps"][index]["requires_local_badges"] = badge
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.check(contract=c)

    def test_07_battle_result_cannot_be_replaced_with_scene_or_talk(self):
        for index, result in ((1, "scene_completed"), (2, "talked"),
                              (3, "battle_won"), (4, "approached")):
            c = copy.deepcopy(self.contract)
            c["steps"][index]["outcome"] = result
            with self.subTest(index=index), self.assertRaises(ValueError):
                self.check(contract=c)

    def test_08_ch14_false_progress_must_not_approve_s19(self):
        for key in ("native_events_installed", "can_install", "gameplay_verified"):
            c = copy.deepcopy(self.story)
            c[key] = True
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "CH14"):
                self.check(story=c)
        c = copy.deepcopy(self.story)
        c["steps"][2]["requires_local_badges"] = []
        with self.assertRaisesRegex(ValueError, "CH14"):
            self.check(story=c)

    def test_09_coverage_event_must_exist_in_correct_phase_and_pending(self):
        c = copy.deepcopy(self.coverage)
        phase = next(p for p in c["phases"] if p["phase"] == 5)
        row = next(x for x in phase["events"] if x["key"] == IDS[0])
        row["verified"] = True
        with self.assertRaisesRegex(ValueError, "duplicado ou declarado"):
            self.check(coverage=c)
        c = copy.deepcopy(self.coverage)
        phase = next(p for p in c["phases"] if p["phase"] == 5)
        phase["events"] = [x for x in phase["events"] if x["key"] != IDS[0]]
        with self.assertRaisesRegex(ValueError, "diverge"):
            self.check(coverage=c)

    def test_10_ruby_native_source_registry_must_remain_empty(self):
        broken = self.ruby.replace(
            "VERIFIED_NATIVE_SOURCES = {}.freeze",
            'VERIFIED_NATIVE_SOURCES = {"P05_COMMANDER_MARS" => "unverified"}.freeze',
        )
        with self.assertRaisesRegex(ValueError, "guardas obrigatórias"):
            self.check(ruby=broken)

    def test_11_ruby_sequence_and_ch14_save_guard_must_not_change(self):
        broken = self.ruby.replace('"P05_COMMANDER_MARS",',
                                  '"P08_CYRUS",', 1)
        with self.assertRaisesRegex(ValueError, "sequência Galactic"):
            self.check(ruby=broken)
        story_broken = self.story_ruby.replace(
            'events == STEPS.first(events.length)', 'events.length <= 22')
        with self.assertRaisesRegex(ValueError, "CH14 save"):
            self.check(story_ruby=story_broken)

    def test_12_runtime_fixture_must_attempt_no_real_source_and_validated_synthetic(self):
        for token in (
            "galactic.record_from_native(state, event, outcome: kind, source: source)",
            "galactic.fixture_record(state, event, outcome: kind, source: source,",
            "SINNOH_S19_GALACTIC_FIVE_PHASES_BADGE_ORDER_SAVE_ISOLATION_OFFLINE_OK",
        ):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "teste Ruby"):
                self.check(fixture=self.fixture.replace(token, ""))


if __name__ == "__main__":
    unittest.main()
