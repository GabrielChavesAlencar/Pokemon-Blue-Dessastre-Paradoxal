#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Organiza em Markdown diálogos de arquivos locais de uma descompilação de FireRed.

O programa não inclui nem distribui textos do jogo. É necessário informar um
repositório/arquivo local legitimamente obtido pelo usuário.

Uso:
  python extrair_traduzir_dialogos_firered.py ./pokefirered --saida dialogos.md
  python extrair_traduzir_dialogos_firered.py ./pokefirered --traduzir --saida dialogos_en_pt.md

Tradução opcional (local): pip install argostranslate
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ASSEMBLY_STR_RE = re.compile(r'\s*\.string\s+"((?:\\.|[^"\\])*)"')
LABEL_RE = re.compile(r'^\s*([A-Za-z_][\w.]*)\s*::?\s*(?:@.*)?$')
C_STRING_RE = re.compile(r'"((?:\\.|[^"\\])*)"', re.S)
C_GETTEXT_RE = re.compile(
    r'_\s*\(\s*((?:"(?:\\.|[^"\\])*"\s*)+)\)', re.S
)
CONTROL_RE = re.compile(r'\{[^{}]+\}|\[[A-Z][A-Z_0-9 ]+\]')
JAPANESE_RE = re.compile(r'[\u3040-\u30ff\u3400-\u9fff]')

@dataclass(frozen=True)
class Entry:
    ident: str
    source: str
    location: str
    line: int
    original_raw: str


def decode_string(s: str) -> str:
    """Converte apenas escapes visuais conhecidos; preserva macros do jogo."""
    s = s.replace(r'\"', '"').replace(r'\\', '\\')
    # Os comandos de quebra de página GBA são separados do texto visível.
    s = s.replace(r'\p', '\n\n').replace(r'\l', '\n').replace(r'\n', '\n')
    s = s.replace(r'\t', '    ')
    # Em scripts da engine, $ é terminador de string, não uma letra exibida.
    s = s.rstrip('$')
    return s


def context_from_relative(rel: str) -> str:
    p = Path(rel)
    parts = p.parts
    if 'maps' in parts:
        i = parts.index('maps')
        if i + 1 < len(parts):
            return parts[i + 1]
    if 'text' in parts:
        return 'Sistema / textos globais'
    if 'src' in parts:
        return 'Mensagens programáticas (src)'
    return 'Scripts globais e outros'


def iter_assembly_entries(root: Path):
    base = root / 'data'
    if not base.is_dir():
        return
    for path in sorted(list(base.rglob('*.inc')) + list(base.rglob('*.s'))):
        # Grandes arquivos de dados não textuais são ignorados automaticamente.
        try:
            lines = path.read_text(encoding='utf-8-sig', errors='replace').splitlines()
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        label = None
        start_line = 0
        fragments = []
        unnamed = 0
        def flush():
            if not fragments:
                return None
            raw = ''.join(fragments)
            if not raw.strip():
                return None
            return Entry(label or f'{path.stem}_anonimo_{unnamed}', rel,
                         context_from_relative(rel), start_line, raw)

        for no, line in enumerate(lines, 1):
            m_label = LABEL_RE.match(line)
            if m_label:
                old = flush()
                if old:
                    yield old
                label, fragments, start_line = m_label.group(1), [], no
                continue
            m_string = ASSEMBLY_STR_RE.match(line)
            if m_string:
                if not fragments:
                    start_line = no
                    if label is None:
                        unnamed += 1
                fragments.append(m_string.group(1))
                continue
            if fragments and line.strip() and not line.lstrip().startswith('@'):
                old = flush()
                if old:
                    yield old
                fragments = []
                label = None
        last = flush()
        if last:
            yield last


