# Regional progress is additive. It never changes native badges or existing saves on load.
module BlueRegions
  # Platinum HMs used by the eight Sinnoh field permissions.  An item held
  # in a foreign-region Bag is never a substitute for a LOCAL pickup event.
  # Source-of-truth alignment is checked against site/public/data/regions.json.
  SINNOH_HM_ITEMS = {
    "ROCK_SMASH" => :HM06, "CUT" => :HM01, "FLY" => :HM02,
    "DEFOG" => :HM05, "SURF" => :HM03, "STRENGTH" => :HM04,
    "ROCK_CLIMB" => :HM08, "WATERFALL" => :HM07
  }.freeze

  def self.valid_sinnoh_badges?(state)
    return false unless state.is_a?(Hash) && state["version"] == 1 &&
                        state["achievements"].is_a?(Hash)
    records = state["achievements"].fetch("SINNOH", [])
    milestones = info("SINNOH")["milestones"]
    records.is_a?(Array) && records.uniq.length == records.length &&
      records.all? { |badge| badge.is_a?(String) && milestones.include?(badge) }
  end

  def self.sinnoh_local_hms(state)
    return nil unless state.is_a?(Hash) && state["version"] == 1
    registry = state.fetch("region_local_hms", {})
    return nil unless registry.is_a?(Hash)
    claims = registry.fetch("SINNOH", [])
    return nil unless claims.is_a?(Array) && claims.uniq.length == claims.length &&
                      claims.all? { |key| key.is_a?(String) && SINNOH_HM_ITEMS.key?(key) }
    claims
  end

  # Only trusted *Sinnoh pickup events* should call this after the item has
  # been placed in the active regional Bag. It does NOT create an HM item,
  # assign badges, activate gym events, or approve a planned map as playable.
  def self.record_sinnoh_hm(state, action, item, bag, pickup_confirmed = false)
    return false unless pickup_confirmed == true &&
                        state.is_a?(Hash) && state["version"] == 1 &&
                        state["current"] == "SINNOH" && valid_sinnoh_badges?(state)
    return false unless action.is_a?(String) && SINNOH_HM_ITEMS[action] == item
    return false unless bag && bag.respond_to?(:has?) && bag.has?(item)
    return false unless defined?(GameData::Item) && GameData::Item.respond_to?(:try_get)
    metadata = GameData::Item.try_get(item)
    return false unless metadata && metadata.respond_to?(:is_HM?) && metadata.is_HM? &&
                        metadata.respond_to?(:move) &&
                        metadata.move.to_s.upcase.delete("_") == action.delete("_")
    claims = sinnoh_local_hms(state)
    return false unless claims && !claims.include?(action)
    state["region_local_hms"] ||= {}
    state["region_local_hms"]["SINNOH"] ||= []
    state["region_local_hms"]["SINNOH"] << action
    true
  end

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
    # Regional journeys are no longer gated by League victory. League records
    # still determine world-champion/rematch progress, never transport access.
    # The special Hisui chapter keeps its own quest requirement; it also needs
    # a separately verified install before it can become a physical destination.
    available = circuit.dup
    hisui = BlueRegionData::REGISTRY["hisui"]
    available << "HISUI" if state["initial"] == "HISUI" || state["hisui_quest"]
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
    # CH11: a forged or malformed Sinnoh achievement list must fail closed.
    # Do not mutate somebody else's regional save or native badge array.
    if region == "SINNOH"
      return false unless valid_sinnoh_badges?(state)
    end
    return false unless state["current"] == region && unlocked(state).include?(region)
    return false unless region != "DECADES" && known?(region) && info(region)["milestones"].include?(key)
    list = (state["achievements"][region] ||= [])
    return false if list.include?(key)
    list << key
    true
  end

  def self.local_achievements(state, region, native_badges = [])
    return [] if region == "SINNOH" && !valid_sinnoh_badges?(state)
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
    # Prevent direct calls from borrowing Sinnoh permissions while the player
    # is elsewhere; badges, tools and saved local HM claims are separate gates.
    if region == "SINNOH"
      return :unavailable unless valid_sinnoh_badges?(state) &&
                                 state["current"] == "SINNOH" &&
                                 sinnoh_local_hms(state)
    end
    rule = info(region)["field"][action]
    return :unavailable unless rule
    if rule["badge"]
      area, badge = rule["badge"].split(":", 2)
      return :badge unless local_achievements(state, area).include?(badge)
    end
    return :event if rule["event"] && !state["field_events"].fetch(region, []).include?(rule["event"])
    return :tool if rule["tool"] && !tool_ready
    if region == "SINNOH" && rule["tool"] &&
       !sinnoh_local_hms(state).include?(action)
      return :hm
    end
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

  # The pause menu is informational only: to switch regions the player MUST
  # speak to the physical agent in the initial town of the current region.
  def self.menu
    state = snapshot
    return unless state
    keys = circuit + ["HISUI"]
    loop do
      options = keys.map do |key|
        name = info(key)["name"]
        if key == state["current"]
          _INTL("{1} · atual", name)
        elsif defined?(BlueRegionTravel) && BlueRegionTravel.destination(state, key)
          _INTL("{1} · disponível no NPC", name)
        else
          _INTL("{1} · em preparação", name)
        end
      end
      choice = pbMessage(_INTL("Regiões · informação de viagem"),
                         options + [_INTL("Voltar")], -1)
      break if choice.nil? || choice < 0 || choice >= keys.length
      key = keys[choice]
      if key == state["current"]
        pbMessage(_INTL("Você está em {1}.",info(key)["name"]))
      elsif defined?(BlueRegionTravel) && BlueRegionTravel.destination(state,key)
        pbMessage(_INTL("Para ir a {1}, converse com o Agente Regional na cidade inicial da sua região. Não é necessário vencer a Liga.",info(key)["name"]))
      else
        pbMessage(_INTL("{1} ainda não está integrada a este jogo. Não é possível viajar até lá.",info(key)["name"]))
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
