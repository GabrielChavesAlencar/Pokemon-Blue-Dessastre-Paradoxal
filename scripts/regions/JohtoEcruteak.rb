# Johto phase 08/16: Routes 35-37, Ecruteak, Burned Tower, Morty.
# Not a plugin for the native Decades/Kanto installation. Install only in an
# audited, isolated Johto pilot after real map events and trainer PBS exist.
module BlueJohtoEcruteak
  REGION = "JOHTO".freeze
  PREVIOUS_BADGE = "PLAIN".freeze
  BADGE = "FOG".freeze
  READY_FILE = "Data/blue-johto-ecruteak-ready.txt".freeze
  READY_VALUE = "BLUE_JOHTO_ECRUTEAK_V1_READY".freeze
  SURF_REWARD_FILE = "Data/blue-johto-ecruteak-surf-ready.txt".freeze
  SURF_REWARD_VALUE = "BLUE_JOHTO_ECRUTEAK_SURF_V1_READY".freeze
  TOWER_RIVAL_TYPE = :BLUE_JOHTO_BURNED_TOWER_RIVAL
  DANCE_ROCKET_TYPE = :BLUE_JOHTO_DANCE_ROCKET
  MORTY_TYPE = :BLUE_JOHTO_MORTY

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

  def self.fog_earned?
    earned?(BADGE)
  end

  def self.marker?(path, value)
    File.file?(path) && File.read(path).strip == value
  rescue IOError, SystemCallError
    false
  end

  def self.trainers_ready?
    marker?(READY_FILE, READY_VALUE) &&
      defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
  end

  def self.route35
    flags = progress
    return false unless flags
    unless earned?(PREVIOUS_BADGE) && flags["ilex_passed"]
      pbMessage(_INTL("Conclua o desafio em Goldenrod e a passagem por Ilex primeiro."))
      return false
    end
    return false if flags["route35_visited"]
    flags["route35_visited"] = true
    pbMessage(_INTL("Rota 35: o National Park fica logo adiante."))
    true
  end

  # The National Park and its optional contest are separate. Visiting the park
  # must never start a fake contest or award a bug-catching prize.
  def self.national_park
    flags = progress
    return false unless flags && flags["route35_visited"]
    return false if flags["national_park_visited"]
    flags["national_park_visited"] = true
    pbMessage(_INTL("National Park: a competicao de captura ainda nao esta disponivel."))
    true
  end

  # The Sudowoodo event is implemented separately in phase 07; this gate only
  # reads the cleared flag. Map collision, removal, and battle outcome must be
  # independently verified in the pilot before enabling the actual warp.
  def self.route36
    flags = progress
    return false unless flags
    unless earned?(PREVIOUS_BADGE) && flags["route35_visited"] &&
           flags["goldenrod_squirtbottle_received"] &&
           flags["route36_sudowoodo_cleared"]
      pbMessage(_INTL("A arvore da Rota 36 ainda bloqueia o caminho para Ecruteak."))
      return false
    end
    return false if flags["route36_opened"]
    flags["route36_opened"] = true
    pbMessage(_INTL("O caminho da Rota 36 foi liberado."))
    true
  end

  def self.route37
    flags = progress
    return false unless flags && flags["route36_opened"]
    return false if flags["route37_visited"]
    flags["route37_visited"] = true
    pbMessage(_INTL("Rota 37: a cidade historica de Ecruteak esta ao norte."))
    true
  end

  def self.ecruteak_arrive
    flags = progress
    return false unless flags && flags["route37_visited"]
    return false if flags["ecruteak_visited"]
    flags["ecruteak_visited"] = true
    pbMessage(_INTL("Bem-vindo a Ecruteak. Conheca a Burned Tower e o Dance Theater."))
    true
  end

  def self.burned_tower
    flags = progress
    return false unless flags && flags["ecruteak_visited"]
    return false if flags["burned_tower_entered"]
    flags["burned_tower_entered"] = true
    pbMessage(_INTL("Burned Tower: ha sinais de antigos Pokemon lendarios por aqui."))
    true
  end

  def self.tower_rival
    flags = progress
    return false unless flags && flags["burned_tower_entered"] &&
                        earned?(PREVIOUS_BADGE)
    if flags["burned_tower_rival_defeated"]
      pbMessage(_INTL("Rival: ainda vou superar voce."))
      return false
    end
    unless trainers_ready? && BlueJohtoPilot.starter
      pbMessage(_INTL("O combate do rival ainda nao esta instalado no piloto."))
      return false
    end
    won = TrainerBattle.start(TOWER_RIVAL_TYPE, "Rival", BlueJohtoPilot.rival_version)
    return false unless won == true
    flags["burned_tower_rival_defeated"] = true
    pbMessage(_INTL("Rival: essa torre guarda algo especial. Vou continuar treinando."))
    true
  end

  # The three beasts' real sprites, positions and maps belong to the future
  # RMXP event integration. This flag is not a capture or legendary unlock.
  def self.legendary_awakening
    flags = progress
    return false unless flags && flags["burned_tower_rival_defeated"]
    return false if flags["burned_tower_beasts_awakened"]
    flags["burned_tower_beasts_awakened"] = true
    pbMessage(_INTL("Tres Pokemon misteriosos despertaram e desapareceram."))
    true
  end

  def self.dance_theater_rocket
    flags = progress
    return false unless flags && flags["ecruteak_visited"]
    return false if flags["dance_theater_rocket_defeated"]
    unless trainers_ready?
      pbMessage(_INTL("O treinador Rocket do Dance Theater ainda nao esta disponivel."))
      return false
    end
    return false unless TrainerBattle.start(DANCE_ROCKET_TYPE, "Rocket", 0) == true
    flags["dance_theater_rocket_defeated"] = true
    pbMessage(_INTL("A apresentacao das Kimono Girls esta segura novamente."))
    true
  end

  # HM03 is a placeholder until the installed item's exact key is audited.
  # The reward is *never* fabricated or repeated in native Decades/Kanto.
  def self.surf_reward
    flags = progress
    return false unless flags && flags["dance_theater_rocket_defeated"]
    return false if flags["ecruteak_surf_rewarded"]
    unless marker?(SURF_REWARD_FILE, SURF_REWARD_VALUE) &&
           defined?(GameData::Item) && GameData::Item.respond_to?(:exists?) &&
           GameData::Item.exists?(:HM03) && defined?(pbReceiveItem)
      pbMessage(_INTL("A recompensa Surf ainda nao esta instalada no piloto."))
      return false
    end
    return false unless pbReceiveItem(:HM03) == true
    flags["ecruteak_surf_rewarded"] = true
    pbMessage(_INTL("Obrigado! Use Surf quando conquistar a insígnia correta de Johto."))
    true
  end

  def self.morty
    flags = progress
    state = record
    return false unless flags && state
    if fog_earned?
      pbMessage(_INTL("Morty: voce ja conquistou a Fog Badge!"))
      return false
    end
    unless earned?(PREVIOUS_BADGE) && flags["ecruteak_visited"] &&
           flags["burned_tower_beasts_awakened"]
      pbMessage(_INTL("Morty: explore a Burned Tower antes de enfrentar o Ginasio."))
      return false
    end
    unless trainers_ready?
      pbMessage(_INTL("A equipe de Morty ainda nao esta compilada no piloto de Johto."))
      return false
    end
    won = TrainerBattle.start(MORTY_TYPE, "Morty", 0)
    return false unless won == true
    unless defined?(BlueRegions) && BlueRegions.award(state, REGION, BADGE) == true
      pbMessage(_INTL("A Fog Badge nao pode ser registrada neste save."))
      return false
    end
    flags["ecruteak_morty_defeated"] = true
    pbMessage(_INTL("Morty: parabens! Aqui esta a Fog Badge de Johto."))
    true
  end

  def self.surf_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    # Never use Kanto badges or global emeralds to bypass the local FOG rule.
    BlueRegions.field_access(state, REGION, "SURF", tool_ready) == :allowed
  end
end
