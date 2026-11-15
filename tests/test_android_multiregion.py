"""Offline proof that the combined Android edition cannot fake Kanto/Hoenn.

No source maps, proprietary game binary, network or user saves are needed.
"""
import json
import tempfile
import sys
import unittest
import zipfile
import zlib
from pathlib import Path
from unittest.mock import patch

from scripts.android import package as mobile
sys.path.insert(0,str(mobile.ROOT/'scripts/regions'))
from scripts.android.build_manifest import installed_manifest
from scripts.android.publish_updates import from_archive
from scripts.android.update_client import CHANNELS, release_for


class MultiRegionPackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="blue-android-three-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.game = self.root / "game"
        self.game.mkdir()
        self.revision = "a" * 40
        self.output = self.root / "Blue-Android-Decades-Kanto-Hoenn.zip"
        (self.game / "Data").mkdir()
        (self.game / "PBS").mkdir()
        self._write("Game.exe", b"fixture exe, not a game")
        self._write("Game.ini", b"[Game]\nTitle=Blue\n")
        self._write("mkxp.json", b"{}")
        self._write("Data/MapInfos.rxdata", b"fixture")
        self._write("Data/Tilesets.rxdata", b"fixture")
        self._write("Data/Map700.rxdata", b"fixture Hoenn map")
        self._write("Data/Map701.rxdata", b"fixture Kanto map")
        self._write("Data/Scripts.rxdata", b"fixture compiled source")
        self._write("Data/PluginScripts.rxdata", b"fixture compiled plugins")
        self._write(mobile.MOBILE, b"fixture mobile")
        self._write(mobile.KANTO_PLUGIN, b"fixture kanto")
        self._write(mobile.HOENN_PLUGIN, b"fixture hoenn")
        self._write(mobile.REGION_START_PLUGIN, b"fixture RegionStart")
        for rel in mobile.REGIONAL_FILES:
            self._write(rel, b"required regional metadata")
        self._write("Data/blue-kanto-install.json", b'{"maps": {"7": 701}}')
        self._write("Data/blue-hoenn-install.json", b'{"maps": {"8": 700}}')
        self._write("Saves/File A.rxdata", b"never ship user save")
        self._write("Data/blue-android-compiled.txt", mobile.fingerprint(self.game).encode())

    def _write(self, rel, data):
        target = self.game / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def test_two_regions_are_required_before_packaging(self):
        (self.game/"Data/blue-hoenn-ready.txt").unlink()
        with self.assertRaisesRegex(ValueError, "Missing mandatory"):
            with patch("install_kanto.verify_installed", return_value={"maps": 142}), \
                 patch("install_hoenn.verify_installed", return_value={"maps": 199}), \
                 patch.object(mobile,"loads",return_value=[]):
                mobile.verify_regions(self.game)

    def test_compiled_plugin_must_match_actual_ruby(self):
        valid=zlib.compress(b"def self.test; true; end")
        corrupt=zlib.compress(b"def self.test; false; end")
        records=[(None,None,[(b"HoennPilot.rb",valid),
                                   (b"RegionStart.rb",valid),
                                   (b"KantoPilot.rb",corrupt)])]
        with patch.object(mobile,"loads",return_value=records):
            mobile.compiled_region(b"fixture", "HoennPilot.rb", b"def self.test; true; end")
            mobile.compiled_region(b"fixture", "RegionStart.rb", b"def self.test; true; end")
            with self.assertRaisesRegex(ValueError,"KantoPilot"):
                mobile.compiled_region(b"fixture", "KantoPilot.rb", b"def self.test; true; end")

    def test_shared_zip_contains_manifests_and_separate_update_channel(self):
        with patch.object(mobile,"verify_regions",return_value=({"maps":142},{"maps":199})), \
             patch.object(mobile,"compiled_mobile",return_value="b"*64), \
             patch.object(mobile,"verify_archive") as verify:
            result=mobile.build(self.game,self.output,self.revision,"multiregion")
            verify.assert_called_once_with(self.output,self.revision,"b"*64,"multiregion")
        self.assertGreater(result["bytes"],0)
        with zipfile.ZipFile(self.output) as archive:
            root="Pokemon-Blue-Android/"
            names=set(archive.namelist())
            for rel in (mobile.KANTO_PLUGIN,mobile.HOENN_PLUGIN,
                        mobile.REGION_START_PLUGIN,*mobile.REGIONAL_FILES,
                        "Data/Map700.rxdata","Data/Map701.rxdata"):
                self.assertIn(root+rel,names)
            self.assertNotIn(root+"Saves/File A.rxdata",names)
            self.assertNotIn(root+"Data/blue-android-compiled.txt",names)
            marker=json.loads(archive.read(root+"Data/blue-update.json"))
            self.assertEqual(marker["channel"],"multiregion")
            self.assertEqual(marker["revision"],self.revision)
            self.assertIn("Data/blue-hoenn-install.json",marker["files"])
            self.assertIn("Data/blue-kanto-install.json",marker["files"])
            self.assertIn("Game.exe",marker["immutable"])
            self.assertIn("EDICAO MULTIRREGIONAL",archive.read(root+"LEIA-ME-ANDROID.txt").decode())
        indexed,folder=from_archive(self.output,"multiregion")
        self.assertEqual(folder,"Pokemon-Blue-Android/")
        self.assertEqual(indexed["revision"],self.revision)

    def test_patch_channels_do_not_cross(self):
        self.assertIn("multiregion",CHANNELS)
        self.assertNotEqual(CHANNELS["decades"],CHANNELS["multiregion"])
        releases=[{"tag_name":"battle-hub-legacy","assets":[]},
                  {"tag_name":"android-multiregion-5-abc1234","target_commitish":self.revision,
                   "assets":[{"name":"Blue-Android-Decades-Kanto-Hoenn.zip",
                              "state":"uploaded","size":1024,
                              "browser_download_url":"https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/download/android-multiregion-5-abc1234/Blue-Android-Decades-Kanto-Hoenn.zip"}]}]
        with patch("scripts.android.update_client.get_json",return_value=releases):
            result=release_for("multiregion")
        self.assertEqual(result["tag_name"],"android-multiregion-5-abc1234")
        with self.assertRaisesRegex(ValueError,"Unknown Android update channel"):
            installed_manifest("unknown",self.revision,{})

if __name__=="__main__":
    unittest.main()
