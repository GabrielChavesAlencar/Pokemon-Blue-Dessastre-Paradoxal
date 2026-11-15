# Offline regression for the *actual* BlueCampaign defaults. No Game.exe/saves.
class PokemonGlobalMetadata
  attr_accessor :blue_regions, :blue_campaign_started, :blue_campaign_departure,
                :blue_campaign_mechanics
end
class FakeBag
  attr_reader :clears
  def initialize; @clears=0; end
  def clear; @clears+=1; end
end
module BlueBattleOptions
  def self.defaults
    {"tera"=>true,"dynamax"=>true,"mega"=>true,"zmove"=>true}
  end
  def self.mechanics_menu(*)
    raise "Campaign opened the unwanted mechanics menu"
  end
end
module BlueStory
  def self.story?; true; end
  def self.current_region; $PokemonGlobal.blue_regions["current"]; end
end
def check(label,condition)
  raise "FAIL #{label}" unless condition
end
load ARGV.fetch(0)
$bag=FakeBag.new
$PokemonGlobal=PokemonGlobalMetadata.new
$PokemonGlobal.blue_regions={"current"=>"DECADES"}
check("Decades defaults",BlueCampaign.default_mechanics_for("DECADES")==
      {"tera"=>true,"dynamax"=>false,"mega"=>true,"zmove"=>true})
check("Kanto defaults remain separate",BlueCampaign.default_mechanics_for("KANTO")==
      BlueBattleOptions.defaults)
BlueCampaign.begin_journey(true)
check("Decades mechanics initialized silently",
      $PokemonGlobal.blue_campaign_mechanics==
      {"tera"=>true,"dynamax"=>false,"mega"=>true,"zmove"=>true})
check("Journey set up",$PokemonGlobal.blue_campaign_started && $bag.clears==1)
$PokemonGlobal.blue_campaign_mechanics["zmove"]=false
BlueCampaign.begin_journey(true)
check("Existing preferences not overwritten",
      $PokemonGlobal.blue_campaign_mechanics["zmove"]==false && $bag.clears==1)
$PokemonGlobal=PokemonGlobalMetadata.new
$PokemonGlobal.blue_regions={"current"=>"KANTO"}
BlueCampaign.begin_journey(false)
check("Kanto not disabled by Decades",
      $PokemonGlobal.blue_campaign_mechanics==BlueBattleOptions.defaults)
puts "PASS: Decades story defaults Mega/Z/Tera ON, Dynamax OFF; no menu; Kanto unchanged"
