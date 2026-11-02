# Original adapters for the installed help/character screens and fishing handler.
module BlueExploration
  def self.encounter_types(types)
    copy=types.transform_values { |slots| slots.map(&:dup) }
    fishing=[:SuperRod,:GoodRod,:OldRod].filter_map { |type| copy[type] }.find { |slots| !slots.empty? }
    if fishing
      [:OldRod,:GoodRod,:SuperRod].each { |type| copy[type]=fishing.map(&:dup) if !copy[type] || copy[type].empty? }
    end
    copy
  end
  module Encounters
    def setup(map_id)
      super
      @encounter_tables=BlueExploration.encounter_types(@encounter_tables)
    end
  end
  module Controls
    def update;BlueStartMouse.with_scope(:controls) { super };end
  end
  module Characters
    def pbMidScene
      @blue_selecting_character=true;super
    ensure
      @blue_selecting_character=false
    end
    def pbDisplayConfirm(*args)
      previous=@blue_selecting_character;@blue_selecting_character=false;super
    ensure
      @blue_selecting_character=previous
    end
    def update
      super
      return unless @blue_selecting_character && BlueStartMouse.click?
      point=BlueLabPointer.position
      @overworld.each_index do |i|
        next unless BlueLabPointer.hit_sprite?(@sprites['icon'+i.to_s],point)
        updateCursor(i);BlueLabPointer.emit(Input::USE);return
      end
      BlueLabPointer.emit(Input::USE) if BlueLabPointer.hit_sprite?(@sprites['battler'],point)
    end
  end
  module Fishing
    def pbFishing(has_encounter,rod_type=1)
      $stats.fishing_count+=1
      window=nil;finished=false
      pbFishingBegin
      window=pbCreateMessageWindow
      # The installed base already guarantees a bite when this rod has a table.
      # Its manual-hook path never returned success, even after a valid input.
      pbWaitMessage(window,rand(5..10))
      unless has_encounter
        pbFishingEnd { pbMessageDisplay(window,_INTL('Not even a nibble...')) };finished=true
        return false
      end
      $scene.spriteset.addUserAnimation(Settings::EXCLAMATION_ANIMATION_ID,$game_player.x,$game_player.y,true,3)
      hooked=BlueStartMouse.with_scope(:fishing) { pbWaitForInput(window,_INTL('Oh! A bite!'),rand(5..10)/10.0) }
      pbFishingEnd do
        pbMessageDisplay(window,_INTL(hooked ? 'Landed a Pokémon!' : 'The Pokémon got away...'))
      end
      finished=true;hooked
    ensure
      pbFishingEnd if $PokemonGlobal.fishing && !finished
      pbDisposeMessageWindow(window) if window
    end
  end
  def self.install
    return if @installed
    ButtonEventScene.prepend(Controls);CharacterSelectionScene.prepend(Characters)
    Object.prepend(Fishing);PokemonPokedexScreen.prepend(BlueHabitat::DexMenu);PokemonEncounters.prepend(Encounters)
    @installed=true
  end
end
