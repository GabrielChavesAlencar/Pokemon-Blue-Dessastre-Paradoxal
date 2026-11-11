import importlib.util,shutil,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('blue_polish_install',ROOT/'scripts/battle_polish/install.py')
polish=importlib.util.module_from_spec(spec);spec.loader.exec_module(polish)
class PolishInstallTests(unittest.TestCase):
    def fixture(self,root):
        source=root/'scripts/battle_polish';source.mkdir(parents=True)
        for name in polish.FILES+polish.SUPPORT:shutil.copy2(ROOT/'scripts/battle_polish'/name,source/name)
        for name in ('site/public/data/regions.json','scripts/regions/runtime.py'):
            destination=root/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,destination)
        game=root/'game'
        for name in ['Data/Map001.rxdata','PBS/trainers.txt','Saves/Game.rxdata','Graphics/Pokemon/Front/TEST.png']:
            path=game/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b'original '+name.encode())
        return game
    def test_installs_only_own_plugin_and_preserves_campaign(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=self.fixture(root);before={p:p.read_bytes() for p in game.rglob('*') if p.is_file()}
            self.assertEqual(polish.install(root,game),len(polish.FILES)+1);self.assertEqual(polish.install(root,game),0)
            self.assertTrue(all(p.read_bytes()==raw for p,raw in before.items()))
    def test_master_team_rules_are_isolated_and_native_smoke_covers_them(self):
        import subprocess
        ruby=shutil.which('ruby')
        if ruby:
            for filename in ('Campaign.rb','CampaignValidation.rb'):
                checked=subprocess.run([ruby,'-c',str(ROOT/'scripts/battle_polish'/filename)],
                                       capture_output=True,text=True)
                self.assertEqual(checked.returncode,0,checked.stderr)
        source=(ROOT/'scripts/battle_polish/Campaign.rb').read_text()
        validation=(ROOT/'scripts/battle_polish/CampaignValidation.rb').read_text()
        self.assertIn('scaled_level(party,master? ? 90 : 70)',source)
        self.assertIn('trainer.party.length.between?(1,3)',source)
        self.assertIn('slots=[6-trainers.sum',source)
        self.assertIn('master_weaknesses(party)',source)
        self.assertIn('Effectiveness.calculate',source)
        self.assertIn('BlueCampaign.expand_master_teams(trainers,level)',source)
        self.assertIn('Master fills 3-member trainer teams to 4 at 90 percent level',validation)
        self.assertIn('Master keeps complete six-Pokemon boss/leader teams intact',validation)

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
