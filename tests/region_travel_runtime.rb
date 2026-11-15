# Standalone unit-level regression. Does not load the game or any real saves.
require "tmpdir"
def check(v, name); raise name unless v; end
class PokemonGlobalMetadata
  attr_accessor :blue_regions, :blue_campaign_mechanics, :pcItemStorage
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
class FakePCItemStorage
  attr_reader :items
  def initialize; @items=[];@capacity=12; end
  def quantity(id)
    row=@items.find { |entry| entry[0]==id }
    row ? row[1] : 0
  end
  def add(id,qty=1)
    return false unless GameData::Item.try_get(id) && qty>0
    row=@items.find { |entry| entry[0]==id }
    return false if !row && @items.size>=@capacity
    row ? row[1]+=qty : @items << [id,qty]
    true
  end
  def remove(id,qty=1)
    row=@items.find { |entry| entry[0]==id }
    return false unless row && row[1]>=qty
    row[1]-=qty
    @items.delete(row) if row[1]==0
    true
  end
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
  module Item
    Entry=Struct.new(:id,:pocket,:key,:hm,:move) do
      def is_key_item?; !!key; end
      def is_HM?; !!hm; end
    end
    DATA={
      OAKSPARCEL: Entry.new(:OAKSPARCEL, 2, true, false, nil),
      POKEFLUTE: Entry.new(:POKEFLUTE, 2, true, false, nil),
      HM01: Entry.new(:HM01, 3, false, true, :CUT),
      HM03: Entry.new(:HM03, 3, false, true, :SURF),
      TM01: Entry.new(:TM01, 3, false, false, :FOCUSPUNCH),
      POTION: Entry.new(:POTION, 1, false, false, nil),
      MEGASTONE: Entry.new(:MEGASTONE, 1, false, false, nil)
    }.freeze
    def self.try_get(id); DATA[id]; end
  end
end
class FakeBag
  attr_reader :pockets,:registered_items
  def initialize
    @pockets=Array.new(4) { [] }
    @registered_items=[]
    @capacity=16
  end
  def quantity(id)
    @pockets.sum { |pocket| (pocket.find { |row| row[0]==id } || [nil,0])[1] }
  end
  def has?(id); quantity(id)>0; end
  def can_add?(id,qty=1)
    item=GameData::Item.try_get(id)
    return false unless item
    pocket=@pockets[item.pocket]
    (pocket.any? { |row| row[0]==id } || pocket.length<@capacity) && qty>0
  end
  def add_all(id,qty=1)
    return false unless can_add?(id,qty)
    item=GameData::Item.try_get(id)
    row=@pockets[item.pocket].find { |entry| entry[0]==id }
    row ? row[1]+=qty : @pockets[item.pocket] << [id,qty]
    true
  end
  alias add add_all
  def remove_all(id,qty=1)
    item=GameData::Item.try_get(id)
    return false unless item && quantity(id)>=qty
    row=@pockets[item.pocket].find { |entry| entry[0]==id }
    row[1]-=qty
    @pockets[item.pocket].delete(row) if row[1]==0
    true
  end
  alias remove remove_all
  def register(id)
    @registered_items << id unless @registered_items.include?(id)
  end
end
module BlueCampaign
  def self.active?; true; end
  def self.default_mechanics_for(region)
    value={"tera"=>true,"mega"=>true,"zmove"=>true,"dynamax"=>true}
    value["dynamax"]=false if region=="DECADES"
    value
  end
end
module BlueBattleOptions
  def self.battle_area?; false; end
end
module BlueRegionStart
  def self.kanto_integrated?; true; end
  def self.kanto_spawn; [300,28,14]; end
  def self.johto_spawn; @johto_ready ? [712,9,6] : nil; end
  def self.johto_town_point; @johto_ready ? [713,10,11,2] : nil; end
  def self.johto_agent_point; @johto_ready ? [713,11,11,4] : nil; end
  def self.enable_johto; @johto_ready = true; end
  def self.disable_johto; @johto_ready = false; end
