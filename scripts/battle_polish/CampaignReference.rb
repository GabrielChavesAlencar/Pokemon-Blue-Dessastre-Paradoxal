# Exported by an explicit native validation/request, never by loading a campaign.
# Uses the same replacements and move filters as the actual opponent constructor.
module BlueCampaignReference
  STAGES=[['beginner','Iniciante',0,1,350,60,70],['intermediate','Intermediário',2,4,450,90,70],
    ['advanced','Avançado',5,10,540,nil,70],['master','Master',11,18,nil,nil,90]].freeze
  RULES=%w[Story.rb Balance.rb Campaign.rb].freeze
  def self.pokemon(source,level,cap,move_cap,battle)
    pkmn=Marshal.load(Marshal.dump(source));pkmn.level=level;pkmn.calc_stats
    pkmn=BlueStory.adjust(pkmn,cap) if cap
    BlueTrainerMoves.adjust(pkmn,move_cap,battle) if move_cap
    pkmn
  end
  def self.export(battle)
    started=BlueBattleUI.clock
    output={version:1,format:'2v2 Full Power',referencePlayerLevel:50,
      sourceCRC:Zlib.crc32(File.binread('PBS/trainers_story_mode.txt')),
      rulesCRC:Zlib.crc32(RULES.map { |name| File.binread('Plugins/ZZZZ Blue Story and Presentation/'+name) }.join),masters:{}}
    BlueJourney::GYM_NAMES.each do |name|
      matches=[];GameData::Trainer.each { |data| matches << data if data.real_name==name+' (2v2 Full Power)' }
      raise 'Ambiguous Full Doubles source: '+name unless matches.length==1
      trainer=matches.first.to_trainer
      raise 'Incomplete Full Doubles source: '+name unless trainer.party.length==6
      output[:masters][name]=STAGES.map do |id,label,min,max,cap,move_cap,percent|
        raise 'Campaign profile export exceeded ten minutes' if BlueBattleUI.clock-started>600
        File.write('Data/blue-reference-progress.txt',name+' / '+label)
        team=trainer.party.map do |source|
          selected=pokemon(source,[50*percent/100,1].max,cap,move_cap,battle)
          series=[]
          # Species/item/ability replacement is level-independent. The legal move
          # pool changes only at levels present in the selected form's learnset.
          levels=([1]+selected.getMoveList.map(&:first).select { |n| n>1 && n<=100 }).uniq.sort
          levels.each do |level|
            pkmn=pokemon(source,level,cap,move_cap,battle);moves=pkmn.moves.map { |m| m.id.to_s }
            series << {level:level,moves:moves} if series.empty? || series.last[:moves]!=moves
          end
          Graphics.update;Input.update
          {species:selected.species.to_s,form:selected.form,level:selected.level,
            item:selected.item_id&.to_s,ability:selected.ability&.name,nature:selected.nature_id.to_s,
            evs:selected.ev.transform_keys(&:to_s),ivs:selected.iv.transform_keys(&:to_s),
            moves:selected.moves.map { |m| m.id.to_s },movesByLevel:series}
        end
        {id:id,label:label,format:'Full Doubles',crystals:[min,max],bstCap:cap,movePowerCap:move_cap,
          levelPercent:percent,origin:'blue-engine',team:team}
      end
    end
    File.binwrite('Data/blue-campaign-reference.dat',Marshal.dump(output))
    output
  end
end
