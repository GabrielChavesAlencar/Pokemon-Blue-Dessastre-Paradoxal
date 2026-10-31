import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'server'))
import prepare_game

class BrandingTest(unittest.TestCase):
  def test_window_titles_and_backups(self):
    with tempfile.TemporaryDirectory() as temp:
      oldgame,oldbackups=prepare_game.GAME,prepare_game.BACKUP
      try:
        prepare_game.GAME=Path(temp)/'game'
        prepare_game.BACKUP=Path(temp)/'backup'
        prepare_game.GAME.mkdir()
        ini=prepare_game.GAME/'Game.ini'
        ini.write_text('[Game]\nLibrary=RGSS104E.dll\nTitle=Pokemon Decades 3.0.0\n',encoding='utf-8')
        mkxp=prepare_game.GAME/'mkxp.json'
        mkxp.write_text('''{\n   // the game window\n   "windowTitle": "Pokémon Essentials v21.1",\n   "defScreenW": 512\n}\n''',encoding='utf-8')
        self.assertEqual(prepare_game.main(),0)
        self.assertIn('Title=Pokemon Blue Dessastre Paradoxal',ini.read_text())
        self.assertIn('"windowTitle": "Pokémon Blue: Dessastre Paradoxal"',mkxp.read_text())
        self.assertEqual(len(list(prepare_game.BACKUP.glob('*.bak'))),2)
        self.assertEqual(prepare_game.main(),0)
        self.assertEqual(len(list(prepare_game.BACKUP.glob('*.bak'))),2)
      finally:
        prepare_game.GAME,prepare_game.BACKUP=oldgame,oldbackups
