"""CH16: negatives for Sinnoh music rights, routes, priorities and runtime."""
from __future__ import annotations
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts/music"))
from audit_sinnoh_music_ch16 import (
    FILES,GROUPS,TOP,audit,read,json_file,expected,documented
)


class SinnohCH16MusicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=json_file(FILES["catalog"])
        cls.doc=read(FILES["reference"])
        cls.blue=read(FILES["blue"])
        cls.adapter=read(FILES["adapter"])
        cls.regions=json_file(FILES["regions"])

    def check(self,catalog=None,doc=None,blue=None,adapter=None,regions=None):
        return audit(copy.deepcopy(self.catalog if catalog is None else catalog),
                     self.doc if doc is None else doc,
                     self.blue if blue is None else blue,
                     self.adapter if adapter is None else adapter,
                     copy.deepcopy(self.regions if regions is None else regions))
    def rejects(self,pattern,**changes):
        with self.assertRaisesRegex(ValueError,pattern):
            self.check(**changes)
    def modified(self):
        return copy.deepcopy(self.catalog)

    def test_46_symbolic_cues_not_audio(self):
        result=self.check()
        self.assertEqual(result["cue_count"],46)
        self.assertEqual(result["bgm_cues"],43)
        self.assertEqual(result["me_cues"],3)
        self.assertEqual(result["document_keys_matched"],45)
        self.assertEqual(result["native_bindings_verified"],0)
        self.assertFalse(result["can_install"])

    def test_cli_read_only(self):
        cp=subprocess.run([sys.executable,str(ROOT/"scripts/music/audit_sinnoh_music_ch16.py")],
                          capture_output=True,text=True)
        self.assertEqual(cp.returncode,0,cp.stderr)
        self.assertFalse(json.loads(cp.stdout)["copyright_cleared"])

    def test_groups_cover_battles_towns_routes_caves(self):
        report=self.check()
        self.assertEqual(report["by_scope"],
                         {k:len(v) for k,v in GROUPS.items()})
        self.assertTrue(any(x["key"]=="SINNOH_CHAMPION" and
                            x["scope"]=="battle" for x in self.catalog["cues"]))
        self.assertTrue(any(x["key"]=="SINNOH_GALACTIC_HQ" and
                            x["scope"]=="cave" for x in self.catalog["cues"]))

    def test_hall_of_fame_has_distinct_bgm_me_pending(self):
        cues={c["key"]:c for c in self.catalog["cues"]}
        a,b=cues["SINNOH_HALL_OF_FAME_BGM"],cues["SINNOH_HALL_OF_FAME_ME"]
        self.assertEqual(a["source_key"],b["source_key"])
        self.assertEqual((a["kind"],b["kind"]),("BGM","ME"))
        self.assertFalse(a["enabled"] or b["enabled"])
        self.assertIsNone(a["track_path"])
        self.check()

    def test_source_document_key_drift_rejected(self):
        doc=self.doc.replace("SINNOH_CYRUS","SINNOH_CYRUS_COPY",1)
        self.rejects("Chaves do MD",doc=doc)
        doc=self.doc.replace("### 4.1. Catálogo funcional proposto","### 4.1. DELETE")
        self.rejects("Tabela",doc=doc)

    def test_missing_or_extra_top_fields(self):
        c=self.modified()
        c.pop("rights_policy")
        self.rejects("Campos",catalog=c)
        c=self.modified()
        c["new_map_id"]=800
        self.rejects("Campos",catalog=c)

    def test_unknown_injected_duplicate_or_missing_cue(self):
        c=self.modified()
        c["cues"].append(copy.deepcopy(c["cues"][0]))
        self.rejects("Quantidade",catalog=c)
        c=self.modified()
        c["cues"].pop()
        self.rejects("Quantidade",catalog=c)
        c=self.modified()
        c["cues"][0]["key"]="SINNOH_UNKNOWN"
        self.rejects("Cue",catalog=c)
        c=self.modified()
        c["cues"][1],c["cues"][2]=c["cues"][2],c["cues"][1]
        self.rejects("Cue",catalog=c)

    def test_cannot_publish_audio_bytes_or_distribution(self):
        for key,value in (
            ("recordings",["sample.mp3"]),("verified_tracks",1),
            ("byte_assets_added",900),("redistribution_approved",True),
            ("copyright_clearance_verified",True),
            ("rights_policy","FREE_TO_DISTRIBUTE")):
            with self.subTest(key=key):
                c=self.modified()
                c[key]=value
                self.rejects("adulterado",catalog=c)

    def test_cannot_mark_install_native_hook_or_gameplay(self):
        for key in ("native_game_installed","active_audio_overrides",
                    "compiled_event_hooks_verified","gameplay_verified",
                    "can_install","default_enabled"):
            with self.subTest(key=key):
                c=self.modified()
                c[key]=True
                self.rejects("adulterado",catalog=c)

    def test_no_fake_map_ids_or_event_ids(self):
        for key,val in (("physical_map_id",1000),("physical_event_id",23)):
            c=self.modified()
            c["cues"][0][key]=val
            self.rejects("Cue",catalog=c)

    def test_no_unlicensed_file_or_fake_sha(self):
        for key,val in (("track_path","Sinnoh/Cynthia.mp3"),
                        ("track_sha256","a"*64),("source_verified",True),
                        ("license_verified",True),
                        ("native_hook_verified",True),
                        ("compiled_binding_verified",True),
                        ("enabled",True)):
            with self.subTest(key=key):
                c=self.modified()
                c["cues"][5][key]=val
                self.rejects("Cue",catalog=c)

    def test_no_fake_loop_fade_volume_pitch(self):
        for key,val in (("loop_start_ms",10),("loop_end_ms",6000),
                        ("fade_seconds",0.4),("volume",80),("pitch",100)):
            with self.subTest(key=key):
                c=self.modified()
                c["cues"][17][key]=val
                self.rejects("Cue",catalog=c)

    def test_night_day_qualifiers_stay_symbolic(self):
        c=self.modified()
        c["cues"][0]["time_window"]="night"
        self.rejects("Cue",catalog=c)
        c=self.modified()
        c["cues"][1]["time_window"]=None
        self.rejects("Cue",catalog=c)

    def test_scope_kind_and_priority_cannot_be_changed(self):
        for key,val in (("scope","me"),("kind","ME"),("priority",5)):
            with self.subTest(key=key):
                c=self.modified()
                c["cues"][8][key]=val
                self.rejects("Cue",catalog=c)

    def test_me_sfx_must_not_be_regular_bgm(self):
        c=self.modified()
        c["cues"][-1]["kind"]="BGM"
        self.rejects("Cue",catalog=c)

    def test_bad_fallback_causes_rejection(self):
        for key,value in (
            ("missing_file","MUTE_ALL"),
            ("cross_region","USE_SINNOH_EVERYWHERE"),
            ("after_scene_map_changed","RESTORE_OLD"),
            ("after_me","KEEP_SINNOH_BGM_FOREVER"),
            ("no_repeat_same_track",False)):
            with self.subTest(key=key):
                c=self.modified()
                c["fallback_policy"][key]=value
                self.rejects("fallback",catalog=c)

    def test_priority_cannot_override_explicit_events_or_user(self):
        c=self.modified()
        c["priority_policy"]=["VERIFIED_BATTLE"]+c["priority_policy"][:-1]
        self.rejects("prioridade",catalog=c)
        c=self.modified()
        c["scope_guards"]["explicit_player_choices_first"]=False
        self.rejects("scope_guards",catalog=c)

    def test_region_scoping_and_no_hooks_guarded(self):
        c=self.modified()
        c["scope_guards"]["only_current_region"]="KANTO"
        self.rejects("scope_guards",catalog=c)
        c=self.modified()
        c["scope_guards"]["no_autoplay_or_hook_install"]=False
        self.rejects("scope_guards",catalog=c)
        registry=copy.deepcopy(self.regions)
        registry["regions"]["SINNOH"]["status"]="playable"
        self.rejects("planned",regions=registry)

    def test_fade_and_loop_are_unknown_not_zero(self):
        for key,value in (
            ("fade_seconds",0.4),("loop_points",[0,6000]),
            ("loop_validation_required",False)):
            with self.subTest(key=key):
                c=self.modified()
                c["fade_loop_policy"][key]=value
                self.rejects("fallback",catalog=c)

    def test_existing_blue_music_priority_cannot_be_broken(self):
        self.rejects("BlueMusic",blue=self.blue.replace(
            "def self.entry(scope,key)","def self.missing_entry(scope,key)"))
        self.rejects("BlueMusic",blue=self.blue.replace(
            "map.autoplay_bgm=original[0];map.bgm=original[1].clone",
            "map.autoplay_bgm=true;map.bgm=audio"))
        self.rejects("BlueMusic",blue=self.blue.replace(
            "return nil if $PokemonGlobal && $PokemonGlobal.nextBattleBGM",
            "return nil if false"))

    def test_cannot_install_runtime_audio_hooks(self):
        self.rejects("Proteção Ruby",adapter=self.adapter.replace(
            "blue_music.entry('global',blue_global_key)",
            "blue_music.config"))
        self.rejects("Ruby de planejamento",adapter=self.adapter+"\ndef self.install; pbBGMPlay('fake'); end\n")
        self.rejects("CH16 não pode instalar",blue=self.blue+"\nBlueSinnohMusicContracts.install\n")

    def test_default_and_sound_reference_is_consistent(self):
        self.assertEqual(expected(),self.catalog["cues"])
        self.assertTrue("SINNOH_GIRATINA" in documented(self.doc))
        self.assertTrue("SINNOH_HALL_OF_FAME" in documented(self.doc))
        self.check()

    def test_cli_missing_source_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            cp=subprocess.run([
                sys.executable,str(ROOT/"scripts/music/audit_sinnoh_music_ch16.py"),
                "--reference",str(Path(d)/"missing.md"),
            ],capture_output=True,text=True)
            self.assertEqual(cp.returncode,2)
            self.assertIn("SINNOH_CH16_BLOQUEADO",cp.stderr)


if __name__=="__main__":
    unittest.main()
