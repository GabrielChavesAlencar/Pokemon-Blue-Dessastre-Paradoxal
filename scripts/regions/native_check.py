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


def prepare(game, integrated=False, k03e=False, k04=False, k05_city=False, k05_tower=False, k06_approach=False):
    game = game.resolve()
    if sum((integrated, k03e, k04, k05_city, k05_tower, k06_approach)) > 1:
        raise ValueError("Choose one native proof")
    if k06_approach:
        from audit import json_file
        from build_k06_approach import MAP_DIR, PROOF, SAVE_APP, APPROACH
        from qa_k04_migration import save_namespace_valid
        if os.getenv("GITHUB_ACTIONS")!="true" or game!=(ROOT/".blue-work"/MAP_DIR).resolve():
            raise ValueError("K06 approach native check requires its disposable fixture")
        marker=json_file(game/PILOT_META)
        if (marker.get(PROOF) is not True or marker.get("save_app")!=SAVE_APP or
                not save_namespace_valid(game,SAVE_APP) or len(marker["maps"])!=178 or
                not all(str(i) in marker["maps"] for i in APPROACH) or
                marker["maps"].get("93")!=609):
            raise ValueError("K06 approach save isolation or map identities invalid")
    if k05_city or k05_tower:
        from audit import json_file
        from build_k05_city import CITY_SLOTS, SAVE_APP
        from qa_k04_migration import save_namespace_valid
        from build_k05_tower import SLOTS as TOWER_SLOTS, SAVE_APP as TOWER_APP
        slots = {**CITY_SLOTS, **TOWER_SLOTS} if k05_tower else CITY_SLOTS
        kind = "tower" if k05_tower else "city"
        if k05_tower:
            SAVE_APP = TOWER_APP
        stage = (ROOT / f".blue-work/kanto-k05-{kind}").resolve()
        from build_k05_product import PRODUCT_APP, PRODUCT_NAME
        product = (ROOT / ".blue-work" / PRODUCT_NAME).resolve()
        from qa_k05_migration import locations, require_candidate_game
        migration=False
        if k05_tower and game==product and os.getenv("GITHUB_ACTIONS")=="true":
            kind,SAVE_APP="product",PRODUCT_APP
        elif k05_tower and game in {locations(n)[1].resolve() for n in (156,160,165)}:
            old_count=require_candidate_game(game)
            isolation=game/"Data/blue-k05-ci-isolated.txt"
            migration=(isolation.is_file() and isolation.read_text("ascii")==str(old_count))
            if not migration:
                raise ValueError("Missing K05 migrated CI isolation witness")
            SAVE_APP=f"Kanto K05 Migrated {old_count} CI"
        elif os.getenv("GITHUB_ACTIONS") != "true" or game != stage:
            raise ValueError("K05 requires its disposable fixture only")
        marker = json_file(game / ("Data/blue-kanto-install.json" if migration else PILOT_META))
        if (not save_namespace_valid(game, SAVE_APP) or len(marker["maps"]) != (178 if k05_tower else 171)
                or (not migration and (marker.get("save_app") != SAVE_APP or
                    marker.get(f"k05_{kind}_fixture_only") is not True))
                or any(marker["maps"].get(str(k)) != mid for k, mid in slots.items())):
            raise ValueError("K05 fixture identity or save isolation is missing")
    if k04:
        from audit import json_file
        standalone = game == (ROOT / ".blue-work/kanto-k04-gameplay").resolve()
        migrated = game == (ROOT / ".blue-work/kanto-k04-migration-ci/game").resolve()
        if os.getenv("GITHUB_ACTIONS") != "true" or not (standalone or migrated):
            raise ValueError("K04 requires a disposable CI product game")
        from k04_corridor import published_destinations
        from qa_k04_migration import MIGRATED_PROFILE, STANDALONE_PROFILE, save_namespace_valid
        marker = json_file(game / (PILOT_META if standalone else "Data/blue-kanto-install.json"))
        profile = STANDALONE_PROFILE if standalone else MIGRATED_PROFILE
        if (not save_namespace_valid(game, profile) or len(marker["maps"]) != 165
                or any(marker["maps"].get(k) != mid for k, mid in published_destinations().items())
                or (standalone and (marker.get("k04_fixture_only") is not True or
                                    marker["save_app"] != profile))
                or (migrated and not (game / "Data/blue-k04-ci-isolated.txt").is_file())):
            raise ValueError("K04 fixture identity or save isolation is missing")
    if k03e:
        from k03e_contract import migration_game
        migrated = game == migration_game(ROOT)
        standalone = game in {(ROOT / ".blue-work" / name).resolve()
                              for name in ("kanto-k03e-functional", "kanto-release-pilot")}
        if integrated or os.getenv("GITHUB_ACTIONS") != "true" or not (migrated or standalone):
            raise ValueError("K03-E requires a disposable CI candidate")
        from audit import json_file
        marker = game/"Data/blue-kanto-install.json" if migrated else game/PILOT_META
        valid_counts = {160, 165} if game.name == "kanto-release-pilot" else {160}
        if len(json_file(marker)["maps"]) not in valid_counts:
            raise ValueError("K03-E candidate must contain 160 maps")
    if integrated:
        # Integrated proof modifies Main only on a disposable GitHub runner.
        # Never allow this on the user's installed game on a local computer.
        if os.getenv("GITHUB_ACTIONS") != "true" or game != (ROOT / "game").resolve():
            raise ValueError("Integrated Main injection is allowed only on a CI copy of game/")
        if not (game / "Data/blue-kanto-start.txt").is_file():
            raise ValueError("The CI game has no installed Kanto marker")
    elif not (k03e or k04 or k05_city or k05_tower or k06_approach) and (not game.is_relative_to((ROOT / ".blue-work").resolve()) or not (game / PILOT_META).is_file()):
        raise ValueError("Native proof requires a dedicated Kanto build under .blue-work.")
    if not (integrated or k03e or k04 or k05_city or k05_tower or k06_approach):
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
        if k04:
            proof_file = "Data/blue-kanto-k04-check.rb"
            klass = "KantoK04NativeCheck"
        if k05_city:
            proof_file = "Data/blue-kanto-k05-city-check.rb"
            klass = "KantoK05CityNativeCheck"
        if k05_tower:
            proof_file = "Data/blue-kanto-k05-tower-check.rb"
            klass = "KantoK05TowerNativeCheck"
        if k06_approach:
            proof_file = "Data/blue-kanto-k06-approach-check.rb"
            klass = "KantoK06ApproachNativeCheck"
        failure = "Data/blue-kanto-integrated-error.txt" if integrated else "Data/blue-kanto-error.txt"
        prerequisite = 'load "Data/blue-kanto-proof.rb"' if k03e or k04 or k05_city or k05_tower or k06_approach else ""
        if k04 or k05_city or k05_tower or k06_approach:
            prerequisite += '\n      load "Data/blue-kanto-k03e-check.rb"'
        if k05_tower or k06_approach:
            prerequisite += '\n      load "Data/blue-kanto-k05-city-check.rb"'
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
    if k04:
        for dst, src in (("blue-kanto-proof.rb", "KantoNativeCheck.rb"),
                         ("blue-kanto-k03e-check.rb", "KantoK03ENativeCheck.rb"),
                         ("blue-kanto-k04-check.rb", "KantoK04NativeCheck.rb")):
            (game / "Data" / dst).write_bytes((ROOT / "scripts/regions" / src).read_bytes())
    if k05_city or k05_tower or k06_approach:
        for dst, src in (("blue-kanto-proof.rb", "KantoNativeCheck.rb"),
                         ("blue-kanto-k03e-check.rb", "KantoK03ENativeCheck.rb"),
                         ("blue-kanto-k05-city-check.rb", "KantoK05CityNativeCheck.rb")):
            (game / "Data" / dst).write_bytes((ROOT / "scripts/regions" / src).read_bytes())
    if k05_tower:
        (game / proof_file).write_bytes((ROOT / "scripts/regions/KantoK05TowerNativeCheck.rb").read_bytes())
    if k06_approach:
        (game / proof_file).write_bytes((ROOT / "scripts/regions/KantoK06ApproachNativeCheck.rb").read_bytes())
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
    parser.add_argument("--k04", action="store_true", help="CI only: isolated Rock Tunnel")
    parser.add_argument("--k05-city", action="store_true", help="CI only: isolated Lavender city")
    parser.add_argument("--k05-tower", action="store_true", help="CI only: isolated Pokémon Tower")
    parser.add_argument("--k06-approach", action="store_true", help="CI only: disposable Celadon approach")
    args = parser.parse_args()
    prepare(args.game, args.integrated, args.k03e, args.k04, args.k05_city, args.k05_tower, args.k06_approach)
