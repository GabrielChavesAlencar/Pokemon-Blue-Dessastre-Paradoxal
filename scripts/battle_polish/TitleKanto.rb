# Add "Testar Kanto" to the MAIN Game.exe's load/new-game screen.
# Decades' Auto Multi Save changes the original PokemonLoadScreen method, so
# do not replace that controller: adapt only scene commands and return their
# ORIGINAL indexes. Existing save-slot navigation remains untouched.
module BlueKantoTitle
  LABEL = "Testar Kanto".freeze
  LAUNCHER = "KANTO_JOGAR_EXPERIMENTAL.bat".freeze

  def self.pilot?
    File.file?("Kanto pilot.json")
  end

  def self.command_order(commands, show_continue)
    indices = (0...commands.length).to_a
    return indices unless !pilot? && (new_game = commands.index(_INTL("New Game")))
    ordered = []
    ordered << 0 if show_continue && new_game != 0
    ordered << new_game
    ordered << :blue_test_kanto
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

  module Scene
    def pbStartScene(commands, show_continue, trainer, stats, map_id)
      @blue_original_commands = commands
      @blue_kanto_order = BlueKantoTitle.command_order(commands, show_continue)
      @blue_kanto_commands = @blue_kanto_order.map do |item|
        item == :blue_test_kanto ? _INTL(BlueKantoTitle::LABEL) : commands[item]
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
        if original == :blue_test_kanto
          if BlueKantoTitle.launch
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
