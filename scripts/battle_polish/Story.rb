# Runtime-only opponent teams. Original PBS, event flags and player Pokemon stay intact.
class PokemonGlobalMetadata
  attr_accessor :blue_story_mode,:blue_traditional_starters,:blue_story_wins
end
module BlueStory
  LABELS=['Inicial','Intermediario','Avancado','Master'].freeze
  def self.story?
    return false unless $PokemonGlobal
    return $PokemonGlobal.blue_story_mode==:story if $PokemonGlobal.blue_story_mode
    $game_switches && $game_switches[76] && !$game_switches[62]
  end
  def self.enabled?
    story? && $PokemonGlobal.blue_traditional_starters==true &&
      !(defined?(BlueBattleLab) && BlueBattleLab::ACTIVE) && !BlueBattleOptions.battle_area?
  end
  def self.stage(badges=$player.badge_count);badges>=11 ? 3 : (badges>=5 ? 2 : (badges>=2 ? 1 : 0));end
  def self.cap;[350,450,540,nil][stage];end
  def self.bst(data);data.base_stats.values.sum;end
  def self.choose_mode(mode)
    $PokemonGlobal.blue_story_mode=mode
    $PokemonGlobal.blue_traditional_starters=false
  end
  # Keep the interpreter's branch mapping; only change the displayed order.
  module Choices
    def setup_choices(params)
      result=super
      original=params[0].index('Traditional Starters')
      if original
        pos=result[2].index(original)
        if pos
          order=(0...result[0].length).to_a;order.delete(pos);order.unshift(pos)
          cancel=result[1]
          result[0]=order.map { |i| result[0][i] }
          result[2]=order.map { |i| result[2][i] }
          result[1]=order.index(cancel-1)+1 if cancel && cancel>0 && order.include?(cancel-1)
        end
      end
      result
    end
    def command_402
      if @branch[@list[@index].indent]==@parameters[0]
        label=@parameters[1]
        if label=='Story Mode'
          BlueStory.choose_mode(:story)
          BlueCampaign.begin_journey unless defined?(BlueBattleLab) && BlueBattleLab::ACTIVE
        end
        BlueStory.choose_mode(:battle) if label=='Battle Mode'
        $PokemonGlobal.blue_traditional_starters=true if label=='Traditional Starters' && BlueStory.story?
        $PokemonGlobal.blue_traditional_starters=false if ['VGC Starters','Any Pokémon'].include?(label) && BlueStory.story?
      end
      super
    end
  end
  def self.pool(limit)
    @pools ||= {}
    @pools[limit] ||= begin
      list=[]
      GameData::Species.each do |s|
        next unless s.form==0 && bst(s)>0 && bst(s)<=limit
        next if (s.flags & ['Legendary','Mythical','UltraBeast','Paradox']).any?
        list << s
      end
      list
    end
  end
  def self.replacement(source,limit)
    return source if bst(source)<=limit
    @replacements ||= {}
    @replacements[[source.id,limit]] ||= begin
      @families ||= {}
      family=(@families[source.species] ||= source.get_baby_species)
      target=[limit,bst(source)*limit/600.0].min
      pool(limit).min_by do |s|
        baby=(@families[s.species] ||= s.get_baby_species)
        [baby==family ? 0 : 1,s.types==source.types ? 0 : 1,
         s.types.first==source.types.first ? 0 : 1,-(s.types & source.types).length,
         (bst(s)-target).abs,s.id.to_s]
      end || raise('No legal Story replacement for '+source.id.to_s)
    end
  end
  def self.adjust(pkmn,limit)
    source=pkmn.species_data;selected=replacement(source,limit)
    copy=Marshal.load(Marshal.dump(pkmn))
    return copy if selected.id==source.id
    copy.species=selected.species;copy.form=selected.form
    copy.level=pkmn.level  # Different growth curves must not change the scaled level.
    copy.name='' unless pkmn.nicknamed?
    copy.ability=nil;copy.ability_index=0
    copy.item=nil if copy.item && copy.item.is_mega_stone?
    copy.moves=pkmn.moves.map(&:clone)
    legal=(selected.moves.select { |level,id| level<=copy.level }.map(&:last)+selected.tutor_moves+selected.egg_moves).uniq
    previous=copy.moves.map(&:id).select { |id| legal.include?(id) }
    copy.reset_moves
    copy.moves=(previous+copy.moves.map(&:id)).uniq.first(4).map { |id| Pokemon::Move.new(id) }
    copy.calc_stats;copy.heal
    copy
  end
  module Teams
    def initialize(*args)
      @blue_story_cap=BlueStory.cap if BlueStory.enabled?
      if BlueStory.enabled? && args[4] && !Array(args[4]).empty?
        trainers=Array(args[4])
        if BlueStory.context
          BlueStory.context[:foes]=trainers.map { |t| [t.trainer_type,t.name,t.version || 0] }
        end
        if @blue_story_cap
          trainers=trainers.map do |t|
            copy=t.clone
            copy.party=t.party.map { |p| BlueStory.adjust(p,@blue_story_cap) }
            copy
          end
          args[4]=trainers;args[2]=trainers.flat_map(&:party)
        end
      end
      super(*args)
    end
    def pbCanMegaEvolve?(index)
      return false if blue_story_forbidden_mega?(index)
      super
    end
    def blue_story_forbidden_mega?(index)
      b=@battlers[index]
      if @blue_story_cap && b && b.opposes? && b.pokemon.hasMegaForm?
        form=b.pokemon.getMegaForm
        return BlueStory.bst(GameData::Species.get_species_form(b.species,form))>@blue_story_cap
      end
      false
    end
    def pbMegaEvolve(index)
      return if blue_story_forbidden_mega?(index)
      super
    end
    def pbPrimalReversion(index)
      return if @blue_story_cap && @battlers[index]&.opposes?
      super
    end
  end
  module Forms
    def pbChangeForm(form,*args)
      return if blue_story_forbidden_form?(form)
      super
    end
    def pbSimpleFormChange(form,*args)
      return if blue_story_forbidden_form?(form)
      super
    end
    def blue_story_forbidden_form?(form)
      limit=@battle.instance_variable_get(:@blue_story_cap)
      limit && opposes? && BlueStory.bst(GameData::Species.get_species_form(species,form))>limit
    end
  end
  def self.context;@context;end
  def self.replaying?;!!@replaying;end
  def self.history;$PokemonGlobal.blue_story_wins ||= {};end
  def self.record(context,outcome)
    return unless outcome==1 && context && context[:foes] && !context[:foes].empty?
    # Group a battle by its full trainer identity, including variants and doubles.
    key=context[:foes].map { |r| r.join('|') }.join(' / ')
    row=history[key] ||= {foes:context[:foes],stages:[],size:context[:size]}
    row[:stages] << context[:stage] unless row[:stages].include?(context[:stage])
  end
  module BattleStart
    def start_core(*args)
      previous=BlueStory.context
      current=BlueStory.enabled? ? {stage:BlueStory.stage,size:$game_temp.battle_rules['size']} : nil
      BlueStory.instance_variable_set(:@context,current)
      result=super
      BlueStory.record(current,result)
      result
    ensure
      BlueStory.instance_variable_set(:@context,previous)
    end
  end
  module Preparation
    def prepare_battle(battle)
      super
      if BlueStory.context && battle.trainerBattle?
        BlueStory.context[:size]="#{battle.pbSideSize(0)}v#{battle.pbSideSize(1)}"
      end
      if BlueStory.replaying?
        battle.expGain=true;battle.moneyGain=true;battle.internalBattle=true
      end
    end
  end
  module NoPickup
    def pbPickup(*args);return if BlueStory.replaying?;super;end
    def pbHoneyGather(*args);return if BlueStory.replaying?;super;end
  end
  def self.rematches
    history.values.select { |r| !r[:stages].empty? && r[:stages].min<stage && !r[:stages].include?(stage) }
  end
  def self.replay(row)
    raise 'Revanche indisponivel neste estagio.' unless enabled? && rematches.include?(row)
    previous=$game_temp.battle_rules.dup
    @replaying=true
    $game_temp.clear_battle_rules
    setBattleRule(row[:size] || 'single','canLose')
    TrainerBattle.start_core(*row[:foes])
  ensure
    @replaying=false
    if previous
      $game_temp.clear_battle_rules
      $game_temp.battle_rules.merge!(previous)
    end
  end
  def self.menu
    unless $PokemonGlobal.blue_traditional_starters
      if pbConfirmMessage('Ativar a progressao neste save? Inicial: 0-1 cristais; Intermediario: 2-4; Avancado: 5-10 (540 BST); Master: 11+ (sem teto).')
        $PokemonGlobal.blue_traditional_starters=true
      end
      return
    end
    rows=rematches
    if rows.empty?
      pbMessage("Modo #{LABELS[stage]}. As revanches Blue ficam disponiveis ao mudar de estagio, apos registrar uma vitoria. Treinadores da campanha continuam aceitando batalhas normalmente.")
      return
    end
    choice=pbMessage("#{LABELS[stage]} / Revanche: EXP e dinheiro, sem drops.",rows.map { |r| r[:foes].map { |f| f[1] }.join(' + ') }+['Voltar'],-1)
    replay(rows[choice]) if choice>=0 && choice<rows.length
  end
  def self.install
    return if @installed
    Interpreter.prepend(Choices);Battle.prepend(Teams);Battle::Battler.prepend(Forms)
    TrainerBattle.singleton_class.prepend(BattleStart)
    BattleCreationHelperMethods.singleton_class.prepend(Preparation)
    Object.prepend(NoPickup)
    MenuHandlers.add(:pause_menu,:blue_story_progress,{
      'name'=>'Progressao / Revanches Blue','order'=>66,
      'condition'=>proc { |menu| story? && !BlueBattleOptions.battle_area? },
      'effect'=>proc { |menu| menu.pbHideMenu;pbFadeOutIn { BlueStory.menu };menu.pbShowMenu;false }
    })
    @installed=true
  end
