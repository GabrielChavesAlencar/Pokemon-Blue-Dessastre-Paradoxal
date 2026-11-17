# S22: actual Regions/RegionTravel/CH14 on entirely synthetic states.
# No Game.exe, real MapID, teleport, PC, Bag, party or user save is touched.
require "json"
class PokemonGlobalMetadata
  attr_accessor :pcItemStorage
end

module BlueRegionStart
  class << self
    attr_accessor :synthetic_hoenn_present
    def kanto_integrated?; true; end
    def hoenn_integrated?; !!@synthetic_hoenn_present; end
    def hoenn_town_point
      @synthetic_hoenn_present ? [741, 9, 8, 2] : nil # fake CI coords
    end
  end
end

load File.expand_path(ARGV.fetch(0)) # shared registry mock
load File.expand_path(ARGV.fetch(1)) # real Regions.rb
load File.expand_path(ARGV.fetch(2)) # real RegionTravel.rb
load File.expand_path(ARGV.fetch(3)) # real Story CH14
load File.expand_path(ARGV.fetch(4)) # new S22 read-only adapter
contract = JSON.parse(File.read(File.expand_path(ARGV.fetch(5))))
story = BlueSinnohStoryContracts
travel = BlueSinnohTravelContracts

def check22(ok, why)
  raise "SINNOH_S22: #{why}" unless ok
end

def unchanged22(state, reason)
  snapshot = Marshal.dump(state)
  yield
  check22(Marshal.dump(state) == snapshot, reason)
end

check22(travel::POST_LEAGUE_DESTINATIONS ==
        contract.fetch("post_league_destinations"),
        "Hoenn/Unova travel contract mismatch")
check22(travel::VERIFIED_NATIVE_DEPARTURES.empty?,
        "unverified Sinnoh NPC marked installed")
check22(BlueRegions.circuit.include?("HOENN") &&
        BlueRegions.circuit.include?("UNOVA"),
        "Blue circuit lost Hoenn/Unova")
check22(!travel.respond_to?(:perform) && !travel.respond_to?(:teleport),
        "S22 created a native travel or teleport command")
check22(!travel.valid_arrival?([0, 9, 8, 2]) &&
        !travel.valid_arrival?([5, -1, 0, 2]) &&
        !travel.valid_arrival?([5, 9, 8, 3]) &&
        !travel.valid_arrival?([5, 9, 8]) &&
        !travel.valid_arrival?([5, 9, 8, "2"]) &&
        travel.valid_arrival?([5, 9, 8, 2]),
        "arrival point validation weakened")

state = BlueRegions.new_state("SINNOH")
state["leagues"] << "KANTO"
existing_leagues = state["leagues"].dup
check22(BlueRegions.unlocked(state).include?("UNOVA"),
        "logical circuit should be free-travel, not a HoF lock")
check22(travel.preview(state, "HOENN") == :story_incomplete &&
        travel.preview(state, "UNOVA") == :story_incomplete,
        "pre-Hall physical journey enabled")
check22(travel.preview(state, "KANTO") == :unsupported_destination &&
        travel.preview(state, :HOENN) == :unsupported_destination &&
        travel.preview(state, "") == :unsupported_destination,
        "unlisted post-League destination allowed")

