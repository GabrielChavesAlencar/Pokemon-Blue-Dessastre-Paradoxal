# Blue's opt-in sandbox. This file is original project code, not game assets.
module BlueBattleLab
  REQUEST = 'Data/blue-battle-lab-request.txt'
  request = File.file?(REQUEST) && (Time.now - File.mtime(REQUEST) < 120) ? File.read(REQUEST).strip : ''
  ACTIVE = ENV['BLUE_BATTLE_LAB'] == '1' || ['play', 'smoke'].include?(request)
  SMOKE = ENV['BLUE_BATTLE_LAB_SMOKE'] == '1' || request == 'smoke'
  File.delete(REQUEST) if File.file?(REQUEST)
  $DEBUG = true if ACTIVE
  LOG = 'Data/blue-battle-lab.log'
  def self.log(text)
    File.open(LOG, 'ab') { |f| f.puts("#{Time.now} | #{text}") }
  end

  def self.install
    # Install after all other plugins, including Auto Multi Save, have loaded.
    Game.define_singleton_method(:set_up_system) do
      SaveData.initialize_bootup_values
      pbSetResizeFactor(1)
    end
    Game.define_singleton_method(:save) { |*args, **kwargs| false }
    Game.define_singleton_method(:auto_save) { |*args| false }
    SaveData.define_singleton_method(:exists?) { false }
    SaveData.define_singleton_method(:read_from_file) { |*args| {} }
    SaveData.define_singleton_method(:save_to_file) { |*args| false }
    Object.send(:define_method, :pbEmergencySave) { BlueBattleLab.log('Emergency save blocked in lab') }
    Object.send(:define_method, :pbCallTitle) { BlueBattleLab::Scene.new }
    log('INSTALLED | campaign save read/write disabled')
  end

  def self.setup
    SaveData.load_new_game_values
    $player.name = 'Blue Lab'
    pbChangePlayer(0)
    # Only load map data required by battle plugins; do not run Scene_Map or events.
    $map_factory = PokemonMapFactory.new($data_system.start_map_id)
    $game_player.moveto($data_system.start_x, $data_system.start_y)
    $PokemonEncounters = PokemonEncounters.new
    $PokemonEncounters.setup($game_map.map_id)
    $game_temp.last_uptime_refreshed_play_time = System.uptime
    $PokemonGlobal.partner = nil
    $bag.add(:MEGARING) if GameData::Item.try_get(:MEGARING)
    log('READY | fresh in-memory player; no campaign loaded')
  end

  def self.choose_species(default)
    return pbChooseSpeciesFormList(default) unless GameData::Species.try_get(:CAVEFANG)
    group=choose('Escolha a geracao.', ['Dessastre Paradoxal','Catalogo completo'])
    return pbChooseSpeciesFormList(default) if group==1
    return nil if group!=0
    list=[]
    GameData::Species.each { |sp| list << sp if sp.flags.include?('DessastreParadoxal') }
    list.sort_by! { |sp| (sp.form>0 ? sp.form_name : sp.name).downcase }
    labels=list.map { |sp| sp.form>0 ? sp.form_name : sp.name }
    selected=choose('Dessastre Paradoxal',labels, list.index { |sp| sp.id == default } || 0)
    return selected>=0 && selected<list.length ? list[selected].id : nil
  end

  def self.build(species, level)
    pkmn = Pokemon.new(species, level, $player, true, false)
    pkmn.nature = :HARDY
    pkmn.iv.each_key { |stat| pkmn.iv[stat] = 31 }
    pkmn.ev.each_key { |stat| pkmn.ev[stat] = 0 }
    pkmn.calc_stats
    pkmn.heal
    pkmn.learn_move(:TACKLE) if pkmn.moves.empty?
    return pkmn
  end

  # A real animated battle scene, with confirmations disabled only in smoke tests.
  class SmokeScene < Battle::Scene
    def pbDisplayMessage(message, brief = false); end
    def pbDisplayPausedMessage(message); end
    def pbDisplayConfirmMessage(message); true; end
  end

  def self.validate_teams(allies, foes, format)
    raise ArgumentError, 'Formato desconhecido.' unless ['single','double'].include?(format)
    [allies, foes].each do |team|
      raise ArgumentError, 'Cada time deve ter de 1 a 6 Pokemon.' unless team.is_a?(Array) && (1..6).include?(team.length)
      raise ArgumentError, 'Batalhas em dupla precisam de pelo menos dois Pokemon por time.' if format == 'double' && team.length < 2
    end
  end

  def self.battle(allies, foes, automated = false, format = 'single')
    allies = [allies] unless allies.is_a?(Array)
    foes = [foes] unless foes.is_a?(Array)
    validate_teams(allies, foes, format)
    # Battles may consume items, transform forms and reorder a party. Keep the
    # editable roster intact and give the battle its own complete Pokemon copies.
    team1, team2 = Marshal.load(Marshal.dump([allies, foes]))
    [*team1, *team2].each(&:heal)
    previous_party = $player.party
    $player.party = team1
    trainer = NPCTrainer.new('Rival do Lab', $player.trainer_type)
    trainer.party = team2
    EventHandlers.trigger(:on_start_battle)
    scene = automated ? SmokeScene.new : Battle::Scene.new
    battle = Battle.new(scene, team1, team2, [$player], [trainer])
    battle.setBattleMode(format)
    battle.internalBattle = false
    battle.canLose = true
    battle.canRun = true
    battle.expGain = false
    battle.moneyGain = false
    battle.disablePokeBalls = true
    battle.environment = :None
    battle.backdrop = 'indoor1'
    battle.time = 0
    battle.controlPlayer = true if automated
    battle.showAnims = !automated
    $game_temp.in_battle = true
    log("BATTLE | format=#{format} teams=#{team1.length}x#{team2.length} allies=#{team1.map { |p| p.species_data.id }.join(',')} foes=#{team2.map { |p| p.species_data.id }.join(',')}")
    pbBGMPlay(pbGetTrainerBattleBGM([trainer])) unless automated
    result = battle.pbStartBattle
    log("RESULT | format=#{format} teams=#{team1.length}x#{team2.length} outcome=#{result} rounds=#{battle.turnCount} foe_fainted=#{team2.count(&:fainted?)}")
    return result
  ensure
    $game_temp.in_battle = false
    $player.party = previous_party if defined?(previous_party) && previous_party
    pbBGMStop unless automated
  end

end

module Compiler
    class << self
      alias blue_battle_lab_original_main main
      def main
        blue_battle_lab_original_main
        BlueBattleLab.install_interface
        BlueBattleLab.install if BlueBattleLab::ACTIVE
      end
    end
  end
