# Authored K05 runtime. Never infer a Tower victory from a trainer's name:
# Jody appears twice in the source (different floors and victory keys).
module BlueKantoTower
  RIVAL_KEY = "KANTO_TOWER_RIVAL".freeze
  RIVAL_LANES = [3,6].freeze
  RIVAL_TYPE = :BLUE_KANTO_RIVAL_TOWER
  RIVAL_VERSIONS = {BULBASAUR:51,CHARMANDER:52,SQUIRTLE:53}.freeze

  def self.rival
    version = RIVAL_VERSIONS[BlueKantoPilot.starter]
    return false unless version && on_floor?([101])
    wins = (BlueKantoPilot.progress["pilot_wins"] ||= [])
    unless wins.include?(RIVAL_KEY)
      pbMessage(BlueKantoPilot.t("Gary: What brings you to the Tower? Let's see how your team is doing!",
                                "Gary: O que trouxe você à Torre? Quero ver como está sua equipe!"))
      return false unless start_trainer!(RIVAL_TYPE,"Blue",version,RIVAL_KEY)
      wins << RIVAL_KEY
    end
    return false unless on_floor?([101])
    RIVAL_LANES.each { |id| BlueKantoPilot.sync_trainer_event(RIVAL_KEY,"Blue",id) }
    true
  end

  def self.start_trainer!(type,name,version,key)
    raise "Missing compiled Tower trainer #{name}/#{version}" unless GameData::Trainer.exists?(type,name,version)
    setBattleRule("cannotLose")
    TrainerBattle.start(type,name,version)
  rescue StandardError => error
    BlueKantoPilot.log_trainer_failure(error,type,name,key,version,"k05_tower")
    $game_temp.clear_battle_rules if $game_temp && $game_temp.respond_to?(:clear_battle_rules)
    pbMessage(BlueKantoPilot.t("This battle could not start. Nothing was recorded.",
                              "A batalha não pôde começar. Nada foi registrado."))
    false
  end

  def self.channeler(source, event_id, name)
    return false unless (102..105).cover?(source) && BlueKantoPilot.starter &&
      BlueKantoPilot.kanto_current? && $game_map &&
      $game_map.map_id == BlueKantoPilot.kanto_map_id(source) && $game_map.events[event_id]
    type = :BLUE_KANTO_CHANNELER
    key = "KANTO_TOWER_%03d_%03d" % [source,event_id]
    wins = (BlueKantoPilot.progress["pilot_wins"] ||= [])
    unless wins.include?(key)
      return false unless start_trainer!(type,name,0,key)
      wins << key
    end
    return false unless $game_map.map_id == BlueKantoPilot.kanto_map_id(source)
    BlueKantoPilot.sync_trainer_event(key,name,event_id)
  end
end

module BlueKantoTower
  def self.on_floor?(sources)
    return false unless $game_map && BlueKantoPilot.kanto_current?
    here = $game_map.map_id
    sources.any? { |sid| BlueKantoPilot.kanto_map_id(sid) == here }
  end

  def self.unidentified_appearance?
    on_floor?(102..105) && !(
      BlueKantoPilot.progress["pilot_rocket_hideout_scope"] == true &&
      $bag && GameData::Item.exists?(:SILPHSCOPE) && $bag.has?(:SILPHSCOPE))
  end

  # Handles both ordinary and double encounter dispatches before a battle can
  # render a species name, consume a Poké Ball or award XP. Scripted battles
  # (including the separate K07 progression) do not set can_override.
  module EncounterMask
    def start(*args, can_override: false)
      if can_override && BlueKantoTower.unidentified_appearance?
        pbMessage(BlueKantoPilot.t("An unidentified ghost appeared, then slipped away into the mist.",
                                  "Um fantasma desconhecido apareceu e desapareceu na névoa."))
        $game_temp.clear_battle_rules
        return true
      end
      super(*args, can_override: can_override)
    end
  end
end

WildBattle.singleton_class.prepend(BlueKantoTower::EncounterMask)
