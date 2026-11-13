"""Build and verify the *isolated* Kanto JoiPlay pilot; never substitute Decades."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.android.package import allowed, compiled_mobile, fingerprint, request_compile
from scripts.android.build_manifest import installed_manifest, verify_manifest

ASSET = "Blue-Android-Kanto-Piloto.zip"
FOLDER = "Pokemon-Blue-Kanto-Android/"
PILOT = ROOT / ".blue-work/kanto-pilot"
MOBILE = "Plugins/ZZZZ Blue Battle Lab/Mobile.rb"
KANTO_PLUGIN = "Plugins/ZZZZZ Blue Kanto Pilot/KantoPilot.rb"
REGIONAL_FILES = (
    "Data/blue-kanto-start.txt",
    "Data/blue-kanto-music.txt",
    "Data/blue-kanto-experimental-stops.txt",
    "Data/blue-kanto-silph-floors.txt",
)
SHARED_FILES = (
    "Data/blue-trainer-album.dat",
    "Data/blue-hub-presets.dat",
    "Data/blue-pt-br.dat",
    "Data/blue-music.rxdata",
    "Data/blue-music-categories.rxdata",
    "Data/blue-official-rules.dat",
    "Data/blue-radical-ai.dat",
)
CORE_FILES = (
    "Game.exe", "Game.ini", "mkxp.json", "Kanto pilot.json",
    "Data/System.rxdata", "Data/Scripts.rxdata",
    "Data/MapInfos.rxdata", "Data/Tilesets.rxdata",
    "Data/PluginScripts.rxdata", MOBILE, KANTO_PLUGIN,
    *REGIONAL_FILES,
)
DOC = (
    "PILOTO KANTO EXPERIMENTAL PARA JOIPLAY + RPG MAKER PLUGIN.\n"
    "Nao e APK. Extraia o ZIP completo numa pasta separada.\n"
    "No JoiPlay selecione Game.exe da pasta Pokemon-Blue-Kanto-Android.\n"
    "Use Novo Jogo: este pacote e o piloto isolado de Kanto, nao o Decades.\n"
    "Os saves usam o perfil Kanto Piloto; nao sobrescreva os saves do Decades.\n"
    "Fonte dos mapas: Essentials FRLG 1.1, TheTinfoilTemplar, equipe Essentials.\n"
    "https://eeveeexpo.com/resources/1797/\n"
    "Atualizacoes: feche o JoiPlay; no Termux use Python.\n"
    "Verificar: python ATUALIZAR-ANDROID.py\n"
    "Instalar patch: python ATUALIZAR-ANDROID.py --update\n"
    "Guia no GitHub: docs/ANDROID_ATUALIZACOES_INCREMENTAIS.md\n"
    "A compatibilidade final depende de testes em aparelho Android real.\n"
)

def _kanto_save_profile(text: str) -> bool:
    """mkxp.json is JSON-with-comments in Decades, not strict JSON."""
    expected = {
        "dataPathApp": "Kanto Piloto",
        "dataPathOrg": "Dessastre Paradoxal Kanto Testes",
    }
    # Existing Kanto pilot.py writes both settings on a *single* JSONC line.
    # Drop full-line comments first; never let a commented old value count.
    active = "\n".join(line for line in text.splitlines()
                       if not line.lstrip().startswith("//"))
    for key, value in expected.items():
        matches = re.findall(r'"' + key + r'"\s*:\s*"((?:[^"\\]|\\.)*)"',
                             active)
        if len(matches) != 1:
            return False
        try:
            parsed = json.loads('"' + matches[0] + '"')
        except json.JSONDecodeError:
            return False
        if parsed != value:
            return False
    return True

def _metadata(game: Path) -> dict:
    marker = game / "Kanto pilot.json"
    if not marker.is_file() or marker.is_symlink():
        raise ValueError("Pilot metadata absent; refusing to package the main Decades game.")
    metadata = json.loads(marker.read_text(encoding="utf-8"))
    if (metadata.get("save_app") != "Kanto Piloto"
            or metadata.get("save_org") != "Dessastre Paradoxal Kanto Testes"):
        raise ValueError("Pilot has no independent Kanto save profile.")
    mapping = metadata.get("maps")
    declared = json.loads((ROOT / "data/regions/kanto-source.json").read_text(encoding="utf8"))["maps"]
    if (not isinstance(mapping, dict) or set(mapping) != set(declared)
            or any(type(v) is not int or not 276 <= v <= 999 for v in mapping.values())
            or len(set(mapping.values())) != len(mapping)):
        raise ValueError("Pilot map remapping differs from the pinned Kanto manifest.")
    ini = (game / "Game.ini").read_text(encoding="utf-8-sig")
    if not re.search(r"(?m)^Title=Kanto Piloto\s*$", ini):
        raise ValueError("Kanto title missing in Game.ini.")
    config_text = (game / "mkxp.json").read_text(encoding="utf-8-sig")
    if not _kanto_save_profile(config_text):
        raise ValueError("JoiPlay save paths are not isolated from Decades.")
    start = (game / REGIONAL_FILES[0]).read_text(encoding="ascii").strip().split(",")
    if (len(start) != 5 or start[:2] != ["BLUE_KANTO_START_V1", "KANTO"]
            or not all(x.isdecimal() for x in start[2:])
            or int(start[2]) != mapping["7"]):
        raise ValueError("Kanto mobile pilot must start inside the player's Pallet house.")
    for name in CORE_FILES:
        file = game / name
        if not file.is_file() or file.is_symlink() or file.stat().st_size == 0:
            raise ValueError(f"Missing or empty required Kanto runtime file: {name}")
    for dest in mapping.values():
        file = game / f"Data/Map{dest:03d}.rxdata"
        if not file.is_file() or file.is_symlink() or not file.stat().st_size:
            raise ValueError(f"Uncompiled or missing Kanto map: {dest}")
    if (game / "Data/blue-android-build-request.txt").exists():
        raise ValueError("Android native compile request is still pending.")
    if (game / "Data/blue-kanto-proof.rb").exists():
        # The CI native-check script modifies Main to exit before gameplay.
        # The test hook source must be removed before packaging.
        raise ValueError("Kanto native test-only script remains in the mobile build.")
    from scripts.official_rules.prepare_restore import Marshal
    import zlib
    for row in Marshal((game / "Data/Scripts.rxdata").read_bytes()).read():
        if row[1] == b"Main":
            main = zlib.decompress(row[2])
            if b'blue-kanto-proof.rb' in main or b'KantoNativeCheck.run' in main:
                raise ValueError("Main would run native CI test instead of Kanto gameplay.")
            break
    else:
        raise ValueError("Compiled runtime lacks Main.")
    return metadata

def _compiled(game: Path) -> tuple[str, str]:
    marker = game / "Data/blue-android-compiled.txt"
    digest = fingerprint(game)
    if not marker.is_file() or marker.read_text(encoding="ascii") != digest:
        raise ValueError("Native Android compile is absent or stale.")
    cache = (game / "Data/PluginScripts.rxdata").read_bytes()
    mobile = compiled_mobile(cache, (game / MOBILE).read_bytes())
    compiled_kanto(cache, (game / KANTO_PLUGIN).read_bytes())
    return digest, mobile

def compiled_kanto(cache: bytes, source: bytes) -> str:
    """Prove regional event handlers were included in the native plugin compile."""
    from server.ruby_marshal import loads
    import zlib
    expected = source.replace(b"\r\n", b"\n")
    for plugin in loads(cache):
        for name, compressed in plugin[2]:
            if name == b"KantoPilot.rb":
                actual = zlib.decompress(compressed).replace(b"\r\n", b"\n")
                if actual == expected:
                    return hashlib.sha256(expected).hexdigest()
    raise ValueError("KantoPilot.rb was not compiled into the game plugin cache.")

def select_files(game: Path) -> dict[str, Path]:
    selected = {f.relative_to(game).as_posix(): f for f in game.rglob("*")
                if f.is_file() and not f.is_symlink() and allowed(f.relative_to(game))}
    for name in (*REGIONAL_FILES, *SHARED_FILES, "Kanto pilot.json"):
        file = game / name
        if file.is_file() and not file.is_symlink():
            selected[name] = file
        elif name in REGIONAL_FILES or name == "Kanto pilot.json":
            raise ValueError(f"Mandatory regional metadata was not found: {name}")
    for item in list(selected):
        if item.startswith("Data/blue-kanto-proof") or item.lower().endswith((".log", ".bak")):
            raise ValueError("Diagnostic or backup selected for distribution: " + item)
    if not set(CORE_FILES).issubset(selected):
        raise ValueError("The pilot archive is missing the Kanto runtime or metadata.")
    return selected

def build(game: Path, output: Path, revision: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("A full Git commit hash is mandatory for published Android builds.")
    _metadata(game)
    plugin_hash, mobile_hash = _compiled(game)
    files = select_files(game)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise ValueError("Existing Kanto mobile ZIP must not be overwritten.")
    text = DOC + "Revision: " + revision + "\n"
    build_info = ("Region: KANTO\nRevision: " + revision + "\n"
                  "Mobile-SHA256: " + mobile_hash + "\n"
                  "Plugins-SHA256: " + plugin_hash + "\n")
    try:
        with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                             allowZip64=True) as archive:
            for name, file in sorted(files.items()):
                archive.write(file, FOLDER + name)
            archive.writestr(FOLDER + "LEIA-ME-ANDROID-KANTO.txt", text)
            archive.writestr(FOLDER + "Data/blue-kanto-android-build.txt", build_info)
            archive.writestr(FOLDER + "Data/blue-update.json",
                             installed_manifest("kanto", revision, {
                                 **files, "Data/blue-kanto-android-build.txt": build_info.encode("utf8"),
                                 "ATUALIZAR-ANDROID.py":
                                     (ROOT / "scripts/android/update_client.py").read_bytes(),
                                 "LEIA-ME-ANDROID-KANTO.txt": text.encode("utf8")
                             }))
            archive.writestr(FOLDER + "ATUALIZAR-ANDROID.py",
                             (ROOT / "scripts/android/update_client.py").read_bytes())
        verify_archive(output, revision)
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    digest = hashlib.sha256()
    with output.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    output.with_name(output.name + ".sha256").write_text(digest.hexdigest() + "  " + output.name + "\n", encoding="ascii")
    return {"asset": ASSET, "revision": revision, "files": len(files), "sha256": digest.hexdigest(),
            "bytes": output.stat().st_size}

def verify_archive(zip_path: Path, revision: str) -> dict:
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError("Duplicate ZIP entries.")
        if any(not name.startswith(FOLDER) or name.endswith("/") for name in names):
            raise ValueError("Unexpected ZIP entry or folder.")
        expected = {FOLDER + name for name in CORE_FILES}
        if not expected.issubset(names):
            raise ValueError("ZIP has no complete Kanto pilot installation.")
        metadata = json.loads(archive.read(FOLDER + "Kanto pilot.json"))
        manifest = json.loads((ROOT / "data/regions/kanto-source.json").read_text(encoding="utf8"))["maps"]
        mapping = metadata.get("maps", {})
        if (not isinstance(mapping, dict) or set(mapping) != set(manifest)
                or any(FOLDER + f"Data/Map{num:03d}.rxdata" not in names for num in mapping.values())):
            raise ValueError("ZIP is missing mapped Kanto terrain.")
        info = archive.read(FOLDER + "Data/blue-kanto-android-build.txt").decode("utf8")
        readme = archive.read(FOLDER + "LEIA-ME-ANDROID-KANTO.txt").decode("utf8")
        if "Revision: " + revision + "\n" not in info or "Revision: " + revision + "\n" not in readme:
            raise ValueError("Archive revision does not match the published commit.")
        mobile = compiled_mobile(archive.read(FOLDER + "Data/PluginScripts.rxdata"),
                                 archive.read(FOLDER + MOBILE))
        compiled_kanto(archive.read(FOLDER + "Data/PluginScripts.rxdata"),
                       archive.read(FOLDER + KANTO_PLUGIN))
        if "Mobile-SHA256: " + mobile + "\n" not in info:
            raise ValueError("JoiPlay adapter in ZIP differs from the compiled source.")
        config = archive.read(FOLDER + "mkxp.json").decode("utf-8-sig")
        if not _kanto_save_profile(config):
            raise ValueError("Archived Kanto saves would overlap with Decades.")
        verify_manifest(archive, FOLDER, "kanto", revision)
        return {"region": "KANTO", "revision": revision, "maps": len(mapping), "mobile_sha256": mobile}

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game-dir", type=Path, default=PILOT)
    parser.add_argument("--output", type=Path, default=ROOT / "dist" / ASSET)
    parser.add_argument("--revision", required=False, default="")
    parser.add_argument("--request-compile", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.request_compile:
        _metadata(args.game_dir)
        request_compile(args.game_dir)
        print("Kanto JoiPlay native compilation requested.")
    elif args.verify:
        print(json.dumps(verify_archive(args.output, args.revision), ensure_ascii=False))
    else:
        print(json.dumps(build(args.game_dir, args.output, args.revision), ensure_ascii=False))

if __name__ == "__main__":
    main()
