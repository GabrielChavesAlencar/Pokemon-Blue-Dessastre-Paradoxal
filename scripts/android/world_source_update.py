"""Assemble the official source recipe locally, then verify and install it."""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts/regions")]

from scripts.android import package
from scripts.android.build_manifest import installed_manifest
from scripts.android.source_bootstrap import INSTALLER, SHA
from scripts.android.source_update import (
    RECOVERY_FILE, atomic_file, checked_row, clone_verified_install, commit_local, compiler_config,
    manifest_row, recover_under_lock, recovery_plan, update_lock, write_compiler_ini,
)
from scripts.android.update_client import MARKER, _save_file, read_installed
from scripts.install_game import install

BUILD = "Data/blue-mobile-build.txt"
MOBILE_MARKER = "Data/blue-mobile.txt"
COMPILED = "Data/blue-android-compiled.txt"
MODE = "pinned-world-sources"
ENGINE_FILES = {
    "game.exe", "game.ini", "mkxp.json", "preload.rb", "rgss104e.dll",
    "x64-msvcrt-ruby310.dll", "zlib1.dll", "soundfont.sf2", "credits.txt",
}
EXTRA_DATA = {
    "blue-trainer-album.dat", "blue-hub-presets.dat", "blue-pt-br.dat",
    "blue-music.rxdata", "blue-music-categories.rxdata", "blue-official-rules.dat",
    "blue-radical-ai.dat", "blue-kanto-k06-approach.json", "blue-kanto-k06-services.json",
}


def put_json(path, value):
    atomic_file(path, (json.dumps(value, sort_keys=True) + "\n").encode("utf8"))


def source_inventory(game):
    if not game.is_dir() or game.resolve() != game:
        raise ValueError("Pasta de montagem inválida.")
    files = {}
    names = set()
    for path in game.rglob("*"):
        rel = path.relative_to(game)
        name = rel.as_posix()
        if (_save_file(rel) or not (
                package.allowed(rel) or name.casefold() in ENGINE_FILES or name in package.REGIONAL_FILES or
                name in (BUILD, MOBILE_MARKER, INSTALLER) or
                (rel.parts[0] == "Data" and rel.name in EXTRA_DATA))):
            continue
        if path.is_symlink() or path.resolve() != path:
            raise ValueError(f"Caminho indireto na montagem: {name}")
        if not path.is_file():
            continue
        if name.casefold() in names or ":" in name or "\\" in name:
            raise ValueError(f"Caminho inválido ou ambíguo na montagem: {name}")
        names.add(name.casefold())
        files[name] = path
    return files


def current_install(root):
    if not root.exists():
        return None
    result = read_installed(root)
    stamp = result.get("source_update")
    if (result["channel"] != "multiregion" or not isinstance(stamp, dict) or stamp.get("mode") != MODE):
        raise ValueError("Esta pasta pertence a outra edição. Extraia o instalador em uma pasta nova.")
    if type(result["source_update"].get("release")) is not int:
        raise ValueError("Identidade da instalação pela fonte inválida.")
    return result


def protected_pairs(game):
    return {region: json.loads((game / f"Data/blue-{region}-install.json").read_bytes())["maps"]
            for region in ("kanto", "hoenn")}


def verify_pairs(baseline, candidate):
    for region, pairs in baseline.items():
        if any(candidate[region].get(key) != dest for key, dest in pairs.items()):
            raise ValueError(f"A atualização mudaria um MapID instalado de {region.title()}.")


