# Native menu callbacks are retained, including the pause/save teardown path.
module BlueDexControls
  def self.choose(title,labels,default=0);BlueBattleLab.choose(title,labels,default,1_000_010);end
  def self.in_front(scene)
    viewport=scene.instance_variable_get(:@viewport);visible=viewport.visible;viewport.visible=false
    yield
  ensure
    viewport.visible=visible if viewport && !viewport.disposed?
    Input.update
  end
  def self.text(initial)
    scene=PokemonEntryScene.new;scene.pbStartScene(_INTL('Search Pokémon name'),0,24,initial,0)
    scene.pbEntry
  ensure
    scene&.pbEndScene
  end
  module PauseMouse
    def update
      if !@menu.hidden && !@menu.start_up && BlueStartMouse.click?
        point=BlueLabPointer.position
        if BlueLabPointer.hit_sprite?(@sprites['leftarrow'],point) || BlueLabPointer.hit_sprite?(@sprites['rightarrow'],point)
          direction=BlueLabPointer.hit_sprite?(@sprites['leftarrow'],point) ? -1 : 1
          BlueLabPointer.claimed=true;shift_cursor(direction)
        else
          middle=@disp_indices.length/2
          hit=(0...@disp_indices.length).sort_by { |i| (i-middle).abs }.find { |i| BlueLabPointer.hit_sprite?(@sprites['icon_'+i.to_s],point) }
          hit=middle if hit.nil? && BlueLabPointer.hit_sprite?(@sprites['entrytext'],point)
          if hit
            @current_selection=@disp_indices[hit]
            @entry_indices.rotate!(@entry_indices.index(@current_selection)-@entries.length/2)
            calc_display_index;recalc_icon_positions(true);refresh_menu
            BlueLabPointer.emit(Input::USE)
          end
        end
      end
      super
    end
  end
  module Summary
    def pbStartScene(*args)
      super
      button=BitmapSprite.new(126,26,@viewport);button.x=72;button.y=94;button.z=50;button.visible=false
      button.bitmap.fill_rect(0,0,126,26,Color.new(23,61,90));pbSetSmallFont(button.bitmap)
      button.bitmap.font.color=Color.new(239,248,255);button.bitmap.draw_text(0,0,126,26,'Pokédex [P]',1)
      @sprites['blueDexButton']=button
    end
    def pbScene
      @blue_summary_active=true;super
    ensure
      @blue_summary_active=false
    end
    def pbOptions
      @blue_summary_options=true
      unless @pokemon.egg?
        options=UIHandlers.get_info(:summary,@page_id,:options).dup
        UIHandlers.edit_hash(:summary,@page_id,'options',options+[:pokedex]) unless options.include?(:pokedex)
      end
      super
    ensure
      @blue_summary_options=false
    end
    def pbUpdate
      super
      button=@sprites['blueDexButton'];return unless button
      button.visible=!!(@blue_summary_active && !@blue_summary_options && !@inbattle && !@pokemon.egg? && $player.has_pokedex)
      return unless button.visible && !@blue_opening_dex
      clicked=BlueStartMouse.click? && BlueLabPointer.hit_sprite?(button,BlueLabPointer.position)
      return unless clicked || Input.triggerex?(:P)
      BlueLabPointer.claimed=true if clicked
      blue_open_dex
    end
    def blue_open_dex
      return if @pokemon.egg? || @inbattle || !$player.has_pokedex
      @blue_opening_dex=true
      $player.pokedex.register_last_seen(@pokemon)
      pbFadeOutIn do
        scene=PokemonPokedexInfo_Scene.new;screen=PokemonPokedexInfoScreen.new(scene)
        screen.pbStartSceneSingle(@pokemon.species)
      end
      drawPage(@page)
    ensure
      @blue_opening_dex=false;Input.update
    end
  end
  module DexSearch
    def pbStartScene
      super
      @blue_kanto_dex=false
      dex_button=BitmapSprite.new(174,28,@viewport)
      dex_button.x=24;dex_button.y=244;dex_button.z=20
      @sprites['blueKantoDexButton']=dex_button
      blue_refresh_dex_button
      button=BitmapSprite.new(174,28,@viewport);button.x=24;button.y=276;button.z=20
      button.bitmap.fill_rect(0,0,174,28,Color.new(24,62,91));pbSetSmallFont(button.bitmap)
      button.bitmap.font.color=Color.new(239,248,255);button.bitmap.draw_text(0,0,174,28,_INTL('Search / Filters [F]'),1)
      @sprites['blueSearchButton']=button
    end
    def pbUpdate
      super
      dex_button=@sprites['blueKantoDexButton']
      if dex_button
        dex_button.visible=!@blue_search_open && @sprites['pokedex'].active
        if dex_button.visible
          dex_clicked=BlueStartMouse.click? && BlueLabPointer.hit_sprite?(dex_button,BlueLabPointer.position)
          if dex_clicked || Input.triggerex?(:K)
            BlueLabPointer.claimed=true if dex_clicked
            blue_toggle_kanto_dex
            return
          end
        end
      end
      button=@sprites['blueSearchButton'];return unless button
      button.visible=!@blue_search_open && @sprites['pokedex'].active
      return unless button.visible
      clicked=BlueStartMouse.click? && BlueLabPointer.hit_sprite?(button,BlueLabPointer.position)
      return unless clicked || Input.triggerex?(:F)
      BlueLabPointer.claimed=true if clicked
      pbDexSearch
    end
    def blue_refresh_dex_button
      button=@sprites['blueKantoDexButton'];return unless button
      b=button.bitmap;b.clear;b.fill_rect(0,0,174,28,Color.new(24,62,91))
      pbSetSmallFont(b);b.font.color=Color.new(239,248,255)
      b.draw_text(0,0,174,28,_INTL(@blue_kanto_dex ? 'National Dex [K]' : 'KantoDex [K]'),1)
    end
    def blue_kanto_dex_rows(rows)
      return rows unless @blue_kanto_dex
      # Do not use the player's national registration counter as the local
      # index. Kanto is the original 151 species, starting with Bulbasaur.
      rows.select { |row| BlueKantoDex.number(row[:species]) }.map do |row|
        copy=row.dup
        copy[:number]=BlueKantoDex.number(row[:species])
        copy
      end.sort_by { |row| row[:number] }
    end
    def blue_toggle_kanto_dex
      @blue_kanto_dex=!@blue_kanto_dex
      @blue_filters=nil
      if @blue_kanto_dex
        blue_show_kanto_list
      else
        @searchResults=false
        pbRefreshDexList(0)
      end
      blue_refresh_dex_button
    end
    def blue_show_kanto_list
      records=blue_kanto_dex_rows(pbGetDexList)
      if records.empty?
        pbMessage(_INTL('KantoDex unavailable: the base Pokédex has no Kanto species.'))
        @blue_kanto_dex=false
        return
      end
      @dexlist=records
      @searchResults=true
      window=@sprites['pokedex'];window.commands=records;window.index=0;window.refresh
      pbRefresh
    end
    def pbCloseSearch
      @blue_filters=nil;super
    end
    def pbDexSearch
      return super if @blue_advanced_search
      @blue_search_open=true
      BlueDexControls.in_front(self) { BlueDexFilters.menu(self) }
    ensure
      @blue_search_open=false
    end
    def blue_advanced_search
      @blue_advanced_search=true;pbDexSearch
    ensure
      @blue_advanced_search=false;@blue_filters=nil
    end
    def blue_apply_filters(filters)
      if filters==BlueDexFilters.defaults
        @blue_filters=filters
        if @blue_kanto_dex
          blue_show_kanto_list
        else
          @searchResults=false;pbRefreshDexList(0)
        end
        return true
      end
      results=BlueDexFilters.apply(blue_kanto_dex_rows(pbGetDexList),filters)
      if results.empty?;pbMessage(_INTL('No Pokémon match these filters.'));return false;end
      @blue_filters=filters.dup;@dexlist=results;@searchResults=true
      window=@sprites['pokedex'];window.commands=results;window.index=0;window.refresh
      @sprites['background'].setBitmap('Graphics/UI/Pokedex/bg_listsearch');pbRefresh
      true
    end
  end
  def self.install
    return if @installed
    VoltseonsPauseMenu.prepend(PauseMouse);PokemonSummary_Scene.prepend(Summary)
    PokemonPokedex_Scene.prepend(DexSearch);@installed=true
  end
