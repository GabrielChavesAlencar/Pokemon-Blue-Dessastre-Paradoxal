# Generated destinations are limited to this private experimental copy.
module BlueSinnohQATeleport
  DESTINATIONS = __F01_DESTINATIONS__.freeze

  def self.available?
    return false unless defined?(BlueSinnohExperimental) &&
      BlueSinnohExperimental.respond_to?(:private_copy?) &&
      BlueSinnohExperimental.private_copy? && $player && $game_map &&
      defined?($PokemonGlobal) && $PokemonGlobal &&
      $PokemonGlobal.respond_to?(:blue_regions)
    state=$PokemonGlobal.blue_regions
    state.is_a?(Hash) && state["current"]=="SINNOH" &&
      DESTINATIONS.any? { |r| r[3] && r[3][0]==$game_map.map_id }
  end

  def self.choose(rows)
    return nil if rows.empty?
    labels=rows.map { |r| r[1]+(r[3] ? "" : " [Pendente]") }
    choice=pbMessage(_INTL("Escolha um destino:"),labels,-1)
    return nil unless choice.is_a?(Integer) && choice>=0 && choice<rows.length
    row=rows[choice]
    unless row[3]
      pbMessage(_INTL("Este mapa ainda nao foi instalado no piloto."))
      return nil
    end
    row
  end

  def self.select_destination
    categories=DESTINATIONS.map { |r| r[2] }.uniq
    options=["Buscar destino"]+categories.map do |cat|
      rows=DESTINATIONS.select { |r| r[2]==cat }
      "#{cat} (#{rows.count { |r| r[3] }}/#{rows.length})"
    end
    index=pbMessage(_INTL("Teleportar - Sinnoh QA"),options,-1)
    return nil unless index.is_a?(Integer) && index>=0 && index<options.length
    if index==0
      query=pbEnterText(_INTL("Nome ou numero da rota"),0,32,"")
      return nil if !query || query.strip.empty?
      term=query.strip.downcase
      rows=DESTINATIONS.select { |r| r[0].downcase.include?(term) || r[1].downcase.include?(term) }
      if rows.empty?
        pbMessage(_INTL("Nenhum destino encontrado."))
        return nil
      end
    else
      rows=DESTINATIONS.select { |r| r[2]==categories[index-1] }
    end
    # Stable category listing; installed destinations are shown first.
    choose(rows.sort_by { |r| [r[3] ? 0 : 1,r[1]] })
  end

  def self.valid_destination?(row)
    return false unless available? && row && DESTINATIONS.include?(row) && row[3]
    mid,x,y=row[3]
    return false unless [mid,x,y].all? { |n| n.is_a?(Integer) && n>=0 }
    return false unless defined?(BlueKantoTitle) &&
      BlueKantoTitle.sinnoh_experimental_maps_ready?
    # Revalidate current map file through the private title's hash gate.
    File.file?(sprintf("Data/Map%03d.rxdata",mid)) &&
      !File.symlink?(sprintf("Data/Map%03d.rxdata",mid))
  end

  def self.open(menu)
    return false unless available?
    menu.pbHideMenu
    closed=false
    begin
      row=select_destination
      return false unless valid_destination?(row)
      return false unless pbConfirmMessage(_INTL("Teleportar para {1}? Isso nao completa a historia.",row[1]))
      return false unless valid_destination?(row) && $scene.respond_to?(:transfer_player)
      menu.pbEndScene
      closed=true
      $game_temp.in_menu=false
      mid,x,y=row[3]
      @arrival_map=mid
      @arrival_player=$game_player
      pbFadeOutIn do
        $game_temp.player_new_map_id=mid
        $game_temp.player_new_x=x
        $game_temp.player_new_y=y
        $game_temp.player_new_direction=2
        pbDismountBike
        $scene.transfer_player
        $game_map.autoplay
        $game_map.refresh
      end
      true
    ensure
      unless closed
        menu.pbRefresh
        menu.pbShowMenu
      end
    end
  end

  # Do not run the map-entry story autorun just because QA teleported here.
  # The suppression is transient; ordinary NPC interaction is unaffected.
  def self.suppress_story_autorun?(event)
    @arrival_player && @arrival_player.equal?($game_player) &&
      event.map_id==@arrival_map && event.trigger==3 &&
      %w[SN_PROFILE_SETUP SN_MOTHER_SCENE SN_BARRY_SCENE SN_ROWAN_SCENE SN_DEX_SCENE].include?(event.name)
  end

  def self.clear_arrival_if_left
    @arrival_map=nil if !$game_map || $game_map.map_id!=@arrival_map
  end

  module StoryAutorun
    def check_event_trigger_auto
      return if BlueSinnohQATeleport.suppress_story_autorun?(self)
      super
    end
  end

  # Voltseon's menu resolves every command through an existing theme bitmap.
  # Reuse the stock town-map icon rather than reference a nonexistent image.
  module ThemeIcon
    def from_current_menu_theme(data,default=nil)
      return super("menu_town_map", "menu_town_map") if data=="menu_blue_sinnoh_qa_teleport" &&
        BlueSinnohQATeleport.available? && pbResolveBitmap(MENU_FILE_PATH+"menu_town_map")
      return super("menu_bag","menu_bag") if data=="menu_blue_sinnoh_qa_teleport" &&
        BlueSinnohQATeleport.available?
      super
    end
  end

  def self.install!
    return unless defined?(BlueSinnohExperimental) && BlueSinnohExperimental.respond_to?(:private_copy?) &&
      BlueSinnohExperimental.private_copy? && defined?(MenuHandlers)
    if defined?(Game_Event) && Game_Event.method_defined?(:check_event_trigger_auto) &&
       !Game_Event.ancestors.include?(StoryAutorun)
      Game_Event.prepend(StoryAutorun)
    end
    if defined?(EventHandlers)
      EventHandlers.add(:on_enter_map,:blue_sinnoh_qa_arrival,proc { |*args| BlueSinnohQATeleport.clear_arrival_if_left })
    end
    if defined?(PokemonSystem) && PokemonSystem.method_defined?(:from_current_menu_theme) &&
       defined?(MENU_FILE_PATH) && !PokemonSystem.ancestors.include?(ThemeIcon)
      PokemonSystem.prepend(ThemeIcon)
    end
    MenuHandlers.add(:pause_menu,:blue_sinnoh_qa_teleport,{
      "name"=>_INTL("Teleportar - Sinnoh QA"),
      "order"=>55,
      "condition"=>proc { BlueSinnohQATeleport.available? },
      "effect"=>proc { |menu| BlueSinnohQATeleport.open(menu) }
    })
  end
end
