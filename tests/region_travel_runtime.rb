# Standalone unit-level regression. Does not load the game or any real saves.
require "tmpdir"
def check(v, name); raise name unless v; end
class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
FakeSpeciesData = Struct.new(:flags, :form)
class FakePokemon
  attr_reader :species_data
  def initialize(flags = [], can_fight = true)
    @species_data = FakeSpeciesData.new(flags, 0)
    @fighting = can_fight
  end
  def egg?; false; end
  def fainted?; !@fighting; end
end
class FakePlayer
  attr_accessor :party, :badges
  def initialize
    @badges = Array.new(24, false)
    @party = []
  end
  def heal_party; @party.each { |_p| }; end
end
class FakeStorage
  def initialize
    @slots = {}
  end
  def maxBoxes; 2; end
  def maxPokemon(_box); 3; end
  def [](box,slot); @slots[[box,slot]]; end
  def []=(box,slot,mon); @slots[[box,slot]]=mon; end
end
class FakePlayerSprite
  attr_accessor :x,:y,:direction
  def initialize; @x=5; @y=8; @direction=2; end
end
class FakeGameMap
  attr_accessor :map_id
  def initialize; @map_id=1; end
end
class FakeTemp
  attr_accessor :player_new_map_id,:player_new_x,:player_new_y,
                :player_new_direction,:player_transferring,
                :in_battle,:message_window_showing,:transition_processing
end
class FakeScene
  attr_accessor :fail_once
  def transfer_player
    $game_map.map_id = $game_temp.player_new_map_id
    $game_player.x = $game_temp.player_new_x
    $game_player.y = $game_temp.player_new_y
    $game_player.direction = $game_temp.player_new_direction
    if @fail_once
      @fail_once = false
      raise "Simulated failed transfer after moving"
    end
  end
end
module GameData
  module Species
    def self.get(*); raise "Not used for base forms"; end
  end
end
module BlueCampaign
  def self.active?; true; end
end
module BlueBattleOptions
  def self.battle_area?; false; end
end
module BlueRegionStart
  def self.kanto_spawn; [300,28,14]; end
end
class PokemonStorageScreen
  def initialize(storage); @storage=storage; end
  def pbWithdraw(*); :withdrawn; end
  def pbPlace(*); :placed; end
  def pbSwap(*); :swapped; end
  def pbDisplay(*); end
end
module MenuHandlers
  def self.add(*); end
end
def pbRgssExists?(path); File.file?(path); end
def pbMapInterpreterRunning?; false; end
def pbFadeOutIn; yield; end
def pbMessage(*); nil; end
def pbConfirmMessage(*); true; end
def _INTL(message, *args)
  args.each_with_index { |v, i| message = message.gsub("{#{i+1}}", v.to_s) }
  message
end

require ARGV.fetch(0)
require ARGV.fetch(1)
require ARGV.fetch(2)
BlueRegionTravel.install

Dir.mktmpdir("blue-region-travel-") do |dir|
  Dir.chdir(dir) do
    Dir.mkdir("Data")
    File.write("Data/blue-kanto-install.json", "{}")
    File.write("Data/Map300.rxdata", "dummy")
    File.write("Data/Map001.rxdata", "dummy")
    $game_map=FakeGameMap.new
    $game_player=FakePlayerSprite.new
    $game_temp=FakeTemp.new
    $scene=FakeScene.new
    $PokemonStorage=FakeStorage.new
    $PokemonGlobal=PokemonGlobalMetadata.new
    $player=FakePlayer.new
    $game_switches=Hash.new(false)
    $player.badges[18]=true
    $game_switches[122]=true
    normal=FakePokemon.new
    special=FakePokemon.new(["Paradox"])
    $player.party=[normal,special]
    before=$player.party.dup

    # A fresh Kanto save, before its League, must not see the agent.
    check(!BlueRegionTravel.available?(BlueRegions.new_state("KANTO")),
          "Kanto travel agent appeared before a League or prior visit")

    # Read-only until a real, successful transfer.
    state=BlueRegions.snapshot
    check(state["leagues"] == ["DECADES"], "Audited Decades finale was not recognized")
    check($PokemonGlobal.blue_regions.nil?, "Snapshot mutated old save")
    check(BlueRegionTravel.available?(state), "Transport not available after proven ending")
    check(BlueRegionTravel.preview(state,"KANTO")[0] == :ok, "Travel preview failed")
    check(BlueRegionTravel.travel("KANTO",true), "Could not arrive in Kanto")
    check($game_map.map_id == 300 && $game_player.x == 28, "Wrong Kanto arrival")
    check($player.party == [normal], "Non-special party member changed")
    check($PokemonStorage[0,0] == special, "Special was not deposited")
    check(BlueRegionTravel.restricted?(special), "Special can be withdrawn before 8 local badges")
    check(PokemonStorageScreen.new($PokemonStorage).pbWithdraw([0,0],nil) == false,
          "Storage withdrawal restriction bypassed")
    check($PokemonGlobal.blue_regions["initial"] == "DECADES", "Initial region overwritten")
    check($PokemonGlobal.blue_regions["current"] == "KANTO", "Current region not updated")
    check($PokemonGlobal.blue_regions["decades_return"] == [1,5,8,2], "Return coords lost")

    saved=Marshal.load(Marshal.dump([$PokemonGlobal.blue_regions,$player.party,$PokemonStorage]))
    check(saved[0]["current"] == "KANTO" && saved[1].size == 1 && saved[2][0,0],
          "Regional trip state cannot be marshalled into a single save")
    check(BlueRegionTravel.travel("DECADES",true), "Could not return to Decades")
    check($game_map.map_id == 1 && $game_player.x == 5, "Wrong Decades return")
    check($PokemonGlobal.blue_regions["initial"] == "DECADES", "Return changed initial region")
    check($PokemonStorage[0,0] == special, "PC was cleared after return")
    check($player.party == [normal], "Party was unexpectedly refilled")
    check($PokemonGlobal.blue_regions["travel_history"].length == 2, "Journey not recorded")

    # Rollback even after scene transfer has moved the player.
    $scene.fail_once=true
    prior_state=Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueRegionTravel.travel("KANTO",true), "Failed map transfer reported success")
    check($game_map.map_id == 1 && $game_player.x == 5, "Rollback did not restore origin")
    check(Marshal.dump($PokemonGlobal.blue_regions) == prior_state, "Failed travel wrote progress")
    check($PokemonStorage[0,0] == special, "Rollback lost stored special")

    # No storage space: the party and all flags stay intact.
    $player.party=[normal,special]
    2.times { |box| 3.times { |slot| $PokemonStorage[box,slot]=FakePokemon.new } }
    state=BlueRegions.snapshot
    check(BlueRegionTravel.preview(state,"KANTO")[0] == :box_full, "Full PC not detected")
    check(!BlueRegionTravel.travel("KANTO",true), "Travel was allowed with full PC")
    check($player.party == [normal,special], "Full PC changed the team")

    # All specials (or unusable normal survivors) cannot strand the player.
    $PokemonStorage=FakeStorage.new
    $player.party=[special]
    check(BlueRegionTravel.preview(state,"KANTO")[0] == :no_usable_party, "No usable team missed")
    check(!BlueRegionTravel.travel("KANTO",true), "Travel stranded trainer with no team")

    # Even if someone forges a snapshot, unverified Hall of Fame is not access.
    $game_switches[122]=false
    check(!BlueRegionTravel.available?(BlueRegions.snapshot), "Travel before ending was allowed")
  end
end
puts "Regional travel, restricted PC, rollback, single save and return OK"
