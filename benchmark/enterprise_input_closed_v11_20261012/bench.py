"""Portable resource lookup and environment checks; no implicit model dispatch."""
from pathlib import Path
import argparse,copy,hashlib,json,shutil,subprocess,sys,os

BASE=Path(__file__).resolve().parent

def fs(path):
    """Filesystem-only Windows long path; keep request/mount paths ordinary."""
    path=Path(path).resolve()
    value=str(path)
    if os.name=='nt' and len(value)>=240 and not value.startswith('\\\\?\\'):
        return Path('\\\\?\\UNC\\'+value[2:] if value.startswith('\\\\') else '\\\\?\\'+value)
    return path

def rows(path):
    with fs(path).open(encoding='utf-8-sig') as f:return [json.loads(x) for x in f if x.strip()]
def load(path):return json.loads(fs(path).read_text('utf-8-sig'))
def write(path,value):
    path=fs(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='')
def sha(path):
    h=hashlib.sha256()
    with fs(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def file_path(value):
    p=Path(value)
    return p if p.is_absolute() else BASE/p
def resolve_files(value):
    if isinstance(value,list):return [resolve_files(x) for x in value]
    if not isinstance(value,dict):return value
    result={k:resolve_files(v) for k,v in value.items()}
    for k,h in (('path','sha256'),('client_path','client_sha256'),('state_generator_path','state_generator_sha256')):
        if value.get(k) and value.get(h):result[k]=str(file_path(value[k]).resolve())
    return result
def contracts():return rows(BASE/'contracts/evolution.jsonl')+rows(BASE/'contracts/evaluation.jsonl')
def select(session=None,query=None):
    matches=[c for c in contracts() if (not session or c['session_id']==session) and (not query or query in c['title'] or any(query in t['text'] for t in c['replay']['users']))]
    if len(matches)!=1:
        raise ValueError('请选择唯一会话：'+json.dumps([{'title':c['title'],'session_id':c['session_id']} for c in matches[:30]],ensure_ascii=False))
    return matches[0]
def doctor(out):
    checks=[]
    for spec in rows(BASE/'resources/actual_file_inventory.jsonl'):
        p=BASE/spec['path'];checks.append({'path':spec['path'],'exists':p.is_file(),'sha_matches':p.is_file() and sha(p)==spec['sha256']})
    cs=contracts();components={};component_failures=[]
    for c in cs:
        previous=components.setdefault(c['leakage_component_id'],c['split'])
        if previous!=c['split']:component_failures.append(c['session_id'])
    problems=[c for c in checks if not c['exists'] or not c['sha_matches']]
    gaps=load(BASE/'environment/readiness.json') if (BASE/'environment/readiness.json').is_file() else {'status':'environment_admission_in_progress'}
    result={'whole_sources':len(cs),'evolution':sum(c['split']=='evolution' for c in cs),'evaluation':sum(c['split']=='evaluation' for c in cs),
        'actual_file_checks':len(checks),'file_errors':problems,'component_split_errors':component_failures,
        'environment':gaps,'file_integrity_passed':not problems and not component_failures,
        'all_original_task_requirements_verified':False,'model_calls':0}
    write(out,result);print(json.dumps(result,ensure_ascii=False));return 1 if problems or component_failures else 0
def prepare(c,turn,out):
    out=Path(out).resolve()
    if fs(out).exists():raise ValueError('保留已有控制，换一个新输出目录')
    blocked=BASE/'environment/input_preflight_blockers.json'
    if blocked.is_file():
        active={(d['resource_id'],a['sha256']) for d in c['dependencies'] for a in d.get('artifacts',[])}
        failures=[b for b in load(blocked)['blockers'] if b['session_id']==c['session_id']
                  and turn in b['affected_dispatch_indices'] and (b['resource_id'],b['artifact_sha256']) in active]
        if failures:raise ValueError('该原输入的材料字段尚未准入：'+json.dumps([{'file':b['original_filename'],'reason':b['reason']} for b in failures],ensure_ascii=False))
    original=c
    c=resolve_files(copy.deepcopy(c));selected=[t for t in c['replay']['users'] if t['dispatch']]
    if not 0<=turn<len(selected):raise ValueError('所选导出用户记录超出范围')
    user=selected[turn];workspace=out/'workspace';fs(workspace).mkdir(parents=True)
    resources=list(c.get('public_baseline_resources',[]))
    for d in c['dependencies']:
        for a in d['artifacts']:
            if a.get('available_from_dispatch_index',0)<=turn:resources.append(a|{'resource_id':d['resource_id'],'original_path_or_url':d.get('original_path_or_url')})
    seen={};delivered=[]
    for a in resources:
        mount=a['mount'].replace('\\','/').removeprefix('/workspace/')
        if mount.startswith('/') or ':' in mount or '..' in Path(mount).parts:raise ValueError('无效文件mount')
        source=Path(a['path']);target=workspace/mount
        if not fs(source).is_file() or sha(source)!=a['sha256']:raise ValueError('输入文件SHA不一致')
        # Later original attachments overwrite only when their staged version
        # has actually become available; no future bytes are delivered early.
        fs(target.parent).mkdir(parents=True,exist_ok=True);shutil.copyfile(fs(source),fs(target))
        seen[mount]={'path':str(target),'mount':mount,'sha256':a['sha256'],'synthetic':a.get('synthetic',False),'resource_id':a.get('resource_id')}
        delivered.append({'mount':mount,'source_path':str(source.resolve()),'historical_source_reference':original.get('historical_reference_path'),'actual_sha256':a['sha256'],'synthetic':a.get('synthetic',False),'original_reference':a.get('original_path_or_url'),'available_from_dispatch_index':a.get('available_from_dispatch_index',0)})
    context=copy.deepcopy(c['actor']['context'])
    # Scope the explanatory metadata as well as the delivered bytes. A future
    # attachment name, hash or constraint must not enter an earlier control.
    deps_by_id={d['resource_id']:d for d in c['dependencies']}
    scoped_substitutions=[]
    for sub in context.get('resource_substitutions',[]):
        eligible=[a for a in sub.get('artifacts',[]) if a.get('available_from_dispatch_index',0)<=turn and a.get('mount') in seen and a.get('sha256')==seen[a['mount']]['sha256']]
        if sub.get('artifacts') and not eligible:continue
        dep=deps_by_id.get(sub.get('resource_id'),{})
        if not sub.get('artifacts') and dep.get('available_from_dispatch_index',0)>turn:continue
        scoped=copy.deepcopy(sub);scoped['artifacts']=eligible
        scoped_substitutions.append(scoped)
    if 'resource_substitutions' in context:context['resource_substitutions']=scoped_substitutions
    mappings=context.get('link_adaptations',{}).get('mappings',[])
    # A single-record control has one dispatch: admit only mappings whose bytes
    # actually exist, and convert their delivery time to this controlled stage.
    current=[]
    for m in mappings:
        if (m.get('available_from_dispatch_index',0)<=turn and m['mount'] in seen
                and m.get('sha256')==seen[m['mount']]['sha256']):
            n=dict(m);n['available_from_dispatch_index']=0;current.append(n)
    if 'link_adaptations' in context:context['link_adaptations']['mappings']=current
    context['directory_adaptations']=[dict(r,available_from_dispatch_index=0) for r in context.get('directory_adaptations',[]) if r.get('available_from_dispatch_index',0)<=turn]
    context['prior_produced_resources']=[r for r in context.get('prior_produced_resources',[]) if r['available_from_dispatch_index']<=turn]
    service=context.get('business_services',{})
    if service.get('client_path'):
        sim=workspace/'simulation';fs(sim).mkdir(exist_ok=True)
        shutil.copyfile(fs(service['client_path']),fs(sim/'service_client.py'))
        state=load(service['initial_state']['path']) if service.get('initial_state') else {'schema':'synthetic-enterprise-services-v1','synthetic':True,'session_id':c['session_id'],'knowledge':[],'mail':[],'calendar':[],'messages':[]}
        state['knowledge']=[{'id':'doc-'+str(i),'title':Path(m).name,'path':m,'synthetic':True} for i,m in enumerate(seen) if Path(m).suffix.lower() in ('.md','.txt','.csv','.json','.docx','.pdf','.pptx','.xlsx') and not m.startswith(('skills/','reference_support/'))]
        write(sim/'state.json',state)
        context['business_services']={'synthetic':True,'external_delivery':False,'usage':'python /workspace/simulation/service_client.py --state /workspace/simulation/state.json --workspace /workspace <service> <action>；实际读写本题合成状态，无原企业账户认证。'}
    context['environment_control_scope']='原某一导出用户记录的独立环境控制；不认证完整历史回放，不将历史AI或评分要求发给agent。'
    request={'protocol':'single-original-user-environment-control-v1','stage':'environment_control','task_id':c['session_id']+'-user-'+str(user['user_index']),
        'input':user['text'],'context':context,'followup_inputs':[],'resources':list(seen.values()),'learned_skills':[],
        'required_commands':[],'seed':20261008}
    write(out/'request.json',request)
    write(out/'input_receipt.json',{'session_id':c['session_id'],'title':c['title'],'source_message_id':user['source_message_id'],
        'original_user_text_sha256':hashlib.sha256(user['text'].encode()).hexdigest(),'export_user_index':user['user_index'],
        'original_dispatch_index':turn,'delivered':delivered,'historical_AI_sent_to_actor':False,'original_source_modified':False,
        'single_control_reconstructs_full_episode':False,'prior_episode_state_supplied':False,
        'skill_policy':c['baseline_skill_policy'],'environment_all_requirements_verified':False})
    print(json.dumps({'request':str(out/'request.json'),'title':c['title'],'input_files':len(seen),'source_message_id':user['source_message_id']},ensure_ascii=False))
def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['doctor','lookup','prepare'])
    p.add_argument('--session');p.add_argument('--query');p.add_argument('--turn',type=int,default=0);p.add_argument('--output',required=True)
    a=p.parse_args()
    if a.action=='doctor':return doctor(a.output)
    c=select(a.session,a.query)
    if a.action=='lookup':
        state=next((s for s in rows(BASE/'environment/case_readiness.jsonl') if s['session_id']==c['session_id']),{})
        write(a.output,{'title':c['title'],'users':c['replay']['users'],'dependencies':c['dependencies'],'skills':c['baseline_skill_policy'],
            'readiness':{'status':'known_gaps_and_limited_controls_only','all_original_task_requirements_verified':False,
                         'current_case_environment':state},'legacy_source_readiness_snapshot':c['readiness']});return 0
    prepare(c,a.turn,a.output);return 0
if __name__=='__main__':sys.exit(main())
