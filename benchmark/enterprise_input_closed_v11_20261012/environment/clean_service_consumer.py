"""Personal-service consumer with canonical staging and source-specific contexts."""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, shutil, sys

BASE=Path(__file__).resolve().parent.parent
LAYER=Path('D:/skillloop/research/environment/20261008_personal_service_access/personal_service_consumer.py')

def rows(path):
    with open(path,encoding='utf-8-sig') as f:return [json.loads(line) for line in f if line.strip()]

def hydrate(request_path):
    request_path=Path(request_path);raw=json.loads(request_path.read_text('utf-8-sig'))
    contracts=rows(BASE/'contracts/evolution.jsonl')+rows(BASE/'contracts/evaluation.jsonl')
    contract=next((c for c in contracts if c['task_id']==raw.get('task_id')),None)
    if contract:
        actor=contract['actor']
        if raw['input']!=actor['input'] or raw.get('followup_inputs',[])!=actor['followup_inputs']:
            raise ValueError('The request differs from the canonical complete source')
        raw['context']=copy.deepcopy(actor['context']);raw['turn_contexts']=copy.deepcopy(actor['turn_contexts'])
        raw['resource_link_context']=copy.deepcopy(contract['consumer_resource_link_context'])
        later={}
        for dependency in contract['dependencies']:
            for resource in dependency.get('artifacts',[]):
                when=resource.get('available_from_dispatch_index',0)
                if when:later.setdefault(when,[]).append(resource)
        # Pipeline plugins may omit staging fields; reconstruct only the pinned contract's inputs.
        if later and not raw.get('turn_resources'):
            staged=[]
            for when,values in sorted(later.items()):
                resources={}
                for resource in values:
                    source=BASE/resource['path'];dest=request_path.parent/'staged_resources'/str(when)/resource['mount']
                    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest)
                    resources[resource['mount']]={**resource,'path':str(dest)}
                staged.append({'user_index':when,'resources':list(resources.values())})
            raw['turn_resources']=staged
    elif isinstance(raw.get('context'),list):
        context=raw['context']
        if len(context)==1:
            try:raw['context']=json.loads(context[0])
            except ValueError:raw['context']={'supplied_context':context}
        else:raw['context']={'supplied_context':context}
    output=request_path.parent/'consumer_canonical_request.json'
    if output.exists():raise ValueError('Retain the earlier attempt and choose a fresh directory')
    output.write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return output


def load_module(path, name):
    path=Path(path)
    if not path.is_file():raise ValueError('Packaged service initializer is missing: '+path.name)
    if str(path.parent) not in sys.path:sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def choose_workspace(raw,request_path,response_path,explicit=None):
    parent=Path(request_path).resolve().parent
    candidates=[Path(explicit).resolve()] if explicit else []
    if not explicit:
        if raw.get('workspace'):candidates.append(Path(raw['workspace']).resolve())
        candidates.extend([parent/'workspace',parent/'actor_workspace'])
        for resource in raw.get('resources',[]):
            path=Path(resource['path']).resolve();mount=Path(resource['mount'])
            candidate=path
            for _ in mount.parts:candidate=candidate.parent
            if candidate.is_dir():candidates.append(candidate)
    for candidate in candidates:
        if candidate.is_dir() and candidate!=parent and candidate.is_relative_to(parent):return candidate
    if explicit:raise ValueError('Explicit workspace must be an existing subdirectory of the request directory')
    response_parent=Path(response_path).resolve().parent
    workspace=(response_parent if response_parent.is_relative_to(parent) else parent)/'actor_workspace'
    workspace.mkdir(parents=True,exist_ok=True)
    return workspace


def remove_old_service_state(value,owned_keys):
    if isinstance(value,dict):
        return {k:remove_old_service_state(v,owned_keys) for k,v in value.items()
                if k not in owned_keys|{'source_service_preparation','source_service_state','attempt_service_preparation'}}
    if isinstance(value,list):return [remove_old_service_state(v,owned_keys) for v in value]
    return value


def rebind_resource_metadata(value,updates):
    if isinstance(value,dict):
        result={k:rebind_resource_metadata(v,updates) for k,v in value.items()}
        mount=result.get('mount')
        if mount in updates:
            actual=updates[mount]
            result['sha256']=actual['sha256']
            if 'bytes' in result:result['bytes']=actual['bytes']
            if 'path' in result:result['path']=actual['path']
        return result
    if isinstance(value,list):return [rebind_resource_metadata(v,updates) for v in value]
    return value


