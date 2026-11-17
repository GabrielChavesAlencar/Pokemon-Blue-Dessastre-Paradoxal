#!/usr/bin/env python3
"""U03: validate a *symbolic*, non-playable Unova Black/White area catalog.

No installation, MapID allocation, game state, or source metadata is altered.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / 'data/regions/unova-u03-areas.json'
SITE_REGISTRY = ROOT / 'site/public/data/regions.json'
EXPECTED_BADGES = ('TRIO', 'BASIC', 'INSECT', 'BOLT', 'QUAKE', 'JET', 'FREEZE', 'LEGEND')
EXPECTED_GYMS = {
    'UNOVA_STRIATON_GYM', 'UNOVA_NACRENE_GYM', 'UNOVA_CASTELIA_GYM',
    'UNOVA_NIMBASA_GYM', 'UNOVA_DRIFTVEIL_GYM', 'UNOVA_MISTRALTON_GYM',
    'UNOVA_ICIRRUS_GYM', 'UNOVA_OPELUCID_GYM',
}
EXPECTED_CRITICAL = {
    'UNOVA_NUVEMA_TOWN', 'UNOVA_ACCUMULA_TOWN', 'UNOVA_WHITE_FOREST',
    'UNOVA_NS_CASTLE', 'UNOVA_VICTORY_ROAD', 'UNOVA_ELITE_FOUR',
    'UNOVA_DRAGONSPIRAL_TOWER', 'UNOVA_RELIC_CASTLE',
}
KEY = re.compile(r'UNOVA_[A-Z][A-Z0-9_]{3,72}\Z')
PHASE = re.compile(r'U(?:0[7-9]|1[0-9]|2[0-9]|30)\Z')


def validate(catalog: dict, region: dict) -> dict:
    if not isinstance(catalog, dict) or (
        catalog.get('schema'), catalog.get('region'), catalog.get('phase'),
        catalog.get('state'), catalog.get('may_install'),
        catalog.get('unova_game_files_audited')) != (
        1, 'UNOVA', 'U03', 'PLANNED_REFERENCE_ONLY', False, False
    ):
        raise ValueError('UNOVA U03: cabeçalho nao pode aprovar importacao')
    if catalog.get('reference_version') != 'WHITE_BW':
        raise ValueError('UNOVA U03: campanha precisa ser White BW original')
    if not isinstance(region, dict) or region.get('status') != 'planned':
        raise ValueError('UNOVA U03: registro regional nao deve ser jogavel')
    if tuple(region.get('milestones', ())) != EXPECTED_BADGES:
        raise ValueError('UNOVA U03: insígnias incorretas')
    areas = catalog.get('areas')
    if not isinstance(areas, list) or not 50 <= len(areas) <= 500:
        raise ValueError('UNOVA U03: catalogo incompleto')
    ids = set()
    gyms = set()
    routes = set()
    phases = Counter()
    for row in areas:
        if not isinstance(row, dict):
            raise ValueError('UNOVA U03: area invalida')
        key = row.get('key')
        if not isinstance(key, str) or not KEY.fullmatch(key) or key in ids:
            raise ValueError('UNOVA U03: chave invalida/duplicada')
        ids.add(key)
        phase = row.get('phase')
        if not isinstance(phase, str) or not PHASE.fullmatch(phase):
            raise ValueError('UNOVA U03: fase fora do plano U07–U30')
        phases[phase] += 1
        if (not isinstance(row.get('name'), str) or not row['name'].strip()
                or row.get('state') != 'planned'
                or row.get('source_map_id') is not None
                or row.get('destination_map_id') is not None
                or row.get('npc_events_verified') is not False
                or row.get('distribution_rights_verified') is not False
                or row.get('game_exe_tested') is not False):
            raise ValueError('UNOVA U03: area anuncia fonte, MapID ou gameplay ficticio')
        if row.get('kind') == 'gym':
            gyms.add(key)
        if row.get('kind') == 'route':
            routes.add(key)
    if gyms != EXPECTED_GYMS:
        raise ValueError('UNOVA U03: faltam ginásios White / Iris')
    if routes != {f'UNOVA_ROUTE_{n:02d}' for n in range(1, 19)}:
        raise ValueError('UNOVA U03: faltam rotas BW 1 a 18')
    if not EXPECTED_CRITICAL <= ids:
        raise ValueError('UNOVA U03: faltam marcos do roteiro')
    return {
        'schema': 1, 'region': 'UNOVA', 'phase': 'U03',
        'status': 'SYMBOLIC_CATALOG_VALIDATED_NOT_PLAYABLE',
        'catalog_areas': len(areas), 'catalog_gym_count': len(gyms),
        'catalog_route_count': len(routes),
        'areas_with_real_map_ids': 0, 'source_maps_verified': 0,
        'can_install': False, 'game_exe_tested': False,
        'story_completed': False, 'playable_fases': 0,
        'phases_with_catalog_areas': dict(sorted(phases.items())),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalog', type=Path, default=CATALOG)
    parser.add_argument('--registry', type=Path, default=SITE_REGISTRY)
    args = parser.parse_args(argv)
    try:
        catalog = json.loads(args.catalog.read_text('utf-8'))
        registry = json.loads(args.registry.read_text('utf-8'))
        report = validate(catalog, registry['regions']['UNOVA'])
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 0
    except (OSError, KeyError, ValueError, TypeError) as exc:
        print('UNOVA_U03_BLOQUEADO: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
