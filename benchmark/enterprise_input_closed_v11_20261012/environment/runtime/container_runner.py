"""Container-side native OpenClaw execution. Inputs are already task-scoped."""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import secrets
import signal
import sqlite3
import subprocess
import sys
import time
import uuid
from contextlib import closing

from consumer import (redact, skill_read_evidence, tool_result_summary, write_json,
                      validate_observation_seconds, OBSERVATION_ARCHIVE_RESERVE_SECONDS)
from openclaw_config import (build_openclaw_config, build_process_env, build_agent_argv,
                             build_trajectory_export_argv, build_gateway_argv,
                             build_gateway_health_argv)
from runtime_compat import configure_runtime_compat
from links_runtime import ResourceLinks, configure_skill_root_aliases
from runtime_support import configure as configure_builtin_support
from verify_public_delivery import verify_public_delivery
from public_publish import stop_public_delivery

PUBLIC_DELIVERY_SOURCE_ID = 'conv_60fd9245d56a'
PUBLIC_DELIVERY_RESERVE_SECONDS = 120
PUBLIC_DELIVERY_CLEANUP_RESERVE_SECONDS = 10


def public_delivery_required(raw):
    """Only the declared complete public-publishing source admits this hook."""
    initial = raw.get('context', {})
    context = dict(initial) if isinstance(initial, dict) else {}
    final_user_index = len(raw.get('followup_inputs', []))
    for entry in raw.get('turn_contexts', []):
        if entry.get('user_index') == final_user_index and isinstance(entry.get('context'), dict):
            context.update(entry['context'])
    declaration = context.get('source_public_delivery')
    if declaration is None:
        return False
    if not isinstance(declaration, dict):
        raise ValueError('Invalid source public delivery declaration')
    if declaration.get('required') is not True:
        return False
    if declaration.get('session_id') != PUBLIC_DELIVERY_SOURCE_ID:
        raise ValueError('Public delivery hook is limited to conv_60fd9245d56a')
    return True


def file_hashes(root):
    return {p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file() and not p.is_symlink()}


def declared_baseline_skills(resources, aliases, turn_resources=None):
    """Declared initial/late input bodies only; no discovery of generated skills."""
    expected={}
    candidates=[(r,0) for r in resources]
    for entry in turn_resources or []:
        candidates.extend((r,entry['user_index']) for r in entry['resources'])
    for resource,first in candidates:
        path=Path(resource['path'])
        mount=resource.get('mount',str(path)).removeprefix('/workspace/')
        parts=mount.split('/')
        if len(parts)!=3 or parts[0] not in ('skills','environment_skills') or parts[2]!='SKILL.md':continue
        body_path=Path(resource.get('source',resource['path']))
        if not body_path.is_file():continue
        body=body_path.read_bytes()
        if resource.get('sha256') and hashlib.sha256(body).hexdigest()!=resource['sha256']:
            raise ValueError('Declared baseline body hash mismatch')
        sid=parts[1];paths=[str(path)]
        if parts[0]=='skills':paths.append(str(Path('/workspace/.claude/skills')/sid/'SKILL.md'))
        for alias in aliases:
            if alias.get('target')==str(path.parent) and alias.get('changes_skill_bytes') is False:
                paths.append(str(Path(alias['path'])/'SKILL.md'))
        record={'path':str(path),'paths':paths,'content':body.decode('utf-8-sig'),
                'available_from_dispatch_index':first,'declared_input_only':True}
        if sid in expected and expected[sid]['content']!=record['content']:
            raise ValueError('Different baseline bodies share one declared skill name')
        expected[sid]=record
    return expected


def initialize_native_cron_seed(context, workspace, state, env, transport, *, run_command=subprocess.run):
    """Admit a declared synthetic cron input through the pinned native store API.

    OpenClaw 2026.9.5 stores cron partitions in SQLite. The jobs.json input is
    retained as evidence and its controlled partition is populated with the
    official saveCronStore API before the Gateway acquires state ownership.
    """
    seed=context.get('native_cron_seed') if isinstance(context,dict) else None
    if seed is None:return None
    if not isinstance(seed,dict) or seed.get('synthetic') is not True:
        raise ValueError('Native cron seed must explicitly be synthetic')
    workspace=Path(workspace).resolve();state=Path(state).resolve()
    source=Path(seed.get('path','')).resolve()
    if not source.is_relative_to(workspace/'inputs') or not source.is_file():
        raise ValueError('Native cron input must be a real workspace inputs file')
    expected=seed.get('sha256')
    if not isinstance(expected,str) or len(expected)!=64 or hashlib.sha256(source.read_bytes()).hexdigest()!=expected:
        raise ValueError('Native cron input SHA differs from frozen input')
    store=json.loads(source.read_text(encoding='utf-8-sig'))
    if store.get('version')!=1 or store.get('synthetic') is not True or not isinstance(store.get('jobs'),list) or not store['jobs']:
        raise ValueError('Native cron fixture must be a nonempty version 1 synthetic store')
    ids=[]
    for job in store['jobs']:
        if not isinstance(job,dict) or not isinstance(job.get('id'),str) or not job['id'] or job['id'] in ids:
            raise ValueError('Native cron input has an invalid or duplicate job ID')
        if job.get('agentId')!='eval' or job.get('enabled') is not False or job.get('sessionTarget')!='isolated':
            raise ValueError('Synthetic old cron must be disabled, isolated, and owned by eval')
        if job.get('payload',{}).get('kind')!='agentTurn' or job.get('delivery',{}).get('mode')!='none':
            raise ValueError('Synthetic cron must be an agentTurn without external delivery')
        ids.append(job['id'])
    if seed.get('job_ids')!=ids:raise ValueError('Declared native cron IDs differ from input')
    target=state/'cron'/'jobs.json'
    if target.exists():raise ValueError('Native cron state already initialized')
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
    # Immutable, pinned official module names; no user-supplied script or SQL.
    program="""
import fs from 'node:fs';
import { n as invalidJob } from '/opt/openclaw/lib/node_modules/openclaw/dist/persisted-shape-B7XsqkY-.mjs';
import { v as saveCronStore, s as loadCronStore } from '/opt/openclaw/lib/node_modules/openclaw/dist/store-DZlHo5vp.mjs';
const target=process.argv[1];
const input=JSON.parse(fs.readFileSync(target,'utf8'));
for (const job of input.jobs) { const reason=invalidJob(job); if(reason)throw Error('Invalid native cron job: '+reason); }
await saveCronStore(target,{version:1,jobs:input.jobs});
const actual=await loadCronStore(target);
if(actual.jobs.length!==input.jobs.length || actual.jobs.some((j,i)=>j.id!==input.jobs[i].id))throw Error('Native cron persistence mismatch');
console.log(JSON.stringify({native_api:'saveCronStore/loadCronStore',version:actual.version,job_ids:actual.jobs.map(j=>j.id),model_calls:0}));
"""
    proc=run_command(['node','--input-type=module','-e',program,str(target)],env=env,capture_output=True,timeout=60)
    Path(transport,'native_cron_seed.stdout.log').write_bytes(proc.stdout)
    Path(transport,'native_cron_seed.stderr.log').write_bytes(proc.stderr)
    if proc.returncode:raise RuntimeError('Pinned native cron store initialization failed')
    receipt={'synthetic':True,'historical_state_restored':False,'source_path':str(source),
             'source_sha256':expected,'store_partition':str(target),'job_ids':ids,
             'official_validation_and_persistence':parse_json_output(proc.stdout.decode('utf-8')),
             'enabled_initially':False,'model_calls':0,'initialized_before_gateway':True}
    write_json(Path(transport,'native_cron_seed_receipt.json'),receipt)
    return receipt


