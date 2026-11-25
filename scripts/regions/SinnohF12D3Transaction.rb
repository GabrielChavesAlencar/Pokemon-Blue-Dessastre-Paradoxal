# F12D3 transaction candidate. Not loaded by the installer until geometry is proved.
# No global bag/state writes, map events, switches, saves, or source script execution.
module BlueSinnohF12D3Transaction
  ITEM=:SECRETPOTION
  LEDGER="sinnoh_f12d3_quest".freeze
  ORDER=%w[SECRETPOTION_RECEIVED PSYDUCK_CLEARED].freeze
  CHASE=%w[PASTORIA ROUTE_213 VALOR_BATTLE].freeze

  def self.history(state)
    return nil unless state.is_a?(Hash) && state["current"]=="SINNOH" &&
      state["sinnoh_f12d_quest"]==CHASE
    h=state.fetch(LEDGER,[])
    return nil unless h.is_a?(Array) && h.length<=ORDER.length && h==ORDER.first(h.length)
    h.dup
  end

  def self.compiled_item_valid?
    return false unless defined?(GameData::Item) && GameData::Item.respond_to?(:try_get)
    item=GameData::Item.try_get(ITEM)
    !!(item && item.respond_to?(:id) && item.id==ITEM && item.respond_to?(:is_key_item?) &&
       item.is_key_item? && defined?(BlueRegionTravel) && BlueRegionTravel.regional_item?(ITEM))
  end

  # A binder must first validate actual interaction coordinates and geometry,
  # private copy, compiled catalogue, and regional state. This function only
  # prepares a transaction; caller must commit both objects together.
  def self.stage(state,bag,action,catalogue_verified:false,geometry_verified:false)
    return nil unless catalogue_verified==true && geometry_verified==true && compiled_item_valid?
    h=history(state)
    return nil unless h && !state.frozen? && ORDER[h.length]==action
    return nil unless bag && [:quantity,:add,:remove].all? { |method| bag.respond_to?(method) }
    qty=bag.quantity(ITEM)
    return nil unless qty.is_a?(Integer) && qty==(action==ORDER[0] ? 0 : 1)
    staged_bag=Marshal.load(Marshal.dump(bag))
    return nil if staged_bag.equal?(bag)
    return nil unless staged_bag.quantity(ITEM)==qty
    ok=action==ORDER[0] ? staged_bag.add(ITEM,1) : staged_bag.remove(ITEM,1)
    return nil unless ok && staged_bag.quantity(ITEM)==(action==ORDER[0] ? 1 : 0)
    return nil unless bag.quantity(ITEM)==qty && history(state)==h
    staged_state=state.dup
    staged_state[LEDGER]=h+[action]
    {state:staged_state,bag:staged_bag,history:staged_state[LEDGER].dup}
  rescue StandardError
    nil
  end

  # Event binder may use this to select blocking versus cleared pages
  # after validating the same regional context. Malformed history stays blocked.
  def self.cleared?(state)
    history(state)==ORDER
  end
end
