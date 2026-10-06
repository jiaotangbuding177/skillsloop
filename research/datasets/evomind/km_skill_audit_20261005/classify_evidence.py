"""Conservative classification: reading != application, shell success != task success."""
from pathlib import Path
from collections import defaultdict,Counter
import json,re,csv,sys
ROOT=Path(__file__).resolve().parent;P=ROOT/'private'
tools=json.loads((P/'normalized_skill_tools.json').read_text(encoding='utf-8'))
def flat(x):
    if isinstance(x,str):return x
    if isinstance(x,list):return '\n'.join(flat(y) for y in x)
    if isinstance(x,dict):return '\n'.join(flat(x[k]) for k in ['text','content','output','stdout','stderr','message'] if k in x)
    return ''
events=[]
for i,t in enumerate(tools):
    args=t['args'];args=args if isinstance(args,dict) else {'command':str(args)}
    command=args.get('command',args.get('cmd',''));out=flat(t['output'])
    details=t['output'].get('details',{}) if isinstance(t['output'],dict) else {};details=details if isinstance(details,dict) else {}
    code=details.get('exitCode');failed=t['status']=='failed' or bool(t['error']) or (isinstance(code,int) and code!=0)
    failed=failed or bool(re.match(r'\s*(?:Error:|Error executing|ENOENT|cat:.*No such file|sed:.*No such file)',out,re.I))
    paths=t['paths'];names={p['skill'] for p in paths}
    doc=re.match(r'^\s*---\s*\r?\n([\s\S]{1,3000}?)\r?\n---(?:\s|$)',out)
    # Truncated reads may expose only the YAML opening, name and description.
    head=doc.group(1) if doc else out[:1200] if out.lstrip().startswith('---') else ''
    reported=re.search(r'(?m)^name:\s*["\']?([^\r\n"\']+)',head)
    reported_name=reported.group(1).strip() if reported else None
    if not names and reported_name:names={reported_name}
    kind='path_reference_or_management'
    if t['name']=='read' and out.strip() and not failed and t['status'] in ['completed','done']:
        kind='successful_read'
    elif t['name']=='read':kind='read_failed_or_unconfirmed'
    elif t['name']=='exec':
        docpaths=[p for p in paths if p['path'].lower().endswith(('/skill.md','/openclaw.md'))]
        scripts=[p for p in paths if re.search(r'\.(?:py|sh|js|mjs|cjs)(?:$)',p['path'])]
        if docpaths and re.search(r'\b(?:cat|head|sed|more)\b',command) and out.strip() and not failed and t['status'] in ['completed','done'] and code in [0,None]:kind='successful_shell_doc_read'
        elif scripts and any(re.search(r'\b(?:python(?:[\d.]*)?|bash|sh|node)(?:\s+-[\w-]+)*\s+["\']?'+re.escape(p['path']),command) for p in scripts):
            maintenance=all(re.search(r'/(?:install_[^/]*|check_environment)\.(?:sh|py)$',p['path']) for p in scripts)
            kind='script_help' if re.search(r'--help\b',command) else 'script_management' if maintenance else 'script_execution_attempt'
        elif reported_name and not failed and t['status'] in ['completed','done'] and re.match(r'\s*---',out):kind='successful_shell_doc_read'
    for name in names:
        relevant=[p['path'] for p in paths if p['skill']==name]
        runtime=any('/openclaw-shared-skills/' in p or '/evomind-shared-skills/' in p or '/evomindskills/' in p or '/.openclaw/' in p or '/.evomind/' in p or '/home/km-agent/skills/' in p for p in relevant)
        events.append({'index':i,'skill':name,'session_id':t['session_id'],'tool_call_id':t['tool_call_id'],'tool':t['name'],'status':t['status'],'exit_code':code,'kind':kind,'runtime_skill_path':runtime,'paths':relevant,'reported_yaml_name':reported_name,'source_refs':t['source_refs']})
byname=defaultdict(list)
for e in events:byname[e['skill']].append(e)
rows=[]
for name,es in sorted(byname.items()):
    read=[e for e in es if e['kind'] in ['successful_read','successful_shell_doc_read']]
    execs=[e for e in es if e['kind']=='script_execution_attempt']
    rows.append({'skill':name,'read_records':len({(e['session_id'],e['tool_call_id'],e['index']) for e in read}),'script_attempt_records':len(execs),'read_or_script_sessions':sorted({e['session_id'] for e in read+execs}),'runtime_path_evidence':any(e['runtime_skill_path'] for e in read+execs),'other_event_kinds':dict(Counter(e['kind'] for e in es))})
(P/'classified_events.json').write_text(json.dumps(events,ensure_ascii=False,indent=2),encoding='utf-8')
(ROOT/'skill_evidence_counts.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
unknown=[{'index':i,'tool':t['name'],'session_id':t['session_id'],'status':t['status'],'paths':t['paths'],'kind':sorted({e['kind'] for e in events if e['index']==i}),'args':{k:v for k,v in (t['args'] if isinstance(t['args'],dict) else {}).items() if k in ['path','file_path','limit']},'output_head':flat(t['output'])[:120] if t['name']=='read' else ''} for i,t in enumerate(tools)]
(P/'classification_review.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in unknown)+'\n',encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps({'unique_skills_with_read_or_script':sum(bool(r['read_or_script_sessions']) for r in rows),'unique_successful_reads':sum(r['read_records']>0 for r in rows),'unique_script_attempts':sum(r['script_attempt_records']>0 for r in rows),'runtime_path_read_or_exec':sum(r['runtime_path_evidence'] for r in rows)},ensure_ascii=False))
