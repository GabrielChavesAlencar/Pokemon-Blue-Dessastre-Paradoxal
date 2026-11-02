# Native campaign choices and boxes. Original map files and saves are not rewritten.
module BlueAdventure
  def self.battle_save?
    return false unless $PokemonGlobal
    $PokemonGlobal.blue_story_mode==:battle || ($game_switches && $game_switches[62] && !BlueStory.story?)
  end
  def self.select(result,keep,aliases={})
    labels,cancel,mapping=result
    indices=labels.each_index.select { |i| keep.call(labels[i]) }
    return result if indices.length==labels.length && aliases.empty?
    return [['Cancel'],1,[-999]] if indices.empty?
    shown=indices.map { |i| aliases.fetch(labels[i],labels[i]) }
    branches=indices.map { |i| mapping[i] }
    exit_index=shown.index { |s| ['Cancel','No'].include?(s) }
    if cancel.to_i>0 && !indices.include?(cancel-1) && !exit_index
      shown << 'Cancel';branches << -999;exit_index=shown.length-1
    end
    next_cancel=exit_index ? exit_index+1 : (cancel.to_i>0 ? indices.index(cancel-1).to_i+1 : 0)
    [shown,next_cancel,branches]
  end
  def self.filter(result)
    labels=result[0]
    return select(result,proc { |s| !['Begin Story Mode','Story Mode'].include?(s) }) if battle_save?
    return result unless BlueStory.story?
    if labels.include?('Yes (Metagame Wiki Dex)')
      return select(result,proc { |s| s=='Yes (Metagame Wiki Dex)' })
    end
    if labels.include?('Traditional Starters')
      return select(result,proc { |s| ['Traditional Starters','Any Pokémon','Monotype Starters','Cancel'].include?(s) },{'Any Pokémon'=>'Monotype Starters'})
    end
    if labels.include?('Monotype Starters') && labels.any? { |s| s.include?('Starters (') }
      normal=labels.find { |s| s.start_with?('All Starters') }
      return select(result,proc { |s| [normal,'Monotype Starters','Cancel'].include?(s) },{normal=>'Traditional Starters'})
    end
    if labels.any? { |s| s.match?(/\AMono \w+ Types?\z/) }
      return select(result,proc { |s| s.match?(/\AMono \w+ Types?\z/) || s=='Cancel' })
    end
    result
  end
  def self.monotype_pool(type)
    type=type.to_s.upcase.to_sym;list=[]
    GameData::Species.each do |s|
      next unless s.types.include?(type) && s.base_stats.values.all? { |v| v>0 } && BlueStory.bst(s)<=350
      next if s.form>0 && !s.is_regional_form?
      next if (s.flags & ['Legendary','Mythical','UltraBeast','Paradox','Pending']).any?
      list << s.id
    end
    list.sort_by { |id| data=GameData::Species.get(id);[data.name,data.form] }
  end
  def self.choose_monotype_starters
    types=[];GameData::Type.each { |type| types << type.id unless type.pseudo_type || type.id==:STELLAR }
    choice=BlueBattleLab.choose(_INTL('Choose the type for your two starters.'),types.map { |id| GameData::Type.get(id).name })
    return false unless choice>=0 && choice<types.length
    pool=monotype_pool(types[choice]);raise 'Empty monotype starter pool' if pool.empty?
    selected=2.times.map { |i| pbPokemonSelection(pool,true,PokemonSelections::STARTER.merge(blue_monotype_pick:i+1)) }
    return false unless selected.all? { |p| p && pool.include?(p.species_data.id) && p.species_data.base_stats.values.sum<=350 }
    selected.each { |p| pbAddPokemonSilent(p) }
    $PokemonGlobal.blue_traditional_starters=true
    true
  end
  module Choices
    def setup_choices(params);BlueAdventure.filter(BlueLocale.with_raw { super });end
    def command_101
      if @map_id==1 && @parameters[0].to_s.include?('What do you think about Emulator Speed Up/Delta Speed Up?')
        # The base's quiz can send the player into a punitive joke encounter.
        # Delta is the installed accelerator; skip the quiz's outer choice block.
        choice=@list[@index+1]
        if choice&.code==102
          finish=(@index+2...@list.length).find { |i| @list[i].code==404 && @list[i].indent==choice.indent }
          if finish
            $game_switches[90]=false;$CanToggle=true
            @index=finish;return true
          end
        end
      end
      # Bypass the new-game soundtrack question, keeping its intended BGM branch.
      if @map_id==1 && @list[@index+1]&.code==102 && @list[@index+1].parameters[0].include?('Intended Soundtrack')
        choice=@list[@index+1];indent=choice.indent
        finish=(@index+2...@list.length).find { |i| @list[i].code==404 && @list[i].indent==indent }
        if finish
          wanted=choice.parameters[0].index('Intended Soundtrack')
          branch=(@index+2...finish).find { |i| @list[i].code==402 && @list[i].indent==indent && @list[i].parameters[0]==wanted }
          if branch
            @branch[indent]=wanted;$game_switches[100]=false;@index=branch-1;return true
          end
        end
      end
      super
    end
    def command_402
      chosen=@branch[@list[@index].indent]==@parameters[0];label=@parameters[1]
      return command_skip if chosen && BlueAdventure.battle_save? && ['Story Mode','Begin Story Mode'].include?(label)
      if chosen && BlueStory.story? && @map_id==1 && ['Any Pokémon','Monotype Starters'].include?(label)
        if BlueAdventure.choose_monotype_starters
          return command_skip
        end
        # Back returns to the actual root choice, rather than starting with no team.
        root=(0...@index).to_a.reverse.find { |i| @list[i].code==102 && @list[i].parameters[0].include?('Traditional Starters') }
        @index=root-2 if root
        return true
      end
      result=super
      if chosen && BlueStory.story? && (['Any Pokémon','Monotype Starters','Traditional Starters'].include?(label) || label.start_with?('All Starters'))
        $PokemonGlobal.blue_traditional_starters=true
      end
      result
    end
  end
  module ModeGuard
    def choose_mode(mode);return false if mode==:story && BlueAdventure.battle_save?;super;end
  end
  module Selection
    def pbStoryModeSetup;return false if BlueAdventure.battle_save?;super;end
    def pbPokemonSelection(list,must_choose=true,settings=nil)
      list=:Traditional_Starters if BlueCampaign.active? && list==:All_Starters
      if BlueCampaign.active? && list.to_s.match?(/\A(?:Final_)?Mono_/i)
        type=list.to_s.sub(/\A(?:Final_)?Mono_/i,'');pool=BlueAdventure.monotype_pool(type)
        raise 'No legal monotype starter: '+type if pool.empty?
        return super(pool,must_choose,settings)
      end
      super
    end
  end
  module Theme
    def from_current_menu_theme(data,default=nil)
      return super('menu_party',nil) if data=='menu_blue_pc'
      super
    end
  end
  module StoryDexes
    def accessible_dexes
      return [0] if BlueStory.story? && unlocked?(0)
      super
    end
  end
  def self.pc_available?
    $player && $PokemonStorage && $game_temp && !$game_temp.in_battle &&
      !(defined?(BlueBattleLab) && BlueBattleLab::ACTIVE) && !pbInSafari? && !pbInBugContest?
  end
  def self.open_pc
    return false unless pc_available?
    pbFadeOutIn do
      scene=PokemonStorageScene.new;screen=PokemonStorageScreen.new(scene,$PokemonStorage);screen.pbStartScreen(0)
    end
    true
  end
  def self.install
    return if @installed
    Interpreter.prepend(Choices);Object.prepend(Selection);BlueStory.singleton_class.prepend(ModeGuard);PokemonSystem.prepend(Theme)
    Player::Pokedex.prepend(StoryDexes)
    MenuHandlers.add(:pause_menu,:blue_pc,{
      'name'=>'PC / Pokémon Boxes','order'=>25,'condition'=>proc { |menu| BlueAdventure.pc_available? },
      'effect'=>proc do |menu|
        menu.pbHideMenu if menu.respond_to?(:pbHideMenu)
        BlueAdventure.open_pc
        menu.pbShowMenu if menu.respond_to?(:pbShowMenu)
        menu.pbRefresh;false
      end
    })
    @installed=true
  end
end
