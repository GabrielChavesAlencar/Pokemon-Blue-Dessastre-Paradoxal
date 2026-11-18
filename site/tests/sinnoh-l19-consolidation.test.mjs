import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import path from "node:path";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const get=p=>readFile(path.join(root,p),"utf8");
const file="data/regions/sinnoh-l19-public-gap-consolidation.json";
const mirror="site/public/data/sinnoh-l19-public-gap-consolidation.json";
const data=async()=>JSON.parse(await get(file));

test("L19 primary report and public portal mirror are identical",async()=>{
 assert.equal(await get(file),await get(mirror));
});
test("L19 preserves 88 PENDING/BLOCKED requests with zero approvals",async()=>{
 const d=await data();
 assert.equal(d.schema,1);assert.equal(d.stage,"L19");assert.equal(d.version,1);
 assert.equal(d.status,"PUBLIC_GAP_CONSOLIDATION_VALID_METADATA_ALL_BLOCKED");
 assert.equal(d.mode,"READ_ONLY_PUBLIC_GIT_DOCUMENTS_NO_NATIVE_QA");
 assert.equal(d.records.length,88);
 assert.deepEqual(d.records.map(x=>x.order),Array.from({length:88},(_,i)=>i+1));
 assert.equal(new Set(d.records.map(x=>x.request_id)).size,88);
 assert.ok(d.records.every(x=>x.status==="PENDING"&&x.readiness==="BLOCKED"
  &&x.review_state==="NOT_REVIEWED"&&x.review_gap_status==="OPEN_DOCUMENTARY_ONLY"
  &&!x.independent_review_approved&&!x.exit_criteria_met&&!x.native_qa_executed
  &&!x.physical_evidence_accepted&&!x.assigned_reviewer&&!x.anonymous_identity_assigned));
 assert.equal(d.counts.consolidated_requests,88);
 assert.equal(d.counts.consolidated_gaps_open,88);
 assert.equal(d.counts.consolidated_gaps_closed,0);
 assert.equal(d.counts.consolidated_human_signoffs,0);
 assert.equal(d.counts.consolidated_native_passes,0);
});
test("L19 1084 public links match 846+218+20, no physical inference",async()=>{
 const d=await data();
 assert.deepEqual(d.edge_summary,{case_to_criterion:846,case_to_blocker:218,criterion_to_blocker:20,total:1084});
 assert.equal(d.records.reduce((n,x)=>n+x.documentary_dependency_count,0),1084);
 assert.equal(d.counts.consolidated_links,1084);
 assert.ok(d.records.every(x=>x.public_coverage==="LINKS_DOCUMENTED_NOT_PHYSICAL_EVIDENCE"));
 assert.ok(d.records.every(x=>x.missing_evidence==="INDEPENDENT_REVIEW_AND_NATIVE_QA_UNAVAILABLE"));
 assert.equal(d.policy.public_links_are_not_physical_evidence,true);
});
test("L19 18 anonymous slots remain unassigned, by type 5+13",async()=>{
 const d=await data();
 const anon=d.records.filter(x=>x.anonymous_bookkeeping_slot);
 assert.equal(anon.length,18);
 assert.equal(anon.filter(x=>x.kind==="LOCAL_REPORT_SLOT").length,5);
 assert.equal(anon.filter(x=>x.kind==="BCD_PENDING_SLOT").length,13);
 assert.ok(anon.every(x=>x.documentary_dependency_count===0
  &&x.documentary_dependency_request_ids.length===0
  &&x.linked_l04_criterion_ids.length===0&&!x.anonymous_identity_assigned));
});
test("L19 groups 5 1 5 20 13 44 and R09 regional global",async()=>{
 const d=await data();
 assert.deepEqual(d.kind_summary.map(x=>[x.kind,x.requests,x.documentary_edges]),[
  ["BLOCKER_DEPENDENCY",5,0],["GLOBAL_REGIONAL_GATE",1,0],
  ["LOCAL_REPORT_SLOT",5,0],["HUMAN_CRITERION",20,20],
  ["BCD_PENDING_SLOT",13,0],["NATIVE_CASE",44,1064]]);
 assert.ok(d.kind_summary.every(x=>x.independent_signoffs===0&&x.native_qa_passed===0
  &&x.missing_reviews===x.requests));
 assert.equal(d.global_r09.id,"R09");
 assert.deepEqual(d.global_r09.case_ids,[]);
 assert.deepEqual(d.global_r09.documentary_dependency_request_ids,[]);
 assert.equal(d.global_r09.signoff,false);
 assert.equal(d.global_r09.review_complete,false);
});
test("L19 43 Windows/1 Android remain independent and never executed",async()=>{
 const d=await data();
 assert.deepEqual(d.platform_partition.map(x=>[x.platform,x.native_requests,x.native_completed]),[
  ["windows",43,0],["android",1,0]
 ]);
 assert.equal(d.platform_partition[0].requires_windows_b10_b11,true);
 assert.equal(d.platform_partition[1].requires_windows_b10_b11,false);
 assert.ok(d.platform_partition.every(x=>x.native_authorization===false&&x.review_complete===false));
 const native=d.records.filter(x=>x.kind==="NATIVE_CASE");
 assert.equal(native.filter(x=>x.platform==="windows").length,43);
 const android=native.filter(x=>x.platform==="android");
 assert.equal(android.length,1);
 assert.ok(android.every(x=>!x.prerequisite_blocker_ids.includes("B10")&&!x.prerequisite_blocker_ids.includes("B11")));
});
test("L19 commits L07–L18 and Git blob L18 exactly anchored",async()=>{
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
 L17:"eb1333953d02d319e9b44a96c23fe2e071bd2a2e",
 L18:"38ff6e635287f84464e1371160f3a06ae8dba953"
 });
 assert.equal(d.public_sources.length,6);
 assert.deepEqual(d.public_sources.at(-1),{
  stage:"L18",path:"data/regions/sinnoh-l18-public-review-gaps.json",
  git_blob_sha1:"649e85b2daef7635d00e19201ad5f39cc43c5c90"});
});
test("L19 never converts Git-only review into local reports, human or native QA",async()=>{
 const d=await data();
 assert.deepEqual([d.counts.local_reports,d.counts.human_approved,d.counts.native_completed,
   d.counts.native_approved,d.counts.phase_bcd_completed],[0,0,0,0,0]);
 assert.equal(d.counts.phase_bcd_total,13);
 assert.deepEqual([d.gates.r07,d.gates.r08,d.gates.r09],["PENDING","PENDING","PENDING"]);
 assert.equal(d.policy.sinnoh_playable,false);
 for(const k of ["document_only","comparison_does_not_approve_native_qa",
   "priorities_P0_P4_are_documentary_only","no_private_uploads",
   "R08_asset_rights_not_approved","R07_mapids_not_authorized",
   "B11_watch_unchanged_is_not_global_save_isolation"])assert.equal(d.policy[k],true);
});
test("L19 portal filters, text rendering and no upload/POST",async()=>{
 const html=await get("site/public/sinnoh-l19-consolidacao.html");
 const js=await get("site/public/assets/sinnoh-l19-consolidation.js");
 for(const id of ["search","priority","kind","platform","blocker","gap","reset","status",
 "recordRows","groupRows","platformRows","detail","comparacao","filtros","pedidos",
 "detalhes","proveniencia"])assert.ok(html.includes('id="'+id+'"'),id);
 for(const s of ["document.createElement","textContent","replaceChildren",
   "addEventListener","public_coverage","no_private_uploads"])assert.ok(js.includes(s),s);
 for(const s of ["innerHTML","eval(","FormData","WebSocket","localStorage",
 "XMLHttpRequest","navigator.sendBeacon",'method: "POST"'])assert.equal(js.includes(s),false,s);
 assert.ok(js.includes("/data/sinnoh-l19-public-gap-consolidation.json"));
 assert.ok((await get("site/src/index.html")).includes("/sinnoh-l19-consolidacao.html"));
});
