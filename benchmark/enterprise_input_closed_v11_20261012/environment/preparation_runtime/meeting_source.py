"""Real Tencent Meeting calls with source-scoped experiment object mappings."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0,'/opt/real-services')
from service_cli import credentials,invoke

def find_objects(value):
    if isinstance(value,dict):
        if value.get('meeting_id'):yield value
        for v in value.values():yield from find_objects(v)
    elif isinstance(value,list):
        for v in value:yield from find_objects(v)

def filtered(value,allowed):
    if isinstance(value,list):
        return [filtered(v,allowed) for v in value if not isinstance(v,dict) or not v.get('meeting_id') or str(v['meeting_id']) in allowed]
    if isinstance(value,dict):
        result={k:filtered(v,allowed) for k,v in value.items()}
        for k in ('meeting_number','total_count'):
            if k in result and 'meeting_info_list' in result:result[k]=len(result['meeting_info_list'])
        return result
    return value

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('tool')
    p.add_argument('--source-id',required=True);p.add_argument('--json-file')
    p.add_argument('--context-file',default='/workspace/service-context/tencent-meeting.json')
    p.add_argument('--state-file',default='/workspace/.runtime-context/tencent-meeting-created.json')
    a=p.parse_args();ctx=json.loads(Path(a.context_file).read_text(encoding='utf-8-sig'))
    if ctx['source_id']!=a.source_id:raise ValueError('Meeting context belongs to another source')
    state=json.loads(Path(a.state_file).read_text(encoding='utf-8')) if Path(a.state_file).exists() else {'source_id':a.source_id,'created_ids':[]}
    if state['source_id']!=a.source_id:raise ValueError('Meeting state belongs to another source')
    args=json.loads(Path(a.json_file).read_text(encoding='utf-8-sig')) if a.json_file else {}
    option_label=args.pop('experiment_option_label',None)
    allowed=set(str(x['meeting_id']) for x in ctx.get('initial_meetings',[]))|set(state['created_ids'])
    alias=ctx.get('meeting_code_aliases',{})
    if str(args.get('meeting_code','')) in alias:args['meeting_code']=alias[str(args['meeting_code'])]
    if a.tool in ('cancel_meeting','update_meeting','get_meeting') and str(args.get('meeting_id','')) not in allowed:raise ValueError('Requested meeting is not in this source experiment state')
    result=invoke(credentials(),'tencent-meeting',a.tool,'GET',args)
    good=result['http_status']==200 and not result.get('body',{}).get('error') and not result.get('body',{}).get('result',{}).get('isError',False) and all(r.get('business_http_status',200)<400 for r in result.get('tool_results',[]))
    if good and a.tool=='schedule_meeting':
        for obj in find_objects(result.get('tool_results',[])):
            mid=str(obj['meeting_id'])
            if mid not in state['created_ids']:state['created_ids'].append(mid)
            state.setdefault('created_objects',[]).append({'meeting_id':mid,'meeting_code':obj.get('meeting_code'),'join_url':obj.get('join_url'),
                'label':option_label,'until_count':args.get('recurring_rule',{}).get('until_count'),'subject':args.get('subject'),
                'source_id':a.source_id,'origin':'actual current trial schedule_meeting tool result'})
        Path(a.state_file).parent.mkdir(parents=True,exist_ok=True)
        Path(a.state_file).write_text(json.dumps(state,ensure_ascii=False,indent=2),encoding='utf-8')
        allowed|=set(state['created_ids'])
    # Do not expose unrelated personal-account meetings to another source.
    response={'http_status':result['http_status'],'tool':a.tool,'source_id':a.source_id,'real_remote_call':True,'passed':good,
        'tool_results':filtered(result.get('tool_results',[]),allowed)}
    if not good:response['native_error']=result.get('body')
    print(json.dumps(response,ensure_ascii=False));return 0 if good else 2

if __name__=='__main__':raise SystemExit(main())
