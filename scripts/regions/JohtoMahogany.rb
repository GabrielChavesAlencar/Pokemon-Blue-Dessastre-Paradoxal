# Johto phase 11/16 -- Mahogany, Lake of Rage, Rocket HQ, Pryce, Radio Tower.
# FUTURE ISOLATED PILOT ONLY: not loaded by native Decades/Kanto scripts.
# Real maps/PBS, battle result adapters, items, sprites and physical puzzles
# remain unverified. Markers must not be created by this code or CI tests.
module BlueJohtoMahogany
  REGION = "JOHTO".freeze
  PRIOR_BADGE = "MINERAL".freeze
  BADGE = "GLACIER".freeze
  GRUNTS = [0, 1].freeze
  ELECTRODES = [0, 1, 2].freeze
  RADIO_EXECUTIVES = [0, 1, 2].freeze
  LAKE_READY = "Data/blue-johto-lake-ready.txt".freeze
  LAKE_TOKEN = "BLUE_JOHTO_LAKE_V1_READY".freeze
  SCALE_READY = "Data/blue-johto-red-scale-ready.txt".freeze
  SCALE_TOKEN = "BLUE_JOHTO_RED_SCALE_V1_READY".freeze
  HQ_READY = "Data/blue-johto-rocket-hq-ready.txt".freeze
  HQ_TOKEN = "BLUE_JOHTO_ROCKET_HQ_V1_READY".freeze
  HQ_PUZZLE_READY = "Data/blue-johto-rocket-hq-puzzle-ready.txt".freeze
  HQ_PUZZLE_TOKEN = "BLUE_JOHTO_ROCKET_HQ_PUZZLE_V1_READY".freeze
  ELECTRODE_READY = "Data/blue-johto-electrode-ready.txt".freeze
  ELECTRODE_TOKEN = "BLUE_JOHTO_ELECTRODE_V1_READY".freeze
  WHIRLPOOL_READY = "Data/blue-johto-whirlpool-item-ready.txt".freeze
  WHIRLPOOL_TOKEN = "BLUE_JOHTO_WHIRLPOOL_ITEM_V1_READY".freeze
  PRYCE_READY = "Data/blue-johto-pryce-ready.txt".freeze
  PRYCE_TOKEN = "BLUE_JOHTO_PRYCE_V1_READY".freeze
  ICE_PUZZLE_READY = "Data/blue-johto-pryce-puzzle-ready.txt".freeze
  ICE_PUZZLE_TOKEN = "BLUE_JOHTO_PRYCE_PUZZLE_V1_READY".freeze
  RADIO_READY = "Data/blue-johto-radio-tower-ready.txt".freeze
  RADIO_TOKEN = "BLUE_JOHTO_RADIO_TOWER_V1_READY".freeze
  RADIO_PUZZLE_READY = "Data/blue-johto-radio-puzzle-ready.txt".freeze
  RADIO_PUZZLE_TOKEN = "BLUE_JOHTO_RADIO_PUZZLE_V1_READY".freeze

  # All item and trainer keys are provisional until reviewed against the pilot.
  RED_SCALE_ITEM = :REDSCALE
  WHIRLPOOL_ITEM = :HM06
  HQ_GRUNT = :BLUE_JOHTO_HQ_GRUNT
  HQ_PETREL = :BLUE_JOHTO_HQ_PETREL
  HQ_ARIANA = :BLUE_JOHTO_HQ_ARIANA
  PRYCE_TRAINER = :BLUE_JOHTO_PRYCE
  RADIO_PETREL = :BLUE_JOHTO_RADIO_PETREL
  RADIO_RIVAL = :BLUE_JOHTO_RADIO_RIVAL
  RADIO_EXEC = :BLUE_JOHTO_RADIO_EXEC

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

  def self.glacier_earned?
    earned?(BADGE)
  end

  def self.marker?(path, token)
    File.file?(path) && File.read(path).strip == token
  rescue IOError, SystemCallError
    false
  end

  def self.trainer_won?(path, token, kind, name, version)
    return false unless marker?(path, token) &&
                        defined?(TrainerBattle) && TrainerBattle.respond_to?(:start)
    TrainerBattle.start(kind, name, version) == true
  end

  def self.gift?(item, path, token)
    return false unless marker?(path, token) &&
                        defined?(GameData::Item) &&
                        GameData::Item.respond_to?(:exists?) &&
                        GameData::Item.exists?(item) && defined?(pbReceiveItem)
    pbReceiveItem(item) == true
  end

  def self.route42
    flags = progress
    return false unless flags && flags["ecruteak_visited"] == true &&
                        earned?(PRIOR_BADGE)
    return false if flags["route42_visited"]
    flags["route42_visited"] = true
    pbMessage(_INTL("Route 42: Mahogany Town fica alem da estrada a leste."))
    true
  end

  def self.mahogany_arrive
    flags = progress
    return false unless flags && flags["route42_visited"]
    return false if flags["mahogany_visited"]
    flags["mahogany_visited"] = true
    pbMessage(_INTL("Mahogany Town: ha relatos de atividade suspeita perto do lago."))
    true
  end

  def self.route43
    flags = progress
    return false unless flags && flags["mahogany_visited"]
    return false if flags["route43_visited"]
    flags["route43_visited"] = true
    pbMessage(_INTL("Route 43: a trilha ao norte leva ao Lake of Rage."))
    true
  end

  def self.lake_arrive
    flags = progress
    return false unless flags && flags["route43_visited"]
    return false if flags["lake_of_rage_visited"]
    flags["lake_of_rage_visited"] = true
    pbMessage(_INTL("Lake of Rage: um Gyarados vermelho perturba as aguas."))
    true
  end

  # Only a trusted, audited map event may start a Red Gyarados wild encounter.
  # No pbWildBattle call here: Essentials versions differ in result semantics.
  def self.red_gyarados_begin
    flags = progress
    return false unless flags && flags["lake_of_rage_visited"] &&
                        !flags["lake_red_gyarados_resolved"] &&
                        !flags["lake_red_gyarados_pending"]
    return false unless marker?(LAKE_READY, LAKE_TOKEN) &&
                        defined?(GameData::Species) &&
                        GameData::Species.respond_to?(:exists?) &&
                        GameData::Species.exists?(:GYARADOS)
    flags["lake_red_gyarados_pending"] = true
    true
  end

  # Call only after a version-audited battle adapter reports caught/defeated.
  # Flee, loss and an unrecognized result MUST NOT unlock Lance or the Rockets.
  def self.red_gyarados_result(result)
    flags = progress
    return false unless flags && flags["lake_red_gyarados_pending"] &&
                        marker?(LAKE_READY, LAKE_TOKEN)
    flags["lake_red_gyarados_pending"] = false
    return false unless [:caught, :defeated].include?(result)
    flags["lake_red_gyarados_resolved"] = true
    pbMessage(_INTL("O encontro com o Gyarados vermelho terminou."))
    true
  end

  def self.red_scale
    flags = progress
    return false unless flags && flags["lake_red_gyarados_resolved"] &&
                        !flags["lake_red_scale_received"]
    return false unless gift?(RED_SCALE_ITEM, SCALE_READY, SCALE_TOKEN)
    flags["lake_red_scale_received"] = true
    true
  end

  def self.lance_meeting
    flags = progress
    return false unless flags && flags["lake_red_scale_received"]
    return false if flags["lake_lance_met"]
    flags["lake_lance_met"] = true
    pbMessage(_INTL("Lance: vamos investigar a transmissao da Equipe Rocket em Mahogany."))
    true
  end

  def self.rocket_hq_enter
    flags = progress
    return false unless flags && flags["mahogany_visited"] && flags["lake_lance_met"]
    return false if flags["rocket_hq_entered"]
    flags["rocket_hq_entered"] = true
    pbMessage(_INTL("Voce encontrou uma instalacao escondida sob Mahogany."))
    true
  end

  def self.hq_grunt(number)
    flags = progress
    return false unless flags && GRUNTS.include?(number) &&
                        flags["rocket_hq_entered"] && !flags["rocket_hq_cleared"]
    beaten = flags["rocket_hq_grunts"] || []
    return false unless beaten.is_a?(Array)
    return false if beaten.include?(number)
    return false if number > 0 && !beaten.include?(number - 1)
    return false unless trainer_won?(HQ_READY, HQ_TOKEN, HQ_GRUNT, "Rocket", number)
    (flags["rocket_hq_grunts"] ||= []) << number
    true
  end

  def self.hq_security_off
    flags = progress
    return false unless flags && !flags["rocket_hq_cleared"] &&
                        (flags["rocket_hq_grunts"] || []).include?(0)
    return false if flags["rocket_hq_security_off"]
    return false unless marker?(HQ_PUZZLE_READY, HQ_PUZZLE_TOKEN)
    flags["rocket_hq_security_off"] = true
    true
  end

  def self.hq_door
    flags = progress
    return false unless flags && flags["rocket_hq_security_off"] &&
                        GRUNTS.all? { |number| (flags["rocket_hq_grunts"] || []).include?(number) }
    return false if flags["rocket_hq_door_open"]
    return false unless marker?(HQ_PUZZLE_READY, HQ_PUZZLE_TOKEN)
    flags["rocket_hq_door_open"] = true
    true
  end

  def self.hq_petrel
    flags = progress
    return false unless flags && flags["rocket_hq_door_open"] &&
                        !flags["rocket_hq_petrel_defeated"]
    return false unless trainer_won?(HQ_READY, HQ_TOKEN, HQ_PETREL, "Petrel", 0)
    flags["rocket_hq_petrel_defeated"] = true
    true
  end

  def self.hq_lance_help
    flags = progress
    return false unless flags && flags["rocket_hq_petrel_defeated"]
    return false if flags["rocket_hq_lance_helped"]
    flags["rocket_hq_lance_helped"] = true
    pbMessage(_INTL("Lance: vou ajuda-lo a interromper o sinal dos Rockets."))
    true
  end

  def self.hq_ariana
    flags = progress
    return false unless flags && flags["rocket_hq_lance_helped"] &&
                        !flags["rocket_hq_ariana_defeated"]
    return false unless trainer_won?(HQ_READY, HQ_TOKEN, HQ_ARIANA, "Ariana", 0)
    flags["rocket_hq_ariana_defeated"] = true
    true
  end

  def self.hq_electrode_begin(number)
    flags = progress
    return false unless flags && ELECTRODES.include?(number) &&
                        flags["rocket_hq_ariana_defeated"] &&
                        marker?(ELECTRODE_READY, ELECTRODE_TOKEN) &&
                        defined?(GameData::Species) &&
                        GameData::Species.respond_to?(:exists?) &&
                        GameData::Species.exists?(:ELECTRODE)
    return false if (flags["rocket_hq_electrodes"] || []).include?(number)
    return false if flags["rocket_hq_electrode_pending"]
    flags["rocket_hq_electrode_pending"] = number
    true
  end

  # Trusted map adapter resolves :caught or :defeated. Neither flee nor loss
  # permanently removes an Electrode or claims an HM.
  def self.hq_electrode_result(number, result)
    flags = progress
    return false unless flags && ELECTRODES.include?(number) &&
                        flags["rocket_hq_electrode_pending"] == number &&
                        marker?(ELECTRODE_READY, ELECTRODE_TOKEN)
    flags.delete("rocket_hq_electrode_pending")
    return false unless [:caught, :defeated].include?(result)
    (flags["rocket_hq_electrodes"] ||= []) << number
    true
  end

  def self.hq_lance_electrodes
    flags = progress
    return false unless flags && flags["rocket_hq_ariana_defeated"] &&
                        marker?(HQ_PUZZLE_READY, HQ_PUZZLE_TOKEN)
    return false if flags["rocket_hq_lance_electrodes_disabled"]
    flags["rocket_hq_lance_electrodes_disabled"] = true
    true
  end

  def self.hq_finish
    flags = progress
    return false unless flags && flags["rocket_hq_lance_electrodes_disabled"] &&
                        ELECTRODES.all? { |number| (flags["rocket_hq_electrodes"] || []).include?(number) }
    return false if flags["rocket_hq_cleared"]
    flags["rocket_hq_cleared"] = true
    pbMessage(_INTL("A transmissao dos Rockets em Mahogany foi interrompida."))
    true
  end

  def self.whirlpool_reward
    flags = progress
    return false unless flags && flags["rocket_hq_cleared"] &&
                        !flags["rocket_hq_whirlpool_received"]
    return false unless gift?(WHIRLPOOL_ITEM, WHIRLPOOL_READY, WHIRLPOOL_TOKEN)
    flags["rocket_hq_whirlpool_received"] = true
    true
  end

  def self.pryce_ice_puzzle
    flags = progress
    return false unless flags && flags["rocket_hq_cleared"] &&
                        earned?(PRIOR_BADGE) &&
                        marker?(ICE_PUZZLE_READY, ICE_PUZZLE_TOKEN)
    return false if flags["mahogany_ice_puzzle_solved"]
    flags["mahogany_ice_puzzle_solved"] = true
    true
  end

  def self.pryce
    state = record
    flags = progress
    return false unless state && flags
    return false if glacier_earned?
    return false unless earned?(PRIOR_BADGE) && flags["rocket_hq_cleared"] &&
                        flags["mahogany_ice_puzzle_solved"]
    return false unless trainer_won?(PRYCE_READY, PRYCE_TOKEN, PRYCE_TRAINER, "Pryce", 0)
    return false unless defined?(BlueRegions) &&
                        BlueRegions.award(state, REGION, BADGE) == true
    flags["mahogany_pryce_defeated"] = true
    pbMessage(_INTL("Pryce: parabens! Esta e a Glacier Badge de Johto."))
    true
  end

  def self.whirlpool_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.field_access(state, REGION, "WHIRLPOOL", tool_ready) == :allowed
  end

  # Goldenrod Radio Tower arc begins AFTER Pryce, not during Lake of Rage.
  def self.radio_takeover
    flags = progress
    return false unless flags && flags["rocket_hq_cleared"] && glacier_earned?
    return false if flags["goldenrod_radio_takeover_started"]
    flags["goldenrod_radio_takeover_started"] = true
    true
  end

  def self.radio_petrel
    flags = progress
    return false unless flags && flags["goldenrod_radio_takeover_started"] &&
                        !flags["goldenrod_radio_petrel_defeated"]
    return false unless trainer_won?(RADIO_READY, RADIO_TOKEN, RADIO_PETREL, "Petrel", 0)
    flags["goldenrod_radio_petrel_defeated"] = true
    true
  end

  def self.radio_rival
    flags = progress
    return false unless flags && flags["goldenrod_radio_petrel_defeated"] &&
                        !flags["goldenrod_radio_rival_defeated"] &&
                        defined?(BlueJohtoPilot) && BlueJohtoPilot.starter
    return false unless trainer_won?(RADIO_READY, RADIO_TOKEN, RADIO_RIVAL,
                                     "Rival", BlueJohtoPilot.rival_version)
    flags["goldenrod_radio_rival_defeated"] = true
    true
  end

  def self.radio_underground_puzzle
    flags = progress
    return false unless flags && flags["goldenrod_radio_rival_defeated"] &&
                        marker?(RADIO_PUZZLE_READY, RADIO_PUZZLE_TOKEN)
    return false if flags["goldenrod_radio_underground_solved"]
    flags["goldenrod_radio_underground_solved"] = true
    true
  end

  # Story flag only; the actual Card Key and Basement Key item IDs must be
  # audited before being awarded by the original mapped event.
  def self.radio_director_rescue
    flags = progress
    return false unless flags && flags["goldenrod_radio_underground_solved"] &&
                        marker?(RADIO_PUZZLE_READY, RADIO_PUZZLE_TOKEN)
    return false if flags["goldenrod_radio_director_rescued"]
    flags["goldenrod_radio_director_rescued"] = true
    true
  end

  def self.radio_executive(number)
    flags = progress
    return false unless flags && RADIO_EXECUTIVES.include?(number) &&
                        flags["goldenrod_radio_director_rescued"]
    beaten = flags["goldenrod_radio_executives"] || []
    return false unless beaten.is_a?(Array)
    return false if beaten.include?(number)
    return false if number > 0 && !beaten.include?(number - 1)
    name = ["Proton", "Ariana", "Archer"][number]
    return false unless trainer_won?(RADIO_READY, RADIO_TOKEN, RADIO_EXEC, name, number)
    (flags["goldenrod_radio_executives"] ||= []) << number
    true
  end

  def self.radio_finish
    flags = progress
    return false unless flags && RADIO_EXECUTIVES.all? do |number|
      (flags["goldenrod_radio_executives"] || []).include?(number)
    end
    return false if flags["goldenrod_radio_tower_cleared"]
    flags["goldenrod_radio_tower_cleared"] = true
    pbMessage(_INTL("Goldenrod Radio Tower esta livre da Equipe Rocket."))
    true
  end

  # Route 44 prepares phase 12; do not warp players into unverified maps.
  def self.route44
    flags = progress
    return false unless flags && glacier_earned? &&
                        flags["goldenrod_radio_tower_cleared"]
    return false if flags["route44_ready"]
    flags["route44_ready"] = true
    true
  end
end
