"""Install Windows keyboard remapping using the existing Blue plugin installer pattern."""
from datetime import datetime, timezone
from pathlib import Path
import os
import shutil
import tempfile

FILES = ('00_SetControls.rb', '10_BlueSettings.rb', 'meta.txt')


def install(project: Path, game: Path) -> int:
    source = project / 'scripts' / 'controls'
    target = game / 'Plugins' / 'ZZZZ Blue Keyboard Controls'
    changes = {
        target / name: (source / name).read_bytes()
        for name in FILES
        if not (target / name).is_file()
        or (target / name).read_bytes() != (source / name).read_bytes()
    }
    if not changes:
        return 0
    backup = project / '.blue-backups' / ('controls-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    previous = {path: path.read_bytes() if path.is_file() else None for path in changes}
    for path, old in previous.items():
        if old is not None:
            backup.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, backup / path.name)

    def write(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(prefix='.blue-controls-', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp, path)
        finally:
            if os.path.exists(temp):
                os.unlink(temp)

    written = []
    try:
        for path, data in changes.items():
            write(path, data)
            written.append(path)
    except Exception:
        for path in reversed(written):
            if previous[path] is None:
                path.unlink(missing_ok=True)
            else:
                write(path, previous[path])
        raise
    return len(changes)