def iter_c_entries(root: Path):
    base = root / 'src'
    if not base.exists():
        return
    for path in sorted(base.rglob('*.c')):
        try:
            content = path.read_text(encoding='utf-8-sig', errors='replace')
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for i, match in enumerate(C_GETTEXT_RE.finditer(content), 1):
            quoted = match.group(1)
            fragments = C_STRING_RE.findall(quoted)
            if not fragments:
                continue
            line = content.count('\n', 0, match.start()) + 1
            snippet = content[max(0, match.start() - 300):match.start()]
            ids = re.findall(r'\b(?:sText|gText|sString|gString|sMsg|gMsg)\w*', snippet)
            ident = (ids[-1] if ids else f'{path.stem}_C_{i:05d}')
            yield Entry(ident, rel, context_from_relative(rel), line, ''.join(fragments))


def all_entries(root: Path, include_c: bool):
    collected = list(iter_assembly_entries(root))
    if include_c:
        collected.extend(iter_c_entries(root))
    unique = []
    found = set()
    for entry in collected:
        fingerprint = (entry.source, entry.ident, entry.line, entry.original_raw)
        if fingerprint not in found:
            unique.append(entry)
            found.add(fingerprint)
    return unique


class Translator:
    def __init__(self):
        try:
            import argostranslate.package as package
            import argostranslate.translate as translate
        except ImportError as exc:
            raise RuntimeError('Instale o tradutor offline com: pip install argostranslate') from exc
        self.translate = translate
        self.cache = {}
        try:
            langs = translate.get_installed_languages()
            en = next((l for l in langs if l.code == 'en'), None)
            pt = next((l for l in langs if l.code == 'pt'), None)
            if en is None or pt is None or not any(x.to_lang.code == 'pt' for x in en.translations):
                print('[info] Obtendo o pacote de tradução en -> pt (primeiro uso).', file=sys.stderr)
                package.update_package_index()
                matches = [p for p in package.get_available_packages() if p.from_code == 'en' and p.to_code == 'pt']
                if not matches:
                    raise RuntimeError('Não foi encontrado o pacote en -> pt no Argos Translate.')
                package.install_from_path(matches[0].download())
        except (OSError, ConnectionError) as exc:
            raise RuntimeError('Falha no download do modelo. Conecte à internet ou instale manualmente o pacote Argos en->pt.') from exc

    def __call__(self, text: str) -> str:
        if text in self.cache:
            return self.cache[text]
        # Salvaguarda tokens dinâmicos (nomes, itens e códigos).
        refs = {}
        def protect(m):
            key = f'ZXQVAR{len(refs):04d}ZXQ'
            refs[key] = m.group(0)
            return key
        masked = CONTROL_RE.sub(protect, text)
        try:
            out = self.translate.translate(masked, 'en', 'pt')
        except Exception as exc:
            out = f'[Falha na tradução automática: {type(exc).__name__}]'
        # Nunca silenciosamente corromper um marcador dinâmico importante.
        if any(key not in out for key in refs):
            # Fallback: tradução segmentada que preserva os placeholders.
            pieces = CONTROL_RE.split(text)
            tokens = CONTROL_RE.findall(text)
            rebuilt = []
            for pos, piece in enumerate(pieces):
                if piece.strip():
                    rebuilt.append(self.translate.translate(piece, 'en', 'pt'))
                else:
                    rebuilt.append(piece)
                if pos < len(tokens):
                    rebuilt.append(tokens[pos])
            out = ''.join(rebuilt)
        else:
            for key, token in refs.items():
                out = out.replace(key, token)
        self.cache[text] = out
        return out


def translated_text(text: str, translator: Translator) -> str:
    if JAPANESE_RE.search(text):
        return '[Texto não identificado como inglês; requer revisão manual.]'
    if not re.search(r'[A-Za-z]', text):
        return text
    parts = text.split('\n\n')
    out = []
    for part in parts:
        # Quebras dentro da janela GBA não precisam ocupar o mesmo ponto em português;
        # são reformatadas pelo motor de diálogo do jogo no passo de localização.
        clean = re.sub(r'\s*\n\s*', ' ', part).strip()
        out.append(translator(clean) if clean else '')
    return '\n\n'.join(out)


def quote_md(content: str) -> str:
    # Fenced text evita interpretação de chaves e tags como Markdown.
    delimiter = '```'
    if '```' in content:
        delimiter = '````'
    return f'{delimiter}text\n{content}\n{delimiter}'


