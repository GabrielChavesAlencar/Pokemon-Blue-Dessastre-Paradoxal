// G06.2: generate read-only Unova site guide from audited contracts.
// This code is executed only by the site build, NOT by Essentials/Game.exe.
export const unovaGuideSources={
  areas:'data/regions/unova-u03-areas.json',
  story:'data/regions/unova-g01-state-contract.json',
  transitions:'data/regions/unova-g01-chapter-transitions.json',
  gyms:'data/regions/unova-g02-gym-story-contracts.json',
  finale:'data/regions/unova-g02-elite-finale-contracts.json',
  postgame:'data/regions/unova-g02-postgame-contracts.json',
  rivals:'data/regions/unova-g03-rivals-plasma-story-contracts.json',
  npcs:'data/regions/unova-sp04-npcs.json'
};
const reject=reason=>{throw new Error('unova-g062-source-invalid: '+reason);};
const unique=(list,key)=>{if(new Set(list.map(x=>x[key])).size!==list.length)reject('duplicate '+key);};
const ensure=(test,msg)=>{if(!test)reject(msg);};
const indexPhase=value=>/^U(0[1-9]|[1-3][0-9])$/.test(value)?Number(value.slice(1)):null;
const contract=(obj,phase)=>ensure(obj?.region==='UNOVA'&&obj.phase===phase&&obj.can_install!==true&&obj.game_exe_tested===false,'unsafe '+phase+' source');

