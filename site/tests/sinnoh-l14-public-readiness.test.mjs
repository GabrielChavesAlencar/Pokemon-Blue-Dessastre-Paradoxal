import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import path from "node:path";

const ROOT=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const get=p=>readFile(path.join(ROOT,p),"utf8");
const source="data/regions/sinnoh-l14-public-readiness-matrix.json";
const mirror="site/public/data/sinnoh-l14-public-readiness-matrix.json";
const data=async()=>JSON.parse(await get(source));

test("L14 public source and mirror match byte for byte",async()=>{
 assert.equal(await get(source),await get(mirror));
});
test("L14 all 88 requests blocked and same L13 order and priorities",async()=>{
 const d=await data();
 assert.equal(d.schema,1);
 assert.equal(d.stage,"L14");
 assert.equal(d.status,"ALL_DEPENDENCY_REQUESTS_BLOCKED_NO_NATIVE_QA");
 assert.equal(d.mode,"PUBLIC_READ_ONLY_DOCUMENTARY_DEPENDENCIES");
 assert.equal(d.rows.length,88);
 assert.deepEqual(d.rows.map(r=>r.order),Array.from({length:88},(_,i)=>i+1));
 assert.equal(new Set(d.rows.map(r=>r.request_id)).size,88);
 assert.ok(d.rows.every(r=>r.readiness==="BLOCKED"&&r.status==="PENDING"
   &&r.human_approval===false&&r.physical_evidence_received===false
   &&r.native_qa_authorized===false&&r.private_submission_allowed===false));
 assert.equal(d.counts.rows_ready,0);
 assert.equal(d.counts.rows_pending,88);
 assert.equal(d.counts.rows_blocked,88);
});
test("L14 documentary dependencies exactly 1084 and never include R09 case link",async()=>{
 const d=await data();
 const rows=d.rows;
 assert.equal(rows.reduce((n,x)=>n+x.documentary_dependency_request_ids.length,0),1084);
 assert.equal(d.counts.request_documentary_links,1084);
 assert.deepEqual([d.counts.case_to_criterion_request_links,
 d.counts.case_to_blocker_request_links,d.counts.criterion_to_blocker_request_links],[846,218,20]);
 const human=rows.filter(r=>r.kind==="HUMAN_CRITERION");
 const native=rows.filter(r=>r.kind==="NATIVE_CASE");
 assert.equal(human.length,20);assert.equal(native.length,44);
 assert.equal(human.reduce((n,x)=>n+x.documentary_dependency_count,0),20);
 assert.equal(native.reduce((n,x)=>n+x.documentary_dependency_count,0),1064);
 const all=new Set(rows.map(r=>r.request_id));
 assert.ok(rows.every(r=>r.documentary_dependency_request_ids.every(id=>all.has(id))));
 assert.ok(rows.every(r=>!r.documentary_dependency_request_ids.includes("L13-GLOBAL-R09")));
 assert.deepEqual(d.global_r09.dependency_request_ids,[]);
 assert.deepEqual(d.global_r09.case_ids,[]);
});
test("L14 keeps all 18 anonymous bookkeeping slots unlinked and does not fabricate real reports",async()=>{
 const d=await data();
 const anonymous=d.rows.filter(x=>x.anonymous_bookkeeping_slot);
 assert.equal(anonymous.length,18);
 assert.ok(anonymous.every(x=>!x.scope_known&&x.documentary_dependency_count===0
    &&x.documentary_dependency_request_ids.length===0));
 assert.equal(d.dependency_semantics.no_derived_dependencies_for_anonymous_slots,true);
 assert.equal(d.dependency_semantics.priority_is_not_execution_order,true);
 assert.equal(d.dependency_semantics.links_are_documentary_only,true);
 assert.equal(d.dependency_semantics.readiness_never_infers_auth,true);
});
test("L14 Windows 43 versus Android 1 separate with no B10/B11 Android links",async()=>{
 const d=await data();
 assert.deepEqual(d.platform_partition.map(p=>[p.platform,p.native_requests,p.native_completed]),
 [["windows",43,0],["android",1,0]]);
 assert.equal(d.platform_partition[0].requires_windows_sandbox_b10_b11,true);
 assert.equal(d.platform_partition[1].requires_windows_sandbox_b10_b11,false);
 assert.ok(d.platform_partition.every(p=>p.readiness==="BLOCKED"&&!p.authorization));
 const native=d.rows.filter(r=>r.kind==="NATIVE_CASE");
 assert.equal(native.filter(r=>r.platform==="windows").length,43);
 assert.equal(native.filter(r=>r.platform==="android").length,1);
 assert.ok(native.filter(r=>r.platform==="android").every(r=>
 !r.documentary_dependency_request_ids.some(id=>id==="L13-BLOCKER-B10"||id==="L13-BLOCKER-B11")));
});
test("L14 baseline L07–L13 and no natively playable assertion",async()=>{
 const d=await data();
 assert.deepEqual(d.baseline_commits,{
   L07:"d98033b362dac82347e0d97cb5606870eaa70b22",
   L08:"8617ef47ea6745920cb6fe4be251982380d7628d",
   L09:"39e51de92aafdab3f5aea3f929f57f5c0bb72b2d",
   L10:"7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a",
   L11:"9d901a0cf21aa2742f731ee387a51f945bac8a5d",
   L12:"58b7f2fec9f66dee06d95676eec66fb2ded6a1de",
   L13:"1f12bcc86c10dcc934b024a0562cdadb65d5e2c2"
 });
 assert.equal(d.source_l13.git_blob_sha1,"357215cdfd96b37eaac291e1c0ab3873069a12fe");
 assert.equal(d.counts.documentary_links_verified,1084);
 assert.deepEqual([d.gates.r07,d.gates.r08,d.gates.r09],["PENDING","PENDING","PENDING"]);
 assert.deepEqual([d.counts.local_reports,d.counts.human_approved,
 d.counts.native_completed,d.counts.native_approved,d.counts.phase_bcd_completed],[0,0,0,0,0]);
 assert.equal(d.counts.phase_bcd_total,13);
 assert.equal(d.disclaimer.sinnoh_playable,false);
 assert.equal(d.disclaimer.none_ready,true);
 assert.equal(d.disclaimer.none_physically_approved,true);
 assert.equal(d.disclaimer.no_upload_or_attachments,true);
 assert.equal(d.disclaimer.mapids_not_reserved,true);
 assert.equal(d.disclaimer.asset_rights_not_approved,true);
 assert.equal(d.disclaimer.watch_unchanged_is_not_global_save_isolation,true);
});
test("L14 site only renders text and filters locally without upload or execution",async()=>{
 const html=await get("site/public/sinnoh-l14-prontidao.html");
 const js=await get("site/public/assets/sinnoh-l14-public-readiness.js");
 for(const id of ["search","priority","kind","platform","readiness","link","reset","status",
  "matrixRows","platformRows","detail","matriz","detalhes","filas","proveniencia"])
   assert.ok(html.includes('id="'+id+'"'),id);
 for(const token of ["document.createElement","textContent","replaceChildren","addEventListener","documentary_dependency_request_ids"])
   assert.ok(js.includes(token),token);
 for(const forbidden of ["innerHTML","eval(","localStorage","FormData","WebSocket","navigator.sendBeacon",'method: "POST"'])
   assert.equal(js.includes(forbidden),false,forbidden);
 assert.ok(js.includes("/data/sinnoh-l14-public-readiness-matrix.json"));
 assert.ok((await get("site/src/index.html")).includes("/sinnoh-l14-prontidao.html"));
});
