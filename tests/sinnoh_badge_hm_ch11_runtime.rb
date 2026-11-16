# CH11: use real shared Regions.rb, RegionTravel.rb and RegionalPolicy.rb.
# Synthetic Bag/PC, no real Game.exe, maps, native Gym badges, or player saves.
require "json"
require "tmpdir"

def check(condition, message)
  raise "SINNOH CH11: #{message}" unless condition
end

module BlueCampaign
  def self.active?; true; end
end
module BlueBattleOptions
  def self.battle_area?; false; end
end
module BlueRegionStart
  def self.kanto_integrated?; true; end
end
module GameData
  module Item
    Entry = Struct.new(:id, :pocket, :key, :hm, :move) do
      def is_key_item?; !!key; end
      def is_HM?; !!hm; end
    end
    DATA = {
      :HM01 => Entry.new(:HM01, 3, false, true, :CUT),
      :HM02 => Entry.new(:HM02, 3, false, true, :FLY),
      :HM03 => Entry.new(:HM03, 3, false, true, :SURF),
      :HM04 => Entry.new(:HM04, 3, false, true, :STRENGTH),
      :HM05 => Entry.new(:HM05, 3, false, true, :DEFOG),
      :HM06 => Entry.new(:HM06, 3, false, true, :ROCKSMASH),
      :HM07 => Entry.new(:HM07, 3, false, true, :WATERFALL),
      :HM08 => Entry.new(:HM08, 3, false, true, :ROCKCLIMB),
      :OAKSPARCEL => Entry.new(:OAKSPARCEL, 2, true, false, nil),
      :POKEFLUTE => Entry.new(:POKEFLUTE, 2, true, false, nil),
      :POTION => Entry.new(:POTION, 1, false, false, nil),
      :TM01 => Entry.new(:TM01, 3, false, false, :FOCUSPUNCH),
    }
    def self.try_get(key); DATA[key]; end
    def self.exists?(key); DATA.key?(key); end
    def self.each
      DATA.each_value { |item| yield item }
    end
  end
end

class SyntheticBag
  attr_reader :pockets, :registered_items
  def initialize
    @pockets = Array.new(4) { [] }
    @registered_items = []
  end
  def quantity(id)
    @pockets.sum { |pocket|
      (pocket.find { |entry| entry[0] == id } || [nil, 0])[1]
    }
  end
  def has?(id); quantity(id) > 0; end
  def add_all(id, qty = 1)
    meta = GameData::Item.try_get(id)
    return false unless meta && qty.is_a?(Integer) && qty > 0
    pocket = @pockets[meta.pocket]
    row = pocket.find { |entry| entry[0] == id }
    row ? row[1] += qty : pocket << [id, qty]
    true
  end
  alias add add_all
  def remove_all(id, qty = 1)
    meta = GameData::Item.try_get(id)
    return false unless meta && qty.is_a?(Integer) && qty > 0 &&
                        quantity(id) >= qty
    pocket = @pockets[meta.pocket]
    row = pocket.find { |entry| entry[0] == id }
    row[1] -= qty
    pocket.delete(row) if row[1] == 0
    true
  end
  def register(item)
    @registered_items << item unless @registered_items.include?(item)
  end
end

class SyntheticItemPC
  attr_reader :items
  def initialize; @items = []; end
  def has?(id); @items.any? { |row| row[0] == id }; end
  def add(id, qty = 1)
    return false unless GameData::Item.try_get(id) && qty > 0
    row = @items.find { |entry| entry[0] == id }
    row ? row[1] += qty : @items << [id, qty]
    true
  end
  def remove(id, qty = 1)
    row = @items.find { |entry| entry[0] == id }
    return false unless row && row[1] >= qty
    row[1] -= qty
    @items.delete(row) if row[1] == 0
    true
  end
end

require File.expand_path(ARGV.fetch(0))
require File.expand_path(ARGV.fetch(1))
require File.expand_path(ARGV.fetch(2))
require File.expand_path(ARGV.fetch(3))

$player = Struct.new(:badges, :party).new(Array.new(24, false), [])
$game_switches = nil
$PokemonGlobal = PokemonGlobalMetadata.new
$PokemonGlobal.define_singleton_method(:pcItemStorage) { @pcItemStorage }
$PokemonGlobal.define_singleton_method(:pcItemStorage=) { |value| @pcItemStorage = value }
$bag = SyntheticBag.new
$PokemonGlobal.pcItemStorage = SyntheticItemPC.new

def active(state)
  $PokemonGlobal.blue_regions = state
  state
end
def field(move)
  BlueRegionalPolicy.field_result(move)
end

# 1. Existing Platinum badge and HM pairing is the source of truth.
rules = JSON.parse(File.read(File.expand_path(ARGV.fetch(4)))).fetch("rules")
check(rules.size == 8, "eight badge/HM definitions required")
check(rules.map { |row| row.fetch("badge") } ==
      BlueRegions.info("SINNOH")["milestones"], "milestone registry drift")