def parse_json_output(text):
    # Some pinned CLI plugins print a startup note before the final JSON object.
    decoder=json.JSONDecoder()
    for pos,char in enumerate(text):
        if char!='{': continue
        try:
            value,end=decoder.raw_decode(text[pos:])
            if isinstance(value,dict) and not text[pos+end:].strip(): return value
        except ValueError: pass
    raise RuntimeError('Native OpenClaw stdout did not end in a JSON object')


def redact_runtime(value, *secret_values):
    for secret_value in secret_values: value=redact(value,secret_value)
    return value


def stop_gateway(handle, *, grace_seconds=15):
    """Stop the single state owner before reading/exporting its SQLite store."""
    proc=handle['process'];forced=False
    if proc.poll() is None:
        proc.terminate()
        try: proc.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            forced=True
            if os.name=='posix':
                try: os.killpg(proc.pid,signal.SIGKILL)
                except ProcessLookupError: pass
            else: proc.kill()
            proc.wait(timeout=5)
    for stream in handle['streams']: stream.close()
    return {'returncode':proc.returncode,'forced_kill':forced}


def start_gateway(env, *, private_dir=Path('/tmp/openclaw-eval-gateway'),
                  ready_timeout=90, run_command=subprocess.run, popen=subprocess.Popen):
    """Foreground Gateway in this container; authenticated native health probe.

    There is no embedded fallback.  Probe and service logs stay in container
    private_dir until the caller has stopped the process and redacted them.
    """
    private_dir=Path(private_dir);private_dir.mkdir(parents=True,exist_ok=False)
    streams=[(private_dir/(name+'.log')).open('wb') for name in ('stdout','stderr')]
    try:
        proc=popen(build_gateway_argv(),env=env,stdout=streams[0],stderr=streams[1],start_new_session=True)
    except Exception:
        for stream in streams: stream.close()
        raise
    handle={'process':proc,'streams':streams};deadline=time.monotonic()+ready_timeout;attempts=0
    try:
        with (private_dir/'health.log').open('wb') as log:
            while time.monotonic()<deadline:
                if proc.poll() is not None: raise RuntimeError('Native Gateway exited before readiness')
                attempts+=1
                try:
                    probe=run_command(build_gateway_health_argv(),env=env,capture_output=True,timeout=12)
                    log.write(probe.stdout+probe.stderr);log.flush()
                    if probe.returncode==0:
                        health=parse_json_output(probe.stdout.decode('utf-8',errors='replace'))
                        if health.get('ok') is True:
                            handle['readiness']={'attempts':attempts,'health_ok':True}
                            return handle
                except (subprocess.TimeoutExpired,RuntimeError,ValueError) as error:
                    log.write((type(error).__name__+' during readiness\n').encode());log.flush()
                time.sleep(0.25)
        raise RuntimeError('Native Gateway readiness deadline exceeded')
    except Exception:
        stop_gateway(handle)
        raise


def export_gateway_logs(private_dir, transport, *secret_values):
    for file in Path(private_dir).glob('*.log'):
        (transport/('gateway.'+file.name)).write_text(
            redact_runtime(file.read_text(encoding='utf-8',errors='replace'),*secret_values),encoding='utf-8')


def select_session_key(listing, session_id):
    """Match the requested native id, rather than taking the latest session."""
    rows=listing.get('sessions')
    if not isinstance(rows,list): raise RuntimeError('Native sessions list omitted sessions array')
    keys={row.get('key') for row in rows if isinstance(row,dict)
          and row.get('sessionId')==session_id and isinstance(row.get('key'),str)}
    if len(keys)!=1: raise RuntimeError('Native session id did not resolve to exactly one stored key')
    return next(iter(keys))


def export_native_session(session_id, env, transport, secret, *,
                          export_workspace=Path('/tmp/export-workspace'), run_command=subprocess.run):
    """Export the native redacted support bundle inside the disposable container.

    The official exporter emits events.jsonl and session-branch.json.  Its
    events wrap transcript messages in data.message, so the existing read
    bundle's diagnostic sanitization can alter content and must not replace the
    complete transcript read from SQLite below.  Raw exporter output is never
    written to a host bind mount; only native-redacted, additionally key-redacted
    text is copied after the command completes.
    """
    secret_values=(secret,) if isinstance(secret,str) else tuple(secret)
    export_workspace=Path(export_workspace)
    export_workspace.mkdir(parents=True,exist_ok=False)
    listing_proc=run_command(['openclaw','sessions','--agent','eval','--json'],
                             env=env,capture_output=True,timeout=35)
    listing_stdout=listing_proc.stdout.decode('utf-8',errors='replace')
    (transport/'sessions.stdout.log').write_text(redact_runtime(listing_stdout,*secret_values),encoding='utf-8')
    (transport/'sessions.stderr.log').write_text(redact_runtime(listing_proc.stderr.decode('utf-8',errors='replace'),*secret_values),encoding='utf-8')
    if listing_proc.returncode: raise RuntimeError('Native OpenClaw sessions listing failed')
    listing=parse_json_output(listing_stdout)
    session_key=select_session_key(listing,session_id)
    argv=build_trajectory_export_argv(session_key,workspace=str(export_workspace),output_name='trajectory')
    proc=run_command(argv,env=env,capture_output=True,timeout=55)
    stdout=proc.stdout.decode('utf-8',errors='replace')
    (transport/'export.stdout.log').write_text(redact_runtime(stdout,*secret_values),encoding='utf-8')
    (transport/'export.stderr.log').write_text(redact_runtime(proc.stderr.decode('utf-8',errors='replace'),*secret_values),encoding='utf-8')
    if proc.returncode: raise RuntimeError('Native OpenClaw trajectory export failed')
    summary=parse_json_output(stdout)
    if summary.get('sessionId')!=session_id:
        raise RuntimeError('Native trajectory export returned a different session id')
    source=export_workspace/'.openclaw'/'trajectory-exports'/'trajectory'
    if Path(summary.get('outputDir','')).resolve()!=source.resolve():
        raise RuntimeError('Native trajectory export escaped the private container output directory')
    branch_path=source/'session-branch.json'
    events_path=source/'events.jsonl'
    if not branch_path.is_file() or not events_path.is_file():
        raise RuntimeError('Native trajectory bundle omitted branch or event evidence')
    branch=json.loads(branch_path.read_text(encoding='utf-8'))
    entries=branch.get('entries')
    if not isinstance(entries,list) or not entries:
        raise RuntimeError('Native trajectory contains no branch entries')
    if not any(isinstance(entry,dict) and entry.get('type')=='message' for entry in entries):
        raise RuntimeError('Native trajectory branch contains no messages')
    evidence_dir=transport/'evidence';evidence_dir.mkdir(exist_ok=False)
    copied=[]
    for file in sorted(source.rglob('*')):
        if file.is_symlink(): raise RuntimeError('Native trajectory bundle contains a symlink')
        if not file.is_file(): continue
        relative=file.relative_to(source)
        dest=evidence_dir/relative;dest.parent.mkdir(parents=True,exist_ok=True)
        dest.write_text(redact_runtime(file.read_text(encoding='utf-8'),*secret_values),encoding='utf-8')
        copied.append(relative.as_posix())
    return entries, {'session_key':session_key,'event_count':summary.get('eventCount'),
                     'runtime_event_count':summary.get('runtimeEventCount'),
                     'transcript_event_count':summary.get('transcriptEventCount'),
                     'files':copied,'source':'native_sessions_export_trajectory'}


