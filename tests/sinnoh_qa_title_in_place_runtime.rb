# Native-ish Ruby title routing fixture for J12-E private Sinnoh QA.
# No Game.exe/ROM, no real save data, no installed maps or rights approvals.
require "json"
require "digest"
require "tmpdir"
require "fileutils"

ROOT = File.expand_path("..", __dir__)
SOURCE = File.join(ROOT, "scripts/battle_polish/TitleKanto.rb")
TOKEN = "df40e0c369e2"
START = [442, 10, 8].freeze

module BlueSinnohExperimental
  TOKEN = "df40e0c369e2".freeze
  START = [442, 10, 8].freeze
end

$messages = []
def _INTL(str, *args)
  args.empty? ? str : format(str, *args)
end
def pbMessage(message, *args)
  $messages << message
  0
end
def pbConfirmMessage(*_args)
  raise "UNEXPECTED_CONFIRMATION_OR_PROCESS_SPAWN"
end

class PokemonLoad_Scene
  attr_reader :test_scene_args
  def pbStartScene(*args)
    @test_scene_args = args
  end
  def pbChoose(*_args)
    4  # Testar Sinnoh in the 6-item augmented title menu.
  end
end

load SOURCE
def assert(test, message)
  raise "SINNOH_QA_TITLE_TEST_FAILED: #{message}" unless test
end

def setup_copy(folder)
  FileUtils.mkdir_p(folder)
  profile = {
    "title" => "Sinnoh QA " + TOKEN,
    "dataPathApp" => "Sinnoh-QA-" + TOKEN,
    "dataPathOrg" => "Dessastre-Sinnoh-QA-" + TOKEN
  }
  jsonc = profile.merge("windowTitle" => profile["title"])
  File.write(File.join(folder, "mkxp.json"), JSON.generate(jsonc))
  File.write(File.join(folder, "Game.ini"), "Title=#{profile["title"]}\n")
  File.write(File.join(folder, "Game.exe"), "fake-non-executable")
  FileUtils.mkdir_p(File.join(folder, "Data"))
  maps = {"SINNOH_PLAYER_BEDROOM" => 442}
  %w[SINNOH_PLAYER_HOUSE_1F SINNOH_BARRY_HOUSE SINNOH_LAKE_VERITY
     SINNOH_PROFESSOR_ROWAN_LABORATORY SINNOH_TWINLEAF_TOWN
     SINNOH_ROUTE_201 SINNOH_SANDGEM_TOWN SINNOH_ROUTE_202].each_with_index do |key,i|
    maps[key] = 443+i
  end
  filenames = ["Data/MapInfos.rxdata", "Data/Tilesets.rxdata"] +
              maps.values.map { |id| "Data/Map%03d.rxdata" % id }
  hashes = {}
  filenames.each do |filename|
    content = "synthetic Ruby Marshal fixture only: #{filename}"
    File.write(File.join(folder, filename), content)
    hashes[filename] = Digest::SHA256.hexdigest(content)
  end
  proof = "a" * 64
  File.write(File.join(folder, "Data/sinnoh-experimental-compiled.txt"), proof)
  manifest = {
    "schema" => 1, "region" => "SINNOH",
    "mode" => "SINNOH_EXPERIMENTAL_TEST_COPY_NOT_NATIVE_APPROVED",
    "profile_token" => TOKEN, "start" => START,
    "save_profile" => profile, "mapids" => maps,
    "file_sha256" => hashes, "compile_token" => proof,
    "main_game_modified" => false, "personal_saves_copied" => false,
    "r09_native_qa_executed" => 0,
    "runtime_playable_verified" => false
  }
  File.write(File.join(folder, "sinnoh-experimental-qa.json"), JSON.pretty_generate(manifest))
end

Dir.mktmpdir("blue-sinnoh-qa-title-") do |home|
  main = File.join(home, "game")
  FileUtils.mkdir_p(main)
  Dir.chdir(main) do
    assert(!BlueKantoTitle.sinnoh_experimental_copy?,
           "main game cannot qualify as private QA")
    assert(!BlueKantoTitle.sinnoh_experimental_ready?,
           "main game cannot pass QA ready gate")
  end

  qa = File.join(home, "game-sinnoh-experimental-#{TOKEN}")
  setup_copy(qa)
  Dir.chdir(qa) do
    assert(BlueKantoTitle.sinnoh_experimental_copy?,
           "QA folder+token+plugin must be recognized")
    assert(BlueKantoTitle.sinnoh_experimental_ready?,
           "9 synthetic map files, compiled proof, profile and checksums should pass")
    assert(BlueKantoTitle.launch_sinnoh == :blue_sinnoh_local_new_game,
           "Testar Sinnoh must mean local new game, never a secondary EXE")
    assert(BlueKantoTitle.command_order(["New Game","Quit Game"], false).include?(:blue_test_sinnoh),
           "QA Testar Sinnoh command remains on title")
    scene = PokemonLoad_Scene.new
    scene.pbStartScene(["New Game","Quit Game"], false, nil, nil, nil)
    assert(scene.pbChoose([], nil) == 0,
           "selecting Testar Sinnoh must return the native New Game index")
    assert($messages.empty?, "verified QA must not display old pilot missing message")

    file = "Data/sinnoh-experimental-compiled.txt"
    File.write(file, "tampered")
    assert(!BlueKantoTitle.sinnoh_experimental_ready?,
           "invalid Barry compilation token must block new game")
    File.write(file, "a" * 64)
    File.write("Data/Map443.rxdata", "corrupted map")
    assert(!BlueKantoTitle.sinnoh_experimental_ready?,
           "edited/corrupted map cannot be accepted as verified QA")
  end

  fake = File.join(home, "wrong-place")
  setup_copy(fake)
  Dir.chdir(fake) do
    assert(!BlueKantoTitle.sinnoh_experimental_copy?,
           "QA marker copied into wrong folder must not authorize launch")
  end
end
puts "SINNOH_QA_TITLE_IN_PLACE_ROUTE_PASS"
