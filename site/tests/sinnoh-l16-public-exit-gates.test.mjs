import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import path from "node:path";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const get=p=>readFile(path.join(root,p),"utf8");
const file="data/regions/sinnoh-l16-public-exit-gates.json";
const mirror="site/public/data/sinnoh-l16-public-exit-gates.json";
const data=async()=>JSON.parse(await get(file));

test("L16 source and public mirror are byte-identical",async()=>{
 assert.equal(await get(file),await get(mirror));
});
test("L16 all 88 public exit gates pending and blocked",async()=>{
 const d=await data();
 assert.equal(d.schema,1);assert.equal(d.stage,"L16");
 assert.equal(d.mode,"PUBLIC_READ_ONLY_EXIT_GATE_REGISTER");
 assert.equal(d.status,"EXIT_CRITERIA_DOCUMENTED_ALL_PENDING_NO_NATIVE_AUTHORIZATION");
 assert.equal(d.records.length,88);
 assert.deepEqual(d.records.map(x=>x.order),Array.from({length:88},(_,i)=>i+1));
 assert.equal(new Set(d.records.map(x=>x.request_id)).size,88);
 assert.ok(d.records.every(x=>x.status==="PENDING"&&x.readiness==="BLOCKED"
  &&!x.exit_criteria_met&&!x.physical_evidence_received&&!x.human_review_completed
  &&!x.native_execution_approved&&x.action_authorization==="NONE"));
 assert.equal(d.counts.exit_ready,0);
 assert.equal(d.counts.exit_criteria_met,0);
 assert.equal(d.counts.exit_blocked,88);
});
test("L16 1084 documentary links and anonymous 18 slots unchanged",async()=>{
 const d=await data();
 assert.equal(d.records.reduce((n,x)=>n+x.documentary_dependency_count,0),1084);
 assert.equal(d.counts.documentary_link_count,1084);
 const anon=d.records.filter(x=>x.anonymous_bookkeeping_slot);
 assert.equal(anon.length,18);
 assert.ok(anon.every(x=>x.documentary_dependency_count===0
  &&x.documentary_dependency_request_ids.length===0
  &&x.linked_l04_criterion_ids.length===0&&!x.scope_known));
 assert.deepEqual(d.group_summary.map(x=>[x.kind,x.requests,x.documentary_links]),[
  ["BLOCKER_DEPENDENCY",5,0],
  ["GLOBAL_REGIONAL_GATE",1,0],
  ["LOCAL_REPORT_SLOT",5,0],
  ["HUMAN_CRITERION",20,20],
  ["BCD_PENDING_SLOT",13,0],
  ["NATIVE_CASE",44,1064],
 ]);
});
test("L16 preserved L04 independent review and G12 native QA requirements",async()=>{
 const d=await data();
 const human=d.records.filter(x=>x.kind==="HUMAN_CRITERION");
 const native=d.records.filter(x=>x.kind==="NATIVE_CASE");
 assert.equal(human.length,20);assert.equal(native.length,44);
 assert.ok(human.every(x=>x.exit_criteria_codes.includes("INDEPENDENT_L04_SIGNOFF_PENDING")));
 assert.ok(native.every(x=>x.exit_criteria_codes.includes("NATIVE_G12_QA_NOT_EXECUTED")));
 assert.equal(d.counts.required_human_reviews_pending,20);
 assert.equal(d.counts.required_native_cases_pending,44);
 assert.equal(d.counts.physical_evidence_accepted,0);
});
test("L16 Windows 43 + Android 1 never share Windows B10/B11 authorization",async()=>{
 const d=await data();
 const native=d.records.filter(x=>x.kind==="NATIVE_CASE");
 assert.equal(native.filter(x=>x.platform==="windows").length,43);
 assert.equal(native.filter(x=>x.platform==="android").length,1);
 assert.ok(native.filter(x=>x.platform==="windows").every(x=>
   x.prerequisite_blocker_ids.includes("B10")&&x.prerequisite_blocker_ids.includes("B11")));
 assert.ok(native.filter(x=>x.platform==="android").every(x=>
   !x.prerequisite_blocker_ids.includes("B10")&&!x.prerequisite_blocker_ids.includes("B11")));
 assert.deepEqual(d.platform_partition.map(x=>[x.platform,x.native_requests,x.native_completed]),
  [["windows",43,0],["android",1,0]]);
 assert.equal(d.platform_partition[1].requires_windows_b10_b11,false);
 assert.ok(d.platform_partition.every(x=>x.exit_met===0&&!x.native_authorization));
});
test("L16 R09 remains global with zero case-scoped edges",async()=>{
 const d=await data();
 assert.deepEqual(d.global_r09.case_ids,[]);
 assert.deepEqual(d.global_r09.documentary_dependency_request_ids,[]);
 assert.equal(d.global_r09.approval,false);
 assert.equal(d.global_r09.exit_met,false);
 assert.equal(d.global_r09.global_gate_only,true);
 const gate=d.records.find(x=>x.kind==="GLOBAL_REGIONAL_GATE");
 assert.equal(gate.subject_id,"R09");
 assert.deepEqual(gate.prerequisite_blocker_ids,["R09"]);
 assert.deepEqual(gate.documentary_dependency_request_ids,[]);
 assert.ok(d.records.filter(x=>x.kind==="NATIVE_CASE").every(x=>
  !x.prerequisite_blocker_ids.includes("R09")));
});
test("L16 fixed commits L07–L15 and three immutable public blobs",async()=>{
 const d=await data();
 assert.deepEqual(d.baseline_commits,{
  L07:"d98033b362dac82347e0d97cb5606870eaa70b22",
  L08:"8617ef47ea6745920cb6fe4be251982380d7628d",
  L09:"39e51de92aafdab3f5aea3f929f57f5c0bb72b2d",
  L10:"7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a",
  L11:"9d901a0cf21aa2742f731ee387a51f945bac8a5d",
  L12:"58b7f2fec9f66dee06d95676eec66fb2ded6a1de",
  L13:"1f12bcc86c10dcc934b024a0562cdadb65d5e2c2",
  L14:"11eda18f7225e16b13007c1eb955ccc3d7667b66",
  L15:"0192075fb02587c9f3d9db6b170500cba365251c"
 });
 assert.deepEqual(d.public_sources,[
 {stage:"L13",path:"data/regions/sinnoh-l13-public-evidence-queue.json",git_blob_sha1:"357215cdfd96b37eaac291e1c0ab3873069a12fe"},
 {stage:"L14",path:"data/regions/sinnoh-l14-public-readiness-matrix.json",git_blob_sha1:"d882d6a20b1c01be33744f14ab7826af2fb6ef41"},
 {stage:"L15",path:"data/regions/sinnoh-l15-public-consistency-diff.json",git_blob_sha1:"1a19883a3f0523add6aeaa4f78262b922a041e95"}
 ]);
});
test("L16 all real evidence gates still empty, never playable",async()=>{
 const d=await data();
 assert.deepEqual([d.counts.local_reports,d.counts.human_approved,d.counts.native_completed,
  d.counts.native_approved,d.counts.phase_bcd_completed],[0,0,0,0,0]);
 assert.equal(d.counts.phase_bcd_total,13);
 assert.deepEqual([d.gates.r07,d.gates.r08,d.gates.r09],["PENDING","PENDING","PENDING"]);
 assert.equal(d.policy.sinnoh_playable,false);
 assert.equal(d.policy.mapids_not_reserved,true);
 assert.equal(d.policy.asset_rights_not_approved,true);
 assert.equal(d.policy.watch_unchanged_not_global_save_isolation,true);
 assert.equal(d.policy.no_uploads,true);
 assert.equal(d.policy.criteria_are_future_requirements_not_signoffs,true);
 assert.equal(d.policy.priority_is_not_native_execution_order,true);
});
test("L16 portal safely renders text only, with read-only filters",async()=>{
 const html=await get("site/public/sinnoh-l16-criterios-saida.html");
 const js=await get("site/public/assets/sinnoh-l16-public-exit-gates.js");
 for(const id of ["search","priority","kind","platform","blocker","criterion","reset",
  "status","recordRows","groupRows","platformRows","detail","filtros","pedidos",
  "detalhes","resumo","proveniencia"]){
  assert.ok(html.includes('id="'+id+'"'),id);
 }
 for(const token of ["document.createElement","textContent","replaceChildren","addEventListener",
  "exit_criteria_codes","no_uploads"]){
  assert.ok(js.includes(token),token);
 }
 for(const forbidden of ["innerHTML","eval(","localStorage","FormData","WebSocket","navigator.sendBeacon",
   "XMLHttpRequest",'method: "POST"']){
  assert.equal(js.includes(forbidden),false,forbidden);
 }
 assert.ok(js.includes("/data/sinnoh-l16-public-exit-gates.json"));
 assert.ok((await get("site/src/index.html")).includes("/sinnoh-l16-criterios-saida.html"));
});
