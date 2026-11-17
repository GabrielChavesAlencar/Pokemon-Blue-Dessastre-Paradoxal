// G10: public, read-only Sinnoh implementation evidence. NOT game telemetry.
export const sinnohG10Sources=Object.freeze({
  b07:'data/regions/sinnoh-b07-private-stage.json',
  b08:'data/regions/sinnoh-b08-private-qa.json',
  b09:'data/regions/sinnoh-b09-native-qa.json',
  gyms:'data/regions/sinnoh-gyms-s15.json',
  hms:'data/regions/sinnoh-hms-s16.json',
  league:'data/regions/sinnoh-league-s21.json',
  postgame:'data/regions/sinnoh-postgame-s23.json',
  registry:'site/public/data/regions.json'
});
const fail=msg=>{throw new Error('sinnoh-g10-invalid: '+msg);};
const badges=['COAL','FOREST','RELIC','COBBLE','FEN','MINE','ICICLE','BEACON'];
const hmCatalog=['COAL','FOREST','COBBLE','RELIC','FEN','MINE','ICICLE','BEACON'];
const leagueIds=['P09_VOLKNER_BEACON_BADGE','SINNOH_LEAGUE_BARRY_GATE',
  'P09_AARON_BATTLE','P09_BERTHA_BATTLE','P09_FLINT_BATTLE',
  'P09_LUCIAN_BATTLE','P09_CYNTHIA_BATTLE','P09_HALL_OF_FAME'];
const postgameIds=['P10_BATTLE_ZONE_ENTRY','P10_HEATRAN_QUEST','P10_CRESSELIA_EVENT',
  'P10_DARKRAI_CONDITIONAL_QUEST','P10_SHAYMIN_CONDITIONAL_QUEST',
  'P10_OFFICIAL_STRONGEST_TEAM_REMATCHES'];
