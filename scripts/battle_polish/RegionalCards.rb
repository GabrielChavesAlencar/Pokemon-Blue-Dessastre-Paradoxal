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
      bitmap.font.color = color || Color.new(40, 68, 67)
      bitmap.draw_text(x, y, Graphics.width - x - 14, 23, line.to_s)
    end

    # The FireRed-inspired frame is drawn from primitives, without depending on
    # external artwork or changing the existing, native Decades Trainer Card.
    def card_frame(bitmap)
      width, height = Graphics.width, Graphics.height
      bitmap.fill_rect(0, 0, width, height, Color.new(53, 130, 114))
      bitmap.fill_rect(5, 5, width - 10, height - 10, Color.new(26, 63, 60))
      bitmap.fill_rect(11, 11, width - 22, height - 22, Color.new(225, 238, 225))
      bitmap.fill_rect(16, 16, width - 32, 52, Color.new(64, 106, 102))
    end

    def trainer_info
      trainer = $player
      return ["—", "—", "—", "—", "—"] unless trainer
      id = trainer.respond_to?(:public_ID) ? trainer.public_ID : "—"
      money = trainer.respond_to?(:money) ? trainer.money : 0
      owned = "—"
      if trainer.respond_to?(:pokedex) && trainer.pokedex &&
         trainer.pokedex.respond_to?(:owned_count)
        owned = trainer.pokedex.owned_count.to_s
      end
      seconds = (defined?($stats) && $stats && $stats.respond_to?(:play_time)) ?
                $stats.play_time.to_i : 0
      hours, minutes = seconds.divmod(3600)
      [trainer.name.to_s, id.to_s, "$#{money}", owned, "#{hours}h #{minutes / 60}m"]
    end

    def draw_badges(bitmap, data)
      width, height = Graphics.width, Graphics.height
      y = height - 80
      bitmap.fill_rect(18, y - 11, width - 36, 67, Color.new(184, 212, 198))
      write(bitmap, "INSÍGNIAS DE KANTO", 24, y - 10, 14)
      names = data[:milestones].first(8)
      return if names.empty?
      step = (width - 75) / 8.0
      names.each_with_index do |badge, index|
        x = (32 + step * index).to_i
        owned = data[:acquired].include?(badge)
        outline = owned ? Color.new(123, 87, 37) : Color.new(112, 135, 128)
        fill = owned ? Color.new(252, 218, 102) : Color.new(204, 218, 209)
        bitmap.fill_rect(x, y + 15, 27, 27, outline)
        bitmap.fill_rect(x + 3, y + 18, 21, 21, fill)
        bitmap.fill_rect(x + 8, y + 23, 11, 11,
                         owned ? Color.new(244, 166, 67) : Color.new(159, 186, 174))
      end
    end

    def draw(data)
      b = @sprites["card"].bitmap
      b.clear
      card_frame(b)
      pbSetSmallFont(b)
      label = @page == 0 ? (data[:current] == "KANTO" ? "KANTO" : "REGIÃO ATUAL") : "GERAL"
      write(b, "CARTÃO DE TREINADOR · #{label}", 24, 17, 19, Color.new(255, 253, 217))
      write(b, "Página #{@page + 1}/2  ·  ←/→ trocar cartão  ·  Voltar: sair", 24, 42, 13,
            Color.new(231, 242, 235))
      if @page == 0
        draw_local(b, data)
      else
        draw_global(b, data)
      end
    end

    def draw_local(bitmap, data)
      name, id, money, pokedex, playtime = trainer_info
      write(bitmap, "NOME", 27, 82, 15)
      write(bitmap, name, 152, 82, 18)
      write(bitmap, "DINHEIRO", 27, 113, 15)
      write(bitmap, money, 152, 113, 18)
      write(bitmap, "POKÉDEX", 27, 144, 15)
      write(bitmap, pokedex, 152, 144, 18)
      write(bitmap, "TEMPO", 27, 175, 15)
      write(bitmap, playtime, 152, 175, 18)
      write(bitmap, "ID: #{id}", 27, 206, 15)
      draw_badges(bitmap, data)
      write(bitmap, "#{data[:local]} insígnias · #{data[:global]} esmeraldas totais",
            24, Graphics.height - 104, 15)
      write(bitmap, "Dificuldade: #{BlueStory::LABELS[data[:stage]]}", 24,
            Graphics.height - 22, 14)
    end

    def draw_global(bitmap, data)
      write(bitmap, "TOTAL: #{data[:global]} esmeraldas  ·  " +
            "Dificuldade #{BlueStory::LABELS[data[:stage]]}", 22, 78, 19,
            Color.new(27, 105, 91))
      write(bitmap, "1 insígnia regional = 1 esmeralda global (sem duplicar).",
            22, 108, 14, Color.new(55, 98, 88))
      data[:rows].each_with_index do |(key, name, count, limit), index|
        y = 137 + index * 22
        marker = key == data[:current] ? "●" : " "
        text = key == "DECADES" ? "#{count} cristais" : "#{count}/#{limit} insígnias"
        write(bitmap, "#{marker} #{name}: #{text}", 25, y, 15,
              key == data[:current] ? Color.new(23, 121, 94) : Color.new(45, 75, 73))
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

  def self.kanto_active?
    return false unless defined?($PokemonGlobal) && $PokemonGlobal
    state = BlueRegions.snapshot
    state && state["current"] == "KANTO" && !BlueBattleOptions.battle_area?
  end

  # Clicking the game's original Trainer Card must actually open the requested
  # Kanto/Global pages. Extra pause entries alone were not sufficient.
  module NativeCard
    def pbStartScreen(*args)
      return super unless BlueRegionalCards.kanto_active?
      BlueRegionalCards.open(0)
    end
  end

  def self.install
    return if @installed
    if defined?(PokemonTrainerCardScreen) &&
       !PokemonTrainerCardScreen.ancestors.include?(NativeCard)
      PokemonTrainerCardScreen.prepend(NativeCard)
    end
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
