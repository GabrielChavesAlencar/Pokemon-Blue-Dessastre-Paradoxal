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
    record
  end

  def self.progress
    state = regional_state
    return nil unless state
    existing = state["sinnoh_pilot"]
    return nil unless existing.nil? || existing.is_a?(Hash)
    state["sinnoh_pilot"] ||= {}
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
    flags["mother_intro"] = true
    true
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
    flags["barry_intro"] = true
    true
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
    flags["rowan_briefcase_seen"] = true
    true
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
    # Never set the selection flag if the engine rejects the grant.
    return false unless pbAddPokemonSilent(requested, 5)
    flags["starter"] = requested.to_s
    flags["starter_received"] = true
    pbMessage(_INTL("Rowan: Ótima escolha! Observe seu parceiro durante a viagem."))
    true
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
    unless (ready_for_release || qa_test_only) &&
           defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
      pbMessage(_INTL("Barry: Nossa primeira batalha estará disponível no piloto de Sinnoh."))
      return false
    end
    pbMessage(_INTL("Barry: Vamos descobrir como nossos parceiros se saem!"))
    setBattleRule("canLose")
    result = TrainerBattle.start(:BLUE_SINNOH_RIVAL, "Barry", rival_version)
    return false if result.nil?
    $player.heal_party if defined?($player) && $player && $player.respond_to?(:heal_party)
    flags["rival_fought"] = true
    pbMessage(result ?
      _INTL("Barry: Você venceu! Vou melhorar minha estratégia.") :
      _INTL("Barry: Que batalha! Vamos continuar treinando."))
    true
  rescue IOError, SystemCallError
    pbMessage(_INTL("Barry: Nossa batalha não pôde ser validada."))
    false
  end

  def self.rowan_pokedex
    flags = progress
    return false unless flags
    unless flags["rival_fought"] && starter
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
    $player.has_pokedex = true
    flags["pokedex_received"] = true
    pbMessage(_INTL("Rowan: Sua Pokédex está pronta. Explore Sinnoh com cuidado."))
    true
  end
end
