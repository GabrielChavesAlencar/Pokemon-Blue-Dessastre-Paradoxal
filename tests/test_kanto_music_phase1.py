"""Kanto F1: map-ID resolution, opt-in, safe integration and Decades isolation."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path
from scripts.music import compile_kanto_music as compiler

ROOT = Path(__file__).resolve().parents[1]
FILES = ("data/regions/kanto-source.json", "data/kanto-music.json",
         "data/kanto-music-rules.json", "data/shared-music.json")


class KantoMusicPhaseOneTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.project = Path(temporary.name) / "project"
        self.game = self.project / "game"
        for relative in FILES:
            dest = self.project / relative
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes((ROOT / relative).read_bytes())
        self.source = self.read("data/regions/kanto-source.json")
        self.catalog = self.read("data/kanto-music.json")
        self.rules = self.read("data/kanto-music-rules.json")
        self.mapping = {sid: int(sid) + 700 for sid in self.source["maps"]}
        (self.game / "Data").mkdir(parents=True)
        for dest in self.mapping.values():
            (self.game / "Data" / f"Map{dest:03d}.rxdata").write_bytes(b"mock Kanto map")
        self.pilot = self.game / "Kanto pilot.json"
        self.pilot.write_text(json.dumps({"maps":self.mapping}), encoding="utf-8")

    def read(self, relative):
        return json.loads((self.project / relative).read_text(encoding="utf-8"))

    def write_rules(self):
        path = self.project / "data/kanto-music-rules.json"
        path.write_text(json.dumps(self.rules,ensure_ascii=False), encoding="utf-8")

    def compile(self):
        return compiler.compile_bytes(self.project, self.game,
                                      compiler.load_mapping(self.game))

    def add_music(self, number):
        item = next(x for x in self.catalog["files"] if x["number"] == number)
        file = self.game / item["game_path"]
        file.parent.mkdir(parents=True,exist_ok=True)
        file.write_bytes(b"synthetic fixture, no soundtrack recording")

    def test_142_actual_ids_and_45_previews_are_scoped_but_not_playing(self):
        content, report = self.compile()
        lines = content.decode().splitlines()
        self.assertEqual(report["source_maps"], 142)
        self.assertEqual(report["preview_maps"], 45)
        self.assertEqual(report["staged_map_rules"], 52)
        self.assertEqual(report["staged_battles"], 8)
        self.assertEqual(report["staged_events"], 14)
        self.assertEqual(report["staged_scenes"], 13)
        self.assertEqual(report["active_map_bindings"], 0)
        self.assertEqual(report["active_battle_bindings"], 0)
        self.assertEqual(len([line for line in lines if line.startswith("SCOPE\t")]), 142)
        self.assertEqual(len([line for line in lines if line.startswith(("MAP\t","BATTLE\t"))]),0)
        pallet = report["real_map_ids"]["PALLET_TOWN"]
        self.assertEqual(pallet, 705)
        self.assertIn("SCOPE\t705\tPALLET_TOWN\t0", lines)
        self.assertNotIn("SCOPE\t5\tPALLET_TOWN\t0", lines)

    def test_opt_in_map_requires_real_compiled_id_and_audio_present(self):
        rule = next(r for r in self.rules["maps"] if r["map"] == "PALLET_TOWN")
        rule["enabled"] = True
        self.write_rules()
        content, report = self.compile()
        self.assertEqual(report["active_map_bindings"], 0)
        self.assertIn("Kanto/", report["missing_audio"][0])
        self.add_music(rule["track"])
        content, report = self.compile()
        self.assertEqual(report["active_map_bindings"], 1)
        row = [line for line in content.decode().splitlines() if line.startswith("MAP\t")]
        self.assertEqual(len(row),1)
        self.assertTrue(row[0].startswith("MAP\t705\tKanto/1-06. Pallet Town.mp3\t"))
        self.assertEqual(report["real_map_ids"]["OAK_LAB"], 706)

    def test_preview_map_cannot_be_enabled_early(self):
        preview = {self.source["maps"][str(i)] for i in self.source["preview_only"]}
        candidate = next(row for row in self.rules["maps"] if row["map"] in preview)
        candidate["enabled"] = True
        self.write_rules()
        self.add_music(candidate["track"])
        content, report = self.compile()
        # The same Silph soundtrack is shared by eleven non-preview floors.
        # Those floors may be active; only the preview lobby must be blocked.
        approved = {row["map"] for row in self.rules["maps"]
                    if row["enabled"] and row["track"] == candidate["track"]
                    and row["map"] not in preview}
        self.assertEqual(report["active_map_bindings"],len(approved))
        self.assertIn(candidate["map"], report["preview_skipped"])
        preview_id = next(sid for sid, key in self.source["maps"].items()
                          if key == candidate["map"])
        self.assertFalse(any(row.startswith(f"MAP\t{self.mapping[preview_id]}\t")
                             for row in content.decode().splitlines()))

    def test_uses_no_original_source_id_or_wrong_map_number(self):
        broken = dict(self.mapping)
        broken["5"] = broken["6"]
        with self.assertRaisesRegex(ValueError, "Duplicate compiled MapID"):
            compiler.compile_bytes(self.project,self.game,broken)
        del broken["5"]
        with self.assertRaisesRegex(ValueError, "precisely Kanto"):
            compiler.compile_bytes(self.project,self.game,broken)
        missing = self.game / "Data" / f"Map{self.mapping['5']:03d}.rxdata"
        missing.unlink()
        with self.assertRaisesRegex(ValueError, "Compiled Kanto map missing"):
            self.compile()

    def test_rejects_cross_region_and_wrong_music_kind(self):
        original = copy.deepcopy(self.rules)
        self.rules["maps"][0]["map"] = "NON_KANTO_DECADES"
        self.write_rules()
        with self.assertRaisesRegex(ValueError, "symbolic Kanto map"):
            self.compile()
        self.rules = copy.deepcopy(original)
        self.rules["maps"][0]["track"] = 29  # Gym badge is ME, not a looped BGM.
        self.write_rules()
        with self.assertRaisesRegex(ValueError, "Unknown Kanto BGM"):
            self.compile()
        self.rules = copy.deepcopy(original)
        self.rules["events"][0]["enabled"] = True
        self.write_rules()
        with self.assertRaisesRegex(ValueError, "Unverified Kanto ME"):
            self.compile()

    def test_apply_is_idempotent_backed_up_and_does_not_touch_decades(self):
        content, _ = self.compile()
        decades = self.game / "Data/blue-music.json"
        decades.write_bytes(b'{"user":"custom-decades-playlist"}\n')
        saved = decades.read_bytes()
        self.assertEqual(compiler.write_safely(self.project,self.game,content), "written")
        self.assertEqual(compiler.write_safely(self.project,self.game,content), "unchanged")
        output = self.game / compiler.OUTPUT
        self.assertEqual(output.read_bytes(),content)
        self.assertEqual(decades.read_bytes(),saved)
        changed = content + b"# trailing marker\n"
        self.assertEqual(compiler.write_safely(self.project,self.game,changed),"written")
        backups = list((self.project/".blue-backups").rglob("blue-kanto-music.txt"))
        self.assertEqual(len(backups),1)
        self.assertEqual(backups[0].read_bytes(),content)

    def test_installed_manifest_works_without_pilot_json(self):
        self.pilot.unlink()
        meta = self.game / "Data/blue-kanto-install.json"
        meta.write_text(json.dumps({"schema":1,"maps":self.mapping}),encoding="utf-8")
        (self.game/"Data/blue-kanto-start.txt").write_text(
            "BLUE_KANTO_START_V1,KANTO,707,25,7\n",encoding="ascii")
        plan = compiler.plan_installed(self.project,self.game)
        self.assertEqual(set(plan),{self.game/compiler.OUTPUT})
        self.assertIn(b"SCOPE\t705\tPALLET_TOWN", next(iter(plan.values())))
        self.assertFalse((self.game/compiler.OUTPUT).exists())
        self.assertFalse((self.game/"Data/blue-music.rxdata").exists())

    def test_no_kanto_installed_does_not_create_any_regional_file(self):
        self.pilot.unlink()
        self.assertEqual(compiler.plan_installed(self.project,self.game), {})
        self.assertFalse((self.game/compiler.OUTPUT).exists())


if __name__ == "__main__":
    unittest.main()