def write_md(entries: list[Entry], outfile: Path, *, translate: bool, max_entries: int, include_c: bool):
    if max_entries > 0:
        entries = entries[:max_entries]
    translator = Translator() if translate else None
    groups = collections.defaultdict(list)
    for e in entries:
        groups[e.location].append(e)
    lines = [
        '# Pokémon FireRed — Catálogo de diálogos por arquivo e identificador',
        '',
        '> **Origem:** arquivos locais fornecidos na execução. Este gerador não inclui conteúdo original do jogo.',
        '> **Tradução:** automática, en → pt-BR, com Argos Translate (quando ativada); necessita revisão humana.',
        '> **Escopo:** diretrizes `.string` em `data/**/*.inc` e `data/**/*.s`' + ('; macros `_()` de `src/**/*.c`.' if include_c else '.'),
        '> **Limites:** falas geradas dinamicamente, textos externos e algumas mensagens construídas em código podem exigir auditoria manual.',
        '',
        f'- Entradas extraídas: **{len(entries)}**',
        f'- Grupos de origem: **{len(groups)}**',
        f'- Data de geração: **{dt.datetime.now().strftime("%Y-%m-%d %H:%M")}**',
        '',
        '## Índice de grupos', '',
    ]
    for i, (group, values) in enumerate(sorted(groups.items()), 1):
        lines.append(f'{i}. **{group}** — {len(values)} entradas')
    lines += ['', '---', '']
    counter = 0
    for group, values in sorted(groups.items()):
        lines.append(f'## Local: {group}')
        lines.append('')
        for e in values:
            counter += 1
            text_en = decode_string(e.original_raw)
            en_caption = 'Texto original (inglês do arquivo; verificar idioma quando necessário)'
            lines += [
                f'### {counter:05d} — `{e.ident}`', '',
                f'- **Fonte:** `{e.source}:{e.line}`',
                f'- **Chave:** `{e.ident}`',
                '',
                f'**{en_caption}**', '',
                quote_md(text_en), '',
                '**Português (pt-BR)**', '',
            ]
            if translator:
                tr = translated_text(text_en, translator)
                lines += [quote_md(tr), '', '**Estado:** tradução automática — revisar contexto, termos e quebras GBA.', '']
            else:
                lines += [quote_md('[PENDENTE — execute novamente com --traduzir ou insira a tradução manualmente]'), '', '**Estado:** pendente.', '']
            if counter % 100 == 0:
                print(f'[processando] {counter}/{len(entries)} entradas', file=sys.stderr)
        lines += ['---', '']
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text('\n'.join(lines), encoding='utf-8')
    return len(entries), len(groups)


def main():
    p = argparse.ArgumentParser(description='Extrai textos de um repositório local FireRed para Markdown inglês/português.')
    p.add_argument('origem', type=Path, help='Pasta local do projeto pokefirered (deve conter data/)')
    p.add_argument('--saida', type=Path, default=Path('FireRed_Dialogos_EN_PT.md'))
    p.add_argument('--traduzir', action='store_true', help='Traduz de inglês para português localmente com Argos Translate')
    p.add_argument('--sem-c', action='store_true', help='Ignora mensagens embutidas nos arquivos C')
    p.add_argument('--limite', type=int, default=0, help='Opcional: processa só as primeiras N entradas para testar')
    args = p.parse_args()
    root = args.origem.expanduser().resolve()
    if not (root / 'data').is_dir():
        p.error('A pasta deve conter a subpasta data/ do projeto; nenhum diálogo foi distribuído com este script.')
    entries = all_entries(root, include_c=not args.sem_c)
    if not entries:
        p.error('Nenhuma entrada .string localizada na pasta. Confira se é a descompilação correta.')
    print(f'[info] {len(entries)} entradas textuais encontradas.', file=sys.stderr)
    try:
        total, groups = write_md(entries, args.saida, translate=args.traduzir,
                                 max_entries=args.limite, include_c=not args.sem_c)
    except RuntimeError as exc:
        p.exit(2, f'[erro] {exc}\n')
    print(f'[concluído] {total} entradas em {groups} grupos -> {args.saida.resolve()}')

if __name__ == '__main__':
    main()