def load_native_session_events(state_dir, session_id, *, agent_id='eval'):
    """Read immutable native transcript events through a read-only connection.

    Official support export always applies diagnostic JSON sanitizers.  Those
    can replace valid natural language mixed with JSON with a placeholder.  We
    therefore preserve the runtime's event_json itself, selecting only this
    attempt's session_id and ordering by its stored sequence.  No role, tool
    call, reply pairing, deduplication, or active-branch reconstruction is added.
    The caller applies exact key/token redaction before writing to the host.
    """
    state_dir=Path(state_dir).resolve()
    database=state_dir/'agents'/agent_id/'agent'/'openclaw-agent.sqlite'
    if database.is_symlink() or not database.is_file():
        raise RuntimeError('Native agent SQLite transcript database is missing')
    if not database.resolve().is_relative_to(state_dir):
        raise RuntimeError('Native SQLite database escaped the attempt state directory')
    with closing(sqlite3.connect(database.resolve().as_uri()+'?mode=ro',uri=True)) as connection:
        connection.execute('PRAGMA query_only=ON')
        columns={row[1] for row in connection.execute('PRAGMA table_info(transcript_events)')}
        if not {'session_id','seq','event_json'}.issubset(columns):
            raise RuntimeError('Pinned native transcript_events schema is incompatible')
        user_version=connection.execute('PRAGMA user_version').fetchone()[0]
        rows=connection.execute('SELECT seq,event_json FROM transcript_events WHERE session_id=? ORDER BY seq',
                                (session_id,)).fetchall()
    if not rows: raise RuntimeError('Native SQLite contains no transcript for the requested session id')
    entries=[]
    for sequence,text in rows:
        event=json.loads(text)
        if not isinstance(event,dict): raise RuntimeError('Native transcript event_json is not an object')
        entries.append(event)
    messages=[event for event in entries if event.get('type')=='message']
    if not messages: raise RuntimeError('Native SQLite transcript contains no messages')
    return entries,{'source':'native_sqlite_transcript_events.event_json','read_only':True,
                    'session_id':session_id,'agent_id':agent_id,'user_version':user_version,
                    'rows':len(rows),'message_rows':len(messages),'first_seq':rows[0][0],'last_seq':rows[-1][0],
                    'redaction':'exact_model_key_and_gateway_token_only',
                    'scope':'all_persisted_native_events_for_this_session_in_seq_order'}


def episode_messages(first_message, followup_inputs):
    if not isinstance(followup_inputs,list) or any(not isinstance(text,str) or not text.strip() for text in followup_inputs):
        raise ValueError('followup_inputs must be a list of nonempty user strings')
    return [first_message,*followup_inputs]


def observe_runtime(handle, seconds, env, transport, secret_values, *, deadline,
                    run_command=subprocess.run, monotonic=time.monotonic, sleep=time.sleep):
    """Keep this Gateway alive after the last answer, then archive native cron.

    The finite window is part of the same attempt deadline. Evidence reports
    observations, not success of every scheduled job or service after teardown.
    Initial job ids survive auto-deletion of one-shot jobs in the final list.
    """
    seconds=validate_observation_seconds(seconds)
    start=monotonic();record={'requested_seconds':seconds,'status':'disabled' if not seconds else 'running',
                            'job_ids':[],'history_limit_per_job':100,'commands':[],
                            'scope':'same_container_gateway_after_final_answer_before_teardown'}
    transport=Path(transport);transport.mkdir(parents=True,exist_ok=True)
    def alive():
        if handle['process'].poll() is not None:
            raise RuntimeError('Native Gateway exited during post-answer observation')
        if monotonic()>=deadline:
            raise RuntimeError('Episode deadline exhausted during runtime observation')
    def cli(label,args):
        alive();remaining=deadline-monotonic()
        try:
            proc=run_command(['openclaw',*args],env=env,capture_output=True,timeout=min(15,remaining))
        except subprocess.TimeoutExpired as error:
            for suffix,value in (('stdout',error.stdout),('stderr',error.stderr)):
                text=value.decode('utf-8',errors='replace') if isinstance(value,bytes) else value or ''
                (transport/(label+'.'+suffix+'.log')).write_text(redact_runtime(text,*secret_values),encoding='utf-8')
            record['commands'].append({'label':label,'status':'timeout'})
            raise RuntimeError('Native cron evidence command exceeded observation deadline') from error
        for suffix,value in (('stdout',proc.stdout),('stderr',proc.stderr)):
            (transport/(label+'.'+suffix+'.log')).write_text(redact_runtime(value.decode('utf-8',errors='replace'),*secret_values),encoding='utf-8')
        record['commands'].append({'label':label,'returncode':proc.returncode})
        if proc.returncode:raise RuntimeError('Native cron evidence command failed: '+label)
        alive();value=parse_json_output(proc.stdout.decode('utf-8',errors='replace'))
        write_json(transport/(label+'.json'),redact_runtime(value,*secret_values))
        return value
    def job_ids(value):
        rows=value.get('jobs')
        if not isinstance(rows,list):raise RuntimeError('Native cron list omitted jobs array')
        ids=set()
        for job in rows:
            if not isinstance(job,dict) or not isinstance(job.get('id'),str) or not job['id']:
                raise RuntimeError('Native cron list contains invalid job id')
            ids.add(job['id'])
        return ids
    try:
        if not seconds:return record
        alive()
        if deadline-start < seconds + OBSERVATION_ARCHIVE_RESERVE_SECONDS:
            raise RuntimeError('Observation window and evidence reserve exceed remaining episode deadline')
        ids=job_ids(cli('cron_before',['cron','list','--all','--agent','eval','--json']))
        record['job_ids']=sorted(ids)
        until=start+seconds
        while monotonic()<until:
            alive();sleep(min(0.25,until-monotonic(),deadline-monotonic()))
        alive();record['observed_seconds']=monotonic()-start
        ids.update(job_ids(cli('cron_after',['cron','list','--all','--agent','eval','--json'])))
        record['job_ids']=sorted(ids)
        record['run_archives']=[]
        for index,job_id in enumerate(sorted(ids)):
            label=f'cron_runs_{index:04d}'
            cli(label,['cron','runs',job_id,'--limit','100','--json'])
            record['run_archives'].append({'job_id':job_id,'file':label+'.json'})
        record['status']='completed'
        return record
    except Exception as error:
        record.update(status='failed',error=redact_runtime(str(error),*secret_values))
        raise
    finally:
        record['elapsed_seconds']=monotonic()-start
        write_json(transport/'runtime_observation.json',redact_runtime(record,*secret_values))


