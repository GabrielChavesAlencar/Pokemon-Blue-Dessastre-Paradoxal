"""Install a one-shot native check into a dedicated Kanto build for GitHub Actions."""
import argparse
import os
import sys
import zlib
from pathlib import Path

from audit import ROOT
from pilot import PILOT_META

sys.path.insert(0, str(ROOT / "scripts/official_rules"))
from prepare_restore import Marshal, RubyString, dump


def prepare(game, integrated=False):
    game = game.resolve()
    if integrated:
        # Integrated proof modifies Main only on a disposable GitHub runner.
        # Never allow this on the user's installed game on a local computer.
        if os.getenv("GITHUB_ACTIONS") != "true" or game != (ROOT / "game").resolve():
            raise ValueError("Integrated Main injection is allowed only on a CI copy of game/")
        if not (game / "Data/blue-kanto-start.txt").is_file():
            raise ValueError("The CI game has no installed Kanto marker")
    elif not game.is_relative_to((ROOT / ".blue-work").resolve()) or not (game / PILOT_META).is_file():
        raise ValueError("Native proof requires a dedicated Kanto build under .blue-work.")
    if not integrated:
        # Stage-16 preflight runs on the exact compiled, disposable Kanto pilot
        # in CI, not against an ordinary player's save or Game.exe.
        from release_gate import inspect as release_inspect
        report = release_inspect(ROOT, game)
        if not report["ci_preflight_passed"] or report["declared_playable"]:
            raise ValueError("Kanto release gate did not confirm prototype safety")
        out = ROOT / ".blue-work/kanto-phase-16-release-gate.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        import json
        out.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("KANTO_RELEASE_GATE:" + json.dumps(report, ensure_ascii=True), flush=True)
    scripts = game / "Data/Scripts.rxdata"
    rows = Marshal(scripts.read_bytes()).read()
    for row in rows:
        if row[1] != b"Main":
            continue
        main = zlib.decompress(row[2]).decode("utf8")
        needle = "    Game.set_up_system"
        if main.count(needle) != 1:
            raise ValueError("Could not identify the native start hook.")
        proof_file = "Data/blue-kanto-integrated-check.rb" if integrated else "Data/blue-kanto-proof.rb"
        klass = "KantoIntegratedCheck" if integrated else "KantoNativeCheck"
        failure = "Data/blue-kanto-integrated-error.txt" if integrated else "Data/blue-kanto-error.txt"
        proof = f"""    begin
      load "{proof_file}"
      {klass}.run
    rescue StandardError => error
      File.write("{failure}", error.full_message)
      exit! 1
    end
    exit
"""
        row[2] = RubyString(zlib.compress(main.replace(needle, proof + needle).encode("utf8")))
        scripts.write_bytes(b"\x04\x08" + dump(rows))
        break
    else:
        raise ValueError("Main script is missing.")
    (game / proof_file).write_bytes(
        (ROOT / "scripts/regions/KantoIntegratedCheck.rb" if integrated
         else ROOT / "scripts/regions/KantoNativeCheck.rb").read_bytes()
    )
    if not integrated:
        # One-shot native test only; not distributed as a gameplay plugin.
        (game / "Data/blue-kanto-walk-check.rb").write_bytes(
            (ROOT / "scripts/regions/KantoWalkCheck.rb").read_bytes()
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("--integrated", action="store_true", help="CI only: probe initial region in disposable main game")
    args = parser.parse_args()
    prepare(args.game, args.integrated)