story::STEPS.each do |event|
  case event
  when "P05_COMMANDER_JUPITER"
    check22(BlueRegions.award(state, "SINNOH", "FOREST"),
            "synthetic Forest prerequisite failed")
  when "P08_CYRUS"
    %w[MINE ICICLE].each do |key|
      check22(BlueRegions.award(state, "SINNOH", key),
              "synthetic Cyrus prerequisite missing #{key}")
    end
  when "P09_VOLKNER_BEACON_BADGE"
    check22(BlueRegions.award(state, "SINNOH", "BEACON"),
            "synthetic Volkner prerequisite failed")
  when "SINNOH_LEAGUE_BARRY_GATE"
    %w[COAL COBBLE RELIC FEN].each do |badge|
      check22(BlueRegions.award(state, "SINNOH", badge),
              "synthetic Barry prerequisite failed #{badge}")
    end
  end
  before = Marshal.dump(state)
  if event == "P09_HALL_OF_FAME"
    check22(travel.preview(state, "HOENN") == :story_incomplete,
            "Cynthia victory bypassed engine Hall of Fame")
    check22(!story.record(state, event, confirmed: true),
            "unverified Hall completed regional League")
    check22(Marshal.dump(state) == before,
            "rejected Hall mutated regional save")
    check22(story.record(state, event, confirmed: true,
                         hall_of_fame_verified: true),
            "synthetic engine Hall confirmation failed")
  else
    check22(story.record(state, event, confirmed: true),
            "synthetic CH14 checkpoint failed #{event}")
  end
end
check22(story.league_cleared?(state) &&
        state["leagues"] == existing_leagues + ["SINNOH"],
        "Hall did not clear only Sinnoh in existing league ledger")
check22(!state.key?("hoenn_unlocked") &&
        !state.key?("unova_unlocked") &&
        !state.key?("travel_enabled"),
        "S22 invented a parallel travel unlock flag")
check22(BlueRegionTravel.destination(state, "UNOVA").nil?,
        "logical Unova entry was mistaken for native arrival")
check22(!BlueRegionTravel.source_valid?(state),
        "Sinnoh unverified departure became native")
unchanged22(state, "post-league preflight changed save") do
  check22(travel.destinations(state) == {
            "HOENN" => :destination_not_installed,
            "UNOVA" => :destination_not_installed
          }, "uninstalled destinations were shown as available")
  check22(!travel.available?(state, "HOENN") &&
          !travel.available?(state, "UNOVA"),
          "uninstalled departure marked eligible")
end

# Hoenn has installed arrival in SOME independent Blue builds. The fake CI
# point below is NOT proof. Sinnoh remains a forbidden departure source.
BlueRegionStart.synthetic_hoenn_present = true
check22(BlueRegionTravel.hoenn_installed?, "synthetic Hoenn fixture missing")
check22(BlueRegionTravel.destination(state, "HOENN") == [741, 9, 8, 2],
        "only synthetic Hoenn point should exist")
unchanged22(state, "destination preflight modified league/save") do
  check22(travel.preview(state, "HOENN", npc_context: true) == :source_not_installed,
          "Hoenn arrival overcame missing Sinnoh source")
  check22(travel.preview(state, "UNOVA", npc_context: true) ==
          :destination_not_installed,
          "Unova reused Hoenn's arrival map")
  check22(story.post_cynthia_destination(state, "HOENN") ==
          :source_not_installed,
          "CH14 source gate drifted")
end

# A fully mocked source and NPC is still not an installed Sinnoh handler.
# The frozen native registry is the final guard; never call perform/travel.
class << BlueRegionTravel
  alias_method :s22_original_source_valid?, :source_valid?
  alias_method :s22_original_available?, :available?
  def source_valid?(state)
    state["current"] == "SINNOH" || s22_original_source_valid?(state)
  end
  def available?(state = nil)
    state && state["current"] == "SINNOH" ? true : s22_original_available?(state)
  end
end
unchanged22(state, "fake source/NPC preflight modified regional save") do
  check22(travel.preview(state, "HOENN") == :npc_context_required,
          "NPC context absent but travel was approved")
  check22(travel.preview(state, "HOENN", npc_context: 1) ==
          :npc_context_required, "non-boolean NPC context allowed")
  check22(travel.preview(state, "HOENN", npc_context: true) ==
          :departure_handler_not_verified,
          "synthetic source+NPC bypassed native registry")
  check22(!travel.available?(state, "HOENN", npc_context: true),
          "synthetic NPC certified physical travel")
