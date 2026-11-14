"""Translate actual imported FRLG NPC text to Brazilian Portuguese on the user's PC.

Run once after preparing an isolated Kanto pilot. Uses a local Argos Translate
model (downloaded only with --install-model), then rebuilds the pilot to embed
translations in the pilot-only BlueLocale table. No third-party dialogue text
is uploaded or committed to the Blue repo.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from audit import ROOT
from kanto_npc_locale import imported_npc_lines, read_custom_translations
from scripts.localization.catalog import CONTROL, validate


def current_pilot(root: Path):
    workspace = root / ".blue-work"
    candidates = [
        item for item in workspace.glob("kanto-pilot*")
        if (item / "Kanto pilot.json").is_file() and
           (item / "Data/blue-kanto-field-events.json").is_file()
    ]
    if not candidates:
        raise ValueError(
            "No Kanto pilot found. Run KANTO_JOGAR_EXPERIMENTAL.bat first.")
    return max(candidates, key=lambda item: (
        (item / "Data/blue-kanto-field-events.json").stat().st_mtime, item.name))


def get_argos_translator(install_model: bool):
    try:
        from argostranslate import package, translate
    except ImportError as error:
        raise RuntimeError(
            "Argos Translate is not installed. Run: py -3 -m pip install argostranslate"
        ) from error

    def model():
        source = next((lang for lang in translate.get_installed_languages()
                       if lang.code == "en"), None)
        target = next((lang for lang in translate.get_installed_languages()
                       if lang.code == "pt"), None)
        if source is None or target is None:
            return None
        try:
            return source.get_translation(target)
        except Exception:
            return None

    translator = model()
    if translator:
        return translator
    if not install_model:
        raise RuntimeError(
            "English-to-Portuguese Argos model missing. Run again with --install-model.")
    package.update_package_index()
    available = package.get_available_packages()
    supported = [entry for entry in available if entry.from_code == "en"
                 and entry.to_code == "pt"]
    if not supported:
        raise RuntimeError("Argos translation package en -> pt unavailable.")
    print("[KANTO PT-BR] Downloading and installing Argos en->pt model locally...",
          flush=True)
    file = supported[0].download()
    package.install_from_path(file)
    translator = model()
    if not translator:
        raise RuntimeError("Could not activate downloaded Argos en->pt model.")
    return translator


def safe_translate(english: str, translator):
    """Avoid producing malformed event controls and placeholder replacements."""
    # Rich text and character variable escapes require contextual review.
    # Do not submit their control sequences to a machine translator.
    if CONTROL.search(english):
        return None, "contains game control/placeholder"
    if re.search(r"#\{|\{[A-Za-z_][^}]*\}", english):
        return None, "contains dynamic interpolation"
    if not re.search(r"[A-Za-z]{3}", english):
        return None, "not a prose sentence"
    try:
        portuguese = translator.translate(english).strip()
        if portuguese == english or not portuguese:
            return None, "no distinct Portuguese translation returned"
        validate(english, portuguese)
        # Generic token artifacts can break the event dialogue UI.
        if "\ufffd" in portuguese or "\u2047" in portuguese:
            return None, "unknown glyph in translation"
        return portuguese, None
    except Exception as error:
        return None, f"{type(error).__name__}: {error}"


def run(root: Path, pilot: Path, source: Path, install_model: bool):
    if not (source / "Data/MapInfos.rxdata").is_file():
        raise ValueError("FRLG source not found. Use Testar Kanto first.")
    if not (pilot / "Data/blue-kanto-field-events.json").is_file():
        raise ValueError("Pilot field events inventory not found.")
    inventory = json.loads(
        (pilot / "Data/blue-kanto-field-events.json").read_text("utf-8"))
    npc_records = imported_npc_lines(source, inventory)
    strings = sorted({line for row in npc_records for line in row["lines"]})
    existing, errors = read_custom_translations(root)
    if errors:
        raise ValueError("Existing translations are invalid: " + "; ".join(errors))
    compiled = json.loads((root / "data/pt-br.json").read_text("utf8"))
    originals = compiled.get("translations", {})
    # Reviewed translations committed with Blue supersede raw machine output.
    # In particular the screenshot-confirmed Viridian guard must never be
    # re-translated into an unreviewed Argos version.
    curated_path = root / "data/kanto-npc-ptbr.json"
    reviewed = (json.loads(curated_path.read_text("utf8"))
                .get("translations", {}) if curated_path.is_file() else {})
    pending = [line for line in strings if line not in existing
               and not originals.get(line) and not reviewed.get(line)]
    print(f"[KANTO PT-BR] {len(npc_records)} imported NPCs, {len(strings)} "
          f"unique lines, {len(pending)} need author-time localization.", flush=True)
    if not pending:
        return {"npc_events": len(npc_records), "localized_new": 0,
                "remaining": 0, "pending": []}
    translator = get_argos_translator(install_model)
    translated = {}
    review = []
    for i, english in enumerate(pending, 1):
        portuguese, issue = safe_translate(english, translator)
        if issue:
            review.append({"english": english, "reason": issue})
        else:
            translated[english] = portuguese
        if i % 25 == 0:
            print(f"[KANTO PT-BR] {i}/{len(pending)} texts processed", flush=True)
    # Write translations only to private .blue-work. The source FRLG script
    # is never changed, and the English original still works in English mode.
    result = {
        "version": 1, "language": "pt-BR",
        "translation_method": "Argos Translate en-pt, automatic/unreviewed",
        "translations": {**existing, **translated},
    }
    outfile = root / ".blue-work/kanto-npc-ptbr.json"
    outfile.parent.mkdir(parents=True, exist_ok=True)
    outfile.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
    report = {"npc_events": len(npc_records), "localized_new": len(translated),
              "remaining": len(review), "pending": review}
    (root / ".blue-work/kanto-npc-ptbr-review.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"[KANTO PT-BR] {len(translated)} new pt-BR translations saved in {outfile}.")
    if review:
        print(f"[KANTO PT-BR] {len(review)} strings require manual review. "
              "See .blue-work/kanto-npc-ptbr-review.json.")
    print("[KANTO PT-BR] Rebuild Testar Kanto to apply locale; select Português "
          "in the game settings.")
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pilot", type=Path,
                        help="Pilot to inspect; default most recent isolated pilot")
    parser.add_argument("--source", type=Path,
                        default=ROOT / ".blue-work/frlg-source/Essentials FRLG")
    parser.add_argument("--install-model", action="store_true",
                        help="Download/install the local Argos en->pt model if absent")
    args = parser.parse_args(argv)
    pilot = args.pilot or current_pilot(ROOT)
    try:
        run(ROOT, pilot.resolve(), args.source.resolve(), args.install_model)
    except (OSError, ValueError, RuntimeError) as error:
        print("[ERRO] Kanto tradução de NPCs:", error, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
