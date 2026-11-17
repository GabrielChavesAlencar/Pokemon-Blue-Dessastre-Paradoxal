// CH18: pure query/filter contract for the non-playable Sinnoh reference guide.
export const SINNOH_TABS=Object.freeze([
  'visao','areas','treinadores','ginasios','liga','itens','progresso','pendencias'
]);
export const SINNOH_PENDING_TYPES=Object.freeze([
  'areas','treinadores','equipes','itens','historia','encontros','musica'
]);
const fail=why=>{throw new Error('sinnoh-guide-invalid: '+why);};
const clean=x=>typeof x==='string'?x.trim().slice(0,100):'';
export const normalizeSinnohText=x=>String(x??'').normalize('NFKD')
  .replace(/[\u0300-\u036f]/g,'').toLowerCase()
  .replace(/\brotas?\b/g,'route').replace(/\s+/g,' ').trim();
const match=(hay,query)=>!query||query.split(' ').every(word=>hay.includes(word));
const joinFields=x=>normalizeSinnohText(x.flat(Infinity).filter(v=>v!=null).join(' '));
const exactKeys=(value,keys)=>value!==null&&typeof value==='object'&&
  !Array.isArray(value)&&Object.keys(value).length===keys.length&&
  keys.every(key=>Object.hasOwn(value,key));
