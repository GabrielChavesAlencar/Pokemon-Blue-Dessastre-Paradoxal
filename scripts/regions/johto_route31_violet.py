"""Audit the additional Route 31 <-> Violet road, as offline-only PBS candidate.

It reuses the same unique 3-tile road signature validator as Route29/Cherrygrove.
It never patches the imported source connection manifest or touches game/.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from johto_route29_cherrygrove import ROOT, derive_connection, load_grid

SYMBOLS = {'JOHTO_ROUTE_31': 106, 'JOHTO_VIOLET_CITY': 81}


def derive_violet(route31, violet, route31_id: int, violet_id: int, existing: str = '') -> dict:
    base = derive_connection(route31, violet, route_id=route31_id,
                             city_id=violet_id, existing=existing)
    return {
        'schema': 1, 'region': 'JOHTO',
        'status': 'STATIC_GEOMETRY_BORDER_CANDIDATE_NOT_PLAYABLE',
        'route31_id': route31_id, 'violet_id': violet_id,
        'route31_west_road_start_y': base['route29_west_road_start_y'],
        'violet_east_road_start_y': base['cherrygrove_east_road_start_y'],
        'signature': base['signature'], 'checked_inward_columns': 4,
        'offset_y': base['offset_y'], 'pbs_line': base['pbs_line'],
        'static_tile_passability': base['static_tile_passability'],
        'actual_game_engine_passability_verified': False,
        'tested_in_game': False, 'can_install': False, 'gameplay_playable': False,
        'next_action': 'Confirmar ida e volta Route31/Violet dentro do Game.exe isolado',
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--preview', type=Path, default=ROOT / '.blue-work/johto-staging')
    p.add_argument('--existing', type=Path, default=ROOT / '.blue-work/johto-connections-preview.txt')
    p.add_argument('--output', type=Path, default=ROOT / '.blue-work/johto-route31-violet.json')
    args = p.parse_args(argv)
    try:
        from audit_johto import checksum, read_map_data
        work = (ROOT.resolve() / '.blue-work').resolve()
        preview = args.preview.resolve()
        if (not preview.is_relative_to(work) or preview == work
                or args.preview.is_symlink() or args.existing.is_symlink()
                or args.output.is_symlink() or args.output.exists()
                or not args.output.resolve().is_relative_to(work)):
            raise ValueError('Entradas/saidas precisam ficar em .blue-work sem symlinks/overwrite')
        stage = json.loads((preview / 'johto-stage.json').read_text(encoding='utf-8'))
        if (stage.get('schema'), stage.get('region'), stage.get('status'),
                stage.get('not_playable'), stage.get('can_install')) != (
                1, 'JOHTO', 'GEOMETRY_PREVIEW_ONLY', True, False):
            raise ValueError('Preview geometrica nao auditada')
        if not re.fullmatch(r'[0-9a-f]{64}', stage.get('source_archive_sha256', '')):
            raise ValueError('SHA-256 da fonte Johto ausente')
        ids = {}
        for symbol, sid in SYMBOLS.items():
            matches = [r for r in stage['maps'] if r.get('symbol') == symbol
                       and r.get('source_id') == sid]
            if len(matches) != 1 or type(matches[0].get('destination_id')) is not int:
                raise ValueError('Simbolo/ID errado para ' + symbol)
            ids[symbol] = matches[0]['destination_id']
        tiles = read_map_data(preview / 'Data/Tilesets.rxdata')
        if not isinstance(tiles, list):
            raise ValueError('Tilesets da preview invalidos')
        rid, vid = ids['JOHTO_ROUTE_31'], ids['JOHTO_VIOLET_CITY']
        route = load_grid(preview / 'Data' / f'Map{rid:03d}.rxdata', tiles)
        city = load_grid(preview / 'Data' / f'Map{vid:03d}.rxdata', tiles)
        report = derive_violet(route, city, rid, vid,
                               existing=args.existing.read_text(encoding='utf-8'))
        report['map_sha256'] = {
            'route31': checksum(preview / 'Data' / f'Map{rid:03d}.rxdata'),
            'violet': checksum(preview / 'Data' / f'Map{vid:03d}.rxdata'),
        }
        report['source_archive_sha256'] = stage['source_archive_sha256']
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x', encoding='utf-8') as out:
            json.dump(report, out, ensure_ascii=False, indent=2)
            out.write('\n')
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('[JOHTO][BLOQUEADO]', exc, file=sys.stderr)
        return 2
    print('[JOHTO][CANDIDATA] PBS:', report['pbs_line'])
    print('[JOHTO] Relatorio:', args.output)
    print('[JOHTO] Ainda nao testado no Game.exe. Nao alterar 1/13.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
