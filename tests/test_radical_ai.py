import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('blue_radical_install',ROOT/'scripts/radical_ai/install.py')
ai=importlib.util.module_from_spec(spec);spec.loader.exec_module(ai)

class RadicalAIInstallerTests(unittest.TestCase):
    def fixture(self,root):
        (root/'data').mkdir()
        shutil.copy2(ROOT/'data/radical-ai.json',root/'data/radical-ai.json')
        shutil.copytree(ROOT/'scripts/radical_ai',root/'scripts/radical_ai')
        game=root/'game';(game/'Data').mkdir(parents=True)
        (game/'Data/Scripts.rxdata').write_bytes(b'original scripts')
        (game/'Data/Map001.rxdata').write_bytes(b'campaign map')
        (game/'PBS').mkdir();(game/'PBS/trainers.txt').write_bytes(b'original trainers')
        (game/'save.rxdata').write_bytes(b'campaign save')
        return game

    def test_install_is_idempotent_and_preserves_campaign(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            before={p:p.read_bytes() for p in game.rglob('*') if p.is_file()}
            dry=ai.install(root,game)
            self.assertFalse(dry['applied']);self.assertFalse((game/'Plugins').exists())
            self.assertTrue(ai.install(root,game,True)['applied'])
            self.assertEqual(ai.install(root,game,True)['files'],0)
            self.assertTrue(all(p.read_bytes()==data for p,data in before.items()))
            config=(game/'Plugins/ZZZZZ Blue Radical AI/000_Config.rb').read_text()
            self.assertIn("'defaultProfile' => 'radical'",config)

    def test_invalid_policy_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            p=root/'data/radical-ai.json';config=json.loads(p.read_text());config['defaultProfile']='unknown'
            p.write_text(json.dumps(config))
            with self.assertRaises(ValueError):ai.install(root,game,True)
            self.assertFalse((game/'Plugins').exists())

    def test_missing_source_file_cannot_partially_install(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            (root/'scripts/radical_ai/Snapshot.rb').unlink()
            with self.assertRaises(FileNotFoundError):ai.install(root,game,True)
            self.assertFalse((game/'Plugins').exists())

    def test_updated_plugin_has_exact_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            ai.install(root,game,True)
            plugin=game/'Plugins/ZZZZZ Blue Radical AI/Policy.rb';old=plugin.read_bytes()
            source=root/'scripts/radical_ai/Policy.rb';source.write_bytes(old+b'\n# new version\n')
            result=ai.install(root,game,True)
            self.assertEqual(result['files'],1)
            self.assertEqual((Path(result['backup'])/'Plugins/ZZZZZ Blue Radical AI/Policy.rb').read_bytes(),old)

    def test_failure_rolls_back_installed_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            ai.install(root,game,True)
            plugin=game/'Plugins/ZZZZZ Blue Radical AI'
            before={p:p.read_bytes() for p in plugin.iterdir()}
            for name in ['Policy.rb','Snapshot.rb']:
                p=root/'scripts/radical_ai'/name;p.write_bytes(p.read_bytes()+b'\n# updated\n')
            original=ai.atomic
            def fail_second(path,data):
                if path==plugin/'Snapshot.rb' and data.endswith(b'# updated\n'):raise OSError('simulated write failure')
                return original(path,data)
            with patch.object(ai,'atomic',side_effect=fail_second):
                with self.assertRaises(OSError):ai.install(root,game,True)
            self.assertTrue(all(p.read_bytes()==data for p,data in before.items()))

    def test_policy_bounds_and_ruby_strings_are_checked(self):
        config=json.loads((ROOT/'data/radical-ai.json').read_text())
        config['profiles']['radical']['strength']=float('nan')
        with self.assertRaises(ValueError):ai.validate(config)
        self.assertEqual(ai.ruby("a'b\\c"),"'a\\'b\\\\c'")

if __name__=='__main__':unittest.main()
