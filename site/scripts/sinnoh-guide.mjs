// CH17 — source-grounded Sinnoh guide data. Pure generator; NOT native gameplay.
const reject=message=>{throw new Error('sinnoh-guide-invalid: '+message);};
const keys=['coverage','pending','teams','badges','encounters','story','music','regions'];
const repoPaths={
  coverage:'data/regions/sinnoh-coverage.json',
  pending:'site/public/data/pending-regions.json',
  teams:'data/regions/sinnoh-trainer-teams-ch15.json',
  badges:'data/regions/sinnoh-badges-hms-contract.json',
  encounters:'data/regions/sinnoh-symbolic-encounters.json',
  story:'data/regions/sinnoh-story-ch14-contract.json',
  music:'data/regions/sinnoh-music-ch16.json',
  regions:'site/public/data/regions.json'
};
export const sinnohSourcePaths=Object.freeze(repoPaths);
const planned=(row,field='gameplay_verified')=>row&&row[field]===false;
const nameOf=e=>String(e?.name??e?.label??'').trim();
const requireUnique=(values,label)=>{
  if(values.length!==new Set(values).size)reject('duplicated '+label);
};
export function generateSinnohGuide(sources){
  if(!sources||keys.some(key=>!sources[key]))reject('missing CH11–CH16 source');
  const {coverage,pending,teams,badges,encounters,story,music,regions}=sources;
  const pendingRegion=pending.regions?.SINNOH;
  // S29: o Blue usa o maior nivel nao-ovo da party. O registro regional
  // nao possui um cap numerico confirmado; badge/esmeralda nao vira level.
  if(teams.ui_policy?.publish_historical_fixed_levels!==false||
     teams.ui_policy?.render_actual_levels_from!=='BLUE_CAMPAIGN_DYNAMIC_SCALING_ONLY'||
     teams.dynamic_balance?.reference_level!=='highest_non_egg_party_level'||
     teams.dynamic_balance?.normal_percent!==70||
     teams.dynamic_balance?.master_percent!==90||
     encounters.global_progress?.reference_party!=='highest_non_egg_party_level'||
     encounters.global_progress?.regional_numeric_level_cap!==null||
     badges.no_cross_region_key_item_or_hm_transfer!==true)
    reject('S29 dynamic level policy unverified');
  if(coverage.region!=='SINNOH'||coverage.status!=='PLANNED_AUDIT_CHECKLIST_ONLY'||
      coverage.integrity?.verified_runtime_entries!==0||
      pending.state!=='REFERENCE_NOT_NATIVE_GAMEPLAY'||!pendingRegion||
      teams.region!=='SINNOH'||teams.status!=='HISTORICAL_REFERENCE_ONLY_NOT_INSTALLED'||
      !planned(teams)||teams.native_pbs_compilation_verified!==false||teams.can_install!==false||
      !planned(badges)||badges.status!=='PLANNED_CONTRACT_NOT_INSTALLED'||
      badges.approved_for_install!==false||badges.native_map_ids_assigned!==false||
      !planned(encounters)||encounters.may_install!==false||
      encounters.status!=='PLANNED_REFERENCE_ONLY_NOT_INSTALLED'||
      !planned(story)||story.native_events_installed!==false||story.can_install!==false||
      !planned(music)||music.recordings?.length!==0||music.can_install!==false||
      music.status!=='SYMBOLIC_CUES_PLANNED_NOT_INSTALLED'||
      regions.regions?.SINNOH?.status!=='planned')reject('false native installation or incompatible source');
  if(!Array.isArray(pendingRegion.areas)||pendingRegion.areas.length<75||
     !Array.isArray(pendingRegion.trainers)||pendingRegion.trainers.length<30||
     !Array.isArray(coverage.phases)||coverage.phases.length!==8||
     !Array.isArray(teams.trainers)||teams.trainers.length!==13||
     !Array.isArray(badges.rules)||badges.rules.length!==8||
     !Array.isArray(story.steps)||story.steps.length!==22||
     !Array.isArray(music.cues)||music.cues.length!==46||
     !Array.isArray(encounters.areas)||encounters.areas.length!==21)reject('incomplete catalog');
  if(coverage.phases.some(p=>p.areas?.some(a=>a.verified!==false||a.source_map_ids?.length||a.destination_map_ids?.length)||
      p.events?.some(e=>e.verified!==false)))reject('native map/event declared without proof');
  if(badges.rules.some(r=>r.verified_gym_event!==false||r.verified_hm_pickup_event!==false))reject('HM reward verified without native event');
  // S28: os 13 times sao composições HISTORICAS de Platinum. O repositorio
  // nao contem PBS de Sinnoh e nao se deve converter revanche em Full Power.
  if(teams.ui_policy?.publish_rematch_as_blue_strongest!==false||
     teams.ui_policy?.publish_unverified_blue_native_as_installed!==false||
     teams.native_event_battle_bindings_verified!==false||
     teams.may_write_pbs!==false)reject('S28 team policy would claim native gameplay');
  if(teams.trainers.some(t=>{
    const first=t.first_battle, rematch=t.historical_rematch;
    const native=t.native_pbs, strongest=t.blue_strongest;
    return !first||first.source!=='PLATINUM_FIRST_BATTLE'||
      first.source_game!=='POKEMON_PLATINUM'||
      first.status!=='HISTORICAL_REFERENCE_ONLY'||
      first.levels_are_not_runtime_levels!==true||
      first.verified_in_blue_pbs!==false||
      !Array.isArray(first.species)||first.species.length<1||
      first.species.length>6||first.species.some(s=>!s||typeof s!=='string')||
      !Array.isArray(first.historical_levels)||
      first.historical_levels.length!==first.species.length||
      (rematch!==null&&(
        t.role==='GYM_LEADER'||rematch.source!=='PLATINUM_LEAGUE_REMATCH'||
        rematch.source_game!=='POKEMON_PLATINUM'||
        rematch.status!=='HISTORICAL_REFERENCE_ONLY'||
        rematch.levels_are_not_runtime_levels!==true||
        rematch.verified_in_blue_pbs!==false||
        !Array.isArray(rematch.species)||
        rematch.species.length!==first.species.length||
        !Array.isArray(rematch.historical_levels)||
        rematch.historical_levels.length!==rematch.species.length))||
      !native||native.status!=='NATIVE_PBS_NOT_AVAILABLE_OR_VERIFIED'||
      native.team!==null||native.source_file!==null||native.source_sha256!==null||
      native.compiled!==false||native.event_bound!==false||
      native.game_exe_verified!==false||
      !strongest||strongest.status!=='BLUE_FULL_POWER_VARIANT_NOT_VERIFIED'||
      strongest.species!==null||strongest.source_sha256!==null||
      strongest.game_exe_verified!==false;
  }))reject('S28 catalog or native team status inconsistent');
  if(encounters.areas.some(a=>a.installed!==false||a.native_pbs_verified!==false||
      a.map_id!==null||a.encounter_slots?.length||a.weight_percentages!==null||
      a.level_ranges!==null))reject('wild encounter falsely installed');
  if(story.steps.some(s=>s.native_event_installed!==false||s.native_event_verified!==false||
      s.grants_map!==false||s.grants_badge!==false||s.grants_item!==false))reject('story reward falsely granted');
  if(music.cues.some(c=>c.enabled!==false||c.track_path!==null||c.physical_map_id!==null||
      c.license_verified!==false))reject('unlicensed music shown as active');
  const ids=pendingRegion.areas.map(a=>a.id);
  requireUnique(ids,'area IDs');
  const encountersBySymbol=new Map(encounters.areas.filter(a=>a.area_symbol)
    .map(a=>[a.area_symbol,a]));
  requireUnique([...encountersBySymbol.keys()],'encounter symbols');
  const phases=coverage.phases.map(p=>({
    number:p.phase,title:p.section,status:'planned',
    areaCount:p.areas.length,eventCount:p.events.length
  }));
  requireUnique(phases.map(p=>p.number),'phase numbers');
  const phaseNumbers=new Set(phases.map(p=>p.number));
  const areas=pendingRegion.areas.map(a=>{
    if(a.status!=='not_added'||!nameOf(a)||
        (a.phase!=null&&!phaseNumbers.has(a.phase))||
        'map_id' in a||'level' in a||'rate' in a)reject('unverified area entered as playable');
    const match=encountersBySymbol.get(a.source_symbol);
    return {id:a.id,name:nameOf(a),phase:a.phase??null,
      referenceSymbol:a.source_symbol??null,status:'planned',
      notes:a.notes??'Mapas e encontros nativos ainda não confirmados.',
      speciesCandidates:match?[...match.reference_species]:[],
      encounterAuditOnly:!!match,confirmedWildEncounters:0};
  });
  const trainers=pendingRegion.trainers.map(t=>{
    if(t.status!=='not_added'||!nameOf(t)||'level' in t||'map_id' in t)
      reject('unverified trainer entered as playable');
    return {id:t.id,name:t.name,area:t.area??null,notes:t.notes??null,
      status:'planned',teamInstalled:false};
  });
  requireUnique(trainers.map(t=>t.id),'trainer IDs');
  const bosses=teams.trainers.map(t=>({
    id:t.id,name:t.name,role:t.role,order:t.order,badge:t.badge,
    city:t.reference_city??null,status:'planned',
    speciesReference:[...t.first_battle.species],
    rematchSpeciesReference:t.historical_rematch?[...t.historical_rematch.species]:null,
    referenceGame:'Pokémon Platinum',
    // S28: composicao de referencia, nunca PBS compilado nem nivel runtime.
    teamAudit:{
      firstBattle:{origin:'PLATINUM_FIRST_BATTLE',
        memberCount:t.first_battle.species.length,verifiedInBlue:false},
      historicalRematch:t.historical_rematch?{
        origin:'PLATINUM_LEAGUE_REMATCH',
        memberCount:t.historical_rematch.species.length,verifiedInBlue:false}:null,
      blueFullPower:{status:'pending',species:null,verified:false},
      nativePBS:{status:'pending',team:null,compiled:false,eventBound:false,
        gameExeVerified:false}
    },
    fullPowerVerified:false,pbsInstalled:false,
    // NO historical_levels: they are not runtime levels.
  }));
  requireUnique(bosses.map(t=>t.id),'boss IDs');
  if(bosses.some(b=>b.teamAudit.firstBattle.memberCount!==b.speciesReference.length||
      (b.rematchSpeciesReference===null)!==(b.teamAudit.historicalRematch===null)||
      (b.teamAudit.historicalRematch&&
       b.teamAudit.historicalRematch.memberCount!==b.rematchSpeciesReference.length)))
    reject('S28 team counts inconsistent');
  if(bosses.filter(b=>b.role==='GYM_LEADER').length!==8||
     bosses.filter(b=>b.role==='ELITE_FOUR').length!==4||
     bosses.filter(b=>b.role==='CHAMPION').length!==1||
     bosses.filter(b=>b.rematchSpeciesReference).length!==5)reject('bad boss breakdown');
  const items=badges.rules.map(r=>({
    id:r.hm_item,badge:r.badge,fieldMove:r.field_move,
    label:r.hm_item+' · '+r.field_move.replaceAll('_',' '),
    status:'planned',pickupVerified:false,regionalOnly:true
  }));
  const badgesSet=new Set(bosses.filter(b=>b.role==='GYM_LEADER').map(b=>b.badge));
  if(items.some(r=>!badgesSet.has(r.badge)))reject('HM badge association unverified');
  requireUnique(items.map(r=>r.id),'HM item IDs');
  const steps=story.steps.map((s,i)=>({
    id:s.id,phase:s.phase,order:i+1,
    title:s.id.replace(/^P\d\d_/,'').replaceAll('_',' '),
    requiresBadges:[...s.requires_local_badges],status:'planned',
    engineHallOfFameRequired:s.proof_kind==='ENGINE_HALL_OF_FAME_CONFIRMED',
    eventInstalled:false
  }));
  if(steps.at(-1).id!=='P09_HALL_OF_FAME'||!steps.at(-1).engineHallOfFameRequired)
    reject('Hall of Fame gate missing');
  return {
    schema:1,region:'SINNOH',sourceGame:'Pokémon Platinum',
    status:'planned',gameplayVerified:false,canPlay:false,
    meaning:'Guia de planejamento: os dados são referências auditadas, não mapas, batalhas, itens ou encontros instalados no Game.exe.',
    counts:{areas:areas.length,trainers:trainers.length,gyms:8,eliteFour:4,champions:1,
      hmItems:items.length,encounterReferenceAreas:encounters.areas.length,
      musicCueReferences:music.cues.length,storySteps:steps.length,
      verifiedNativeMaps:0,verifiedNativeTrainers:0,verifiedNativeItems:0},
    phases,areas,trainers,bosses,items,steps,
    teamCatalog:{
      status:'historical_reference_only',
      historicalTrainerCount:bosses.length,
      regularTrainersWithoutVerifiedTeams:trainers.length,
      verifiedBlueTrainerTeams:0,
      compiledNativePBSTeams:0,
      officialPlatinumRematchReferences:bosses.filter(b=>b.teamAudit.historicalRematch).length,
      blueFullPowerVerifiedTeams:0,
      gameExeVerifiedTeams:0,
      fixedRuntimeLevelsPublished:false
    },
    music:{cueCount:music.cues.length,audioInstalled:false,
      status:'planned',fallback:'Manter BlueMusic/Decades atual'},
    balance:{normalPercent:teams.dynamic_balance.normal_percent,
      masterPercent:teams.dynamic_balance.master_percent,
      note:'Escalonamento dinâmico do Blue; níveis fixos históricos não representam os combates.'},
    // S29: metadados explicativos, NUNCA niveis nem valores lidos de um save.
    levelPolicy:{
      reference:teams.dynamic_balance.reference_level,
      regionalNumericCap:encounters.global_progress.regional_numeric_level_cap,
      badgesDoNotRevealExactLevel:true,
      verifiedRuntimeLevels:false,
      source:'scripts/battle_polish/Campaign.rb',
      fieldEvolutionSource:encounters.blue_evolution_source
    },
    sourcePaths:repoPaths
  };
}