def preserve_failure_events(state,session_id,transport,secret_values,receipt):
    """Keep already-persisted native history on failure, without claiming success."""
    if (transport/'session_events.jsonl').exists():return
    try:
        events,metadata=load_native_session_events(state,session_id)
        with (transport/'session_events.jsonl').open('w',encoding='utf-8',newline='\n') as out:
            for event in events:out.write(json.dumps(redact_runtime(event,*secret_values),ensure_ascii=False)+'\n')
        receipt['full_transcript_export']=metadata
        receipt['failure_trace_preserved']=True
    except Exception as error:
        receipt['failure_transcript_export_error']=redact_runtime(str(error),*secret_values)


def deliver_turn_resources(entries, user_index, workspace, transport):
    delivered=[];workspace=Path(workspace).resolve();transport=Path(transport).resolve()
    for entry in entries:
        if entry['user_index']!=user_index: continue
        for resource in entry['resources']:
            source=Path(resource['source']).resolve();target=Path(resource['path']).resolve()
            if not source.is_relative_to(transport/'staged_inputs') or not source.is_file():
                raise ValueError('Staged source outside the explicit transport')
            if not target.is_relative_to(workspace) or target.relative_to(workspace).parts[0] in ('skills','learned_skills','runtime_links','outputs'):
                raise ValueError('Staged target must be a source-bound input inside the workspace')
            actual=hashlib.sha256(source.read_bytes()).hexdigest()
            if actual!=resource['sha256']: raise ValueError('Staged container input hash mismatch')
            before=hashlib.sha256(target.read_bytes()).hexdigest() if target.is_file() else None
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            delivered.append({'user_index':user_index,'path':str(target),'sha256':actual,'previous_sha256':before})
    return delivered


def render_context(value):
    if isinstance(value,str): return value
    if isinstance(value,dict): return json.dumps(value,ensure_ascii=False,indent=2)
    if isinstance(value,list) and all(isinstance(item,str) for item in value):return '\n\n'.join(value)
    raise ValueError('Explicit context must be text, text list, or structured object')


def validate_native_completion(data):
    meta=data.get('meta',{}) or {};completion=meta.get('completion',{}) or {}
    reason=meta.get('stopReason') or completion.get('finishReason') or completion.get('stopReason')
    if reason in ('length','max_tokens','token_limit'):
        raise RuntimeError('Native model output was truncated at its token limit; partial text is not completion')
    if meta.get('aborted'):raise RuntimeError('Native OpenClaw turn aborted')


def configure_registration_condition(config, env, context, workspace, text):
    adapter=Path('/opt/experiment-services/configure.py')
    if not adapter.is_file():return None
    import importlib.util
    spec=importlib.util.spec_from_file_location('experiment_cron_config',adapter)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.configure(config,env,context,workspace,active_user_text=text,adapter_root=str(adapter.parent))


def prepare_registration_targets(context, env, workspace, text):
    adapter=Path('/opt/experiment-services/configure.py')
    if not adapter.is_file() or not context.get('cron_neutral_old_job_condition'):return None
    import importlib.util
    spec=importlib.util.spec_from_file_location('experiment_cron_config',adapter)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.prepare_after_gateway(context,env,workspace,active_user_text=text,adapter_root=str(adapter.parent))


