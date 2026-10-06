"""Publish AI-assisted labels and a reduced human queue without changing 066/068."""
from pathlib import Path
from collections import Counter
import copy,hashlib,importlib.util,json,re,sys
ROOT=Path(__file__).resolve().parent;P=ROOT/'private';OLD=ROOT.parent/'annotation_068'
spec=importlib.util.spec_from_file_location('run069',ROOT/'run_annotation.py');run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)
def dump(p,x):run.dump(p,x)
def k(role,nid):return role+':'+nid

def main():
    data=json.loads((OLD/'private/review_data.json').read_text(encoding='utf-8'));human=json.loads((P/'human_annotations_original.json').read_text(encoding='utf-8'))
    labels=json.loads((P/'seed_labels.json').read_text(encoding='utf-8'));jobs=json.loads((P/'jobs.json').read_text(encoding='utf-8'));queries=json.loads((P/'queries.json').read_text(encoding='utf-8'));missing=[]
    for job in jobs:
        f=P/'responses'/(job['id']+'.json')
        lookup={q['q']:case for case in job['cases'] for q in case['questions']}
        if f.exists():
            saved=json.loads(f.read_text(encoding='utf-8'));rows,_=run.validate(saved['text'],job)
        else:
            missing.append(job['id']);rows=[{'q':qid,'d':'U','t':[],'r':'调用未取得可用返回'} for qid in lookup]
        for row in rows:
            q=queries[str(row['q'])];case=lookup[row['q']];targets=[case['node_map'][str(n)] for n in row['t']]
            labels.setdefault(q['session'],{})[q['key']]={'decision':{'M':'matched','N':'none','U':'uncertain'}[row['d']],
                'targets':targets,'note':row.get('r','模型未提供理由'),'basis':'ai_semantic_annotation_069',
                'granularity':'deduplicated_content_group','source_job':job['id'],'candidate_set_complete':q['complete']}
    dump(P/'first_pass_labels.json',labels)
    audit_jobs=[]
    for audit_dir in ['audit','short_audit']:
        jf=P/audit_dir/'jobs.json'
        if jf.exists():audit_jobs.extend([{**j,'response_dir':audit_dir} for j in json.loads(jf.read_text(encoding='utf-8'))])
    audit_changes=[];audit_missing=[]
    for job in audit_jobs:
        f=P/job['response_dir']/'responses'/(job['id']+'.json');lookup={q['q']:c for c in job['cases'] for q in c['questions']}
        if f.exists():
            saved=json.loads(f.read_text(encoding='utf-8'));rows,_=run.validate(saved['text'],job)
        else:
            audit_missing.append(job['id']);rows=[{'q':qid,'d':'U','t':[],'r':'定向复核未取得结果'} for qid in lookup]
        for row in rows:
            q=queries[str(row['q'])];case=lookup[row['q']];before=labels[q['session']][q['key']]
            after={'decision':{'M':'matched','N':'none','U':'uncertain'}[row['d']],
                   'targets':[case['node_map'][str(n)] for n in row['t']],'note':row.get('r','复核无文字理由'),
                   'basis':'ai_review_069','granularity':'deduplicated_content_group','source_job':job['id']}
            labels[q['session']][q['key']]=after
            if before['decision']!=after['decision'] or set(before['targets'])!=set(after['targets']):audit_changes.append({'q':row['q'],'session':q['session'],'key':q['key'],'before':before,'after':after})
    dump(P/'audit_changes.json',audit_changes)
    # Direct source reading found one clear action mismatch that the batch reviewer repeated.
    # This is an assistant correction, never a user-provided gold label.
    overrides=json.loads((P/'assistant_review_overrides.json').read_text(encoding='utf-8'))
    for fix in overrides:
        q=queries[str(fix['q'])]
        assert q['key'] not in human['labels'].get(q['session'],{})
        labels[q['session']][q['key']]={**labels[q['session']][q['key']],**fix['label']}
    dump(P/'labels_before_reconciliation.json',labels);log=[]
    for s in data['sessions']:
        sid=s['id'];ls=labels.setdefault(sid,{});hum=human['labels'].get(sid,{})
        # Human decisions are immutable; project their explicit edges onto AI decisions.
        for key,l in list(ls.items()):
            if key in hum:continue
            role,nid=key.split(':',1);opposite=s['assistants'] if role=='user' else s['users'];before=copy.deepcopy(l)
            required=[];allowed=[]
            for n in opposite:
                h=hum.get(k(n['role'],n['id']))
                if h and h['decision']!='uncertain':
                    if nid in h['targets']:required.append(n['id']);allowed.append(n['id'])
                else:allowed.append(n['id'])
            targets=[t for t in l['targets'] if t in allowed]
            targets=list(dict.fromkeys(targets+required))
            if required:
                l['decision']='matched';l['targets']=targets;l['note']='尊重已有人工匹配；'+l['note']
            elif l['decision']=='matched':
                l['targets']=targets
                if not targets:l['decision']='uncertain';l['note']='原AI匹配与人工判断冲突，交回核验'
            if l!=before:log.append({'session':sid,'key':key,'type':'human_constraint','before':before,'after':copy.deepcopy(l)})
        # Positive AI edges are reciprocal. A positive/none disagreement remains uncertain.
        for key,l in list(ls.items()):
            if l['decision']!='matched':continue
            role,nid=key.split(':',1);oprole='assistant' if role=='user' else 'user'
            for oid in list(l['targets']):
                ok=k(oprole,oid);ol=ls.get(ok)
                if not ol or ok in hum:continue
                before=copy.deepcopy(ol)
                if ol.get('basis')=='ai_review_069' and ol['decision']!='uncertain' and nid not in ol['targets']:
                    if key not in hum:
                        old=copy.deepcopy(l);l['decision']='uncertain';l['targets']=[];l['note']='与定向语义复核结果不一致，保留核验'
                        log.append({'session':sid,'key':key,'type':'audit_over_prior_prediction','before':old,'after':copy.deepcopy(l)});break
                if ol['decision']=='matched' and nid not in ol['targets']:
                    ol['targets'].append(nid);ol['note']='合并另一方向的AI正向对应；'+ol['note']
                elif ol['decision']=='none':
                    ol['decision']='uncertain';ol['targets']=[];ol['note']='AI两方向判断冲突，需人工复核'
                if ol!=before:log.append({'session':sid,'key':ok,'type':'reciprocal_consistency','before':before,'after':copy.deepcopy(ol)})
        for key,h in hum.items():assert ls[key]==h
        assert all(k(t['role'],t['id']) in ls for t in s['issues'])
    dump(P/'reconciliation_log.json',log)
    seed={'schema':'evomind-human-links-v1','dataset':data['fingerprint'],'labels':labels,'drafts':copy.deepcopy(human.get('drafts',{})),
          'history':copy.deepcopy(human.get('history',[])),'ai_assistance_version':'069','annotation_scope':'semantic_correspondence_not_success_or_chronology'}
    counts=Counter();remaining=[]
    for s in data['sessions']:
        pending=[]
        for t in s['issues']:
            key=k(t['role'],t['id']);l=labels[s['id']][key];counts['items']+=1;counts[l['decision']]+=1
            counts['human_items']+=key in human['labels'].get(s['id'],{})
            if l['decision']=='uncertain':pending.append({'key':key,'reason':l['note']})
        if pending:remaining.append({'session_id':s['id'],'items':pending});counts['sessions_needing_human']+=1
        else:counts['sessions_resolved']+=1
    counts['sessions']=len(data['sessions']);counts['human_labels_preserved']=sum(len(ls) for ls in human['labels'].values())
    ledger=[]
    for path in [P/'request_ledger.jsonl',P/'audit/request_ledger.jsonl',P/'short_audit/request_ledger.jsonl']:
        if path.exists():ledger.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines())
    plan=json.loads((ROOT/'plan.json').read_text(encoding='utf-8'))
    summary={**counts,'jobs':len(jobs),'jobs_without_response':len(missing),'api_attempts':len(ledger),
        'audit_jobs':len(audit_jobs),'audit_jobs_without_response':len(audit_missing),'audit_changed_items':len(audit_changes),'assistant_source_corrections':len(overrides),
        'reported_input_tokens':sum(sum(e.get('usage',{}).get(t,0) for t in ('input_tokens','cache_read_input_tokens','cache_creation_input_tokens')) for e in ledger),
        'reported_output_tokens':sum(e.get('usage',{}).get('output_tokens',0) for e in ledger),
        'failed_attempts':sum(e['status']=='failed' for e in ledger),'reused_prior_semantic_items':plan['reused_prior_semantic_items'],
        'no_opposite_content_items':plan['no_opposite_content_items'],'new_query_items':plan['new_query_items'],
        'remaining_human_items':counts['uncertain'],'resolved_items':counts['matched']+counts['none'],
        'independent_accuracy_measured':False,'cash_cost':'UNKNOWN','unknown_failed_usage_not_zero':True}
    dump(ROOT/'summary.json',summary);dump(P/'ai_assisted_annotations.json',seed);dump(P/'remaining_human_review.json',remaining);dump(P/'incomplete_jobs.json',missing)
    data['seed']=seed;data['ai_summary']=summary;dump(P/'review_data.json',data)
    # Keep the proven data/state UI and give AI predictions explicit, separate labels.
    core=(OLD/'annotation_core.js').read_text(encoding='utf-8')
    old="validateLabel(s,role,id,label);const copy=clone(state.labels[s.id]||{});copy[key(role,id)]=clone(label);validateSession(s,copy);"
    new="""validateLabel(s,role,id,label);const copy=clone(state.labels[s.id]||{});copy[key(role,id)]=clone(label);
    for(const other of nodes(s,role==='user'?'assistant':'user')){const ok=key(other.role,other.id),ol=copy[ok];if(!ol||ol.decision==='uncertain'||label.decision==='uncertain')continue;
      if(label.targets.includes(other.id)!==ol.targets.includes(id)&&ol.basis!=='human_explicit_selection'){copy[ok]={...ol,decision:'uncertain',targets:[],note:'与最新人工修订冲突，需复核',basis:'ai_conflict_after_human'};}}
    validateSession(s,copy);"""
    assert old in core;core=core.replace(old,new)
    # A later human correction may replace an AI prediction during backup restore.
    core=core.replace("if(dest[k]&&!equivalent(dest[k],l))throw", "if(dest[k]&&!equivalent(dest[k],l)&&dest[k].basis==='human_explicit_selection'&&(l.basis!=='human_explicit_selection'||!(Date.parse(l.updatedAt)>Date.parse(dest[k].updatedAt))))throw")
    core=core.replace("dest[k]=clone(l);", "if(!(dest[k]&&dest[k].basis==='human_explicit_selection'&&l.basis!=='human_explicit_selection'))dest[k]=clone(l);")
    core=core.replace("validateSession(data.sessions.find(s=>s.id===sid),dest);", "const ss=data.sessions.find(s=>s.id===sid);for(const [hk,hl] of Object.entries(dest)){if(hl.basis==='human_explicit_selection'){const at=hk.indexOf(':');result.labels[sid]=apply(result,ss,hk.slice(0,at),hk.slice(at+1),hl);}}validateSession(ss,result.labels[sid]);")
    (ROOT/'annotation_core.js').write_text(core,encoding='utf-8')
    template=(OLD/'review_ui.html').read_text(encoding='utf-8')
    replacements={
      'EvoMind · 人工匹配标注':'EvoMind · AI辅助标注与剩余核验',
      '505 条会话 · 逐项核对用户输入与 AI 回复 · 同文折叠，原文不改写':'AI 已接手初标 · 默认仅显示仍需你判断的会话 · 你的原标注已保留',
      "KEY='evomind-annotation-068:'+DATA.fingerprint":"KEY='evomind-annotation-069:'+DATA.fingerprint",
      "let state=C.empty(DATA.fingerprint)":"let state=C.clone(DATA.seed)",
      '<option value="pending">尚未全部确认</option>':'<option value="pending" selected>只看仍需人工判断</option>',
      '<option value="done">待核验项已全部确认</option>':'<option value="done">人工或 AI 已给出明确判断</option>',
      '<option value="issues">本会话待核验项</option>':'<option value="remaining">只看仍无法判断的项</option><option value="issues">查看原待核验项全部判断</option>',
      "$('unitFilter').value='issues'":"$('unitFilter').value='remaining'",
      "return !l?'未标注':l.decision==='matched'?'已确认匹配':l.decision==='none'?'已确认无匹配':'暂不能判断';":"return !l?'未标注':(l.basis==='human_explicit_selection'?'人工':'AI')+(l.decision==='matched'?'：匹配':l.decision==='none'?'：无匹配':'：无法判断');",
      ":s.issues;}":":$('unitFilter').value==='remaining'?s.issues.filter(t=>!labelFor(s,t)||labelFor(s,t).decision==='uncertain'):s.issues;}",
      "${p.done?' · 完成':''}":"${p.done?' · 已有明确判断':''}",
      "已确认 ${p.resolved} / ${p.total} 项":"已有判断 ${p.resolved} / ${p.total} 项 · 待人工 ${p.total-p.resolved}",
      "已确认 ${resolved} / 2674 项 · 已完成 ${done} / 505 条会话 · 已查看并提交 ${reviewed} 项":"已有明确判断 ${resolved} / 2674 项 · 还需你判断 ${2674-resolved} 项 / ${505-done} 条会话",
      "人工状态：<strong>":"当前标注来源与状态：<strong>",
      "机器候选不会自动勾选":"已显示AI预标注；可修改后确认，成为你的人工标注",
      "对侧人工状态：":"对侧标注状态：",
      "已有机器匹配":"已有机器匹配",
      "'evomind-human-annotations-'":"'evomind-ai-assisted-annotations-'",
      '已合并导入人工标注；不同的已有标注不会被静默覆盖。':'已合并导入：人工优先；已恢复文件中较新的人工修改。',
      "chooseSession(sid);\n</script>":"chooseSession((DATA.sessions.find(s=>!C.progress(s,state).done)||DATA.sessions[0]).id);\n</script>"
    }
    for old,new in replacements.items():
        if old!=new:assert old in template,old
        template=template.replace(old,new)
    template=template.replace("$('unitFilter').value='remaining';const s=session();", "const s=session();$('unitFilter').value=C.progress(s,state).done?'issues':'remaining';")
    template=template.replace('机器已有对应也会显示','机器已有对应也会显示')
    # Import of the original human backup remains compatible; exported AI labels are never renamed human.
    template=template.replace('同文折叠，原文不改写','同文折叠，原文不改写')
    data_text=run.js(data).replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    page=template.replace('/*__CORE__*/',core).replace('/*__DATA__*/',data_text)
    (ROOT/'review_ui_generated.html').write_text(template,encoding='utf-8');(P/'index.html').write_text(page,encoding='utf-8')
    manifest={'dataset':data['fingerprint'],'human_backup_sha256':hashlib.sha256((P/'human_annotations_original.json').read_bytes()).hexdigest(),
        'html_sha256':hashlib.sha256(page.encode()).hexdigest(),'html_bytes':len(page.encode()),'human_labels_preserved':True,
        'source_066_and_068_not_modified':True,'browser_visual_verification':'NOT_RUN_FILE_URL_POLICY_BLOCK'}
    dump(ROOT/'manifest.json',manifest);print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
