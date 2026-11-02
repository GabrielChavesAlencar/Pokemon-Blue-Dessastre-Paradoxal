# Original Blue presentation/input adapters. Run always uses the engine's own command.
module BlueBattleUI
  MISS_SECONDS=1.6
  def self.clock;System.respond_to?(:unscaled_uptime) ? System.unscaled_uptime : System.uptime;end
  def self.duration(value);value.to_i>0 ? ' ('+value.to_s+')' : '';end
  def self.field_rows(battle)
    rows=[];field=battle.field
    if field.weather!=:None
      rows << [_INTL('Weather')+': '+BlueLocale.field_term(GameData::BattleWeather.get(field.weather).name)+duration(field.weatherDuration),:weather]
    end
    if field.terrain!=:None
      rows << [_INTL('Terrain')+': '+BlueLocale.field_term(GameData::BattleTerrain.get(field.terrain).name)+duration(field.terrainDuration),:terrain]
    end
    room=field.effects[PBEffects::TrickRoom]
    rows << ['Trick Room'+duration(room),:room] if room.to_i>0
    2.times do |side|
      turns=battle.sides[side].effects[PBEffects::Tailwind]
      rows << ['Tailwind / '+_INTL(side==0 ? 'Your side' : 'Opponent')+duration(turns),side==0 ? :ally : :foe] if turns.to_i>0
    end
    rows << [_INTL('Field: clear'),:none] if rows.empty?
    rows << ['R: '+_INTL('Run'),:shortcut]
    rows
  end
  module Miss
    def pbMissMessage(*args)
      previous=@battle.instance_variable_get(:@blue_miss_notice)
      @battle.instance_variable_set(:@blue_miss_notice,true)
      super
    ensure
      @battle.instance_variable_set(:@blue_miss_notice,previous)
    end
  end
  module Scene
    def pbDisplayMessage(message,brief=false,&block)
      return super unless @battle && @battle.instance_variable_get(:@blue_miss_notice)
      pbWaitMessage;pbShowWindow(Battle::Scene::MESSAGE_BOX)
      window=@sprites['messageWindow'];window.setText(message)
      PBDebug.log_message(message)
      loop do
        pbUpdate(window)
        break unless window.busy?
        window.skipAhead if Input.trigger?(Input::USE) || Input.trigger?(Input::BACK)
      end
      block.call if block
      # Real time, not the accelerated timeline used by the speed-up plugin.
      until_time=BlueBattleUI.clock+BlueBattleUI::MISS_SECONDS
      pbUpdate(window) while BlueBattleUI.clock<until_time
      window.text='';window.visible=false
    end
    def pbCommandMenu(index,first_action)
      if @blue_run_pending
        @blue_run_pending=false
        @lastCmd[index]=3
        return 3
      end
      @blue_run_scope=:command
      result=catch(:blue_run_shortcut) { super }
      @lastCmd[index]=3 if result==3
      result
    ensure
      @blue_run_scope=nil
    end
    def pbFightMenu(index,special=nil,&block)
      @blue_run_scope=:fight
      interrupted=true
      catch(:blue_run_shortcut) do
        super(index,special,&block)
        interrupted=false
      end
      if interrupted
        @blue_run_pending=true
        window=@sprites['fightWindow']
        pbFightMenu_End(@battle.battlers[index],special,window)
        @lastMove[index]=window.index
      end
    ensure
      @blue_run_scope=nil
    end
    def pbUpdate(*args)
      super
      throw :blue_run_shortcut,3 if @blue_run_scope && Input.triggerex?(:R)
    end
    def pbInitSprites
      super
      sprite=BitmapSprite.new(264,64,@viewport)
      sprite.x=Graphics.width-270;sprite.y=0;sprite.z=299
      sprite.bitmap.font.name=['Arial','Verdana'];sprite.bitmap.font.size=14
      @sprites['blueFieldHUD']=sprite
      @sprites['blueCommandLocale']=BitmapSprite.new(Graphics.width,Graphics.height,@viewport)
      @sprites['blueCommandLocale'].z=350
      @sprites['blueCommandLocale'].visible=false
      @blue_field_rows=nil
      blue_refresh_field_hud
      blue_refresh_command_locale
    end
    def pbGraphicsUpdate
      blue_refresh_field_hud
      blue_refresh_command_locale
      super
    end
    def blue_refresh_field_hud
      sprite=@sprites && @sprites['blueFieldHUD']
      return unless sprite && !sprite.disposed?
      sprite.visible=!(@sprites['enhancedUI'] && @sprites['enhancedUI'].visible)
      rows=BlueBattleUI.field_rows(@battle)
      if @blue_mechanic_button && !@blue_mechanic_button.disposed?
        @blue_mechanic_button.y=((rows.length+1)/2)*18+8
      end
      return if rows==@blue_field_rows
      @blue_field_rows=rows
      bitmap=sprite.bitmap;bitmap.clear
      bitmap.fill_rect(0,0,264,((rows.length+1)/2)*18+4,Color.new(8,20,36,205))
      rows.each_with_index do |(label,kind),i|
        color=case kind
        when :ally then Color.new(100,205,255)
        when :foe then Color.new(255,170,100)
        when :room then Color.new(226,165,255)
        else Color.new(245,248,255)
        end
        bitmap.font.size=12
        measured=bitmap.text_size(label).width
        bitmap.font.size=[(12.0*124/[measured,1].max).floor,12].min.clamp(9,12)
        bitmap.font.color=color;bitmap.draw_text(4+(i%2)*132,2+(i/2)*18,126,18,label)
      end
    end
    def blue_refresh_command_locale
      overlay=@sprites && @sprites['blueCommandLocale'];window=@sprites && @sprites['commandWindow']
      return unless overlay && !overlay.disposed?
      overlay.visible=BlueLocale.enabled? && window && window.visible && @blue_run_scope==:command && !(@sprites['enhancedUI'] && @sprites['enhancedUI'].visible)
      return unless overlay.visible
      labels=window.blue_command_labels || []
      key=[labels,window.index]
      return if key==@blue_command_locale_key
      @blue_command_locale_key=key
      bitmap=overlay.bitmap;bitmap.clear;pbSetSystemFont(bitmap);bitmap.font.size=24
      buttons=window.instance_variable_get(:@buttons) || []
      buttons.each_with_index do |button,i|
        next unless labels[i]
        x,y=button.x,button.y;w=button.src_rect.width;h=button.src_rect.height
        border=i==window.index ? Color.new(160,236,140) : Color.new(96,142,192)
        fill=i==window.index ? Color.new(30,98,72) : Color.new(24,42,70)
        bitmap.fill_rect(x+1,y+1,w-2,h-2,border);bitmap.fill_rect(x+3,y+3,w-6,h-6,fill)
        bitmap.font.color=Color.new(248,252,255);bitmap.draw_text(x+4,y+4,w-8,h-8,labels[i],1)
      end
    end
  end
  def self.clean_evs(pkmn)
    return false if pkmn.egg? || pkmn.ev.values.all? { |v| v==0 }
    pkmn.ev.each_key { |stat| pkmn.ev[stat]=0 }
    pkmn.calc_stats;true
  end
  def self.use_cleaner(pkmn,scene)
    if pkmn.egg? || pkmn.ev.values.all? { |v| v==0 }
      scene.pbDisplay(_INTL('It will not have any effect.'));return false
    end
    return false unless scene.pbConfirm(_INTL('Reset all EVs of {1}?',pkmn.name))
    return false unless clean_evs(pkmn)
    scene.pbRefresh;scene.pbDisplay(_INTL("{1}'s EVs were reset!",pkmn.name));true
  end
  module Icons
    def icon_filename(item)
      return super(:HPUP) if try_get(item)&.id==:BLUEEVCLEANER
      super
    end
  end
  def self.install
    return if @installed
    Battle::Battler.prepend(Miss);Battle::Scene.prepend(Scene)
    GameData::Item.singleton_class.prepend(Icons)
    ItemHandlers::UseOnPokemon.add(:BLUEEVCLEANER,proc { |item,qty,pkmn,scene| BlueBattleUI.use_cleaner(pkmn,scene) })
    @installed=true
  end
end
