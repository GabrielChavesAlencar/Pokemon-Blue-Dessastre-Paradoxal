import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import path from "node:path";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const get=p=>readFile(path.join(root,p),"utf8");
const data=async()=>JSON.parse(await get("data/regions/sinnoh-l20-public-reconciliation.json"));
test("L20 mirror is byte-identical to the source report",async()=>{
 assert.equal(await get("data/regions/sinnoh-l20-public-reconciliation.json"),
              await get("site/public/data/sinnoh-l20-public-reconciliation.json"));
});
test("L20 is public-only and keeps 88/88 open",async()=>{
 const d=await data(),c=d.counts;
 assert.equal(d.stage,"L20");assert.equal(d.schema,1);
 assert.equal(d.records.length,88);assert.equal(new Set(d.records.map(r=>r.request_id)).size,88);
 assert.deepEqual(d.records.map(r=>r.order),Array.from({length:88},(_,i)=>i+1));
 assert.equal(c.reconciled_requests,88);assert.equal(c.open_gaps,88);
 assert.equal(c.closed_gaps,0);assert.equal(c.records_added,0);assert.equal(c.records_removed,0);
 assert.ok(d.records.every(r=>r.status==="PENDING"&&r.readiness==="BLOCKED"&&r.gap_open===true
  &&r.correspondence==="MATCHED_L19_PUBLIC_METADATA_ONLY"));
});
test("L20 does not invent human or native approvals",async()=>{
 const d=await data(),c=d.counts;
 for(const k of ["human_approved","native_executed","native_approved","local_reports_received",
 "phase_bcd_completed","exit_criteria_met","physical_evidence_accepted"])assert.equal(c[k],0);
 assert.equal(c.anonymous_unassigned,18);
 assert.ok(d.records.every(r=>!r.independent_review_approved&&!r.native_qa_executed
  &&!r.exit_criteria_met&&!r.physical_evidence_accepted&&!r.assigned_reviewer
  &&!r.anonymous_identity_assigned));
 assert.equal(d.policy.sinnoh_playable,false);
});
test("L20 keeps 1084 documentary edges unchanged",async()=>{
 const d=await data(),c=d.counts;
 assert.deepEqual(d.edge_summary,{case_to_criterion:846,case_to_blocker:218,criterion_to_blocker:20,total:1084});
 assert.equal(c.documentary_links,1084);
 assert.equal(d.records.reduce((n,r)=>n+r.documentary_dependency_count,0),1084);
});
test("L20 platform boundaries and regional R09 are preserved",async()=>{
 const d=await data();
 assert.equal(d.records.filter(r=>r.kind==="NATIVE_CASE"&&r.platform==="windows").length,43);
 assert.equal(d.records.filter(r=>r.kind==="NATIVE_CASE"&&r.platform==="android").length,1);
 assert.deepEqual(d.global_r09.case_ids,[]);
 assert.deepEqual(d.global_r09.documentary_dependency_request_ids,[]);
 assert.equal(d.gates.r07,"PENDING");assert.equal(d.gates.r08,"PENDING");assert.equal(d.gates.r09,"PENDING");
 assert.ok(d.records.filter(r=>r.kind==="NATIVE_CASE"&&r.platform==="android")
  .every(r=>!r.prerequisite_blocker_ids.includes("B10")&&!r.prerequisite_blocker_ids.includes("B11")));
});
test("L20 IDs priorities metadata are strictly projected from L19",async()=>{
 const d=await data();
 const p=JSON.parse(await get("data/regions/sinnoh-l19-public-gap-consolidation.json"));
 const fields=["order","request_id","subject_id","kind","platform","priority","priority_label","gap_types",
 "exit_criteria_codes","prerequisite_blocker_ids","linked_l04_criterion_ids",
 "documentary_dependency_request_ids","documentary_dependency_count","anonymous_bookkeeping_slot",
 "review_state","review_gap_status","status","readiness","independent_review_approved",
 "exit_criteria_met","native_qa_executed","physical_evidence_accepted","assigned_reviewer","anonymous_identity_assigned"];
 for(let i=0;i<88;i++)for(const field of fields)assert.deepEqual(d.records[i][field],p.records[i][field]);
 assert.equal(d.source.git_blob_sha1,"ff9f86e14cd28f7960331580d85e2b10d99b8240");
 assert.equal(d.baseline_commits.L19,"54bbb63a7f2f7a74a26ce8dbc61d52793a27315d");
});
test("L20 panel stays read-only, escaped and links to its pinned JSON",async()=>{
 const [html,js]=await Promise.all([get("site/public/sinnoh-l20-reconciliacao.html"),
 get("site/public/assets/sinnoh-l20-reconciliation.js")]);
 assert.match(html,/sinnoh-l20-reconciliation.js/);
 assert.match(html,/L20/);assert.match(html,/match/);assert.match(html,/blocker/);
 assert.match(js,/textContent/);assert.match(js,/replaceChildren/);
 assert.match(js,/MATCHED_L19_PUBLIC_METADATA_ONLY/);
 assert.doesNotMatch(js,/innerHTML|localStorage|sessionStorage|\.post\s*\(/);
 assert.doesNotMatch(html,/<form\b|type="file"|type="submit"/);
});
