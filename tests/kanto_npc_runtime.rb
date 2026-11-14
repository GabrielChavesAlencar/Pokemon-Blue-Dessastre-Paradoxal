# Standalone Ruby regression using the REAL BlueLocale and Kanto event bridge.
# No FRLG archive, ROM, game window, Windows or player save is needed.
require "fileutils"
require "tmpdir"

pilot_source = File.expand_path(ARGV.fetch(0))
locale_source = File.expand_path(ARGV.fetch(1))

class Game_Player; end
class PokemonSystem; end
module MessageTypes
  ABILITY_NAMES = 14
end
module GameData
  class Species; def self.each; end; end
  class Move; def self.each; end; end
  class Item; def self.each; end; end
  class Ability; def self.each; end; end
end
module MenuHandlers
  def self.add(*_args); end
end
def _INTL(source, *args); source.gsub(/\{(\d+)\}/) { args.fetch($1.to_i - 1).to_s }; end
def load_data(path); Marshal.load(File.binread(path)); end

$shown_dialogues = []
def pbMessage(value, *_args)
  $shown_dialogues << value
end

load locale_source
load pilot_source
raise "Kanto NPC bridge missing" unless BlueKantoPilot.respond_to?(:npc_dialogue)
$PokemonSystem = PokemonSystem.new

Dir.mktmpdir("blue-kanto-npc-runtime-") do |path|
  Dir.chdir(path) do
    FileUtils.mkdir_p("Data")
    original = "I absolutely forbid you from going through here!"
    formatted = '\b' + original
    combined = original + " This is private property!"
    File.binwrite("Data/blue-kanto-npc-dialogues.dat", Marshal.dump([
      [10, 7, [original, formatted, combined]],
      [24, 2, ["Welcome to Kanto!"]]
    ]))
    File.binwrite("Data/blue-pt-br.dat", Marshal.dump([
      [combined, "Está terminantemente proibido passar por aqui! Esta é uma propriedade privada!"]
    ]))
    $PokemonSystem.blue_locale = "pt-BR"
    option_help = "Interface and story language. Pokémon, item, move and ability names stay unchanged."
    raise "Selected Portuguese must translate the actual options help string" unless
      BlueLocale.translate(option_help) == "Traduz interface e história. Mantém nomes de Pokémon, itens, golpes e habilidades."
    BlueKantoPilot.npc_dialogue(10, 7, 0)
    raise "pt-BR guard was not translated at talk time" unless
      $shown_dialogues.last == "Está terminantemente proibido passar por aqui!"

    BlueKantoPilot.npc_dialogue(10, 7, 1)
    raise "Formatted FRLG NPC message was not translated with color preserved" unless
      $shown_dialogues.last == '\b' + "Está terminantemente proibido passar por aqui!"

    BlueKantoPilot.npc_dialogue(10, 7, 2)
    raise "Combined FRLG NPC message was not translated via catalog" unless
      $shown_dialogues.last == "Está terminantemente proibido passar por aqui! Esta é uma propriedade privada!"

    BlueKantoPilot.oak_warning
    raise "Oak PT-BR line missing" unless $shown_dialogues.last == "Oak: Ei! Espere um pouco!"
    raise "PT-BR placeholder lost" unless BlueKantoPilot.t("Hello, {1}!", "Olá, {1}!", "Red") == "Olá, Red!"

    $PokemonSystem.blue_locale = "en"
    BlueKantoPilot.oak_warning
    raise "Oak EN line missing after language change" unless $shown_dialogues.last == "Oak: Hey! Wait a second!"
    BlueKantoPilot.npc_dialogue(10, 7, 0)
    raise "English dialogue was modified" unless $shown_dialogues.last == original
    BlueKantoPilot.npc_dialogue(10, 7, 1)
    raise "Original formatted English dialogue was modified" unless $shown_dialogues.last == formatted

    $PokemonSystem.blue_locale = "pt-BR"
    BlueKantoPilot.npc_dialogue(24, 2, 0)
    raise "Untranslated dialogue should keep the original" unless $shown_dialogues.last == "Welcome to Kanto!"

    begin
      BlueKantoPilot.npc_dialogue(10, 7, 3)
      raise "Invalid dialogue index was accepted"
    rescue RuntimeError => error
      raise if error.message == "Invalid dialogue index was accepted"
    end
  end
end
puts "PASS: real BlueLocale translates plain, color-coded and combined guard speech in Kanto, preserving English"
