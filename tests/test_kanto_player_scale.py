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
class Game_Player
  attr_accessor :character_name
  def initialize; @character_name = "player"; end
end

# Padded 4x4 sheets: simulate actual alpha, not raw frame dimensions.
class TestBitmap
  attr_reader :width, :height
  def initialize(frame_height, visible)
    @width = 32 * 4
    @height = frame_height * 4
    @frame_height = frame_height
    @visible = visible
  end
  def get_pixel(x,y)
    local_y = y % @frame_height
    visible = @visible.is_a?(Array) ? @visible[(x/32)%@visible.length] : @visible
    Struct.new(:alpha).new(x % 32 < 12 && local_y >= @frame_height - visible ? 255 : 0)
  end
end

class Sprite_Character
  attr_accessor :zoom_x, :zoom_y, :ox, :oy
  attr_reader :base_updates, :bitmap, :src_rect
  def initialize(character)
    @character = character
    @base_updates = 0
    @ox = 16
    @oy = 32
    @zoom_x = @zoom_y = 1.0
    change_sheet(48,16)
  end
  def change_sheet(frame,visible)
    @cw = 32
    @ch = frame
    @bitmap = TestBitmap.new(frame,visible)
    @src_rect = Struct.new(:x,:y,:width,:height).new(0,0,@cw,@ch)
  end
  def update
    @base_updates += 1
    # Simulate native engine retaining the previous zoom.
  end
end

module MenuHandlers
  def self.add(*_args); end
end
def _INTL(text, *_args); text; end
def check(condition, message)
  raise message unless condition
end

File.write("Kanto pilot.json", "{}")
load ARGV.fetch(0)
check(BlueKantoPilot::PILOT_OVERWORLD_SCALE, "isolated pilot marker ignored")
def BlueKantoPilot.gary_overworld_height
  overworld_visible_height(TestBitmap.new(48,32),32,48)
end
check(BlueKantoPilot.gary_overworld_height == 32, "Gary alpha reference wrong")
# Build 1606 screenshot: 80px NPC and 62px player at 2x screen zoom.
# Model the native 50 opaque pixels in a 64px padded frame. Previous
# 40px cap rendered 62.5px; correct alpha ratio yields 80px, not 103px.
capture = TestBitmap.new(64,50)
visible = BlueKantoPilot.overworld_visible_height(capture,32,64)
old_render = visible * (40.0/64) * 2
corrected = visible * BlueKantoPilot.player_overworld_zoom(visible,40) * 2
check((old_render-62).abs <= 1 && (corrected-80).abs <= 1,
  "screenshot 62->80 regression not fixed")
check(BlueKantoPilot.overworld_frame_bounds(capture,0,0,32,64) == [14,63],
  "opaque frame bounds do not exclude padding")
puts "KANTO_PLAYER_SCREENSHOT_62_TO_80_OK"
check(BlueKantoPilot.player_overworld_zoom(nil) == 1.0, "missing player evidence must use native zoom")
check(BlueKantoPilot.player_overworld_zoom(16,nil) == 1.0, "missing Gary evidence must use native zoom")

$game_player = Game_Player.new
sprite = Sprite_Character.new($game_player)
2.times { sprite.update }
check(sprite.zoom_x == 2.0 && sprite.zoom_y == 2.0, "small visible avatar did not match Gary")
$game_player.character_name = "tall"
sprite.change_sheet(80,64)
sprite.update
check(sprite.zoom_x == 0.5 && sprite.zoom_y == 0.5, "tall avatar did not match Gary")
$game_player.character_name = "equal"
sprite.change_sheet(48,32)
sprite.update
check(sprite.zoom_x == 1.0 && sprite.zoom_y == 1.0, "equal visible avatar changed")
check(sprite.ox == 16 && sprite.oy == 32, "feet pivot changed")
check(sprite.base_updates == 4, "native animation update skipped")
# Reproduce the actual integrated failure: active 46px pose in 50px sheet.
$game_player.character_name = "varying"
sprite.change_sheet(64,[46,50])
sprite.update
check((46*sprite.zoom_y-32).abs < 0.01, "46px frame used tallest frame zoom")
sprite.src_rect.x = 32
sprite.update
check((50*sprite.zoom_y-32).abs < 0.01, "walking frame was not normalized")
sprite.src_rect.x = 0
sprite.update
check((46*sprite.zoom_y-32).abs < 0.01, "active frame cache did not restore")
check(sprite.ox == 16 && sprite.oy == 32, "native feet pivot changed")

