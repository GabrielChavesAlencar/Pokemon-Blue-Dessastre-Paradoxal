# Johto phase 13/16 -- Tohjo Falls, Victory Road, Elite Four and Lance.
# STORY CONTRACT FOR A FUTURE, AUDITED JOHTO PILOT. NOT LOADED IN GAME.EXE.
# No native Kanto/Decades Hall of Fame, badge, map, switch or save is changed.
module BlueJohtoLeague
  REGION = "JOHTO".freeze
  BADGES = %w[ZEPHYR HIVE PLAIN FOG STORM MINERAL GLACIER RISING].freeze
  ELITE = [
    [:BLUE_JOHTO_ELITE_WILL, "Will"],
    [:BLUE_JOHTO_ELITE_KOGA, "Koga"],
    [:BLUE_JOHTO_ELITE_BRUNO, "Bruno"],
    [:BLUE_JOHTO_ELITE_KAREN, "Karen"]
  ].freeze
  CHAMPION = :BLUE_JOHTO_CHAMPION_LANCE
  RIVAL = :BLUE_JOHTO_VICTORY_ROAD_RIVAL
  MAP_READY = "Data/blue-johto-league-route-ready.txt".freeze
  MAP_TOKEN = "BLUE_JOHTO_LEAGUE_ROUTE_V1_READY".freeze
  RIVAL_READY = "Data/blue-johto-victory-rival-ready.txt".freeze
  RIVAL_TOKEN = "BLUE_JOHTO_VICTORY_RIVAL_V1_READY".freeze
  PBS_READY = "Data/blue-johto-league-trainers-ready.txt".freeze
  PBS_TOKEN = "BLUE_JOHTO_LEAGUE_TRAINERS_V1_READY".freeze
  HOF_READY = "Data/blue-johto-hall-of-fame-ready.txt".freeze
  HOF_TOKEN = "BLUE_JOHTO_HALL_OF_FAME_V1_READY".freeze

  def self.record
    return nil unless defined?(BlueJohtoPilot)
    BlueJohtoPilot.regional_state
  end

  def self.progress
    return nil unless record
    BlueJohtoPilot.progress
  end

  def self.marker?(path, expected)
    File.file?(path) && File.read(path).strip == expected
  rescue IOError, SystemCallError
    false
  end

  def self.eight_badges?
    state = record
    return false unless state && defined?(BlueRegions)
    local = BlueRegions.local_achievements(state, REGION)
    BADGES.all? { |badge| local.include?(badge) }
  end

  def self.league_cleared?
    state = record
    state && state["leagues"].is_a?(Array) && state["leagues"].include?(REGION)
  end

  def self.eligible?
    flags = progress
    eight_badges? && flags && flags["johto_league_approach_ready"] == true &&
      flags["blackthorn_rising_claimed"] == true &&
      flags["dragon_master_approved"] == true &&
      flags["goldenrod_radio_tower_cleared"] == true
  end

  def self.surf_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.field_access(state, REGION, "SURF", tool_ready) == :allowed
  end

  def self.waterfall_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.field_access(state, REGION, "WATERFALL", tool_ready) == :allowed
  end

  # Route 27 must be entered from the audited New Bark/Johto side, never by
  # reusing Kanto's Indigo Plateau event IDs or player coordinates.
  def self.new_bark_return
    flags = progress
    return false unless eligible? && flags
    return false if flags["johto_league_new_bark_return"]
    flags["johto_league_new_bark_return"] = true
    pbMessage(_INTL("New Bark: o caminho para a Liga segue para o leste."))
    true
  end

  def self.route27(tool_ready = false)
    flags = progress
    return false unless eligible? && flags &&
                        flags["johto_league_new_bark_return"] &&
                        surf_allowed?(tool_ready) &&
                        marker?(MAP_READY, MAP_TOKEN)
    return false if flags["johto_route27_entered"]
    flags["johto_route27_entered"] = true
    true
  end

  def self.tohjo_falls_enter
    flags = progress
    return false unless flags && flags["johto_route27_entered"] &&
                        marker?(MAP_READY, MAP_TOKEN)
    return false if flags["johto_tohjo_entered"]
    flags["johto_tohjo_entered"] = true
    pbMessage(_INTL("Tohjo Falls: uma cachoeira separa voce do proximo caminho."))
    true
  end

  def self.tohjo_waterfall(tool_ready = false)
    flags = progress
    return false unless flags && flags["johto_tohjo_entered"] &&
                        flags["ice_path_waterfall_received"] == true &&
                        waterfall_allowed?(tool_ready) &&
                        marker?(MAP_READY, MAP_TOKEN)
    return false if flags["johto_tohjo_waterfall_crossed"]
    flags["johto_tohjo_waterfall_crossed"] = true
    true
  end

  def self.route26
    flags = progress
    return false unless flags && flags["johto_tohjo_waterfall_crossed"] &&
                        marker?(MAP_READY, MAP_TOKEN)
    return false if flags["johto_route26_entered"]
    flags["johto_route26_entered"] = true
    true
  end

  def self.victory_road
    flags = progress
    return false unless flags && flags["johto_route26_entered"] &&
                        eight_badges? && marker?(MAP_READY, MAP_TOKEN)
    return false if flags["johto_victory_road_entered"]
    flags["johto_victory_road_entered"] = true
    pbMessage(_INTL("Victory Road: o ultimo desafio antes da Liga de Johto."))
    true
  end

  def self.victory_road_rival
    flags = progress
    return false unless flags && flags["johto_victory_road_entered"] &&
                        !flags["johto_victory_rival_defeated"]
    return false unless marker?(RIVAL_READY, RIVAL_TOKEN) &&
                        defined?(BlueJohtoPilot) && BlueJohtoPilot.starter &&
                        defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
    return false unless TrainerBattle.start(RIVAL, "Rival",
                                          BlueJohtoPilot.rival_version) == true
    flags["johto_victory_rival_defeated"] = true
    true
  end

  def self.indigo_plateau_arrive
    flags = progress
    return false unless flags && flags["johto_victory_rival_defeated"] &&
                        marker?(MAP_READY, MAP_TOKEN)
    return false if flags["johto_indigo_arrived"]
    flags["johto_indigo_arrived"] = true
    pbMessage(_INTL("Indigo Plateau: somente a campanha Johto foi selecionada."))
    true
  end

  def self.reset_challenge
    flags = progress
    return false unless flags && !league_cleared? &&
                        flags["johto_league_active"] == true
    flags["johto_league_active"] = false
    flags["johto_league_step"] = 0
    flags["johto_league_lance_won"] = false
    flags["johto_league_hof_pending"] = false
    true
  end

  # Always restart at Will after an interrupted/defeated attempt. No
  # Elite Four victory switches from Kanto are read or written.
  def self.begin_challenge
    flags = progress
    return false unless eligible? && flags &&
                        flags["johto_indigo_arrived"] &&
                        !league_cleared? &&
                        marker?(PBS_READY, PBS_TOKEN) &&
                        defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
    return false if flags["johto_league_active"]
    flags["johto_league_step"] = 0
    flags["johto_league_lance_won"] = false
    flags["johto_league_hof_pending"] = false
    flags["johto_league_active"] = true
    true
  end

  def self.elite_four(number)
    flags = progress
    return false unless flags && number.is_a?(Integer) &&
                        number >= 0 && number < ELITE.length &&
                        flags["johto_league_active"] &&
                        flags["johto_league_step"] == number &&
                        !league_cleared?
    return false unless marker?(PBS_READY, PBS_TOKEN) &&
                        defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
    type, name = ELITE[number]
    won = TrainerBattle.start(type, name, 0)
    unless won == true
      reset_challenge
      return false
    end
    flags["johto_league_step"] = number + 1
    true
  end

  def self.champion_lance
    flags = progress
    return false unless flags && flags["johto_league_active"] &&
                        flags["johto_league_step"] == ELITE.length &&
                        !flags["johto_league_lance_won"] && !league_cleared?
    return false unless marker?(PBS_READY, PBS_TOKEN) &&
                        defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
    won = TrainerBattle.start(CHAMPION, "Lance", 0)
    unless won == true
      reset_challenge
      return false
    end
    flags["johto_league_lance_won"] = true
    pbMessage(_INTL("Lance: voce venceu o desafio de Johto. Prepare o Hall of Fame."))
    true
  end

  # A verified map event starts Hall of Fame, but this is NOT proof that
  # Hall of Fame/save recording succeeded.
  def self.hall_of_fame_begin
    flags = progress
    return false unless flags && flags["johto_league_active"] &&
                        flags["johto_league_step"] == ELITE.length &&
                        flags["johto_league_lance_won"] == true &&
                        !flags["johto_league_hof_pending"] &&
                        !league_cleared? && marker?(HOF_READY, HOF_TOKEN)
    flags["johto_league_hof_pending"] = true
    true
  end

  # Only an adapter verified against Essentials' actual Hall of Fame and
  # persisted save outcome may report :recorded. A failed/cancelled recording
  # cannot complete Johto. No global Hall of Fame call is invented here.
  def self.hall_of_fame_result(result)
    state = record
    flags = progress
    return false unless state && flags &&
                        flags["johto_league_active"] &&
                        flags["johto_league_hof_pending"] &&
                        flags["johto_league_lance_won"] &&
                        flags["johto_league_step"] == ELITE.length &&
                        marker?(HOF_READY, HOF_TOKEN)
    return false unless result == :recorded
    return false unless defined?(BlueRegions) &&
                        BlueRegions.complete_league(state, REGION) == true
    flags["johto_league_hof_pending"] = false
    flags["johto_league_active"] = false
    flags["johto_league_cleared"] = true
    pbMessage(_INTL("Liga de Johto concluida. O Hall of Fame foi registrado."))
    true
  end

  # The starting city's travel NPC is a future physical map event; this
  # method never creates an NPC, transfers the player, changes party or boxes.
  def self.travel_agent_intro
    flags = progress
    return false unless flags && flags["johto_league_cleared"] &&
                        league_cleared?
    return false if flags["johto_travel_agent_met"]
    flags["johto_travel_agent_met"] = true
    pbMessage(_INTL("New Bark: as regioes vizinhas foram liberadas no circuito."))
    true
  end

  def self.region_unlock_preview
    state = record
    return [] unless state && league_cleared? && defined?(BlueRegions)
    BlueRegions.unlocked(state) & ["KANTO", "HOENN"]
  end
end
