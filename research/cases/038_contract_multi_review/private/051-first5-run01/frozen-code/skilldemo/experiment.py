"""Frozen, isolated first-five-stage experiments; no model-driven repair or adoption."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import sys
import time
from urllib.parse import urlsplit, urlunsplit

from .runtime import digest

VERSION = 'first5-experiment-v1'
INITIALIZATION = {'status':'KNOWN_NONE', 'basis':'User confirmed the historical enterprise agent had no skills; not inferred from absent receipts.'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def file_sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1024*1024),b''):value.update(chunk)
    return value.hexdigest()


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)


def select_source(case):
    """Use manual index solely as an allowlist; reconstruct pairs downstream from events."""
    case = Path(case)
    selection = json.loads((case/'recovered_trajectories.json').read_text(encoding='utf-8'))
    selected = [s for s in selection if s.get('split') == 'generation']
    if not selected: raise ValueError('No generation sessions selected')
    sessions = [s['sessionId'] for s in selected]
    if len(set(sessions)) != len(sessions): raise ValueError('Duplicate selected session')
    selected_ids = []
    for session in selected:
        ids = [i for t in session['turns'] for i in [t['userMessageId'], *t['assistantMessageIds']]]
        if len(ids) != session['sourceMessageCount']: raise ValueError('Selection count mismatch')
        selected_ids.extend(ids)
    if len(set(selected_ids)) != len(selected_ids): raise ValueError('Duplicate selected message')
    allowed = set(selected_ids)
    index_rows = json.loads((case/'source_index.json').read_text(encoding='utf-8'))
    index = {r['messageId']:r for r in index_rows}
    if len(index) != len(index_rows): raise ValueError('Duplicate source-index message')
    rows, provenance, seen = [], [], set()
    for raw in (case/'private/raw_messages.jsonl').read_bytes().splitlines():
        if not raw.strip(): continue
        row = json.loads(raw)
        if row['id'] not in allowed: continue
        if row['id'] in seen: raise ValueError('Duplicate selected raw message')
        seen.add(row['id'])
        meta = index.get(row['id'])
        if not meta or meta['sessionId'] != row['sessionId'] or row['sessionId'] not in sessions:
            raise ValueError('Selected source identity mismatch')
        if sha(raw) != meta['rawLineSha256'] or sha((row.get('content') or '').encode()) != meta['contentSha256']:
            raise ValueError('Selected source hash mismatch: '+row['id'])
        if meta['role'] != row['role'] or not isinstance(row.get('content'),str):
            raise ValueError('Missing body or role mismatch: '+row['id'])
        files = (row.get('rawPayload') or {}).get('files') or []
        attachments = [{'name':f.get('name',f.get('fileName','unknown')) if isinstance(f,dict) else 'unknown',
                        'available':False,'basis':'EXPORT_METADATA_ONLY'} for f in files]
        rows.append({k:row.get(k) for k in ('id','sessionId','role','content','status')} |
                    {'sourceOrder':meta['sourceLine'],'sourceTimestamp':meta.get('userCreatedAt'),
                     'orderBasis':'SOURCE_JSONL_ROW','attachments':attachments})
        provenance.append({k:meta.get(k) for k in ('messageId','sessionId','sourceLine','role','rawLineSha256','contentSha256','userCreatedAt')})
    if seen != allowed: raise ValueError('Selected message body missing')
    rows.sort(key=lambda r:(r['sessionId'],r['sourceOrder']))
    provenance.sort(key=lambda r:(r['sessionId'],r['sourceLine']))
    for sid in sessions:
        orders = [r['sourceOrder'] for r in rows if r['sessionId']==sid]
        if len(orders)!=len(set(orders)): raise ValueError('Ambiguous source order')
    descriptor = {'sessionIds':sorted(sessions),'messageIds':[r['id'] for r in rows],
                  'eventCount':len(rows),'userCount':sum(r['role']=='user' for r in rows),
                  'assistantCount':sum(r['role']=='assistant' for r in rows),'eventHash':digest(rows),
                  'selectedProvenance':provenance,'selectionFieldsUsed':['split','sessionId','sourceMessageCount','turns.userMessageId','turns.assistantMessageIds'],
                  'manualLabelsImported':False,'holdoutBodiesImported':False}
    return rows, descriptor


def source_fingerprint(demo):
    demo = Path(demo)
    files = sorted((demo/'skilldemo').glob('*.py')) + [demo/'scripts/run_038_first5.py']
    return {p.relative_to(demo).as_posix():sha(p.read_bytes()) for p in files if p.is_file()}


def runtime_fingerprint(demo):
    """Record only allowlisted, non-secret configuration and installed runtime hashes."""
    demo = Path(demo)
    base = urlsplit(os.getenv('DEMO_BASE_URL','https://api.openai.com/v1'))
    host=(base.hostname or '')+(':'+str(base.port) if base.port else '')
    endpoint = urlunsplit((base.scheme,host,base.path,'',''))
    config = {k:os.getenv(k) for k in ('DEMO_MODEL','DEMO_MODEL_API','DEMO_NETWORK_MODE','DEMO_DETECT_TIMEOUT','DEMO_AGENT_TIMEOUT','DEMO_OPENCLAW_TIMEOUT')}
    config['baseUrl'] = endpoint
    config['temperature'] = 0
    config['python'] = sys.version
    config['platform'] = platform.platform()
    paths = ['.runtime/launcher.json','.runtime/package-lock.json','.runtime/node_modules/openclaw/package.json',
             '.runtime/node_modules/openclaw/openclaw.mjs','scripts/patch_openclaw_windows.py',
             '.runtime/node_modules/openclaw/skills/skill-creator/SKILL.md',
             '.runtime/node_modules/openclaw/skills/skill-creator/scripts/package_skill.py',
             '.runtime/node_modules/openclaw/skills/skill-creator/scripts/quick_validate.py']
    if os.name=='nt':paths.append('.runtime/node_modules/openclaw/dist/child-hDIQtCC4.mjs')
    missing=[p for p in paths if not (demo/p).is_file()]
    if missing:raise ValueError('Required local runtime dependencies missing: '+', '.join(missing))
    config['runtimeFiles'] = {p:file_sha(demo/p) for p in paths}
    command=(json.loads(os.environ['DEMO_OPENCLAW_COMMAND']) if os.getenv('DEMO_OPENCLAW_COMMAND') else
             json.loads((demo/'.runtime/launcher.json').read_text(encoding='utf-8'))['command'])
    if not isinstance(command,list) or not command or not all(isinstance(v,str) for v in command):
        raise ValueError('Invalid OpenClaw launcher command')
    executable=Path(command[0]) if Path(command[0]).is_file() else Path(shutil.which(command[0]) or '')
    if not executable.is_file():raise ValueError('Configured Node/OpenClaw executable missing')
    config['launcherFiles']={str(Path(p).resolve()):file_sha(p) for p in command if Path(p).is_file()}
    config['launcherFiles'][str(executable.resolve())]=file_sha(executable)
    config['pythonExecutable']={'path':sys.executable,'sha256':file_sha(sys.executable)}
    if not os.getenv('DEMO_MODEL') or not os.getenv('DEMO_API_KEY'):
        raise ValueError('Configured model/API credential missing; key is never written to manifest')
    from . import runtime
    if hasattr(runtime,'request_config'):
        config['requests']={purpose:runtime.request_config(purpose) for purpose in
                            ('detect_pairs','recover_trace','workflow_extract','workflow_merge','workflow_creator')}
    return config


def make_manifest(source, code, runtime, daily_limit=12, max_candidates=3):
    if daily_limit < 1 or max_candidates < 1: raise ValueError('Positive experiment limits required')
    fixed = {'schemaVersion':VERSION,'source':source,'codeFiles':code,'runtime':runtime,
             'actor':'alice','initialization':INITIALIZATION,
             'protocol':{'dailyDispatchLimit':daily_limit,'maxCandidates':max_candidates,
                 'candidateSelection':'All approved NEW workflows ordered by candidate ID; stop PARTIAL when the fixed cap excludes any.',
                 'maxOuterDispatchAttemptsPerRequest':1,'onFailure':'STOP_AND_PRESERVE; no automatic host repair/retry',
                 'internalAgentRequests':'Creator may use multiple model/tool turns and runtime retries; count all observed starts and usage.',
                 'resume':'Only identical manifest and persisted completed/QUEUED work; no historic DB import',
                 'adopt':False,'organizationPublish':False,'settleSeconds':0,'poolWaitSeconds':0}}
    return {**fixed,'manifestHash':digest(fixed)}


@contextmanager
def exclusive_run(data):
    """OS-owned lock is released on process death; a leftover file is not a stale lock."""
    data = Path(data); data.mkdir(parents=True,exist_ok=True)
    # Use the very same directory lock as server.serve: no active research
    # console can silently share a formally frozen experiment database.
    with (data/'server.lock').open('a+b') as stream:
        stream.seek(0); stream.write(b'0'); stream.flush(); stream.seek(0)
        if os.name == 'nt':
            import msvcrt
            try: msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            except OSError as exc: raise RuntimeError('Another experiment or server owns this directory') from exc
        else:
            import fcntl
            fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        try: yield
        finally:
            stream.seek(0)
            if os.name == 'nt': msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else: fcntl.flock(stream.fileno(),fcntl.LOCK_UN)


def freeze(data, manifest):
    data = Path(data); data.mkdir(parents=True,exist_ok=True)
    target = data/'manifest.json'
    if target.exists():
        old = json.loads(target.read_text(encoding='utf-8'))
        if old != manifest: raise ValueError('MANIFEST_CHANGED: use a new run directory; existing evidence is preserved')
    else:
        if (data/'loop.sqlite').exists(): raise ValueError('UNOWNED_DATABASE: never import or reuse a historical database')
        write_json(target,manifest)


def checkpoints(data, state):
    projections = {
        1:('pairs','intakes'),2:('pairAnnotations','pairDetections','stageStatus'),
        3:('traces','recoveries','stageStatus'),4:('workflows','learningDecisions','pools','workflowStatuses'),5:('candidates',)}
    for stage, keys in projections.items():
        write_json(Path(data)/f'stage-{stage}.json',{k:state.get(k,[]) for k in keys})
    write_json(Path(data)/'model-runs.json',state.get('runs',[]))
    write_json(Path(data)/'request-states.json',state.get('requestStates',{}))


def experiment_state(loop):
    state=loop.snapshot('alice')
    with loop.store.tx() as db:
        state['workflowStatuses']=loop.store.rows(db,'stage4_status','alice')
        state['requestStates']={kind:loop.store.rows(db,kind,'alice') for kind in
                              ('front_analysis_request','workflow_analysis_request','front_analysis','workflow_analysis')}
    return state


def stage_checks(state, source):
    pairs = state.get('pairs',[])
    statuses = state.get('stageStatus',[])
    traces = [t for t in state.get('traces',[]) if t.get('state')!='SUPERSEDED']
    trace_ids = {t['id'] for t in traces}
    workflows = [w for w in state.get('workflows',[]) if w.get('action')=='NEW']
    candidates = [c for c in state.get('candidates',[]) if c.get('workflowId') and c.get('action')=='NEW']
    checks = {
        '1':{'exactSourceMessageCoverage':{i for p in pairs for i in p.get('sourceMessageIds',[])}==set(source['messageIds']),
             'onePairPerUser':len(pairs)==source['userCount'],
             'allContentReadable':bool(pairs) and all(p['contentStatus']=='READABLE' for p in pairs),
             'noOrphans':all(not i.get('unassignedEvents') for i in state.get('intakes',[])),
             'onlySelectedSessions':{p['session'] for p in pairs}==set(source['sessionIds'])},
        '2':{'allSessionsAnnotated':len(statuses)==len(source['sessionIds']) and all(s.get('stage2')=='ANNOTATED' for s in statuses),
             'everyPairAnnotated':{a['pairId'] for a in state.get('pairAnnotations',[])}=={p['id'] for p in pairs}},
        '3':{'allSessionsRecovered':len(statuses)==len(source['sessionIds']) and all(s.get('stage3')=='RECOVERED' for s in statuses),
             'hasTaskTraces':bool(traces),'onlyGenerationSources':all(t.get('purposeSplit')=='generation' and t['session'] in source['sessionIds'] for t in traces),
             'businessOutcomeNotInvented':all(t.get('businessOutcome')=='UNKNOWN' for t in traces)},
        '4':{'hasApprovedNewWorkflow':bool(workflows),'hasMethodLedger':bool(state.get('learningDecisions')) and all(d.get('methodLedger') and d.get('analysisId') for d in state.get('learningDecisions',[])),
             'sameRunTraceSources':bool(workflows) and all(w.get('sourceRefs') and {r['id'] for r in w['sourceRefs']}<=trace_ids for w in workflows),
             'everyTraceHasDecision':bool(traces) and all(t.get('decision') for t in traces),
             'candidatePerNewWorkflow':{c['workflowId'] for c in candidates}=={w['id'] for w in workflows}},
        '5':{'allNewCandidatesReady':bool(candidates) and all(c.get('status')=='READY' for c in candidates),
             'allCreatorReadsObserved':bool(candidates) and all(c.get('validation',{}).get('creatorRead',{}).get('status')=='FILE_READ' for c in candidates),
             'allOfficialPackagesVerified':bool(candidates) and all(c.get('validation',{}).get('officialPackage',{}).get('status')=='PASS' for c in candidates),
             'noAutomaticAdoptionOrPublication':not state.get('skills') and not state.get('submissions')}}
    return checks


def export_deliverables(data, state):
    from .creator import verify_archive
    result = []
    for candidate in state.get('candidates',[]):
        if candidate.get('status')!='READY' or not candidate.get('workflowId'): continue
        work = Path(data)/'workspaces'/candidate['runId']
        verify_archive(work,candidate['package'],candidate['files'])
        dest = Path(data)/'deliverables'/candidate['id']
        hashes = {}
        for item in candidate['files']:
            path = dest/item['path']
            if not path.resolve().is_relative_to(dest.resolve()): raise ValueError('Illegal delivery path')
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(item['content'].encode('utf-8'))
            hashes[item['path']] = sha(path.read_bytes())
        archive = dest/(candidate['id']+'.skill')
        shutil.copyfile(work/candidate['package']['path'],archive)
        result.append({'candidateId':candidate['id'],'workflowId':candidate['workflowId'],
                       'files':hashes,'archive':str(archive.resolve()),'archiveSha256':sha(archive.read_bytes()),
                       'canonicalContentHash':digest(hashes),'status':'READY'})
    return result


def execute_experiment(data, events, manifest, loop_factory, preflight_only=False, progress=None, final_manifest=None):
    """One fresh database for stages 1→5. Factory injection permits free, real-host controls."""
    data = Path(data); progress = progress or (lambda message:None)
    with exclusive_run(data):
        freeze(data,manifest)
        if digest(events)!=manifest['source']['eventHash']: raise ValueError('INPUT_CHANGED after preflight')
        if preflight_only:
            result={'status':'PREFLIGHT_PASSED','manifestHash':manifest['manifestHash'],'paidCalls':0,
                    'sourceEventCount':len(events),'sessions':manifest['source']['sessionIds']}
            write_json(data/'preflight-summary.json',result)
            return result
        prior_path=data/'acceptance-summary.json'
        if prior_path.exists():
            prior=json.loads(prior_path.read_text(encoding='utf-8'))
            if prior.get('status') in ('FAILED','PARTIAL'):
                return {**prior,'resumeBlocked':'Terminal failed run preserved; new run required by maxAttempts=1 protocol'}
        loop=loop_factory(data)
        state=experiment_state(loop)
        if any(r.get('status') in ('RUNNING','UNKNOWN','FAILED') for r in state.get('runs',[])):
            result={'status':'FAILED','passed':False,'manifestHash':manifest['manifestHash'],
                    'error':'Interrupted or failed request preserved; no automatic redispatch','metrics':state.get('metrics')}
            checkpoints(data,state); write_json(prior_path,result); return result
        phase='1'; error=None; partial=False
        try:
            progress('Stage 1: selected raw source events → readable QAPairs')
            for session in manifest['source']['sessionIds']:
                loop.import_events('alice',[r for r in events if r['sessionId']==session],'generation',manifest['initialization'])
            state=experiment_state(loop); checkpoints(data,state)
            if not all(stage_checks(state,manifest['source'])['1'].values()): raise ValueError('Stage 1 acceptance failed')
            phase='2/3'; progress('Stages 2/3: semantic task detection → recovered traces')
            loop.run_stages('alice',stop_on_failure=True)
            state=experiment_state(loop); checkpoints(data,state)
            checks=stage_checks(state,manifest['source'])
            if not all(checks['2'].values()) or not all(checks['3'].values()): raise ValueError('Stage 2/3 acceptance failed; inspect stage-2.json and stage-3.json')
            phase='4'; progress('Stage 4: semantic methods → clusters → frozen workflows')
            loop.discover('alice',stop_on_failure=True)
            state=experiment_state(loop); checkpoints(data,state)
            if not all(stage_checks(state,manifest['source'])['4'].values()): raise ValueError('Stage 4 acceptance failed; inspect stage-4.json')
            phase='5'; candidates=sorted((c for c in state['candidates'] if c.get('workflowId') and c.get('action')=='NEW'),key=lambda c:c['id'])
            cap=manifest['protocol']['maxCandidates']; partial=len(candidates)>cap
            for candidate in candidates[:cap]:
                if candidate['status']=='QUEUED':
                    progress('Stage 5: generate and package '+candidate['id'])
                    created=loop.generate('alice',candidate['id'])
                    state=experiment_state(loop); checkpoints(data,state)
                    if created.get('status')!='READY': raise ValueError('Creator did not produce READY: '+candidate['id'])
                elif candidate['status']!='READY': raise ValueError('Persisted candidate is not resumable: '+candidate['id'])
            if partial: raise ValueError('Fixed candidate cap reached; remaining candidates preserved, not full acceptance')
        except Exception as exc:
            error=str(exc)[:1000]
        state=experiment_state(loop); checkpoints(data,state)
        checks=stage_checks(state,manifest['source']); deliverables=[]
        try: deliverables=export_deliverables(data,state)
        except Exception as exc: error=error or ('Delivery validation: '+str(exc)[:600])
        frozen_unchanged=True
        if final_manifest is not None:
            try:frozen_unchanged=final_manifest()==manifest
            except Exception as exc:
                frozen_unchanged=False;error=error or ('Final manifest verification: '+str(exc)[:600])
            if not frozen_unchanged:error=error or 'MANIFEST_CHANGED_DURING_RUN: input/code/runtime drift; this run is not accepted'
        passed=not error and all(all(c.values()) for c in checks.values())
        result={'status':'PASSED' if passed else 'PARTIAL' if partial else 'FAILED','passed':passed,
                'manifestHash':manifest['manifestHash'],'stoppedAt':None if passed else phase,'error':error,
                'frozenInputsCodeAndConfigUnchanged':frozen_unchanged,
                'checks':checks,'eventCount':len(events),'pairCount':len(state.get('pairs',[])),
                'traceCount':len([t for t in state.get('traces',[]) if t.get('state')!='SUPERSEDED']),
                'workflowCount':len(state.get('workflows',[])),'candidateStatuses':{c['id']:c['status'] for c in state.get('candidates',[])},
                'deliverables':deliverables,'metrics':state.get('metrics'),
                'privateRequestArtifacts':[{'runId':r['id'],
                    'request':str(Path('workspaces')/r['id']/'request.json'),
                    'response':str(Path('workspaces')/r['id']/'response.json')}
                    for r in state.get('runs',[]) if (data/'workspaces'/r['id']/'request.json').is_file()],
                'enterpriseOutcome':'UNKNOWN','professionalQuality':'NOT_EVALUATED',
                'adoptionOrPublication':False,'completedAt':time.time()}
        write_json(prior_path,result)
        integrity={p.name:sha(p.read_bytes()) for p in sorted(data.glob('stage-*.json'))}
        for name in ('model-runs.json','request-states.json','manifest.json','acceptance-summary.json'):
            integrity[name]=sha((data/name).read_bytes())
        write_json(data/'artifact-hashes.json',integrity)
        return result


def verify_saved_results(data):
    """Integrity replay only; clearly distinct from fresh model or validator replay."""
    data=Path(data)
    integrity=json.loads((data/'artifact-hashes.json').read_text(encoding='utf-8'))
    checks={name:sha((data/name).read_bytes())==expected for name,expected in integrity.items()}
    result=json.loads((data/'acceptance-summary.json').read_text(encoding='utf-8'))
    for delivery in result.get('deliverables',[]):
        archive=Path(delivery['archive'])
        checks[delivery['candidateId']+':archive']=sha(archive.read_bytes())==delivery['archiveSha256']
        for name,expected in delivery['files'].items():
            checks[delivery['candidateId']+':'+name]=sha((archive.parent/name).read_bytes())==expected
    return {'status':'PASS' if all(checks.values()) else 'FAILED','mode':'SAVED_ARTIFACT_INTEGRITY_ONLY',
            'checks':checks,'paidCalls':0,'originalAcceptance':result['status']}
