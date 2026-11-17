# Authored Sinnoh introductory story for a FUTURE isolated test copy only.
# DO NOT load into main Decades, Kanto, Johto or Hoenn.
# No global hooks, map IDs, starter grants without a Poké Ball, or donor scripts.
# RPG Maker events must be compiled after REAL Twinleaf/Verity/Sandgem audits.
module BlueSinnohPilot
  STARTERS = [:TURTWIG, :CHIMCHAR, :PIPLUP].freeze
  RIVAL_CHOICES = {
    :TURTWIG => [:CHIMCHAR, 0],
    :CHIMCHAR => [:PIPLUP, 1],
    :PIPLUP => [:TURTWIG, 2]
  }.freeze
  RIVAL_READY = "Data/blue-sinnoh-rival-ready.txt".freeze
  RIVAL_PROOF = "BLUE_SINNOH_BARRY_V1_READY".freeze

  # All state lives ONLY in the active Sinnoh region-scoped save record.
  # Never initialize/replace the BlueRegions global state for other regions.
  def self.regional_state
    return nil unless defined?($PokemonGlobal) && $PokemonGlobal
    return nil unless $PokemonGlobal.respond_to?(:blue_regions)
    record = $PokemonGlobal.blue_regions
    return nil unless record.is_a?(Hash) &&
                      record["version"] == 1 &&
                      record["current"] == "SINNOH"
    # CH07: private Sinnoh QA saves must not borrow another region's initial.
    return nil if record.key?("initial") && record["initial"] != "SINNOH"
    record
  end

  # Checkpoint reads must not create or repair flags, especially after a
  # failed event or when a loaded save is incomplete or forged.
  def self.valid_flags?(flags)
    return false unless flags.is_a?(Hash)
    checkpoints = %w[mother_intro barry_intro rowan_briefcase_seen
                     starter_received rival_fought pokedex_received]
    # Refuse arbitrary saved flags: only these six checkpoints plus the
    # paired physical starter species belong to this isolated story.
    return false unless flags.keys.all? { |key|
      key.is_a?(String) && (checkpoints.include?(key) || key == "starter")
    }
    checkpoints.each do |key|
      return false if flags.key?(key) && flags[key] != true && flags[key] != false
    end
    return false if flags["barry_intro"] == true && flags["mother_intro"] != true
    return false if flags["rowan_briefcase_seen"] == true && flags["barry_intro"] != true
    raw = flags["starter"]
    chosen = raw.is_a?(String) && STARTERS.include?(raw.to_sym)
    granted = flags["starter_received"] == true
    return false if granted != !!chosen
    return false if granted && flags["rowan_briefcase_seen"] != true
    return false if flags.key?("starter") && !granted
    return false if flags["rival_fought"] == true && !granted
    return false if flags["pokedex_received"] == true && flags["rival_fought"] != true
    true
  end

  def self.progress
    state = regional_state
    return nil unless state
    existing = state["sinnoh_pilot"]
    return {} if existing.nil?
    valid_flags?(existing) ? existing : nil
  end

  # Only a completed action may create/update the isolated progress record.
  def self.commit_flag(key)
    state = regional_state
    flags = progress
    return false unless state && flags && key.is_a?(String)
    # Exactly one transition per verified event, never arbitrary direct writes.
    previous = {
      "mother_intro" => nil,
      "barry_intro" => "mother_intro",
      "rowan_briefcase_seen" => "barry_intro",
      "rival_fought" => "starter_received",
      "pokedex_received" => "rival_fought"
    }
    return false unless previous.key?(key) && flags[key] != true
    required = previous[key]
    return false if required && flags[required] != true
    return false if key == "rival_fought" && !@rival_battle_in_progress
    return false if key == "pokedex_received" && !@pokedex_grant_in_progress
    return false unless valid_flags?(flags.merge(key => true))
    state["sinnoh_pilot"] ||= {}
    state["sinnoh_pilot"][key] = true
    true
  end

  def self.starter
    flags = progress
    return nil unless flags
    current = flags["starter"]
    selected = current.is_a?(String) ? current.to_sym : nil
    STARTERS.include?(selected) ? selected : nil
  end

  def self.starter_name
    selected = starter
    return nil unless selected
    if defined?(GameData::Species)
      return GameData::Species.get(selected).name
    end
    selected.to_s.capitalize
  end

  def self.mother
    flags = progress
    return false unless flags
    if flags["mother_intro"]
      pbMessage(_INTL("Mãe: Boa viagem! Volte quando quiser descansar."))
      return false
    end
    pbMessage(_INTL("Mãe: Barry veio procurar você. Ele falou sobre uma pesquisa perto do lago."))
    commit_flag("mother_intro")
  end

  def self.barry_intro
    flags = progress
    return false unless flags
    unless flags["mother_intro"]
      pbMessage(_INTL("Barry: Sua mãe está esperando você em casa."))
      return false
    end
    if flags["barry_intro"]
      pbMessage(_INTL("Barry: Vamos descobrir o que o professor está investigando!"))
      return false
    end
    pbMessage(_INTL("Barry: Dizem que um pesquisador esteve perto do Lago Verity. Vamos conferir!"))
    commit_flag("barry_intro")
  end

  # In this Blue-authored pilot, Rowan authorizes the player to choose a
  # research partner from THREE physical ball events after Barry's introduction.
  def self.rowan_briefcase
    flags = progress
    return false unless flags
    unless flags["barry_intro"]
      pbMessage(_INTL("Rowan: Quero conversar com você e Barry juntos."))
      return false
    end
    if flags["rowan_briefcase_seen"]
      pbMessage(_INTL("Rowan: A maleta está aberta. Examine uma das três Poké Bolas."))
      return false
    end
    pbMessage(_INTL("Rowan: Preciso de ajuda para observar os Pokémon desta região."))
    pbMessage(_INTL("Rowan: Escolha um parceiro da maleta. Os três precisam de bons treinadores."))
    commit_flag("rowan_briefcase_seen")
  end

  def self.choose_starter_from_ball(species)
    flags = progress
    return false unless flags
    requested = (species.is_a?(Symbol) || species.is_a?(String)) ? species.to_sym : nil
    return false unless STARTERS.include?(requested)
    if flags["starter_received"] || flags.key?("starter")
      pbMessage(_INTL("Rowan: Você já escolheu um parceiro desta maleta."))
      return false
    end
    unless flags["rowan_briefcase_seen"]
      pbMessage(_INTL("Rowan: Aguarde minha explicação antes de escolher."))
      return false
    end
    return false unless defined?(pbAddPokemonSilent)
    # Only a physical ball grants a starter; nested grants are denied.
    return false if @starter_grant_in_progress
    scope = regional_state
    @starter_grant_in_progress = true
    begin
      return false unless pbAddPokemonSilent(requested, 5)
      return false unless scope && regional_state.equal?(scope)
      current = progress
      return false unless current && !current.key?("starter") &&
                          current["starter_received"] != true &&
                          current["rowan_briefcase_seen"] == true
      scope["sinnoh_pilot"] ||= {}
      scope["sinnoh_pilot"]["starter"] = requested.to_s
      scope["sinnoh_pilot"]["starter_received"] = true
      pbMessage(_INTL("Rowan: Ótima escolha! Observe seu parceiro durante a viagem."))
      true
    ensure
      @starter_grant_in_progress = false
    end
  end

  # The professor never exposes a choice dialog or grants Pokémon.
  def self.choose_starter
    flags = progress
    return false unless flags
    pbMessage(_INTL("Rowan: Toque na Poké Bola do Pokémon que deseja acompanhar."))
    false
  end

  def self.rival_species
    selected = starter
    selected ? RIVAL_CHOICES.fetch(selected)[0] : nil
  end

  def self.rival_version
    selected = starter
    selected ? RIVAL_CHOICES.fetch(selected)[1] : nil
  end

  def self.rival_fought?
    flags = progress
    flags && flags["rival_fought"] == true
  end

  # CH08: a marker is not a compiled PBS team. A missing or mismatched
  # GameData trainer must never call TrainerBattle.start or advance the save.
  # Check only the selected version (0/1/2) in this isolated pilot.
  def self.compiled_rival_valid?
    version = rival_version
    expected = rival_species
    return false unless version.is_a?(Integer) && (0..2).cover?(version) && expected
    return false unless defined?(GameData::Trainer) &&
                        GameData::Trainer.respond_to?(:get)
    trainer = GameData::Trainer.get(:BLUE_SINNOH_RIVAL, "Barry", version)
    return false unless trainer && trainer.respond_to?(:pokemon)
    team = trainer.pokemon
    return false unless team.is_a?(Array) && team.length == 1
    pokemon = team.first
    species = pokemon.is_a?(Hash) ? (pokemon[:species] || pokemon["species"]) :
              (pokemon.respond_to?(:species) ? pokemon.species : nil)
    level = pokemon.is_a?(Hash) ? (pokemon[:level] || pokemon["level"]) :
            (pokemon.respond_to?(:level) ? pokemon.level : nil)
    species.to_s == expected.to_s && level.is_a?(Integer) && level == 5
  rescue StandardError
    false
  end

  def self.barry_rival
    flags = progress
    return false unless flags
    unless starter
      pbMessage(_INTL("Barry: Primeiro escolha seu parceiro na maleta!"))
      return false
    end
    if rival_fought?
      pbMessage(_INTL("Barry: Ainda vamos ter muitas batalhas pela frente!"))
      return false
    end
    # Until all three versions exist and are checked by the isolated build,
    # DO NOT attempt to start an arbitrary PBS trainer from the main game.
    ready_for_release = File.file?(RIVAL_READY) && !File.symlink?(RIVAL_READY) &&
                        File.read(RIVAL_READY).strip == RIVAL_PROOF
    # The private QA may TEST the battle before final gameplay acceptance.
    # Its native map/PBS probe + per-copy hash proof is mandatory, and this
    # does not create the release marker or change behavior in the main game.
    qa_test_only = defined?(BlueSinnohQAStart) &&
                   BlueSinnohQAStart.respond_to?(:barry_test_authorized?) &&
                   BlueSinnohQAStart.barry_test_authorized?
    unless (ready_for_release || qa_test_only) && compiled_rival_valid? &&
           defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
      pbMessage(_INTL("Barry: Nossa primeira batalha estará disponível no piloto de Sinnoh."))
      return false
    end
    return false if @rival_battle_in_progress
    @rival_battle_in_progress = true
    scope = regional_state
    chosen = starter
    begin
      pbMessage(_INTL("Barry: Vamos descobrir como nossos parceiros se saem!"))
      setBattleRule("canLose")
      result = TrainerBattle.start(:BLUE_SINNOH_RIVAL, "Barry", rival_version)
      # false means a completed canLose defeat, nil means no confirmed battle.
      return false unless result == true || result == false
      return false unless scope && regional_state.equal?(scope) && starter == chosen
      $player.heal_party if defined?($player) && $player && $player.respond_to?(:heal_party)
      return false unless commit_flag("rival_fought")
      pbMessage(result ?
        _INTL("Barry: Você venceu! Vou melhorar minha estratégia.") :
        _INTL("Barry: Que batalha! Vamos continuar treinando."))
      true
    rescue IOError, SystemCallError
      pbMessage(_INTL("Barry: Nossa batalha não pôde ser validada."))
      false
    ensure
      @rival_battle_in_progress = false
    end
  end

  def self.rowan_pokedex
    flags = progress
    return false unless flags
    unless flags["rival_fought"] == true && starter
      pbMessage(_INTL("Rowan: Primeiro conheça seu parceiro e complete o treino com Barry."))
      return false
    end
    if flags["pokedex_received"]
      pbMessage(_INTL("Rowan: Registre suas descobertas na Pokédex."))
      return false
    end
    # Only mark dex as delivered after the engine's actual player field exists.
    return false unless defined?($player) && $player &&
                        $player.respond_to?(:has_pokedex=)
    return false if @pokedex_grant_in_progress
    @pokedex_grant_in_progress = true
    begin
      # Do not grant a Pokédex before committing a valid regional checkpoint.
      return false unless commit_flag("pokedex_received")
      $player.has_pokedex = true
      pbMessage(_INTL("Rowan: Sua Pokédex está pronta. Explore Sinnoh com cuidado."))
      true
    ensure
      @pokedex_grant_in_progress = false
    end
  end
end
