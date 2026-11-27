# Add regional test options to the main Game.exe load/new-game screen.
# Decades' Auto Multi Save changes the original PokemonLoadScreen method, so
# do not replace that controller: adapt only scene commands and return their
# ORIGINAL indexes. Existing save-slot navigation remains untouched.
# The embedded Ruby interpreter used by some Windows Game.exe builds does not
# bundle Ruby's json/digest gems. This reader and SHA-256 verifier are self-
# contained: QA integrity must never silently depend on host Ruby packages.
# No eval, YAML.load, Marshal.load from manifest, shell commands or gem loading.
module BlueSinnohQA
  MASK32 = 0xffffffff
  SHA256_INITIAL = [
    0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
    0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19
  ].freeze
  SHA256_K = %w[
    428a2f98 71374491 b5c0fbcf e9b5dba5 3956c25b 59f111f1 923f82a4 ab1c5ed5
    d807aa98 12835b01 243185be 550c7dc3 72be5d74 80deb1fe 9bdc06a7 c19bf174
    e49b69c1 efbe4786 0fc19dc6 240ca1cc 2de92c6f 4a7484aa 5cb0a9dc 76f988da
    983e5152 a831c66d b00327c8 bf597fc7 c6e00bf3 d5a79147 06ca6351 14292967
    27b70a85 2e1b2138 4d2c6dfc 53380d13 650a7354 766a0abb 81c2c92e 92722c85
    a2bfe8a1 a81a664b c24b8b70 c76c51a3 d192e819 d6990624 f40e3585 106aa070
    19a4c116 1e376c08 2748774c 34b0bcb5 391c0cb3 4ed8aa4a 5b9cca4f 682e6ff3
    748f82ee 78a5636f 84c87814 8cc70208 90befffa a4506ceb bef9a3f7 c67178f2
  ].map { |hex| hex.to_i(16) }.freeze

  def self.rotr(value, amount)
    ((value >> amount) | (value << (32 - amount))) & MASK32
  end

  def self.sha256_block(state, block)
    words = block.unpack("N16")
    (16...64).each do |i|
      a = words[i-15]
      c = words[i-2]
      s0 = rotr(a,7) ^ rotr(a,18) ^ (a >> 3)
      s1 = rotr(c,17) ^ rotr(c,19) ^ (c >> 10)
      words << ((words[i-16] + s0 + words[i-7] + s1) & MASK32)
    end
    a,b,c,d,e,f,g,h = state
    64.times do |i|
      s1 = rotr(e,6) ^ rotr(e,11) ^ rotr(e,25)
      choice = (e & f) ^ ((~e) & g)
      t1 = (h + s1 + choice + SHA256_K[i] + words[i]) & MASK32
      s0 = rotr(a,2) ^ rotr(a,13) ^ rotr(a,22)
      majority = (a & b) ^ (a & c) ^ (b & c)
      t2 = (s0 + majority) & MASK32
      h,g,f,e,d,c,b,a = g,f,e,(d+t1)&MASK32,c,b,a,(t1+t2)&MASK32
    end
    [a,b,c,d,e,f,g,h].each_with_index do |word,i|
      state[i] = (state[i] + word) & MASK32
    end
  end

  def self.sha256_file(path)
    raise ArgumentError, "QA_HASH_INVALID_FILE" unless File.file?(path) && !File.symlink?(path)
    state = SHA256_INITIAL.dup
    buffer = "".b
    length = 0
    File.open(path,"rb") do |file|
      while (part = file.read(32768))
        length += part.bytesize
        raise ArgumentError, "QA_HASH_FILE_TOO_LARGE" if length > 256*1024*1024
        buffer << part
        while buffer.bytesize >= 64
          sha256_block(state,buffer.slice!(0,64))
        end
      end
    end
    buffer << "\x80".b
    buffer << "\x00".b until (buffer.bytesize % 64) == 56
    bit_length = length * 8
    buffer << [(bit_length >> 32) & MASK32, bit_length & MASK32].pack("N2")
    while buffer.bytesize >= 64
      sha256_block(state,buffer.slice!(0,64))
    end
    state.pack("N8").unpack("H*").first
  end

  # Restore a first-boot compiler rewrite ONLY from an exact preverified copy.
  # This never changes the manifest, trusts a newly calculated hash, or
  # approves maps/Bary. Caller must require a new Game.exe process because
  # the current Ruby runtime may already have loaded the changed tilesets.
  def self.restore_pristine_tilesets(path, expected, hashes)
    original = "Data/sinnoh-experimental-tilesets-pristine.bin"
    return false unless path == "Data/Tilesets.rxdata" &&
      hashes.is_a?(Hash) && hashes[original] == expected &&
      File.file?(original) && !File.symlink?(original) &&
      File.file?(path) && !File.symlink?(path) &&
      sha256_file(original) == expected
    File.open(original,"rb") do |src|
      File.open(path,"wb") do |dst|
        while (chunk = src.read(32768))
          dst.write(chunk)
        end
      end
    end
    sha256_file(path) == expected
  rescue StandardError
    false
  end

  class JSONReader
    def initialize(text)
      raise ArgumentError, "QA_JSON_TOO_LARGE" if text.bytesize > 2*1024*1024
      @text = text.dup.force_encoding("UTF-8")
      raise ArgumentError, "QA_JSON_NOT_UTF8" unless @text.valid_encoding?
      @pos = 0
    end

    def peek
      @text[@pos,1]
    end

    def white
      @pos += 1 while (c = peek) && (c == " " || c == "\t" || c == "\r" || c == "\n")
    end

    def take(c)
      raise ArgumentError, "QA_JSON_SYNTAX_AT_#{@pos}" unless peek == c
      @pos += 1
    end

    def string
      take('"')
      out = "".dup.force_encoding("UTF-8")
      loop do
        c = peek
        raise ArgumentError, "QA_JSON_UNTERMINATED_STRING" if c.nil?
        @pos += 1
        return out if c == '"'
        raise ArgumentError, "QA_JSON_CONTROL_CHARACTER" if c.ord < 32
        if c == "\\"
          escape = peek
          raise ArgumentError, "QA_JSON_BAD_ESCAPE" if escape.nil?
          @pos += 1
          case escape
          when '"', "\\", "/" then out << escape
          when "b" then out << "\b"
          when "f" then out << "\f"
          when "n" then out << "\n"
          when "r" then out << "\r"
          when "t" then out << "\t"
          when "u"
            digits = @text[@pos,4]
            raise ArgumentError, "QA_JSON_BAD_UNICODE" unless digits && digits.match?(/\A[0-9a-fA-F]{4}\z/)
            value = digits.to_i(16)
            @pos += 4
            if value.between?(0xd800,0xdbff)
              raise ArgumentError, "QA_JSON_BAD_SURROGATE" unless @text[@pos,2] == "\\u"
              @pos += 2
              lo = @text[@pos,4]
              raise ArgumentError, "QA_JSON_BAD_SURROGATE" unless lo && lo.match?(/\A[0-9a-fA-F]{4}\z/)
              other = lo.to_i(16)
              raise ArgumentError, "QA_JSON_BAD_SURROGATE" unless other.between?(0xdc00,0xdfff)
              @pos += 4
              value = 0x10000 + ((value - 0xd800) << 10) + other - 0xdc00
            elsif value.between?(0xdc00,0xdfff)
              raise ArgumentError, "QA_JSON_BAD_SURROGATE"
            end
            out << [value].pack("U")
          else
            raise ArgumentError, "QA_JSON_BAD_ESCAPE"
          end
        else
          out << c
        end
      end
    end

    def value(depth=0)
      raise ArgumentError, "QA_JSON_TOO_DEEP" if depth > 32
      white
      case peek
      when "{"
        take("{")
        obj = {}
        white
        unless peek == "}"
          loop do
            white
            key = string
            raise ArgumentError, "QA_JSON_DUPLICATE_KEY" if obj.key?(key)
            white
            take(":")
            obj[key] = value(depth+1)
            white
            break unless peek == ","
            take(",")
          end
        end
        take("}")
        obj
      when "["
        take("[")
        arr = []
        white
        unless peek == "]"
          loop do
            arr << value(depth+1)
            white
            break unless peek == ","
            take(",")
          end
        end
        take("]")
        arr
      when '"' then string
      when "t","f","n"
        literals = {"true"=>true,"false"=>false,"null"=>nil}
        match = literals.keys.find { |key| @text[@pos,key.length] == key }
        raise ArgumentError, "QA_JSON_BAD_LITERAL" unless match
        @pos += match.length
        literals[match]
      else
        rest = @text[@pos..-1]
        token = rest && rest.match(/\A-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/)
        raise ArgumentError, "QA_JSON_BAD_VALUE_AT_#{@pos}" unless token
        @pos += token[0].length
        token[0].include?(".") || token[0].match?(/[eE]/) ? token[0].to_f : token[0].to_i
      end
    end

    def parse
      result = value
      white
      raise ArgumentError, "QA_JSON_TRAILING_DATA" unless @pos == @text.length
      result
    end
  end

  def self.parse_json(text)
    JSONReader.new(text).parse
  end
