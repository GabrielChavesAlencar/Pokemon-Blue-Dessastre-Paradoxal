# Original height/weight comparisons. Measurements come from current species/form data.
class PokemonGlobalMetadata
  attr_accessor :blue_player_height_cm,:blue_player_weight_kg
end
module BlueDexCompare
  PAGES=[:blue_height,:blue_weight].freeze
  def self.height_cm;($PokemonGlobal.blue_player_height_cm || 170).clamp(30,250);end
  def self.weight_kg;($PokemonGlobal.blue_player_weight_kg || 60).clamp(10,500);end
  def self.number(value);format('%.2f',value).sub(/0\z/,'');end
  def self.crop(bitmap,rect,silhouette=false)
    left=rect.width;top=rect.height;right=bottom=-1
    rect.height.times do |y|
      rect.width.times do |x|
        next if bitmap.get_pixel(rect.x+x,rect.y+y).alpha<24
        left=[left,x].min;top=[top,y].min;right=[right,x].max;bottom=[bottom,y].max
      end
    end
    return Bitmap.new(1,1) if right<left
    result=Bitmap.new(right-left+1,bottom-top+1)
    result.blt(0,0,bitmap,Rect.new(rect.x+left,rect.y+top,result.width,result.height))
    if silhouette
      result.height.times do |y|
        result.width.times do |x|
          alpha=result.get_pixel(x,y).alpha
          result.set_pixel(x,y,Color.new(111,168,217,alpha)) if alpha>0
        end
      end
    end
    result
  end
  def self.settings
    loop do
      i=BlueDexControls.choose(_INTL('Player reference'),[_INTL('Height')+': '+height_cm.to_s+' cm',_INTL('Weight')+': '+weight_kg.to_s+' kg',_INTL('Reset to 1.70 m / 60 kg')])
      break if i<0
      if i==2;$PokemonGlobal.blue_player_height_cm=170;$PokemonGlobal.blue_player_weight_kg=60;next;end
      params=ChooseNumberParams.new;params.setRange(i==0 ? 30 : 10,i==0 ? 250 : 500)
      params.setDefaultValue(i==0 ? height_cm : weight_kg);params.setCancelValue(-1)
      n=pbMessageChooseNumber(_INTL(i==0 ? 'Player height in cm' : 'Player weight in kg'),params)
      next if n<0
      i==0 ? $PokemonGlobal.blue_player_height_cm=n : $PokemonGlobal.blue_player_weight_kg=n
    end
  end
  def self.beam_offset(pokemon_kg,phase=1.0)
    return 0 if pokemon_kg<=0
    (Math.log(pokemon_kg/weight_kg.to_f)*16).clamp(-42,42)*phase
  end
  module Entry
    def drawPageIcons
      super
      blue_tab_rects.each do |index,x,y,w,h|
        next unless BlueDexCompare::PAGES.include?(@page_list[index])
        b=@sprites['overlay'].bitmap;b.fill_rect(x,y,w,h,@page-1==index ? Color.new(62,124,172) : Color.new(30,59,83))
        pbSetSmallFont(b);b.font.color=Color.new(244,250,255)
        b.draw_text(x,y,w,h,_INTL(@page_list[index]==:blue_height ? 'Height' : 'Weight'),1);pbSetSystemFont(b)
      end
    end
    def blue_tab_rects
      x,y=PokemonPokedexInfo_Scene::PAGE_ICONS_POSITION;w,h=PokemonPokedexInfo_Scene::PAGE_ICON_SIZE
      max=PokemonPokedexInfo_Scene::MAX_PAGE_ICONS;current=@page_list.index(@page_id) || 0
      start=[current-(max-1),0].max;last=[start+max-1,@page_list.length-1].min;count=[@page_list.length,max].min
      offset=case PokemonPokedexInfo_Scene::PAGE_ICONS_ALIGNMENT
      when :left then 0
      when :right then Graphics.width-x-42-w*count
      else (Graphics.width-x-42)/2-count*(w/2)
      end
      (start..last).map { |i| [i,x+offset+(i-start)*(w+4),y,w,h] }
    end
    def blue_compare_bitmaps
      key=[@species,@form,@gender,$player.trainer_type]
      return if @blue_compare_key==key
      @blue_mon_raster&.dispose;@blue_player_raster&.dispose
      sprite=@sprites['infosprite'];@blue_mon_raster=BlueDexCompare.crop(sprite.bitmap,sprite.src_rect)
      raw=Bitmap.new(GameData::TrainerType.player_front_sprite_filename($player.trainer_type))
      @blue_player_raster=BlueDexCompare.crop(raw,Rect.new(0,0,raw.width,raw.height),true)
      @blue_compare_key=key
    ensure
      raw&.dispose
    end
    def blue_draw_body(bitmap,raster,center,bottom,height)
      width=[(raster.width*height/raster.height).round,1].max;height=[height.round,1].max
      bitmap.stretch_blt(Rect.new((center-width/2).round,(bottom-height).round,width,height),raster,Rect.new(0,0,raster.width,raster.height))
    end
    def blue_draw_comparison(kind,phase=1.0)
      blue_compare_bitmaps
      data=GameData::Species.get_species_form(@species,@form);b=@sprites['overlay'].bitmap
      b.fill_rect(0,32,Graphics.width,Graphics.height-32,Color.new(10,25,42));pbSetSmallFont(b)
      light=Color.new(237,247,255);muted=Color.new(153,193,225);shadow=Color.new(10,25,42)
      pbDrawTextPositions(b,[[_INTL(kind==:blue_height ? 'Height comparison' : 'Weight comparison'),256,42,:center,light,shadow]])
      if kind==:blue_height
        mon_cm=data.height*10.0;human_cm=BlueDexCompare.height_cm.to_f
        if mon_cm>0
          # Both figures share exactly the same pixels-per-centimetre scale.
          scale=[190.0/[mon_cm,human_cm].max,210.0/(@blue_mon_raster.width.to_f/@blue_mon_raster.height*mon_cm),210.0/(@blue_player_raster.width.to_f/@blue_player_raster.height*human_cm)].min
          b.fill_rect(24,282,464,2,Color.new(85,120,151))
          blue_draw_body(b,@blue_mon_raster,136,280,mon_cm*scale)
          blue_draw_body(b,@blue_player_raster,376,280,human_cm*scale)
          @blue_height_pixels=[mon_cm*scale,human_cm*scale]
        else
          blue_draw_body(b,@blue_player_raster,376,280,160)
          pbDrawTextPositions(b,[['?',136,170,:center,light,shadow]])
          @blue_height_pixels=nil
        end
        values=[data.height>0 ? BlueDexCompare.number(data.height/10.0)+' m' : '?',BlueDexCompare.number(human_cm/100.0)+' m']
      else
        offset=BlueDexCompare.beam_offset(data.weight/10.0,phase);@blue_beam_offset=offset
        left=224-offset;right=224+offset
        if data.weight>0
          288.times do |i|;y=left+(right-left)*i/287.0;b.fill_rect(112+i,y.round,3,4,Color.new(174,198,218));end
          54.times { |i| b.fill_rect(256-i/2,228+i,i+1,1,Color.new(61,96,125)) }
          b.fill_rect(88,left.round+8,64,4,Color.new(118,159,191));b.fill_rect(368,right.round+8,64,4,Color.new(118,159,191))
        else
          pbDrawTextPositions(b,[['?',256,190,:center,light,shadow]])
        end
        blue_draw_body(b,@blue_player_raster,120,left+6,110)
        h=[110.0,160.0*@blue_mon_raster.height/@blue_mon_raster.width].min
        blue_draw_body(b,@blue_mon_raster,400,right+6,h)
        values=[data.weight>0 ? BlueDexCompare.number(data.weight/10.0)+' kg' : '?',BlueDexCompare.number(BlueDexCompare.weight_kg)+' kg']
      end
      centers=kind==:blue_height ? [136,376] : [400,120]
      [data.name,_INTL('Player')].each_with_index do |name,i|
        pbDrawTextPositions(b,[[name,centers[i],292,:center,light,shadow],[values[i],centers[i],316,:center,muted,shadow]])
      end
      [[8,100,_INTL('Previous')],[112,174,_INTL('Player reference')],[290,100,_INTL('Next')],[394,110,_INTL('Back')]].each do |x,w,label|
        b.fill_rect(x,352,w,28,Color.new(28,64,94));b.draw_text(x,352,w,28,label,1)
      end
    end
    def draw_blue_height;@blue_weight_started=nil;blue_draw_comparison(:blue_height);end
    def draw_blue_weight;@blue_weight_started=BlueBattleUI.clock;blue_draw_comparison(:blue_weight,0.0);end
    def pbUpdate
      super
      custom=BlueDexCompare::PAGES.include?(@page_id)
      if @page_id==:blue_weight && @blue_weight_started
        elapsed=BlueBattleUI.clock-@blue_weight_started
        blue_draw_comparison(:blue_weight,[elapsed/0.6,1.0].min)
        @blue_weight_started=nil if elapsed>=0.6
      end
      return if @blue_comparison_modal || @brief
      if BlueStartMouse.click?
        point=BlueLabPointer.position
        tab=blue_tab_rects.find { |i,x,y,w,h| BlueLabPointer.inside?(point,x,y,w,h) }
        if tab
          BlueLabPointer.claimed=true;@page=tab[0]+1;drawPage(@page);return
        end
        return unless custom && point[1]>=352
        BlueLabPointer.claimed=true
        if point[0]<108;blue_change_page(-1)
        elsif point[0]<286;blue_reference_settings
        elsif point[0]<394;blue_change_page(1)
        else BlueLabPointer.emit(Input::BACK)
        end
      end
    end
    def blue_change_page(delta);@page=(@page-1+delta)%@page_list.length+1;drawPage(@page);end
    def blue_reference_settings
      @blue_comparison_modal=true
      BlueDexControls.in_front(self) { BlueDexCompare.settings }
      drawPage(@page)
    ensure
      @blue_comparison_modal=false
    end
    def pbPageCustomUse(page_id)
      unless BlueDexCompare::PAGES.include?(page_id)
        previous=@blue_comparison_modal;@blue_comparison_modal=true
        begin;return super;ensure;@blue_comparison_modal=previous;end
      end
      blue_reference_settings;true
    end
    def pbChooseForm(*args)
      previous=@blue_comparison_modal;@blue_comparison_modal=true;super
    ensure
      @blue_comparison_modal=previous
    end
    def pbEndScene
      super
    ensure
      @blue_mon_raster&.dispose;@blue_player_raster&.dispose
      @blue_mon_raster=@blue_player_raster=nil;@blue_compare_key=nil
    end
  end
  def self.install
    return if @installed
    PokemonPokedexInfo_Scene.prepend(Entry)
    UIHandlers.add(:pokedex,:blue_height,{'name'=>'HEIGHT','suffix'=>'info','order'=>60,'layout'=>proc { |species,scene| scene.draw_blue_height }})
    UIHandlers.add(:pokedex,:blue_weight,{'name'=>'WEIGHT','suffix'=>'info','order'=>70,'layout'=>proc { |species,scene| scene.draw_blue_weight }})
    @installed=true
  end
end
