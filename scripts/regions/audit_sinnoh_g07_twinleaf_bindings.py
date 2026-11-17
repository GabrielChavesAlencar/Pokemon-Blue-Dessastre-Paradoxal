#!/usr/bin/env python3
"""G07: read-only Twinleaf physical-binding matrix from public offline contracts.

No map/source binaries, no user PC, no donor events, no arbitrary coordinates.
The CH06 symbolic graph is NOT evidence of installed links or a map-id mapping.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "scripts/regions") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts/regions"))

from audit_sinnoh_twinleaf_events import (
    audit as audit_ch06, MAPS, HANDLERS, BALLS, PAIRS
)

FILES = {
    "events": "data/regions/sinnoh-twinleaf-events.json",
    "schema": "data/regions/sinnoh-twinleaf-events.schema.json",
    "intro": "data/regions/sinnoh-intro-s13.json",
    "starters": "data/regions/sinnoh-starters-s14.json",
    "b07": "data/regions/sinnoh-b07-private-stage.json",
    "b08": "data/regions/sinnoh-b08-private-qa.json",
    "b09": "data/regions/sinnoh-b09-native-qa.json",
}
INTRO_FLAGS = (
    "mother_intro", "barry_intro", "rowan_briefcase_seen",
    "starter_received", "rival_fought", "pokedex_received",
)
INTRO_HANDLERS = (
    "mother", "barry_intro", "rowan_briefcase",
    "choose_starter_from_ball", "barry_rival", "rowan_pokedex",
)
INTRO_KIND = (
    "dialogue", "dialogue", "dialogue", "physical_starter",
    "confirmed_battle_can_lose", "engine_pokedex_flag",
)
BALL_ORDER = ("TURTWIG", "CHIMCHAR", "PIPLUP")
BARRY_COUNTER = {"TURTWIG": ("CHIMCHAR", 0),
                 "CHIMCHAR": ("PIPLUP", 1),
                 "PIPLUP": ("TURTWIG", 2)}
STEP_NULL = ("native_map_id", "native_event_id")
STEP_FALSE = ("native_callback_verified", "player_interaction_verified",
              "game_exe_verified", "joiplay_verified")
BALL_NULL = ("native_map_id", "native_event_id", "verified_position",
             "verified_sprite", "verified_native_callback")
BALL_FALSE = ("event_compiled", "grant_tested_in_game", "save_load_tested_in_game")


def blocked(reason: str) -> None:
    raise ValueError("SINNOH_G07_BLOCKED: " + reason)


def load_public(path: Path) -> dict:
    if (path.is_symlink() or not path.is_file()
            or path.stat().st_size > 250000):
        blocked("manifesto publico inacessivel ou inseguro")
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError, UnicodeError):
        blocked("JSON publico malformado")
    if type(data) is not dict:
        blocked("manifesto precisa ser objeto")
    return data


def require_false(source: dict, fields: tuple[str, ...], label: str) -> None:
    if type(source) is not dict:
        blocked("manifesto nao e objeto: " + label)
    for field in fields:
        if source.get(field) is not False:
            blocked(label + " falsamente aprovado: " + field)


def check_intro(intro: dict, events: dict, by_key: dict, balls: list[dict]) -> list[dict]:
    if (type(intro) is not dict or
            (intro.get("region"), intro.get("task"), intro.get("status")) != (
                "SINNOH", "S13", "INTRO_SEQUENCE_OFFLINE_ONLY_NOT_INSTALLED")
            or intro.get("source_events") != FILES["events"]
            or intro.get("step_count") != 6):
        blocked("contrato S13 incorreto")
    require_false(intro, (
        "source_sprites_verified", "start_spawn_verified", "game_exe_executed",
        "joiplay_executed", "native_qa_approved", "can_install",
        "gameplay_approved", "global_hooks_installed",
        "native_barry_pbs_compiled",
    ), "S13")
    if (type(intro.get("native_maps_compiled")) is not int
            or intro["native_maps_compiled"] != 0
            or type(intro.get("native_handlers_verified")) is not int
            or intro["native_handlers_verified"] != 0):
        blocked("S13 declarou mapas/handlers nativos")
    steps = intro.get("steps")
    if (type(steps) is not list or len(steps) != 6
            or [s.get("flag") if type(s) is dict else None for s in steps] != list(INTRO_FLAGS)):
        blocked("ordem de 6 checkpoints S13 adulterada")

    expected_balls = [{"map": b["map"], "event": b["key"],
                       "species": b["species"]} for b in balls]
    output = []
    for index, step in enumerate(steps):
        flag, handler, kind = INTRO_FLAGS[index], INTRO_HANDLERS[index], INTRO_KIND[index]
        source = by_key.get(step.get("event")) if kind != "physical_starter" else None
        if kind == "physical_starter":
            symbol = "SINNOH_LAKE_VERITY"
            key = None
            if step.get("physical_balls") != expected_balls:
                blocked("tres bolas fisicas diferem do roteiro CH06")
        else:
            if source is None or source["kind"] != "handler" or source["handler"] != handler:
                blocked("handler S13 sem evento CH06 correspondente: " + flag)
            symbol = source["map"]
            key = source["key"]
            if step.get("physical_balls") != []:
                blocked("step S13 inclui Pokebolas fora da escolha fisica")
        if (step.get("handler") != handler or step.get("kind") != kind
                or step.get("map") != symbol or step.get("event") != key
                or type(step.get("order")) is not int or step["order"] != index + 1
                or step.get("needs") != ([INTRO_FLAGS[index - 1]] if index else [])
                or step.get("status") != "OFFLINE_CONTRACT_ONLY"):
            blocked("dependencia, mapa ou evento de historia S13 adulterado: " + flag)
        if any(step.get(k) is not None for k in STEP_NULL):
            blocked("S13 atribuiu MapID/evento nativo sem verificacao")
        require_false(step, STEP_FALSE, "S13." + flag)
        output.append({
            "step": index + 1, "flag": flag, "handler": handler,
            "map": symbol, "event_key": key,
            "needs": step["needs"],
            "physical_starter_ball_keys": ([b["key"] for b in balls]
                                           if kind == "physical_starter" else []),
            "native_handler_verified": False,
            "status": "AUTHORING_ONLY_NOT_INSTALLED",
        })
    return output


def check_starters(starters: dict, balls: list[dict]) -> list[dict]:
    if (type(starters) is not dict or
            (starters.get("region"), starters.get("task"), starters.get("status")) != (
                "SINNOH", "S14", "PHYSICAL_STARTERS_OFFLINE_CONTRACT_NOT_INSTALLED")
            or starters.get("source_events") != FILES["events"]
            or starters.get("source_intro") != FILES["intro"]
            or starters.get("starter_count") != 3
            or starters.get("physical_interaction") != "action"
            or starters.get("grant_seed_level") != 5
            or starters.get("save_key") != "sinnoh_pilot"):
        blocked("contrato S14 alterado")
    require_false(starters, (
        "approved_for_install", "starter_selection_playable",
        "game_exe_verified", "joiplay_verified", "native_qa_approved",
        "source_assets_verified", "compiled_pbs_barry_verified",
        "cross_region_key_items_migrated", "can_write_game",
    ), "S14")
    if (starters.get("native_map_id") is not None or
            type(starters.get("native_compiled_events")) is not int or
            starters["native_compiled_events"] != 0 or
            type(starters.get("native_verified_starter_balls")) is not int or
            starters["native_verified_starter_balls"] != 0 or
            starters.get("verified_native_sources") != {}):
        blocked("prova fisica S14 inventada")
    rows = starters.get("balls")
    if type(rows) is not list or len(rows) != 3:
        blocked("S14 sem exatamente 3 bolas")
    by_species = {b["species"]: b for b in balls}
    if set(by_species) != set(BALL_ORDER) or len(by_species) != 3:
        blocked("trio CH06 ausente/duplicado")
    out = []
    for i, species in enumerate(BALL_ORDER):
        row = rows[i]
        source = by_species[species]
        expected = BARRY_COUNTER[species]
        if (type(row) is not dict
                or row.get("species") != species
                or row.get("event_key") != source["key"]
                or row.get("map_symbol") != source["map"]
                or row.get("trigger") != "action"
                or row.get("rival_species") != expected[0]
                or type(row.get("rival_pbs_version")) is not int
                or row["rival_pbs_version"] != expected[1]
                or row.get("status") != "AUTHOR_ONLY_NOT_INSTALLED"):
            blocked("S14/Pokebola/rival nao correspondem a CH06: " + species)
        if any(row.get(k, "MISSING") is not None for k in BALL_NULL):
            blocked("S14 inventou binding fisico de Pokebola")
        require_false(row, BALL_FALSE, "S14." + species)
        out.append({
            "species": species, "event_key": source["key"],
            "map_symbol": source["map"], "trigger": "action",
            "barry_counter_species": expected[0], "barry_pbs_version": expected[1],
            "sprite": None, "native_map_id": None,
            "native_event_id": None, "position": None,
            "status": "PENDING_PHYSICAL_BALL_AND_NATIVE_PBS",
        })
    return out


def check_geometry(b07: dict, b08: dict, b09: dict) -> dict:
    if any(type(x) is not dict for x in (b07, b08, b09)):
        blocked("contratos geometricos ausentes")
    if ((b07.get("region"), b07.get("stage")) != ("SINNOH", "B07")
            or (b08.get("region"), b08.get("stage")) != ("SINNOH", "B08")
            or (b09.get("region"), b09.get("stage")) != ("SINNOH", "B09")):
        blocked("cadeia B07-B09 nao corresponde a Sinnoh")
    if (b07.get("candidate_terrain_destinations") != list(range(442, 496))
            or b07.get("excluded_empty_destinations") != list(range(496, 518))
            or b08.get("expected_staged_terrain_ids") != list(range(442, 496))
            or b08.get("excluded_empty_ids") != list(range(496, 518))
            or b09.get("candidate_installed_sinnoh_ids") != list(range(442, 496))
            or b09.get("sinnoh_empty_placeholder_ids") != list(range(496, 518))
            or type(b09.get("expected_qa_clone_map_count")) is not int
            or b09.get("expected_qa_clone_map_count") != 702
            or type(b09.get("expected_installed_native_map_count")) is not int
            or b09["expected_installed_native_map_count"] != 648
            or b09.get("expected_sinnoh_terrain_maps_in_clone") != 54):
        blocked("geometrias/MapIDs/contagem B07-B09 nao reconciliados")
    if (b08.get("b07_source_sha256") != b07.get("source_zip_sha256")
            or b09.get("native_baseline_mapinfos_sha256") != b07.get("native_mapinfos_sha256")
            or b09.get("native_baseline_tilesets_sha256") != b07.get("native_tilesets_sha256")):
        blocked("proveniencia B07-B09 quebrada")
    if (b07.get("imports_donor_events") is not False
            or b07.get("imports_donor_scripts") is not False
            or b07.get("imports_donor_pbs") is not False
            or b07.get("preserves_saves") is not True
            or b08.get("overlay_is_a_non_runnable_private_copy") is not True):
        blocked("B07/B08 passou a incluir eventos estrangeiros ou instalacao")
    require_false(b07, (
        "can_install_into_game", "rights_per_asset_verified",
        "r07_complete", "r08_complete", "r09_complete",
        "native_game_exe_tested", "joiplay_tested",
    ), "B07")
    require_false(b08, (
        "can_install", "can_mark_gameplay", "has_live_stage_evidence",
        "r07_complete", "r08_complete", "r09_complete", "rights_per_asset_verified",
    ), "B08")
    require_false(b09, (
        "runtime_save_isolation_verified", "future_reservations_verified",
        "third_party_asset_rights_verified", "game_exe_tested", "joiplay_tested",
        "can_install_live_game", "can_mark_native_playable", "r07_complete",
        "r08_complete", "r09_complete",
    ), "B09")
    for stage in (b07, b08, b09):
        if any(type(stage.get(k)) is not int or stage[k] != 0 for k in (
                "phase_b_approved", "phase_c_approved", "phase_d_approved")):
            blocked("fase nativa falsamente aprovada B07-B09")
    return {
        "terrain_candidate_count": 54,
        "empty_placeholders_not_installed": 22,
        "clone_map_count_declared_by_b09_contract": 702,
        "terrain_candidate_window": [442, 495],
        "symbol_to_terrain_map_link_proven": False,
        "donor_events_present_in_private_geometry": False,
        "source_or_runtime_physical_data_read": False,
    }


def audit(events: dict, schema: dict, intro: dict, starters: dict,
          b07: dict, b08: dict, b09: dict) -> dict:
    try:
        ch06 = audit_ch06(events, schema)
    except (ValueError, TypeError, KeyError) as err:
        blocked("CH06 simbolos e topologia invalidos")
    if (ch06.get("maps"), ch06.get("events"), ch06.get("warps"),
        ch06.get("handlers"), ch06.get("starter_balls"),
        ch06.get("bidirectional_pairs"), ch06.get("coordinates_mode")) != (
            9, 24, 16, 5, 3, 8, "NULL_UNVERIFIED_TEMPLATE"):
        blocked("CH06 alterou escopo ou fabricou geometria")
    if events.get("approved_for_install") is not False or events.get("gameplay_verified") is not False:
        blocked("template Twinleaf nao pode ser declarada jogavel")
    if events.get("start") != {
        "symbol": "SINNOH_PLAYER_BEDROOM", "map_id": None,
        "x": None, "y": None, "verified_position": False,
        "passability_verified": False,
    }:
        blocked("spawn fisico foi inventado")
    symbols = [x["symbol"] for x in events["maps"]]
    if tuple(symbols) != MAPS:
        blocked("ordem canonica dos 9 mapas mudou sem reconciliar historia")
    by_key = {}
    directed = {}
    handler_rows = []
    ball_rows = []
    map_rows = []
    for m in events["maps"]:
        sym = m["symbol"]
        if m["map_id"] is not None or m["map_sha256"] is not None:
            blocked("mapa simbolico recebeu MapID ou SHA nao comprovado")
        output_events = []
        for e in m["events"]:
            if e["key"] in by_key:
                blocked("key duplicada")
            by_key[e["key"]] = {"map": sym, **e}
            if (e["verified_position"] is not False or e["x"] is not None
                    or e["y"] is not None):
                blocked("posicao fisica sem mapa verificado")
            item = {"key": e["key"], "kind": e["kind"],
                    "position": None, "native_event_id": None,
                    "physical_binding_verified": False}
            if e["kind"] == "warp":
                if (e["arrival_x"] is not None or e["arrival_y"] is not None
                        or e["verified_arrival"] is not False):
                    blocked("chegada nativa indevidamente declarada")
                directed[(sym, e["destination"])] = e["key"]
                item["destination_symbol"] = e["destination"]
                item["arrival_position"] = None
                item["native_transfer_verified"] = False
            else:
                if e["sprite"] is not None or e["verified_sprite"] is not False:
                    blocked("sprite fisico declarado sem fonte")
                if e["kind"] == "handler":
                    handler_rows.append({
                        "key": e["key"], "handler": e["handler"],
                        "map_symbol": sym, "native_event_id": None,
                        "sprite": None, "position": None,
                        "status": "PENDING_NATIVE_HANDLER_AND_SPRITE",
                    })
                elif e["kind"] == "starter_ball":
                    ball_rows.append({"key": e["key"], "species": e["species"],
                                      "map": sym})
                else:
                    blocked("kind de evento inesperado")
            output_events.append(item)
        map_rows.append({
            "symbol": sym, "native_map_id": None, "map_sha256": None,
            "map_dimensions_verified": False,
            "position_geometry_verified": False, "passability_verified": False,
            "candidate_terrain_mapping_verified": False,
            "planned_event_count": len(output_events),
            "planned_events": output_events,
            "status": "PENDING_REAL_MAP_IDENTIFICATION",
        })

    if set((r["key"], r["map_symbol"], r["handler"]) for r in handler_rows) != {
        (key, place, handler) for key, (place, handler) in HANDLERS.items()
    }:
        blocked("chaves/locais dos cinco handlers diferem do contrato CH06")
    if set((r["key"], r["map"], r["species"]) for r in ball_rows) != {
        (key, place, species) for key, (place, species) in BALLS.items()
    }:
        blocked("Pokebolas diferem do contrato CH06")
    balls_ordered = sorted(ball_rows, key=lambda x: BALL_ORDER.index(x["species"]))
    story = check_intro(intro, events, by_key, balls_ordered)
    starters_matrix = check_starters(starters, balls_ordered)
    geometry = check_geometry(b07, b08, b09)

    pairs = []
    for pair in sorted(PAIRS, key=lambda group: sorted(group)):
        a, b = sorted(pair)
        if (a, b) not in directed or (b, a) not in directed:
            blocked("par de transferencias nao reciproco")
        pairs.append({
            "source_symbol": a, "destination_symbol": b,
            "forward_event_key": directed[(a, b)],
            "return_event_key": directed[(b, a)],
            "forward_native_event_id": None,
            "return_native_event_id": None,
            "arrival_passability_verified": False,
            "status": "SYMBOLIC_TWO_WAY_ONLY_NOT_INSTALLED",
        })
    if len(pairs) != 8 or len(directed) != 16:
        blocked("contagens 8 pares/16 warps alteradas")

    return {
        "schema": 1, "region": "SINNOH", "stage": "G07",
        "status": "TWINLEAF_SYMBOLIC_BINDING_MATRIX_ONLY_NATIVE_EVIDENCE_PENDING",
        "mode": "READ_ONLY_GITHUB_STATIC_CONTRACTS",
        "maps": map_rows, "reciprocal_pairs": pairs,
        "story_checkpoints": story, "handler_bindings": handler_rows,
        "starter_balls": starters_matrix,
        "start_spawn": {
            "symbol": "SINNOH_PLAYER_BEDROOM", "native_map_id": None,
            "x": None, "y": None,
            "passability_verified": False, "native_spawn_verified": False,
        },
        "terrain_stage": geometry,
        "counts": {
            "symbolic_maps": 9, "planned_events": 24,
            "planned_warps": 16, "reciprocal_pairs": 8,
            "planned_handlers": 5, "planned_physical_starter_balls": 3,
            "story_checkpoints": 6, "physically_bound_maps": 0,
            "physically_bound_events": 0, "native_transfers_verified": 0,
            "physical_starter_balls_verified": 0,
        },
        "gate_order": [
            "Identify each of nine symbols in authorized real map geometry with MapID and SHA, without reusing Johto/Hoenn IDs",
            "Verify each map's real dimensions and collision/passability, and start bedroom spawn",
            "Verify all 16 portals' event tiles and arrival tiles in both directions",
            "Verify five handlers' physical events, sprites, and trusted callbacks",
            "Verify the three Lake Verity ball objects, sprites and Barry PBS versions 0/1/2",
            "Compile authored events only into a private QA copy after full independent evidence",
            "Perform Windows Sandbox B10/B11 and native Game.exe/JoiPlay playtests before acceptance",
        ],
        "asset_rights_verified": False,
        "real_native_map_evidence_inspected_on_github": False,
        "game_exe_tested": False, "joiplay_tested": False,
        "r07_complete": False, "r08_complete": False, "r09_complete": False,
        "can_install_live_game": False, "gameplay_approved": False,
        "phase_b_approved": 0, "phase_c_approved": 0, "phase_d_approved": 0,
    }


def run(root: Path = ROOT) -> dict:
    return audit(**{name: load_public(root / path) for name, path in FILES.items()})


def main(argv=None) -> int:
    if argv not in (None, []):
        blocked("G07 nao aceita caminhos ou arquivos privados como entrada")
    try:
        print(json.dumps(run(), ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, ValueError, KeyError, TypeError):
        print("SINNOH_G07_BLOCKED: contratos publicos inconsistentes",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
