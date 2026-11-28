"""Prove Windows/Android-ready publication inputs without touching the baseline."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/regions"))
from k03e_contract import MAPS, MUSIC
from k03e_release_inputs import promote_inputs
from k04_corridor import MAPS as K04_MAPS
from export_kanto import slug
from scripts.music.compile_kanto_music import compile_bytes


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


class K03EReleaseInputsTests(unittest.TestCase):
    def setUp(self):
        self.source = read(ROOT / "data/regions/kanto-source.json")
        self.site = read(ROOT / "site/public/data/kanto.json")
        self.music = read(ROOT / "data/kanto-music-rules.json")
        self.evidence = read(ROOT / "data/regions/kanto-k03e-portal-delta.json")
        from scripts.regions.k05_contract import MAPS as K05_MAPS
        later={**K04_MAPS,**K05_MAPS}
        # K03-E is a historical promotion fixture independent of K04.
        self.source["maps"] = {i: key for i,key in self.source["maps"].items()
                               if int(i) not in later}
        rock_ids = {slug(key) for key in later.values()}
        self.site["locations"] = [row for row in self.site["locations"] if row["id"] not in rock_ids]
        self.site["trainers"] = [row for row in self.site["trainers"] if row["location"] not in rock_ids]
        self.active_triplet = copy.deepcopy((self.source, self.site, self.music))
        self.source["maps"] = {i: key for i,key in self.source["maps"].items()
                               if int(i) not in MAPS}
        for field in ("locations", "trainers"):
            delta_ids = {row["id"] for row in self.evidence[field]}
            self.site[field] = [row for row in self.site[field] if row["id"] not in delta_ids]
        self.music["maps"] = [row for row in self.music["maps"] if row["map"] not in MAPS.values()]

    def test_prepare_triplet_from_real_ci_artifact_and_compile_music(self):
        active, site, music = promote_inputs(self.source, self.site, self.music, self.evidence)
        self.assertEqual((active, site, music), self.active_triplet)
        self.assertEqual((len(active["maps"]), len(site["locations"]), len(site["trainers"])),
                         (160, 160, 173))
        self.assertEqual((len(self.source["maps"]), len(self.site["locations"])), (156, 156))
        mapping = {key: 700 + n for n, key in enumerate(active["maps"])}
        catalog = read(ROOT / "data/kanto-music.json")
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            game = project / "game"
            (game / "Data").mkdir(parents=True)
            for dest in mapping.values():
                (game / "Data" / f"Map{dest:03}.rxdata").write_bytes(b"synthetic")
            for item in catalog["files"]:
                target = game / item["game_path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(b"synthetic")
            for relative, obj in (
                ("data/kanto-music.json", catalog),
                ("data/regions/kanto-source.json", active),
                ("data/kanto-music-rules.json", music),
                ("data/shared-music.json", read(ROOT / "data/shared-music.json")),
            ):
                path = project / relative
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(obj), encoding="utf-8")
            compiled, report = compile_bytes(project, game, mapping)
        self.assertEqual(report["source_maps"], 160)
        lines = compiled.decode("utf-8").splitlines()
        song_names = {entry["number"]: "Kanto/" + entry["filename"] for entry in catalog["files"]}
        self.assertTrue(all(any(row.startswith(f"MAP\t{mapping[str(source)]}\t{song_names[track['track']]}\t")
                                for row in lines)
                            for source, track in zip(MAPS, MUSIC)))
        self.assertEqual(sum(row.startswith("MAP\t") for row in lines), 88)

    def test_reject_colliding_trainer_and_changed_scope(self):
        evidence = copy.deepcopy(self.evidence)
        evidence["trainers"][0]["id"] = self.site["trainers"][0]["id"]
        with self.assertRaises(ValueError):
            promote_inputs(self.source, self.site, self.music, evidence)
        evidence = copy.deepcopy(self.evidence)
        evidence["locations"] = evidence["locations"][:-1]
        with self.assertRaises(ValueError):
            promote_inputs(self.source, self.site, self.music, evidence)


if __name__ == "__main__":
    unittest.main()
