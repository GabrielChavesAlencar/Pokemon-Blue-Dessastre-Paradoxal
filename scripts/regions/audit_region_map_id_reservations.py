#!/usr/bin/env python3
"""CH05: audit declared MapID reservations without declaring any ID free.

Sources in GitHub are static contracts, not a native install snapshot.
Optionally compare a *local* READ_ONLY_INERT_RMXP report, while retaining
unknown ownership and an unconditional installation/allocator blockade.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = Path("data/regions/sinnoh-map-id-reservations.json")
REGIONS = frozenset({"DECADES", "KANTO", "JOHTO", "HOENN", "SINNOH"})
EXPECTED = {
    "JOHTO": (600, 699, "SHARED_PREVIEW_CODE_RESERVATION"),
    "HOENN": (700, 999, "SHARED_INSTALLER_CODE_RANGE"),
}
EVIDENCE = {
    "DECADES": ("scripts/install_game.py", "def ensure_base(project,game):"),
    "KANTO": ("scripts/regions/install_kanto.py",
              'mapping = {int(k): int(v) for k, v in info["maps"].items()}'),
    "JOHTO": ("scripts/regions/johto_main_preview.py",
              "PREVIEW_IDS = frozenset(range(600, 700))"),
    "HOENN": ("scripts/regions/pilot_hoenn.py",
              "free = [n for n in range(700, 1000) if n not in reserved]"),
    "SINNOH": ("scripts/regions/sinnoh_map_id_guard.py",
               "JOHTO_SINNOH_EXCLUSION = frozenset(range(600, 1000))"),
}
LEGACY_EVIDENCE = ("scripts/regions/pilot_sinnoh.py",
                   "IDS = dict(zip(NAMES, range(800, 806)))")


def fail(reason: str) -> None:
    raise ValueError("[SINNOH CH05] " + reason)


def read_json(path: Path) -> dict:
    obj = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(obj, dict):
        fail("documento deve ser um objeto JSON")
    return obj


def validate(manifest: dict, root: Path = ROOT) -> None:
    """Fail closed when sources, ownership labels or approval flags drift."""
    if (manifest.get("schema"), manifest.get("region"), manifest.get("mode")) != (
            1, "MULTIREGION", "DOCUMENTED_MAP_ID_CLAIMS_ONLY"):
        fail("modo/esquema inválido ou alegação de ocupação nativa")
    base = manifest.get("native_snapshot")
    if not isinstance(base, dict) or base != {
            "status": "NOT_PROVIDED", "occupied_ids": None,
            "ownership_by_region": None}:
        fail("ocupação física não pode ser declarada sem auditoria local")
    approval = manifest.get("allocation")
    if not isinstance(approval, dict) or approval != {
            "confirmed_free_ids": None, "confirmed_free_status": "UNKNOWN",
            "can_allocate": False, "can_install": False, "safe_to_merge": False}:
        fail("manifesto não pode liberar IDs, importação ou instalação")
    records = manifest.get("regions")
    if not isinstance(records, dict) or set(records) != REGIONS:
        fail("faltam regiões ou há regiões desconhecidas")
    for region in sorted(REGIONS):
        record = records[region]
        if not isinstance(record, dict):
            fail("registro regional inválido: " + region)
        if record.get("physical_occupied_ids") is not None:
            fail("ocupação física de " + region + " não foi comprovada")
        expected_dest = [] if region == "SINNOH" else None
        if record.get("known_shared_destinations") != expected_dest:
            fail("destinos presumidos sem prova: " + region)
        state = record.get("shared_destination_status")
        expected_state = {
            "DECADES": "UNKNOWN_REQUIRES_LOCAL_GAME_DATA",
            "KANTO": "UNKNOWN_DYNAMIC_PILOT_MAPPING",
            "JOHTO": "DOCUMENTED_PREVIEW_RESERVATION_NOT_INSTALLED_PROOF",
            "HOENN": "DOCUMENTED_INSTALLER_RANGE_NOT_INSTALLED_PROOF",
            "SINNOH": "NO_SHARED_IDS_ALLOCATED",
        }[region]
        if state != expected_state:
            fail("estado de evidência regional incorreto: " + region)
        sources = record.get("evidence")
        if not isinstance(sources, list) or not sources:
            fail("região sem fonte auditável: " + region)
        expected_source = EVIDENCE[region]
        if not any(isinstance(source, dict) and
                   (source.get("path"), source.get("contains")) == expected_source
                   for source in sources):
            fail("fonte principal não coincide com código: " + region)
        for source in sources:
            if (not isinstance(source, dict)
                    or set(source) != {"path", "contains"}
                    or not isinstance(source["path"], str)
                    or not isinstance(source["contains"], str)
                    or not source["contains"]):
                fail("fonte de evidência inválida: " + region)
            path = Path(source["path"])
            if path.is_absolute() or ".." in path.parts:
                fail("caminho fora do repositório")
            file = root / path
            if file.is_symlink() or not file.is_file():
                fail("fonte de evidência ausente: " + source["path"])
            if source["contains"] not in file.read_text(encoding="utf-8"):
                fail("contrato alterado sem revisão: " + source["path"])
    claims = manifest.get("documented_shared_reservations")
    if not isinstance(claims, list) or len(claims) != len(EXPECTED):
        fail("reservas declaradas incompletas ou adicionais sem prova")
    seen = set()
    for claim in claims:
        if not isinstance(claim, dict) or set(claim) != {
                "owner", "start", "end", "claim_type", "source"}:
            fail("formato de reserva inválido")
        owner = claim["owner"]
        if owner not in EXPECTED or owner in seen:
            fail("dono da reserva repetido/desconhecido")
        seen.add(owner)
        lo, hi, kind = EXPECTED[owner]
        if (type(claim["start"]) is not int or type(claim["end"]) is not int
                or (claim["start"], claim["end"], claim["claim_type"],
                    claim["source"]) != (lo, hi, kind, EVIDENCE[owner][0])):
            fail("faixa/documentação inconsistente: " + owner)
    if seen != set(EXPECTED):
        fail("faltam reservas regionais")
    exclusion = manifest.get("sinnoh_shared_exclusion")
    if exclusion != {
            "start": 600, "end": 999, "rule": "CONSERVATIVE_NO_NEW_SINNOH_MAPS",
            "source": "scripts/regions/sinnoh_map_id_guard.py"}:
        fail("faixa proibida para Sinnoh foi modificada")
    legacy = manifest.get("legacy_standalone")
    if legacy != {
            "region": "SINNOH", "start": 800, "end": 805,
            "mode": "STANDALONE_PILOT_ONLY_NOT_SHARED_RESERVATION",
            "source": LEGACY_EVIDENCE[0]}:
        fail("piloto 800–805 não pode virar reserva compartilhada")
    source = root / LEGACY_EVIDENCE[0]
    if source.is_symlink() or not source.is_file() or (
            LEGACY_EVIDENCE[1] not in source.read_text(encoding="utf-8")):
        fail("origem do piloto legado foi alterada")
    for key in ("unknown_ownership", "review_required"):
        value = manifest.get(key)
        if not isinstance(value, list) or not value or any(
                not isinstance(x, str) or not x.strip() for x in value):
            fail("campo de incertezas obrigatório: " + key)


def native_report(report: dict) -> set[int]:
    """Interpret user-supplied read-only audit as *reported*, not proof/permission."""
    if (report.get("schema"), report.get("region"), report.get("mode"),
            report.get("import_allowed")) != (
            1, "SINNOH", "READ_ONLY_INERT_RMXP", False):
        fail("relatório não veio do formato de auditoria inerte de Sinnoh")
    block = report.get("native")
    if not isinstance(block, dict) or block.get("status") != "LOCAL_READ_ONLY":
        fail("auditoria do game/Data não está disponível")
    values = block.get("occupied_ids")
    if (not isinstance(values, list)
            or any(type(x) is not int or x <= 0 for x in values)
            or len(set(values)) != len(values)):
        fail("ocupações observadas inválidas/duplicadas")
    return set(values)


def inspect_id(map_id: int, manifest: dict, *, observed: set[int] | None = None) -> dict:
    """Produce one status without allocating or attributing installed ownership."""
    if type(map_id) is not int or map_id <= 0:
        fail("MapID consultado precisa ser inteiro positivo")
    owners = [
        claim["owner"] for claim in manifest["documented_shared_reservations"]
        if claim["start"] <= map_id <= claim["end"]
    ]
    legacy = manifest["legacy_standalone"]
    return {
        "map_id": map_id,
        "documented_reservation_owners": owners,
        "reserved_by_code": bool(owners),
        "legacy_sinnoh_standalone_candidate":
            legacy["start"] <= map_id <= legacy["end"],
        "excluded_from_shared_sinnoh":
            600 <= map_id <= 999,
        "physical_observation": (
            "NO_LOCAL_REPORT" if observed is None else
            "REPORTED_OCCUPIED_UNATTRIBUTED" if map_id in observed
            else "NOT_REPORTED_OCCUPIED_NOT_PROOF_FREE"
        ),
        "physical_owner": None,
        "free_to_allocate": False,
        "import_approved": False,
        "requires_native_baseline_and_reservation_review": True,
    }


def report(manifest: dict, *, observed: set[int] | None = None,
           query_ids: list[int] | None = None) -> dict:
    ids = query_ids if query_ids is not None else [1, 500, 599, 600, 699,
                                                    700, 800, 805, 999, 1000]
    if any(type(x) is not int or x <= 0 for x in ids) or len(set(ids)) != len(ids):
        fail("MapIDs de consulta inválidos ou duplicados")
    return {
        "schema": 1, "region": "MULTIREGION",
        "mode": "INFORMATIONAL_READ_ONLY_NO_ALLOCATION",
        "native_report_supplied": observed is not None,
        "shared_installation_verified": False,
        "can_allocate": False, "can_install": False,
        "classified": [inspect_id(x, manifest, observed=observed) for x in ids],
    }


def main() -> int:
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--root", type=Path, default=ROOT)
    cli.add_argument("--manifest", type=Path,
                     help="manifesto CH05; padrão data/regions/sinnoh-map-id-reservations.json")
    cli.add_argument("--native-report", type=Path,
                     help="opcional: JSON do audit_sinnoh_rxdata.py com game/Data real")
    cli.add_argument("--id", dest="ids", type=int, action="append",
                     help="consultar ID (repetível, sem inferir disponibilidade)")
    args = cli.parse_args()
    try:
        document = read_json(args.manifest or args.root / MANIFEST)
        validate(document, args.root)
        physical = native_report(read_json(args.native_report)) if args.native_report else None
        result = report(document, observed=physical, query_ids=args.ids)
    except (ValueError, KeyError, OSError, UnicodeError, TypeError) as exc:
        print("SINNOH_MAP_ID_MANIFEST_BLOQUEADO: " + str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
