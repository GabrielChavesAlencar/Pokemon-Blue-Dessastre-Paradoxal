import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const read=p=>readFile(path.join(root,p),"utf8");
test("J playable progress mirror matches exactly",async()=>{
 assert.equal(await read("data/regions/sinnoh-playable-progress.json"),
 await read("site/public/data/sinnoh-playable-progress.json"));
});
test("J01 to J07 are engineering code only, native game and saves untouched",async()=>{
 const d=JSON.parse(await read("data/regions/sinnoh-playable-progress.json"));
 assert.equal(d.track,"JOGAVEL_TWINLEAF_SANDGEM");
 assert.equal(d.status,"PILOT_NOT_INSTALLED_NOT_PLAYABLE");
 assert.equal(d.stages_code_ready,7);
 assert.equal(d.engineering_percent,87.5);
 assert.equal(d.stages_native_validated,0);assert.equal(d.native_verified_percent,0);
 assert.equal(d.stages_total,8);assert.equal(d.stages.length,8);
 assert.equal(d.stages[0].status,"code_ready");
 assert.equal(d.stages[1].status,"code_ready");
 assert.equal(d.stages[2].status,"code_ready");
 assert.equal(d.stages[3].status,"code_ready");
 assert.equal(d.stages[4].status,"code_ready");
 assert.equal(d.stages[5].status,"code_ready");
 assert.equal(d.stages[6].status,"code_ready");
 assert.ok(d.stages.slice(7).every(x=>x.status==="blocked"&&!x.code_ready));
 assert.ok(d.stages.every(x=>!x.native_verified&&!x.playable));
 assert.equal(d.game_exe_tested,false);assert.equal(d.joiplay_tested,false);
 assert.equal(d.main_game_modified,false);assert.equal(d.save_migration_performed,false);
 assert.equal(d.native_source_terrain_candidates,4);assert.equal(d.native_source_maps_missing,5);
 assert.equal(d.native_map_bindings_verified,0);assert.equal(d.native_maps_installed,0);
 assert.equal(d.next_stage,"J08");
 assert.match(d.next_issue_url,/\/issues\/234$/);
 assert.match(d.next_prompt,/J08/);
});
test("J02 source audit pins only four historical maps; five absent",async()=>{
 const d=JSON.parse(await read("data/regions/sinnoh-j02-map-source-catalog.json"));
 assert.equal(d.mode,"HISTORICAL_SOURCE_REFERENCE_ONLY");
 assert.equal(d.maps.length,9);
 assert.equal(d.source_terrain_candidates,4);assert.equal(d.source_maps_missing,5);
 assert.equal(d.native_playable,false);assert.equal(d.source_rights_verified,false);
 assert.equal(d.destination_mapids_assigned,0);assert.equal(d.destination_game_maps_installed,0);
 assert.deepEqual(
   d.maps.filter(x=>x.source_id!==null).map(x=>x.source_id).sort((a,b)=>a-b),
   [209,210,227,228]);
 assert.ok(d.maps.every(x=>x.destination_map_id===null&&!x.installed&&!x.source_asset_rights_verified));
 assert.ok(d.maps.filter(x=>x.source_id===null).every(x=>x.source_sha256===null));
});
test("J02 page has two honest bars and next-action button without automatic execution",async()=>{
 const [html,js]=await Promise.all([
  read("site/public/sinnoh-jogavel.html"),
  read("site/public/assets/sinnoh-playable-progress.js")]);
 assert.match(html,/SINNOH_J01_DIAGNOSTICAR_JOGAVEL\.bat/);
 assert.match(html,/id="engineering"/);assert.match(html,/id="native"/);
 assert.match(html,/id="nextAction"/);assert.match(html,/id="nextIssue"/);
 assert.match(html,/id="referenceCount"/);assert.match(html,/id="missingCount"/);
 assert.match(js,/PILOT_NOT_INSTALLED_NOT_PLAYABLE/);
 assert.match(js,/encodeURIComponent\(d\.next_prompt\)/);
 assert.match(js,/\/issues\//);
 assert.match(js,/replaceChildren/);
 assert.doesNotMatch(html,/<form\b|type="file"/);
 assert.doesNotMatch(js,/innerHTML|localStorage|sessionStorage|postMessage|XMLHttpRequest/);
});
test("next phase URL stays in allowed GitHub repo",async()=>{
 const d=JSON.parse(await read("data/regions/sinnoh-playable-progress.json"));
 assert.match(d.next_issue_url,/^https:\/\/github\.com\/GabrielChavesAlencar\/Pokemon-Blue-Dessastre-Paradoxal\/issues\/234$/);
 assert.ok(d.next_prompt.includes("Sinnoh jogável"));
 assert.equal(typeof d.next_button_label,"string");
});

test("J03 is a private code stage only, not a native stage or rights grant",async()=>{
 const d=JSON.parse(await read("data/regions/sinnoh-playable-progress.json"));
 assert.equal(d.staging_code_prepared,true);
 assert.equal(d.local_stage_created_and_verified,false);
 assert.equal(d.staging_real_terrain_maps_confirmed,0);
 assert.equal(d.native_maps_installed,0);
 assert.equal(d.stages_native_validated,0);
 assert.equal(d.next_stage,"J08");
 assert.equal(d.next_button_label.includes("J08"),true);
 const html=await read("site/public/sinnoh-jogavel.html");
 assert.match(html,/J03.*(stage|staging)/is);
 assert.match(html,/id="nextAction"/);
});

test("J04 compile-only code never claims real maps, handlers, or Game.exe",async()=>{
 const d=JSON.parse(await read("data/regions/sinnoh-playable-progress.json"));
 assert.equal(d.j04_compiler_code_prepared,true);
 assert.equal(d.j04_native_events_compiled,0);
 assert.equal(d.j04_native_warps_compiled,0);
 assert.equal(d.j04_native_npcs_compiled,0);
 assert.equal(d.j04_native_starter_balls_compiled,0);
 assert.equal(d.j04_story_handlers_runtime_verified,false);
 assert.equal(d.j04_nine_map_source_stage_verified,false);
 assert.equal(d.j04_real_map_passability_verified,false);
 assert.equal(d.native_maps_installed,0);
 assert.equal(d.stages_native_validated,0);
 assert.equal(d.next_stage,"J08");
 const html=await read("site/public/sinnoh-jogavel.html");
 assert.match(html,/J04[^\n]*eventos|J04[^\n]*portais/i);
 assert.match(html,/id="nextAction"/);
});

test("J05 has executable offline handlers but explicitly zero native gameplay",async()=>{
 const d=JSON.parse(await read("data/regions/sinnoh-playable-progress.json"));
 assert.equal(d.j05_handlers_engineering_ready,true);
 assert.equal(d.j05_starter_ball_dispatch_matches_runtime,true);
 assert.equal(d.j05_synthetic_reentrant_grants_tested,true);
 assert.equal(d.j05_native_starter_grants,0);
 assert.equal(d.j05_native_barry_battles,0);
 assert.equal(d.j05_native_save_reload_cases,0);
 assert.equal(d.j05_compiled_pbs_native_verified,false);
 assert.equal(d.j05_isolated_save_profile_native_verified,false);
 assert.equal(d.native_maps_installed,0);
 assert.equal(d.native_windows_cases_executed,0);
 assert.equal(d.native_android_cases_executed,0);
 assert.equal(d.stages_native_validated,0);
 assert.equal(d.next_stage,"J08");
 const html=await read("site/public/sinnoh-jogavel.html");
 assert.match(html,/J05[^\n]*Barry/i);
 assert.match(html,/id="nextAction"/);
});

test("J06 Windows QA installer uses explicit local sources but stays unexecuted in native game",async()=>{
 const d=JSON.parse(await read("data/regions/sinnoh-playable-progress.json"));
 assert.equal(d.j06_guarded_launcher_code_ready,true);
 assert.equal(d.j06_windows_synthetic_qa_checks_ready,true);
 assert.equal(d.j06_private_qa_copy_installed,false);
 assert.equal(d.j06_rights_source_verified,false);
 assert.equal(d.j06_r07_reservations_approved,false);
 assert.equal(d.j06_game_exe_private_started,false);
 assert.equal(d.j06_native_build_verified,false);
 assert.equal(d.j06_native_save_profile_verified,false);
 assert.equal(d.j06_pristine_rollback_native_executed,false);
 assert.equal(d.stages_native_validated,0);
 assert.equal(d.native_windows_cases_executed,0);
 assert.equal(d.native_maps_installed,0);
 assert.equal(d.next_stage,"J08");
 assert.match(d.next_issue_url,/\/issues\/234$/);
 const html=await read("site/public/sinnoh-jogavel.html");
 assert.match(html,/J06[^\n]*Windows|J06[^\n]*QA/i);
 assert.match(html,/id="nextAction"/);
});

test("J07 43 Windows native QA harness built but no live evidence",async()=>{
 const d=JSON.parse(await read("data/regions/sinnoh-playable-progress.json"));
 assert.equal(d.j07_windows_harness_engineering_ready,true);
 assert.equal(d.j07_g12_exact_cases_validated_offline,true);
 assert.equal(d.j07_qa_native_game_exe_run,false);
 assert.equal(d.j07_native_barry_battles_verified,0);
 assert.equal(d.j07_native_save_reload_verified,0);
 assert.equal(d.j07_native_warp_cases_verified,0);
 assert.equal(d.j07_native_npc_cases_verified,0);
 assert.equal(d.j07_native_regression_cases_verified,0);
 assert.equal(d.j07_private_qa_session_observed,false);
 assert.equal(d.j07_evidence_independently_reviewed,0);
 assert.equal(d.j07_android_native_verified,false);
 assert.equal(d.native_windows_cases_total,43);
 assert.equal(d.native_windows_cases_executed,0);
 assert.equal(d.native_android_cases_total,1);
 assert.equal(d.native_android_cases_executed,0);
 assert.equal(d.stages_code_ready,7);
 assert.equal(d.stages_native_validated,0);
 assert.equal(d.next_stage,"J08");
 assert.match(d.next_issue_url,/\/issues\/234$/);
 const html=await read("site/public/sinnoh-jogavel.html");
 assert.match(html,/J07[^\n]*Windows/);
 assert.match(html,/0\/43 Windows/);
 assert.match(html,/id="nextAction"/);
 assert.match(await read("docs/SINNOH_J07_QA_WINDOWS_NATIVA.md"),/43 casos Windows/);
});
