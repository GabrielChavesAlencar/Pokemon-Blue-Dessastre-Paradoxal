# Pure Ruby regression for the original Essentials + Decades Auto Multi Save
# title menu. No graphics/ROM/saves/Windows process is required.
require "tmpdir"
require "fileutils"

def _INTL(text, *); text; end
def pbMessage(*); $notices += 1; end
def pbConfirmMessage(*); true; end
def require_check(condition, label)
  raise(label) unless condition
end

class PokemonLoad_Scene
  attr_accessor :queue
  attr_reader :displayed, :last_continue
  def pbStartScene(commands, has_continue, *args)
    @displayed = commands
    @with_save = has_continue
  end
  # Matches Decades' Auto Multi Save: TWO arguments and negative slot arrows.
  def pbChoose(commands, continue_idx)
    @last_continue = continue_idx
    @queue.shift
  end
end

$notices = 0
require ARGV.fetch(0)
BlueKantoTitle.install

original = [" <- My Save -> ", "New Game", "Options", "Quit Game"]
scene = PokemonLoad_Scene.new
scene.queue = [1]
scene.pbStartScene(original, true, nil, nil, 0)
require_check(scene.displayed == [" <- My Save -> ", "New Game", "Testar Kanto", "Testar Johto", "Testar Hoenn", "Testar Sinnoh", "Options", "Quit Game"],
              "Kanto/Johto test options have wrong positions after Continue")
require_check(scene.pbChoose(original, 0) == 1, "New Game index changed")
require_check(scene.last_continue == 0, "Continue slot arrows were remapped")
require_check(original == [" <- My Save -> ", "New Game", "Options", "Quit Game"],
              "Original load command array was mutated")

scene.queue = [-3]
require_check(scene.pbChoose(original, 0) == -3, "Previous save-slot arrow changed")
scene.queue = [-2]
require_check(scene.pbChoose(original, 0) == -2, "Next save-slot arrow changed")

# Mystery Gift can appear before New Game in Decades' loader. Both the third
# slot and the ORIGINAL handler index must be preserved.
gift = [" <- Save 2 -> ", "Mystery Gift", "New Game", "Options", "Quit Game"]
scene2 = PokemonLoad_Scene.new
scene2.queue = [1, 6]
scene2.pbStartScene(gift, true, nil, nil, 0)
require_check(scene2.displayed == [" <- Save 2 -> ", "New Game", "Testar Kanto", "Testar Johto",
                                   "Testar Hoenn", "Testar Sinnoh", "Mystery Gift", "Options", "Quit Game"],
              "Mystery Gift broke title menu order")
require_check(scene2.pbChoose(gift, 0) == 2, "New Game handler no longer maps to original")
require_check(scene2.pbChoose(gift, 0) == 1, "Mystery Gift handler no longer maps to original")

# In a first-time launch, without Continue, New Game must remain first.
fresh = ["New Game", "Options", "Quit Game"]
scene3 = PokemonLoad_Scene.new
scene3.queue = [0]
scene3.pbStartScene(fresh, false, nil, nil, 0)
require_check(scene3.displayed == ["New Game", "Testar Kanto", "Testar Johto", "Testar Hoenn", "Testar Sinnoh", "Options", "Quit Game"],
              "No-save title order is invalid")
require_check(scene3.pbChoose(fresh, -1) == 0, "No-save New Game changed")

# Successful test choice dispatches to the original Quit command for native
# cleanup, rather than overwriting Decades' save profile or altering Game.start_new.
BlueKantoTitle.define_singleton_method(:launch) { true }
scene.queue = [2]
require_check(scene.pbChoose(original, 0) == 3, "Pilot success did not cleanly quit main game")
BlueKantoTitle.define_singleton_method(:launch) { false }
scene.queue = [2, 1]
require_check(scene.pbChoose(original, 0) == 1, "Pilot failure must return to normal title")

# Johto uses the fourth option and must never hijack Kanto or save-slot indexes.
BlueKantoTitle.define_singleton_method(:launch_johto) { true }
scene.queue = [3]
require_check(scene.pbChoose(original, 0) == 3, "Johto pilot success did not cleanly quit main game")
BlueKantoTitle.define_singleton_method(:launch_johto) { false }
scene.queue = [3, 1]
require_check(scene.pbChoose(original, 0) == 1, "Johto unavailable must return to normal title")

# Hoenn occupies the slot between Johto and Sinnoh.
BlueKantoTitle.define_singleton_method(:launch_hoenn) { true }
scene.queue = [4]
require_check(scene.pbChoose(original, 0) == 3, "Hoenn success did not cleanly quit main game")
BlueKantoTitle.define_singleton_method(:launch_hoenn) { false }
scene.queue = [4, 1]
require_check(scene.pbChoose(original, 0) == 1, "Unavailable Hoenn must return to title")

