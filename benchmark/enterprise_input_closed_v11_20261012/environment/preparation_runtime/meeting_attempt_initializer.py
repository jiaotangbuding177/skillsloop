"""Create fresh source-scoped real meetings for each independent benchmark attempt.

Host Windows entrypoint uses the already pinned container. Container/runtime
entrypoint uses the existing private real-service transport. No old live IDs
are copied into a new attempt's mutable state.
"""
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime,timedelta,timezone
from pathlib import Path

IMAGE='sha256:2a45d063a0945811fc5405c652736347898e494c9dc40762e4d606f9bb46c4f0'
ROOT=Path('D:/skillloop')
HERE=Path(__file__).resolve().parent

def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+'.tmp');tmp.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8');tmp.replace(p)
def mount_path(path):
    p=Path(path).resolve();s=str(p).replace('\\','/')
    if re.match(r'^[A-Za-z]:/',s):return '/mnt/'+s[0].lower()+s[2:]
    return s

def initialize_meeting_attempt(plan_path,session_id,attempt_id,state_root,workspace):
    """Return a fresh source context, stable only within this exact attempt."""
    if not re.fullmatch(r'conv_[a-z0-9]+',session_id):raise ValueError('Invalid source identity')
    if not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',attempt_id):raise ValueError('Attempt identity must be a safe unique identifier')
    plan_path=Path(plan_path).resolve();workspace=Path(workspace).resolve();state_root=Path(state_root).resolve()
    workspace.mkdir(parents=True,exist_ok=True);state_root.mkdir(parents=True,exist_ok=True)
    if os.name=='nt':
        binding=state_root/session_id/attempt_id/'host_workspace_binding.json'
        identity=str(workspace)
        if binding.exists() and load(binding)['workspace']!=identity:
            raise ValueError('Same attempt identity cannot be reused in a different host workspace')
        if not binding.exists():save(binding,{'workspace':identity,'session_id':session_id,'attempt_id':attempt_id})
        service=ROOT/'research/environment/20261008_personal_service_access'
        cmd=['wsl.exe','-d','Ubuntu','--exec','/usr/bin/docker','run','--rm','--entrypoint','/opt/eval-venv/bin/python',
             '--mount','type=bind,src='+mount_path(service/'private/services_active.json')+',dst=/run/secrets/services.json,readonly',
             '--mount','type=bind,src='+mount_path(service/'cloud')+',dst=/opt/real-services,readonly',
             '--mount','type=bind,src='+mount_path(HERE)+',dst=/opt/initializer,readonly',
             '--mount','type=bind,src='+mount_path(plan_path.parent)+',dst=/plan,readonly',
             '--mount','type=bind,src='+mount_path(state_root)+',dst=/attempt-state',
             '--mount','type=bind,src='+mount_path(workspace)+',dst=/workspace',IMAGE,
             '/opt/initializer/meeting_attempt_initializer.py','--plan','/plan/'+plan_path.name,
             '--session-id',session_id,'--attempt-id',attempt_id,'--state-root','/attempt-state','--workspace','/workspace']
        proc=subprocess.run(cmd,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=80)
        if proc.returncode:raise RuntimeError('Fresh meeting initializer failed: '+proc.stderr[-1500:])
        # The complete, source-scoped context is the on-disk receipt, not stdout.
        result=load(state_root/session_id/attempt_id/'initialization_receipt.json')
        result['context_path']=str(workspace/'service-context/tencent-meeting.json')
        return result
    plan=load(plan_path)
    row=next((r for r in plan['sources'] if r['session_id']==session_id),None)
    if row is None or 'tencent_meeting_experiment' not in row['context']:raise ValueError('Source has no declared Tencent Meeting environment condition')
    state=state_root/session_id/attempt_id;state.mkdir(parents=True,exist_ok=True)
    receipt_path=state/'initialization_receipt.json'
    target=workspace/'service-context/tencent-meeting.json'
    if receipt_path.exists():
        existing=load(receipt_path)
        if existing['workspace']!=str(workspace):raise ValueError('Same attempt identity cannot be reused in a different workspace')
        if not target.exists():save(target,existing['source_context'])
        return existing
    lock=state/'initialization.lock'
    artifact=next(a for a in row['artifacts'] if a['mount']=='service-context/tencent-meeting.json')
    original=Path(artifact['path'])
    if not original.exists():original=plan_path.parent/'source_contexts'/session_id/'腾讯会议实验对象.json'
    template=load(original)
    if hashlib.sha256(original.read_bytes()).hexdigest()!=artifact['sha256']:raise ValueError('Source condition bytes differ from admitted plan')
    sys.path.insert(0,'/opt/real-services')
    from service_cli import MeetingClient,credentials,decoded_tool_results
    fresh=[];calls=[];created=[]
    client=None
    fd=os.open(str(lock),os.O_CREAT|os.O_EXCL|os.O_WRONLY);os.close(fd)
    try:
        if template.get('initial_meetings'):
            client=MeetingClient(credentials()['tencent_meeting']['token']);status,data,_=client.initialize()
            if status!=200 or 'error' in data:raise RuntimeError('Real meeting transport initialization failed')
        for item in template.get('initial_meetings',[]):
            start=datetime.fromisoformat(item['experimental_start_time']);end=datetime.fromisoformat(item['experimental_end_time'])
            # Preserve weekday and time on future trial dates; declared as an
            # experiment date adaptation, not original enterprise restoration.
            now=datetime.now(timezone(timedelta(hours=8)))
            while start<=now:start+=timedelta(days=7);end+=timedelta(days=7)
            subject=item['experimental_subject']+' ['+attempt_id[:16]+']'
            args={'subject':subject,'start_time':start.isoformat(),'end_time':end.isoformat(),'time_zone':'Asia/Shanghai','invitees':[]}
            status,body,_=client.call('schedule_meeting',args);decoded=decoded_tool_results(body)
            if status!=200 or body.get('result',{}).get('isError') or any(x.get('business_http_status',200)!=200 for x in decoded):raise RuntimeError('Actual initial meeting creation failed')
            obj=next(x['data']['meeting_info_list'][0] for x in decoded if x.get('data',{}).get('meeting_info_list'))
            mid=str(obj['meeting_id']);created.append(mid)
            status,body,_=client.call('get_meeting',{'meeting_id':mid,'timezone':'Asia/Shanghai'});decoded=decoded_tool_results(body)
            if status!=200 or body.get('result',{}).get('isError'):raise RuntimeError('Actual fresh meeting readback failed')
            got=next(x['data']['meeting_info_list'][0] for x in decoded if x.get('data',{}).get('meeting_info_list'))
            if datetime.fromisoformat(got['start_time'])!=start or datetime.fromisoformat(got['end_time'])!=end:raise RuntimeError('Fresh initial meeting has wrong time')
            entry={'meeting_id':mid,'meeting_code':obj.get('meeting_code'),'join_url':obj.get('join_url'),'experimental_subject':subject,
                   'experimental_start_time':start.isoformat(),'experimental_end_time':end.isoformat(),'source_id':session_id,'attempt_id':attempt_id,'origin':'fresh real source-scoped synthetic initial condition'}
            fresh.append(entry);calls.append({'operation':'native_schedule_meeting_and_get_readback','verified':True,'meeting_id':mid})
        aliases={}
        if fresh:
            for old_code in template.get('meeting_code_aliases',{}):aliases[old_code]=fresh[0]['meeting_code']
        ctx={**template,'initial_meetings':fresh,'meeting_code_aliases':aliases,'attempt_id':attempt_id,
             'old_live_ids_reused':False,'original_historical_state_restored':False,
             'mutable_scope':'one source and one independent attempt only','current_trial_created_objects_take_precedence':True}
        save(target,ctx)
        result={'schema':'fresh-real-meeting-attempt-initialization-v1','source_id':session_id,'attempt_id':attempt_id,
                'workspace':str(workspace),'context_path':str(target),'source_context':ctx,'actual_native_checks':calls,
                'fresh_native_meetings_created':len(fresh),'previous_live_ids_reused':False,'invited_other_people':False,
                'passed':True,'completed_at':datetime.now(timezone.utc).isoformat(),'natural_language_model_calls':0,'actor_calls':0}
        save(receipt_path,result);return result
    except Exception:
        if client:
            for mid in created:client.call('cancel_meeting',{'meeting_id':mid})
        raise
    finally:lock.unlink(missing_ok=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--plan',required=True);p.add_argument('--session-id',required=True);p.add_argument('--attempt-id',required=True);p.add_argument('--state-root',required=True);p.add_argument('--workspace',required=True)
    a=p.parse_args();r=initialize_meeting_attempt(a.plan,a.session_id,a.attempt_id,a.state_root,a.workspace)
    print(json.dumps({'passed':r['passed'],'source_id':r['source_id'],'attempt_id':r['attempt_id'],'fresh_native_meetings_created':r['fresh_native_meetings_created'],'previous_live_ids_reused':False,'context_path':r['context_path']},ensure_ascii=False))