def initialize_attempt_services(raw,request_path,response_path,workspace=None,services=None,attempt_id=None):
    """Prepare fresh mutable service objects, then rebind every turn snapshot.

    No model/actor is called. Non-service requests do not load credentials or
    initializer modules. Returned runtime inputs are delivered only at their
    original availability index, and canonical user text remains byte-equal.
    """
    request_path=Path(request_path).resolve();parent=request_path.parent
    workspace=choose_workspace(raw,request_path,response_path,workspace)
    raw=copy.deepcopy(raw);original_inputs=(raw.get('input'),raw.get('followup_inputs',[]))
    context=raw.get('context',{})
    sid=context.get('source_session_id') if isinstance(context,dict) else None
    plan_path=BASE/'environment/personal_service_preparation_plan.json'
    plan=json.loads(plan_path.read_text('utf-8-sig')) if plan_path.is_file() else {'sources':[]}
    personal=next((s for s in plan['sources'] if s['session_id']==sid),None)
    meeting_plan_path=BASE/'environment/meeting_service_preparation_plan.json'
    meeting_plan=json.loads(meeting_plan_path.read_text('utf-8-sig')) if meeting_plan_path.is_file() else {'sources':[]}
    meeting=next((s for s in meeting_plan['sources'] if s['session_id']==sid and 'tencent_meeting_experiment' in s['context']),None)
    declared_meeting=isinstance(context,dict) and ('tencent_meeting_experiment' in context or any('tencent_meeting_experiment' in x for x in context.get('source_service_preparation',[]) if isinstance(x,dict)))
    if declared_meeting and not meeting:raise ValueError('Declared meeting source is missing its packaged preparation plan')
    if not personal and not meeting:
        return raw,workspace,{'service_initialization_required':False,'source_session_id':sid,'remote_authentication_calls':0}

    # Preserve controller-staged future inputs; materialize only current inputs.
    for resource in raw.get('resources',[]):
        if resource.get('available_from_dispatch_index',0)>0:
            raise ValueError('Future resources must be staged, never in initial resources')
        source=Path(resource['path']).resolve();target=(workspace/resource['mount']).resolve()
        if not target.is_relative_to(workspace):raise ValueError('Input mount escapes attempt workspace')
        if hashlib.sha256(source.read_bytes()).hexdigest()!=resource['sha256']:raise ValueError('Initial input SHA differs from request')
        target.parent.mkdir(parents=True,exist_ok=True)
        if source!=target:shutil.copyfile(source,target)
        resource['path']=str(target)
    attempt_id=attempt_id or 'attempt_'+hashlib.sha256(str(parent).encode()).hexdigest()[:32]
    state_root=parent/'service_initialization';prepared={};events=[];runtime_files=[];receipts={}
    runtime=BASE/'environment/preparation_runtime'
    if personal:
        module=load_module(runtime/'initialize_source_attempt.py','packaged_source_attempt_initializer')
        result=module.initialize(plan_path,sid,attempt_id,state_root/'personal',workspace=None,credentials=services or LAYER.parent/'private/services_active.json')
        prepared.update(result['context']);events.extend(result['contexts_by_turn'])
        runtime_files.extend(result['runtime_files']);receipts['personal']=result
        module.materialize({'runtime_files':[f for f in runtime_files if not f.get('available_from_dispatch_index',0)]},workspace)
    if meeting:
        module=load_module(runtime/'meeting_attempt_initializer.py','packaged_meeting_attempt_initializer')
        result=module.initialize_meeting_attempt(meeting_plan_path,sid,attempt_id,state_root/'meeting',workspace)
        if not result.get('passed'):raise ValueError('Fresh meeting preparation did not pass')
        actual=Path(result['context_path']).resolve()
        runtime_files.append({'path':str(actual),'mount':'service-context/tencent-meeting.json','sha256':hashlib.sha256(actual.read_bytes()).hexdigest(),'available_from_dispatch_index':0})
        mapped={**meeting['context']['tencent_meeting_experiment'],'attempt_id':attempt_id,'fresh_source_context':result['source_context']}
        prepared['tencent_meeting_experiment']=mapped;receipts['meeting']=result
        if meeting['context'].get('meeting_link_adaptations'):
            initial=result['source_context'].get('initial_meetings',[])
            if len(initial)!=len(meeting['context']['meeting_link_adaptations']):raise ValueError('Meeting link aliases do not match fresh initial objects')
            prepared['meeting_link_adaptations']=[{**alias,'experimental_url':obj['join_url'],'experimental_meeting_code':obj['meeting_code'],'experimental_meeting_id':obj['meeting_id'],'origin':'fresh real current-attempt synthetic initial state'} for alias,obj in zip(meeting['context']['meeting_link_adaptations'],initial)]

    updates={};future={e['user_index']:e for e in raw.get('turn_resources',[])}
    for file in runtime_files:
        when=file.get('available_from_dispatch_index',0)
        source=Path(file['path']).resolve()
        actual=hashlib.sha256(source.read_bytes()).hexdigest()
        if actual!=file['sha256']:raise ValueError('Fresh service runtime-file SHA differs')
        target=(workspace/file['mount']).resolve() if when==0 else parent/'staged_resources'/str(when)/file['mount']
        if when==0 and not target.is_relative_to(workspace):raise ValueError('Runtime input escapes attempt workspace')
        if when and not target.resolve().is_relative_to(parent/'staged_resources'):raise ValueError('Staged service input escapes controller directory')
        target.parent.mkdir(parents=True,exist_ok=True)
        if source!=target:shutil.copyfile(source,target)
        item={**file,'path':str(target),'sha256':actual,'bytes':target.stat().st_size,'available_from_dispatch_index':when}
        updates[file['mount']]=item
        if when==0:
            existing=next((r for r in raw.setdefault('resources',[]) if r['mount']==file['mount']),None)
            if existing:existing.update(item)
            else:raw['resources'].append(item)
        else:
            entry=future.setdefault(when,{'user_index':when,'resources':[]})
            existing=next((r for r in entry['resources'] if r['mount']==file['mount']),None)
            if existing:existing.update(item)
            else:entry['resources'].append(item)
    if future:raw['turn_resources']=[future[k] for k in sorted(future)]

    owned={'personal_mail','personal_feishu','personal_ima','personal_feishu_document_mapping','personal_feishu_wiki','source_gitee_experiment'}
    if meeting:owned.update({'tencent_meeting_experiment','meeting_link_adaptations'})
    summary={'source_session_id':sid,'attempt_id':attempt_id,'fresh_mutable_objects_prepared':True,'source_initialization_receipts_archived':True,'previous_attempt_objects_reused':False,'original_enterprise_history_restored':False}
    def snapshot(old,index):
        clean=remove_old_service_state(old,owned);state=copy.deepcopy(prepared)
        for event in sorted(events,key=lambda e:e['user_index']):
            if event['user_index']<=index:state.update(copy.deepcopy(event['context']))
        clean.update(state);clean['source_service_preparation']=[copy.deepcopy(state)]
        clean['attempt_service_preparation']=summary
        return rebind_resource_metadata(clean,updates)
    raw['context']=snapshot(raw['context'],0)
    by_turn={t['user_index']:t for t in raw.get('turn_contexts',[])}
    for index in range(1,len(raw.get('followup_inputs',[]))+1):
        entry=by_turn.setdefault(index,{'user_index':index,'context':copy.deepcopy(context)})
        entry['context']=snapshot(entry['context'],index)
    raw['turn_contexts']=[by_turn[k] for k in sorted(by_turn)]
    if isinstance(raw.get('resource_link_context'),dict):raw['resource_link_context']=snapshot(raw['resource_link_context'],0)
    declared_services=copy.deepcopy(raw.get('services',[]))
    if not isinstance(raw.get('services'),dict):raw['services']={}
    previous_experiment_context=raw['services'].get('experiment_context',{})
    if not isinstance(previous_experiment_context,dict):previous_experiment_context={}
    raw['services']['experiment_context']=remove_old_service_state(previous_experiment_context,owned)
    service_context=raw['services']['experiment_context']
    for key,value in prepared.items():service_context[key]=copy.deepcopy(value)
    if original_inputs!=(raw.get('input'),raw.get('followup_inputs',[])):raise ValueError('Service initialization changed canonical user text')
    receipt={'schema':'clean-consumer-attempt-service-preparation-v1',**summary,'workspace':str(workspace),'runtime_files':list(updates.values()),'service_receipts':receipts,'declared_services_before_normalization':declared_services,'future_runtime_files_not_preloaded':True,'canonical_user_inputs_unchanged':True,'model_actor_calls':0}
    state_root.mkdir(parents=True,exist_ok=True)
    (state_root/'consumer_initialization.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return raw,workspace,receipt

def main():
    p=argparse.ArgumentParser();p.add_argument('request');p.add_argument('response');p.add_argument('--workspace')
    p.add_argument('--services',default=str(LAYER.parent/'private/services_active.json'))
    p.add_argument('--credentials',default='D:/skillloop/output/20261008_openclaw_eval/private/model_evolution_32768.json')
    p.add_argument('--timeout',type=int,default=1800)
    a=p.parse_args();request=hydrate(a.request)
    raw,workspace,preparation=initialize_attempt_services(json.loads(request.read_text('utf-8-sig')),request,a.response,a.workspace,Path(a.services).resolve())
    request.write_text(json.dumps(raw,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    spec=importlib.util.spec_from_file_location('preserved_personal_layer',LAYER)
    layer=importlib.util.module_from_spec(spec);spec.loader.exec_module(layer)
    layer.ACTIVE_BENCH=BASE;layer.ORIGINAL=BASE/'environment/runtime/consumer.py'
    consumer=layer.install_layer(Path(a.services).resolve());original_command=consumer.build_command
    original_project=consumer.project_request
    def project(raw,workspace):
        result=original_project(raw,workspace)
        def update_business_services(context):
            state=context.get('attempt_service_preparation',{})
            services=context.setdefault('business_services',{})
            services['per_source_identity_and_url_mapping_completed']=bool(state.get('fresh_mutable_objects_prepared'))
            services['current_attempt_service_preparation']=state or {'service_initialization_required':False}
            services.setdefault('commands',{}).update({'mail':'python /opt/real-services/mail_cli.py status|list|read|send','ima':'python /opt/real-services/source_ima_cli.py --plan /workspace/services/source_ima.json list|read|search|export','gitee':'python /opt/experiment-services/source_gitee_cli.py --state /workspace/services/gitee_activity.json projects|repositories|members|search|issues|read|create-issue|update-issue|close-issue','tencent_meeting':'python /opt/experiment-services/meeting_source.py <schedule_meeting|get_meeting|get_user_meetings|update_meeting|cancel_meeting> --source-id <source_session_id> --context-file /workspace/service-context/tencent-meeting.json --json-file <arguments.json>','wecom':'python /opt/experiment-services/wecom_self.py show|send --message-file <message.md>','cron_registration':'python /opt/experiment-services/cron_registration.py add|update|delete|list|verify|ensure --source-id <source_session_id>','feishu':'lark-cli docs/wiki --as user; declared private chat messages --as bot'})
        update_business_services(result['context'])
        for turn in result.get('turn_contexts',[]):
            if isinstance(turn.get('context'),dict):update_business_services(turn['context'])
        return result
    consumer.project_request=project
    def command(*args,**kwargs):
        result=original_command(*args,**kwargs)
        transport=Path(args[3] if len(args)>3 else kwargs['transport'])
        overrides=BASE/'environment/preparation_runtime'
        if overrides.is_dir():
            for file in overrides.iterdir():
                if file.is_file():shutil.copyfile(file,transport/'personal_service_tools'/file.name)
        image=args[0] if args else kwargs['image'];backend=args[6] if len(args)>6 else kwargs.get('backend','native')
        extra=['--mount','type=bind,source='+consumer.mount_source(transport/'personal_service_tools',backend)+',target=/opt/experiment-services,readonly']
        current_sid=raw.get('context',{}).get('source_session_id')
        private_config=BASE/'environment/private_runtime_mounts.json'
        if private_config.is_file():
            for mapping in json.loads(private_config.read_text('utf-8-sig')):
                if mapping.get('applies_to_sources') and current_sid not in mapping['applies_to_sources']:continue
                extra+=['--mount','type=bind,source='+consumer.mount_source(mapping['path'],backend)+',target='+mapping['mount']+',readonly']
        result[result.index(image):result.index(image)]=extra
        index=result.index('/opt/real-services/service_bootstrap.py')
        result.insert(index,'/opt/eval-adapter/builtin_service_bootstrap.py')
        result.insert(result.index('/opt/eval-adapter/container_runner.py'),'/opt/experiment-services/darwin_bootstrap.py')
        workspace=Path(args[2] if len(args)>2 else kwargs['workspace'])
        if (workspace/'services/gitee_activity.json').is_file():
            result.insert(result.index('/opt/eval-adapter/container_runner.py'),'/opt/experiment-services/source_gitee_bootstrap.py')
        if (workspace/'services/source_mail.json').is_file():
            result.insert(result.index('/opt/eval-adapter/container_runner.py'),'/opt/experiment-services/source_mail_bootstrap.py')
        return result
    consumer.build_command=command
    image=json.loads((BASE/'environment/config.json').read_text('utf-8-sig'))['image']
    consumer.run(request,a.response,image=image,timeout=a.timeout,credentials=a.credentials,backend='wsl',workspace=str(workspace))

if __name__=='__main__':main()