export function generateUnovaGuide({areas,story,transitions,gyms,finale,postgame,rivals,npcs}){
  ensure(areas?.schema===1&&areas.region==='UNOVA'&&areas.phase==='U03'&&areas.state==='PLANNED_REFERENCE_ONLY'&&areas.unova_game_files_audited===false&&areas.may_install===false,'areas must remain planned');
  contract(story,'G01.1');contract(gyms,'G02.2');contract(finale,'G02.3');contract(postgame,'G02.4');contract(rivals,'G03.3');contract(npcs,'SP04');
  ensure(transitions?.phase==='G01.2'&&transitions.region==='UNOVA'&&transitions.native_save_adapter===false&&transitions.game_exe_tested===false,'G01.2 synthetic transitions only');
  ensure(Array.isArray(areas.areas)&&areas.areas.length===74&&Array.isArray(story.chapters)&&story.chapters.length===13&&
   story.chapters[0].index===0&&Array.isArray(story.missions)&&story.missions.length===12&&
   Array.isArray(transitions.transitions)&&transitions.transitions.length===12&&
   Array.isArray(gyms.gyms)&&gyms.gyms.length===8&&
   Array.isArray(finale.elite_members)&&finale.elite_members.length===4&&
   Array.isArray(npcs.characters)&&npcs.characters.length>0&&Array.isArray(rivals.encounters),'source coverage');
  for(const [list,key] of [[areas.areas,'key'],[story.chapters,'key'],[story.missions,'key'],[gyms.gyms,'id'],
   [npcs.characters,'key'],[rivals.encounters,'id'],[finale.elite_members,'key']])unique(list,key);
  const areaIndex=new Map(areas.areas.map(a=>[a.key,a]));
  const chapterIndex=new Map(story.chapters.map(c=>[c.key,c]));
  const allChapterKeys=new Set(chapterIndex.keys());
  const areaKeys=new Set(areaIndex.keys());
  ensure(story.chapters.every((c,i)=>c.index===i&&c.map_id===null&&c.game_exe_verified===false&&
   (c.reference_area_key===null||areaKeys.has(c.reference_area_key))&&indexPhase(c.planned_phase)!==null),'chapter evidence invalid');
  ensure(areas.areas.every(a=>a.state==='planned'&&a.source_map_id===null&&a.destination_map_id===null&&
    a.npc_events_verified===false&&a.distribution_rights_verified===false&&a.game_exe_tested===false&&
    indexPhase(a.phase)!==null&&['campaign','postgame','optional','event_only'].includes(a.chapter)
    &&typeof a.name==='string'&&a.name.trim().length>0),'area has invented native proof');
  ensure(story.missions.every(m=>allChapterKeys.has(m.chapter_key)&&areaKeys.has(m.reference_area_key)&&
    m.planned_only===true&&m.real_event_id===null),'mission native-proof mismatch');
  ensure(transitions.transitions.every(t=>allChapterKeys.has(t.to)&&allChapterKeys.has(t.from)
    &&(t.required_mission_key===null||story.missions.some(m=>m.key===t.required_mission_key))),'transition provenance');
  ensure(gyms.gyms.every((g,i)=>g.index===i+1&&allChapterKeys.has(g.chapter_key)&&
    areaKeys.has(g.city_area_key)&&areaKeys.has(g.gym_area_key)&&
    g.challenge_status==='PLANNED_NOT_PLAYABLE'&&g.native_badge_item_id===null&&
    g.native_badge_switch_id===null&&g.trainer_levels===null),'gym false playable');
  ensure(finale.elite_members.every(e=>allChapterKeys.has(e.chapter_key)&&areaKeys.has(e.area_key)&&
   e.native_trainer_id===null&&e.team===null&&e.levels===null&&e.simulation_only===true),'Elite falsely playable');
  ensure(Array.isArray(finale.castle_events)&&finale.castle_events.every(e=>
   allChapterKeys.has(e.chapter_key)&&areaKeys.has(e.area_key)&&e.native_event_id===null&&e.native_map_id===null&&
   e.team===null&&e.levels===null),'castle native evidence');
  ensure(npcs.characters.every(n=>areaKeys.has(n.primary_area_key)&&
   (n.additional_area_keys||[]).every(k=>areaKeys.has(k))&&
   n.status==='PLANNED_REFERENCE_ONLY'&&n.installed===false&&n.npc_event_verified===false&&
   n.game_exe_tested===false),'NPC falsely playable');
  ensure(rivals.encounters.every(e=>areaKeys.has(e.reference_area_key)&&allChapterKeys.has(e.chapter_key)&&
   e.canonical_team===null&&e.canonical_levels===null&&e.native_event_id===null&&e.native_map_id===null),
   'trainer team or event falsely verified');
  const chapterRows=story.chapters.filter(c=>c.index>0);
  const byArea=(key,arr,field)=>arr.filter(e=>e[field]===key);
  // Editorial grouping, never a verified route: postgame goes to CH12; otherwise
  // choose the most recent chapter's audited planning phase, not a map transfer.
  const editorialChapter=a=>{
    if(a.chapter==='postgame'||a.chapter==='event_only'&&indexPhase(a.phase)>=28)
      return chapterRows.at(-1).key;
    const phase=indexPhase(a.phase);
    return chapterRows.filter(c=>indexPhase(c.planned_phase)<=phase).at(-1)?.key ?? chapterRows[0].key;
  };
  const arows=areas.areas.map(a=>{
    const chapterKey=editorialChapter(a);
    const people=npcs.characters.filter(n=>n.primary_area_key===a.key||(n.additional_area_keys||[]).includes(a.key));
    const trainers=rivals.encounters.filter(e=>e.reference_area_key===a.key);
    return {
      key:a.key,name:a.name,kind:a.kind,plannedPhase:a.phase,storyScope:a.chapter,
      chapterKey,chapterAssociation:'EDITORIAL_PHASE_GROUP_NOT_VERIFIED_ROUTE',
      status:'planned',nativeMapId:null,installed:false,verifiedEncounters:0,
      verifiedNpcEvents:0,verifiedTrainerTeams:0,verifiedLevels:null,
      npcKeys:people.map(n=>n.key),trainerEventKeys:trainers.map(t=>t.id),
      dependencies:['MAP_ID_PENDING','NATIVE_EVENTS_PENDING','ENCOUNTER_PBS_PENDING','GAME_EXE_QA_PENDING'],
      sourcePath:unovaGuideSources.areas
    };
  });
  const chapters=chapterRows.map(c=>{
    const mission=story.missions.find(m=>m.chapter_key===c.key);
    const transition=transitions.transitions.find(t=>t.to===c.key);
    return {
      key:c.key,index:c.index,title:c.title,plannedPhase:c.planned_phase,arc:c.arc,
      referenceAreaKey:c.reference_area_key,missionKey:mission?.key??null,
      requiredMissionKey:transition?.required_mission_key??null,
      requiredCompletionFlag:transition?.required_completion_flag??null,
      areaKeys:arows.filter(a=>a.chapterKey===c.key).map(a=>a.key),
      association:'EDITORIAL_PLANNING_PHASE_NOT_NATIVE_ROUTE',
      status:'planned',nativeMapId:null,nativeEventId:null,installed:false
    };
  });
  ensure(chapters.length===12&&arows.every(a=>chapters.some(c=>c.key===a.chapterKey))
   &&new Set(chapters.flatMap(c=>c.areaKeys)).size===74,'all 74 areas must have explicit editorial groups');
  const leaders=gyms.gyms.map(g=>({
    key:g.id,index:g.index,chapterKey:g.chapter_key,missionKey:g.mission_key,
    cityAreaKey:g.city_area_key,gymAreaKey:g.gym_area_key,badge:g.badge,
    leaderKey:g.leader_key,leaderByStarter:g.leader_by_starter??null,
    sourcePhase:g.planned_phase,status:'planned',team:null,levels:null,
    nativeTrainerId:null,installed:false
  }));
  const elite=finale.elite_members.map(e=>({
    key:e.key,name:e.member_name,specialty:e.specialty,chapterKey:e.chapter_key,
    areaKey:e.area_key,status:'planned',team:null,levels:null,nativeTrainerId:null
  }));
  const castle=finale.castle_events.map(e=>({
    key:e.id,description:e.description_ptbr,chapterKey:e.chapter_key,
    areaKey:e.area_key,status:'planned',nativeEventId:null,
    trainerTeam:null,levels:null
  }));
  const missions=story.missions.map(m=>{
    const chapter=chapterIndex.get(m.chapter_key);
    ensure(chapter&&m.planned_only===true&&m.real_event_id===null
      &&areaKeys.has(m.reference_area_key),'mission native-event or area drift');
    return {
      key:m.key,chapterKey:m.chapter_key,chapterTitle:chapter.title,
      areaKey:m.reference_area_key,plannedPhase:chapter.planned_phase,
      kind:m.kind,status:'planned',nativeEventId:null,nativeMapId:null,
      installed:false,sourcePath:unovaGuideSources.story
    };
  });
  const people=npcs.characters.map(n=>({
    key:n.key,name:n.display_name,role:n.role,areaKey:n.primary_area_key,
    relatedAreaKeys:[...n.additional_area_keys],status:'planned',
    spriteVerified:false,nativeEventId:null,installed:false
  }));
  const trainers=rivals.encounters.map(e=>({
    key:e.id,actor:e.actor_key,chapterKey:e.chapter_key,areaKey:e.reference_area_key,
    policy:e.battle_policy,sourceMode:e.source_mode,npcKey:e.npc_reference_key,
    trainerRef:e.trainer_reference_key??null,status:'planned',
    team:null,levels:null,nativeTrainerId:null,installed:false
  }));
  return {
    schema:1,region:'UNOVA',campaign:'WHITE_BW',phase:'G06.2',
    status:'PLANNED_REFERENCE_GUIDE_ONLY',canPlay:false,canInstall:false,
    gameExeTested:false,nativeMapIdsVerified:0,nativeTeamsVerified:0,
    nativeEventsVerified:0,nativeEncounterRatesVerified:0,
    sourcePaths:unovaGuideSources,
    counts:{areas:74,chapters:12,missions:12,gyms:8,eliteFour:4,npcs:people.length,trainerReferences:trainers.length},
    warning:'Guia editorial de Unova White. Fases, locais, personagens e batalhas são referências contratuais; não são mapas, encontros, equipes, níveis ou eventos instalados.',
    chapterGroupingExplanation:'Áreas agrupadas editorialmente por fase U03/U07–U30; associação não significa ligação física, ordem de transferência ou capítulo jogável confirmado.',
    chapters,missions,areas:arows,gyms:leaders,elite,castle,npcs:people,trainers,
    pending:{maps:74,events:'PENDENTE',npcSprites:'PENDENTE',trainerTeams:'PENDENTE',
      levels:'PENDENTE',wildEncounters:'PENDENTE',rights:'PENDENTE',gameExe:'NÃO TESTADO'}
  };
}
