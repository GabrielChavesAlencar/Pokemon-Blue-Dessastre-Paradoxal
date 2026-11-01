import importlib.util,hashlib,json,subprocess,sys,tempfile,unittest,zipfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path);obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj
package=load('hub_package','scripts/battle_hub/package.py');setup=load('hub_setup','scripts/install_game.py')
class HubPackageTests(unittest.TestCase):
    def test_package_is_reproducible_and_contains_only_hub_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            first=Path(tmp)/'one/Blue-Battle-Hub.zip';second=Path(tmp)/'two/Blue-Battle-Hub.zip'
            a=package.build(ROOT,first,'test');b=package.build(ROOT,second,'test');self.assertEqual(a['sha256'],b['sha256'])
            with zipfile.ZipFile(first) as archive:
                names=archive.namelist();self.assertIn('Blue-Battle-Hub/HUB_DE_BATALHA.bat',names)
                self.assertFalse(any('/game/' in n or '/.git/' in n or '/.blue-backups/' in n or n.endswith('.exe') for n in names))
                self.assertNotIn('Blue-Battle-Hub/server/main.py',names);self.assertNotIn('Blue-Battle-Hub/site/src/index.html',names)
                manifest=json.loads(archive.read('Blue-Battle-Hub/hub-manifest.json'));self.assertFalse(manifest['baseIncluded'])
                for row in manifest['files']:
                    raw=archive.read('Blue-Battle-Hub/'+row['path']);self.assertEqual(hashlib.sha256(raw).hexdigest(),row['sha256'])
                archive.extractall(Path(tmp)/'extract')
            root=Path(tmp)/'extract/Blue-Battle-Hub'
            for script in ['scripts/install_game.py','scripts/battle_lab/launch.py','scripts/dessastre_paradoxal/install.py','scripts/official_rules/restore.py']:
                result=subprocess.run([sys.executable,script,'--help'],cwd=root,capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
    def test_hub_only_installer_does_not_prepare_or_launch_campaign(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);game=root/'game';(game/'PBS').mkdir(parents=True);(game/'Game.exe').write_bytes(b'fixture');(game/'PBS/pokemon.txt').write_text('fixture')
            with patch.object(setup,'run') as run:
                setup.install(root,game,True)
                commands=[list(map(str,c.args[0])) for c in run.call_args_list]
                self.assertTrue(any('scripts/battle_lab/launch.py' in c and '--install-only' in c for c in commands))
                self.assertFalse(any('scripts/launch_game.py' in c for c in commands))
if __name__=='__main__':unittest.main()
