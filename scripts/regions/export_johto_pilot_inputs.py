"""Exporta somente dados de mapa/arte/PBS para auditoria privada de Johto.

Nunca copia saves, executáveis, plugins, scripts, .env ou códigos de acesso.
Este ZIP NÃO deve ser commitado no GitHub: pode conter conteúdo de terceiros.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / '.blue-work/johto-pilot-inputs.zip'
MAX_FILE = 80 * 1024 * 1024
MAX_TOTAL = 850 * 1024 * 1024
MAX_COUNT = 8500
PNG = b'\x89PNG\r\n\x1a\n'
REQUIRED = ('Data/MapInfos.rxdata', 'Data/Tilesets.rxdata', 'Data/System.rxdata')
MAP = re.compile(r'Map[0-9]{3,4}\.rxdata\Z', re.IGNORECASE)
SAFE_PBS = re.compile(r'[A-Za-z0-9_ -]+\.txt\Z')
SAFE_PNG = re.compile(r'[A-Za-z0-9_ .()\-]+\.png\Z')


def gather(game: Path, *, sprites: bool = False) -> list[tuple[str, Path]]:
    """Exact allowlist; refuse symlinks, excessive files and unexpected paths."""
    if game.is_symlink() or not game.is_dir():
        raise ValueError('A pasta game/ local nao existe ou e um link')
    selected: dict[str, Path] = {}

    def add(relative: str) -> None:
        path = game / relative
        if any(p.is_symlink() for p in (path, *path.parents) if p != path.anchor):
            raise ValueError('Link simbolico proibido: ' + relative)
        if not path.is_file():
            raise ValueError('Arquivo esperado ausente: ' + relative)
        if not path.resolve().is_relative_to(game.resolve()):
            raise ValueError('Arquivo fora do jogo: ' + relative)
        size = path.stat().st_size
        if size <= 0 or size > MAX_FILE:
            raise ValueError('Arquivo vazio/grande demais: ' + relative)
        selected[relative] = path

    for file in REQUIRED:
        add(file)
    data = game / 'Data'
    if data.is_symlink():
        raise ValueError('Data/ link simbolico proibido')
    maps = sorted(x for x in data.iterdir() if MAP.fullmatch(x.name))
    if not maps:
        raise ValueError('Nenhum MapNNN.rxdata nativo encontrado')
    for file in maps:
        add('Data/' + file.name)

    folders = [('PBS', SAFE_PBS), ('Graphics/Tilesets', SAFE_PNG),
               ('Graphics/Autotiles', SAFE_PNG)]
    if sprites:
        folders += [('Graphics/Characters', SAFE_PNG),
                    ('Graphics/Trainers', SAFE_PNG)]
    for dirname, allowed in folders:
        folder = game / dirname
        if not folder.exists():
            continue
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError('Pasta invalida: ' + dirname)
        for file in sorted(folder.iterdir()):
            if file.is_symlink():
                raise ValueError('Link simbolico proibido: ' + str(file))
            if file.is_file() and allowed.fullmatch(file.name):
                rel = dirname + '/' + file.name
                add(rel)
                if file.suffix.lower() == '.png':
                    with file.open('rb') as f:
                        if f.read(8) != PNG:
                            raise ValueError('PNG invalido: ' + rel)
    if len(selected) > MAX_COUNT or sum(p.stat().st_size for p in selected.values()) > MAX_TOTAL:
        raise ValueError('Pacote excessivo: selecione apenas os dados necessarios')
    return sorted(selected.items())


def export(game: Path, output: Path, *, sprites: bool = False,
           root: Path = ROOT) -> dict:
    root = root.resolve()
    if game.is_symlink() or game.resolve() != (root / 'game').resolve():
        raise ValueError('Apenas a instalacao original root/game/ pode ser lida')
    work = (root / '.blue-work').resolve()
    if (work.is_symlink() or output.is_symlink() or
            not output.absolute().resolve().is_relative_to(work) or
            output.exists() or output.resolve() == work):
        raise ValueError('Destino deve ser novo e estar dentro de .blue-work/')
    candidates = gather(game, sprites=sprites)
    hashes = []
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.johto-private-', suffix='.zip',
                                     dir=output.parent)
    os.close(fd)
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED,
                             compresslevel=3, allowZip64=True) as archive:
            for relative, path in candidates:
                raw = path.read_bytes()
                digest = hashlib.sha256(raw).hexdigest()
                archive.writestr('game/' + relative, raw)
                hashes.append({'path': 'game/' + relative,
                               'bytes': len(raw), 'sha256': digest})
            report = {'schema': 1, 'purpose': 'PRIVATE_JOHTO_PILOT_ANALYSIS',
                      'safe_for_public_github': False,
                      'includes_sprites': sprites, 'files': hashes,
                      'contains_game_exe': False, 'contains_saves': False,
                      'note': 'Private upload only; rights of game assets remain with their owners.'}
            archive.writestr('johto-inputs-manifest.json',
                             json.dumps(report, ensure_ascii=False, indent=2) + '\n')
        if output.exists() or output.is_symlink():
            raise ValueError('Saida criada durante exportacao; sobrescrita bloqueada')
        os.rename(temporary, output)
        return {'output': str(output), 'files': len(hashes),
                'archive_bytes': output.stat().st_size,
                'includes_sprites': sprites}
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sprites', action='store_true',
                        help='Incluir Characters e Trainers; pode aumentar muito o ZIP')
    args = parser.parse_args(argv)
    try:
        result = export(ROOT / 'game', OUTPUT, sprites=args.sprites)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print('[JOHTO][BLOQUEADO]', exc)
        return 2
    print('[JOHTO] Pacote PRIVADO gerado:', result['output'])
    print('[JOHTO] Arquivos:', result['files'], 'Bytes ZIP:', result['archive_bytes'])
    print('[JOHTO] Envie o ZIP somente em conversa privada, nunca no GitHub.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
