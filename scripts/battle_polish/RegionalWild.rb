# Dynamic regional wild encounters. This does NOT edit any region's PBS or
# touch Decades encounters, map IDs, trainer parties, saves or Johto staging.
module BlueRegionalWild
  REGIONS = %w[KANTO JOHTO HOENN].freeze
  EVOLVED_SLOT_PERCENT = 35
  PROTECTED_FLAGS = %w[Legendary Mythical UltraBeast Paradox Pending].freeze

  def self.active_region?
    return false unless defined?(BlueCampaign) && BlueCampaign.active?
    return false unless defined?(BlueRegions) && defined?($PokemonGlobal) && $PokemonGlobal
    state = BlueRegions.snapshot
    state.is_a?(Hash) && REGIONS.include?(state["current"])
  end

  # Only unambiguous automatic level evolution, never friendship, trades,
  # items, branching conditions, regional forms or special species.
  def self.level_evolution(species, level)
    current = species
    seen = {}
    3.times do
      break if seen[current]
      seen[current] = true
      data = GameData::Species.try_get(current)
      break unless data && data.form == 0
      break unless (data.flags & PROTECTED_FLAGS).empty?
      candidates = data.evolutions.select do |target, method, required, prevolution|
        !prevolution && method == :Level && required.is_a?(Integer) &&
          level >= required && GameData::Species.try_get(target)
      end
      break unless candidates.length == 1
      target = GameData::Species.try_get(candidates.first[0])
      break unless target && target.form == 0 &&
                   (target.flags & PROTECTED_FLAGS).empty?
      current = target.species
    end
    current == species ? nil : current
  end

  def self.change(encounter, roll = nil)
    return encounter unless active_region?
    return encounter unless encounter.is_a?(Array) && encounter.length >= 2
    return encounter unless $game_map && $game_temp && $game_temp.encounter_type
    # Only ordinary, table-backed map encounters. Never touch scripted gifts,
    # roaming legendaries or debug battles, even when a species matches.
    data = GameData::Encounter.get($game_map.map_id, $PokemonGlobal.encounter_version || 0)
    return encounter unless data
    slots = data.types[$game_temp.encounter_type]
    return encounter unless slots && slots.any? { |slot| slot[1] == encounter[0] }
    level = BlueCampaign.wild_level
    encounter[1] = level
    # Eligibility tracks the player's progression cap; wild battles retain
    # the existing 45% level scale. At a trainer cap of 30, Rattata can
    # share its route slot with Raticate instead of waiting for wild level 20.
    progression_level = $player.party.reject(&:egg?).map(&:level).max || 1
    evolved = level_evolution(encounter[0], progression_level)
    chance = roll.nil? ? rand(100) : roll
    encounter[0] = evolved if evolved && chance < EVOLVED_SLOT_PERCENT
    encounter
  end

  def self.install
    EventHandlers.add(:on_wild_species_chosen, :blue_regional_wild_evolution,
                      proc { |encounter| BlueRegionalWild.change(encounter) })
  end
end
BlueRegionalWild.install
