#!/usr/bin/env python3
# Inventario de eventos de mapas do projeto pret/pokefirered (fonte decompilada)
# Uso: python extrair_eventos_firered.py /caminho/para/pokefirered --out ./auditoria
# Biblioteca padrão Python 3, sem ROM, sem recursos gráficos.
import argparse
import csv
import json
import re
from pathlib import Path

CATEGORIES = {
    'object_events':'NPC/objeto/treinador',
    'warp_events':'transicao/warp',
    'coord_events':'gatilho de coordenada',
    'bg_events':'placa/objeto oculto',
    'connections':'conexao de borda',
}
FIELDS = ['group','map','kind','index','x','y','elevation','type','script','flag','var',
          'var_value','graphics_id','trainer_type','sight','dest_map','dest_warp_id',
          'direction','offset','note','json_event']

def md_escape(value):
    return str(value).replace('|', '\\|').replace('\n', ' ')

def inline_list(values):
    return ', '.join('`'+str(x)+'`' for x in values) if values else '—'

def main():
    p = argparse.ArgumentParser(description='Gera inventário completo de eventos explícitos de mapas do FireRed')
    p.add_argument('repo', help='Pasta raiz de pret/pokefirered')
    p.add_argument('--out', default='auditoria-firered', help='Pasta de relatórios de saída')
    a = p.parse_args()
    root = Path(a.repo).expanduser().resolve()
    src = root / 'data' / 'maps'
    groups_path = src / 'map_groups.json'
    if not groups_path.is_file():
        p.error('Não encontrei data/maps/map_groups.json. Aponte para a raiz do projeto pret/pokefirered.')
    groups = json.loads(groups_path.read_text(encoding='utf-8'))
    order = [(g, name) for g in groups.get('group_order', []) for name in groups.get(g, [])]
    rows = []
    summaries = []
    missing = []
    script_index = []
    for group, name in order:
        path = src / name / 'map.json'
        if not path.is_file():
            missing.append(str(path.relative_to(root)))
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        counts = {key:len(data.get(key, [])) for key in CATEGORIES}
        scripts_path = src / name / 'scripts.inc'
        contents = scripts_path.read_text(encoding='utf-8') if scripts_path.is_file() else ''
        labels = re.findall(r'^([A-Za-z_][A-Za-z_0-9]*)::', contents, re.M)
        flags = sorted(set(re.findall(r'\bFLAG_[A-Z0-9_]+\b', contents)))
        variables = sorted(set(re.findall(r'\bVAR_[A-Z0-9_]+\b', contents)))
        map_scripts = re.findall(r'^\s*map_script\s+(MAP_SCRIPT_[A-Z_]+)', contents, re.M)
        summaries.append({
            'group':group,'map':name,'path':str(path.relative_to(root)),
            'map_id':data.get('id'),'music':data.get('music'),
            'requires_flash':data.get('requires_flash'), 'weather':data.get('weather'),
            'map_type':data.get('map_type'),'script_file_exists':scripts_path.is_file(),
            'script_labels':len(labels),'flags':flags,'variables':variables,
            'map_scripts':map_scripts,**counts
        })
        if labels or flags or variables:
            script_index.append((name, labels, flags, variables, map_scripts))
        for key in CATEGORIES:
            for i, ev in enumerate(data.get(key, []), 1):
                row = {k:'' for k in FIELDS}
                row.update({'group':group,'map':name,'kind':key,'index':i})
                for fld in FIELDS:
                    if fld in ev:row[fld]=ev[fld]
                row['sight']=ev.get('trainer_sight_or_berry_tree_id', '')
                row['json_event']=json.dumps(ev, ensure_ascii=False, sort_keys=True)
                if key=='bg_events' and ev.get('type')=='hidden_item': row['note']='item oculto'
                rows.append(row)
    out = Path(a.out).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    with (out/'eventos_detalhados.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w = csv.DictWriter(f,fieldnames=FIELDS,extrasaction='ignore');w.writeheader();w.writerows(rows)
    with (out/'mapas_resumo.json').open('w',encoding='utf-8') as f:
        json.dump({'source':'https://github.com/pret/pokefirered','maps':summaries,
                   'missing_maps':missing},f,ensure_ascii=False,indent=2)
    with (out/'eventos_detalhados.json').open('w',encoding='utf-8') as f:
        json.dump({'source':'https://github.com/pret/pokefirered','events':rows},
                  f,ensure_ascii=False,indent=2)
    totals = {k:sum(m[k] for m in summaries) for k in CATEGORIES}
    lines = ['# Inventário automático de eventos de mapa — Pokémon FireRed',
             '', '> Extração de `data/maps/*/map.json` e identificação de rótulos nos `scripts.inc`.',
             '> Este relatório cataloga o que é explícito nos arquivos. **Não** interpreta automaticamente',
             '> o fluxo de todos os scripts globais, encontros aleatórios, mecânicas nativas ou pré-condições.',
             '',f'- Mapas enumerados: **{len(order)}**',
             f'- Mapas lidos: **{len(summaries)}**',
             f'- Eventos/conexões explícitos: **{len(rows)}**',
             '']
    for k, v in totals.items(): lines.append(f'- {CATEGORIES[k]} (`{k}`): **{v}**')
    if missing:
        lines.extend(['','## Mapas ausentes na cópia local',''] + ['- `'+x+'`' for x in missing])
    lines.extend(['','## Resumo por mapa','','| Grupo | Mapa | Objetos | Warps | Coord. | BG | Conexões | Script |',
                  '|---|---|---:|---:|---:|---:|---:|---|'])
    for m in summaries:
        vals = [m['group'],m['map']]+[str(m[k]) for k in CATEGORIES]+['sim' if m['script_file_exists'] else 'não']
        lines.append('| '+' | '.join(md_escape(v) for v in vals)+' |')
    lines.extend(['','## Eventos individuais (todos os registros explícitos de mapa)','',
                  'Campos são mantidos como no `map.json`; consulte o CSV/JSON para metadados restantes.',''])
    for m in summaries:
        events = [r for r in rows if r['map']==m['map'] and r['group']==m['group']]
        lines.extend([f"### {m['map']} — {len(events)} registros",'',
                      f"Origem: `{m['path']}`; script: `data/maps/{m['map']}/scripts.inc`.",
                      '', '| # | Categoria | Posição | Origem/destino | Script/flag |',
                      '|---:|---|---|---|---|'])
        for r in events:
            xy = f"({r['x']},{r['y']})" if r['x']!='' and r['y']!='' else '—'
            dest = r['dest_map'] or r['graphics_id'] or r['direction'] or r['type'] or '—'
            ident = ' / '.join(filter(None,[str(r['script']),str(r['flag'])])) or '—'
            lines.append('| '+ ' | '.join(md_escape(x) for x in [r['index'],r['kind'],xy,dest,ident])+' |')
        lines.append('')
    lines.extend(['','## Índice dos scripts por mapa','','> Rótulos, flags e variáveis **citados** em cada `scripts.inc` (não necessariamente exclusivos deste mapa).',''])
    for name, labels, flags, variables, map_scripts in script_index:
        lines.extend([f'### {name}', '',f'- Map scripts: {inline_list(map_scripts)}',
                      f'- Rótulos ({len(labels)}): {inline_list(labels)}',
                      f'- Flags: {inline_list(flags)}',f'- Variáveis: {inline_list(variables)}',''])
    lines.extend(['## Limitações','',
                  '- `object_events` não indica automaticamente se uma batalha é obrigatória; investigar o script associado.',
                  '- `bg_events` pode representar placa, item oculto e outros tipos; conferir `type` e os campos.',
                  '- Encontros em grama/água são tabelas externas, não cada um um evento de mapa.',
                  '- Eventos globais, mapas especiais, menus e flags podem usar arquivos fora dos `scripts.inc`.',
                  '- Nenhum mapa RPG Maker foi criado/importado por este programa.', ''])
    (out/'INVENTARIO_COMPLETO_FIRERED.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f'Mapas {len(summaries)}/{len(order)}, registros {len(rows)}, ausentes {len(missing)}.')
    for k,v in totals.items():print(f'  {k}: {v}')
    print('Arquivos gerados em:',out)
    if missing: print('Atenção: arquivo de mapas ausentes disponível no relatório.')
if __name__=='__main__': main()