"""Install a one-shot native check into a dedicated Kanto build for GitHub Actions."""
import argparse
import sys
import zlib
from pathlib import Path

from audit import ROOT
from pilot import PILOT_META

sys.path.insert(0, str(ROOT / "scripts/official_rules"))
from prepare_restore import Marshal, RubyString, dump


def prepare(game):
    game = game.resolve()
    if not game.is_relative_to((ROOT / ".blue-work").resolve()) or not (game / PILOT_META).is_file():
        raise ValueError("Native proof requires a dedicated Kanto build under .blue-work.")
    scripts = game / "Data/Scripts.rxdata"
    rows = Marshal(scripts.read_bytes()).read()
    for row in rows:
        if row[1] != b"Main":
            continue
        main = zlib.decompress(row[2]).decode("utf8")
        needle = "    Game.set_up_system"
        if main.count(needle) != 1:
            raise ValueError("Could not identify the native start hook.")
        proof = """    begin
      load "Data/blue-kanto-proof.rb"
      KantoNativeCheck.run
    rescue StandardError => error
      File.write("Data/blue-kanto-error.txt", error.full_message)
      exit! 1
    end
    exit
"""
        row[2] = RubyString(zlib.compress(main.replace(needle, proof + needle).encode("utf8")))
        scripts.write_bytes(b"\x04\x08" + dump(rows))
        break
    else:
        raise ValueError("Main script is missing.")
    (game / "Data/blue-kanto-proof.rb").write_bytes(
        (ROOT / "scripts/regions/KantoNativeCheck.rb").read_bytes()
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    prepare(parser.parse_args().game)
