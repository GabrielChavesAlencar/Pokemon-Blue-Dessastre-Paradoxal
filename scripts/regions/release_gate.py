"""Phase 16 release-readiness gate for experimental Kanto.

This verifies catalog, maps, trainer references, badges, probabilities,
registry status and optional isolated-build mapping. It cannot prove walking,
battle UI, graphical collisions or JoiPlay; it ALWAYS leaves manual acceptance
open. Reports remain in .blue-work and never upload save games.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit import KANTO, ROOT, json_file, stable_source_order
from export_kanto import LOCATION_NAMES, slug
from pbs import ENCOUNTER_REVIEW_SOURCE_IDS

BADGES = (
    ("Brock", "BOULDER"), ("Misty", "CASCADE"), ("Lt. Surge", "THUNDER"),
    ("Erika", "RAINBOW"), ("Koga", "SOUL"), ("Sabrina", "MARSH"),
    ("Blaine", "VOLCANO"), ("Giovanni", "EARTH"),
)
BLOCKERS = (
    "Etapa 02: caminhar, portas, eventos, batalhas reais e save/reload no Windows",
    "Fase 16: percurso completo e HMs reais (Strength/Surf/Cut/Flash) sem atalhos",
    "Route 23 Map209: método LandDay duplicado, encontros não liberados",
    "Independência FireRed/LeafGreen: conferir exclusividades das ROMs oficiais",
    "Itens, histórias/quests, sprites, sons, créditos e licenças pendentes",
    "JoiPlay/Android: controles, mapa, captura, batalhas e saves reais",
    "Pós-Liga: verificar PC, especiais, NPC de viagem, retorno e save legado",
)


def inspect(root: Path = ROOT, pilot: Path | None = None,
            manual_report: Path | None = None) -> dict:
    manifest = json_file(root / "data/regions/kanto-source.json")
    registry = json_file(root / "site/public/data/regions.json")
    site = json_file(root / "site/public/data/kanto.json")
    dex = json_file(root / "site/public/data/catalog.json")
    expected_ids = {int(key) for key in manifest["maps"]}
    if len(expected_ids) != 142:
        raise ValueError("Stage-16 Kanto map catalog must keep 142 IDs")
    expected_order = stable_source_order(expected_ids)
    if len(expected_order) != len(set(expected_order)) or set(expected_order) != expected_ids:
        raise ValueError("Kanto source ID plan is corrupt")
    if len(expected_order[:127]) != 127 or expected_order[126] != 13:
        raise ValueError("Previous Kanto save IDs were shifted")
    preview = set(manifest["preview_only"])
    if len(preview) != 35 or not preview.issubset(expected_ids):
        raise ValueError("35 geometry-only previews must remain protected")
    review = set(ENCOUNTER_REVIEW_SOURCE_IDS)
    if review != {209} or review & preview:
        raise ValueError("Unreviewed Route 23 wild encounter exception changed")
    official = registry["regions"]["KANTO"]
    if official["status"] != "prototype":
        raise ValueError("Cannot mark Kanto playable before real Windows/JoiPlay acceptance")
    names = [name for name, badge in BADGES]
    badges = [badge for _, badge in BADGES]
    if official["milestones"] != badges:
        raise ValueError("Regional milestone order no longer matches the eight Kanto gyms")
    if site.get("version") != 1 or len(site["locations"]) != 142 or len(site["trainers"]) != 144:
        raise ValueError("Kanto portal is not synchronized with 142 maps/144 grouped trainers")

    locations = {loc["id"]: loc for loc in site["locations"]}
    if len(locations) != len(site["locations"]):
        raise ValueError("Duplicate location IDs in Kanto portal")
    expected_locations = {
        slug(key): (int(original), key, name)
        for original, key in manifest["maps"].items()
        for name in (LOCATION_NAMES[key],)
    }
    if set(locations) != set(expected_locations):
        raise ValueError("Portal locations diverge from the verified FRLG map manifest")
    by_source = {int(k):slug(key) for k,key in manifest["maps"].items()}
    for original, ident in by_source.items():
        loc = locations[ident]
        expected_status = ("preview" if original in preview else
                           "encounter_review" if original in review else "experimental")
        if loc["status"] != expected_status:
            raise ValueError(f"Incorrect prototype/preview/review classification: {ident}")
        if original in preview and (loc["methods"] or loc["trainers"]):
            raise ValueError(f"Preview was accidentally activated: {ident}")
        if original in review and loc["methods"]:
            raise ValueError("Map209 received unofficial/mixed encounter probabilities")

    species = {mon["id"] for mon in dex["species"]}
    # The editable FRLG kit uses mixed-case PBS IDs NIDORANfE/NIDORANmA;
    # the public Pokédex stores NIDORANFE/NIDORANMA. This is a DISPLAY
    # alias only: never rewrite Pokémon species in native PBS or saves.
    normalize_species = lambda value: value.upper()
    display_species = {normalize_species(ident) for ident in species}
    if len(species) != len(dex["species"]):
        raise ValueError("Duplicate species in Pokédex")
    trainer_ids = {item["id"] for item in site["trainers"]}
    if len(trainer_ids) != len(site["trainers"]):
        raise ValueError("Duplicate Kanto trainer IDs")
    linked = []
    for loc in site["locations"]:
        for trainer_id in loc["trainers"]:
            if trainer_id not in trainer_ids:
                raise ValueError(f"Missing trainer referenced by location {loc['id']}: {trainer_id}")
            linked.append(trainer_id)
    if len(linked) != len(trainer_ids) or set(linked) != trainer_ids:
        raise ValueError("Every trainer must occur in exactly one area")
    actual_leaders = {t["name"] for t in site["trainers"] if t["leader"]}
    if actual_leaders != set(names):
        raise ValueError("Gym leader catalog does not match eight badge rewards")
    trainer_locations = locations.keys()
    for trainer in site["trainers"]:
        if trainer["location"] not in trainer_locations:
            raise ValueError(f"Unmapped trainer: {trainer['name']}")
        if not trainer["variants"]:
            raise ValueError(f"Trainer team missing: {trainer['name']}")
        for variant in trainer["variants"]:
            if not variant["team"]:
                raise ValueError("Empty trainer party")
            for pokemon in variant["team"]:
                if normalize_species(pokemon["species"]) not in display_species:
                    raise ValueError("Pokémon not in site Pokédex: " + pokemon["species"])
                if not 1 <= pokemon["level"] <= 100:
                    raise ValueError("Invalid trainer Pokémon level")

    wild_locations = 0
    methods = 0
    encounter_species = set()
    for loc in site["locations"]:
        if loc["methods"]:
            wild_locations += 1
        for method in loc["methods"]:
            methods += 1
            if not method["slots"]:
                raise ValueError(f"Empty encounter table: {loc['id']}")
            total = sum(row["weight"] for row in method["slots"])
            if total != method["weightTotal"] or total <= 0:
                raise ValueError(f"Invalid source weight total: {loc['id']}")
            if abs(sum(row["chance"] for row in method["slots"]) - 100) > 0.000001:
                raise ValueError(f"Chances not normalized to 100: {loc['id']}")
            for slot in method["slots"]:
                encounter_species.add(slot["species"])
                if normalize_species(slot["species"]) not in display_species:
                    raise ValueError(f"Wild Pokémon absent from site's Pokédex: {slot['species']}")
                if (slot["weight"] <= 0 or
                    not 1 <= slot["min"] <= slot["max"] <= 100):
                    raise ValueError("Illegal encounter level or source weight")
    if wild_locations != 26 or methods != 88 or len(encounter_species) != 67:
        raise ValueError("Audited wild content differs from the portal")

    isolated = None
    if pilot is not None:
        from pilot_catalog import prepared_plan
        plan = prepared_plan(pilot, manifest)
        mapping = {row["source_id"]:row["proposed_id"] for row in plan["maps"]}
        if len(mapping) != 142 or len(set(mapping.values())) != 142:
            raise ValueError("Compiled pilot map IDs are incomplete")
        # The canonical stable order must also remain stable for old saves,
        # despite lower-numbered source IDs appended in later phases.
        if [mapping[k] for k in expected_order] != sorted(mapping.values()):
            raise ValueError("Compiled map slots are no longer in stable save order")
        from verify_pilot import inspect as verify
        structural = verify(pilot)
        if structural["preview_event_count"] != 0 or structural["experimental_stops"] != 64:
            raise ValueError("Pilot contains unsafe preview events or lost testing destinations")
        isolated = {
            "map_count":structural["maps"],
            "preview_count":structural["preview_geometry_only"],
            "qa_test_destinations":structural["experimental_stops"],
            "transfers_check":"directed reachability and return path verified",
        }

    manual = {"supplied": False, "reviewed": False, "accepted_integrally": False}
    if manual_report:
        local = json_file(manual_report)
        if (local.get("schema") != 2 or
            local.get("type") != "manual_observation_unreviewed" or
            local.get("summary", {}).get("accepted_integrally") is not False):
            raise ValueError("Manual QA report must be unreviewed v2, not forged accepted")
        manual = {
            "supplied":True,
            "reviewed":False,
            "accepted_integrally":False,
            "summary":local["summary"],
            "platform":local.get("platform"),
        }
    return {
        "phase":16,
        "stage":"automated_release_preflight",
        "ci_preflight_passed":True,
        "declared_playable":False,
        "accepted_integrally":False,
        "source":"Essentials FRLG 1.1; independent official FR/LG equivalence pending",
        "map_count":len(expected_ids),
        "preview_maps":len(preview),
        "prototype_maps":len(expected_ids-preview),
        "encounter_review_maps":sorted(review),
        "trainers":len(trainer_ids),
        "regional_badges":badges,
        "wild_locations":wild_locations,
        "wild_methods":methods,
        "wild_species":len(encounter_species),
        "experimental_build":isolated,
        "manual_report":manual,
        "blocking_checks":list(BLOCKERS),
        "next_step":"manual interactive Windows and JoiPlay acceptance; fix defects before playable",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot",type=Path,default=None)
    parser.add_argument("--manual-report",type=Path,default=None)
    parser.add_argument("--output",type=Path,default=ROOT/".blue-work/kanto-phase-16-release-gate.json")
    args=parser.parse_args()
    workspace=(ROOT/".blue-work").resolve()
    if not args.output.resolve().is_relative_to(workspace):
        parser.error("O relatório deve ser salvo em .blue-work, nunca em saves ou game/")
    result=inspect(ROOT,args.pilot,args.manual_report)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("KANTO_RELEASE_GATE:"+json.dumps(result,ensure_ascii=True))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
