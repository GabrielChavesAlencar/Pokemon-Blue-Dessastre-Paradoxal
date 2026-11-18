# Isolated runtime contracts for FRLG source Map039/053/054/055.
# Does not access real saves, Android, Game.exe or source map archives.
require "tmpdir"
require "fileutils"

source = File.expand_path(ARGV.fetch(0))
def check(v, msg)
  raise "KANTO_CERULEAN_NORTH: #{msg}" unless v
end
class Game_Player; end
module MenuHandlers
  def self.add(*); end
end
module BlueRegions
  def self.new_state(region)
    {"current"=>region,"pilot_wins"=>[]}
  end
  def self.local_achievements(*); ["CASCADE"]; end
end
module BlueLocale
  def self.enabled?; true; end
  def self.with_raw; yield; end
end
def _INTL(str, *args)
  str.gsub(/\{(\d+)\}/) { args[$1.to_i - 1].to_s }
end
$messages = []
$battle_results = []
$called_battles = []
$confirmation = false
def pbMessage(msg, *); $messages << msg; end
def pbConfirmMessage(*); $confirmation; end
def setBattleRule(rule); ($rules ||= []) << rule; end
module GameData
  class Trainer
    def self.exists?(type, name, v)
      (type == :BLUE_KANTO_RIVAL && name == "Blue" && [31,32,33].include?(v)) ||
        (type == :BLUE_KANTO_ROCKET && name == "Grunt" && v == 5)
    end
  end
  class Item
    def self.exists?(sym); [:NUGGET, :SSTICKET].include?(sym); end
  end
end
class TrainerBattle
  def self.start(type, name, v)
    $called_battles << [type,name,v]
    result = $battle_results.shift
    raise "Android native battle failed" if result == :error
    result
  end
end
class FakeTemp
  def clear_battle_rules; @cleared = true; end
end
class FakeMap
  attr_accessor :need_refresh, :map_id, :events
  def initialize(mid, ids)
    @map_id = mid
    @events = ids.to_h { |id| [id,Object.new] }
    @need_refresh = false
  end
end
class FakeBag
  attr_accessor :full
  attr_reader :counts
  def initialize; @counts = Hash.new(0); @full = false; end
  def add(item, quantity)
    return false if @full
    @counts[item] += quantity
    true
  end
  def has?(item); @counts[item] > 0; end
end
class FakePlayer
  def name; "Tester"; end
end

Dir.mktmpdir("cerulean-north-fixture") do |folder|
  Dir.chdir(folder) do
    FileUtils.mkdir_p("Data")
    File.write("Data/blue-kanto-install.json", '{"maps":{"39":501,"53":502,"54":503,"55":504}}')
    load source
    $PokemonGlobal = Struct.new(:blue_regions).new(BlueRegions.new_state("KANTO"))
    $PokemonGlobal.blue_regions["pilot_starter"] = "BULBASAUR"
    $player = FakePlayer.new
    $bag = FakeBag.new
    $game_temp = FakeTemp.new
    $game_self_switches = {}
    $game_map = FakeMap.new(501,[15,32,34])
    $rules = []

    # Three paths share one Kanto win and retry if the player loses.
    $battle_results = [false, true]
    check(!BlueKantoPilot.cerulean_rival, "defeat unexpectedly completed encounter")
    check(!$PokemonGlobal.blue_regions["pilot_cerulean_rival"], "loss set story flag")
    check($game_self_switches.empty?, "loss closed the bridge")
    check(BlueKantoPilot.cerulean_rival, "retry win failed")
    check($called_battles.length == 2, "Gary should battle once per attempt")
    check($called_battles.last == [:BLUE_KANTO_RIVAL,"Blue",31], "wrong starter rival version")
    check([15,32,34].all? { |id| $game_self_switches[[501,id,"A"]] }, "three crossing lanes not closed")
    check(BlueKantoPilot.cerulean_rival, "finished rival not idempotent")
    check($called_battles.length == 2, "rival replayed after victory")

    # The Nugget Rocket cannot be farmed by repeatedly losing or speaking.
    $game_map = FakeMap.new(502,[6])
    $battle_results = [false,true]
    check(!BlueKantoPilot.nugget_rocket, "lost Nugget battle returned success")
    check($bag.counts[:NUGGET] == 0, "Nugget awarded before victory")
    $bag.full = true
    check(!BlueKantoPilot.nugget_rocket, "full Bag granted Nugget")
    check($PokemonGlobal.blue_regions["pilot_wins"].include?("KANTO_053_006"), "Rocket real win lost")
    check($bag.counts[:NUGGET] == 0, "Bag-full duplicated Nugget")
    $bag.full = false
    check(BlueKantoPilot.nugget_rocket, "cannot claim earned Nugget")
    check(BlueKantoPilot.nugget_rocket, "repeat Nugget talks must be safe")
    check($bag.counts[:NUGGET] == 1, "Nugget duplicated")
    check($called_battles.length == 4, "Rocket battle replayed after victory")

    # Bill cannot dispense ticket before helping him.
    $game_map = FakeMap.new(504,[3,4,8])
    check(!BlueKantoPilot.bill_machine, "PC worked without Bill asking")
    check(!BlueKantoPilot.bill_ticket, "ticket issued before Bill restored")
    $confirmation = false
    check(!BlueKantoPilot.bill_request, "declined Bill request persisted")
    $confirmation = true
    check(BlueKantoPilot.bill_request, "accepted Bill request missing")
    check(BlueKantoPilot.bill_machine, "PC did not restore Bill")
    check([3,8].all? {|id| $game_self_switches[[504,id,"A"]]}, "Bill sprite states invalid")
    check(BlueKantoPilot.bill_ticket, "Bill did not give ticket")
    check(BlueKantoPilot.bill_ticket, "ticket repeat unsafe")
    check($bag.counts[:SSTICKET] == 1, "S.S. Ticket duplicated")

    # Older saves with a ticket remain valid even if the quest was absent.
    $PokemonGlobal.blue_regions["pilot_ss_ticket"] = true
    $PokemonGlobal.blue_regions["pilot_bill_separated"] = false
    BlueKantoPilot.ticketmaster
    check($PokemonGlobal.blue_regions["pilot_ss_ticket"], "legacy ticket was revoked")
    check($bag.counts[:SSTICKET] == 1, "harbor granted a duplicate ticket")

    # Kanto-only callback is inert on other regions.
    $PokemonGlobal.blue_regions["current"] = "JOHTO"
    before = $called_battles.length
    check(!BlueKantoPilot.cerulean_rival, "cross-region Gary executed")
    check($called_battles.length == before, "cross-region battle was started")
  end
end
puts "PASS: Gary (all north crossing tiles), Nugget, Bill, item idempotency, save boundaries"
