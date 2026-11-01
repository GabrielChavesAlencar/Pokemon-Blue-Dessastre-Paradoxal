# Opt-in feasibility test only. Never loaded by the normal project installer.
module BlueOnlineProbe
  REQUEST='Data/blue-online-engine-request.txt'
  def self.json(value)
    case value
    when Hash then '{'+value.map { |k,v| json(k.to_s)+':'+json(v) }.join(',')+'}'
    when Array then '['+value.map { |v| json(v) }.join(',')+']'
    when String,Symbol then '"'+value.to_s.gsub(/["\\\x00-\x1f]/) { |c| '\\u%04x'%c.ord }+'"'
    when Integer then value.to_s
    when TrueClass then 'true'
    when FalseClass then 'false'
    when NilClass then 'null'
    else raise 'Unsupported catalog value'
    end
  end
  class Scene < Battle::DebugSceneNoVisuals
    VisualState=Struct.new(:vanishMode,:prepare_mosaic,:substitute)
    attr_reader :messages,:sprites
    def initialize
      super(false);@messages=[];@sprites={}
      # The animation plugin queries render-state even on an ordinary end turn.
      # Store only those flags, without allocating sprites or bitmaps.
      6.times { |i| @sprites["pokemon_#{i}"]=VisualState.new(0,false,false) }
    end
    def pbDisplayMessage(message,*args);@messages << message.to_s;end
    def pbDisplayPausedMessage(message);@messages << message.to_s;end
    # This animation plugin calls its presentation hook even with showAnims=false.
    # Keep the adapter local to the probe; do not patch the installed plugin.
    def pbUpdateSubstituteSprite(*args);end
    def pbAnimateSubstitute(*args);end
    def pbForceEndSpeech(*args);end
    def pbBeginCommandPhase
      raise 'No-visuals simulation exceeded 30 turns' if @battle.turnCount>30
      Graphics.update;Input.update
    end
    def pbUpdate(*args);Graphics.update;end
  end
  def self.export_catalog
    species={}
    GameData::Species.each do |data|
      next if data.base_stats.values.sum<=0
      species[data.id.to_s]={'mega'=>!!(data.mega_stone || data.mega_move),'abilities'=>(data.abilities+data.hidden_abilities).uniq.map(&:to_s)}
    end
    catalog={'schema'=>1,'species'=>species}
    {'items'=>GameData::Item,'moves'=>GameData::Move,'natures'=>GameData::Nature}.each do |key,klass|
      ids=[];klass.each { |data| ids << data.id.to_s };catalog[key]=ids.sort
    end
    File.open('Data/blue-online-catalog.json','wb') { |f| f.write(json(catalog)) }
  end
  def self.battle(allies,foes,format)
    # Server-side failures must propagate to the report, never open a modal.
    logger=PBDebug.method(:logonerr)
    PBDebug.define_singleton_method(:logonerr) { |*args,&block| block.call }
    # All state is fresh and temporary. No player party or campaign data is loaded.
    scene=Scene.new;trainer=NPCTrainer.new('Online engine probe',$player.trainer_type);trainer.party=foes
    battle=Battle.new(scene,allies,foes,[$player],[trainer]);battle.setBattleMode(format)
    battle.internalBattle=false;battle.canLose=true;battle.canRun=false;battle.expGain=false;battle.moneyGain=false
    battle.disablePokeBalls=true;battle.controlPlayer=true;battle.showAnims=false
    battle.instance_variable_set(:@blue_radical_profile,'radical')
    battle.instance_variable_set(:@blue_mechanics,{'mega'=>false,'zmove'=>false,'tera'=>false,'dynamax'=>false})
    previous=$game_temp.in_battle;$game_temp.in_battle=true
    result=battle.pbStartBattle
    raise 'No-visuals simulation did not finish' unless result==1 && foes.all?(&:fainted?)
    "PASS | #{format} #{allies.length}x#{foes.length} no-visuals simulation; result=#{result}; turns=#{battle.turnCount}; messages=#{scene.messages.length}"
  ensure
    PBDebug.define_singleton_method(:logonerr,logger) if logger
    $game_temp.in_battle=previous if defined?(previous)
  end
  def self.run
    # A stuck diagnostic must never leave the test process running indefinitely.
    # This thread uses only Ruby IO/process APIs, never graphics or engine HTTP.
    watchdog=Thread.new do
      sleep 20
      File.open('Data/blue-online-engine-validation.txt','wb') { |f| f.write("FAIL | Native probe exceeded 20 seconds\n"+Thread.main.backtrace.join("\n")+"\nRESULT=FAIL\n") }
      exit! 1
    end
    lines=[];before=Marshal.dump($player.party)
    make=proc { |species,move| m=BlueBattleLab.build(species,50);m.moves=[Pokemon::Move.new(move)];m }
    lines << battle([make.call(:PIKACHU,:THUNDERBOLT)],[make.call(:MAGIKARP,:SPLASH)],'single')
    lines << battle(Array.new(4) { make.call(:PIKACHU,:THUNDERBOLT) },Array.new(4) { make.call(:MAGIKARP,:SPLASH) },'double')
    lines << battle([make.call(:CAVEFANG,:SLUDGEBOMB)],[make.call(:MAGIKARP,:SPLASH)],'single')
    raise 'The engine probe mutated the offline party' unless Marshal.dump($player.party)==before
    export_catalog;lines << 'PASS | Native catalog exported; original party preserved';lines << 'RESULT=PASS';true
  rescue StandardError,SystemStackError=>error
    lines << "FAIL | #{error.class}: #{error.message}";lines.concat(error.backtrace);lines << 'RESULT=FAIL';false
  ensure
    watchdog.kill if watchdog && watchdog.alive?
    File.open('Data/blue-online-engine-validation.txt','wb') { |f| f.write(lines.join("\n")+"\n") }
    File.delete(REQUEST) if File.file?(REQUEST)
  end
  module Smoke
    def run_smoke
      only=File.read(BlueOnlineProbe::REQUEST).strip=='probe-only'
      check(BlueOnlineProbe.run,'Online opt-in engine probe; Data/blue-online-engine-validation.txt')
      if only
        log('ONLINE_PROBE=PASS | no offline validation skipped in ordinary smoke mode')
      else
        super
      end
    end
  end
end
module Compiler
  class << self
    alias blue_online_probe_original_main main
    def main
      blue_online_probe_original_main
      if defined?(BlueBattleLab) && BlueBattleLab::SMOKE && File.file?(BlueOnlineProbe::REQUEST) && Time.now-File.mtime(BlueOnlineProbe::REQUEST)<120
        BlueBattleLab.singleton_class.prepend(BlueOnlineProbe::Smoke) unless BlueBattleLab.singleton_class.ancestors.include?(BlueOnlineProbe::Smoke)
      end
    end
  end
end
