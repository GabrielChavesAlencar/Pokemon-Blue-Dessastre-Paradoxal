#!/usr/bin/env python3
"""A09 read-only intro-transfer forensics and local installer claims triage.

Scope is deliberately bounded: Map001 event 1/2, Scripts.rxdata and manifest
files in Data. This is not a Ruby interpreter, dynamic execution, authorization
for MapIDs, or proof of game progression. No native data is changed.
"""
from __future__ import annotations

import hashlib
import json
import re
import zlib
from pathlib import Path

import audit_unova_a04_mapids as a04
import audit_unova_a07_reference_provenance as a07
import audit_unova_a08_readiness as a08
from server.ruby_marshal import RubyObject, loads

OUT = Path('.blue-work/unova/audit')
TRIGGERS = {0:'ACTION_BUTTON',1:'PLAYER_TOUCH',2:'EVENT_TOUCH',3:'AUTORUN',4:'PARALLEL_PROCESS'}
COMMANDS = {0:'END',101:'SHOW_TEXT',102:'CHOICE',108:'COMMENT',111:'BRANCH',112:'LOOP',113:'BREAK_LOOP',115:'EXIT_EVENT',118:'LABEL',119:'JUMP_LABEL',121:'SWITCHES',122:'VARIABLES',123:'SELF_SWITCH',125:'GOLD',201:'TRANSFER_PLAYER',202:'SET_EVENT_LOCATION',205:'MOVE_ROUTE',301:'BATTLE',355:'RUBY_SCRIPT',408:'COMMENT_CONTINUATION',411:'ELSE',412:'END_BRANCH',655:'RUBY_SCRIPT_CONTINUATION'}
SENSITIVE_IDS = set(range(518,600)) | {3}
TRANSFER_CALL = re.compile(r'\b(reserve_transfer|pbWarp|pbTeleport|pbTransferPlayer|pbTransfer|transfer_player)\s*\(\s*([^,\)\r\n]{0,100})', re.I)
ASSIGN_CALL = re.compile(r'\b(player_new_map_id)\s*=\s*([^\r\n;,\)]{0,100})', re.I)
MAX_SCRIPT_PER_ENTRY = a07.SCRIPT_ENTRY_LIMIT
MAX_SCRIPT_TOTAL = a07.SCRIPT_TOTAL_LIMIT
MAX_EVIDENCE = 400
MAX_READ = a07.MAP_LIMIT


def deny(reason):
    raise ValueError('UNOVA_A09_BLOQUEADO: '+str(reason))


def fields(obj):
    return obj.attrs if isinstance(obj,RubyObject) else {}


def safe_obj_size(value):
    return isinstance(value, list) and len(value) <= a07.MAX_COMMANDS


def summarize_command(cmd, index):
    obj=fields(cmd)
    code=obj.get('@code')
    if type(code) is not int:deny('Comando do Map001 invalido')
    return {'index':index,'code':code,'kind':COMMANDS.get(code,'OTHER'),
            'indent':obj.get('@indent') if type(obj.get('@indent')) is int else None}


