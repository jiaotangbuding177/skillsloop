"""Prepare evidence cards for AI semantic screening, preserving the source corpus."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,hashlib,json,re,sys
R=Path(__file__).resolve().parent;B=R.parent;P=R/'private';P.mkdir(parents=True,exist_ok=True)
SOURCE=B/'matched_066/private/evomind_conversations.json';ANN=B/'accepted_071/private/accepted_annotations.json'
CATEGORIES=B/'analysis_20261005/private/session_task_categories.json'
def dump(p,x):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
helpers=ast.parse((B/'analysis_20261005/analyze_local.py').read_text(encoding='utf-8'))
clean_node=next(x for x in helpers.body if isinstance(x,ast.FunctionDef) and x.name=='clean')
exec(compile(ast.Module(body=[clean_node],type_ignores=[]),'<audited_clean>','exec'))
def redact(t):
    if re.fullmatch(r'[A-Za-z0-9]{16}',t.strip()):return '[独立短凭据或标识已隐藏]'
    if re.fullmatch(r'[A-Za-z0-9_+/=\-]{24,}',t.strip()):return '[独立长标识或凭据已隐藏]'
    t=re.sub(r'([\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\s+)[A-Za-z0-9]{16,}(?=\s|$)',r'\1[邮件凭据已隐藏]',t)
    t=re.sub(r'(\*+@\*+\s+)[A-Za-z0-9]{16,}(?=\s|$)',r'\1[邮件凭据已隐藏]',t)
    t=re.sub(r'(?i)([?&](?:flow_id|user_code|access_token|api_key|token)=)[^&\s]+',r'\1[隐藏]',t)
    t=re.sub(r'(?i)(/api/v1/pq/)[a-f0-9]{12,}(?:\s*[a-f0-9]{8,})?',r'\1[订阅标识已隐藏]',t)
    t=re.sub(r'(?i)\b(?:sk|ak)-[\w-]{12,}','[密钥已隐藏]',t)
    t=re.sub(r'(?i)\b(?:gh[pousr]_[A-Za-z0-9_]{12,}|github_pat_[A-Za-z0-9_]{12,})','[密钥已隐藏]',t)
    t=re.sub(r'(?i)((?:api\s*key|access\s*key|secret\s*key|访问密钥|授权码|密码)\s*[:：=]\s*["\x27]?)[A-Za-z0-9_+/=.\-]{8,}',r'\1[隐藏]',t)
    t=re.sub(r'(?i)Bearer\s+[^\s"\x27]+','Bearer [隐藏]',t)
    return re.sub(r'(?i)(\b[A-Za-z0-9_]*(?:access[_-]?key|api[_-]?key|token|secret|password|authorization)[A-Za-z0-9_]*\b\s*[:：=]\s*["\x27]?)[^\s"\x27`,;；]{8,}',r'\1[隐藏]',t)
def clean_user(t):
    t=re.sub(r'^\[PromptGuard\][^\n]*\n+','',t.strip())
    return clean(t)
def assistant_noise(t,has_tool=False):
    t=t.strip()
    if not t:return '空正文'
    if has_tool:return None
    if re.fullmatch(r'(?:NO_REPLY|HEARTBEAT_OK|好的[。！!]?|收到[。！!]?|明白[。！!]?|你好[。！!]?|谢谢[。！!]?|不客气[。！!]?)',t,re.I):return '纯寒暄或控制回应'
    if len(t)<220 and re.match(r'^(?:让我|我先|我来|我会|接下来|现在我|好的[，,]|收到[，,])',t) and t.endswith(('：',':','…','...')) and not re.search(r'失败|错误|报错|不支持|不能|没有|未能|修复|修正|返回|结果|已经|完成|疏忽|导致|遗漏|错位|遮挡|异常|冲突|查到|诊断|缺少|\d[\.、）]',t):return '无工具证据的纯计划/进度'
    return None
def excerpt(t,n):
    return t if len(t)<=n else t[:n*2//3]+' … '+t[-n//3:]
def assoc(s,labels):
    links={x['assistant_group_id']:set(x['user_group_ids']) for x in s['associations']}
    for k,x in labels.items():
        if k.startswith('user:'):
            uid=k.split(':',1)[1]
            for aids in links.values():aids.discard(uid)
            if x['decision']=='matched':
                for aid in x['targets']:links.setdefault(aid,set()).add(uid)
        elif k.startswith('assistant:'):
            aid=k.split(':',1)[1];links[aid]=set(x['targets']) if x['decision']=='matched' else set()
    return links
source=json.loads(SOURCE.read_text(encoding='utf-8'));annotations=json.loads(ANN.read_text(encoding='utf-8'))['labels']
cats={x['session_id']:x for x in json.loads(CATEGORIES.read_text(encoding='utf-8'))}
# Reuse only extraction/deduplication prefix; never execute historical shell commands.
toolpath=B/'km_skill_audit_20261005/normalize_tools.py'
namespace={'__file__':str(toolpath)}
exec(compile(toolpath.read_text(encoding='utf-8').split('hits=[]')[0],str(toolpath),'exec'),namespace)
toolmap=defaultdict(list)
for i,t in enumerate(namespace['records']):toolmap[t['session_id']].append({'record_index':i,'tool':t['name'],'status':t['status'],'call_id':t['tool_call_id']})
noise_override_path=P/'noise_semantic_overrides.json'
noise_overrides=json.loads(noise_override_path.read_text(encoding='utf-8')) if noise_override_path.exists() else []
protected_noise={(x['session_id'],x['assistant_id']) for x in noise_overrides if x['action']=='KEEP_CONTEXT'}
sessions=[];noise=[]
for sid,s in source.items():
    links=assoc(s,annotations.get(sid,{}));users=[];answers=[]
    for u in s['user_requests']:
        text=clean_user(u['content'])
        users.append({'id':u['group_id'],'text':redact(excerpt(text,180)),'full_chars':len(text),'truncated':len(text)>180,'source_ids':[o['id'] for o in u['occurrences']]})
    for a in s['assistant_contents']:
        tool=any((o.get('raw_record',{}).get('rawPayload') or {}).get('toolActivity') for o in a['occurrences'])
        kind=None if (sid,a['group_id']) in protected_noise else assistant_noise(a['content'],tool)
        if kind:noise.append({'session_id':sid,'assistant_id':a['group_id'],'reason':kind});continue
        text=redact(a['content'])
        lines=[l.strip() for l in text.splitlines() if l.strip()]
        procedural=[l for l in lines if re.search(r'步骤|流程|核对|校验|检查|修正|失败|不应|不能|保留|确保|按.*(?:排序|分组|分类)|先.*再|\d[\.、)]|```',l)]
        snippets=[excerpt(l,100) for l in procedural[:3]]
        score=(len(procedural)>0)*5+min(len(procedural),8)+tool*5+min(len(text)/800,3)
        answers.append({'id':a['group_id'],'users':sorted(links.get(a['group_id'],set())),'text':excerpt(text,260),'method_lines':snippets,'full_chars':len(text),'truncated':len(text)>260,'has_tool_snapshot':bool(tool),'score':score})
    # Evidence cards show all user groups and top content-rich AI groups, not all AI text.
    top=sorted(answers,key=lambda a:-a['score'])[:2]
    top=sorted(top,key=lambda a:next(i for i,x in enumerate(s['assistant_contents']) if x['group_id']==a['id']))
    card={'session_id':sid,'topic':cats[sid]['primary'],'topic_reason':cats[sid]['reason'],'user_count':len(users),'assistant_count':len(s['assistant_contents']),'non_noise_ai_count':len(answers),'tool_names':dict(Counter(x['tool'] for x in toolmap[sid])),'users':users,'assistant_evidence':top,'omitted_assistant_groups':len(answers)-len(top),'order_verified':False}
    sessions.append(card)
dump(P/'all_cards.json',sessions);dump(P/'deterministic_noise.json',noise);dump(P/'tool_refs.json',toolmap)
for shard in range(3):
    assigned=sessions[shard::3];root=P/f'shard_{shard+1}';root.mkdir(exist_ok=True)
    for batch in range(0,len(assigned),25):
        chunk=assigned[batch:batch+25]
        # Compact form retains explicit group identifiers and truncation indicators.
        lines=[]
        for x in chunk:
            lines.append(f"{x['session_id']} | {x['topic']} {x['topic_reason']} | U{x['user_count']} A{x['assistant_count']} 非噪AI{x['non_noise_ai_count']} 工具:{x['tool_names']}")
            for u in x['users']:lines.append(f" U {u['id']} {'[截断]' if u['truncated'] else ''} {u['text']}")
            for a in x['assistant_evidence']:lines.append(f" A {a['id']}→{','.join(a['users'])} {'[截断]' if a['truncated'] else ''} {a['text']} 方法:{' / '.join(a['method_lines'])}")
            if x['omitted_assistant_groups']:lines.append(f" [另有{x['omitted_assistant_groups']}组AI未在卡片展示，可定向扩读]")
        (root/f'batch_{batch//25+1:02d}.txt').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    dump(root/'assigned_ids.json',[x['session_id'] for x in assigned])
dump(R/'preparation_manifest.json',{'date':'2026-10-06','source_sha256':sha(SOURCE),'annotations_sha256':sha(ANN),'categories_sha256':sha(CATEGORIES),'sessions':len(sessions),'users':sum(x['user_count'] for x in sessions),'ai_groups':sum(x['assistant_count'] for x in sessions),'deterministic_ai_noise_groups':len(noise),'noise_reasons':dict(Counter(x['reason'] for x in noise)),'protected_short_ai_groups':len(protected_noise),'noise_override_sha256':sha(noise_override_path) if noise_override_path.exists() else None,'extracted_tool_records':len(namespace['records']),'semantic_review_input':'all user group excerpts + 2 ranked AI excerpts; truncated and omitted explicitly marked','official_api_model_calls':0})
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps({'sessions':len(sessions),'shard_sizes':[len(sessions[i::3]) for i in range(3)],'ai_noise':len(noise),'tool_records':len(namespace['records'])},ensure_ascii=False))
