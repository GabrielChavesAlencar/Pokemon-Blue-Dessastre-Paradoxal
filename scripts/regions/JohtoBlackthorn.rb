# Johto phase 12/16 -- Route 44, Ice Path, Blackthorn, Clair, Dragon's Den.
# FUTURE ISOLATED JOHTO PILOT ONLY; no native Decades/Kanto map or save hooks.
# Event positions, item IDs, PBS teams, puzzles and warp destinations must be
# validated before the pilot mounts any of these story handlers.
module BlueJohtoBlackthorn
  REGION = "JOHTO".freeze
  BADGE = "RISING".freeze
  REQUIRED_BADGES = %w[ZEPHYR HIVE PLAIN FOG STORM MINERAL GLACIER].freeze
  BOULDER_IDS = [0, 1, 2, 3].freeze
  CLAIR_TYPE = :BLUE_JOHTO_CLAIR

  ICE_READY = "Data/blue-johto-ice-path-ready.txt".freeze
  ICE_TOKEN = "BLUE_JOHTO_ICE_PATH_V1_READY".freeze
  BOULDER_READY = "Data/blue-johto-ice-boulders-ready.txt".freeze
  BOULDER_TOKEN = "BLUE_JOHTO_ICE_BOULDERS_V1_READY".freeze
  WATERFALL_READY = "Data/blue-johto-waterfall-item-ready.txt".freeze
  WATERFALL_TOKEN = "BLUE_JOHTO_WATERFALL_ITEM_V1_READY".freeze
  GYM_READY = "Data/blue-johto-blackthorn-gym-ready.txt".freeze
  GYM_TOKEN = "BLUE_JOHTO_BLACKTHORN_GYM_V1_READY".freeze
  GYM_PUZZLE_READY = "Data/blue-johto-blackthorn-puzzle-ready.txt".freeze
  GYM_PUZZLE_TOKEN = "BLUE_JOHTO_BLACKTHORN_PUZZLE_V1_READY".freeze
  DEN_READY = "Data/blue-johto-dragons-den-ready.txt".freeze
  DEN_TOKEN = "BLUE_JOHTO_DRAGONS_DEN_V1_READY".freeze
  MASTER_READY = "Data/blue-johto-dragon-master-ready.txt".freeze
  MASTER_TOKEN = "BLUE_JOHTO_DRAGON_MASTER_V1_READY".freeze

  # These are candidates, not compiled item IDs or evidence of gameplay.
  WATERFALL_ITEM = :HM07
  DRAGON_TRIAL = [
    ["Como voce deve tratar os seus Pokemon?",
     ["Como ferramentas", "Como companheiros", "Como trofeus"], 1],
    ["O que importa quando voce perde uma batalha?",
     ["Aprender e tentar novamente", "Abandonar o time"], 0],
    ["O que demonstra forca entre treinador e Pokemon?",
     ["Respeito e confianca", "Apenas o nivel"], 0]
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

  def self.rising_earned?
    earned?(BADGE)
  end

  def self.seven_badges?
    state = record
    return false unless state && defined?(BlueRegions)
    badges = BlueRegions.local_achievements(state, REGION)
    REQUIRED_BADGES.all? { |key| badges.include?(key) }
  end

  def self.marker?(path, token)
    File.file?(path) && File.read(path).strip == token
  rescue IOError, SystemCallError
    false
  end

  def self.strength_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.field_access(state, REGION, "STRENGTH", tool_ready) == :allowed
  end

  def self.whirlpool_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.field_access(state, REGION, "WHIRLPOOL", tool_ready) == :allowed
  end

  def self.waterfall_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.field_access(state, REGION, "WATERFALL", tool_ready) == :allowed
  end

  def self.route44
    flags = progress
    return false unless flags && seven_badges? &&
                        flags["goldenrod_radio_tower_cleared"] == true &&
                        flags["route44_ready"] == true
    return false if flags["route44_visited"]
    flags["route44_visited"] = true
    pbMessage(_INTL("Rota 44: Ice Path leva ate Blackthorn City."))
    true
  end

  def self.ice_path_enter
    flags = progress
    return false unless flags && flags["route44_visited"] &&
                        marker?(ICE_READY, ICE_TOKEN)
    return false if flags["ice_path_entered"]
    flags["ice_path_entered"] = true
    pbMessage(_INTL("Ice Path: o gelo e as pedras exigem atencao."))
    true
  end

  # Each step must be bound to a separately audited ice sliding event.
  # No coordinate, collision, animation or solved maze is fabricated here.
  def self.ice_slide
    flags = progress
    return false unless flags && flags["ice_path_entered"] &&
                        marker?(ICE_READY, ICE_TOKEN)
    return false if flags["ice_path_slide_solved"]
    flags["ice_path_slide_solved"] = true
    true
  end

  def self.ice_boulder(number, tool_ready = false)
    flags = progress
    return false unless flags && BOULDER_IDS.include?(number) &&
                        flags["ice_path_slide_solved"] &&
                        strength_allowed?(tool_ready) &&
                        marker?(BOULDER_READY, BOULDER_TOKEN)
    solved = flags["ice_path_boulders"] || []
    return false unless solved.is_a?(Array)
    return false if solved.include?(number)
    # Physical placements can be independent: no invented boulder ordering.
    (flags["ice_path_boulders"] ||= []) << number
    true
  end

  def self.boulders_complete?
    flags = progress
    flags && BOULDER_IDS.all? do |number|
      (flags["ice_path_boulders"] || []).include?(number)
    end
  end

  def self.waterfall_item
    flags = progress
    return false unless flags && flags["ice_path_entered"] &&
                        !flags["ice_path_waterfall_received"] &&
                        marker?(WATERFALL_READY, WATERFALL_TOKEN) &&
                        defined?(GameData::Item) &&
                        GameData::Item.respond_to?(:exists?) &&
                        GameData::Item.exists?(WATERFALL_ITEM) &&
                        defined?(pbReceiveItem)
    return false unless pbReceiveItem(WATERFALL_ITEM) == true
    flags["ice_path_waterfall_received"] = true
    pbMessage(_INTL("Voce encontrou uma tecnica para atravessar cachoeiras."))
    true
  end

  def self.ice_path_exit
    flags = progress
    return false unless flags && flags["ice_path_slide_solved"] &&
                        boulders_complete? &&
                        marker?(ICE_READY, ICE_TOKEN)
    return false if flags["ice_path_cleared"]
    flags["ice_path_cleared"] = true
    pbMessage(_INTL("Voce atravessou Ice Path com seguranca."))
    true
  end

  def self.blackthorn_arrive
    flags = progress
    return false unless flags && flags["ice_path_cleared"]
    return false if flags["blackthorn_visited"]
    flags["blackthorn_visited"] = true
    pbMessage(_INTL("Blackthorn City: a ultima insígnia de Johto esta aqui."))
    true
  end

  # The real HGSS rotating platform maze must be installed in the map.
  def self.clair_gym_puzzle
    flags = progress
    return false unless flags && flags["blackthorn_visited"] &&
                        seven_badges? &&
                        marker?(GYM_PUZZLE_READY, GYM_PUZZLE_TOKEN)
    return false if flags["blackthorn_gym_puzzle_solved"]
    flags["blackthorn_gym_puzzle_solved"] = true
    true
  end

  # Clair's battle alone never awards RISING.
  def self.clair
    flags = progress
    return false unless flags && flags["blackthorn_gym_puzzle_solved"] &&
                        seven_badges?
    return false if flags["blackthorn_clair_defeated"] || rising_earned?
    unless marker?(GYM_READY, GYM_TOKEN) &&
           defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
      pbMessage(_INTL("A equipe de Clair ainda nao foi compilada no piloto."))
      return false
    end
    return false unless TrainerBattle.start(CLAIR_TYPE, "Clair", 0) == true
    flags["blackthorn_clair_defeated"] = true
    pbMessage(_INTL("Clair: procure o Dragon Master na Dragon's Den."))
    true
  end

  def self.dragons_den_enter
    flags = progress
    return false unless flags && flags["blackthorn_clair_defeated"] &&
                        marker?(DEN_READY, DEN_TOKEN)
    return false if flags["dragons_den_entered"]
    flags["dragons_den_entered"] = true
    pbMessage(_INTL("Dragon's Den: a prova final esta alem do redemoinho."))
    true
  end

  def self.dragon_shrine_access(tool_ready = false)
    flags = progress
    return false unless flags && flags["dragons_den_entered"] &&
                        flags["rocket_hq_whirlpool_received"] == true &&
                        whirlpool_allowed?(tool_ready) &&
                        marker?(DEN_READY, DEN_TOKEN)
    return false if flags["dragon_shrine_reached"]
    flags["dragon_shrine_reached"] = true
    true
  end

  # Three new original ethics questions; no Dragon Fang requirement for HGSS
  # baseline. Crystal variant must be designed separately, not implicitly.
  def self.dragon_master_trial
    flags = progress
    return false unless flags && flags["blackthorn_clair_defeated"] &&
                        flags["dragon_shrine_reached"] &&
                        marker?(MASTER_READY, MASTER_TOKEN)
    if flags["dragon_master_approved"]
      pbMessage(_INTL("Dragon Master: voce ja demonstrou seu respeito."))
      return false
    end
    DRAGON_TRIAL.each do |question, options, correct|
      answer = pbMessage(_INTL(question),
                         options + [_INTL("Voltar")], options.length)
      unless answer.is_a?(Integer) && answer == correct
        pbMessage(_INTL("Dragon Master: reflita e tente novamente."))
        return false
      end
    end
    flags["dragon_master_approved"] = true
    pbMessage(_INTL("Dragon Master: voce demonstrou o respeito necessario."))
    true
  end

  # HGSS: Clair's return to the Den awards RISING only after Master approval.
  def self.clair_rising_badge
    state = record
    flags = progress
    return false unless state && flags
    return false if rising_earned?
    return false unless flags["blackthorn_clair_defeated"] == true &&
                        flags["dragon_master_approved"] == true &&
                        flags["dragon_shrine_reached"] == true &&
                        marker?(MASTER_READY, MASTER_TOKEN)
    return false unless defined?(BlueRegions) &&
                        BlueRegions.award(state, REGION, BADGE) == true
    flags["blackthorn_rising_claimed"] = true
    pbMessage(_INTL("Clair: aqui esta a Rising Badge de Johto."))
    true
  end

  def self.specials_unlocked?
    state = record
    return false unless state && defined?(BlueRegions)
    rising_earned? && BlueRegions.allow_specials?(state, REGION) == true
  end

  def self.route45
    flags = progress
    return false unless flags && rising_earned? &&
                        flags["blackthorn_visited"]
    return false if flags["route45_visited"]
    flags["route45_visited"] = true
    true
  end

  def self.route46
    flags = progress
    return false unless flags && flags["route45_visited"]
    return false if flags["route46_visited"]
    flags["route46_visited"] = true
    true
  end

  # Dark Cave is NOT physically staged: do not warp into unknown maps.
  def self.dark_cave_entry
    return false unless record
    pbMessage(_INTL("As entradas de Dark Cave ainda nao foram auditadas."))
    false
  end

  # Prepares a handoff to phase 13, NOT a travel/league unlock in Game.exe.
  def self.league_handoff
    flags = progress
    return false unless flags && flags["blackthorn_rising_claimed"] &&
                        flags["dragon_master_approved"] &&
                        rising_earned? && seven_badges? &&
                        flags["goldenrod_radio_tower_cleared"]
    return false if flags["johto_league_approach_ready"]
    flags["johto_league_approach_ready"] = true
    pbMessage(_INTL("As oito insígnias de Johto foram conquistadas."))
    true
  end
end
