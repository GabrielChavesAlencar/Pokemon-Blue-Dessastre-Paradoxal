import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const j=async p=>JSON.parse(await readFile(path.join(root,p),'utf8'));
const schema=await j('data/regions/unova-a16-receipt.schema.json');
const a16=await j('data/regions/unova-a16-receipt-contract.json');
const a15=await j('data/regions/unova-a15-native-readiness-matrix.json');
const board=await j('site/public/data/unova-github-progress.json');
const registry=await j('site/public/data/regions.json');
const required=Object.keys(schema.properties);

test('A16 uses strict JSON Schema 2020-12',()=>{
 assert.equal(schema.$schema,'https://json-schema.org/draft/2020-12/schema');
 assert.equal(schema.additionalProperties,false);
 assert.deepEqual(new Set(schema.required),new Set(required));
});
test('A16 declared unverified, not a native installer',()=>{
 assert.equal(a16.phase,'A16');
 assert.equal(a16.status,'REDACTED_RECEIPT_VALIDATION_ONLY');
 assert.equal(a16.can_install,false);
 assert.equal(a16.can_reserve_mapids,false);
 assert.equal(a16.can_release,false);
});
test('A16 strictly requires 11 A04-A14 receipts in order',()=>{
 const names=Array.from({length:11},(_,i)=>'A'+String(i+4).padStart(2,'0'));
 assert.deepEqual(a16.input_policy.exact_order,names);
 assert.deepEqual(a15.steps.map(s=>s.id),names);
 assert.equal(schema.properties.receipts.minItems,11);
 assert.equal(schema.properties.receipts.maxItems,11);
});
test('A16 references the published A15 source gate, not a game directory',()=>{
 assert.equal(a16.sources.a15,'data/regions/unova-a15-native-readiness-matrix.json');
 assert.equal(a16.sources.a15_validator,'scripts/regions/audit_unova_a15_native_readiness.py');
 assert.ok(Object.values(a16.sources).every(x=>!x.includes('Game.exe')&&!x.includes('Saves')));
});
test('A16 cannot leak source filenames or raw asset data',()=>{
 for(const key of ['path_fields_allowed','raw_asset_bytes_allowed','raw_saves_allowed','source_filenames_allowed',
                   'operator_receipt_files_opened_automatically','provenance_authenticated']){
  assert.equal(a16.input_policy[key],false,key);
 }
 assert.equal(a16.input_policy.max_bundle_bytes,131072);
});
test('SHA-256 is integrity only, not proven authenticity or rights',()=>{
 assert.equal(a16.input_policy.sha256_is_not_authenticity,true);
 assert.equal(a16.evidence_absence.source_licenses_verified,false);
 assert.equal(a16.evidence_absence.independent_human_approved,false);
});
test('MapInfos historical hash remains clearly unverified',()=>{
 assert.equal(schema.properties.source_baseline.properties.mapinfos_sha256.const,
              a15.historical_snapshot.mapinfos_sha256);
 assert.equal(schema.properties.source_baseline.properties.independent_recheck.const,false);
 assert.equal(a15.historical_snapshot.independently_verified_native_mapids_from_repo,false);
});
test('native candidate 518–599 cannot be reserved',()=>{
 const candidate=schema.properties.source_baseline.properties.unova_candidate_range.properties;
 assert.equal(candidate.start.const,518);
 assert.equal(candidate.end.const,599);
 assert.equal(candidate.reserved.const,false);
 assert.equal(a15.historical_snapshot.candidate_block_native_reserved,false);
});
test('Map001 events remain two unresolved references to MapID 3',()=>{
 const props=schema.properties.intro_map001.properties;
 assert.equal(props.mapid_3_resolved.const,false);
 assert.equal(props.computed_destinations_unresolved.const,20);
 assert.equal(props.events.minItems,2);
 assert.equal(props.events.items.properties.destination_map_id.const,3);
});
test('rights and QA cannot be silently promoted in schema',()=>{
 const props=schema.properties.rights.properties;
 assert.equal(props.license_verified.const,false);
 assert.equal(props.redistribution_approved.const,false);
 assert.equal(props.human_decision.const,'NOT_REVIEWED');
 const safe=schema.properties.protections.properties;
 assert.ok(Object.values(safe).every(p=>p.const===false));
});
test('no false registry/playability promotion after A16',()=>{
 assert.equal(registry.regions.UNOVA.status,'planned');
 assert.equal(board.status,'PLANNED_NOT_NATIVE_PLAYABLE');
 assert.deepEqual(board.native_technical_bar,{completed:0,total:8});
 assert.deepEqual(board.native_playable_bar,{completed:0,total:32});
 assert.equal(board.groups.flatMap(g=>g.tasks).filter(t=>t.status==='done').length,32);
});
test('schema is closed on receipts, not permissive with extra fields',()=>{
 const row=schema.properties.receipts.items;
 assert.equal(row.additionalProperties,false);
 assert.deepEqual(new Set(row.required),new Set(Object.keys(row.properties)));
 for(const key of ['receipt_sha256','previous_receipt_sha256','baseline_sha256',
                   'mapinfos_sha256','regional_manifests_sha256','map001_evidence_sha256']){
  assert.ok(row.required.includes(key));
 }
});
test('separate A17 requires independent review, never automated approval',()=>{
 assert.equal(a16.next_step.id,'A17');
 assert.equal(a16.next_step.cannot_auto_approve,true);
 assert.equal(a16.next_step.cannot_reserve_mapids,true);
 assert.equal(a16.next_step.cannot_install_maps,true);
 assert.equal(a16.next_step.cannot_change_save_data,true);
});
