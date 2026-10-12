"""Create real isolated A/B experiment state when the current user refers to B."""
import argparse
import json
import sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,'/opt/real-services')
from service_cli import MeetingClient,credentials,decoded_tool_results

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--fixture',required=True);p.add_argument('--dispatch-index',type=int,required=True)
    p.add_argument('--output',required=True);p.add_argument('--trial-id',default='environment-preparation')
    p.add_argument('--current-state');p.add_argument('--current-context')
    a=p.parse_args();fixture=json.loads(Path(a.fixture).read_text(encoding='utf-8-sig'))
    if a.dispatch_index<fixture['available_from_dispatch_index']:raise ValueError('Meeting choice state is not visible before current user B reference')
    out=Path(a.output)
    if out.exists():raise ValueError('Use a fresh trial state path; do not silently overwrite an initialized state')
    current={};prior_context={}
    if a.current_context and Path(a.current_context).exists():
        prior_context=json.loads(Path(a.current_context).read_text(encoding='utf-8-sig'))
        if prior_context['source_id']!=fixture['source_id']:raise ValueError('Current context belongs to another source')
    if a.current_state and Path(a.current_state).exists():
        prior=json.loads(Path(a.current_state).read_text(encoding='utf-8-sig'))
        if prior['source_id']!=fixture['source_id']:raise ValueError('Current state belongs to another source')
        owned=set(prior.get('created_ids',[]))
        for obj in prior.get('created_objects',[]):
            if obj.get('label') in {'A','B'} and obj['meeting_id'] in owned:current[obj['label']]=obj
    client=MeetingClient(credentials()['tencent_meeting']['token']);status,data,_=client.initialize()
    if status!=200 or 'error' in data:raise ValueError('Meeting auth failed')
    created=[];calls=[];used_current=[]
    try:
        for option in fixture['options']:
            if option['label'] in current:
                prior_obj=current[option['label']]
                status,body,_=client.call('get_meeting',{'meeting_id':prior_obj['meeting_id'],'timezone':'Asia/Shanghai'})
                if status!=200 or body.get('result',{}).get('isError'):raise ValueError('Current trial object no longer exists')
                actual=next(r['data']['meeting_info_list'][0] for r in decoded_tool_results(body) if r.get('data',{}).get('meeting_info_list'))
                used_current.append({**prior_obj,'meeting_code':actual.get('meeting_code'),'join_url':actual.get('join_url'),'until_count':actual.get('recurring_rule',{}).get('until_count'),'actual_current_object_readback_verified':True});continue
            # "Keep B" needs no synthetic A if the current actor already made B
            # and never made the duplicate. Preserve the actual trajectory.
            if option['label']=='A' and 'B' in current:continue
            args={'subject':'SkillLoop 周例会实验候选'+option['label'],'start_time':fixture['experimental_start_time'],'end_time':fixture['experimental_end_time'],'time_zone':'Asia/Shanghai','invitees':[],
                'meeting_type':1,'recurring_rule':{'recurring_type':2,'until_type':1,'until_count':option['until_count']}}
            status,body,_=client.call('schedule_meeting',args);decoded=decoded_tool_results(body)
            if status!=200 or body.get('result',{}).get('isError') or any(r.get('business_http_status',200)!=200 for r in decoded):raise ValueError('Meeting creation failed')
            obj=next(r['data']['meeting_info_list'][0] for r in decoded if r.get('data',{}).get('meeting_info_list'))
            entry={'label':option['label'],'meeting_id':str(obj['meeting_id']),'meeting_code':obj.get('meeting_code'),'join_url':obj.get('join_url'),'until_count':option['until_count'],'experimental_start_time':args['start_time'],'experimental_end_time':args['end_time']}
            created.append(entry)
            status,body,_=client.call('get_meeting',{'meeting_id':entry['meeting_id'],'timezone':'Asia/Shanghai'});decoded=decoded_tool_results(body)
            if status!=200 or body.get('result',{}).get('isError'):raise ValueError('Meeting readback failed')
            read=next(r['data']['meeting_info_list'][0] for r in decoded if r.get('data',{}).get('meeting_info_list'))
            if read['recurring_rule']['until_count']!=option['until_count']:raise ValueError('Wrong recurrence count in actual meeting')
            if read['start_time']!=args['start_time'] or read['end_time']!=args['end_time']:raise ValueError('Wrong actual meeting time')
            calls.append({'label':option['label'],'actual_create_readback_verified':True,'recurring_rule':read['recurring_rule'],'start_time':read['start_time'],'end_time':read['end_time']})
    except Exception:
        for entry in created:
            client.call('cancel_meeting',{'meeting_id':entry['meeting_id'],'meeting_type':1})
        raise
    all_objects=used_current+created;labels={obj['label']:obj for obj in all_objects}
    result={**prior_context,'source_id':fixture['source_id'],'trial_id':a.trial_id,'available_from_dispatch_index':fixture['available_from_dispatch_index'],
        'initial_meetings':all_objects,'meeting_code_aliases':{str(option['original_meeting_code']):str(labels[option['label']]['meeting_code']) for option in fixture['options'] if option['label'] in labels},
        'original_historical_state_restored':False,'synthetic_previous_state':bool(created),'condition':'experimental historical-reference bridge only when current trial objects are absent',
        'current_actor_produced_objects_preferred':True,'current_actor_objects_reused':len(used_current),'created_fallback_objects':len(created),
        'does_not_claim_actor_previously_created_fallback_objects':True,'desired_user_action_not_executed':True,'invited_other_people':False,'actual_create_readback':calls,'created_at':datetime.now(timezone.utc).isoformat()}
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'source_id':result['source_id'],'actual_self_owned_objects':len(created),'current_actor_objects_reused':len(used_current),'available_from_dispatch_index':result['available_from_dispatch_index'],'verified':True,'invited_other_people':False},ensure_ascii=False));return 0

if __name__=='__main__':raise SystemExit(main())