check(rules.map { |row| row.fetch("field_move") }.sort ==
      BlueRegions.info("SINNOH")["field"].keys.sort,
      "the badge/HM field mapping drifted")
check(rules.to_h { |row| [row.fetch("field_move"), row.fetch("hm_item").to_sym] } ==
      BlueRegions::SINNOH_HM_ITEMS, "canonical Platinum item IDs drifted")

# 2. No local badges means no HM permission, even while holding foreign HMs.
s = active(BlueRegions.new_state("SINNOH"))
rules.each do |row|
  move = row.fetch("field_move")
  item = row.fetch("hm_item").to_sym
  ruby_move = move.delete("_").to_sym
  $bag.add(item)
  check(BlueRegions.field_access(s, "SINNOH", move, true) == :badge,
        "#{move} skipped its Sinnoh badge")
  check(field(ruby_move) == :badge, "#{move} bypassed Sinnoh badge in policy")
  check(!BlueRegions.record_sinnoh_hm(s, move, item, $bag),
        "#{move} registered without a trusted pickup")
  check(!BlueRegions.record_sinnoh_hm(s, move, :TM01, $bag, true),
        "#{move} accepted TM/item from wrong region")
  check(BlueRegions.award(s, "SINNOH", row.fetch("badge")),
        "#{move} was not awarded after a simulated Gym win")
  check(!BlueRegions.award(s, "SINNOH", row.fetch("badge")),
        "#{move} duplicated a badge")
  check(field(ruby_move) == :hm,
        "#{move} used an HM held in Bag without a local pickup")
  check(BlueRegions.record_sinnoh_hm(s, move, item, $bag, true),
        "#{move} refused a confirmed Sinnoh pickup")
  check(!BlueRegions.record_sinnoh_hm(s, move, item, $bag, true),
        "#{move} created duplicate local acquisition")
  check(BlueRegions.field_access(s, "SINNOH", move, true) == :allowed,
        "#{move} blocked after badge and local HM acquisition")
  check(field(ruby_move) == :allowed,
        "#{move} policy blocked legitimate Sinnoh HM")
  $bag.remove_all(item)
  check(field(ruby_move) == :hm,
        "#{move} worked without physical HM held in Sinnoh Bag")
end
check(BlueRegions.local_achievements(s, "SINNOH").length == 8,
      "the eight achievements were not unique")
check(BlueRegions.allow_specials?(s, "SINNOH"),
      "eight Sinnoh badges did not unlock local special access")
%w[KANTO JOHTO HOENN].each do |other|
  check(!BlueRegions.allow_specials?(s, other),
        "Sinnoh badges unlocked a foreign region: " + other)
end
check(!BlueRegions.allow_specials?(s, "DECADES", $player.badges),
      "Sinnoh achievements wrote the native Decades badge array")
check($player.badges.none?, "Sinnoh badges leaked to Decades native badges")

# 3. Switch regions: neither Sinnoh badges nor HM claim is exported.
s["current"] = "KANTO"
old = Marshal.dump(s)
check(BlueRegions.field_access(s, "SINNOH", "SURF", true) == :unavailable,
      "foreign region used previously earned Sinnoh Surf")
check(!BlueRegions.award(s, "SINNOH", "BEACON"),
      "foreign region awarded Sinnoh badge")
check(!BlueRegions.record_sinnoh_hm(s, "SURF", :HM03, $bag, true),
      "foreign region registered Sinnoh HM")
check(Marshal.dump(s) == old, "foreign-region checks mutated a save")
s["current"] = "SINNOH"
saved = Marshal.load(Marshal.dump(s))
check(BlueRegions.local_achievements(saved, "SINNOH").length == 8,
      "reload lost the local badge sequence")
check(BlueRegions.sinnoh_local_hms(saved).sort ==
      BlueRegions::SINNOH_HM_ITEMS.keys.sort,
      "reload lost region HM proof")
check(BlueRegions.crystal_total(saved, 0) == 8,
      "cross-region crystal total duplicated progress")

# 4. Forged/invalid achievement or local HM lists fail closed, never repair.
[
  ["achievements", {"SINNOH" => ["COAL", "COAL"]}],
  ["achievements", {"SINNOH" => ["SOUL"]}],
  ["achievements", {"SINNOH" => true}],
  ["region_local_hms", {"SINNOH" => ["SURF", "SURF"]}],
  ["region_local_hms", {"SINNOH" => ["ROCKCLIMB"]}],
  ["region_local_hms", {"SINNOH" => "SURF"}],
].each do |key, value|
  corrupted = Marshal.load(Marshal.dump(saved))
  corrupted[key] = value
  before = Marshal.dump(corrupted)
  check(BlueRegions.field_access(corrupted, "SINNOH", "SURF", true) == :unavailable,
        "corrupt regional achievement/HM list was accepted")
  check(!BlueRegions.award(corrupted, "SINNOH", "COAL") ||
        key == "region_local_hms",
        "corrupt Sinnoh achievements were auto-repaired")
  check(!BlueRegions.record_sinnoh_hm(corrupted, "SURF", :HM03, $bag, true),
        "corrupt Sinnoh HM record was overwritten")
  # award() only sees badge state; malformed HM data never gets rewritten.
  if key == "achievements"
    check(Marshal.dump(corrupted) == before, "bad achievements mutated a save")
  end
