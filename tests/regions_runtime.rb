# No game, save, graphics, or external dependencies are loaded.
def check(value, description)
  raise description unless value
end

class PokemonGlobalMetadata; end
require ARGV.fetch(0)
require ARGV.fetch(1)

ring = %w[DECADES KANTO JOHTO HOENN SINNOH UNOVA KALOS ALOLA GALAR PALDEA]
ring.each_with_index do |region, i|
  s = BlueRegions.new_state(region)
  check(BlueRegions.unlocked(s) == [region], "initial #{region}")
  check(!BlueRegions.complete_league(s, ring[i-1]), "foreign league")
  check(BlueRegions.complete_league(s, region), "complete #{region}")
  check(BlueRegions.unlocked(s).sort == [region, ring[i-1], ring[(i+1)%10]].sort, "neighbors #{region}")
  check(!BlueRegions.complete_league(s, region), "duplicate #{region}")
  check(!BlueRegions.world_champion?(s), "premature world champion")
end
s = BlueRegions.new_state
ring.each do |region|
  check(BlueRegions.unlocked(s).include?(region), "forward circuit #{region}")
  s["current"] = region
  check(BlueRegions.complete_league(s, region), "complete #{region}")
end
check(BlueRegions.world_champion?(s), "all ten leagues")
check(BlueRegions.profile(s, true) == :world_champion_rematch, "verified rematch")
check(BlueRegions.profile(s, false) == :first_clear, "no invented rematch")
check(!BlueRegions.unlocked(s).include?("HISUI"), "no automatic Hisui")
s["current"] = "SINNOH"
check(BlueRegions.unlock_hisui_quest(s) && BlueRegions.unlocked(s).include?("HISUI"), "Sinnoh quest")

h = BlueRegions.new_state("HISUI")
check(!BlueRegions.allow_specials?(h, "HISUI"), "Hisui before ending")
check(!BlueRegions.complete_league(h, "HISUI"), "no Hisui league")
check(BlueRegions.finish_hisui(h), "Hisui ending")
check(BlueRegions.unlocked(h).sort == %w[DECADES HISUI SINNOH], "Hisui exits")
check(BlueRegions.allow_specials?(h, "HISUI"), "Hisui after ending")
check(BlueRegions.crystal_total(h, 3) == 3, "Hisui does not give crystal")

s = BlueRegions.new_state("KANTO")
check(BlueRegions.field_access(s, "KANTO", "SURF", true) == :badge, "regional badge required")
check(BlueRegions.award(s, "KANTO", "SOUL"), "first award")
check(!BlueRegions.award(s, "KANTO", "SOUL"), "duplicate award")
check(!BlueRegions.award(s, "JOHTO", "FOG"), "foreign award")
check(BlueRegions.crystal_total(s, 7) == 8, "global progress")
check(BlueRegions.field_access(s, "KANTO", "SURF") == :tool, "tool required")
check(BlueRegions.field_access(s, "KANTO", "SURF", true) == :allowed, "regional surf")
check(BlueRegions.field_access(s, "JOHTO", "SURF", true) == :badge, "other region denied")
check(BlueRegions.field_access(s, "DECADES", "SURF", true) == :native, "Decades retains native rule")
check(BlueRegions.field_access(s, "UNOVA", "SURF", true) == :event, "Unova story prerequisite")
s["field_events"]["UNOVA"] = ["SURF_LOCAL"]
check(BlueRegions.field_access(s, "UNOVA", "SURF", true) == :allowed, "Unova no badge")
check(!BlueRegions.allow_specials?(s, "KANTO"), "eight required")
BlueRegions.info("KANTO")["milestones"].each { |badge| BlueRegions.award(s, "KANTO", badge) }
check(BlueRegions.allow_specials?(s, "KANTO"), "eight unlock specials")
check(BlueRegions.field_access(s, "JOHTO", "ROCK_CLIMB", true) == :allowed, "HGSS Earth Badge")

Pkmn = Struct.new(:special, :egg?, :fainted?)
normal, special, fainted = Pkmn.new(false,false,false), Pkmn.new(true,false,false), Pkmn.new(false,false,true)
party = [normal,special]
classify = proc { |pkmn| pkmn.special }
check(BlueRegions.transfer_plan(s, "JOHTO", party, [[0,0]], &classify) == [:locked,[]], "locked destination")
BlueRegions.complete_league(s, "KANTO")
check(BlueRegions.transfer_plan(s, "JOHTO", party, [], &classify) == [:box_full,[]], "full boxes")
check(BlueRegions.transfer_plan(s, "JOHTO", [fainted,special], [[0,0]], &classify) == [:no_usable_party,[]], "no usable party")
check(BlueRegions.transfer_plan(s, "JOHTO", party, [[0,0]], &classify) == [:ok,[[special,[0,0]]]], "preserve identity and slot")
check(party == [normal,special], "preview does not mutate party")

$PokemonGlobal = PokemonGlobalMetadata.new
$player = Struct.new(:badges).new(Array.new(20,false))
$game_switches = Hash.new(false)
check(BlueRegions.snapshot["initial"] == "DECADES", "legacy save defaults")
$player.badges[18] = true
check(BlueRegions.snapshot["leagues"].empty?, "emerald without finishing cutscene")
$game_switches[122] = true
expected = BlueRegionData::DECADES_VERIFIED ? ["DECADES"] : []
check(BlueRegions.snapshot["leagues"] == expected, "only audited ending recognized")
check($PokemonGlobal.blue_regions.nil?, "legacy save is never modified by snapshot")
$PokemonGlobal.blue_regions = {"version"=>99}
check(BlueRegions.snapshot.nil?, "newer schema never overwritten")
puts "Blue regional progression OK"
