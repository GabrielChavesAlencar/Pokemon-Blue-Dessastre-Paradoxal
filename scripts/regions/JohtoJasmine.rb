# Johto phase 10/16 -- Ampharos, Jasmine, Mineral Badge, Whirl Islands preflight.
# FUTURE ISOLATED JOHTO PILOT ONLY. No native Decades/Kanto hooks or map writes.
# MapIDs, events, item adapter, PBS trainers and island warps remain unverified.
module BlueJohtoJasmine
  REGION = "JOHTO".freeze
  REQUIRE_BADGE = "STORM".freeze
  BADGE = "MINERAL".freeze
  GYM_TRAINER = :BLUE_JOHTO_JASMINE
  TRAINERS_READY = "Data/blue-johto-jasmine-ready.txt".freeze
  TRAINERS_READY_VALUE = "BLUE_JOHTO_JASMINE_V1_READY".freeze
  CURE_READY = "Data/blue-johto-ampharos-cure-ready.txt".freeze
  CURE_READY_VALUE = "BLUE_JOHTO_AMPHAROS_CURE_V1_READY".freeze

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

  def self.mineral_earned?
    earned?(BADGE)
  end

  def self.ampharos_healed?
    flags = progress
    flags && flags["olivine_ampharos_healed"] == true
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

  def self.medicine_item
    return nil unless defined?(BlueJohtoOlivineCianwood)
    BlueJohtoOlivineCianwood::MEDICINE_ITEM
  end

  def self.medicine_present?
    item = medicine_item
    return false unless item && defined?(GameData::Item) &&
                        GameData::Item.respond_to?(:exists?) &&
                        GameData::Item.exists?(item)
    return false unless defined?($bag) && $bag &&
                        $bag.respond_to?(:quantity) && $bag.respond_to?(:remove)
    $bag.quantity(item) >= 1
  end

  # The *physical* Ampharos event and visual healing are pending RMXP binding.
  # Only consume after the Phase 09 legitimate pharmacy & return checkpoints.
  # A separate, manually verified item-adapter marker prevents early usage.
  # Installer MUST verify PokemonBag#remove returns true on success and decrements
  # quantity exactly once in the target game before creating the marker.
  def self.deliver_medicine
    flags = progress
    return false unless flags
    if ampharos_healed?
      pbMessage(_INTL("Jasmine: Ampharos ja se recuperou. Obrigada pela ajuda!"))
      return false
    end
    unless flags["olivine_medicine_requested"] == true &&
           flags["cianwood_medicine_received"] == true &&
           flags["olivine_returned_with_medicine"] == true &&
           flags["olivine_lighthouse_floor"] == 6
      pbMessage(_INTL("Jasmine: a medicina de Cianwood ainda nao chegou ao farol."))
      return false
    end
    unless marker?(CURE_READY, CURE_READY_VALUE) && medicine_present?
      pbMessage(_INTL("A entrega da medicina ainda nao foi verificada neste piloto."))
      return false
    end
    item = medicine_item
    quantity_before = $bag.quantity(item)
    removed = $bag.remove(item, 1)
    # Never record the cure if the item was not truly consumed once.
    return false unless removed == true &&
                        $bag.quantity(item) == quantity_before - 1
    flags["olivine_medicine_delivered"] = true
    flags["olivine_ampharos_healed"] = true
    pbMessage(_INTL("Ampharos se recuperou! Jasmine voltou ao Ginasio de Olivine."))
    true
  end

  def self.gym_entrance
    flags = progress
    return false unless flags
    unless ampharos_healed? && earned?(REQUIRE_BADGE)
      pbMessage(_INTL("Jasmine espera que Ampharos se recupere e que voce conclua Cianwood."))
      return false
    end
    return false if flags["olivine_gym_entered"]
    flags["olivine_gym_entered"] = true
    pbMessage(_INTL("Ginasio de Olivine: Jasmine esta pronta para batalhar."))
    true
  end

  def self.jasmine
    state = record
    flags = progress
    return false unless state && flags
    if mineral_earned?
      pbMessage(_INTL("Jasmine: voce ja recebeu a Mineral Badge de Johto!"))
      return false
    end
    unless ampharos_healed? && earned?(REQUIRE_BADGE) &&
           flags["olivine_gym_entered"] == true
      pbMessage(_INTL("Jasmine: precisamos terminar o tratamento de Ampharos primeiro."))
      return false
    end
    unless trainers_ready?
      pbMessage(_INTL("A equipe de Jasmine ainda nao esta compilada no piloto de Johto."))
      return false
    end
    return false unless TrainerBattle.start(GYM_TRAINER, "Jasmine", 0) == true
    unless defined?(BlueRegions) && BlueRegions.award(state, REGION, BADGE) == true
      pbMessage(_INTL("Nao foi possivel registrar a Mineral Badge neste save."))
      return false
    end
    flags["olivine_jasmine_defeated"] = true
    pbMessage(_INTL("Jasmine: parabens! Voce conquistou a Mineral Badge de Johto."))
    true
  end

  def self.whirlpool_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    # Whirl Islands requires GLACIER in Johto, not STORM/MINERAL or Kanto badges.
    BlueRegions.field_access(state, REGION, "WHIRLPOOL", tool_ready) == :allowed
  end

  # NO warp implementation until real island entrance/exit IDs, underwater
  # collision, tide/current behavior and backtracking have been validated.
  # This always fails closed, even after GLACIER.
  def self.whirl_islands_entry(tool_ready = false)
    return false unless record
    if !whirlpool_allowed?(tool_ready)
      pbMessage(_INTL("As Whirl Islands exigem Whirlpool e a insígnia de Johto correta."))
    else
      pbMessage(_INTL("As entradas e saidas das Whirl Islands ainda nao foram auditadas."))
    end
    false
  end
end