end

module BlueKantoTitle
  LABEL = "Testar Kanto".freeze
  JOHTO_LABEL = "Testar Johto".freeze
  HOENN_LABEL = "Testar Hoenn".freeze
  SINNOH_LABEL = "Testar Sinnoh".freeze
  LAUNCHER = "KANTO_JOGAR_EXPERIMENTAL.bat".freeze
  JOHTO_LAUNCHER = "JOHTO_JOGAR_EXPERIMENTAL.bat".freeze

  # J12-E: the generated Sinnoh QA is already a separate running Game.exe.
  # It is NOT the old "Sinnoh pilot.json" format, so never attempt to launch a
  # second pilot or claim the maps are absent. Validate the actual private
  # profile, original nine RXDATA and local PBS compilation before New Game.
  # In the main Decades/Blue installation there is no QA manifest, hence this
  # method never changes the main title or its region/save rules.
  def self.sinnoh_experimental_copy?
    return false unless File.file?("sinnoh-experimental-qa.json") &&
                        !File.symlink?("sinnoh-experimental-qa.json") &&
                        defined?(BlueSinnohExperimental) &&
                        BlueSinnohExperimental.const_defined?(:TOKEN, false) &&
                        BlueSinnohExperimental.const_defined?(:START, false)
    token = BlueSinnohExperimental::TOKEN
    return false unless token.is_a?(String) && token.match?(/\A[a-f0-9]{12}\z/)
    File.basename(Dir.pwd) == "game-sinnoh-experimental-" + token
  rescue IOError, SystemCallError, ArgumentError
    false
  end

  # These are TWO independent gates. Map exploration can run in an isolated
  # copy with verified original RXDATA even if Essentials has not compiled
  # Barry's three trainer versions. Do not manufacture a native compile proof.
  # Barry's event handler remains blocked by its own strict trainer checks.
  def self.sinnoh_qa_block(reason)
    @sinnoh_qa_last_error = reason
    false
  end

  def self.sinnoh_qa_last_error
    @sinnoh_qa_last_error || "Sinnoh QA: falha de verificação desconhecida."
  end

  def self.sinnoh_experimental_maps_ready?
    @sinnoh_qa_last_error = nil
    return sinnoh_qa_block("Fora da pasta Sinnoh QA autorizada.") unless sinnoh_experimental_copy?
    begin
      # Bundled Game.exe Ruby may not include the json/digest gems.
      # Validate with self-contained JSON + SHA256, never skip map checks.
      return sinnoh_qa_block("Manifesto QA ausente.") unless
        File.file?("sinnoh-experimental-qa.json") && !File.symlink?("sinnoh-experimental-qa.json")
      data = BlueSinnohQA.parse_json(File.binread("sinnoh-experimental-qa.json"))
      return sinnoh_qa_block("Manifesto QA nao corresponde ao piloto isolado.") unless
        data.is_a?(Hash) && data["schema"] == 1 &&
        data["region"] == "SINNOH" &&
        data["mode"] == "SINNOH_EXPERIMENTAL_TEST_COPY_NOT_NATIVE_APPROVED" &&
        data["profile_token"] == BlueSinnohExperimental::TOKEN &&
        data["start"] == BlueSinnohExperimental::START &&
        data["main_game_modified"] == false &&
        data["personal_saves_copied"] == false &&
        data["r09_native_qa_executed"] == 0 &&
        data["runtime_playable_verified"] == false
      token = data["profile_token"]
      save_token = data.fetch("save_profile_token", token)
      return sinnoh_qa_block("Token de saves QA invalido.") unless save_token.is_a?(String) && save_token.match?(/\A[a-f0-9]{12}\z/)
      namespace = data["save_profile"]
      return sinnoh_qa_block("Perfil de saves QA inconsistente.") unless
        namespace.is_a?(Hash) &&
        namespace["title"] == "Sinnoh QA " + save_token &&
        namespace["dataPathApp"] == "Sinnoh-QA-" + save_token &&
        namespace["dataPathOrg"] == "Dessastre-Sinnoh-QA-" + save_token
      return sinnoh_qa_block("Arquivos mkxp.json/Game.ini ausentes ou links inseguros.") unless
        File.file?("mkxp.json") && !File.symlink?("mkxp.json") &&
        File.file?("Game.ini") && !File.symlink?("Game.ini")
      conf = BlueSinnohQA.parse_json(File.binread("mkxp.json"))
      return sinnoh_qa_block("Namespace de saves do Game.exe diferente do QA.") unless
        conf.is_a?(Hash) &&
        conf["windowTitle"] == namespace["title"] &&
        conf["dataPathApp"] == namespace["dataPathApp"] &&
        conf["dataPathOrg"] == namespace["dataPathOrg"] &&
        conf.keys.none? { |key| key.to_s.downcase.include?("save") ||
                                key.to_s.downcase.include?("userdata") } &&
        File.readlines("Game.ini").count { |row| row.strip == "Title=" + namespace["title"] } == 1
      ids = data["mapids"]
      files = data["file_sha256"]
      lake_story = data["private_lake_story"]
      expected_count = lake_story.is_a?(Hash) && lake_story["portal_pairs"] == 2 ? 10 : 9
      city_keys = %w[SINNOH_JUBILIFE_CITY SINNOH_OREBURGH_CITY SINNOH_FLOAROMA_TOWN SINNOH_ETERNA_CITY SINNOH_HEARTHOME_CITY SINNOH_SOLACEON_TOWN SINNOH_VEILSTONE_CITY SINNOH_PASTORIA_CITY SINNOH_CELESTIC_TOWN SINNOH_CANALAVE_CITY SINNOH_SNOWPOINT_CITY SINNOH_SUNYSHORE_CITY]
      city_report = data["city_expansion"]
      if city_report.is_a?(Hash) && !city_report.empty?
        return sinnoh_qa_block("Manifesto F04 de cidades invalido.") unless expected_count == 10 && ids.is_a?(Hash) && city_report.keys.sort == city_keys.sort && city_keys.all? { |k| ids.key?(k) && city_report[k].is_a?(Hash) && city_report[k]["target_id"] == ids[k] }
        expected_count = 22
      end
      route_report = data["route_expansion"]
      if route_report.is_a?(Hash) && !route_report.empty?
        route_keys = (203..230).map { |n| "SINNOH_ROUTE_" + n.to_s } + [205,210,212,224,225,228].map { |n| "SINNOH_ROUTE_" + n.to_s + "_SEGMENT_2" }
        return sinnoh_qa_block("Manifesto F05 de rotas invalido.") unless expected_count == 22 && ids.is_a?(Hash) && route_report.keys.sort == route_keys.sort && route_keys.all? { |k| ids.key?(k) && route_report[k].is_a?(Hash) && route_report[k]["target_id"] == ids[k] }
        expected_count = 56
      end
      interior_report = data["interior_expansion"]
      interior_keys = [32,43,48,81,86,87,88,97,107,115,120,124,125,129,130,131,132,133,134,135,136,137,138,143,148,149,158,167,168,169,170,171,172,187,188,220].map { |id| sprintf("SINNOH_F07_INTERIOR_%03d",id) }
      extra_report = data["f08c_expansion"]
      extra_keys = %w[SINNOH_RESORT_AREA SINNOH_CYCLING_ROAD SINNOH_SURVIVAL_AREA SINNOH_FIGHT_AREA]
      gym_keys = %w[SINNOH_OREBURGH_GYM SINNOH_ETERNA_GYM SINNOH_HEARTHOME_GYM SINNOH_VEILSTONE_GYM SINNOH_PASTORIA_GYM SINNOH_CANALAVE_GYM SINNOH_SNOWPOINT_GYM SINNOH_SUNYSHORE_GYM]
      windworks_key = "SINNOH_VALLEY_WINDWORKS"
      eterna_keys = (1..4).map { |n| "SINNOH_GALACTIC_ETERNA_#{n}F" }
      natural_report = data["natural_expansion"]
      if natural_report.is_a?(Hash) && !natural_report.empty?
        natural_keys = %w[SINNOH_OREBURGH_MINE SINNOH_OREBURGH_GATE SINNOH_MT_CORONET_WEST_APPROACH SINNOH_SOLACEON_RUINS SINNOH_ETERNA_FOREST SINNOH_ETERNA_FOREST_SOURCE_093 SINNOH_FLOAROMA_MEADOW SINNOH_MT_CORONET_SOURCE_117 SINNOH_MT_CORONET_INTERIOR_ROUTES SINNOH_RAVAGED_PATH SINNOH_STARK_MOUNTAIN SINNOH_STARK_MOUNTAIN_SOURCE_153 SINNOH_ACUITY_LAKEFRONT SINNOH_LAKE_ACUITY SINNOH_ACUITY_CAVERN SINNOH_SNOWPOINT_TEMPLE SINNOH_MT_CORONET_SOURCE_174 SINNOH_MT_CORONET_SOURCE_182 SINNOH_MT_CORONET_SOURCE_183 SINNOH_MT_CORONET_SOURCE_184 SINNOH_WAYWARD_CAVE SINNOH_WAYWARD_CAVE_SOURCE_190 SINNOH_VERITY_CAVERN SINNOH_MANIAC_TUNNEL SINNOH_SPRING_PATH SINNOH_SENDOFF_SPRING SINNOH_TURNBACK_CAVE SINNOH_TURNBACK_CAVE_SOURCE_211 SINNOH_TURNBACK_CAVE_SOURCE_212 SINNOH_TURNBACK_CAVE_SOURCE_213 SINNOH_VALOR_LAKEFRONT SINNOH_LAKE_VALOR SINNOH_LAKE_VALOR_SOURCE_216 SINNOH_VALOR_CAVERN SINNOH_GREAT_MARSH]
        return sinnoh_qa_block("Manifesto F06 invalido.") unless expected_count == 56 && ids.is_a?(Hash) && natural_report.keys.sort == natural_keys.sort && natural_keys.all? { |k| ids.key?(k) && natural_report[k].is_a?(Hash) && natural_report[k]["target_id"] == ids[k] } && ids.all? { |k,n| natural_keys.include?(k) || (interior_report.is_a?(Hash) && !interior_report.empty? && interior_keys.include?(k)) || (extra_report.is_a?(Hash) && !extra_report.empty? && extra_keys.include?(k)) || gym_keys.include?(k) || k==windworks_key || eterna_keys.include?(k) || (n.is_a?(Integer) && n.between?(442,517)) }
        expected_count = 91
      end
      if interior_report.is_a?(Hash) && !interior_report.empty?
        return sinnoh_qa_block("Manifesto F07 invalido.") unless expected_count == 91 && ids.is_a?(Hash) && interior_report.keys.sort == interior_keys.sort && interior_keys.all? { |k| ids.key?(k) && interior_report[k].is_a?(Hash) && interior_report[k]["target_id"] == ids[k] && interior_report[k]["source_tileset_id"] == 25 && interior_report[k]["outdoor"] == false }
        expected_count = 127
      end
      if extra_report.is_a?(Hash) && !extra_report.empty?
        return sinnoh_qa_block("Manifesto F08C invalido.") unless expected_count == 127 && ids.is_a?(Hash) && extra_report.keys.sort == extra_keys.sort && extra_keys.all? { |k| ids.key?(k) && extra_report[k].is_a?(Hash) && extra_report[k]["target_id"] == ids[k] && extra_report[k]["source_tileset_id"] == 24 && extra_report[k]["outdoor"] == true }
        expected_count = 131
      end
      gym_art = []
      %w[a b c d e f g h].each_with_index do |letter,i|
        report = data["f11#{letter}_gym"]
        next unless report.is_a?(Hash) && report["gym_rooms_added"] == 1
        key = gym_keys[i]
        return sinnoh_qa_block("Manifesto F11 invalido.") unless expected_count == 131+i &&
          ids.is_a?(Hash) && ids.key?(key) && report["maps_after"] == expected_count+1 &&
          report["gyms"].is_a?(Array) && report["gyms"][i].is_a?(Hash) &&
          report["gyms"][i]["map_id"] == ids[key] && report["gyms"][i]["installed"] == true
        expected_count += 1
        gym_art << ["ROCK","GRASS","GHOST","FIGHTING","WATER","STEEL","ICE","ELECTRIC"][i].then { |s| "Graphics/Tilesets/SNQA_F11#{letter.upcase}_#{s}_GYM.png" }
      end
      windworks = data["f12b4_windworks_access"]
      if windworks.is_a?(Hash) && windworks["runtime_install_enabled"] == true
        return sinnoh_qa_block("Manifesto Windworks invalido.") unless expected_count==139 &&
          ids.is_a?(Hash) && ids.key?(windworks_key) && windworks["preview_map_id"]==ids[windworks_key] &&
          windworks["new_maps"]==1 && [0,1].include?(windworks["new_seams"]) &&
          windworks["baseline_preserved"]==true
        expected_count+=1
        gym_art << "Graphics/Tilesets/SNQA_F12B_111.png"
      end
      eterna = data["f12c4_install"]
      if eterna.is_a?(Hash) && eterna["runtime_install_enabled"] == true
        rooms = eterna["rooms"]
        return sinnoh_qa_block("Manifesto Galactic Eterna invalido.") unless expected_count==140 &&
          ids.is_a?(Hash) && rooms.is_a?(Array) && rooms.length==4 &&
          eterna["status"]=="F12C4_INSTALL_PREPARED" && eterna["maps_after"]==144 &&
          eterna["baseline_preserved"]==true && eterna["new_portals"]==8 &&
          eterna["qa_teleport_excluded"]==eterna_keys &&
          rooms.each_with_index.all? { |r,i| r.is_a?(Hash) && r["symbol"]==eterna_keys[i] &&
            ids[r["symbol"]]==r["map_id"] && files.is_a?(Hash) &&
            files[sprintf("Data/Map%03d.rxdata",r["map_id"])]==r["sha256"] }
        expected_count+=4
        gym_art << "Graphics/Tilesets/SNQA_F12C2_GALACTIC.png"
      end
      return sinnoh_qa_block("MapIDs QA invalidos ou colisao entre mapas.") unless
        ids.is_a?(Hash) && ids.length == expected_count &&
        (expected_count == 9 || ids.key?("SINNOH_VERITY_LAKEFRONT")) &&
        ids.values.all? { |value| value.is_a?(Integer) && value.between?(442,expected_count >= 91 ? 599 : 517) } &&
        ids.values.uniq.length == expected_count && files.is_a?(Hash)
      start = data["start"]
      return sinnoh_qa_block("Quarto inicial nao corresponde aos MapIDs QA.") unless
        start.is_a?(Array) && start.length == 3 &&
        start.all? { |v| v.is_a?(Integer) } &&
        ids["SINNOH_PLAYER_BEDROOM"] == start[0] &&
        start[1] >= 0 && start[2] >= 0
      required = ["Data/MapInfos.rxdata", "Data/Tilesets.rxdata"] +
                 ids.values.map { |id| sprintf("Data/Map%03d.rxdata", id) }
      if expected_count >= 22
        source_ids = city_report.values.map { |r| r["source_id"] }
        return sinnoh_qa_block("Fontes das cidades F04 invalidas.") unless source_ids.all? { |id| id.is_a?(Integer) } && source_ids.sort == [22,77,84,90,96,106,109,123,160,205,219,225]
        required += source_ids.map { |id| sprintf("Graphics/Tilesets/SNQA_F04_%03d.png",id) }
      end
      if expected_count >= 56
        source_ids = route_report.values.map { |r| r["source_id"] }
        return sinnoh_qa_block("Fontes F05 invalidas.") unless source_ids.all? { |id| id.is_a?(Integer) } && source_ids.sort == [42,79,80,91,94,104,105,108,110,116,122,126,140,141,142,146,150,151,155,156,157,164,165,198,199,200,206,218,222,223,224,226,233,234]
        required += source_ids.map { |id| sprintf("Graphics/Tilesets/SNQA_F05_%03d.png",id) }
      end
      if expected_count >= 91
        source_ids = natural_report.values.map { |r| r["source_id"] }
        return sinnoh_qa_block("Fontes F06 invalidas.") unless source_ids.all? { |id| id.is_a?(Integer) } && source_ids.sort == [33,76,82,89,92,93,98,117,121,145,152,153,159,161,162,173,174,182,183,184,189,190,197,207,208,209,210,211,212,213,214,215,216,217,221]
        required += source_ids.map { |id| sprintf("Graphics/Tilesets/SNQA_F06_%03d.png",id) }
      end
      if expected_count >= 127
        source_ids = interior_report.values.map { |r| r["source_id"] }
        return sinnoh_qa_block("Fontes F07 invalidas.") unless source_ids.all? { |id| id.is_a?(Integer) } && source_ids.sort == [32,43,48,81,86,87,88,97,107,115,120,124,125,129,130,131,132,133,134,135,136,137,138,143,148,149,158,167,168,169,170,171,172,187,188,220]
        required += source_ids.map { |id| sprintf("Graphics/Tilesets/SNQA_F07_%03d.png",id) }
      end
      if expected_count >= 131
        source_ids = extra_report.values.map { |r| r["source_id"] }
        return sinnoh_qa_block("Fontes F08C invalidas.") unless source_ids.all? { |id| id.is_a?(Integer) } && source_ids.sort == [139,147,163,166]
        required += source_ids.map { |id| sprintf("Graphics/Tilesets/SNQA_F08C_%03d.png",id) }
      end
      required += gym_art
      required.each do |file|
        hash = files[file]
        return sinnoh_qa_block("Manifesto SHA-256 incompleto: " + file) unless
          hash.is_a?(String) && hash.match?(/\A[a-f0-9]{64}\z/)
        return sinnoh_qa_block("Mapa ou indice ausente ou inseguro: " + file) unless
          File.file?(file) && !File.symlink?(file)
        if BlueSinnohQA.sha256_file(file) != hash
          if file == "Data/Tilesets.rxdata" &&
             BlueSinnohQA.restore_pristine_tilesets(file, hash, files)
            # Only the Blue-Story managed supervisor may request an automatic
            # one-time restart. Standalone/manual launches keep the safe
            # explanatory message, without an uncontrolled restart loop.
            enabled = "Data/sinnoh-experimental-auto-restart-enabled.txt"
            request = "Data/sinnoh-experimental-auto-restart-request.txt"
            if File.file?(enabled) && !File.symlink?(enabled) &&
               File.binread(enabled).strip == token &&
               !File.exist?(request) && !File.symlink?(request)
              File.open(request, File::WRONLY | File::CREAT | File::EXCL, 0600) do |out|
                out.write(token + "\n" + hash + "\n")
              end
              # This process may already have loaded the wrong tilesets;
              # supervisor will re-audit and relaunch the same QA once.
              exit(0)
            end
            return sinnoh_qa_block("Tilesets QA restaurado de copia original verificada. Feche esta janela e reabra a copia Sinnoh QA para carregar os tilesets corretos.")
          end
          return sinnoh_qa_block("Mapa ou indice alterado (SHA-256): " + file)
        end
      end
      true
    rescue StandardError, LoadError => error
      label = error.message.to_s.gsub(/[\r\n]/," ").slice(0,150)
      sinnoh_qa_block("Erro ao ler QA: " + error.class.to_s + " (" + label + ")")
    end
  end

  def self.sinnoh_experimental_barry_compiled?
    return false unless sinnoh_experimental_copy?
    marker = "Data/sinnoh-experimental-compiled.txt"
    return false unless File.file?(marker) && !File.symlink?(marker) &&
      !File.exist?("Data/sinnoh-experimental-compile-request.txt") &&
      !File.exist?("Data/sinnoh-experimental-compile-error.txt")
    data = BlueSinnohQA.parse_json(File.binread("sinnoh-experimental-qa.json"))
    token = data["compile_token"]
    token.is_a?(String) && token.match?(/\A[a-f0-9]{64}\z/) &&
      File.read(marker).strip == token
  rescue StandardError, LoadError
    false
  end

  # Historical strict predicate: used by build/QA regressions. It means both
  # verified maps AND locally compiled Barry, NOT gameplay/R09 acceptance.
  def self.sinnoh_experimental_ready?
    sinnoh_experimental_maps_ready? && sinnoh_experimental_barry_compiled?
  end

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
    ordered << :blue_test_sinnoh if sinnoh_experimental_copy?
    ordered.concat(indices.reject { |idx| ordered.include?(idx) })
    ordered
  end

  # Main New Game uses the shared world for integrated regions.
  # Sinnoh QA remains accessible only via the explicit Testar Sinnoh command.
  START_REGIONS = [
    ["Decades", :decades],
    ["Kanto", :kanto],
    ["Johto (piloto experimental)", :johto],
    ["Hoenn (piloto experimental)", :hoenn],
    ["Sinnoh (instalação necessária)", :sinnoh],
    ["Unova (indisponível)", :unavailable],
    ["Kalos (indisponível)", :unavailable],
    ["Alola (indisponível)", :unavailable],
    ["Galar (indisponível)", :unavailable],
    ["Paldea (indisponível)", :unavailable],
    ["Hisui (indisponível)", :unavailable],
    ["Voltar ao menu", :cancel]
  ].freeze

  def self.start_region_names
    kanto = defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:kanto_integrated?) &&
            BlueRegionStart.kanto_integrated?
    hoenn = defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:hoenn_integrated?) &&
            BlueRegionStart.hoenn_integrated?
    johto = defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:johto_spawn) &&
            BlueRegionStart.johto_spawn
    johto_release = johto && BlueRegionStart.respond_to?(:johto_install_proof) &&
                    BlueRegionStart.johto_install_proof
    sinnoh = defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:sinnoh_spawn) && BlueRegionStart.sinnoh_spawn
    START_REGIONS.map do |name, region|
      label = if region == :johto && johto
                # Same main game and shared save as Kanto/Hoenn.
                "Johto"
              elsif region == :johto
                "Johto (instalação necessária)"
              elsif region == :kanto && !kanto
                "Kanto (instalação necessária)"
              elsif region == :hoenn && hoenn
                "Hoenn"
              elsif region == :sinnoh && sinnoh
                "Sinnoh"
              else
                name
              end
      _INTL(label)
    end
  end

  def self.choose_start_region
    loop do
      choice = pbMessage(_INTL("Em qual região deseja começar um novo jogo?"), start_region_names, 0)
      return :cancel unless choice.is_a?(Integer) && (0...START_REGIONS.length).cover?(choice)
      region = START_REGIONS[choice][1]
      case region
      when :decades
        # Prevent a second region picker in the old Decades Story Mode event.
        BlueRegionStart.request_initial("DECADES") if defined?(BlueRegionStart) &&
                                                     BlueRegionStart.respond_to?(:request_initial)
        return :decades
      when :kanto
        # Kanto runs in the same Game.exe and save system as Decades only when
        # an audited map+PBS installation exists in the MAIN game directory.
        if defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:request_initial) &&
           BlueRegionStart.request_initial("KANTO")
          return :integrated
        end
        pbMessage(_INTL("Kanto não foi instalado. Feche o jogo e abra novamente o Blue-Story.exe: ele tentará baixar e integrar Kanto automaticamente. Se a instalação falhar, consulte o diagnóstico em .blue-work/kanto-install-status.json. Seus saves serão preservados."))
      when :johto
        # Installable Johto belongs to the SAME Game.exe, save and regional
        # journey as Kanto/Hoenn. A separate experimental QA launcher is only
        # a fallback while the shared installer lacks a verified start point.
        if defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:request_initial) &&
           BlueRegionStart.request_initial("JOHTO")
          return :integrated
        end
        # The main New Game picker must NEVER launch another executable or
        # switch to a standalone Johto save. Experimental pilots are only
        # available through the separate "Testar Johto" title command.
        pbMessage(_INTL("Johto ainda não foi instalada no jogo principal. Feche o jogo e abra Blue-Story.exe. Coloque o arquivo Johto_Offline_Fase12_Auditoria_Integracao_Privado.zip em Downloads, sem extrair. Veja o erro exato em .blue-work/johto-main-install-status.json. Decades, Kanto e Hoenn permanecem disponíveis."))
      when :hoenn
        if defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:hoenn_integrated?) &&
           BlueRegionStart.hoenn_integrated? &&
           BlueRegionStart.respond_to?(:request_initial) &&
           BlueRegionStart.request_initial("HOENN")
          return :integrated
        end
        # Keep existing isolated pilot available until the shared 199-map
        # installation is verified. It retains its own independent save.
        return :launched if launch_hoenn
        pbMessage(_INTL("Hoenn ainda não está integrada nesta instalação. Coloque o ZIP original de Hoenn na pasta do projeto e execute a atualização Blue-Story.exe. Seus saves de Decades/Kanto não foram modificados."))
      when :sinnoh
        if defined?(BlueRegionStart) && BlueRegionStart.respond_to?(:sinnoh_spawn) &&
           BlueRegionStart.sinnoh_spawn && BlueRegionStart.request_initial("SINNOH")
          return :integrated
        end
        pbMessage(_INTL("Para instalar Sinnoh neste jogo, coloque os dois ZIPs de origem junto ao Blue-Story.exe e abra o inicializador novamente."))
      when :cancel then return :cancel
      when :unavailable
        pbMessage(_INTL("Essa região ainda não tem uma campanha jogável instalada. Nenhum save foi alterado."))
      else
        # Other regions still require separate experimental copies. They must
        # never silently start Decades or claim to share its progress.
        return :launched if public_send("launch_#{region}")
      end
    end
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
    candidates = []
    if region == "Hoenn"
      candidates << File.expand_path("../.blue-work/hoenn-imp-qa", game)
      candidates << File.expand_path("../.blue-work/hoenn-qa-fase12", game)
    end
    candidates << File.expand_path("../.blue-work/#{directory}-pilot", game)
    candidates << File.expand_path("../.blue-work/game-johto-qa", game) if region == "Johto"
    profile = ENV["USERPROFILE"]
    if profile && !profile.empty?
      if region == "Hoenn"
        candidates << File.expand_path("Documents/Codex/.blue-work/hoenn-imp-qa", profile)
      end
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
    # When invoked INSIDE the verified QA executable, "Testar Sinnoh" means
    # start a new game HERE. The user must not launch another process or
    # consume a save from a different regional profile.
    if sinnoh_experimental_copy?
      unless sinnoh_experimental_maps_ready?
        pbMessage(_INTL("Sinnoh QA bloqueado: {1}. Nenhum save foi alterado.", sinnoh_qa_last_error))
        return false
      end
      unless sinnoh_experimental_barry_compiled?
        pbMessage(_INTL("Piloto de exploração: mapas verificados. As equipes de Barry ainda não estão compiladas, então sua batalha permanece bloqueada. Você pode testar quarto, caminhada e portais na cópia QA."))
      end
      return :blue_sinnoh_local_new_game
    end
    false
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
      @blue_kanto_new_game = commands.index(_INTL("New Game"))
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
        if BlueKantoTitle.sinnoh_experimental_copy? && original == @blue_kanto_new_game
          # Do not ask for Decades/Kanto/Hoenn here. The QA copy has its own
          # save namespace and BlueSinnohExperimental overrides its spawn.
          if BlueKantoTitle.sinnoh_experimental_maps_ready?
            return original
          end
          pbMessage(_INTL("Sinnoh QA bloqueado: {1}. Nenhum save foi alterado.", BlueKantoTitle.sinnoh_qa_last_error))
          next
        end
        if !BlueKantoTitle.pilot? && original == @blue_kanto_new_game
          # Let Decades' ORIGINAL New Game branch initialize its own save.
          # All other choices either open a separate regional pilot or return
          # to the title without writing a save or advancing story flags.
          return original unless @blue_kanto_quit
          case BlueKantoTitle.choose_start_region
          when :decades, :integrated then return original
          when :launched then return @blue_kanto_quit
          end
          next
        end
        if [:blue_test_kanto, :blue_test_johto, :blue_test_hoenn, :blue_test_sinnoh].include?(original)
          launched = case original
                     when :blue_test_kanto then BlueKantoTitle.launch
                     when :blue_test_johto then BlueKantoTitle.launch_johto
                     when :blue_test_hoenn then BlueKantoTitle.launch_hoenn
                     when :blue_test_sinnoh then BlueKantoTitle.launch_sinnoh
                     end
          if launched == :blue_sinnoh_local_new_game
            # The native New Game route will call BlueSinnohExperimental's
            # isolated start hook. Do not quit or spawn another Game.exe.
            return @blue_kanto_new_game if @blue_kanto_new_game
            pbMessage(_INTL("Sinnoh QA: a opção Novo Jogo não foi encontrada."))
            next
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
