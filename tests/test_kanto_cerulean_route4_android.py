"""Regression: no-map-rewrite music fix for Mt Moon exit and Cerulean City."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from types import SimpleNamespace

from scripts.android.repack_multiregion_hotfix import (
    PREFIX, KANTO_MANIFEST, repair_kanto_cerulean_bgm,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = json.loads((ROOT / "data/regions/kanto-source.json").read_text(encoding="utf8"))
CATALOG = json.loads((ROOT / "data/kanto-music.json").read_text(encoding="utf8"))
RULES = json.loads((ROOT / "data/kanto-music-rules.json").read_text(encoding="utf8"))
TRACKS = {item["number"]: item for item in CATALOG["files"]}


class SourceZipFixture:
    def __init__(self):
        # This regression targets a pre-Route24/25 Android ZIP intentionally.
        # Keep the old 142-map incremental hotfix supported even though the
        # *new* full Kanto manifest contains 145 maps.
        legacy = {k: v for k, v in SOURCE["maps"].items()
                  if k not in ("53", "54", "55")}
        self.mapping = {k: 700 + i for i, k in enumerate(legacy)}
        preview = set(SOURCE["preview_only"])
        self.lines = ["BLUE_KANTO_MUSIC_V1\tKANTO\t" + "a" * 64]
        for old, symbol in legacy.items():
            self.lines.append(
                f"SCOPE\t{self.mapping[old]}\t{symbol}\t{int(int(old) in preview)}"
            )
        for row in RULES["maps"]:
            if row["enabled"] and row["map"] in legacy.values() and row["map"] not in ("CERULEAN_CITY", "ROUTE_4"):
                original = next(k for k, symbol in SOURCE["maps"].items()
                                if symbol == row["map"])
                track = TRACKS[row["track"]]
                self.lines.append(f"MAP\t{self.mapping[original]}\tKanto/{track['filename']}\t100\t100")
        if len([l for l in self.lines if l.startswith("MAP\t")]) != 72:
            raise AssertionError("Fixture must be exactly the old 72-map baseline")
        self.proof = {"schema": 1, "maps": self.mapping}
        self.available = {
            PREFIX + TRACKS[n]["game_path"]: TRACKS[n]["bytes"] for n in (32, 50)
        }

    def read(self, name):
        if name == PREFIX + KANTO_MANIFEST:
            return json.dumps(self.proof).encode()
        raise KeyError(name)

    def namelist(self):
        return list(self.available)

    def getinfo(self, name):
        return SimpleNamespace(file_size=self.available[name])

    def music(self):
        return ("\n".join(self.lines) + "\n").encode("utf8")


class KantoCeruleanMusicRegression(unittest.TestCase):
    def setUp(self):
        self.source = SourceZipFixture()

    def test_rules_are_source_grounded_nonpreview_and_music_assets_reused(self):
        symbols = {row["map"]: row for row in RULES["maps"]}
        self.assertEqual(SOURCE["maps"]["33"], "ROUTE_4")
        self.assertEqual(SOURCE["maps"]["39"], "CERULEAN_CITY")
        self.assertNotIn(33, SOURCE["preview_only"])
        self.assertNotIn(39, SOURCE["preview_only"])
        self.assertEqual((symbols["ROUTE_4"]["track"], symbols["ROUTE_4"]["enabled"]), (32, True))
        self.assertEqual((symbols["CERULEAN_CITY"]["track"], symbols["CERULEAN_CITY"]["enabled"]), (50, True))
        self.assertTrue(TRACKS[32]["filename"].startswith("1-32. Road to Cerulean City"))
        self.assertEqual(TRACKS[50]["filename"], "1-50. Fuchsia City.mp3")
        self.assertEqual(sum(row["enabled"] for row in RULES["maps"]), 77)

    def test_produces_two_exact_bindings_without_reordering_other_music(self):
        original = self.source.music()
        result = repair_kanto_cerulean_bgm(self.source, music=original).decode()
        lines = result.splitlines()
        route = self.source.mapping["33"]
        city = self.source.mapping["39"]
        self.assertIn(
            f"MAP\t{route}\tKanto/1-32. Road to Cerulean City - Leaving Mt. Moon.mp3\t100\t100",
            lines,
        )
        self.assertIn(f"MAP\t{city}\tKanto/1-50. Fuchsia City.mp3\t100\t100", lines)
        self.assertEqual(sum(line.startswith("MAP\t") for line in lines), 74)
        self.assertEqual(sum(line.startswith("SCOPE\t") for line in lines), 142)
        self.assertEqual(lines[1:-2], original.decode().splitlines()[1:])
        self.assertEqual(len([line for line in lines if line.startswith("BATTLE\t")]), 0)

    def test_missing_or_changed_audio_never_generates_fictitious_music(self):
        for number in (32, 50):
            with self.subTest(track=number):
                fake = SourceZipFixture()
                fake.available.pop(PREFIX + TRACKS[number]["game_path"])
                with self.assertRaisesRegex(ValueError, "BGM missing"):
                    repair_kanto_cerulean_bgm(fake, music=fake.music())
                fake = SourceZipFixture()
                fake.available[PREFIX + TRACKS[number]["game_path"]] -= 1
                with self.assertRaisesRegex(ValueError, "MP3 size"):
                    repair_kanto_cerulean_bgm(fake, music=fake.music())

    def test_reject_wrong_map_id_preview_duplicated_entry_or_rule(self):
        fake = SourceZipFixture()
        fake.proof["maps"]["33"] = "invalid"
        with self.assertRaisesRegex(ValueError, "MapID"):
            repair_kanto_cerulean_bgm(fake, music=fake.music())
        fake = SourceZipFixture()
        fake.lines = [line.replace("ROUTE_4\t0", "ROUTE_4\t1") for line in fake.lines]
        with self.assertRaisesRegex(ValueError, "non-preview"):
            repair_kanto_cerulean_bgm(fake, music=fake.music())
        fake = SourceZipFixture()
        fake.lines.append("MAP\t{}\tKanto/old.mp3\t100\t100".format(fake.mapping["33"]))
        with self.assertRaisesRegex(ValueError, "MAP counts"):
            repair_kanto_cerulean_bgm(fake, music=fake.music())
        fake = SourceZipFixture()
        wrong = copy.deepcopy(RULES)
        next(row for row in wrong["maps"] if row["map"] == "ROUTE_4")["enabled"] = False
        with self.assertRaisesRegex(ValueError, "required|Required"):
            repair_kanto_cerulean_bgm(fake, rules=wrong, music=fake.music())

    def test_does_not_patch_unknown_source_inventory_or_older_header(self):
        fake = SourceZipFixture()
        fake.proof["maps"].pop("39")
        with self.assertRaisesRegex(ValueError, "provenance"):
            repair_kanto_cerulean_bgm(fake, music=fake.music())
        fake = SourceZipFixture()
        with self.assertRaisesRegex(ValueError, "header"):
            repair_kanto_cerulean_bgm(fake, music=fake.music().replace(b"BLUE_KANTO_MUSIC_V1", b"INVALID"))
        fake = SourceZipFixture()
        with self.assertRaisesRegex(ValueError, "MAP counts"):
            repair_kanto_cerulean_bgm(fake, music=repair_kanto_cerulean_bgm(fake, music=fake.music()))


if __name__ == "__main__":
    unittest.main()
