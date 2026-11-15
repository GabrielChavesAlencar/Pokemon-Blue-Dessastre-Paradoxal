# Shared travel service for the main Blue campaign (Essentials v21.1).
# No second save, no mutation of existing Decades event flags or native badges.
module BlueRegionTravel
  SPECIAL_FLAGS = %w[Legendary Mythical UltraBeast Paradox].freeze

  def self.installed?
    # A start marker alone is not a merged campaign; require the audited
    # installer proof used by the native title screen.
    defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:kanto_integrated?) &&
      !!BlueRegionStart.kanto_integrated?
  end

  def self.johto_installed?
    return false unless installed? && defined?(BlueRegionStart) &&
                        BlueRegionStart.respond_to?(:johto_spawn) &&
                        BlueRegionStart.respond_to?(:johto_town_point) &&
                        BlueRegionStart.respond_to?(:johto_agent_point)
    BlueRegionStart.johto_spawn && BlueRegionStart.johto_town_point &&
      BlueRegionStart.johto_agent_point
  end

  def self.safe_context?
    return false unless BlueRegions.active? && $player && $game_map && $game_player && $scene
    return false unless $game_temp && !$game_temp.in_battle && !$game_temp.player_transferring
    return false if $game_temp.message_window_showing || $game_temp.transition_processing
    return false if defined?(pbMapInterpreterRunning?) && pbMapInterpreterRunning? && !@npc_event_context
    return false unless $scene.respond_to?(:transfer_player)
    true
  end

  def self.ending_verified?
    return false unless BlueRegionData::DECADES_VERIFIED && $player && $game_switches
    finale = BlueRegionData::REGISTRY["decades"]["league"]
    $game_switches[finale["switch"]] == true && $player.badges[finale["badge"]] == true
  end

  def self.source_valid?(state)
    return false unless state && BlueRegions.known?(state["current"])
    # No League or badge requirement: only an actually merged region may
    # supply an NPC and depart. Neither an independent pilot nor a forged
    # unlocked flag can make a region without maps playable.
    case state["current"]
    when "DECADES" then installed?
    when "KANTO" then installed?
    when "JOHTO" then !!johto_installed?
    else false
    end
  end

  def self.available?(state = nil)
    return false unless safe_context? && installed?
    state ||= BlueRegions.snapshot
    source_valid?(state) && %w[DECADES KANTO JOHTO].include?(state["current"])
  end

  # A new adventure begins upstairs at home, but returning from another
  # region should arrive in Pallet Town beside the agent, not in the bedroom.
  # Map 5 and tile (18,8) are source-proven FRLG house-door coordinates.
  def self.kanto_town_point
    path = "Data/blue-kanto-install.json"
    return nil unless File.file?(path)
    text = File.read(path)
    map_match = text.match(/"5"\s*:\s*(\d+)/)
    return nil unless map_match
    map_id = map_match[1].to_i
    return nil unless map_id > 0 && pbRgssExists?(sprintf("Data/Map%03d.rxdata", map_id))
    [map_id, 18, 8, 2]
  rescue IOError, SystemCallError
    nil
  end

  def self.destination(state, key)
    return nil unless state && BlueRegions.unlocked(state).include?(key)
    return nil if key == state["current"]
    if key == "KANTO"
      # The regional NPC is at Pallet, not in the initial bedroom.
      return nil unless installed?
      kanto_town_point
    elsif key == "JOHTO"
      # Never use Kanto's maps or Johto's bedroom as an arrival fallback.
      return nil unless johto_installed?
      BlueRegionStart.johto_town_point
    elsif key == "DECADES"
      position = state["decades_return"]
      # Kanto starters may visit Decades BEFORE their first League. This
      # real native start point was captured when the new game was created.
      # Never invent fallback coordinates in a foreign map.
      position ||= state["decades_first_arrival"] if state["current"] == "KANTO"
      return nil unless position.is_a?(Array) && position.length == 4
      return nil unless position.all? { |v| v.is_a?(Integer) } && position[0] > 0 &&
                        position[1] >= 0 && position[2] >= 0 && [2,4,6,8].include?(position[3])
      return nil unless pbRgssExists?(sprintf("Data/Map%03d.rxdata", position[0]))
      position
    end
  end

  def self.special?(pkmn)
    return false unless pkmn
    # Species metadata is the authority; never infer Legendary from BST.
    data = pkmn.species_data
    flags = data.flags
    if data.respond_to?(:species) && data.form != 0
      flags = flags + GameData::Species.get(data.species).flags
    end
    !(flags & SPECIAL_FLAGS).empty?
  end

  def self.free_storage_slots(limit)
    slots = []
    return slots if !$PokemonStorage || limit <= 0
    $PokemonStorage.maxBoxes.times do |box|
      $PokemonStorage.maxPokemon(box).times do |slot|
        slots << [box, slot] if $PokemonStorage[box,slot].nil?
        return slots if slots.length >= limit
      end
    end
    slots
  end

  def self.preview(state, key)
    return [:locked, []] unless destination(state, key)
    forbidden = BlueRegions.allow_specials?(state, key, $player.badges) ? [] :
                $player.party.select { |pkmn| special?(pkmn) }
    slots = free_storage_slots(forbidden.length)
    BlueRegions.transfer_plan(state, key, $player.party, slots, $player.badges) { |pkmn| special?(pkmn) }
  end

  def self.message_for(status)
    case status
    when :locked then _INTL("Essa região ainda está bloqueada ou não tem ponto seguro de chegada.")
    when :no_usable_party then _INTL("Sua equipe ficaria sem um Pokémon comum capaz de batalhar. Organize o PC antes de viajar.")
    when :box_full then _INTL("Não há vagas suficientes nas Boxes. Libere espaço antes de viajar.")
    else _INTL("Não foi possível concluir a viagem. Nenhum Pokémon foi perdido.")
    end
  end

  def self.move_to(point)
    $game_temp.player_new_map_id = point[0]
    $game_temp.player_new_x = point[1]
    $game_temp.player_new_y = point[2]
    $game_temp.player_new_direction = point[3]
    $game_temp.player_transferring = true
    $scene.transfer_player
    raise "A transferência não chegou ao mapa esperado" unless $game_map.map_id == point[0]
  ensure
    $game_temp.player_transferring = false if $game_temp
  end

  def self.perform(state, key, plan = nil)
    raise "Viagem indisponível" unless available?(state) && destination(state, key)
    status, reservations = preview(state, key)
    raise message_for(status) unless status == :ok
    point = destination(state, key)
    before = [$game_map.map_id, $game_player.x, $game_player.y, $game_player.direction]
    old_state = $PokemonGlobal.blue_regions
    old_party = $player.party.dup
    old_slots = reservations.map { |pkmn, pos| [pos, $PokemonStorage[pos[0],pos[1]]] }
    next_state = Marshal.load(Marshal.dump(state))
    next_state["decades_return"] = before if state["current"] == "DECADES"
    next_state["current"] = key
    next_state["travel_history"] ||= []
    next_state["travel_history"] << [state["current"], key, before[0], point[0]]
    begin
      # All PC positions are reserved before the first write.
      reservations.each do |pkmn, pos|
        raise "Vaga do PC foi ocupada durante a confirmação" unless $PokemonStorage[pos[0],pos[1]].nil?
        $PokemonStorage[pos[0],pos[1]] = pkmn
        party_index = $player.party.index { |item| item.equal?(pkmn) }
        raise "Pokémon reservado não está mais na party" unless party_index
        $player.party.delete_at(party_index)
      end
      $PokemonGlobal.blue_regions = next_state
      pbFadeOutIn { move_to(point) }
      true
    rescue StandardError => error
      $PokemonGlobal.blue_regions = old_state
      $player.party.replace(old_party)
      old_slots.each { |pos, previous| $PokemonStorage[pos[0],pos[1]] = previous }
      if $game_map.map_id != before[0] || $game_player.x != before[1] || $game_player.y != before[2]
        pbFadeOutIn { move_to(before) }
      end
      raise error
    end
  end

  def self.travel(key, quiet = false)
    # A transport request is only valid inside the initial-town NPC event.
    # 'quiet' affects message boxes, not permission to teleport.
    return false unless @npc_event_context
    state = BlueRegions.snapshot
    return false unless available?(state)
    status, reservations = preview(state, key)
    if status != :ok
      pbMessage(message_for(status)) unless quiet
      return false
    end
    if !quiet
      notice = _INTL("Viajar para {1}? Sua equipe e seu save serão mantidos.", BlueRegions.info(key)["name"])
      notice += _INTL(" {1} Pokémon especiais serão enviados ao PC.", reservations.length) unless reservations.empty?
      return false unless pbConfirmMessage(notice)
    end
    begin
      perform(state, key)
      pbMessage(_INTL("Chegada a {1}. Salve a partida no mesmo slot de sempre.", BlueRegions.info(key)["name"])) unless quiet
      true
    rescue StandardError => error
      pbMessage(_INTL("Viagem cancelada: {1}", error.message)) unless quiet
      false
    end
  end

  def self.agent(from_npc = false)
    previous_event_context = @npc_event_context
    @npc_event_context = true if from_npc
    state = BlueRegions.snapshot
    unless available?(state)
      pbMessage(_INTL("O transporte está disponível pelo NPC da cidade inicial quando a região estiver integrada ao jogo principal."))
      return
    end
    loop do
      keys = BlueRegions.circuit + ["HISUI"]
      names = keys.map do |key|
        name = BlueRegions.info(key)["name"]
        if key == state["current"]
          _INTL("{1} (atual)",name)
        elsif destination(state,key)
          _INTL("{1} (viajar)",name)
        else
          _INTL("{1} (em preparação)",name)
        end
      end
      choice = pbMessage(_INTL("Agente de Transporte Regional"), names +
                         [_INTL("Organizar PC"),_INTL("Permanecer")], -1)
      break if !choice || choice < 0 || choice == keys.length + 1
      if choice == keys.length
        if defined?(BlueAdventure) && BlueAdventure.pc_available?
          BlueAdventure.open_pc
        else
          pbMessage(_INTL("PC indisponível neste momento."))
        end
      elsif choice < keys.length
        key = keys[choice]
        if key == state["current"]
          pbMessage(_INTL("Você já está em {1}.",BlueRegions.info(key)["name"]))
        elsif destination(state,key)
          break if travel(key)
        else
          pbMessage(message_for(:locked))
        end
      else
        break
      end
    end
  ensure
    @npc_event_context = previous_event_context
  end

  module StorageRules
    def pbWithdraw(selected, heldpoke = nil)
      if selected && selected[0] >= 0 &&
         BlueRegionTravel.restricted?(heldpoke || @storage[selected[0],selected[1]])
        pbDisplay(_INTL("Pokémon especial bloqueado: obtenha as oito conquistas da região atual."))
        return false
      end
      super
    end
    def pbPlace(selected)
      # Essentials v21.1 accepts only the selected slot here.
      if selected && selected[0] == -1 && BlueRegionTravel.restricted?(@heldpkmn)
        pbDisplay(_INTL("Esse Pokémon especial só pode entrar na party após oito conquistas locais."))
        return false
      end
      super
    end
    def pbSwap(selected)
      if selected && selected[0] == -1 && BlueRegionTravel.restricted?(@heldpkmn)
        pbDisplay(_INTL("Esse Pokémon especial não pode entrar na party desta região."))
        return false
      end
      super
    end
  end

  def self.restricted?(pkmn)
    return false unless pkmn && BlueRegions.active? && installed?
    # A legacy Decades save without regional travel must retain its original
    # PC rules, even if Blue/Kanto was installed after the save was created.
    stored = $PokemonGlobal && $PokemonGlobal.blue_regions
    return false unless stored.is_a?(Hash) && stored["version"] == 1
    if stored["current"] == "DECADES"
      history = stored["travel_history"]
      return false unless history.is_a?(Array) && !history.empty?
    end
    state = BlueRegions.snapshot
    return false unless state && BlueRegions.known?(state["current"])
    !BlueRegions.allow_specials?(state, state["current"], $player.badges) && special?(pkmn)
  end

  # Cherryhill City (native Decades Map077) is the first city in the
  # source map catalog. A generated event avoids writing native Map077.rxdata.
  # Only installed, genuine regional campaigns get the NPC; arena and legacy
  # saves without the Kanto installation retain their original maps.
  DECADES_AGENT_MAP = 77
  DECADES_AGENT_GRAPHIC = "NPC_POKENGINE_Gardener".freeze
  DECADES_AGENT_NAME = "Agente Regional Blue".freeze

  def self.attach_decades_agent(map)
    return unless installed? && map && map.map_id == DECADES_AGENT_MAP
    state = $PokemonGlobal && $PokemonGlobal.blue_regions
    return unless BlueRegions.active? && (state.nil? ||
      (state.is_a?(Hash) && state["version"] == 1 && state["current"] == "DECADES"))
    return unless map.events.is_a?(Hash)
    return if map.events.values.any? { |event| event.name == DECADES_AGENT_NAME }
    return unless defined?(RPG::Event) && defined?(RPG::EventCommand) && defined?(Game_Event)
    # The existing Quest NPC uses this actor graphic on Map077; don't rely on
    # a new asset or a third-party source graphic in the native Decades game.
    occupied = map.events.values.map { |event| [event.x, event.y] }
    positions = (18..31).flat_map { |y| (10..35).map { |x| [x,y] } }
    positions.sort_by! { |x,y| [(x-24).abs+(y-24).abs,y,x] }
    point = positions.find do |x,y|
      !occupied.include?([x,y]) && (map.valid?(x,y) rescue false) &&
        (map.passable?(x,y,2) rescue false)
    end
    return unless point
    event = RPG::Event.new(point[0], point[1])
    event.id = (map.events.keys.max || 0) + 1
    event.name = DECADES_AGENT_NAME
    page = event.pages.first
    page.graphic.character_name = DECADES_AGENT_GRAPHIC
    page.trigger = 0
    page.list = [
      RPG::EventCommand.new(355,0,["BlueRegionTravel.agent(true)"]),
      RPG::EventCommand.new(0,0,[])
    ]
    map.events[event.id] = Game_Event.new(map.map_id, event)
  end

  # Johto's real New Bark point comes from its verified install manifest.
  # The NPC is in-memory only and no longer requires Hall of Fame.
  JOHTO_AGENT_NAME = "Agente Regional Johto".freeze
  def self.attach_johto_agent(map)
    return unless johto_installed? && map && map.events.is_a?(Hash)
    point = BlueRegionStart.johto_agent_point
    return unless point && map.map_id == point[0]
    state = $PokemonGlobal && $PokemonGlobal.blue_regions
    return unless state.is_a?(Hash) && state["version"] == 1 &&
                  state["current"] == "JOHTO"
    return if map.events.values.any? { |event| event.name == JOHTO_AGENT_NAME }
    return unless defined?(RPG::Event) && defined?(RPG::EventCommand) && defined?(Game_Event)
    x, y = point[1, 2]
    return if map.events.values.any? { |event| event.x == x && event.y == y }
    return unless (map.valid?(x,y) rescue false) && (map.passable?(x,y,2) rescue false)
    event = RPG::Event.new(x,y)
    event.id = (map.events.keys.max || 0) + 1
    event.name = JOHTO_AGENT_NAME
    page = event.pages.first
    page.graphic.character_name = DECADES_AGENT_GRAPHIC
    page.trigger = 0
    page.list = [
      RPG::EventCommand.new(355,0,["BlueRegionTravel.agent(true)"]),
      RPG::EventCommand.new(0,0,[])
    ]
    map.events[event.id] = Game_Event.new(map.map_id,event)
  end

  # Pallet Town (source Map005), after merge into Decades, gets the same
  # physical NPC. Never edit Map*.rxdata or affect the isolated pilot.
  KANTO_AGENT_NAME = "Agente Regional Kanto".freeze
  def self.attach_kanto_agent(map)
    return unless installed? && map && map.events.is_a?(Hash)
    state = $PokemonGlobal && $PokemonGlobal.blue_regions
    return unless state.is_a?(Hash) && state["version"] == 1 &&
                  state["current"] == "KANTO"
    town = kanto_town_point
    return unless town && map.map_id == town[0]
    return if map.events.values.any? { |event| event.name == KANTO_AGENT_NAME }
    return unless defined?(RPG::Event) && defined?(RPG::EventCommand) && defined?(Game_Event)
    occupied = map.events.values.map { |event| [event.x,event.y] }
    # Use only real passable tiles near the audited Pallet arrival and do not
    # occupy the arrival point, a map event or a source actor's event position.
    arrival = town[1,2]
    places = (0..4).flat_map do |distance|
      (-distance..distance).flat_map do |dx|
        dy = distance - dx.abs
        (dy == 0 ? [0] : [-dy,dy]).map { |offset| [arrival[0]+dx,arrival[1]+offset] }
      end
    end.uniq
    point = places.find do |x,y|
      [x,y] != arrival && !occupied.include?([x,y]) &&
        (map.valid?(x,y) rescue false) && (map.passable?(x,y,2) rescue false)
    end
    return unless point
    event = RPG::Event.new(point[0],point[1])
    event.id = (map.events.keys.max || 0) + 1
    event.name = KANTO_AGENT_NAME
    page = event.pages.first
    page.graphic.character_name = DECADES_AGENT_GRAPHIC
    page.trigger = 0
    page.list = [
      RPG::EventCommand.new(355,0,["BlueRegionTravel.agent(true)"]),
      RPG::EventCommand.new(0,0,[])
    ]
    map.events[event.id] = Game_Event.new(map.map_id,event)
  end

  module DecadesTownAgent
    def setup(*args)
      result = super
      BlueRegionTravel.attach_decades_agent(self)
      BlueRegionTravel.attach_kanto_agent(self)
      BlueRegionTravel.attach_johto_agent(self)
      result
    end
  end

  def self.install
    return if @installed
    Game_Map.prepend(DecadesTownAgent) if defined?(Game_Map) && !Game_Map.ancestors.include?(DecadesTownAgent)
    PokemonStorageScreen.prepend(StorageRules)
    # Travel is deliberately NOT registered in the pause menu. Interact with
    # the NPC in Pallet, Cherryhill or New Bark instead.
    @installed = true
  end
end
