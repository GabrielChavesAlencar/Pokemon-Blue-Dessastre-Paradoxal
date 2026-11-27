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

  def self.cross(scene, door)
    source, event_id, threshold, destination, arrival =
      door.values_at("source", "event", "threshold", "destination", "arrival")
    require!($game_map.map_id == source, "Porta procurada no mapa errado")
    event = $game_map.events.fetch(event_id)
    require!(event.trigger == 1 && [event.x, event.y] == threshold, "Player Touch ausente")
    directions = path_to(threshold)
    require!(!directions.empty?, "Personagem já parado no gatilho")
    directions.each { |direction| step(direction) }
    require!(event.starting, "Andar até a porta não iniciou o evento")
    interpreter = pbMapInterpreter
    require!(!interpreter.running?, "Interpretador já ocupado antes da porta")
    interpreter.setup_starting_event
    require!(interpreter.running? && interpreter.instance_variable_get(:@event_id) == event_id,
             "Interpretador escolheu outro evento")
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
    { "from" => source, "event" => event_id, "to" => requested, "steps" => directions.length }
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
    map, x, y = config.fetch("spawn")
    $map_factory.setup(map)
    $game_player.moveto(x, y)
    scene = Scene_Map.new
    $scene = scene
    scene.createSpritesets
    Graphics.transition(0)
    edges = config.fetch("doors").to_h { |door| [door.values_at("source", "destination"), door] }
    walked = []
    visited = []
    saved_at = nil
    config.fetch("journey").each_cons(2) do |source, destination|
      walked << cross(scene, edges.fetch([source, destination]))
      visited << destination
      next unless destination == config.fetch("map_ids").fetch("UNOVA_ACCUMULA_CENTER")
      scene.dispose
      scene = nil
      saved_at = reload_here
      scene = Scene_Map.new
      $scene = scene
      scene.createSpritesets
    end
    require!(position[0] == map && visited.uniq.size == 7, "Travessia de volta incompleta")
    require!(!saved_at.nil? && walked.size == edges.size, "Faltou uma porta ou prova de save")
    { "windows_game_exe" => true, "doors" => walked, "visited_map_ids" => visited.uniq.sort,
      "saved_and_reloaded_at" => saved_at, "joiplay_tested" => false }
  ensure
    scene.dispose if scene
  end
end
