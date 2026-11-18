import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import path from "node:path";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const get=p=>readFile(path.join(root,p),"utf8");
const source="data/regions/sinnoh-l15-public-consistency-diff.json";
const mirror="site/public/data/sinnoh-l15-public-consistency-diff.json";
const data=async()=>JSON.parse(await get(source));

test("L15 public mirror and source are byte-for-byte identical",async()=>{
 assert.equal(await get(source),await get(mirror));
});
test("L15 88 requests preserve order, identities, priority, states, platforms",async()=>{
 const d=await data();
 assert.equal(d.schema,1);assert.equal(d.stage,"L15");
 assert.equal(d.status,"PUBLIC_DOC_CONSISTENT_L14_PROJECTION_ONLY_ALL_BLOCKED");
 assert.equal(d.mode,"PUBLIC_READ_ONLY_ZERO_PHYSICAL_APPROVAL");
 assert.equal(d.records.length,88);
 assert.deepEqual(d.records.map(x=>x.order),Array.from({length:88},(_,i)=>i+1));
 assert.equal(new Set(d.records.map(x=>x.request_id)).size,88);
 assert.ok(d.records.every(x=>x.source_l13_status==="PENDING"&&x.source_l14_status==="PENDING"
  &&x.readiness==="BLOCKED"&&x.comparison_status==="CONSISTENT_DOCUMENTARY_METADATA"));
 assert.ok(d.records.every(x=>x.identity_drift.length===0&&x.priority_drift.length===0
  &&x.platform_drift.length===0&&x.status_drift.length===0));
 assert.equal(d.counts.source_records_matched,88);
 assert.equal(d.counts.source_records_added,0);
 assert.equal(d.counts.source_records_removed,0);
 assert.equal(d.counts.source_records_reordered,0);
});
test("L15 reports 1084 L14 documentary projection links, not native evidence",async()=>{
 const d=await data();
 assert.deepEqual(d.change_categories.map(x=>[x.id,x.baseline,x.observed,x.added,x.drift]),[
  ["REQUEST_IDENTITIES_AND_ORDER",88,88,0,0],
  ["PRIORITY_PLATFORM_STATUS",88,88,0,0],
  ["L14_DOCUMENTARY_DEPENDENCY_PROJECTION",0,1084,1084,0],
  ["REAL_HUMAN_AND_NATIVE_APPROVAL",0,0,0,0]
 ]);
 assert.equal(d.change_categories[2].state,"ADDED_DOCUMENTARY_PROJECTION_NOT_NATIVE_EVIDENCE");
 assert.equal(d.change_categories[3].state,"NO_REAL_EVIDENCE_RECEIVED");
 assert.equal(d.records.reduce((n,x)=>n+x.l14_documentary_dependency_count,0),1084);
 assert.ok(d.records.every(x=>x.projection_only_no_physical_change));
 assert.equal(d.counts.physical_approval_change_count,0);
 assert.equal(d.counts.actual_evidence_received,0);
});
test("L15 groups retain 5+1+5+20+13+44 and 18 anonymous unassigned",async()=>{
 const d=await data();
 assert.deepEqual(d.group_summary.map(g=>[g.kind,g.requests]),[
  ["BLOCKER_DEPENDENCY",5],["GLOBAL_REGIONAL_GATE",1],
  ["LOCAL_REPORT_SLOT",5],["HUMAN_CRITERION",20],
  ["BCD_PENDING_SLOT",13],["NATIVE_CASE",44]
 ]);
 assert.deepEqual(d.group_summary.map(g=>g.documentary_dependency_links),[0,0,0,20,0,1064]);
 assert.ok(d.group_summary.every(g=>g.ready===0&&g.blocked===g.requests&&g.actual_evidence_received===0));
 const anonymous=d.records.filter(x=>x.anonymous_bookkeeping_slot);
 assert.equal(anonymous.length,18);
 assert.ok(anonymous.every(x=>x.l14_documentary_dependency_count===0));
});
test("L15 R09 remains global and Windows 43 Android 1 retain separate QA lanes",async()=>{
 const d=await data();
 assert.equal(d.global_r09.id,"R09");
 assert.equal(d.global_r09.status,"PENDING");
 assert.equal(d.global_r09.global_gate_only,true);
 assert.deepEqual(d.global_r09.case_ids,[]);
 assert.deepEqual(d.global_r09.documentary_dependency_request_ids,[]);
 assert.deepEqual(d.platform_partition.map(p=>[p.platform,p.native_requests,p.native_completed]),[
  ["windows",43,0],["android",1,0]
 ]);
 assert.equal(d.platform_partition[0].requires_windows_b10_b11,true);
 assert.equal(d.platform_partition[1].requires_windows_b10_b11,false);
 assert.ok(d.platform_partition.every(x=>!x.authorization&&x.native_approved===0&&x.state==="PENDING_BLOCKED"));
 assert.equal(d.records.filter(x=>x.kind==="NATIVE_CASE"&&x.platform==="windows").length,43);
 assert.equal(d.records.filter(x=>x.kind==="NATIVE_CASE"&&x.platform==="android").length,1);
});
test("L15 immutable public L07–L14 and both public Git blob hashes",async()=>{
 const d=await data();
 assert.deepEqual(d.baseline_commits,{
  L07:"d98033b362dac82347e0d97cb5606870eaa70b22",
  L08:"8617ef47ea6745920cb6fe4be251982380d7628d",
  L09:"39e51de92aafdab3f5aea3f929f57f5c0bb72b2d",
  L10:"7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a",
  L11:"9d901a0cf21aa2742f731ee387a51f945bac8a5d",
  L12:"58b7f2fec9f66dee06d95676eec66fb2ded6a1de",
  L13:"1f12bcc86c10dcc934b024a0562cdadb65d5e2c2",
  L14:"11eda18f7225e16b13007c1eb955ccc3d7667b66"
 });
 assert.deepEqual(d.public_source_blobs,[
  {stage:"L13",path:"data/regions/sinnoh-l13-public-evidence-queue.json",git_blob_sha1:"357215cdfd96b37eaac291e1c0ab3873069a12fe"},
  {stage:"L14",path:"data/regions/sinnoh-l14-public-readiness-matrix.json",git_blob_sha1:"d882d6a20b1c01be33744f14ab7826af2fb6ef41"}
 ]);
});
test("L15 every physical signoff and native gate stays closed",async()=>{
 const d=await data();
 assert.deepEqual([d.counts.local_reports,d.counts.human_approved,d.counts.native_completed,
  d.counts.native_approved,d.counts.phase_bcd_completed],[0,0,0,0,0]);
 assert.equal(d.counts.phase_bcd_total,13);
 assert.deepEqual([d.gates.r07,d.gates.r08,d.gates.r09],["PENDING","PENDING","PENDING"]);
 assert.ok(d.records.every(x=>x.accepted_evidence===false&&x.human_approved===false
  &&x.native_qa_authorized===false&&x.private_file_received===false));
 assert.equal(d.policy.sinnoh_playable,false);
 assert.equal(d.policy.zero_documentary_drift_does_not_mean_physical_approval,true);
 assert.equal(d.policy.new_links_are_l14_projection_only,true);
 assert.equal(d.policy.watch_unchanged_not_global_save_isolation,true);
 assert.equal(d.policy.mapids_not_reserved,true);
 assert.equal(d.policy.asset_rights_not_approved,true);
 assert.equal(d.policy.no_uploads,true);
});
test("L15 public viewer has read-only filters, safe text-only rendering and page link",async()=>{
 const html=await get("site/public/sinnoh-l15-consistencia.html");
 const js=await get("site/public/assets/sinnoh-l15-public-diff.js");
 for(const id of ["search","priority","kind","platform","links","drift","reset","status",
 "changesRows","recordRows","groupRows","platformRows","detail","mudancas","comparacoes","detalhes","categorias","proveniencia"]){
  assert.ok(html.includes('id="'+id+'"'),id);
 }
 for(const token of ["document.createElement","textContent","replaceChildren","addEventListener",
  "l14_documentary_dependency_count","no_uploads"]){
   assert.ok(js.includes(token),token);
 }
 for(const bad of ["innerHTML","eval(","localStorage","FormData","WebSocket","navigator.sendBeacon",
   'method: "POST"',"XMLHttpRequest"]){
   assert.equal(js.includes(bad),false,bad);
 }
 assert.ok(js.includes("/data/sinnoh-l15-public-consistency-diff.json"));
 assert.ok((await get("site/src/index.html")).includes("/sinnoh-l15-consistencia.html"));
});
