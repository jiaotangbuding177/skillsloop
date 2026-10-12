"""Apply the explicitly authorized registration-only condition to a new runtime."""
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime,timedelta,timezone
from pathlib import Path

def configure(config,env,context,workspace,active_user_text='',adapter_root='/opt/experiment-services'):
    policy=context.get('cron_registration_evaluation')
    if not isinstance(policy,dict) or policy.get('evaluation_mode')!='native_registration_only':return None
    config['cron']={'enabled':False}
    candidates=[];basis=[]
    first=policy.get('source_first_user_timestamp')
    if first:
        try:candidates.append(datetime.fromisoformat(first.replace('Z','+00:00')));basis.append('source first known user timestamp')
        except ValueError:pass
    # Only the currently dispatched original input supplies absolute job dates.
    for match in re.finditer(r'单次执行[^\n]*?(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})',active_user_text):
        candidates.append(datetime.fromisoformat(match.group(1)+'T'+match.group(2)+':00+08:00')-timedelta(minutes=5))
        basis.append('current dispatched user absolute one-shot time minus five minutes')
    if not candidates:return {'scheduler_enabled':False,'clock':'wallclock; no historical absolute date supplied yet'}
    epoch=min(candidates).astimezone(timezone.utc).isoformat()
    file=Path(workspace)/'.runtime-context'/'cron-clock.json';file.parent.mkdir(parents=True,exist_ok=True)
    record={'epoch':epoch,'basis':basis,'source_id':context.get('source_id'),
        'current_user_input_sha256':hashlib.sha256(active_user_text.encode()).hexdigest(),
        'affects_only':'pinned native one-shot schedule timestamp validation',
        'does_not_change':'actual record timestamps, ownership leases, auth clocks, other CLI processes'}
    file.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    env['SKILLLOOP_CRON_CLOCK_FILE']=str(file)
    imported='--import='+str(Path(adapter_root)/'cron_clock.mjs')
    env['NODE_OPTIONS']=(env.get('NODE_OPTIONS','')+' '+imported).strip()
    return {**record,'clock_file':str(file),'scheduler_enabled':False,'trigger_required':False}

def prepare_after_gateway(context,env,workspace,active_user_text='',adapter_root='/opt/experiment-services'):
    """Resolve current-turn old IDs only; preserve this trial's actual state."""
    declaration=context.get('cron_neutral_old_job_condition')
    if not declaration:return None
    sid=context.get('source_id')
    if not sid:raise ValueError('Neutral target preparation requires source identity')
    aliases={};receipts=[]
    for original_id in declaration.get('job_ids',[]):
        if original_id not in active_user_text:raise ValueError('Old target ID is not present in the current user input')
        state=Path(workspace)/'.runtime-context'/'cron-registration-state.json'
        proc=subprocess.run([sys.executable,str(Path(adapter_root)/'cron_registration.py'),'ensure','--source-id',sid,'--job-id',original_id,'--state-file',str(state)],env=env,capture_output=True,text=True,timeout=45)
        if proc.returncode:raise RuntimeError('Native neutral target preparation failed: '+proc.stderr[-1000:])
        result=json.loads(proc.stdout);aliases[original_id]=result['native_job_id'];receipts.append(result)
    context.setdefault('cron_job_id_aliases',{}).update(aliases)
    return {'synthetic_neutral_initial_condition':True,'historical_state_restored':False,
        'native_job_id_aliases':aliases,'actual_native_receipts':receipts,'requested_update_not_executed':True}
