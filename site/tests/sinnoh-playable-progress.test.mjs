import test from "node:test";
import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),"../..");
const read=p=>readFile(path.join(root,p),"utf8");
test("J playable progress mirror matches exactly",async()=>{
 assert.equal(await read("data/regions/sinnoh-playable-progress.json"),
 await read("site/public/data/sinnoh-playable-progress.json"));
});
test("J series is independent of documentary milestones and not playable",async()=>{
 const d=JSON.parse(await read("data/regions/sinnoh-playable-progress.json"));
 assert.equal(d.track,"JOGAVEL_TWINLEAF_SANDGEM");
 assert.equal(d.status,"PILOT_NOT_INSTALLED_NOT_PLAYABLE");
 assert.equal(d.stages_code_ready,1);assert.equal(d.stages_native_validated,0);
 assert.equal(d.stages_total,8);assert.equal(d.stages.length,8);
 assert.equal(d.stages[0].status,"code_ready");
 assert.ok(d.stages.slice(1).every(x=>x.status==="blocked"&&!x.code_ready));
 assert.ok(d.stages.every(x=>!x.native_verified&&!x.playable));
 assert.equal(d.game_exe_tested,false);assert.equal(d.joiplay_tested,false);
});
test("J playable page has two honest bars and no upload/permission controls",async()=>{
 const [html,js]=await Promise.all([
  read("site/public/sinnoh-jogavel.html"),
  read("site/public/assets/sinnoh-playable-progress.js")]);
 assert.match(html,/SINNOH_J01_DIAGNOSTICAR_JOGAVEL\.bat/);
 assert.match(html,/id="engineering"/);assert.match(html,/id="native"/);
 assert.match(js,/PILOT_NOT_INSTALLED_NOT_PLAYABLE/);
 assert.match(js,/replaceChildren/);
 assert.doesNotMatch(html,/<form\b|type="file"/);
 assert.doesNotMatch(js,/innerHTML|localStorage|sessionStorage|postMessage|XMLHttpRequest/);
});
