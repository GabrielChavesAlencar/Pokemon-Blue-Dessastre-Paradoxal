"""Local pt-BR dialogue compilation for newly imported Kanto overworld NPCs.

No FRLG dialogue text or generated translation model is committed to GitHub.
Only the audited, passive NPCs in the generated pilot inventory are eligible.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path

from audit import ROOT, load
from kanto_overworld import source_npc_dialogue
from server.ruby_marshal import dumps_simple, loads, text

LOCALE_FILE = ROOT / ".blue-work/kanto-npc-ptbr.json"
LITERAL_SCRIPT = re.compile(r'^pbMessage\(_INTL\("((?:\\.|[^"\\])*)"\)\)$')


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
              if r["kind"] == "npc_dialogue"]
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
            messages = source_npc_dialogue(original)
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


def install_npc_locale(root: Path, source: Path, target: Path):
    """Merge only confirmed local NPC translations into the pilot's own locale.

    English remains the original source. pt-BR changes only when players
    choose Português in the Blue options. The main Decades locale is untouched.
    """
    inventory = json.loads((target / "Data/blue-kanto-field-events.json")
                           .read_text(encoding="utf-8"))
    rows = imported_npc_lines(source, inventory)
    custom, errors = read_custom_translations(root)
    path = target / "Data/blue-pt-br.dat"
    baseline = {}
    if path.is_file():
        baseline = {text(pair[0]): text(pair[1])
                    for pair in loads(path.read_bytes())}
    else:
        # Some custom installs may not have compiled the locale yet.
        upstream = root / "data/pt-br.json"
        if upstream.is_file():
            original = json.loads(upstream.read_text(encoding="utf-8"))
            baseline = original.get("translations", {})

    # Controls and variables must survive source-to-target conversion.
    from scripts.localization.catalog import validate
    all_lines = {s for row in rows for s in row["lines"]}
    new_locale = {}
    for english, portuguese in custom.items():
        if english not in all_lines or not portuguese.strip():
            continue
        try:
            validate(english, portuguese)
        except ValueError as error:
            errors.append(f"Invalid controls in NPC text {english[:90]!r}: {error}")
            continue
        new_locale[english] = portuguese
    baseline.update(new_locale)
    if baseline:
        path.write_bytes(dumps_simple([[k, v] for k, v in sorted(baseline.items())]))

    pending = []
    translated = []
    for row in rows:
        missing = [en for en in row["lines"] if en not in baseline or
                   baseline[en] == en]
        item = {k: row[k] for k in ("source_map", "map", "event", "x", "y")}
        if missing:
            pending.append({**item, "english_lines": missing})
        if len(missing) != len(row["lines"]):
            translated.append(item)
    report = {
        "version": 1, "language": "pt-BR",
        "total_npc_events": len(rows),
        "total_unique_english_lines": len(all_lines),
        "localized_unique_lines": len([s for s in all_lines
                                       if s in baseline and baseline[s] != s]),
        "remaining_unique_lines": len([s for s in all_lines
                                       if s not in baseline or baseline[s] == s]),
        "npc_events_with_some_portuguese": len(translated),
        "missing_english_lines_by_npc": pending,
        "invalid_local_translations": errors,
        "local_translation_file": str(root / ".blue-work/kanto-npc-ptbr.json"),
    }
    (target / "Data/blue-kanto-npc-translation-audit.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(f"[KANTO PT-BR] {report['localized_unique_lines']}/"
          f"{report['total_unique_english_lines']} NPC lines localized. "
          "Untranslated lines documented in Data/blue-kanto-npc-translation-audit.json.")
    return report
