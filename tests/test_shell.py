"""Regressão estrutural do shell (não requer jogo instalado)."""
from html.parser import HTMLParser
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "web" / "index.html").read_text(encoding="utf-8")
JS = (ROOT / "web" / "navigation.js").read_text(encoding="utf-8")
CSS = (ROOT / "web" / "studio-shell.css").read_text(encoding="utf-8")

class Elements(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.panels = []
        self.shells = []
        self.scripts = []
    def handle_starttag(self, name, attrs):
        a = dict(attrs)
        if "id" in a:
            assert a["id"] not in self.ids, "ID duplicado: " + a["id"]
            self.ids.add(a["id"])
        if "data-panel" in a:
            self.panels.append(a["data-panel"])
        if "data-shell" in a:
            self.shells.append(a["data-shell"])
        if name == "script" and "src" in a:
            self.scripts.append(a["src"])

class ShellRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dom = Elements()
        cls.dom.feed(HTML)

    def test_required_workspace_elements(self):
        essential = {"status","fileList","fileTitle","recordTitle","records",
                     "editorBody","reload","save","new","play","history",
                     "modal","modalBody","toast","romStudio","featurePanel","pbsWorkspace"}
        self.assertFalse(essential - self.dom.ids)

    def test_all_emerald_rom_tabs_preserved(self):
        core = {"project","script","flags","pokemon","items","starters","trainers","wild",
                "map","title-logo","title-flames","music","midi-studio","test-lab"}
        extra = {"hex","table","graphics","sprite","text","patch"}
        self.assertEqual(set(self.dom.panels),core|extra)
        self.assertEqual(len(self.dom.panels),20)
        self.assertEqual(set(self.dom.shells),{"home","rom","movesets"})

    def test_scripts_and_css_exist(self):
        for f in ("style.css","studio-shell.css","app.js","navigation.js"):
            self.assertTrue((ROOT/"web"/f).is_file())
        self.assertEqual(self.dom.scripts,["/app.js","/navigation.js"])
        self.assertIn('href="/studio-shell.css"',HTML)

    def test_feature_gating_and_safe_pbs_files(self):
        for path in ("pokemon.txt","items.txt","trainers_story_mode.txt","encounters.txt"):
            self.assertIn(path,JS)
        self.assertIn("PLANEJADO",JS)
        self.assertIn('work.hidden = !ready',JS)
        self.assertIn('placeholder.hidden = ready',JS)
        self.assertIn('state.raw !== state.original',JS)
        self.assertNotIn("git reset --hard",JS)
        self.assertIn(":root",CSS)

if __name__ == "__main__":
    unittest.main()
