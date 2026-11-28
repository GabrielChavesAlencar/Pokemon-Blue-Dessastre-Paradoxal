import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_k05_lavender import K05, CITY, TOWER, propose_slots, scoped_links, page_scripts, role


class K05SourceTests(unittest.TestCase):
    def test_slots_are_append_only_and_provisional(self):
        catalog = json.loads((ROOT / "data/regions/kanto-source.json").read_text(encoding="utf8"))
        active = {int(k) for k in catalog["maps"]}
        if active & set(K05):
            catalog["maps"] = {k:v for k,v in catalog["maps"].items() if int(k) not in K05}
        self.assertEqual(CITY, (93,94,95,96,97,98))
        self.assertEqual(TOWER, (100,101,102,103,104,105,106))
        slots = propose_slots(catalog, set(range(1,300)))
        self.assertEqual(set(slots), set(K05))
        self.assertEqual(list(slots.values()), list(range(609,622)))
        with self.assertRaisesRegex(ValueError, "reserved map ID 604"):
            propose_slots(catalog, {299,604})

    def test_source_seam_and_deferred_lanes(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp) / "map_connections.txt"
            p.write_text("93,North,0,87,South,0\n93,South,0,83,North,0\n", encoding="utf8")
            known = scoped_links(p,{87})
            self.assertTrue(known[0]["both_ends_in_first_visit"])
            self.assertFalse(known[1]["both_ends_in_first_visit"])
            p.write_text("93,North,1,87,South,0\n", encoding="utf8")
            with self.assertRaisesRegex(ValueError, "zero offset"):
                scoped_links(p,{87})

    def test_audit_extracts_logic_not_dialogue(self):
        p = {"commands":[{"code":101,"indent":0,"parameters":["story dialogue"]},
                         {"code":355,"indent":1,"parameters":["pbPokemonMart([:POTION])"]}]}
        self.assertEqual(list(page_scripts(p)),[(355,1,"pbPokemonMart([:POTION])")])
        self.assertEqual(role("pbPokemonMart"),"mart")
        self.assertEqual(role("pbSetPokemonCenter"),"center")
        self.assertEqual(role("pbReceiveItem"),"item_write")
        self.assertIsNone(role("pbMessage"))
