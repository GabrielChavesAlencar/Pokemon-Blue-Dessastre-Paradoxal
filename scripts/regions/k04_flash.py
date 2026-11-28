"""Compile only the anchored Route 2 Flash reward; never run donor Ruby."""
from copy import deepcopy
import re

from audit import text
from pilot import command, new_event

SOURCE_ID = 21
EVENT_ID = 2
XY = (3, 6)
DEX = re.compile(r"\$player\.pokedex\.owned_count\(\s*0\s*\)\s*(>=|>|<|<=)\s*(\d+)")
REWARD = re.compile(r"\bpbReceiveItem\s*\(\s*:HM05\s*(?:,\s*1\s*)?\)")


def verify_aide(donor):
    if tuple(donor.attrs[k] for k in ("@x", "@y")) != XY:
        raise ValueError("K04 Flash aide moved in source")
    pages = donor.attrs["@pages"]
    page = pages[0].attrs
    if page["@trigger"] != 0 or not page["@graphic"].attrs["@character_name"]:
        raise ValueError("K04 Flash aide lacks an original action/graphic")
    stack = {}
    witness = []
    for op in page["@list"]:
        row = op.attrs
        code, indent, row_args = (row[k] for k in ("@code", "@indent", "@parameters"))
        if code == 111:
            term = DEX.fullmatch(text(row_args[-1]).strip()) if row_args and row_args[0] == 12 else None
            stack[indent] = (term, True)
        elif code == 411 and indent in stack:
            stack[indent] = (stack[indent][0], False)
        elif code == 412:
            stack.pop(indent, None)
        elif code in (355,655) and row_args and REWARD.search(text(row_args[0])):
            for depth, (test, true_side) in stack.items():
                if depth >= indent or not test:
                    continue
                comparison, threshold = test[1], int(test[2])
                accepts_ten = ((comparison, threshold, true_side) in {
                    (">=",10,True), (">",9,True), ("<",10,False), ("<=",9,False)})
                witness.append(accepts_ten)
    if witness != [True]:
        raise ValueError("K04 original HM05 branch must require exactly 10 Kanto dex species")


def install_flash_aide(baseline, donor, graphic):
    verify_aide(donor)
    native = deepcopy(baseline)
    events = native.attrs["@events"]
    old = events.get(EVENT_ID)
    if old and (tuple(old.attrs[k] for k in ("@x", "@y")) != XY or any(
            op.attrs["@code"] not in (0,101,401,355) or
            (op.attrs["@code"] == 355 and not text(op.attrs["@parameters"][0]).startswith("BlueKantoPilot.npc_dialogue(21, 2,"))
            for page in old.attrs["@pages"] for op in page.attrs["@list"])):
        raise ValueError("K04 will not replace an active Route 2 reward or transfer")
    events[EVENT_ID] = new_event(donor, [command(355,b"BlueKantoPilot.route2_flash")], 0, graphic)
    return native