def intro_events(game, a04_report, a07_report, a08_report):
    data=a04.directory_root(game)
    base=a04_report['sources']['DECADES']
    row=next((x for x in base['maps'] if x.get('id')==1),None)
    if not row:deny('Map001 ausente do inventario A04')
    path=data/row['source_filename']
    raw=a07.limited_read(path,MAX_READ)
    if hashlib.sha256(raw).hexdigest()!=row['sha256']:
        deny('Hash Map001 divergente A04')
    root=loads(raw)
    if not isinstance(root,RubyObject) or root.name!='RPG::Map':deny('Map001 invalido')
    events=fields(root).get('@events',{})
    if not isinstance(events,dict):deny('Lista de eventos invalida')
    intro=[];transfer_fingerprints=[];pending=[]
    a08_index={r['event_id']:r for r in a08_report.get('map001_event_context',[])}
    for eid in (1,2):
        event=events.get(eid)
        if not isinstance(event,RubyObject):
            pending.append('EVENT_%d_NOT_FOUND'%eid)
            continue
        ep=fields(event)
        pages=ep.get('@pages',[])
        if not isinstance(pages,list) or len(pages)>a07.MAX_PAGES:deny('Paginas Map001 invalidas')
        found={'event_id':eid,'event_name':a08_index.get(eid,{}).get('name') or a08.plain(ep.get('@name',b'')),
               'pages_total':len(pages),'pages':[]}
        a08_pages={p['page_index']:p for p in a08_index.get(eid,{}).get('pages',[])}
        for pn,page in enumerate(pages,1):
            p=fields(page)
            commands=p.get('@list',[])
            if not safe_obj_size(commands):deny('Comandos Map001 invalidos')
            trigger=p.get('@trigger')
            cond=fields(p.get('@condition'))
            conditions={k:bool(cond.get('@'+k)) for k in ('switch1_valid','switch2_valid','variable_valid','self_switch_valid')}
            guards={k:cond.get('@'+k) for k in ('switch1_id','switch2_id','variable_id','variable_value') if type(cond.get('@'+k)) is int}
            if '@self_switch_ch' in cond:guards['self_switch_ch']=a08.plain(cond['@self_switch_ch'],10)
            evidence=[];branches=[]
            for ci,cmd in enumerate(commands):
                d=fields(cmd);code=d.get('@code')
                if type(code) is not int:deny('Comando nao numerico')
                if code in (111,411,412,121,122,123):
                    branches.append(summarize_command(cmd,ci))
                if code!=201:continue
                params=d.get('@parameters',[])
                literal=(isinstance(params,list) and len(params)>1 and type(params[0]) is int and
                         params[0]==0 and type(params[1]) is int and params[1]>0)
                target=params[1] if literal else None
                if target not in SENSITIVE_IDS and literal:continue
                entry={'command_index':ci,'destination_map_id':target,'transfer_kind':'STATIC' if literal else 'DYNAMIC_OR_UNSUPPORTED',
                       'x':params[2] if literal and len(params)>2 and type(params[2]) is int else None,
                       'y':params[3] if literal and len(params)>3 and type(params[3]) is int else None,
                       'surrounding_codes':[summarize_command(commands[j],j) for j in range(max(0,ci-3), min(len(commands),ci+4))],
                       'event_page_gate_only':True,'runtime_path_verified':False}
                evidence.append(entry)
                if target==3:
                    transfer_fingerprints.append((eid,pn,ci,3))
            page_report={'page_index':pn,'trigger_code':trigger if type(trigger) is int else None,
                         'trigger_label':TRIGGERS.get(trigger,'UNKNOWN'),
                         'condition_flags':conditions,'condition_ids':guards,
                         'command_total':len(commands),'branch_like_command_count':len(branches),
                         'branch_like_command_sample':branches[:25],
                         'transfer_evidence':evidence[:MAX_EVIDENCE],
                         'transfer_evidence_truncated':len(evidence)>MAX_EVIDENCE,
                         'has_static_transfer_to_3':any(x['destination_map_id']==3 for x in evidence),
                         'a08_page_present':pn in a08_pages}
            found['pages'].append(page_report)
        intro.append(found)
    a07_fingerprints=sorted((x['event_id'],x['page_index'],x['command_index'],3)
        for x in a07_report.get('static_interest_references',[])
        if x.get('source_type')=='MAP' and x.get('source_map_id')==1 and x.get('event_id') in (1,2) and x.get('destination_map_id')==3)
    same=sorted(transfer_fingerprints)==a07_fingerprints
    if not same:pending.append('TRANSFER_FINGERPRINT_MISMATCH_WITH_A07')
    return {'map001_sha256':row['sha256'],'events':intro,
            'static_transfer_to_mapid3_count':len(transfer_fingerprints),
            'mapid3_origin_matches_a07':same,'findings':pending,
            'runtime_conditions_evaluated':False}


def analyze_snippet(script, provenance, findings, counts):
    if not isinstance(script,(bytes,str)):
        counts['skipped_entries']+=1;return
    script=script.decode('utf-8','replace') if isinstance(script,bytes) else script
    if len(script)>MAX_SCRIPT_PER_ENTRY:
        counts['skipped_entries']+=1;return
    counts['text_sections_scanned']+=1
    for pattern in (TRANSFER_CALL,ASSIGN_CALL):
        for match in pattern.finditer(script):
            if len(findings)>=MAX_EVIDENCE:
                counts['findings_truncated']+=1;continue
            prefix=script[max(0,match.start()-25):match.start()]
            argument=match.group(2).strip()
            # Classify function definitions separately; a function signature does not transfer a player.
            if re.search(r'\bdef\s*$',prefix,re.I): category='DEFINITION'
            elif re.fullmatch(r'\d+',argument):
                mid=int(argument)
                category='LITERAL_TARGET_3' if mid==3 else ('LITERAL_UNOVA_CANDIDATE' if mid in SENSITIVE_IDS else 'LITERAL_OTHER')
            elif not argument:category='INCOMPLETE_OR_UNCERTAIN'
            else:category='SYMBOLIC_OR_COMPUTED'
            counts[category]=counts.get(category,0)+1
            findings.append({**provenance,'api':match.group(1),'classification':category,
                             'literal_target_mapid':int(argument) if argument.isdigit() else None,
                             'argument_kind':'NUMERIC' if argument.isdigit() else 'NON_LITERAL',
                             'line_number':script.count('\n',0,match.start())+1,
                             'code_executed':False})


