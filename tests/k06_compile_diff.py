"""Report typed compiler changes in disposable CI maps; never export map contents."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "regions"))
from audit import load  # noqa: E402
from server.ruby_marshal import RubyObject  # noqa: E402


def describe(value):
    if isinstance(value, RubyObject):
        code = value.attrs.get("@code")
        code = f":opcode={code}" if type(code) is int else ""
        return f"{value.name}{code}"
    if type(value) in {bool, int, type(None)}:
        return repr(value)
    if isinstance(value, (dict, list, bytes, str)):
        return f"{type(value).__name__}[{len(value)}]"
    return type(value).__name__


def diff(previous, after, path):
    if type(previous) is type(after) and not isinstance(previous, (RubyObject, dict, list)) and previous == after:
        return
    if type(previous) is type(after):
        if isinstance(previous, RubyObject) and previous.name == after.name:
            yield from diff(previous.attrs, after.attrs, path)
            return
        if isinstance(previous, dict):
            for key in sorted(previous.keys() | after.keys(), key=str):
                label = str(key) if re.fullmatch(r"@\w+|\d+", str(key)) else "[key]"
                pair = f"{path}/{label}"
                if key not in previous:
                    yield f"{pair} added ({describe(after[key])})"
                elif key not in after:
                    yield f"{pair} removed ({describe(previous[key])})"
                else:
                    yield from diff(previous[key], after[key], pair)
            return
        if isinstance(previous, list):
            for idx, (a, b) in enumerate(zip(previous, after)):
                yield from diff(a, b, f"{path}/{idx}")
            if len(previous) != len(after):
                for idx in range(min(len(previous), len(after)), max(len(previous), len(after))):
                    arr = previous if idx < len(previous) else after
                    direction = "removed" if arr is previous else "added"
                    yield f"{path}/{idx} {direction} ({describe(arr[idx])})"
            return
    yield f"{path} {describe(previous)} -> {describe(after)}"


def main(before, after):
    from itertools import islice
    fingerprint = json.loads((after / "Data/blue-kanto-k06-services.json").read_text("utf8"))
    for rel in fingerprint["map_fields"]:
        path = Path(rel)
        for change in islice(diff(load(before / path.name), load(after / path), rel), 45):
            print("KANTO_K06_COMPILER_DELTA", change)


if __name__ == "__main__":
    main(*map(Path, sys.argv[1:]))