const noProof=(x,fields)=>fields.every(k=>x?.[k]===false);
const empty=(x)=>Array.isArray(x)&&x.length===0;
export function generateSinnohG10Status(source,guide){
  if(!source||Object.keys(sinnohG10Sources).some(k=>!source[k]))fail('source missing');
  const {b07,b08,b09,gyms,hms,league,postgame,registry}=source;
  if(guide?.schema!==1||guide.region!=='SINNOH'||guide.status!=='planned'||
     guide.canPlay!==false||guide.gameplayVerified!==false||
     guide.counts?.areas!==120||guide.counts?.verifiedNativeMaps!==0||
     guide.counts?.verifiedNativeTrainers!==0||guide.counts?.verifiedNativeItems!==0)
    fail('guide is not verified planned-only');
  if(registry?.regions?.SINNOH?.status!=='planned')fail('region incorrectly playable');
  if(b07.region!=='SINNOH'||b07.stage!=='B07'||
     b07.status!=='PRIVATE_GEOMETRY_BUILDER_READY_NOT_NATIVE_INSTALLED'||
     b07.native_tileset_strategy!=='APPEND_TO_SNAPSHOT_COPY_ONLY'||
     b07.imports_donor_events!==false||b07.imports_donor_scripts!==false||
     b07.imports_donor_pbs!==false||
     b07.can_install_into_game!==false||b07.rights_per_asset_verified!==false||
     b07.r07_complete!==false||b07.r08_complete!==false||b07.r09_complete!==false||
     b07.phase_b_approved!==0||b07.phase_c_approved!==0||b07.phase_d_approved!==0)
    fail('B07 unexpected stage or installation proof');
  const ids=Array.from({length:54},(_,i)=>i+442);
  if(JSON.stringify(b07.candidate_terrain_destinations)!==JSON.stringify(ids)||
     JSON.stringify(b07.excluded_empty_destinations)!==JSON.stringify(
       Array.from({length:22},(_,i)=>i+496)))fail('B07 geometries changed');
  if(b08.region!=='SINNOH'||b08.stage!=='B08'||
     b08.status!=='PRIVATE_QA_AUDITOR_READY_USER_STAGE_NOT_RECEIVED'||
     b08.b07_source_sha256!==b07.source_zip_sha256||
     b08.expected_staged_maps!==54||b08.expected_pngs!==14||
     b08.has_live_stage_evidence!==false||
     b08.can_install!==false||b08.can_mark_gameplay!==false||
     b08.rights_per_asset_verified!==false||
     b08.phase_b_approved!==0||b08.phase_c_approved!==0||b08.phase_d_approved!==0)
    fail('B08 private stage falsely certified');
  if(b09.region!=='SINNOH'||b09.stage!=='B09'||
     b09.status!=='PRIVATE_NATIVE_QA_CLONE_BUILDER_READY_B08_RUNTIME_EVIDENCE_PENDING'||
     b09.expected_installed_native_map_count!==648||
     b09.expected_sinnoh_terrain_maps_in_clone!==54||
     b09.expected_qa_clone_map_count!==702||
     b09.expected_png_count!==14||
     b09.native_b08_user_report_received!==false||
     b09.never_launches_executable!==true||
     b09.runtime_save_isolation_verified!==false||
     b09.game_exe_tested!==false||b09.joiplay_tested!==false||
     b09.can_install_live_game!==false||b09.can_mark_native_playable!==false||
     b09.r07_complete!==false||b09.r08_complete!==false||b09.r09_complete!==false||
     b09.phase_b_approved!==0||b09.phase_c_approved!==0||b09.phase_d_approved!==0)
    fail('B09 clone incorrectly approved');
  if(gyms.region!=='SINNOH'||gyms.task!=='S15'||gyms.gym_count!==8||
     !noProof(gyms,['approved_for_install','battles_playable','native_qa_approved',
       'native_badges_awardable','native_pbs_compiled','game_exe_tested'])||
     !Array.isArray(gyms.gyms)||gyms.gyms.length!==8||
     !gyms.gyms.every((g,i)=>g.order===i+1&&g.badge===badges[i]&&
       g.status==='GYM_REFERENCE_NOT_INSTALLED'&&g.physical_map_id===null&&
       noProof(g,['trainer_pbs_compiled','physical_map_installed',
         'physical_event_installed','battle_victory_verified','badge_award_verified'])))
    fail('S15 gyms marked installed or reordered');
  if(hms.region!=='SINNOH'||hms.stage!=='S16'||hms.hm_count!==8||
     !noProof(hms,['approved_for_install','can_grant_hm','native_qa_approved'])||
     hms.native_pickups_installed!==0||hms.native_receipts_verified!==0||
     !Array.isArray(hms.hms)||hms.hms.length!==8||
     !hms.hms.every((r,i)=>r.badge===hmCatalog[i]&&
       r.status==='REQUIRES_NATIVE_LOCAL_PICKUP'&&
       r.physical_map_id===null&&noProof(r,['handler_compiled','pickup_event_verified',
         'local_receipt_verified','enabled'])))
    fail('S16 HMs marked installed or reordered');
  if(league.region!=='SINNOH'||league.stage!=='S21'||
     !noProof(league,['native_league_installed','native_hall_of_fame_verified',
       'gameplay_verified','can_install'])||
     !empty(league.installed_map_ids)||!empty(league.installed_native_trainers)||
     !empty(league.compiled_native_pbs)||
     !Array.isArray(league.steps)||league.steps.length!==8||
     !league.steps.every((r,i)=>r.id===leagueIds[i]&&r.physical_map_id===null&&
       r.reference_only===true&&
       noProof(r,['native_handler_installed','native_battle_result_verified']))||
     league.steps[7].outcome!=='engine_hall_of_fame_confirmed'||
     league.steps[6].outcome!=='battle_won'||
     league.restrictions?.hall_of_fame_requires_separate_engine_confirmation!==true)
    fail('S21 league prematurely released');
  if(postgame.region!=='SINNOH'||postgame.stage!=='S23'||
     postgame.requires_separate_hall_of_fame!==true||
     postgame.global_world_champion_requires_all_ten_leagues!==true||
     !empty(postgame.installed_postgame_map_ids)||!empty(postgame.verified_event_items)||
     !empty(postgame.verified_native_sources)||
     !noProof(postgame.verification,['postgame_native_maps_installed',
       'game_exe_executed','joiplay_executed','native_qa_approved','gameplay_certified',
       'can_install'])||
     !Array.isArray(postgame.events)||postgame.events.length!==6||
     !postgame.events.every((r,i)=>r.id===postgameIds[i]&&
       r.physical_map_id===null&&r.reference_only===true&&
       r.requires_completed_sinnoh_hall_of_fame===true&&
       noProof(r,['native_callback_installed','native_quest_verified']))||
     postgame.events[1].requires_previous_event!=='P10_BATTLE_ZONE_ENTRY'||
     !postgame.events.slice(3,5).every(r=>r.requires_event_item_verification===true)||
     postgame.events[5].requires_all_ten_leagues!==true||
     postgame.events[5].requires_native_strongest_team!==true)
    fail('S23 postgame gate wrongly released');
  const hmByBadge=new Map(hms.hms.map(r=>[r.badge,r]));
  if(hmByBadge.size!==8||gyms.gyms.some(g=>hmByBadge.get(g.badge)?.leader!==g.name))
    fail('gym HM connection must use badge key');
  const gymRows=gyms.gyms.map(g=>{
    const hm=hmByBadge.get(g.badge);
    return {id:g.id,label:g.name,city:g.reference_city,
      badge:g.badge,hm:hm.hm_item,move:hm.action,
      state:'pending',mapVerified:false,pbsVerified:false,hmPickupVerified:false};
  });
  return {
    schema:1,region:'SINNOH',stage:'G10',
    status:'PUBLIC_CONTRACT_EVIDENCE_ONLY_NO_NATIVE_APPROVAL',
    // "private_preparation" means candidate records in contracts, NOT proof
    // that a user actually ran a stage or installed a private build.
    states:[
      {key:'planned',label:'Planejado',count:guide.counts.areas,
        meaning:'Áreas de referência descritas nos guias; não são MapIDs comprovados.'},
      {key:'private_preparation',label:'Cópia privada prevista',count:54,
        meaning:'54 terrenos candidatos nos manifestos B07–B09; execução e arquivos reais não verificados neste portal.'},
      {key:'installed',label:'Instalado no jogo',count:0,
        meaning:'Nenhum mapa/evento de Sinnoh certificado como instalado na build principal.'},
      {key:'playable',label:'Jogável e testado',count:0,
        meaning:'Nenhuma execução Game.exe/JoiPlay ou aceitação de gameplay comprovada.'},
    ],
    categories:[
      {key:'areas',label:'Áreas',count:guide.counts.areas,pending:'MapIDs/portais não verificados',tab:'areas'},
      {key:'trainers',label:'Treinadores',count:guide.counts.trainers,pending:'PBS e vínculo físico ausentes',tab:'treinadores'},
      {key:'gyms',label:'Ginásios',count:8,pending:'Batalhas e insígnias nativas pendentes',tab:'ginasios'},
      {key:'hms',label:'HMs locais',count:8,pending:'Requerem insígnia + coleta local',tab:'itens'},
      {key:'league',label:'Liga e Hall of Fame',count:8,pending:'Cynthia não substitui Hall confirmado',tab:'liga'},
      {key:'postgame',label:'Pós-jogo',count:6,pending:'Hall de Sinnoh obrigatório; Full Power exige dez Ligas',tab:'progresso'},
    ],
    gyms:gymRows,
    league:league.steps.map(s=>({id:s.id,state:'pending',nativeVerified:false})),
    postgame:postgame.events.map(s=>({id:s.id,state:'pending',nativeVerified:false})),
    blockers:['R07: vinculação física e MapIDs','R08: recursos e permissões de uso',
      'B10/B11: isolamento e auditoria de saves',
      'R09: Game.exe/JoiPlay e callbacks reais'],
    verification:{
      nativeAssetBytesInspected:false,
      privateStageExecutionVerified:false,
      nativeMapBindingsVerified:false,
      gameExeTested:false,joiplayTested:false,
      installedVerified:false,playableVerified:false,
      phaseBApproved:0,phaseCApproved:0,phaseDApproved:0,
    }
  };
}
