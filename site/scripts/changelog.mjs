import {execFileSync} from 'node:child_process';
import {readFileSync, writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';

const site = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const generatedPrefix = 'chore(site): sincronizar histórico';
export function category(title) {
  if (/^feat(?:\(|:)|adicion|novo|nova/i.test(title)) return 'Novidades';
  if (/^fix(?:\(|:)|corrig|corre[cç]/i.test(title)) return 'Correções';
  if (/^docs(?:\(|:)|manual|guia/i.test(title)) return 'Documentação';
  if (/^test(?:\(|:)/i.test(title)) return 'Testes';
  return 'Melhorias';
}
export function mergeHistory(seed, commits) {
  const map = new Map();
  for (const item of [...seed, ...commits]) {
    if (!/^[a-f0-9]{40}$/.test(item.sha ?? '') || !item.title?.trim() || !Number.isFinite(Date.parse(item.date))) continue;
    if (item.title.startsWith(generatedPrefix)) continue;
    map.set(item.sha, {...item, title: item.title.trim(), category: category(item.title)});
  }
  return [...map.values()].sort((a,b) => Date.parse(b.date)-Date.parse(a.date) || a.sha.localeCompare(b.sha));
}
export function generate({cwd = path.resolve(site,'..'), env = process.env, seedPath = path.join(site,'public/data/updates.json')} = {}) {
  let seed=[]; let commits=[];
  try { seed=JSON.parse(readFileSync(seedPath,'utf8')).commits ?? []; } catch {}
  try {
    const raw=execFileSync('git',['log','HEAD','--format=%H%x1f%cI%x1f%s%x1e'],{cwd,encoding:'utf8',maxBuffer:8*1024*1024,stdio:['ignore','pipe','ignore']});
    commits=raw.split('\x1e').map(line=>line.trim()).filter(Boolean).map(line=>{
      const [sha,date,...title]=line.split('\x1f'); return {sha,date,title:title.join('\x1f')};
    });
  } catch {}
  // Vercel's Git metadata includes the current push even in a shallow checkout.
  if (env.VERCEL_GIT_COMMIT_SHA && env.VERCEL_GIT_COMMIT_MESSAGE) {
    const date=commits.find(x=>x.sha===env.VERCEL_GIT_COMMIT_SHA)?.date ?? seed.find(x=>x.sha===env.VERCEL_GIT_COMMIT_SHA)?.date ?? new Date().toISOString();
    commits.push({sha:env.VERCEL_GIT_COMMIT_SHA,date,title:env.VERCEL_GIT_COMMIT_MESSAGE.split('\n')[0]});
  }
  const history=mergeHistory(seed,commits);
  if (!history.length) throw new Error('O histórico de atualizações está vazio.');
  return {repository:'GabrielChavesAlencar/Pokemon-Blue-Dessastre-Paradoxal',commits:history};
}
if (process.argv.includes('--write-seed')) {
  const data=generate(); writeFileSync(path.join(site,'public/data/updates.json'),JSON.stringify(data,null,2)+'\n');
  console.log(`Histórico sincronizado: ${data.commits.length} atualizações.`);
}
