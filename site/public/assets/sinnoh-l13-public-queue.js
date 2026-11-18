"use strict";
// L13 public same-origin viewer ONLY. No uploads, edits or execution actions.
const $=id=>document.getElementById(id);
const txt=(type,value,cls)=>{
 const x=document.createElement(type);x.textContent=String(value);
 if(cls)x.className=cls;return x;
};
function tableRow(values){
 const row=document.createElement("tr");
 for(const [value,cls] of values){
   const td=document.createElement("td");td.append(txt("span",value,cls));row.append(td);
 }
 return row;
}
function validate(d){
 const c=d?.counts||{}, g=d?.gates||{}, s=d?.disclaimer||{};
 const kinds=["BLOCKER_DEPENDENCY","GLOBAL_REGIONAL_GATE","LOCAL_REPORT_SLOT","HUMAN_CRITERION","BCD_PENDING_SLOT","NATIVE_CASE"];
 const counts=[5,1,5,20,13,44];
 if(d?.schema!==1||d.region!=="SINNOH"||d.stage!=="L13"
   ||d.status!=="PUBLIC_REQUEST_QUEUE_PENDING_NO_PHYSICAL_EVIDENCE"
   ||d.mode!=="PUBLIC_READ_ONLY_NO_UPLOAD_NO_QA"
   ||!Array.isArray(d.queue)||d.queue.length!==88
   ||!Array.isArray(d.priority_rules)||d.priority_rules.length!==5
   ||!Array.isArray(d.platform_queues)||d.platform_queues.length!==2
   ||!Array.isArray(d.coverage_layers)||d.coverage_layers.length!==6
   ||c.evidence_requests_total!==88||c.requests_pending!==88||c.requests_approved!==0
   ||c.blocker_requests!==5||c.global_gate_requests!==1||c.report_slots!==5
   ||c.human_criterion_requests!==20||c.bcd_slots!==13||c.native_case_requests!==44
   ||c.cases_total!==44||c.criteria_total!==20||c.windows!==43||c.android!==1
   ||c.local_reports!==0||c.human_approved!==0||c.native_completed!==0||c.native_approved!==0
   ||c.phase_bcd_completed!==0||c.phase_bcd_total!==13
   ||c.public_edges_verified!==1084||c.documentary_links_missing!==0
   ||g.r07!=="PENDING"||g.r08!=="PENDING"||g.r09!=="PENDING"
   ||s.public_documentary_only!==true||s.no_reports_received!==true
   ||s.no_upload_or_attachments!==true||s.no_local_paths_or_saves!==true
   ||s.no_game_execution!==true||s.no_windows_sandbox_execution!==true
   ||s.no_joiplay_execution!==true||s.watch_unchanged_is_not_global_save_isolation!==true
   ||s.mapids_not_reserved!==true||s.asset_rights_not_approved!==true
   ||s.android_local_l05_not_completed!==true||s.sinnoh_playable!==false
   ||new Set(d.queue.map(x=>x.request_id)).size!==88
   ||d.queue.some((x,i)=>x.order!==i+1||x.status!=="PENDING"
      ||x.accepted_evidence!==false||x.human_approved!==false
      ||x.native_qa_authorized!==false||x.read_only!==true
      ||x.request_mode!=="SANITIZED_PUBLIC_STATUS_ONLY"
      ||!Array.isArray(x.case_ids)||!Array.isArray(x.criterion_ids)||!Array.isArray(x.blocker_ids))
   ||d.queue.some((x,i)=>i>0&&x.priority<d.queue[i-1].priority)
   ||kinds.some((kind,i)=>d.queue.filter(x=>x.kind===kind).length!==counts[i])
   ||d.queue.filter(x=>x.kind==="NATIVE_CASE"&&x.platform==="windows").length!==43
   ||d.queue.filter(x=>x.kind==="NATIVE_CASE"&&x.platform==="android").length!==1
   ||d.queue.filter(x=>x.kind==="NATIVE_CASE"&&x.platform==="android").some(x=>x.blocker_ids.includes("B10")||x.blocker_ids.includes("B11"))
   ||d.queue.filter(x=>x.kind==="LOCAL_REPORT_SLOT"||x.kind==="BCD_PENDING_SLOT").some(x=>x.placeholder_not_a_real_artifact!==true)
   ||d.global_r09?.id!=="R09"||d.global_r09.status!=="PENDING"
   ||d.global_r09.approved!==false||d.global_r09.not_case_scoped!==true||d.global_r09.case_ids.length!==0
   ||d.queue.find(x=>x.kind==="GLOBAL_REGIONAL_GATE")?.case_ids.length!==0
   ||d.platform_queues[0]?.native_requests!==43||d.platform_queues[1]?.native_requests!==1
   ||d.platform_queues[0].requires_windows_sandbox_b10_b11!==true
   ||d.platform_queues[1].requires_windows_sandbox_b10_b11!==false
   ||d.platform_queues.some(x=>x.native_completed!==0||x.authorization!==false)
   ||!["L07","L08","L09","L10","L11","L12"].every(k=>/^[a-f0-9]{40}$/.test(d.baseline_commits?.[k]))) {
   throw new Error("Fila pública inválida ou não verificada");
 }
 return d;
}
function filter(d){
 const q=$("search").value.trim().toLocaleLowerCase("pt-BR");
 const pr=$("priority").value,kind=$("kind").value,platform=$("platform").value,
 block=$("blocker").value,criterion=$("criterion").value;
 const items=d.queue.filter(x=>
  (!q||(x.request_id+" "+x.subject_id+" "+x.reason).toLocaleLowerCase("pt-BR").includes(q))
  &&(!pr||x.priority===Number(pr))&&(!kind||x.kind===kind)
  &&(!platform||x.platform===platform)
  &&(!block||x.blocker_ids.includes(block))
  &&(!criterion||x.criterion_ids.includes(criterion)));
 $("queueRows").replaceChildren(...items.map(x=>tableRow([
  [String(x.order),""],[x.request_id,""],[x.priority_label+" / "+x.kind,""],
  [x.platform,""],[x.case_ids.length+" casos · "+x.criterion_ids.length+" critérios",""],
  ["Pendente, sem evidência","pending"]
 ])));
 $("status").textContent=items.length+" de 88 pedidos exibidos · 0 aprovados / 0 arquivos recebidos.";
}
function render(d){
 const add=(id,value)=>{const n=txt("option",value);n.value=value;$(id).append(n);};
 [...new Set(d.queue.map(x=>x.kind))].forEach(x=>add("kind",x));
 ["B09","B10","B11","R07","R08","R09"].forEach(x=>add("blocker",x));
 d.queue.filter(x=>x.kind==="HUMAN_CRITERION").forEach(x=>add("criterion",x.subject_id));
 $("platformRows").replaceChildren(...d.platform_queues.map(x=>tableRow([
  [x.platform,""],[String(x.native_requests),""],[String(x.native_completed),"pending"],
  [x.requires_windows_sandbox_b10_b11?"Pendente Windows":"Não se aplica ao Android",""],
  ["Não autorizado","pending"]
 ])));
 for(const id of ["search","priority","kind","platform","blocker","criterion"])$(id).addEventListener("input",()=>filter(d));
 $("reset").addEventListener("click",()=>{
   for(const id of ["search","priority","kind","platform","blocker","criterion"])$(id).value="";
   filter(d);$("search").focus();
 });
 for(const k of ["L07","L08","L09","L10","L11","L12"])$("sha"+k).textContent=d.baseline_commits[k];
 filter(d);
}
async function main(){
 try{
  const response=await fetch("/data/sinnoh-l13-public-evidence-queue.json",{cache:"no-store"});
  if(!response.ok)throw Error("Ausência de fonte pública");
  render(validate(await response.json()));
 }catch(_error){
  $("status").textContent="Bloqueado: integridade da fila pública não confirmada.";
  $("queueRows").replaceChildren();$("platformRows").replaceChildren();
 }
}
main();