# Standalone guard: first regional bosses must not receive BST/base-power caps.
# Requires no game assets, no save and no native engine.
class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
module Compiler
  def self.main; end
end
module BlueBattleOptions
  def self.battle_area?; false; end
end
load File.expand_path(ARGV.fetch(0))
load File.expand_path(ARGV.fetch(1))

Trainer = Struct.new(:trainer_type)
def check(condition, message)
  raise message unless condition
end
global = PokemonGlobalMetadata.new
$PokemonGlobal = global
leader = Trainer.new(:BLUE_KANTO_LEADER)
elite = Trainer.new(:BLUE_KANTO_ELITE_LORELEI)
champion = Trainer.new(:BLUE_KANTO_CHAMPION_BLUE)
normal = Trainer.new(:BLUE_KANTO_LASS)
rocket = Trainer.new(:BLUE_KANTO_ROCKETBOSS)

global.blue_regions = {"current" => "DECADES"}
check(!BlueStory.regional_first_boss?([leader]), "Decades must retain original caps")
global.blue_regions["current"] = "KANTO"
[leader, elite, champion].each do |trainer|
  check(BlueStory.regional_first_boss?([trainer]), "first regional boss must be exempt")
end
check(!BlueStory.regional_first_boss?([normal]), "regular trainer still uses caps")
check(!BlueStory.regional_first_boss?([rocket]), "Rocket boss is not an initial Gym/Elite/Champion")
check(BlueStory.with_regional_full_power {
  !BlueStory.regional_first_boss?([leader]) && BlueStory.regional_full_power?
}, "Full Power rematch must restore both caps")
check(!BlueStory.regional_full_power?, "Full Power mode must be scoped")
begin
  BlueStory.with_regional_full_power { raise "intentional" }
rescue RuntimeError
end
check(!BlueStory.regional_full_power?, "exception must restore the previous mode")
battle = Object.new
battle.instance_variable_set(:@blue_story_regional_exempt, true)
check(BlueTrainerMoves.apply(battle).nil?, "base-power adapter must skip initial regional boss")
puts "PASS: regional first boss exemption + Full Power + Decades + safe context restoration"