def analyze_calls(game, a04_report):
    """Heuristic triage only, scope mapped in output; no scripts are executed."""
    findings=[];counts={'text_sections_scanned':0,'skipped_entries':0,'findings_truncated':0}
    data=a04.directory_root(game)
    row=next((m for m in a04_report['sources']['DECADES']['maps'] if m['id']==1),None)
    if row is None:deny('Sem Map001')
    raw=a07.limited_read(data/row['source_filename'],MAX_READ)
    if hashlib.sha256(raw).hexdigest()!=row['sha256']:deny('Map001 alterado')
    map1=loads(raw)
    for eid in (1,2):
        for pn,page in enumerate(fields(fields(map1).get('@events',{}).get(eid)).get('@pages',[]),1):
            for ci,cmd in enumerate(fields(page).get('@list',[])):
                c=fields(cmd)
                if c.get('@code') in (355,655):
                    params=c.get('@parameters',[])
                    if isinstance(params,list) and params:
                        analyze_snippet(params[0],{'source_type':'MAP001','event_id':eid,'page_index':pn,'command_index':ci},findings,counts)
    scripts=data/'Scripts.rxdata'
    status='NOT_FOUND'
    total=0;entries=0;errors=[]
    if scripts.exists() or scripts.is_symlink():
        try:
            root=loads(a07.limited_read(scripts,MAX_READ))
            if not isinstance(root,list) or len(root)>3000:deny('Scripts.rxdata invalido')
            status='INERT_PARTIAL_OR_FULL_SCAN'
            for i,item in enumerate(root):
                if not isinstance(item,list) or len(item)<3 or not isinstance(item[2],bytes):
                    errors.append({'script_entry':i,'error':'UNSUPPORTED_FORMAT'});continue
                try:
                    decoder=zlib.decompressobj()
                    value=decoder.decompress(item[2],MAX_SCRIPT_PER_ENTRY+1)
                    if not decoder.eof or decoder.unconsumed_tail or decoder.unused_data or len(value)>MAX_SCRIPT_PER_ENTRY:
                        raise ValueError('INCOMPLETE_OR_TOO_LARGE')
                    total+=len(value)
                    if total>MAX_SCRIPT_TOTAL:raise ValueError('TOTAL_LIMIT')
                    entries+=1
                    analyze_snippet(value,{'source_type':'SCRIPTS_RXDATA','script_entry':i},findings,counts)
                except (zlib.error,ValueError,TypeError) as exc:
                    errors.append({'script_entry':i,'error':str(exc)[:80]})
            if errors:status='PARTIAL_SCAN_ERRORS'
        except (ValueError,OSError,TypeError,IndexError,RecursionError) as exc:
            status='BLOCKED_SCRIPTS_FILE';errors.append({'error':str(exc)[:120]})
    return {'scope':'MAP001_EVENTS_1_2_AND_SCRIPTS_RXDATA','scripts_rxdata_status':status,
            'script_entries_decoded':entries,'api_findings':findings,'classification_counts':counts,
            'scan_errors':errors[:MAX_EVIDENCE], 'scan_error_count':len(errors),
            'all_dynamic_destinations_covered':False,'ruby_executed':False}


def manifest_claims(game):
    evidence=a08.local_proofs(game)
    manifests=[]
    data=a04.directory_root(game)
    for info in evidence['manifests']:
        name=info['file'];entry={'filename':name,'status':info['status'],
            'candidate_overlap_ids':info.get('candidate_overlap_ids',[]),
            'recognized_destination_id_count':info.get('recognized_destination_id_count')}
        if info.get('sha256'):entry['sha256']=info['sha256']
        if info['status'] not in ('NOT_FOUND_NOT_PROOF','READ_OR_SCHEMA_ERROR'):
            try:
                raw=a08.read_json(data/name)
                # Diagnostic indicators are not approved future claims.
                entry['top_level_keys']=sorted(str(x)[:60] for x in raw.keys())[:40]
            except (ValueError,OSError,TypeError):
                entry['top_level_keys']=[]
        manifests.append(entry)
    return {'files':manifests,'observed_candidate_collisions':evidence['observed_candidate_overlaps'],
            'missing_or_unrecognized_coverage':evidence['manifest_coverage_incomplete'],
            'installer_code_or_future_claims_executed':False,
            'all_future_reserved_ids_known':False}


