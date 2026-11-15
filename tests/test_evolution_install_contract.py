"""Verifies the already-used Blue-Story installer distributes the new script."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
PLUGINS=ROOT/"scripts/battle_polish"

class EvolutionInstallerTests(unittest.TestCase):
    def test_new_script_in_atomic_blue_story_installer(self):
        tree=ast.parse((PLUGINS/"install.py").read_text(encoding="utf8"))
        assignment=next(n for n in tree.body
                        if isinstance(n,ast.Assign) and any(
                            isinstance(t,ast.Name) and t.id=="FILES" for t in n.targets))
        files=ast.literal_eval(assignment.value)
        self.assertEqual(files.count("EvolutionScaling.rb"),1)
        self.assertTrue((PLUGINS/"EvolutionScaling.rb").is_file())
        self.assertLess(files.index("Balance.rb"),files.index("EvolutionScaling.rb"))
    def test_essentials_plugin_load_order(self):
        meta=(PLUGINS/"meta.txt").read_text(encoding="utf8")
        scripts=next(line for line in meta.splitlines()
                     if line.startswith("Scripts =")).split("=",1)[1].split(",")
        scripts=[s.strip() for s in scripts]
        self.assertEqual(scripts.count("EvolutionScaling.rb"),1)
        self.assertLess(scripts.index("Story.rb"),scripts.index("EvolutionScaling.rb"))
        self.assertLess(scripts.index("EvolutionScaling.rb"),scripts.index("Habitat.rb"))
        story=(PLUGINS/"Story.rb").read_text(encoding="utf8")
        self.assertIn("BlueEvolutionScaling.install",story)
    def test_no_destructive_pbs_or_save_rewriting(self):
        script=(PLUGINS/"EvolutionScaling.rb").read_text(encoding="utf8")
        self.assertIn("PokemonEncounters.prepend(WildEncounters)",script)
        self.assertNotIn("SaveData.delete",script)
        self.assertNotIn("GameData::Species.register",script)
        self.assertNotIn("GameData::Trainer.register",script)

if __name__=="__main__":
    unittest.main()
