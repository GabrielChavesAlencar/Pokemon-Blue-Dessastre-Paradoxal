# Add regional test options to the main Game.exe load/new-game screen.
# Decades' Auto Multi Save changes the original PokemonLoadScreen method, so
# do not replace that controller: adapt only scene commands and return their
# ORIGINAL indexes. Existing save-slot navigation remains untouched.
module BlueKantoTitle
  LABEL = "Testar Kanto".freeze
  JOHTO_LABEL = "Testar Johto".freeze
  HOENN_LABEL = "Testar Hoenn".freeze
  SINNOH_LABEL = "Testar Sinnoh".freeze
  LAUNCHER = "KANTO_JOGAR_EXPERIMENTAL.bat".freeze
  JOHTO_LAUNCHER = "JOHTO_JOGAR_EXPERIMENTAL.bat".freeze
  SINNOH_LAUNCHER = "SINNOH_JOGAR_EXPERIMENTAL.bat".freeze

  def self.pilot?
    File.file?("Kanto pilot.json") || File.file?("Johto pilot.json") ||
      File.file?("Hoenn pilot.json") || File.file?("Sinnoh pilot.json")
  end

  def self.command_order(commands, show_continue)
    indices = (0...commands.length).to_a
    return indices unless !pilot? && (new_game = commands.index(_INTL("New Game")))
    ordered = []
    ordered << 0 if show_continue && new_game != 0
    ordered << new_game
    ordered << :blue_test_kanto
    ordered << :blue_test_johto
    ordered << :blue_test_hoenn
    ordered << :blue_test_sinnoh
    ordered.concat(indices.reject { |idx| ordered.include?(idx) })
    ordered
  end

  def self.launcher
    # The main executable must run from the installed Blue game directory.
    # Never run a launcher from an untrusted/current arbitrary directory.
    game_dir = File.expand_path(Dir.pwd)
    return nil unless File.file?(File.join(game_dir, "Game.exe"))
    return nil if pilot?
    script = File.expand_path("../" + LAUNCHER, game_dir)
    root = File.dirname(script)
    return nil unless File.file?(script) && File.file?(File.join(root, "scripts/regions/pilot.py"))
    [script, root]
  end

  # The Johto pilot will only be launchable when its own files exist.
  # Never reuse the Kanto launcher or its save profile for Johto.
  def self.johto_launcher
    game_dir = File.expand_path(Dir.pwd)
    return nil unless File.file?(File.join(game_dir, "Game.exe"))
    return nil if pilot?
    direct = regional_pilot("johto", "Johto", "JohtoQA", "blue-johto-qa-compiled.txt")
    return direct if direct
    script = File.expand_path("../" + JOHTO_LAUNCHER, game_dir)
    root = File.dirname(script)
    return nil unless File.file?(script) && File.file?(File.join(root, "scripts/regions/pilot_johto.py"))
    [script, root]
  end

  # Sinnoh must have an independent, project-owned pilot before it is launchable.
  # Never fall back to Kanto/Johto or start the unmodified main game.
  def self.sinnoh_launcher
    game_dir = File.expand_path(Dir.pwd)
    return nil unless File.file?(File.join(game_dir, "Game.exe"))
    return nil if pilot?
    direct = regional_pilot("sinnoh", "Sinnoh", "SinnohQA", "blue-sinnoh-compiled.txt")
    return direct if direct
    script = File.expand_path("../" + SINNOH_LAUNCHER, game_dir)
    root = File.dirname(script)
    return nil unless File.file?(script) && File.file?(File.join(root, "scripts/regions/pilot_sinnoh.py"))
    [script, root]
  end

  def self.windows?
    !!(RUBY_PLATFORM =~ /mswin|mingw|cygwin/i)
  end

  def self.launch
    unless windows?
      pbMessage(_INTL("O teste de Kanto pelo menu inicial está disponível no Windows."))
      return false
    end
    target = launcher
    unless target
      pbMessage(_INTL("O piloto de Kanto não foi localizado. Abra o projeto completo pelo Game.exe da pasta game, com KANTO_JOGAR_EXPERIMENTAL.bat na pasta anterior."))
      return false
    end
    unless pbConfirmMessage(_INTL("Abrir o Kanto experimental com saves separados? O menu do Decades será fechado."))
      return false
    end
    script, root = target
    begin
      # cmd.exe opens the preexisting, project-owned BAT without modifying the
      # installed Game.exe or its save slots. It builds/starts the isolated
      # pilot in .blue-work and collects a local manual test report on exit.
      pid = Process.spawn("cmd.exe", "/d", "/c", script, :chdir => root)
      Process.detach(pid)
      true
    rescue SystemCallError, ArgumentError, NotImplementedError => error
      pbMessage(_INTL("Não foi possível iniciar Kanto: {1}", error.message))
      false
    end
  end

  def self.launch_johto
    unless windows?
      pbMessage(_INTL("O teste de Johto pelo menu inicial estará disponível no Windows."))
      return false
    end
    target = johto_launcher
    unless target
      pbMessage(_INTL("Johto ainda está em preparação. O piloto experimental não foi instalado; Decades e Kanto continuam disponíveis."))
      return false
    end
    return false unless pbConfirmMessage(_INTL("Abrir o Johto experimental com saves separados? O menu principal será fechado."))
    script, root = target
    begin
      pid = if File.extname(script).casecmp?(".exe")
              Process.spawn([script, script], :chdir => root)
            else
              Process.spawn("cmd.exe", "/d", "/c", script, :chdir => root)
            end
      Process.detach(pid)
      true
    rescue SystemCallError, ArgumentError, NotImplementedError => error
      pbMessage(_INTL("Não foi possível iniciar Johto: {1}", error.message))
      false
    end
  end

  def self.regional_pilot(directory, region, desktop_folder, compiled)
    return nil if pilot? || !File.file?("Game.exe")
    game = File.expand_path(Dir.pwd)
    candidates = [File.expand_path("../.blue-work/#{directory}-pilot", game)]
    candidates << File.expand_path("../.blue-work/game-johto-qa", game) if region == "Johto"
    profile = ENV["USERPROFILE"]
    if profile && !profile.empty?
      candidates << File.expand_path("Documents/Codex/#{desktop_folder}", profile)
    end
    candidates.each do |folder|
      exe = File.join(folder, "Game.exe")
      next unless File.file?(exe) && File.realpath(folder) != File.realpath(game)
      next unless File.file?(File.join(folder, "#{region} pilot.json"))
      next unless File.file?(File.join(folder, "Data", compiled))
      return [exe, folder]
    end
    nil
  rescue SystemCallError, ArgumentError
    nil
  end

  def self.hoenn_launcher
    regional_pilot("hoenn", "Hoenn", "HoennQA", "blue-hoenn-compiled.txt")
  end

  def self.launch_hoenn
    unless windows?
      pbMessage(_INTL("O teste de Hoenn pelo menu inicial está disponível no Windows."))
      return false
    end
    target = hoenn_launcher
    unless target
      pbMessage(_INTL("O piloto de Hoenn ainda não está disponível. Monte e compile a cópia de teste antes de abrir por aqui."))
      return false
    end
    return false unless pbConfirmMessage(_INTL("Abrir o piloto de Hoenn com saves separados? O menu principal será fechado."))
    exe, folder = target
    pid = Process.spawn([exe, exe], :chdir => folder)
    Process.detach(pid)
    true
  rescue SystemCallError, ArgumentError, NotImplementedError => error
    pbMessage(_INTL("Não foi possível iniciar Hoenn: {1}", error.message))
    false
  end

  def self.launch_sinnoh
    unless windows?
      pbMessage(_INTL("O teste de Sinnoh pelo menu inicial estará disponível no Windows."))
      return false
    end
    target = sinnoh_launcher
    unless target
      pbMessage(_INTL("Sinnoh ainda não tem um piloto instalado. É preciso preparar os mapas de Twinleaf, Rota 201 e Sandgem antes de testar."))
      return false
    end
    return false unless pbConfirmMessage(_INTL("Abrir o Sinnoh experimental com saves separados? O menu principal será fechado."))
    script, root = target
    begin
      pid = if File.extname(script).casecmp?(".exe")
              Process.spawn([script, script], :chdir => root)
            else
              Process.spawn("cmd.exe", "/d", "/c", script, :chdir => root)
            end
      Process.detach(pid)
      true
    rescue SystemCallError, ArgumentError, NotImplementedError => error
      pbMessage(_INTL("Não foi possível iniciar Sinnoh: {1}", error.message))
      false
    end
  end

  module Scene
    def pbStartScene(commands, show_continue, trainer, stats, map_id)
      @blue_original_commands = commands
      @blue_kanto_order = BlueKantoTitle.command_order(commands, show_continue)
      @blue_kanto_commands = @blue_kanto_order.map do |item|
        case item
        when :blue_test_kanto then _INTL(BlueKantoTitle::LABEL)
        when :blue_test_johto then _INTL(BlueKantoTitle::JOHTO_LABEL)
        when :blue_test_hoenn then _INTL(BlueKantoTitle::HOENN_LABEL)
        when :blue_test_sinnoh then _INTL(BlueKantoTitle::SINNOH_LABEL)
        else commands[item]
        end
      end
      @blue_kanto_quit = commands.index(_INTL("Quit Game"))
      super(@blue_kanto_commands, show_continue, trainer, stats, map_id)
    end

    def pbChoose(commands, continue_idx = nil)
      return super(commands, continue_idx) unless @blue_kanto_order
      current_continue = @blue_kanto_order.index(continue_idx) || -1
      loop do
        # The original Auto Multi Save loader requires TWO arguments; the
        # original Essentials loader accepts one. Keep both contracts.
        selection = if continue_idx.nil?
                      super(@blue_kanto_commands)
                    else
                      super(@blue_kanto_commands, current_continue)
                    end
        return selection if selection.nil? || selection < 0
        original = @blue_kanto_order[selection]
        if [:blue_test_kanto, :blue_test_johto, :blue_test_hoenn, :blue_test_sinnoh].include?(original)
          launched = case original
                     when :blue_test_kanto then BlueKantoTitle.launch
                     when :blue_test_johto then BlueKantoTitle.launch_johto
                     when :blue_test_hoenn then BlueKantoTitle.launch_hoenn
                     when :blue_test_sinnoh then BlueKantoTitle.launch_sinnoh
                     end
          if launched
            # Allow the original load screen to dispose itself normally; its
            # Quit Game branch closes the main process after spawning pilot.
            return @blue_kanto_quit if @blue_kanto_quit
          end
          next
        end
        return original if original.is_a?(Integer)
      end
    end
  end

  def self.install
    return if @installed || !defined?(PokemonLoad_Scene)
    PokemonLoad_Scene.prepend(Scene)
    @installed = true
  end
end

BlueKantoTitle.install
