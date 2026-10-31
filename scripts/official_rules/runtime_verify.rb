# An opt-in diagnostic. Normal launches have no diagnostic side effects.
module BlueOfficialRules
  def self.verify
    lines = []
    checks = []
    check = proc do |name, actual, expected|
      passed = (actual == expected)
      checks << passed
      lines << "#{passed ? 'PASS' : 'FAIL'} | #{name} | #{actual.inspect}"
    end
    GameData.load_all
    stats = [:HP, :ATTACK, :DEFENSE, :SPEED, :SPECIAL_ATTACK, :SPECIAL_DEFENSE]
    bulba = GameData::Species.get(:BULBASAUR)
    check.call('Bulbasaur stats', stats.map { |s| bulba.base_stats[s] }, [45,49,49,45,65,65])
    check.call('Bulbasaur ability', bulba.abilities, [:OVERGROW])
    check.call('Bulbasaur hidden ability', bulba.hidden_abilities, [:CHLOROPHYLL])
    check.call('Bulbasaur EV yield', bulba.evs[:SPECIAL_ATTACK], 1)
    check.call('Bulbasaur catch rate', bulba.catch_rate, 45)
    check.call('Charmeleon type', GameData::Species.get(:CHARMELEON).types, [:FIRE])
    check.call('Blastoise type', GameData::Species.get(:BLASTOISE).types, [:WATER])
    check.call('Tackle power', GameData::Move.get(:TACKLE).power, 40)
    check.call('Stealth Rock type', GameData::Move.get(:STEALTHROCK).type, :ROCK)
    check.call('Torch Song power', GameData::Move.get(:TORCHSONG).power, 80)
    check.call('Electro Drift power', GameData::Move.get(:ELECTRODRIFT).power, 100)
    check.call('Sleep mechanics', Settings::SLEEP_EFFECTS_CAUSE_DROWSY, false)
    check.call('Freeze mechanics', Settings::FREEZE_EFFECTS_CAUSE_FROSTBITE, false)
    check.call('Snow mechanics', Settings::HAIL_WEATHER_TYPE, 1)
    check.call('Separate EVs', Settings::PURIST_MODE, true)
    check.call('Total EV limit', Pokemon::EV_LIMIT, 510)
    check.call('Individual EV limit', Pokemon::EV_STAT_LIMIT, 252)

    # Exercise actual loaded battle methods with small dependency stubs.
    user = Object.new
    def user.abilityActive?; false; end
    def user.selectedMoveIsZMove; false; end
    def user.pbTypes(*args); [:FIRE]; end
    def user.pbHasType?(type); type == :FIRE; end
    def user.effects; Hash.new(false); end
    field = Struct.new(:effects).new(Hash.new(false))
    battle = Struct.new(:field).new(field)
    tackle = Battle::Move.from_pokemon_move(battle, Pokemon::Move.new(:TACKLE))
    check.call('Fire user retains Normal Tackle', tackle.pbCalcType(user), :NORMAL)
    counter = Battle::Move::CounterPhysicalDamage.allocate
    counter_user = Struct.new(:effects).new({ PBEffects::Counter => 10 })
    check.call('Counter multiplier', counter.pbFixedDamage(counter_user, nil), 20)
    mults = { :power_multiplier => 1.0 }
    slicing_move = Object.new
    def slicing_move.slicingMove?; true; end
    Battle::AbilityEffects.triggerDamageCalcFromUser(:SHARPNESS, user, nil, slicing_move, mults, 40, :NORMAL)
    check.call('Sharpness multiplier', mults[:power_multiplier], 1.5)
    lines << "RESULT=#{checks.all? ? 'PASS' : 'FAIL'}"
    File.binwrite('Data/blue-official-validation.txt', lines.join("\n") + "\n")
    File.delete('Data/blue-verify-request.txt') if checks.all?
  rescue Exception => error
    lines ||= []
    lines << "RESULT=ERROR | #{error.class}: #{error.message}"
    lines.concat(error.backtrace || [])
    File.binwrite('Data/blue-official-validation.txt', lines.join("\n") + "\n")
  end
end

if $DEBUG && File.file?('Data/blue-verify-request.txt')
  module Compiler
    class << self
      alias blue_official_original_main main
      def main
        blue_official_original_main
        BlueOfficialRules.verify
        exit
      end
    end
  end
end