# Sinnoh is the sixth option and must keep the original Quit/New Game indices.
BlueKantoTitle.define_singleton_method(:launch_sinnoh) { true }
scene.queue = [5]
require_check(scene.pbChoose(original, 0) == 3, "Sinnoh pilot success did not cleanly quit main game")
BlueKantoTitle.define_singleton_method(:launch_sinnoh) { false }
scene.queue = [5, 1]
require_check(scene.pbChoose(original, 0) == 1, "Unavailable Sinnoh must return to title")

# Isolated pilot cannot spawn itself recursively from its own Game.exe.
Dir.mktmpdir("blue-title-") do |folder|
  Dir.chdir(folder) do
    File.write("Kanto pilot.json", "{}")
    isolated = PokemonLoad_Scene.new
    isolated.queue = [1]
    isolated.pbStartScene(original, true, nil, nil, 0)
    require_check(isolated.displayed == original, "Test option appeared inside the pilot")
    require_check(isolated.pbChoose(original, 0) == 1, "Pilot New Game no longer works")
    require_check(BlueKantoTitle.launcher.nil?, "Pilot may recursively launch another pilot")
    require_check(BlueKantoTitle.johto_launcher.nil?, "Kanto pilot may launch Johto recursively")
    require_check(BlueKantoTitle.sinnoh_launcher.nil?, "Kanto pilot may launch Sinnoh recursively")
  end
end

# The real launcher is resolved relative to game/Game.exe and must reference
# the project-owned BAT and Python pilot, never an arbitrary path.
Dir.mktmpdir("blue-title-root-") do |root|
  game = File.join(root, "game")
  FileUtils.mkdir_p(File.join(root, "scripts/regions"))
  FileUtils.mkdir_p(game)
  File.write(File.join(game, "Game.exe"), "native game")
  File.write(File.join(root, "KANTO_JOGAR_EXPERIMENTAL.bat"), "@echo off")
  File.write(File.join(root, "scripts/regions/pilot.py"), "# pilot")
  Dir.chdir(game) do
    files = BlueKantoTitle.launcher
    require_check(files == [File.join(root, "KANTO_JOGAR_EXPERIMENTAL.bat"), root],
                  "Pilot launcher escaped the project root")
    require_check(BlueKantoTitle.johto_launcher.nil?, "Johto must not reuse Kanto launcher")
    require_check(BlueKantoTitle.sinnoh_launcher.nil?, "Sinnoh must not reuse Kanto launcher")
    File.write(File.join(root, "JOHTO_JOGAR_EXPERIMENTAL.bat"), "@echo off")
    File.write(File.join(root, "scripts/regions/pilot_johto.py"), "# isolated Johto pilot")
    require_check(BlueKantoTitle.johto_launcher == [File.join(root, "JOHTO_JOGAR_EXPERIMENTAL.bat"), root],
                  "Johto launcher must use only its own project-owned pilot")
    File.write(File.join(root, "SINNOH_JOGAR_EXPERIMENTAL.bat"), "@echo off")
    require_check(BlueKantoTitle.sinnoh_launcher.nil?, "Sinnoh needs its own Python pilot, not only a BAT")
    File.write(File.join(root, "scripts/regions/pilot_sinnoh.py"), "# isolated Sinnoh pilot")
    require_check(BlueKantoTitle.sinnoh_launcher == [File.join(root, "SINNOH_JOGAR_EXPERIMENTAL.bat"), root],
                  "Sinnoh launcher must use only its project-owned pilot")
    File.write("Sinnoh pilot.json", "{}")
    require_check(BlueKantoTitle.sinnoh_launcher.nil?, "Sinnoh pilot may launch itself recursively")
    File.delete("Sinnoh pilot.json")
    hoenn = File.join(root, ".blue-work", "hoenn-pilot")
    FileUtils.mkdir_p(File.join(hoenn, "Data"))
    File.write(File.join(hoenn, "Game.exe"), "pilot")
    File.write(File.join(hoenn, "Hoenn pilot.json"), "{}")
    File.write(File.join(hoenn, "Data/blue-hoenn-pilot.txt"), "BLUE_HOENN_PILOT_V1")
    previous_profile = ENV.delete("USERPROFILE")
    begin
      require_check(BlueKantoTitle.hoenn_launcher.nil?, "Hoenn needs compiled game data")
      File.write(File.join(hoenn, "Data/blue-hoenn-compiled.txt"), "compiled")
      require_check(BlueKantoTitle.hoenn_launcher == [File.join(hoenn, "Game.exe"), hoenn],
                    "Hoenn must use its own compiled pilot")
      Dir.chdir(hoenn) do
        require_check(BlueKantoTitle.hoenn_launcher.nil?, "Hoenn may launch itself recursively")
        require_check(BlueKantoTitle.command_order(original, true) == [0, 1, 2, 3],
                      "Regional options appeared inside Hoenn")
      end
    ensure
      ENV["USERPROFILE"] = previous_profile
    end
  end
end
puts "Third, fourth and fifth title options, save slots, Mystery Gift, pilot isolation and launcher paths OK"
