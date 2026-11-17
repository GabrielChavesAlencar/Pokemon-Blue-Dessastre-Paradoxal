# S14: actual BlueSinnohPilot, three physical ball choices, save reload,
# foreign region isolation and in-flight reentrancy under isolated fake engine.
require 'json'
load File.expand_path(ARGV.fetch(0))
load File.expand_path(ARGV.fetch(1))
manifest=JSON.parse(File.read(File.expand_path(ARGV.fetch(2))))
class S14Global
  attr_accessor :blue_regions
end
class S14Player
  attr_accessor :party
  def initialize;@party=[];end
end
$messages=[]
$grant_allowed=true
$grant_hook=nil
def _INTL(message,*_args);message;end
def pbMessage(message);$messages<<message;end
def pbAddPokemonSilent(species,level)
  return false unless $grant_allowed
  $grant_hook.call if $grant_hook
  $player.party << [species,level]
  true
end
def check(value,label)
  raise "SINNOH_S14_RUBY: #{label}" unless value
end
def fresh(region="SINNOH", initial="SINNOH")
  $PokemonGlobal=S14Global.new
  $PokemonGlobal.blue_regions={"version"=>1,"current"=>region,"initial"=>initial}
  $player=S14Player.new
  $messages.clear
  $grant_allowed=true
  $grant_hook=nil
end
contract=BlueSinnohStarterContracts
check(contract::VERIFIED_NATIVE_SOURCES.empty?,"fictitious native starter callbacks")
check(manifest["balls"].length==3,"three balls contract changed")
manifest["balls"].each do |row|
  species=row["species"]
  event=row["event_key"]
  check(contract::BALLS[species][0]==event,"event maps to wrong species")
  check(row["trigger"]=="action","walk-over ball present")
  fresh
  save=$PokemonGlobal.blue_regions
  check(contract.preview(save,species)==:rowan_not_ready,"Rowan not required")
  check(!BlueSinnohPilot.choose_starter_from_ball(species.to_sym),"early ball accepted")
  check($player.party.empty?,"early grant mutated team")
  check(BlueSinnohPilot.mother,"mother step blocked")
  check(BlueSinnohPilot.barry_intro,"Barry step blocked")
  check(BlueSinnohPilot.rowan_briefcase,"Rowan step blocked")
  check(contract.preview(save,species)==:native_event_missing,"unverified ball considered native")
  check(!contract.native_event_ready?(save,species,"fake"),"fake callback accepted")
  $grant_allowed=false
  before=Marshal.dump(save)
  check(!BlueSinnohPilot.choose_starter_from_ball(species.to_sym),"failed engine grant accepted")
  check(Marshal.dump(save)==before,"failed grant wrote save")
  $grant_allowed=true
  $grant_hook=proc do
    check(!BlueSinnohPilot.choose_starter_from_ball(:TURTWIG),
          "reentrant choice bypassed physical grant lock")
  end
  check(BlueSinnohPilot.choose_starter_from_ball(species.to_sym),
        "selected starter was blocked")
  $grant_hook=nil
  check($player.party==[[species.to_sym,5]],"wrong or duplicate starter granted")
  check(BlueSinnohPilot.starter==species.to_sym,"incorrect save species")
  check(BlueSinnohPilot.rival_species==row["rival_species"].to_sym,
        "counterstarter drift")
  check(BlueSinnohPilot.rival_version==row["rival_pbs_version"],
        "Barry version drift")
  check(contract.preview(save,species)==:already_selected,"own ball not marked chosen")
  contract::BALLS.keys.each do |other|
    next if other==species
    check(contract.preview(save,other)==:other_selected,"second ball visually available")
    check(!BlueSinnohPilot.choose_starter_from_ball(other.to_sym),
          "second starter physically granted")
  end
  saved=Marshal.dump(save)
  $PokemonGlobal.blue_regions=Marshal.load(saved)
  check(BlueSinnohPilot.starter==species.to_sym,"save/load lost starter")
  check(contract.preview($PokemonGlobal.blue_regions,species)==:already_selected,
        "save reload permits duplicate")
  state=$PokemonGlobal.blue_regions
  %w[KANTO JOHTO HOENN DECADES].each do |region|
    state["current"]=region
    snapshot=Marshal.dump(state)
    check(contract.preview(state,species)==:wrong_region,"foreign region exposes balls")
    check(!BlueSinnohPilot.choose_starter_from_ball(:PIPLUP),"foreign region granted")
    check(Marshal.dump(state)==snapshot,"foreign region save polluted")
  end
  state["current"]="SINNOH"
  check(contract.preview(state,species)==:already_selected,
        "return from travel reopens ball")
  check(!BlueSinnohPilot.choose_starter_from_ball(species.to_sym),
        "returning to Sinnoh duplicating ball")
  state["sinnoh_pilot"]["starter"]="PIKACHU"
  check(contract.preview(state,species)==:invalid_flags,"forged starter accepted")
  check(!BlueSinnohPilot.choose_starter_from_ball(species.to_sym),"tampered save gave starter")
end
fresh("KANTO")
check(contract.preview($PokemonGlobal.blue_regions,"TURTWIG")==:wrong_region,
      "Kanto not rejected")
fresh("SINNOH","HOENN")
check(contract.preview($PokemonGlobal.blue_regions,"TURTWIG")==:foreign_initial,
      "foreign initial save not rejected")
check(contract.preview($PokemonGlobal.blue_regions,"MAGIKARP")==:unknown_species,
      "unknown species accepted")
puts "SINNOH_S14_THREE_BALL_SAVE_REGION_RUNTIME_OK_OFFLINE"