def prepare_meeting_choice_targets(context, env, workspace, text, *, dispatch_index,
                                   trial_id, transport, run_command=subprocess.run,
                                   timeout_seconds=60, secret_values=(),
                                   adapter_root=Path('/opt/experiment-services')):
    """Bridge a current explicit A/B reference after this turn's inputs arrive.

    Current-trial tool products take precedence. Missing referenced background
    is explicitly experimental; this hook never executes the keep/cancel action.
    """
    condition=context.get('meeting_choices_initialization')
    if not isinstance(condition,dict) or context.get('source_id')!='conv_5bff0ded32bc':return None
    admitted_index=condition.get('available_from_dispatch_index')
    if dispatch_index!=admitted_index:return None
    compact=re.sub(r'\s+','',text).upper()
    if not re.search(r'(?<!不)(?<!不要)(?<!别)(?<!勿)(?:保留B|删除A|取消A|KEEPB|DELETEA|CANCELA)',compact):return None
    workspace=Path(workspace).resolve();transport=Path(transport).resolve()
    fixture_path=Path(condition.get('fixture','')).resolve()
    if not fixture_path.is_relative_to(workspace/'inputs') or not fixture_path.is_file():
        raise ValueError('Current-turn meeting choice input has not been delivered inside workspace inputs')
    fixture=json.loads(fixture_path.read_text(encoding='utf-8-sig'))
    source=context['source_id']
    if fixture.get('source_id')!=source or fixture.get('synthetic') is not True or fixture.get('available_from_dispatch_index')!=dispatch_index:
        raise ValueError('Meeting choice fixture does not match the current source and dispatch')
    adapter=Path(adapter_root)/'prepare_meeting_choices.py'
    if not adapter.is_file():raise RuntimeError('Declared meeting choice preparation helper is absent')
    current_context=workspace/'service-context/tencent-meeting.json'
    if not current_context.is_file():raise ValueError('Source-scoped meeting context was not initialized')
    prior_context=json.loads(current_context.read_text(encoding='utf-8-sig'))
    if prior_context.get('source_id')!=source:raise ValueError('Meeting context belongs to another source')
    current_state=workspace/'.runtime-context/tencent-meeting-created.json'
    normalized_state=current_state;label_adaptations=[]
    # Actors need not attach experimental labels to their real service calls.
    # Infer a missing label only from a unique owned actual tool object whose
    # recurrence count matches the currently admitted historical reference.
    if current_state.is_file():
        prior=json.loads(current_state.read_text(encoding='utf-8-sig'))
        if prior.get('source_id')!=source:raise ValueError('Meeting tool products belong to another source')
        owned={str(mid) for mid in prior.get('created_ids',[])}
        objects=prior.get('created_objects',[])
        labelled={obj.get('label') for obj in objects if str(obj.get('meeting_id','')) in owned and obj.get('label') in ('A','B')}
        for option in fixture.get('options',[]):
            label=option.get('label')
            if label in labelled:continue
            candidates={str(obj['meeting_id']):obj for obj in objects
                        if str(obj.get('meeting_id','')) in owned and obj.get('label') not in ('A','B')
                        and obj.get('until_count')==option.get('until_count')}
            if label in ('A','B') and len(candidates)==1:
                obj=next(iter(candidates.values()));obj['label']=label
                label_adaptations.append({'meeting_id':str(obj['meeting_id']),'label':label,
                    'basis':'unique actual current-trial tool recurrence count matches current admitted reference'})
        unresolved={str(obj['meeting_id']):obj for obj in objects
                    if str(obj.get('meeting_id','')) in owned and obj.get('label') not in ('A','B')}
        if unresolved:
            references=[{key:obj.get(key) for key in ('meeting_id','meeting_code','until_count','subject')}
                        for obj in unresolved.values()]
            receipt={'source_id':source,'canonical_user_index':dispatch_index,'native_trial_id':trial_id,
                     'status':'current_trial_reference_requires_clarification','actual_native_helper_called':False,
                     'created_fallback_objects':0,'desired_user_action_not_executed':True,
                     'current_actor_produced_objects_preferred':True,'unresolved_current_objects':references,
                     'guide':'当前运行已经产生以下真实会议，尚不能唯一对应用户提到的A/B：\n'+json.dumps(references,ensure_ascii=False)+
                         '\n请根据你本次实际前轮工具结果确认对应关系，必要时向用户澄清。不得用历史候选覆盖这些产物，也不要另建候选或假装已执行保留／取消。'}
            write_json(transport/f'turn_{dispatch_index+1:04d}.meeting_choice_preparation.json',redact_runtime(receipt,*secret_values))
            return receipt
        if label_adaptations:
            normalized_state=workspace/'.runtime-context'/f'meeting-choice-owned-state-{dispatch_index:04d}.json'
            write_json(normalized_state,prior)
    safe_trial=hashlib.sha256(trial_id.encode('utf-8')).hexdigest()[:24]
    output=workspace/'.runtime-context'/'meeting-choices'/safe_trial/f'turn-{dispatch_index:04d}.json'
    if output.exists():raise ValueError('Meeting choice state has already been prepared for this exact native trial and turn')
    if timeout_seconds<1:raise RuntimeError('Episode deadline exhausted before current meeting reference preparation')
    argv=[sys.executable,str(adapter),'--fixture',str(fixture_path),'--dispatch-index',str(dispatch_index),
          '--output',str(output),'--trial-id',trial_id,'--current-state',str(normalized_state),
          '--current-context',str(current_context)]
    proc=run_command(argv,env=env,capture_output=True,timeout=timeout_seconds)
    prefix=f'turn_{dispatch_index+1:04d}.meeting_choice_preparation'
    for name,value in (('stdout',proc.stdout),('stderr',proc.stderr)):
        text_value=value.decode('utf-8',errors='replace') if isinstance(value,bytes) else value or ''
        (transport/(prefix+'.'+name+'.log')).write_text(redact_runtime(text_value,*secret_values),encoding='utf-8')
    if proc.returncode or not output.is_file():raise RuntimeError('Native current-turn meeting reference preparation failed')
    prepared=json.loads(output.read_text(encoding='utf-8-sig'))
    if (prepared.get('source_id')!=source or prepared.get('trial_id')!=trial_id
        or prepared.get('desired_user_action_not_executed') is not True
        or prepared.get('current_actor_produced_objects_preferred') is not True):
        raise ValueError('Meeting bridge output does not preserve current-trial object precedence')
    write_json(current_context,prepared)
    alias_guide=[{key:obj.get(key) for key in ('label','meeting_id','meeting_code','until_count')}
                 for obj in prepared.get('initial_meetings',[])]
    guide=('本次当前轮会议引用的本人实验对象映射：\n'+json.dumps(alias_guide,ensure_ascii=False)+
           '\n原会议号兼容映射：'+json.dumps(prepared.get('meeting_code_aliases',{}),ensure_ascii=False)+
           '\n本轮真实工具产物优先。缺少引用时补建的对象只是明确标注的历史引用实验背景，'
           '不表示你前轮已经创建了它们；保留或取消动作尚未执行，必须按当前用户要求调用真实工具。'
           '\n只保留B时，若映射中没有A，不要新建A。操作入口：python '+str(Path(adapter_root)/'meeting_source.py')+
           ' TOOL --source-id '+source+' --json-file 参数.json；使用映射中的本次meeting_id。'
           '\n实际状态文件：'+str(current_context))
    receipt={'source_id':source,'canonical_user_index':dispatch_index,'native_trial_id':trial_id,
             'original_input_sha256':hashlib.sha256(text.encode('utf-8')).hexdigest(),
             'fixture_sha256':hashlib.sha256(fixture_path.read_bytes()).hexdigest(),
             'context_path':str(current_context),'context_sha256':hashlib.sha256(current_context.read_bytes()).hexdigest(),
             'bridge_output':str(output),'actual_native_helper_called':True,'returncode':proc.returncode,
             'current_actor_objects_reused':prepared.get('current_actor_objects_reused'),
             'created_fallback_objects':prepared.get('created_fallback_objects'),
             'actual_owned_object_label_adaptations':label_adaptations,
             'desired_user_action_not_executed':True,'current_actor_produced_objects_preferred':True,
             'alias_guide':alias_guide,'guide':guide}
    write_json(transport/(prefix+'.json'),redact_runtime(receipt,*secret_values))
    return receipt


def prepare_same_episode_created_skill(context, workspace, transport, session_id, dispatch_index, phase):
    """Trusted source-level capture/alias; business skill bytes come from this actor."""
    if not isinstance(context,dict):return None
    key='same_episode_skill_creation' if dispatch_index==0 else 'same_episode_created_skill'
    if not isinstance(context.get(key),dict) or context[key].get('required') is not True:return None
    adapter=Path('/opt/experiment-services/produced_skill_bridge.py')
    if not adapter.is_file():raise RuntimeError('Declared current-episode skill bridge is missing')
    import importlib.util
    spec=importlib.util.spec_from_file_location('current_episode_skill_bridge',adapter)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.handle_turn(context,workspace,transport,session_id,dispatch_index,phase)
    if result is not None:
        write_json(Path(transport)/f'turn_{dispatch_index+1:04d}.episode_created_skill.{phase}.json',result)
    return result


def prepare_same_episode_created_output(context, workspace, transport, session_id, dispatch_index, phase):
    """A later attached-file reference reads this trial's previous real output."""
    if not isinstance(context,dict):return None
    keys=('same_episode_output_continuity','same_episode_output_reference')
    if not any(isinstance(context.get(key),dict) and context[key].get('required') is True for key in keys):return None
    adapter=Path('/opt/experiment-services/current_output_bridge.py')
    if not adapter.is_file():raise RuntimeError('Declared current-episode output bridge is missing')
    import importlib.util
    spec=importlib.util.spec_from_file_location('current_episode_output_bridge',adapter)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.handle_turn(context,workspace,transport,session_id,dispatch_index,phase)
    if result is not None:
        write_json(Path(transport)/f'turn_{dispatch_index+1:04d}.episode_created_output.{phase}.json',result)
    return result


def prepare_named_python_support(context, workspace, env):
    """Apply declared, source-scoped Python support after its late file delivery."""
    if not isinstance(context,dict) or not context.get('source_named_python_support'):return None
    import importlib.util
    helper=Path('/opt/experiment-services/named_python_bootstrap.py')
    if not helper.is_file():raise ValueError('Declared named Python support helper is missing')
    spec=importlib.util.spec_from_file_location('source_named_python_support',helper)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.apply(context,workspace,env)


