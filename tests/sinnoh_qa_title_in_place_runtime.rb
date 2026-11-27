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
  return $new_game_choices.shift if $new_game_choices && message.include?("Em qual região deseja começar")
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
  pristine = "Data/sinnoh-experimental-tilesets-pristine.bin"
  File.binwrite(File.join(folder,pristine),
                File.binread(File.join(folder,"Data/Tilesets.rxdata")))
  hashes[pristine] = hashes["Data/Tilesets.rxdata"]
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

    # A normal New Game may never spawn the isolated Sinnoh QA process.
    # The separate Testar Sinnoh command is covered below.
    Object.const_set(:BlueRegionStart, Module.new)
    BlueRegionStart.define_singleton_method(:sinnoh_spawn) { @ready ? [442,10,8] : nil }
    BlueRegionStart.define_singleton_method(:request_initial) do |region|
      @requested = region
      region == "SINNOH" && !!sinnoh_spawn
    end
    BlueKantoTitle.singleton_class.alias_method(:original_launch_sinnoh, :launch_sinnoh)
    BlueKantoTitle.define_singleton_method(:launch_sinnoh) { raise "NORMAL_NEW_GAME_LAUNCHED_QA" }
    begin
      assert(BlueKantoTitle.start_region_names[4] == "Sinnoh (instalação necessária)",
             "missing shared region must be labeled as not installed")
      $new_game_choices = [4, BlueKantoTitle::START_REGIONS.length - 1]
      assert(BlueKantoTitle.choose_start_region == :cancel,
             "missing shared Sinnoh must return to the region menu")
      assert($messages.any? { |m| m.include?("coloque os dois ZIPs de origem junto ao Blue-Story.exe") },
             "missing shared Sinnoh must explain installation")
      BlueRegionStart.instance_variable_set(:@ready, true)
      assert(BlueKantoTitle.start_region_names[4] == "Sinnoh",
             "integrated Sinnoh must use the same plain name as other regions")
      $new_game_choices = [4]
      assert(BlueKantoTitle.choose_start_region == :integrated &&
             BlueRegionStart.instance_variable_get(:@requested) == "SINNOH",
             "Sinnoh must request shared New Game in the existing process")
    ensure
      $new_game_choices = nil
      $messages.clear
      BlueKantoTitle.singleton_class.alias_method(:launch_sinnoh, :original_launch_sinnoh)
      BlueKantoTitle.singleton_class.remove_method(:original_launch_sinnoh)
      Object.send(:remove_const,:BlueRegionStart)
    end
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

    # Real failure reported by the user: title opens but Barry's native
    # compilation may not have completed. Map QA must still be reachable
    # without claiming the battle is ready or inventing a compiled marker.
    file = "Data/sinnoh-experimental-compiled.txt"
    File.delete(file)
    File.write("Data/sinnoh-experimental-compile-request.txt", "a" * 64)
    assert(BlueKantoTitle.sinnoh_experimental_maps_ready?,
           "all 9 maps and save namespace must pass independently of Barry")
    assert(!BlueKantoTitle.sinnoh_experimental_ready?,
           "strict combined QA must NOT claim Barry compiled")
    assert(!BlueKantoTitle.sinnoh_experimental_barry_compiled?,
           "native Barry compile marker must remain absent")
    assert(BlueKantoTitle.launch_sinnoh == :blue_sinnoh_local_new_game,
           "Testar Sinnoh must allow map exploration with Barry pending")
    scene = PokemonLoad_Scene.new
    scene.pbStartScene(["New Game","Quit Game"], false, nil, nil, nil)
    assert(scene.pbChoose([], nil) == 0,
           "the QA menu must still route to same-window New Game")
    assert($messages.any? { |m| m.include?("batalha permanece bloqueada") },
           "player must be told Barry remains unavailable, no silent approval")
    File.delete("Data/sinnoh-experimental-compile-request.txt")
    File.write(file, "tampered")
    assert(!BlueKantoTitle.sinnoh_experimental_ready?,
           "invalid Barry compilation token must block new game")
    File.write(file, "a" * 64)
    # First-run native compiler may rewrite Tilesets after the signed-in-copy
    # SHA snapshot. Never silently accept/rebaseline the compiler output.
    tile_path = "Data/Tilesets.rxdata"
    pristine_path = "Data/sinnoh-experimental-tilesets-pristine.bin"
    pristine_bytes = File.binread(pristine_path)
    File.binwrite(tile_path, "compiler-generated different tilesets")
    assert(!BlueKantoTitle.sinnoh_experimental_maps_ready?,
           "first compiler rewrite must block until a fresh process")
    assert(BlueKantoTitle.sinnoh_qa_last_error.include?("Tilesets QA restaurado"),
           "QA explains trusted restore and restart without approving gameplay")
    assert(File.binread(tile_path) == pristine_bytes,
           "restored bytes must exactly match preverified original")
    assert(BlueKantoTitle.sinnoh_experimental_maps_ready?,
           "a fresh validation of restored exact bytes must succeed")

    # Blue-Story supervision: verified repair exits automatically; supervisor
    # reopens this same QA. Manual launches still show the old safe message.
    enabled_path = "Data/sinnoh-experimental-auto-restart-enabled.txt"
    request_path = "Data/sinnoh-experimental-auto-restart-request.txt"
    File.write(enabled_path, TOKEN + "\n")
    File.binwrite(tile_path, "compiler mutates on menu boot")
    caught_exit = false
    begin
      BlueKantoTitle.sinnoh_experimental_maps_ready?
    rescue SystemExit => e
      caught_exit = true
      assert(e.status == 0, "managed restart exits cleanly")
    end
    assert(caught_exit, "managed QA should exit automatically after verified repair")
    assert(File.binread(tile_path) == pristine_bytes,
           "auto-restart must leave original verified tile bytes")
    assert(File.read(request_path) == TOKEN + "\n" + Digest::SHA256.hexdigest(pristine_bytes) + "\n",
           "restart request must bind QA token and the original SHA")
    File.delete(request_path)
    File.delete(enabled_path)
    assert(BlueKantoTitle.sinnoh_experimental_maps_ready?,
           "verified copy remains valid for the new supervised game process")

    # Missing or altered backup must NEVER authorize repair/bypass.
    File.binwrite(tile_path, "compiler-generated different tilesets")
    File.binwrite(pristine_path, "tampered backup")
    assert(!BlueKantoTitle.sinnoh_experimental_maps_ready?,
           "corrupt pristine backup must fail closed")
    assert(BlueKantoTitle.sinnoh_qa_last_error.include?(tile_path),
           "corrupt backup must be diagnosed as a real checksum mismatch")
    assert(File.binread(tile_path) == "compiler-generated different tilesets",
           "invalid backup must not overwrite the QA tilesets")
    File.binwrite(pristine_path, pristine_bytes)
    File.binwrite(tile_path, pristine_bytes)

    File.write("Data/Map443.rxdata", "corrupted map")
    assert(!BlueKantoTitle.sinnoh_experimental_maps_ready?,
           "edited/corrupted map cannot pass map-only gate")
    assert(BlueKantoTitle.sinnoh_qa_last_error.include?("Data/Map443.rxdata"),
           "title must explain exact corrupted map")
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
# Dedicated regression for the embedded Windows Ruby that lacks json/digest.
# Construct a synthetic QA using standard Ruby fixtures, then REMOVE both
# modules and forbid subsequent gem loading. Integrity must still be enforced.
Dir.mktmpdir("blue-sinnoh-no-stdlib-") do |home|
  qa = File.join(home, "game-sinnoh-experimental-#{TOKEN}")
  setup_copy(qa)
  baseline = File.join(home, "sha256-abc.bin")
  File.binwrite(baseline, "abc")
  assert(BlueSinnohQA.sha256_file(baseline) ==
    "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad",
    "pure Ruby SHA-256 must match the NIST abc vector")
  File.binwrite(baseline, "")
  assert(BlueSinnohQA.sha256_file(baseline) ==
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "pure Ruby SHA-256 must match the empty file vector")
  File.binwrite(baseline, "a" * 10000)
  assert(BlueSinnohQA.sha256_file(baseline) == Digest::SHA256.file(baseline).hexdigest,
    "pure Ruby SHA-256 must match system SHA256 on multi-block data")
  sample = {"test" => [true, false, nil, -42, 1.5],
            "accent" => "São Paulo", "escaped" => "line\nslash\\value",
            "astral" => "🚀"}
  assert(BlueSinnohQA.parse_json(JSON.generate(sample)) == sample,
    "pure Ruby JSON reader should support Unicode, escapes, number and nested shapes")
  assert(BlueSinnohQA.parse_json('{"rocket":"\uD83D\uDE80"}') == {"rocket"=>"🚀"},
    "pure Ruby JSON reader should decode surrogate pairs")
  ['{"same":1,"same":2}', '{"open":true}junk', '{"bad":"\uD800"}',
   '{"too": [1,]}'].each do |bad|
    begin
      BlueSinnohQA.parse_json(bad)
      raise "SINNOH_QA_TITLE_TEST_FAILED: unsafe JSON accepted"
    rescue ArgumentError
      # Correct: manifest parser blocks tampering and malformed JSON.
    end
  end

  Object.send(:remove_const,:JSON) if defined?(JSON)
  Object.send(:remove_const,:Digest) if defined?(Digest)
  Kernel.prepend(Module.new do
    def require(name)
      raise LoadError, "EMBEDDED_RUBY_NO_#{name}" if %w[json digest digest/sha2].include?(name)
      super
    end
  end)
  assert(!defined?(JSON) && !defined?(Digest),
         "fixture must genuinely hide unavailable standard libraries")
  Dir.chdir(qa) do
    assert(BlueKantoTitle.sinnoh_experimental_maps_ready?,
      "missing json/digest MUST NOT prevent validating nine original RXDATA")
    assert(BlueKantoTitle.sinnoh_experimental_barry_compiled?,
      "missing json/digest MUST NOT prevent verifying real Barry marker hash")
    assert(BlueKantoTitle.launch_sinnoh == :blue_sinnoh_local_new_game,
      "Testar Sinnoh must start native New Game without bundled stdlib")
    File.write("Data/Map442.rxdata", "corrupted")
    assert(!BlueKantoTitle.sinnoh_experimental_maps_ready?,
      "pure Ruby fallback must still detect corrupted map SHA")
    assert(BlueKantoTitle.sinnoh_qa_last_error.include?("Data/Map442.rxdata"),
      "pure Ruby fallback must identify the exact altered file")
  end
end
puts "SINNOH_QA_STDLIB_FREE_JSON_SHA256_PASS"
puts "SINNOH_QA_TITLE_IN_PLACE_ROUTE_PASS"
