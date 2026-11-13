"""Stage 16 guardrails: never infer manual gameplay success from CI."""
from __future__ import annotations

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

REGIONS=Path(__file__).resolve().parents[1]/"scripts/regions"
ROOT=REGIONS.parents[1]
sys.path.insert(0,str(REGIONS))
try:
    import release_gate
finally:
    sys.path.remove(str(REGIONS))


class KantoReleaseGateTests(unittest.TestCase):
    def clone(self, root: Path):
        for part in ["data/regions/kanto-source.json",
                     "site/public/data/regions.json",
                     "site/public/data/kanto.json",
                     "site/public/data/catalog.json"]:
            out=root/part
            out.parent.mkdir(parents=True,exist_ok=True)
            out.write_bytes((ROOT/part).read_bytes())

    def patch_json(self, root, relative, change):
        file=root/relative
        data=json.loads(file.read_text("utf-8"))
        change(data)
        file.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")

    def test_current_catalog_is_safe_prototype_not_final_acceptance(self):
        result=release_gate.inspect(ROOT)
        self.assertTrue(result["ci_preflight_passed"])
        self.assertEqual(result["map_count"],142)
        self.assertEqual(result["preview_maps"],45)
        self.assertEqual(result["trainers"],144)
        self.assertEqual(result["wild_locations"],23)
        self.assertEqual(result["wild_methods"],69)
        self.assertEqual(result["wild_species"],53)
        self.assertFalse(result["declared_playable"])
        self.assertFalse(result["accepted_integrally"])
        self.assertGreater(len(result["blocking_checks"]),4)

    def test_forged_playable_status_rejected_before_manual_qa(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.clone(root)
            self.patch_json(root,"site/public/data/regions.json",
                            lambda d:d["regions"]["KANTO"].update(status="playable"))
            with self.assertRaisesRegex(ValueError,"Cannot mark Kanto playable"):
                release_gate.inspect(root)

    def test_preview_cannot_be_marked_as_functional(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.clone(root)
            def corrupt(d):
                loc=next(x for x in d["locations"] if x["status"]=="preview")
                loc["status"]="experimental"
            self.patch_json(root,"site/public/data/kanto.json",corrupt)
            with self.assertRaisesRegex(ValueError,"classification"):
                release_gate.inspect(root)

    def test_badge_order_and_trainer_pokedex_integrity(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.clone(root)
            self.patch_json(root,"site/public/data/regions.json",
                            lambda d:d["regions"]["KANTO"]["milestones"].reverse())
            with self.assertRaisesRegex(ValueError,"milestone"):
                release_gate.inspect(root)
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.clone(root)
            self.patch_json(root,"site/public/data/kanto.json",
                            lambda d:d["trainers"][0]["variants"][0]["team"][0].update(species="NOT_A_REAL_SPECIES"))
            with self.assertRaisesRegex(ValueError,"Pokédex"):
                release_gate.inspect(root)

    def test_uploaded_like_manual_pass_is_not_marked_as_integrally_accepted(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            self.clone(root)
            path=root/"manual.json"
            path.write_text(json.dumps({
                "schema":2,"type":"manual_observation_unreviewed",
                "platform":"windows",
                "summary":{"total":40,"passed_reported":40,
                           "manual_review_required":True,"accepted_integrally":False}
            }),encoding="utf-8")
            result=release_gate.inspect(root,manual_report=path)
            self.assertTrue(result["manual_report"]["supplied"])
            self.assertFalse(result["manual_report"]["reviewed"])
            self.assertFalse(result["accepted_integrally"])
            path.write_text(json.dumps({
                "schema":2,"type":"manual_observation_unreviewed",
                "summary":{"accepted_integrally":True}
            }),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"unreviewed"):
                release_gate.inspect(root,manual_report=path)


if __name__=="__main__":
    unittest.main()
