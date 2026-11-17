# S18: execute the REAL EvolutionScaling WildEncounters adapter, using
# synthetic CH12 species and encounters. Never write PBS or a player's save.
fixture = ARGV.shift
raise 'S18 requires the CH12 runtime fixture' unless fixture
load File.expand_path(fixture)

def s18_check(condition, label)
  raise "SINNOH_S18: #{label}" unless condition
end

$PokemonGlobal.blue_story_mode = :story
$PokemonGlobal.blue_traditional_starters = true
$PokemonGlobal.blue_regions = BlueRegions.new_state('SINNOH')
$player.badge_count = 0
$player.party = [Pokemon.new(:TURTWIG, 40), Pokemon.new(:SUPPORT, 99, true)]
s18_check(BlueEvolutionScaling.active?, 'Sinnoh story evolution not active')
s18_check(BlueEvolutionScaling.progress_level == 40,
          'egg incorrectly raised wild progress')
s18_check(BlueCampaign.trainer_level(nil) == 28,
          'wild progress wrongly replaced 70% trainer levels')

# No badge-derived numeric cap exists. These are thresholds from the real
# native Species.get_evolutions(true), plus Blue's five-level grace.
s18_check(BlueEvolutionScaling.available_wild_species(:SHINX, 19) == [:SHINX],
          'Shinx evolved before threshold 20')
s18_check(BlueEvolutionScaling.available_wild_species(:SHINX, 20) == [:SHINX, :LUXIO],
          'Luxio absent after threshold 20')
s18_check(BlueEvolutionScaling.available_wild_species(:TURTWIG, 36) ==
          [:TURTWIG, :GROTLE], 'Torterra available before threshold 37')
s18_check(BlueEvolutionScaling.available_wild_species(:TURTWIG, 37) ==
          [:TURTWIG, :GROTLE, :TORTERRA], 'second evolution not available at 37')
s18_check(BlueEvolutionScaling.available_wild_species(:EEVEE, 90) == [:EEVEE],
          'ambiguous Eevee evolution was auto-selected')
s18_check(BlueEvolutionScaling.available_wild_species(:IRON_TEST, 90) ==
          [:IRON_TEST], 'special/paradox species evolved automatically')

# Chances: 0-4 levels beyond threshold 15%, 5-14 30%, 15-24 45%,
# 25+ 60%. Keep every original species slot at every progress level.
[
  [19, 0, 0], [20, 15, 20], [24, 15, 20],
  [25, 30, 20], [34, 30, 20], [35, 45, 20],
  [44, 45, 20], [45, 60, 20], [99, 60, 20]
].each do |cap, chance, evolved_level|
  threshold = 20
  s18_check(BlueEvolutionScaling.wild_chance(cap, threshold) == chance,
            "cap #{cap}: wrong chance #{chance}")
  if chance.zero?
    s18_check(BlueEvolutionScaling.wild_option(:SHINX, 6, cap, proc { 0 }) ==
              [:SHINX, 6], "cap #{cap}: evolved below threshold")
  else
    s18_check(BlueEvolutionScaling.wild_option(:SHINX, 6, cap,
              proc { chance - 1 }) == [:LUXIO, evolved_level],
              "cap #{cap}: accepted RNG boundary changed")
    s18_check(BlueEvolutionScaling.wild_option(:SHINX, 6, cap,
              proc { chance }) == [:SHINX, 6],
              "cap #{cap}: rejected RNG boundary changed")
  end
end

# Native 3-stage evolution can take two consecutive independent rolls,
# but it must respect both thresholds. Failing the second roll retains
# the middle stage rather than rewriting the encounter source.
s18_check(BlueEvolutionScaling.wild_option(:TURTWIG, 6, 36,
          proc { 0 }) == [:GROTLE, 23], 'Torterra before stage-2 threshold')
s18_check(BlueEvolutionScaling.wild_option(:TURTWIG, 6, 37,
          proc { 0 }) == [:TORTERRA, 37], 'two-stage evolution unavailable')
rolls = [0, 99]
s18_check(BlueEvolutionScaling.wild_option(:TURTWIG, 6, 37,
          proc { |_| rolls.shift }) == [:GROTLE, 23],
          'failed second RNG roll removed the original middle stage')
s18_check(rolls.empty?, 'wild evolution did not roll per stage')

# Stone/trade/friendship are offered only at the documented thresholds;
# unknown methods, ambiguous stone branches and special Pokémon fail closed.
s18_check(BlueEvolutionScaling.wild_option(:ROSELIA, 15, 29,
          proc { 0 }) == [:ROSELIA, 15], 'Roselia before stone level')