const disallowed=new Set([
  'map_id','mapId','physical_map_id','level','historical_levels','level_ranges',
  'rate','weight_percentages','slots','encounter_slots','trainerVersion',
  'versionPBS','chance','x','y','effectiveLevel','effective_level','levelCap',
  'level_cap','fixedLevel','fixed_level','levelRange','exactLevel','exact_level'
]);
export function validateSinnohGuide(data){
  if(!data||data.schema!==1||data.region!=='SINNOH'||data.sourceGame!=='Pokémon Platinum'||
     data.status!=='planned'||data.canPlay!==false||data.gameplayVerified!==false||
     !data.counts||data.counts.verifiedNativeMaps!==0||
     data.counts.verifiedNativeTrainers!==0||data.counts.verifiedNativeItems!==0||
     !Array.isArray(data.phases)||data.phases.length!==8||
     !Array.isArray(data.areas)||data.areas.length<100||
     !Array.isArray(data.trainers)||data.trainers.length<30||
     !Array.isArray(data.bosses)||data.bosses.length!==13||
     !Array.isArray(data.items)||data.items.length!==8||
     !Array.isArray(data.steps)||data.steps.length!==22||
     data.counts.areas!==data.areas.length||data.counts.trainers!==data.trainers.length||
     data.counts.gyms!==8||data.counts.eliteFour!==4||data.counts.champions!==1||
     data.counts.hmItems!==8||data.counts.storySteps!==22||
     data.counts.encounterReferenceAreas!==21||data.counts.musicCueReferences!==46||
     data.music?.status!=='planned'||data.music?.audioInstalled!==false||
     data.music?.cueCount!==46||data.balance?.normalPercent!==70||
     data.balance?.masterPercent!==90||
     !data.levelPolicy||
     data.levelPolicy.reference!=='highest_non_egg_party_level'||
     data.levelPolicy.regionalNumericCap!==null||
     data.levelPolicy.badgesDoNotRevealExactLevel!==true||
     data.levelPolicy.verifiedRuntimeLevels!==false||
     !data.teamCatalog||
     data.teamCatalog.status!=='historical_reference_only'||
     data.teamCatalog.historicalTrainerCount!==13||
     data.teamCatalog.regularTrainersWithoutVerifiedTeams!==data.trainers?.length||
     data.teamCatalog.verifiedBlueTrainerTeams!==0||
     data.teamCatalog.compiledNativePBSTeams!==0||
     data.teamCatalog.officialPlatinumRematchReferences!==5||
     data.teamCatalog.blueFullPowerVerifiedTeams!==0||
     data.teamCatalog.gameExeVerifiedTeams!==0||
     data.teamCatalog.fixedRuntimeLevelsPublished!==false||
     data.levelPolicy.source!=='scripts/battle_polish/Campaign.rb'||
     data.levelPolicy.fieldEvolutionSource!=='scripts/battle_polish/EvolutionScaling.rb'||
     ['level','levelCap','level_cap','effectiveLevel','effective_level',
      'fixedLevel','fixed_level','historical_levels','exactLevel']
       .some(k=>Object.hasOwn(data.balance,k)||Object.hasOwn(data.levelPolicy,k)))
    fail('metadata or reference counts');
  const groups={areas:data.areas,trainers:data.trainers,bosses:data.bosses,
    items:data.items,steps:data.steps,phases:data.phases};
  for(const [key,records] of Object.entries(groups)){
    const ids=new Set();
    for(const row of records){
      const id=key==='phases'?row?.number:row?.id;
      if(!row||row.status!=='planned'||!id||ids.has(id))fail(key+' status/duplicate');
      ids.add(id);
      for(const field of Object.keys(row))if(disallowed.has(field))fail(key+' invented field '+field);
      if(row.installed===true||row.playable===true||
         row.nativeVerified===true||row.gameplayVerified===true)fail(key+' falsely installed');
    }
  }
  const phases=new Set(data.phases.map(x=>x.number));
  if(data.phases.some(p=>typeof p.number!=='number'||p.areaCount<0||p.eventCount<0)||
    data.areas.some(a=>typeof a.name!=='string'||(a.phase!==null&&!phases.has(a.phase))||
      a.confirmedWildEncounters!==0||!Array.isArray(a.speciesCandidates)||
      a.speciesCandidates.some(x=>typeof x!=='string'))||
    data.trainers.some(t=>typeof t.name!=='string'||t.teamInstalled!==false)||
    data.bosses.some(b=>{
      const audit=b.teamAudit,first=audit?.firstBattle,rematch=audit?.historicalRematch,
            blue=audit?.blueFullPower,native=audit?.nativePBS;
      return b.pbsInstalled!==false||b.fullPowerVerified!==false||
        !exactKeys(audit,['firstBattle','historicalRematch','blueFullPower','nativePBS'])||
        !exactKeys(first,['origin','memberCount','verifiedInBlue'])||
        (rematch!==null&&!exactKeys(rematch,['origin','memberCount','verifiedInBlue']))||
        !exactKeys(blue,['status','species','verified'])||
        !exactKeys(native,['status','team','compiled','eventBound','gameExeVerified'])||
        !Array.isArray(b.speciesReference)||
        !b.speciesReference.length||b.speciesReference.length>6||
        !['GYM_LEADER','ELITE_FOUR','CHAMPION'].includes(b.role)||
        b.referenceGame!=='Pokémon Platinum'||
        first?.origin!=='PLATINUM_FIRST_BATTLE'||
        first?.memberCount!==b.speciesReference.length||
        first?.verifiedInBlue!==false||
        (b.rematchSpeciesReference===null?rematch!==null:
          !Array.isArray(b.rematchSpeciesReference)||
          !b.rematchSpeciesReference.length||
          rematch?.origin!=='PLATINUM_LEAGUE_REMATCH'||
          rematch?.memberCount!==b.rematchSpeciesReference.length||
          rematch?.verifiedInBlue!==false)||
        (b.role==='GYM_LEADER'&&rematch!==null)||
        blue?.status!=='pending'||blue?.species!==null||
        blue?.verified!==false||
        native?.status!=='pending'||native?.team!==null||
        native?.compiled!==false||native?.eventBound!==false||
        native?.gameExeVerified!==false;
    })||
    data.bosses.filter(b=>b.role==='GYM_LEADER').length!==8||
    data.bosses.filter(b=>b.role==='ELITE_FOUR').length!==4||
    data.bosses.filter(b=>b.role==='CHAMPION').length!==1||
    data.items.some(r=>r.pickupVerified!==false||r.regionalOnly!==true)||
    data.steps.some(r=>r.eventInstalled!==false||!Array.isArray(r.requiresBadges))||
    data.steps.at(-1)?.engineHallOfFameRequired!==true)
    fail('record claims native proof');
  return data;
}
const tabKey=tab=>SINNOH_TABS.includes(tab)?tab:'visao';
export function sinnohGuideUrl(tab='visao',params={}){
  const url=new URLSearchParams({aba:tabKey(tab)});
  for(const key of ['fase','busca','pendencia','tipo']){
    const value=clean(params[key]);
    if(value&&value!=='all'&&value!=='todas'&&value!=='todos')
      url.set(key,value);
  }
  return '/sinnoh?'+url.toString();
}
const fields={
  areas:r=>[r.name,r.notes,r.referenceSymbol,r.speciesCandidates,
    r.phase==null?'sem fase':'fase '+r.phase],
  treinadores:r=>[r.name,r.area,r.notes],
  ginasios:r=>[r.name,r.city,r.badge,r.speciesReference,'ginasio '+r.order],
  liga:r=>[r.name,r.city,r.speciesReference,r.rematchSpeciesReference,r.role],
  itens:r=>[r.label,r.id,r.badge,r.fieldMove],
  progresso:r=>[r.title,r.id,r.phase,r.requiresBadges]
};
export function sinnohPendingGroups(data){
  validateSinnohGuide(data);
  return [
    {key:'areas',label:'Mapas e áreas',count:data.areas.length,
      description:'MapIDs, geometria e viagem nativa não verificados.',tab:'areas'},
    {key:'treinadores',label:'Treinadores e NPCs',count:data.trainers.length,
      description:'Vínculo de evento, versão e equipe PBS não certificados.',tab:'treinadores'},
    {key:'equipes',label:'Ginásios, Elite Four e Cynthia',count:data.bosses.length,
      description:'Times de Platinum não são Full Power nem PBS compilados.',tab:'ginasios'},
    {key:'itens',label:'HMs e permissões',count:data.items.length,
      description:'Coleta e insígnias locais não comprovadas na engine.',tab:'itens'},
    {key:'historia',label:'Galactic, Cyrus e Liga',count:data.steps.length,
      description:'Checkpoints sem eventos nativos verificados.',tab:'progresso'},
    {key:'encontros',label:'Encontros selvagens',count:data.counts.encounterReferenceAreas,
      description:'Espécies candidatas sem taxas, níveis ou slots nativos.',tab:'areas'},
    {key:'musica',label:'Chaves musicais',count:data.music.cueCount,
      description:'Sem gravações autorizadas, arquivos ou hooks de Sinnoh.',tab:'visao'}
  ];
}
export function filterSinnohGuide(data,tab='areas',options={}){
  validateSinnohGuide(data);
  const selected=tabKey(tab);
  const search=normalizeSinnohText(clean(options.busca));
  const phase=options.fase==='sem-fase'?'sem-fase':
    data.phases.some(p=>String(p.number)===String(options.fase))?
    String(options.fase):'all';
  const choices={areas:['todas','sem-fase','com-especies','sem-especies'],
    treinadores:['todas','com-area','sem-area'],
    ginasios:['todas'],liga:['todas','com-revanche','sem-revanche'],
    itens:['todas','sem-coleta'],progresso:['todas'],pendencias:['todas']};
  const pendencia=(choices[selected]??['todas']).includes(options.pendencia)?
    options.pendencia:'todas';
  const tipo=SINNOH_PENDING_TYPES.includes(options.tipo)?options.tipo:'todos';
  let rows=[];
  if(selected==='areas')rows=data.areas.filter(r=>
    (phase==='all'||(phase==='sem-fase'?r.phase===null:String(r.phase)===phase))&&
    (pendencia==='sem-fase'?r.phase===null:
     pendencia==='com-especies'?r.speciesCandidates.length>0:
     pendencia==='sem-especies'?r.speciesCandidates.length===0:true));
  else if(selected==='treinadores')rows=data.trainers.filter(r=>
    pendencia==='sem-area'?!r.area:pendencia==='com-area'?!!r.area:true);
  else if(selected==='ginasios')rows=data.bosses.filter(r=>r.role==='GYM_LEADER');
  else if(selected==='liga')rows=data.bosses.filter(r=>
    (r.role==='ELITE_FOUR'||r.role==='CHAMPION')&&
    (pendencia==='com-revanche'?!!r.rematchSpeciesReference:
     pendencia==='sem-revanche'?!r.rematchSpeciesReference:true));
  else if(selected==='itens')rows=data.items;
  else if(selected==='progresso')rows=data.steps;
  else if(selected==='pendencias')rows=sinnohPendingGroups(data).filter(
    r=>tipo==='todos'||r.key===tipo);
  const field=fields[selected]??(r=>[r.label,r.description,r.key]);
  const result=rows.filter(row=>match(joinFields(field(row)),search));
  return {tab:selected,items:result,count:result.length,total:rows.length,
    busca:clean(options.busca),fase:phase,pendencia,tipo,
    noResults:result.length===0};
}
