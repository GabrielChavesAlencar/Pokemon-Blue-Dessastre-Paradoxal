import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import path from "node:path";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const get=p=>readFile(path.join(root,p),"utf8");
const source="data/regions/sinnoh-l18-public-review-gaps.json";
const mirror="site/public/data/sinnoh-l18-public-review-gaps.json";
const data=async()=>JSON.parse(await get(source));

test("L18 Git-public source and web mirror are byte-identical",async()=>{
 assert.equal(await get(source),await get(mirror));
});
test("L18 all 88 gaps remain open and all review decisions pending",async()=>{
 const d=await data();
 assert.equal(d.stage,"L18");assert.equal(d.schema,1);assert.equal(d.version,1);
 assert.equal(d.mode,"PUBLIC_READ_ONLY_DOCUMENTARY_HANDOFF");
 assert.equal(d.status,"PUBLIC_REVIEW_GAPS_DOCUMENTED_ALL_OPEN_NO_NATIVE_QA");
 assert.equal(d.records.length,88);
 assert.deepEqual(d.records.map(x=>x.order),Array.from({length:88},(_,i)=>i+1));
 assert.equal(new Set(d.records.map(x=>x.request_id)).size,88);
 assert.ok(d.records.every(x=>x.status==="PENDING"&&x.readiness==="BLOCKED"&&x.review_state==="NOT_REVIEWED"
  &&x.review_gap_status==="OPEN_DOCUMENTARY_ONLY"
  &&x.next_step_scope==="READ_ONLY_PUBLIC_DOCUMENTATION"
  &&x.human_signoff===false&&x.native_qa_executed===false&&x.native_qa_approved===false
  &&x.local_report_received===false&&x.assigned_reviewer===false&&x.source_authenticated===false));
 assert.equal(d.counts.review_gaps_open,88);
 assert.equal(d.counts.review_gaps_closed,0);
 assert.equal(d.counts.documentary_next_steps,88);
});
test("L18 1084 links unchanged; 18 anonymous slots have no inferred dependency",async()=>{
 const d=await data();
 assert.equal(d.records.reduce((n,x)=>n+x.documentary_dependency_count,0),1084);
 assert.equal(d.counts.links_preserved,1084);
 assert.equal(d.counts.documentary_links_verified,1084);
 assert.deepEqual([d.counts.case_to_criterion_request_links,d.counts.case_to_blocker_request_links,
  d.counts.criterion_to_blocker_request_links],[846,218,20]);
 const slots=d.records.filter(x=>x.anonymous_bookkeeping_slot);
 assert.equal(slots.length,18);
 assert.ok(slots.every(x=>x.documentary_dependency_request_ids.length===0
  &&x.linked_l04_criterion_ids.length===0&&x.documentary_dependency_count===0));
});
test("L18 group totals 5 1 5 20 13 44; next steps only documentary",async()=>{
 const d=await data();
 assert.deepEqual(d.group_summary.map(x=>[x.kind,x.requests,x.documentary_links]),[
 ["BLOCKER_DEPENDENCY",5,0],["GLOBAL_REGIONAL_GATE",1,0],
 ["LOCAL_REPORT_SLOT",5,0],["HUMAN_CRITERION",20,20],
 ["BCD_PENDING_SLOT",13,0],["NATIVE_CASE",44,1064]]);
 assert.ok(d.group_summary.every(x=>x.reviewed===0&&x.ready===0&&x.physical_evidence_accepted===0));
 assert.equal(d.gap_templates.length,6);
 assert.ok(d.records.every(x=>x.gap_types.length>0&&x.next_documentary_step.length>10));
 assert.equal(d.counts.independent_reviews_completed,0);
 assert.equal(d.counts.exit_criteria_met,0);
});
test("L18 R09 global only, 43 Windows + 1 Android isolated",async()=>{
 const d=await data(),g=d.global_r09;
 assert.equal(g.id,"R09");assert.equal(g.status,"PENDING");
 assert.deepEqual(g.case_ids,[]);
 assert.deepEqual(g.documentary_dependency_request_ids,[]);
 assert.equal(g.gaps_open,1);assert.equal(g.review_completed,false);
 assert.deepEqual(d.platform_partition.map(x=>[x.platform,x.native_requests,x.native_completed]),[
  ["windows",43,0],["android",1,0]]);
 assert.equal(d.platform_partition[0].requires_windows_b10_b11,true);
 assert.equal(d.platform_partition[1].requires_windows_b10_b11,false);
 assert.ok(d.platform_partition.every(x=>x.review_completed===false&&!x.native_authorization));
 const native=d.records.filter(x=>x.kind==="NATIVE_CASE");
 assert.equal(native.filter(x=>x.platform==="windows").length,43);
 const android=native.filter(x=>x.platform==="android");
 assert.equal(android.length,1);
 assert.ok(!android[0].prerequisite_blocker_ids.includes("B10")&&!android[0].prerequisite_blocker_ids.includes("B11"));
});
test("L18 ancestry pins L07–L17 commits and L13–L17 public blobs",async()=>{
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
 L15:"0192075fb02587c9f3d9db6b170500cba365251c",
 L16:"709776022679dc5831748ea4ed2254c6ced1da84",
 L17:"eb1333953d02d319e9b44a96c23fe2e071bd2a2e"});
 assert.deepEqual(d.public_sources,[
 {stage:"L13",path:"data/regions/sinnoh-l13-public-evidence-queue.json",git_blob_sha1:"357215cdfd96b37eaac291e1c0ab3873069a12fe"},
 {stage:"L14",path:"data/regions/sinnoh-l14-public-readiness-matrix.json",git_blob_sha1:"d882d6a20b1c01be33744f14ab7826af2fb6ef41"},
 {stage:"L15",path:"data/regions/sinnoh-l15-public-consistency-diff.json",git_blob_sha1:"1a19883a3f0523add6aeaa4f78262b922a041e95"},
 {stage:"L16",path:"data/regions/sinnoh-l16-public-exit-gates.json",git_blob_sha1:"c9e3047106d7860bb966b5927a1fd8304506d395"},
 {stage:"L17",path:"data/regions/sinnoh-l17-public-review-index.json",git_blob_sha1:"273feb1460b9200cd3c0af63cf4ebb092b8691df"}]);
});
test("L18 0/5 local, 0/20 humans, 0/44 native, 0/13 BCD, R07–R09 pending",async()=>{
 const d=await data();
 assert.deepEqual([d.counts.local_reports,d.counts.human_approved,d.counts.native_completed,
 d.counts.native_approved,d.counts.phase_bcd_completed],[0,0,0,0,0]);
 assert.equal(d.counts.phase_bcd_total,13);
 assert.deepEqual([d.gates.r07,d.gates.r08,d.gates.r09],["PENDING","PENDING","PENDING"]);
 assert.equal(d.policy.sinnoh_playable,false);
 for(const k of ["gaps_are_not_human_signoffs","no_private_evidence_intake","next_steps_are_not_native_instructions",
  "no_uploads","no_native_execution","watch_unchanged_not_global_save_isolation",
  "asset_rights_not_approved","mapids_not_reserved"])assert.equal(d.policy[k],true);
});
test("L18 portal accessible read-only filters and safe textContent rendering",async()=>{
 const html=await get("site/public/sinnoh-l18-lacunas-revisao.html");
 const js=await get("site/public/assets/sinnoh-l18-review-gaps.js");
 for(const id of ["search","priority","kind","platform","blocker","gap","reset","status",
 "recordRows","groupRows","platformRows","detail","filtros","pedidos","detalhes",
 "grupos","proveniencia"])assert.ok(html.includes('id="'+id+'"'),id);
 for(const token of ["document.createElement","textContent","replaceChildren","addEventListener",
  "next_documentary_step","no_private_evidence_intake"])assert.ok(js.includes(token),token);
 for(const forbidden of ["innerHTML","eval(","localStorage","FormData","WebSocket",
 "navigator.sendBeacon","XMLHttpRequest",'method: "POST"'])assert.equal(js.includes(forbidden),false,forbidden);
 assert.ok(js.includes("/data/sinnoh-l18-public-review-gaps.json"));
 assert.ok((await get("site/src/index.html")).includes("/sinnoh-l18-lacunas-revisao.html"));
});
