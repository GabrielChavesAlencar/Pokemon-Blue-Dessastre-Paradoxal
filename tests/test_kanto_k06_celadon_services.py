from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts/regions"))
from audit_k06_celadon_services import script_groups, typed_services, vending_controls
from build_k06_celadon_services import CANDIDATES, FLOORS, allocate, check_approach_stamp, commands_for, copy_celadon_fixture, ensure_tea_item, SAVE


class CeladonSourceReceiptsTest(unittest.TestCase):
    def test_multiline_stock_has_no_script_or_dialogue_in_receipt(self):
        commands=[{"code":355,"parameters":["pbPokemonMart(["]},
                  {"code":655,"parameters":[":POTION, :REPEL,"]},
                  {"code":655,"parameters":["], 'DONOR DIALOGUE')"]},
                  {"code":101,"parameters":["DONOR TEXT"]}]
        groups=list(script_groups(commands))
        self.assertEqual(len(groups),1)
        self.assertEqual(typed_services(groups[0]),{
            "shops":[{"literal":True,"items":["POTION","REPEL"]}],
            "rewards":[],"item_arguments":[],"interaction_calls":[]})

    def test_dynamic_shop_is_marked_for_review_and_rewards_are_symbols(self):
        row=typed_services("pbPokemonMart([:POTION, eval('unreviewed')]); pbReceiveItem(:COINCASE)")
        self.assertEqual(row["shops"],[{"literal":False,"items":[]}])
        self.assertEqual(row["rewards"],[{"operation":"pbReceiveItem","item_or_species":"COINCASE"}])


    def test_item_operands_are_typed(self):
        typed = typed_services("$bag.remove(:FRESHWATER, 1); pbAddPokemon(:EEVEE, 25)")
        self.assertEqual(typed["item_arguments"], [
            {"operation": "remove", "item_or_species": "FRESHWATER", "quantity": 1},
            {"operation": "pbAddPokemon", "item_or_species": "EEVEE", "quantity": 25},
        ])

    def test_candidate_ids_reject_even_an_orphan_map_file(self):
        before = dict(zip(range(178), range(300, 478), strict=True))
        # Invented donor keys must not overlap the exact four candidate keys.
        before = {sid+300: mid for sid, mid in before.items()}
        registry = dict.fromkeys(before.values())
        after = allocate(registry, registry, before)
        self.assertEqual(after, {**before, **CANDIDATES})
        with self.assertRaises(ValueError):
            allocate(registry, {**registry,276: None}, before)
        with self.assertRaises(ValueError):
            allocate({**registry,277: None}, registry, before)

    def test_elevator_exits_are_native_and_cannot_reach_roof(self):
        mapping = {sid: sid + 250 for sid in FLOORS}
        rows = [{"source": 123, "destination": sid, "xy": [6, 2], "direction": 0}
                for sid in FLOORS]
        commands = [op.attrs for op in commands_for(rows, mapping)]
        self.assertEqual([c["@code"] for c in commands], [111, 201, 412]*5)
        self.assertEqual([c["@parameters"] for c in commands if c["@code"] == 201],
                         [[0,mapping[sid],6,2,0,0] for sid in FLOORS])
        rows[-1]["destination"] = 122
        with self.assertRaises(ValueError):
            commands_for(rows, mapping)

    def test_copies_only_the_exact_synthetic_save(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            baseline, copy = root/"before", root/"copy"
            sentinel = baseline/SAVE
            sentinel.parent.mkdir(parents=True)
            (sentinel.parent/"arbitrary.rxdata").write_bytes(b"never copy this")
            sentinel.write_bytes(b"unexpected marker")
            with self.assertRaises(ValueError):
                copy_celadon_fixture(baseline, copy)
            self.assertFalse(copy.exists())
            sentinel.write_bytes(b"test save marker; not actual game data")
            copy_celadon_fixture(baseline, copy)
            self.assertEqual((copy/SAVE).read_bytes(), sentinel.read_bytes())
            self.assertEqual(list((copy/SAVE).parent.iterdir()), [copy/SAVE])

    def test_vending_records_pure_numeric_money_operands(self):
        out = vending_controls({"commands":[
            {"code":111,"parameters":[7,200,0],"indent":2},
            {"code":125,"parameters":[1,0,200],"indent":3},
            {"code":125,"parameters":[1,1,9],"indent":3},
        ]}, ["$player.money -= 300; unrelated()"])
        self.assertEqual(out, [
            {"operation":"native_gold_condition","operand":200,"at_least":True,"indent":2},
            {"operation":"native_gold_change","operand":200,"increase":False,"indent":3},
            {"operation":"typed_money_operand","operator":"-=","amount":300},
        ])

    def test_mansion_tea_authored_only_when_missing_and_proven(self):
        witness = {"services":[{"source":128,"event":1,"page":1,"at":[2,9],"conditions":{},
                                 "trigger":0,"rewards":[{"operation":"pbReceiveItem","item_or_species":"TEA"}]}]}
        with TemporaryDirectory() as folder:
            root = Path(folder)
            (root/"PBS").mkdir()
            base = root/"PBS/items.txt"
            base.write_text("[BICYCLE]\nFlags = KeyItem\nPocket = 8\n", encoding="utf8")
            with self.assertRaises(ValueError):
                ensure_tea_item(root, {"services":[]})
            out = root/"PBS/items_kanto.txt"
            self.assertFalse(out.exists())
            self.assertTrue(ensure_tea_item(root, witness))
            self.assertFalse(ensure_tea_item(root, witness))
            self.assertIn("Pocket = 8", out.read_text("utf8"))
            self.assertEqual(out.read_text("utf8").count("[TEA]"), 1)
            self.assertNotIn("[TEA]", base.read_text("utf8"))

    def test_released_android_approach_stage_is_in_source_receipt(self):
        source = {"source_update":{"stage":"K06_APPROACH"}}
        check_approach_stamp({}, android_base=source)
        check_approach_stamp({"content_stage":"K06_APPROACH"})
        with self.assertRaises(ValueError):
            check_approach_stamp({})
        with self.assertRaises(ValueError):
            check_approach_stamp({}, android_base={"source_update":None})
        with self.assertRaises(ValueError):
            check_approach_stamp({"content_stage":"OTHER"}, android_base=source)

    def test_map_marshal_reencoding_keeps_strict_native_fields(self):
        from k06_windows_services import semantic_map_fields, verify_celadon_map
        from pilot import EVENT_CLASSES, RubyObject, command, write_map
        from hashlib import sha256

        with TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            path = root/"Map277.rxdata"
            events = {1: RubyObject("RPG::Event", {"@x":4, "@y":10,
                      "@list":[command(201,0,379,49,35,0,0)]})}
            fields = {"@width":20, "@height":15, "@events":events}
            write_map(path,RubyObject("RPG::Map",fields),EVENT_CLASSES)
            old = sha256(path.read_bytes()).hexdigest()
            semantic = semantic_map_fields(path)
            write_map(path,RubyObject("RPG::Map",dict(reversed(list(fields.items())))),EVENT_CLASSES)
            self.assertNotEqual(sha256(path.read_bytes()).hexdigest(),old)
            verify_celadon_map(root,path.name,old,semantic)
            events[1].attrs["@x"] = 5
            write_map(path,RubyObject("RPG::Map",fields),EVENT_CLASSES)
            with self.assertRaisesRegex(ValueError,"event:1"):
                verify_celadon_map(root,path.name,old,semantic)
