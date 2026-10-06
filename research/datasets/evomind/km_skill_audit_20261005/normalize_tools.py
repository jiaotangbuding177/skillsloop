from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parent;P=ROOT/'private'
source=json.loads((ROOT.parent/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
path_re=re.compile(r'(?:/[\w.\-]+)*/(?:skills|openclaw-shared-skills|evomind-shared-skills|evomindskills)/([A-Za-z0-9][A-Za-z0-9_.-]*)(?:/[^\s`"\'<>，。；、)\x5c]*)?')
def j(x):return x if isinstance(x,str) else json.dumps(x,ensure_ascii=False)
def flat(x):
    if isinstance(x,str):return x
    if isinstance(x,list):return '\n'.join(flat(y) for y in x)
    if isinstance(x,dict):return '\n'.join(flat(x[k]) for k in ['text','content','output','stdout','stderr','message'] if k in x)
    return ''
def sanitize(t):
    t=re.sub(r'(?i)\bsk-[\w-]{12,}','[KEY]',t)
    t=re.sub(r'(?i)\bak-[\w-]{12,}','[KEY]',t)
    t=re.sub(r'(?i)(\b\w*(?:access[_-]?key|api[_-]?key|token|secret|password)\w*[\s：:=]*["\']?)[^\s"\'`,;；]{8,}',r'\1[HIDDEN]',t)
    t=re.sub(r'(?i)((?:api[_-]?key|access[_-]?token|secret|password|authorization|授权码|密码)[\s：:=]*["\']?)[^\s"\'`,;；]{8,}',r'\1[HIDDEN]',t)
    t=re.sub(r'(?i)Bearer\s+[^\s"\']+','Bearer [HIDDEN]',t)
    return t
records=[]
def add(sid,mid,t,origin,group=''):
    if not isinstance(t,dict):return
    args=t.get('args',t.get('arguments',{}));out=t.get('output','')
    records.append({'session_id':sid,'message_id':mid,'group_id':group,'origin':origin,'tool_call_id':t.get('toolCallId',t.get('tool_call_id')),'name':t.get('name',''),'status':t.get('status',''),'args':args,'output':out,'error':t.get('error'),'started_at':t.get('startedAt')})
for sid,s in source.items():
    for key in ['user_requests','assistant_contents']:
        for g in s[key]:
            for o in g['occurrences']:
                rp=o.get('raw_record',{}).get('rawPayload') or {};ts=rp.get('toolActivity',[]);ts=ts if isinstance(ts,list) else [ts]
                for t in ts:add(sid,o['id'],t,'message_toolActivity',g['group_id'])
sample_text=Path('C:/Users/39835/Downloads/zkys-raw-export-20260925/raw_payload_sample.jsonl').read_text(encoding='utf-8-sig');dec=json.JSONDecoder(strict=False);pos=0
while pos<len(sample_text):
    while pos<len(sample_text) and sample_text[pos].isspace():pos+=1
    if pos>=len(sample_text):break
    x,pos=dec.raw_decode(sample_text,pos)
    if x.get('sessionId') not in source:continue
    rp=x.get('rawPayload') or {};ts=rp.get('toolActivity',[]);ts=ts if isinstance(ts,list) else [ts]
    for t in ts:add(x['sessionId'],x['id'],t,'raw_sample_toolActivity')
    if rp.get('name'):
        t={**rp};t.setdefault('output',x.get('content',''));t.setdefault('status',x.get('status',''))
        add(x['sessionId'],x['id'],t,'raw_sample_top_level')
unique={}
for r in records:
    key=(r['session_id'],r['tool_call_id'] or r['message_id'],r['name'],j(r['args']))
    old=unique.get(key)
    if old is None:unique[key]={**r,'source_refs':[{'origin':r['origin'],'message_id':r['message_id'],'group_id':r['group_id']}], 'snapshot_statuses':[r['status']]}
    else:
        old['source_refs'].append({'origin':r['origin'],'message_id':r['message_id'],'group_id':r['group_id']});old['snapshot_statuses'].append(r['status'])
        if len(j(r['output']))>len(j(old['output'])):old['output']=r['output']
        if r['status']=='completed':old['status']='completed'
        if r.get('error'):old['error']=r['error']
records=list(unique.values())
hits=[]
other_skillmd_paths=[]
for r in records:
    paths=[{'skill':m.group(1),'path':m.group(0)} for m in path_re.finditer(j(r['args']))]
    args=r['args'] if isinstance(r['args'],dict) else {}
    read_path=args.get('path',args.get('file_path',''))
    if r['name']=='read' and isinstance(read_path,str) and read_path.lower().endswith('/skill.md'):
        if not paths:other_skillmd_paths.append({'path':read_path,'status':r['status'],'session_id':r['session_id']})
        name=read_path.rstrip('/').split('/')[-2]
        if name not in ['workspace','tmp','skills','.']:
            paths=[{'skill':name,'path':read_path}]
    output=flat(r['output'])
    if paths or (r['name'] in ['read','exec'] and ('name:' in output[:500] and 'description:' in output[:1200])):
        hits.append({**r,'paths':paths})
(P/'normalized_skill_tools.json').write_text(json.dumps(hits,ensure_ascii=False,indent=2),encoding='utf-8')
review=[]
for i,r in enumerate(hits):
    out=r['output'];details=out.get('details',{}) if isinstance(out,dict) else {};details=details if isinstance(details,dict) else {};review.append({'index':i,'session_id':r['session_id'],'name':r['name'],'status':r['status'],'paths':r['paths'],'args':sanitize(j(r['args']))[:1800],'output_keys':list(out) if isinstance(out,dict) else [],'details':{k:details[k] for k in ['exitCode','status','pid'] if k in details},'error':bool(r['error']),'output_excerpt':sanitize(flat(out))[:1500],'tail':sanitize(flat(out))[-250:] if len(flat(out))>1500 else ''})
(P/'tool_review.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in review)+'\n',encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps({'all_deduplicated_tool_records':len(records),'review_candidates':len(review),'candidate_skill_path_count':len({p['skill'] for r in hits for p in r['paths']}),'other_skillmd_path_count':len(other_skillmd_paths),'review_readme_frontmatter_no_path':sum(not x['paths'] for x in review)},ensure_ascii=False))
