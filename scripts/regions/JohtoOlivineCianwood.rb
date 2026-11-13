# Johto phase 09/16 -- Olivine Lighthouse, Routes 38-41, Cianwood, Chuck.
# Future isolated Johto pilot ONLY. Never install in native Decades/Kanto.
# All maps, trainer PBS, item IDs, animations, and warp destinations require
# verification before any caller binds these methods to RPG::Event.
module BlueJohtoOlivineCianwood
  REGION = "JOHTO".freeze
  REQUIRED_BADGE = "FOG".freeze
  BADGE = "STORM".freeze
  LIGHTHOUSE_FLOORS = [1, 2, 3, 4, 5, 6].freeze
  CHUCK_TRAINER = :BLUE_JOHTO_CHUCK

  TRAINERS_READY = "Data/blue-johto-cianwood-ready.txt".freeze
  TRAINERS_READY_VALUE = "BLUE_JOHTO_CIANWOOD_V1_READY".freeze
  MEDICINE_READY = "Data/blue-johto-medicine-ready.txt".freeze
  MEDICINE_READY_VALUE = "BLUE_JOHTO_MEDICINE_V1_READY".freeze
  FLY_READY = "Data/blue-johto-fly-ready.txt".freeze
  FLY_READY_VALUE = "BLUE_JOHTO_FLY_V1_READY".freeze

  # Item IDs are candidate Essentials keys, NOT evidence of compiled items.
  # Each must be checked against the future pilot's GameData::Item catalog.
  MEDICINE_ITEM = :SECRETPOTION
  FLY_ITEM = :HM02

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

  def self.storm_earned?
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

  def self.surf_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.field_access(state, REGION, "SURF", tool_ready) == :allowed
  end

  def self.fly_allowed?(tool_ready = false)
    state = record
    return false unless state && defined?(BlueRegions)
    BlueRegions.field_access(state, REGION, "FLY", tool_ready) == :allowed
  end

  def self.route38
    flags = progress
    return false unless flags && earned?(REQUIRED_BADGE) &&
                        flags["ecruteak_visited"]
    return false if flags["route38_visited"]
    flags["route38_visited"] = true
    pbMessage(_INTL("Rota 38: siga para oeste em direcao ao porto de Olivine."))
    true
  end

  def self.route39
    flags = progress
    return false unless flags && flags["route38_visited"]
    return false if flags["route39_visited"]
    flags["route39_visited"] = true
    pbMessage(_INTL("Rota 39: o farol de Olivine ja pode ser visto ao longe."))
    true
  end

  def self.olivine_arrive
    flags = progress
    return false unless flags && flags["route39_visited"]
    return false if flags["olivine_visited"]
    flags["olivine_visited"] = true
    pbMessage(_INTL("Bem-vindo a Olivine! Ha algo errado com o Pokemon do farol."))
    true
  end

  def self.lighthouse_entrance
    flags = progress
    return false unless flags && flags["olivine_visited"]
    return false if flags["olivine_lighthouse_entered"]
    flags["olivine_lighthouse_entered"] = true
    flags["olivine_lighthouse_floor"] = 0
    pbMessage(_INTL("Lighthouse: suba ate Jasmine para conhecer a situacao de Ampharos."))
    true
  end

  # Logic checkpoint, NOT a physical floor transfer. Installers must verify
  # stair/warp topology, collisions, elevator and all trainer event positions.
  def self.lighthouse_floor(number)
    flags = progress
    return false unless flags && flags["olivine_lighthouse_entered"]
    return false unless LIGHTHOUSE_FLOORS.include?(number)
    previous = flags["olivine_lighthouse_floor"]
    return false unless previous.is_a?(Integer)
    return false if previous >= number
    return false unless number == previous + 1
    flags["olivine_lighthouse_floor"] = number
    pbMessage(_INTL("Lighthouse: andar {1} visitado.", number))
    true
  end

  def self.jasmine_request
    flags = progress
    return false unless flags && flags["olivine_lighthouse_floor"] == 6
    if flags["olivine_medicine_requested"]
      pbMessage(_INTL("Jasmine: por favor, traga a medicina da farmacia de Cianwood."))
      return false
    end
    flags["olivine_medicine_requested"] = true
    pbMessage(_INTL("Jasmine: Ampharos esta doente. Pode buscar a medicina em Cianwood?"))
    true
  end

  # Sailing is not granted merely by visiting Olivine. Region-local FOG, a
  # functioning Surf tool, and the previous pilot's actual HM reward are needed.
  def self.route40(tool_ready = false)
    flags = progress
    return false unless flags && flags["olivine_visited"]
    unless flags["ecruteak_surf_rewarded"] && surf_allowed?(tool_ready)
      pbMessage(_INTL("Para atravessar o mar, voce precisa de Surf e da Fog Badge."))
      return false
    end
    return false if flags["route40_surf_started"]
    flags["route40_surf_started"] = true
    pbMessage(_INTL("Rota 40: a travessia ate Cianwood comecou."))
    true
  end

  def self.route41(tool_ready = false)
    flags = progress
    return false unless flags && flags["route40_surf_started"] &&
                        surf_allowed?(tool_ready)
    return false if flags["route41_visited"]
    flags["route41_visited"] = true
    pbMessage(_INTL("Rota 41: atravesse as aguas e tome cuidado com os redemoinhos."))
    true
  end

  def self.cianwood_arrive
    flags = progress
    return false unless flags && flags["route41_visited"]
    return false if flags["cianwood_visited"]
    flags["cianwood_visited"] = true
    pbMessage(_INTL("Bem-vindo a Cianwood. A farmacia fica perto do mar."))
    true
  end

  def self.pharmacy
    flags = progress
    return false unless flags && flags["cianwood_visited"]
    if flags["cianwood_medicine_received"]
      pbMessage(_INTL("Farmaceutico: leve logo a medicina para Ampharos."))
      return false
    end
    unless flags["olivine_medicine_requested"]
      pbMessage(_INTL("Farmaceutico: esta medicina foi reservada ao Ampharos do farol."))
      return false
    end
    unless marker?(MEDICINE_READY, MEDICINE_READY_VALUE) &&
           defined?(GameData::Item) && GameData::Item.respond_to?(:exists?) &&
           GameData::Item.exists?(MEDICINE_ITEM) && defined?(pbReceiveItem)
      pbMessage(_INTL("O item de medicina ainda nao foi validado no piloto de Johto."))
      return false
    end
    return false unless pbReceiveItem(MEDICINE_ITEM) == true
    flags["cianwood_medicine_received"] = true
    pbMessage(_INTL("Farmaceutico: entregue esta medicina a Jasmine em Olivine."))
    true
  end

  # Phase 10 consumes the actual SecretPotion and heals Ampharos. Phase 09
  # MUST NOT automatically cure Ampharos or unlock Jasmine's battle.
  def self.return_to_olivine(tool_ready = false)
    flags = progress
    return false unless flags && flags["cianwood_visited"] &&
                        flags["cianwood_medicine_received"] &&
                        flags["route41_visited"] && surf_allowed?(tool_ready)
    return false if flags["olivine_returned_with_medicine"]
    flags["olivine_returned_with_medicine"] = true
    pbMessage(_INTL("Voce voltou a Olivine com a medicina. Procure Jasmine no farol."))
    true
  end

  # Gym waterfall switch: event logic only, without real collision/graphics.
  def self.chuck_waterfall
    flags = progress
    return false unless flags && flags["cianwood_visited"]
    return false if flags["cianwood_chuck_waterfall_off"]
    flags["cianwood_chuck_waterfall_off"] = true
    pbMessage(_INTL("A agua do Ginasio de Cianwood parou de cair."))
    true
  end

  def self.chuck
    flags = progress
    state = record
    return false unless flags && state
    if storm_earned?
      pbMessage(_INTL("Chuck: voce ja conquistou a Storm Badge!"))
      return false
    end
    unless earned?(REQUIRED_BADGE) && flags["cianwood_visited"] &&
           flags["cianwood_chuck_waterfall_off"]
      pbMessage(_INTL("Chuck: encontre o Ginasio de Cianwood e interrompa a queda d'agua."))
      return false
    end
    unless trainers_ready?
      pbMessage(_INTL("A equipe de Chuck ainda nao esta compilada no piloto de Johto."))
      return false
    end
    won = TrainerBattle.start(CHUCK_TRAINER, "Chuck", 0)
    return false unless won == true
    unless defined?(BlueRegions) && BlueRegions.award(state, REGION, BADGE) == true
      pbMessage(_INTL("Nao foi possivel registrar a Storm Badge neste save."))
      return false
    end
    flags["cianwood_chuck_defeated"] = true
    pbMessage(_INTL("Chuck: parabens! Voce conquistou a Storm Badge de Johto."))
    true
  end

  # The Fly item ID is only a candidate; no HM or route unlock is fabricated.
  def self.chuck_wife_fly_reward
    flags = progress
    return false unless flags && storm_earned?
    if flags["cianwood_fly_rewarded"]
      pbMessage(_INTL("Use Fly com sua Storm Badge para viajar quando disponivel."))
      return false
    end
    unless marker?(FLY_READY, FLY_READY_VALUE) &&
           defined?(GameData::Item) && GameData::Item.respond_to?(:exists?) &&
           GameData::Item.exists?(FLY_ITEM) && defined?(pbReceiveItem)
      pbMessage(_INTL("O HM Fly ainda nao esta validado no piloto de Johto."))
      return false
    end
    return false unless pbReceiveItem(FLY_ITEM) == true
    flags["cianwood_fly_rewarded"] = true
    pbMessage(_INTL("Obrigado por enfrentar Chuck! Aqui esta Fly."))
    true
  end
end
