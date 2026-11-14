# EXPLICIT, READ-ONLY PROBE for a private compiled Game.exe copy.
# Not a plugin installer; never add to the shared story on import.
# Invoke inside the isolated Essentials runtime AFTER compiling Barry's
# three PBS variants, before enabling his battle. No marker or save writes.
module BlueSinnohBarryNativeProbe
  EXPECTED = [
    [:TURTWIG, :CHIMCHAR],
    [:CHIMCHAR, :PIPLUP],
    [:PIPLUP, :TURTWIG]
  ].freeze
  TRAINER = :BLUE_SINNOH_RIVAL
  NAME = "Barry".freeze
  READY_MARKER = "Data/blue-sinnoh-rival-ready.txt".freeze

  def self.require_check!(condition, message)
    raise "[SINNOH BARRY NATIVE] #{message}" unless condition
  end

  def self.species_of(pokemon)
    if pokemon.is_a?(Hash)
      pokemon[:species] || pokemon["species"]
    elsif pokemon.respond_to?(:species)
      pokemon.species
    end
  end

  def self.seed_level_of(pokemon)
    if pokemon.is_a?(Hash)
      pokemon[:level] || pokemon["level"]
    elsif pokemon.respond_to?(:level)
      pokemon.level
    end
  end

  # Checks the compiled GameData index in the *actual* Essentials runtime.
  # Does NOT simulate/start a battle, assert 70/90% levels, or certify QA.
  def self.run!
    require_check!(File.file?("Sinnoh pilot.json"),
                   "Execute apenas na copia isolada do piloto Sinnoh.")
    require_check!(!File.file?(READY_MARKER),
                   "O marcador Barry ja existe antes da validacao da compilacao.")
    require_check!(defined?(GameData::Trainer),
                   "GameData::Trainer nao foi carregado pelo Essentials.")
    require_check!(defined?(BlueCampaign) && BlueCampaign.respond_to?(:trainer_level),
                   "Balanceamento BlueCampaign ainda nao carregado.")
    rows = EXPECTED.each_with_index.map do |pair, version|
      player_starter, rival = pair
      trainer = GameData::Trainer.get(TRAINER, NAME, version)
      require_check!(!trainer.nil?, "Barry versao #{version} ausente no compilado.")
      mons = trainer.respond_to?(:pokemon) ? trainer.pokemon : nil
      require_check!(mons.is_a?(Array) && mons.length == 1,
                     "Barry versao #{version} precisa de um inicial unico.")
      actual = species_of(mons.first)
      actual = actual.to_sym if actual.is_a?(String)
      require_check!(actual == rival,
                     "Barry versao #{version}: especie diferente do contra-inicial.")
      seed = seed_level_of(mons.first)
      require_check!(seed.is_a?(Integer) && seed == 5,
                     "Barry versao #{version}: seed PBS deve ser nivel 5.")
      {
        :version => version, :player_starter => player_starter,
        :rival_species => rival, :pbs_seed_level => 5
      }
    end

    {
      :region => "SINNOH",
      :mode => "NATIVE_COMPILED_TRAINER_INDEX_CHECK_ONLY",
      :compiled_teams_indexed => 3,
      :teams => rows,
      :battle_executed => false,
      :effective_level_checked_in_battle => false,
      :trainer_sprite_checked => false,
      :save_load_checked => false,
      :joi_play_checked => false,
      :ready_marker_created => false,
      :safe_to_enable_barry => false,
      :gameplay_approved => false
    }
  end
end