def run_episode(messages, session_id, env, transport, secret_values, *,
                workspace=Path('/workspace'), message_dir=Path('/tmp'), deadline,
                run_command=subprocess.run, monotonic=time.monotonic, turn_resources=None, resource_links=None, turn_contexts=None, initial_context=None, original_inputs=None):
    """Sequential native turns in one session; deadline covers the whole episode."""
    answers=[];native_results=[];turns=[]
    for turn_index,message in enumerate(messages,1):
        current_contexts=[entry['context'] for entry in (turn_contexts or []) if entry['user_index']==turn_index-1]
        native_config_path=Path(env['OPENCLAW_CONFIG_PATH'])
        native_config=json.loads(native_config_path.read_text('utf-8'))
        active_context=dict(initial_context or {})
        if turn_index > 1:
            active_context.pop('cron_neutral_old_job_condition',None)
            active_context.pop('cron_current_turn_requirements',None)
            active_context.pop('meeting_choices_initialization',None)
        for ctx in current_contexts:
            if isinstance(ctx,dict):active_context.update(ctx)
        delivered=deliver_turn_resources(turn_resources or [],turn_index-1,workspace,transport)
        python_support=prepare_named_python_support(active_context,workspace,env)
        if python_support:write_json(transport/f'turn_{turn_index:04d}.named_python_support.json',python_support)
        clock=configure_registration_condition(native_config,env,active_context,workspace,(original_inputs or messages)[turn_index-1])
        if clock:write_json(transport/f'turn_{turn_index:04d}.cron_registration_clock.json',clock)
        target_preparation=prepare_registration_targets(active_context,env,workspace,(original_inputs or messages)[turn_index-1])
        if target_preparation:
            write_json(transport/f'turn_{turn_index:04d}.cron_target_preparation.json',target_preparation)
            message+='\n\n本次旧任务ID的实验原生映射（仅建立中性禁用记录，用户要求的修改仍需你执行）：\n'+json.dumps(target_preparation['native_job_id_aliases'],ensure_ascii=False)
        meeting_preparation=prepare_meeting_choice_targets(active_context,env,workspace,(original_inputs or messages)[turn_index-1],
            dispatch_index=turn_index-1,trial_id=session_id,transport=transport,run_command=run_command,
            timeout_seconds=min(60,max(0,deadline-monotonic())),secret_values=secret_values)
        created_skill_preparation=prepare_same_episode_created_skill(active_context,workspace,transport,session_id,turn_index-1,'before_turn')
        created_output_preparation=prepare_same_episode_created_output(active_context,workspace,transport,session_id,turn_index-1,'before_turn')
        if current_contexts:
            visible_contexts=[{key:value for key,value in ctx.items() if key!='meeting_choices_initialization'}
                              if isinstance(ctx,dict) else ctx for ctx in current_contexts]
            visible_contexts=[ctx for ctx in visible_contexts if ctx]
            if visible_contexts:
                message+='\n\n本次用户输入对应的实验文件／服务映射更新：\n'+'\n\n'.join(render_context(ctx) for ctx in visible_contexts)
            write_json(transport/f'turn_{turn_index:04d}.context_delivery.json',{'canonical_user_index':turn_index-1,
                'context_count':len(current_contexts),'orchestration_only_meeting_condition_removed_from_actor_context':True})
        if meeting_preparation:message+='\n\n'+meeting_preparation['guide']
        if created_skill_preparation and created_skill_preparation.get('guide'):
            message+='\n\n'+created_skill_preparation['guide']
        if created_output_preparation and created_output_preparation.get('guide'):
            message+='\n\n'+created_output_preparation['guide']
        if resource_links is not None:
            resource_links.advance(turn_index-1)
            link_guide=resource_links.guide()
            if link_guide:message+='\n\n'+link_guide
        if delivered:
            write_json(transport/f'turn_{turn_index:04d}.input_delivery.json',delivered)
            message+='\n\n本次用户输入随附的文件已到位：\n'+'\n'.join('- '+r['path'] for r in delivered)
        remaining=int(deadline-monotonic())
        if remaining<1: raise RuntimeError('Episode deadline exhausted before next user turn')
        message_path=Path(message_dir)/f'openclaw-eval-message-{turn_index:04d}.txt'
        message_path.write_text(message,encoding='utf-8')
        prefix=f'turn_{turn_index:04d}'
        try:
            result=run_command(build_agent_argv(str(message_path),session_id,timeout_seconds=remaining),
                               cwd=workspace,env=env,capture_output=True,timeout=remaining+5)
        except subprocess.TimeoutExpired as error:
            for name,value in (('stdout',error.stdout),('stderr',error.stderr)):
                text=value.decode('utf-8',errors='replace') if isinstance(value,bytes) else value or ''
                (transport/(prefix+'.'+name+'.log')).write_text(redact_runtime(text,*secret_values),encoding='utf-8')
            turns.append({'turn_index':turn_index,'status':'timeout','timeout_seconds':remaining})
            write_json(transport/'episode_turns.json',turns)
            raise
        stdout=result.stdout.decode('utf-8',errors='replace');stderr=result.stderr.decode('utf-8',errors='replace')
        prefix=f'turn_{turn_index:04d}'
        (transport/(prefix+'.stdout.log')).write_text(redact_runtime(stdout,*secret_values),encoding='utf-8')
        (transport/(prefix+'.stderr.log')).write_text(redact_runtime(stderr,*secret_values),encoding='utf-8')
        turns.append({'turn_index':turn_index,'returncode':result.returncode,'timeout_seconds':remaining})
        write_json(transport/'episode_turns.json',turns)
        if result.returncode: raise RuntimeError(f'Native OpenClaw turn {turn_index} exited nonzero')
        native=parse_json_output(stdout)
        write_json(transport/(prefix+'.native_result.json'),redact_runtime(native,*secret_values))
        data=native.get('result',native)
        validate_native_completion(data)
        payloads=data.get('payloads',[])
        answer='\n\n'.join(p.get('text','') for p in payloads if isinstance(p,dict) and p.get('text'))
        if not answer.strip(): raise RuntimeError(f'Native OpenClaw turn {turn_index} produced no text payload')
        answers.append(answer);native_results.append(native)
        prepare_same_episode_created_skill(active_context,workspace,transport,session_id,turn_index-1,'after_turn')
        prepare_same_episode_created_output(active_context,workspace,transport,session_id,turn_index-1,'after_turn')
    return answers,native_results,turns


