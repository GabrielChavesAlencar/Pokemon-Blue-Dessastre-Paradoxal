from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts/regions"))
from audit_k06_celadon_services import script_groups, typed_services, vending_controls
from build_k06_celadon_services import CANDIDATES, FLOORS, allocate, commands_for, copy_celadon_fixture, SAVE


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
