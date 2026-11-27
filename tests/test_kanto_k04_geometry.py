"""K04 geometry copies no donor callbacks or out-of-scope transfers."""
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/regions"))
from audit import load
from build_k04_geometry import inject_warps
from k04_corridor import WARPS
from pilot import EVENT_CLASSES, command, write_map
from server.ruby_marshal import RubyObject


class K04GeometryTests(unittest.TestCase):
    def test_event_commands_round_trip_without_source_logic(self):
        def event():
            return RubyObject("RPG::Event", {"@pages": [RubyObject("RPG::Event::Page", {
                "@condition": RubyObject("RPG::Event::Page::Condition", {"@switch1_valid": True}),
                "@graphic": RubyObject("RPG::Event::Page::Graphic", {"@character_name": b"foreign"}),
                "@list": [command(355, b"foreign_script")],
            })]})
        donor = RubyObject("RPG::Map", {"@events": {i:event() for i in (7, 9, 12, 13, 22)}})
        native = RubyObject("RPG::Map", {"@events": {}})
        ids = {88:606, 90:607}
        inject_warps(donor, native, 87, ids)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "Map605.rxdata"
            write_map(path, native, EVENT_CLASSES)
            events = load(path).attrs["@events"]
        self.assertEqual(set(events), {12, 13, 22})
        for i, compiled in events.items():
            dest, x, y, facing = WARPS[87, i]
            page, = compiled.attrs["@pages"]
            self.assertEqual(page.attrs["@trigger"], 1)
            self.assertFalse(page.attrs["@condition"].attrs["@switch1_valid"])
            self.assertEqual(page.attrs["@graphic"].attrs["@character_name"], b"")
            self.assertEqual([op.attrs["@code"] for op in page.attrs["@list"]], [201, 0])
            self.assertEqual(page.attrs["@list"][0].attrs["@parameters"], [0, ids[dest], x, y, facing, 0])


if __name__ == "__main__":
    unittest.main()
