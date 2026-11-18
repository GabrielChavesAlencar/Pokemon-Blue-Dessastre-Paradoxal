import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const get=p=>readFile(path.join(root,p),"utf8");
const parsed=async p=>JSON.parse(await get(p));
const file="data/regions/sinnoh-l10-public-blocker-index.json";
const mirror="site/public/data/sinnoh-l10-public-blocker-index.json";

test("L10 public mirror equals source byte for byte",async()=>{
 assert.equal(await get(file),await get(mirror));
});
test("L10 preserves all 44 IDs/20 criteria and independent Windows/Android blockers",async()=>{
 const d=await parsed(file);
 assert.equal(d.stage,"L10");
 assert.equal(d.status,"PUBLIC_BLOCKER_INDEX_ONLY_ALL_PENDING");
 assert.deepEqual(d.blockers.map(x=>x.id),["B09","B10","B11","R07","R08","R09"]);
 assert.equal(d.cases.length,44);
 assert.equal(new Set(d.cases.map(x=>x.id)).size,44);
 assert.equal(d.criteria.length,20);
 assert.equal(new Set(d.criteria.map(x=>x.id)).size,20);
 assert.equal(d.cases.filter(x=>x.platform==="windows").length,43);
 assert.equal(d.cases.filter(x=>x.platform==="android").length,1);
 assert.deepEqual(d.blockers.map(x=>[x.windows_cases,x.android_cases]),[[43,1],[43,0],[43,0],[43,1],[43,1],[0,0]]);
 assert.equal(d.blockers.at(-1).scope,"GLOBAL_REGION_PENDING_NOT_CASE_GATE");
 assert.deepEqual(d.blockers.at(-1).case_ids,[]);
 assert.ok(d.cases.every(x=>x.native_status==="pending" && x.review_state==="NOT_REVIEWED" && x.approved===false && x.native_execution_authorized===false));
 assert.ok(d.criteria.every(x=>x.review_state==="NOT_REVIEWED" && x.signoff===false));
});
test("L10 keeps native rights, MapIDs, global saves, R09 and regional gameplay blocked",async()=>{
 const d=await parsed(file);
 assert.deepEqual([d.gates.r07,d.gates.r08,d.gates.r09],["PENDING","PENDING","PENDING"]);
 assert.equal(d.gates.sinnoh_playable,false);
 for(const key of ["can_run_game_exe","can_run_windows_sandbox","can_run_joiplay","can_install_live_game","sinnoh_playable","local_android_l05_completed"]){
   assert.equal(d[key],false,key);
 }
 assert.equal(d.counts.local_reports,0);
 assert.equal(d.counts.human_approved,0);
 assert.equal(d.counts.native_completed,0);
 assert.equal(d.counts.native_approved,0);
 assert.equal(d.counts.phase_bcd_completed,0);
 assert.equal(d.mapids_not_reserved,true);
 assert.equal(d.asset_rights_not_approved,true);
 assert.equal(d.watch_unchanged_not_global_isolation,true);
});
test("L10 navigable static page has local search and safe text-only rendering",async()=>{
 const html=await get("site/public/sinnoh-l10-bloqueios.html");
 const js=await get("site/public/assets/sinnoh-l10-blocker-index.js");
 for(const id of ["blockers","casos","criterios","origem","search","platform","kind","blocker","criterion","caseRows","criterionRows","status","reset"])
   assert.ok(html.includes('id="'+id+'"'),id);
 assert.ok(js.includes('fetch("/data/sinnoh-l10-public-blocker-index.json"'));
 for(const s of ["document.createElement","textContent","replaceChildren","addEventListener","blocked_by","criterion"])
   assert.ok(js.includes(s),s);
 for(const forbidden of ["innerHTML","eval(","localStorage","FormData","WebSocket","navigator.sendBeacon","method: \"POST\""])
   assert.equal(js.includes(forbidden),false,forbidden);
 assert.ok((await get("site/src/index.html")).includes('/sinnoh-l10-bloqueios.html'));
});
