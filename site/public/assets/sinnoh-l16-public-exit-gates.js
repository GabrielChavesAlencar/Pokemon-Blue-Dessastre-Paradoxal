"use strict";
// GitHub public metadata read-only viewer. Never collect private evidence.
const $=id=>document.getElementById(id);
const node=(tag,value,cls)=>{const t=document.createElement(tag);t.textContent=String(value);if(cls)t.className=cls;return t;};
const tr=(values)=>{const row=document.createElement("tr");for(const [s,cls] of values){const td=document.createElement("td");td.append(node("span",s,cls));row.append(td);}return row;};
function validate(d){
 const c=d?.counts||{},p=d?.policy||{};
 if(d?.schema!==1||d.region!=="SINNOH"||d.stage!=="L16"||d.version!==1
 ||d.status!=="EXIT_CRITERIA_DOCUMENTED_ALL_PENDING_NO_NATIVE_AUTHORIZATION"
 ||d.mode!=="PUBLIC_READ_ONLY_EXIT_GATE_REGISTER"
 ||!Array.isArray(d.records)||d.records.length!==88
 ||!Array.isArray(d.group_summary)||d.group_summary.length!==6
 ||!Array.isArray(d.platform_partition)||d.platform_partition.length!==2
 ||!Array.isArray(d.public_sources)||d.public_sources.length!==3
 ||!Array.isArray(d.exit_code_templates)||d.exit_code_templates.length!==6
 ||c.exit_rows!==88||c.exit_blocked!==88||c.exit_ready!==0||c.exit_criteria_met!==0
 ||c.documentary_link_count!==1084||c.anonymous_unassigned!==18
 ||c.required_human_reviews_pending!==20||c.required_native_cases_pending!==44
 ||c.global_r09_pending!==1||c.physical_evidence_accepted!==0
 ||c.local_reports!==0||c.human_approved!==0||c.native_completed!==0
 ||c.native_approved!==0||c.phase_bcd_completed!==0||c.phase_bcd_total!==13
 ||d.gates?.r07!=="PENDING"||d.gates?.r08!=="PENDING"||d.gates?.r09!=="PENDING"
 ||!["public_documentary_metadata_only","criteria_are_future_requirements_not_signoffs",
  "priority_is_not_native_execution_order","links_do_not_authenticate_physical_evidence",
  "anonymous_slots_not_mapped","r09_is_global_not_case_scoped",
  "android_does_not_inherit_windows_b10_b11","watch_unchanged_not_global_save_isolation",
  "asset_rights_not_approved","mapids_not_reserved","no_private_inputs","no_uploads",
  "no_saves","no_game_exe","no_windows_sandbox","no_joiplay"].every(k=>p[k]===true)
 ||p.sinnoh_playable!==false||p.local_reports_received!==false
 ||p.human_criteria_approved!==false||p.native_cases_executed!==false
 ||new Set(d.records.map(x=>x.request_id)).size!==88
 ||d.records.some((x,i)=>x.order!==i+1||x.status!=="PENDING"||x.readiness!=="BLOCKED"
   ||x.exit_criteria_met!==false||x.physical_source_verified!==false
   ||x.human_review_completed!==false||x.physical_evidence_received!==false
   ||x.native_execution_approved!==false||x.action_authorization!=="NONE"
   ||!Array.isArray(x.exit_criteria_codes)||!x.exit_criteria_codes.length
   ||x.documentary_dependency_count!==x.documentary_dependency_request_ids.length)
 ||d.records.reduce((n,x)=>n+x.documentary_dependency_count,0)!==1084
 ||d.records.filter(x=>x.anonymous_bookkeeping_slot).length!==18
 ||d.records.some(x=>x.anonymous_bookkeeping_slot&&x.documentary_dependency_count!==0)
 ||d.records.some(x=>x.kind==="NATIVE_CASE"&&x.platform==="android"&&
   (x.prerequisite_blocker_ids.includes("B10")||x.prerequisite_blocker_ids.includes("B11")))
 ||d.global_r09?.id!=="R09"||d.global_r09.status!=="PENDING"
 ||d.global_r09.case_ids.length!==0||d.global_r09.documentary_dependency_request_ids.length!==0
 ||d.global_r09.exit_met!==false||d.global_r09.global_gate_only!==true||d.global_r09.approval!==false
 ||d.platform_partition[0].native_requests!==43||d.platform_partition[1].native_requests!==1
 ||d.platform_partition[0].requires_windows_b10_b11!==true
 ||d.platform_partition[1].requires_windows_b10_b11!==false
 ||d.platform_partition.some(x=>x.native_completed!==0||x.native_authorization!==false||x.exit_met!==0)
 ||!["L07","L08","L09","L10","L11","L12","L13","L14","L15"].every(k=>/^[0-9a-f]{40}$/.test(d.baseline_commits?.[k])))throw Error("Matriz L16 pública não validada");
 return d;
}
function show(x){
 const chips=document.createElement("div");chips.className="chips";
 for(const c of x.exit_criteria_codes)chips.append(node("span",c));
 const deps=document.createElement("div");deps.className="chips";
 if(!x.documentary_dependency_count)deps.append(node("span","Nenhum vínculo documental atribuído"));
 else for(const id of x.documentary_dependency_request_ids)deps.append(node("span",id));
 $("detail").replaceChildren(
  node("h3",x.request_id),node("p",x.criterion_description),
  node("p","P"+x.priority+" · "+x.kind+" · "+x.platform),
  node("p","Critérios ainda não atendidos:", "pending"),chips,
  node("p","Dependências entre IDs públicos: "+x.documentary_dependency_count,"documentary"),deps,
  node("p","Não há revisão física aprovada, evidência aceita ou autorização de executar QA nativa.","pending")
 );
 $("detalhes").scrollIntoView();
}
function filter(d){
 const q=$("search").value.trim().toLocaleLowerCase("pt-BR"),
  priority=$("priority").value,kind=$("kind").value,platform=$("platform").value,
  blocker=$("blocker").value,criterion=$("criterion").value;
 const rows=d.records.filter(x=>
  (!q||(x.request_id+" "+x.subject_id+" "+x.criterion_description).toLocaleLowerCase("pt-BR").includes(q))
  &&(!priority||x.priority===Number(priority))
  &&(!kind||x.kind===kind)&&(!platform||x.platform===platform)
  &&(!blocker||x.prerequisite_blocker_ids.includes(blocker))
  &&(!criterion||x.exit_criteria_codes.includes(criterion)));
 $("recordRows").replaceChildren(...rows.map(x=>{
  const r=document.createElement("tr"),td=document.createElement("td"),b=node("button",x.request_id);
  b.type="button";b.addEventListener("click",()=>show(x));td.append(b);r.append(td);
  for(const [s,cls] of [["P"+x.priority,""],[x.kind+" · "+x.platform,""],
   [String(x.exit_criteria_codes.length)+" pendentes","pending"],
   [String(x.documentary_dependency_count),"documentary"],["PENDING/BLOCKED","pending"]]){
   const cell=document.createElement("td");cell.append(node("span",s,cls));r.append(cell);
  }
  return r;
 }));
 $("status").textContent=rows.length+" de 88 pedidos · 0 critérios concluídos.";
}
function render(d){
 const kindNames=[...new Set(d.records.map(x=>x.kind))];
 for(const k of kindNames){const opt=node("option",k);opt.value=k;$("kind").append(opt);}
 const codes=[...new Set(d.records.flatMap(x=>x.exit_criteria_codes))];
 for(const c of codes){const opt=node("option",c);opt.value=c;$("criterion").append(opt);}
 $("groupRows").replaceChildren(...d.group_summary.map(x=>tr([
  [x.kind,""],[String(x.requests),""],[String(x.blocked),"pending"],
  [String(x.criteria_met),"pending"],[String(x.documentary_links),"documentary"]
 ])));
 $("platformRows").replaceChildren(...d.platform_partition.map(x=>tr([
  [x.platform,""],[String(x.native_requests),""],[String(x.native_completed),"pending"],
  [x.requires_windows_b10_b11?"Pendente Windows":"Não se aplica ao Android",""],["Não autorizada","pending"]
 ])));
 for(const id of ["search","priority","kind","platform","blocker","criterion"])
  $(id).addEventListener("input",()=>filter(d));
 $("reset").addEventListener("click",()=>{
  for(const id of ["search","priority","kind","platform","blocker","criterion"])$(id).value="";
  filter(d);$("search").focus();
 });
 for(const k of ["L07","L08","L09","L10","L11","L12","L13","L14","L15"])
  $("sha"+k).textContent=d.baseline_commits[k];
 filter(d);
}
async function main(){
 try{
  const response=await fetch("/data/sinnoh-l16-public-exit-gates.json",{cache:"no-store"});
  if(!response.ok)throw Error("Fonte pública indisponível");
  render(validate(await response.json()));
 }catch(_error){
  $("status").textContent="Bloqueado: integridade dos critérios públicos não confirmada.";
  $("recordRows").replaceChildren();$("groupRows").replaceChildren();$("platformRows").replaceChildren();
 }
}
main();