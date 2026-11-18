import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const get=p=>readFile(path.join(root,p),"utf8");
const json=async p=>JSON.parse(await get(p));
const src="data/regions/sinnoh-l12-public-coverage-gaps.json";
const mirror="site/public/data/sinnoh-l12-public-coverage-gaps.json";

test("L12 mirror bytes identical and document stage version locked",async()=>{
 assert.equal(await get(src),await get(mirror));
 const d=await json(src);
 assert.equal(d.schema,1);
 assert.equal(d.stage,"L12");
 assert.equal(d.version,1);
 assert.equal(d.status,"DOCUMENTARY_COVERAGE_COMPLETE_PHYSICAL_EVIDENCE_MISSING");
 assert.equal(d.mode,"PUBLIC_READ_ONLY_EVIDENCE_GAPS");
});
test("L12 public links are complete without approving any real evidence",async()=>{
 const d=await json(src);
 assert.deepEqual(d.coverage_layers.map(x=>[x.expected,x.observed,x.missing]),[
  [1084,1084,0],[20,0,20],[43,0,43],[1,0,1],[5,0,5],[13,0,13]]);
 assert.ok(d.coverage_layers.every(x=>!x.native_evidence));
 assert.equal(d.counts.documentary_links_verified,1084);
 assert.equal(d.counts.documentary_links_missing,0);
 assert.equal(d.documentary_integrity.physical_source_authenticated,false);
 assert.equal(d.documentary_integrity.human_review_completed,false);
 assert.equal(d.documentary_integrity.native_qa_completed,false);
});
test("L12 preserves 44 distinct cases and 20 distinct pending review criteria",async()=>{
 const d=await json(src);
 assert.equal(d.case_handoff.length,44);
 assert.equal(new Set(d.case_handoff.map(x=>x.id)).size,44);
 assert.equal(d.criterion_handoff.length,20);
 assert.equal(new Set(d.criterion_handoff.map(x=>x.id)).size,20);
 assert.ok(d.case_handoff.every(x=>x.native_qa_state==="NOT_EXECUTED"&&x.independent_human_review_state==="NOT_REVIEWED"
  &&x.authorized_native_qa===false&&x.evidence_accepted===false));
 assert.ok(d.criterion_handoff.every(x=>x.independent_review_state==="NOT_REVIEWED"
  &&x.accepted_evidence===false&&x.human_signoff===false));
 assert.equal(d.counts.human_approved,0);
 assert.equal(d.counts.native_completed,0);
 assert.equal(d.counts.native_approved,0);
 assert.equal(d.counts.local_reports,0);
 assert.equal(d.counts.phase_bcd_completed,0);
});
test("L12 Windows B10/B11 do not leak to independent Android and R09 is global",async()=>{
 const d=await json(src);
 assert.deepEqual(d.platform_handoff.map(x=>[x.platform,x.native_cases_missing]),[["windows",43],["android",1]]);
 assert.ok(d.platform_handoff.every(x=>!x.shares_android_approval&&x.native_cases_tested===0));
 assert.equal(d.platform_handoff[0].requires_windows_b10_b11,true);
 assert.equal(d.platform_handoff[1].requires_windows_b10_b11,false);
 assert.equal(d.case_handoff.filter(x=>x.platform==="android").length,1);
 assert.ok(d.case_handoff.filter(x=>x.platform==="android").every(x=>!x.pending_gates.includes("B10")&&!x.pending_gates.includes("B11")));
 assert.ok(d.case_handoff.filter(x=>x.platform==="windows").every(x=>x.pending_gates.includes("B10")&&x.pending_gates.includes("B11")));
 assert.equal(d.global_r09.id,"R09");
 assert.equal(d.global_r09.not_a_new_case,true);
 assert.deepEqual(d.global_r09.case_ids,[]);
 assert.equal(d.blockers.at(-1).id,"R09");
 assert.deepEqual(d.blockers.at(-1).case_ids,[]);
});
test("L12 commits L07-L11 and real gates remain pending",async()=>{
 const d=await json(src);
 assert.deepEqual(d.baseline_commits,{
  L07:"d98033b362dac82347e0d97cb5606870eaa70b22",
  L08:"8617ef47ea6745920cb6fe4be251982380d7628d",
  L09:"39e51de92aafdab3f5aea3f929f57f5c0bb72b2d",
  L10:"7fd821007e63fe9cf0d0c4bf14d153a23cda2b6a",
  L11:"9d901a0cf21aa2742f731ee387a51f945bac8a5d"
 });
 assert.equal(d.source_l11.git_blob_sha1,"c39f81867568fb95c65ca8113431e1db05919168");
 assert.deepEqual([d.gates.r07,d.gates.r08,d.gates.r09],["PENDING","PENDING","PENDING"]);
 assert.equal(d.guardrails.sinnoh_playable,false);
 assert.equal(d.guardrails.watch_unchanged_not_global_save_isolation,true);
 assert.equal(d.guardrails.asset_rights_not_approved,true);
 assert.equal(d.guardrails.mapids_not_reserved,true);
 assert.equal(d.guardrails.local_android_l05_complete,false);
});
test("L12 public page has read-only filters and text-only rendering",async()=>{
 const html=await get("site/public/sinnoh-l12-lacunas.html");
 const js=await get("site/public/assets/sinnoh-l12-coverage-gaps.js");
 for(const id of ["layersRows","casesRows","criteriaRows","blockersRows",
  "search","platform","kind","criterion","blocker","gap","reset","status"])
  assert.ok(html.includes('id="'+id+'"'),id);
 for(const s of ["document.createElement","textContent","replaceChildren","addEventListener","coverage_layers","case_handoff"])
  assert.ok(js.includes(s),s);
 for(const forbidden of ["innerHTML","eval(","localStorage","FormData","WebSocket","navigator.sendBeacon",'method: "POST"'])
  assert.equal(js.includes(forbidden),false,forbidden);
 assert.ok(js.includes("/data/sinnoh-l12-public-coverage-gaps.json"));
 assert.ok((await get("site/src/index.html")).includes("/sinnoh-l12-lacunas.html"));
});
