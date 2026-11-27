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


def prepare(game, integrated=False, k03e=False):
    game = game.resolve()
    if k03e:
        from k03e_contract import migration_game
        migrated = game == migration_game(ROOT)
        if integrated or os.getenv("GITHUB_ACTIONS") != "true" or not (migrated or game == (ROOT / ".blue-work/kanto-k03e-functional").resolve()):
            raise ValueError("K03-E requires a disposable CI candidate")
        from audit import json_file
        marker = game/"Data/blue-kanto-install.json" if migrated else game/PILOT_META
        if len(json_file(marker)["maps"]) != 160:
            raise ValueError("K03-E candidate must contain 160 maps")
    if integrated:
        # Integrated proof modifies Main only on a disposable GitHub runner.
        # Never allow this on the user's installed game on a local computer.
        if os.getenv("GITHUB_ACTIONS") != "true" or game != (ROOT / "game").resolve():
            raise ValueError("Integrated Main injection is allowed only on a CI copy of game/")
        if not (game / "Data/blue-kanto-start.txt").is_file():
            raise ValueError("The CI game has no installed Kanto marker")
    elif not k03e and (not game.is_relative_to((ROOT / ".blue-work").resolve()) or not (game / PILOT_META).is_file()):
        raise ValueError("Native proof requires a dedicated Kanto build under .blue-work.")
    if not integrated and not k03e:
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
        if k03e:
            proof_file = "Data/blue-kanto-k03e-check.rb"
            klass = "KantoK03ENativeCheck"
        failure = "Data/blue-kanto-integrated-error.txt" if integrated else "Data/blue-kanto-error.txt"
        prerequisite = 'load "Data/blue-kanto-proof.rb"' if k03e else ""
        proof = f"""    begin
      {prerequisite}
      load "{proof_file}"
      {klass}.run
    rescue Exception => error
      # Capture native EventScriptError as well as StandardError in CI only.
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
    if k03e:
        (game / "Data/blue-kanto-proof.rb").write_bytes(
            (ROOT / "scripts/regions/KantoNativeCheck.rb").read_bytes())
        (game / proof_file).write_bytes(
            (ROOT / "scripts/regions/KantoK03ENativeCheck.rb").read_bytes())
    (game / "Data/blue-kanto-music-native-probe.rb").write_bytes(
        (ROOT / "scripts/regions/KantoMusicNativeProbe.rb").read_bytes()
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
    parser.add_argument("--k03e", action="store_true", help="CI only: functional 160-map candidate")
    args = parser.parse_args()
    prepare(args.game, args.integrated, args.k03e)
