# Runtime campaign rules. Original maps, teams and existing saves are not rewritten.
module BlueJourney
  GYM_NAMES=%w[Marigold Reva Keegan Quinn Luis Luna Galen Christopher Atlas Sophia Hermes Cethin Keiko Roho Belinda Gohar Eira Azure].freeze
  def self.gym_name(name)
    base=name.to_s.split(' (').first
    GYM_NAMES.include?(base) ? base : nil
  end
  def self.trainer_event?(list)
    list && list.any? { |c| [111,355,655].include?(c.code) && c.parameters.any? { |v| v.is_a?(String) && v.include?('TrainerBattle.start') } }
  end
  def self.gym_event?(list)
    list.any? { |c| [111,355,655].include?(c.code) && c.parameters.any? { |v| v.is_a?(String) && GYM_NAMES.any? { |n| v.include?(n+' (') } } }
  end
  # Keep Essentials' original branch indices, including cancel. Never map Back to Heal.
  def self.filter_choices(result,gym=false)
    labels,cancel,mapping=result
    keep=if labels.any? { |s| s.include?('Start Battle (Exp Gain)') }
      labels.each_index.select { |i| !labels[i].include?('Forfeit') && !labels[i].include?('Full Team Heal') }
    elsif gym && labels.include?('Full Power Team')
      labels.each_index.select { |i| ['Full Power Team','Cancel','No'].include?(labels[i]) }
    elsif gym && labels.include?('Double Battle')
      labels.each_index.select { |i| ['Double Battle','Cancel','No'].include?(labels[i]) }
    else
      labels.each_index.reject { |i| labels[i]=='Full Team Heal' }
    end
    return [['Cancel'],1,[-999]] if keep.empty?
    return result if keep.length==labels.length
    shown=keep.map { |i| labels[i] };branches=keep.map { |i| mapping[i] }
    exit_index=shown.index { |s| ['No','Cancel'].include?(s) }
    unless exit_index
      shown << 'Cancel';branches << -999;exit_index=shown.length-1
    end
    [shown,exit_index+1,branches]
  end
  module Choices
    def setup_choices(params)
      result=super
      return result unless BlueCampaign.active? && BlueJourney.trainer_event?(@list)
      gym=BlueJourney.gym_event?(@list)
      BlueJourney.filter_choices(result,gym)
    end
  end
  module TrainerStart
    def start_core(*args)
      if BlueCampaign.active?
        # TrainerBattle accepts flattened triples and nested trainer descriptors.
        convert=proc do |value|
          if value.is_a?(Array)
            value.map { |v| convert.call(v) }
          elsif value.is_a?(String) && BlueJourney.gym_name(value)
            BlueJourney.gym_name(value)+' (2v2 Full Power)'
          else value
          end
        end
        gym=args.flatten.any? { |a| a.is_a?(String) && BlueJourney.gym_name(a) }
        args=args.map { |a| convert.call(a) } if gym
        setBattleRule('double') if gym
        # Old events may still contain towerBattle/noExp. The preparation hook
        # below also covers battles started directly rather than by an event.
        $game_temp.battle_rules['expGain']=true
      end
      super(*args)
    end
  end
  module Preparation
    def prepare_battle(battle)
      super
      if BlueCampaign.active? && battle.trainerBattle?
        battle.expGain=true;battle.internalBattle=true;battle.moneyGain=true
      end
    end
  end
  module Wild
    def pbGenerateWildPokemon(species,level,isRoamer=false)
      return super unless BlueCampaign.active?
      chosen=GameData::Species.get(species)
      chosen=BlueStory.replacement(chosen,BlueStory.cap) if BlueStory.enabled? && BlueStory.cap
      pkmn=super(chosen.species,BlueCampaign.wild_level,isRoamer)
      # Finalize after the base's generation handlers, which otherwise rescale it.
      pkmn.species=chosen.species;pkmn.form=chosen.form;pkmn.level=BlueCampaign.wild_level
      pkmn.reset_moves;pkmn.calc_stats;pkmn.heal
      pkmn
    end
  end
  module WildTeams
    def initialize(*args)
      if BlueCampaign.active? && (args[4].nil? || Array(args[4]).empty?)
        args[2]=Array(args[2]).map do |source|
          mon=BlueStory.enabled? && BlueStory.cap ? BlueStory.adjust(source,BlueStory.cap) : Marshal.load(Marshal.dump(source))
          mon.level=BlueCampaign.wild_level;mon.reset_moves;mon.calc_stats;mon.heal;mon
        end
      end
      super(*args)
    end
  end
  module Sleep
    def pbSleepDuration(duration=-1)
      # Count includes the waking action: [2,3,3] blocks 1/2/2 actions.
      # Explicit durations (Rest) and the engine's Early Bird handling remain intact.
      duration=[2,3,3][@battle.pbRandom(3)] if duration<=0
      super(duration)
    end
  end
  module ResidualFeedback
    def pbSpeedyEndOfRound?;false;end
  end
  module PauseLifecycle
    def update
      @has_terminated=false
      loop do
        Graphics.update;Input.update
        @pause_menu.update
        # Saving can call pbEndScene inside the menu callback. No component may
        # read its overlay sprite after that point (the quest HUD used to crash).
        break if @has_terminated
        unless @should_exit
          @components.each(&:update)
          pbUpdateSpriteHash(@sprites);pbUpdateSceneMap;pbRefresh
        end
        next unless @should_exit
        pbSEPlay(MENU_CLOSE_SOUND);pbHideMenu;pbEndScene
        break
      end
    end
  end
  def self.install
    return if @installed
    Interpreter.prepend(Choices);Object.prepend(Wild)
    TrainerBattle.singleton_class.prepend(TrainerStart)
    BattleCreationHelperMethods.singleton_class.prepend(Preparation)
    Battle::Battler.prepend(Sleep);Battle.prepend(ResidualFeedback);Battle.prepend(WildTeams)
    VoltseonsPauseMenu_Scene.prepend(PauseLifecycle) if defined?(VoltseonsPauseMenu_Scene)
    @installed=true
  end
end
