# Dynamic evolutions for author-defined trainer teams and wild encounters.
# Never edits PBS encounter probabilities/teams, the player's party or saves.
# Selectors use native Essentials 21.1 GameData::Species#get_evolutions.
module BlueEvolutionScaling
  TRAINER_GRACE = 5
  STONE_LEVEL = 30
  TRADE_LEVEL = 40
  FRIENDSHIP_LEVEL = 45
  LEVEL_METHODS = %i[Level LevelMale LevelFemale LevelDay LevelNight
                     LevelMorning LevelAfternoon LevelEvening].freeze
  STONE_METHODS = %i[Item ItemMale ItemFemale ItemDay ItemNight].freeze
  TRADE_METHODS = %i[Trade TradeMale TradeFemale TradeDay TradeNight TradeItem].freeze
  FRIENDSHIP_METHODS = %i[Happiness HappinessMale HappinessFemale
                          HappinessDay HappinessNight].freeze
  SPECIAL_FLAGS = %w[Legendary Mythical UltraBeast Paradox Pending
                     DessastreParadoxal Regional RegionalForm
                     Convergent Mega Gigantamax].freeze

  def self.active?
    defined?(BlueCampaign) && BlueCampaign.active? &&
      defined?(BlueStory) && BlueStory.enabled? &&
      defined?($player) && $player && !$player.party.empty?
  end

  # There is no numerical level-cap field in the current regional save.
  # The campaign bases its dynamic levels on the highest *non-egg* party
  # member; use that same signal rather than the old BST/crystal tier.
  def self.progress_level
    return 1 unless $player && $player.respond_to?(:party)
    highest = $player.party.reject(&:egg?).map(&:level).max || 1
    [[highest, 1].max, GameData::GrowthRate.max_level].min
  end

  def self.special?(data)
    return true if !data || data.form != 0
    (Array(data.flags) & SPECIAL_FLAGS).any?
  end

  def self.method_threshold(method, parameter, kind, pokemon = nil)
    id = method.to_sym
    if LEVEL_METHODS.include?(id)
      return nil unless parameter.is_a?(Integer) && parameter > 0
      level = parameter + TRAINER_GRACE
    elsif STONE_METHODS.include?(id)
      level = STONE_LEVEL
    elsif TRADE_METHODS.include?(id)
      level = TRADE_LEVEL
    elsif FRIENDSHIP_METHODS.include?(id)
      level = FRIENDSHIP_LEVEL
    else
      # E.g. location, held item, required move, special weather, alternate
      # player party or stat/Personality-based branches: never guess.
      return nil
    end
    if id.to_s.end_with?("Male")
      return nil unless pokemon && pokemon.respond_to?(:male?) && pokemon.male?
    elsif id.to_s.end_with?("Female")
      return nil unless pokemon && pokemon.respond_to?(:female?) && pokemon.female?
    end
    if id.to_s.end_with?("Day")
      return nil unless defined?(PBDayNight) && PBDayNight.isDay?
    elsif id.to_s.end_with?("Night")
      return nil unless defined?(PBDayNight) && PBDayNight.isNight?
    elsif id == :LevelMorning
      return nil unless defined?(PBDayNight) && PBDayNight.isMorning?
    elsif id == :LevelAfternoon
      return nil unless defined?(PBDayNight) && PBDayNight.isAfternoon?
    elsif id == :LevelEvening
      return nil unless defined?(PBDayNight) && PBDayNight.isEvening?
    end
    level
  end

  def self.options(species, level, kind = :trainer, pokemon = nil)
    source = GameData::Species.get(species)
    return [] if special?(source)
    matches = []
    source.get_evolutions(true).each do |target_id, method, parameter|
      target = GameData::Species.try_get(target_id)
      next if !target || special?(target)
      minimum = method_threshold(method, parameter, kind, pokemon)
      next if !minimum || level < minimum
      matches << [target_id, minimum]
    end
    # Multiple eligible forms (e.g. Eevee) have no safe implicit preference.
    # Never fabricate an evolution or select a branch by Pokédex order.
    # Different native methods may reach the same form. This is still
    # unambiguous; keep the earliest eligible threshold for that target.
    targets = matches.map { |row| row[0] }.uniq
    return [] unless targets.length == 1
    [[targets[0], matches.map { |row| row[1] }.min]]
  end

  # Called on an already cloned trainer Pokémon, after its final level is
  # known. Rebuilds legal moves/stats; never modifies the trainer PBS.
  def self.upgrade_trainer!(pokemon)
    return pokemon unless pokemon && !pokemon.egg? && !pokemon.shadowPokemon?
    return pokemon unless active?
    3.times do
      eligible = options(pokemon.species, pokemon.level, :trainer, pokemon)
      break if eligible.empty?
      evolved = eligible[0][0]
      break if evolved == pokemon.species
      pokemon.species = evolved
      pokemon.form = 0 if pokemon.respond_to?(:form=)
      pokemon.name = "" unless pokemon.nicknamed?
      pokemon.ability = nil
      pokemon.ability_index = 0
      pokemon.moves = pokemon.moves.select { |m| GameData::Move.exists?(m.id) }
      pokemon.reset_moves
      pokemon.calc_stats
      pokemon.heal
    end
    pokemon
  end

  # Protect a *natural, level-appropriate* evolved form from the earlier
  # BST limit (350/450/540); keep all other BST protections intact.
  def self.legitimate_trainer_form?(pokemon)
    return false unless active? && pokemon && !pokemon.egg?
    species = GameData::Species.get(pokemon.species)
    return false if special?(species)
    previous = species.get_previous_species
    return false if previous == species.species
    options(previous, pokemon.level, :trainer, pokemon).any? { |id, _| id == species.species }
  end

  # When cap reaches 25, approximately 15% of the original Rattata slots
  # can become Raticate. Around cap 30 it is 30%. Base species always has
  # a chance, so original habitat identities and encounter weights survive.
  def self.wild_chance(cap, threshold)
    return 0 if cap < threshold
    gap = cap - threshold
    return 15 if gap < 5
    return 30 if gap < 15
    return 45 if gap < 25
    60
  end

  def self.wild_option(species, base_level, cap, roll = nil)
    return [species, base_level] unless active?
    current = species
    evolved_level = base_level
    3.times do
      choices = options(current, cap, :wild)
      break if choices.empty?
      next_species, minimum = choices[0]
      chance = wild_chance(cap, minimum)
      break unless (roll ? roll.call(100) : rand(100)) < chance
      evolved_level = [evolved_level, minimum].max
      break if evolved_level > cap
      current = next_species
    end
    [current, evolved_level]
  end

  def self.available_wild_species(species, cap)
    result = [species]
    3.times do
      choices = options(result.last, cap, :wild)
      break if choices.empty?
      candidate = choices[0][0]
      break if result.include?(candidate)
      result << candidate
    end
    result
  end

  module WildEncounters
    def choose_wild_pokemon(enc_type, chance_rolls = 1)
      result = super
      return result unless BlueEvolutionScaling.active? &&
                           result.is_a?(Array) && result.length >= 2
      changed = BlueEvolutionScaling.wild_option(
        result[0], result[1], BlueEvolutionScaling.progress_level
      )
      result.dup.tap { |row| row[0], row[1] = changed }
    end
  end

  def self.install
    return if @installed
    PokemonEncounters.prepend(WildEncounters) if defined?(PokemonEncounters) &&
      !PokemonEncounters.ancestors.include?(WildEncounters)
    @installed = true
  end
end
