/* Music editor end-to-end; synthetic audio/maps, no installed game changes. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const net=require('node:net');
const {spawn,spawnSync}=require('node:child_process');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),python=process.env.PYTHON||'python3';
const delay=ms=>new Promise(r=>setTimeout(r,ms));
(async()=>{
  const folder=fs.mkdtempSync(path.join(os.tmpdir(),'blue-music-browser-')),game=path.join(folder,'game');
  const fixture=spawnSync(python,['tests/music_fixture.py',game],{cwd:root,encoding:'utf8'});
  assert.equal(fixture.status,0,fixture.stderr);
  const original=fs.readFileSync(path.join(game,'Data/Map001.rxdata'));
  const port=await new Promise(resolve=>{const s=net.createServer();s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>resolve(p));});});
  const url='http://127.0.0.1:'+port;
  const child=spawn(python,['-u','server/main.py','--no-browser','--game-dir',game,'--port',String(port)],{cwd:root,stdio:['ignore','pipe','pipe']});
  let log='',browser;child.stderr.on('data',b=>log+=b);
  try{
    let ready=false;for(let i=0;i<120;i++){try{if((await fetch(url+'/api/status')).ok){ready=true;break;}}catch{}await delay(150);}
    assert.ok(ready,'Server did not start: '+log);
    browser=await chromium.launch({headless:true,...(process.env.BROWSER_EXECUTABLE_PATH?{executablePath:process.env.BROWSER_EXECUTABLE_PATH}:{})});
    const page=await browser.newPage({viewport:{width:1440,height:1000}}),errors=[];
    const save=async()=>{
      const [response]=await Promise.all([page.waitForResponse(r=>r.url().endsWith('/api/music/assignment')&&r.request().method()==='POST'),page.locator('#musicSave').click()]);
      assert.equal(response.status(),200,await response.text());
      await page.waitForFunction(()=>document.getElementById('musicSave').disabled&&document.getElementById('musicNotice').textContent.includes('Música salva'));
    };
    page.on('pageerror',e=>errors.push(String(e)));await page.goto(url);
    await page.locator('[data-panel="music"]').click();
    await page.locator('[data-music-track="Town.wav"]').waitFor();
    await page.locator('[data-music-track="Battle.wav"]').click();
    await page.locator('#musicUse').click();
    await save();
    const config=()=>JSON.parse(fs.readFileSync(path.join(game,'Data/blue-music.json'),'utf8'));
    assert.equal(config().global.wild.track,'Battle.wav');
    await Promise.all([page.waitForResponse(r=>r.url().includes('/api/music/assignment?scope=map')),page.locator('#musicScope').selectOption('map')]);
    await page.waitForFunction(()=>document.getElementById('musicOriginal').textContent.includes('Town'));
    await page.locator('#musicUse').click();
    await page.locator('#musicVolume').fill('63');
    await save();
    assert.equal(config().maps['1'].volume,63);
    const response=await page.request.get(url+'/api/music/audio?id=Battle.wav',{headers:{Range:'bytes=0-11'}});
    assert.equal(response.status(),206);assert.equal((await response.body()).length,12);
    const source=path.join(game,'Audio/BGM/Town.wav');
    await page.locator('#musicUpload').setInputFiles(source);
    await page.locator('#musicFilename').fill('Nova.wav');
    await page.locator('#musicImport').click();
    await page.waitForFunction(()=>document.getElementById('musicNotice').textContent.includes('Áudio importado'));
    assert.deepEqual(fs.readFileSync(path.join(game,'Audio/BGM/Nova.wav')),fs.readFileSync(source));
    await page.locator('#musicReplace').check();
    await page.locator('#musicUpload').setInputFiles(path.join(game,'Audio/BGM/Battle.wav'));
    await page.locator('#musicImport').click();
    await page.waitForFunction(()=>document.getElementById('musicNotice').textContent.includes('Faixa substituída'));
    assert.deepEqual(fs.readFileSync(path.join(game,'Audio/BGM/Nova.wav')),fs.readFileSync(path.join(game,'Audio/BGM/Battle.wav')));
    await page.locator('#musicMode').selectOption('original');
    await save();
    assert.equal(config().maps['1'],undefined);
    assert.deepEqual(fs.readFileSync(path.join(game,'Data/Map001.rxdata')),original);
    // Re-selecting the tab/hash must not discard an unsaved assignment.
    await page.locator('#musicMode').selectOption('mute');
    await page.locator('[data-panel="music"]').click();
    assert.equal(await page.locator('#musicMode').inputValue(),'mute');
    page.on('dialog',dialog=>dialog.dismiss());
    await page.locator('[data-panel="pokemon"]').click();
    assert.equal(await page.locator('#musicWorkspace').isVisible(),true);
    await page.setViewportSize({width:390,height:844});
    assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),'Mobile horizontal overflow');
    assert.deepEqual(errors,[]);
    console.log('PASS music browser: battle, city, preview range, import, replace, original restoration, draft guard, mobile');
  }finally{if(browser)await browser.close();child.kill();await new Promise(r=>child.exitCode!==null?r():child.once('exit',r));fs.rmSync(folder,{recursive:true,force:true});}
})().catch(error=>{console.error(error);process.exitCode=1;});
