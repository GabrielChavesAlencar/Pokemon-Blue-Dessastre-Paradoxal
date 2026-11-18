import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import path from "node:path";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const get=p=>readFile(path.join(root,p),"utf8");
const data="data/regions/sinnoh-l13-public-evidence-queue.json";
const mirror="site/public/data/sinnoh-l13-public-evidence-queue.json";
const json=async()=>JSON.parse(await get(data));

test("L13 public source and portal mirror are byte-identical",async()=>{
 assert.equal(await get(data),await get(mirror));
});
test("L13 deterministic 88 entries and five levels, all pending",async()=>{
 const d=await json();
 assert.equal(d.schema,1);assert.equal(d.stage,"L13");
 assert.equal(d.status,"PUBLIC_REQUEST_QUEUE_PENDING_NO_PHYSICAL_EVIDENCE");
 assert.equal(d.mode,"PUBLIC_READ_ONLY_NO_UPLOAD_NO_QA");
 assert.equal(d.queue.length,88);
 assert.deepEqual(d.queue.map(x=>x.order),Array.from({length:88},(_,i)=>i+1));
 assert.equal(new Set(d.queue.map(x=>x.request_id)).size,88);
 assert.deepEqual(d.queue.map(x=>x.priority),[...d.queue.map(x=>x.priority)].sort((a,b)=>a-b));
 assert.deepEqual(d.priority_rules.map(x=>x.priority),[0,1,2,3,4]);
 assert.ok(d.queue.every(x=>x.status==="PENDING"&&!x.accepted_evidence
   &&!x.human_approved&&!x.native_qa_authorized&&x.read_only
   &&x.request_mode==="SANITIZED_PUBLIC_STATUS_ONLY"));
});
test("L13 5 blockers, 1 regional R09, 5 report slots, 20 human criteria, 13 bookkeeping, 44 native",async()=>{
 const d=await json();
 const n=(kind)=>d.queue.filter(x=>x.kind===kind);
 assert.deepEqual([
  n("BLOCKER_DEPENDENCY").length,n("GLOBAL_REGIONAL_GATE").length,
  n("LOCAL_REPORT_SLOT").length,n("HUMAN_CRITERION").length,
  n("BCD_PENDING_SLOT").length,n("NATIVE_CASE").length],[5,1,5,20,13,44]);
 assert.ok(n("LOCAL_REPORT_SLOT").every(x=>x.placeholder_not_a_real_artifact&&!x.case_ids.length));
 assert.ok(n("BCD_PENDING_SLOT").every(x=>x.placeholder_not_a_real_artifact&&!x.criterion_ids.length));
 assert.deepEqual(n("BLOCKER_DEPENDENCY").map(x=>x.subject_id),["B09","B10","B11","R07","R08"]);
 assert.deepEqual(n("GLOBAL_REGIONAL_GATE")[0].case_ids,[]);
 assert.deepEqual(d.global_r09.case_ids,[]);
 assert.equal(d.global_r09.not_case_scoped,true);
 assert.equal(n("NATIVE_CASE").some(x=>x.blocker_ids.includes("R09")),false);
});
test("L13 Windows 43 vs Android 1 distinct and B10/B11 never inherited",async()=>{
 const d=await json();
 const native=d.queue.filter(x=>x.kind==="NATIVE_CASE");
 assert.equal(native.filter(x=>x.platform==="windows").length,43);
 assert.equal(native.filter(x=>x.platform==="android").length,1);
 assert.ok(native.filter(x=>x.platform==="windows").every(x=>x.blocker_ids.includes("B10")&&x.blocker_ids.includes("B11")));
 assert.ok(native.filter(x=>x.platform==="android").every(x=>!x.blocker_ids.includes("B10")&&!x.blocker_ids.includes("B11")));
 assert.deepEqual(d.platform_queues.map(x=>[x.platform,x.native_requests,x.native_completed]),[["windows",43,0],["android",1,0]]);
 assert.equal(d.platform_queues[0].requires_windows_sandbox_b10_b11,true);
 assert.equal(d.platform_queues[1].requires_windows_sandbox_b10_b11,false);
 assert.ok(d.platform_queues.every(x=>!x.authorization));
});
test("L13 retains immutable public SHA ancestry L07-L12 and zero external evidence",async()=>{
 const d=await json();
 assert.deepEqual(d.baseline_commits,{
   L07:"d98033b362dac82347e0d97cb5606870eaa70b22",
   L08:"8617ef47ea6745920cb6fe4be251982380d7628d",
   L09:"39e51de92aafdab3f5aea3f929f57f5c0bb72b2d",
   L10:"7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a",
   L11:"9d901a0cf21aa2742f731ee387a51f945bac8a5d",
   L12:"58b7f2fec9f66dee06d95676eec66fb2ded6a1de"
 });
 assert.equal(d.source_l12.git_blob_sha1,"dbd9181a5910c7fc711eaaa20d0e3b24a9d1710e");
 assert.equal(d.counts.public_edges_verified,1084);
 assert.equal(d.counts.human_approved,0);
 assert.equal(d.counts.local_reports,0);
 assert.equal(d.counts.native_completed,0);
 assert.equal(d.counts.native_approved,0);
 assert.equal(d.counts.phase_bcd_completed,0);
 assert.deepEqual([d.gates.r07,d.gates.r08,d.gates.r09],["PENDING","PENDING","PENDING"]);
 assert.equal(d.disclaimer.sinnoh_playable,false);
 assert.equal(d.disclaimer.mapids_not_reserved,true);
 assert.equal(d.disclaimer.asset_rights_not_approved,true);
 assert.equal(d.disclaimer.watch_unchanged_is_not_global_save_isolation,true);
 assert.equal(d.disclaimer.no_upload_or_attachments,true);
});
test("L13 public viewer renders only text and supports client-only filters",async()=>{
 const html=await get("site/public/sinnoh-l13-pendencias.html");
 const js=await get("site/public/assets/sinnoh-l13-public-queue.js");
 for(const id of ["search","priority","kind","platform","blocker","criterion","reset","queueRows","platformRows","status"])
   assert.ok(html.includes('id="'+id+'"'),id);
 for(const x of ["document.createElement","textContent","replaceChildren","addEventListener","request_mode"])
   assert.ok(js.includes(x),x);
 for(const bad of ["innerHTML","eval(","localStorage","FormData","WebSocket","navigator.sendBeacon",'method: "POST"'])
   assert.equal(js.includes(bad),false,bad);
 assert.ok(js.includes('/data/sinnoh-l13-public-evidence-queue.json'));
 assert.ok((await get("site/src/index.html")).includes('/sinnoh-l13-pendencias.html'));
});