npc = Sprite_Character.new(Object.new)
npc.update
check(npc.zoom_x == 1.0 && npc.zoom_y == 1.0, "NPC zoom changed")
$game_player = Game_Player.new
sprite.update
check(sprite.zoom_x == 1.0 && sprite.zoom_y == 1.0, "previous player retained zoom")
new_sprite = Sprite_Character.new($game_player)
2.times { new_sprite.update }
check(new_sprite.zoom_x == 2.0 && new_sprite.zoom_y == 2.0, "new player scale unstable")
BlueKantoPilot.send(:remove_const, :PILOT_OVERWORLD_SCALE)
BlueKantoPilot.const_set(:PILOT_OVERWORLD_SCALE, false)
new_sprite.update
check(new_sprite.zoom_x == 1.0 && new_sprite.zoom_y == 1.0, "Decades wrongly scaled")

File.delete("Kanto pilot.json")
Dir.mkdir("Data")
File.write("Data/blue-kanto-install.json", "{}")
BlueKantoPilot.send(:remove_const, :INTEGRATED_KANTO)
BlueKantoPilot.const_set(:INTEGRATED_KANTO, true)
$PokemonGlobal = Struct.new(:blue_regions).new({"current"=>"DECADES"})
new_sprite.update
check(new_sprite.zoom_x == 1.0 && new_sprite.zoom_y == 1.0, "integrated Decades scaled")
$PokemonGlobal.blue_regions["current"] = "KANTO"
new_sprite.update
check(new_sprite.zoom_x == 2.0 && new_sprite.zoom_y == 2.0, "integrated small avatar not enlarged")
%w[JOHTO HOENN SINNOH DECADES].each do |region|
  $PokemonGlobal.blue_regions["current"] = region
  new_sprite.update
  check(new_sprite.zoom_x == 1.0 && new_sprite.zoom_y == 1.0, "#{region} inherited Kanto zoom")
  $PokemonGlobal.blue_regions["current"] = "KANTO"
  new_sprite.update
  check(new_sprite.zoom_x == 2.0 && new_sprite.zoom_y == 2.0, "Kanto reentry scale lost")
end
$game_player = Game_Player.new
new_sprite.update
check(new_sprite.zoom_x == 1.0 && new_sprite.zoom_y == 1.0, "old integrated player remained scaled")
$PokemonGlobal = nil
Sprite_Character.new($game_player).update
puts "PASS: Kanto player visible height matches Gary; NPCs, pivots and Decades unchanged"
puts "KANTO_K02B_INTEGRATED_SCALE_OK"
puts "KANTO_1605_NATIVE_PLAYER_SCALE_REGRESSION_OK"
puts "KANTO_GARY_VISIBLE_PLAYER_SCALE_FIXTURE_OK"

"""


# Model the Event Indicators alias order from the native crash: plugin
# aliasing refresh after the Kanto plugin must never call itself via super.
QUEST_PAGE_CHECK = r"""
class Game_Player; end
class Game_Event
  attr_reader :calls
  def initialize
    @calls = 0
  end
  def refresh
    @calls += 1
  end
end
class Game_Map
  attr_reader :map_id, :events, :flags_at_setup
  attr_accessor :need_refresh
  def setup(map_id)
    @map_id = map_id
    @flags_at_setup = $game_self_switches.dup
    @events = {13=>Game_Event.new,25=>Game_Event.new,26=>Game_Event.new}
    @events.each_value(&:refresh)
  end
