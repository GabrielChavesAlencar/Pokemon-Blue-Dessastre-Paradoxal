"use strict";
// Static public report viewer. No upload, write, file read or native actions.
const $=id=>document.getElementById(id);
const text=(tag,val,cls)=>{const n=document.createElement(tag);n.textContent=String(val);if(cls)n.className=cls;return n;};
function tablerow(vals){
 const tr=document.createElement("tr");
 for(const [value,cls] of vals){const td=document.createElement("td");td.append(text("span",value,cls));tr.append(td);}
 return tr;
}
function verify(d){
 const c=d?.counts||{},p=d?.policy||{};
 if(d?.schema!==1||d.stage!=="L15"||d.region!=="SINNOH"
 ||d.mode!=="PUBLIC_READ_ONLY_ZERO_PHYSICAL_APPROVAL"
 ||d.status!=="PUBLIC_DOC_CONSISTENT_L14_PROJECTION_ONLY_ALL_BLOCKED"
 ||!Array.isArray(d.records)||d.records.length!==88
 ||!Array.isArray(d.change_categories)||d.change_categories.length!==4
 ||!Array.isArray(d.group_summary)||d.group_summary.length!==6
 ||!Array.isArray(d.platform_partition)||d.platform_partition.length!==2
 ||c.reported_comparisons!==88||c.source_records_matched!==88
 ||c.source_records_added!==0||c.source_records_removed!==0||c.source_records_reordered!==0
 ||c.id_drift_count!==0||c.priority_drift_count!==0||c.platform_drift_count!==0||c.status_drift_count!==0
 ||c.physical_approval_change_count!==0||c.actual_evidence_received!==0
 ||c.l14_documentary_projection_links!==1084||c.l14_metadata_projection_added!==1084
 ||c.l13_direct_dependency_request_links!==0
 ||c.rows_blocked!==88||c.rows_pending!==88||c.rows_ready!==0
 ||c.anonymous_rows_unassigned!==18
 ||c.local_reports!==0||c.human_approved!==0||c.native_completed!==0||c.native_approved!==0
 ||c.phase_bcd_completed!==0||c.phase_bcd_total!==13
 ||d.gates?.r07!=="PENDING"||d.gates?.r08!=="PENDING"||d.gates?.r09!=="PENDING"
 ||p.comparisons_are_public_json_only!==true
 ||p.new_links_are_l14_projection_only!==true
 ||p.zero_documentary_drift_does_not_mean_physical_approval!==true
 ||p.p0_p4_not_native_execution_order!==true
 ||p.no_private_evidence_intake!==true||p.no_uploads!==true
 ||p.no_game_exe!==true||p.no_joiplay!==true||p.no_windows_sandbox!==true
 ||p.watch_unchanged_not_global_save_isolation!==true||p.mapids_not_reserved!==true
 ||p.asset_rights_not_approved!==true||p.sinnoh_playable!==false
 ||new Set(d.records.map(r=>r.request_id)).size!==88
 ||d.records.some((r,i)=>r.order!==i+1||r.readiness!=="BLOCKED"
  ||r.source_l13_status!=="PENDING"||r.source_l14_status!=="PENDING"
  ||r.comparison_status!=="CONSISTENT_DOCUMENTARY_METADATA"
  ||r.human_approved!==false||r.native_qa_authorized!==false||r.accepted_evidence!==false
  ||r.private_file_received!==false
  ||r.l14_documentary_dependency_count!==r.l14_documentary_projection_added)
 ||d.records.reduce((n,r)=>n+r.l14_documentary_dependency_count,0)!==1084
 ||d.records.filter(r=>r.anonymous_bookkeeping_slot).length!==18
 ||d.records.some(r=>r.anonymous_bookkeeping_slot&&r.l14_documentary_dependency_count!==0)
 ||d.change_categories[2].added!==1084
 ||d.change_categories[2].state!=="ADDED_DOCUMENTARY_PROJECTION_NOT_NATIVE_EVIDENCE"
 ||d.change_categories[3].observed!==0
 ||d.global_r09?.status!=="PENDING"||d.global_r09?.case_ids.length!==0
 ||d.global_r09?.documentary_dependency_request_ids.length!==0
 ||d.global_r09?.approved!==false||d.global_r09?.global_gate_only!==true
 ||d.platform_partition[0].native_requests!==43||d.platform_partition[1].native_requests!==1
 ||d.platform_partition[0].requires_windows_b10_b11!==true
 ||d.platform_partition[1].requires_windows_b10_b11!==false
 ||d.platform_partition.some(x=>x.native_completed!==0||x.authorization!==false||x.state!=="PENDING_BLOCKED")
 ||!["L07","L08","L09","L10","L11","L12","L13","L14"].every(k=>/^[0-9a-f]{40}$/.test(d.baseline_commits?.[k])))
   throw Error("Relatório documental não íntegro");
 return d;
}
function detail(r){
 const wrap=$("detail");
 wrap.replaceChildren(
  text("h3",r.request_id),text("p","P"+r.priority+" · "+r.kind+" · "+r.platform),
  text("p","L13: "+r.source_l13_status+" → L14: "+r.source_l14_status+" / "+r.readiness),
  text("p","Bloqueios L13: "+r.l13_blockers_count+" · Critérios L13: "+r.l13_criteria_count),
  text("p","Vínculos da projeção documental L14: "+r.l14_documentary_projection_added,"document"),
  text("p","Nenhuma prova física recebida. Nenhuma revisão humana ou teste nativo autorizado.","pending")
 );
 $("detalhes").scrollIntoView();
}
function filter(d){
 const q=$("search").value.trim().toLocaleLowerCase("pt-BR"),prio=$("priority").value,
  kind=$("kind").value,plat=$("platform").value,links=$("links").value,drift=$("drift").value;
 const items=d.records.filter(r=>(!q||(r.request_id+" "+r.subject_id).toLocaleLowerCase("pt-BR").includes(q))
   &&(!prio||r.priority===Number(prio))&&(!kind||r.kind===kind)
   &&(!plat||r.platform===plat)
   &&(!links||(links==="yes"?r.l14_documentary_dependency_count>0:r.l14_documentary_dependency_count===0))
   &&(!drift||(drift==="consistent"&&r.comparison_status==="CONSISTENT_DOCUMENTARY_METADATA")));
 $("recordRows").replaceChildren(...items.map(r=>{
  const row=document.createElement("tr"),td=document.createElement("td");
  const btn=text("button",r.request_id);btn.type="button";
  btn.addEventListener("click",()=>detail(r));
  td.append(btn);row.append(td);
  for(const [v,s] of [["P"+r.priority,""],[r.kind+" · "+r.platform,""],
   [String(r.l14_documentary_projection_added),"document"],
   ["PENDING → BLOCKED","pending"],["Ausente","pending"]]){
    const t=document.createElement("td");t.append(text("span",v,s));row.append(t);
  }
  return row;
 }));
 $("status").textContent=items.length+" de 88 pedidos · nenhuma aprovação física.";
}
function render(d){
 const add=(id,val)=>{const op=text("option",val);op.value=val;$(id).append(op);};
 [...new Set(d.records.map(r=>r.kind))].forEach(x=>add("kind",x));
 $("changesRows").replaceChildren(...d.change_categories.map(c=>tablerow([
   [c.id,""],[String(c.baseline),""],[String(c.observed),""],[String(c.added),"document"],
   [String(c.drift),""],[c.state,""]
 ])));
 $("groupRows").replaceChildren(...d.group_summary.map(g=>tablerow([
  [g.kind,""],[String(g.requests),""],[String(g.blocked),"pending"],
  [String(g.documentary_dependency_links),"document"],[String(g.actual_evidence_received),"pending"]
 ])));
 $("platformRows").replaceChildren(...d.platform_partition.map(p=>tablerow([
  [p.platform,""],[String(p.native_requests),""],[String(p.native_completed),"pending"],
  [p.requires_windows_b10_b11?"Pendente Windows":"Não se aplica",""],[p.state,"pending"]
 ])));
 for(const id of ["search","priority","kind","platform","links","drift"])
  $(id).addEventListener("input",()=>filter(d));
 $("reset").addEventListener("click",()=>{
   for(const id of ["search","priority","kind","platform","links","drift"])$(id).value="";
   filter(d);$("search").focus();
 });
 for(const k of ["L07","L08","L09","L10","L11","L12","L13","L14"])$("sha"+k).textContent=d.baseline_commits[k];
 filter(d);
}
async function main(){
 try{
  const rsp=await fetch("/data/sinnoh-l15-public-consistency-diff.json",{cache:"no-store"});
  if(!rsp.ok)throw Error("Fonte pública indisponível");
  render(verify(await rsp.json()));
 }catch(_error){
  $("status").textContent="Bloqueado: a integridade da comparação pública não foi confirmada.";
  for(const id of ["changesRows","recordRows","groupRows","platformRows"])$(id).replaceChildren();
 }
}
main();