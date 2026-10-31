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
    log('READY | fresh in-memory player; no campaign loaded')
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

  def self.battle(ally, foe, automated = false)
    ally.heal
    foe.heal
    $player.party = [ally]
    EventHandlers.trigger(:on_start_battle)
    scene = automated ? SmokeScene.new : Battle::Scene.new
    battle = Battle.new(scene, [ally], [foe], [$player], nil)
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
    log("BATTLE | #{ally.species_data.id} L#{ally.level} #{ally.moves.map(&:id).join(',')} vs #{foe.species_data.id} L#{foe.level}")
    pbBGMPlay(pbGetWildBattleBGM([foe])) unless automated
    result = battle.pbStartBattle
    log("RESULT | outcome=#{result} rounds=#{battle.turnCount} ally_hp=#{ally.hp} foe_hp=#{foe.hp}")
    return result
  ensure
    $game_temp.in_battle = false
    ally.heal
    foe.heal
    pbBGMStop unless automated
  end

  class Scene
    def main
      BlueBattleLab.setup
      if BlueBattleLab::SMOKE
        [[ :PIKACHU, :MAGIKARP, 10 ], [ :MIRAIDON, :KORAIDON, 50 ], [ :GREATTUSK, :IRONVALIANT, 50 ]].each do |a,b,level|
          result = BlueBattleLab.battle(BlueBattleLab.build(a,level), BlueBattleLab.build(b,level), true)
          raise 'Battle did not finish' unless [1,2,3,5].include?(result)
        end
        raise 'Save protection failed' unless Game.save == false && Game.auto_save == false && SaveData.exists? == false && SaveData.save_to_file('Data/blue-lab-should-not-save.rxdata') == false
        raise 'Save unexpectedly created' if File.file?('Data/blue-lab-should-not-save.rxdata')
        BlueBattleLab.log('SMOKE=PASS | three complete engine battles; save guards passed')
        $scene = nil
        return
      end
      @level = 50
      @ally = BlueBattleLab.build(:MIRAIDON, @level)
      @foe = BlueBattleLab.build(:KORAIDON, @level)
      @background = Sprite.new
      @background.bitmap = Bitmap.new(Graphics.width, Graphics.height)
      redraw
      Graphics.transition(0)
      BlueBattleLab.log('MENU_READY')
      loop do
        commands = ['Iniciar batalha 1 x 1', 'Escolher meu Pokemon', 'Escolher adversario', "Nivel: #{@level}", 'Editar meus golpes', 'Editar golpes do adversario', 'Teste rapido: Pikachu x Eevee', 'Sair do laboratorio']
        choice = pbMessage('BLUE - LABORATORIO DE BATALHA', commands, commands.length)
        case choice
        when 0
          result = BlueBattleLab.battle(@ally, @foe)
          redraw
          pbMessage({1=>'Vitoria!',2=>'Derrota.',3=>'Batalha encerrada.',5=>'Empate.'}[result] || 'Teste encerrado.')
        when 1, 2
          current = choice == 1 ? @ally : @foe
          selected = pbChooseSpeciesFormList(current.species_data.id)
          if selected
            pkmn = BlueBattleLab.build(selected, @level)
            choice == 1 ? @ally = pkmn : @foe = pkmn
          end
        when 3
          params = ChooseNumberParams.new
          params.setRange(1,100)
          params.setDefaultValue(@level)
          params.setCancelValue(@level)
          @level = pbMessageChooseNumber('Nivel dos dois Pokemon (1 a 100).', params)
          [@ally,@foe].each { |p| p.level=@level; p.reset_moves; p.calc_stats; p.heal }
        when 4 then edit_moves(@ally)
        when 5 then edit_moves(@foe)
        when 6
          @level=10
          @ally=BlueBattleLab.build(:PIKACHU,@level)
          @foe=BlueBattleLab.build(:EEVEE,@level)
        else break
        end
        redraw
      end
      $scene = nil
    rescue StandardError => error
      BlueBattleLab.log("ERROR | #{error.class}: #{error.message}\n#{error.backtrace.join("\n")}")
      raise
    ensure
      @background.bitmap.dispose if @background && @background.bitmap
      @background.dispose if @background
    end

    def edit_moves(pkmn)
      loop do
        names=(0...4).map { |i| "#{i+1}: #{pkmn.moves[i] ? pkmn.moves[i].name : '(vazio)'}" } + ['Voltar']
        slot=pbMessage('Escolha o golpe para trocar. Lista livre para testes.',names,5)
        break if slot<0 || slot>=4
        move=pbChooseMoveList(pkmn.moves[slot]&.id)
        next unless move
        if slot>pkmn.moves.length
          pbMessage('Preencha os espacos anteriores primeiro.')
        else
          pkmn.moves[slot]=Pokemon::Move.new(move)
        end
      end
    end

    def redraw
      bitmap=@background.bitmap
      bitmap.fill_rect(0,0,Graphics.width,Graphics.height,Color.new(9,18,35))
      pbSetSystemFont(bitmap)
      bitmap.font.color=Color.new(135,190,255)
      bitmap.draw_text(20,16,Graphics.width-40,36,'POKEMON BLUE / BATTLE LAB')
      bitmap.font.color=Color.new(245,248,255)
      bitmap.draw_text(20,68,Graphics.width-40,32,"Voce: #{@ally.species_data.name} / forma #{@ally.form}")
      bitmap.draw_text(20,104,Graphics.width-40,32,"Rival: #{@foe.species_data.name} / forma #{@foe.form}")
      bitmap.draw_text(20,146,Graphics.width-40,32,"Nivel #{@level} | IVs 31 | EVs 0 | Natureza neutra")
      bitmap.font.color=Color.new(170,190,210)
      bitmap.draw_text(20,196,Graphics.width-40,32,'Teste isolado. Nao carrega nem grava a campanha.')
      bitmap.draw_text(20,228,Graphics.width-40,32,'Especies novas precisam estar compiladas nos PBS.')
    end
  end
end

if BlueBattleLab::ACTIVE
  module Compiler
    class << self
      alias blue_battle_lab_original_main main
      def main
        blue_battle_lab_original_main
        BlueBattleLab.install
      end
    end
  end
end
