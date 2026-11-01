# Team builder for the real engine. All configuration lives in this lab session.
module BlueBattleLab
  def self.preset(author = false, level = 50)
    sides = if author && GameData::Species.try_get(:CAVEFANG)
      [[:CAVEFANG,:ARCHGUTOR,:MAGNETRIX,:AMMNOID,:MIRAIDON,:PIKACHU],
       [:IRONCRUSHER,:STUNDRIFT,:DYNAMOTRODE,:CEPHALONID,:KORAIDON,:EEVEE]]
    else
      [[:PIKACHU,:CHARIZARD,:BLASTOISE,:VENUSAUR,:GENGAR,:SNORLAX],
       [:EEVEE,:DRAGONITE,:GYARADOS,:ALAKAZAM,:ARCANINE,:MACHAMP]]
    end
    sides.map { |ids| ids.map { |id| build(id, level) } }
  end

  class Scene
    def main
      BlueBattleLab.setup
      if BlueBattleLab::SMOKE
        BlueBattleLab.run_smoke
        $scene = nil
        return
      end
      @format = 'single'
      @ai_profile = defined?(BlueRadicalAI) ? BlueRadicalAI::CONFIG['defaultProfile'] : 'engine'
      @allies, @foes = BlueBattleLab.preset(true)
      BlueBattleLab.log('MENU_READY | teams=6x6 mouse=true')
      loop do
        format_label = @format == 'double' ? 'Dupla (2 em campo)' : 'Individual (1 em campo)'
        choice = BlueBattleLab.choose("BLUE LAB / Times #{@allies.length} x #{@foes.length}", [
          'Iniciar batalha', "Formato: #{format_label}", 'Editar meu time',
          'Editar time rival', 'Nivel de todos', 'Preparar times Dessastre Paradoxal',
          'Preparar times oficiais', 'Teste rapido: Pikachu x Eevee',
          "IA: #{@ai_profile == 'radical' ? 'Blue Radical' : @ai_profile == 'normal' ? 'Blue estrategica' : 'IA da base'}",
          'Mecanicas: Terastal / Dynamax / Mega / Z', 'Qualidade dos sprites', 'Sair do laboratorio'
        ])
        case choice
        when 0
          begin
            BlueBattleLab.validate_teams(@allies, @foes, @format)
          rescue ArgumentError => error
            BlueBattleLab.choose(error.message, ['Voltar']); next
          end
          result = BlueBattleLab.battle(@allies, @foes, false, @format, @ai_profile)
          BlueBattleLab.choose({1=>'Vitoria!',2=>'Derrota.',3=>'Batalha encerrada.',5=>'Empate.'}[result] || 'Teste encerrado.', ['Voltar ao laboratorio'])
        when 1
          selected = BlueBattleLab.choose('Formato de batalha', ['Individual / times de ate 6', 'Dupla / dois Pokemon em campo'], @format == 'double' ? 1 : 0)
          @format = selected == 1 ? 'double' : 'single' if selected >= 0
        when 2 then edit_team(@allies, 'Meu time')
        when 3 then edit_team(@foes, 'Time rival')
        when 4
          level = choose_level(@allies.first.level)
          [*@allies, *@foes].each { |p| set_level(p, level) } if level
        when 5 then @allies, @foes = BlueBattleLab.preset(true)
        when 6 then @allies, @foes = BlueBattleLab.preset
        when 7
          @format = 'single'
          @allies = [BlueBattleLab.build(:PIKACHU,10)]
          @foes = [BlueBattleLab.build(:EEVEE,10)]
        when 8
          if defined?(BlueRadicalAI)
            profiles=BlueRadicalAI::CONFIG['profiles']
            selected=BlueBattleLab.choose('IA do adversario / comparar comportamentos',profiles.values.map { |p| p['label'] },profiles.keys.index(@ai_profile) || 0)
            @ai_profile=profiles.keys[selected] if selected>=0
          end
        when 9 then BlueBattleOptions.mechanics_menu(:lab)
        when 10 then BlueBattleOptions.quality_menu
        else break
        end
      end
      $scene = nil
    rescue StandardError => error
      BlueBattleLab.log("ERROR | #{error.class}: #{error.message}\n#{error.backtrace.join("\n")}")
      raise unless BlueBattleLab::SMOKE
      $scene = nil
    end

    def label(pkmn)
      data = pkmn.species_data
      name = data.form > 0 ? "#{data.name} / #{data.form_name || data.form}" : data.name
      "#{name} / Nv.#{pkmn.level}"
    end

    def choose_level(current)
      result = BlueBattleLab.choose('Nivel (1 a 100)', (1..100).map { |n| "Nivel #{n}" }, current - 1)
      result >= 0 ? result + 1 : nil
    end

    def set_level(pkmn, level)
      pkmn.level = level
      pkmn.reset_moves
      pkmn.calc_stats
      pkmn.heal
    end

    def edit_team(team, title)
      loop do
        labels = (0...6).map { |i| "#{i+1}: #{team[i] ? label(team[i]) : '(adicionar Pokemon)'}" }
        slot = BlueBattleLab.choose("#{title} / primeiros entram em campo", labels + ['Voltar'])
        break if slot < 0 || slot >= 6
        unless team[slot]
          selected = BlueBattleLab.choose_species(team.first.species_data.id)
          next unless selected
          # Compact rosters: clicking any empty slot appends, never creates holes.
          team << BlueBattleLab.build(selected, team.first.level)
          slot = team.length - 1
        end
        edit_member(team, slot)
      end
    end

    def edit_member(team, slot)
      loop do
        mon = team[slot]
        item = mon.item_id ? GameData::Item.get(mon.item_id).name : '(nenhum)'
        choice = BlueBattleLab.choose(label(mon), [
          'Trocar Pokemon / forma', "Nivel: #{mon.level}", 'Editar quatro golpes',
          "Habilidade: #{mon.ability.name}", "Item: #{item}", 'Retirar item',
          'Mover para primeira posicao', 'Remover do time', 'Voltar'
        ])
        case choice
        when 0
          species = BlueBattleLab.choose_species(mon.species_data.id)
          team[slot] = BlueBattleLab.build(species, mon.level) if species
        when 1
          level = choose_level(mon.level)
          set_level(mon, level) if level
        when 2 then edit_moves(mon)
        when 3
          abilities = mon.getAbilityList
          selected = BlueBattleLab.choose('Escolha a habilidade', abilities.map { |a| GameData::Ability.get(a[0]).name })
          mon.ability_index = abilities[selected][1] if selected >= 0
        when 4
          selected = pbChooseItemList(mon.item_id)
          mon.item = selected if selected
        when 5 then mon.item = nil
        when 6
          team.unshift(team.delete_at(slot)); slot = 0
        when 7
          if team.length == 1
            BlueBattleLab.choose('Mantenha pelo menos um Pokemon no time.', ['Voltar'])
          else
            team.delete_at(slot); break
          end
        else break
        end
      end
    end

    def edit_moves(mon)
      loop do
        labels = (0...4).map { |i| "#{i+1}: #{mon.moves[i] ? mon.moves[i].name : '(vazio)'}" }
        slot = BlueBattleLab.choose('Golpes / lista livre para testes', labels + ['Voltar'])
        break if slot < 0 || slot >= 4
        if slot > mon.moves.length
          BlueBattleLab.choose('Preencha os espacos anteriores primeiro.', ['Voltar']); next
        end
        move = pbChooseMoveList(mon.moves[slot]&.id)
        mon.moves[slot] = Pokemon::Move.new(move) if move
      end
    end
  end
end
