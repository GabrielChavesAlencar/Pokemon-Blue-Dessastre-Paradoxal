/* Regression smoke: real browser + temporary PBS fixture, never edits Decades. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const net = require("node:net");
const {spawn} = require("node:child_process");
const {chromium} = require("playwright");

const root = path.resolve(__dirname, "..");
function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer();
    server.on("error", reject);
    server.listen(0, "127.0.0.1", () => {
      const port = server.address().port;
      server.close(() => resolve(port));
    });
  });
}
function sleep(ms) {return new Promise(resolve => setTimeout(resolve, ms));}
async function ready(url, child) {
  for (let i=0;i<120;i++) {
    if (child.exitCode !== null) throw Error("Servidor Blue Studio encerrou antes de iniciar");
    try {const res = await fetch(url + "/api/status");if(res.ok) return;} catch (_) {}
    await sleep(150);
  }
  throw Error("Servidor Blue Studio nao iniciou em 18 segundos");
}
(async () => {
  const folder = fs.mkdtempSync(path.join(os.tmpdir(), "blue-studio-regression-"));
  const game = path.join(folder, "game");
  fs.mkdirSync(path.join(game, "PBS"), {recursive:true});
  fs.writeFileSync(path.join(game,"PBS","pokemon.txt"), "[TESTMON]\nName = Testmon\nTypes = WATER\nBaseStats = 70,70,70,70,70,70\n");
  fs.writeFileSync(path.join(game,"PBS","items.txt"), "[POTION]\nName = Potion\nPrice = 300\n");
  fs.writeFileSync(path.join(game,"PBS","trainers_story_mode.txt"), "[YOUNGSTER,TEST]\nPokemon = TESTMON,5\n");
  fs.writeFileSync(path.join(game,"PBS","encounters.txt"), "[005]\nLand,21\n  100,TESTMON,5\n");
  const port = await freePort();
  const url = "http://127.0.0.1:" + port;
  const child = spawn(process.env.PYTHON || "python3",
    ["-u","server/main.py","--no-browser","--game-dir",game,"--port",String(port)],
    {cwd:root,stdio:["ignore","pipe","pipe"]});
  let serverLog = "";
  child.stderr.on("data", b => {serverLog += String(b);});
  let browser;
  try {
    await ready(url, child);
    browser = await chromium.launch({headless:true});
    const page = await browser.newPage({viewport:{width:1440,height:900}});
    const errors = [];
    page.on("pageerror", error => errors.push(String(error)));
    await page.goto(url, {waitUntil:"domcontentloaded"});
    await page.waitForFunction(() => document.getElementById("fileTitle").textContent === "pokemon.txt");
    assert.equal(await page.locator("[data-panel]").count(), 20, "As 20 abas devem existir");
    assert.equal(await page.locator('[data-panel="pokemon"]').getAttribute("aria-selected"),"true");
    assert.equal(await page.locator("#pbsWorkspace").isVisible(),true);

    await page.locator('[data-panel="items"]').click();
    await page.waitForFunction(() => document.getElementById("fileTitle").textContent === "items.txt");
    await page.locator(".record").first().click();
    await page.waitForSelector("#f0");
    await page.locator("#f0").fill("Potion Regression");
    await page.locator("#save").click();
    await page.waitForFunction(() => document.querySelector("#save").disabled === true);
    assert.match(fs.readFileSync(path.join(game,"PBS","items.txt"),"utf-8"),/Potion Regression/);

    await page.locator('[data-panel="map"]').click();
    assert.equal(await page.locator("#featurePanel").isVisible(),true);
    assert.equal(await page.locator("#pbsWorkspace").isVisible(),false);
    assert.match(await page.locator("#featureStatus").textContent(),/PLANEJADO/);

    await page.locator('[data-panel="sprite"]').click();
    assert.match(await page.locator("#featureTitle").textContent(),/Importar sprites/);
    await page.locator('[data-shell="home"]').click();
    assert.equal(await page.locator("#studioHome").isVisible(),true);
    await page.locator('[data-shell="movesets"]').click();
    assert.equal(await page.locator("#movesetPanel").isVisible(),true);
    await page.locator('#movesetPanel [data-shortcut="pokemon"]').click();
    await page.waitForFunction(() => document.getElementById("fileTitle").textContent === "pokemon.txt");
    assert.equal(await page.locator("#pbsWorkspace").isVisible(),true);
    assert.deepEqual(errors,[],"Sem erros JS no navegador");

    const shotDir = path.join(root,"tests","artifacts");
    fs.mkdirSync(shotDir,{recursive:true});
    await page.screenshot({path:path.join(shotDir,"blue-studio-smoke.png"),fullPage:true});
    console.log("PASS: UI Emerald-like, 20 abas, PBS, save, placeholders, navegação, sem pageerror.");
  } catch (error) {
    console.error("REGRESSION FAILURE:", error);
    console.error(serverLog.slice(-2500));
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
    child.kill();
    fs.rmSync(folder, {recursive:true,force:true});
  }
})().catch(error => {console.error(error);process.exitCode = 1;});
