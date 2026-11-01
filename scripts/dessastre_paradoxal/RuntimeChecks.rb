module BlueDessastreParadoxal
  EXPECTED_SPECIES = [
[:CAVEFANG,0,[85, 130, 65, 155, 50, 85],[:POISON,:DARK]],
[:ABYSSLURE,0,[152, 48, 48, 80, 116, 126],[:WATER,:FAIRY]],
[:ANCESTRASH,0,[120, 130, 130, 50, 50, 90],[:POISON,:GROUND]],
[:BURIALGAZE,0,[60, 70, 150, 40, 100, 150],[:GHOST,:GROUND]],
[:CRAGGYSIPHON,0,[90, 145, 70, 50, 145, 70],[:WATER,:FIGHTING]],
[:DIRERUFF,0,[100, 150, 90, 120, 40, 70],[:DARK,:GROUND]],
[:DREADCREST,0,[133, 40, 45, 90, 146, 116],[:FLYING,:GROUND]],
[:FETIDGULLET,0,[120, 83, 107, 30, 123, 107],[:POISON,:GHOST]],
[:FOSSILHUSK,0,[95, 125, 180, 30, 50, 90],[:BUG,:ROCK]],
[:FOSSLTIDE,0,[141, 103, 93, 49, 102, 82],[:WATER,:STEEL]],
[:JAGGEDMAW,0,[70, 115, 200, 60, 75, 50],[:WATER,:ROCK]],
[:MIASMIC,0,[80, 70, 145, 80, 115, 80],[:POISON,:DARK]],
[:MIRECREST,0,[123, 133, 77, 94, 62, 81],[:DARK,:FIGHTING]],
[:PHANTOMIRE,0,[65, 45, 55, 145, 185, 75],[:GHOST,:DARK]],
[:PRIAMALGONG,0,[100, 70, 80, 55, 105, 160],[:ICE,:DRAGON]],
[:PRIMALCATERPIE,0,[90, 135, 95, 90, 90, 70],[:BUG,:DRAGON]],
[:PRIMALDRENAW,0,[105, 155, 90, 94, 48, 78],[:WATER,:DRAGON]],
[:PRIMALPUNNY,0,[105, 156, 94, 85, 44, 86],[:GROUND,:FIGHTING]],
[:PRIMALTROPICAL,0,[119, 88, 93, 71, 92, 107],[:GRASS,:DRAGON]],
[:PRIMALDUURR,0,[125, 165, 115, 30, 50, 85],[:FIGHTING,:GROUND]],
[:PRIMALGEOT,0,[93, 110, 85, 121, 81, 80],[:FLYING,:FIGHTING]],
[:PRIMALKORCH,0,[130, 145, 50, 50, 100, 95],[:BUG,:DRAGON]],
[:PRIMALMOTH,0,[90, 55, 55, 120, 140, 110],[:BUG,:ICE]],
[:PRIMALMUK,0,[135, 125, 85, 40, 60, 125],[:POISON,:GROUND]],
[:PRIMALSEAKING,0,[110, 132, 75, 98, 55, 100],[:WATER,:POISON]],
[:PRIMALSECT,0,[90, 135, 140, 20, 85, 100],[:GRASS,:ROCK]],
[:PRIMALVIPER,0,[83, 130, 80, 75, 120, 82],[:POISON,:DRAGON]],
[:PRIMATIZER,0,[81, 93, 108, 49, 140, 99],[:WATER,:ROCK]],
[:RAMPAGEHORN,0,[125, 135, 155, 35, 45, 75],[:ROCK,:DRAGON]],
[:RAVENOUSCREST,0,[105, 160, 95, 75, 55, 80],[:FIGHTING]],
[:RAZORCARAPACE,0,[90, 120, 200, 40, 50, 70],[:STEEL,:DRAGON]],
[:SAVEGEJOWL,0,[110, 170, 95, 45, 70, 80],[:FAIRY,:DARK]],
[:SCORCHMANE,0,[80, 135, 50, 145, 100, 60],[:FIRE,:ELECTRIC]],
[:SCORIASHELL,0,[80, 70, 140, 25, 135, 120],[:FIRE,:STEEL]],
[:THORNBASTION,0,[95, 135, 175, 45, 45, 75],[:GROUND,:ROCK]],
[:TITANBALEEN,0,[190, 115, 110, 50, 65, 40],[:WATER,:STEEL]],
[:WOOLYSTING,0,[90, 120, 115, 120, 40, 85],[:FLYING,:FIGHTING]],
[:IRONCRAWLER,0,[70, 135, 100, 165, 40, 60],[:BUG,:POISON]],
[:IRONCRUSHER,0,[75, 170, 145, 65, 50, 65],[:WATER,:STEEL]],
[:IRONFEASTER,0,[170, 120, 85, 20, 55, 120],[:NORMAL,:STEEL]],
[:IRONINVERNOSE,0,[80, 125, 55, 135, 105, 70],[:FIRE,:STEEL]],
[:IRONLEPORIS,0,[75, 46, 64, 155, 154, 76],[:NORMAL,:ELECTRIC]],
[:IRONMAELTROM,0,[105, 65, 109, 61, 130, 100],[:FLYING,:STEEL]],
[:IRONMATRIARCH,0,[125, 120, 120, 70, 45, 90],[:NORMAL,:STEEL]],
[:ARCHGUTOR,0,[120, 105, 105, 35, 135, 90],[:GRASS,:PSYCHIC]],
[:DYNAMOTRODE,0,[60, 40, 80, 165, 130, 80],[:ELECTRIC,:STEEL]],
[:MAGNETRIX,0,[65, 60, 60, 120, 145, 80],[:STEEL,:ELECTRIC]],
[:MAGISCALE,0,[100, 50, 65, 75, 115, 130],[:WATER,:PSYCHIC]],
[:AMMNOID,0,[65, 75, 105, 70, 100, 80],[:ROCK,:PSYCHIC]],
[:CEPHALONID,0,[70, 90, 105, 80, 120, 85],[:ROCK,:PSYCHIC]],
[:STUNDRIFT,0,[129, 76, 104, 22, 101, 109],[:GROUND,:ELECTRIC]],
[:SWADLOADNE,0,[90, 60, 120, 35, 100, 95],[:GRASS,:BUG]],
[:TENTACRUEL,1,[80, 80, 85, 120, 100, 150],[:WATER,:POISON]],
[:SUNFLORA,1,[75, 85, 75, 20, 155, 115],[:GRASS,:FAIRY]],
[:ARBOK,1,[60, 135, 89, 100, 65, 99],[:POISON,:DRAGON]],
[:FEAROW,1,[65, 130, 78, 127, 61, 81],[:FLYING,:POISON]],
[:HYPNO,1,[85, 113, 90, 57, 103, 135],[:PSYCHIC,:FAIRY]],
[:KABUTOPS,1,[60, 155, 75, 130, 95, 80],[:ROCK,:STEEL]],
[:LEDIAN,1,[55, 80, 65, 125, 55, 110],[:BUG,:FIGHTING]],
[:LUDICOLO,1,[80, 50, 100, 90, 140, 120],[:WATER,:GRASS]],
[:MILTANK,1,[95, 90, 155, 95, 40, 95],[:NORMAL,:FIGHTING]],
[:PURUGLY,1,[71, 104, 94, 120, 84, 79],[:NORMAL,:DARK]],
[:VILEPLUME,1,[75, 70, 135, 40, 130, 140],[:GRASS,:POISON]],
[:WALREIN,1,[110, 110, 140, 55, 105, 110],[:ICE,:ROCK]]
  ]
  PENDING = [:HORSAND,:SPINEDRA,:STINGDRA,:GILLBLE,:GALBITE,:GARCHOLT,:PRIMALNOTIC]
  PRESENTATION = {
    [:CAVEFANG,0] => ['Cave Fang','An ancient relative of Zubat, it hunts in pitch-black caves using ultrasonic cries. Its oversized fangs inject a powerful venom, paralyzing prey before it can escape.',1.6,36.0],
    [:ABYSSLURE,0] => ['Abyss Lure','An ancient relative of Lanturn, it roamed the deepest oceans using its enormous fins. Its golden lure emits an enchanting glow that draws unsuspecting prey straight into its powerful jaws.',1.9,64.0],
    [:ANCESTRASH,0] => ['Ancestrash','An ancient relative of Garbodor, it piles bones and decaying vegetation onto its muddy body. Toxic fumes seep from the rotting mass, turning the ground around it into a deadly bog.',2.4,260.0],
    [:BURIALGAZE,0] => ['Burial Gaze','An ancient relative of Duskull, it wanders forgotten burial grounds with its body covered in grave dust. Those who meet its unblinking gaze are said to hear the voices of spirits buried deep underground.',1.4,42.0],
    [:CRAGGYSIPHON,0] => ['Craggy Siphon','An ancient relative of Octillery, it ruled rocky coastal waters with its immense strength. It strikes foes with stone-hard tentacles and fires powerful jets of water from its muscular siphon.',1.7,108.0],
    [:DIRERUFF,0] => ['Dire Ruff','An ancient relative of Mightyena, it hunted in ruthless packs across barren plains. Its jagged mane bristles as it kicks up blinding clouds of dust, allowing its pack to ambush unsuspecting prey.',1.6,82.0],
    [:DREADCREST,0] => ['Dread Crest','An ancient relative of Noctowl, it ruled the skies above barren canyons. Its enormous crest intimidated rivals, while its powerful wings stirred up blinding dust clouds to conceal its attacks.',2.1,58.0],
    [:FETIDGULLET,0] => ['Fetid Gullet','An ancient relative of Swalot, it swallowed decaying matter from primeval marshes without pause. The foul gases in its cavernous body are said to trap the lingering spirits of anything it consumes.',1.9,94.0],
    [:FOSSILHUSK,0] => ['Fossil Husk','An ancient relative of Pineco, it developed a shell of mineralized plates as hard as solid rock. It clung to trees along prehistoric cliffs, dropping onto predators with enough force to shatter stone.',1.1,79.0],
    [:FOSSLTIDE,0] => ['Fossl Tide','An ancient relative of Gastrodon, it absorbed iron from the prehistoric seafloor to form a thick metallic shell. Its armored body could withstand crushing ocean currents and attacks from enormous predators.',1.6,118.0],
    [:JAGGEDMAW,0] => ['Jagged Maw','An ancient relative of Cloyster, it lurked among submerged cliffs, disguising its jagged shell as stone. When prey approached, its enormous jaws snapped shut with enough force to crush solid rock.',2.2,285.0],
    [:MIASMIC,0] => ['Miasmic','An ancient relative of Weezing, it drifted through toxic marshes while spewing a noxious yellow haze. Prey that inhaled its miasma grew weak and disoriented, making them easy targets for its vicious assault.',1.8,72.0],
    [:MIRECREST,0] => ['Mire crest','An ancient relative of Skuntank, it flares its towering mane to frighten rivals. It fights with deceptive lunges and crushing claw strikes, refusing to retreat even when outnumbered.',1.5,74.0],
    [:PHANTOMIRE,0] => ['Phantomire','An ancient relative of Haunter, it prowled mist-covered marshes long before humans existed. Its spectral hands spread unnatural darkness, trapping unsuspecting prey in terrifying illusions.',1.9,0.4],
    [:PRIAMALGONG,0] => ['Frost Plume','An ancient relative of Dewgong, it glided beneath polar ice on featherlike fins. Its icy breath froze seawater into sharp crystals, driving away even the fiercest predators.',2.3,148.0],
    [:PRIMALCATERPIE,0] => ['Spined Wyrm','An ancient relative of Caterpie, it charged larger predators with its dragonlike horns. Its armored segments and sharp spines made it a fearsome forest dweller.',1.2,24.0],
    [:PRIMALDRENAW,0] => ['Tidal Tyrant','An ancient relative of Drednaw, it stalked prehistoric seas beneath a jagged, armored shell. Its crushing jaws could drag even massive prey into the depths.',2.8,310.0],
    [:PRIMALPUNNY,0] => ['Burrow Brawler','An ancient relative of Lopunny, it carved deep burrows with its powerful hind legs. Its devastating kicks could crack the ground beneath charging predators.',1.6,62.0],
    [:PRIMALTROPICAL,0] => ['Canopy Titan','An ancient relative of Tropius, it carried enormous leaflike wings above its back. Its long neck reached fruit growing far beyond the reach of other Pokémon.',3.2,240.0],
    [:PRIMALDUURR,0] => ['Timber Maul','An ancient relative of Conkeldurr, it uprooted whole trees to wield as clubs. Its mighty blows left deep fractures across the earth.',2.1,185.0],
    [:PRIMALGEOT,0] => ['Tempest Talon','An ancient relative of Pidgeot, it challenged rivals with ferocious aerial dives. Its powerful talons could knock even large Pokémon out of the sky.',2.1,61.0],
    [:PRIMALKORCH,0] => ['Cinder Coil','An ancient relative of Centiskorch, it guarded volcanic tunnels with its armored coils. Its glowing plates radiated enough heat to drive away predators.',4.2,180.0],
    [:PRIMALMOTH,0] => ['Rime Shroud','An ancient relative of Venomoth, it drifted through frozen forests, scattering icy scales that numbed anything they touched. Its powder lingered in the frigid air for hours.',1.8,21.0],
    [:PRIMALMUK,0] => ['Tar Chasm','An ancient relative of Muk, it lurked in primeval tar pits, its sludge thick with bones and sediment. Prey pulled into its gaping maw rarely escaped.',2.0,180.0],
    [:PRIMALSEAKING,0] => ['Venom Crown','An ancient relative of Seaking, it spread its venomous fins like a crown to warn predators. A single prick from its spines could paralyze even larger foes.',1.8,67.0],
    [:PRIMALSECT,0] => ['Spore Rampart','An ancient relative of Parasect, it grew jagged, stone-hard fungal plates across its back. It used its massive claws to defend the spore colonies beneath its shell.',1.7,132.0],
    [:PRIMALVIPER,0] => ['Venom Scythe','An ancient relative of Seviper, it hunted through primeval jungles using its scythe-shaped tail. Venom seeping from the blade could weaken even towering predators.',4.2,92.0],
    [:PRIMATIZER,0] => ['Primatizer','Its massive, stone-plated claw fires bursts of pressurized water strong enough to shatter coral. It ambushes prey among ancient reefs.',2.2,135.0],
    [:RAMPAGEHORN,0] => ['Rampage Horn','????',nil,nil],
    [:RAVENOUSCREST,0] => ['Ravenous Crest','????',nil,nil],
    [:RAZORCARAPACE,0] => ['Razor Carapace','????',nil,nil],
    [:SAVEGEJOWL,0] => ['Savege Jowl','????',nil,nil],
    [:SCORCHMANE,0] => ['Scorch Mane','An ancient relative of Rapidash, it galloped across volcanic plains with a mane crackling with electricity. Its blazing hooves left trails of fire wherever it ran.',2.1,140.0],
    [:SCORIASHELL,0] => ['Scoria Shell','An ancient relative of Magcargo, it crawled through volcanic craters with a shell of hardened scoria. Molten rock constantly seeped from the cracks in its body, scorching everything in its path.',1.4,190.0],
    [:THORNBASTION,0] => ['Thorn Bastion','????',nil,nil],
    [:TITANBALEEN,0] => ['Titan Baleen','An ancient relative of Wailord, it crossed prehistoric seas in metallic armor. Its tough baleen strained whole shoals of fish, while its dorsal spines repelled predators.',17.0,1250.0],
    [:WOOLYSTING,0] => ['Wooly sting','An ancient relative of Gliscor, it glided between icy cliffs with thick fur shielding it from the cold. It used its powerful pincers and hooked tail to repel rivals.',2.3,76.0],
    [:IRONCRAWLER,0] => ['iron crawler','A futuristic relative of Wimpod, it scuttles across polluted shores. Its glowing sensors detect toxins, which it absorbs and releases as a defensive mist.',0.8,22.0],
    [:IRONCRUSHER,0] => ['Iron Crusher','A futuristic relative of Kingler, it patrols the seafloor with hydraulic claws. Its oversized pincer can crush the metal hulls of sunken vessels.',1.9,210.0],
    [:IRONFEASTER,0] => ['iron feaster','A futuristic relative of Snorlax, it devours scrap metal to charge the reactor in its belly. Once fully powered, it enters a deep, motionless sleep.',2.4,850.0],
    [:IRONINVERNOSE,0] => ['iron invernose','A futuristic relative of Centiskorch, it slithers through industrial tunnels with a body heated like a furnace. The vents along its armor release bursts of flame to melt obstacles in its path.',3.8,145.0],
    [:IRONLEPORIS,0] => ['iron leporis','A futuristic relative of Lopunny, it stores electricity in its powerful limbs to unleash explosive jumps. Its blade-like ears and charged kicks can disable foes in an instant.',1.7,48.0],
    [:IRONMAELTROM,0] => ['Iron maeltrom','A futuristic relative of Gyarados, it uses turbines along its armored body to fly over raging seas. The violent air currents it creates can capsize ships.',7.5,620.0],
    [:IRONMATRIARCH,0] => ['Iron Matriarch','????',nil,nil],
    [:ARCHGUTOR,0] => ['Archgutor','After decades on tropical beaches, this evolution of Exeggutor stores solar energy in its coconuts. It uses sun-powered moves even beneath storm clouds.',3.2,185.0],
    [:DYNAMOTRODE,0] => ['Dynamotrode','An evolution of Electrode resembling a Fast Ball, it propels itself with electromagnetic bursts. It rolls so quickly that sparks trail behind it.',1.4,118.0],
    [:MAGNETRIX,0] => ['Magnetrix','An alternate evolution of Magneton, it spins four powerful magnets around its core to build immense electrical pressure. It can electrify the ground or propel itself through the air at incredible speed.',1.3,82.0],
    [:MAGISCALE,0] => ['Magiscale','An alternate evolution of Magikarp, it reads ocean currents through its golden whiskers. With a pulse of its mind, it blankets the battlefield in psychic energy.',5.4,128.0],
    [:AMMNOID,0] => ['Ammnoid','After exposure to a Dusk Stone, Omanyte evolves into Ammnoid. Its gold-banded shell amplifies psychic pulses that reveal movement across the dark seafloor.',0.9,31.0],
    [:CEPHALONID,0] => ['Cephalonid','Its horned shell stores immense psychic energy. When the blue gem on its crown flashes, Cephalonid can bend deep-sea currents and repel predators without touching them.',1.7,110.0],
    [:STUNDRIFT,0] => ['Stundrift','Buried deep beneath the seabed, it absorbs energy from rushing water and shifting earth. Its golden markings glow before it releases a powerful electric shock.',1.2,36.0],
    [:SWADLOADNE,0] => ['Swadloadne','After evolving with a Leaf Stone, it guards its forest beneath overlapping leaf shields. Thick inner padding protects it from heat and cold, while its armor covers vulnerable spots.',1.1,42.0],
    [:TENTACRUEL,1] => ['Mega Tentacruel','????',nil,nil],
    [:SUNFLORA,1] => ['Mega sunflora','????',nil,nil],
    [:ARBOK,1] => ['mega Arbok','????',nil,nil],
    [:FEAROW,1] => ['mega fearow','????',nil,nil],
    [:HYPNO,1] => ['mega hypno','????',nil,nil],
    [:KABUTOPS,1] => ['mega kabutops','????',nil,nil],
    [:LEDIAN,1] => ['mega ledian','????',nil,nil],
    [:LUDICOLO,1] => ['mega ludicolo','????',nil,nil],
    [:MILTANK,1] => ['mega miltank','????',nil,nil],
    [:PURUGLY,1] => ['mega purugly','????',nil,nil],
    [:VILEPLUME,1] => ['mega vileplume','????',nil,nil],
    [:WALREIN,1] => ['mega walrein','????',nil,nil]
  }
  CRIES = [:ABYSSLURE,:AMMNOID,:ANCESTRASH,:ARCHGUTOR,:BURIALGAZE,:CAVEFANG,:CEPHALONID,:CRAGGYSIPHON,:DIRERUFF,:DREADCREST,:DYNAMOTRODE,:FETIDGULLET,:FOSSILHUSK,:FOSSLTIDE,:IRONCRAWLER,:IRONCRUSHER,:IRONFEASTER,:IRONLEPORIS,:IRONMAELTROM,:JAGGEDMAW,:MAGISCALE,:MAGNETRIX,:MIASMIC,:MIRECREST,:PHANTOMIRE,:PRIAMALGONG,:PRIMALCATERPIE,:PRIMALDRENAW,:PRIMALPUNNY,:PRIMALDUURR,:PRIMALGEOT,:PRIMALMOTH,:PRIMALMUK,:PRIMALSEAKING,:PRIMALSECT,:PRIMALVIPER,:PRIMATIZER,:RAMPAGEHORN,:RAVENOUSCREST,:RAZORCARAPACE,:SAVEGEJOWL,:SCORCHMANE,:SCORIASHELL,:STUNDRIFT,:SWADLOADNE,:THORNBASTION,:TITANBALEEN,:WOOLYSTING]
  STONES = [:DPARBOKITE,:DPFEAROWITE,:DPHYPNOITE,:DPKABUTOPSITE,:DPLEDIANITE,:DPLUDICOLOITE,:DPMILTANKITE,:DPPURUGLYITE,:DPSUNFLORAITE,:DPTENTACRUELITE,:DPVILEPLUMEITE,:DPWALREINITE]
  ENCOUNTERS = {
    156 => [:CAVEFANG,:ABYSSLURE,:ANCESTRASH,:BURIALGAZE,:CRAGGYSIPHON,:DIRERUFF,:DREADCREST,:FETIDGULLET,:FOSSILHUSK,:FOSSLTIDE,:JAGGEDMAW,:MIASMIC,:MIRECREST,:PHANTOMIRE,:PRIAMALGONG,:PRIMALCATERPIE,:PRIMALDRENAW,:PRIMALPUNNY,:PRIMALTROPICAL,:PRIMALDUURR,:PRIMALGEOT,:PRIMALKORCH,:PRIMALMOTH,:PRIMALMUK,:PRIMALSEAKING,:PRIMALSECT,:PRIMALVIPER,:PRIMATIZER,:RAMPAGEHORN,:RAVENOUSCREST,:RAZORCARAPACE,:SAVEGEJOWL,:SCORCHMANE,:SCORIASHELL,:THORNBASTION,:TITANBALEEN,:WOOLYSTING],
    157 => [:IRONCRAWLER,:IRONCRUSHER,:IRONFEASTER,:IRONINVERNOSE,:IRONLEPORIS,:IRONMAELTROM,:IRONMATRIARCH]
  }
  def self.run_checks
    lines=[]
    check=proc { |label,ok| lines << "#{ok ? 'PASS' : 'FAIL'} | #{label}"; raise label unless ok }
    order=[:HP,:ATTACK,:DEFENSE,:SPEED,:SPECIAL_ATTACK,:SPECIAL_DEFENSE]
    EXPECTED_SPECIES.each do |species,form,stats,types|
      data=GameData::Species.get_species_form(species,form)
      check.call("#{species},#{form} stats",order.map { |s| data.base_stats[s] }==stats)
      check.call("#{species},#{form} types",data.types==types)
      check.call("#{species},#{form} generation",data.generation_label==NAME)
      expected=PRESENTATION[[species,form]]
      check.call("#{species},#{form} name",(form>0 ? data.form_name : data.name)==expected[0])
      check.call("#{species},#{form} description",data.pokedex_entry==expected[1])
      check.call("#{species},#{form} height",data.height==(expected[2]*10).round) if expected[2]
      check.call("#{species},#{form} weight",data.weight==(expected[3]*10).round) if expected[3]
    end
    PENDING.each { |id| check.call("#{id} draft excluded from battle catalog",!GameData::Species.try_get(id)) }
    EXPECTED_SPECIES.each do |species,form,stats,types|
      next if form==0
      mon=Pokemon.new(species,50,$player,true,false)
      mon.item=('DP'+species.to_s+'ITE').to_sym
      check.call("#{species} mega stone",mon.getMegaForm==form)
    end
    # Validate author assets through the same resolution used by the engine.
    CRIES.each do |id|
      filename=GameData::Species.cry_filename(id)
      resolved=filename && pbResolveAudioSE(filename)
      check.call("#{id} author cry",resolved && File.file?(resolved) && File.binread(resolved,4)=='RIFF')
    end
    STONES.each do |id|
      filename=GameData::Item.icon_filename(id)
      image=Bitmap.new(filename)
      check.call("#{id} author stone art",image.width==64 && image.height==64)
      image.dispose
    end
    {EXEGGUTOR: [:SUNSTONE,:ARCHGUTOR], ELECTRODE: [:FASTBALL,:DYNAMOTRODE], MAGNETON: [:SHINYSTONE,:MAGNETRIX], MAGIKARP: [:DAWNSTONE,:MAGISCALE], OMANYTE: [:DUSKSTONE,:AMMNOID], SWADLOON: [:LEAFSTONE,:SWADLOADNE]}.each do |from,pair|
      mon=Pokemon.new(from,50,$player,true,false)
      check.call("Native item evolution #{from} -> #{pair[1]}",mon.check_evolution_on_use_item(pair[0])==pair[1])
    end
    {AMMNOID: [42,:CEPHALONID], STUNFISK: [47,:STUNDRIFT]}.each do |from,pair|
      mon=Pokemon.new(from,pair[0]-1,$player,true,false)
      check.call("#{from} level threshold enforced",mon.check_evolution_on_level_up!=pair[1])
      mon.level=pair[0]
      check.call("Native level evolution #{from} -> #{pair[1]}",mon.check_evolution_on_level_up==pair[1])
    end
    ENCOUNTERS.each do |map,ids|
      data=GameData::Encounter.get(map,0)
      slots=data.types[:Land]
      check.call("#{map} encounter weights sum 100",slots.sum { |s| s[0] }==100)
      ids.each { |id| check.call("#{id} present in #{map}",slots.any? { |s| s[1]==id }) }
      check.call("#{map} excludes draft Pokemon",slots.none? { |s| PENDING.include?(s[1]) })
    end
    check.call('Laboratory has Mega Ring',$bag.has?(:MEGARING))
    {EXEGGUTOR: :ARCHGUTOR,ELECTRODE: :DYNAMOTRODE,MAGNETON: :MAGNETRIX,MAGIKARP: :MAGISCALE,OMANYTE: :AMMNOID,AMMNOID: :CEPHALONID,STUNFISK: :STUNDRIFT,SWADLOON: :SWADLOADNE}.each do |from,to|
      check.call("Evolution #{from} -> #{to}",GameData::Species.get(from).evolutions.any? { |e| e[0]==to })
    end
    arbok=Pokemon.new(:ARBOK,50,$player,true,false);arbok.item=:DPARBOKITE
    opponent=Pokemon.new(:PIKACHU,50,$player,true,false)
    mega_battle=Battle.new(Battle::DebugSceneNoVisuals.new,[arbok],[opponent],[$player],nil)
    mega_actor=Battle::Battler.new(mega_battle,0);mega_actor.pbInitialize(arbok,0);mega_battle.battlers[0]=mega_actor
    check.call('Arbok can activate the custom Mega Evolution',mega_battle.pbCanMegaEvolve?(0))
    arch=Pokemon.new(:ARCHGUTOR,50,$player,true,false);arch.ability=:MEGASOL
    rival=Pokemon.new(:PIKACHU,50,$player,true,false)
    battle=Battle.new(Battle::DebugSceneNoVisuals.new,[arch],[rival],[$player],nil)
    actor=Battle::Battler.new(battle,0);actor.pbInitialize(arch,0);battle.battlers[0]=actor
    target=Battle::Battler.new(battle,1);target.pbInitialize(rival,0);battle.battlers[1]=target
    check.call('Mega Sol does not create field weather',battle.field.weather==:None)
    check.call('Mega Sol outside own move',actor.effectiveWeather==:None)
    sun=Battle::Move.from_pokemon_move(battle,Pokemon::Move.new(:SOLARBEAM))
    fire=Battle::Move.from_pokemon_move(battle,Pokemon::Move.new(:EMBER))
    BlueDessastreParadoxal.with_move_user(battle,actor) do
      check.call('Mega Sol personal sun',actor.effectiveWeather==:Sun)
      check.call('Other Pokemon does not receive personal sun',target.effectiveWeather==:None)
      check.call('Solar Beam without charging',sun.pbIsChargingTurn?(actor)==false)
      multipliers={power_multiplier:1.0,attack_multiplier:1.0,defense_multiplier:1.0,final_damage_multiplier:1.0}
      fire.pbCalcDamageMults_Weather(actor,target,1,:FIRE,40,multipliers)
      check.call('Own Fire move sun multiplier',multipliers[:final_damage_multiplier]==1.5)
      actor.effects[PBEffects::GastroAcid]=true
      check.call('Suppressed ability has no personal sun',actor.effectiveWeather==:None)
      actor.effects[PBEffects::GastroAcid]=false
    end
    BlueDessastreParadoxal.with_move_user(battle,target) do
      multipliers={power_multiplier:1.0,attack_multiplier:1.0,defense_multiplier:1.0,final_damage_multiplier:1.0}
      fire.pbCalcDamageMults_Weather(target,actor,1,:FIRE,40,multipliers)
      check.call('Incoming Fire receives no Mega Sol boost',multipliers[:final_damage_multiplier]==1.0)
    end
    check.call('Field weather remains unchanged',battle.field.weather==:None)
    check.call('Move context cleared',battle.instance_variable_get(:@blue_dp_move_user).nil?)
    check.call('Fast Ball supports author evolution',GameData::Item.get(:FASTBALL).is_evolution_stone?)
    check.call('Official Bulbasaur preserved',order.map { |s| GameData::Species.get(:BULBASAUR).base_stats[s] }==[45,49,49,45,65,65])
    lines << 'RESULT=PASS'
    true
  rescue StandardError => error
    lines << "RESULT=FAIL | #{error.class}: #{error.message}"
    lines.concat(error.backtrace || [])
    false
  ensure
    File.binwrite('Data/blue-generation-validation.txt',lines.join("\n")+"\n")
  end
end
