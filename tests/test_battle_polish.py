import importlib.util,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('blue_polish_install',ROOT/'scripts/battle_polish/install.py')
polish=importlib.util.module_from_spec(spec);spec.loader.exec_module(polish)
class PolishInstallTests(unittest.TestCase):
    def fixture(self,root):
        source=root/'scripts/battle_polish';source.mkdir(parents=True)
        for name in polish.FILES:shutil.copy2(ROOT/'scripts/battle_polish'/name,source/name)
        game=root/'game'
        for name in ['Data/Map001.rxdata','PBS/trainers.txt','Saves/Game.rxdata','Graphics/Pokemon/Front/TEST.png']:
            path=game/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'original '+name.encode())
        return game
    def test_installs_only_own_plugin_and_preserves_campaign(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root);before={p:p.read_bytes() for p in game.rglob('*') if p.is_file()}
            self.assertEqual(polish.install(root,game),4);self.assertEqual(polish.install(root,game),0)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))
    def test_failure_rolls_back_existing_plugin(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root);polish.install(root,game)
            path=game/'Plugins/ZZZZ Blue Story and Presentation/Presentation.rb';path.write_bytes(b'prior version')
            second=game/'Plugins/ZZZZ Blue Story and Presentation/Story.rb';second.write_bytes(b'prior story')
            original=polish.atomic;failed=False
            def fail_once(p,b):
                nonlocal failed
                if p==second and not failed:failed=True;raise OSError('simulated disk failure')
                original(p,b)
            with patch.object(polish,'atomic',side_effect=fail_once),self.assertRaises(OSError):polish.install(root,game)
            self.assertEqual(path.read_bytes(),b'prior version');self.assertEqual(second.read_bytes(),b'prior story')
            self.assertTrue(any(p.read_bytes()==b'prior version' for p in (root/'.blue-backups').rglob('Presentation.rb')))
if __name__=='__main__':unittest.main()
