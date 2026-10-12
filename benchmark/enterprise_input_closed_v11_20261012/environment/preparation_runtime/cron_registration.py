"""Actual native cron RPC wrapper for isolated registration-only evaluation."""
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

def load(path): return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')

def parse_response(text):
    dec=json.JSONDecoder()
    for i,c in enumerate(text):
        if c=='{':
            try:
                obj,end=dec.raw_decode(text[i:])
                if not text[i+end:].strip():return obj
            except ValueError:pass
    raise RuntimeError('Native cron did not return JSON')

def rpc(action,params):
    p=subprocess.run(['openclaw','gateway','call','cron.'+action,'--params',json.dumps(params,ensure_ascii=False),'--json'],capture_output=True,text=True,timeout=40)
    if p.returncode:raise RuntimeError('Native cron '+action+' failed: '+p.stderr[-1500:])
    return parse_response(p.stdout)

def neutral_target(original_id,state):
    listing=rpc('list',{'includeDisabled':True})
    existing={str(j['id']):j for j in listing.get('jobs',[])}
    native_id=state.get('aliases',{}).get(original_id,original_id)
    if native_id in existing:return native_id,False
    job=rpc('add',{'agentId':'eval','name':'实验既有任务（历史字段未知）','enabled':False,
        'schedule':{'kind':'every','everyMs':86400000},'sessionTarget':'isolated',
        'payload':{'kind':'agentTurn','message':'实验中性占位任务，仅用于修改或删除接口。历史名称、内容与计划均未知。','toolsAllow':['*']},
        'delivery':{'mode':'none'},'description':'experimental neutral disabled initial state; historical fields unknown'})
    state.setdefault('aliases',{})[original_id]=job['id']
    state.setdefault('neutral_initial_states',[]).append({'original_job_id':original_id,'native_job_id':job['id'],
        'unknown_historical_fields':['name','payload','schedule','delivery','timeout'],
        'neutral_synthetic_job':job,'target_values_not_backfilled':True})
    return job['id'],True

def stamp(job,metadata,source):
    job=dict(job);job['agentId']='eval';job['enabled']=False
    job.setdefault('sessionTarget','isolated');job.setdefault('delivery',{'mode':'none'})
    payload=dict(job.get('payload',{}));payload.setdefault('kind','agentTurn')
    payload.setdefault('toolsAllow',['*']);job['payload']=payload
    m={'source_id':source,'registration_only':True,**metadata}
    job['description']='benchmark-registration-context: '+json.dumps(m,ensure_ascii=False)
    return job

def compare(actual,expected):
    checks=[]
    def test(name,ok,want,got):checks.append({'field':name,'passed':ok,'expected':want,'actual':got})
    sch=actual.get('schedule',{});want=expected.get('schedule',{})
    for k,v in want.items():
        a=sch.get(k)
        if k=='at':
            ok=datetime.fromisoformat(str(a).replace('Z','+00:00'))==datetime.fromisoformat(str(v).replace('Z','+00:00'))
        else:ok=a==v
        test('schedule.'+k,ok,v,a)
    for k in ('name','agentId','sessionTarget'):
        if k in expected:test(k,actual.get(k)==expected[k],expected[k],actual.get(k))
    if 'payload' in expected:
        for k,v in expected['payload'].items():test('payload.'+k,actual.get('payload',{}).get(k)==v,v,actual.get('payload',{}).get(k))
    if 'message_contains' in expected:
        for v in expected['message_contains']:test('payload.message contains',v in actual.get('payload',{}).get('message',''),v,actual.get('payload',{}).get('message',''))
    if 'registration_metadata' in expected:
        prefix='benchmark-registration-context: '
        desc=actual.get('description','');metadata=json.loads(desc[len(prefix):]) if desc.startswith(prefix) else {}
        for k,v in expected['registration_metadata'].items():test('registration_metadata.'+k,metadata.get(k)==v,v,metadata.get(k))
    test('enabled',actual.get('enabled') is False,False,actual.get('enabled'))
    return {'passed':all(c['passed'] for c in checks),'checks':checks,'trigger_required':False,'trigger_tested':False}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('operation',choices=['add','update','delete','list','verify','ensure'])
    p.add_argument('--source-id',required=True);p.add_argument('--json-file');p.add_argument('--job-id');p.add_argument('--expected-file')
    p.add_argument('--state-file',default='/workspace/.runtime-context/cron-registration-state.json')
    a=p.parse_args();state=load(a.state_file) if Path(a.state_file).exists() else {'source_id':a.source_id,'aliases':{}}
    if state['source_id']!=a.source_id:raise ValueError('Cron registration state belongs to another source')
    cfg=load(os.environ.get('OPENCLAW_CONFIG_PATH','/tmp/openclaw-eval-config.json'))
    if cfg.get('cron',{}).get('enabled') is not False:raise ValueError('Registration-only helper requires globally disabled scheduler')
    request=load(a.json_file) if a.json_file else {}
    if a.operation=='add':
        job={k:v for k,v in request.get('job',request).items() if k!='registration_metadata'}
        result=rpc('add',stamp(job,request.get('registration_metadata',{}),a.source_id))
    elif a.operation in ('update','delete','ensure'):
        original=str(a.job_id or request.get('id',''))
        if not original:raise ValueError('Job identity is required')
        jid,created=neutral_target(original,state)
        if a.operation=='ensure':result={'job_id':jid,'neutral_initial_state_prepared':created}
        elif a.operation=='update':
            patch=dict(request.get('patch',{}));patch['enabled']=False
            metadata={'source_id':a.source_id,'registration_only':True,**request.get('registration_metadata',{})}
            if request.get('registration_metadata'):patch['description']='benchmark-registration-context: '+json.dumps(metadata,ensure_ascii=False)
            result=rpc('update',{'jobId':jid,'patch':patch})
        else:result=rpc('remove',{'jobId':jid})
        result={'native_result':result,'original_job_id':original,'native_job_id':jid,'created_neutral_initial_state':created}
    else:
        result=rpc('list',{'includeDisabled':True})
        if a.operation=='verify':
            jid=state['aliases'].get(a.job_id,a.job_id)
            got=next((j for j in result.get('jobs',[]) if j['id']==jid),None)
            if got is None:result={'passed':False,'reason':'Requested job not present in actual native list'}
            else:result=compare(got,load(a.expected_file))
    state.setdefault('actual_operations',[]).append({'operation':a.operation,'completed_at':datetime.now(timezone.utc).isoformat(),'response':result})
    save(a.state_file,state);print(json.dumps(result,ensure_ascii=False))
    return 2 if result.get('passed') is False else 0

if __name__=='__main__':raise SystemExit(main())
