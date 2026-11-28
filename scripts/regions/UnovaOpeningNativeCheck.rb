# Real engine movement, transfer and save/load in a disposable Windows game.
module UnovaOpeningNativeCheck
  DIRECTIONS = { 2 => [0, 1], 4 => [-1, 0], 6 => [1, 0], 8 => [0, -1] }.freeze

  def self.position
    [$game_map.map_id, $game_player.x, $game_player.y]
  end

  def self.require!(value, message)
    raise message unless value
  end

  def self.path_to(target)
    start = [$game_player.x, $game_player.y]
    blocked = $game_map.events.values.map { |event| [event.x, event.y] } - [target]
    queue = [start]
    path = { start => [] }
    until queue.empty?
      cell = queue.shift
      return path.fetch(cell) if cell == target
      DIRECTIONS.each do |direction, (dx, dy)|
        next_cell = [cell[0] + dx, cell[1] + dy]
        next if path.key?(next_cell) || blocked.include?(next_cell)
        next unless $game_map.valid?(*next_cell) && $game_player.passable?(*cell, direction)
        path[next_cell] = path.fetch(cell) + [direction]
        queue << next_cell
      end
    end
    raise "Sem caminho no motor para #{position.inspect} -> #{target.inspect}"
  end

  def self.step(direction)
    before = position
    dx, dy = DIRECTIONS.fetch(direction)
    $game_player.move_generic(direction, true)
    require!(position == [before[0], before[1] + dx, before[2] + dy],
             "Passo recusado pelo motor: #{before.inspect} direção #{direction}")
    deadline = System.uptime + 3
    loop do
      Graphics.update
      $game_player.update
      break unless $game_player.moving?
      require!(System.uptime < deadline, "Movimento não terminou")
    end
  end

  def self.start_door(door)
    source, event_id, threshold = door.values_at("source", "event", "threshold")
    require!($game_map.map_id == source, "Porta procurada no mapa errado")
    event = $game_map.events.fetch(event_id)
    require!(event.trigger == 1 && [event.x, event.y] == threshold, "Player Touch ausente")
    directions = path_to(threshold)
    require!(!directions.empty?, "Personagem já parado no gatilho")
    directions.each { |direction| step(direction) }
    require!(event.starting, "Andar até a porta não iniciou o evento")
    directions.length
  end

  def self.start_interpreter(event_id)
    interpreter = pbMapInterpreter
    require!(!interpreter.running?, "Interpretador ocupado antes da interação")
    interpreter.setup_starting_event
    require!(interpreter.running? && interpreter.instance_variable_get(:@event_id) == event_id,
             "Interpretador escolheu outro evento")
    interpreter
  end

  def self.cross(scene, door)
    source, event_id, destination, arrival = door.values_at("source", "event", "destination", "arrival")
    steps = start_door(door)
    interpreter = start_interpreter(event_id)
    deadline = System.uptime + 3
    until $game_temp.player_transferring
      interpreter.update
      require!(interpreter.running? && System.uptime < deadline, "Evento não solicitou transferência")
      Graphics.update
    end
    requested = [$game_temp.player_new_map_id, $game_temp.player_new_x, $game_temp.player_new_y]
    require!(requested == [destination, *arrival], "Evento solicitou destino incorreto")
    scene.transfer_player
    interpreter.update
    require!(position == requested && !$game_temp.player_transferring,
             "Transferência de cena não chegou ao destino")
    { "from" => source, "event" => event_id, "to" => requested, "steps" => steps }
  end

  def self.finish_interaction(event_id)
    interpreter = start_interpreter(event_id)
    deadline = System.uptime + 3
    while interpreter.running?
      interpreter.update
      require!(!$game_temp.player_transferring, "Interação iniciou uma transferência inesperada")
      require!(System.uptime < deadline, "Interação não terminou")
      Graphics.update if interpreter.running?
    end
  end

  def self.act(actor)
    map, event_id, approach = actor.values_at("map", "event", "approach")
    require!($game_map.map_id == map, "Estação de campo procurada no mapa errado")
    path_to(approach).each { |direction| step(direction) }
    $game_player.turn_up
    require!($game_player.check_event_trigger_there([0]), "Botão de ação não iniciou a estação")
    finish_interaction(event_id)
  end

  def self.verify_encounter(table)
    grass = [20, 13]
    path_to(grass).each { |direction| step(direction) }
    type = $PokemonEncounters.encounter_type
    require!(type == :Land && $PokemonEncounters.encounter_possible_here?, "Grama sem encontro nativo")
    encounter = GameData::Encounter.get($game_map.map_id, 0)
    slots = encounter.types.fetch(:Land).map { |weight, species, minimum, maximum| [weight, species.to_s, minimum, maximum] }
    require!(slots == table, "Encontros da Rota 1 divergiram do PBS")
    species, level = $PokemonEncounters.choose_wild_pokemon(type)
    require!(slots.any? { |_, name, minimum, maximum| species.to_s == name && level.between?(minimum, maximum) },
             "Engine sorteou um encontro fora da tabela")
    { "grass" => grass, "slots" => slots, "selected" => [species.to_s, level] }
  end

  def self.verify_check_in(actor, choices)
    require!(!BlueUnovaOpeningStory.checked_in? && $player.party.empty?, "Início de QA já tinha parceiro")
    choices.push(3, 0)
    act(actor)
    require!(!BlueUnovaOpeningStory.checked_in? && $player.party.empty?, "Cancelar concedeu um parceiro")
    act(actor)
    act(actor)
    require!(choices.empty? && $player.party.map(&:species) == [:SNIVY], "Credenciamento duplicou ou perdeu o parceiro")
  end

  def self.verify_report(actor)
    before = $bag.quantity(:POKEBALL)
    act(actor)
    act(actor)
    require!($bag.quantity(:POKEBALL) == before + BlueUnovaOpeningStory::BALL_REWARD,
             "O kit foi perdido ou entregue mais de uma vez")
    $bag.quantity(:POKEBALL)
  end

  def self.reload_here
    before = position
    slot = "Unova Opening Native QA"
    require!(Game.save(slot), "Game.save não completou o save de QA")
    path = SaveData.get_full_path(slot)
    saved = SaveData.read_from_file(path)
    require!(saved.is_a?(Hash), "Save do motor fora do formato esperado")
    SaveData.mark_values_as_unloaded
    Game.load(saved)
    require!(position == before, "Game.load não recuperou o mapa e a posição")
    before
  end

  def self.run(config)
    SaveData.initialize_bootup_values
    BlueRegionStart.request_initial("DECADES") if defined?(BlueRegionStart)
    Game.start_new
    # Walk deterministically while testing the real encounter calculation separately.
    $game_system.encounter_disabled = true
    choices = []
    original_message = Object.instance_method(:pbMessage)
    Object.send(:define_method, :pbMessage) do |_text, commands = nil, *_args|
      next unless commands.is_a?(Array)
      raise "Escolha inesperada no teste de QA" if choices.empty?
      choices.shift
    end
    Object.send(:private, :pbMessage)
    map, x, y = config.fetch("spawn")
    $map_factory.setup(map)
    $game_player.moveto(x, y)
    scene = Scene_Map.new
    $scene = scene
    scene.createSpritesets
    Graphics.transition(0)
    edges = config.fetch("doors").to_h { |door| [door.values_at("source", "destination"), door] }
    maps = config.fetch("map_ids")
    fieldwork = config.fetch("fieldwork")
    walked = []
    visited = []
    saved_at = nil
    wild = nil
    blocked_without_partner = false
    config.fetch("journey").each_cons(2) do |source, destination|
      walked << cross(scene, edges.fetch([source, destination]))
      visited << destination
      if destination == maps.fetch("UNOVA_NUVEMA_TOWN") && !blocked_without_partner
        gate = edges.fetch([destination, maps.fetch("UNOVA_ROUTE_01")])
        start_door(gate)
        finish_interaction(gate.fetch("event"))
        require!($game_map.map_id == destination, "Saída abriu sem credencial")
        blocked_without_partner = true
      end
      if destination == fieldwork.fetch("check_in").fetch("map")
        verify_check_in(fieldwork.fetch("check_in"), choices)
      end
      if destination == fieldwork.fetch("read_gauge").fetch("map") && wild.nil?
        wild = verify_encounter(config.fetch("encounters"))
        act(fieldwork.fetch("read_gauge"))
      end
      next unless destination == fieldwork.fetch("deliver_report").fetch("map")
      balls = verify_report(fieldwork.fetch("deliver_report"))
      scene.dispose
      scene = nil
      saved_at = reload_here
      scene = Scene_Map.new
      $scene = scene
      scene.createSpritesets
      require!($player.party.map(&:species) == [:SNIVY] && $bag.quantity(:POKEBALL) == balls,
               "O save perdeu parceiro ou Poké Bolas")
      act(fieldwork.fetch("deliver_report"))
      require!($bag.quantity(:POKEBALL) == balls, "O save permitiu receber o kit uma segunda vez")
    end
    require!(position[0] == map && visited.uniq.size == 7, "Travessia de volta incompleta")
    require!(!saved_at.nil? && walked.size == edges.size, "Faltou uma porta ou prova de save")
    { "windows_game_exe" => true, "doors" => walked, "visited_map_ids" => visited.uniq.sort,
      "saved_and_reloaded_at" => saved_at, "joiplay_tested" => false, "wild_encounter" => wild,
      "route_blocked_without_partner" => blocked_without_partner, "fieldwork" => BlueUnovaOpeningStory.progress }
  ensure
    scene.dispose if scene
    if original_message
      Object.send(:define_method, :pbMessage, original_message)
      Object.send(:private, :pbMessage)
    end
  end
end
