import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {fileURLToPath} from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const read = relative => readFile(path.join(root, relative), "utf8");
const parse = async relative => JSON.parse(await read(relative));

test("L07 site snapshot mirrors audited GitHub public matrix byte-for-byte", async () => {
  assert.equal(await read("data/regions/sinnoh-l07-public-triage.json"),
               await read("site/public/data/sinnoh-l07-public-triage.json"));
});
test("L07 44 real cases, 20 criteria, no native evidence", async () => {
  const data = await parse("site/public/data/sinnoh-l07-public-triage.json");
  assert.equal(data.stage,"L07");
  assert.equal(data.status,"PUBLIC_READ_ONLY_TRIAGE_ALL_NATIVE_PENDING");
  assert.deepEqual(data.counts,{cases_total:44,windows:43,android:1,criteria_total:20,human_approved:0,native_completed:0,native_approved:0,local_reports:0,phase_bcd_completed:0,phase_bcd_total:13});
  assert.equal(new Set(data.cases.map(x=>x.id)).size,44);
  assert.equal(new Set(data.criteria.map(x=>x.id)).size,20);
  assert.equal(data.cases.filter(x=>x.platform==="android").length,1);
  assert.equal(data.cases.filter(x=>x.platform==="windows").length,43);
  assert.ok(data.cases.every(x=>x.action==="KEEP_PENDING" && x.native_status==="pending" && !x.native_qa_authorized && !x.evidence_accepted));
  assert.ok(data.criteria.every(x=>x.status==="NOT_REVIEWED" && !x.human_signoff && !x.physical_evidence_accepted));
  assert.deepEqual([data.gates.r07,data.gates.r08,data.gates.r09],["PENDING","PENDING","PENDING"]);
  assert.equal(data.gates.sinnoh_playable,false);
  assert.equal(data.gates.b11_global_save_isolation_proven,false);
  assert.equal(data.gates.mapids_reserved,false);
  assert.equal(data.gates.asset_rights_approved,false);
});
test("L07 platform partitions have distinct future native gates", async () => {
  const data = await parse("site/public/data/sinnoh-l07-public-triage.json");
  assert.deepEqual(data.platform_queues.map(x=>x.count),[43,1]);
  assert.equal(data.platform_queues[1].case_ids[0],"android-joi-play");
  assert.ok(data.platform_queues.every(x=>x.documentary_only && !x.approved));
  assert.ok(data.cases.filter(x=>x.platform==="android").every(x=>!x.blocked_by.includes("B10") && !x.blocked_by.includes("B11")));
  assert.ok(data.cases.filter(x=>x.platform==="windows").every(x=>x.blocked_by.includes("B10") && x.blocked_by.includes("B11")));
});
test("L07 static page only reads same-origin public JSON and filters locally", async () => {
  const html = await read("site/public/sinnoh-l07-triagem.html");
  const js = await read("site/public/assets/sinnoh-l07-triage.js");
  for(const id of ["q","platform","kind","criterion","blocker","cases","criteria","reset"]){
    assert.match(html,new RegExp('id="'+id+'"'));
  }
  assert.match(js,/fetch\("\/data\/sinnoh-l07-public-triage\.json"/);
  assert.match(js,/textContent/);
  assert.match(js,/replaceChildren/);
  for(const forbidden of ["innerHTML","localStorage","eval(","postMessage(","WebSocket","FormData","navigator.sendBeacon"]){
    assert.equal(js.includes(forbidden),false,forbidden);
  }
  assert.match(await read("site/src/index.html"),/sinnoh-l07-triagem\.html/);
});