end

# 5. The existing RegionalTravel Bag+PC vault remains authoritative.
# Simulate state commits only; no maps or transfer NPCs are installed here.
state = active(BlueRegions.new_state("KANTO"))
$bag = SyntheticBag.new
$PokemonGlobal.pcItemStorage = SyntheticItemPC.new
$bag.add(:OAKSPARCEL)
$bag.add(:HM03)
$bag.add(:POTION)
$bag.add(:TM01)
$bag.register(:HM03)
$PokemonGlobal.pcItemStorage.add(:OAKSPARCEL)
$PokemonGlobal.pcItemStorage.add(:HM03)

def hop(state, destination)
  bag, source, pc = BlueRegionTravel.stage_local_bag(state, destination)
  state["region_key_items"] ||= {}
  state["region_key_items"][state["current"]] = source
  state["current"] = destination
  $bag = bag
  $PokemonGlobal.pcItemStorage.items.replace(pc.items)
end

hop(state, "SINNOH")
check(!$bag.has?(:HM03) && !$bag.has?(:OAKSPARCEL),
      "Kanto HM and key item leaked into Sinnoh")
check($bag.has?(:POTION) && $bag.has?(:TM01),
      "ordinary items and TMs were unnecessarily moved")
check(!$PokemonGlobal.pcItemStorage.has?(:HM03),
      "Kanto item PC's Surf leaked to Sinnoh")
$bag.add(:HM06)
$bag.add(:POKEFLUTE)
$bag.register(:HM06)
$PokemonGlobal.pcItemStorage.add(:HM06)
check(BlueRegions.award(state, "SINNOH", "COAL"),
      "Sinnoh Coal badge failed in separate region state")
check(BlueRegions.record_sinnoh_hm(state, "ROCK_SMASH", :HM06, $bag, true),
      "Sinnoh local Rock Smash receipt did not persist")
hop(state, "HOENN")
check(!$bag.has?(:HM06) && !$bag.has?(:POKEFLUTE),
      "Sinnoh HM/key item leaked to Hoenn")
check(!$PokemonGlobal.pcItemStorage.has?(:HM06),
      "Sinnoh HM leaked through Hoenn item PC")
$bag.add(:HM03)
$bag.add(:POKEFLUTE)
$bag.register(:HM03)
hop(state, "KANTO")
check($bag.has?(:HM03) && $bag.has?(:OAKSPARCEL) &&
      !$bag.has?(:HM06) && !$bag.has?(:POKEFLUTE),
      "Kanto's original HMs/Key Items not restored independently")
check($PokemonGlobal.pcItemStorage.has?(:HM03) &&
      !$PokemonGlobal.pcItemStorage.has?(:HM06),
      "Kanto PC received the wrong HM on return")
hop(state, "SINNOH")
check($bag.has?(:HM06) && $bag.has?(:POKEFLUTE) &&
      !$bag.has?(:HM03) && !$bag.has?(:OAKSPARCEL),
      "Sinnoh items not restored independently from Kanto and Hoenn")
check($PokemonGlobal.pcItemStorage.has?(:HM06) &&
      !$PokemonGlobal.pcItemStorage.has?(:HM03),
      "Sinnoh item PC received a foreign HM")
check($bag.registered_items.include?(:HM06) &&
      !$bag.registered_items.include?(:HM03),
      "foreign HM shortcut leaked into Sinnoh")
check(BlueRegions.sinnoh_local_hms(state) == ["ROCK_SMASH"],
      "Sinnoh local HM flag lost across Kanto/Hoenn travel")
check(BlueRegions.field_access(state, "SINNOH", "ROCK_SMASH", true) == :allowed,
      "Sinnoh permission lost after correct local return")
check(BlueRegions.field_access(state, "SINNOH", "SURF", true) == :badge,
      "foreign badge/HM unlocked Surf")

# 6. An old native Decades save still has its unmodified native permissions.
legacy = active(BlueRegions.new_state("DECADES"))
check(BlueRegions.field_access(legacy, "DECADES", "SURF", true) == :native,
      "Decades field access no longer delegates to native")
check(!legacy.key?("region_local_hms") && !legacy.key?("region_key_items"),
      "legacy Decades state was migrated by an isolated Sinnoh test")

puts "SINNOH_CH11_BADGES_HMS_ISOLATION_AND_VAULT_OK"
