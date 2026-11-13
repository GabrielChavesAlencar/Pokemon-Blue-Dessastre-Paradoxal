# Pure Ruby contract simulation. The three following ARGV files are actual
# Johto story modules, not installed map handlers.
require "tmpdir"

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
module BlueRegions
  BADGES = %w[ZEPHYR HIVE PLAIN FOG STORM MINERAL GLACIER RISING].freeze
  def self.local_achievements(state, region)
    (state["achievements"] || {}).fetch(region, [])
  end
  def self.award(state, region, key)
    return false unless state["current"] == "JOHTO" && region == "JOHTO"
    return false unless BADGES.include?(key)
    list = (state["achievements"] ||= {})[region] ||= []
    return false if list.include?(key)
    list << key
    true
  end
  def self.crystal_total(state, native)
    native + local_achievements(state, "JOHTO").length
  end
  def self.field_access(state, region, action, ready = false)
    return :unavailable unless state["current"] == "JOHTO" && region == "JOHTO"
    need = {"WHIRLPOOL"=>"GLACIER"}[action]
    return :unavailable unless need
    return :badge unless local_achievements(state, "JOHTO").include?(need)
    ready ? :allowed : :tool
  end
end
module TrainerBattle
  class << self
    attr_accessor :result
    def history
      @history ||= []
    end
    def start(*args)
      history << args
      result
    end
  end
end
module GameData
  module Item
    def self.exists?(id)
      id == :SECRETPOTION
    end
  end
end
class FakeBag
  attr_accessor :mode
  def initialize(items = {})
    @items = items.dup
    @mode = :normal
  end
  def quantity(key)
    @items.fetch(key, 0)
  end
  def remove(key, amount = 1)
    return false if mode == :fail || quantity(key) < amount
    return true if mode == :dishonest
    @items[key] -= amount
    true
  end
end
$messages = []
def _INTL(value, *arguments)
  arguments.each_with_index { |v, i| value = value.gsub("{#{i + 1}}", v.to_s) }
  value
end
def pbMessage(message, *options)
  $messages << message
end
def check(condition, message)
  raise message unless condition
end

require ARGV.fetch(0)
require ARGV.fetch(1)
require ARGV.fetch(2)

