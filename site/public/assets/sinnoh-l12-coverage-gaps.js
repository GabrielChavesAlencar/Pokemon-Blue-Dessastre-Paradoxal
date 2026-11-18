"use strict";
// Public read-only viewer. No mutation, uploads, secrets or arbitrary HTML.
const $=id=>document.getElementById(id);
const el=(tag,s,cls)=>{
 const x=document.createElement(tag);x.textContent=String(s);
 if(cls)x.className=cls;return x;
};
const addOpt=(id,value)=>{const x=el("option",value);x.value=value;$(id).append(x);};
function validate(d) {
 const c=d?.counts||{}, g=d?.gates||{}, q=d?.guardrails||{};
 if(d?.schema!==1||d.stage!=="L12"
    ||d.status!=="DOCUMENTARY_COVERAGE_COMPLETE_PHYSICAL_EVIDENCE_MISSING"
    ||d.mode!=="PUBLIC_READ_ONLY_EVIDENCE_GAPS"
    ||!Array.isArray(d.case_handoff)||d.case_handoff.length!==44
    ||!Array.isArray(d.criterion_handoff)||d.criterion_handoff.length!==20
    ||!Array.isArray(d.blockers)||d.blockers.length!==6
    ||!Array.isArray(d.coverage_layers)||d.coverage_layers.length!==6
    ||!Array.isArray(d.platform_handoff)||d.platform_handoff.length!==2
    ||c.cases_total!==44||c.criteria_total!==20||c.windows!==43||c.android!==1
    ||c.documentary_links_verified!==1084||c.documentary_links_missing!==0
    ||c.local_reports!==0||c.human_approved!==0||c.native_completed!==0
    ||c.native_approved!==0||c.phase_bcd_completed!==0||c.phase_bcd_total!==13
    ||c.human_evidence_missing!==20||c.native_tests_missing!==44
    ||c.local_reports_missing!==5||c.phase_bcd_missing!==13
    ||g.r07!=="PENDING"||g.r08!=="PENDING"||g.r09!=="PENDING"
    ||!q.r09_pending||!q.mapids_not_reserved||!q.asset_rights_not_approved
    ||!q.watch_unchanged_not_global_save_isolation||q.sinnoh_playable!==false
    ||d.documentary_integrity?.links_checked!==1084
    ||d.documentary_integrity.differences_found!==0
    ||d.documentary_integrity.verified_public_metadata_only!==true
    ||d.documentary_integrity.physical_source_authenticated!==false
    ||d.documentary_integrity.human_review_completed!==false
    ||d.documentary_integrity.native_qa_completed!==false
    ||JSON.stringify(d.coverage_layers.map(x=>[x.expected,x.observed,x.missing]))
      !==JSON.stringify([[1084,1084,0],[20,0,20],[43,0,43],[1,0,1],[5,0,5],[13,0,13]])
    ||d.coverage_layers.some(x=>x.native_evidence!==false)
    ||new Set(d.case_handoff.map(x=>x.id)).size!==44
    ||new Set(d.criterion_handoff.map(x=>x.id)).size!==20
    ||d.case_handoff.filter(x=>x.platform==="windows").length!==43
    ||d.case_handoff.filter(x=>x.platform==="android").length!==1
    ||d.case_handoff.some(x=>x.native_qa_state!=="NOT_EXECUTED"
       ||x.independent_human_review_state!=="NOT_REVIEWED"
       ||x.authorized_native_qa!==false||x.evidence_accepted!==false
       ||(x.platform==="android"&&(x.pending_gates.includes("B10")||x.pending_gates.includes("B11")))
       ||(x.platform==="windows"&&(!x.pending_gates.includes("B10")||!x.pending_gates.includes("B11"))))
    ||d.criterion_handoff.some(x=>x.independent_review_state!=="NOT_REVIEWED"
       ||x.accepted_evidence!==false||x.human_signoff!==false)
    ||JSON.stringify(d.blockers.map(x=>x.id))!==JSON.stringify(["B09","B10","B11","R07","R08","R09"])
    ||d.blockers.some(x=>x.state!=="PENDING"||x.approved!==false)
    ||d.global_r09?.id!=="R09"||d.global_r09.approved!==false
    ||d.global_r09.not_a_new_case!==true||d.global_r09.case_ids.length!==0
    ||d.platform_handoff[1].requires_windows_b10_b11!==false
    ||d.platform_handoff.some(x=>x.native_cases_tested!==0||x.shares_android_approval!==false)
    ||!["L07","L08","L09","L10","L11"].every(k=>/^[a-f0-9]{40}$/.test(d.baseline_commits?.[k]))) {
   throw new Error("Relatório documental incompatível");
 }
 return d;
}
function tr(parts){
 const row=document.createElement("tr");
 for(const [txt,style] of parts){
   const td=document.createElement("td");td.append(el("span",txt,style));row.append(td);
 }
 return row;
}
function filter(d){
 const q=$("search").value.trim().toLocaleLowerCase("pt-BR");
 const p=$("platform").value,k=$("kind").value,c=$("criterion").value,b=$("blocker").value,gap=$("gap").value;
 const found=d.case_handoff.filter(x=>
   (!q||(x.id+" "+x.kind).toLocaleLowerCase("pt-BR").includes(q))
   &&(!p||x.platform===p)&&(!k||x.kind===k)
   &&(!c||x.criterion_ids.includes(c))&&(!b||x.pending_gates.includes(b))
   &&(gap!=="metadata")
   &&(!gap||gap==="human"&&x.independent_human_review_state==="NOT_REVIEWED"
             ||gap==="native"&&x.native_qa_state==="NOT_EXECUTED"));
 $("casesRows").replaceChildren(...found.map(x=>tr([
    [x.id,""],[x.platform+" · "+x.kind,""],[String(x.documentary_criterion_links),"document"],
    [x.pending_gates.join(", "),"pending"],["Humana ausente / QA não executada","pending"]
 ])));
 $("status").textContent=gap==="metadata"
   ?"0 lacunas de vínculos públicos. Isso não representa aprovação de QA."
   :found.length+" de 44 casos · todos sem evidência humana e execução nativa.";
}
function render(d){
 $("layersRows").replaceChildren(...d.coverage_layers.map(x=>tr([
   [x.id,""],[x.scope,""],[x.observed+"/"+x.expected,x.id==="PUBLIC_METADATA_LINKS"?"document":"pending"],
   [String(x.missing),x.missing?"pending":"document"],[x.state,x.missing?"pending":"document"]
 ])));
 [...new Set(d.case_handoff.map(x=>x.kind))].forEach(x=>addOpt("kind",x));
 d.criterion_handoff.forEach(x=>addOpt("criterion",x.id));
 d.blockers.filter(x=>x.id!=="R09").forEach(x=>addOpt("blocker",x.id));
 $("criteriaRows").replaceChildren(...d.criterion_handoff.map(x=>tr([
   [x.id,""],[x.stage,""],[String(x.case_ids.length),"document"],["Não revisado","pending"]
 ])));
 $("blockersRows").replaceChildren(...d.blockers.map(x=>tr([
   [x.id,""],[x.scope,""],[x.id==="R09"?"Global, nenhum novo caso":String(x.case_ids.length),""],["Pendente","pending"]
 ])));
 for(const id of ["search","platform","kind","criterion","blocker","gap"])
   $(id).addEventListener("input",()=>filter(d));
 $("reset").addEventListener("click",()=>{
   for(const id of ["search","platform","kind","criterion","blocker","gap"])$(id).value="";
   filter(d);$("search").focus();
 });
 for(const k of ["L07","L08","L09","L10","L11"])$("sha"+k).textContent=d.baseline_commits[k];
 filter(d);
}
async function main(){
 try{
   const res=await fetch("/data/sinnoh-l12-public-coverage-gaps.json",{cache:"no-store"});
   if(!res.ok)throw new Error("Fonte pública indisponível");
   render(validate(await res.json()));
 }catch(_e){
   $("status").textContent="Bloqueado: integridade do relatório L12 não comprovada.";
   for(const id of ["layersRows","casesRows","criteriaRows","blockersRows"])$(id).replaceChildren();
 }
}
main();