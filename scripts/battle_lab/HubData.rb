# Original native team builder/importer. External text is parsed, never evaluated.
module BlueBattleHub
  DIR='BlueHub'
  STATS=[:HP,:ATTACK,:DEFENSE,:SPECIAL_ATTACK,:SPECIAL_DEFENSE,:SPEED].freeze
  SHORT=['HP','Atk','Def','SpA','SpD','Spe'].freeze
  class ImportError < StandardError;end
  def self.token(value)
    value.to_s.tr('éÉèÈêÊáÁàÀâÂãÃíÍóÓôÔõÕúÚüÜçÇ♀♂','eEeEeEaAaAaAaAiIoOoOoOuUuUcCfm').downcase.gsub(/[^a-z0-9]/,'')
  end
  def self.real(data)
    data.respond_to?(:real_name) ? data.real_name : data.name
  end
  def self.species
    @species ||= begin
      list=[];GameData::Species.each { |s| list << s if s.base_stats.values.sum>0 };list.sort_by { |s| display(s).downcase }
    end
  end
  def self.display(s)
    s.form>0 && s.form_name && !s.form_name.empty? ? "#{s.name} / #{s.form_name}" : s.name
  end
  def self.form_label(s)
    return real(s) if s.form==0
    base=real(GameData::Species.get(s.species))
    form=s.respond_to?(:real_form_name) ? s.real_form_name.to_s : s.form_name.to_s
    form=form.gsub(/#{Regexp.escape(base)}/i,'').gsub(/\b(?:Forme?|Evolution)\b/i,'').strip
    {'Alolan'=>'Alola','Galarian'=>'Galar','Hisuian'=>'Hisui','Paldean'=>'Paldea','Female'=>'F','Male'=>'M'}.each { |a,b| form=form.gsub(/\b#{a}\b/i,b) }
    form=form.gsub(/\s+/,'-')
    "#{base}-#{form}"
  end
  def self.index(kind)
    @indexes ||= {}
    @indexes[kind] ||= begin
      result={}
      values=[]
      if kind==:species;values=species
      else;GameData.const_get(kind.to_s.capitalize).each { |data| values << data };end
      values.each do |s|
        names=[s.id.to_s]
        names << real(s) if kind!=:species || s.form==0
        names << form_label(s) if kind==:species && s.form>0
        names.each { |n| result[token(n)]=s }
      end
      result
    end
  end
  def self.resolve(kind,value)
    index(kind)[token(value)] || raise(ImportError,"#{kind==:species ? 'Pokemon/forma' : kind.to_s}: #{value} nao existe nesta base.")
  end
  def self.header(line)
    pokemon,item=line.split(/\s+@\s+/,2)
    gender=nil
    if pokemon.sub!(/\s*(?:\((M|F)\)|\[(Male|Female)\])\s*\z/i,'')
      gender=[$1,$2].compact.first.to_s.downcase.start_with?('f') ? 1 : 0
    end
    nickname=''
    if pokemon =~ /\A(.+?)\s+\(([^()]+)\)\z/
      nickname=$1;pokemon=$2
    end
    {'pokemon'=>pokemon.strip,'nickname'=>nickname.strip,'item'=>item.to_s.strip,'gender'=>gender,'level'=>100,'nature'=>'Hardy','ability'=>'','shiny'=>false,'tera'=>'','evs'=>Array.new(6,0),'ivs'=>Array.new(6,31),'moves'=>[],'happiness'=>255}
  end
  def self.stat_line(raw,max)
    result=Array.new(6,max==31 ? 31 : 0)
    raw.split('/').each do |part|
      m=part.strip.match(/\A(\d+)\s+(HP|Atk|Def|SpA|SpD|Spe)\z/i)
      raise ImportError,'Distribuicao de atributos invalida: '+part unless m
      i=SHORT.index { |s| s.downcase==m[2].downcase };value=m[1].to_i
      raise ImportError,"Atributo deve estar entre 0 e #{max}." unless value.between?(0,max)
      result[i]=value
    end
    raise ImportError,'O total de EVs nao pode ultrapassar 510.' if max==252 && result.sum>510
    result
  end
  def self.parse(text)
    raise ImportError,'Time vazio ou maior que 64 KB.' unless text.is_a?(String) && !text.strip.empty? && text.bytesize<=65536
    rows=[];row=nil
    text.gsub(/\r\n?/,"\n").each_line do |raw|
      line=raw.strip
      next if line.empty? || line.start_with?('#','===')
      if line.start_with?('- ')
        raise ImportError,'Golpe sem cabecalho de Pokemon.' unless row
        row['moves'] << line[2..].strip
      elsif line =~ /\A(.+?) Nature\z/i
        raise ImportError,'Nature sem Pokemon.' unless row
        row['nature']=$1
      elsif line =~ /\A(Ability|Level|EVs|IVs|Shiny|Tera Type|Happiness|Gender|Pokeball|Dynamax Level|Gigantamax):\s*(.*)\z/i
        raise ImportError,'Detalhe sem Pokemon.' unless row
        key=$1.downcase;value=$2
        case key
        when 'ability' then row['ability']=value
        when 'level','happiness','dynamax level'
          raise ImportError,'Numero invalido: '+value unless value.match?(/\A\d+\z/)
          row[{'level'=>'level','happiness'=>'happiness','dynamax level'=>'dynamax'}[key]]=value.to_i
        when 'evs' then row['evs']=stat_line(value,252)
        when 'ivs' then row['ivs']=stat_line(value,31)
        when 'tera type' then row['tera']=value
        when 'pokeball' then row['ball']=value
        when 'shiny','gigantamax'
          raise ImportError,'Use Yes ou No em '+key unless ['yes','no'].include?(value.downcase)
          row[key]=value.downcase=='yes'
        when 'gender' then row['gender']=value.downcase.start_with?('f') ? 1 : 0
        end
      else
        rows << row if row
        raise ImportError,'Um time pode ter no maximo seis Pokemon.' if rows.length>=6
        row=header(line)
      end
    end
    rows << row if row
    raise ImportError,'Nenhum Pokemon encontrado.' if rows.empty?
    rows
  end
  def self.make_move(id)
    m=Pokemon::Move.new(id);m.ppup=3;m.pp=m.total_pp;m
  end
  def self.build(row)
    errors=[];data=nil;item=nil
    begin;data=resolve(:species,row['pokemon']);rescue ImportError=>e;errors << e.message;end
    stone=data && data.mega_stone
    begin
      item=resolve(:item,row['item']) unless row['item'].to_s.empty?
    rescue ImportError=>e
      # This base uses a generic stone for the ZA Floette Mega. Other unknown
      # items remain errors, even when a Mega form was requested.
      alias_stone=stone && data.species==:FLOETTE && token(row['item'])==token('Floettite')
      errors << e.message unless alias_stone
    end
    raise ImportError,errors.join(' ') unless errors.empty?
    level=row['level'];raise ImportError,'Nivel deve estar entre 1 e 100.' unless level.is_a?(Integer) && level.between?(1,100)
    if row['gender']==1 && data.form==0
      female=index(:species)[token(real(data)+'-F')];data=female if female
    end
    target=data
    if stone && item && item.id!=stone && !item.is_mega_stone?
      raise ImportError,'A forma Mega requer uma pedra Mega; '+item.name+' nao e uma pedra.'
    end
    if data.mega_stone || data.mega_move
      item=GameData::Item.get(data.mega_stone) if data.mega_stone
      data=GameData::Species.get_species_form(data.species,data.unmega_form)
    end
    mon=BlueBattleLab.build(data.id,level)
    mon.ability_index=0
    mon.instance_variable_set(:@blue_hub_mega,target.id) if target.id!=data.id
    if stone && !row['item'].to_s.empty? && token(row['item'])!=token(real(item))
      mon.instance_variable_set(:@blue_hub_source_item,row['item'])
      mon.instance_variable_set(:@blue_hub_import_note,row['item']+' -> '+item.name+' (pedra usada pela engine)')
    end
    mon.item=item&.id
    mon.name=row['nickname'].to_s[0,24]
    mon.gender=row['gender'] unless row['gender'].nil?
    mon.shiny=row['shiny']==true
    mon.nature=resolve(:nature,row['nature']).id
    unless row['ability'].to_s.empty?
      ability=resolve(:ability,row['ability'])
      # A Mega paste can contain either the pre-Mega or post-Mega ability.
      available=mon.getAbilityList.map(&:first)
      if available.include?(ability.id)
        mon.ability_index=mon.getAbilityList.find { |a| a[0]==ability.id }[1]
      elsif target.id==data.id || !(target.abilities+target.hidden_abilities).include?(ability.id)
        raise ImportError,'Habilidade incompativel com '+data.name+': '+row['ability']
      end
    end
    [['evs',252,mon.ev],['ivs',31,mon.iv]].each do |key,max,stats|
      values=row[key]
      raise ImportError,'Distribuicao invalida de '+key unless values.is_a?(Array) && values.length==6 && values.all? { |n| n.is_a?(Integer) && n.between?(0,max) }
      raise ImportError,'O total de EVs nao pode ultrapassar 510.' if key=='evs' && values.sum>510
      STATS.each_with_index { |stat,i| stats[stat]=values[i] }
    end
    raise ImportError,'Use de um a quatro golpes.' unless row['moves'].is_a?(Array) && row['moves'].length.between?(1,4)
    ids=row['moves'].map { |m| resolve(:move,m.sub(/\s*\[[^\]]+\]\z/,'' )).id }
    raise ImportError,'Nao repita golpes.' unless ids.uniq.length==ids.length
    mon.moves=ids.map { |id| make_move(id) }
    unless row['tera'].to_s.empty?
      type=resolve(:type,row['tera']);raise ImportError,'Tera Type indisponivel.' unless mon.respond_to?(:tera_type=)
      mon.tera_type=type.id
    end
    happiness=row['happiness'] || 255
    raise ImportError,'Happiness deve estar entre 0 e 255.' unless happiness.between?(0,255)
    mon.happiness=happiness
    mon.poke_ball=resolve(:item,row['ball']).id if row['ball'] && !row['ball'].empty?
    if row['dynamax'] && mon.respond_to?(:dynamax_lvl=)
      raise ImportError,'Dynamax Level deve estar entre 0 e 10.' unless row['dynamax'].between?(0,10)
      mon.dynamax_lvl=row['dynamax']
    end
    mon.gmax_factor=row['gigantamax'] if row.key?('gigantamax') && mon.respond_to?(:gmax_factor=)
    mon.calc_stats;mon.heal;mon
  end
  def self.preview(text)
    parse(text).each_with_index.map do |row,i|
      begin;{'index'=>i,'name'=>row['pokemon'],'pokemon'=>build(row),'error'=>nil}
      rescue StandardError=>e;{'index'=>i,'name'=>row['pokemon'],'pokemon'=>nil,'error'=>e.message};end
    end
  end
  def self.export(team)
    team.map do |mon|
      wanted=mon.instance_variable_get(:@blue_hub_mega)
      data=GameData::Species.get(wanted || mon.species_data.id)
      name=form_label(data)
      name="#{mon.name} (#{name})" if mon.nicknamed?
      name+=' (M)' if mon.gender==0 && !mon.genderless?
      name+=' (F)' if mon.gender==1 && !mon.genderless?
      name+=' @ '+(mon.instance_variable_get(:@blue_hub_source_item) || real(mon.item)) if mon.item
      lines=[name,'Ability: '+real(mon.ability),'Level: '+mon.level.to_s]
      lines << 'Shiny: Yes' if mon.shiny?
      lines << 'Tera Type: '+real(GameData::Type.get(mon.tera_type)) if mon.respond_to?(:tera_type)
      lines << 'Happiness: '+mon.happiness.to_s
      lines << 'EVs: '+STATS.each_with_index.filter_map { |s,i| "#{mon.ev[s]} #{SHORT[i]}" if mon.ev[s]>0 }.join(' / ') if mon.ev.values.sum>0
      lines << 'IVs: '+STATS.each_with_index.filter_map { |s,i| "#{mon.iv[s]} #{SHORT[i]}" if mon.iv[s]!=31 }.join(' / ') if mon.iv.values.any? { |n| n!=31 }
      lines << real(mon.nature)+' Nature'
      lines.concat(mon.moves.map { |m| '- '+real(GameData::Move.get(m.id)) })
      lines.join("\n")
    end.join("\n\n")+"\n"
  end
  def self.url(raw)
    m=raw.strip.match(/\Ahttps:\/\/pokepast\.es\/([a-f0-9]{16})(?:\/raw)?\/?\z/i)
    raise ImportError,'Use um link https://pokepast.es/ seguido do ID de 16 caracteres.' unless m
    'https://pokepast.es/'+m[1].downcase+'/raw'
  end
  def self.fetch(raw)
    response=HTTPLite.get(url(raw),{'User-Agent'=>'BlueBattleHub/1.0'})
    raise ImportError,'Nao foi possivel baixar o Pokepaste. Copie o texto do time e use Colar.' unless response.is_a?(Hash) && response[:status]==200
    body=response[:body]
    raise ImportError,'Pokepaste vazio ou muito grande.' unless body.is_a?(String) && body.bytesize.between?(1,65536)
    body.force_encoding('UTF-8')
  end
  def self.atomic(path,raw)
    Dir.mkdir(DIR) unless Dir.exist?(DIR)
    temp=path+'.tmp'
    File.open(temp,'wb') { |f| f.write(raw);f.flush }
    # Windows Ruby rename cannot replace an existing target on every runtime.
    backup=path+'.bak';File.delete(backup) if File.file?(backup)
    File.rename(path,backup) if File.file?(path)
    begin;File.rename(temp,path)
    rescue Exception;File.rename(backup,path) if File.file?(backup);raise
    ensure;File.delete(temp) if File.file?(temp);end
  end
  def self.save_session(teams,names,format,ai)
    return if BlueBattleLab::SMOKE
    data=[1,*teams.map { |t| export(t) },names,format,ai,BlueBattleOptions.snapshot(:lab),BlueSpriteQuality.mode.to_s]
    atomic(DIR+'/session.rxdata',Marshal.dump(data))
  end
  def self.load_session
    return nil unless File.file?(DIR+'/session.rxdata')
    raise ImportError,'Sessao muito grande.' if File.size(DIR+'/session.rxdata')>150000
    row=load_data(DIR+'/session.rxdata')
    raise ImportError,'Sessao incompativel.' unless row.is_a?(Array) && row.length==8 && row[0]==1 && ['single','double'].include?(row[4])
    raise ImportError,'Nomes de time invalidos.' unless row[3].is_a?(Array) && row[3].length==2 && row[3].all? { |s| s.is_a?(String) && s.length.between?(1,64) }
    raise ImportError,'Perfil de IA indisponivel.' unless BlueRadicalAI::CONFIG['profiles'].key?(row[5])
    teams=[row[1],row[2]].map do |text|
      entries=preview(text);raise ImportError,'Time salvo tem dados indisponiveis.' if entries.any? { |e| e['error'] }
      entries.map { |e| e['pokemon'] }
    end
    [teams,row[3],row[4],row[5],row[6],row[7]]
  rescue StandardError=>e
    BlueBattleLab.log('HUB_SESSION_WARNING | '+e.message);nil
  end
  def self.library
    Dir.mkdir(DIR) unless Dir.exist?(DIR)
    Dir[DIR+'/team-*.txt'].sort.reverse
  end
  def self.save_team(team,name)
    path=DIR+'/team-'+Time.now.strftime('%Y%m%d-%H%M%S')+'-'+rand(1000000).to_s+'.txt'
    atomic(path,'# '+name.to_s.gsub(/[\r\n]/,' ')[0,64]+"\n"+export(team));path
  end
end
