"use strict";
// Same-origin static public metadata viewer. No write, upload or execution.
const $=id=>document.getElementById(id);
const make=(tag,val,cls)=>{const x=document.createElement(tag);x.textContent=String(val);if(cls)x.className=cls;return x;};
function row(vals){const r=document.createElement("tr");for(const [v,c] of vals){const t=document.createElement("td");t.append(make("span",v,c));r.append(t);}return r;}
function validate(d){
 const c=d?.counts||{},p=d?.policy||{};
 if(d?.schema!==1||d.stage!=="L17"||d.region!=="SINNOH"||d.version!==1
 ||d.status!=="PUBLIC_REVIEWER_INDEX_ALL_UNREVIEWED_NO_NATIVE_QA"
 ||d.mode!=="PUBLIC_READ_ONLY_NO_EVIDENCE_INTAKE"
 ||!Array.isArray(d.records)||d.records.length!==88
 ||!Array.isArray(d.group_summary)||d.group_summary.length!==6
 ||!Array.isArray(d.platform_partition)||d.platform_partition.length!==2
 ||!Array.isArray(d.public_sources)||d.public_sources.length!==4
 ||!Array.isArray(d.review_guidance_templates)||d.review_guidance_templates.length!==6
 ||c.indexed_requests!==88||c.requests_pending!==88||c.requests_blocked!==88
 ||c.reviews_completed!==0||c.physical_signoffs!==0||c.exit_criteria_fulfilled!==0
 ||c.anonymous_slots_unassigned!==18||c.review_index_documentary_links!==1084
 ||c.windows_native_pending!==43||c.android_native_pending!==1
 ||c.local_reports!==0||c.human_approved!==0||c.native_completed!==0
 ||c.native_approved!==0||c.phase_bcd_completed!==0||c.phase_bcd_total!==13
 ||d.gates?.r07!=="PENDING"||d.gates?.r08!=="PENDING"||d.gates?.r09!=="PENDING"
 ||!["public_documentation_only","review_guidance_is_not_signoff",
  "independent_review_not_performed","no_evidence_intake","no_private_uploads",
  "no_assigned_reviewers","no_native_test_authority","priority_not_execution_order",
  "r09_global_only","android_not_windows_sandbox","anonymous_slots_have_no_identity",
  "links_not_physical_evidence","watch_unchanged_not_global_save_isolation",
  "rights_not_approved","mapids_not_reserved","no_game_exe","no_windows_sandbox",
  "no_joiplay","no_saves","no_private_files"].every(k=>p[k]===true)
 ||p.sinnoh_playable!==false
 ||new Set(d.records.map(x=>x.request_id)).size!==88
 ||d.records.some((x,i)=>x.order!==i+1||x.review_state!=="NOT_REVIEWED"
  ||x.status!=="PENDING"||x.readiness!=="BLOCKED"||x.exit_criteria_met!==false
  ||x.independent_signoff!==false||x.physical_evidence_accepted!==false
  ||x.native_qa_authorized!==false||x.assigned_reviewer!==false
  ||x.private_document_reference!==false||x.review_scope!=="PUBLIC_METADATA_ORIENTATION_ONLY"
  ||!x.reviewer_guidance||x.documentary_dependency_count!==x.documentary_dependency_request_ids.length)
 ||d.records.reduce((s,x)=>s+x.documentary_dependency_count,0)!==1084
 ||d.records.filter(x=>x.anonymous_bookkeeping_slot).length!==18
 ||d.records.some(x=>x.anonymous_bookkeeping_slot&&x.documentary_dependency_count!==0)
 ||d.records.some(x=>x.kind==="NATIVE_CASE"&&x.platform==="android"
  &&(x.prerequisite_blocker_ids.includes("B10")||x.prerequisite_blocker_ids.includes("B11")))
 ||d.global_r09?.case_ids.length!==0||d.global_r09?.documentary_dependency_request_ids.length!==0
 ||d.global_r09?.independent_review_complete!==false||d.global_r09?.approval!==false
 ||d.platform_partition[0].native_requests!==43||d.platform_partition[1].native_requests!==1
 ||d.platform_partition[0].requires_windows_b10_b11!==true
 ||d.platform_partition[1].requires_windows_b10_b11!==false
 ||d.platform_partition.some(x=>x.native_completed!==0||x.native_authorization!==false
    ||x.independent_review_complete!==false)
 ||!["L07","L08","L09","L10","L11","L12","L13","L14","L15","L16"]
   .every(k=>/^[0-9a-f]{40}$/.test(d.baseline_commits?.[k])))
 throw Error("Índice público sem integridade verificada");
 return d;
}
function detail(x){
 const chips=document.createElement("div");chips.className="chips";
 for(const id of x.exit_criteria_codes)chips.append(make("span",id));
 const refs=document.createElement("div");refs.className="chips";
 if(x.documentary_dependency_count===0)refs.append(make("span","Nenhum vínculo documental adicional"));
 else for(const id of x.documentary_dependency_request_ids)refs.append(make("span",id));
 $("detail").replaceChildren(
  make("h3",x.request_id),make("p",x.reviewer_guidance),
  make("p","P"+x.priority+" · "+x.kind+" · "+x.platform),
  make("p","Critérios de saída ainda pendentes:","pending"),chips,
  make("p","Vínculos documentais públicos: "+x.documentary_dependency_count,"meta"),refs,
  make("p","Nenhuma revisão independente, aprovação física ou execução nativa comprovada.","pending"));
 $("detalhes").scrollIntoView();
}
function filter(d){
 const q=$("search").value.trim().toLocaleLowerCase("pt-BR"),pr=$("priority").value,
  kind=$("kind").value,plat=$("platform").value,block=$("blocker").value,criterion=$("criterion").value;
 const found=d.records.filter(x=>
  (!q||(x.request_id+" "+x.subject_id+" "+x.reviewer_guidance).toLocaleLowerCase("pt-BR").includes(q))
  &&(!pr||x.priority===Number(pr))&&(!kind||x.kind===kind)&&(!plat||x.platform===plat)
  &&(!block||x.prerequisite_blocker_ids.includes(block))
  &&(!criterion||x.exit_criteria_codes.includes(criterion)));
 $("recordRows").replaceChildren(...found.map(x=>{
  const r=document.createElement("tr"),td=document.createElement("td");
  const btn=make("button",x.request_id);btn.type="button";btn.addEventListener("click",()=>detail(x));td.append(btn);r.append(td);
  for(const [v,c] of [["P"+x.priority,""],[x.kind+" · "+x.platform,""],
    [String(x.documentary_dependency_count),"meta"],["Não realizada","pending"],["PENDING/BLOCKED","pending"]]){
   const cell=document.createElement("td");cell.append(make("span",v,c));r.append(cell);
  }
  return r;
 }));
 $("status").textContent=found.length+" de 88 pedidos exibidos · 0 revisões concluídas.";
}
function render(d){
 const opt=(id,v)=>{const o=make("option",v);o.value=v;$(id).append(o);};
 [...new Set(d.records.map(x=>x.kind))].forEach(x=>opt("kind",x));
 [...new Set(d.records.flatMap(x=>x.exit_criteria_codes))].forEach(x=>opt("criterion",x));
 $("groupRows").replaceChildren(...d.group_summary.map(x=>row([
  [x.kind,""],[String(x.requests),""],[String(x.blocked),"pending"],
  [String(x.documentary_links),"meta"],[String(x.independent_reviews_completed),"pending"]])));
 $("platformRows").replaceChildren(...d.platform_partition.map(x=>row([
  [x.platform,""],[String(x.native_requests),""],[String(x.native_completed),"pending"],
  [x.requires_windows_b10_b11?"Pendente Windows":"Não se aplica",""],["Pendente","pending"]])));
 for(const id of ["search","priority","kind","platform","blocker","criterion"])
  $(id).addEventListener("input",()=>filter(d));
 $("reset").addEventListener("click",()=>{
  for(const id of ["search","priority","kind","platform","blocker","criterion"])$(id).value="";
  filter(d);$("search").focus();
 });
 for(const k of ["L07","L08","L09","L10","L11","L12","L13","L14","L15","L16"])
  $("sha"+k).textContent=d.baseline_commits[k];
 filter(d);
}
async function main(){
 try{
  const resp=await fetch("/data/sinnoh-l17-public-review-index.json",{cache:"no-store"});
  if(!resp.ok)throw Error("Fonte pública indisponível");
  render(validate(await resp.json()));
 }catch(_error){
  $("status").textContent="Bloqueado: integridade documental não confirmada.";
  $("recordRows").replaceChildren();$("groupRows").replaceChildren();$("platformRows").replaceChildren();
 }
}
main();