def main(request_path):
    transport=Path(request_path).parent; workspace=Path('/workspace')
    stage_started=time.monotonic();progress=[]
    def stage(name,**metadata):
        progress.append({'stage':name,'elapsed_seconds':time.monotonic()-stage_started,**metadata})
        write_json(transport/'runtime_progress.json',progress)
    stage('container_started')
    raw=json.loads(Path(request_path).read_text(encoding='utf-8'))
    model=json.loads(Path('/run/secrets/model.json').read_text(encoding='utf-8-sig'))
    secret=model['api_key'];gateway_token=secrets.token_urlsafe(32)
    secret_values=(secret,gateway_token);timeout=int(os.environ.get('OPENCLAW_EVAL_TIMEOUT','900'))
    observation_seconds=validate_observation_seconds(raw.get('runtime_observation_seconds',0),timeout)
    public_required=public_delivery_required(raw)
    public_reserve=PUBLIC_DELIVERY_RESERVE_SECONDS if public_required else 0
    archive_reserve=OBSERVATION_ARCHIVE_RESERVE_SECONDS if observation_seconds else 0
    if observation_seconds+archive_reserve+public_reserve>=timeout:
        raise ValueError('Observation and public acceptance reserve exhaust the container timeout')
    state=Path('/tmp/openclaw-eval-state');state.mkdir(exist_ok=False)
    config_path=Path('/tmp/openclaw-eval-config.json')
    env=os.environ.copy();env.update(build_process_env(str(state),str(config_path)));env['ECNU_API_KEY']=secret
    env['OPENCLAW_EVAL_GATEWAY_TOKEN']=gateway_token
    compat=configure_runtime_compat(workspace)
    stage('path_compatibility_ready')
    env.update(compat['env'])
    for key in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy'): env.pop(key,None)
    config=build_openclaw_config(base_url=model['base_url'],model_id=model['model'],timeout_seconds=timeout,
                                  max_tokens=int(model.get('max_tokens',8192)),
                                  input_modalities=model.get('input_modalities',['text','image']))
    registration_condition=configure_registration_condition(config,env,raw.get('context',{}),workspace,raw['input'])
    write_json(config_path,config)
    stage('input_fingerprinting_started')
    before=file_hashes(workspace); expected_skills={}
    stage('input_fingerprinting_complete',files=len(before))
    for skill in raw.get('learned_skills',[]):
        src=Path(skill['path']);dst=workspace/'skills'/skill['id']
        if dst.exists(): raise RuntimeError('Learned skill collides with a baseline skill: '+skill['id'])
        if file_hashes(src)!=skill['files']: raise RuntimeError('Learned skill hash mismatch')
        shutil.copytree(src,dst)
        expected_skills[skill['id']]={'path':str(dst/'SKILL.md'),'content':(dst/'SKILL.md').read_text(encoding='utf-8-sig')}
    checks={name:shutil.which(name) for name in raw.get('required_commands',[])}
    if any(not path for path in checks.values()): raise RuntimeError('Required container command missing: '+str(checks))
    guide=(
      '实验运行环境说明：当前工作目录为 /workspace，输入文件已经放在相应相对路径。'
      '请实际完成用户任务，必要时调用工具；不要仅描述做法。生成的交付文件放在 /workspace/outputs。'
      '可以使用 exec 运行 Python、Node、LibreOffice、pandoc、PDF工具、Tesseract、ffmpeg、Chromium/Playwright。'
      'Python虚拟环境已在PATH，中文字体为Noto Sans CJK SC，可通过fc-match定位实际字体文件。Office公式应通过LibreOffice实际重算。'
      '填写可编辑PDF文本表单可用 python /opt/eval-adapter/pdf_form.py INPUT.pdf VALUES.json OUTPUT.pdf --receipt RECEIPT.json；'
      'VALUES.json是实际字段名到文字值的JSON对象，该通用工具生成嵌入中文字体的字段外观并保留可编辑字段；'
      '完成后需实际渲染检查显示文字，不能仅检查字段值或文件存在。'
      '以下命令客户端（包括local-asr、remotion和ecnu_tools.py）均通过exec执行，不是额外的原生工具名。'
      '要用原生view_image查看的渲染图请写入/workspace/tmp（先创建目录）或/tmp/openclaw；已有其他/tmp路径的图先复制到/workspace/tmp再查看。'
      'Playwright Chromium executable_path=/usr/bin/chromium，launch args=["--no-sandbox"]。'
      '原生browser本地网页请先启动HTTP服务并使用http://127.0.0.1地址；file:页面用Playwright。'
      'Remotion、React和CLI已安装，可直接 remotion render，指定 --browser-executable=/usr/bin/chromium；无需重复安装同套依赖。'
      '网络访问可用；用户要求下载的材料和skills请在任务中真实下载。'
      '当前ecnu-plus的文本与图片理解已通过独立接口探针；原生web_search已显式配置Parallel Search Free公开搜索，无需额外搜索API密钥。'
      '该搜索提供商通过真实匿名Search MCP提供结果，网络或额度错误以实际返回为准；据实际工具结果报告，不编造命中。公开网页也可使用browser或HTTP读取。'
      '图像生成命令是 python /opt/eval-adapter/ecnu_tools.py image '
      '--text "图片描述" --output /workspace/outputs/结果.png；16:9幻灯片可指定--size 1280x720。'
      '单图编辑命令是 python /opt/eval-adapter/ecnu_tools.py image-edit '
      '--image-path "实际输入图片" --text "修改要求" --output /workspace/outputs/修改后.png。'
      '图片生成和编辑prompt上限1024字符，不能静默截字；多参考图可用--image-paths上传明确编号拼版，接口仍为单图。'
      '本实验图片模型为ecnu-image，属于公开接口适配，不声称与历史gpt-image-2、2048x1152或多图image[]同条件；'
      '中文语音命令是 python /opt/eval-adapter/ecnu_tools.py speech '
      '--text "需要朗读的内容" --output /workspace/outputs/结果.wav；'
      '独立图片理解可调用该helper的 vision --image-path "图片路径" --text "问题" '
      '--output /workspace/outputs/说明.txt。helper自行读取私有模型凭据，禁止读取或展示密钥；'
      '本地离线中文语音识别可运行 local-asr "输入音频路径" --language zh '
      '--output /workspace/outputs/识别结果.json。'
      '工具执行成功与否以本次实际结果为准。'
      '不得假装调用未配置的外部服务。未提供的私人文件/企业账号请明确说明。'
      '已发现的skills按原生skills规则读取后再使用，不能把标题当作已读正文。\n\n')+compat['guide']+'\n\n'
    builtin_support=configure_builtin_support(workspace,raw.get('context'))
    guide+=builtin_support['guide']+'\n\n'
    resources='\n'.join('- '+r['path'] for r in raw.get('resources',[]))
    context=render_context(raw.get('context',[]))
    message=guide+'本题提供的文件：\n'+resources+'\n\n用户提供的上下文：\n'+context+'\n\n用户任务：\n'+raw['input']
    messages=episode_messages(message,raw.get('followup_inputs',[]))
    session_id=str(uuid.uuid4());start=time.monotonic();receipt={'session_id':session_id,'requested_model':model['model'],'command_checks':checks}
    receipt['runtime_path_aliases']=compat['aliases']
    receipt['builtin_package_compatibility']=builtin_support
    receipt['runtime_skill_root_aliases']=configure_skill_root_aliases(workspace,raw.get('context'))
    expected_baselines=declared_baseline_skills(raw.get('resources',[]),receipt['runtime_skill_root_aliases'],raw.get('turn_resources',[]))
    resource_links=ResourceLinks(raw.get('resource_link_context',raw.get('context')),workspace,transport)
    deadline=start+timeout
    actor_deadline=deadline-observation_seconds-archive_reserve-public_reserve
    receipt['public_delivery_required']=public_required
    receipt['public_delivery_source_id']=PUBLIC_DELIVERY_SOURCE_ID if public_required else None
    receipt['public_delivery_reserve_seconds']=public_reserve
    receipt['runtime_observation_seconds']=observation_seconds
    receipt['cron_registration_condition']=registration_condition
    (workspace/'outputs').mkdir(exist_ok=True)
    gateway_handle=None;gateway_log_dir=Path('/tmp/openclaw-eval-gateway')
    try:
        stage('resource_links_starting')
        receipt['resource_link_service']=resource_links.start()
        stage('config_validation_starting')
        valid=subprocess.run(['openclaw','config','validate'],env=env,capture_output=True,timeout=60)
        receipt['config_validate_returncode']=valid.returncode
        (transport/'config-validation.log').write_text(redact_runtime((valid.stdout+valid.stderr).decode(errors='replace'),*secret_values),encoding='utf-8')
        if valid.returncode: raise RuntimeError('Pinned OpenClaw rejected generated config')
        stage('config_validation_complete')
        receipt['native_cron_seed']=initialize_native_cron_seed(raw.get('context'),workspace,state,env,transport)
        remaining=deadline-time.monotonic()
        if remaining<1: raise RuntimeError('Episode deadline exhausted before Gateway startup')
        stage('gateway_starting')
        gateway_handle=start_gateway(env,private_dir=gateway_log_dir,ready_timeout=min(90,remaining))
        stage('gateway_ready')
        receipt['gateway_readiness']=gateway_handle['readiness']
        receipt['runtime_mode']='gateway'
        try:
            stage('native_actor_started')
            turn_answers,native_results,turns=run_episode(messages,session_id,env,transport,secret_values,deadline=actor_deadline,
                                                         turn_resources=raw.get('turn_resources',[]),resource_links=resource_links,turn_contexts=raw.get('turn_contexts',[]),
                                                         initial_context=raw.get('context'),original_inputs=[raw['input'],*raw.get('followup_inputs',[])])
            stage('native_actor_returned',turns=len(turns))
            receipt['turns']=turns
            receipt['runtime_observation']=observe_runtime(gateway_handle,observation_seconds,env,transport,
                                                         secret_values,deadline=deadline-public_reserve)
            if public_required:
                stage('independent_public_delivery_verification_started')
                acceptance=verify_public_delivery(workspace,deadline=deadline-PUBLIC_DELIVERY_CLEANUP_RESERVE_SECONDS)
                write_json(transport/'public_delivery_acceptance.json',acceptance)
                receipt['public_delivery_acceptance']=acceptance
                if acceptance.get('passed') is not True:
                    raise RuntimeError('Current output public delivery failed independent acceptance')
                stage('independent_public_delivery_verified',verified_files=acceptance.get('verified_files'))
        finally:
            active_run_error=sys.exc_info()[0] is not None
            try:
                receipt['gateway_shutdown']=stop_gateway(gateway_handle);gateway_handle=None
            except Exception as error:
                receipt['gateway_cleanup_error']=redact_runtime(str(error),*secret_values)
                if not active_run_error: raise
        events,sqlite_receipt=load_native_session_events(state,session_id)
        stage('native_events_loaded',events=len(events))
        receipt['full_transcript_export']=sqlite_receipt
        with (transport/'session_events.jsonl').open('w',encoding='utf-8',newline='\n') as out:
            for event in events: out.write(json.dumps(redact_runtime(event,*secret_values),ensure_ascii=False)+'\n')
        try:
            _,export_receipt=export_native_session(session_id,env,transport,secret_values)
            receipt['native_trajectory_export']=export_receipt
        except Exception as error:
            receipt['native_support_export_error']=redact_runtime(str(error),*secret_values)
        native=native_results[-1];write_json(transport/'native_result.json',redact_runtime(native,*secret_values))
        data=native.get('result',native)
        answer=turn_answers[-1]
        evidence=skill_read_evidence(events,expected_skills);write_json(transport/'skill_reads.json',evidence)
        baseline_evidence=skill_read_evidence(events,expected_baselines)
        baseline_evidence.update(timing_verified=False,observation_scope='whole_episode_successful_full_read; per-turn loading time is not certified')
        write_json(transport/'baseline_skill_reads.json',baseline_evidence)
        after=file_hashes(workspace)
        declared_inputs={r['path']:r.get('sha256') for r in raw.get('resources',[])}
        for entry in raw.get('turn_resources',[]):
            declared_inputs.update({r['path']:r.get('sha256') for r in entry['resources']})
        artifacts=[rel for rel,sha in after.items() if before.get(rel)!=sha
                   and declared_inputs.get(str(workspace/rel))!=sha
                   and not rel.startswith(('skills/','learned_skills/','runtime_links/'))]
        tool_summary=tool_result_summary(events)
        response={'answer':answer,'turn_answers':turn_answers,'artifacts':artifacts,'loaded_skill_ids':evidence['loaded_skill_ids'],
                  'loading_evidence':evidence,'baseline_loading_evidence':baseline_evidence,'runtime':{'backend':'openclaw-docker','session_id':session_id,'native_meta':data.get('meta'),
                  **tool_summary}}
        if public_required:
            response['runtime']['public_delivery_acceptance']={
                'passed':receipt['public_delivery_acceptance']['passed'],
                'public_url':receipt['public_delivery_acceptance']['public_url'],
                'verified_files':receipt['public_delivery_acceptance']['verified_files'],
                'receipt':'/transport/public_delivery_acceptance.json',
                'lifetime_scope':'complete-source acceptance before container cleanup; not permanent hosting'}
        write_json(transport/'response.json',redact_runtime(response,*secret_values));receipt['status']='completed'
        stage('response_archived')
    except Exception as exc:
        stage('runtime_failed',error=redact_runtime(str(exc),*secret_values))
        receipt.update(status='failed',error=redact_runtime(str(exc),*secret_values));raise
    finally:
        if public_required:
            stage('public_delivery_cleanup_started')
            try:
                cleanup=stop_public_delivery(workspace)
                write_json(transport/'public_delivery_cleanup.json',cleanup)
                receipt['public_delivery_cleanup']=cleanup
                stage('public_delivery_cleanup_complete',stopped=len(cleanup.get('stopped_publication_ids',[])))
            except Exception as error:
                receipt['public_delivery_cleanup_error']=redact_runtime(str(error),*secret_values)
        try:resource_links.close()
        except Exception as error:receipt['resource_link_cleanup_error']=redact_runtime(str(error),*secret_values)
        if gateway_handle is not None:
            try:receipt['gateway_shutdown']=stop_gateway(gateway_handle)
            except Exception as error:receipt['gateway_cleanup_error']=redact_runtime(str(error),*secret_values)
        if receipt.get('status')=='failed':
            preserve_failure_events(state,session_id,transport,secret_values,receipt)
        try:export_gateway_logs(gateway_log_dir,transport,*secret_values)
        except Exception as error:receipt['gateway_log_export_error']=redact_runtime(str(error),*secret_values)
        receipt['seconds']=time.monotonic()-start;write_json(transport/'container_receipt.json',receipt)
        # State and generated model stores stay inside this disposable container.
        # Only explicit redacted evidence above is exported.


if __name__=='__main__': main(sys.argv[1])
