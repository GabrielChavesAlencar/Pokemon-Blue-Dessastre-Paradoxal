"""Early RGSS Input bootstrap for JoiPlay XP builds.

The game's Input script can call Input.mouse_in_window before Mobile.rb
plugins finish loading. Install this tiny compatibility method at the beginning
of that script, guarded by the Android marker written into each release ZIP.
Windows/native runs have no marker and remain unmodified at runtime.
"""
from __future__ import annotations

import zlib
from pathlib import Path

from scripts.official_rules.prepare_restore import Marshal, RubyString, dump

MARKER = "# BLUE_JOIPLAY_INPUT_EARLY_V1"
# Do NOT depend on BlueMobile: it is a plugin loaded later than Input.
EARLY_BOOTSTRAP = (
    MARKER + "\n"
    "if File.file?('Data/blue-mobile.txt')\n"
    "  module Input\n"
    "    def self.mouse_in_window; true; end unless respond_to?(:mouse_in_window)\n"
    "  end\n"
    "end\n"
)


def _scripts(data: bytes):
    return Marshal(data).read()


def install(game: Path) -> bool:
    """Inject before the first Input statement; return True if changed."""
    path = game / "Data/Scripts.rxdata"
    rows = _scripts(path.read_bytes())
    matches = [row for row in rows if bytes(row[1]) == b"Input"]
    if len(matches) != 1:
        raise ValueError("Expected exactly one RGSS Input script; cannot guarantee JoiPlay touch compatibility.")
    row = matches[0]
    source = zlib.decompress(row[2]).decode("utf8")
    if MARKER in source:
        if not source.startswith(EARLY_BOOTSTRAP):
            raise ValueError("Unknown early Input compatibility modification.")
        return False
    row[2] = RubyString(zlib.compress((EARLY_BOOTSTRAP + source).encode("utf8")))
    path.write_bytes(b"\x04\x08" + dump(rows))
    return True


def verify(data: bytes) -> None:
    rows = _scripts(data)
    matches = [row for row in rows if bytes(row[1]) == b"Input"]
    if len(matches) != 1:
        raise ValueError("JoiPlay ZIP lacks the RGSS Input script.")
    content = zlib.decompress(matches[0][2]).decode("utf8")
    if not content.startswith(EARLY_BOOTSTRAP):
        raise ValueError("JoiPlay ZIP lacks the pre-plugin Input.mouse_in_window compatibility fix.")
