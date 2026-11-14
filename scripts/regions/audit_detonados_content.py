"""Audit documented regional habitats and leader names against published Blue catalogs.

This is a READ-ONLY reference-vs-catalog review, not a PBS/RXDATA importer.
Site entries are NOT evidence that an NPC, trainer battle or encounter works.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = "data/regions/detonados-content-review.json"
CATALOG_PATHS = {
    "KANTO": "site/public/data/kanto.json",
    "JOHTO": "site/public/data/johto-pilot.json",
    "HOENN": "site/public/data/hoenn-pilot.json",
}
PREVIEW_PATH = "site/public/data/johto-preview.json"
ALIASES = {
    "viridianforest": "florestadeviridian",
    "sprouttower": "torresprout",
    "mtmoon": "mtmoon",
    "safarizone": "safarizone",
}
VALID_REGIONS = ("KANTO", "JOHTO", "HOENN", "SINNOH")


def normalize(value: str) -> str:
    """Normalize Portuguese/English route aliases without fuzzy map ID inference."""
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = value.lower().replace("rota ", "route ").replace("rotas ", "routes ")
    # Names in Kanto may include subtitles after an em dash.
    value = re.split(r"\s+[\u2014\u2013]\s+", value, 1)[0]
    return re.sub(r"[^a-z0-9]", "", value)


def location_matches(reference: str, actual: str) -> bool:
    wanted = normalize(reference)
    found = normalize(actual)
    wanted = ALIASES.get(wanted, wanted)
    found = ALIASES.get(found, found)
    if wanted == found:
        return True
    # Multi-floor location names: "Mt. Moon — 1F", "Safari Zone — ...".
    if wanted in ("mtmoon", "safarizone", "victoryroad", "unioncave", "granitecave"):
        return found.startswith(wanted)
    return False


def load_json(root: Path, relative: str) -> dict:
    with (root / relative).open(encoding="utf-8") as stream:
        return json.load(stream)


def extract_species(location: dict) -> set[str]:
    """Published catalog formats only; NEVER reinterpret weights or level caps."""
    species = set()
    for method in location.get("methods", []):
        for slot in method.get("slots", []):
            if isinstance(slot, dict) and isinstance(slot.get("species"), str):
                species.add(slot["species"].upper())
    for slots in location.get("encounters", {}).values():
        for slot in slots:
            if isinstance(slot, list) and slot and isinstance(slot[0], str):
                species.add(slot[0].upper())
    return species


def validate_manifest(manifest: dict, root: Path | None = None) -> None:
    if manifest.get("schema") != 1 or manifest.get("status") != "REFERENCE_ONLY_NEVER_AUTO_INSTALL":
        raise ValueError("Reference manifest schema or safety status invalid")
    regions = manifest.get("regions", {})
    if tuple(regions) != VALID_REGIONS:
        raise ValueError("The manifest must contain Kanto, Johto, Hoenn and Sinnoh in order")
    for region, data in regions.items():
        if len(data.get("leaders", [])) != 8 or len(set(data["leaders"])) != 8:
            raise ValueError(f"{region}: eight unique gym leaders required")
        if not data.get("areas"):
            raise ValueError(f"{region}: no habitat sample")
        seen = set()
        for area in data["areas"]:
            name = normalize(area["area"])
            if not name or name in seen:
                raise ValueError(f"{region}: duplicate/invalid habitat {area['area']!r}")
            seen.add(name)
            if area.get("verification") != "REFERENCE_NOT_NATIVE_VERIFIED":
                raise ValueError(f"{region}: cannot mark reference as installed")
            if any(not re.fullmatch(r"[A-Z0-9]+", s) for s in area["reference_species"]):
                raise ValueError(f"{region}: invalid reference species token")
            if len(set(area["reference_species"])) != len(area["reference_species"]):
                raise ValueError(f"{region}: duplicate species in {name}")
            # Levels and percentages may NOT be synthesized from summaries.
            if any(key in area for key in ("map_id", "rate", "levels", "weights", "installed")):
                raise ValueError(f"{region}: reference cannot assert runtime placement")
        if root is not None and not (root / data["doc"]).is_file():
            raise ValueError(f"{region}: source detonado missing: {data['doc']}")


def audit(root: Path = ROOT) -> dict:
    manifest = load_json(root, MANIFEST)
    validate_manifest(manifest, root)
    by_region = {}
    for region in VALID_REGIONS:
        source = manifest["regions"][region]
        catalog_path = CATALOG_PATHS.get(region)
        catalog = load_json(root, catalog_path) if catalog_path else None
        if catalog and region == "KANTO":
            locations = catalog["locations"]
            trainers = catalog["trainers"]
        elif catalog:
            locations = catalog["locations"]
            trainers = catalog["trainers"]
        else:
            locations, trainers = [], []
        present_trainers = {normalize(t.get("name", "")) for t in trainers}
        habitat_rows = []
        for record in source["areas"]:
            matches = [loc for loc in locations if location_matches(record["area"], loc["name"])]
            recorded = set().union(*(extract_species(loc) for loc in matches))
            missing = sorted(set(record["reference_species"]) - recorded)
            entry = {
                "area": record["area"],
                "catalog_locations": [loc["name"] for loc in matches],
                "reference_species_count": len(record["reference_species"]),
                "reference_species_not_in_catalog": missing,
                "status": (
                    "NO_GAMEPLAY_CATALOG" if not matches
                    else "CATALOG_REVIEW_REQUIRED" if missing
                    else "CATALOG_SPECIES_PRESENT_REVIEW_NATIVE"
                ),
                "gameplay_verified": False,
            }
            habitat_rows.append(entry)
        leaders = []
        for name in source["leaders"]:
            leaders.append({
                "name": name,
                "in_published_catalog": normalize(name) in present_trainers,
                "native_battle_verified": False,
            })
        planned_only = 0
        if region == "JOHTO":
            preview = load_json(root, PREVIEW_PATH)
            # A symbolic preview is intentionally NEVER counted as a live map.
            planned_only = sum(1 for row in preview.get("locations", []) if not row.get("in_game", False))
        by_region[region] = {
            "reference_game": source["game"],
            "detonado": source["doc"],
            "rankedboost": source["map_url"],
            "catalog": catalog_path,
            "reference_habitats_reviewed": len(habitat_rows),
            "catalog_missing_or_partial": sum(row["status"] != "CATALOG_SPECIES_PRESENT_REVIEW_NATIVE" for row in habitat_rows),
            "leaders_absent_from_published_catalog": [row["name"] for row in leaders if not row["in_published_catalog"]],
            "symbolic_preview_locations_not_counted_as_gameplay": planned_only,
            "habitats": habitat_rows,
            "leaders": leaders,
        }
    return {
        "schema": 1,
        "status": "CATALOG_AUDIT_ONLY_NOT_GAMEPLAY_PROOF",
        "message": "Missing means absent from public catalog or not mapped; never proof of missing native encounters. No files modified.",
        "regions": by_region,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Repository root")
    parser.add_argument("--output", type=Path, help="Write review JSON to this path (optional)")
    parser.add_argument("--strict", action="store_true", help="Exit 2 on catalog gaps")
    args = parser.parse_args(argv)
    report = audit(args.root)
    output = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
        print(f"Audit saved to {args.output}")
    else:
        print(output, end="")
    for region, item in report["regions"].items():
        print(
            f"{region}: {item['catalog_missing_or_partial']}/{item['reference_habitats_reviewed']} "
            f"habitats need catalog review; {len(item['leaders_absent_from_published_catalog'])} "
            "leaders absent from public catalog",
            file=sys.stderr,
        )
    if args.strict and any(
        row["catalog_missing_or_partial"] or row["leaders_absent_from_published_catalog"]
        for row in report["regions"].values()
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
