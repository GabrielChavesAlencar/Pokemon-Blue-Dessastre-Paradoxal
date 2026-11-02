# Square native cards for the Dex entrance and habitat encounter-method menus.
module BlueDexCards
  def self.home
    {cancel:2,subtitle:_INTL('Choose a section'),icons:[{pause:'menu_pokedex'},{item: :TOWNMAP}]}
  end
  def self.methods(types)
    icons=[{item: :TOWNMAP}]
    types.each do |type|
      item=case type.to_s
      when /OldRod/ then :OLDROD
      when /GoodRod/ then :GOODROD
      when /SuperRod/ then :SUPERROD
      when /Water/ then :MYSTICWATER
      when /RockSmash/ then :HARDSTONE
      when /Headbutt/ then :HONEY
      when /Cave/ then :ESCAPEROPE
      when /Radar/ then :POKERADAR
      else :MIRACLESEED
      end
      icons << {item:item}
    end
    icons << {item: :TOWNMAP}
    {subtitle:_INTL('Encounters and location'),icons:icons}
  end
  class Scene
    attr_reader :index
    def initialize(title,commands,options,default=0,z=99999)
      @title=title;@commands=commands;@options=options;@z=z;@sprites={}
      @indices=(0...commands.length).reject { |i| i==options[:cancel] };@index=@indices.index(default) || 0
      @large=@indices.length<=2;@columns=@large ? 2 : 3;@per_page=@large ? 2 : 6
    end
    def pages;[(@indices.length+@per_page-1)/@per_page,1].max;end
    def page;@index/@per_page;end
    def card_rects
      count=[@per_page,@indices.length-page*@per_page].min
      size=@large ? 192 : 112;gap=@large ? 32 : 40
      left=(Graphics.width-(@columns*size+(@columns-1)*gap))/2
      top=@large ? 92 : 68
      count.times.map { |i| [page*@per_page+i,left+(i%@columns)*(size+gap),top+(i/@columns)*(size+16),size] }
    end
    def start
      @viewport=Viewport.new(0,0,Graphics.width,Graphics.height);@viewport.z=@z
      @sprites['canvas']=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
      refresh;Graphics.transition(0)
    end
    def label_lines(bitmap,label,width)
      lines=['']
      label.split.each do |word|
        text=(lines.last.empty? ? word : lines.last+' '+word)
        if !lines.last.empty? && bitmap.text_size(text).width>width;lines << word;else;lines[-1]=text;end
      end
      lines.first(2)
    end
    def refresh
      @sprites.keys.grep(/^cardIcon/).each { |key| @sprites.delete(key).dispose }
      b=@sprites['canvas'].bitmap;b.clear;b.fill_rect(0,0,Graphics.width,Graphics.height,Color.new(9,24,41));pbSetSmallFont(b)
      light=Color.new(240,248,255);shadow=Color.new(9,24,41)
      pbDrawTextPositions(b,[[@title,16,8,:left,light,shadow],[@options[:subtitle].to_s,16,36,:left,Color.new(157,193,224),shadow],[(page+1).to_s+'/'+pages.to_s,492,36,:right,light,shadow]])
      card_rects.each do |i,x,y,size|
        selected=i==@index
        b.fill_rect(x,y,size,size,selected ? Color.new(121,197,250) : Color.new(42,74,100))
        b.fill_rect(x+2,y+2,size-4,size-4,selected ? Color.new(28,62,91) : Color.new(18,43,64))
        spec=@options[:icons][@indices[i]] || {item: :POKEBALL}
        if spec[:pause]
          icon=IconSprite.new(@viewport);icon.setBitmap(MENU_FILE_PATH+$PokemonSystem.from_current_menu_theme(spec[:pause]))
        else
          item=GameData::Item.exists?(spec[:item]) ? spec[:item] : :POKEBALL
          icon=ItemIconSprite.new(0,0,item,@viewport)
        end
        icon.ox=icon.src_rect.width/2;icon.oy=icon.src_rect.height/2
        image_size=@large ? 80 : 44
        scale=image_size.to_f/[icon.src_rect.width,icon.src_rect.height,1].max
        icon.zoom_x=icon.zoom_y=scale;icon.x=x+size/2;icon.y=y+(@large ? 66 : 34);icon.z=2
        @sprites['cardIcon'+i.to_s]=icon
        b.font.size=@large ? 22 : 18;b.font.color=light
        label_lines(b,@commands[@indices[i]],size-12).each_with_index do |line,row|
          b.draw_text(x+4,y+(@large ? 126 : 68)+row*21,size-8,24,line,1)
        end
      end
      pbSetSmallFont(b);b.font.color=light
      if pages>1
        [[8,156,_INTL('Previous')],[176,156,_INTL('Next')],[344,160,_INTL('Back / Esc')]].each do |x,w,label|
          b.fill_rect(x,338,w,40,Color.new(28,64,94));b.draw_text(x,342,w,32,label,1)
        end
      else
        b.fill_rect(8,338,496,40,Color.new(28,64,94));b.draw_text(8,342,496,32,_INTL('Back / Esc'),1)
      end
    end
    def move(delta);@index=(@index+delta)%@indices.length;refresh;end
    def turn(delta);@index=((page+delta)%pages)*@per_page;refresh;end
    def run
      start
      loop do
        Graphics.update;Input.update;pbUpdateSpriteHash(@sprites)
        return @options[:cancel] || -1 if Input.trigger?(Input::BACK)
        return @indices[@index] if Input.trigger?(Input::USE)
        if Input.repeat?(Input::LEFT);move(-1)
        elsif Input.repeat?(Input::RIGHT);move(1)
        elsif Input.repeat?(Input::UP);move(-@columns)
        elsif Input.repeat?(Input::DOWN);move(@columns)
        elsif Input.trigger?(Input::MOUSELEFT)
          point=BlueLabPointer.position
          card=card_rects.find { |i,x,y,size| BlueLabPointer.inside?(point,x,y,size,size) }
          return @indices[card[0]] if card
          if BlueLabPointer.inside?(point,0,338,Graphics.width,46)
            return @options[:cancel] || -1 if pages==1 || point[0]>=340
            turn(point[0]<170 ? -1 : 1)
          end
        end
      end
    ensure
      pbDisposeSpriteHash(@sprites);@viewport&.dispose
    end
  end
end
module BlueFanBackFacing
  FLIPPED=[:AMMNOID].freeze
  def setPokemonBitmap(pokemon,battler,back=false)
    self.mirror=!self.mirror if @blue_fan_back_flip
    @blue_fan_back_flip=false
    result=super
    if back && !@substitute && pokemon && FLIPPED.include?(pokemon.species)
      self.mirror=!self.mirror;@blue_fan_back_flip=true
    end
    result
  end
end
