# Original Blue UI adapters, shared by the campaign and the opt-in lab.
module BlueLabPointer
  class << self
    attr_accessor :keys, :claimed
    def enabled?; !BlueBattleLab::SMOKE || @testing_campaign; end
    # Some Essentials menus update their windows BEFORE Input.update; others
    # update them afterwards. Carry an unread click across one update only.
    def reset
      @frame ||= 0
      self.keys = (keys || {}).select { |key,born| born==@frame && !(@read || {})[key] }
      @frame += 1
      @read={};self.claimed=false
    end
    def key?(key)
      return false unless (keys || {}).key?(key)
      (@read ||= {})[key]=true
      true
    end
    def emit(key)
      self.keys ||= {}
      self.keys[key] = @frame || 0
      self.claimed = true
    end
    def position; Mouse.getMousePos; end
    def inside?(point, x, y, width, height)
      point && width > 0 && height > 0 && point[0] >= x && point[0] < x + width && point[1] >= y && point[1] < y + height
    end
    def origin(sprite)
      x = sprite.x; y = sprite.y
      viewport = sprite.viewport if sprite.respond_to?(:viewport)
      if viewport
        x += viewport.rect.x - viewport.ox
        y += viewport.rect.y - viewport.oy
      end
      [x, y]
    end
    def hit_sprite?(sprite, point)
      return false unless sprite && !sprite.disposed? && sprite.visible && sprite.bitmap
      x, y = origin(sprite)
      inside?(point, x - sprite.ox * sprite.zoom_x, y - sprite.oy * sprite.zoom_y,
              sprite.src_rect.width * sprite.zoom_x, sprite.src_rect.height * sprite.zoom_y)
    end
  end
end

module BlueLabInput
  def update
    BlueLabPointer.reset
    super
  end
  def trigger?(key)
    return true if BlueLabPointer.enabled? && BlueLabPointer.key?(key)
    return true if BlueLabPointer.enabled? && key == Input::BACK && super(Input::MOUSERIGHT)
    super
  end
end

# Item rectangles come from the actual scrolled window, including its borders.
module BlueLabListMouse
  def update
    super
    return unless BlueLabPointer.enabled? && visible && active && !@ignore_input
    return if BlueLabPointer.claimed || !Input.trigger?(Input::MOUSELEFT)
    point = BlueLabPointer.position
    x0, y0 = BlueLabPointer.origin(self)
    return unless BlueLabPointer.inside?(point, x0 + startX, y0 + startY, width - borderX, height - borderY)
    (top_item...[itemCount, top_item + page_item_max].min).each do |i|
      rect = itemRect(i)
      next unless BlueLabPointer.inside?(point, x0 + startX + rect.x, y0 + startY + rect.y, rect.width, rect.height)
      self.index = i
      BlueLabPointer.emit(Input::USE)
      break
    end
  end
end

module BlueLabBattleMenuMouse
  def update
    super
    return unless BlueLabPointer.enabled? && visible && !BlueLabPointer.claimed
    return unless Input.trigger?(Input::MOUSELEFT)
    point = BlueLabPointer.position
    if is_a?(Battle::Scene::FightMenu)
      if @mode > 0 && BlueLabPointer.hit_sprite?(@megaButton, point)
        BlueLabPointer.emit(Input::ACTION); return
      end
      if @shiftMode > 0 && BlueLabPointer.hit_sprite?(@shiftButton, point)
        BlueLabPointer.emit(Input::SPECIAL); return
      end
    end
    (@buttons || []).each_with_index do |button, i|
      next unless BlueLabPointer.hit_sprite?(button, point)
      next if is_a?(Battle::Scene::FightMenu) && !@battler.moves[i]&.id
      next if is_a?(Battle::Scene::TargetMenu) && nil_or_empty?(@texts[i])
      self.index = i
      BlueLabPointer.emit(Input::USE)
      BlueBattleLab.log("MOUSE | #{self.class} index=#{i}") if BlueBattleLab::ACTIVE
      break
    end
  end
end

