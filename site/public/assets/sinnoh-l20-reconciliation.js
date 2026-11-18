"use strict";
// Static, same-origin public report. No uploads, native commands, storage or writes.
const byId=id=>document.getElementById(id);
const el=(tag,text)=>{const x=document.createElement(tag);x.textContent=String(text);return x;};
const set=(id,value)=>{byId(id).textContent=String(value);};
const addText=(parent,text)=>parent.append(el("p",text));
function validate(d){
 const c=d?.counts, p=d?.policy,rows=d?.records;
 if(d?.schema!==1||d?.region!=="SINNOH"||d?.stage!=="L20"||d?.version!==1
 ||d.status!=="PUBLIC_METADATA_RECONCILED_88_GAPS_OPEN_NO_NATIVE_QA"
 ||d.mode!=="PUBLIC_READ_ONLY_RECONCILIATION_NO_PHYSICAL_EVIDENCE"
 ||d.source?.git_blob_sha1!=="ff9f86e14cd28f7960331580d85e2b10d99b8240"
 ||d.baseline_commits?.L19!=="54bbb63a7f2f7a74a26ce8dbc61d52793a27315d"
 ||!Array.isArray(rows)||rows.length!==88||new Set(rows.map(r=>r.request_id)).size!==88
 ||!c||c.reconciled_requests!==88||c.records_matched!==88
 ||c.records_added!==0||c.records_removed!==0||c.identity_drift!==0
 ||c.priority_drift!==0||c.platform_drift!==0||c.status_drift!==0||c.approval_drift!==0
 ||c.open_gaps!==88||c.closed_gaps!==0||c.pending!==88||c.blocked!==88
 ||c.documentary_links!==1084||c.case_to_criterion!==846
 ||c.case_to_blocker!==218||c.criterion_to_blocker!==20
 ||c.anonymous_unassigned!==18||c.local_reports_received!==0
 ||c.human_approved!==0||c.native_executed!==0||c.native_approved!==0
 ||c.phase_bcd_completed!==0||c.windows_pending!==43||c.android_pending!==1
 ||c.exit_criteria_met!==0||c.physical_evidence_accepted!==0
 ||d.edge_summary?.total!==1084||!Array.isArray(d.priority_summary)
 ||d.priority_summary.map(x=>x.open).join(",")!=="6,5,20,13,44"
 ||d.gates?.r07!=="PENDING"||d.gates?.r08!=="PENDING"||d.gates?.r09!=="PENDING"
 ||d.global_r09?.case_ids?.length!==0||d.global_r09?.documentary_dependency_request_ids?.length!==0
 ||!p||p.sinnoh_playable!==false||p.not_a_native_qa_result!==true
 ||p.not_a_human_review!==true||p.no_private_uploads!==true
 ||p.no_game_exe!==true||p.no_joiplay!==true||p.no_saves!==true
 ||p.android_no_windows_approval_inheritance!==true
 ||rows.reduce((v,r)=>v+r.documentary_dependency_count,0)!==1084
 ||rows.filter(r=>r.anonymous_bookkeeping_slot).length!==18
 ||rows.filter(r=>r.kind==="NATIVE_CASE"&&r.platform==="windows").length!==43
 ||rows.filter(r=>r.kind==="NATIVE_CASE"&&r.platform==="android").length!==1
 ||rows.some((r,i)=>r.order!==i+1||r.status!=="PENDING"||r.readiness!=="BLOCKED"
  ||r.review_state!=="NOT_REVIEWED"||r.review_gap_status!=="OPEN_DOCUMENTARY_ONLY"
  ||r.correspondence!=="MATCHED_L19_PUBLIC_METADATA_ONLY"||r.gap_open!==true
  ||r.independent_review_approved!==false||r.native_qa_executed!==false
  ||r.exit_criteria_met!==false||r.physical_evidence_accepted!==false
  ||r.assigned_reviewer!==false||r.anonymous_identity_assigned!==false
  ||r.prerequisite_blocker_ids.includes("R09")
  ||r.kind==="NATIVE_CASE"&&r.platform==="android"&&
   (r.prerequisite_blocker_ids.includes("B10")||r.prerequisite_blocker_ids.includes("B11"))))
 throw new Error("PUBLIC_L20_FAIL_CLOSED");
 return d;
}
function detail(x){
 const out=byId("details");out.replaceChildren();
 addText(out,"ID: "+x.request_id+" · "+x.kind+" · "+x.platform);
 addText(out,"Estado: "+x.status+" / "+x.readiness+" / "+x.review_gap_status);
 addText(out,"Correspondência: "+x.correspondence+" (somente metadados Git)");
 addText(out,"Lacunas: "+x.gap_types.join(", "));
 addText(out,"Bloqueios por pedido: "+(x.prerequisite_blocker_ids.join(", ")||"nenhum específico; R09 é global"));
 addText(out,"Critérios L04 relacionados: "+(x.linked_l04_criterion_ids.join(", ")||"nenhum"));
 addText(out,"Pedidos de dependência pública: "+(x.documentary_dependency_request_ids.join(", ")||"nenhum"));
 addText(out,"Vínculos documentais: "+x.documentary_dependency_count+" · revisão humana: não realizada · QA nativa: não executada");
}
function filter(d){
 const q=byId("search").value.trim().toLocaleLowerCase("pt-BR");
 const k=byId("kind").value, pr=byId("priority").value, pl=byId("platform").value;
 const bl=byId("blocker").value, gap=byId("gap").value, match=byId("match").value;
 const found=d.records.filter(r=>
  (!q||(r.request_id+" "+r.subject_id).toLocaleLowerCase("pt-BR").includes(q))
  &&(!k||r.kind===k)&&(!pr||r.priority===Number(pr))&&(!pl||r.platform===pl)
  &&(!bl||r.prerequisite_blocker_ids.includes(bl))
  &&(!gap||r.gap_types.includes(gap))&&(!match||r.correspondence===match));
 const tbody=byId("rows");tbody.replaceChildren();
 for(const r of found){
  const tr=el("tr",""),first=el("td",""),button=el("button",r.request_id);
  button.type="button";button.addEventListener("click",()=>detail(r));first.append(button);tr.append(first);
  for(const v of ["P"+r.priority,r.kind,r.platform,r.documentary_dependency_count,r.correspondence,"PENDING / BLOCKED"])
   tr.append(el("td",v));
  tbody.append(tr);
 }
 set("status",found.length+" de 88 pedidos — 88 lacunas abertas, 0 aprovações.");
}
function render(d){
 set("countRequests",d.counts.reconciled_requests);
 set("countGaps",d.counts.open_gaps);
 set("countLinks",d.counts.documentary_links);
 set("countAnonymous",d.counts.anonymous_unassigned);
 const opts=(id,values)=>{for(const val of values){const x=el("option",val);x.value=val;byId(id).append(x);}};
 opts("kind",[...new Set(d.records.map(r=>r.kind))]);
 opts("gap",[...new Set(d.records.flatMap(r=>r.gap_types))]);
 for(const id of ["search","kind","priority","platform","blocker","gap","match"])
  byId(id).addEventListener("input",()=>filter(d));
 byId("clear").addEventListener("click",()=>{
  for(const id of ["search","kind","priority","platform","blocker","gap","match"])byId(id).value="";
  filter(d);byId("search").focus();
 });
 set("commits",Object.entries(d.baseline_commits).map(([l,sha])=>l+": "+sha).join(" · "));
 filter(d);
}
async function main(){
 try{const r=await fetch("/data/sinnoh-l20-public-reconciliation.json",{cache:"no-store"});
  if(!r.ok)throw new Error("PUBLIC_L20_UNAVAILABLE");render(validate(await r.json()));}
 catch(_e){set("status","BLOQUEADO: integridade dos metadados públicos não confirmada.");
  byId("rows").replaceChildren();byId("details").textContent="Sem exibição de conteúdo não validado.";}
}
main();
