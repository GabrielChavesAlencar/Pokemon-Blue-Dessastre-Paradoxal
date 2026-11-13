"""Teste do exportador privado usando dados sinteticos, sem assets do jogo."""
import hashlib
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/regions'))
from export_johto_pilot_inputs import export, gather


class JohtoPrivateExportTests(unittest.TestCase):
    def setUp(self):
        self._temp = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp.cleanup)
        self.root = Path(self._temp.name)
        self.game = self.root / 'game'
        for path, content in {
            'Data/MapInfos.rxdata': b'info',
            'Data/Tilesets.rxdata': b'tiles',
            'Data/System.rxdata': b'system',
            'Data/Map001.rxdata': b'map',
            'Data/Scripts.rxdata': b'private-scripts',
            'Data/Save001.rxdata': b'save',
            'Game.exe': b'EXE',
            'PBS/trainers.txt': b'[TEST]',
            'PBS/.env': b'APIKEY',
            'Graphics/Tilesets/Inside.png': b'\x89PNG\r\n\x1a\nabc',
            'Graphics/Characters/Mom.png': b'\x89PNG\r\n\x1a\nxyz',
        }.items():
            dest = self.game / path
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(content)

    def test_private_zip_excludes_executables_saves_and_code(self):
        out = self.root / '.blue-work/johto-pilot-inputs.zip'
        before = hashlib.sha256((self.game / 'Data/Map001.rxdata').read_bytes()).hexdigest()
        result = export(self.game, out, root=self.root)
        self.assertEqual(result['files'], 6)
        with zipfile.ZipFile(out) as z:
            names = set(z.namelist())
            self.assertIn('game/Data/Map001.rxdata', names)
            self.assertIn('game/Graphics/Tilesets/Inside.png', names)
            self.assertNotIn('game/Data/Scripts.rxdata', names)
            self.assertNotIn('game/Data/Save001.rxdata', names)
            self.assertNotIn('game/Game.exe', names)
            self.assertNotIn('game/PBS/.env', names)
            self.assertNotIn('game/Graphics/Characters/Mom.png', names)
            manifest = json.loads(z.read('johto-inputs-manifest.json'))
            self.assertFalse(manifest['safe_for_public_github'])
            self.assertFalse(manifest['contains_saves'])
            self.assertEqual(len(manifest['files']), result['files'])
        self.assertEqual(before, hashlib.sha256((self.game / 'Data/Map001.rxdata').read_bytes()).hexdigest())
        with self.assertRaisesRegex(ValueError, 'novo'):
            export(self.game, out, root=self.root)

    def test_opt_in_sprites_and_external_output_blocked(self):
        out = self.root / '.blue-work/johto-sprites.zip'
        export(self.game, out, sprites=True, root=self.root)
        with zipfile.ZipFile(out) as z:
            self.assertIn('game/Graphics/Characters/Mom.png', z.namelist())
        with self.assertRaisesRegex(ValueError, 'Destino'):
            export(self.game, self.root / 'published.zip', root=self.root)

    def test_missing_map_and_symlink_rejected(self):
        (self.game / 'Data/Map001.rxdata').unlink()
        with self.assertRaisesRegex(ValueError, 'Nenhum Map'):
            gather(self.game)
        (self.game / 'Data/Map001.rxdata').symlink_to(self.game / 'Data/MapInfos.rxdata')
        with self.assertRaisesRegex(ValueError, 'Link simbolico'):
            gather(self.game)

if __name__ == '__main__':
    unittest.main()
