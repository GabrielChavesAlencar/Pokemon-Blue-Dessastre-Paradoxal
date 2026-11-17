# S17: exercise the ACTUAL shared BlueStory/Campaign/EvolutionScaling
# through Battle.prepend, using only synthetic trainers and Pokemon.
# CH12 fixture loads the same runtime modules; no PBS, save or Game.exe used.
require 'json'
fixture = ARGV.shift
raise 'S17 fixture path missing' unless fixture
load File.expand_path(fixture)

def s17_assert(value, reason)
  raise "SINNOH_S17: #{reason}" unless value
end

def s17_player(level, eggs = [])
  $player.party = [Pokemon.new(:TURTWIG, level)] + eggs
end

def s17_trainers(rosters)
  trainers = rosters.map.with_index do |team, index|
    type, name, version, species = team
    pokes = species.map { |id| Pokemon.new(id, 5) }
    Trainer.new(type, name || "S17 synthetic #{index}", version || 0, pokes)
  end
  before = Marshal.dump(trainers)
  p_before = Marshal.dump($player.party)
  battle = Battle.new(nil, nil, [], nil, trainers)
  s17_assert(Marshal.dump(trainers) == before, 'authored PBS trainers changed')
  s17_assert(Marshal.dump($player.party) == p_before, 'player party changed')
  result = battle.captured[4]
  s17_assert(result.is_a?(Array), 'trainer output is not array')
  s17_assert(result.length == rosters.length, 'trainers were lost or duplicated')
  [result, trainers, battle.captured[2]]
end

# CH12 ended in Battle Mode. Re-enable regular story for a fresh Sinnoh save.
$PokemonGlobal.blue_story_mode = :story
$PokemonGlobal.blue_traditional_starters = true
$PokemonGlobal.blue_regions = BlueRegions.new_state('SINNOH')
$player.badge_count = 0
s17_assert(BlueStory.current_region == 'SINNOH', 'wrong current region')
s17_assert(BlueCampaign.active? && BlueStory.enabled?, 'story scaling inactive')
s17_assert(!BlueCampaign.master?, 'new region already Master')

# Every normal opponent is level floor(70% * highest NON-EGG party member).
# Never publish these as fixed numerical trainer levels.
s17_player(53, [Pokemon.new(:SUPPORT, 99, true)])
out, originals, opponents = s17_trainers([
  [:BLUE_SINNOH_HIKER, 'S17 Hiker', 2, [:TURTWIG, :SHINX]],
  [:BLUE_SINNOH_BUGCATCHER, 'S17 Catcher', 0, [:CHIMCHAR]]
])
s17_assert(out.flat_map(&:party).all? { |pk| pk.level == 37 },
           'normal trainer did not use floor(53 * 70 / 100)')
s17_assert(opponents.length == 3, 'battle opposing side missing a Pokemon')
s17_assert(out.first.party.length == 2 && out.last.party.length == 1,
           'normal mode inserted extra team slots')
s17_assert(out.first.party.first.species == :TORTERRA,
           'trainer evolution failed after selecting final level')
s17_assert(originals.first.party.first.level == 5 &&
           originals.first.party.first.species == :TURTWIG,
           'trainer PBS input was modified by dynamic level')

# First gym/Elite/Champion battles bypass the lower BST tiers, keeping
# authored species. Other boss-like classes (Rival/Admin/Boss) still obey
# Story's BST tier unless an explicit Full Power context is selected.
%w[LEADER ELITE ELITEFOUR CHAMPION].each do |role|
  kind = ("BLUE_SINNOH_" + role).to_sym
  team, native, = s17_trainers([[kind, "S17 #{role}", 3, [:TORTERRA]]])
  s17_assert(team.first.party.first.species == :TORTERRA,
             "#{role}: first regional boss species replaced")
  s17_assert(team.first.party.first.level == 37, "#{role}: wrong dynamic level")
  s17_assert(team.first.version == 3 && native.first.version == 3,
             "#{role}: version changed")
end
%w[RIVAL ADMIN BOSS].each do |role|
  kind = ("BLUE_SINNOH_" + role).to_sym
  team, native, = s17_trainers([[kind, "S17 #{role}", 3, [:TORTERRA]]])
  s17_assert(team.first.party.first.species != :TORTERRA,
             "#{role}: strong non-exempt class escaped early BST tier")
  s17_assert(team.first.party.first.level == 37,
             "#{role}: BST tier changed dynamic level")
  s17_assert(native.first.party.first.species == :TORTERRA,
             "#{role}: authored PBS changed by BST tier")
end

# The stages in Blue are based on cumulative local medals + native badges,
# NOT a fabricated fixed numeric level cap for each regional gym.
state = $PokemonGlobal.blue_regions
BlueRegions.info('SINNOH')['milestones'].each do |badge|
  s17_assert(BlueRegions.award(state, 'SINNOH', badge),
             "synthetic regional badge couldn't be recorded")