end
class Scene_Map
  def createSpritesets
    :native
  end
end
module MenuHandlers
  def self.add(*_args); end
end
def check(condition, message)
  raise message unless condition
end
def _INTL(text, *_args); text; end
Dir.mkdir("Data")
File.write("Data/blue-kanto-install.json",'{"maps":{"39":321,"43":445}}')
load ARGV.fetch(0)
# Alias AFTER Kanto loads, matching Event Indicators' native failure.
class Game_Event
  alias indicators_original_refresh refresh
  def refresh
    indicators_original_refresh
  end
end
$game_self_switches = {}
$PokemonGlobal = Struct.new(:blue_regions).new({"current"=>"KANTO"})
map = Game_Map.new
map.setup(321)
check(map.events[13].calls == 1,"native event refresh chain changed")
check(!$game_self_switches[[321,13,"A"]],"police moved before Bill")
$PokemonGlobal.blue_regions["pilot_bill_helped"] = true
map.setup(321)
check(map.flags_at_setup[[321,13,"A"]] && map.flags_at_setup[[321,25,"A"]],"map setup missed police flags")
$PokemonGlobal.blue_regions["pilot_cerulean_dig_awarded"] = true
$map_factory = Struct.new(:maps).new([map])
check(Scene_Map.new.createSpritesets == :native,"native spriteset load skipped")
check([26,37,38].all? { |id| $game_self_switches[[321,id,"A"]] },"loaded map missed Rocket flags")
check(map.events[26].calls == 2 && map.need_refresh,"loaded map did not refresh")
Scene_Map.new.createSpritesets
check(map.events[26].calls == 2,"unchanged flags refreshed unnecessarily")
%w[DECADES JOHTO HOENN SINNOH].each do |region|
  $PokemonGlobal.blue_regions["current"] = region
  $game_self_switches.clear
  map.setup(321)
  check($game_self_switches.empty?,"quest switches leaked into #{region}")
end
$PokemonGlobal.blue_regions["current"] = "KANTO"
map.setup(322)
check($game_self_switches.empty?,"quest switches leaked into unrelated map")
File.write("Data/blue-kanto-install.json",'{"maps":{"39":321}}')
map.setup(321)
check($game_self_switches.empty?,"old 145-map install was modified")
puts "KANTO_K02C_EVENT_INDICATORS_ALIAS_SAFE_OK"
"""

class KantoOverworldPlayerScaleTests(unittest.TestCase):
    def test_cerulean_quest_map_hooks_are_safe_with_event_indicators_alias(self):
        ruby = shutil.which("ruby")
        if ruby is None:
            self.skipTest("Ruby interpreter unavailable")
        with tempfile.TemporaryDirectory(prefix="kanto-quest-pages-") as tmp:
            result = subprocess.run([ruby, "-e", QUEST_PAGE_CHECK, str(KANTO_RUBY)],
                                    cwd=tmp, capture_output=True, text=True,
                                    timeout=20, check=False)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("KANTO_K02C_EVENT_INDICATORS_ALIAS_SAFE_OK", result.stdout)
        print(result.stdout.strip())

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
        self.assertIn("PASS: Kanto player visible height matches Gary", result.stdout)
        self.assertIn("KANTO_K02B_INTEGRATED_SCALE_OK", result.stdout)
        self.assertIn("KANTO_1605_NATIVE_PLAYER_SCALE_REGRESSION_OK", result.stdout)
        self.assertIn("KANTO_GARY_VISIBLE_PLAYER_SCALE_FIXTURE_OK", result.stdout)
        self.assertIn("KANTO_PLAYER_SCREENSHOT_62_TO_80_OK", result.stdout)
        print(result.stdout.strip())


if __name__ == "__main__":
    unittest.main()
