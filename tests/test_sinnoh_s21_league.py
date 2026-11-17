"""S21 negative contracts: Elite, Cynthia and Hall must not fake gameplay."""
from __future__ import annotations
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_s21_league import (
    CONTRACT, STORY, COVERAGE, TEAMS, BADGES, RUBY, STORY_RUBY,
    WALKTHROUGH, FIXTURE, IDS, OUTCOMES, EIGHT, audit,
)


class S21LeagueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = json.loads(CONTRACT.read_text("utf-8"))
        cls.s = json.loads(STORY.read_text("utf-8"))
        cls.cov = json.loads(COVERAGE.read_text("utf-8"))
        cls.teams = json.loads(TEAMS.read_text("utf-8"))
        cls.badges = json.loads(BADGES.read_text("utf-8"))
        cls.ruby = RUBY.read_text("utf-8")
        cls.story_ruby = STORY_RUBY.read_text("utf-8")
        cls.walkthrough = WALKTHROUGH.read_text("utf-8")
        cls.fixture = FIXTURE.read_text("utf-8")

    def check(self, **mods):
        values = {
            "contract": self.c, "story": self.s, "coverage": self.cov,
            "teams": self.teams, "badges": self.badges,
            "ruby": self.ruby, "story_ruby": self.story_ruby,
            "walkthrough": self.walkthrough, "fixture": self.fixture,
        }
        values.update(mods)
        values = {k: copy.deepcopy(v) for k, v in values.items()}
        return audit(**values)

    def test_01_eight_ordered_gates_and_synthetic_scope_only(self):
        r = self.check()
        self.assertEqual(r["status"], "LEAGUE_EIGHT_GATES_AUDITED_NATIVE_BATTLES_PENDING")
        self.assertEqual(r["checkpoints"], 8)
        self.assertEqual(r["required_local_badges"], 8)
        self.assertEqual(r["historical_teams"], 13)
        self.assertEqual(r["elite_and_champion_reference_teams"], 5)
        self.assertEqual([x["id"] for x in self.c["steps"]], list(IDS))
        self.assertEqual([x["outcome"] for x in self.c["steps"]], list(OUTCOMES))
        self.assertEqual(r["native_trainers_installed"], 0)
        self.assertEqual(r["native_map_ids_verified"], 0)
        self.assertFalse(r["native_hall_of_fame_verified"])
        self.assertFalse(r["game_exe_joiplay_tested"])
        self.assertFalse(r["gameplay_certified"])

    def test_02_game_exe_joiplay_hof_native_claims_rejected(self):
        for key in ("game_exe_executed", "joiplay_executed",
                    "native_league_installed", "native_hall_of_fame_verified",
                    "gameplay_verified", "can_install"):
            with self.subTest(key=key):
                doc = copy.deepcopy(self.c)
                doc[key] = True
                with self.assertRaisesRegex(ValueError, "alegacao falsa"):
                    self.check(contract=doc)

    def test_03_fake_mapids_trainers_pbs_and_hall_handlers_rejected(self):
        for key, forged in (
            ("verified_native_sources", ["trusted?"]),
            ("installed_map_ids", [800]),
            ("installed_native_trainers", ["CYNTHIA"]),
            ("compiled_native_pbs", ["PBS/trainers.txt"]),
            ("native_hall_of_fame_callbacks", ["fake"]),
        ):
            with self.subTest(key=key):
                doc = copy.deepcopy(self.c)
                doc[key] = forged
                with self.assertRaisesRegex(ValueError, "inventados"):
                    self.check(contract=doc)

    def test_04_gate_cannot_claim_native_battles_or_reward_or_teleport(self):
        for key, value in (
            ("physical_map_id", 802), ("native_handler_installed", True),
            ("native_handler_verified", True),
            ("native_trainer_pbs_compiled", True),
            ("native_battle_result_verified", True),
            ("native_engine_hall_of_fame_verified", True),
            ("grants_badge", True), ("grants_item", True),
            ("grants_map", True),
            ("teleport_destination", [801, 8, 4]),
            ("reference_only", False),
        ):
            with self.subTest(key=key):
                doc = copy.deepcopy(self.c)
                doc["steps"][6][key] = value
                with self.assertRaisesRegex(ValueError, "etapa da Liga"):
                    self.check(contract=doc)

    def test_05_skipping_or_reordering_opponents_is_rejected(self):
        for kind in ("skip", "swap", "duplicate"):
            doc = copy.deepcopy(self.c)
            if kind == "skip":
                doc["steps"].pop(2)
            elif kind == "swap":
                doc["steps"][3], doc["steps"][4] = (
                    doc["steps"][4], doc["steps"][3])
            else:
                doc["steps"][5] = doc["steps"][4]
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                self.check(contract=doc)

    def test_06_barry_eight_local_badges_not_fewer_or_cross_region(self):
        for keys in ([], ["BEACON"], list(EIGHT)[:-1],
                     ["KANTO"] + list(EIGHT)[1:]):
            doc = copy.deepcopy(self.c)
            doc["steps"][1]["requires_local_badges"] = keys
            with self.subTest(keys=keys), self.assertRaises(ValueError):
                self.check(contract=doc)
        doc = copy.deepcopy(self.c)
        doc["steps"][0]["requires_local_badges"] = []
        with self.assertRaises(ValueError):
            self.check(contract=doc)

    def test_07_cynthia_win_cannot_substitute_hall_confirmation(self):
        for index, outcome in (
            (1, "talked"), (2, "approached"), (3, "battle_lost"),
            (4, "scene_completed"), (5, "badge_awarded"),
            (6, "hall_of_fame_confirmed"),
            (7, "battle_won"), (7, "scene_completed"),
        ):
            doc = copy.deepcopy(self.c)
            doc["steps"][index]["outcome"] = outcome
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, "etapa da Liga"):
                self.check(contract=doc)

    def test_08_regional_source_ch14_must_remain_separate_and_uninstalled(self):
        for field in ("hall_of_fame_requires_separate_engine_confirmation",
                      "native_hall_of_fame_verified", "native_events_installed",
                      "can_install", "gameplay_verified"):
            doc = copy.deepcopy(self.s)
            doc[field] = not doc[field]
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "CH14"):
                self.check(story=doc)
        doc = copy.deepcopy(self.s)
        doc["steps"][21]["proof_kind"] = "TRUSTED_NATIVE_EVENT_CONFIRMED"
        with self.assertRaisesRegex(ValueError, "CH14"):
            self.check(story=doc)
        doc = copy.deepcopy(self.s)
        doc["steps"][15]["requires_local_badges"] = ["BEACON"]
        with self.assertRaisesRegex(ValueError, "CH14"):
            self.check(story=doc)

    def test_09_historical_ch15_teams_must_never_be_compiled(self):
        for field in ("native_source_available_in_repository",
                      "native_pbs_compilation_verified", "native_event_battle_bindings_verified",
                      "gameplay_verified", "can_install", "may_write_pbs"):
            doc = copy.deepcopy(self.teams)
            doc[field] = True
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "CH15"):
                self.check(teams=doc)
        doc = copy.deepcopy(self.teams)
        trainer = next(t for t in doc["trainers"] if t["id"] == "SINNOH_CYNTHIA")
        trainer["native_pbs"]["compiled"] = True
        with self.assertRaisesRegex(ValueError, "historico CH15"):
            self.check(teams=doc)
        doc = copy.deepcopy(self.teams)
        trainer = next(t for t in doc["trainers"] if t["id"] == "SINNOH_AARON")
        trainer["native_pbs"]["team"] = ["DRAPION"]
        with self.assertRaisesRegex(ValueError, "historico CH15"):
            self.check(teams=doc)

    def test_10_missing_or_fake_badge_event_is_not_eight_badges(self):
        doc = copy.deepcopy(self.badges)
        doc["rules"].pop()
        with self.assertRaisesRegex(ValueError, "8 insignias"):
            self.check(badges=doc)
        doc = copy.deepcopy(self.badges)
        doc["rules"][0]["verified_gym_event"] = True
        with self.assertRaisesRegex(ValueError, "8 insignias"):
            self.check(badges=doc)
        doc = copy.deepcopy(self.badges)
        doc["native_gym_events_verified"] = True
        with self.assertRaisesRegex(ValueError, "CH11"):
            self.check(badges=doc)

    def test_11_ch01_coverage_elite_and_hall_must_stay_unverified(self):
        doc = copy.deepcopy(self.cov)
        phase = next(p for p in doc["phases"] if p["phase"] == 9)
        row = next(e for e in phase["events"] if e["key"] == "P09_CYNTHIA_BATTLE")
        row["verified"] = True
        with self.assertRaisesRegex(ValueError, "cobertura"):
            self.check(coverage=doc)
        doc = copy.deepcopy(self.cov)
        phase = next(p for p in doc["phases"] if p["phase"] == 9)
        phase["events"] = [e for e in phase["events"] if e["key"] != "P09_HALL_OF_FAME"]
        with self.assertRaisesRegex(ValueError, "cobertura"):
            self.check(coverage=doc)

    def test_12_no_native_callback_registry_can_be_prefilled(self):
        forged = self.ruby.replace("VERIFIED_NATIVE_SOURCES = {}.freeze",
                                   "VERIFIED_NATIVE_SOURCES = {1 => 800}.freeze")
        with self.assertRaisesRegex(ValueError, "Ruby"):
            self.check(ruby=forged)
        forged = self.ruby.replace("private_class_method :record_with_sources", "")
        with self.assertRaisesRegex(ValueError, "Ruby"):
            self.check(ruby=forged)

    def test_13_ch14_hall_guards_and_league_ledger_must_be_preserved(self):
        for token in (
            'SAVE_KEY = "sinnoh_ch14"',
            "events == STEPS.first(events.length)",
            "hall_of_fame_verified.equal?(true)",
            'BlueRegions.complete_league(state, "SINNOH")',
        ):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "CH14"):
                self.check(story_ruby=self.story_ruby.replace(token, ""))

    def test_14_ruby_order_cannot_insert_a_fake_extra_elite(self):
        altered = self.ruby.replace("P09_LUCIAN_BATTLE", "P09_CYRUS_BATTLE", 1)
        with self.assertRaisesRegex(ValueError, "ordem"):
            self.check(ruby=altered)

    def test_15_warpless_championship_and_s42_s43_references_required(self):
        doc = copy.deepcopy(self.c)
        doc["ch14_save_key"] = "fake_new_league_save"
        with self.assertRaisesRegex(ValueError, "politica S21"):
            self.check(contract=doc)
        altered = self.walkthrough.replace("### S43 ", "### REMOVED ")
        with self.assertRaisesRegex(ValueError, "S42/S43"):
            self.check(walkthrough=altered)

    def test_16_no_dummy_fixture_or_hidden_native_signoff(self):
        for token in (
            "SINNOH_S21_EIGHT_BADGES_ELITE_CYNTHIA_HOF_SEPARATE_OFFLINE_OK",
            "league.record_from_native(state, id, outcome: outcome, source: source)",
            "send(:record_with_sources,",
            "post_cynthia_destination",
        ):
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "runner Ruby"):
                self.check(fixture=self.fixture.replace(token, ""))
        doc = copy.deepcopy(self.c)
        doc["unexpected_playability_certificate"] = True
        with self.assertRaisesRegex(ValueError, "campos S21"):
            self.check(contract=doc)


if __name__ == "__main__":
    unittest.main()
