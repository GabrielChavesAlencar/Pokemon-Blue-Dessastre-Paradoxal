import importlib.util,shutil,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('blue_options_install',ROOT/'scripts/battle_options/install.py')
options=importlib.util.module_from_spec(spec);spec.loader.exec_module(options)

class BattleOptionsInstallTests(unittest.TestCase):
    def fixture(self,root):
        source=root/'scripts/battle_options';source.mkdir(parents=True)
        for name in options.FILES:shutil.copy2(ROOT/'scripts/battle_options'/name,source/name)
        game=root/'game'
        for name,raw in [('Data/Map033.rxdata',b'original map'),('Graphics/Pokemon/Front/TEST.png',b'original art'),('Saves/Game.rxdata',b'campaign save')]:
            path=game/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        return game
    def test_installer_preserves_original_maps_art_saves_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            before={p:p.read_bytes() for p in game.rglob('*') if p.is_file()}
            self.assertEqual(options.install(root,game),5)
            self.assertEqual(options.install(root,game),0)
            for p,raw in before.items():self.assertEqual(p.read_bytes(),raw)
    def test_replacing_old_own_plugin_keeps_exact_backup(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root)
            p=game/'Plugins/ZZZZ Blue Battle Options/Rules.rb';p.parent.mkdir(parents=True);p.write_bytes(b'old rules')
            options.install(root,game)
            backups=list((root/'.blue-backups').rglob('Rules.rb'))
            self.assertEqual(len(backups),1);self.assertEqual(backups[0].read_bytes(),b'old rules')

if __name__=='__main__':unittest.main()
