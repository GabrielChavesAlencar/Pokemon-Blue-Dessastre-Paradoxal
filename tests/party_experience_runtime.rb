# Native EXP_ALL adapter regression. No ROM/Essentials assets or save files.
# The mock base battle mirrors Essentials 21.1's existing 100%/50% policy;
# the REAL BluePartyExperience adapter must select that path exactly once.
require "tmpdir"

plugin = File.expand_path(ARGV.fetch(0))
def verify(value, message)
  raise "PARTY_EXP_REGRESSION: #{message}" unless value
end

class PartyMember
  attr_accessor :exp, :ev, :fainted, :egg
  attr_reader :name, :max_exp
  def initialize(name, max_exp = 999)
    @name, @max_exp = name, max_exp
    @exp = @ev = 0
    @fainted = @egg = false
  end
  def eligible?
    !@fainted && !@egg
  end
end
class Player
  attr_accessor :has_exp_all
  def initialize(value = false); @has_exp_all = value; end
end
class Bag
  attr_accessor :expall
  def initialize; @expall = false; end
  def has?(item); item == :EXPALL && @expall; end
end
module BlueBattleOptions
  def self.battle_area?; @battle_area || false; end
  def self.battle_area=(state); @battle_area = state; end
end
module BlueBattleLab
  ACTIVE = false
end

class Battle
  attr_accessor :internalBattle, :expGain, :parties, :participants, :caught,
                :native_calls, :raise_on_gain
  def initialize
    @internalBattle = true
    @expGain = true
    @parties = []
    @participants = []
    @caught = false
    @native_calls = 0
  end
  def pbGainExp
    @native_calls += 1
    raise "native EXP failure" if @raise_on_gain
    return if !@internalBattle || !@expGain
    all = $player.has_exp_all || $bag.has?(:EXPALL)
    @parties.each_with_index do |p, i|
      next if !p.eligible? || p.exp >= p.max_exp
      participant = @participants.include?(i)
      next unless participant || all
      amount = participant ? 100 : 50
      # Simulates base Essentials' level cap and per-member EV distribution.
      p.exp = [p.exp + amount, p.max_exp].min
      p.ev += 1
    end
    :native_result
  end
end

load plugin
BluePartyExperience.install
BluePartyExperience.install
verify(Battle.ancestors.count(BluePartyExperience::NativeExpAll) == 1,
       "adapter installed twice")

Dir.mktmpdir("blue-party-exp-") do |dir|
  Dir.chdir(dir) do
    $player = Player.new(false)
    $bag = Bag.new
    battle = Battle.new
    active = PartyMember.new("Pidgey")
    bench = PartyMember.new("Bulbasaur")
    fainted = PartyMember.new("Squirtle"); fainted.fainted = true
    egg = PartyMember.new("Egg"); egg.egg = true
    maxed = PartyMember.new("Max level", 0)
    boxed = PartyMember.new("Boxed")
    battle.parties = [active, bench, fainted, egg, maxed]
    battle.participants = [0]
    verify(battle.pbGainExp == :native_result, "native EXP method was replaced")
    verify([active.exp, bench.exp, fainted.exp, egg.exp, maxed.exp, boxed.exp] ==
           [100, 50, 0, 0, 0, 0], "active 100% / bench 50% / invalid zero")
    verify([active.ev, bench.ev, fainted.ev, egg.ev, maxed.ev, boxed.ev] ==
           [1, 1, 0, 0, 0, 0], "native EV distribution was overridden")
    verify(battle.native_calls == 1, "duplicate native EXP award")
    verify($player.has_exp_all == false, "saved EXP_ALL property was modified")

    # More than one participant: all eligible participants are rewarded.
    battle.participants = [0, 1]
    battle.pbGainExp
    verify(active.exp == 200 && bench.exp == 150, "participants lost EXP")
    verify(battle.native_calls == 2, "native EXP invoked more than once")
    verify($player.has_exp_all == false, "EXP_ALL flag leaked to save")

    # Existing purchased EXPALL does not stack a second grant.
    $bag.expall = true
    battle.participants = [0]
    battle.pbGainExp
    verify(active.exp == 300 && bench.exp == 200, "owned EXPALL was stacked")
    $bag.expall = false

    # Permanently unlocked Exp All remains as it was.
    $player.has_exp_all = true
    battle.pbGainExp
    verify($player.has_exp_all, "existing EXP_ALL entitlement lost")
    $player.has_exp_all = false

    # Native rules for capture are preserved, provided the base calls pbGainExp.
    battle.caught = true
    battle.pbGainExp
    verify(bench.exp == 300, "capture reward did not follow native EXP path")

    # Battle Lab, arena, external PvP, and explicit no-EXP battles are isolated.
    baseline = bench.exp
    $player.has_exp_all = false
    battle.expGain = false
    battle.pbGainExp
    verify(bench.exp == baseline, "no-EXP battle rewarded EXP")
    battle.expGain = true

    battle.internalBattle = false
    battle.pbGainExp
    verify(bench.exp == baseline, "PvP rewarded EXP")
    battle.internalBattle = true

    battle.instance_variable_set(:@blue_lab_battle, true)
    battle.pbGainExp
    verify(bench.exp == baseline, "Battle Lab rewarded party EXP")
    battle.instance_variable_set(:@blue_lab_battle, false)

    BlueBattleOptions.battle_area = true
    battle.pbGainExp
    verify(bench.exp == baseline, "Battle Arena leaked EXP sharing")
    BlueBattleOptions.battle_area = false

    # Earlier Ruby methods and exceptions must never leave Exp All on.
    battle.raise_on_gain = true
    begin
      battle.pbGainExp
      raise "native exception not raised"
    rescue RuntimeError => e
      verify(e.message == "native EXP failure", "native error was swallowed")
    end
    verify($player.has_exp_all == false, "EXP_ALL flag not restored after exception")
  end
end
puts "PASS: modern party EXP native 100/50, fainted/eggs/boxes excluded, no double award, saved flags intact, battle modes isolated"
