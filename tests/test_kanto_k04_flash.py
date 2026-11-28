"""Only the observed aide, its original threshold and reward are accepted."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts/regions"))
from k04_flash import install_flash_aide, verify_aide
from pilot import command
from server.ruby_marshal import RubyObject


def aide(test=b"$player.pokedex.owned_count(0)>=10", else_side=False):
    ops = [command(111,12,test)]
    if else_side:
        ops.append(command(411))
    ops.extend((command(355,b"pbReceiveItem(:HM05)",indent=1),command(412),command(0)))
    return RubyObject("RPG::Event", {"@x":3,"@y":6,"@pages":[
        RubyObject("RPG::Event::Page", {"@trigger":0,
            "@condition":RubyObject("RPG::Event::Page::Condition",{}),
            "@graphic":RubyObject("RPG::Event::Page::Graphic",{"@character_name":b"NPC"}),
            "@list":ops})]})


class FlashAideTests(unittest.TestCase):
    def test_guard_must_award_at_ten_and_not_below(self):
        verify_aide(aide())
        verify_aide(aide(b"$player.pokedex.owned_count(0)<10",True))
        for invalid in (aide(else_side=True),aide(b"$player.pokedex.owned_count(0)>=9"),
                        aide(b"$player.pokedex.owned_count(1)>=10")):
            with self.assertRaisesRegex(ValueError,"10 Kanto dex species"):
                verify_aide(invalid)

    def test_install_preserves_existing_door_and_authors_only_callback(self):
        door = RubyObject("RPG::Event", {"commands":[201,0]})
        base = RubyObject("RPG::Map", {"@events":{1:door}})
        native = install_flash_aide(base,aide(),b"BlueNPC")
        self.assertEqual(base.attrs["@events"],{1:door})
        self.assertEqual(native.attrs["@events"][1],door)
        page = native.attrs["@events"][2].attrs["@pages"][0].attrs
        self.assertEqual(page["@list"][0].attrs["@parameters"],[b"BlueKantoPilot.route2_flash"])
        self.assertEqual([op.attrs["@code"] for op in page["@list"]],[355,0])
