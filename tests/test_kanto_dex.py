"""KantoDex: 151 species, no renumbering National or clearing player data."""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
try:
    from kanto_dex import first_151, sections, install_pilot_kantodex
finally:
    sys.path.remove(str(ROOT / "scripts/regions"))


class TestKantoDex(unittest.TestCase):
    def test_starts_bulbasaur_and_has_all_original_151(self):
        data = first_151(ROOT)
        self.assertEqual(len(data), 151)
        self.assertEqual(data[:9], [
            "BULBASAUR", "IVYSAUR", "VENUSAUR",
            "CHARMANDER", "CHARMELEON", "CHARIZARD",
            "SQUIRTLE", "WARTORTLE", "BLASTOISE"])
        self.assertEqual(data[-2:], ["MEWTWO", "MEW"])
        self.assertIn("NIDORANfE", data)
        self.assertIn("NIDORANmA", data)
        self.assertEqual(len(set(data)), 151)

    def fixture(self, pbs_content=""):
        temp = tempfile.TemporaryDirectory()
        target = Path(temp.name) / "pilot"
        (target / "PBS").mkdir(parents=True)
        (target / "Data").mkdir(parents=True)
        pbs = target / "PBS/regional_dexes.txt"
        pbs.write_text(pbs_content, encoding="utf8")
        return temp, target, pbs

    def test_kantodex_is_added_as_new_native_section_and_national_unchanged(self):
        temp, target, pbs = self.fixture(
            "[0]\nPIKACHU,RAICHU\n\n[1]\nCHIKORITA,BAYLEEF\n")
        try:
            old = pbs.read_text("utf8")
            report = install_pilot_kantodex(ROOT, target)
            entries = sections(pbs.read_text("utf8"))
            self.assertTrue(pbs.read_text("utf8").startswith(old.rstrip()))
            self.assertEqual(entries[0], ["PIKACHU", "RAICHU"])
            self.assertEqual(entries[1], ["CHIKORITA", "BAYLEEF"])
            self.assertEqual(entries[2], first_151(ROOT))
            self.assertEqual(report["index"], 2)
            self.assertTrue(report["added"])
            self.assertTrue(report["national_dex_unchanged"])
            self.assertEqual(report["length"], 151)
            self.assertEqual(json.loads(
                (target / "Data/blue-kanto-dex.json").read_text("utf8"))["first"],
                "BULBASAUR")
            self.assertNotIn("[National]", pbs.read_text("utf8"))
            self.assertEqual(
                (target / "Data/blue-kanto-dex-index.txt").read_text("ascii").strip(),
                "2|1|2")
        finally:
            temp.cleanup()

    def test_reuses_existing_exact_kanto_list_without_duplicating(self):
        first = first_151(ROOT)
        initial = "[0]\n" + "\n".join(first) + "\n\n[1]\nCHIKORITA\n"
        temp, target, pbs = self.fixture(initial)
        try:
            info = install_pilot_kantodex(ROOT, target)
            self.assertFalse(info["added"])
            self.assertEqual(info["index"], 0)
            self.assertEqual(pbs.read_text("utf8"), initial)
        finally:
            temp.cleanup()

    def test_supports_a_game_with_only_a_national_dex(self):
        temp, target, pbs = self.fixture()
        try:
            info = install_pilot_kantodex(ROOT, target)
            self.assertEqual(info["index"], 0)
            self.assertEqual(sections(pbs.read_text("utf8"))[0],
                             first_151(ROOT))
        finally:
            temp.cleanup()

    def test_rejects_unsafe_overlapping_regional_indices(self):
        temp, target, pbs = self.fixture("[0]\nPIKACHU\n[0]\nRAICHU\n")
        try:
            with self.assertRaisesRegex(ValueError, "Duplicate"):
                install_pilot_kantodex(ROOT, target)
            self.assertNotIn("[1]", pbs.read_text("utf8"))
        finally:
            temp.cleanup()

    def test_native_pokedex_menu_and_save_migration_contract(self):
        script = (ROOT / "scripts/regions/KantoPilot.rb").read_text("utf8")
        self.assertIn("module BlueKantoDex", script)
        self.assertIn('Data/blue-kanto-dex-index.txt', script)
        self.assertNotIn("JSON.parse", script)
        self.assertIn("PokemonPokedexMenuScreen.prepend(DexMenu)", script)
        self.assertIn("Player::Pokedex.prepend(PokedexAccess)", script)
        self.assertIn("flags.insert(index, false)", script)
        self.assertIn("flags[-1] = true", script)
        self.assertIn('result << _INTL("Pokédex Nacional")', script)
        pilot = (ROOT / "scripts/regions/pilot.py").read_text("utf8")
        self.assertIn("install_pilot_kantodex(ROOT, target)", pilot)
        self.assertIn('"data/national-species.json"', pilot)


if __name__ == "__main__":
    unittest.main()
