from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts/regions"))
from audit_k06_celadon_services import script_groups, typed_services


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
            "rewards":[],"interaction_calls":[]})

    def test_dynamic_shop_is_marked_for_review_and_rewards_are_symbols(self):
        row=typed_services("pbPokemonMart([:POTION, eval('unreviewed')]); pbReceiveItem(:COINCASE)")
        self.assertEqual(row["shops"],[{"literal":False,"items":[]}])
        self.assertEqual(row["rewards"],[{"operation":"pbReceiveItem","item_or_species":"COINCASE"}])
