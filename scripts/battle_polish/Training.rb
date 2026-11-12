# Paid, single-stat cleaners and the party's native level-up move reminder.
module BlueTraining
  CLEANERS={BLUEEVHP: :HP,BLUEEVATTACK: :ATTACK,BLUEEVDEFENSE: :DEFENSE,
    BLUEEVSPATK: :SPECIAL_ATTACK,BLUEEVSPDEF: :SPECIAL_DEFENSE,BLUEEVSPEED: :SPEED}.freeze
  ICONS={HP: :HPUP,ATTACK: :PROTEIN,DEFENSE: :IRON,SPECIAL_ATTACK: :CALCIUM,SPECIAL_DEFENSE: :ZINC,SPEED: :CARBOS}.freeze
  LABELS=['Beginner','Intermediate','Advanced','Master'].freeze
  def self.difficulty;_INTL(LABELS[BlueStory.stage]);end
  def self.clean(pokemon,stat)
    return false unless CLEANERS.value?(stat) && !pokemon.egg? && pokemon.ev[stat]>0
    pokemon.ev[stat]=0;pokemon.calc_stats;true
  end
  def self.use(item,pokemon,scene)
    stat=CLEANERS.fetch(item)
    if pokemon.egg? || pokemon.ev[stat]==0
      scene.pbDisplay(_INTL('It will not have any effect.'));return false
    end
    return false unless scene.pbConfirm(_INTL('Reset {1} EVs of {2}?',GameData::Stat.get(stat).name,pokemon.name))
    return false unless clean(pokemon,stat)
    scene.pbRefresh;scene.pbDisplay(_INTL("{1}'s EVs were reset!",pokemon.name));true
  end
  def self.moves(pokemon)
    return [] unless pokemon && !pokemon.egg? && !pokemon.shadowPokemon?
    learned=pokemon.getMoveList.select { |level,id| level<=pokemon.level }.map(&:last)
    (learned+Array(pokemon.first_moves)).uniq.select { |id| GameData::Move.exists?(id) && !pokemon.hasMove?(id) }
  end
  class Reminder < MoveRelearnerScreen
    def pbGetRelearnableMoves(pokemon);BlueTraining.moves(pokemon);end
  end
  def self.remember(screen,party,index)
    pokemon=party[index]
    if moves(pokemon).empty?
      screen.pbDisplay(_INTL('No forgotten moves are available at this level.'));return
    end
    pbFadeOutIn { Reminder.new(MoveRelearner_Scene.new).pbStartScreen(pokemon) }
    screen.pbRefresh
  end
  module Icons
    def icon_filename(item)
      data=try_get(item);stat=data && BlueTraining::CLEANERS[data.id]
      return super(BlueTraining::ICONS[stat]) if stat
      super
    end
  end
  module Card
    def pbDrawTrainerCardFront
      super
      @sprites['blueDifficulty'] ||= BitmapSprite.new(Graphics.width-16,28,@viewport)
      panel=@sprites['blueDifficulty'];panel.x=8;panel.y=350;panel.z=10
      b=panel.bitmap;b.clear;b.fill_rect(0,0,b.width,b.height,Color.new(15,43,66));pbSetSmallFont(b)
      pbDrawTextPositions(b,[[_INTL('Difficulty')+': '+BlueTraining.difficulty,10,0,:left,Color.new(240,248,255),Color.new(15,43,66)],
        [_INTL('{1} esmeraldas',BlueRegions.crystal_total(BlueRegions.snapshot || BlueRegions.new_state, $player.badge_count)),b.width-10,0,:right,Color.new(161,210,243),Color.new(15,43,66)]])
    end
  end
  def self.install
    return if @installed
    CLEANERS.each_key { |id| ItemHandlers::UseOnPokemon.add(id,proc { |item,qty,pkmn,scene| BlueTraining.use(item,pkmn,scene) }) }
    GameData::Item.singleton_class.prepend(Icons);PokemonTrainerCard_Scene.prepend(Card)
    MenuHandlers.add(:party_menu,:blue_remember,{
      'name'=>_INTL('Remember moves'),'order'=>22,
      'condition'=>proc { |screen,party,index| pokemon=party[index];pokemon && !pokemon.egg? && !pokemon.shadowPokemon? && !($game_temp && $game_temp.in_battle) },
      'effect'=>proc { |screen,party,index| BlueTraining.remember(screen,party,index) }
    })
    @installed=true
  end
end
