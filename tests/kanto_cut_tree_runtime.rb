# Standalone regression for the REAL KantoPilot.rb CutTree frame guard.
# No FRLG/ROM, Game.exe, network, or saves from the user's installation.
require "tmpdir"

pilot_source = File.expand_path(ARGV.fetch(0))

class Game_Player; end

module MenuHandlers
  def self.add(*_args); end
end

def _INTL(text, *_args); text; end

class Game_Event
  attr_accessor :direction, :pattern
  attr_reader :name, :updates

  def initialize(name, direction = 2, pattern = 1)
    @name = name
    graphic = Struct.new(:direction, :pattern).new(direction, pattern)
    @page = Struct.new(:graphic).new(graphic)
    @direction = direction
    @pattern = pattern
    @direction_fix = false
    @walk_anime = true
    @step_anime = true
    @erased = false
    @updates = 0
  end

  # The native RPG Maker event interaction can turn a non-NPC charset.
  def lock
    @direction = 4 unless @direction_fix
    @pattern = 3
  end

  def update
    @updates += 1
  end

  def refresh
    @direction = 6 unless @direction_fix
    @pattern = 2
  end

  def erase
    @erased = true
  end
end

$native_smashes = 0
$animation_frame = nil
def pbSmashEvent(event)
  $native_smashes += 1
  # This part emulates native Essentials' Cut event move route/erase.
  event.direction = 4
  event.pattern = 3
  event.update
  $animation_frame = [
    event.direction, event.pattern,
    event.instance_variable_get(:@direction_fix),
    event.instance_variable_get(:@blue_kanto_cut_animating)
  ]
  event.erase
  true
end

def check(value, description)
  raise "CutTree runtime failure: #{description}" unless value
end

Dir.mktmpdir("kanto-cut-tree-") do |dir|
  Dir.chdir(dir) do
    File.write("Kanto pilot.json", "{}")
    load pilot_source

    tree = Game_Event.new("CutTree")
    tree.direction = 6
    tree.pattern = 3
    tree.update
    check([tree.direction, tree.pattern] == [2, 1],
          "an old changed/stump frame was not reset on a Kanto map")
    check(tree.instance_variable_get(:@direction_fix) == true &&
          tree.instance_variable_get(:@walk_anime) == false &&
          tree.instance_variable_get(:@step_anime) == false,
          "a standing tree was not frozen")

    # Reproduce the screenshot: press action, show the badge warning,
    # leave the Cut conditional false, then render another frame.
    tree.lock
    tree.update
    check([tree.direction, tree.pattern] == [2, 1],
          "failed Cut interaction displayed a stump instead of the tree")
    check($native_smashes == 0, "failed Cut accidentally began Cut animation")
    tree.direction = 8
    tree.pattern = 2
    tree.refresh
    check([tree.direction, tree.pattern] == [2, 1],
          "refresh did not recover the original graphics")

    # Other NPCs must still look toward the player; no global sprite freeze.
    npc = Game_Event.new("NPC_Youngster")
    npc.lock
    check([npc.direction, npc.pattern] == [4, 3],
          "NPC interaction/turning was altered by the tree guard")

    # Only an authorized successful cut is allowed to rotate the tree
    # through its normal animation frames, then erase it.
    check(pbSmashEvent(tree), "native smash callback did not run")
    check($native_smashes == 1, "native smash was duplicated")
    check($animation_frame == [4, 3, false, true],
          "real Cut animation was frozen or did not release direction fix")
    check(tree.instance_variable_get(:@erased), "successful Cut did not erase tree")
    check(!tree.instance_variable_get(:@blue_kanto_cut_animating),
          "animation guard did not clean up after Cut")

    # The same patch must remain completely inert in the main Decades game.
    File.delete("Kanto pilot.json")
    decades = Game_Event.new("CutTree")
    decades.lock
    check([decades.direction, decades.pattern] == [4, 3],
          "main Decades CutTree was modified by isolated Kanto")
  end
end
puts "PASS: Kanto CutTree remains on original frame after denied Cut; native success animates and erases; NPCs/Decades unchanged"