def audit(game:Path,project:Path,a04_report:dict,a06_report:dict,a07_report:dict,a08_report:dict):
    game=a04.safe_path(game);project=a04.safe_path(project)
    digest=a04_report.get('sources',{}).get('DECADES',{}).get('mapinfos_sha256')
    if (not digest or a04_report.get('phase')!='A04' or a06_report.get('phase')!='A06'
        or a07_report.get('phase')!='A07' or a08_report.get('phase')!='A08'
        or a06_report.get('mapinfos_sha256')!=digest
        or a07_report.get('mapinfos_sha256')!=digest
        or a08_report.get('mapinfos_sha256')!=digest
        or a07_report.get('review_errors_count')!=0
        or a08_report.get('status','').startswith('BLOCKED_A08_INCOMPLETE')):
        deny('Cadeia de auditoria A04 A06 A07 A08 incompleta ou incoerente')
    intro=intro_events(game,a04_report,a07_report,a08_report)
    calls=analyze_calls(game,a04_report)
    manifests=manifest_claims(game)
    unova=set(range(518,600))
    occupied=set(a04_report.get('observed_or_declared_occupied_map_ids',[]))
    problems=[]
    if not intro['mapid3_origin_matches_a07']:problems.append('MAP001_A07_MISMATCH')
    if intro['static_transfer_to_mapid3_count'] and 3 not in occupied:problems.append('MAPID_3_UNRESOLVED_INTRO_DESTINATION')
    if occupied&unova:problems.append('BLOCK_518_599_OBSERVED_OCCUPIED')
    if manifests['observed_candidate_collisions']:problems.append('INSTALLER_MANIFEST_OVERLAP_CANDIDATES')
    if manifests['missing_or_unrecognized_coverage']:problems.append('INSTALLER_MANIFEST_COVERAGE_INCOMPLETE')
    if calls['scan_error_count']:problems.append('SCRIPT_SCAN_PARTIAL_ERRORS')
    if calls['classification_counts'].get('SYMBOLIC_OR_COMPUTED',0):problems.append('COMPUTED_TRANSFERS_REQUIRE_MANUAL_REVIEW')
    problems+=intro['findings']
    return {'schema':1,'phase':'A09','region':'UNOVA',
        'mode':'INERT_INTRO_AND_INSTALLER_TRIAGE',
        'status':'REVIEW_REQUIRED_NO_RESERVATION',
        'mapinfos_sha256':digest,
        'intro_event_evidence':intro,
        'script_transfer_triage':calls,
        'manifest_provenance':manifests,
        'candidate_518_599_observed_occupied':sorted(occupied&unova),
        'candidate_518_599_physically_vacant_in_this_snapshot':not bool(occupied&unova),
        'followup_review_flags':sorted(set(problems)),
        'future_installer_claims_certified':False,
        'script_scan_exhaustive':False,'runtime_intro_proven_safe':False,
        'mapid3_repaired':False,'all_mapid_references_certified':False,
        'can_reserve_mapids':False,'can_install':False,
        'mapids_allocated':False,'game_exe_tested':False,'android_tested':False,
        'game_or_saves_modified':False,'bar_a_completed':0,'bar_a_total':8}


def save(project:Path,report:dict):
    project=a04.safe_path(project)
    for folder in (project/'.blue-work',project/'.blue-work/unova',project/OUT):
        if folder.is_symlink() or (folder.exists() and not folder.is_dir()):
            deny('Caminho de relatorio inseguro')
        folder.mkdir(exist_ok=True)
    raw=(json.dumps(report,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode('utf-8')
    dest=project/OUT/('a09-intro-claims-'+hashlib.sha256(raw).hexdigest()[:16]+'.json')
    if dest.is_symlink():deny('Arquivo symlink de relatorio')
    if dest.exists():
        if dest.read_bytes()!=raw:deny('Nao sobrescrever evidencia divergente')
    else:
        with dest.open('xb') as output:output.write(raw)
    return dest
