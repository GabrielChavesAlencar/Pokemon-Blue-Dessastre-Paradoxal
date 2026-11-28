"""Offline proof that the combined Android edition cannot fake Kanto/Hoenn.

No source maps, proprietary game binary, network or user saves are needed.
"""
import hashlib
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
from hoenn_catalog import (
    CATALOG, CATALOG_REVISION, INSTALL_STATUS, LEGACY_SOURCE_IDS, UPSTREAM,
    approved_source_ids, marker_bytes,
)
from server.ruby_marshal import integer


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

    def _verified_hoenn_zip(self, schema, *, transform=None, catalog_revision=1):
        legacy = {str(src): dst for dst, src in enumerate(sorted(LEGACY_SOURCE_IDS), 700)}
        mapping = dict(legacy)
        if schema == 2:
            extras = approved_source_ids(catalog_revision) - LEGACY_SOURCE_IDS
            mapping.update((str(src), dst) for dst, src in enumerate(
                sorted(extras), max(legacy.values()) + 1,
            ))
        proof = {
            "schema": schema, "region": "HOENN", "source_commit": UPSTREAM,
            "status": INSTALL_STATUS, "maps": mapping,
            "start": [mapping["8"], 25, 6, 2], "town": [mapping["7"], 10, 10, 2],
            "installed_sha256": {},
        }
        if schema == 2:
            proof.update(catalog_revision=catalog_revision, legacy_maps=legacy)
        files = {rel: b"fixture" for rel in mobile.REGIONAL_FILES}
        files.update(marker_bytes(proof))
        compact = "Data/blue-hoenn-pilot.txt"
        proof["installed_sha256"][compact] = hashlib.sha256(files[compact]).hexdigest()
        files["Data/blue-hoenn-install.json"] = json.dumps(proof).encode("utf-8")
        files["Data/blue-kanto-install.json"] = json.dumps(
            {"maps": {str(mid): mid for mid in range(400, 501)}}).encode("utf-8")
        files["Data/MapInfos.rxdata"] = (
            b"\x04\x08{" + integer(len(mapping)) +
            b"".join(b"i" + integer(dest) + b"i" + integer(1) for dest in mapping.values())
        )
        for dest in mapping.values():
            files[f"Data/Map{dest:03}.rxdata"] = b"fixture map"
        for rel in (mobile.MOBILE, mobile.KANTO_PLUGIN, mobile.HOENN_PLUGIN,
                    mobile.REGION_START_PLUGIN, "Data/Scripts.rxdata", "Data/PluginScripts.rxdata"):
            files[rel] = b"fixture"
        files["Data/blue-mobile-build.txt"] = (
            f"Revision: {self.revision}\nMobile-SHA256: {'b' * 64}\n".encode("ascii")
        )
        files["LEIA-ME-ANDROID.txt"] = f"Revision: {self.revision}\n".encode("ascii")
        if transform:
            transform(files, mapping)
        files["Data/blue-update.json"] = installed_manifest("multiregion", self.revision, files)
        with zipfile.ZipFile(self.output, "w") as archive:
            for name, blob in files.items():
                archive.writestr("Pokemon-Blue-Android/" + name, blob)

    def _verify_hoenn_zip(self):
        with patch.object(mobile, "compiled_mobile", return_value="b" * 64), \
             patch.object(mobile, "verify_early_input"), patch.object(mobile, "compiled_region"):
            return mobile.verify_archive(self.output, self.revision, channel="multiregion")

    def test_zip_reads_legacy_and_versioned_hoenn_manifests(self):
        for schema in (1, 2):
            with self.subTest(schema=schema):
                self._verified_hoenn_zip(schema)
                self.assertEqual(self._verify_hoenn_zip()["revision"], self.revision)

    def test_zip_accepts_expansion_only_with_an_approved_catalog(self):
        revision = CATALOG_REVISION + 1
        with patch.dict(CATALOG["revisions"], {str(revision): [*sorted(LEGACY_SOURCE_IDS), 10000]}):
            self._verified_hoenn_zip(2, catalog_revision=revision)
            self.assertEqual(self._verify_hoenn_zip()["revision"], self.revision)
        with self.assertRaisesRegex(ValueError, "Revisão desconhecida"):
            self._verify_hoenn_zip()

    def test_zip_rejects_missing_physical_map_and_conflicting_id(self):
        def remove_map(files, mapping):
            files.pop(f"Data/Map{mapping['8']:03}.rxdata")
        self._verified_hoenn_zip(2, transform=remove_map)
        with self.assertRaisesRegex(ValueError, "missing a Hoenn map file"):
            self._verify_hoenn_zip()

        def steal_map(files, mapping):
            rel = "Data/blue-kanto-install.json"
            kanto = json.loads(files[rel])
            kanto["maps"]["400"] = mapping["8"]
            files[rel] = json.dumps(kanto).encode("utf-8")
        self._verified_hoenn_zip(2, transform=steal_map)
        with self.assertRaisesRegex(ValueError, "claim the same map ID"):
            self._verify_hoenn_zip()

    def test_zip_rejects_forged_hoenn_marker_and_compact_checksum(self):
        def wrong_generation(files, mapping):
            rel = "Data/blue-hoenn-ready.txt"
            files[rel] = files[rel].replace(b"V2", b"V1")
        self._verified_hoenn_zip(2, transform=wrong_generation)
        with self.assertRaisesRegex(ValueError, "blue-hoenn-ready"):
            self._verify_hoenn_zip()

        def change_compact_encoding(files, mapping):
            rel = "Data/blue-hoenn-pilot.txt"
            files[rel] = files[rel].replace(b"\n", b"\r\n")
        self._verified_hoenn_zip(2, transform=change_compact_encoding)
        with self.assertRaisesRegex(ValueError, "blue-hoenn-pilot"):
            self._verify_hoenn_zip()

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

    def test_sinnoh_qa_requires_johto_boot_markers_and_all_maps(self):
        self._write(mobile.JOHTO_QA_PROOF,json.dumps({
            "region":"JOHTO", "status":"EXPERIMENTAL_PRIVATE_UNVERIFIED",
            "source_bundle_sha256":"74e727875803f70b3c0598b6b88fe5d79717df849ba1b888fae0583c09202a49",
            "native_gameplay_verified":False, "map_ids":list(range(600,700))}).encode())
        for rel in (mobile.JOHTO_QA_BOOT, "PBS/trainers_johto.txt",
                    "PBS/trainer_types_johto.txt", "PBS/map_metadata_johto_main.txt",
                    *(f"Data/Map{i:03d}.rxdata" for i in range(600,700))):
            self._write(rel,b"fixture")
        read = lambda rel: (self.game/rel).read_bytes()
        with patch.object(mobile,"compiled_region") as compile_check:
            with self.assertRaises(FileNotFoundError):
                mobile.verify_johto_qa(read)
            self._write(mobile.JOHTO_QA_READY,b"BLUE_JOHTO_PRIVATE_PREVIEW_V1,100,674,6,7,600,10,26,600,10,25")
            mobile.verify_johto_qa(read)
            compile_check.assert_called_once_with(b"fixture compiled plugins","Boot.rb",b"fixture")
            with patch.object(mobile,"verify_regions"), self.assertRaisesRegex(ValueError,"prévia privada de Johto"):
                mobile.build(self.game,self.output,self.revision,"multiregion")
            (self.game/"Data/Map699.rxdata").unlink()
            with self.assertRaises(FileNotFoundError):
                mobile.verify_johto_qa(read)

    def test_shared_zip_contains_manifests_and_separate_update_channel(self):
        with patch.object(mobile,"verify_regions",return_value=({"maps":142},{"maps":199})), \
             patch.object(mobile,"compiled_mobile",return_value="b"*64), \
             patch.object(mobile,"verify_archive") as verify:
            result=mobile.build(self.game,self.output,self.revision,"multiregion")
        verify.assert_called_once_with(self.output,self.revision,"b"*64,"multiregion",sinnoh_qa=False)
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
                              "browser_download_url":"https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/download/android-multiregion-5-abc1234/Blue-Android-Decades-Kanto-Hoenn.zip"},
                             {"name":"Blue-Android-Decades-Kanto-Hoenn.update.json",
                              "state":"uploaded",
                              "browser_download_url":"https://github.com/GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal/releases/download/android-multiregion-5-abc1234/Blue-Android-Decades-Kanto-Hoenn.update.json"}]}]
        with patch("scripts.android.update_client.get_json",return_value=releases):
            result=release_for("multiregion")
        self.assertEqual(result["tag_name"],"android-multiregion-5-abc1234")
        with self.assertRaisesRegex(ValueError,"Unknown Android update channel"):
            installed_manifest("unknown",self.revision,{})

if __name__=="__main__":
    unittest.main()