module BlueLabPartyMouse
  def pbChoosePokemon(*args)
    @blue_lab_choosing = true
    super
  ensure
    @blue_lab_choosing = false
  end
  def update
    super
    return unless @blue_lab_choosing && BlueLabPointer.enabled? && !BlueLabPointer.claimed
    return unless Input.trigger?(Input::MOUSELEFT)
    point = BlueLabPointer.position
    @party.each_index do |i|
      panel = @sprites["pokemon#{i}"]
      next unless panel && panel.visible
      x, y = BlueLabPointer.origin(panel)
      next unless BlueLabPointer.inside?(point, x, y, Graphics.width / 2, 96)
      @activecmd = i
      pbRefresh
      BlueLabPointer.emit(Input::USE)
      BlueBattleLab.log("MOUSE | party index=#{i}") if BlueBattleLab::ACTIVE
      break
    end
  end
end

module BlueTextMouse
  def update
    super
    return unless BlueLabPointer.enabled? && visible && !BlueLabPointer.claimed
    return unless Input.trigger?(Input::MOUSELEFT)
    x0,y0=BlueLabPointer.origin(self)
    BlueLabPointer.emit(Input::USE) if BlueLabPointer.inside?(BlueLabPointer.position,x0,y0,width,height)
  end
end

module BlueBattleLab
  def self.install_interface
    # Restore the engine's own interpolation, numbers, colors and DBK triggers.
    klass = Battle::Scene::PokemonDataBox
    klass.send(:remove_const, :HP_BAR_CHANGE_TIME)
    klass.const_set(:HP_BAR_CHANGE_TIME, 1.0)
    return if @interface_installed
    Input.singleton_class.prepend(BlueLabInput)
    SpriteWindow_Selectable.prepend(BlueLabListMouse)
    Battle::Scene::MenuBase.prepend(BlueLabBattleMenuMouse)
    PokemonParty_Scene.prepend(BlueLabPartyMouse)
    Window_AdvancedTextPokemon.prepend(BlueTextMouse)
    @interface_installed = true
  end

  # A scrollable menu with mouse-accessible paging and Back controls.
  def self.choose(title, commands, default = 0)
    log("MENU_OPEN | #{title}")
    viewport = Viewport.new(0, 0, Graphics.width, Graphics.height)
    viewport.z = 99999
    header = Window_UnformattedTextPokemon.newWithSize(title, 0, 0, Graphics.width, 64, viewport)
    list = Window_CommandPokemon.newWithSize(commands, 0, 64, Graphics.width, Graphics.height - 112, viewport)
    list.index = default.clamp(0, commands.length - 1)
    footer = BitmapSprite.new(Graphics.width, 48, viewport)
    footer.y = Graphics.height - 48
    pbSetSmallFont(footer.bitmap)
    labels = ['Pagina anterior', 'Proxima pagina', 'Voltar / Esc']
    labels.each_with_index { |label,i| footer.bitmap.draw_text(i * Graphics.width / 3, 0, Graphics.width / 3, 48, label, 1) }
    log('MENU_DRAWN | header, list and footer created')
    # Main freezes the frame before entering the title/lab scene. Release it
    # after the menu exists, before native input queries the rendered viewport.
    Graphics.transition(0)
    Input.update
    first_frame=true
    loop do
      Graphics.update; Input.update; list.update
      if first_frame
        log('MENU_FRAME | graphics and input updated')
        check_live_menu_pixels if @test_live_menu_at
        first_frame=false
      end
      if Input.trigger?(Input::MOUSELEFT) && !BlueLabPointer.claimed
        point = BlueLabPointer.position
        if point && point[1] >= Graphics.height - 48
          section = point[0] * 3 / Graphics.width
          return -1 if section == 2
          list.index = (list.index + (section == 0 ? -list.page_item_max : list.page_item_max)).clamp(0, commands.length - 1)
        end
      end
      return -1 if Input.trigger?(Input::BACK)
      if Input.trigger?(Input::USE)
        pbPlayDecisionSE
        return list.index
      end
    end
  ensure
    list&.dispose; header&.dispose; footer&.dispose; viewport&.dispose
    Input.update
  end
end