end
class << BlueRegionTravel
  alias_method :source_valid?, :s22_original_source_valid?
  alias_method :available?, :s22_original_available?
  remove_method :s22_original_source_valid?
  remove_method :s22_original_available?
end
BlueRegionStart.synthetic_hoenn_present = false

saved = Marshal.load(Marshal.dump(state))
copy = travel.destinations(saved)
copy["HOENN"] = :forged
check22(travel.destinations(saved)["HOENN"] == :destination_not_installed,
        "read-only preview returned mutable save property")
saved["current"] = "KANTO"
unchanged22(saved, "foreign Kanto save mutated by S22") do
  check22(travel.preview(saved, "HOENN") == :invalid_state,
          "foreign region reused Sinnoh Hall")
end
saved["current"] = "SINNOH"
check22(story.league_cleared?(saved),
        "regional travel back to Sinnoh lost Hall of Fame")
corrupt = Marshal.load(Marshal.dump(state))
corrupt["sinnoh_ch14"] = ["P09_HALL_OF_FAME"]
unchanged22(corrupt, "invalid CH14 ledger silently repaired") do
  check22(travel.preview(corrupt, "HOENN") == :invalid_state,
          "corrupt save allowed regional departure")
end
%w[DECADES KANTO JOHTO HOENN].each do |region|
  foreign = BlueRegions.new_state(region)
  unchanged22(foreign, "#{region} regional state modified by S22") do
    check22(travel.preview(foreign, "HOENN") == :invalid_state,
            "#{region} falsely inherited Sinnoh post-Hall gate")
  end
end

# The CURRENT real BlueRegionTravel stages local Key Items and HMs in both
# Bag and item PC. Exercise the function with local-only fake item objects.
class S22ItemMeta
  def initialize(kind); @kind=kind; end
  def is_key_item?; @kind == :key; end
  def is_HM?; @kind == :hm; end
end
module GameData
  module Item
    def self.try_get(id)
      kind = case id
             when :HM01, :HM03, :HM04, :HM05 then :hm
             when :SINNOH_KEY, :HOENN_KEY then :key
             else :ordinary
             end
      S22ItemMeta.new(kind)
    end
  end
end

class S22Bag
  attr_accessor :pockets, :registered_items
  def initialize(rows, registered=[])
    @pockets = [Marshal.load(Marshal.dump(rows))]
    @registered_items = registered.dup
  end
  def remove_all(id, qty)
    row = @pockets.first.find { |entry| entry.first == id }
    return false unless row && row[1] >= qty
    row[1] -= qty
    @pockets.first.delete(row) if row[1] == 0
    @registered_items.delete(id) unless @pockets.first.any? { |x| x[0] == id }
    true
  end
  def add_all(id, qty)
    row = @pockets.first.find { |entry| entry.first == id }
    row ? row[1] += qty : @pockets.first << [id, qty]
    true
  end
  def register(id); @registered_items << id unless @registered_items.include?(id); end
end
class S22PC
  attr_accessor :items
  def initialize(rows); @items = Marshal.load(Marshal.dump(rows)); end
  def remove(id, qty)
    row = @items.find { |entry| entry.first == id }
    return false unless row && row[1] >= qty
    row[1] -= qty
    @items.delete(row) if row[1] == 0
    true
  end
  def add(id, qty)
    row = @items.find { |entry| entry.first == id }
    row ? row[1] += qty : @items << [id, qty]
    true
  end
end

$PokemonGlobal = PokemonGlobalMetadata.new
$bag = S22Bag.new([[:HM01,1],[:SINNOH_KEY,1],[:POTION,5]], [:HM01])
$PokemonGlobal.pcItemStorage = S22PC.new([[:HM05,1],[:POTION,2]])
bag_before = Marshal.dump($bag)
pc_before = Marshal.dump($PokemonGlobal.pcItemStorage)
state_before = Marshal.dump(state)
state["region_key_items"] = {
  "HOENN" => {
    "items" => [[:HM03,1],[:HOENN_KEY,1]],
    "registered" => [:HM03],
    "pc_items" => [[:HM04,1]]
  }
}
state_before = Marshal.dump(state)
bag_staged, sinnoh_items, pc_staged =
  BlueRegionTravel.stage_local_bag(state, "HOENN")
