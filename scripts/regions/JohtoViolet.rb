# Violet City / Sprout Tower / Falkner -- phase 05/16 (story runtime only).
# Loaded solely by a future separately installed Johto pilot. Do not add
# these handlers to the native Decades/Kanto Plugins folder.
#
# The map pack, trainer PBS, encounters, artwork and map events have NOT
# been audited. No trainer battle is callable until a trusted pilot installer
# has compiled the trainer entries and written the local ready marker.
module BlueJohtoViolet
  REGION = "JOHTO".freeze
  BADGE = "ZEPHYR".freeze
  READY_FILE = "Data/blue-johto-violet-ready.txt".freeze
  READY_VALUE = "BLUE_JOHTO_VIOLET_V1_READY".freeze
  FALKNER_TYPE = :BLUE_JOHTO_FALKNER
  ELDER_TYPE = :BLUE_JOHTO_ELDER
  FALKNER_NAME = "Falkner".freeze
  ELDER_NAME = "Li".freeze

  def self.record
    return nil unless defined?(BlueJohtoPilot)
    BlueJohtoPilot.regional_state
  end

  def self.progress
    return nil unless record
    BlueJohtoPilot.progress
  end

  def self.violet_intro
    flags = progress
    return false unless flags
    if flags["violet_visited"]
      pbMessage(_INTL("Violet City: a Torre Sprout e o Ginasio aguardam sua visita."))
      return false
    end
    pbMessage(_INTL("Bem-vindo a Violet City! Conheca a Torre Sprout e desafie Falkner no Ginasio."))
    flags["violet_visited"] = true
    true
  end

  def self.trainers_ready?
    File.file?(READY_FILE) &&
      File.read(READY_FILE).strip == READY_VALUE &&
      defined?(TrainerBattle) &&
      TrainerBattle.respond_to?(:start)
  rescue IOError, SystemCallError
    false
  end

  def self.can_challenge?
    return false unless record
    return false unless BlueJohtoPilot.starter
    # Require the early rival tutorial; no gym challenge before the Johto intro.
    BlueJohtoPilot.rival_fought?
  end

  def self.badge_earned?
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.local_achievements(state, REGION).include?(BADGE)
  end

  def self.sprout_elder
    flags = progress
    return false unless flags
    unless can_challenge?
      pbMessage(_INTL("Anciao Li: Volte depois de iniciar sua jornada e conhecer seu rival."))
      return false
    end
    if flags["violet_elder_defeated"]
      pbMessage(_INTL("Anciao Li: Sua paciencia e dedicacao serao recompensadas."))
      return false
    end
    unless trainers_ready?
      pbMessage(_INTL("O desafio da Torre Sprout ainda nao esta instalado no piloto de Johto."))
      return false
    end
    won = TrainerBattle.start(ELDER_TYPE, ELDER_NAME, 0)
    return false unless won == true
    flags["violet_elder_defeated"] = true
    pbMessage(_INTL("Anciao Li: Boa batalha. Continue seu treinamento em Johto!"))
    true
  end

  def self.falkner
    state = record
    flags = progress
    return false unless state && flags
    if badge_earned?
      pbMessage(_INTL("Falkner: Voce ja conquistou a Zephyr Badge!"))
      return false
    end
    unless can_challenge?
      pbMessage(_INTL("Falkner: Comece sua jornada com Elm e enfrente seu rival primeiro."))
      return false
    end
    unless trainers_ready?
      pbMessage(_INTL("A batalha contra Falkner ainda nao esta instalada no piloto de Johto."))
      return false
    end
    # Existing Decades/Blue battle-balancing hooks own actual levels/difficulty.
    # Never award a badge because a marker exists or because the battle began.
    won = TrainerBattle.start(FALKNER_TYPE, FALKNER_NAME, 0)
    return false unless won == true
    unless defined?(BlueRegions) && BlueRegions.award(state, REGION, BADGE) == true
      pbMessage(_INTL("A insígnia de Violet nao pôde ser registrada. Revise o progresso regional."))
      return false
    end
    flags["violet_falkner_defeated"] = true
    pbMessage(_INTL("Falkner: Parabens! Voce conquistou a Zephyr Badge de Johto."))
    true
  end

  def self.rock_smash_allowed?
    state = record
    return false unless state && defined?(BlueRegions)
    # Registry also checks tool readiness in the actual field-move handler.
    BlueRegions.field_access(state, REGION, "ROCK_SMASH", true) == :allowed
  end
end