s18_check(BlueEvolutionScaling.wild_option(:ROSELIA, 15, 30,
          proc { 0 }) == [:ROSERADE, 30], 'Roselia stone threshold missed')
s18_check(BlueEvolutionScaling.wild_option(:GRAVELER, 20, 40,
          proc { 0 }) == [:GOLEM, 40], 'trade threshold missed')
s18_check(BlueEvolutionScaling.wild_option(:EEVEE, 15, 90,
          proc { 0 }) == [:EEVEE, 15], 'ambiguous Eevee branch chosen')
s18_check(BlueEvolutionScaling.wild_option(:IRON_TEST, 15, 90,
          proc { 0 }) == [:IRON_TEST, 15], 'paradox species altered')
PBDayNight.day = false
s18_check(BlueEvolutionScaling.wild_option(:RIOLU, 15, 50,
          proc { 0 }) == [:RIOLU, 15], 'day-only evolution offered at night')
PBDayNight.day = true
s18_check(BlueEvolutionScaling.wild_option(:RIOLU, 15, 50,
          proc { 0 }) == [:LUCARIO, 45], 'friendship threshold blocked in daytime')

# S18 guard: malformed or out-of-range encounter slot MUST stay unchanged;
# do not use a negative/invalid cap to create higher-level evolutions.
[
  [:SHINX, 0, 50], [:SHINX, -1, 50], [:SHINX, 1.5, 50],
  [:SHINX, 50, 20], [:SHINX, 6, nil], [:SHINX, 6, '50'],
  [:SHINX, 6, -1], [:SHINX, 6, 101], [:SHINX, 101, 101]
].each do |species, original_level, cap|
  original = [species, original_level]
  s18_check(BlueEvolutionScaling.wild_option(species, original_level, cap,
            proc { raise 'invalid RNG called' }) == original,
            "invalid level/cap changed original encounter #{original.inspect}/#{cap}")
end

# The actual PokemonEncounters#choose_wild_pokemon prepend must preserve
# encounter type, extra native metadata, the slot source and random tables.
class S18SyntheticNativeEncounters
  attr_accessor :slot
  def choose_wild_pokemon(_kind, _rolls = 1)
    @slot
  end
end
S18SyntheticNativeEncounters.prepend(BlueEvolutionScaling::WildEncounters)
encounters = S18SyntheticNativeEncounters.new
slot = [:SHINX, 6, :original_encounter_metadata, 77]
encounters.slot = slot
$player.party = [Pokemon.new(:TURTWIG, 19)]
result = encounters.choose_wild_pokemon(:Land, 1)
s18_check(result == slot && result != nil, 'wild hook ignored uneligible encounter')
s18_check(slot == [:SHINX, 6, :original_encounter_metadata, 77],
          'native encounter slot was mutated')
$player.party = [Pokemon.new(:TURTWIG, 50), Pokemon.new(:SUPPORT, 99, true)]
result = encounters.choose_wild_pokemon(:Cave, 1)
s18_check(result[0] == :SHINX || result[0] == :LUXIO,
          'encounter hook fabricated species')
s18_check(result[1] == 6 || result[1] == 20,
          'encounter hook assigned wrong evolved level')
s18_check(result[2..-1] == slot[2..-1] && slot[0..1] == [:SHINX, 6],
          'encounter metadata/slot source changed')
$PokemonGlobal.blue_story_mode = :battle
s18_check(encounters.choose_wild_pokemon(:Land, 1).equal?(slot),
          'battle mode modified wild result')
$PokemonGlobal.blue_story_mode = :story

# Shared global rule remains consistent in every installed region without
# relocating the Sinnoh area/PBS species into another region's maps.
%w[KANTO HOENN JOHTO DECADES].each do |region|
  $PokemonGlobal.blue_regions = BlueRegions.new_state(region)
  $player.party = [Pokemon.new(:TURTWIG, 35)]
  s18_check(BlueEvolutionScaling.progress_level == 35,
            "#{region}: highest non-egg level changed")
  s18_check(BlueEvolutionScaling.wild_option(:SHINX, 6, 19,
            proc { 0 }) == [:SHINX, 6],
            "#{region}: wild threshold regressed")
end

puts 'SINNOH_S18_NATIVE_WILD_ADAPTER_THRESHOLDS_SLOTS_NO_PBS_MUTATION_OFFLINE_OK'
