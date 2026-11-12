# Local Kanto pilot events. Loaded only by the separately prepared test game.
module BlueKantoPilot
  STARTERS = [:BULBASAUR, :CHARMANDER, :SQUIRTLE].freeze
  RIVAL_VERSIONS = {BULBASAUR: 11, CHARMANDER: 12, SQUIRTLE: 13}.freeze
  VIRIDIAN_MART_STOCK = [:POKEBALL, :POTION, :ANTIDOTE, :PARALYZEHEAL].freeze

  def self.progress
    $PokemonGlobal.blue_regions ||= BlueRegions.new_state("KANTO")
  end

  def self.starter
    progress["pilot_starter"]&.to_sym
  end

  def self.choose_starter
    if starter
      if progress["pilot_oak_parcel_received"] && !progress["pilot_oak_parcel_delivered"]
        # Record the parcel's delivery in the region-specific save instead of
        # creating an unknown FRLG quest item in the Decades item catalogue.
        progress["pilot_oak_parcel_delivered"] = true
        $player.has_pokedex = true if $player.respond_to?(:has_pokedex=)
        pbMessage(_INTL("Oak: O pacote chegou de Viridian! Sua Pokédex está pronta. Obrigado!"))
      else
        pbMessage(_INTL("Oak: Cuide bem do seu {1}.", GameData::Species.get(starter).name))
      end
      return
    end
    names = STARTERS.map { |id| GameData::Species.get(id).name }
    choice = pbMessage(_INTL("Oak: Qual Pokémon vai viajar com você?"), names + [_INTL("Voltar")], 4)
    return unless choice && choice.between?(0, STARTERS.length - 1)
    species = STARTERS[choice]
    return unless pbAddPokemonSilent(species, 5)
    progress["pilot_starter"] = species.to_s
    $bag.add(:POKEBALL, 5)
    $bag.add(:POTION, 2)
    pbSetPokemonCenter
    pbMessage(_INTL("Oak: {1} escolheu você! Pegue estas Poké Bolas e fale com Blue.", names[choice]))
  end

  # A safe, local story step for the first Pallet -> Viridian -> Pallet
  # loop. The source item need not exist in Decades; state is saved only in
  # the active Kanto campaign. Existing Boulder+ saves skip the new quest.
  def self.viridian_mart
    completed = progress["pilot_oak_parcel_delivered"]
    advanced = BlueRegions.local_achievements(progress, "KANTO").include?("BOULDER")
    if starter && !completed && !progress["pilot_oak_parcel_received"] && !advanced
      progress["pilot_oak_parcel_received"] = true
      pbMessage(_INTL("Funcionário: Oak pediu que você leve este pacote até seu laboratório em Pallet."))
    elsif progress["pilot_oak_parcel_received"] && !completed
      pbMessage(_INTL("Funcionário: O pacote é para o professor Oak, em Pallet."))
    end
    pbPokemonMart(VIRIDIAN_MART_STOCK)
  end

  def self.rival_done?
    progress["pilot_rival"] == true
  end

  def self.rival
    if !starter
      pbMessage(_INTL("Blue: Escolha o seu Pokémon primeiro."))
      return
    end
    if rival_done?
      pbMessage(_INTL("Blue: Continue treinando. Nossa revanche fica para a próxima etapa!"))
      return
    end
    setBattleRule("canLose")
    result = TrainerBattle.start(:BLUE_KANTO_RIVAL, "Blue", RIVAL_VERSIONS.fetch(starter))
    $player.heal_party
    progress["pilot_rival"] = true
    if result
      pbMessage(_INTL("Blue: Você venceu. Vou treinar para a revanche!"))
    else
      pbMessage(_INTL("Blue: Essa foi minha. Vá treinar na Rota 1."))
    end
  end

  def self.battle(type, name, event_key = nil, version = 0)
    return unless starter
    if type == :BLUE_KANTO_LEADER_SABRINA && !progress["pilot_silph_rescued"]
      pbMessage(_INTL("Sabrina está aguardando a libertação da Silph Co. Derrote Giovanni primeiro."))
      return
    end
    if type == :BLUE_KANTO_LEADER_SURGE && !progress["pilot_surge_unlocked"]
      pbMessage(_INTL("Lt. Surge aguarda atrás das trancas elétricas. Resolva o enigma das lixeiras primeiro."))
      return
    end
    wins = (progress["pilot_wins"] ||= [])
    # New events persist stable region/map/event keys. Accept old name-only
    # entries from pilot saves built before this fix without replaying battles.
    key = event_key || "#{type}:#{name}"
    if wins.include?(key) || wins.include?(name)
      pbMessage(_INTL("{1}: Boa sorte na sua jornada!", name))
      return
    end
    setBattleRule("canLose")
    won = TrainerBattle.start(type, name, version)
    unless won
      $player.heal_party
      return
    end
    wins << key
    if type == :BLUE_KANTO_LEADER && BlueRegions.award(progress, "KANTO", "BOULDER")
      pbMessage(_INTL("Brock: A Boulder Badge é sua. O caminho para Cerulean está aberto!"))
    elsif type == :BLUE_KANTO_LEADER_MISTY && BlueRegions.award(progress, "KANTO", "CASCADE")
      pbMessage(_INTL("Misty: Você conquistou a Cascade Badge! Siga ao sul para Vermilion!"))
    elsif type == :BLUE_KANTO_LEADER_SURGE && BlueRegions.award(progress, "KANTO", "THUNDER")
      pbMessage(_INTL("Lt. Surge: A Thunder Badge é sua! Agora você pode usar Fly em Kanto."))
    elsif type == :BLUE_KANTO_LEADER_ERIKA && BlueRegions.award(progress, "KANTO", "RAINBOW")
      pbMessage(_INTL("Erika: Você conquistou a Rainbow Badge!"))
    elsif type == :BLUE_KANTO_LEADER_KOGA && BlueRegions.award(progress, "KANTO", "SOUL")
      pbMessage(_INTL("Koga: A Soul Badge agora é sua!"))
    elsif type == :BLUE_KANTO_ROCKETBOSS && name == "Giovanni"
      progress["pilot_silph_rescued"] = true
      pbMessage(_INTL("Giovanni foi derrotado! A Silph Co. está livre."))
    elsif type == :BLUE_KANTO_LEADER_SABRINA && BlueRegions.award(progress, "KANTO", "MARSH")
      pbMessage(_INTL("Sabrina: Você conquistou a Marsh Badge!"))
    end
  end

  # MAN-02: keep the native line-of-sight trainer on Event Touch until a
  # real victory. This is invoked only by the trainer's own local event page.
  # The page's second state is a self-switch A; old name-only saves still work.
  def self.sync_trainer_event(key, name, event_id)
    won = progress.fetch("pilot_wins", [])
    return false unless won.include?(key) || won.include?(name)
    return false if !$game_map || !$game_map.events[event_id]
    index = [$game_map.map_id, event_id, "A"]
    unless $game_self_switches[index]
      $game_self_switches[index] = true
      $game_map.need_refresh = true
    end
    true
  end

  def self.trainer_repeat(name)
    pbMessage(_INTL("{1}: Boa sorte na sua jornada!", name))
  end

  SURGE_CANS = ([4, 10] + (22..34).to_a).freeze
  SURGE_LOCKS = ([8] + (11..19).to_a).freeze

  # The original gym used source-project global switches. The pilot uses only
  # its own Kanto state and gym-event self switches, so Decades remains safe.
  def self.surge_pairs
    cans = SURGE_CANS.filter_map do |id|
      event = $game_map.events[id]
      [id, event.x, event.y] if event
    end
    return [] if cans.length < 2
    horizontal_or_vertical = cans.combination(2).filter_map do |a, b|
      next unless a[1] == b[1] || a[2] == b[2]
      [[a[0], b[0]], (a[1]-b[1]).abs + (a[2]-b[2]).abs]
    end
    return [] if horizontal_or_vertical.empty?
    closest = horizontal_or_vertical.map(&:last).min
    horizontal_or_vertical.select { |_pair, distance| distance == closest }.map(&:first)
  end

  def self.surge_can(event_id)
    if progress["pilot_surge_unlocked"]
      pbMessage(_INTL("As duas trancas elétricas já foram desativadas."))
      return
    end
    possible = surge_pairs
    if possible.empty?
      pbMessage(_INTL("O mecanismo não está pronto nesta cópia do ginásio."))
      return
    end
    progress["pilot_surge_solution"] ||= possible.sample
    target = progress["pilot_surge_solution"]
    if !progress["pilot_surge_first"]
      if event_id == target[0]
        progress["pilot_surge_first"] = true
        pbMessage(_INTL("Você encontrou a primeira chave! Procure outra lixeira próxima."))
      else
        pbMessage(_INTL("Não há chave nesta lixeira."))
      end
    elsif event_id == target[1]
      progress["pilot_surge_unlocked"] = true
      progress["pilot_surge_first"] = false
      SURGE_LOCKS.each do |id|
        $game_self_switches[[$game_map.map_id, id, "A"]] = true
      end
      $game_map.need_refresh = true
      pbMessage(_INTL("As duas trancas foram desativadas! Lt. Surge está acessível."))
    else
      progress["pilot_surge_first"] = false
      progress.delete("pilot_surge_solution")
      pbMessage(_INTL("Chave errada! O sistema reiniciou a sequência de lixeiras."))
    end
  end

  def self.surge_gate
    pbMessage(_INTL("A trava elétrica está ativa. Encontre duas chaves nas lixeiras."))
  end

  # TEMPORARY phase 08 story bridge: Bill's canonical S.S. Ticket event is
  # outside the installed route until the Cerulean north passage is audited.
  # Only players with Cascade may claim a ticket; never award it more than once.
  def self.ticketmaster
    if !BlueRegions.local_achievements(progress, "KANTO").include?("CASCADE")
      pbMessage(_INTL("Porto: Primeiro conquiste a Cascade Badge em Cerulean."))
      return
    end
    if progress["pilot_ss_ticket"] || (GameData::Item.exists?(:SSTICKET) && $bag.has?(:SSTICKET))
      progress["pilot_ss_ticket"] = true
      pbMessage(_INTL("Porto: Sua passagem para o S.S. Anne está liberada!"))
    elsif !GameData::Item.exists?(:SSTICKET)
      # Decades does not guarantee the FRLG ticket item exists. Use a local
      # save-state permit without changing native item PBS or other saves.
      progress["pilot_ss_ticket"] = true
      pbMessage(_INTL("Acesso experimental: a passagem digital para o S.S. Anne está liberada."))
    elsif $bag.add(:SSTICKET, 1)
      progress["pilot_ss_ticket"] = true
      pbMessage(_INTL("Acesso experimental: recebeu o S.S. Ticket. O evento de Bill será adaptado depois."))
    else
      pbMessage(_INTL("Você precisa liberar espaço na Bolsa para receber o S.S. Ticket."))
    end
  end

  def self.harbor_gate(map_id, x, y)
    unless progress["pilot_ss_ticket"] || (GameData::Item.exists?(:SSTICKET) && $bag.has?(:SSTICKET))
      pbMessage(_INTL("O acesso ao porto exige o S.S. Ticket. Fale com o atendente."))
      return
    end
    pbFadeOutIn { BlueRegionTravel.move_to([map_id, x, y, 2]) }
  end

  # The captain's original scripts are not executed in Blue. Give the audited
  # Cut HM once, using the item ID actually available in the installed game.
  def self.captain
    events = (progress["field_events"]["KANTO"] ||= [])
    if events.include?("SS_ANNE_CAPTAIN")
      pbMessage(_INTL("Capitão: Use Cut para abrir caminhos onde tiver permissão."))
      return
    end
    item = [:HM01, :HMCUT].find { |candidate| GameData::Item.exists?(candidate) }
    unless item
      pbMessage(_INTL("O HM Cut ainda não está cadastrado nesta versão do Blue."))
      return
    end
    unless $bag.add(item, 1)
      pbMessage(_INTL("Capitão: Libere espaço na Bolsa para receber o HM Cut."))
      return
    end
    events << "SS_ANNE_CAPTAIN"
    pbMessage(_INTL("O Capitão entregou o HM Cut! A Cascade Badge permite usá-lo em Kanto."))
  end

  def self.pickup(item, key)
    collected = (progress["pilot_items"] ||= [])
    if collected.include?(key)
      pbMessage(_INTL("Você já recolheu este item."))
      return
    end
    if $bag.add(item, 1)
      collected << key
      pbMessage(_INTL("Encontrou {1}!", GameData::Item.get(item).name))
    else
      pbMessage(_INTL("Sua Bolsa está cheia. Libere espaço para recolher o item."))
    end
  end


  # Silph Card Key: persist locally, never import a foreign item into Decades.
  def self.silph_card_key
    if progress["pilot_silph_card_key"]
      pbMessage(_INTL("Você já encontrou a Card Key da Silph Co."))
      return
    end
    progress["pilot_silph_card_key"] = true
    $game_self_switches[[$game_map.map_id, 9, "A"]] = true
    $game_map.need_refresh = true
    pbMessage(_INTL("Encontrou a Card Key! Agora pode abrir as portas da Silph Co."))
  end

  # Adjacent source map event tiles form a single original locked door.
  def self.silph_door(event_ids)
    unless progress["pilot_silph_card_key"]
      pbMessage(_INTL("Uma trava de segurança. Encontre a Card Key no 5º andar."))
      return
    end
    event_ids.each do |eid|
      next unless $game_map.events[eid]
      $game_self_switches[[$game_map.map_id, eid, "A"]] = true
    end
    $game_map.need_refresh = true
    pbMessage(_INTL("A Card Key abriu a porta!"))
  end

  def self.silph_rival
    return unless starter
    versions = { BULBASAUR: 51, CHARMANDER: 52, SQUIRTLE: 53 }
    key = "KANTO_184_043"
    battle(:BLUE_KANTO_RIVAL_SILPH, "Blue", key, versions.fetch(starter))
  end

  def self.silph_president
    unless progress["pilot_silph_rescued"]
      pbMessage(_INTL("Presidente: Giovanni ainda controla o último andar!"))
      return
    end
    if progress["pilot_silph_master_ball"]
      pbMessage(_INTL("Presidente: Obrigado por libertar a Silph Co.!"))
      return
    end
    unless GameData::Item.exists?(:MASTERBALL)
      pbMessage(_INTL("A Master Ball ainda não está cadastrada nesta versão do Blue."))
      return
    end
    unless $bag.add(:MASTERBALL, 1)
      pbMessage(_INTL("Presidente: Abra espaço na Bolsa para receber a Master Ball."))
      return
    end
    progress["pilot_silph_master_ball"] = true
    pbMessage(_INTL("Recebeu a Master Ball pela libertação da Silph Co.!"))
  end

  def self.dojo_prize(species, event_id)
    unless progress.fetch("pilot_wins", []).include?("KANTO_172_012")
      pbMessage(_INTL("Vença primeiro o mestre Koichi para escolher um Pokémon."))
      return
    end
    if progress["pilot_dojo_prize"]
      pbMessage(_INTL("Você já escolheu seu Pokémon no Fighting Dojo."))
      return
    end
    if $player.party.length >= 6
      pbMessage(_INTL("Sua equipe está cheia. Deixe uma vaga para o Pokémon do dojo."))
      return
    end
    return unless GameData::Species.exists?(species)
    return unless pbConfirmMessage(_INTL("Escolher {1} como prêmio único do dojo?", GameData::Species.get(species).name))
    return unless pbAddPokemonSilent(species, 25)
    progress["pilot_dojo_prize"] = species.to_s
    [1, 2].each { |eid| $game_self_switches[[$game_map.map_id, eid, "A"]] = true }
    $game_map.need_refresh = true
    pbMessage(_INTL("Prêmio do Fighting Dojo recebido!"))
  end

  def self.silph_elevator
    filename = "Data/blue-kanto-silph-floors.txt"
    unless experimental? && File.file?(filename)
      pbMessage(_INTL("Os controles do elevador não estão disponíveis fora do piloto."))
      return
    end
    floors = File.readlines(filename, encoding: "UTF-8").filter_map do |raw|
      parts = raw.strip.split("|")
      next unless parts.length == 5
      coords = parts.map { |part| Integer(part, 10) rescue nil }
      next unless coords.all? { |value| value.is_a?(Integer) }
      floor, map_id, x, y, direction = coords
      next unless floor.between?(1, 11) && map_id > 0 && x >= 0 && y >= 0
      next unless [2, 4, 6, 8].include?(direction)
      next unless pbRgssExists?(sprintf("Data/Map%03d.rxdata", map_id))
      [floor, [map_id, x, y, direction]]
    end
    return if floors.empty?
    choice = pbMessage(_INTL("Silph Co. — escolher andar"),
                       floors.map { |row| _INTL("Andar {1}F", row[0]) } + [_INTL("Voltar")], -1)
    return unless choice && choice.between?(0, floors.length - 1)
    pbFadeOutIn { BlueRegionTravel.move_to(floors[choice][1]) }
  end

  # Travel shortcuts exist only in the standalone pilot, NEVER in the
  # main Blue campaign. Stops are generated from source-defined warp entries.
  def self.experimental?
    File.file?("Kanto pilot.json") &&
      File.file?("Data/blue-kanto-experimental-stops.txt") &&
      $PokemonGlobal && $PokemonGlobal.blue_regions.is_a?(Hash) &&
      $PokemonGlobal.blue_regions["current"] == "KANTO"
  end

  def self.experimental_stops
    return [] unless experimental?
    File.readlines("Data/blue-kanto-experimental-stops.txt", encoding: "UTF-8").filter_map do |raw|
      parts = raw.strip.split("|")
      next unless parts.length == 6
      map, x, y, dir = parts[2,4].map { |part| Integer(part, 10) rescue nil }
      next unless [map,x,y,dir].all? { |item| item.is_a?(Integer) }
      next unless map > 0 && x >= 0 && y >= 0 && [2,4,6,8].include?(dir)
      next unless pbRgssExists?(sprintf("Data/Map%03d.rxdata", map))
      [parts[1], [map,x,y,dir]]
    end
  end

  def self.experimental_menu
    return unless experimental?
    unless $player.party.any? { |pkmn| !pkmn.egg? }
      pbMessage(_INTL("Escolha um Pokémon com Oak antes de usar os teletransportes de teste."))
      return
    end
    unless $scene && $scene.respond_to?(:transfer_player) && $game_temp && !$game_temp.in_battle
      pbMessage(_INTL("O transporte de teste não está disponível durante batalhas."))
      return
    end
    stops = experimental_stops
    if stops.empty?
      pbMessage(_INTL("Nenhum destino experimental foi preparado."))
      return
    end
    choice = pbMessage(_INTL("Teste experimental: viajar sem concluir a história anterior."),
                       stops.map(&:first) + [_INTL("Cancelar")], -1)
    return if !choice || choice < 0 || choice >= stops.length
    label, point = stops[choice]
    return unless pbConfirmMessage(_INTL("Ir para {1}? Esta opção existe apenas no piloto de testes.", label))
    begin
      pbFadeOutIn { BlueRegionTravel.move_to(point) }
      pbMessage(_INTL("Chegou a {1}. Continue jogando e salve no perfil Kanto Piloto.",label))
    rescue StandardError => e
      pbMessage(_INTL("Falha no destino experimental: {1}",e.message))
    end
  end

  # The source Safari Gate is mapped for navigation, but the isolated
  # pilot must NOT start a fake Safari session: native catch rules, step
  # limits, Safari Balls and exit restoration have not been audited.
  # Both the gate's counter and its guide use this non-transactional message.
  def self.safari_preview
    pbMessage(_INTL("Safari Zone: a entrada para captura está em preparação. " +
                    "Nenhum ingresso, dinheiro ou Safari Ball será consumido nesta versão."))
  end

  # Local Pallet residents; never run the foreign FRLG quest scripts.
  def self.mom
    if $player && $player.party.any? { |pkmn| !pkmn.egg? }
      $player.heal_party
      pbMessage(_INTL("Mãe: Descanse um pouco antes de continuar sua aventura por Kanto."))
    else
      pbMessage(_INTL("Mãe: Seu quarto fica no andar de cima. Depois visite Oak no laboratório."))
    end
  end

  def self.daisy
    pbMessage(_INTL("Daisy: Bem-vindo à casa do Blue! O laboratório de Oak fica ao sul de Pallet."))
  end

  def self.heal
    $player.heal_party
    pbSetPokemonCenter
    pbMessage(_INTL("Sua equipe está descansada."))
  end
end

# This menu is visible ONLY in the isolated pilot with its local stop manifest.
MenuHandlers.add(:pause_menu, :blue_kanto_experimental, {
  "name"=>_INTL("Testes Kanto (experimental)"),
  "order"=>71,
  "condition"=>proc { |_menu| BlueKantoPilot.experimental? },
  "effect"=>proc do |menu|
    menu.pbHideMenu
    BlueKantoPilot.experimental_menu
    menu.pbShowMenu
    false
  end
})
