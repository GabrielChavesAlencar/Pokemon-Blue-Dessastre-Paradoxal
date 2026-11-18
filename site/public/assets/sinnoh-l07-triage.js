"use strict";
// Read-only visual filtering. No mutation, execution, user upload or persistence.
const $ = id => document.getElementById(id);
const selects = ["q", "platform", "kind", "criterion", "blocker"].map($);
const el = (tag, value, cls) => {
  const node = document.createElement(tag);
  node.textContent = value;
  if (cls) node.className = cls;
  return node;
};
const option = (value, label) => {
  const item = document.createElement("option");
  item.value = value;
  item.textContent = label;
  return item;
};
function validated(data) {
  if (!data || data.stage !== "L07" || data.status !== "PUBLIC_READ_ONLY_TRIAGE_ALL_NATIVE_PENDING"
      || !Array.isArray(data.cases) || data.cases.length !== 44
      || !Array.isArray(data.criteria) || data.criteria.length !== 20
      || data.counts?.windows !== 43 || data.counts?.android !== 1
      || data.counts?.human_approved !== 0 || data.counts?.native_approved !== 0
      || data.counts?.native_completed !== 0 || data.counts?.local_reports !== 0
      || data.gates?.sinnoh_playable !== false
      || new Set(data.cases.map(x => x.id)).size !== 44
      || new Set(data.criteria.map(x => x.id)).size !== 20
      || data.cases.some(x => x.action !== "KEEP_PENDING" || x.review_state !== "NOT_REVIEWED"
          || x.native_status !== "pending" || x.evidence_accepted !== false
          || x.native_qa_authorized !== false)
      || data.criteria.some(x => x.status !== "NOT_REVIEWED"
          || x.human_signoff !== false || x.physical_evidence_accepted !== false)
      || data.cases.filter(x => x.platform === "windows").length !== 43
      || data.cases.filter(x => x.platform === "android").length !== 1
      || data.cases.some(x => x.platform === "android"
            && (x.blocked_by.includes("B10") || x.blocked_by.includes("B11")))
      || data.cases.some(x => x.platform === "windows"
            && (!x.blocked_by.includes("B10") || !x.blocked_by.includes("B11")))) {
    throw new Error("Fonte documental inconsistente: exibição bloqueada.");
  }
  return data;
}
function drawRow(row) {
  const tr = document.createElement("tr");
  const fields = [
    el("code", row.id),
    el("span", row.kind + " / " + (row.platform === "windows" ? "Windows" : "Android"), "tag"),
    el("span", row.required_criteria_ids.join(", ")),
    el("span", row.blocked_by.join(", ")),
    el("strong", "Pendente · sem QA", "status"),
  ];
  fields.forEach(field => {
    const td = document.createElement("td");
    td.append(field);
    tr.append(td);
  });
  return tr;
}
function loadCriteria(data) {
  $("criteria").replaceChildren(...data.criteria.map(row => {
    const tr = document.createElement("tr");
    [el("code", row.id),
     el("span", row.requirement),
     el("span", String(row.dependent_cases) + " casos (" + row.windows_dependencies + " Windows, " + row.android_dependencies + " Android)"),
     el("strong", "Não revisado", "status")].forEach(node => {
       const td = document.createElement("td");
       td.append(node);
       tr.append(td);
     });
    return tr;
  }));
}
function filterRows(data) {
  const q = $("q").value.trim().toLocaleLowerCase("pt-BR");
  const platform = $("platform").value;
  const kind = $("kind").value;
  const criterion = $("criterion").value;
  const blocker = $("blocker").value;
  const visible = data.cases.filter(row =>
    (!q || (row.id + " " + row.kind).toLocaleLowerCase("pt-BR").includes(q)) &&
    (!platform || row.platform === platform) &&
    (!kind || row.kind === kind) &&
    (!criterion || row.required_criteria_ids.includes(criterion)) &&
    (!blocker || row.blocked_by.includes(blocker)));
  $("cases").replaceChildren(...visible.map(drawRow));
  $("count").textContent = String(visible.length) + " de 44 casos · todos pendentes, 0 testes nativos aprovados.";
}
async function main() {
  try {
    const response = await fetch("/data/sinnoh-l07-public-triage.json", {cache: "no-store"});
    if (!response.ok) throw new Error("JSON indisponível");
    const data = validated(await response.json());
    [...new Set(data.cases.map(x => x.kind))].forEach(k => $("kind").append(option(k,k)));
    data.criteria.forEach(c => $("criterion").append(option(c.id,c.id)));
    loadCriteria(data);
    selects.forEach(s => s.addEventListener("input", () => filterRows(data)));
    $("reset").addEventListener("click", () => {
      selects.forEach(s => {s.value = "";});
      filterRows(data);
      $("q").focus();
    });
    filterRows(data);
  } catch (_error) {
    $("count").textContent = "Falha de integridade ou carregamento. A triagem foi bloqueada; nenhum caso pode ser considerado aprovado.";
    $("cases").replaceChildren();
    $("criteria").replaceChildren();
  }
}
main();
