# Blue Keyboard Controls: in-game options, WASD defaults and separate persistence.
# Uses FL's Set the Controls Screen 1.2.8 (MIT-0) for physical keyboard/gamepad input.
unless File.file?('Data/blue-mobile.txt')
module BlueKeyboardDefaults
  def default_controls
    controls = super
    # Keep arrows, but reserve A/S for movement rather than menu scrolling.
    controls.reject! do |control|
      (control.control_action == "Scroll Up" && control.key_name == "A") ||
        (control.control_action == "Scroll Down" && control.key_name == "S")
    end
    controls.concat(ControlConfig.multiple_new("Up", ["W"]))
    controls.concat(ControlConfig.multiple_new("Left", ["A"]))
    controls.concat(ControlConfig.multiple_new("Down", ["S"]))
    controls.concat(ControlConfig.multiple_new("Right", ["D"]))
    controls.reject! { |control| control.control_action == "Ready Menu" && control.key_name == "D" }
    controls.concat(ControlConfig.multiple_new("Ready Menu", ["R"]))
    controls.concat(ControlConfig.multiple_new("Scroll Up", ["Q"]))
    controls.concat(ControlConfig.multiple_new("Scroll Down", ["E"]))
    controls
  end
end
Keys.singleton_class.prepend(BlueKeyboardDefaults)

module BlueKeyboardStorage
  FILE_NAME = "blue-keyboard-controls.txt"
  def self.path
    directory = (defined?(System) && System.respond_to?(:data_directory) &&
                 File.directory?(System.data_directory)) ? System.data_directory : Dir.pwd
    File.join(directory, FILE_NAME)
  end
  def self.allowed_codes
    codes = Keys::KEYBOARD_LIST.values
    if Input.const_defined?(:Controller)
      codes += Keys::GAMEPAD_LIST.values.map { |code| code + Input::GAMEPAD_OFFSET }
      codes += Keys::GAMEPAD_AXIS_LIST.values.map { |code| code + Input::AXIS_OFFSET }
    end
    codes
  end
  def self.load
    return nil unless File.file?(path)
    actions = Keys.default_controls.map(&:control_action).uniq
    codes = allowed_codes
    lines = File.readlines(path, encoding: "UTF-8").map(&:strip).reject(&:empty?)
    return nil if lines.empty? || lines.length > actions.length * SetControls::MAX_KEYS_PER_ACTION
    controls = lines.map do |line|
      parts = line.split("\t", 2)
      return nil unless parts.length == 2 && actions.include?(parts[0]) && parts[1].match?(/\A\d+\z/)
      code = parts[1].to_i
      return nil unless codes.include?(code)
      ControlConfig.new_by_code(parts[0], code)
    end
    return nil unless actions.all? { |action| controls.any? { |row| row.control_action == action } }
    return nil unless controls.map(&:key_code).uniq.length == controls.length
    controls
  rescue SystemCallError, ArgumentError, EncodingError
    nil
  end
  def self.save(controls)
    allowed = allowed_codes
    actions = Keys.default_controls.map(&:control_action).uniq
    return false unless controls.all? { |c| actions.include?(c.control_action) && allowed.include?(c.key_code) }
    return false unless actions.all? { |action| controls.any? { |c| c.control_action == action } }
    destination = path
    temp = destination + ".tmp"
    File.open(temp, "w:UTF-8") do |file|
      controls.each { |control| file.write("#{control.control_action}\t#{control.key_code}\n") }
    end
    File.delete(destination) if File.file?(destination)
    File.rename(temp, destination)
    true
  rescue SystemCallError, ArgumentError
    false
  end
end

class PokemonSystem
  alias_method :blue_original_game_controls, :game_controls
  alias_method :blue_original_game_controls_set, :game_controls=
  def game_controls
    unless instance_variable_defined?(:@blue_keyboard_loaded)
      @blue_keyboard_loaded = true
      saved = BlueKeyboardStorage.load
      @game_controls = saved if saved
    end
    blue_original_game_controls
  end
  def game_controls=(controls)
    blue_original_game_controls_set(controls)
    pbMessage("Aviso: nao foi possivel gravar as teclas. Verifique as permissoes do Windows.") unless BlueKeyboardStorage.save(controls)
  end
end

# The stock options screen does not have buttons. A specialized EnumOption entry
# opens the full key capture interface when the player presses Confirm on it.
class BlueKeyboardOption < EnumOption; end
MenuHandlers.add(:options_menu, :blue_keyboard_controls, {
  "name"        => "Teclas",
  "order"       => 125,
  "type"        => BlueKeyboardOption,
  "parameters"  => ["Editar"],
  "description" => "Aperte confirmar para editar movimento, confirmar, voltar, menu e atalhos. Nao precisa de F1.",
  "get_proc"    => proc { 0 },
  "set_proc"    => proc { |_value, _scene| }
})
module BlueKeyboardOptionWindow
  def update
    super
    return unless active && index < @options.length && @options[index].is_a?(BlueKeyboardOption)
    return unless Input.trigger?(Input::USE)
    pbPlayDecisionSE
    SetControls.open_ui
    refresh
  end
end
Window_PokemonOption.prepend(BlueKeyboardOptionWindow)
end
