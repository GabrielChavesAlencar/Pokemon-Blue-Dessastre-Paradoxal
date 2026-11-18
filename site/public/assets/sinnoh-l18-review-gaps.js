"use strict";
// L18: same-origin static JSON only. No uploads, writes, native actions or private input.
const $=id=>document.getElementById(id);
const make=(tag,val,cls)=>{const e=document.createElement(tag);e.textContent=String(val);if(cls)e.className=cls;return e;};
function tableRow(fields){const r=document.createElement("tr");for(const [v,c] of fields){const t=document.createElement("td");t.append(make("span",v,c));r.append(t);}return r;}
function check(d){
 const c=d?.counts||{},p=d?.policy||{};
 if(d?.schema!==1||d.stage!=="L18"||d.region!=="SINNOH"||d.version!==1
 ||d.mode!=="PUBLIC_READ_ONLY_DOCUMENTARY_HANDOFF"
 ||d.status!=="PUBLIC_REVIEW_GAPS_DOCUMENTED_ALL_OPEN_NO_NATIVE_QA"
 ||!Array.isArray(d.records)||d.records.length!==88
 ||!Array.isArray(d.group_summary)||d.group_summary.length!==6
 ||!Array.isArray(d.platform_partition)||d.platform_partition.length!==2
 ||!Array.isArray(d.public_sources)||d.public_sources.length!==5
 ||!Array.isArray(d.gap_templates)||d.gap_templates.length!==6
 ||c.gaps_total_requests!==88||c.review_gaps_open!==88||c.review_gaps_closed!==0
 ||c.documentary_next_steps!==88||c.independent_reviews_completed!==0
 ||c.exit_criteria_met!==0||c.physical_evidence_accepted!==0
 ||c.links_preserved!==1084||c.unassigned_anonymous_slots!==18
 ||c.local_reports!==0||c.human_approved!==0||c.native_completed!==0
 ||c.native_approved!==0||c.phase_bcd_completed!==0||c.phase_bcd_total!==13
 ||d.gates?.r07!=="PENDING"||d.gates?.r08!=="PENDING"||d.gates?.r09!=="PENDING"
 ||!["public_documentary_only","gaps_are_not_human_signoffs","next_steps_are_not_native_instructions",
 "no_new_case_links_to_r09","priorities_are_documentary_only","anonymous_slots_unassigned",
 "android_separate_from_windows_b10_b11","no_physical_evidence_inferred",
 "no_uploads","no_private_evidence_intake","no_reviewer_identification",
 "no_native_execution","no_game_exe","no_windows_sandbox","no_joiplay","no_saves",
 "no_private_files","watch_unchanged_not_global_save_isolation","asset_rights_not_approved",
 "mapids_not_reserved"].every(k=>p[k]===true)||p.sinnoh_playable!==false
 ||new Set(d.records.map(x=>x.request_id)).size!==88
 ||d.records.some((x,i)=>x.order!==i+1||x.status!=="PENDING"
   ||x.readiness!=="BLOCKED"||x.review_state!=="NOT_REVIEWED"
   ||x.review_gap_status!=="OPEN_DOCUMENTARY_ONLY"
   ||x.next_step_scope!=="READ_ONLY_PUBLIC_DOCUMENTATION"||!x.next_documentary_step
   ||!Array.isArray(x.gap_types)||!x.gap_types.length||x.human_signoff!==false
   ||x.native_qa_executed!==false||x.native_qa_approved!==false
   ||x.local_report_received!==false||x.assigned_reviewer!==false
   ||x.source_authenticated!==false
   ||x.documentary_dependency_count!==x.documentary_dependency_request_ids.length)
 ||d.records.reduce((s,x)=>s+x.documentary_dependency_count,0)!==1084
 ||d.records.filter(x=>x.anonymous_bookkeeping_slot).length!==18
 ||d.records.some(x=>x.anonymous_bookkeeping_slot&&x.documentary_dependency_count!==0)
 ||d.records.some(x=>x.kind==="NATIVE_CASE"&&x.platform==="android"
   &&(x.prerequisite_blocker_ids.includes("B10")||x.prerequisite_blocker_ids.includes("B11")))
 ||d.global_r09?.case_ids.length!==0||d.global_r09?.documentary_dependency_request_ids.length!==0
 ||d.global_r09?.gaps_open!==1||d.global_r09?.review_completed!==false
 ||d.platform_partition[0].native_requests!==43||d.platform_partition[1].native_requests!==1
 ||d.platform_partition[0].requires_windows_b10_b11!==true
 ||d.platform_partition[1].requires_windows_b10_b11!==false
 ||d.platform_partition.some(x=>x.native_completed!==0||x.native_authorization!==false
   ||x.review_completed!==false)
 ||!["L07","L08","L09","L10","L11","L12","L13","L14","L15","L16","L17"]
 .every(k=>/^[0-9a-f]{40}$/.test(d.baseline_commits?.[k])))throw Error("Relatório público não verificado");
 return d;
}
function detail(x){
 const chips=document.createElement("div");chips.className="chips";
 for(const gap of x.gap_types)chips.append(make("span",gap));
 const refs=document.createElement("div");refs.className="chips";
 if(!x.documentary_dependency_count)refs.append(make("span","Nenhuma dependência nova atribuída"));
 else for(const id of x.documentary_dependency_request_ids)refs.append(make("span",id));
 $("detail").replaceChildren(
 make("h3",x.request_id),make("p","P"+x.priority+" · "+x.kind+" · "+x.platform),
 make("p","Lacunas ainda abertas:","pending"),chips,
 make("p","Próximo passo permitido: "+x.next_documentary_step,"meta"),
 make("p","Vínculos documentais públicos: "+x.documentary_dependency_count),refs,
 make("p","PENDING/BLOCKED: nenhuma revisão física, signoff ou QA nativa autorizada.","pending"));
 $("detalhes").scrollIntoView();
}
function filter(d){
 const q=$("search").value.trim().toLocaleLowerCase("pt-BR"),p=$("priority").value,
 k=$("kind").value,plat=$("platform").value,b=$("blocker").value,g=$("gap").value;
 const rows=d.records.filter(x=>(!q||(x.request_id+" "+x.subject_id+" "+x.next_documentary_step).toLocaleLowerCase("pt-BR").includes(q))
 &&(!p||x.priority===Number(p))&&(!k||x.kind===k)&&(!plat||x.platform===plat)
 &&(!b||x.prerequisite_blocker_ids.includes(b))&&(!g||x.gap_types.includes(g)));
 $("recordRows").replaceChildren(...rows.map(x=>{
  const row=document.createElement("tr"),cell=document.createElement("td"),btn=make("button",x.request_id);
  btn.type="button";btn.addEventListener("click",()=>detail(x));cell.append(btn);row.append(cell);
  for(const [v,c] of [["P"+x.priority,""],[x.kind+" · "+x.platform,""],
   [String(x.gap_types.length)+" abertas","pending"],
   [String(x.documentary_dependency_count),"meta"],["PENDING/BLOCKED","pending"]]){
   const t=document.createElement("td");t.append(make("span",v,c));row.append(t);
  }
  return row;
 }));
 $("status").textContent=rows.length+" de 88 pedidos · 0 revisões concluídas.";
}
function render(d){
 const option=(id,v)=>{const o=make("option",v);o.value=v;$(id).append(o);};
 [...new Set(d.records.map(x=>x.kind))].forEach(x=>option("kind",x));
 [...new Set(d.records.flatMap(x=>x.gap_types))].forEach(x=>option("gap",x));
 $("groupRows").replaceChildren(...d.group_summary.map(x=>tableRow([
 [x.kind,""],[String(x.requests),""],[String(x.blocked),"pending"],
 [String(x.documentary_links),"meta"],[String(x.reviewed),"pending"]])));
 $("platformRows").replaceChildren(...d.platform_partition.map(x=>tableRow([
 [x.platform,""],[String(x.native_requests),""],[String(x.native_completed),"pending"],
 [x.requires_windows_b10_b11?"Pendente Windows":"Não se aplica",""],["Não autorizada","pending"]])));
 for(const id of ["search","priority","kind","platform","blocker","gap"])$(id).addEventListener("input",()=>filter(d));
 $("reset").addEventListener("click",()=>{for(const id of ["search","priority","kind","platform","blocker","gap"])$(id).value="";filter(d);$("search").focus();});
 for(const k of ["L07","L08","L09","L10","L11","L12","L13","L14","L15","L16","L17"])
 $("sha"+k).textContent=d.baseline_commits[k];
 filter(d);
}
async function main(){
 try{
  const resp=await fetch("/data/sinnoh-l18-public-review-gaps.json",{cache:"no-store"});
  if(!resp.ok)throw Error("Relatório público indisponível");
  render(check(await resp.json()));
 }catch(_error){
  $("status").textContent="Bloqueado: integridade do relatório documental não confirmada.";
  $("recordRows").replaceChildren();$("groupRows").replaceChildren();$("platformRows").replaceChildren();
 }
}
main();