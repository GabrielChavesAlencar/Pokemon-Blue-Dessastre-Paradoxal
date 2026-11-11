# Non-destructive procedural animation for authored static battle sprites.
# Designed for Essentials 21.1 / Decades [DBK] Animated Pokemon System.
module BlueProceduralAnimation
  MODES = {'off'=>'Desligado', 'light'=>'Leve', 'full'=>'Completo'}.freeze
  PROFILES = {
    :ground => [1.0, 0.6, 2.4, 3.2, 0.009],
    :quadruped => [1.0, 0.3, 2.7, 3.4, 0.008],
    :serpentine => [1.8, 0.8, 2.5, 3.1, 0.007],
    :floating => [1.5, 2.5, 2.2, 3.0, 0.004],
    :flying => [1.8, 2.8, 1.8, 2.7, 0.003],
    :aquatic => [1.5, 1.5, 2.8, 3.5, 0.005],
    :irregular => [1.3, 1.0, 2.3, 3.4, 0.010],
    :mechanical => [0.8, 0.8, 2.9, 4.0, 0.003]
  }.freeze
  ANATOMY = {
    :flying => [:CAVEFANG, :DREADCREST, :PRIMALGEOT, :WOOLYSTING, :FEAROW_1, :LEDIAN_1],
    :floating => [:BURIALGAZE, :MIASMIC, :PHANTOMIRE, :FOSSILHUSK, :DYNAMOTRODE, :MAGNETRIX],
    :serpentine => [:PRIMALVIPER, :PRIMALKORCH, :IRONINVERNOSE, :IRONMAELTROM, :ARBOK_1],
    :aquatic => [:ABYSSLURE, :CRAGGYSIPHON, :FOSSLTIDE, :JAGGEDMAW,
                 :PRIMALDRENAW, :PRIMALSEAKING, :PRIMATIZER, :TITANBALEEN,
                 :IRONCRUSHER, :MAGISCALE, :AMMNOID, :CEPHALONID, :TENTACRUEL_1, :WALREIN_1],
    :quadruped => [:DIRERUFF, :PRIMALPUNNY, :PRIMALTROPICAL, :RAMPAGEHORN,
                   :IRONFEASTER, :IRONLEPORIS, :IRONMATRIARCH, :PURUGLY_1, :MILTANK_1],
    :mechanical => [:IRONCRAWLER, :IRONCRUSHER, :IRONFEASTER, :IRONLEPORIS,
                    :IRONMATRIARCH, :IRONINVERNOSE, :IRONMAELTROM],
    :irregular => [:ANCESTRASH, :FETIDGULLET, :PRIMALMUK, :THORNBASTION,
                   :PRIMALSECT, :SWADLOADNE, :STUNDRIFT]
  }.freeze

  def self.mode
    value = $PokemonSystem && $PokemonSystem.blue_procedural_animation
    MODES.key?(value) ? value : 'light'
  end

  def self.enabled?
    mode != 'off' && $PokemonSystem && $PokemonSystem.animated_sprites.to_i == 0
  end

  def self.static_author?(pokemon, wrapper, substitute=false)
    return false unless enabled? && !substitute && pokemon && wrapper
    return false unless wrapper.respond_to?(:length) && wrapper.length == 1
    # 'Economico' mode stores a single frame even for animated source files.
    if wrapper.instance_variable_get(:@blue_lowres)
      count = wrapper.respond_to?(:blue_source_frames) ? wrapper.blue_source_frames : nil
      return false unless count == 1
    end
    data = pokemon.species_data
    data && data.flags.include?('DessastreParadoxal')
  end

  def self.profile(pokemon)
    id = pokemon.species_data.id
    ANATOMY.each do |preset, species|
      return PROFILES[preset] if species.include?(id)
    end
    PROFILES[:ground]
  end

  def self.sample(t, profile, back, strength)
    sway, bob, period_y, period_x, breath = profile
    perspective = back ? 0.72 : 1.0
    phase_y = (2.0 * Math::PI * t) / (period_y + (back ? 0.35 : 0.0))
    phase_x = (2.0 * Math::PI * t) / (period_x + (back ? 0.40 : 0.0))
    dx = (Math.sin(phase_x) * sway * strength * perspective).round
    dy = (Math.sin(phase_y) * bob * strength * perspective).round
    zoom = 1.0 + ((1.0 - Math.cos(phase_y)) / 2.0) * breath * strength * perspective
    [dx, dy, zoom]
  end

  module Battler
    def setPokemonBitmap(*args)
      blue_procedural_restore
      result = super
      @blue_procedural_active = BlueProceduralAnimation.static_author?(
        @pkmn, @_iconBitmap, @substitute
      )
      @blue_procedural_started = System.uptime
      @blue_procedural_hp = @battler.hp if @battler
      @blue_procedural_hit = nil
      result
    end

    def update
      blue_procedural_restore
      result = super
      begin
        blue_procedural_tick
      rescue StandardError => error
        blue_procedural_restore
        @blue_procedural_active = false
        warn("[Blue procedural] #{error.class}: #{error.message}") if $DEBUG
      end
      result
    end

    def dispose
      blue_procedural_restore unless disposed?
      super
    end

    private

    def blue_procedural_restore
      dx = @blue_procedural_dx || 0
      dy = @blue_procedural_dy || 0
      if dx != 0 || dy != 0
        @spriteXExtra = (@spriteXExtra || 0) - dx
        @spriteYExtra = (@spriteYExtra || 0) - dy
        @blue_procedural_dx = @blue_procedural_dy = 0
        self.x = self.x
        self.y = self.y
      end
      if @blue_procedural_zoom
        original, applied = @blue_procedural_zoom
        self.zoom_y = original if (self.zoom_y - applied).abs < 0.0001
        @blue_procedural_zoom = nil
      end
    end

    def blue_procedural_tick
      return unless @blue_procedural_active
      return unless BlueProceduralAnimation.static_author?(@pkmn, @_iconBitmap, @substitute)
      now = System.uptime
      if @battler
        hp = @battler.hp
        @blue_procedural_hit = now if @blue_procedural_hp && hp < @blue_procedural_hp
        @blue_procedural_hp = hp
      end
      return unless @spriteVisible && self.visible && self.opacity == 255
      return if @vanishMode && @vanishMode != 0
      return if @battler && @battler.fainted?
      return unless @selected == 0 || @selected == 1
      # Do not deform Pokeball release, mega transformations or move zoom.
      return unless (self.zoom_y - 1.0).abs < 0.001 && (self.zoom_x - 1.0).abs < 0.001
      return unless self.bitmap && !disposed?
      strength = BlueProceduralAnimation.mode == 'full' ? 1.0 : 0.55
      strength *= 0.6 if defined?(BlueSpriteQuality) && BlueSpriteQuality.mode == 'minimal'
      elapsed = [now - (@blue_procedural_started || now), 0.0].max
      dx, dy, zoom = BlueProceduralAnimation.sample(
        elapsed, BlueProceduralAnimation.profile(@pkmn), @index.even?, strength
      )
      if @blue_procedural_hit && BlueProceduralAnimation.mode == 'full'
        hit_time = now - @blue_procedural_hit
        if hit_time >= 0 && hit_time < 0.18
          dx += (@index.even? ? -1 : 1) * (3 * Math.sin(Math::PI * hit_time / 0.18)).round
        end
      end
      @blue_procedural_dx = dx
      @blue_procedural_dy = dy
      @spriteXExtra = (@spriteXExtra || 0) + dx
      @spriteYExtra = (@spriteYExtra || 0) + dy
      self.x = self.x
      self.y = self.y
      if BlueProceduralAnimation.mode == 'full'
        @blue_procedural_zoom = [self.zoom_y, self.zoom_y * zoom]
        self.zoom_y = @blue_procedural_zoom[1]
      end
    end
  end

  def self.install
    return if @installed
    Battle::Scene::BattlerSprite.prepend(Battler)
    @installed = true
  end
end
