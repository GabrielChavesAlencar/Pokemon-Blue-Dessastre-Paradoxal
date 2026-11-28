#!/usr/bin/env python3
"""QA12: integrated Hoenn static acceptance gate and PRIVATE native playtest queue.

Combines real reports from QA01..QA11 for the same fresh 199-map QA12 copy,
checks code/data provenance and inventories known gaps. Neither this script nor
GitHub Actions can run/verify Game.exe, JoiPlay or original save compatibility.
A green technical gate MUST NEVER be interpreted as 12/12 playable approval.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from hoenn_catalog import CATALOG_REVISION, approved_source_ids

# Each QA01..QA11 report is generated immediately before QA12 by TESTAR_HOENN.bat.
# Order matters; a missing or BLOCKED report stops the acceptance gate.
AUDITS = (
    ("01", "prep", "COPY_READY_FOR_NATIVE_TEST"),
    ("02", "mapas", "STATIC_MAP_CONNECTIONS_AUDITED"),
    ("03", "encontros", "SOURCE_ENCOUNTERS_MERGED_STATICALLY"),
    ("04", "campo", "FIELD_OBSTACLE_CONTRACT_PREPARED"),
    ("05", "story", "STORY_ANCHORS_STATICALLY_VERIFIED"),
    ("06", "clima", "CLIMATE_STORY_STATICALLY_VERIFIED"),
    ("07", "ginasios", "EIGHT_GYM_BINDINGS_STATICALLY_VERIFIED"),
    ("08", "victory-road", "VICTORY_ROAD_WALLY_STATICALLY_VERIFIED"),
    ("09", "liga", "LEAGUE_ELITE_CHAMPION_STATICALLY_VERIFIED"),
    ("10", "hall", "HALL_OF_FAME_CIRCUIT_STATICALLY_VERIFIED"),
    ("11", "interface", "PTBR_SIGNS_MUSIC_TRAINER_CARD_STATICALLY_VERIFIED"),
)
APPROVAL_KEYS = (
    "native_game_exe_approved", "native_approved", "gameplay_accepted",
    "game_exe_tested", "native_game_exe_tested", "android_approved",
    "android_tested", "native_story_approved", "phase_fully_approved",
    "game_exe_tested_here", "android_tested_here",
)
NATIVE_SCENARIOS = (
    ("inicio", "01", "Littleroot: nova partida, quarto, relógio, mãe, Birch, três bolas, rival, Pokédex"),
    ("mapas", "02", "Todos os acessos, interiores, escadas, entradas e saídas sem softlock"),
    ("encontros", "03", "Treinadores, NPCs, placas, itens no chão, encontros por dia/noite e Pokémon selvagens"),
    ("movimentos", "04", "Cut, Flash, Rock Smash, Strength, Surf, Dive, Waterfall, pedras, água e puzzles"),
    ("magma-aqua", "05", "Aqua/Magma, Meteor Falls, esconderijos, Seafloor Cavern e submarino"),
    ("clima", "06", "Crise de Sootopolis, Cave of Origin, Sky Pillar, Rayquaza e condições visuais"),
    ("ginasios", "07", "Oito ginásios, puzzles, insígnias, TMs, level cap e scaling real"),
    ("wally", "08", "Victory Road, Waterfall, trilhas, Wally, vitória/derrota e acesso à Liga"),
    ("elite", "09", "Sidney, Phoebe, Glacia, Drake e Wallace na ordem; times, artes, músicas"),
    ("hall", "10", "Hall da Fama, vitória, registro único, créditos, retorno e Johto/Sinnoh"),
    ("localizacao", "11", "Português/Inglês, texto NPCs, placas, interface, insígnias e Trainer Card"),
    ("audio", "11", "BGM e loop: cidades, rotas, Centro, clima, batalha, Liga e Hall"),
    ("saves", "12", "Salvar/carregar no início, ginásios, cavernas, Elite e pós-jogo; sem corrupção"),
    ("regioes", "12", "Decades, Kanto, Johto e Sinnoh não alterados; viagem e PC sem perda"),
    ("travamentos", "12", "Paredes e colisão, hotkeys, fechamento/reabertura e erros reais de jogo"),
)
PLATFORMS = ("windows_game_exe", "android_joiplay")


def report_filename(key: str) -> str:
    # Report suffixes are stable and are never shared with older QA copies.
    return f"hoenn-qa-fase12-{key}-report.json"


def accepted_reports(evidence: dict[str, dict], *, catalog_revision=CATALOG_REVISION) -> list[dict]:
    """Validate cross-stage outputs; NEVER accept booleans asserting native QA."""
    expected_maps = len(approved_source_ids(catalog_revision))
    validated = []
    if set(evidence) != {phase for phase, _, _ in AUDITS}:
        raise ValueError("QA12: os 11 relatórios técnicos de Fase01–11 são obrigatórios")
    for phase, _, expected_status in AUDITS:
        row = evidence[phase]
        if not isinstance(row, dict) or row.get("region") != "HOENN":
            raise ValueError(f"QA12: relatório {phase} inválido ou de outra região")
        if row.get("status") != expected_status:
            raise ValueError(f"QA12: Fase{phase} não passou: {row.get('status')}")
        if row.get("errors"):
            raise ValueError(f"QA12: Fase{phase} contém erro anterior")
        if any(row.get(key) is True for key in APPROVAL_KEYS):
            raise ValueError(f"QA12: Fase{phase} reivindica aprovação nativa indevida")
        if phase == "01":
            if row.get("copy", {}).get("maps_present") != expected_maps:
                raise ValueError(f"QA12: a cópia QA01 não contém {expected_maps} mapas")
            if row.get("copy", {}).get("distinct_save_profile") != "Hoenn QA Fase12":
                raise ValueError("QA12: QA01 não verificou perfil isolado QA12")
        elif phase == "02" and row.get("maps_read") != expected_maps:
            raise ValueError(f"QA12: QA02 não varreu os {expected_maps} mapas físicos")
        elif phase == "07" and len(row.get("gym_source_map_ids", [])) != 8:
            raise ValueError("QA12: QA07 não conferiu oito ginásios")
        elif phase == "09" and row.get("pbs_reference_party_sizes") != [5,5,5,5,6]:
            raise ValueError("QA12: QA09 não conferiu cinco chefes da Liga")
        elif phase == "10" and row.get("expected_neighbor_unlocks") != ["JOHTO","SINNOH"]:
            raise ValueError("QA12: QA10 não confirma desbloqueio Johto/Sinnoh")
        elif phase == "11":
            if row.get("maps_with_ptbr_display_label") != expected_maps or row.get("map_bgms_assigned") != expected_maps:
                raise ValueError(f"QA12: QA11 não auditou {expected_maps} rótulos e BGMs")
        validated.append({"phase": phase + "/12", "status": expected_status})
    return validated


def backlog(manifest: dict) -> dict:
    qa3 = manifest.get("qa3", {})
    qa4 = manifest.get("qa4", {})
    stage = manifest.get("stage10", {})
    if not all(isinstance(x, dict) for x in (qa3, qa4, stage)):
        raise ValueError("QA12: faltam inventários QA03, QA04 e Stage10")
    pending_events = qa3.get("source_events", {}).get("unimplemented_source_event_candidates")
    pending_obstacles = qa4.get("source_obstacles_needing_review")
    art = stage.get("boss_battle_art_placeholder")
    if not isinstance(pending_events, list) or not isinstance(pending_obstacles, list) or not isinstance(art, dict):
        raise ValueError("QA12: backlog fonte ou sprites não foi preservado")
    return {
        "unimplemented_original_npc_trainer_sign_candidates": len(pending_events),
        "obstacle_source_candidates_requiring_review": len(pending_obstacles),
        "stage10_boss_graphics_using_placeholders": sorted(k for k,v in art.items() if v is True),
        "full_ptbr_npc_dialogue": "pending_visual_review",
        "complete_authentic_hoenn_soundtrack": "pending_original_audio_and_audition",
        "native_field_puzzles_and_map_passability": "pending_game_exe",
        "league_hall_credits_and_postgame": "pending_game_exe",
        "regional_travel_and_original_save_regression": "pending_windows_and_android",
    }


def audit_generated(manifest: dict) -> dict:
    """Stable QA12 contract; executed during private copy creation."""
    from pilot_hoenn import UPSTREAM, validate_pilot_mapping
    expected = approved_source_ids(manifest.get("catalog_revision", 1))
    try:
        validate_pilot_mapping(manifest)
    except ValueError as error:
        raise ValueError(f"QA12: conjunto aprovado de {len(expected)} mapas inválido") from error
    if manifest.get("source_commit") != UPSTREAM or manifest.get("region") != "HOENN":
        raise ValueError(f"QA12: a origem dos {len(expected)} mapas não é a revisão fixada")
    for index in range(3,12):
        if not isinstance(manifest.get(f"qa{index}"), dict):
            raise ValueError(f"QA12: falta manifesto QA{index:02}")
    teleports = manifest.get("qa_test_stops")
    if (not isinstance(teleports, dict) or teleports.get("count") != len(expected)
        or teleports.get("file") != "Data/blue-hoenn-test-stops.txt"
        or teleports.get("real_terrain_walkable") is not True
        or teleports.get("debug_only_no_story_flag_mutation") is not True
        or teleports.get("game_exe_tested") is not False
        or not isinstance(teleports.get("source_ids"), list)
        or teleports["source_ids"] != sorted(expected)
        or not isinstance(teleports.get("sha256"), str)
        or len(teleports["sha256"]) != 64
        or any(c not in "0123456789abcdef" for c in teleports["sha256"])):
        raise ValueError(f"QA12: catálogo de teleporte dos {len(expected)} mapas não foi preparado")
    return {
        "source_commit": UPSTREAM,
        "maps_expected": len(expected),
        "test_teleport_map_count": len(expected),
        "debug_teleport_catalog_sha256": teleports["sha256"],
        "debug_teleport_scope": "isolated_hoenn_pilot_only",
        "debug_teleport_native_playtested": False,
        "audits_expected": [phase for phase, _, _ in AUDITS],
        "native_scenario_count_per_platform": len(NATIVE_SCENARIOS),
        "native_platforms_expected": list(PLATFORMS),
        "unresolved_backlog": backlog(manifest),
        "all_native_scenarios_pending": True,
        "source_dialogues_or_scripts_copied": False,
        "original_decades_and_other_region_saves_untouched_by_staging": True,
        "technical_prepared_not_native_approved": True,
        "native_game_exe_tested": False,
        "android_joiplay_tested": False,
        "native_story_approved": False,
        "all_12_phases_playable_approved": False,
    }


def manual_template() -> dict:
    """Two independent native platforms. A checklist never certifies itself."""
    tests = []
    for platform in PLATFORMS:
        for name, phase, description in NATIVE_SCENARIOS:
            tests.append({
                "id": f"{platform}:{name}", "platform": platform,
                "qa_origin": phase + "/12", "scope": description,
                "status": "pending_native", "observations": "",
                "evidence": [], "game_version": "",
            })
    return {
        "schema": 1, "region": "HOENN", "kind": "MANUAL_NATIVE_QA_ONLY",
        "profile": "Hoenn QA Fase12", "native_approved": False,
        "readme": "Preencha observações após testes reais; este arquivo NÃO concede aprovação automática.",
        "tests": tests,
    }


def verify_test_stops_copy(copy: Path, manifest: dict) -> dict:
    """Read every physically staged map and check its QA landing tile.

    Only validates a private local copy; it does not run native Game.exe or
    prove trainer/surf/warp/puzzle event behavior in-game.
    """
    from server.ruby_marshal import loads
    from pilot_hoenn import SOURCE_MAPS, open_tile, validate_pilot_mapping
    from hoenn_qa_phase11 import localized_map_name

    path = copy / "Data/blue-hoenn-test-stops.txt"
    if not path.is_file() or path.is_symlink():
        raise ValueError("QA12: falta Data/blue-hoenn-test-stops.txt")
    raw = path.read_bytes()
    expected = manifest["qa_test_stops"]["sha256"]
    if hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError("QA12: hash do catálogo de teleporte não confere")
    lines = raw.decode("utf-8").splitlines()
    ids = validate_pilot_mapping(manifest)
    if not lines or lines.pop(0) != "BLUE_HOENN_TEST_STOPS_V1" or len(lines) != len(ids):
        raise ValueError("QA12: catálogo de teleporte incompleto")
    tilesets = loads((copy / "Data/Tilesets.rxdata").read_bytes())
    matched = set()
    for line in lines:
        parts = line.split("|", 5)
        if len(parts) != 6:
            raise ValueError("QA12: registro de teleporte inválido")
        try:
            src, dest, x, y, direction = map(int, parts[:5])
        except ValueError:
            raise ValueError("QA12: MapID ou posição de teleporte inválida") from None
        if (src not in ids or src in matched or ids[src] != dest
            or direction not in (2,4,6,8) or x < 0 or y < 0
            or parts[5] != localized_map_name(SOURCE_MAPS[src])):
            raise ValueError(f"QA12: teleporte de mapa original inválido: {src}")
        filepath = copy / f"Data/Map{dest:03}.rxdata"
        if filepath.is_symlink() or not filepath.is_file():
            raise ValueError(f"QA12: destino de teleporte ausente: {src}")
        world = loads(filepath.read_bytes())
        width, height = world.attrs["@width"], world.attrs["@height"]
        if not 0 <= x < width or not 0 <= y < height:
            raise ValueError(f"QA12: teleporte fora do mapa: {src}")
        events = world.attrs.get("@events", {})
        if any(event.attrs["@x"] == x and event.attrs["@y"] == y
               for event in events.values()):
            raise ValueError(f"QA12: teleporte em evento NPC/porta/obstáculo: {src}")
        tileset = tilesets[world.attrs["@tileset_id"]]
        if not open_tile(world, tileset, x, y):
            raise ValueError(f"QA12: teleporte em terreno sem passagem: {src}")
        if not any(open_tile(world, tileset, x+dx, y+dy)
                   for dx,dy in ((0,1),(0,-1),(1,0),(-1,0))):
            raise ValueError(f"QA12: teleporte sem saída caminhável: {src}")
        matched.add(src)
    if matched != ids.keys():
        raise ValueError("QA12: mapa sem posição de teleporte")
    ruby = (copy / "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb").read_text("utf-8")
    required = (
        "def self.test_tools?", "def self.test_stops",
        "def self.test_teleport(row)", "def self.test_menu",
        "BlueRegionTravel.move_to([native_id,x,y,direction])",
        "MenuHandlers.add(:pause_menu, :blue_hoenn_test_teleport",
    )
    missing = [part for part in required if part not in ruby]
    if missing:
        raise ValueError(f"QA12: menu nativo do teleporte não instalado: {missing}")
    return {"teleport_points_physically_checked": len(matched),
            "teleport_guarded_in_hoenn_test_only": True,
            "native_tested": False}


def verify_copy(copy: Path, report_dir: Path | None = None) -> dict:
    from hoenn_qa_phase1 import ROOT, UPSTREAM, require_private_path, verify_copy as check_base
    copy = require_private_path(copy)
    directory = require_private_path(report_dir or copy.parent)
    if copy.name != "hoenn-qa-fase12" or not copy.is_dir():
        raise ValueError("QA12 exige uma cópia nova no perfil isolado hoenn-qa-fase12")
    source = copy / "Hoenn pilot.json"
    manifest = json.loads(source.read_text("utf-8"))
    if (manifest.get("save_profile") != "Hoenn QA Fase12" or
        manifest.get("source_commit") != UPSTREAM or
        not isinstance(manifest.get("qa12"), dict)):
        raise ValueError("QA12: manifesto da cópia não corresponde à fase 12")
    expected = audit_generated(manifest)
    if manifest["qa12"] != expected:
        raise ValueError("QA12: manifesto integrado foi adulterado")
    # Recheck original Blue Game.exe and all 199 physical maps without
    # touching the installed game, save slots or any source archive.
    base = check_base(copy, ROOT / "game")
    if (base["maps_present"] != expected["maps_expected"] or
            base["distinct_save_profile"] != "Hoenn QA Fase12"):
        raise ValueError("QA12: Game.exe, save ou conjunto de mapas não correspondem ao original")
    reports = {}
    for phase, label, _ in AUDITS:
        file = require_private_path(directory / report_filename(label))
        if not file.is_file() or file.is_symlink():
            raise ValueError(f"QA12: relatório da fase {phase} ausente: {file.name}")
        reports[phase] = json.loads(file.read_text("utf-8"))
    checked = accepted_reports(reports, catalog_revision=manifest.get("catalog_revision", 1))
    teleport = verify_test_stops_copy(copy, manifest)

    # Reproducibility checksums: hashes of our staged private copy, NOT
    # proofs that native Game.exe ever launched or was heard/seen.
    fingerprints = {}
    for label, relative in {
        "manifest": "Hoenn pilot.json",
        "mapinfos": "Data/MapInfos.rxdata",
        "encounters": "PBS/encounters_hoenn_pilot.txt",
        "trainers": "PBS/trainers_hoenn_pilot.txt",
        "plugin": "Plugins/ZZZZZ Blue Hoenn Pilot/HoennPilot.rb",
        "cards": "Plugins/ZZZZ Blue Story and Presentation/RegionalCards.rb",
    }.items():
        path = copy / relative
        if path.is_symlink() or not path.is_file():
            raise ValueError(f"QA12: prova local ausente: {relative}")
        fingerprints[label + "_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    return {
        "schema": 1, "region": "HOENN", "qa_phase": "12/12",
        "status": "STATIC_QA_01_12_PASSED__NATIVE_ACCEPTANCE_PENDING",
        "technical_preparation_passed": True,
        "native_approved_phases": 0,
        "phase_count": 12,
        "game_exe_played_here": False, "android_joiplay_played_here": False,
        "native_game_exe_approved": False,
        "all_12_phases_playable_approved": False,
        "qa01_to_qa11": checked, "physical_map_count": base["maps_present"],
        "test_teleport": teleport,
        "source_commit": UPSTREAM, "save_profile": "Hoenn QA Fase12",
        "pending_native_cases": len(NATIVE_SCENARIOS) * len(PLATFORMS),
        "native_test_plan": manual_template()["tests"],
        "known_blockers": expected["unresolved_backlog"],
        "copy_fingerprints": fingerprints,
        "provenance": "local_private_copy_static_qa_only",
        "limitations": [
            "Sem evidência real de Game.exe: não há aprovação jogável da campanha.",
            "Sem execução Android/JoiPlay, saves reais, BGM, colisão, sprites ou créditos verificados.",
            "CI confirma contratos e testes sintéticos; não substitui walkthrough do jogador.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    from hoenn_qa_phase1 import WORK, require_private_path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--copy", type=Path, default=WORK / "hoenn-qa-fase12")
    parser.add_argument("--report", type=Path, default=WORK / "hoenn-qa-fase12-report.json")
    parser.add_argument("--manual", type=Path, default=WORK / "hoenn-qa-fase12-playtest.json")
    args = parser.parse_args(argv)
    target = None
    try:
        target = require_private_path(args.report)
        checklist = require_private_path(args.manual)
        result = verify_copy(args.copy, target.parent)
        checklist.parent.mkdir(parents=True, exist_ok=True)
        if not checklist.exists():
            # Never overwrite the player's observations on a subsequent run.
            with checklist.open("x", encoding="utf-8") as output:
                json.dump(manual_template(), output, ensure_ascii=False, indent=2)
                output.write("\n")
        if checklist.is_symlink():
            raise ValueError("QA12: checklist não pode ser symlink")
        code = 0
    except (OSError, TypeError, ValueError, KeyError, IndexError,
            json.JSONDecodeError) as err:
        result = {"schema": 1, "region": "HOENN", "qa_phase": "12/12",
                  "status": "BLOCKED_STATIC", "native_approved_phases": 0,
                  "native_game_exe_approved": False,
                  "all_12_phases_playable_approved": False, "errors": [str(err)]}
        code = 2
    if target is not None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "qa_phase": "12/12",
        "native_approved_phases": 0,
        "report": str(target) if target else None,
        "known_blockers": result.get("known_blockers", {}),
        "errors": result.get("errors", []),
    }, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