end
# Minimal RPG event mocks prove that NPCs are generated in-memory without
# altering Decades RXDATA, source Map IDs or the player's save file.
module RPG
  class EventCommand
    attr_reader :code, :parameters
    def initialize(code, _indent, params); @code, @parameters = code, params; end
  end
  class Event
    attr_accessor :x, :y, :id, :name, :pages
    class Page
      attr_accessor :graphic, :trigger, :list
      def initialize
        @graphic = Struct.new(:character_name).new("")
        @list = []
      end
    end
    def initialize(x, y)
      @x, @y = x, y
      @pages = [Page.new]
    end
  end
end
class Game_Event
  attr_reader :name, :x, :y
  def initialize(_map_id, event)
    @name, @x, @y = event.name, event.x, event.y
  end
end
class MockAgentMap
  attr_accessor :map_id, :events
  def initialize(id)
    @map_id = id
    @events = {}
  end
  def valid?(x, y); (0..48).include?(x) && (0..48).include?(y); end
  def passable?(_x, _y, _d); true; end
end

class Game_Map < MockAgentMap
  def initialize; super(77); end
  def setup(id); @map_id=id; end
end

class PokemonStorageScreen
  def initialize(storage); @storage=storage; end
  def pbWithdraw(selected, heldpoke); :withdrawn; end
  def pbPlace(selected); :placed; end
  def pbSwap(selected); :swapped; end
  def pbDisplay(*); end
end
module MenuHandlers
  def self.add(*); end