Dir.mktmpdir("blue-johto-jasmine-") do |dir|
  Dir.chdir(dir) do
    Dir.mkdir("Data")
    $PokemonGlobal = PokemonGlobalMetadata.new
    $bag = FakeBag.new(SECRETPOTION: 1)
    flags = {"starter"=>"CYNDAQUIL", "olivine_medicine_requested"=>true,
             "cianwood_medicine_received"=>true,
             "olivine_returned_with_medicine"=>true,
             "olivine_lighthouse_floor"=>6, "olivine_visited"=>true}
    state = {"version"=>1, "initial"=>"JOHTO", "current"=>"DECADES",
             "achievements"=>{"JOHTO"=>%w[ZEPHYR HIVE PLAIN FOG]},
             "johto_pilot"=>flags}
    $PokemonGlobal.blue_regions = state
    initial = Marshal.dump(state)
    check(!BlueJohtoJasmine.deliver_medicine, "Decades cured Ampharos")
    check(!BlueJohtoJasmine.gym_entrance, "Decades opened Jasmine gym")
    check(!BlueJohtoJasmine.jasmine, "Decades opened Jasmine battle")
    check(!BlueJohtoJasmine.whirlpool_allowed?(true), "Decades allowed whirlpool")
    check(!BlueJohtoJasmine.whirl_islands_entry(true), "Decades warped to islands")
    check(Marshal.dump(state) == initial, "Decades state modified")
    check($bag.quantity(:SECRETPOTION) == 1, "Decades inventory consumed")

    state["current"] = "KANTO"
    saved_kanto = Marshal.dump(state)
    check(!BlueJohtoJasmine.deliver_medicine, "Kanto cured Ampharos")
    check(!BlueJohtoJasmine.jasmine, "Kanto battle")
    check(!BlueJohtoJasmine.whirl_islands_entry(true), "Kanto warp")
    check(Marshal.dump(state) == saved_kanto, "Kanto save modified")

    state["current"] = "JOHTO"
    check(!BlueJohtoJasmine.gym_entrance, "Jasmine before cure")
    check(!BlueJohtoJasmine.jasmine, "Jasmine battle before cure")
    check(!BlueJohtoJasmine.deliver_medicine, "Cure without marker")
    check($bag.quantity(:SECRETPOTION) == 1, "Missing marker consumed item")
    File.write(BlueJohtoJasmine::CURE_READY, "WRONG")
    check(!BlueJohtoJasmine.deliver_medicine, "Wrong cure marker accepted")
    File.write(BlueJohtoJasmine::CURE_READY, "BLUE_JOHTO_AMPHAROS_CURE_V1_READY\n")

    %w[olivine_medicine_requested cianwood_medicine_received
       olivine_returned_with_medicine].each do |key|
      flags[key] = false
      check(!BlueJohtoJasmine.deliver_medicine, "Cure bypassed prerequisite #{key}")
      flags[key] = true
    end
    flags["olivine_lighthouse_floor"] = 5
    check(!BlueJohtoJasmine.deliver_medicine, "Medicine delivered on wrong floor")
    flags["olivine_lighthouse_floor"] = 6

    $bag = nil
    check(!BlueJohtoJasmine.deliver_medicine, "Cure without bag")
    $bag = FakeBag.new
    check(!BlueJohtoJasmine.deliver_medicine, "Cure without item")
    $bag = FakeBag.new(SECRETPOTION: 1)
    $bag.mode = :fail
    check(!BlueJohtoJasmine.deliver_medicine, "Failed removal cured Ampharos")
    check(!flags.key?("olivine_ampharos_healed"), "Failed removal set healing flag")
    $bag.mode = :dishonest
    check(!BlueJohtoJasmine.deliver_medicine, "Unchanged bag count accepted as removal")
    check($bag.quantity(:SECRETPOTION) == 1, "Dishonest adapter changed medicine")
    $bag.mode = :normal
    check(BlueJohtoJasmine.deliver_medicine, "Valid medicine delivery did not work")
    check(BlueJohtoJasmine.ampharos_healed?, "Healing flag missing")
    check(flags["olivine_medicine_delivered"] == true, "Delivery flag missing")
    check($bag.quantity(:SECRETPOTION) == 0, "Medicine not consumed exactly once")
    check(!BlueJohtoJasmine.deliver_medicine, "Medicine duplicated after recovery")
    check(!BlueJohtoJasmine.gym_entrance, "Jasmine gym without STORM")
    check(!BlueJohtoJasmine.jasmine, "Jasmine battle without STORM")
    check(BlueRegions.crystal_total(state, 4) == 8, "Cure created a fake emerald")

    check(BlueRegions.award(state, "JOHTO", "STORM"), "Cannot set Chuck badge")
    check(BlueJohtoJasmine.gym_entrance, "Gym did not open after cure/STORM")
    check(!BlueJohtoJasmine.gym_entrance, "Gym entrance repeated")
    check(!BlueJohtoJasmine.jasmine, "Jasmine fought without trainer PBS")
    check(TrainerBattle.history.empty?, "Jasmine tried uncompiled trainer")
    File.write(BlueJohtoJasmine::TRAINERS_READY, "WRONG")
    check(!BlueJohtoJasmine.jasmine, "Wrong trainer marker accepted")
    File.write(BlueJohtoJasmine::TRAINERS_READY, "BLUE_JOHTO_JASMINE_V1_READY\n")
    TrainerBattle.result = false
    check(!BlueJohtoJasmine.jasmine, "Jasmine loss counted as victory")
    check(!BlueJohtoJasmine.mineral_earned?, "Mineral Badge awarded after loss")
    check(BlueRegions.crystal_total(state, 4) == 9, "Lost gym added emerald")
    TrainerBattle.result = true
    check(BlueJohtoJasmine.jasmine, "Jasmine victory did not award badge")
    check(BlueJohtoJasmine.mineral_earned?, "Mineral badge missing")
    check(BlueRegions.local_achievements(state, "JOHTO") ==
          %w[ZEPHYR HIVE PLAIN FOG STORM MINERAL], "Wrong regional badge list")
    check(BlueRegions.crystal_total(state, 4) == 10, "Mineral emerald count incorrect")
    battle_history = TrainerBattle.history.dup
    check(!BlueJohtoJasmine.jasmine, "Jasmine battle repeated")
    check(TrainerBattle.history == battle_history, "TrainerBattle started twice")
    check(!BlueJohtoJasmine.whirlpool_allowed?(true), "Mineral bypassed GLACIER")
    check(!BlueJohtoJasmine.whirl_islands_entry(true), "Islands warped with Mineral only")
    check(!flags.key?("whirl_islands_entered"), "Fake island warp flag")
    check(!flags.key?("lugia_caught"), "Legendary unlocked prematurely")
    check(BlueRegions.award(state, "JOHTO", "GLACIER"), "Cannot setup later badge")
    check(!BlueJohtoJasmine.whirlpool_allowed?, "Whirlpool bypassed field tool")
    check(BlueJohtoJasmine.whirlpool_allowed?(true), "GLACIER + tool not allowed")
    check(!BlueJohtoJasmine.whirl_islands_entry(true), "Unverified islands opened")

    $PokemonGlobal.blue_regions = Marshal.load(Marshal.dump(state))
    check(BlueJohtoJasmine.ampharos_healed?, "Healing lost on save/reload")
    check(BlueJohtoJasmine.mineral_earned?, "Mineral lost on save/reload")
    check(!BlueJohtoJasmine.deliver_medicine, "Medicine delivered again on reload")
    check(!BlueJohtoJasmine.jasmine, "Jasmine awarded again on reload")
    check($bag.quantity(:SECRETPOTION) == 0, "Save reintroduced consumed medicine")
    $PokemonGlobal.blue_regions["current"] = "KANTO"
    before = Marshal.dump($PokemonGlobal.blue_regions)
    check(!BlueJohtoJasmine.mineral_earned?, "Mineral shown in Kanto")
    check(!BlueJohtoJasmine.deliver_medicine, "Kanto replayed delivery")
    check(!BlueJohtoJasmine.jasmine, "Kanto replayed Jasmine battle")
    check(!BlueJohtoJasmine.whirlpool_allowed?(true), "Johto Whirlpool allowed in Kanto")
    check(Marshal.dump($PokemonGlobal.blue_regions) == before, "Kanto modified")
  end
end
puts "JOHTO_JASMINE_RUNTIME_OK"