def assemble(root, staged, previous):
    game = ROOT / "game"
    # This checkout is private to one installation and recipe. Reuse verified
    # source downloads across retries, but rebuild the game from clean inputs.
    owner = ROOT / ".blue-work/android-source-owner.json"
    if game.exists() or game.is_symlink():
        if (game.resolve() != game or not owner.is_file() or owner.is_symlink() or
                json.loads(owner.read_bytes()) != {"game": str(game), "target": str(root)}):
            raise ValueError("Já existe uma pasta game fora desta montagem. Seus arquivos foram preservados.")
        shutil.rmtree(game)
    put_json(owner, {"game": str(game), "target": str(root)})
    state = ROOT / ".blue-work/installation.json"
    state.unlink(missing_ok=True)
    if previous:
        clone_verified_install(root, game, previous)
        # The registered installation already contains the official rules.
        put_json(state, {"game": str(game), "officialRules": True})
    guard = "BLUE_KANTO_WORLD_TARGET"
    previous_guard = os.environ.get(guard)
    os.environ[guard] = str(root)
    try:
        install(ROOT, game, install_windows_editor=False)
    finally:
        if previous_guard is None:
            os.environ.pop(guard, None)
        else:
            os.environ[guard] = previous_guard
    from install_kanto import verify_installed as kanto
    from install_hoenn import verify_installed as hoenn
    kanto(game)
    hoenn(game)
    if previous:
        verify_pairs(protected_pairs(root), protected_pairs(game))
    atomic_file(game / INSTALLER, (ROOT / "scripts/android/source_bootstrap.py").read_bytes())
    # The marker is consumed by Mobile.rb before the first title screen.
    atomic_file(game / MOBILE_MARKER, b"experimental-v1\n")
    for name, path in source_inventory(game).items():
        out = staged / name
        out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, out)


def prepare(root, holder, identity, previous):
    if holder.exists():
        raise ValueError(f"Pasta de compilação já existe: {holder}. Preserve seus arquivos e verifique a tentativa anterior.")
    holder.mkdir()
    game = holder / "game"
    game.mkdir()
    try:
        assemble(root, game, previous)
        for name in ("mkxp.json", "Game.ini"):
            shutil.copyfile(game / name, holder / name)
        config = compiler_config((holder / "mkxp.json").read_text("utf-8-sig"),
                                 "Blue Android Fontes " + identity["revision"][:12])
        atomic_file(game / "mkxp.json", config.encode("utf8"))
        write_compiler_ini(game)
        package.request_compile(game)
        put_json(holder / "receita.json", identity)
    except Exception:
        if holder.resolve() == holder and holder.parent == root.parent:
            shutil.rmtree(holder)
        raise


def finish(root, holder, identity, previous):
    game = holder / "game"
    marker = game / COMPILED
    if not marker.is_file() or marker.read_text("ascii") != package.fingerprint(game):
        return False
    if (game / "Data/blue-android-build-request.txt").exists():
        raise ValueError("A compilação ainda está ativa.")
    package.verify_regions(game,allow_celadon=True)
    native_cache = (game / "Data/PluginScripts.rxdata").read_bytes()
    mobile = package.compiled_mobile(native_cache, (game / package.MOBILE).read_bytes())
    build = ("Compatibility: 2\nRevision: " + identity["revision"] + "\nBuild-UTC: " +
             datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z") +
             "\nMobile-SHA256: " + mobile + "\nPlugins-SHA256: " + package.fingerprint(game) + "\n")
    atomic_file(game / BUILD, build.encode("ascii"))
    for name in ("mkxp.json", "Game.ini"):
        atomic_file(game / name, (holder / name).read_bytes())
    planned = json.loads(installed_manifest("multiregion", identity["revision"], source_inventory(game)))
    planned["source_update"] = {"mode": MODE, "release": identity["release"],
                                "recipe_revision": identity["revision"]}
    if previous is None:
        if root.exists() or root.is_symlink():
            raise ValueError("A pasta de destino passou a existir durante a montagem.")
        if any(_save_file(path.relative_to(game)) for path in game.rglob("*")):
            raise ValueError("A cópia de compilação contém saves. Preserve-os antes de concluir.")
        for name in (COMPILED, "Data/blue-android-stage.txt", "errorlog.txt"):
            (game / name).unlink(missing_ok=True)
        put_json(game / MARKER, planned)
        # Rename within shared storage. The final folder only appears after
        # the compiler and all regional proofs pass.
        game.rename(root)
    else:
        verify_pairs(protected_pairs(root), protected_pairs(game))
        if previous.get("immutable") != planned["immutable"]:
            raise ValueError("Esta receita altera arquivos de configuração ou do motor. Use uma instalação nova.")
        old = previous["files"]
        removed = set(old) - set(planned["files"])
        changed = {name: row for name, row in planned["files"].items() if row != old.get(name)}
        for name in changed.keys() | removed:
            if checked_row(root / name) != old.get(name):
                raise ValueError(f"Arquivo local foi alterado durante a compilação: {name}")
        before = (root / MARKER).read_bytes()
        if read_installed(root) != previous:
            raise ValueError("O jogo mudou durante a compilação.")
        commit_local(root, game, changed, json.dumps(planned, sort_keys=True).encode("utf8"),
                     holder / "backup", verify=lambda path:package.verify_regions(path,allow_celadon=True), before_marker=before,
                     baseline=previous["revision"], removed=removed)
    return True


