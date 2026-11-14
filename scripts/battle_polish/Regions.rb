# Regional progress is additive. It never changes native badges or existing saves on load.
module BlueRegions
  def self.known?(region)
    BlueRegionData::REGISTRY["regions"].key?(region)
  end

  def self.info(region)
    BlueRegionData::REGISTRY["regions"].fetch(region)
  end

  def self.circuit
    BlueRegionData::REGISTRY["circuit"]
  end

  def self.neighbors(region)
    i = circuit.index(region)
    i ? [circuit[i-1], circuit[(i+1) % circuit.length]] : []
  end

  def self.new_state(region = "DECADES")
    raise ArgumentError, "Unknown region" unless known?(region)
    {"version"=>1, "initial"=>region, "current"=>region, "leagues"=>[],
     "achievements"=>{}, "field_events"=>{}, "hisui_complete"=>false, "hisui_quest"=>false}
  end

  def self.unlocked(state)
    available = [state["initial"]] + state["leagues"].flat_map { |key| neighbors(key) }
    hisui = BlueRegionData::REGISTRY["hisui"]
    available.concat(hisui["startExits"]) if state["initial"] == "HISUI" && state["hisui_complete"]
    available << "HISUI" if state["hisui_quest"] && available.include?(hisui["questRegion"])
    available.uniq
  end

  # For trusted map events after their final sequence has completed successfully.
  def self.complete_league(state, region)
    return false unless circuit.include?(region) && state["current"] == region && unlocked(state).include?(region)
    return false if state["leagues"].include?(region)
    state["leagues"] << region
    true
  end

  def self.finish_hisui(state)
    return false unless state["current"] == "HISUI" && unlocked(state).include?("HISUI") && !state["hisui_complete"]
    state["hisui_complete"] = true
  end

  def self.unlock_hisui_quest(state)
    return false unless state["current"] == BlueRegionData::REGISTRY["hisui"]["questRegion"]
    return false if state["hisui_quest"] || !unlocked(state).include?(state["current"])
    state["hisui_quest"] = true
  end

  def self.world_champion?(state)
    (circuit - state["leagues"]).empty?
  end

  def self.profile(state, verified_rematch)
    world_champion?(state) && verified_rematch ? :world_champion_rematch : :first_clear
  end

  def self.award(state, region, key)
    return false unless state["current"] == region && unlocked(state).include?(region)
    return false unless region != "DECADES" && known?(region) && info(region)["milestones"].include?(key)
    list = (state["achievements"][region] ||= [])
    return false if list.include?(key)
    list << key
    true
  end

  def self.local_achievements(state, region, native_badges = [])
    if region == "DECADES"
      return [] unless BlueRegionData::DECADES_VERIFIED
      return BlueRegionData::REGISTRY["decades"]["milestones"].map { |row| row["badge"] }
                            .select { |index| native_badges[index] == true }
    end
    info(region)["milestones"] & state["achievements"].fetch(region, [])
  end

  def self.crystal_total(state, native_total)
    native_total + (circuit - ["DECADES"]).sum { |region| local_achievements(state, region).length }
  end

  def self.allow_specials?(state, region, native_badges = [])
    return state["hisui_complete"] if region == "HISUI"
    local_achievements(state, region, native_badges).length >= 8
  end

  # The caller classifies the effective species using the verified species catalog.
  # Return a preview; the travel adapter must reserve real Box slots before committing.
  def self.transfer_plan(state, destination, party, slots, native_badges = [], &classify)
    return [:locked, []] unless unlocked(state).include?(destination)
    deposit = allow_specials?(state, destination, native_badges) ? [] : party.select(&classify)
    return [:no_usable_party, []] unless party.any? { |pkmn| !deposit.include?(pkmn) && !pkmn.egg? && !pkmn.fainted? }
    return [:box_full, []] if slots.length < deposit.length
    [:ok, deposit.zip(slots)]
  end

  def self.field_access(state, region, action, tool_ready = false)
    return :native if region == "DECADES"
    rule = info(region)["field"][action]
    return :unavailable unless rule
    if rule["badge"]
      area, badge = rule["badge"].split(":", 2)
      return :badge unless local_achievements(state, area).include?(badge)
    end
    return :event if rule["event"] && !state["field_events"].fetch(region, []).include?(rule["event"])
    return :tool if rule["tool"] && !tool_ready
    :allowed
  end

  def self.active?
    BlueCampaign.active? && !BlueBattleOptions.battle_area?
  end

  def self.snapshot
    stored = $PokemonGlobal.blue_regions
    # Preserve old Decades saves; regional state is persisted only on travel.
    return nil if stored && (!stored.is_a?(Hash) || stored["version"] != 1)
    state = stored ? Marshal.load(Marshal.dump(stored)) : new_state
    # Audited native ending: the switch is set after the Hall of Fame and the
    # Stellar Emerald was awarded only after the victory branch.
    ending = BlueRegionData::REGISTRY["decades"]["league"]
    if BlueRegionData::DECADES_VERIFIED && $game_switches &&
       $game_switches[ending["switch"]] && $player.badges[ending["badge"]] == true
      complete_league(state, "DECADES")
    end
    state
  end

  def self.menu
    state = snapshot
    return unless state
    ready = unlocked(state)
    loop do
      keys = circuit + ["HISUI"]
      options = keys.map do |key|
        name = info(key)["name"]
        if key == state["current"]
          _INTL("{1} · atual",name)
        elsif ready.include?(key) && defined?(BlueRegionTravel) &&
              BlueRegionTravel.available?(state) && BlueRegionTravel.destination(state,key)
          _INTL("{1} · viajar",name)
        elsif ready.include?(key)
          _INTL("{1} · mapa em preparação",name)
        else
          _INTL("{1} · bloqueada",name)
        end
      end
      choice = pbMessage(_INTL("Circuito de regiões"),options + [_INTL("Voltar")],-1)
      break if !choice || choice < 0 || choice >= keys.length
      key = keys[choice]
      if key != state["current"] && defined?(BlueRegionTravel) &&
         BlueRegionTravel.available?(state) && BlueRegionTravel.destination(state,key)
        break if BlueRegionTravel.travel(key)
      elsif key == "DECADES"
        amount = local_achievements(state,key,$player.badges).length
        ending = state["leagues"].include?(key) ? _INTL("Final registrado") : _INTL("Final pendente")
        pbMessage(_INTL("Decades: {1}/8 marcos regionais. {2}.",amount,ending))
      elsif ready.include?(key)
        pbMessage(_INTL("{1} foi desbloqueada. A viagem ficará disponível quando a campanha estiver pronta.",info(key)["name"]))
      elsif key == "HISUI"
        pbMessage(_INTL("Jornada especial. O acesso por Sinnoh depende da missão temporal."))
      else
        names = neighbors(key).map { |region| info(region)["name"] }
        pbMessage(_INTL("Conclua a Liga em {1} ou {2} para liberar {3}.",names[0],names[1],info(key)["name"]))
      end
    end
  end

  module PauseIcon
    def from_current_menu_theme(name, default = nil)
      return super("menu_town_map", nil) if ["menu_blue_regions", "menu_blue_johto_teleport"].include?(name)
      super
    end
  end

  def self.install
    if PokemonSystem.method_defined?(:from_current_menu_theme) && !PokemonSystem.ancestors.include?(PauseIcon)
      PokemonSystem.prepend(PauseIcon)
    end
    MenuHandlers.add(:pause_menu,:blue_regions,{
      "name"=>_INTL("Circuito de regiões"),"order"=>67,
      "condition"=>proc { |_menu| active? },
      "effect"=>proc { |menu| menu.pbHideMenu; BlueRegions.menu; menu.pbShowMenu; false }
    })
  end
end

class PokemonGlobalMetadata
  attr_accessor :blue_regions
end
