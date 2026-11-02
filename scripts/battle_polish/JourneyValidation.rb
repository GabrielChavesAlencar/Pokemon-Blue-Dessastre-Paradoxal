# Native regression for campaign rules, residual effects and pause/save lifecycle.
module BlueJourneyValidation
  class StartCapture
    def self.start_core(*args);args;end
    singleton_class.prepend(BlueJourney::TrainerStart)
  end
  class QuietScene
    attr_reader :messages
    def initialize;@messages=[];end
    def pbDisplayMessage(text,*args);@messages << text;end
    def method_missing(*args);end
  end
  def self.check(value,label)
    raise label unless value
    @lines << 'PASS | '+label
  end
  def self.battle(wild=false)
    a=BlueBattleLab.build(:EEVEE,50);a.moves=[Pokemon::Move.new(:TACKLE)]
    b=BlueBattleLab.build(:SNORLAX,50);b.moves=[Pokemon::Move.new(:SPLASH)]
    t=NPCTrainer.new('Residual regression',:YOUNGSTER);t.party=[b]
    battle=Battle.new(QuietScene.new,[a],[b],[$player],wild ? nil : [t])
    battle.internalBattle=false;battle.showAnims=false
    battle.pbEnsureParticipants;battle.pbSetUpSides
    battle
  end
  def self.residuals
    battle=self.battle;user,target=battle.battlers[0],battle.battlers[1]
    seed=Battle::Move.from_pokemon_move(battle,Pokemon::Move.new(:LEECHSEED))
    check(seed.is_a?(Battle::Move::StartLeechSeedTarget),'Compiled Leech Seed uses the native seeding function')
    check(!seed.pbFailsAgainstTarget?(user,target,false),'Leech Seed accepts a normal non-Grass target')
    seed.pbEffectAgainstTarget(user,target);user.hp=1
    amount=target.totalhp/8;hp=target.hp
    3.times do
      before=user.hp;battle.pbEORHealingEffects([user,target])
      check(target.hp==hp-amount,'Leech Seed drains exactly 1/8 HP on a consecutive turn')
      check(user.hp==[before+amount,user.totalhp].min,'Leech Seed heals the current recipient')
      hp=target.hp
    end
    battle.instance_variable_set(:@endOfRound,true)
    check(!battle.pbSpeedyEndOfRound?,'Residual messages and native HP animations are visible')
    battle.pbDisplay('Residual feedback regression')
    check(battle.scene.messages.last=='Residual feedback regression','End-of-round text reaches the real scene callback')
    target.ability=:MAGICGUARD;before=target.hp;battle.pbEORHealingEffects([user,target])
    check(target.hp==before,'Magic Guard still prevents seed residual damage')
    grass=BlueBattleLab.build(:BULBASAUR,50)
    target.pbInitialize(grass,0)
    check(seed.pbFailsAgainstTarget?(user,target,false),'Grass immunity to Leech Seed is preserved')
  end
  def self.statuses
    battle=self.battle;mon=battle.battlers[0];move=mon.moves.first
    battle.define_singleton_method(:pbRandom) { |n| @blue_test_roll || 0 }
    durations=(0...3).map { |n| battle.instance_variable_set(:@blue_test_roll,n);mon.pbSleepDuration }
    check(durations==[2,3,3],'Champions sleep counter distribution is 2/3/3 (one or two blocked actions)')
    durations.each do |duration|
      mon.status=:SLEEP;mon.statusCount=duration
      actions=Array.new(duration) { mon.pbTryUseMove([:UseMove,0,move,-1],move,false,false) }
      check(actions==Array.new(duration-1,false)+[true] && mon.status==:NONE,'Native move checks wake on the correct action')
    end
    check(mon.pbSleepDuration(3)==3,'Explicit Rest sleep duration is preserved')
    mon.ability=:EARLYBIRD;battle.instance_variable_set(:@blue_test_roll,2)
    check(mon.pbSleepDuration==1,'Early Bird still shortens the Champions sleep duration')
    mon.ability=:RUNAWAY;mon.status=:PARALYSIS
    rolls=[];blocked=[]
    battle.define_singleton_method(:pbRandom) { |n| rolls << n;@blue_test_roll || 0 }
    8.times do |n|
      battle.instance_variable_set(:@blue_test_roll,n)
      blocked << !mon.pbTryUseMove([:UseMove,0,move,-1],move,false,false)
    end
    check(rolls==[8]*8 && blocked.count(true)==1 && blocked.first,'Native full paralysis is exactly one outcome in eight')
  end
  def self.choices
    cases=[
      [['No','Start Battle (Exp Gain)','Start Battle (Forfeit Option)','Full Team Heal'],false,['No','Start Battle (Exp Gain)'],[0,1]],
      [['Full Team Heal','Basic Team','Full Power Team','Cancel'],true,['Full Power Team','Cancel'],[2,3]],
      [['Single Battle','Double Battle','Triple Battle'],true,['Double Battle','Cancel'],[1,-999]],
      [['Start Battle (Exp Gain)','Start Battle (Forfeit Option)'],true,['Start Battle (Exp Gain)','Cancel'],[0,-999]]
    ]
    cases.each do |labels,gym,wanted,mapping|
      before=Marshal.dump(labels)
      result=BlueJourney.filter_choices([labels,1,(0...labels.length).to_a],gym)
      check(result[0]==wanted && result[2]==mapping,'Trainer choices retain only authorized battle options and correct branch indices')
      check(['No','Cancel'].include?(result[0][result[1]-1]),'Back cancels instead of healing or starting a battle')
      check(Marshal.dump(labels)==before,'Filtering never rewrites source map choices')
    end
    # Inspect every actual trainer event/page, not just synthetic menus.
    pages=0
    load_data('Data/MapInfos.rxdata').keys.sort.each do |id|
      load_data(sprintf('Data/Map%03d.rxdata',id)).events.each_value do |event|
        event.pages.each do |page|
          next unless BlueJourney.trainer_event?(page.list)
          gym=BlueJourney.gym_event?(page.list)
          page.list.select { |c| c.code==102 }.each do |c|
            labels=c.parameters[0];filtered=BlueJourney.filter_choices([labels,c.parameters[1],(0...labels.length).to_a],gym)
            check(!filtered[0].include?('Full Team Heal') && filtered[0].none? { |s| s.include?('Forfeit Option') },'Actual trainer page has no free heal or forfeit battle option')
            check(!gym || (filtered[0] & ['Basic Team','Single Battle','Triple Battle']).empty?,'Actual gym page offers only Full Power doubles')
          end
          pages+=1
        end
      end
      Graphics.update
    end
    @lines << 'TRAINER_PAGES='+pages.to_s
    check(pages>100,'All campaign trainer menus were scanned')
  end
  def self.scaling
    active=BlueCampaign.method(:active?);enabled=BlueStory.method(:enabled?)
    old_party=$player.party;badges=$player.badges.dup
    BlueCampaign.define_singleton_method(:active?) { true }
    BlueStory.define_singleton_method(:enabled?) { true }
    $player.party=[BlueBattleLab.build(:EEVEE,50),BlueBattleLab.build(:PIKACHU,100)]
    check(BlueCampaign.common_level==70 && BlueCampaign.wild_level==45,'Party maximum 100 gives trainers 70 and wild Pokemon 45')
    $player.party.last.level=51
    check(BlueCampaign.common_level==35 && BlueCampaign.wild_level==22,'Ratios round down and use the highest party member')
    [0,2,4].each do |n|
      $player.badges.map!.with_index { |v,i| i<n }
      mon=pbGenerateWildPokemon(:GARCHOMP,99)
      check(mon.level==22,'Wild generation overrides legacy automatic level scaling')
      check(!BlueStory.cap || BlueStory.bst(mon.species_data)<=BlueStory.cap,'Wild species follows the current 350/450 BST ceiling')
      source=BlueBattleLab.build(:GARCHOMP,99);before=Marshal.dump(source)
      b=Battle.new(QuietScene.new,$player.party,[source],[$player],nil)
      check(b.pbParty(1).first.level==22 && Marshal.dump(source)==before,'Direct/static wild battle entry also scales without mutating its source')
      check(!BlueStory.cap || BlueStory.bst(b.pbParty(1).first.species_data)<=BlueStory.cap,'Direct wild entry cannot bypass the species ceiling')
    end
    trainer=NPCTrainer.new('Marigold (2v2 Full Power)',:HOENNIAN_ORAS_AROMALADY)
    trainer.party=[BlueBattleLab.build(:ARCHGUTOR,100)]
    b=Battle.new(QuietScene.new,$player.party,trainer.party,[$player],[trainer])
    check(b.pbParty(1).first.level==35,'Named gym leaders receive the same trainer ratio')
    args=StartCapture.start_core(:HOENNIAN_ORAS_AROMALADY,'Marigold (1v1 Basic Power)',0)
    check(args==[:HOENNIAN_ORAS_AROMALADY,'Marigold (2v2 Full Power)',0],'Gym adapter selects the compiled Full Power doubles roster')
    check($game_temp.battle_rules['size']=='double' && $game_temp.battle_rules['expGain']==true,'Gym adapter forces doubles and EXP even for old event scripts')
    setBattleRule('noExp');BattleCreationHelperMethods.prepare_battle(b)
    check(b.expGain && b.moneyGain,'Normal trainer preparation overrides legacy noExp rules')
    b.pbEnsureParticipants;b.pbSetUpSides
    b.battlers[1].hp=0;b.battlers[1].participants=[0]
    before_exp=$player.party.first.exp;b.pbGainExp
    check($player.party.first.exp>before_exp,'Defeating a scaled trainer actually grants native experience')
    $player.party.each { |p| p.level=1 }
    check(BlueCampaign.common_level==1 && BlueCampaign.wild_level==1,'Both ratios clamp to level 1')
  ensure
    BlueCampaign.define_singleton_method(:active?,active) if active
    BlueStory.define_singleton_method(:enabled?,enabled) if enabled
    $player.party=old_party if old_party;$player.badges.replace(badges) if badges
    $game_temp.clear_battle_rules
  end
  def self.pause
    # Same termination path as the Save menu's success callback. Reopening and
    # map-return tests use fresh native components, never the campaign save.
    original_map=$game_map
    [79,43,79].each do |id|
      map=Game_Map.new;map.setup(id);$game_map=map
      menu=VoltseonsPauseMenu_Scene.new
      component=VPM_NewQuestHud.new
      component.start_component(menu.instance_variable_get(:@viewport),menu)
      menu.instance_variable_set(:@components,[component])
      menu.instance_variable_set(:@hidden,true)
      callback=Object.new
      callback.define_singleton_method(:dispose) { }
      callback.define_singleton_method(:update) { menu.pbEndScene }
      menu.instance_variable_set(:@pause_menu,callback)
      menu.update
      check(menu.instance_variable_get(:@has_terminated) && component.sprites.empty?,'Save-success callback closes without updating disposed quest HUD, map '+id.to_s)
    end
    raw=Marshal.dump(SaveData.compile_save_hash)
    check(Marshal.load(raw)[:player].name==$player.name,'Current campaign objects serialize and reload in memory')
  ensure
    $game_map=original_map if original_map
  end
  def self.run
    @lines=[]
    residuals;statuses;choices;scaling;pause
    @lines << 'RESULT=PASS';true
  rescue StandardError=>error
    @lines << "FAIL | #{error.class}: #{error.message}";@lines.concat(error.backtrace || []);@lines << 'RESULT=FAIL';false
  ensure
    File.open('Data/blue-journey-validation.txt','wb') { |f| f.write(@lines.join("\n")+"\n") }
  end
end
