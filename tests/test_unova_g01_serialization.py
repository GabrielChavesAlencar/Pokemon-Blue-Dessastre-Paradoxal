"""G01.4: synthetic-only serialization and explicit legacy migration regression suite."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/regions"))
import audit_unova_g01_chapter_machine as machine
import audit_unova_g01_reentry_ledger as ledger
import audit_unova_g01_serialization as codec

class UnovaG014Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx=codec.load_project()
        cls.c,cls.rules,cls.policy,cls.events,_=cls.ctx

    def initial(self):
        return ledger.initial(self.c)

    def begin(self):
        return ledger.apply(self.initial(),self.c,self.rules,self.policy,self.events,
                            "begin")["envelope"]

    @staticmethod
    def event_args(event,starter="SNIVY",first_rival_loss=False):
        kw={"event_key":event["key"]}
        if event["kind"]=="choice":kw["starter_choice"]=starter
        if event["battle_policy"] in {"ADVANCE_ON_LOSS","WIN_REQUIRED"}:
            kw["outcome"]="LOSS" if first_rival_loss and event["battle_policy"]=="ADVANCE_ON_LOSS" else "WIN"
        return kw

    def at_events(self,count,starter="SNIVY",first_rival_loss=False):
        env=self.begin()
        for event in self.events[:count]:
            env=ledger.apply(env,self.c,self.rules,self.policy,self.events,
                 "record_u07",**self.event_args(event,starter,first_rival_loss))["envelope"]
        return env

    def at_chapter(self,index,completed=False):
        if index==0:return self.initial()
        env=self.at_events(13)
        for ch in range(1,index+1):
            if ch>1:
                env=ledger.apply(env,self.c,self.rules,self.policy,self.events,
                                 "advance",chapter_key=self.c["chapters"][ch-1]["key"])["envelope"]
            if completed or ch<index:
                env=ledger.apply(env,self.c,self.rules,self.policy,self.events,
                                 "complete",chapter_key=self.c["chapters"][ch]["key"],
                                 simulation_gate=machine.SIMULATION_GATE)["envelope"]
        return env

    def encode(self,env):
        return codec.encode_current(env,self.ctx)

    def decode(self,bytes_):
        return codec.decode_current(bytes_,self.ctx)

    def doc(self,env=None):
        return json.loads(self.encode(self.begin() if env is None else env))

    def tamper_v1(self,modify,env=None,rehash=False,canonical=True):
        d=self.doc(env)
        modify(d)
        if rehash:
            d["canonical_sha256"]=hashlib.sha256(codec._canonical(d["payload"])).hexdigest()
        raw=codec._canonical(d) if canonical else json.dumps(d).encode()
        with self.assertRaises(ValueError):
            self.decode(raw)

    def legacy(self,env=None):
        return json.loads(codec.make_legacy_fixture(
            self.begin() if env is None else env,self.ctx))

    def migrate(self,value):
        raw=codec._canonical(value) if isinstance(value,dict) else value
        return codec.migrate_legacy(raw,self.ctx,acknowledge_fixture_only=True)

    def tamper_legacy(self,modify,env=None):
        doc=self.legacy(env)
        modify(doc)
        with self.assertRaises(ValueError):
            self.migrate(doc)

    def invalid_policy(self,modify):
        p=copy.deepcopy(self.ctx[4])
        modify(p)
        with self.assertRaises(ValueError):
            codec.validate_policy(p,self.c,self.rules,self.policy,self.events)

    def test_01_codec_version_and_policy(self):
        r=codec.validate_policy(self.ctx[4],self.c,self.rules,self.policy,self.events)
        self.assertEqual(r["current_storage_version"],1)
        self.assertEqual(r["explicit_legacy_fixture_version"],0)
        self.assertFalse(r["native_save_compatible"])

    def test_02_initial_state_round_trip(self):
        env=self.initial()
        self.assertEqual(self.decode(self.encode(env)),env)

    def test_03_first_chapter_active_round_trip(self):
        env=self.begin()
        self.assertEqual(self.decode(self.encode(env)),env)

    def test_04_partial_u07_round_trip(self):
        self.assertEqual(self.decode(self.encode(self.at_events(5))),self.at_events(5))

    def test_05_all_thirteen_u07_round_trip(self):
        env=self.at_events(13)
        self.assertEqual(len(self.decode(self.encode(env))["event_receipts"]),13)

    def test_06_chapter_one_completed_round_trip(self):
        env=self.at_chapter(1,completed=True)
        self.assertEqual(self.decode(self.encode(env)),env)

    def test_07_chapter_two_active_round_trip(self):
        env=self.at_chapter(2)
        self.assertEqual(self.decode(self.encode(env)),env)

    def test_08_chapter_four_completed_round_trip(self):
        env=self.at_chapter(4,completed=True)
        self.assertEqual(self.decode(self.encode(env)),env)

    def test_09_terminal_postgame_complete_round_trip(self):
        env=self.at_chapter(12,completed=True)
        self.assertEqual(self.decode(self.encode(env)),env)

    def test_10_each_chapter_active_and_completed_round_trip(self):
        for i in range(1,13):
            with self.subTest(chapter=i):
                for completed in (False,True):
                    env=self.at_chapter(i,completed=completed)
                    self.assertEqual(self.decode(self.encode(env)),env)

    def test_11_all_u07_prefixes_round_trip(self):
        for count in range(0,14):
            with self.subTest(count=count):
                env=self.at_events(count)
                self.assertEqual(self.decode(self.encode(env)),env)

    def test_12_all_starter_options_round_trip(self):
        for starter in ("SNIVY","TEPIG","OSHAWOTT"):
            with self.subTest(starter=starter):
                env=self.at_events(13,starter=starter)
                self.assertEqual(self.decode(self.encode(env)),env)

    def test_13_rival_loss_receipts_round_trip(self):
        env=self.at_events(13,first_rival_loss=True)
        loaded=self.decode(self.encode(env))
        self.assertEqual(loaded["event_receipts"][1]["outcome"],"LOSS")
        self.assertEqual(loaded["event_receipts"][2]["outcome"],"LOSS")

    def test_14_unique_reward_intents_preserved(self):
        env=self.at_events(13)
        loaded=self.decode(self.encode(env))
        self.assertEqual(loaded["reward_intents"],{
            "KEY_ITEM:XTRANSCEIVER":1,"KEY_ITEM:POKEDEX":1,
            "KEY_ITEM:TOWN_MAP":1,"ITEM:POKE_BALL":5,
            "STORY_TOKEN:ROUTE_2_PASSAGE_READY":1})

    def test_15_stable_deterministic_encoding(self):
        env=self.at_events(13)
        self.assertEqual(self.encode(env),self.encode(copy.deepcopy(env)))

    def test_16_payload_mapping_order_does_not_change_encoding(self):
        env=self.at_events(13)
        reordered={k:env[k] for k in reversed(tuple(env))}
        self.assertEqual(self.encode(reordered),self.encode(env))

    def test_17_canonical_encoding_no_padding_or_bom(self):
        data=self.encode(self.initial())
        self.assertEqual(data[:1],b"{")
        self.assertFalse(data.startswith(b"\xef\xbb\xbf"))
        self.assertNotIn(b"\\n",data)
        self.assertNotIn(b": ",data)

    def test_18_sha256_matches_canonical_payload(self):
        doc=self.doc(self.at_events(9))
        digest=hashlib.sha256(codec._canonical(doc["payload"])).hexdigest()
        self.assertEqual(doc["canonical_sha256"],digest)

    def test_19_encoding_does_not_mutate_input(self):
        env=self.at_events(13)
        before=copy.deepcopy(env)
        self.encode(env)
        self.assertEqual(env,before)

    def test_20_decoding_returns_fresh_deep_copies(self):
        encoded=self.encode(self.at_events(4))
        first=self.decode(encoded);second=self.decode(encoded)
        first["reward_intents"]["KEY_ITEM:XTRANSCEIVER"]=999
        self.assertEqual(second["reward_intents"]["KEY_ITEM:XTRANSCEIVER"],1)

    def test_21_empty_binary_input_blocked(self):
        with self.assertRaises(ValueError):self.decode(b"")

    def test_22_string_input_is_not_accepted_as_binary_save(self):
        with self.assertRaises(ValueError):self.decode("{}")

    def test_23_null_input_blocked(self):
        with self.assertRaises(ValueError):self.decode(None)

    def test_24_oversized_document_blocked(self):
        with self.assertRaises(ValueError):self.decode(b"x"*(codec.LIMIT+1))

    def test_25_invalid_utf8_blocked(self):
        with self.assertRaises(ValueError):self.decode(b"\xff\xfe\xff")

    def test_26_utf8_bom_blocked(self):
        with self.assertRaises(ValueError):self.decode(b"\xef\xbb\xbf"+self.encode(self.initial()))

    def test_27_truncated_json_blocked(self):
        with self.assertRaises(ValueError):self.decode(self.encode(self.initial())[:-3])

    def test_28_json_array_not_document(self):
        with self.assertRaises(ValueError):self.decode(b"[]")

    def test_29_json_null_not_document(self):
        with self.assertRaises(ValueError):self.decode(b"null")

    def test_30_duplicate_top_level_key_rejected(self):
        with self.assertRaises(ValueError):self.decode(b'{"format":"a","format":"b"}')

    def test_31_duplicate_nested_key_rejected(self):
        with self.assertRaises(ValueError):self.decode(b'{"payload":{"scope":"a","scope":"b"}}')

    def test_32_nan_not_valid_json(self):
        with self.assertRaises(ValueError):self.decode(b'{"payload":{"x":NaN}}')

    def test_33_infinity_not_valid_json(self):
        with self.assertRaises(ValueError):self.decode(b'{"payload":{"x":Infinity}}')

    def test_34_wrong_format_blocked(self):
        self.tamper_v1(lambda d:d.update(format="NATIVE_GAME_SAVE"))

    def test_35_storage_version_two_blocked(self):
        self.tamper_v1(lambda d:d.update(storage_version=2))

    def test_36_legacy_version_requires_explicit_migration(self):
        legacy=codec.make_legacy_fixture(self.begin(),self.ctx)
        with self.assertRaises(ValueError):self.decode(legacy)

    def test_37_storage_version_boolean_blocked(self):
        self.tamper_v1(lambda d:d.update(storage_version=True))

    def test_38_state_schema_version_two_blocked(self):
        self.tamper_v1(lambda d:d.update(state_schema_version=2))

    def test_39_ledger_schema_version_two_blocked(self):
        self.tamper_v1(lambda d:d.update(ledger_schema_version=2))

    def test_40_cross_region_document_blocked(self):
        self.tamper_v1(lambda d:d.update(region="KANTO"))

    def test_41_cross_campaign_document_blocked(self):
        self.tamper_v1(lambda d:d.update(campaign="BLACK_BW"))

    def test_42_native_scope_rejected(self):
        self.tamper_v1(lambda d:d.update(scope="NATIVE_GAME_SAVE"))

    def test_43_missing_integrity_hash_rejected(self):
        self.tamper_v1(lambda d:d.pop("canonical_sha256"))

    def test_44_extra_native_save_attribute_rejected(self):
        self.tamper_v1(lambda d:d.update(game_save_slot=1))

    def test_45_bad_hex_digest_rejected(self):
        self.tamper_v1(lambda d:d.update(canonical_sha256="bad"))

    def test_46_uppercase_hex_digest_rejected(self):
        self.tamper_v1(lambda d:d.update(canonical_sha256="A"*64))

    def test_47_single_byte_corruption_rejected(self):
        self.tamper_v1(lambda d:d["payload"]["state"].update(current_chapter="UNOVA_CH99"))

    def test_48_rehashed_forged_reward_rejected(self):
        self.tamper_v1(lambda d:d["payload"]["reward_intents"].update({"ITEM:POKE_BALL":500}),
                        env=self.at_events(13),rehash=True)

    def test_49_rehashed_orphan_receipt_rejected(self):
        self.tamper_v1(lambda d:d["payload"]["event_receipts"].pop(),
                        env=self.at_events(8),rehash=True)

    def test_50_rehashed_fake_mapid_rejected(self):
        self.tamper_v1(lambda d:d["payload"]["state"]["checkpoint"].update(map_id=518),
                        rehash=True)

    def test_51_rehashed_future_chapter_rejected(self):
        self.tamper_v1(lambda d:d["payload"]["state"].update(current_chapter="UNOVA_CH10_LEAGUE"),
                        rehash=True)

    def test_52_rehashed_future_state_schema_rejected(self):
        self.tamper_v1(lambda d:d["payload"]["state"].update(schema_version=2),
                        rehash=True)

    def test_53_rehashed_native_save_scope_rejected(self):
        self.tamper_v1(lambda d:d["payload"].update(scope="NATIVE_GAME_SAVE"),
                        rehash=True)

    def test_54_rehashed_duplicate_receipt_rejected(self):
        env=self.at_events(4)
        self.tamper_v1(lambda d:d["payload"]["event_receipts"].append(
            copy.deepcopy(d["payload"]["event_receipts"][-1])),
            env=env,rehash=True)

    def test_55_alternate_whitespace_canonical_blocked(self):
        d=self.doc()
        with self.assertRaises(ValueError):
            self.decode(json.dumps(d,indent=2,sort_keys=True).encode())

    def test_56_newline_suffix_blocked(self):
        with self.assertRaises(ValueError):self.decode(self.encode(self.initial())+b"\n")

    def test_57_unicode_escape_instead_of_canonical_blocked(self):
        data=self.encode(self.at_events(13))
        # Alternate escaped formatting remains valid JSON but is not canonical.
        d=json.loads(data)
        with self.assertRaises(ValueError):
            self.decode(json.dumps(d,sort_keys=True,separators=(",",":"),ensure_ascii=True).encode())

    def test_58_missing_v1_payload_blocked(self):
        self.tamper_v1(lambda d:d.pop("payload"))

    def test_59_legacy_migration_requires_explicit_acknowledgement(self):
        raw=codec.make_legacy_fixture(self.begin(),self.ctx)
        with self.assertRaises(ValueError):codec.migrate_legacy(raw,self.ctx)
        with self.assertRaises(ValueError):codec.migrate_legacy(raw,self.ctx,acknowledge_fixture_only=1)

    def test_60_legacy_initial_fixture_migrates(self):
        env=self.initial()
        self.assertEqual(self.decode(self.migrate(self.legacy(env))),env)

    def test_61_legacy_active_first_chapter_migrates(self):
        env=self.begin()
        self.assertEqual(self.decode(self.migrate(self.legacy(env))),env)

    def test_62_legacy_partial_events_migrate(self):
        env=self.at_events(7)
        self.assertEqual(self.decode(self.migrate(self.legacy(env))),env)

    def test_63_legacy_complete_first_chapter_migrates(self):
        env=self.at_chapter(1,completed=True)
        self.assertEqual(self.decode(self.migrate(self.legacy(env))),env)

    def test_64_legacy_chapter_two_migrates(self):
        env=self.at_chapter(2)
        self.assertEqual(self.decode(self.migrate(self.legacy(env))),env)

    def test_65_legacy_postgame_complete_migrates(self):
        env=self.at_chapter(12,completed=True)
        self.assertEqual(self.decode(self.migrate(self.legacy(env))),env)

    def test_66_legacy_starters_migrate_from_real_events(self):
        for starter in ("SNIVY","TEPIG","OSHAWOTT"):
            with self.subTest(starter=starter):
                env=self.at_events(13,starter=starter)
                self.assertEqual(self.decode(self.migrate(self.legacy(env))),env)

    def test_67_legacy_all_u07_prefixes_migrate(self):
        for n in range(0,14):
            with self.subTest(count=n):
                env=self.at_events(n)
                self.assertEqual(self.decode(self.migrate(self.legacy(env))),env)

    def test_68_legacy_all_chapter_beginnings_migrate(self):
        for chapter in range(1,13):
            with self.subTest(chapter=chapter):
                env=self.at_chapter(chapter)
                self.assertEqual(self.decode(self.migrate(self.legacy(env))),env)

    def test_69_legacy_all_chapter_completions_migrate(self):
        for chapter in range(1,13):
            with self.subTest(chapter=chapter):
                env=self.at_chapter(chapter,completed=True)
                self.assertEqual(self.decode(self.migrate(self.legacy(env))),env)

    def test_70_legacy_rival_loss_provenance_retained(self):
        env=self.at_events(13,first_rival_loss=True)
        self.assertEqual(self.decode(self.migrate(self.legacy(env))),env)

    def test_71_legacy_cross_region_rejected(self):
        self.tamper_legacy(lambda d:d.update(region="SINNOH"))

    def test_72_legacy_wrong_campaign_rejected(self):
        self.tamper_legacy(lambda d:d.update(campaign="BLACK_BW"))

    def test_73_legacy_false_native_scope_rejected(self):
        self.tamper_legacy(lambda d:d.update(scope="GAME_SAVE"))

    def test_74_legacy_version_one_rejected_by_migrator(self):
        self.tamper_legacy(lambda d:d.update(storage_version=1))

    def test_75_legacy_version_boolean_rejected(self):
        self.tamper_legacy(lambda d:d.update(storage_version=False))

    def test_76_legacy_unrecognized_format_rejected(self):
        self.tamper_legacy(lambda d:d.update(format="OLD_RXDATA_SAVE"))

    def test_77_legacy_missing_explicit_gate_rejected(self):
        self.tamper_legacy(lambda d:d.pop("migration_gate"))

    def test_78_legacy_wrong_gate_rejected(self):
        self.tamper_legacy(lambda d:d.update(migration_gate="MIGRATE_REAL_SAVE"))

    def test_79_legacy_additional_field_rejected(self):
        self.tamper_legacy(lambda d:d.update(save_path="C:/Users/Player/Saves"))

    def test_80_legacy_event_out_of_order_rejected(self):
        self.tamper_legacy(lambda d:d["events"].reverse(),env=self.at_events(4))

    def test_81_legacy_duplicate_event_rejected(self):
        self.tamper_legacy(lambda d:d["events"].append(copy.deepcopy(d["events"][-1])),
                           env=self.at_events(4))

    def test_82_legacy_missing_event_rejected(self):
        self.tamper_legacy(lambda d:d["events"].pop(0),env=self.at_events(4))

    def test_83_legacy_unknown_event_rejected(self):
        self.tamper_legacy(lambda d:d["events"][0].update(event_key="UNKNOWN"),
                           env=self.at_events(4))

    def test_84_legacy_mismatched_starter_rejected(self):
        self.tamper_legacy(lambda d:d["events"][0].update(starter_choice="TEPIG"),
                           env=self.at_events(4))

    def test_85_legacy_n_loss_rejected(self):
        self.tamper_legacy(lambda d:d["events"][11].update(outcome="LOSS"),
                           env=self.at_events(12))

    def test_86_legacy_rival_outcome_modified_rejected(self):
        self.tamper_legacy(lambda d:d["events"][1].update(outcome="LOSS"),
                           env=self.at_events(4))

    def test_87_legacy_reward_amount_modified_rejected(self):
        self.tamper_legacy(lambda d:d["reward_intents"].update({"ITEM:POKE_BALL":15}),
                           env=self.at_events(13))

    def test_88_legacy_added_reward_rejected(self):
        self.tamper_legacy(lambda d:d["reward_intents"].update({"KEY_ITEM:RARE_CANDY":1}),
                           env=self.at_events(4))

    def test_89_legacy_deleted_reward_rejected(self):
        self.tamper_legacy(lambda d:d["reward_intents"].pop("ITEM:POKE_BALL"),
                           env=self.at_events(13))

    def test_90_legacy_replay_state_flags_modified_rejected(self):
        self.tamper_legacy(lambda d:d["state"]["flags"].update({"UNOVA_FLAG_CH02_COMPLETED":True}),
                           env=self.at_events(13))

    def test_91_legacy_replay_state_mission_modified_rejected(self):
        self.tamper_legacy(lambda d:d["state"]["missions"].update({
                           "UNOVA_MISSION_CH01_BEGIN_JOURNEY":"completed"}),
                           env=self.at_events(13))

    def test_92_legacy_replay_checkpoint_modified_rejected(self):
        self.tamper_legacy(lambda d:d["state"]["checkpoint"].update(last_safe_area_key="UNOVA_ROUTE_01"),
                           env=self.at_events(13))

    def test_93_legacy_replay_fake_mapid_rejected(self):
        self.tamper_legacy(lambda d:d["state"]["checkpoint"].update(map_id=518),
                           env=self.at_events(13))

    def test_94_legacy_replay_future_chapter_rejected(self):
        self.tamper_legacy(lambda d:d["state"].update(current_chapter="UNOVA_CH11_NS_CASTLE"),
                           env=self.at_events(13))

    def test_95_legacy_replay_state_schema_zero_rejected(self):
        self.tamper_legacy(lambda d:d["state"].update(schema_version=0),
                           env=self.at_events(13))

    def test_96_forged_state_cannot_generate_legacy_fixture(self):
        env=self.begin()
        env["state"]["flags"]["UNOVA_U07_STARTER_GIFT"]=True
        with self.assertRaises(ValueError):codec.make_legacy_fixture(env,self.ctx)

    def test_97_nonreplayable_modified_checkpoint_rejected_as_legacy_fixture(self):
        env=self.at_events(13)
        env["state"]["checkpoint"]["last_safe_area_key"]="UNOVA_ROUTE_01"
        with self.assertRaises(ValueError):codec.make_legacy_fixture(env,self.ctx)

    def test_98_policy_invent_native_save_adapter_rejected(self):
        self.invalid_policy(lambda d:d.update(real_game_save_adapter=True))

    def test_99_policy_auto_migrate_rejected(self):
        self.invalid_policy(lambda d:d.update(auto_migration=True))

    def test_100_policy_new_version_rejected(self):
        self.invalid_policy(lambda d:d.update(storage_version=2))

    def test_101_policy_hash_algorithm_mutation_rejected(self):
        self.invalid_policy(lambda d:d.update(hash_algorithm="MD5"))

    def test_102_policy_expand_max_payload_rejected(self):
        self.invalid_policy(lambda d:d.update(max_payload_bytes=100000000))

    def test_103_policy_real_items_claim_rejected(self):
        self.invalid_policy(lambda d:d.update(native_items_granted=True))

    def test_104_policy_install_flag_rejected(self):
        self.invalid_policy(lambda d:d.update(can_install=True))

    def test_105_policy_wrong_fixture_version_rejected(self):
        self.invalid_policy(lambda d:d.update(explicit_legacy_storage_version=1))

    def test_106_policy_accept_future_versions_rejected(self):
        self.invalid_policy(lambda d:d.update(accepted_current_storage_versions=[1,2]))

    def test_107_policy_wrong_game_campaign_rejected(self):
        self.invalid_policy(lambda d:d.update(campaign="BLACK_BW"))

    def test_108_cli_policy_check_passes_offline(self):
        proc=subprocess.run([sys.executable,str(codec.ROOT/"scripts/regions/audit_unova_g01_serialization.py"),
                             "--check"],cwd=codec.ROOT,capture_output=True,text=True,timeout=25)
        self.assertEqual(proc.returncode,0,proc.stdout+"\n"+proc.stderr)
        report=json.loads(proc.stdout)
        self.assertEqual(report["status"],"OFFLINE_CODEC_POLICY_VALIDATED")
        self.assertFalse(report["can_install"])

    def test_109_cli_demo_roundtrip_and_migration(self):
        proc=subprocess.run([sys.executable,str(codec.ROOT/"scripts/regions/audit_unova_g01_serialization.py"),
                             "--simulate-demo"],cwd=codec.ROOT,capture_output=True,text=True,timeout=25)
        self.assertEqual(proc.returncode,0,proc.stdout+"\n"+proc.stderr)
        report=json.loads(proc.stdout)
        self.assertTrue(report["roundtrip_equal"])
        self.assertTrue(report["migration_equal"])
        self.assertFalse(report["game_exe_tested"])
        self.assertEqual(report["events"],13)
        self.assertEqual(report["reward_tokens"],5)

    def test_110_corruption_is_transactional_and_input_intact(self):
        old=self.encode(self.at_events(13))
        tampered=old[:-2]+b"xx"
        before=bytes(tampered)
        with self.assertRaises(ValueError):self.decode(tampered)
        self.assertEqual(before,tampered)

    def invalid_policy(self,modify):
        obj=copy.deepcopy(self.ctx[4])
        modify(obj)
        with self.assertRaises(ValueError):
            codec.validate_policy(obj,self.c,self.rules,self.policy,self.events)

if __name__=="__main__":
    unittest.main()