check22(sinnoh_items["items"].include?([:HM01,1]) &&
        sinnoh_items["items"].include?([:SINNOH_KEY,1]) &&
        sinnoh_items["registered"] == [:HM01] &&
        sinnoh_items["pc_items"] == [[:HM05,1]],
        "Sinnoh key items/HM or PC stash lost")
check22(bag_staged.pockets.first.include?([:POTION,5]) &&
        bag_staged.pockets.first.include?([:HM03,1]) &&
        bag_staged.pockets.first.include?([:HOENN_KEY,1]) &&
        !bag_staged.pockets.first.any? { |id, _qty|
          [:HM01, :SINNOH_KEY].include?(id) },
        "Hoenn Bag borrowed Sinnoh key items/HM")
check22(pc_staged.items.include?([:POTION,2]) &&
        pc_staged.items.include?([:HM04,1]) &&
        !pc_staged.items.any? { |id, _qty| id == :HM05 },
        "Hoenn item PC borrowed a Sinnoh HM")
check22(Marshal.dump($bag) == bag_before &&
        Marshal.dump($PokemonGlobal.pcItemStorage) == pc_before &&
        Marshal.dump(state) == state_before,
        "preview/staging mutated the original Bag, PC or save")

# Simulate a round trip with detached fake objects. The real move_to() and
# perform() functions must NEVER be called by this regression.
$bag = bag_staged
$PokemonGlobal.pcItemStorage = pc_staged
return_state = Marshal.load(Marshal.dump(state))
return_state["current"] = "HOENN"
return_state["region_key_items"]["SINNOH"] = sinnoh_items
return_snapshot = Marshal.dump(return_state)
back_bag, _hoenn_items, back_pc =
  BlueRegionTravel.stage_local_bag(return_state, "SINNOH")
check22(back_bag.pockets.first.include?([:HM01,1]) &&
        back_bag.pockets.first.include?([:SINNOH_KEY,1]) &&
        back_bag.pockets.first.include?([:POTION,5]) &&
        !back_bag.pockets.first.any? { |id, _qty|
          [:HM03, :HOENN_KEY].include?(id) },
        "returning to Sinnoh did not restore local Bag inventory")
check22(back_pc.items.include?([:HM05,1]) &&
        back_pc.items.include?([:POTION,2]) &&
        !back_pc.items.any? { |id, _qty| id == :HM04 },
        "returning to Sinnoh did not restore local item PC")
check22(Marshal.dump(return_state) == return_snapshot,
        "staging return wrote travel/save state")

# Malformed destination must fail before touching the real Bag/PC.
bad_state = Marshal.load(Marshal.dump(return_state))
bad_state["region_key_items"]["SINNOH"]["items"] = [[:HM01,1],[:HM01,2]]
snapshot_bag = Marshal.dump($bag)
snapshot_pc = Marshal.dump($PokemonGlobal.pcItemStorage)
begin
  BlueRegionTravel.stage_local_bag(bad_state, "SINNOH")
  raise "SINNOH_S22: duplicate regional item did not block stage"
rescue RuntimeError => error
  raise error if error.message.include?("duplicate regional item did not block")
end
check22(Marshal.dump($bag) == snapshot_bag &&
        Marshal.dump($PokemonGlobal.pcItemStorage) == snapshot_pc,
        "invalid destination staging changed original inventory")

puts "SINNOH_S22_HOENN_UNOVA_NPC_ARRIVAL_LOCAL_ITEMS_NO_TELEPORT_OFFLINE_OK"
