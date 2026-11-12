# Johto phase 07/16 -- Ilex Forest, Route 34, Goldenrod, Whitney.
# Loaded ONLY by a future audited, separately installed Johto pilot.
# No native Decades/Kanto scripts, maps, badges or saves are modified.
module BlueJohtoGoldenrod
  REGION = "JOHTO".freeze
  REQUIRE_BADGE = "HIVE".freeze
  BADGE = "PLAIN".freeze

  GYM_TRAINER = :BLUE_JOHTO_WHITNEY
  TRAINERS_READY = "Data/blue-johto-goldenrod-ready.txt".freeze
  TRAINERS_READY_VALUE = "BLUE_JOHTO_GOLDENROD_V1_READY".freeze
  CUT_REWARD_READY = "Data/blue-johto-ilex-cut-ready.txt".freeze
  CUT_REWARD_READY_VALUE = "BLUE_JOHTO_ILEX_CUT_V1_READY".freeze
  FLOWER_READY = "Data/blue-johto-flower-shop-ready.txt".freeze
  FLOWER_READY_VALUE = "BLUE_JOHTO_FLOWER_SHOP_V1_READY".freeze
  SUDOWOODO_READY = "Data/blue-johto-sudowoodo-ready.txt".freeze
  SUDOWOODO_READY_VALUE = "BLUE_JOHTO_SUDOWOODO_V1_READY".freeze
  FARFETCHD_IDS = [0, 1].freeze

  # Short original quiz about Blue's regional rules, not copyrighted game dialog.
  RADIO_QUESTIONS = [
    ["Qual insígnia de Johto permite Cut, com ferramenta adequada?",
     ["Zephyr", "Hive", "Plain"], 1],
    ["Uma insígnia de Kanto substitui a Hive de Johto?",
     ["Sim", "Nao"], 1],
    ["As insígnias de Johto também somam esmeraldas ao total?",
     ["Sim", "Nao"], 0]
  ].freeze

  def self.record
    return nil unless defined?(BlueJohtoPilot)
    BlueJohtoPilot.regional_state
  end

  def self.progress
    return nil unless record
    BlueJohtoPilot.progress
  end

  def self.earned?(badge)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.local_achievements(state, REGION).include?(badge)
  end

  def self.plain_earned?
    earned?(BADGE)
  end

  def self.marker?(path, expected)
    File.file?(path) && File.read(path).strip == expected
  rescue IOError, SystemCallError
    false
  end

  def self.trainers_ready?
    marker?(TRAINERS_READY, TRAINERS_READY_VALUE) &&
      defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
  end

  def self.intro_complete?
    flags = progress
    flags && earned?(REQUIRE_BADGE) &&
      flags["azalea_rival_defeated"] == true
  end

  def self.ilex_entrance
    flags = progress
    return false unless flags
    unless intro_complete?
      pbMessage(_INTL("Antes de entrar em Ilex, vença Bugsy e o rival em Azalea."))
      return false
    end
    return false if flags["ilex_entered"]
    flags["ilex_entered"] = true
    pbMessage(_INTL("Ilex Forest: os dois Farfetch'd do lenhador fugiram pela floresta."))
    true
  end

  def self.woodcutter
    flags = progress
    return false unless flags && intro_complete? && flags["ilex_entered"]
    if flags["ilex_woodcutter_met"]
      pbMessage(_INTL("Lenhador: procure meus dois Farfetch'd na floresta."))
      return false
    end
    flags["ilex_woodcutter_met"] = true
    pbMessage(_INTL("Lenhador: dois Farfetch'd escaparam. Pode me ajudar a trazê-los de volta?"))
    true
  end

  def self.farfetchd_captured?(number)
    flags = progress
    flags && flags["ilex_farfetchd"].is_a?(Array) &&
      flags["ilex_farfetchd"].include?(number)
  end

  # Caller must bind this to a distinct, validated RPG::Event with correct
  # position and facing; this logic doesn't claim to solve collision/AI yet.
  def self.farfetchd(number)
    flags = progress
    return false unless flags && FARFETCHD_IDS.include?(number)
    unless intro_complete? && flags["ilex_entered"] && flags["ilex_woodcutter_met"]
      pbMessage(_INTL("Fale primeiro com o lenhador e entre em Ilex Forest."))
      return false
    end
    if farfetchd_captured?(number)
      pbMessage(_INTL("Este Farfetch'd ja voltou para o lenhador."))
      return false
    end
    if number > 0 && !farfetchd_captured?(number - 1)
      pbMessage(_INTL("Encontre primeiro o Farfetch'd mais proximo."))
      return false
    end
    (flags["ilex_farfetchd"] ||= []) << number
    pbMessage(_INTL("O Farfetch'd voltou para o lenhador!"))
    true
  end

  def self.forest_puzzle_complete?
    FARFETCHD_IDS.all? { |number| farfetchd_captured?(number) }
  end

  def self.cut_reward
    flags = progress
    return false unless flags
    if flags["ilex_cut_rewarded"]
      pbMessage(_INTL("Lenhador: obrigado por salvar os meus Farfetch'd!"))
      return false
    end
    unless intro_complete? && forest_puzzle_complete?
      pbMessage(_INTL("Lenhador: encontre os dois Farfetch'd primeiro."))
      return false
    end
    # The actual item ID is not assumed: requires existing HM01 in the
    # local game's item catalog AND a verified pilot-only reward marker.
    unless marker?(CUT_REWARD_READY, CUT_REWARD_READY_VALUE) &&
           defined?(GameData::Item) && GameData::Item.respond_to?(:exists?) &&
           GameData::Item.exists?(:HM01) && defined?(pbReceiveItem)
      pbMessage(_INTL("A recompensa Cut ainda nao foi instalada no piloto de Johto."))
      return false
    end
    return false unless pbReceiveItem(:HM01) == true
    flags["ilex_cut_rewarded"] = true
    pbMessage(_INTL("Lenhador: use Cut para prosseguir por Ilex Forest."))
    true
  end

  def self.forest_exit(tool_ready = false)
    flags = progress
    return false unless flags
    unless flags["ilex_cut_rewarded"] &&
           defined?(BlueRegions) &&
           BlueRegions.field_access(record, REGION, "CUT", tool_ready) == :allowed
      pbMessage(_INTL("Para sair de Ilex, salve os Farfetch'd e use Cut com a Hive Badge."))
      return false
    end
    return false if flags["ilex_passed"]
    flags["ilex_passed"] = true
    pbMessage(_INTL("Voce encontrou a trilha para a Rota 34 e Goldenrod!"))
    true
  end

  def self.day_care
    flags = progress
    return false unless flags && flags["ilex_passed"]
    if flags["route34_daycare_met"]
      pbMessage(_INTL("Day Care: volte para conhecer nossos servicos quando estiverem prontos."))
      return false
    end
    flags["route34_daycare_met"] = true
    pbMessage(_INTL("Day Care: cuidamos de Pokemon aqui na Rota 34."))
    true
  end

  def self.goldenrod_arrive
    flags = progress
    return false unless flags && flags["ilex_passed"]
    return false if flags["goldenrod_visited"]
    flags["goldenrod_visited"] = true
    pbMessage(_INTL("Bem-vindo a Goldenrod! Conheca a Radio Tower, o Mart e o Ginasio."))
    true
  end

  def self.radio_quiz
    flags = progress
    return false unless flags && flags["ilex_passed"]
    if flags["goldenrod_radio_quiz"]
      pbMessage(_INTL("Radio Tower: voce ja passou no quiz regional!"))
      return false
    end
    RADIO_QUESTIONS.each do |question, answers, correct|
      choice = pbMessage(_INTL(question), answers + [_INTL("Voltar")], answers.length)
      unless choice.is_a?(Integer) && choice == correct
        pbMessage(_INTL("Radio Tower: tente novamente quando quiser."))
        return false
      end
    end
    flags["goldenrod_radio_quiz"] = true
    pbMessage(_INTL("Radio Tower: acertou! Pode visitar o Ginasio de Goldenrod."))
    true
  end

  def self.underground
    flags = progress
    return false unless flags && flags["ilex_passed"]
    return false if flags["goldenrod_underground_met"]
    flags["goldenrod_underground_met"] = true
    pbMessage(_INTL("Goldenrod Underground: explore as lojas pelas entradas da cidade."))
    true
  end

  def self.whitney
    flags = progress
    state = record
    return false unless flags && state
    if plain_earned?
      pbMessage(_INTL("Whitney: voce ja conquistou a Plain Badge!"))
      return false
    end
    if flags["goldenrod_whitney_won"]
      pbMessage(_INTL("Whitney: snif... fale comigo novamente para receber a insígnia."))
      return false
    end
    unless earned?(REQUIRE_BADGE) && flags["ilex_passed"] &&
           flags["goldenrod_radio_quiz"]
      pbMessage(_INTL("Whitney: conclua Ilex Forest e o quiz da Radio Tower primeiro!"))
      return false
    end
    unless trainers_ready?
      pbMessage(_INTL("A equipe de Whitney ainda nao foi compilada no piloto de Johto."))
      return false
    end
    return false unless TrainerBattle.start(GYM_TRAINER, "Whitney", 0) == true
    flags["goldenrod_whitney_won"] = true
    pbMessage(_INTL("Whitney: buaaa! Eu perdi! Fale comigo de novo..."))
    true
  end

  # Two-step sequence mirrors the crying Whitney moment. Award once only
  # after an actual won battle, never on entering the gym or losing.
  def self.whitney_badge
    flags = progress
    state = record
    return false unless flags && state
    return false if plain_earned?
    unless flags["goldenrod_whitney_won"]
      pbMessage(_INTL("Ainda e necessario vencer Whitney."))
      return false
    end
    return false unless defined?(BlueRegions) &&
                        BlueRegions.award(state, REGION, BADGE) == true
    flags["goldenrod_plain_claimed"] = true
    pbMessage(_INTL("Whitney: pronto! Esta e a Plain Badge de Johto."))
    true
  end

  def self.strength_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.field_access(state, REGION, "STRENGTH", tool_ready) == :allowed
  end

  def self.flower_shop
    flags = progress
    return false unless flags && plain_earned?
    return false if flags["goldenrod_squirtbottle_received"]
    unless marker?(FLOWER_READY, FLOWER_READY_VALUE) &&
           defined?(GameData::Item) && GameData::Item.respond_to?(:exists?) &&
           GameData::Item.exists?(:SQUIRTBOTTLE) && defined?(pbReceiveItem)
      pbMessage(_INTL("A SquirtBottle ainda nao foi instalada no piloto de Johto."))
      return false
    end
    return false unless pbReceiveItem(:SQUIRTBOTTLE) == true
    flags["goldenrod_squirtbottle_received"] = true
    pbMessage(_INTL("Florista: cuide desta SquirtBottle e observe a arvore da Rota 36!"))
    true
  end

  # Optional Route 36 encounter preview. No foreign scripted event is
  # imported. With no audited map/event or verified wild encounter marker,
  # this remains blocked even after Whitney.
  def self.sudowoodo
    flags = progress
    return false unless flags && plain_earned? &&
                        flags["goldenrod_squirtbottle_received"]
    return false if flags["route36_sudowoodo_cleared"]
    unless marker?(SUDOWOODO_READY, SUDOWOODO_READY_VALUE) &&
           defined?(GameData::Species) &&
           GameData::Species.respond_to?(:exists?) &&
           GameData::Species.exists?(:SUDOWOODO) &&
           defined?(pbWildBattle) &&
           defined?($bag) && $bag && $bag.respond_to?(:has?) &&
           $bag.has?(:SQUIRTBOTTLE)
      pbMessage(_INTL("A arvore da Rota 36 ainda nao pode ser enfrentada no piloto."))
      return false
    end
    return false unless pbWildBattle(:SUDOWOODO, 20) == true
    flags["route36_sudowoodo_cleared"] = true
    pbMessage(_INTL("A passagem da Rota 36 foi liberada!"))
    true
  end
end
