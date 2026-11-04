# Mouse adapters use the native confirmation/entry paths; no game-wide click-to-Enter.
module BlueStartMouse
  def self.with_scope(value)
    previous=@scope;@scope=value;yield
  ensure
    @scope=previous
  end
  def self.scope;@scope;end
  def self.click?
    BlueLabPointer.enabled? && !BlueLabPointer.claimed && Input.trigger?(Input::MOUSELEFT) &&
      BlueLabPointer.inside?(BlueLabPointer.position,0,0,Graphics.width,Graphics.height)
  end
  module InputKeys
    def trigger?(key)
      if key==Input::USE && [:title,:stats,:controls,:fishing].include?(BlueStartMouse.scope) && BlueStartMouse.click?
        BlueLabPointer.claimed=true;return true
      end
      super
    end
    def triggerex?(key)
      scope=BlueStartMouse.scope
      if key==:RETURN && scope.is_a?(Array) && scope[0]==:keyboard && scope[1].blue_confirm_click?
        BlueLabPointer.claimed=true;return true
      end
      super
    end
  end
  module Title
    def main;BlueStartMouse.with_scope(:title) { super };end
    def update;BlueStartMouse.with_scope(:title) { super };end
    def closeTitle;BlueStartMouse.with_scope(nil) { super };end
    def closeTitleDelete;BlueStartMouse.with_scope(nil) { super };end
  end
  module Load
    def pbUpdate
      super
      return unless BlueStartMouse.click?
      point=BlueLabPointer.position
      @commands.each_index do |i|
        panel=@sprites['panel'+i.to_s];next unless panel && panel.visible
        x,y=BlueLabPointer.origin(panel);height=panel.instance_variable_get(:@isContinue) ? 222 : 46
        next unless BlueLabPointer.inside?(point,x,y,panel.bitmap.width,height)
        @sprites['cmdwindow'].index=i
        @commands.each_index { |j| @sprites['panel'+j.to_s].selected=j==i }
        BlueLabPointer.emit(Input::USE);break
      end
    end
  end
  module NamingGrid
    def pbUpdate
      super
      return unless @sprites['cursor'] && @sprites['cursor'].visible
      return unless BlueStartMouse.click?
      point=BlueLabPointer.position;x,y=point
      target=nil
      if y>=120 && y<158
        [[44,60,PokemonEntryScene2::MODE1],[106,60,PokemonEntryScene2::MODE2],
         [168,60,PokemonEntryScene2::MODE3],[230,60,PokemonEntryScene2::MODE4],
         [314,80,PokemonEntryScene2::BACK],[394,80,PokemonEntryScene2::OK]].each do |left,width,value|
          target=value if x>=left && x<left+width
        end
      elsif x>=52 && x<52+32*PokemonEntryScene2::ROWS && y>=180 && y<180+38*PokemonEntryScene2::COLUMNS
        target=((y-180)/38).floor*PokemonEntryScene2::ROWS+((x-52)/32).floor
      end
      return if target.nil?
      @cursorpos=target;@sprites['cursor'].setCursorPos(target);BlueLabPointer.emit(Input::USE)
    end
  end
  module NamingKeyboard
    def pbStartScene(*args)
      super
      button=BitmapSprite.new(144,40,@viewport);button.x=Graphics.width-162;button.y=Graphics.height-144
      button.z=20;button.bitmap.fill_rect(0,0,144,40,Color.new(20,60,88));pbSetSmallFont(button.bitmap)
      button.bitmap.font.color=Color.new(240,249,255);button.bitmap.draw_text(0,0,144,40,_INTL('Confirm name'),1)
      @sprites['blueConfirmName']=button
    end
    def blue_confirm_click?
      BlueStartMouse.click? && BlueLabPointer.hit_sprite?(@sprites['blueConfirmName'],BlueLabPointer.position)
    end
    def pbEntry1;BlueStartMouse.with_scope([:keyboard,self]) { super };end
  end
  module Modals
    def pbTopRightWindow(*args);BlueStartMouse.with_scope(:stats) { super };end
  end
  module Selection
    def pbStartScene(pokemonlist,settings={})
      @blue_monotype_pick=settings[:blue_monotype_pick]
      super
    end
    def drawPage
      # RGSS/JoiPlay Bitmap lacks mkxp's clear_rect. A transparent fill also
      # replaces the old header pixels without clearing the rest of the overlay.
      result=super;bitmap=@sprites['overlay'].bitmap;bitmap.fill_rect(294,74,218,26,Color.new(0,0,0,0))
      text=@blue_monotype_pick ? _INTL('Starter {1}/2 · {2} options',@blue_monotype_pick,@pokemonlist.length) : _INTL('Options: {1}',@pokemonlist.length)
      pbSetSmallFont(bitmap);pbDrawTextPositions(bitmap,[[text,298,78,:left,Color.new(248,248,248),Color.new(104,104,104)]]);pbSetSystemFont(bitmap)
      result
    end
    def pbUpdate
      super
      return unless BlueStartMouse.click?
      point=BlueLabPointer.position
      if BlueLabPointer.hit_sprite?(@sprites['leftarrow'],point) || BlueLabPointer.hit_sprite?(@sprites['rightarrow'],point)
        direction=BlueLabPointer.hit_sprite?(@sprites['leftarrow'],point) ? -1 : 1
        @index=(@index+direction)%@pokemonlist.length;@pokemon=@pokemonlist[@index]
        BlueLabPointer.claimed=true;updateMenuBar(true);drawPage;return
      end
      @pokemonlist.each_index do |i|
        next unless BlueLabPointer.hit_sprite?(@sprites['pkmnicon'+i.to_s],point)
        if i==@index;BlueLabPointer.emit(Input::USE)
        else
          @index=i;@pokemon=@pokemonlist[i];BlueLabPointer.claimed=true;updateMenuBar;drawPage
        end
        return
      end
      BlueLabPointer.emit(Input::USE) if BlueLabPointer.hit_sprite?(@sprites['pokemon'],point)
    end
  end
  def self.install
    return if @installed
    Input.singleton_class.prepend(InputKeys);Scene_Intro.prepend(Title);PokemonLoad_Scene.prepend(Load)
    PokemonEntryScene2.prepend(NamingGrid);PokemonEntryScene.prepend(NamingKeyboard)
    Object.prepend(Modals);ModularSelection_Scene.prepend(Selection)
    MenuHandlers.each(:options_menu) do |id,hash|
      next unless id==:only_speedup_battles
      hash['name']='Delta Speed Up'
      hash['description']='Use Delta Speed Up at 1x or 3x.'
    end
    @installed=true
  end
end
