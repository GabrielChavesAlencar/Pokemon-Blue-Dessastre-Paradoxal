"""QA11 synthetic PT-BR display labels, OGG references and card safety tests."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts/regions"))
from build_johto_events import ruby
from hoenn_qa_phase11 import (
    AUDIO_LABELS, NATIVE_FALSE, localized_map_name, audit_generated, verify_copy,
)


class HoennQA11Tests(unittest.TestCase):
    def setUp(self):
        self.names = {mid: f"Example{mid} Town" for mid in range(1, 199)}
        self.names[250] = "Victory Road B1F"
        self.bgm = {mid: "Center" for mid in self.names}
        self.maps = {
            mid: ruby("RPG::Map", width=20, height=16, events={},
                      autoplay_bgm=True,
                      bgm=ruby("RPG::AudioFile",
                               name=b"BLUE_HOENN_Center", volume=80, pitch=100))
            for mid in self.names
        }

    def test_199_map_names_and_7_audio_references(self):
        result = audit_generated(self.maps, self.names, self.bgm, {250})
        self.assertEqual(result["maps_with_ptbr_display_label"],199)
        self.assertEqual(result["labels_changed_from_source"],199)
        self.assertEqual(result["map_bgms_assigned"],199)
        self.assertEqual(result["audio_ogg_labels"],list(AUDIO_LABELS))
        self.assertTrue(result["trainer_card_native_open_hoenn_and_kanto"])
        self.assertTrue(result["trainer_card_native_decades_unchanged"])
        self.assertTrue(result["music_fallback_not_an_authentic_full_hoenn_soundtrack"])
        for field in (*NATIVE_FALSE,"donor_dialogue_scripts_copied"):
            self.assertIs(result[field], False, field)

    def test_ptbr_map_names_without_changing_canonical_id(self):
        self.assertEqual(localized_map_name("Littleroot Town"),"Vila Littleroot")
        self.assertEqual(localized_map_name("Oldale Town"),"Vila Oldale")
        self.assertEqual(localized_map_name("Sootopolis City"),"Cidade de Sootopolis")
        self.assertEqual(localized_map_name("Ever Grande City Norte"),"Cidade de Ever Grande Norte")
        self.assertEqual(localized_map_name("Victory Road B2F"),"Estrada da Vitória B2F")
        self.assertEqual(localized_map_name("Cave of Origin B1F"),"Caverna da Origem B1F")
        self.assertEqual(localized_map_name("Seafloor Cavern - Entrada"),"Caverna Submarina - Entrada")
        self.assertEqual(localized_map_name("Sky Pillar 1F"),"Pilar Celeste 1F")
        self.assertEqual(localized_map_name("Hall of Fame de Hoenn"),"Hall da Fama de Hoenn")
        self.assertEqual(localized_map_name("Rota 101"),"Rota 101")
        self.assertEqual(localized_map_name("Poké Mart de Oldale"),"Poké Mart de Oldale")
        self.assertEqual(localized_map_name("Route 123"),"Rota 123")

    def test_blank_or_multiline_map_names_rejected(self):
        for name in ("", "  ", "X\nY"):
            with self.subTest(name=name),self.assertRaises(ValueError):
                localized_map_name(name)

    def test_missing_map_music_rejected(self):
        self.maps[250].attrs["@autoplay_bgm"] = False
        with self.assertRaisesRegex(ValueError,"BGM"):
            audit_generated(self.maps,self.names,self.bgm,{250})

    def test_wrong_or_unlicensed_ogg_name_rejected(self):
        self.bgm[250] = "missing_track"
        with self.assertRaisesRegex(ValueError,"sete assets"):
            audit_generated(self.maps,self.names,self.bgm,{250})
        self.bgm[250] = "Center"
        self.maps[250].attrs["@bgm"].attrs["@name"] = b"BLUE_HOENN_Missing"
        with self.assertRaisesRegex(ValueError,"BGM de origem"):
            audit_generated(self.maps,self.names,self.bgm,{250})

    def test_invalid_pitch_or_volume_rejected(self):
        self.maps[250].attrs["@bgm"].attrs["@volume"] = 200
        with self.assertRaisesRegex(ValueError,"volume"):
            audit_generated(self.maps,self.names,self.bgm,{250})

    def test_missing_199th_map_rejected(self):
        self.maps.pop(250)
        with self.assertRaisesRegex(ValueError,"199 mapas"):
            audit_generated(self.maps,self.names,self.bgm,{250})

    def test_native_game_exe_acceptance_not_inferred(self):
        result = audit_generated(self.maps,self.names,self.bgm,{250})
        self.assertFalse(result["native_game_exe_tested"])
        self.assertFalse(result["native_trainer_card_rendered_verified"])
        self.assertFalse(result["native_ptbr_npc_dialogue_verified"])

    def test_cannot_audit_outside_private_blue_work_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError,".blue-work"):
                verify_copy(Path(tmp))


if __name__ == "__main__":
    unittest.main()
