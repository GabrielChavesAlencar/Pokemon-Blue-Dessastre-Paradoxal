"""CH15: 13 Sinnoh historical/strongest/PBS contracts with negative tests.

No Game.exe, ROM, source assets, native PBS, site edits or actual encounters.
"""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_sinnoh_teams_ch15 import (
    CATALOG, WALKTHROUGH, REVIEW, REGIONS, STRONGEST, STORY_TRAINERS,
    CAMPAIGN, STORY, audit, read_json, read_text, inspect_pbs_candidates,
    parse_document,
)


class SinnohTeamsCH15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = read_json(CATALOG)
        cls.doc = read_text(WALKTHROUGH)
        cls.review = read_json(REVIEW)
        cls.regions = read_json(REGIONS)
        cls.strongest = read_json(STRONGEST)
        cls.other_trainers = read_json(STORY_TRAINERS)
        cls.campaign = read_text(CAMPAIGN)
        cls.story = read_text(STORY)

    def check(self, catalog=None, doc=None, review=None, regions=None,
              strongest=None, other_trainers=None, campaign=None, story=None):
        return audit(
            copy.deepcopy(self.catalog if catalog is None else catalog),
            self.doc if doc is None else doc,
            copy.deepcopy(self.review if review is None else review),
            copy.deepcopy(self.regions if regions is None else regions),
            copy.deepcopy(self.strongest if strongest is None else strongest),
            copy.deepcopy(self.other_trainers if other_trainers is None
                          else other_trainers),
            self.campaign if campaign is None else campaign,
            self.story if story is None else story,
        )

    def rejects(self, reason, **changes):
        with self.assertRaisesRegex(ValueError, reason):
            self.check(**changes)

    def edited(self, index=0):
        return copy.deepcopy(self.catalog)

    def test_all_13_historical_trainers_and_5_rematches_are_reference_only(self):
        result = self.check()
        self.assertEqual((result["historical_gym_leaders"],
                          result["historical_elite"],
                          result["historical_champions"]), (8, 4, 1))
        self.assertEqual(result["platinum_historical_rematches"], 5)
        self.assertEqual(result["native_pbs_teams_compiled_and_event_bound"], 0)
        self.assertEqual(result["blue_full_power_variants_native_verified"], 0)
        self.assertFalse(result["publish_fixed_historical_levels"])
        self.assertFalse(result["gameplay_verified"])

    def test_cli_exposes_only_historical_not_runtime_levels(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/regions/audit_sinnoh_teams_ch15.py")],
            check=False, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data["historical_gym_leaders"], 8)
        self.assertFalse(data["can_install"])
        self.assertNotIn("battle_level", data)

    def test_fantina_is_third_relic_not_ch11_hm_listing_order(self):
        roster = self.catalog["trainers"]
        self.assertEqual([t["name"] for t in roster[:8]],
                         ["Roark", "Gardenia", "Fantina", "Maylene",
                          "Crasher Wake", "Byron", "Candice", "Volkner"])
        self.assertEqual(roster[2]["badge"], "RELIC")
        self.assertEqual(roster[3]["badge"], "COBBLE")
        self.check()

    def test_elite_mrmime_and_cynthia_six_members_preserved(self):
        roster = self.catalog["trainers"]
        self.assertEqual(roster[11]["first_battle"]["species"][0], "MRMIME")
        self.assertEqual(roster[12]["first_battle"]["species"][-1], "GARCHOMP")
        self.assertEqual(len(roster[12]["first_battle"]["historical_levels"]), 6)
        self.assertEqual(len(roster[12]["historical_rematch"]["species"]), 6)
        self.check()

    def test_missing_extra_or_misordered_roster_is_rejected(self):
        c = self.edited()
        c["trainers"].pop()
        self.rejects("oito líderes", catalog=c)
        c = self.edited()
        c["trainers"][2], c["trainers"][3] = c["trainers"][3], c["trainers"][2]
        self.rejects("Identidade, ordem", catalog=c)
        c = self.edited()
        c["trainers"].append(copy.deepcopy(c["trainers"][0]))
        self.rejects("oito líderes", catalog=c)

    def test_missing_extra_top_or_trainer_fields_block(self):
        for field in ("trainers", "sources", "ui_policy"):
            with self.subTest(field=field):
                c = self.edited()
                c.pop(field)
                self.rejects("Campos de catálogo", catalog=c)
        c = self.edited()
        c["trainers"][0]["map_id"] = 500
        self.rejects("Campos de treinador", catalog=c)
        c = self.edited()
        c["trainers"][0].pop("native_pbs")
        self.rejects("Campos de treinador", catalog=c)

    def test_platinum_team_species_or_historical_levels_cannot_drift(self):
        c = self.edited()
        c["trainers"][0]["first_battle"]["species"][0] = "RATTATA"
        self.rejects("Primeiro time", catalog=c)
        c = self.edited()
        c["trainers"][0]["first_battle"]["historical_levels"][0] = 99
        self.rejects("Primeiro time", catalog=c)
        c = self.edited()
        c["trainers"][9]["first_battle"]["species"].pop()
        self.rejects("Primeiro time", catalog=c)

    def test_gym_strongest_must_not_be_fabricated_from_kanto(self):
        c = self.edited()
        c["trainers"][0]["historical_rematch"] = copy.deepcopy(
            c["trainers"][8]["historical_rematch"])
        self.rejects("Revanche", catalog=c)
        c = self.edited()
        c["trainers"][0]["blue_strongest"]["species"] = ["GOLEM", "ONIX"]
        self.rejects("Full Power", catalog=c)
        c = self.edited()
        c["trainers"][5]["blue_strongest"]["trainer_version"] = 2
        self.rejects("Full Power", catalog=c)

    def test_platinum_elite_rematch_does_not_prove_blue_full_power(self):
        c = self.edited()
        c["trainers"][12]["historical_rematch"]["source"] = "BLUE_FULL_POWER"
        self.rejects("Revanche", catalog=c)
        c = self.edited()
        c["trainers"][12]["historical_rematch"]["verified_in_blue_pbs"] = True
        self.rejects("Revanche", catalog=c)
        c = self.edited()
        c["trainers"][12]["blue_strongest"]["game_exe_verified"] = True
        self.rejects("Full Power", catalog=c)

    def test_fake_native_pbs_or_version_claim_rejected(self):
        for key, fake in (
            ("compiled", True), ("event_bound", True),
            ("game_exe_verified", True), ("trainer_type", "BLUE_SINNOH_LEADER"),
            ("trainer_name", "Roark"), ("trainer_version", 0),
            ("source_sha256", "0"*64), ("source_file", "game/PBS/trainers.txt"),
            ("team", ["GEODUDE"]), ("status", "NATIVE_INSTALLED"),
        ):
            with self.subTest(key=key):
                c = self.edited()
                c["trainers"][0]["native_pbs"][key] = fake
                self.rejects("PBS nativa", catalog=c)

    def test_gameplay_and_pbs_install_flags_always_fail_closed(self):
        for key in (
            "native_source_available_in_repository",
            "native_pbs_compilation_verified",
            "native_event_battle_bindings_verified",
            "gameplay_verified", "can_install", "may_write_pbs",
        ):
            with self.subTest(key=key):
                c = self.edited()
                c[key] = True
                self.rejects("verificação nativa", catalog=c)

    def test_fixed_level_ui_or_fabricated_runtime_cap_is_rejected(self):
        for key in (
            "publish_historical_fixed_levels",
            "publish_rematch_as_blue_strongest",
            "publish_unverified_blue_native_as_installed",
        ):
            with self.subTest(key=key):
                c = self.edited()
                c["ui_policy"][key] = True
                self.rejects("nível", catalog=c)
        c = self.edited()
        c["dynamic_balance"]["normal_percent"] = 100
        self.rejects("nível", catalog=c)
        c = self.edited()
        c["dynamic_balance"]["reference_level"] = "regional_level_cap"
        self.rejects("nível", catalog=c)

    def test_untrusted_kanto_and_johto_strongest_not_a_sinnoh_proof(self):
        reference = copy.deepcopy(self.strongest)
        reference["teams"][0]["region"] = "SINNOH"
        self.rejects("Kanto/Johto", strongest=reference)
        reference = copy.deepcopy(self.strongest)
        reference["source"]["path"] = "docs/SINNOH.md"
        self.rejects("Kanto/Johto", strongest=reference)

    def test_decades_masters_cannot_be_rebranded_sinnoh(self):
        other = copy.deepcopy(self.other_trainers)
        other["masters"][0]["name"] = "Roark"
        self.rejects("Decades", other_trainers=other)
        other = copy.deepcopy(self.other_trainers)
        other["source"] = "local-game-pbs"
        self.rejects("Decades", other_trainers=other)

    def test_source_document_or_identity_drift_rejected(self):
        doc = self.doc.replace(
            "Geodude 12, Onix 12, Cranidos 14",
            "Geodude 12, Onix 12, Arceus 14")
        self.rejects("Primeiro time", doc=doc)
        doc = self.doc.replace(
            "Spiritomb 74, Roserade 74, Milotic 74",
            "Spiritomb 76, Roserade 74, Milotic 74")
        self.rejects("Revanche", doc=doc)
        review = copy.deepcopy(self.review)
        review["regions"]["SINNOH"]["leaders"][0] = "Brock"
        self.rejects("Identidades", review=review)

    def test_native_badge_catalog_drift_rejected(self):
        regions = copy.deepcopy(self.regions)
        regions["regions"]["SINNOH"]["milestones"][0] = "BOULDER"
        self.rejects("Insígnias", regions=regions)
        regions = copy.deepcopy(self.regions)
        regions["regions"]["SINNOH"]["status"] = "playable"
        self.rejects("Insígnias", regions=regions)

    def test_campaign_scaling_and_boss_copy_guards_cannot_be_removed(self):
        code = self.campaign.replace("master? ? 90 : 70", "master? ? 100 : 100")
        self.rejects("Campaign", campaign=code)
        code = self.campaign.replace("!BlueCampaign.boss?(trainer)", "true")
        self.rejects("Campaign", campaign=code)
        code = self.campaign.replace(
            "pkmn=Marshal.load(Marshal.dump(original));pkmn.level=level",
            "pkmn=original;pkmn.level=level")
        self.rejects("Campaign", campaign=code)

    def test_regional_boss_species_and_bst_exemption_preserved(self):
        code = self.story.replace("BlueStory.regional_first_boss?(args[4])",
                                  "false")
        self.rejects("Story", story=code)
        code = self.story.replace("LEADER|ELITE|ELITEFOUR|CHAMPION",
                                  "LEADER|ELITE")
        self.rejects("Story", story=code)

    def test_pbs_candidate_lookup_reports_untrusted_not_installed(self):
        raw = (
            "[BLUE_SINNOH_LEADER,Roark,0]\nPokemon = GEODUDE,12\n"
            "Pokemon = CRANIDOS,14\n"
            "[BLUE_SINNOH_CHAMPION,Cynthia,1]\n"
            "Pokemon = SPIRITOMB,74\nPokemon = GARCHOMP,78\n"
            "[BLUE_KANTO_LEADER,Brock,0]\nPokemon = ONIX,11\n"
        )
        report = inspect_pbs_candidates(raw, self.catalog)
        self.assertEqual(report["pbs_candidate_count"], 2)
        self.assertEqual(report["candidates"][0]["trainer_name"], "Cynthia")
        self.assertEqual(report["candidates"][0]["trainer_version"], 1)
        self.assertEqual(report["candidates"][1]["trainer_name"], "Roark")
        self.assertFalse(report["native_source_verified"])
        self.assertEqual(report["native_pbs_teams_compiled_and_event_bound"], 0)
        self.assertFalse(report["gameplay_verified"])

    def test_pbs_candidates_reject_duplicate_versions_and_empty_team(self):
        raw = ("[LEADER,Roark,1]\nPokemon=GEODUDE,12\n"
               "[LEADER,Roark,1]\nPokemon=ONIX,12\n")
        with self.assertRaisesRegex(ValueError, "repetida"):
            inspect_pbs_candidates(raw, self.catalog)
        raw = "[CHAMPION,Cynthia,0]\n"
        with self.assertRaisesRegex(ValueError, "vazia"):
            inspect_pbs_candidates(raw, self.catalog)

    def test_pbs_candidates_reject_more_than_six_and_malformed_target(self):
        raw = ("[LEADER,Roark,1]\n" + "Pokemon = GEODUDE,12\n" * 7)
        with self.assertRaisesRegex(ValueError, "acima de seis"):
            inspect_pbs_candidates(raw, self.catalog)
        raw = "[CHAMPION,Cynthia,0]\nPokemon = ARCEUS,no_level\n"
        with self.assertRaisesRegex(ValueError, "inválida"):
            inspect_pbs_candidates(raw, self.catalog)
        raw = "[BLUE_SINNOH_LEADER,Roark,broken]\nPokemon = ONIX,12\n"
        with self.assertRaisesRegex(ValueError, "Cabeçalho"):
            inspect_pbs_candidates(raw, self.catalog)

    def test_optional_pbs_cli_is_read_only_and_never_marks_installed(self):
        raw = "[LEADER,Roark,0]\nPokemon = GEODUDE,12\n"
        with tempfile.TemporaryDirectory(prefix="sinnoh-ch15-") as tmp:
            source = Path(tmp) / "trainers.txt"
            source.write_text(raw, encoding="utf-8")
            original = hashlib.sha256(source.read_bytes()).hexdigest()
            cmd = [sys.executable,
                   str(ROOT / "scripts/regions/audit_sinnoh_teams_ch15.py"),
                   "--pbs", str(source)]
            cp = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            report = json.loads(cp.stdout)
            self.assertEqual(report["pbs_candidates"]["pbs_candidate_count"], 1)
            self.assertEqual(report["pbs_candidate_source_sha256"],
                             hashlib.sha256(raw.encode()).hexdigest())
            self.assertFalse(report["native_pbs_compilation_verified"])
            self.assertEqual(report["native_pbs_teams_compiled_and_event_bound"], 0)
            self.assertEqual(original,
                             hashlib.sha256(source.read_bytes()).hexdigest())

    def test_missing_source_is_fail_closed(self):
        with tempfile.TemporaryDirectory(prefix="sinnoh-ch15-") as tmp:
            cmd = [sys.executable,
                   str(ROOT / "scripts/regions/audit_sinnoh_teams_ch15.py"),
                   "--pbs", str(Path(tmp) / "missing-pbs.txt")]
            cp = subprocess.run(cmd, capture_output=True, text=True)
            self.assertEqual(cp.returncode, 2)
            self.assertIn("SINNOH_CH15_BLOQUEADO", cp.stderr)


if __name__ == "__main__":
    unittest.main()
