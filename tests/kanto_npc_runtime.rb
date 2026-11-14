# Standalone native Ruby regression: the *runtime* guard must speak pt-BR.
# No ROM, Windows, full Essentials engine or source FRLG archive is required.
require "fileutils"
require "tmpdir"

source = File.expand_path(ARGV.fetch(0))

class Game_Player; end
module MenuHandlers
  def self.add(*_args); end
end
def _INTL(source, *_args); source; end
def load_data(path); Marshal.load(File.binread(path)); end

$shown_dialogues = []
def pbMessage(value, *_args)
  $shown_dialogues << value
end

module BlueLocale
  @language = "en"
  REVIEWED = {
    "I absolutely forbid you from going through here!" =>
      "Está terminantemente proibido passar por aqui!"
  }.freeze
  def self.language=(value); @language = value; end
  def self.translate(value)
    @language == "pt-BR" ? REVIEWED.fetch(value, value) : value
  end
end

load source
raise "Kanto NPC bridge missing" unless BlueKantoPilot.respond_to?(:npc_dialogue)

Dir.mktmpdir("blue-kanto-npc-runtime-") do |path|
  Dir.chdir(path) do
    FileUtils.mkdir_p("Data")
    File.binwrite(
      "Data/blue-kanto-npc-dialogues.dat",
      Marshal.dump([
        [10, 7, ["I absolutely forbid you from going through here!"]],
        [24, 2, ["Welcome to Kanto!"]]
      ])
    )
    BlueLocale.language = "pt-BR"
    BlueKantoPilot.npc_dialogue(10, 7, 0)
    raise "pt-BR dialogue was not translated at talk time" unless
      $shown_dialogues.last == "Está terminantemente proibido passar por aqui!"

    BlueLocale.language = "en"
    BlueKantoPilot.npc_dialogue(10, 7, 0)
    raise "English dialogue was modified" unless
      $shown_dialogues.last == "I absolutely forbid you from going through here!"

    BlueLocale.language = "pt-BR"
    BlueKantoPilot.npc_dialogue(24, 2, 0)
    raise "Untranslated dialogue should keep the original" unless
      $shown_dialogues.last == "Welcome to Kanto!"

    begin
      BlueKantoPilot.npc_dialogue(10, 7, 1)
      raise "Invalid dialogue index was accepted"
    rescue RuntimeError => error
      raise if error.message == "Invalid dialogue index was accepted"
    end
  end
end
puts "PASS: live NPC callback uses pt-BR and restores English"
