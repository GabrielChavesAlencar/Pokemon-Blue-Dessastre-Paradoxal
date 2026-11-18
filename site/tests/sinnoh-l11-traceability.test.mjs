import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import path from "node:path";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const get=p=>readFile(path.join(root,p),"utf8");
const src="data/regions/sinnoh-l11-public-traceability.json";
const mirror="site/public/data/sinnoh-l11-public-traceability.json";
const parsed=async p=>JSON.parse(await get(p));

test("L11 public graph and web mirror are byte-for-byte identical",async()=>{
 assert.equal(await get(src),await get(mirror));
});
test("L11 44 cases, 20 criteria and 1084 exact forward links",async()=>{
 const d=await parsed(src);
 assert.equal(d.schema,1);
 assert.equal(d.stage,"L11");
 assert.equal(d.status,"PUBLIC_TRACEABILITY_ALL_NATIVE_AND_HUMAN_PENDING");
 assert.equal(d.mode,"PUBLIC_READ_ONLY_NO_NATIVE_QA");
 assert.equal(d.case_nodes.length,44);
 assert.equal(d.criterion_nodes.length,20);
 assert.equal(d.blocker_nodes.length,6);
 assert.deepEqual(Object.fromEntries(Object.entries(d.edges).map(([key,values])=>[key,values.length])),{
  case_to_criterion:846,case_to_blocker:218,criterion_to_blocker:20
 });
 assert.equal(d.case_nodes.filter(c=>c.platform==="windows").length,43);
 assert.equal(d.case_nodes.filter(c=>c.platform==="android").length,1);
 assert.equal(d.case_nodes.at(-1).id,"android-joi-play");
 assert.equal(new Set(d.case_nodes.map(x=>x.id)).size,44);
 assert.equal(new Set(d.criterion_nodes.map(x=>x.id)).size,20);
});
test("L11 graph has deterministic inverse criterion links and no R09 case edges",async()=>{
 const d=await parsed(src);
 for(const criterion of d.criterion_nodes){
   assert.deepEqual(d.edges.case_to_criterion.filter(x=>x[1]===criterion.id).map(x=>x[0]),criterion.case_ids);
 }
 assert.deepEqual(d.edges.criterion_to_blocker,d.criterion_nodes.map(x=>[x.id,x.stage]));
 assert.deepEqual(d.edges.case_to_criterion,d.case_nodes.flatMap(c=>c.criteria_ids.map(k=>[c.id,k])));
 assert.deepEqual(d.edges.case_to_blocker,d.case_nodes.flatMap(c=>c.blocker_ids.map(k=>[c.id,k])));
 assert.equal(d.global_region_gate.id,"R09");
 assert.equal(d.global_region_gate.is_case_scoped,false);
 assert.deepEqual(d.global_region_gate.case_ids,[]);
 assert.deepEqual(d.blocker_nodes.at(-1).case_ids,[]);
 assert.equal(d.edges.case_to_blocker.some(e=>e[1]==="R09"),false);
});
test("L11 Windows B10/B11 and Android are independent, no native approval",async()=>{
 const d=await parsed(src);
 assert.deepEqual(d.platform_lanes.map(p=>p.case_ids.length),[43,1]);
 assert.deepEqual(d.platform_lanes.map(p=>p.platform),["windows","android"]);
 assert.ok(d.platform_lanes.every(p=>p.status==="PENDING"&&p.approved===false&&p.separate_native_gate));
 assert.ok(d.case_nodes.filter(x=>x.platform==="windows").every(x=>x.blocker_ids.includes("B10")&&x.blocker_ids.includes("B11")));
 assert.ok(d.case_nodes.filter(x=>x.platform==="android").every(x=>!x.blocker_ids.includes("B10")&&!x.blocker_ids.includes("B11")));
 assert.ok(d.case_nodes.every(x=>x.native_status==="pending"&&!x.native_qa_authorized&&!x.human_signoff));
 assert.ok(d.criterion_nodes.every(x=>x.review_state==="NOT_REVIEWED"&&!x.human_signoff));
 assert.ok(d.blocker_nodes.every(x=>x.status==="PENDING"&&!x.native_qa_authorized));
});
test("L11 public gates and baseline public commit IDs remain exact",async()=>{
 const d=await parsed(src);
 assert.deepEqual(d.baseline_commits,{
 L07:"d98033b362dac82347e0d97cb5606870eaa70b22",
 L08:"8617ef47ea6745920cb6fe4be251982380d7628d",
 L09:"39e51de92aafdab3f5aea3f929f57f5c0bb72b2d",
 L10:"7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a"
 });
 assert.deepEqual([d.gates.r07,d.gates.r08,d.gates.r09],["PENDING","PENDING","PENDING"]);
 assert.equal(d.public_drift_audit.differences_found,0);
 assert.equal(d.public_drift_audit.zero_drift,true);
 assert.equal(d.counts.local_reports,0);
 assert.equal(d.counts.human_approved,0);
 assert.equal(d.counts.native_completed,0);
 assert.equal(d.counts.native_approved,0);
 assert.equal(d.counts.phase_bcd_completed,0);
 assert.equal(d.counts.phase_bcd_total,13);
 for(const [key,value] of Object.entries(d.guarantees)){
   if(["sinnoh_playable","local_android_l05_complete"].includes(key))assert.equal(value,false);
   else assert.equal(value,true,key);
 }
});
test("L11 read-only link and filter panel only renders text",async()=>{
 const html=await get("site/public/sinnoh-l11-rastreabilidade.html");
 const js=await get("site/public/assets/sinnoh-l11-traceability.js");
 for(const id of ["caseRows","criteriaRows","blockerRows","search","platform","criterionFilter",
   "blockerFilter","status","caseDetail","reset","casos","criterios","bloqueios","detalhes"])
     assert.ok(html.includes('id="'+id+'"'),id);
 for(const method of ["document.createElement","textContent","replaceChildren","addEventListener",
   "case_to_criterion","case_to_blocker","criterion_to_blocker"])assert.ok(js.includes(method),method);
 for(const forbidden of ["innerHTML","eval(","localStorage","FormData","WebSocket","navigator.sendBeacon",
   'method: "POST"',"fetch(\"https://"])assert.equal(js.includes(forbidden),false,forbidden);
 assert.ok(js.includes("/data/sinnoh-l11-public-traceability.json"));
 assert.ok((await get("site/src/index.html")).includes("/sinnoh-l11-rastreabilidade.html"));
});
