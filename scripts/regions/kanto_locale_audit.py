"""Audit the actual installed Kanto maps and their resolved locale keys."""

from __future__ import annotations

import argparse
import json
import re
import zlib
from pathlib import Path

from audit import KANTO, ROOT, load
from kanto_npc_locale import BATTLE_TRANSLATIONS, trainer_defeat_lines
from scripts.localization.catalog import CONTROL, validate
from server.ruby_marshal import text

SHARED_BATTLE_SECTIONS = re.compile(r"^(?:Battle(?:_|$)|Item_Effects)")
STOCK_LABELS = {"Mega Ring", "Mega {1}", "{1}!", "PP: {1}/{2}"}
ASSET_PATH = re.compile(r"^(?:Graphics|Audio|Data|Plugins|Fonts|PBS)/", re.I)

BRIDGE = re.compile(r"BlueKantoPilot\.npc_dialogue\((\d+), (\d+), (\d+)\)")
HANDLER = re.compile(r"BlueKantoPilot\.([a-z_][a-z_0-9]*)")
METHOD = re.compile(r"^[ \t]*def self\.([a-z_][a-z_0-9]*)[?( ]?", re.M)
LITERAL = r'"((?:\\.|[^"\\])*)"'
BATTLE_TEXT = re.compile(r"_(?:INTL|ISPRINTF)\(\s*" + LITERAL)
PAIR = re.compile(r"BlueKantoPilot\.t\(\s*" + LITERAL + r",\s*" + LITERAL)
DISPLAY = re.compile(r"(?:_INTL|_MAPINTL|pbMessage|pbConfirmMessage)\s*\(\s*" + LITERAL)


def battle_origin(key):
    if key.startswith("You can't catch"):
        return "Capture warning (plain text)"
    if key.startswith(("You can't throw", "There is no room", "It's no good!")):
        return "Doubles Wild Captures / CanUseInBattle"
    return "Battle_CatchAndStoreMixin"



def ruby_literal(value):
    return re.sub(r'\\([nrt"\\])', lambda match: {"n": "\n", "r": "\r", "t": "\t"}.get(
        match[1], match[1]), value)


def ruby_methods(path):
    source = path.read_text("utf-8")
    methods = list(METHOD.finditer(source))
    return {method[1]: (method.start(), source[method.start(): end.start() if end else len(source)])
            for method, end in zip(methods, [*methods[1:], None])}, source


