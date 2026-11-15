"""Kanto locale overlay must not replace native Decades strings or require RXDATA."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location(
    "blue_locale_integrated_test", ROOT/"scripts/localization/install.py")
locale=importlib.util.module_from_spec(spec)
spec.loader.exec_module(locale)
from server.ruby_marshal import dumps_simple,loads,text


class IntegratedKantoLocaleTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix="kanto-main-locale-")
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.game=self.root/"game"
        (self.root/"data").mkdir()
        (self.game/"Data").mkdir(parents=True)
        (self.root/"data/pt-br.json").write_text(
            json.dumps({"version":1,"language":"pt-BR",
                        "translations":{"Save":"Salvar", "Hello":"Olá"}},
                       ensure_ascii=False),encoding="utf8")
        self.overlay=self.game/"Data/blue-kanto-locale.dat"
        self.overlay.write_bytes(dumps_simple([
            ["Save","Salvar Kanto (não substituir)"],
            ["Professor Oak","Professor Carvalho"],
        ]))

    def compiled(self):
        plan=locale.plan(self.root,self.game)
        data=plan[self.game/"Data/blue-pt-br.dat"]
        return {text(k):text(v) for k,v in loads(data)}

    def proof(self,source="Essentials FRLG 21.1",schema=1):
        (self.game/"Data/blue-kanto-install.json").write_text(
            json.dumps({"schema":schema,"source":source}),encoding="utf8")

    def test_no_installed_kanto_keeps_decades_only(self):
        translations=self.compiled()
        self.assertEqual(translations["Save"],"Salvar")
        self.assertNotIn("Professor Oak",translations)

    def test_installed_kanto_adds_localized_dialogue_without_overriding_decades(self):
        self.proof()
        translations=self.compiled()
        self.assertEqual(translations["Save"],"Salvar")
        self.assertEqual(translations["Hello"],"Olá")
        self.assertEqual(translations["Professor Oak"],"Professor Carvalho")

    def test_unrecognized_installation_cannot_merge_locale(self):
        self.proof(schema=99)
        with self.assertRaises(ValueError):
            self.compiled()

    def test_malformed_regional_locale_cannot_break_decades_silently(self):
        self.proof()
        self.overlay.write_bytes(b"not-a-marshal")
        with self.assertRaises(ValueError):
            self.compiled()


if __name__=="__main__":
    unittest.main()
