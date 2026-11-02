# Cosmetic weight impact, independent of damage, timing choices or battle stats.
module BlueWeightEntry
  def self.profile(pokemon)
    metrics=GameData::SpeciesMetrics.get_species_form(pokemon.species,pokemon.form)
    return nil if pokemon.hasType?(:FLYING) || pokemon.ability_id==:LEVITATE || metrics.front_sprite_altitude>0
    kg=pokemon.species_data.weight/10.0
    return nil if kg<50
    kg>=300 ? {tier:3,shake:5,dust:12,se:'Rock Smash',volume:80,pitch:80} :
      (kg>=150 ? {tier:2,shake:3,dust:8,se:'Battle damage normal',volume:60,pitch:85} :
      {tier:1,shake:1,dust:0,se:'Player bump',volume:40,pitch:100})
  end
  def self.schedule(animation,picture,battler,sprite,at)
    return unless battler && battler.pokemon
    profile=profile(battler.pokemon);return unless profile
    picture.setSE(at,profile[:se],profile[:volume],profile[:pitch])
    picture.moveDelta(at,1,0,profile[:shake]);picture.moveDelta(at+1,3,0,-profile[:shake])
    # A short, closed displacement leaves the battlefield at its original origin.
    sprites=animation.instance_variable_get(:@sprites)
    shadow=sprites['shadow_'+battler.index.to_s]
    ground=shadow ? [shadow.x,shadow.y] : Battle::Scene.pbBattlerPosition(battler.index,sprite.sideSize)
    ground_y=[ground[1],Graphics.height-108].min
    ['battle_bg','battle_bg2'].each do |key|
      background=sprites[key];next unless background
      shake=animation.addSprite(background);amp=profile[:shake]
      [[at,amp],[at+1,-2*amp],[at+3,2*amp],[at+5,-amp]].each { |delay,dx| shake.moveDelta(delay,1,dx,0) }
    end
    profile[:dust].times do |i|
      dust=BitmapSprite.new(20,12,animation.instance_variable_get(:@viewport))
      12.times do |y|
        20.times do |x|
          next if ((x-9.5)/10.0)**2+((y-5.5)/6.0)**2>1 || (x+y+i)%7==0
          dust.bitmap.set_pixel(x,y,Color.new(176,155,125,200))
        end
      end
      direction=i.even? ? -1 : 1;dust.x=ground[0]+direction*(8+(i/2)*5);dust.y=ground_y-4;dust.z=sprite.z+1;dust.visible=false
      p=animation.addSprite(dust,PictureOrigin::CENTER);animation.instance_variable_get(:@tempSprites) << dust
      p.setVisible(0,false);p.setVisible(at,true);p.setOpacity(at,180)
      p.moveDelta(at,12,direction*(18+i*2),-4-(i%3)*3);p.moveZoom(at,12,160)
      p.moveOpacity(at+3,9,0);p.setVisible(at+12,false)
    end
    events=animation.instance_variable_get(:@blue_weight_events) || []
    events << {species:battler.species,at:at,tier:profile[:tier],dust:profile[:dust],ground:[ground[0],ground_y]}
    animation.instance_variable_set(:@blue_weight_events,events)
  end
end
