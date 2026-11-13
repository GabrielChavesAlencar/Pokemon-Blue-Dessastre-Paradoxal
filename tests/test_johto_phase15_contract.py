"""Johto M0-M6 music and site preview fail-closed contracts."""
import importlib.util
import json
import unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("johto_audio_audit",ROOT/"scripts/music/audit_johto_phase15.py")
audit=importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)

def read(name):
    return json.loads((ROOT/name).read_text(encoding="utf-8"))

class JohtoPhase15Tests(unittest.TestCase):
    def test_audio_safe_preview(self):
        result=audit.audit(ROOT)
        self.assertEqual(result["status"],"PASS_SAFE_PREVIEW")
        self.assertEqual(result["cues"],53)
        self.assertEqual(result["bgm"],42)
        self.assertEqual(result["me"],11)
        self.assertEqual(result["enabled_music_rules"],0)
        self.assertEqual(result["playable_maps"],0)

    def test_block_unverified_rights_and_enabled_rules(self):
        original=audit.load
        for filename,field,value in (
            ("johto-music.json","license_verified",True),
            ("johto-music-rules.json","default_enabled",True),
        ):
            def tampered(path):
                item=original(path)
                if path.name==filename:
                    item[field]=value
                return item
            with mock.patch.object(audit,"load",side_effect=tampered):
                with self.assertRaises(ValueError):
                    audit.audit(ROOT)
        def wrong_region(path):
            item=original(path)
            if path.name=="johto-music-rules.json":
                item["guardrails"]["requires_current_region"]="KANTO"
            return item
        with mock.patch.object(audit,"load",side_effect=wrong_region):
            with self.assertRaises(ValueError):
                audit.audit(ROOT)

    def test_maps_are_source_symbolic_and_not_playable(self):
        preview=read("site/public/data/johto-preview.json")
        self.assertEqual(preview["status"],"preview_only_not_playable")
        self.assertEqual(preview["maps_installed"],0)
        self.assertEqual(preview["encounters_verified"],0)
        self.assertEqual([x["mode"] for x in preview["pages"]],["JOHTO","GLOBAL"])
        names=set()
        for loc in preview["locations"]:
            self.assertTrue(loc["key"].startswith("JOHTO_"))
            self.assertIsNone(loc["map_id"])
            self.assertFalse(loc["in_game"])
            self.assertFalse(loc["warps_verified"])
            self.assertFalse(loc["encounters_verified"])
            self.assertNotIn(loc["key"],names)
            names.add(loc["key"])
            source=read(loc["source_manifest"])
            rows=sum((source.get(k,[]) for k in
                      ("corridor","return_corridor","required_interiors","additional_required")),[])
            self.assertIn(loc["key"],[v["key"] for v in rows])
            self.assertEqual(loc["phase"],int(source["phase"].split("/")[0]))
        self.assertGreaterEqual(len(preview["locations"]),100)

    def test_trainer_roster_has_eight_leaders_and_no_fictional_teams(self):
        preview=read("site/public/data/johto-preview.json")
        registry=read("site/public/data/regions.json")
        self.assertEqual(preview["badges"],registry["regions"]["JOHTO"]["milestones"])
        self.assertEqual(preview["trainers_compiled"],0)
        self.assertEqual(preview["teams_verified"],0)
        self.assertEqual({r["badge"] for r in preview["trainers"] if r["role"]=="leader"},
                         set(preview["badges"]))
        self.assertEqual(len([r for r in preview["trainers"] if r["role"]=="leader"]),8)
        self.assertEqual(len(set(t["id"] for t in preview["trainers"])),
                         len(preview["trainers"]))
        for trainer in preview["trainers"]:
            self.assertIsNone(trainer["team"])
            self.assertEqual(trainer["team_variants"],[])
            self.assertFalse(trainer["compiled"])
            self.assertFalse(trainer["master_mode_verified"])
            if trainer["id"]!="BLUE_JOHTO_KIMONO_GIRL":
                source=read(trainer["source_manifest"])
                match=[r for r in source["trainer_requirements"] if r["trainer_type"]==trainer["id"]]
                self.assertEqual(len(match),1)
                self.assertEqual(trainer["versions"],
                                 match[0].get("versions",[match[0].get("version",0)]))

    def test_site_router_keeps_kanto_decades_and_explicit_johto_preview(self):
        app=(ROOT/"site/src/assets/app.js").read_text("utf-8")
        region=(ROOT/"site/src/assets/regions.js").read_text("utf-8")
        page=(ROOT/"site/src/assets/johto.js").read_text("utf-8")
        self.assertIn("url.searchParams.get('regiao')==='johto'",app)
        self.assertIn("main.innerHTML=johtoIndex(data,route)",app)
        self.assertIn("url.searchParams.get('regiao')==='kanto'",app)
        self.assertIn("['decades','Decades'",region)
        self.assertIn("['johto','Johto · prévia'",region)
        self.assertIn("preview_only_not_playable",page)
        self.assertIn("0 mapas instalados, 0 equipes PBS compiladas",page)

if __name__=="__main__":
    unittest.main()
