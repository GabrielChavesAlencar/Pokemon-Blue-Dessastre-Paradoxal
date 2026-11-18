"use strict";
// Static same-origin public JSON; never submit, upload, persist or execute.
const $=id=>document.getElementById(id);
const node=(tag,v,cls)=>{const n=document.createElement(tag);n.textContent=String(v);if(cls)n.className=cls;return n;};
const row=fields=>{const r=document.createElement("tr");for(const [v,cls] of fields){const c=document.createElement("td");c.append(node("span",v,cls));r.append(c);}return r;};
function validate(d){
 const c=d?.counts||{},p=d?.policy||{};
 if(d?.schema!==1||d.stage!=="L19"||d.region!=="SINNOH"||d.version!==1
 ||d.status!=="PUBLIC_GAP_CONSOLIDATION_VALID_METADATA_ALL_BLOCKED"
 ||d.mode!=="READ_ONLY_PUBLIC_GIT_DOCUMENTS_NO_NATIVE_QA"
 ||!Array.isArray(d.records)||d.records.length!==88
 ||!Array.isArray(d.kind_summary)||d.kind_summary.length!==6
 ||!Array.isArray(d.platform_partition)||d.platform_partition.length!==2
 ||!Array.isArray(d.public_sources)||d.public_sources.length!==6
 ||c.consolidated_requests!==88||c.consolidated_pending!==88
 ||c.consolidated_blocked!==88||c.consolidated_gaps_open!==88
 ||c.consolidated_gaps_closed!==0||c.consolidated_links!==1084
 ||c.consolidated_anonymous_slots!==18||c.consolidated_human_signoffs!==0
 ||c.consolidated_native_passes!==0||c.consolidated_exit_criteria_met!==0
 ||c.consolidated_physical_evidence_accepted!==0
 ||c.local_reports!==0||c.human_approved!==0||c.native_completed!==0
 ||c.native_approved!==0||c.phase_bcd_completed!==0||c.phase_bcd_total!==13
 ||d.edge_summary?.total!==1084||d.edge_summary.case_to_criterion!==846
 ||d.edge_summary.case_to_blocker!==218||d.edge_summary.criterion_to_blocker!==20
 ||d.gates?.r07!=="PENDING"||d.gates?.r08!=="PENDING"||d.gates?.r09!=="PENDING"
 ||!["document_only","comparison_does_not_approve_native_qa","priorities_P0_P4_are_documentary_only",
 "public_links_are_not_physical_evidence","r09_global_only_no_case_edges","no_private_uploads",
 "no_private_reviewer_identity","anonymous_slots_unassigned","android_does_not_inherit_windows_b10_b11",
 "B11_watch_unchanged_is_not_global_save_isolation","R07_mapids_not_authorized",
 "R08_asset_rights_not_approved","no_game_exe","no_windows_sandbox","no_joiplay",
 "no_saves","no_private_files"].every(k=>p[k]===true)||p.sinnoh_playable!==false
 ||new Set(d.records.map(x=>x.request_id)).size!==88
 ||d.records.some((x,i)=>x.order!==i+1||x.status!=="PENDING"||x.readiness!=="BLOCKED"
 ||x.review_gap_status!=="OPEN_DOCUMENTARY_ONLY"||x.review_state!=="NOT_REVIEWED"
 ||x.independent_review_approved!==false||x.exit_criteria_met!==false
 ||x.native_qa_executed!==false||x.physical_evidence_accepted!==false
 ||x.assigned_reviewer!==false||x.anonymous_identity_assigned!==false
 ||x.public_coverage!=="LINKS_DOCUMENTED_NOT_PHYSICAL_EVIDENCE"
 ||x.documentary_dependency_count!==x.documentary_dependency_request_ids.length)
 ||d.records.reduce((n,x)=>n+x.documentary_dependency_count,0)!==1084
 ||d.records.filter(x=>x.anonymous_bookkeeping_slot).length!==18
 ||d.records.some(x=>x.anonymous_bookkeeping_slot&&x.documentary_dependency_count!==0)
 ||d.records.some(x=>x.kind==="NATIVE_CASE"&&x.platform==="android"
    &&(x.prerequisite_blocker_ids.includes("B10")||x.prerequisite_blocker_ids.includes("B11")))
 ||d.global_r09?.case_ids.length!==0||d.global_r09?.documentary_dependency_request_ids.length!==0
 ||d.global_r09?.signoff!==false||d.global_r09?.review_complete!==false
 ||d.platform_partition[0].native_requests!==43||d.platform_partition[1].native_requests!==1
 ||d.platform_partition[0].requires_windows_b10_b11!==true
 ||d.platform_partition[1].requires_windows_b10_b11!==false
 ||d.platform_partition.some(x=>x.native_completed!==0||x.native_authorization!==false||x.review_complete!==false)
 ||!["L07","L08","L09","L10","L11","L12","L13","L14","L15","L16","L17","L18"]
    .every(k=>/^[0-9a-f]{40}$/.test(d.baseline_commits?.[k])))throw Error("Public L19 metadata not verified");
 return d;
}
function show(x){
 const gaps=document.createElement("div");gaps.className="chips";
 for(const g of x.gap_types)gaps.append(node("span",g));
 const deps=document.createElement("div");deps.className="chips";
 if(!x.documentary_dependency_count)deps.append(node("span","Nenhum novo vínculo para o slot"));
 else for(const id of x.documentary_dependency_request_ids)deps.append(node("span",id));
 $("detail").replaceChildren(node("h3",x.request_id),node("p","P"+x.priority+" · "+x.kind+" · "+x.platform),
  node("p","Lacunas não atendidas:","pending"),gaps,
  node("p","Próximo passo permitido: "+x.next_documentary_step,"meta"),
  node("p","Vínculos públicos: "+x.documentary_dependency_count),deps,
  node("p","Nenhuma revisão humana, autorização ou QA nativa foi efetuada.","pending"));
 $("detalhes").scrollIntoView();
}
function filter(d){
 const q=$("search").value.trim().toLocaleLowerCase("pt-BR"),p=$("priority").value,
 k=$("kind").value,pl=$("platform").value,bl=$("blocker").value,g=$("gap").value;
 const found=d.records.filter(x=>(!q||(x.request_id+" "+x.subject_id+" "+x.next_documentary_step).toLocaleLowerCase("pt-BR").includes(q))
 &&(!p||x.priority===Number(p))&&(!k||x.kind===k)&&(!pl||x.platform===pl)
 &&(!bl||x.prerequisite_blocker_ids.includes(bl))&&(!g||x.gap_types.includes(g)));
 $("recordRows").replaceChildren(...found.map(x=>{
  const tr=document.createElement("tr"),cell=document.createElement("td"),btn=node("button",x.request_id);
  btn.type="button";btn.addEventListener("click",()=>show(x));cell.append(btn);tr.append(cell);
  for(const [v,cls] of [["P"+x.priority,""],[x.kind+" · "+x.platform,""],
   [String(x.gap_types.length)+" abertas","pending"],[String(x.documentary_dependency_count),"meta"],
   ["PENDING/BLOCKED","pending"]]){const c=document.createElement("td");c.append(node("span",v,cls));tr.append(c);}
  return tr;
 }));
 $("status").textContent=found.length+" de 88 pedidos — 0 revisões independentes.";
}
function render(d){
 const addOption=(id,v)=>{const o=node("option",v);o.value=v;$(id).append(o);};
 [...new Set(d.records.map(x=>x.kind))].forEach(x=>addOption("kind",x));
 [...new Set(d.records.flatMap(x=>x.gap_types))].forEach(x=>addOption("gap",x));
 $("groupRows").replaceChildren(...d.kind_summary.map(x=>row([[x.kind,""],[String(x.requests),""],
 [String(x.blocked),"pending"],[String(x.documentary_edges),"meta"],[String(x.independent_signoffs),"pending"]])));
 $("platformRows").replaceChildren(...d.platform_partition.map(x=>row([[x.platform,""],[String(x.native_requests),""],
 [String(x.native_completed),"pending"],[x.requires_windows_b10_b11?"Pendente Windows":"Não aplicável",""],
 ["Não autorizada","pending"]])));
 for(const id of ["search","priority","kind","platform","blocker","gap"])$(id).addEventListener("input",()=>filter(d));
 $("reset").addEventListener("click",()=>{for(const id of ["search","priority","kind","platform","blocker","gap"])$(id).value="";filter(d);$("search").focus();});
 for(const phase of ["L07","L08","L09","L10","L11","L12","L13","L14","L15","L16","L17","L18"])$("sha"+phase).textContent=d.baseline_commits[phase];
 filter(d);
}
async function main(){
 try{const r=await fetch("/data/sinnoh-l19-public-gap-consolidation.json",{cache:"no-store"});
 if(!r.ok)throw Error("Public report unavailable");render(validate(await r.json()));}
 catch(_e){$("status").textContent="Bloqueado: integridade do relatório público não confirmada.";
 $("recordRows").replaceChildren();$("groupRows").replaceChildren();$("platformRows").replaceChildren();}
}
main();