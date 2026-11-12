# Standalone regression: no RMXP, graphics, saves or external game data.
require "tmpdir"
require "fileutils"

class PokemonGlobalMetadata
  attr_accessor :blue_regions, :blue_story_mode, :blue_traditional_starters,
                :blue_campaign_started, :blue_campaign_departure
end

class FakeSystem
  attr_accessor :start_map_id, :start_x, :start_y
  def initialize
    @start_map_id, @start_x, @start_y = 4, 7, 8
  end
end

module Game
  class << self
    attr_reader :seen
    def start_new
      SaveData.load_new_game_values
      @seen = [$data_system.start_map_id, $data_system.start_x, $data_system.start_y]
    end
    def load(old_data)
      $PokemonGlobal.blue_regions = old_data
    end
  end
end

module SaveData
  def self.load_new_game_values
    $PokemonGlobal = PokemonGlobalMetadata.new
  end
end

module BlueRegions
  def self.circuit
    %w[DECADES KANTO JOHTO HOENN SINNOH UNOVA KALOS ALOLA GALAR PALDEA]
  end
  def self.info(region)
    {"name" => region.capitalize}
  end
  def self.new_state(region)
    {"initial" => region, "current" => region, "leagues" => []}
  end
end

module BlueStory
  def self.choose_mode(mode)
    $PokemonGlobal.blue_story_mode = mode
  end
end
module BlueCampaign
  def self.begin_journey(prompt=true)
    $PokemonGlobal.blue_campaign_started = true
    $PokemonGlobal.blue_campaign_departure = true
  end
end

def pbRgssExists?(path)
  File.file?(path)
end

$choices = []
$messages = 0
def pbMessage(message, choices=nil, default=nil)
  $messages += 1
  choices ? $choices.shift : nil
end

def pbConfirmMessage(message)
  true
end

def _INTL(text, *args)
  args.each_with_index { |value, index| text = text.gsub("{#{index+1}}", value.to_s) }
  text
end

def check(condition, message)
  raise message unless condition
end

require ARGV.fetch(0)
BlueRegionStart.install
Dir.mktmpdir("blue-region-start-") do |folder|
  Dir.chdir(folder) do
    Dir.mkdir("Data")
    $data_system = FakeSystem.new

    # Without a completed install, new game stays in native Decades.
    Game.start_new
    check(Game.seen == [4,7,8], "Decades location changed")
    check($PokemonGlobal.blue_regions["initial"] == "DECADES", "Decades default missing")
    check($messages == 0, "Empty Kanto must not prompt or hang")

    # The marker enables Kanto without changing the global starting map.
    File.binwrite("Data/Map321.rxdata", "pilot")
    File.write("Data/blue-kanto-start.txt", "BLUE_KANTO_START_V1,KANTO,321,28,14\n")
    $choices = [1]
    Game.start_new
    check(Game.seen == [321,28,14], "Kanto was not selected before map setup")
    check([$data_system.start_map_id,$data_system.start_x,$data_system.start_y] == [4,7,8], "System map not restored")
    check($PokemonGlobal.blue_regions["initial"] == "KANTO", "Kanto was not persisted")
    check($PokemonGlobal.blue_story_mode == :story, "Kanto did not use Story Mode")
    check($PokemonGlobal.blue_traditional_starters == true, "Traditional starters not enabled")
    check($PokemonGlobal.blue_campaign_departure == false, "Kanto starter bag would be cleared")

    # Locked regions are displayed, but can't create an invalid spawn.
    $choices = [2,0]
    Game.start_new
    check(Game.seen == [4,7,8], "Locked Johto was incorrectly selected")
    check($PokemonGlobal.blue_regions["initial"] == "DECADES", "Decades fallback missing")

    # A Johto map alone is not enough; only a verified local install/pilot
    # will write the dedicated Johto start and installation markers.
    File.binwrite("Data/Map712.rxdata", "synthetic Johto player room")
    File.write("Data/blue-johto-start.txt", "BLUE_JOHTO_START_V1,JOHTO,712,9,6\n")
    check(!BlueRegionStart.playable?("JOHTO"), "Uninstalled Johto was enabled by a lone marker")
    check(BlueRegionStart.johto_spawn.nil?, "Johto start without install proof was accepted")

    File.write("Data/blue-johto-install.json", "{}")
    check(BlueRegionStart.playable?("JOHTO"), "Valid Johto markers should enable region")
    $choices = [2]
    Game.start_new
    check(Game.seen == [712,9,6], "Johto home spawn is wrong")
    check($PokemonGlobal.blue_regions["initial"] == "JOHTO", "Johto initial region not saved")
    check($PokemonGlobal.blue_story_mode == :story, "Johto regional start lost story mode")
    check($PokemonGlobal.blue_campaign_departure == false, "Johto starter event would lose items")
    check([$data_system.start_map_id,$data_system.start_x,$data_system.start_y] == [4,7,8],
          "Johto changed the native Decades start coordinates")

    File.write("Data/blue-johto-start.txt", "BLUE_JOHTO_START_V1,JOHTO,321,-1,5\n")
    check(BlueRegionStart.johto_spawn.nil?, "Invalid Johto spawn was accepted")
    File.write("Data/blue-johto-start.txt", "BLUE_JOHTO_START_V1,JOHTO,712,9,6\n")

    # Both regional pilot switches must be isolated: Kanto's pilot remains
    # Kanto, Johto's pilot goes to Johto, neither opens the region picker.
    File.write("Johto pilot.json", "{}")
    $messages = 0
    Game.start_new
    check(Game.seen == [712,9,6], "Johto pilot did not start in Johto")
    check($messages == 0, "Johto pilot unexpectedly opened region picker")
    File.delete("Johto pilot.json")

    old_save = {"version"=>1,"initial"=>"DECADES","current"=>"DECADES","leagues"=>["DECADES"]}
    # A load must never start a new game, irrespective of the last tested
    # regional spawn. Johto tests above intentionally changed Game.seen.
    before_load = Game.seen.dup
    Game.load(old_save)
    check($PokemonGlobal.blue_regions.equal?(old_save), "Legacy load was modified")
    check(Game.seen == before_load, "Loading old save unexpectedly restarted game")

    # The stand-alone pilot is always Kanto and never opens a region picker.
    File.write("Kanto pilot.json", "{}")
    $messages = 0
    Game.start_new
    check(Game.seen == [321,28,14], "Standalone pilot no longer starts in Kanto")
    check($messages == 0, "Pilot should bypass region picker")
  end
end
puts "Blue regional new-game selection OK"
