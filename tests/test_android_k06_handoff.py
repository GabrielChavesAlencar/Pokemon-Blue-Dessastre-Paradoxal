"""The source-stage selection never accidentally enters the released K05 cache."""
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from scripts.android import update_client


class K06SourceHandoffTest(TestCase):
    def test_explicit_k06_never_uses_old_k05_cache(self):
        with TemporaryDirectory() as temp:
            top=Path(temp).resolve()
            game=top/"game"
            game.mkdir()
            launcher=game/"ATUALIZAR-ANDROID.py"
            home=top/"termux"
            k05=home/".cache/pokemon-blue-android/k05/scripts/android/source_update.py"
            k05.parent.mkdir(parents=True)
            k05.touch()
            k06=home/".cache/pokemon-blue-android/k06/scripts/android/k06_source_candidate.py"
            baseline={"channel":"multiregion","source_update":{"product_revision":"0eaf940"}}
            with patch.object(update_client,"__file__",str(launcher)), \
                 patch.object(Path,"home",return_value=home), \
                 patch.object(update_client,"read_installed",return_value=baseline), \
                 patch.object(update_client.subprocess,"run",return_value=SimpleNamespace(returncode=0)) as run:
                args=["--game-dir",str(game),"--source","--source-stage","k06","--update"]
                with self.assertRaisesRegex(ValueError,"K06 não está instalada"):
                    update_client.main(args)
                run.assert_not_called()
                k06.parent.mkdir(parents=True)
                k06.touch()
                self.assertEqual(update_client.main(args),0)
                self.assertEqual(run.call_args.args[0][1],str(k06))
                update_client.main(["--game-dir",str(game),"--source"])
                self.assertEqual(run.call_args.args[0][1],str(k05))
                baseline["source_update"]["stage"]="K06_APPROACH"
                update_client.main(["--game-dir",str(game),"--source"])
                self.assertEqual(run.call_args.args[0][1],str(k06))
