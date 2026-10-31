"""Rename the LOCAL Decades game window without redistributing assets.
This is intentionally conservative: it does not patch the RPG Maker event database,
rendered title-screen graphics, or compiled scripts.
"""
from pathlib import Path
import os
import re
import shutil
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(os.environ.get('BLUE_GAME_DIR', str(ROOT / 'game'))).expanduser().resolve()
BACKUP = ROOT / '.blue-backups' / 'game-branding'


def replace_once(path, pattern, new_value):
    if not path.is_file():
        raise FileNotFoundError(path)
    text = path.read_text(encoding='utf-8-sig')
    updated, count = re.subn(pattern,new_value,text,count=1, flags=re.MULTILINE)
    if count != 1:
        raise ValueError(f'Não foi possível localizar a configuração em {path.name}.')
    if updated == text:
        return False
    BACKUP.mkdir(parents=True,exist_ok=True)
    dst = BACKUP / f'{path.name}.{datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")}.bak'
    shutil.copy2(path,dst)
    path.write_text(updated, encoding='utf-8')
    return True


def main():
    game_ini = GAME / 'Game.ini'
    mkxp = GAME / 'mkxp.json'
    if not game_ini.is_file() or not mkxp.is_file():
        print('[ERRO] Jogo não instalado: execute BAIXAR_BASE_DECADES.bat.')
        return 1
    try:
        changed_ini = replace_once(game_ini,r'^Title\s*=.*$', 'Title=Pokemon Blue Dessastre Paradoxal')
        changed_mkxp = replace_once(mkxp,r'^([ \t]*"windowTitle"[ \t]*:[ \t]*)"[^"]*"', r'\1"Pokémon Blue: Dessastre Paradoxal"')
        print('[OK] Janela do jogo personalizada.', 'Game.ini:', 'alterado' if changed_ini else 'já correto', '| mkxp.json:', 'alterado' if changed_mkxp else 'já correto')
        print('Os logos internos e o menu principal ainda exigem arte e edição no RPG Maker XP.')
        return 0
    except (OSError,ValueError) as e:
        print('[ERRO]',e)
        return 1


if __name__=='__main__':
    sys.exit(main())
