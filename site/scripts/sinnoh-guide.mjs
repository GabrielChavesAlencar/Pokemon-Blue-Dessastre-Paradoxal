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
  if(teams.trainers.some(t=>t.first_battle?.verified_in_blue_pbs!==false||
      t.native_pbs?.compiled!==false||t.native_pbs?.event_bound!==false||
      t.native_pbs?.game_exe_verified!==false||t.blue_strongest?.game_exe_verified!==false))reject('trainer PBS claimed installed');
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
    if(a.status!=='not_added'||!nameOf(a)||!phaseNumbers.has(a.phase)||
        'map_id' in a||'level' in a||'rate' in a)reject('unverified area entered as playable');
    const match=encountersBySymbol.get(a.source_symbol);
    return {id:a.id,name:nameOf(a),phase:a.phase,
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
    fullPowerVerified:false,pbsInstalled:false,
    // NO historical_levels: they are not runtime levels.
  }));
  requireUnique(bosses.map(t=>t.id),'boss IDs');
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
    music:{cueCount:music.cues.length,audioInstalled:false,
      status:'planned',fallback:'Manter BlueMusic/Decades atual'},
    balance:{normalPercent:teams.dynamic_balance.normal_percent,
      masterPercent:teams.dynamic_balance.master_percent,
      note:'Escalonamento dinâmico do Blue; níveis fixos históricos não representam os combates.'},
    sourcePaths:repoPaths
  };
}
