import json
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from audit_k05_lavender import K05, CITY, TOWER, propose_slots, scoped_links, page_scripts, role, logic_witness, encounter_rows


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
            p.write_text("93,North,0,87,South,0\n93,South,0,83,North,0\n93,West,0,86,East,90\n", encoding="utf8")
            known = scoped_links(p,{86,87})
            self.assertTrue(known[0]["both_ends_in_first_visit"])
            self.assertFalse(known[1]["both_ends_in_first_visit"])
            self.assertTrue(known[2]["both_ends_in_first_visit"])
            self.assertEqual([r["city_fixture_allowed"] for r in known],[True,False,False])
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


    def test_receipt_never_includes_raw_trainer_script(self):
        lines = [(111,1,"$game_variables[7] == 1 && :CHARMANDER"),
                 (355,2,'TrainerBattle.start(:RIVAL2,"Blue",52); private_text = "do not copy"'),
                 (355,2,'TrainerBattle.start(:RIVAL2,"Blue",team_version)')]
        result = logic_witness(101,3,lines)
        self.assertEqual(result["selector_variables"],[(7,"==",1)])
        self.assertEqual(result["starter_symbols"],["CHARMANDER"])
        self.assertEqual([r["literal_first_extra_argument"] for r in result["battle_calls"]],[52,None])
        self.assertNotIn("do not copy",json.dumps(result))
        self.assertEqual(logic_witness(97,1,[(355,0,"pbChangePokemonName(0)")]),
                         {"native_nickname_calls":["pbChangePokemonName"]})

    def test_encounter_receipt_has_typed_slots(self):
        pbs = {"102,0":["CaveDay,8\n90,GASTLY,12,13,14 # verified\n10,HAUNTER,20,20\nCaveNight,10\n100,GASTLY,13,14"]}
        receipt = encounter_rows(pbs,102)["102,0"]
        self.assertEqual(receipt["CaveDay"],{"step_chance":8,"slots":[[90,"GASTLY",[12,13,14]],[10,"HAUNTER",[20,20]]]})
        self.assertEqual(receipt["CaveNight"],{"step_chance":10,"slots":[[100,"GASTLY",[13,14]]]})