end
module Compiler
  class << self
    alias blue_presentation_original_main main
    def main
      blue_presentation_original_main
      BluePresentation.install;BlueStory.install
      BlueCampaign.install
      BlueJourney.install
      BlueBattleUI.install;BlueLocale.install
      BlueAdventure.install;BlueReadouts.install
      BlueStartMouse.install
      PokemonStorageScene.prepend(BlueStorageMouse::Scene) unless PokemonStorageScene.ancestors.include?(BlueStorageMouse::Scene)
      BlueExploration.install
      BlueDexControls.install;BlueDexCompare.install
      PokemonSummary_Scene.prepend(BlueLearnMouse) unless PokemonSummary_Scene.ancestors.include?(BlueLearnMouse)
      MoveRelearner_Scene.prepend(BlueRelearnMouse) unless MoveRelearner_Scene.ancestors.include?(BlueRelearnMouse)
      Battle::Scene::BattlerSprite.prepend(BlueFanBackFacing) unless Battle::Scene::BattlerSprite.ancestors.include?(BlueFanBackFacing)
      Battle::Scene.prepend(BlueFanBackFacing::Animations) unless Battle::Scene.ancestors.include?(BlueFanBackFacing::Animations)
      PBAnimationPlayerX.prepend(BlueFanBackFacing::Player) unless PBAnimationPlayerX.ancestors.include?(BlueFanBackFacing::Player)
      PokemonRegionMap_Scene.prepend(BlueRegionMapSafety) unless PokemonRegionMap_Scene.ancestors.include?(BlueRegionMapSafety)
      BlueTraining.install
      BlueTrainerAlbum.install
      BlueHabitatRewards.install
      PokemonSummary_Scene.prepend(BlueSummaryBackdrop) unless PokemonSummary_Scene.ancestors.include?(BlueSummaryBackdrop)
      BlueParadoxTitle.install if defined?(BlueParadoxTitle)
    end
  end
end
