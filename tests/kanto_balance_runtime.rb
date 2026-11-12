# Pure Ruby regression for opponent/wild levels in both Decades and Kanto.
# The shared BlueCampaign hook is regional-neutral and uses global stage.
module BlueStory
  class << self; attr_accessor :test_stage; end
  def self.stage; test_stage; end
end
module GameData
  module GrowthRate
    def self.max_level; 100; end
  end
end
def check(value,message)
  raise message unless value
end
require ARGV.fetch(0)
require ARGV.fetch(1)
Pkmn = Struct.new(:level, :egg?)
party = [Pkmn.new(50,false),Pkmn.new(83,true),Pkmn.new(20,false)]
[0,1,2].each do |stage|
  BlueStory.test_stage = stage
  check(BlueCampaign.common_level(party) == 35,
        "Kanto/Decades stages 0-2 must scale opponents to 70% of top non-egg level")
end
BlueStory.test_stage = 3
check(BlueCampaign.common_level(party) == 45,
      "Kanto/Decades Master opponents must scale to 90% of top non-egg level")
check(BlueCampaign.wild_level(party) == 22,
      "Wild Kanto/Decades Pokémon use shared 45% encounter rule")
check(BlueCampaign.scaled_level([Pkmn.new(2,false)],70) == 1,
      "Level scaling must not produce level zero")
check(BlueTrainerMoves::CAPS == [60,90,nil,nil],
      "Shared move-power caps changed unexpectedly")
puts "Kanto uses identical 70/90 trainer and 45% wild level rules"
