"use strict";
// Read-only, same-origin public JSON. Never take arbitrary HTML from JSON.
const $ = id => document.getElementById(id);
const node = (name, text, className) => {
  const x = document.createElement(name);
  x.textContent = String(text);
  if (className) x.className = className;
  return x;
};
function option(value, label) {
  const x = node("option", label);
  x.value = value;
  return x;
}
function valid(data) {
  const c = data?.counts || {};
  const g = data?.gates || {};
  if (data?.schema !== 1 || data?.stage !== "L10"
      || data.status !== "PUBLIC_BLOCKER_INDEX_ONLY_ALL_PENDING"
      || data.mode !== "PUBLIC_GITHUB_READ_ONLY"
      || !Array.isArray(data.cases) || data.cases.length !== 44
      || !Array.isArray(data.criteria) || data.criteria.length !== 20
      || !Array.isArray(data.blockers) || data.blockers.length !== 6
      || c.windows !== 43 || c.android !== 1 || c.cases_total !== 44
      || c.criteria_total !== 20 || c.human_approved !== 0
      || c.native_approved !== 0 || c.native_completed !== 0
      || c.local_reports !== 0 || c.phase_bcd_completed !== 0
      || g.r07 !== "PENDING" || g.r08 !== "PENDING" || g.r09 !== "PENDING"
      || g.sinnoh_playable !== false || data.sinnoh_playable !== false
      || data.can_run_game_exe !== false || data.can_run_joiplay !== false
      || data.can_run_windows_sandbox !== false || data.can_install_live_game !== false
      || data.global_r09_pending !== true || !data.windows_android_review_independent
      || !data.watch_unchanged_not_global_isolation || !data.asset_rights_not_approved
      || !data.mapids_not_reserved || data.local_android_l05_completed !== false
      || new Set(data.cases.map(x => x.id)).size !== 44
      || new Set(data.criteria.map(x => x.id)).size !== 20
      || JSON.stringify(data.blockers.map(x => x.id)) !== JSON.stringify(["B09","B10","B11","R07","R08","R09"])
      || data.cases.filter(x => x.platform === "windows").length !== 43
      || data.cases.filter(x => x.platform === "android").length !== 1
      || data.cases.some(x => x.review_state !== "NOT_REVIEWED"
            || x.action !== "KEEP_PENDING" || x.native_status !== "pending"
            || x.approved !== false || x.native_execution_authorized !== false
            || !Array.isArray(x.criteria) || !Array.isArray(x.blocked_by)
            || (x.platform === "android" && (x.blocked_by.includes("B10") || x.blocked_by.includes("B11")))
            || (x.platform === "windows" && (!x.blocked_by.includes("B10") || !x.blocked_by.includes("B11"))))
      || data.criteria.some(x => x.review_state !== "NOT_REVIEWED" || x.signoff !== false)
      || data.blockers.some(x => x.status !== "PENDING" || x.not_a_native_approval !== true)
      || data.blockers.at(-1).scope !== "GLOBAL_REGION_PENDING_NOT_CASE_GATE"
      || data.blockers.at(-1).case_ids.length !== 0
      || !["L07","L08","L09"].every(x => /^[0-9a-f]{40}$/.test(data.baseline_commits?.[x]))) {
    throw new Error("Integridade pública não comprovada");
  }
  return data;
}
function row(values) {
  const tr = document.createElement("tr");
  for (const x of values) {
    const td = document.createElement("td");
    td.append(x);
    tr.append(td);
  }
  return tr;
}
function render(data) {
  const blockers = data.blockers.map(x => {
    const card = document.createElement("article");
    card.className = "blockcard";
    card.id = "bloqueio-" + x.id;
    const title = node("h3", x.id);
    const desc = node("p", x.description);
    const count = node("small", x.scope === "GLOBAL_REGION_PENDING_NOT_CASE_GATE"
      ? "Pendência regional global, sem vínculo de caso novo"
      : x.windows_cases + " Windows · " + x.android_cases + " Android");
    const pending = node("p", "Pendente · sem aprovação", "pending");
    const jump = node("a", "Ver casos associados");
    jump.href = "#casos";
    jump.addEventListener("click", () => {
      $("blocker").value = x.id === "R09" ? "" : x.id;
      filter(data);
    });
    card.append(title,desc,count,pending,jump);
    return card;
  });
  $("blockers").replaceChildren(...blockers);
  [...new Set(data.cases.map(x => x.kind))].forEach(k => $("kind").append(option(k,k)));
  data.criteria.forEach(c => $("criterion").append(option(c.id,c.id)));
  data.blockers.forEach(x => { if(x.id !== "R09") $("blocker").append(option(x.id,x.id)); });
  $("criterionRows").replaceChildren(...data.criteria.map(c => row([
    node("code",c.id), node("span",c.requirement),
    node("span",c.case_ids.length+" casos ("+c.windows_cases+" Windows, "+c.android_cases+" Android)"),
    node("strong","Não revisado","pending")
  ])));
  for(const k of ["L07","L08","L09"]) $("sha"+k).textContent=data.baseline_commits[k];
  const ids=["search","platform","kind","blocker","criterion"];
  ids.forEach(id => $(id).addEventListener("input",()=>filter(data)));
  $("reset").addEventListener("click",()=>{
    ids.forEach(id=>{$(id).value="";});
    filter(data);
    $("search").focus();
  });
  filter(data);
}
function filter(data) {
  const q=$("search").value.trim().toLocaleLowerCase("pt-BR");
  const p=$("platform").value, k=$("kind").value, b=$("blocker").value, c=$("criterion").value;
  const found=data.cases.filter(x =>
      (!q || (x.id+" "+x.kind).toLocaleLowerCase("pt-BR").includes(q)) &&
      (!p || x.platform === p) &&
      (!k || x.kind === k) &&
      (!b || x.blocked_by.includes(b)) &&
      (!c || x.criteria.includes(c)));
  $("caseRows").replaceChildren(...found.map(x => row([
    node("code",x.id),
    node("span",x.kind+" / "+(x.platform==="windows"?"Windows":"Android/JoiPlay"),"pill"),
    node("span",x.criteria.join(", ")),
    node("span",x.blocked_by.join(", ")),
    node("strong","Pendente · 0 QA","pending")
  ])));
  $("status").textContent=found.length+" de 44 casos exibidos · nenhuma autorização nativa.";
}
async function main() {
  try {
    const response=await fetch("/data/sinnoh-l10-public-blocker-index.json",{cache:"no-store"});
    if(!response.ok) throw new Error("Dados públicos indisponíveis");
    render(valid(await response.json()));
  } catch (_err) {
    $("status").textContent="Bloqueado: não foi possível validar a fonte documental pública.";
    $("blockers").replaceChildren();
    $("caseRows").replaceChildren();
    $("criterionRows").replaceChildren();
  }
}
main();
