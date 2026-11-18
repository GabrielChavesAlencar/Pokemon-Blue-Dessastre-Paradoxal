import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import path from "node:path";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const get=p=>readFile(path.join(root,p),"utf8");
const source="data/regions/sinnoh-l17-public-review-index.json";
const mirror="site/public/data/sinnoh-l17-public-review-index.json";
const data=async()=>JSON.parse(await get(source));

test("L17 public mirror is byte identical",async()=>assert.equal(await get(source),await get(mirror)));
test("L17 all 88 requests remain blocked and without independent review",async()=>{
 const d=await data();
 assert.equal(d.schema,1);assert.equal(d.stage,"L17");assert.equal(d.version,1);
 assert.equal(d.status,"PUBLIC_REVIEWER_INDEX_ALL_UNREVIEWED_NO_NATIVE_QA");
 assert.equal(d.mode,"PUBLIC_READ_ONLY_NO_EVIDENCE_INTAKE");
 assert.equal(d.records.length,88);
 assert.deepEqual(d.records.map(x=>x.order),Array.from({length:88},(_,i)=>i+1));
 assert.equal(new Set(d.records.map(x=>x.request_id)).size,88);
 assert.ok(d.records.every(x=>x.status==="PENDING"&&x.readiness==="BLOCKED"
 &&x.review_state==="NOT_REVIEWED"&&!x.independent_signoff&&!x.physical_evidence_accepted
 &&!x.native_qa_authorized&&!x.assigned_reviewer&&!x.private_document_reference&&!x.exit_criteria_met));
 assert.equal(d.counts.indexed_requests,88);
 assert.equal(d.counts.reviews_completed,0);
 assert.equal(d.counts.physical_signoffs,0);
 assert.equal(d.counts.exit_criteria_fulfilled,0);
});
test("L17 preserves 1084 documentary links and 18 anonymous unassigned slots",async()=>{
 const d=await data();
 assert.equal(d.records.reduce((n,x)=>n+x.documentary_dependency_count,0),1084);
 assert.equal(d.counts.review_index_documentary_links,1084);
 const anon=d.records.filter(x=>x.anonymous_bookkeeping_slot);
 assert.equal(anon.length,18);
 assert.ok(anon.every(x=>x.documentary_dependency_count===0&&x.linked_l04_criterion_ids.length===0
 &&x.documentary_dependency_request_ids.length===0&&!x.assigned_reviewer));
});
test("L17 kinds 5+1+5+20+13+44 remain all unreviewed",async()=>{
 const d=await data();
 assert.deepEqual(d.group_summary.map(x=>[x.kind,x.requests,x.documentary_links]),[
 ["BLOCKER_DEPENDENCY",5,0],["GLOBAL_REGIONAL_GATE",1,0],["LOCAL_REPORT_SLOT",5,0],
 ["HUMAN_CRITERION",20,20],["BCD_PENDING_SLOT",13,0],["NATIVE_CASE",44,1064]]);
 assert.ok(d.group_summary.every(x=>x.independent_reviews_completed===0&&x.physical_evidence_accepted===0
 &&x.review_state==="NOT_REVIEWED"&&x.blocked===x.requests));
 assert.equal(d.review_guidance_templates.length,6);
 assert.ok(d.records.every(x=>x.review_scope==="PUBLIC_METADATA_ORIENTATION_ONLY"&&x.reviewer_guidance));
});
test("L17 R09 global and Windows 43 Android 1 isolated",async()=>{
 const d=await data();
 assert.equal(d.global_r09.id,"R09");assert.equal(d.global_r09.status,"PENDING");
 assert.equal(d.global_r09.independent_review_complete,false);
 assert.deepEqual(d.global_r09.case_ids,[]);
 assert.deepEqual(d.global_r09.documentary_dependency_request_ids,[]);
 assert.deepEqual(d.platform_partition.map(x=>[x.platform,x.native_requests,x.native_completed]),[
 ["windows",43,0],["android",1,0]]);
 assert.equal(d.platform_partition[0].requires_windows_b10_b11,true);
 assert.equal(d.platform_partition[1].requires_windows_b10_b11,false);
 assert.ok(d.platform_partition.every(x=>x.independent_review_complete===false&&!x.native_authorization));
 const native=d.records.filter(x=>x.kind==="NATIVE_CASE");
 assert.equal(native.filter(x=>x.platform==="windows").length,43);
 const android=native.find(x=>x.platform==="android");
 assert.ok(android);
 assert.ok(!android.prerequisite_blocker_ids.includes("B10")&&!android.prerequisite_blocker_ids.includes("B11"));
});
test("L17 immutable L07-L16 Git ancestry and public source SHA",async()=>{
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
 L16:"709776022679dc5831748ea4ed2254c6ced1da84"});
 assert.deepEqual(d.public_sources,[
 {stage:"L13",path:"data/regions/sinnoh-l13-public-evidence-queue.json",git_blob_sha1:"357215cdfd96b37eaac291e1c0ab3873069a12fe"},
 {stage:"L14",path:"data/regions/sinnoh-l14-public-readiness-matrix.json",git_blob_sha1:"d882d6a20b1c01be33744f14ab7826af2fb6ef41"},
 {stage:"L15",path:"data/regions/sinnoh-l15-public-consistency-diff.json",git_blob_sha1:"1a19883a3f0523add6aeaa4f78262b922a041e95"},
 {stage:"L16",path:"data/regions/sinnoh-l16-public-exit-gates.json",git_blob_sha1:"c9e3047106d7860bb966b5927a1fd8304506d395"}]);
});
test("L17 no physical signoffs or permissions from metadata",async()=>{
 const d=await data();
 assert.deepEqual([d.counts.local_reports,d.counts.human_approved,d.counts.native_completed,
 d.counts.native_approved,d.counts.phase_bcd_completed],[0,0,0,0,0]);
 assert.equal(d.counts.phase_bcd_total,13);
 assert.deepEqual([d.gates.r07,d.gates.r08,d.gates.r09],["PENDING","PENDING","PENDING"]);
 assert.equal(d.policy.sinnoh_playable,false);
 for(const k of ["review_guidance_is_not_signoff","no_evidence_intake","no_private_uploads",
 "no_native_test_authority","priority_not_execution_order","watch_unchanged_not_global_save_isolation",
 "rights_not_approved","mapids_not_reserved","no_assigned_reviewers"])assert.equal(d.policy[k],true);
});
test("L17 portal strictly text-only with local filters and no upload actions",async()=>{
 const html=await get("site/public/sinnoh-l17-revisao-independente.html");
 const js=await get("site/public/assets/sinnoh-l17-public-review.js");
 for(const id of ["search","priority","kind","platform","blocker","criterion","reset",
 "recordRows","groupRows","platformRows","detail","status","filtros","pedidos",
 "detalhes","categorias","proveniencia"])assert.ok(html.includes('id="'+id+'"'),id);
 for(const token of ["document.createElement","textContent","replaceChildren","addEventListener",
 "reviewer_guidance","no_evidence_intake"])assert.ok(js.includes(token),token);
 for(const bad of ["innerHTML","eval(","localStorage","FormData","WebSocket",
 "navigator.sendBeacon","XMLHttpRequest",'method: "POST"'])assert.equal(js.includes(bad),false,bad);
 assert.ok(js.includes("/data/sinnoh-l17-public-review-index.json"));
 assert.ok((await get("site/src/index.html")).includes("/sinnoh-l17-revisao-independente.html"));
});
