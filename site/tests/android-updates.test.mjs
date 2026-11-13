import test from 'node:test';
import assert from 'node:assert/strict';
import {androidUpdateGuide,downloadsPage} from '../src/assets/downloads.js';

test('site mostra um tutorial completo e separado para Decades e piloto Kanto',()=>{
  const guide=androidUpdateGuide();
  const rendered=downloadsPage();
  assert.match(rendered, /id="android-updates"/);
  assert.match(guide, /Pokemon-Blue-Android/);
  assert.match(guide, /Pokemon-Blue-Kanto-Android/);
  assert.match(guide, /termux-setup-storage/);
  assert.match(guide, /pkg install python/);
  assert.match(guide, /python ATUALIZAR-ANDROID\.py --update/);
  assert.match(guide, /Onde fica meu save/);
  assert.match(guide, /File A\.rxdata/);
  assert.match(guide, /sem patch direto compatível/);
  assert.match(guide, /Input\.mouse_in_window/);
  assert.match(guide, /JoiPlay/);
  assert.doesNotMatch(guide, /APK nativo com atualização automática/);
  assert.equal((rendered.match(/id="android-updates"/g)||[]).length,1);
  assert.equal((guide.match(/<li>/g)||[]).length,6);
  assert.equal((guide.match(/<\/li>/g)||[]).length,6);
});
