"""Kanto pilot and integrated protagonist: adaptive smaller sprite without regional leakage."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KANTO_RUBY = ROOT / "scripts/regions/KantoPilot.rb"
PILOT_BUILDER = ROOT / "scripts/regions/pilot.py"

RUBY_CHECK = r"""
class Game_Player; end

class Sprite_Character
  attr_accessor :zoom_x, :zoom_y, :ox, :oy
  attr_reader :base_updates

  def initialize(character)
    @character = character
    @base_updates = 0
    @ox = 16
    @oy = 32
  end

  def update
    @base_updates += 1
    self.zoom_x = 1.0
    self.zoom_y = 1.0
  end
end

module MenuHandlers
  def self.add(*_args); end
end

def _INTL(text, *_args); text; end

def check(condition, message)
  raise message unless condition
end

# This file exists only in the compiled, isolated Kanto pilot.
File.write("Kanto pilot.json", "{}")
load ARGV.fetch(0)
check(BlueKantoPilot::PILOT_OVERWORLD_SCALE, "isolated pilot marker ignored")
check(BlueKantoPilot::PLAYER_OVERWORLD_ZOOM == 0.60, "unexpected zoom value")
check(BlueKantoPilot::PLAYER_OVERWORLD_MAX_HEIGHT == 30, "unexpected max rendered height")

$game_player = Game_Player.new
sprite = Sprite_Character.new($game_player)
sprite.instance_variable_set(:@ch, 48)
sprite.update
check(sprite.zoom_x == 0.60 && sprite.zoom_y == 0.60, "player not smaller")
check(sprite.zoom_x * 48 <= 30, "player taller than FRLG reference")
sprite.instance_variable_set(:@ch, 80)
sprite.update
check(sprite.zoom_x == 0.375 && sprite.zoom_y == 0.375, "tall avatar not limited to 30 pixels")
sprite.instance_variable_set(:@ch, 20)
sprite.update
check(sprite.zoom_x == 0.60 && sprite.zoom_y == 0.60, "small avatar was enlarged")
sprite.instance_variable_set(:@ch, 48)
sprite.update
check(sprite.ox == 16 && sprite.oy == 32, "feet pivot changed")
check(sprite.base_updates == 4, "native character animation update skipped")

npc = Sprite_Character.new(Object.new)
npc.update
check(npc.zoom_x == 1.0 && npc.zoom_y == 1.0, "NPC zoom changed")
check(npc.ox == 16 && npc.oy == 32, "NPC pivot changed")

# Save loading can replace the Game_Player object during the same session.
$game_player = Game_Player.new
sprite.update
check(sprite.zoom_x == 1.0 && sprite.zoom_y == 1.0, "previous player still scaled")
new_sprite = Sprite_Character.new($game_player)
2.times { new_sprite.update }
check(new_sprite.zoom_x == 0.60 && new_sprite.zoom_y == 0.60, "new player scale unstable")
check(new_sprite.base_updates == 2, "native updates lost")

# The shared Decades game never has the pilot marker at boot.
BlueKantoPilot.send(:remove_const, :PILOT_OVERWORLD_SCALE)
BlueKantoPilot.const_set(:PILOT_OVERWORLD_SCALE, false)
new_sprite.update
check(new_sprite.zoom_x == 1.0 && new_sprite.zoom_y == 1.0, "Decades wrongly scaled")

# Integrated install: the pilot marker is absent. Switch the current
# region on the same sprite to prove the shared runtime does not leak.
File.delete("Kanto pilot.json")
Dir.mkdir("Data")
File.write("Data/blue-kanto-install.json", "{}")
BlueKantoPilot.send(:remove_const, :INTEGRATED_KANTO)
BlueKantoPilot.const_set(:INTEGRATED_KANTO, true)
$PokemonGlobal = Struct.new(:blue_regions).new({"current"=>"DECADES"})
new_sprite.instance_variable_set(:@ch, 48)
new_sprite.update
check(new_sprite.zoom_x == 1.0 && new_sprite.zoom_y == 1.0, "integrated Decades scaled")
$PokemonGlobal.blue_regions["current"] = "KANTO"
new_sprite.update
check(new_sprite.zoom_x == 0.60 && new_sprite.zoom_y == 0.60, "integrated Kanto not scaled")
new_sprite.instance_variable_set(:@ch, 80)
new_sprite.update
check(new_sprite.zoom_x == 0.375 && new_sprite.zoom_y == 0.375, "integrated tall avatar not capped")
npc.update
check(npc.zoom_x == 1.0 && npc.zoom_y == 1.0, "integrated NPC scaled")
%w[JOHTO HOENN SINNOH DECADES].each do |region|
  $PokemonGlobal.blue_regions["current"] = region
  new_sprite.update
  check(new_sprite.zoom_x == 1.0 && new_sprite.zoom_y == 1.0, "#{region} inherited Kanto zoom")
  $PokemonGlobal.blue_regions["current"] = "KANTO"
  new_sprite.update
  check(new_sprite.zoom_x == 0.375 && new_sprite.zoom_y == 0.375, "Kanto reentry scale lost")
end
$game_player = Game_Player.new
new_sprite.update
check(new_sprite.zoom_x == 1.0 && new_sprite.zoom_y == 1.0, "old integrated player remained scaled")
$PokemonGlobal = nil
Sprite_Character.new($game_player).update
puts "PASS: Kanto player at max 60% and 30px; NPCs, pivots, and Decades unchanged"
puts "KANTO_K02B_INTEGRATED_SCALE_OK"

"""


class KantoOverworldPlayerScaleTests(unittest.TestCase):
    def test_builder_tracks_runtime_as_a_rebuild_input(self):
        builder = PILOT_BUILDER.read_text(encoding="utf-8")
        self.assertIn('"scripts/regions/KantoPilot.rb",', builder)
        self.assertIn("pilot_is_current", builder)

    def test_kanto_zoom_is_scoped_to_player_and_pilot(self):
        source = KANTO_RUBY.read_text(encoding="utf-8")
        self.assertIn('PILOT_OVERWORLD_SCALE = File.file?("Kanto pilot.json")', source)
        self.assertIn("@character.equal?($game_player)", source)
        self.assertIn("Sprite_Character.prepend(BlueKantoPilot::PlayerOverworldScale)", source)

    def test_real_ruby_player_zoom_with_native_sprite_stub(self):
        ruby = shutil.which("ruby")
        if ruby is None:
            self.skipTest("Ruby interpreter unavailable; native Windows CI validates runtime")
        with tempfile.TemporaryDirectory(prefix="kanto-player-scale-") as tmp:
            result = subprocess.run(
                [ruby, "-e", RUBY_CHECK, str(KANTO_RUBY)],
                cwd=tmp, capture_output=True, text=True, timeout=20, check=False,
            )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS: Kanto player at max 60% and 30px", result.stdout)
        self.assertIn("KANTO_K02B_INTEGRATED_SCALE_OK", result.stdout)


if __name__ == "__main__":
    unittest.main()
