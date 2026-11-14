# Runtime regression against the REAL KantoPilot.rb visual CutTree guard.
# No FRLG assets, Game.exe or personal saves. Reproduces save-load refresh.
require "tmpdir"

pilot_source = File.expand_path(ARGV.fetch(0))
class Game_Player; end
module MenuHandlers
  def self.add(*_args); end
end
def _INTL(text, *_args); text; end

class Game_Event
  attr_accessor :direction, :pattern
  attr_reader :name, :refreshes

  def initialize(name, direction = 2, pattern = 1)
    @name = name
    graphic = Struct.new(:direction, :pattern).new(direction, pattern)
    @page = Struct.new(:graphic).new(graphic)
    @direction = direction
    @pattern = pattern
    @erased = false
    @refreshes = 0
  end

  # Native map load refresh is left untouched. Earlier hook prepended
  # Game_Event#refresh with super and caused SystemStackError on a real save.
  def refresh
    @refreshes += 1
    @direction = 4 if @refreshes.odd?
    @pattern = 3
  end

  def lock
    @direction = 4
    @pattern = 2
  end

  def erase; @erased = true; end
end

class FrameRect
  attr_reader :rect
  def set(*params); @rect = params; end
end

class Sprite_Character
  attr_accessor :zoom_x, :zoom_y
  attr_reader :src_rect, :base_updates
  def initialize(character)
    @character = character
    @cw = 32
    @ch = 32
    @tile_id = 0
    @src_rect = FrameRect.new
    @zoom_x = @zoom_y = 1.0
    @base_updates = 0
  end

  def update
    @base_updates += 1
    @src_rect.set(@character.pattern * @cw,
                  ((@character.direction - 2) / 2) * @ch, @cw, @ch)
  end
end

$native_smashes = 0
$animation_frame = nil
def pbSmashEvent(event)
  $native_smashes += 1
  event.direction = 4
  event.pattern = 3
  $animation_frame = $tree_sprite.tap(&:update).src_rect.rect
  event.erase
  true
end

def check(value, name)
  raise "CutTree regression: #{name}" unless value
end

Dir.mktmpdir("kanto-cut-tree-") do |dir|
  Dir.chdir(dir) do
    File.write("Kanto pilot.json", "{}")
    load pilot_source

    check(!Game_Event.ancestors.any? { |m| m.name.to_s.include?("CutTreeFrameGuard") },
          "Game_Event refresh hook still installed (can recurse on map loading)")

    tree = Game_Event.new("CutTree", 2, 1)
    $tree_sprite = Sprite_Character.new(tree)
    # Existing save has event direction/pattern changed to a stump.
    200.times { tree.refresh }
    check(tree.refreshes == 200, "native refresh chain was altered")
    tree.direction = 6
    tree.pattern = 3
    $tree_sprite.update
    check($tree_sprite.src_rect.rect == [32, 0, 32, 32],
          "stump frame not visually normalized after save load")
    check([tree.direction, tree.pattern] == [6, 3],
          "visual fix must not mutate native Game_Event state")

    # A denied Cut interaction must not display a changed tree sprite.
    tree.lock
    $tree_sprite.update
    check($tree_sprite.src_rect.rect == [32, 0, 32, 32],
          "tree sprite changed during a rejected Cut interaction")
    check($native_smashes == 0, "denied Cut invoked removal animation")

    npc = Game_Event.new("NPC_Youngster")
    npc.lock
    npc_sprite = Sprite_Character.new(npc)
    npc_sprite.update
    check(npc_sprite.src_rect.rect == [64, 32, 32, 32],
          "regular NPC rendering was incorrectly frozen")

    # The successful native Cut can temporarily use all animation frames.
    check(pbSmashEvent(tree), "native smash was not invoked")
    check($native_smashes == 1, "successful Cut animation ran twice")
    check($animation_frame == [96, 32, 32, 32],
          "successful Cut animation was still frozen")
    check(tree.instance_variable_get(:@erased), "successful Cut did not remove tree")
    check(!tree.instance_variable_get(:@blue_kanto_cut_animating),
          "Cut animation flag did not reset")

    # Main Decades never has the isolated pilot marker.
    File.delete("Kanto pilot.json")
    original = Game_Event.new("CutTree")
    original.lock
    original_sprite = Sprite_Character.new(original)
    original_sprite.update
    check(original_sprite.src_rect.rect == [64, 32, 32, 32],
          "main Decades was changed by Kanto rendering")
    player = Game_Player.new
    player_sprite = Sprite_Character.new(player)
    def player.pattern; 0; end
    def player.direction; 2; end
    $game_player = player
    player_sprite.update
    check(player_sprite.zoom_x == 0.75 && player_sprite.zoom_y == 0.75,
          "previous protagonist scale fix was lost")
  end
end

puts "PASS: Kanto CutTree save load no Game_Event recursion; denied Cut visual unchanged; successful animation and Decades isolated"
