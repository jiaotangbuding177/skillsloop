"""Prepare all canonical user turns, with inputs delivered at the matching turn."""
from pathlib import Path
import argparse, copy, hashlib, json, shutil
import bench

BASE=Path(__file__).resolve().parent

def prepare(contract, output):
    output=Path(output).resolve()
    if output.exists():raise ValueError('Use a fresh attempt directory')
    workspace=output/'workspace';workspace.mkdir(parents=True)
    initial=list(contract.get('public_baseline_resources',[]));later={}
    for dependency in contract['dependencies']:
        for resource in dependency.get('artifacts',[]):
            when=resource.get('available_from_dispatch_index',dependency.get('available_from_dispatch_index',0))
            if when==0:initial.append(resource)
            else:later.setdefault(when,[]).append(resource)
    def deliver(values, root):
        final={}
        for resource in values:
            source=BASE/resource['path'];mount=resource['mount']
            if mount in final and final[mount]['sha256'] != resource['sha256']:
                raise ValueError('Conflicting input versions at one dispatch: '+mount)
            if not bench.fs(source).is_file() or bench.sha(source)!=resource['sha256']:raise ValueError('Input artifact SHA mismatch: '+mount)
            destination=root/mount
            if not destination.resolve().is_relative_to(root.resolve()):raise ValueError('Input path escapes its staging root')
            bench.fs(destination.parent).mkdir(parents=True,exist_ok=True)
            shutil.copyfile(bench.fs(source),bench.fs(destination))
            final[mount]={**resource,'path':str(destination)}
        return list(final.values())
    resources=deliver(initial,workspace)
    staged=[]
    for index,values in sorted(later.items()):
        staged.append({'user_index':index,'resources':deliver(values,output/'staged_resources'/str(index))})
    actor=contract['actor']
    request={'protocol':'clean-complete-source-replay-v6','stage':'consume','task_id':contract['task_id'],
        'input':actor['input'],'followup_inputs':actor['followup_inputs'],'context':copy.deepcopy(actor['context']),
        'turn_contexts':copy.deepcopy(actor['turn_contexts']),'resource_link_context':copy.deepcopy(contract['consumer_resource_link_context']),
        'resources':resources,'turn_resources':staged,'learned_skills':[], 'required_commands':[],'runtime_observation_seconds':0,'seed':20261009}
    bench.write(output/'request.json',request)
    bench.write(output/'input_receipt.json',{'session_id':contract['session_id'],'canonical_user_turns':1+len(actor['followup_inputs']),
        'source_user_message_ids':[u['source_message_id'] for u in contract['replay']['users']],
        'initial_files':len(resources),'later_input_deliveries':sum(len(e['resources']) for e in staged),
        'historical_AI_sent_to_actor':False,'canonical_text_or_turn_order_changed':False})
    return output/'request.json'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--session');p.add_argument('--query');p.add_argument('--output',required=True);a=p.parse_args()
    contract=bench.select(a.session,a.query)
    request=prepare(contract,a.output)
    print(json.dumps({'request':str(request),'title':contract['title'],'canonical_turns':len(contract['replay']['users'])},ensure_ascii=False))
