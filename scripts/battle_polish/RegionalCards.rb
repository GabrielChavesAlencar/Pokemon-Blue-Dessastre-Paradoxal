# Two separate Trainer Card views: local-region badges and global crystals.
# This is read-only UI: it never edits Decades' native badge switches.
module BlueRegionalCards
  def self.data(state = nil, native_count = nil, native_badges = nil)
    state ||= BlueRegions.snapshot
    return nil unless state
    native_badges ||= $player ? $player.badges : []
    native_count = $player ? $player.badge_count : 0 if native_count.nil?
    native_count = [native_count.to_i, 0].max
    total = BlueRegions.crystal_total(state, native_count)
    rows = BlueRegions.circuit.map do |key|
      earned = key == "DECADES" ? native_count :
        BlueRegions.local_achievements(state, key, native_badges).length
      [key, BlueRegions.info(key)["name"], earned, key == "DECADES" ? 18 : 8]
    end
    current = state["current"]
    achievements = current == "DECADES" ? [] :
      BlueRegions.local_achievements(state, current, native_badges)
    possible = current == "DECADES" ? [] : BlueRegions.info(current)["milestones"]
    {
      current: current,
      current_name: BlueRegions.info(current)["name"],
      local: rows.find { |entry| entry[0] == current }&.[](2) || 0,
      global: total,
      stage: total >= 11 ? 3 : (total >= 5 ? 2 : (total >= 2 ? 1 : 0)),
      rows: rows, milestones: possible,
      acquired: achievements
    }
  end

  class Scene
    def initialize(initial = 0)
      @page = initial == 1 ? 1 : 0
    end

    def write(bitmap, line, x, y, size = 17, color = nil)
      bitmap.font.size = size
      bitmap.font.color = color || Color.new(238, 248, 255)
      bitmap.draw_text(x, y, Graphics.width - x - 14, 23, line.to_s)
    end

    def draw(data)
      b = @sprites["card"].bitmap
      b.clear
      b.fill_rect(0, 0, Graphics.width, Graphics.height, Color.new(8, 23, 40))
      b.fill_rect(8, 8, Graphics.width - 16, 50, Color.new(22, 47, 73))
      pbSetSmallFont(b)
      label = @page == 0 ? (data[:current] == "KANTO" ? "KANTO · INSÍGNIAS" : "REGIÃO ATUAL") : "TODAS AS REGIÕES"
      write(b, "CARTÃO DE TREINADOR — #{label}", 18, 16, 19)
      write(b, "Página #{@page + 1}/2  ·  ←/→ mudar  ·  Voltar: sair", 18, 41, 13,
            Color.new(166, 202, 230))
      if @page == 0
        draw_local(b, data)
      else
        draw_global(b, data)
      end
    end

    def draw_local(bitmap, data)
      write(bitmap, data[:current_name], 18, 70, 22, Color.new(137, 204, 251))
      write(bitmap, "#{data[:local]} insígnias/cristais locais · #{data[:global]} esmeraldas totais",
            18, 103, 16)
      write(bitmap, "Dificuldade: #{BlueStory::LABELS[data[:stage]]}  ·  " +
            (data[:stage] == 3 ? "Nível oponente: 90%" : "Nível oponente: 70%"),
            18, 131, 15, Color.new(175, 214, 238))
      if data[:current] == "DECADES"
        write(bitmap, "Cristais do Decades: #{data[:local]} (contagem nativa).", 18, 180)
        write(bitmap, "Os cristais conquistados aqui também contam no total.", 18, 210, 15)
      elsif data[:milestones].empty?
        write(bitmap, "Essa região ainda não possui insígnias de ginásio.", 18, 184)
      else
        data[:milestones].each_with_index do |badge, i|
          y = 171 + (i / 2) * 42
          x = 18 + (i % 2) * (Graphics.width / 2)
          achieved = data[:acquired].include?(badge)
          bitmap.font.size = 15
          bitmap.font.color = achieved ? Color.new(140, 235, 180) : Color.new(148, 163, 180)
          bitmap.draw_text(x, y, Graphics.width / 2 - 25, 27,
                           "#{achieved ? '✓' : '○'} #{badge.gsub('_', ' ')}")
        end
      end
    end

    def draw_global(bitmap, data)
      write(bitmap, "TOTAL: #{data[:global]} esmeraldas  ·  " +
            "Dificuldade #{BlueStory::LABELS[data[:stage]]}", 18, 71, 19,
            Color.new(139, 211, 250))
      write(bitmap, "1 insígnia regional = 1 esmeralda global (sem duplicar).",
            18, 103, 14, Color.new(171, 205, 234))
      data[:rows].each_with_index do |(key, name, count, limit), index|
        y = 137 + index * 22
        marker = key == data[:current] ? "●" : " "
        text = key == "DECADES" ? "#{count} cristais" : "#{count}/#{limit} insígnias"
        write(bitmap, "#{marker} #{name}: #{text}", 20, y, 15,
              key == data[:current] ? Color.new(151, 222, 255) : Color.new(231, 239, 249))
      end
    end

    def run
      @viewport = Viewport.new(0, 0, Graphics.width, Graphics.height)
      @viewport.z = 999999
      @sprites = {"card" => BitmapSprite.new(Graphics.width, Graphics.height, @viewport)}
      data = BlueRegionalCards.data
      return unless data
      draw(data)
      Graphics.transition(0)
      loop do
        Graphics.update
        Input.update
        break if Input.trigger?(Input::BACK)
        if Input.trigger?(Input::RIGHT) || Input.trigger?(Input::LEFT) || Input.trigger?(Input::USE)
          @page = 1 - @page
          draw(BlueRegionalCards.data || data)
        end
      end
    ensure
      @sprites&.each_value { |sprite| sprite.dispose }
      @viewport&.dispose
    end
  end

  def self.open(page = 0)
    Scene.new(page).run
  end

  def self.install
    return if @installed
    MenuHandlers.add(:pause_menu, :blue_regional_trainer_cards, {
      "name" => _INTL("Cartão do treinador · 2 páginas"),
      "order" => 50,
      "condition" => proc { |_menu|
        state = BlueRegions.snapshot
        BlueStory.story? && state && state["current"] != "KANTO" &&
          !BlueBattleOptions.battle_area?
      },
      "effect" => proc do |menu|
        menu.pbHideMenu
        pbFadeOutIn { BlueRegionalCards.open }
        menu.pbShowMenu
        menu.pbRefresh
        false
      end
    })
    # The Kanto pilot does not necessarily use the Decades Story Mode
    # switch. Expose BOTH real cards directly, each with its own initial page.
    # No change to the native Decades Trainer Card or badge switches.
    MenuHandlers.add(:pause_menu, :blue_kanto_trainer_card, {
      "name" => _INTL("Cartão de Kanto · insígnias"), "order" => 49,
      "condition" => proc { |_menu|
        state = BlueRegions.snapshot
        state && state["current"] == "KANTO" && !BlueBattleOptions.battle_area?
      },
      "effect" => proc do |menu|
        menu.pbHideMenu
        pbFadeOutIn { BlueRegionalCards.open(0) }
        menu.pbShowMenu
        menu.pbRefresh
        false
      end
    })
    MenuHandlers.add(:pause_menu, :blue_global_trainer_card, {
      "name" => _INTL("Cartão global · esmeraldas"), "order" => 50,
      "condition" => proc { |_menu|
        state = BlueRegions.snapshot
        state && state["current"] != "DECADES" && !BlueBattleOptions.battle_area?
      },
      "effect" => proc do |menu|
        menu.pbHideMenu
        pbFadeOutIn { BlueRegionalCards.open(1) }
        menu.pbShowMenu
        menu.pbRefresh
        false
      end
    })
    @installed = true
  end
end
