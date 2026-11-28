import json
import unittest
from scripts.android.k05_package_contract import verify_registry
from scripts.regions.k05_contract import published_destinations


class AndroidLavenderPackageTests(unittest.TestCase):
    def fixture(self):
        slot=published_destinations()
        old={str(200+k):300+k for k in range(164)}
        old["7"]=499
        all_maps={**old,**slot}
        files={"Data/blue-kanto-ready.txt":b"BLUE_KANTO_READY_V1,178,499\n"}
        files.update({f"Data/Map{mid:03d}.rxdata":b"\x04\x08dummy" for mid in slot.values()})
        return all_maps,files

    def verify(self,mapping,files):
        files={**files,"Data/blue-kanto-install.json":json.dumps({"maps":mapping}).encode()}
        return verify_registry(files.__getitem__)

    def test_known_slots_and_older_revision(self):
        maps,files=self.fixture()
        self.assertTrue(self.verify(maps,files))
        old=maps.keys()-published_destinations().keys()
        self.assertFalse(self.verify({k:maps[k] for k in old},files))

    def test_missing_or_swapped_tower_is_never_packaged(self):
        maps,files=self.fixture()
        with self.assertRaises(ValueError):
            self.verify({**maps,"105":621,"106":620},files)
        files["Data/Map621.rxdata"]=b""
        with self.assertRaises(ValueError):
            self.verify(maps,files)

    def test_celadon_world_extension_does_not_change_binary_contract(self):
        from scripts.android.k05_package_contract import CELADON

        maps, files = self.fixture()
        maps.update(CELADON)
        files.update({f"Data/Map{mid:03d}.rxdata": b"\x04\x08dummy" for mid in CELADON.values()})
        files["Data/blue-kanto-ready.txt"] = b"BLUE_KANTO_READY_V1,182,499\n"
        marker = "Data/blue-kanto-install.json"
        def write():
            files[marker] = json.dumps({"maps":maps,"content_stage":"K06_CELADON_SERVICES"}).encode()
        write()
        self.assertTrue(verify_registry(files.__getitem__,allow_celadon=True))
        with self.assertRaisesRegex(ValueError,"historical binary"):
            verify_registry(files.__getitem__)
        for sid, invalid in (("125",622),("105",619)):
            actual = maps[sid]
            maps[sid] = invalid
            write()
            with self.assertRaises(ValueError):
                verify_registry(files.__getitem__,allow_celadon=True)
            maps[sid] = actual