def clear_finished_workspace(holder):
    if holder.resolve() != holder or holder.is_symlink():
        raise ValueError("Pasta de compilação indireta.")
    if any(_save_file(path.relative_to(holder)) for path in holder.rglob("*")):
        raise ValueError(f"Há saves de teste na pasta temporária. Preserve-os antes de remover {holder}.")
    shutil.rmtree(holder)


def workflow(root, release, revision):
    root = root.absolute()
    if root.resolve() != root or not root.parent.is_dir() or root == ROOT or root.is_relative_to(ROOT):
        raise ValueError("Selecione uma pasta no armazenamento do jogo, separada da receita.")
    holder = root.with_name(root.name + "-Compilar-Fontes")
    if holder.resolve() != holder:
        raise ValueError("Pasta de compilação indireta.")
    previous = current_install(root)
    if previous and (root / RECOVERY_FILE).exists():
        with update_lock(root):
            pending = recovery_plan(root)
            if pending:
                recover_under_lock(root, holder / "backup", pending)
        previous = current_install(root)
    if previous and previous["source_update"]["release"] >= release:
        if previous["source_update"]["release"] == release and previous["revision"] == revision:
            if holder.exists() and (holder / "receita.json").is_file():
                receipt = json.loads((holder / "receita.json").read_bytes())
                if receipt.get("target") == str(root) and receipt.get("revision") == revision:
                    clear_finished_workspace(holder)
            print("O jogo já está atualizado:", revision)
            return
        raise ValueError("A receita disponível é anterior à instalação ou tem uma identidade diferente.")
    marker = root / MARKER
    base = manifest_row(marker) if previous else None
    identity = {"schema": 1, "target": str(root), "release": release, "revision": revision, "baseline": base}
    if not holder.exists():
        prepare(root, holder, identity, previous)
    elif not (holder / "receita.json").is_file() or json.loads((holder / "receita.json").read_bytes()) != identity:
        raise ValueError("Pasta de compilação incompatível com a revisão ou instalação atual.")
    if not finish(root, holder, identity, previous):
        print(f"Abra só para compilar no JoiPlay: {holder / 'game/Game.exe'}")
        print("Depois que o jogo fechar, execute ATUALIZAR-ANDROID.py novamente.")
        return
    # A completed workspace is no longer needed. Never touch the installed
    # folder or profiles outside this dedicated sibling.
    clear_finished_workspace(holder)
    print(f"Instalação verificada: {root / 'Game.exe'}")


def main():
    if len(sys.argv) != 4:
        raise ValueError("Execute ATUALIZAR-ANDROID.py.")
    root, version, revision = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if version < 1 or not SHA.fullmatch(revision) or head != revision:
        raise ValueError("A atualização requer a revisão publicada da receita.")
    workflow(root, version, revision)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, RuntimeError, subprocess.SubprocessError) as error:
        print("INSTALAÇÃO NÃO CONCLUÍDA:", error, file=sys.stderr)
        sys.exit(1)
