# Johto phase 06/16 -- Azalea / Slowpoke Well / Bugsy story only.
# Not loaded in native Decades or Kanto. These handlers become available
# only when the isolated Johto pilot installs reviewed RMXP maps and PBS.
module BlueJohtoAzalea
  REGION = "JOHTO".freeze
  BADGE = "HIVE".freeze
  PREVIOUS_BADGE = "ZEPHYR".freeze
  READY_FILE = "Data/blue-johto-azalea-ready.txt".freeze
  READY_VALUE = "BLUE_JOHTO_AZALEA_V1_READY".freeze
  GRUNT_TYPE = :BLUE_JOHTO_ROCKET_GRUNT
  EXECUTIVE_TYPE = :BLUE_JOHTO_ROCKET_PROTON
  BUGSY_TYPE = :BLUE_JOHTO_BUGSY
  RIVAL_TYPE = :BLUE_JOHTO_AZALEA_RIVAL
  GRUNT_VERSIONS = [0, 1].freeze

  def self.record
    return nil unless defined?(BlueJohtoPilot)
    BlueJohtoPilot.regional_state
  end

  def self.progress
    return nil unless record
    BlueJohtoPilot.progress
  end

  def self.earned?(key)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.local_achievements(state, REGION).include?(key)
  end

  def self.hive_earned?
    earned?(BADGE)
  end

  def self.trainers_ready?
    File.file?(READY_FILE) &&
      File.read(READY_FILE).strip == READY_VALUE &&
      defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
  rescue IOError, SystemCallError
    false
  end

  def self.arrive
    flags = progress
    return false unless flags
    unless earned?(PREVIOUS_BADGE)
      pbMessage(_INTL("Azalea fica depois de Violet. Conquiste a Zephyr Badge primeiro."))
      return false
    end
    if flags["azalea_visited"]
      pbMessage(_INTL("Azalea Town: Kurt e o Poco Slowpoke esperam por voce."))
      return false
    end
    flags["azalea_visited"] = true
    pbMessage(_INTL("Bem-vindo a Azalea Town! Alguns Slowpoke desapareceram perto do poco."))
    true
  end

  def self.kurt
    flags = progress
    return false unless flags
    unless earned?(PREVIOUS_BADGE)
      pbMessage(_INTL("Kurt: Converse comigo quando terminar seu desafio em Violet."))
      return false
    end
    if flags["slowpoke_well_cleared"]
      if flags["azalea_kurt_thanked"]
        pbMessage(_INTL("Kurt: Obrigado por ajudar os Slowpoke!"))
        return false
      end
      flags["azalea_kurt_thanked"] = true
      pbMessage(_INTL("Kurt: Voce salvou os Slowpoke! Volte sempre a Azalea."))
      return true
    end
    if flags["azalea_kurt_met"]
      pbMessage(_INTL("Kurt: A Equipe Rocket ainda esta no Poco Slowpoke."))
      return false
    end
    flags["azalea_kurt_met"] = true
    pbMessage(_INTL("Kurt: A Equipe Rocket esta machucando os Slowpoke. Preciso de ajuda!"))
    true
  end

  def self.well_entrance
    flags = progress
    return false unless flags
    unless earned?(PREVIOUS_BADGE) && flags["azalea_kurt_met"]
      pbMessage(_INTL("Fale com Kurt e conquiste a Zephyr Badge antes de entrar no poco."))
      return false
    end
    if flags["slowpoke_well_cleared"]
      pbMessage(_INTL("Os Slowpoke estao em seguranca. A Equipe Rocket recuou."))
      return false
    end
    return false if flags["azalea_well_entered"]
    flags["azalea_well_entered"] = true
    pbMessage(_INTL("Poco Slowpoke: derrote os Rockets para proteger os Pokemon!"))
    true
  end

  def self.grunt_defeated?(number)
    flags = progress
    flags && flags["slowpoke_grunts"].is_a?(Array) &&
      flags["slowpoke_grunts"].include?(number)
  end

  def self.rocket_grunt(number)
    flags = progress
    return false unless flags
    return false unless GRUNT_VERSIONS.include?(number)
    unless earned?(PREVIOUS_BADGE) && flags["azalea_kurt_met"] &&
           flags["azalea_well_entered"]
      pbMessage(_INTL("A missao no Poco Slowpoke ainda nao foi iniciada."))
      return false
    end
    if flags["slowpoke_well_cleared"] || grunt_defeated?(number)
      pbMessage(_INTL("Rocket: Minha missao aqui acabou."))
      return false
    end
    # Explicit order means a later Rocket cannot be skipped via another event.
    if number > 0 && !grunt_defeated?(number - 1)
      pbMessage(_INTL("O caminho ainda esta bloqueado por outro Rocket."))
      return false
    end
    unless trainers_ready?
      pbMessage(_INTL("Os treinadores Rocket ainda nao estao instalados no piloto."))
      return false
    end
    won = TrainerBattle.start(GRUNT_TYPE, "Rocket", number)
    return false unless won == true
    (flags["slowpoke_grunts"] ||= []) << number
    pbMessage(_INTL("Rocket: Nao esperava perder!"))
    true
  end

  def self.rocket_executive
    flags = progress
    return false unless flags
    if flags["slowpoke_well_cleared"]
      pbMessage(_INTL("Os Rockets foram expulsos de Azalea."))
      return false
    end
    unless earned?(PREVIOUS_BADGE) && flags["azalea_well_entered"] &&
           GRUNT_VERSIONS.all? { |number| grunt_defeated?(number) }
      pbMessage(_INTL("Derrote primeiro todos os Rockets do Poco Slowpoke."))
      return false
    end
    unless trainers_ready?
      pbMessage(_INTL("O comandante Rocket ainda nao foi instalado no piloto."))
      return false
    end
    won = TrainerBattle.start(EXECUTIVE_TYPE, "Proton", 0)
    return false unless won == true
    flags["slowpoke_well_cleared"] = true
    pbMessage(_INTL("Proton: A Equipe Rocket vai voltar!"))
    true
  end

  def self.bugsy
    state = record
    flags = progress
    return false unless state && flags
    if hive_earned?
      pbMessage(_INTL("Bugsy: Voce ja conquistou a Hive Badge!"))
      return false
    end
    unless earned?(PREVIOUS_BADGE) && flags["slowpoke_well_cleared"]
      pbMessage(_INTL("Bugsy: Ajude primeiro os Slowpoke e conclua Violet."))
      return false
    end
    unless trainers_ready?
      pbMessage(_INTL("A equipe de Bugsy ainda nao esta instalada no piloto de Johto."))
      return false
    end
    won = TrainerBattle.start(BUGSY_TYPE, "Bugsy", 0)
    return false unless won == true
    unless defined?(BlueRegions) && BlueRegions.award(state, REGION, BADGE) == true
      pbMessage(_INTL("Nao foi possivel registrar a Hive Badge. Verifique o save regional."))
      return false
    end
    flags["azalea_bugsy_defeated"] = true
    pbMessage(_INTL("Bugsy: Parabens! Esta e a Hive Badge de Johto."))
    true
  end

  # Battle after the gym, at the Ilex Forest access point. No new PBS content
  # is inferred from the map pack: three custom rival versions must be compiled.
  def self.azalea_rival
    flags = progress
    return false unless flags
    unless hive_earned? && BlueJohtoPilot.starter
      pbMessage(_INTL("O rival aguarda sua vitoria no Ginasio de Azalea."))
      return false
    end
    if flags["azalea_rival_defeated"]
      pbMessage(_INTL("Rival: Ainda vou me tornar mais forte!"))
      return false
    end
    unless trainers_ready?
      pbMessage(_INTL("As equipes do rival de Azalea ainda nao estao prontas."))
      return false
    end
    won = TrainerBattle.start(RIVAL_TYPE, "Rival", BlueJohtoPilot.rival_version)
    return false unless won == true
    flags["azalea_rival_defeated"] = true
    pbMessage(_INTL("Rival: Vou treinar e te encontrar novamente!"))
    true
  end

  def self.cut_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    # No HM is handed out here. The existing field move implementation
    # verifies both the regional HIVE badge and actual tool availability.
    BlueRegions.field_access(state, REGION, "CUT", tool_ready) == :allowed
  end
end