end
s17_assert(BlueStory.stage == 2 && !BlueCampaign.master?,
           'eight Sinnoh medals alone must not trigger Master')
$player.badge_count = 3
s17_assert(BlueStory.stage == 3 && BlueCampaign.master?,
           'eleven combined medals must trigger Master')
s17_player(53, [Pokemon.new(:SUPPORT, 99, true)])

# Single trainer's 1/2/3-member team is expanded to 4 (never 7) in Master.
[1, 2, 3, 4, 6].each do |size|
  team, raw, foes = s17_trainers([
    [:BLUE_SINNOH_HIKER, 'S17 master normal', 0,
     Array.new(size) { :TURTWIG }]
  ])
  expected = size <= 3 ? 4 : size
  s17_assert(team.first.party.length == expected,
             "Master #{size}-Pokemon roster became #{team.first.party.length}, not #{expected}")
  s17_assert(foes.length == expected && expected <= 6,
             'Master created more than six opponents')
  s17_assert(team.first.party.all? { |p| p.level == 47 },
             'Master level is not floor(53 * 90 / 100)')
  s17_assert(raw.first.party.length == size &&
             raw.first.party.all? { |p| p.level == 5 },
             'Master expanded the authored trainer input')
end

# Two opposing trainers must share the six-slot cap; a double battle is never
# silently expanded into 8 Pokemon because each trainer wants four.
duo, originals, flattened = s17_trainers([
  [:BLUE_SINNOH_HIKER, 'S17 double A', 0, [:TURTWIG]],
  [:BLUE_SINNOH_BUGCATCHER, 'S17 double B', 0, [:CHIMCHAR]]
])
s17_assert(duo.sum { |t| t.party.length } <= 6 &&
           duo.sum { |t| t.party.length } == flattened.length,
           'double battle exceeded six opponent slots')
s17_assert(flattened.all? { |p| p.level == 47 },
           'double battle changed Master level')

# Preserve full authored 4-6 Pokemon gym/Elite/Champion team counts.
%w[LEADER ELITEFOUR CHAMPION].each do |role|
  team, original, = s17_trainers([
    [("BLUE_SINNOH_" + role).to_sym, "S17 #{role}", 1,
     [:TORTERRA, :INFERNAPE, :EMPOLEON, :ROSERADE]]
  ])
  s17_assert(team.first.party.length == 4 && original.first.party.length == 4,
             "#{role}: authored four-member team changed length")
  s17_assert(team.first.party.map(&:species) ==
             [:TORTERRA, :INFERNAPE, :EMPOLEON, :ROSERADE],
             "#{role}: boss roster species were replaced")
end

# Extreme inputs: clamp to engine maximum and do not count eggs; no mutation.
$player.badge_count = 0
$PokemonGlobal.blue_regions = BlueRegions.new_state('SINNOH')
s17_player(250)
s17_assert(BlueCampaign.trainer_level(nil) == 100,
           'normal level exceeded engine max')
s17_player(1)
s17_assert(BlueCampaign.trainer_level(nil) == 1,
           'minimum story level fell below 1')
$player.party = [Pokemon.new(:SUPPORT, 99, true)]
s17_assert(BlueCampaign.trainer_level(nil) == 1,
           'egg-only party raised trainer level')
$player.party.clear
s17_assert(BlueCampaign.trainer_level(nil) == 1,
           'empty party raised trainer level')

# Battle mode must NEVER apply synthetic Sinnoh balancing, nor copy/wipe
# previously authored trainer data.
$PokemonGlobal.blue_story_mode = :battle
s17_player(70)
team, native, = s17_trainers([
  [:BLUE_SINNOH_HIKER, 'S17 not story', 0, [:TURTWIG]]
])
s17_assert(team.first.party.first.level == 5 &&
           team.first.party.first.species == :TURTWIG,
           'Battle mode incorrectly applied story scaling')
s17_assert(native.first.party.first.level == 5,
           'Battle mode edited original trainer')

# Do not leak the current Sinnoh save or regional achievements when traveling:
# Kanto/Hoenn must retain the existing shared campaign policy independently.
$PokemonGlobal.blue_story_mode = :story
state_before = Marshal.dump($PokemonGlobal.blue_regions)
%w[KANTO HOENN JOHTO].each do |region|
  $PokemonGlobal.blue_regions = BlueRegions.new_state(region)
  s17_player(53)
  level = BlueCampaign.trainer_level(nil)
  s17_assert(level == 37, "#{region}: shared 70% policy regressed")
  s17_assert(BlueRegions.info(region) != nil, "#{region}: region missing")
end
$PokemonGlobal.blue_regions = Marshal.load(state_before)
s17_assert(BlueStory.current_region == 'SINNOH',
           'Sinnoh save state changed while comparing regions')

puts 'SINNOH_S17_DYNAMIC_LEVELS_BOSSES_DOUBLE_MASTER_NO_MUTATION_OFFLINE_OK'
