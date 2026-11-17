"""U07 regression tests: symbolic events, starter mapping, replay & save isolation."""
from __future__ import annotations
import copy
import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_u07_events as u07

FILES=(u07.EVENT_FILE,u07.AREA_FILE,u07.NPC_FILE,u07.REGION_FILE)


class UnovaNuvemaContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=u07.load_json(ROOT/u07.EVENT_FILE)
        cls.areas=u07.load_json(ROOT/u07.AREA_FILE)
        cls.npcs=u07.load_json(ROOT/u07.NPC_FILE,max_size=500_000)
        cls.regions=u07.load_json(ROOT/u07.REGION_FILE,max_size=500_000)
        cls.events=u07.validate_contract(cls.data,cls.areas,cls.npcs,cls.regions)

    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix="unova-u07-")
        self.addCleanup(temp.cleanup)
        self.project=Path(temp.name)
        for path in FILES:
            output=self.project/path
            output.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(ROOT/path,output)

    def id(self,suffix):
        return "UNOVA_U07_"+suffix

    def full(self,starter="SNIVY",losses=frozenset()):
        state=u07.empty_state()
        outcomes=[]
        for event in self.events:
            suffix=event["key"].removeprefix("UNOVA_U07_")
            result=u07.apply_event(
                self.events,state,event["key"],
                starter=starter if event["kind"]=="choice" else None,
                outcome=("LOSS" if suffix in losses else "WIN") if event["kind"]=="battle" else None,
            )
            state=result["state"]
            outcomes.append(result)
        return state,outcomes

    def edit_contract(self,modify):
        altered=copy.deepcopy(self.data)
        modify(altered)
        with self.assertRaises(ValueError):
            u07.validate_contract(altered,self.areas,self.npcs,self.regions)

    def event(self,doc,key):
        return next(v for v in doc["events"] if v["key"]==self.id(key))

    def test_01_exactly_thirteen_planned_events(self):
        self.assertEqual(len(self.events),13)
        self.assertEqual(tuple(e["key"] for e in self.events),u07.EVENT_KEYS)
        self.assertFalse(self.data["can_install"])
        self.assertFalse(self.data["game_exe_tested"])

    def test_02_no_mapids_and_not_installed(self):
        for e in self.events:
            self.assertIsNone(e["map_id"])
            self.assertIsNone(e["event_id"])
            self.assertIsNone(e["coordinates"])
            self.assertFalse(e["installed"])
            self.assertFalse(e["game_exe_tested"])

    def test_03_three_initials_and_rival_mapping(self):
        for chosen,cheren,bianca in (
            ("SNIVY","TEPIG","OSHAWOTT"),
            ("TEPIG","OSHAWOTT","SNIVY"),
            ("OSHAWOTT","SNIVY","TEPIG"),
        ):
            with self.subTest(chosen=chosen):
                result=u07.apply_event(self.events,u07.empty_state(),
                                       self.id("STARTER_GIFT"),starter=chosen)
                self.assertEqual(result["state"]["starter"],chosen)
                self.assertEqual(result["state"]["rival_starters"],
                                 {"CHEREN":cheren,"BIANCA":bianca})

    def test_04_wrong_initial_choice_blocked(self):
        with self.assertRaises(ValueError):
            u07.apply_event(self.events,u07.empty_state(),
                            self.id("STARTER_GIFT"),starter="PIKACHU")

    def test_05_missing_choice_blocked(self):
        with self.assertRaises(ValueError):
            u07.apply_event(self.events,u07.empty_state(),self.id("STARTER_GIFT"))

    def test_06_cannot_skip_to_juniper(self):
        with self.assertRaises(ValueError):
            u07.apply_event(self.events,u07.empty_state(),
                            self.id("JUNIPER_LAB_POKEDEX"))

    def test_07_bianca_battle_can_advance_after_loss(self):
        start=u07.apply_event(self.events,u07.empty_state(),
                              self.id("STARTER_GIFT"),starter="SNIVY")["state"]
        result=u07.apply_event(self.events,start,self.id("BIANCA_FIRST_BATTLE"),outcome="LOSS")
        self.assertIn(self.id("BIANCA_FIRST_BATTLE"),result["state"]["completed_events"])
        self.assertEqual(result["status"],"SIMULATED_EVENT_COMPLETED_NOT_INSTALLED")

    def test_08_cheren_battle_can_advance_after_loss(self):
        start,_=self.full(losses={"CHEREN_FIRST_BATTLE"})
        self.assertEqual(len(start["completed_events"]),13)
        self.assertIn(self.id("CHEREN_FIRST_BATTLE"),start["completed_events"])

    def test_09_n_battle_loss_must_retry(self):
        state=u07.empty_state()
        for event in self.events:
            if event["key"]==self.id("N_FIRST_BATTLE"):
                break
            result=u07.apply_event(self.events,state,event["key"],
                                   starter="SNIVY" if event["kind"]=="choice" else None,
                                   outcome="WIN" if event["kind"]=="battle" else None)
            state=result["state"]
        attempt=u07.apply_event(self.events,state,self.id("N_FIRST_BATTLE"),outcome="LOSS")
        self.assertEqual(attempt["status"],"BATTLE_LOST_RETRY_REQUIRED")
        self.assertEqual(attempt["state"],state)
        self.assertEqual(attempt["effects"],[])
        with self.assertRaises(ValueError):
            u07.apply_event(self.events,state,self.id("ROUTE2_PASSAGE"))

    def test_10_n_win_unlocks_story_flag_not_real_map(self):
        state,effects=self.full()
        self.assertIn(self.id("N_FIRST_BATTLE"),state["completed_events"])
        self.assertEqual(state["rewards"]["STORY_TOKEN:ROUTE_2_PASSAGE_READY"],1)
        self.assertFalse(any(e.get("kind")=="INSTALL_MAP" for step in effects for e in step["effects"]))

    def test_11_pokedex_single_reward(self):
        state,_=self.full()
        self.assertEqual(state["rewards"]["KEY_ITEM:POKEDEX"],1)

    def test_12_xtransceiver_single_reward(self):
        state,_=self.full()
        self.assertEqual(state["rewards"]["KEY_ITEM:XTRANSCEIVER"],1)

    def test_13_town_map_single_reward(self):
        state,_=self.full()
        self.assertEqual(state["rewards"]["KEY_ITEM:TOWN_MAP"],1)

    def test_14_route_one_five_pokeballs_once(self):
        state,_=self.full()
        self.assertEqual(state["rewards"]["ITEM:POKE_BALL"],5)

    def test_15_all_events_idempotent(self):
        state,_=self.full()
        for row in self.events:
            repeated=u07.apply_event(self.events,state,row["key"])
            self.assertEqual(repeated["status"],"ALREADY_COMPLETED_NO_EFFECT")
            self.assertEqual(repeated["state"],state)
            self.assertEqual(repeated["effects"],[])

    def test_16_cannot_change_starter_after_selection(self):
        state=u07.apply_event(self.events,u07.empty_state(),
                              self.id("STARTER_GIFT"),starter="TEPIG")["state"]
        with self.assertRaises(ValueError):
            u07.apply_event(self.events,state,self.id("STARTER_GIFT"),starter="SNIVY")

    def test_17_save_reload_roundtrip_idempotent(self):
        state,_=self.full("OSHAWOTT")
        before=json.loads(json.dumps(state))
        u07.validate_state(before,self.events)
        self.assertEqual(before,state)
        again=u07.apply_event(self.events,before,self.id("JUNIPER_CAPTURE_TUTORIAL"))
        self.assertEqual(again["state"]["rewards"]["ITEM:POKE_BALL"],5)
        self.assertEqual(again["effects"],[])

    def test_18_other_region_state_rejected(self):
        state=u07.empty_state()
        state["region"]="KANTO"
        with self.assertRaises(ValueError):
            u07.validate_state(state,self.events)

    def test_19_foreign_flag_rejected(self):
        state,_=self.full()
        state["completed_events"].append("KANTO_OAK_PACKAGE")
        with self.assertRaises(ValueError):
            u07.validate_state(state,self.events)

    def test_20_duplicate_flag_rejected(self):
        state,_=self.full()
        state["completed_events"].append(self.id("STARTER_GIFT"))
        with self.assertRaises(ValueError):
            u07.validate_state(state,self.events)

    def test_21_skip_flag_rejected(self):
        state,_=self.full()
        state["completed_events"].pop(3)
        with self.assertRaises(ValueError):
            u07.validate_state(state,self.events)

    def test_22_forged_reward_rejected(self):
        state,_=self.full()
        state["rewards"]["ITEM:POKE_BALL"]=9999
        with self.assertRaises(ValueError):
            u07.validate_state(state,self.events)

    def test_23_missing_reward_rejected(self):
        state,_=self.full()
        del state["rewards"]["KEY_ITEM:POKEDEX"]
        with self.assertRaises(ValueError):
            u07.validate_state(state,self.events)

    def test_24_missing_starter_after_choice_rejected(self):
        state,_=self.full()
        state["starter"]=None
        with self.assertRaises(ValueError):
            u07.validate_state(state,self.events)

    def test_25_rival_mapping_forged_rejected(self):
        state,_=self.full()
        state["rival_starters"]["CHEREN"]="SNIVY"
        with self.assertRaises(ValueError):
            u07.validate_state(state,self.events)

    def test_26_unexpected_save_format_property_rejected(self):
        state=u07.empty_state()
        state["gameSave"]=True
        with self.assertRaises(ValueError):
            u07.validate_state(state,self.events)

    def test_27_outcome_in_dialogue_rejected(self):
        state,_=self.full()
        # Start a separate partial progression.
        current=u07.empty_state()
        for row in self.events[:4]:
            res=u07.apply_event(self.events,current,row["key"],
                                starter="SNIVY" if row["kind"]=="choice" else None,
                                outcome="WIN" if row["kind"]=="battle" else None)
            current=res["state"]
        with self.assertRaises(ValueError):
            u07.apply_event(self.events,current,self.id("VISIT_BIANCA_HOME"),outcome="WIN")

    def test_28_missing_battle_result_rejected(self):
        state=u07.apply_event(self.events,u07.empty_state(),
                              self.id("STARTER_GIFT"),starter="SNIVY")["state"]
        with self.assertRaises(ValueError):
            u07.apply_event(self.events,state,self.id("BIANCA_FIRST_BATTLE"))

    def test_29_unknown_event_rejected(self):
        with self.assertRaises(ValueError):
            u07.apply_event(self.events,u07.empty_state(),"UNOVA_U07_INVENTED")

    def test_30_mapid_forged_in_contract_rejected(self):
        self.edit_contract(lambda c:self.event(c,"STARTER_GIFT").update(map_id=9001))

    def test_31_installed_flag_forged_in_contract_rejected(self):
        self.edit_contract(lambda c:self.event(c,"JUNIPER_LAB_POKEDEX").update(installed=True))

    def test_32_reward_inflation_rejected(self):
        self.edit_contract(lambda c:self.event(c,"JUNIPER_CAPTURE_TUTORIAL")["grants_once"][0].update(amount=999))

    def test_33_wrong_dependency_order_rejected(self):
        self.edit_contract(lambda c:self.event(c,"CHEREN_FIRST_BATTLE").update(
            requires=[self.id("STARTER_GIFT")]))

    def test_34_wrong_n_battle_loss_policy_rejected(self):
        self.edit_contract(lambda c:self.event(c,"N_FIRST_BATTLE").update(
            battle_policy="ADVANCE_ON_LOSS"))

    def test_35_wrong_npc_reference_rejected(self):
        self.edit_contract(lambda c:self.event(c,"BIANCA_FIRST_BATTLE").update(
            actor_npc_key="UNOVA_NPC_GHETSIS"))

    def test_36_reordered_events_rejected(self):
        self.edit_contract(lambda c:c["events"].reverse())

    def test_37_overridden_rival_initial_rejected(self):
        self.edit_contract(lambda c:c["rival_starter_by_player"]["SNIVY"].update(
            CHEREN="OSHAWOTT"))

    def test_38_registry_unova_playable_falsely_rejected(self):
        registry=copy.deepcopy(self.regions)
        registry["regions"]["UNOVA"]["status"]="playable"
        with self.assertRaises(ValueError):
            u07.validate_contract(self.data,self.areas,self.npcs,registry)

    def test_39_demo_never_writes_game_data(self):
        result=u07.demo(self.events,"TEPIG")
        self.assertEqual(len(result["steps"]),13)
        self.assertEqual(result["final_state"]["starter"],"TEPIG")
        self.assertFalse(result["can_install"])
        self.assertFalse((self.project/"game").exists())

    def test_40_private_report_is_idempotent_and_outside_game(self):
        result={"status":"CONTRACTS_VALIDATED_NOT_INSTALLED","can_install":False}
        path=u07.write_private(self.project,result)
        first=path.read_bytes()
        u07.write_private(self.project,result)
        self.assertEqual(first,path.read_bytes())
        with self.assertRaises(ValueError):
            u07.write_private(self.project,{"status":"FALSIFIED"})
        self.assertFalse((self.project/"game").exists())

    def test_41_symlink_report_does_not_overwrite(self):
        work=self.project/".blue-work"
        external=self.project/"outside"
        external.mkdir()
        try:
            work.symlink_to(external,target_is_directory=True)
        except OSError:
            self.skipTest("symlinks unavailable")
        with self.assertRaises(ValueError):
            u07.write_private(self.project,{"ok":True})
        self.assertEqual(list(external.iterdir()),[])

    def test_42_cli_simulation_validated(self):
        stdout=io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(io.StringIO()):
            code=u07.main(["--project",str(self.project),"--simulate-demo",
                           "--starter","OSHAWOTT","--write"])
        self.assertEqual(code,0)
        result=json.loads(stdout.getvalue())
        self.assertEqual(result["event_count"],13)
        self.assertEqual(result["simulation"]["starter"],"OSHAWOTT")
        self.assertEqual(result["simulation"]["rewards"]["ITEM:POKE_BALL"],5)
        self.assertFalse((self.project/"game").exists())

    def test_43_no_pokemon_item_given_to_real_game(self):
        state,actions=self.full()
        types={effect["kind"] for x in actions for effect in x["effects"]}
        self.assertNotIn("GAME_INVENTORY_ADD",types)
        self.assertNotIn("GAME_POKEMON_ADD",types)
        self.assertNotIn("TRANSFER_PLAYER",types)
        self.assertEqual(state["region"],"UNOVA")

    def test_44_bianca_battle_uses_weak_type_starter(self):
        state=u07.empty_state()
        state=u07.apply_event(self.events,state,self.id("STARTER_GIFT"),starter="SNIVY")["state"]
        outcome=u07.apply_event(self.events,state,self.id("BIANCA_FIRST_BATTLE"),outcome="WIN")
        battle=[x for x in outcome["effects"] if x["kind"]=="BATTLE_OUTCOME_REFERENCE_ONLY"]
        self.assertEqual(battle[0]["opponent_starter_reference"],"OSHAWOTT")

    def test_45_cheren_battle_uses_strong_type_starter(self):
        state=u07.empty_state()
        for row in self.events[:2]:
            state=u07.apply_event(self.events,state,row["key"],
                                  starter="SNIVY" if row["kind"]=="choice" else None,
                                  outcome="WIN" if row["kind"]=="battle" else None)["state"]
        out=u07.apply_event(self.events,state,self.id("CHEREN_FIRST_BATTLE"),outcome="WIN")
        battle=[x for x in out["effects"] if x["kind"]=="BATTLE_OUTCOME_REFERENCE_ONLY"]
        self.assertEqual(battle[0]["opponent_starter_reference"],"TEPIG")


if __name__=="__main__":
    unittest.main()
