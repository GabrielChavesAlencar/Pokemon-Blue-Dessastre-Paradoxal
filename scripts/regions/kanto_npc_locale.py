"""Local pt-BR dialogue compilation for newly imported Kanto overworld NPCs.

No FRLG dialogue text or generated translation model is committed to GitHub.
Only the audited, passive NPCs in the generated pilot inventory are eligible.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

from audit import ROOT, load
from kanto_overworld import source_npc_dialogue, source_sign_dialogue
from server.ruby_marshal import dumps_simple, loads, text

LOCALE_FILE = ROOT / ".blue-work/kanto-npc-ptbr.json"
LITERAL_SCRIPT = re.compile(r'^pbMessage\(_INTL\("((?:\\.|[^"\\])*)"\)\)$')

BATTLE_TRANSLATIONS = {
    "You can't catch a Pokémon that belongs to someone else.":
        "Você não pode capturar um Pokémon que pertence a outro treinador.",
    "You can't throw a Poké Ball!":
        "Você não pode lançar uma Poké Bola!",
    "There is no room left in the PC!":
        "Não há mais espaço no PC!",
    "The Trainer blocked your Poké Ball! Don't be a thief!":
        "O treinador bloqueou a Poké Bola! Você não pode capturar um Pokémon que pertence a outro treinador.",
    "It's no good! It's impossible to aim at a Pokémon that's not in sight!":
        "Não dá para mirar num Pokémon que está fora de vista!",
    "It's no good! It's impossible to aim when there are two Pokémon!":
        "Não dá para mirar com dois Pokémon em campo!",
    "It's no good! It's impossible to aim when there is more than one Pokémon!":
        "Não dá para mirar com mais de um Pokémon em campo!",
    r"... \wt[10]... \wt[10]... \wt[10]... \wt[10]Nope! There's no response.":
        r"... \wt[10]... \wt[10]... \wt[10]... \wt[10]Nada! Nenhuma resposta.",
    "PP: {1: 2d}/{2: 2d}<br>TYPE/{3:s}": "PP: {1: 2d}/{2: 2d}<br>TIPO/{3:s}",
    "{1}'s": "de {1}",
    "Add to your party": "Adicionar à equipe",
    "Send to a Box": "Enviar para um Box",
    "Check party": "Ver equipe",
    "Choose a Pokémon in your party to send to your Boxes.":
        "Escolha um Pokémon da sua equipe para enviar aos Boxes.",
    "{1} has been added to your party.": "{1} entrou para a sua equipe.",
}


def npc_literals(commands):
    """Return precisely the message strings assembled by Essentials' 101/401.

    Essentials' Interpreter.command_101 concatenates successive 401 commands
    with a space, then sends the *whole sentence* to _MAPINTL/pbMessage.
    Translating isolated 401 fragments would miss that runtime lookup.
    """
    messages = []
    current = None

    def flush():
        nonlocal current
        if current is not None and current.strip():
            messages.append(current)
        current = None

    for op in commands:
        code, params = op.attrs["@code"], op.attrs["@parameters"]
        if code == 101 and params:
            flush()
            current = text(params[0])
            continue
        if code == 401 and params and current is not None:
            chunk = text(params[0])
            if chunk and current and not current.endswith(" "):
                current += " "
            current += chunk
            continue
        flush()
        if code == 355 and params:
            found = LITERAL_SCRIPT.fullmatch(text(params[0]))
            if found:
                # Ruby escapes need review before becoming locale keys.
                if "\\" not in found[1] and found[1].strip():
                    messages.append(found[1])
    flush()
    return messages

def imported_npc_lines(source: Path, inventory: dict):
    """Read actual dialogue of NPCs that already passed the Kanto importer."""
    active = [r for r in inventory.get("imported", [])
              if r["kind"] in ("npc_dialogue", "sign_dialogue")]
    by_map = defaultdict(list)
    for record in active:
        by_map[int(record["source_map"])].append(record)
    found = []
    for original_id, rows in sorted(by_map.items()):
        source_map = load(source / "Data" / f"Map{original_id:03}.rxdata")
        source_events = source_map.attrs["@events"]
        for row in rows:
            event_id = int(row["event"])
            if event_id not in source_events:
                raise ValueError(f"Source NPC vanished: {original_id}/{event_id}")
            original = source_events[event_id]
            messages = (source_sign_dialogue(original) if row["kind"] == "sign_dialogue"
                        else source_npc_dialogue(original))
            if messages is None:
                raise ValueError(f"Source NPC event was modified: {original_id}/{event_id}")
            lines = npc_literals(messages)
            found.append({
                "source_map": original_id, "map": int(row["map"]),
                "event": event_id, "x": row["x"], "y": row["y"],
                "lines": lines,
            })
    return found


def read_custom_translations(root: Path = ROOT):
    path = root / ".blue-work/kanto-npc-ptbr.json"
    if not path.is_file():
        return {}, []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if (data.get("version") != 1 or data.get("language") != "pt-BR"
                or not isinstance(data.get("translations"), dict)):
            raise ValueError("Invalid Kanto NPC translation schema")
        values = data["translations"]
        if not all(isinstance(k, str) and isinstance(v, str) for k, v in values.items()):
            raise ValueError("Kanto translations must map strings to strings")
        return values, []
    except (OSError, ValueError, TypeError) as error:
        # An optional translator cache cannot stop the game from launching.
        return {}, [str(error)]


def trainer_defeat_lines(target):
    """Read Kanto PBS lose text without altering trainer identities or rosters."""
    for path in sorted((target / "PBS").glob("trainers_kanto*.txt")):
        trainer = None
        for number, line in enumerate(path.read_text("utf-8-sig").splitlines(), 1):
            if line.startswith("["):
                trainer = line
            if line.lstrip().startswith("LoseText") and "=" in line:
                value = line.partition("=")[2].strip().strip('"')
                yield path, number, trainer, value


def install_npc_locale(root: Path, source: Path, target: Path, *, use_optional_translator=True):
    """Merge only confirmed local NPC translations into the pilot's own locale.

    English remains the original source. pt-BR changes only when players
    choose Português in the Blue options. The main Decades locale is untouched.
    """
    inventory = json.loads((target / "Data/blue-kanto-field-events.json")
                           .read_text(encoding="utf-8"))
    rows = imported_npc_lines(source, inventory)
    custom, errors = read_custom_translations(root)
    path = target / "Data/blue-pt-br.dat"
    # Always update the isolated pilot with the *current* project locale,
    # even if Blue-Story.exe has not recompiled the installed game's cache.
    # This does not change the main Decades installation.
    baseline = {}
    if path.is_file():
        baseline = {text(pair[0]): text(pair[1])
                    for pair in loads(path.read_bytes())}
    upstream = root / "data/pt-br.json"
    if upstream.is_file():
        catalogue = json.loads(upstream.read_text(encoding="utf-8"))
        baseline.update(catalogue.get("translations", {}))

    from scripts.localization.catalog import validate
    # Manually reviewed strings ship with the game so that choosing pt-BR
    # NEVER depends on downloading or manually invoking a translator.
    curated_path = root / "data/kanto-npc-ptbr.json"
    curated = {}
    if curated_path.is_file():
        curated_data = json.loads(curated_path.read_text(encoding="utf-8"))
        if (curated_data.get("version") != 1 or
                curated_data.get("language") != "pt-BR" or
                not isinstance(curated_data.get("translations"), dict)):
            raise ValueError("Invalid built-in Kanto NPC pt-BR catalogue")
        for english, portuguese in curated_data["translations"].items():
            validate(english, portuguese)
            curated[english] = portuguese
    all_lines = {s for row in rows for s in row["lines"]}
    reviewed = root / "data/kanto-event-ptbr.json"
    if reviewed.is_file():
        catalog = json.loads(reviewed.read_text(encoding="utf-8"))
        if (catalog.get("version") != 1 or catalog.get("language") != "pt-BR"
                or not isinstance(catalog.get("translations"), dict)):
            raise ValueError("Invalid reviewed Kanto event pt-BR catalogue")
        active_lines = all_lines | {line for _, _, _, line in trainer_defeat_lines(target)}
        for english in active_lines:
            key = hashlib.sha256(english.encode("utf-8")).hexdigest()
            if key in catalog["translations"]:
                portuguese = catalog["translations"][key]
                validate(english, portuguese)
                curated[english] = portuguese
    baseline.update(curated)

    # Only the source-confirmed, imported, non-quest NPCs are eligible for
    # optional automatic translation. An already installed OFFLINE Argos
    # model can fill gaps; no network call or package install occurs here.
    new_locale = {}
    private_path = root / ".blue-work/kanto-npc-ptbr.json"
    automated_cache = False
    if private_path.is_file():
        try:
            metadata = json.loads(private_path.read_text(encoding="utf-8"))
            automated_cache = str(metadata.get("translation_method", "")).startswith(
                "Argos Translate")
        except (OSError, ValueError, TypeError):
            pass
    for english, portuguese in custom.items():
        if english not in all_lines or not portuguese.strip():
            continue
        # A preexisting, unreviewed Argos cache must not replace a human-
        # reviewed translation that has since shipped with the project.
        if automated_cache and english in curated:
            continue
        try:
            validate(english, portuguese)
        except ValueError as error:
            errors.append(f"Invalid controls in NPC text {english[:90]!r}: {error}")
            continue
        new_locale[english] = portuguese

    automatic = {}
    waiting = sorted(s for s in all_lines
                     if (not baseline.get(s) or baseline[s] == s)
                     and s not in new_locale and s not in curated)
    if waiting and use_optional_translator:
        try:
            from translate_kanto_npcs import get_argos_translator, safe_translate
            offline_translator = get_argos_translator(False)
        except (ImportError, RuntimeError, OSError, ValueError):
            offline_translator = None
        if offline_translator:
            for english in waiting:
                translated, problem = safe_translate(english, offline_translator)
                if translated and not problem:
                    automatic[english] = translated
    baseline.update(automatic)
    # Explicit private corrections always have the final priority.
    baseline.update(new_locale)
    for english, portuguese in BATTLE_TRANSLATIONS.items():
        validate(english, portuguese)
    baseline.update(BATTLE_TRANSLATIONS)
    if baseline:
        path.write_bytes(dumps_simple([[k, v] for k, v in sorted(baseline.items())]))

    pending = []
    translated = []
    covered = {en for en in all_lines if en in curated or baseline.get(en, en) != en}
    for row in rows:
        missing = [en for en in row["lines"] if en not in covered]
        item = {k: row[k] for k in ("source_map", "map", "event", "x", "y")}
        if missing:
            pending.append({**item, "english_lines": missing})
        if len(missing) != len(row["lines"]):
            translated.append(item)
    report = {
        "version": 1, "language": "pt-BR",
        "total_npc_events": len(rows),
        "total_unique_english_lines": len(all_lines),
        "localized_unique_lines": len(covered),
        "remaining_unique_lines": len(all_lines - covered),
        "npc_events_with_some_portuguese": len(translated),
        "missing_english_lines_by_npc": pending,
        "invalid_local_translations": errors,
        "reviewed_project_translations": len(set(curated) & all_lines),
        "automatic_unreviewed_translations": [
            {"english": k, "portuguese": v}
            for k, v in sorted(automatic.items())
        ],
        "local_translation_file": str(root / ".blue-work/kanto-npc-ptbr.json"),
    }
    (target / "Data/blue-kanto-npc-translation-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"[KANTO PT-BR] {report['localized_unique_lines']}/"
          f"{report['total_unique_english_lines']} NPC lines localized. "
          "Untranslated lines documented in Data/blue-kanto-npc-translation-audit.json.")
    return report
