import {execFileSync} from 'node:child_process';
import {readdir} from 'node:fs/promises';
import {cp, mkdir, readFile, writeFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {generate} from './changelog.mjs';
import {extractSprites} from './extract-sprites.mjs';
import {extractExtras} from './extract-extras.mjs';
import {generateGuides} from './guides.mjs';
import {generateSinnohGuide,sinnohSourcePaths} from './sinnoh-guide.mjs';
import {generateUnovaGuide,unovaGuideSources} from './unova-guide.mjs';
import {generateSinnohG10Status,sinnohG10Sources} from './sinnoh-g10-status.mjs';
import {activeLocations} from '../src/assets/data.js';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const output=path.join(root,'dist');
for(const file of await readdir(path.join(root,'src/assets'))) if(file.endsWith('.js')) execFileSync(process.execPath,['--check',path.join(root,'src/assets',file)],{stdio:'inherit'});
await mkdir(output,{recursive:true});
await cp(path.join(root,'src'),output,{recursive:true});
await cp(path.join(root,'public'),output,{recursive:true});
console.log(`Sprites autorais: ${await extractSprites(root,output)}`);
console.log(`Cries e pedras autorais: ${await extractExtras(root,output)}`);
await writeFile(path.join(output,'data/updates.json'),JSON.stringify(generate()));
const trainerEvidence=JSON.parse(await readFile(path.join(root,'../data/regions/trainer-event-bindings-phase1.json'),'utf8'));
if(trainerEvidence.schema!==1||trainerEvidence.records.length!==13||
  trainerEvidence.state!=='NATIVE_AUDIT_PENDING_NOT_GAMEPLAY')throw new Error('regional-trainer-bindings-invalid');
await writeFile(path.join(output,'data/trainer-event-bindings-phase1.json'),JSON.stringify(trainerEvidence));
console.log('Vínculos regionais dos pilotos: '+trainerEvidence.records.length+' (não certificados como jogáveis)');
const repoRoot=path.resolve(root,'..');
const sinnohSourceData=Object.fromEntries(await Promise.all(
  Object.entries(sinnohSourcePaths).map(async ([name,relative])=>[
    name,JSON.parse(await readFile(path.join(repoRoot,relative),'utf8'))
  ])
));
const sinnohGuide=generateSinnohGuide(sinnohSourceData);
await writeFile(path.join(output,'data/sinnoh-guide.json'),JSON.stringify(sinnohGuide));
console.log('Sinnoh CH17: '+sinnohGuide.counts.areas+' áreas, '+sinnohGuide.counts.gyms+' ginásios, 0 mapas nativos');
const unovaSources=Object.fromEntries(await Promise.all(
  Object.entries(unovaGuideSources).map(async ([name,relative])=>[
    name,JSON.parse(await readFile(path.join(repoRoot,relative),'utf8'))
  ])
));
const unovaGuide=generateUnovaGuide(unovaSources);
await writeFile(path.join(output,'data/unova-guide.json'),JSON.stringify(unovaGuide));
console.log('Unova G06.2: '+unovaGuide.counts.areas+' áreas, '+unovaGuide.counts.chapters+' capítulos, 0 mapas nativos');
const sinnohG10Data=Object.fromEntries(await Promise.all(
  Object.entries(sinnohG10Sources).map(async ([key,relative])=>[
    key,JSON.parse(await readFile(path.join(repoRoot,relative),'utf8'))
  ])
));
const sinnohImplementation=generateSinnohG10Status(sinnohG10Data,sinnohGuide);
await writeFile(path.join(output,'data/sinnoh-implementation.json'),JSON.stringify(sinnohImplementation));
console.log('Sinnoh G10: '+sinnohImplementation.states[1].count+
  ' terrenos candidatos privados; instalados=0, jogáveis=0');

const readJson=async name=>JSON.parse(await readFile(path.join(root,'public/data',name+'.json'),'utf8'));
const locationData=await readJson('locations');
const generatedGuides=generateGuides({catalog:await readJson('catalog'),locations:{...locationData,locations:activeLocations(locationData.locations,await readJson('region-points'))},details:await readJson('details'),editorial:await readJson('guides')});
await writeFile(path.join(output,'data/guides.json'),JSON.stringify(generatedGuides));
console.log('Guias sincronizados: '+generatedGuides.guides.length);
for (const file of ['catalog.json','details.json','locations.json','updates.json','guides.json','story-trainers.json','regular-trainers.json','region-points.json','future-eevee.json','regions.json','kanto.json','johto-pilot.json','hoenn-pilot.json']) JSON.parse(await readFile(path.join(output,'data',file),'utf8'));
console.log('Portal Blue pronto: dist/');
