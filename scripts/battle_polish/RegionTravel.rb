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

  def self.hoenn_installed?
    return false unless installed? && defined?(BlueRegionStart) &&
      BlueRegionStart.respond_to?(:hoenn_integrated?) &&
      BlueRegionStart.respond_to?(:hoenn_town_point)
    !!BlueRegionStart.hoenn_integrated? && !!BlueRegionStart.hoenn_town_point
  end

  def self.hoenn_town_point
    hoenn_installed? ? BlueRegionStart.hoenn_town_point : nil
  end

  # The installer writes a simple status inside game/Data so the travel NPC
  # does not hide a missing source behind a vague "em preparação" label.
  # Never treat this message as proof of installation; destination() still
  # requires the independently verified 199 maps and regional manifest.
  HOENN_INSTALL_STATUS = "Data/blue-hoenn-install-status.txt".freeze
  def self.hoenn_pending_message
    status = if File.file?(HOENN_INSTALL_STATUS) && !File.symlink?(HOENN_INSTALL_STATUS)
               File.read(HOENN_INSTALL_STATUS, 80).strip
             end
    case status
    when "awaiting_local_source"
      _INTL("Hoenn ainda não está instalada. Feche o jogo e abra o Blue-Story.exe atualizado: ele agora baixa automaticamente os mapas e recursos verificados, sem precisar colocar ZIP ou executar outro instalador.")
    when "existing_install_needs_review"
      _INTL("Foi detectada uma instalação incompleta ou modificada de Hoenn. A viagem está bloqueada para proteger o save. Consulte o resultado do Blue-Story.exe em .blue-work/hoenn-main-install-status.json.")
    when "integration_blocked"
      _INTL("A instalação automática de Hoenn falhou ou não concluiu o download. Feche o jogo e atualize pelo Blue-Story.exe novamente. Consulte .blue-work/hoenn-main-install-status.json para identificar a causa; seu save foi protegido.")
    else
      _INTL("Hoenn ainda não está integrada neste Game.exe. Feche o jogo e execute o Blue-Story.exe atualizado para baixar e instalar a região automaticamente. Não é necessário usar ZIP ou BAT separado.")
    end
  rescue IOError, SystemCallError
    _INTL("Hoenn não está instalada na build principal. Verifique o instalador antes de viajar.")
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

  def self.sinnoh_points
    return nil unless defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:sinnoh_shared_points)
    BlueRegionStart.sinnoh_shared_points
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
    when "HOENN" then !!hoenn_installed?
    when "SINNOH" then !!sinnoh_points
    else false
    end
  end

  def self.available?(state = nil)
    return false unless safe_context? && installed?
    state ||= BlueRegions.snapshot
    source_valid?(state)
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

  # Keep Map077 as the proven default, but resolve the real native
  # Cherryhill City from MapInfos when a Decades build has reordered maps.
  # Never choose a bedroom or map with a merely similar substring.
  def self.decades_city_map_id
    infos = defined?($data_mapinfos) && $data_mapinfos
    if infos && infos.respond_to?(:each_with_index)
      infos.each_with_index do |info, id|
        next unless id > 0 && info && info.respond_to?(:name)
        next unless info.name.to_s.strip.match?(/\A(?:Cherryhill(?: City)?|Cidade(?: de)? Cherryhill)\z/i)
        return id if pbRgssExists?(sprintf("Data/Map%03d.rxdata", id))
      end
    end
    DECADES_AGENT_MAP
  end

  # A native Decades New Game starts on the introduction/character-selection
  # map, not in Cherryhill. Entering from another region MUST use a walkable
  # tile on Map077, near the real travel NPC, and NEVER restart that intro.
  # Resolve from the installed native map; do not forge coordinates on an
  # unknown or non-passable tile.
  def self.decades_town_point
    city_id = decades_city_map_id
    return nil unless pbRgssExists?(sprintf("Data/Map%03d.rxdata", city_id))
    return nil unless defined?(Game_Map)
    town = Game_Map.new
    town.setup(city_id)
    return nil unless town.respond_to?(:events) && town.events.is_a?(Hash)
    # Game_Map#setup may already have injected the regional agent when
    # the current save is Decades, but not when it is Kanto. Exclude ONLY
    # our generated NPC from the base occupancy list, so the arrival tile
    # is deterministic in both situations and never depends on travel state.
    occupied = town.events.values.reject { |event|
      event.name == DECADES_AGENT_NAME
    }.map { |event| [event.x, event.y] }
    positions = (18..31).flat_map { |y| (10..35).map { |x| [x,y] } }
    positions.sort_by! { |x,y| [(x-24).abs+(y-24).abs,y,x] }
    safe = positions.select do |x,y|
      !occupied.include?([x,y]) && (town.valid?(x,y) rescue false) &&
        (town.passable?(x,y,2) rescue false)
    end
    # When the game switches to Decades it creates the NPC on the first free
    # central tile. Choose a DIFFERENT nearby passable point for the player.
    return nil unless safe.length >= 2
    nearby = safe[1..-1].find { |x,y| (x-safe[0][0]).abs+(y-safe[0][1]).abs <= 4 }
    return nil unless nearby
    [city_id, nearby[0], nearby[1], 2]
  rescue StandardError
    nil
  end

  def self.destination(state, key)
    return nil unless state && BlueRegions.unlocked(state).include?(key)
    return nil if key == state["current"]
    if key == "KANTO"
      # The regional NPC is at Pallet, not in the initial bedroom.
      return nil unless installed?
      kanto_town_point
    elsif key == "HOENN"
      # New Game begins in Littleroot's bedroom. Regional travel goes to a
      # vetted passable outdoor tile in Littleroot, never to that bedroom.
      return nil unless hoenn_installed?
      hoenn_town_point
    elsif key == "JOHTO"
      # Never use Kanto's maps or Johto's bedroom as an arrival fallback.
      return nil unless johto_installed?
      BlueRegionStart.johto_town_point
    elsif key == "SINNOH"
      sinnoh_points&.[](1)
    elsif key == "DECADES"
      # Previous releases mistakenly saved System.rxdata's native INTRO as
      # decades_first_arrival. Ignore it, even for an old Kanto save: visiting
      # Decades must not show character/story/mechanics setup a second time.
      # The NPC is on Cherryhill Map077; any recorded return must be on that
      # same verified town map, not in Decades' introduction or elsewhere.
      position = state["decades_return"]
      city_id = decades_city_map_id
      if position.is_a?(Array) && position.length == 4 &&
         position[0] == city_id &&
         position.all? { |v| v.is_a?(Integer) } && position[1] >= 0 &&
         position[2] >= 0 && [2,4,6,8].include?(position[3]) &&
         pbRgssExists?(sprintf("Data/Map%03d.rxdata", city_id))
        return position
      end
      decades_town_point
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

  # Essentials v21.1: Key Items have the KeyItem flag, and HM machines
  # have field_use=4. TM/TR items, consumables and held Mega Stones stay
  # global. This deliberately uses GameData metadata rather than a list of
  # item names, so new regions and translated items work automatically.
  def self.regional_item?(item)
    return false unless defined?(GameData::Item) && GameData::Item.respond_to?(:try_get)
    data = GameData::Item.try_get(item)
    !!data && (data.is_key_item? || data.is_HM?)
  end

  def self.local_bag_contents(bag)
    raise "Bolsa regional indisponível" unless
      bag && bag.respond_to?(:pockets) && bag.respond_to?(:registered_items)
    items = []
    bag.pockets.each do |pocket|
      Array(pocket).each do |entry|
        next unless entry.is_a?(Array) && regional_item?(entry[0])
        raise "Quantidade inválida de item regional" unless
          entry[1].is_a?(Integer) && entry[1] > 0
        items << [entry[0], entry[1]]
      end
    end
    present = items.map { |entry| entry[0] }
    # Essentials can retain a shortcut after an item was used/removed.
    # Only persist shortcuts for locally held items, so a stale shortcut
    # cannot make later visits reject an otherwise valid save.
    registered = bag.registered_items.select { |id|
      regional_item?(id) && present.include?(id)
    }.uniq
    {"items" => items, "registered" => registered}
  end

  # The vanilla Essentials item PC is separate from Pokémon Boxes but is
  # shared by all regions. Isolate local Key Items/HMs there as well, so a
  # player cannot deposit a Kanto HM and withdraw it in Decades.
  def self.local_pc_contents(storage)
    return [] unless storage
    raise "PC de itens inválido" unless
      storage.respond_to?(:items) && storage.respond_to?(:add) &&
      storage.respond_to?(:remove)
    local = []
    storage.items.each do |entry|
      next unless entry.is_a?(Array) && regional_item?(entry[0])
      raise "Quantidade de item inválida no PC" unless
        entry[1].is_a?(Integer) && entry[1] > 0
      local << [entry[0],entry[1]]
    end
    local
  end

  def self.stage_local_bag(state, destination)
    raise "Não foi possível ler a Bolsa regional" unless $bag
    staged = Marshal.load(Marshal.dump($bag))
    source_contents = local_bag_contents(staged)
    vault = state["region_key_items"] || {}
    raise "Registro de itens regionais inválido" unless vault.is_a?(Hash)
    target_contents = vault[destination] || {"items" => [], "registered" => []}
    raise "Registro de destino inválido" unless
      target_contents.is_a?(Hash) &&
      target_contents["items"].is_a?(Array) &&
      target_contents["registered"].is_a?(Array)
    target_items = target_contents["items"]
    target_pc_items = target_contents.fetch("pc_items", [])
    raise "Itens do PC regional inválidos no save" unless target_pc_items.is_a?(Array)
    validate_items = lambda do |rows|
      seen = {}
      rows.each do |entry|
        raise "Item regional inválido no save" unless
          entry.is_a?(Array) && entry.length == 2 &&
          regional_item?(entry[0]) && entry[1].is_a?(Integer) &&
          entry[1] > 0 && !seen[entry[0]]
        seen[entry[0]] = true
      end
      seen
    end
    seen = validate_items.call(target_items)
    validate_items.call(target_pc_items)
    raise "Atalhos regionais duplicados no save" unless
      target_contents["registered"].uniq.length == target_contents["registered"].length
    target_contents["registered"].each do |id|
      raise "Atalho regional inválido no save" unless seen[id]
    end
    source_contents["items"].each do |id, qty|
      raise "Falha ao guardar itens da região atual" unless staged.remove_all(id, qty)
    end
    target_items.each do |id, qty|
      raise "Sem espaço para os itens-chave/HMs da região de destino" unless
        staged.add_all(id, qty)
    end
    staged.registered_items.delete_if { |id| regional_item?(id) }
    target_contents["registered"].each { |id| staged.register(id) }
    pc = $PokemonGlobal.respond_to?(:pcItemStorage) ?
           $PokemonGlobal.pcItemStorage : nil
    source_contents["pc_items"] = local_pc_contents(pc)
    raise "PC de itens de destino indisponível" if !pc && !target_pc_items.empty?
    staged_pc = pc && Marshal.load(Marshal.dump(pc))
    if staged_pc
      source_contents["pc_items"].each do |id, qty|
        raise "Falha ao guardar itens do PC local" unless staged_pc.remove(id,qty)
      end
      target_pc_items.each do |id, qty|
        raise "Sem espaço no PC de itens da região de destino" unless
          staged_pc.add(id,qty)
      end
    end
    [staged, source_contents, staged_pc]
  end

  def self.preview(state, key)
    return [:locked, []] unless destination(state, key)
    forbidden = BlueRegions.allow_specials?(state, key, $player.badges) ? [] :
                $player.party.select { |pkmn| special?(pkmn) }
    slots = free_storage_slots(forbidden.length)
    status, reservations = BlueRegions.transfer_plan(state, key, $player.party,
      slots, $player.badges) { |pkmn| special?(pkmn) }
    return [status, reservations] unless status == :ok
    begin
      stage_local_bag(state, key)
    rescue StandardError => error
      @last_bag_error = error.message
      return [:bag, []]
    end
    [:ok, reservations]
  end

  def self.message_for(status)
    case status
    when :locked then _INTL("Essa região ainda está bloqueada ou não tem ponto seguro de chegada.")
    when :no_usable_party then _INTL("Sua equipe ficaria sem um Pokémon comum capaz de batalhar. Organize o PC antes de viajar.")
    when :box_full then _INTL("Não há vagas suficientes nas Boxes. Libere espaço antes de viajar.")
    when :bag then _INTL("Viagem cancelada: {1}", @last_bag_error || "Bolsa regional indisponível.")
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
    # Validate again at the final mutating boundary, not only in travel().
    raise "Fale com o NPC na cidade inicial para viajar." unless @npc_event_context && at_departure_town?(state)
    raise "Viagem indisponível" unless available?(state) && destination(state, key)
    status, reservations = preview(state, key)
    raise message_for(status) unless status == :ok
    point = destination(state, key)
    before = [$game_map.map_id, $game_player.x, $game_player.y, $game_player.direction]
    old_state = $PokemonGlobal.blue_regions
    old_party = $player.party.dup
    old_slots = reservations.map { |pkmn, pos| [pos, $PokemonStorage[pos[0],pos[1]]] }
    old_mechanics = $PokemonGlobal.blue_campaign_mechanics
    old_bag = Marshal.load(Marshal.dump($bag))
    pc_storage = $PokemonGlobal.respond_to?(:pcItemStorage) ?
                   $PokemonGlobal.pcItemStorage : nil
    old_pc_items = pc_storage && Marshal.load(Marshal.dump(pc_storage.items))
    staged_bag, source_items, staged_pc = stage_local_bag(state, key)
    # Preserve the player's actual choices independently for each region.
    # The first Decades arrival uses all mechanics except Dynamax, and later
    # returns restore any changes the player made while in Decades.
    next_state = Marshal.load(Marshal.dump(state))
    next_state["region_key_items"] ||= {}
    next_state["region_key_items"][state["current"]] = source_items
    next_state["mechanics_by_region"] ||= {}
    if old_mechanics.is_a?(Hash)
      next_state["mechanics_by_region"][state["current"]] = old_mechanics.dup
    end
    new_mechanics = next_state["mechanics_by_region"][key]
    unless new_mechanics.is_a?(Hash)
      new_mechanics = BlueCampaign.default_mechanics_for(key)
    end
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
      $PokemonGlobal.blue_campaign_mechanics = new_mechanics.dup
      # Keep the exact same Bag object: native item/ready-menu screens may
      # retain references to it. Only replace its serialized contents.
      $bag.pockets.replace(staged_bag.pockets)
      $bag.registered_items.replace(staged_bag.registered_items)
      pc_storage.items.replace(staged_pc.items) if pc_storage && staged_pc
      pbFadeOutIn { move_to(point) }
      true
    rescue StandardError => error
      $PokemonGlobal.blue_regions = old_state
      $PokemonGlobal.blue_campaign_mechanics = old_mechanics
      $bag.pockets.replace(old_bag.pockets)
      $bag.registered_items.replace(old_bag.registered_items)
      pc_storage.items.replace(old_pc_items) if pc_storage && old_pc_items
      $player.party.replace(old_party)
      old_slots.each { |pos, previous| $PokemonStorage[pos[0],pos[1]] = previous }
      if $game_map.map_id != before[0] || $game_player.x != before[1] || $game_player.y != before[2]
        pbFadeOutIn { move_to(before) }
      end
      raise error
    end
  end

  # The player must speak with the actual agent in the initial town.
  # No travel from arbitrary routes, menus, battle scenes or another region.
  def self.at_departure_town?(state)
    return false unless state && $game_map
    case state["current"]
    when "DECADES" then $game_map.map_id == decades_city_map_id
    when "KANTO"
      town = kanto_town_point
      !!town && $game_map.map_id == town[0]
    when "JOHTO"
      point = johto_installed? && BlueRegionStart.johto_agent_point
      !!point && $game_map.map_id == point[0]
    when "HOENN"
      point = hoenn_town_point
      !!point && $game_map.map_id == point[0]
    when "SINNOH"
      point = sinnoh_points&.last
      !!point && $game_map.map_id == point[0]
    else false
    end
  end

  def self.travel(key, quiet = false)
    # A transport request is only valid inside the initial-town NPC event.
    # 'quiet' affects message boxes, not permission to teleport.
    return false unless @npc_event_context
    state = BlueRegions.snapshot
    return false unless available?(state) && at_departure_town?(state)
    status, reservations = preview(state, key)
    if status != :ok
      pbMessage(message_for(status)) unless quiet
      return false
    end
    if !quiet
      notice = _INTL("Viajar para {1}? Sua equipe e seu save serão mantidos. Itens-chave e HMs ficam guardados na região de origem e retornam quando você voltar.", BlueRegions.info(key)["name"])
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
    unless from_npc && available?(state) && at_departure_town?(state)
      pbMessage(_INTL("Para viajar, fale com o Agente Regional na cidade inicial da região atual. Apenas campanhas instaladas podem receber visitantes."))
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
          if key == "HOENN"
            pbMessage(hoenn_pending_message)
          else
            pbMessage(message_for(:locked))
          end
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
    return unless installed? && map && map.map_id == decades_city_map_id
    state = $PokemonGlobal && $PokemonGlobal.blue_regions
    return unless state.nil? || (state.is_a?(Hash) &&
      state["version"] == 1 && state["current"] == "DECADES")
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
    map.events[event.id] = Game_Event.new(map.map_id, event, map)
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
    map.events[event.id] = Game_Event.new(map.map_id,event,map)
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
    map.events[event.id] = Game_Event.new(map.map_id,event,map)
  end

  # The same physical travel agent appears in Littleroot only after the
  # 199-map installation has passed its native file/proof gate. Keep the
  # source event table untouched and never occupy the travel-arrival tile.
  HOENN_AGENT_NAME = "Agente Regional Hoenn".freeze
  def self.attach_hoenn_agent(map)
    return unless hoenn_installed? && map && map.events.is_a?(Hash)
    town = hoenn_town_point
    return unless town && map.map_id == town[0]
    state = $PokemonGlobal && $PokemonGlobal.blue_regions
    return unless state.is_a?(Hash) && state["version"] == 1 &&
      state["current"] == "HOENN"
    return if map.events.values.any? { |event| event.name == HOENN_AGENT_NAME }
    return unless defined?(RPG::Event) && defined?(RPG::EventCommand) && defined?(Game_Event)
    occupied = map.events.values.map { |event| [event.x, event.y] }
    x0, y0 = town[1,2]
    positions = (1..5).flat_map do |distance|
      (-distance..distance).flat_map do |dx|
        dy = distance - dx.abs
        (dy == 0 ? [0] : [-dy, dy]).map { |offset| [x0+dx, y0+offset] }
      end
    end.uniq
    point = positions.find { |x,y| !occupied.include?([x,y]) &&
      (map.valid?(x,y) rescue false) && (map.passable?(x,y,2) rescue false) }
    return unless point
    event = RPG::Event.new(point[0], point[1])
    event.id = (map.events.keys.max || 0) + 1
    event.name = HOENN_AGENT_NAME
    page = event.pages.first
    page.graphic.character_name = DECADES_AGENT_GRAPHIC
    page.trigger = 0
    page.list = [
      RPG::EventCommand.new(355,0,["BlueRegionTravel.agent(true)"]),
      RPG::EventCommand.new(0,0,[])
    ]
    map.events[event.id] = Game_Event.new(map.map_id, event, map)
  end

  SINNOH_AGENT_NAME = "Agente Regional Sinnoh".freeze
  def self.attach_sinnoh_agent(map)
    point = sinnoh_points&.last
    return unless point && map.map_id == point[0] && map.events.is_a?(Hash)
    x, y = point[1,2]
    return unless map.valid?(x,y) && map.passable?(x,y,2)
    return if map.events.values.any? { |event| event.name == SINNOH_AGENT_NAME || [event.x,event.y] == [x,y] }
    event = RPG::Event.new(x,y)
    event.id = (map.events.keys.max || 0) + 1
    event.name = SINNOH_AGENT_NAME
    page = event.pages.first
    page.graphic.character_name = DECADES_AGENT_GRAPHIC
    page.trigger = 0
    page.list = [RPG::EventCommand.new(355,0,["BlueRegionTravel.agent(true)"]), RPG::EventCommand.new(0,0,[])]
    map.events[event.id] = Game_Event.new(map.map_id,event,map)
  end

  # Map setup is not always repeated after loading an existing save.
  # Populate events BEFORE Spriteset_Map builds its character sprites, so a
  # player already standing in Cherryhill can see the NPC on first load.
  # MapFactory can set up several connected maps per player crossing.  The
  # four agent installers each verify regional installations, including 142
  # Kanto maps and Hoenn's provenance checks.  Never run those gates for an
  # unrelated route: dispatch only to the town that can own this NPC.
  #
  # Cache positive *map IDs* only for this running game process.  Android
  # updates require the game to be closed; a fresh launch rechecks the proofs.
  # No failed check is cached, and the actual town's agent installer still
  # performs its original live authorization before creating an event.
  def self.agent_map_id(region)
    @agent_map_ids ||= {}
    return @agent_map_ids[region] if @agent_map_ids.key?(region)
    id = case region
         when "DECADES"
           decades_city_map_id
         when "KANTO"
           town = installed? && kanto_town_point
           town && town[0]
         when "JOHTO"
           johto_installed? ? BlueRegionStart.johto_agent_point&.first : nil
         when "HOENN"
           hoenn_installed? ? BlueRegionStart.hoenn_town_point&.first : nil
         when "SINNOH"
           sinnoh_points&.last&.first
         end
    # MapInfos may not yet be ready during startup: don't freeze the
    # fallback Decades ID before the native registry has loaded.
    ready = region != "DECADES" ||
      (defined?($data_mapinfos) && $data_mapinfos.respond_to?(:each_with_index))
    @agent_map_ids[region] = id if ready && id.is_a?(Integer) && id > 0
    id
  end

  def self.attach_agents(map)
    return unless map && map.respond_to?(:map_id)
    state = $PokemonGlobal && $PokemonGlobal.blue_regions
    region = if state.nil?
               "DECADES"
             elsif state.is_a?(Hash) && state["version"] == 1
               state["current"]
             end
    return unless %w[DECADES KANTO JOHTO HOENN SINNOH].include?(region)
    return unless map.map_id == agent_map_id(region)
    case region
    when "DECADES" then attach_decades_agent(map)
    when "KANTO"   then attach_kanto_agent(map)
    when "JOHTO"   then attach_johto_agent(map)
    when "HOENN"   then attach_hoenn_agent(map)
    when "SINNOH"  then attach_sinnoh_agent(map)
    end
  end

  module DecadesTownAgent
    def setup(*args)
      result = super
      BlueRegionTravel.attach_agents(self)
      result
    end
  end

  module VisibleAgentsOnLoad
    def createSpritesets(*args)
      if defined?($map_factory) && $map_factory &&
         $map_factory.respond_to?(:maps)
        $map_factory.maps.each { |map| BlueRegionTravel.attach_agents(map) }
      else
        BlueRegionTravel.attach_agents($game_map) if defined?($game_map)
      end
      super
    end

    def createSingleSpriteset(*args)
      if defined?($map_factory) && $map_factory && args[0].is_a?(Integer)
        BlueRegionTravel.attach_agents($map_factory.maps[args[0]])
      end
      super
    end
  end

  def self.install
    return if @installed
    Game_Map.prepend(DecadesTownAgent) if defined?(Game_Map) && !Game_Map.ancestors.include?(DecadesTownAgent)
    Scene_Map.prepend(VisibleAgentsOnLoad) if defined?(Scene_Map) &&
      !Scene_Map.ancestors.include?(VisibleAgentsOnLoad)
    PokemonStorageScreen.prepend(StorageRules)
    # Travel is deliberately NOT registered in the pause menu. Interact with
    # the NPC in Pallet, Cherryhill, New Bark or Littleroot instead.
    @installed = true
  end
end