end
module BlueDexFilters
  def self.defaults;{name:'',type:nil,status: :all,sort: :number};end
  def self.normalize(value);value.to_s.downcase.tr('áàâãäéèêëíìîïóòôõöúùûüç','aaaaaeeeeiiiiooooouuuuc').strip;end
  def self.apply(list,filters)
    query=normalize(filters[:name]);type=filters[:type]
    rows=list.select do |row|
      known=$player.seen?(row[:species]) || $player.owned?(row[:species]);owned=$player.owned?(row[:species])
      (filters[:sort]==:number || known) && (filters[:status]!=:seen || known) && (filters[:status]!=:caught || owned) &&
        (query.empty? || (known && normalize(row[:name]).include?(query))) &&
        (!type || (known && row[:types].include?(type)))
    end
    rows.sort_by do |row|
      case filters[:sort]
      when :name then [normalize(row[:name]),row[:number]]
      when :height then [-row[:height],row[:number]]
      when :weight then [-row[:weight],row[:number]]
      else row[:number]
      end
    end
  end
  def self.menu(scene)
    filters=(scene.instance_variable_get(:@blue_filters) || defaults).dup
    loop do
      status={all:_INTL('All entries'),seen:_INTL('Seen only'),caught:_INTL('Caught only')}
      sort={number:_INTL('Dex number'),name:_INTL('Name'),height:_INTL('Tallest first'),weight:_INTL('Heaviest first')}
      labels=[_INTL('Name')+': '+(filters[:name].empty? ? '—' : filters[:name]),_INTL('Type')+': '+(filters[:type] ? GameData::Type.get(filters[:type]).name : _INTL('All')),
        _INTL('Show')+': '+status[filters[:status]],_INTL('Order')+': '+sort[filters[:sort]],_INTL('Apply filters'),_INTL('Clear filters'),_INTL('Advanced search')]
      choice=BlueDexControls.choose(_INTL('Pokédex / Search and filters'),labels)
      case choice
      when 0 then filters[:name]=BlueDexControls.text(filters[:name])
      when 1
        types=[];GameData::Type.each { |t| types << t.id unless t.pseudo_type }
        i=BlueDexControls.choose(_INTL('Type'),[_INTL('All')]+types.map { |id| GameData::Type.get(id).name })
        filters[:type]=i==0 ? nil : types[i-1] if i>=0
      when 2
        i=BlueDexControls.choose(_INTL('Show'),status.values);filters[:status]=status.keys[i] if i>=0
      when 3
        i=BlueDexControls.choose(_INTL('Order'),sort.values);filters[:sort]=sort.keys[i] if i>=0
      when 4 then break if scene.blue_apply_filters(filters)
      when 5 then scene.blue_apply_filters(defaults);break
      when 6 then scene.blue_advanced_search;break
      else break
      end
    end
  end
end
