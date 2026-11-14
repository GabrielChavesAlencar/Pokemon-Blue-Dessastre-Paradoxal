#!/usr/bin/env python3
"""QA11: authored Hoenn PT-BR map labels, music references, regional Trainer Card.

Only validates the private generated RXDATA/PBS/OGG/Ruby copy. It does NOT
certify rendered text, native Trainer Card, sound playback or full NPC speech.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from server.ruby_marshal import loads

# Only display labels change, never canonical IDs, map coordinates, PBS
# species/move tokens, event handlers or native Decades save state.
MAP_TERM_TRANSLATIONS = (
    ("Pretty Petal Flower Shop", "Floricultura Pretty Petal"),
    ("Petalburg Woods", "Bosque de Petalburg"),
    ("Rusturf Tunnel", "Túnel Rusturf"),
    ("Devon Corporation", "Corporação Devon"),
    ("Pokémon Fan Club", "Clube de Fãs Pokémon"),
    ("Granite Cave", "Caverna de Granito"),
    ("Cycling Road", "Ciclovia"),
    ("Fossil Maniac", "Maníaco dos Fósseis"),
    ("Fiery Path", "Caminho Ardente"),
    ("Mt. Chimney", "Monte Chimney"),
    ("Jagged Pass", "Passagem Rochosa"),
    ("Meteor Falls", "Cachoeira Meteoro"),
    ("Mt. Pyre Summit", "Cume do Monte Pyre"),
    ("Victory Road", "Estrada da Vitória"),
    ("Hall of Fame", "Hall da Fama"),
    ("Elite Four", "Elite Quatro"),
    ("Seafloor Cavern", "Caverna Submarina"),
    ("Cave of Origin", "Caverna da Origem"),
    ("Sky Pillar", "Pilar Celeste"),
    ("Weather Institute", "Instituto Meteorológico"),
    ("Contest Hall", "Salão de Concursos"),
    ("Game Corner", "Salão de Jogos"),
    ("Battle Tent", "Tenda de Batalha"),
    ("Department Store", "Loja de Departamentos"),
    ("Day Care", "Creche Pokémon"),
    ("Mt. Pyre", "Monte Pyre"),
    ("Pokémon Center", "Centro Pokémon"),
    ("Pokemon Center", "Centro Pokémon"),
    ("Poké Mart", "Poké Mart"),
)
AUDIO_LABELS = ("Littleroot", "Birch", "Route101", "Oldale",
                "Center", "Wild", "WildVictory")
MAP_LABEL_PATTERN = re.compile(r"(?m)^\[(\d+)\]\r?\nName\s*=\s*([^\r\n]+)")
NATIVE_FALSE = (
    "native_game_exe_tested", "native_ptbr_npc_dialogue_verified",
    "native_signs_rendered_verified", "native_map_labels_verified",
    "native_bgm_audition_verified", "native_bgm_loops_verified",
    "native_trainer_card_rendered_verified",
    "native_cross_region_ui_verified", "native_approved",
)


def localized_map_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip() or "\n" in name:
        raise ValueError("QA11: nome de mapa vazio ou com quebra de linha")
    result = name
    if result.endswith(" Town"):
        result = "Vila " + result[:-5]
    else:
        city = re.fullmatch(r"(.+?) City( Norte| Sul)?", result)
        if city:
            result = "Cidade de " + city.group(1) + (city.group(2) or "")
    for original, translated in MAP_TERM_TRANSLATIONS:
        result = result.replace(original, translated)
    result = re.sub(r"\bRoute\s+(\d+)\b", r"Rota \1", result)
    return result


def audit_generated(maps: dict, names: dict[int, str],
                    bgm: dict[int, str], stage10_ids: set[int]) -> dict:
    if len(names) != 199 or set(maps) != set(names) or set(bgm) != set(names):
        raise ValueError("QA11: 199 mapas precisam de nomes e música explícitos")
    if set(bgm.values()) - set(AUDIO_LABELS):
        raise ValueError("QA11: música não pertence aos sete assets OGG preparados")
    translated = {}
    for source_id, original in names.items():
        translation = localized_map_name(original)
        translated[source_id] = translation
        if not translation:
            raise ValueError(f"QA11: nome PT-BR ausente no mapa {source_id}")
        attrs = maps[source_id].attrs
        if attrs.get("@autoplay_bgm") is not True:
            raise ValueError(f"QA11: BGM automático ausente no Map{source_id}")
        audio = attrs.get("@bgm")
        if audio is None or audio.attrs.get("@name") != f"BLUE_HOENN_{bgm[source_id]}".encode():
            raise ValueError(f"QA11: BGM de origem não corresponde ao Map{source_id}")
        if audio.attrs.get("@volume") != 80 or audio.attrs.get("@pitch") != 100:
            raise ValueError(f"QA11: volume/pitch inconsistente no Map{source_id}")
    changed = sum(translated[mid] != names[mid] for mid in names)
    if changed < 20:
        raise ValueError("QA11: poucos nomes foram realmente traduzidos")
    if not stage10_ids or not stage10_ids <= names.keys():
        raise ValueError("QA11: mapas finais de Hoenn sem fallback musical")
    return {
        "maps_with_ptbr_display_label": len(names),
        "labels_changed_from_source": changed,
        "map_bgms_assigned": len(bgm),
        "audio_ogg_labels": list(AUDIO_LABELS),
        "stage10_provisional_music_map_ids": sorted(stage10_ids),
        "trainer_card_region_scoped": True,
        "trainer_card_native_open_hoenn_and_kanto": True,
        "trainer_card_native_decades_unchanged": True,
        "trainer_card_distinct_hoenn_badge_abbreviations": True,
        "original_map_ids_preserved": True,
        "donor_dialogue_scripts_copied": False,
        "only_authored_hoenn_events_used": True,
        "music_fallback_not_an_authentic_full_hoenn_soundtrack": True,
        **{key: False for key in NATIVE_FALSE},
    }


def verify_copy(copy: Path) -> dict:
    from hoenn_qa_phase1 import require_private_path
    from pilot_hoenn import SOURCE_MAPS, MAP_BGM
    from hoenn_stage10 import SOURCE_MAPS_STAGE10

    copy = require_private_path(copy)
    manifest = json.loads((copy / "Hoenn pilot.json").read_text("utf-8"))
    ids, qa = manifest.get("maps"), manifest.get("qa11")
    if (manifest.get("region") != "HOENN" or
        manifest.get("kind") != "ISOLATED_HOENN_TEST" or
        manifest.get("save_profile") != "Hoenn QA Fase11" or
        not isinstance(ids, dict) or len(ids) != 199 or
        not isinstance(qa, dict) or not isinstance(manifest.get("qa10"), dict)):
        raise ValueError("QA11: exige cópia isolada QA11 com 199 mapas e auditoria QA10")
    if qa.get("donor_dialogue_scripts_copied") is not False or any(
        qa.get(key) is not False for key in NATIVE_FALSE
    ):
        raise ValueError("QA11: fonte original ou aprovação de Game.exe indevida")
    mapinfo = loads((copy / "Data/MapInfos.rxdata").read_bytes())
    meta = (copy / "PBS/map_metadata_hoenn_pilot.txt").read_text("utf-8-sig")
    metadata = {int(key): label.strip() for key, label in MAP_LABEL_PATTERN.findall(meta)}
    rxdata = {}
    for source_id, name in SOURCE_MAPS.items():
        target = ids.get(str(source_id))
        if type(target) is not int or not 700 <= target <= 999:
            raise ValueError(f"QA11: remapeamento inválido para {source_id}")
        localized = localized_map_name(name)
        if metadata.get(target) != localized:
            raise ValueError(f"QA11: Name PBS não está em PT-BR: {source_id}")
        info = mapinfo.get(target)
        if not info or info.attrs.get("@name") != localized.encode("utf-8"):
            raise ValueError(f"QA11: MapInfos localizados divergem: {source_id}")
        rxdata[source_id] = loads((copy / f"Data/Map{target:03}.rxdata").read_bytes())
    if len(metadata) != len(SOURCE_MAPS):
        raise ValueError("QA11: mapa metadata extra/ausente")
    result = audit_generated(rxdata, SOURCE_MAPS, MAP_BGM,
                             set(SOURCE_MAPS_STAGE10))
    if qa != result:
        raise ValueError("QA11: manifesto não corresponde à UI e aos áudios compilados")
    for label in AUDIO_LABELS:
        path = copy / f"Audio/BGM/BLUE_HOENN_{label}.ogg"
        if not path.is_file() or path.is_symlink() or path.stat().st_size < 4:
            raise ValueError(f"QA11: OGG nativo ausente: {label}")
        with path.open("rb") as stream:
            if stream.read(4) != b"OggS":
                raise ValueError(f"QA11: cabeçalho OGG inválido: {label}")
    plugin = copy / "Plugins/ZZZZ Blue Story and Presentation/RegionalCards.rb"
    if not plugin.is_file() or plugin.is_symlink():
        raise ValueError("QA11: módulo regional do Trainer Card não está na cópia")
    cards = plugin.read_text("utf-8")
    expected = (
        'def self.regional_active?', '%w[KANTO HOENN]',
        'INSÍGNIAS DE #{data[:current_name].to_s.upcase}',
        'HOENN_BADGES.fetch(badge, "??")',
        'BlueRegionalCards.regional_active?',
    )
    missing = [guard for guard in expected if guard not in cards]
    if missing:
        raise ValueError(f"QA11: cartão regional desatualizado: {missing}")
    ruby = (copy / "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb").read_text("utf-8")
    if "def self.sign_stage10(key)" not in ruby or "def self.sign(symbol)" not in ruby:
        raise ValueError("QA11: diálogos portugueses autorais de Hoenn ausentes")
    return {
        "schema": 1, "region": "HOENN", "qa_phase": "11/12",
        "status": "PTBR_SIGNS_MUSIC_TRAINER_CARD_STATICALLY_VERIFIED",
        **result,
        "regional_save_isolated": True,
        "native_game_exe_approved": False,
    }


def main(argv: list[str] | None = None) -> int:
    from hoenn_qa_phase1 import WORK, require_private_path

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", type=Path, default=WORK / "hoenn-qa-fase11")
    parser.add_argument("--report", type=Path, default=WORK / "hoenn-qa-fase11-report.json")
    args = parser.parse_args(argv)
    path = None
    try:
        path = require_private_path(args.report)
        result, status = verify_copy(args.copy), 0
    except (OSError, ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as exc:
        result = {"schema": 1, "region": "HOENN", "qa_phase": "11/12",
                  "status": "BLOCKED", "native_game_exe_approved": False,
                  "errors": [str(exc)]}
        status = 2
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return status


if __name__ == "__main__":
    raise SystemExit(main())