def audit_pilot(target, root):
    data = target / "Data"
    mapping = json.loads((target / "Kanto pilot.json").read_text("utf-8"))["maps"]
    manifest = json.loads((root / "data/regions" / KANTO.name).read_text("utf-8"))
    if set(mapping) != set(manifest["maps"]) or len(set(mapping.values())) != len(mapping):
        raise ValueError("A auditoria precisa do conjunto completo de MapIDs do piloto Kanto")
    preview = {str(num) for num in manifest.get("preview_only", [])}
    infos = load(data / "MapInfos.rxdata")
    locale_file = data / "blue-pt-br.dat"
    lookup = ({text(k): text(v) for k, v in load(locale_file)} if locale_file.is_file() else {})
    dialogues = {(mid, eid, index): text(line)
                 for mid, eid, lines in load(data / "blue-kanto-npc-dialogues.dat")
                 for index, line in enumerate(lines)}
    methods, source = ruby_methods(root / "scripts/regions/KantoPilot.rb")
    discovered = {}
    imported_events = set()
    pending = []
    map_rows = []
    imported_keys = set()
    reached_handlers = set()

    def record(origin, value, location, *, approved=False):
        if not re.search(r"[A-Za-zÀ-ÿ]", CONTROL.sub("", value)):
            return
        translated = lookup.get(value)
        ok = bool(translated and translated != value)
        if approved:
            ok = True
        discovered[(origin, value)] = ok
        location["keys"].add((origin, value))
        if not ok:
            pending.append({k: v for k, v in location.items() if k != "keys"} |
                           {"origin": origin, "text": value})

    def event_script(code, where):
        if match := BRIDGE.fullmatch(code):
            key = tuple(map(int, match.groups()))
            value = dialogues[key]
            imported_events.add(key[:2])
            imported_keys.add(value)
            record("imported dialogue", value, where,
                   approved=lookup.get(value) == value and CONTROL.sub("", value).strip() == "Fighting Dojo")
            return
        for match in DISPLAY.finditer(code):
            record("event script", ruby_literal(match[1]), where)
        for handler in sorted(set(HANDLER.findall(code)) & methods.keys()):
            reached_handlers.add(handler)
            _, body = methods[handler]
            for english, portuguese in PAIR.findall(body):
                english, portuguese = ruby_literal(english), ruby_literal(portuguese)
                validate(english, portuguese)
                record(f"KantoPilot.{handler}", english, where, approved=True)
            for match in DISPLAY.finditer(body):
                record(f"KantoPilot.{handler}", ruby_literal(match[1]), where)

    for old, mid in sorted(mapping.items(), key=lambda item: item[1]):
        at = {"map": mid, "source_map": int(old), "name": text(infos[mid].attrs["@name"]), "keys": set()}
        events = load(data / f"Map{mid:03d}.rxdata").attrs["@events"]
        before = len(pending)
        for eid, event in sorted(events.items()):
            for i, page in enumerate(event.attrs["@pages"], 1):
                where = at | {"event": eid, "event_name": text(event.attrs["@name"]), "page": i}
                commands = [(e.attrs["@code"], e.attrs["@parameters"]) for e in page.attrs["@list"]]
                j = 0
                while j < len(commands):
                    code, args = commands[j]
                    j += 1
                    if not args:
                        continue
                    if code in (101, 105):
                        value = text(args[0]) if code == 101 else ""
                        while j < len(commands) and commands[j][0] == (401 if code == 101 else 405):
                            next_line = text(commands[j][1][0])
                            value += (" " if value and not value.endswith(" ") else "") + next_line
                            j += 1
                        record(f"event command {code}", value, where)
                    elif code == 102:
                        for option in args[0]:
                            record("event choice", text(option), where)
                    elif code == 355:
                        lines = [text(args[0])]
                        while j < len(commands) and commands[j][0] == 655:
                            lines.append(text(commands[j][1][0]))
                            j += 1
                        event_script("\n".join(lines), where)
                    elif code == 111 and len(args) > 1 and args[0] == 12:
                        event_script(text(args[1]), where)
        keys = at.pop("keys")
        map_rows.append(at | {"preview_only": old in preview, "events": len(events),
                              "distinct_text_sources": len(keys), "pending": len(pending) - before})

    # Include indirect script calls and text dispatched outside map interpreters.
    for name, (offset, body) in methods.items():
        where = {"file": "scripts/regions/KantoPilot.rb", "line": source.count("\n", 0, offset) + 1,
                 "event": None, "handler": name, "keys": set()}
        for english, portuguese in PAIR.findall(body):
            validate(ruby_literal(english), ruby_literal(portuguese))
        if name not in reached_handlers:
            for match in DISPLAY.finditer(body):
                record(f"KantoPilot.{name}", ruby_literal(match[1]), where)

    trainer_lines = list(trainer_defeat_lines(target))
    for path, number, trainer, value in trainer_lines:
        record("trainer defeat text", value,
               {"file": f"PBS/{path.name}", "line": number, "trainer": trainer, "keys": set()})
    shared = set()
    scripts = data / "Scripts.rxdata"
    if scripts.is_file():
        for _, section, packed in load(scripts):
            name = text(section)
            if not SHARED_BATTLE_SECTIONS.match(name) or name.startswith("Battle_AI"):
                continue
            source_code = zlib.decompress(packed).decode("utf-8")
            for match in BATTLE_TEXT.finditer(source_code):
                value = ruby_literal(match[1])
                if ASSET_PATH.match(value) or value in STOCK_LABELS:
                    continue
                shared.add(value)
                record(f"native battle / {name}", value,
                       {"file": "Data/Scripts.rxdata", "line": source_code.count("\n", 0, match.start()) + 1,
                        "event": None, "keys": set()})
    for key in BATTLE_TRANSLATIONS:
        record(battle_origin(key), key, {"file": "Data/Scripts.rxdata", "event": None, "keys": set()})
    return {"schema": 1, "maps": map_rows, "imported_events": len(imported_events),
            "imported_unique": len(imported_keys),
            "imported_localized": sum(discovered.get(("imported dialogue", value), False)
                                      for value in imported_keys),
            "unique_bilingual_story": len(set(PAIR.findall(source))) + len(re.findall(
                r'\[\[' + LITERAL + r', ' + LITERAL + r'\], (?:true|false)\]', source)),
            "native_battle_keys": len(shared),
            "trainer_lines": len(trainer_lines),
            "trainer_unique": len({value for _, _, _, value in trainer_lines}),
            "pending": pending}


def write_audit(target, root=ROOT):
    report = audit_pilot(target, root)
    path = target / "Data/blue-kanto-locale-audit.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"[KANTO PT-BR] {len(report['maps'])} maps audited; "
          f"{len(report['pending'])} outstanding occurrences. See {path.name}.")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pilot", type=Path)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = audit_pilot(args.pilot, ROOT)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    raise SystemExit(1 if args.strict and report["pending"] else 0)
