#!/usr/bin/env python3
"""Conservative, read-only map-ID guards at shared-region installation boundaries.

Sinnoh's six-map 800..805 pilot is STRICTLY standalone. The range 600..999
is excluded by Sinnoh's current shared-game plan, even though the live
Johto/Hoenn ownership within it may differ. No ID is allocated here.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Mapping

SINNOH_SHARED_MAX = 599
JOHTO_SINNOH_EXCLUSION = frozenset(range(600, 1000))
LEGACY_SINNOH_PILOT_IDS = frozenset(range(800, 806))
JOHTO_SHARED_PREVIEW_IDS = frozenset(range(600, 700))
MAP_FILE = re.compile(r"Data/Map([0-9]+)\.rxdata\Z", re.IGNORECASE)
MAP_LIKE = re.compile(r"Data/Map[0-9]", re.IGNORECASE)


def assert_sinnoh_shared_destinations(destinations: Iterable[int]) -> None:
    """Reject unapproved Sinnoh destinations; never change a donor mapping.

    Existing maps are handled separately by the native MapInfos/PBS audit.
    Accept no implicit four-digit IDs or destinations in Johto/Hoenn space.
    """
    if isinstance(destinations, (str, bytes, Mapping)):
        raise ValueError("Sinnoh: destinos precisam ser IDs inteiros explícitos")
    try:
        values = list(destinations)
    except TypeError as error:
        raise ValueError("Sinnoh: destinos precisam ser lista de MapIDs") from error
    if not values or any(type(mid) is not int for mid in values):
        raise ValueError("Sinnoh: destinos devem ser MapIDs inteiros válidos")
    if len(values) != len(set(values)):
        raise ValueError("Sinnoh: MapID de destino duplicado")
    for mid in values:
        if mid in LEGACY_SINNOH_PILOT_IDS:
            raise ValueError(
                f"Sinnoh legado: MapID {mid} está na faixa reservada 600–999; "
                "somente piloto isolado, nunca jogo multirregional "
                "(limite conservador 1..599)"
            )
        if not 1 <= mid <= SINNOH_SHARED_MAX:
            raise ValueError(
                f"Sinnoh: MapID {mid} fora do limite conservador 1..599; "
                "600–999 excluídos e IDs >=1000 ainda não validados"
            )


def assert_johto_shared_overlay_map_ids(
    files: Mapping[str, bytes], *, allowed_ids: frozenset[int] = JOHTO_SHARED_PREVIEW_IDS
) -> frozenset[int]:
    """Validate staged new map files before Johto's shared installer writes.

    Compare *new map file paths*, not all MapInfos keys: a previously installed
    Hoenn may legitimately contain IDs 800..805. Never delete or overwrite
    those native maps merely because they coincide with old Sinnoh pilot IDs.
    """
    if not isinstance(files, Mapping) or not files:
        raise ValueError("Johto: overlay compartilhado ausente")
    if (not isinstance(allowed_ids, frozenset) or not allowed_ids
            or any(type(mid) is not int or mid not in JOHTO_SHARED_PREVIEW_IDS
                   for mid in allowed_ids)):
        raise ValueError("Johto: reserva esperada inválida")
    found: set[int] = set()
    canonical_names: set[str] = set()
    for path in files:
        if not isinstance(path, str):
            raise ValueError("Johto: nome de arquivo do overlay não é texto")
        lower = path.casefold()
        if lower in canonical_names:
            raise ValueError("Johto: caminhos duplicados por caixa de letras")
        canonical_names.add(lower)
        if path.startswith("/") or "\\" in path or ".." in path.split("/"):
            raise ValueError("Johto: caminho inseguro no overlay")
        match = MAP_FILE.fullmatch(path)
        if match is None:
            if MAP_LIKE.match(path):
                raise ValueError("Johto: formato inesperado de arquivo MapID " + path)
            continue
        mid = int(match.group(1))
        if mid in found:
            raise ValueError(f"Johto: MapID {mid} duplicado no overlay")
        found.add(mid)
        if mid in LEGACY_SINNOH_PILOT_IDS:
            raise ValueError(
                f"Johto: MapID {mid} é do piloto legado de Sinnoh; "
                "não pode ser injetado na instalação multirregional"
            )
        if mid not in allowed_ids:
            raise ValueError(
                f"Johto: MapID {mid} fora dos mapas 600–699 desta prévia; "
                "não incorporar regiões externas"
            )
    if not found:
        raise ValueError("Johto: nenhum mapa novo no overlay")
    return frozenset(found)
