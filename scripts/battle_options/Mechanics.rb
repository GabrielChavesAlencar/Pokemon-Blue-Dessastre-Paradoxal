# Original adapters around the installed engine's eligibility and fight-menu hooks.
module BlueBattleOptions
  PRIORITY=[:mega,:zmove,:tera,:dynamax].freeze
  MECHANIC_NAMES={mega:'Mega Evolucao',zmove:'Z-Move',tera:'Terastal',dynamax:'Dynamax'}.freeze
  CAN={mega: :pbCanMegaEvolve?,zmove: :pbCanZMove?,tera: :pbCanTerastallize?,dynamax: :pbCanDynamax?}.freeze
  REGISTER={mega: :pbRegisterMegaEvolution,zmove: :pbRegisterZMove,tera: :pbRegisterTerastallize,dynamax: :pbRegisterDynamax}.freeze
  module StoneCompatibility
    def getMegaForm
      found=super
      return found if found>0
      row=BlueBattleOptions::CLASSIC_STONES[item_id]
      return found unless row && row[0]==species
      data=GameData::Species.get_species_form(row[0],row[1])
      return found unless data && data.mega_stone && data.unmega_form==form_simple
      return data.form if [:MEGAITE,:MEGAITEX,:MEGAITEY,:MEGAITEZ].include?(data.mega_stone) || data.mega_stone==item_id
      found
    end
  end
  module AlternativeEligibility
    def hasEligibleAction?(*actions)
      if @blue_alternative_eligibility
        actions=actions.reject { |key| BlueBattleOptions::PRIORITY.include?(key) }
        return false if actions.empty?
      end
      super(*actions)
    end
    def hasTera?(*args)
      before=@blue_alternative_eligibility;@blue_alternative_eligibility=true
      super
    ensure
      @blue_alternative_eligibility=before
    end
    def hasDynamax?(*args)
      before=@blue_alternative_eligibility;@blue_alternative_eligibility=true
      super
    ensure
      @blue_alternative_eligibility=before
    end
    def pbDynamaxAvailable?
      return super unless @battle.instance_variable_get(:@blue_lab_battle)
      return false if $game_switches[Settings::NO_DYNAMAX]
      return false if @battle.dynamax[idxOwnSide][@battle.pbGetOwnerIndexFromBattlerIndex(@index)]==-2
      BlueBattleOptions.allowed?(@battle,'dynamax')
    end
  end
  module MechanicChoice
    def blue_available_mechanics(index)
      battler=@battlers[index]
      return [] unless battler && battler.pokemon && !battler.fainted?
      BlueBattleOptions::PRIORITY.select do |key|
        BlueBattleOptions.allowed?(self,key.to_s) && (public_send(BlueBattleOptions::CAN[key],index) || pbBattleMechanicIsRegistered?(index,key))
      end
    end
    def pbGetEligibleBattleMechanic(index)
      available=blue_available_mechanics(index)
      record=(@blue_mechanic_preferences || {})[index]
      if record && record[0]==@battlers[index].pokemon.object_id && record[1]==turnCount && available.include?(record[2])
        return record[2]
      end
      available.empty? ? super : available.first
    end
    def blue_choose_mechanic(index,key)
      return false unless key.nil? || blue_available_mechanics(index).include?(key)
      pbUnregisterAllSpecialActions(index)
      @battlers[index].display_base_moves
      @blue_mechanic_preferences ||= {}
      chosen=key || blue_available_mechanics(index).first
      @blue_mechanic_preferences[index]=[@battlers[index].pokemon.object_id,turnCount,chosen]
      public_send(BlueBattleOptions::REGISTER[key],index) if key
      true
    end
  end
  module MechanicMenu
    def pbShowWindow(kind)
      super
      @blue_mechanic_button.visible=(kind==Battle::Scene::FIGHT_BOX) if @blue_mechanic_button && !@blue_mechanic_button.disposed?
    end
    def pbFightMenu(index,special=nil,&block)
      @blue_mechanic_index=index
      current=special
      loop do
        @blue_mechanic_current=current
        blue_refresh_mechanic_button
        result=catch(:blue_mechanic_changed) do
          super(index,current,&block)
          :finished
        end
        break if result==:finished
        current=result[0]
      end
    ensure
      @blue_mechanic_button&.dispose;@blue_mechanic_button=nil;@blue_mechanic_index=nil
    end
    def blue_refresh_mechanic_button
      @blue_mechanic_button&.dispose
      @blue_mechanic_button=nil
      return unless @battle.blue_available_mechanics(@blue_mechanic_index).length>1
      @blue_mechanic_button=BitmapSprite.new(194,22,@viewport)
      sprite=@blue_mechanic_button;sprite.x=Graphics.width-202;sprite.y=8;sprite.z=10000
      bitmap=sprite.bitmap;bitmap.fill_rect(0,0,194,22,Color.new(12,28,48,235))
      bitmap.font.name=['Arial','Verdana'];bitmap.font.size=15;bitmap.font.color=Color.new(110,218,255)
      bitmap.draw_text(0,0,194,22,'Mecanicas / F6',1)
    end
    def pbSetSpecialActionModes(index,special,cw)
      super
      if special && @battle.pbBattleMechanicIsRegistered?(index,special)
        cw.mode=1
        pbFightMenu_Action(@battle.battlers[index],special,cw)
        cw.mode=2
      end
    end
    def pbFightMenu_Extra(battler,special,cw)
      super
      return unless @blue_mechanic_button
      clicked=Input.trigger?(Input::MOUSELEFT) && BlueLabPointer.hit_sprite?(@blue_mechanic_button,Mouse.getMousePos)
      return unless Input.triggerex?(:F6) || clicked
      blue_open_mechanic_menu(battler,special,cw)
    end
    def blue_open_mechanic_menu(battler,special,cw)
      available=@battle.blue_available_mechanics(battler.index)
      return if available.length<2
      @blue_mechanic_button.visible=false if @blue_mechanic_button
      labels=available.map { |key| BlueBattleOptions::MECHANIC_NAMES[key]+' / ativar' }
      choice=BlueBattleOptions.choose('Escolher mecanica para '+battler.name,labels+['Nao ativar neste turno','Voltar'],available.index(special) || 0)
      return unless choice>=0 && choice<=available.length
      key=available[choice]
      pbFightMenu_End(battler,special,cw)
      @battle.blue_choose_mechanic(battler.index,key)
      @lastMove[battler.index]=cw.index
      throw :blue_mechanic_changed,[@battle.pbGetEligibleBattleMechanic(battler.index)]
    ensure
      @blue_mechanic_button.visible=true if @blue_mechanic_button && !@blue_mechanic_button.disposed?
      Input.update
    end
  end
  # Drought/Drizzle/etc. gained on Mega Evolution can change the Speed of
  # *other* battlers (Chlorophyll, Swift Swim, Sand Rush, Slush Rush).
  # The Decades/DBK Mega hook only refreshes the Mega battler's cached Speed.
  # Re-sort everyone once weather has actually changed, before moves execute.
  module WeatherPriorityAfterMega
    def pbMegaEvolve(idxBattler)
      weather_before=@field.weather
      result=super
      if @field.weather!=weather_before && @priority && !@priority.empty?
        pbCalculatePriority(false)
      end
      result
    end
  end
  def self.install_mechanic_selector
    Pokemon.prepend(StoneCompatibility) unless Pokemon.ancestors.include?(StoneCompatibility)
    Battle::Battler.prepend(AlternativeEligibility) unless Battle::Battler.ancestors.include?(AlternativeEligibility)
    Battle.prepend(MechanicChoice) unless Battle.ancestors.include?(MechanicChoice)
    Battle.prepend(WeatherPriorityAfterMega) unless Battle.ancestors.include?(WeatherPriorityAfterMega)
    Battle::Scene.prepend(MechanicMenu) unless Battle::Scene.ancestors.include?(MechanicMenu)
  end
end