end
def pbRgssExists?(path); File.file?(path); end
def pbMapInterpreterRunning?; $interpreter_running == true; end
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
    File.write("Data/blue-kanto-install.json", '{"maps":{"5":300}}')
    File.write("Data/Map300.rxdata", "dummy")
    File.write("Data/Map077.rxdata", "native Decades opening town")
    File.write("Data/Map001.rxdata", "native Decades INTRO; never a regional arrival")
    $game_map=FakeGameMap.new
    $game_player=FakePlayerSprite.new
    $game_temp=FakeTemp.new
    $scene=FakeScene.new
    $PokemonStorage=FakeStorage.new
    $PokemonGlobal=PokemonGlobalMetadata.new
    $PokemonGlobal.blue_campaign_mechanics=BlueCampaign.default_mechanics_for("KANTO")
    $PokemonGlobal.pcItemStorage=FakePCItemStorage.new
    [:OAKSPARCEL,:HM01,:POTION].each { |id| $PokemonGlobal.pcItemStorage.add(id) }
    $bag=FakeBag.new
    [:OAKSPARCEL,:HM01,:POTION,:TM01,:MEGASTONE].each { |id| $bag.add(id) }
    $bag.register(:OAKSPARCEL)
    $bag.register(:HM01)
    $player=FakePlayer.new
    $game_switches=Hash.new(false)
    $player.badges[18]=true
    $game_switches[122]=true
    normal=FakePokemon.new
    special=FakePokemon.new(["Paradox"])
    $player.party=[normal,special]
    before=$player.party.dup
    # No menu or arbitrary route script can teleport. Only the NPC event in
    # the current region's starting city opens the transport service.
    check(!BlueRegionTravel.travel("KANTO",true),
          "Regional travel bypassed the physical NPC")
    BlueRegionTravel.instance_variable_set(:@npc_event_context,true)
    check(BlueRegions.unlocked(BlueRegions.new_state("KANTO")).include?("JOHTO"),
          "Regions are still locked behind a League")

    # A new save which STARTED in Kanto has no previous Decades position.
    # Its authentic native Decades destination works before Hall of Fame,
    # keeping the same party, PC and save.
    kanto_first = BlueRegions.new_state("KANTO")
    # Simulate old saves: they stored the native INTRO map, which must NEVER
    # run again when arriving via the regional transportation NPC.
    kanto_first["decades_first_arrival"] = [1,5,8,2]
    decades_arrival = BlueRegionTravel.decades_town_point
    check(decades_arrival && decades_arrival[0] == 77 &&
          decades_arrival[1,2] != [24,24],
          "Cherryhill arrival must be safe and avoid the generated travel NPC")
    check(BlueRegionTravel.destination(kanto_first, "DECADES") == decades_arrival,
          "Kanto visit reopened native Decades character-selection intro")
    check(kanto_first["leagues"].empty?, "Travel awarded a League victory")
    $PokemonGlobal.blue_regions = kanto_first
    $game_map.map_id = 300
    $player.party = [normal]
    check(BlueRegionTravel.travel("DECADES", true), "Kanto starter could not enter Decades")
    check($PokemonGlobal.blue_regions["initial"] == "KANTO" &&
          $PokemonGlobal.blue_regions["current"] == "DECADES",
          "One-save Kanto origin was lost after travel")
    check($game_map.map_id == 77 && $game_player.x == decades_arrival[1],
          "Kanto to Decades used the intro map instead of Cherryhill")
    check($PokemonGlobal.blue_campaign_mechanics ==
          {"tera"=>true,"mega"=>true,"zmove"=>true,"dynamax"=>false},
          "Decades arrival did not enable Mega/Z/Tera and disable Dynamax")
    check(!$bag.has?(:OAKSPARCEL) && !$bag.has?(:HM01),
          "Key items and HMs from Kanto leaked into Decades")
    check($bag.has?(:POTION) && $bag.has?(:TM01) && $bag.has?(:MEGASTONE),
          "Ordinary items, TMs or Mega Stones disappeared on travel")
    check(($bag.registered_items & [:OAKSPARCEL,:HM01]).empty?,
          "Registered Kanto-only items leaked into Decades quick access")
    check($PokemonGlobal.pcItemStorage.quantity(:OAKSPARCEL)==0 &&
          $PokemonGlobal.pcItemStorage.quantity(:HM01)==0 &&
          $PokemonGlobal.pcItemStorage.quantity(:POTION)==1,
          "Kanto HMs/key items leaked through the shared item PC")
    check($PokemonGlobal.blue_regions["region_key_items"]["KANTO"]["items"].length==2,
          "Kanto key items and HMs were not backed up in the regional save")
    $bag.add(:POKEFLUTE)
    $bag.add(:HM03)
    $bag.register(:POKEFLUTE)
    $PokemonGlobal.pcItemStorage.add(:POKEFLUTE)
    $PokemonGlobal.pcItemStorage.add(:HM03)
    # The same save must round-trip to Kanto and back before the legacy
    # scenario below intentionally resets regional state to nil.
    check(BlueRegionTravel.travel("KANTO",true),
          "Original Kanto save could not revisit its own region")
    check($bag.has?(:OAKSPARCEL) && $bag.has?(:HM01) &&
          !$bag.has?(:POKEFLUTE) && !$bag.has?(:HM03),
          "Original Kanto save did not restore Kanto key items/HMs")
    check($bag.registered_items.include?(:OAKSPARCEL) &&
          !$bag.registered_items.include?(:POKEFLUTE),
          "Regional registered shortcuts did not switch back to Kanto")
    check($PokemonGlobal.pcItemStorage.quantity(:OAKSPARCEL)==1 &&
          $PokemonGlobal.pcItemStorage.quantity(:HM01)==1 &&
          $PokemonGlobal.pcItemStorage.quantity(:POKEFLUTE)==0 &&
          $PokemonGlobal.pcItemStorage.quantity(:HM03)==0,
          "Kanto item PC did not restore local key items/HMs")
    check(BlueRegionTravel.travel("DECADES",true),
          "Original Kanto save could not return to Decades")
    check($bag.has?(:POKEFLUTE) && $bag.has?(:HM03) &&
          !$bag.has?(:OAKSPARCEL) && !$bag.has?(:HM01),
          "Original Kanto save did not restore Decades key items/HMs")
    check($PokemonGlobal.pcItemStorage.quantity(:POKEFLUTE)==1 &&
          $PokemonGlobal.pcItemStorage.quantity(:HM03)==1 &&
          $PokemonGlobal.pcItemStorage.quantity(:HM01)==0,
          "Decades item PC leaked Kanto's stored HM")
    # Changes made in Decades must survive visits to another region.
    $PokemonGlobal.blue_campaign_mechanics["zmove"]=false
    $PokemonGlobal.blue_regions = nil
    $player.party = [normal,special]

    # The new save can speak to its NPC before the first badge or League.
    check(BlueRegionTravel.available?(BlueRegions.new_state("KANTO")),
          "Kanto travel agent remained locked behind League victory")

    # Read-only until a real, successful transfer.
    state=BlueRegions.snapshot
    check(state["leagues"] == ["DECADES"], "Audited Decades finale was not recognized")
    check($PokemonGlobal.blue_regions.nil?, "Snapshot mutated old save")
    check(BlueRegionTravel.available?(state), "Transport not available after proven ending")
    # The static NPC in Pallet/Decades invokes travel during a map event.
    # Trusted event context may call the menu; arbitrary interpreter code may not.
    BlueRegionTravel.instance_variable_set(:@npc_event_context,false)
    $interpreter_running = true
    check(!BlueRegionTravel.available?(state), "Untrusted map interpreter bypassed travel")
    BlueRegionTravel.agent(true)
    check(!BlueRegionTravel.available?(state), "Trusted NPC context leaked after menu closure")
    $interpreter_running = false
    BlueRegionTravel.instance_variable_set(:@npc_event_context,true)
    check(BlueRegionTravel.preview(state,"KANTO")[0] == :ok, "Travel preview failed")
    check(BlueRegionTravel.travel("KANTO",true), "Could not arrive in Kanto")
    check($game_map.map_id == 300 && $game_player.x == 18, "Wrong Pallet Town arrival")
    check($player.party == [normal], "Non-special party member changed")
    check($PokemonStorage[0,0] == special, "Special was not deposited")
    check(BlueRegionTravel.restricted?(special), "Special can be withdrawn before 8 local badges")
    check(PokemonStorageScreen.new($PokemonStorage).pbWithdraw([0,0],nil) == false,
          "Storage withdrawal restriction bypassed")
    check(PokemonStorageScreen.new($PokemonStorage).pbPlace([0,1]) == :placed,
          "Native PC pbPlace signature changed")
    check($PokemonGlobal.blue_regions["initial"] == "DECADES", "Initial region overwritten")
    check($PokemonGlobal.blue_regions["current"] == "KANTO", "Current region not updated")
    check($PokemonGlobal.blue_regions["decades_return"] == decades_arrival,
          "Return coords lost")
    # A legacy Decades save with no regional vault cannot conjure items
    # earned by a different character in the prior synthetic test scenario.
    check(!$bag.has?(:POKEFLUTE) && !$bag.has?(:HM03),
          "Legacy Decades items remained usable after traveling to Kanto")
    check(!$bag.registered_items.include?(:POKEFLUTE),
          "Legacy Decades shortcut leaked into Kanto")
    check($PokemonGlobal.blue_campaign_mechanics["dynamax"] == true,
          "Kanto mechanics were overwritten by Decades preferences")

    saved=Marshal.load(Marshal.dump([$PokemonGlobal.blue_regions,$player.party,$PokemonStorage]))
    check(saved[0]["current"] == "KANTO" && saved[1].size == 1 && saved[2][0,0],
          "Regional trip state cannot be marshalled into a single save")
    check(BlueRegionTravel.travel("DECADES",true), "Could not return to Decades")
    check($game_map.map_id == 77 && $game_player.x == decades_arrival[1],
          "Wrong Decades return")
    check($PokemonGlobal.blue_campaign_mechanics["dynamax"] == false &&
          $PokemonGlobal.blue_campaign_mechanics["zmove"] == false,
          "Returning to Decades lost its mechanics preferences")
    check($bag.has?(:POKEFLUTE) && $bag.has?(:HM03) &&
          !$bag.has?(:OAKSPARCEL) && !$bag.has?(:HM01),
          "Returning to Decades did not restore only its own HMs/key items")
    check($bag.registered_items.include?(:POKEFLUTE) &&
          !$bag.registered_items.include?(:HM01),
          "Return to Decades restored another region's shortcuts")
    check($PokemonGlobal.blue_regions["initial"] == "DECADES", "Return changed initial region")
    check($PokemonStorage[0,0] == special, "PC was cleared after return")
    check($player.party == [normal], "Party was unexpectedly refilled")
    check($PokemonGlobal.blue_regions["travel_history"].length == 2, "Journey not recorded")

    # Rollback even after scene transfer has moved the player.
    $scene.fail_once=true
    prior_state=Marshal.dump($PokemonGlobal.blue_regions)
    prior_bag=Marshal.dump([$bag.pockets,$bag.registered_items])
    prior_pc=Marshal.dump($PokemonGlobal.pcItemStorage.items)
    check(!BlueRegionTravel.travel("KANTO",true), "Failed map transfer reported success")
    check(Marshal.dump($PokemonGlobal.pcItemStorage.items)==prior_pc,
          "Failed teleport lost key items/HMs deposited in the item PC")
    check(Marshal.dump([$bag.pockets,$bag.registered_items])==prior_bag,
          "Failed map transfer lost or duplicated HMs/key items")
    check($game_map.map_id == 77 && $game_player.x == decades_arrival[1],
          "Rollback did not restore origin")
    check($PokemonGlobal.blue_campaign_mechanics["zmove"] == false,
          "Failed regional transfer corrupted preferences")
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

    # No Hall of Fame flag is required for transport, but it must still be
    # started by a physical NPC in the correct starting town.
    $game_switches[122]=false
    check(BlueRegionTravel.available?(BlueRegions.snapshot),
          "Transport was still gated by the Decades ending")
    BlueRegionTravel.instance_variable_set(:@npc_event_context,false)
    check(!BlueRegionTravel.travel("KANTO",true), "Non-NPC transport was allowed")
    BlueRegionTravel.instance_variable_set(:@npc_event_context,true)
    # A valid NPC script on a route outside the starting town cannot move us.
    $game_map.map_id = 22
    check(!BlueRegionTravel.travel("KANTO",true),
          "Transport worked from outside the starting city")
    $game_map.map_id = 77

    # Phase 16: Kanto/Decades transfer semantics stay unchanged; only a
    # trustworthy, audited installation may add a Johto destination.
    $game_switches[122] = true
    $player.party = [normal]
    $PokemonStorage = FakeStorage.new
    File.write("Data/Map712.rxdata", "synthetic Johto bedroom")
    File.write("Data/Map713.rxdata", "synthetic New Bark arrival beside NPC")
    BlueRegionStart.disable_johto
    state = BlueRegions.snapshot
    state["leagues"] << "KANTO"
    # snapshot is deliberately a copy: persist simulated Kanto League completion
    # before travel() reloads the save for its independent safety checks.
    $PokemonGlobal.blue_regions = state
    check(BlueRegionTravel.destination(state, "JOHTO").nil?,
          "Uninstalled Johto unexpectedly opened from Kanto")
    check(!BlueRegionTravel.johto_installed?,
          "Johto was called installed without a release proof")
    BlueRegionStart.enable_johto
    check(BlueRegionTravel.johto_installed?,
          "Mock approved Johto release was not recognized")
    check(BlueRegionTravel.destination(state, "JOHTO") == [713,10,11,2],
          "Johto destination must be an audited New Bark tile, not a bedroom")
    check(BlueRegionTravel.travel("KANTO", true),
          "Cannot return to Kanto for the Johto travel test")
    check($PokemonGlobal.blue_regions["current"] == "KANTO",
          "Kanto travel did not persist")
    check(BlueRegionTravel.travel("JOHTO", true),
          "Travel from Kanto to installed Johto failed")
    check($game_map.map_id == 713 && $game_player.x == 10,
          "Johto travel reached the wrong town/coordinate")
    check(BlueRegionTravel.available?($PokemonGlobal.blue_regions),
          "New Bark agent still requires a Johto League victory")
    check($PokemonGlobal.blue_regions["leagues"].empty? ||
          !$PokemonGlobal.blue_regions["leagues"].include?("JOHTO"),
          "Free transport falsely credited Johto League")
    check(BlueRegionTravel.destination($PokemonGlobal.blue_regions, "HOENN").nil?,
          "Uninstalled Hoenn was given a fabricated destination")
    before_johto = Marshal.dump($PokemonGlobal.blue_regions)
    $scene.fail_once = true
    check(!BlueRegionTravel.travel("KANTO", true),
          "Johto failed transfer incorrectly succeeded")
    check($game_map.map_id == 713 && $game_player.x == 10,
          "Failed travel stranded player away from New Bark")
    check(Marshal.dump($PokemonGlobal.blue_regions) == before_johto,
          "Failed Johto departure damaged original save")
    check(BlueRegionTravel.travel("KANTO", true), "Johto -> Kanto travel failed")
    check(BlueRegionTravel.travel("JOHTO", true), "Kanto -> Johto return failed")
    check($PokemonGlobal.blue_regions["travel_history"].last[1] == "JOHTO",
          "Return to Johto omitted travel history")
    BlueRegionStart.disable_johto
    check(!BlueRegionTravel.available?($PokemonGlobal.blue_regions),
          "Johto agent remained active after pilot proof was revoked")
    check(!BlueRegionTravel.travel("KANTO", true),
          "Unverified Johto origin allowed travel")
    check($game_map.map_id == 713, "Denied travel after revoked proof moved player")
    BlueRegionTravel.instance_variable_set(:@npc_event_context,false)

    # A native Decades player (including an older save without regional state)
    # sees an interactable agent in Cherryhill before finishing any League.
    $PokemonGlobal.blue_regions = nil
    decades_map = MockAgentMap.new(77)
    decades_file = File.binread("Data/Map077.rxdata")
    BlueRegionTravel.attach_decades_agent(decades_map)
    check(decades_map.events.size == 1 &&
          decades_map.events.values.first.name == BlueRegionTravel::DECADES_AGENT_NAME,
          "Missing native Decades starting-town NPC")
    BlueRegionTravel.attach_decades_agent(decades_map)
    check(decades_map.events.size == 1, "Repeated map setup duplicated Decades NPC")
    check(File.binread("Data/Map077.rxdata") == decades_file,
          "Generated NPC modified native Decades map on disk")

    # Kanto NPC appears in the true Pallet Town map, without blocking the
    # audited destination tile and without creating a second copy on reload.
    $PokemonGlobal.blue_regions = BlueRegions.new_state("KANTO")
    pallet = MockAgentMap.new(300)
    original_map = File.binread("Data/Map300.rxdata")
    BlueRegionTravel.attach_kanto_agent(pallet)
    check(pallet.events.size == 1 &&
          pallet.events.values.first.name == BlueRegionTravel::KANTO_AGENT_NAME,
          "Pallet Town is missing the travel NPC")
    actor = pallet.events.values.first
    check([actor.x,actor.y] != [18,8], "Kanto NPC obstructed the town arrival")
    BlueRegionTravel.attach_kanto_agent(pallet)
    check(pallet.events.size == 1, "Repeated Pallet entry duplicated Kanto NPC")
    check(File.binread("Data/Map300.rxdata") == original_map,
          "Kanto NPC overwrote the FRLG map")

    BlueRegionStart.enable_johto
    $PokemonGlobal.blue_regions = BlueRegions.new_state("JOHTO")
    new_bark = MockAgentMap.new(713)
    BlueRegionTravel.attach_johto_agent(new_bark)
    check(new_bark.events.size == 1 &&
          new_bark.events.values.first.name == BlueRegionTravel::JOHTO_AGENT_NAME,
          "New Bark transport required the Johto Hall of Fame")
    BlueRegionStart.disable_johto
  end
end
puts "Regional travel, restricted PC, rollback, single save and return OK"
