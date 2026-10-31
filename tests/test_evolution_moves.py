"""Regressions for canonical evolution moves (PBS level zero)."""
import sys
import unittest
from pathlib import Path

PROJECT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(PROJECT / 'server'), str(PROJECT / 'tests')]
from test_moves_editor import MoveFixture
from moves_editor import MoveEditorError
from pokemon_studio import validate_pokemon, PokemonValidationError

class EvolutionMoveTests(MoveFixture):
    def test_roundtrip_evolution_move(self):
        first = self.get('pokemon.txt', 0)
        expected = [{'level': 0, 'move': 'TACKLE'}, {'level': 1, 'move': 'BITE'}]
        self.save_record(first, level=expected)
        self.assertEqual(self.get('pokemon.txt', 0)['own']['level'], expected)

    def test_species_validator_accepts_evolution_move(self):
        raw = '[ALPHAMON]\nName = Alpha\nTypes = WATER\nBaseStats = 80,80,80,80,80,80\nAbilities = SWIFTSWIM\nMoves = 0,TACKLE,1,BITE\n'
        self.assertTrue(validate_pokemon(self.root, raw)['valid'])
        with self.assertRaises(PokemonValidationError):
            validate_pokemon(self.root, raw.replace('0,TACKLE','-1,TACKLE'))

    def test_negative_move_levels_are_rejected(self):
        first = self.get('pokemon.txt', 0)
        with self.assertRaises(MoveEditorError):
            self.save_record(first, level=[{'level': -1, 'move': 'TACKLE'}])

if __name__ == '__main__':
    unittest.main(verbosity=2)
