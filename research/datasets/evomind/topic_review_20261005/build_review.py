"""Build a local human review artifact for the 41 uncertain/topic-template sessions."""
from pathlib import Path
import csv, hashlib, html, json, sys

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
OUT = ROOT/'private'

def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def dump(path, value): path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    source_path=BASE/'matched_066/private/evomind_conversations.json'
    label_path=BASE/'analysis_20261005/private/session_task_categories.json'
    annotation_path=BASE/'accepted_071/private/accepted_annotations.json'
    hashes={str(p.relative_to(BASE)): sha(p) for p in [source_path,label_path,annotation_path]}
    source=json.loads(source_path.read_text(encoding='utf-8'))
    labels=json.loads(label_path.read_text(encoding='utf-8'))
    annotations=json.loads(annotation_path.read_text(encoding='utf-8'))['labels']
    cleaned={x['session_id']:x for x in json.loads((BASE/'analysis_20261005/private/conversation_cluster_rows.json').read_text(encoding='utf-8'))}
    categories=json.loads((BASE/'analysis_20261005/category_definitions.json').read_text(encoding='utf-8'))
    selected=sorted((x for x in labels if x['primary'] in ['UNCLEAR','PLATFORM']), key=lambda x:(x['primary']!='UNCLEAR',x['session_id']))
    assert len(selected)==41 and sum(x['primary']=='UNCLEAR' for x in selected)==32
    OUT.mkdir(exist_ok=True); (OUT/'conversations').mkdir(exist_ok=True)
    def node(group):
        occurrences=group['occurrences']
        return {'id':group['group_id'],'role':group['role'],'text':group['content'],'position':min((o.get('source_line',10**12) for o in occurrences),default=10**12),'source_messages':[o['id'] for o in occurrences],'source_lines':[o.get('source_line') for o in occurrences]}
    cases=[]
    for label in selected:
        sid=label['session_id']; session=source[sid]
        users=sorted(map(node,session['user_requests']), key=lambda x:(x['position'],x['id']))
        assistants=sorted(map(node,session['assistant_contents']), key=lambda x:(x['position'],x['id']))
        userids={x['id'] for x in users}; aiids={x['id'] for x in assistants}
        edges={(u,a['assistant_group_id']) for a in session['associations'] for u in a.get('user_group_ids',[])}
        overlay=annotations.get(sid,{})
        for key, label071 in overlay.items():
            role,gid=key.split(':',1)
            edges={e for e in edges if (e[0] if role=='user' else e[1])!=gid}
        for key, label071 in overlay.items():
            role,gid=key.split(':',1)
            if label071['decision']=='matched':
                edges.update((gid,t) if role=='user' else (t,gid) for t in label071['targets'])
        assert all(u in userids and a in aiids for u,a in edges)
        clean=cleaned[sid]; cmap=dict(zip(clean['user_groups'],clean['clean_user_texts']))
        for u in users:
            u['clean_text']=cmap.get(u['id'],u['text'])
            u['replies']=[a['id'] for a in assistants if (u['id'],a['id']) in edges]
        for a in assistants:
            a['user_ids']=[u['id'] for u in users if (u['id'],a['id']) in edges]
        cases.append({'id':sid,'title':session['session_metadata'].get('title',''),'initial_category':label['primary'],'initial_label':categories[label['primary']],'reason':label['reason'],'confidence':label['confidence'],'evidence_user':label['evidence_user'],'users':users,'assistants':assistants,'edges':[list(e) for e in sorted(edges)],'annotation_overlay_applied':bool(overlay)})
    assert sum(len(x['users']) for x in cases)==185
    assert sum(len(x['assistants']) for x in cases)==263
    fingerprint=hashlib.sha256(json.dumps({'inputs':hashes,'sessions':[x['id'] for x in cases]},sort_keys=True).encode()).hexdigest()
    data={'schema':'evomind-topic-review-cases-v1','fingerprint':fingerprint,'categories':{k:v for k,v in categories.items() if k not in ['UNCLEAR','PLATFORM']},'cases':cases}
    dump(OUT/'review_cases.json',data)
    with (OUT/'会话清单.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.writer(f); w.writerow(['会话编号','原分类','归类依据','用户正文组数','AI正文组数','原始标题（仅参考）'])
        w.writerows([x['id'],x['initial_label'],x['reason'],len(x['users']),len(x['assistants']),x['title']] for x in cases)
    for case in cases:
        md=[f"# {case['id']}",f"原分类：{case['initial_label']}。依据：{case['reason']}",f"原始标题（仅作参考）：{case['title']}",'显示去重后的完整正文。按导出位置展示，回复关系叠加071最终标注；不代表原生历史时序已核实。\n']
        seen=set(); amap={x['id']:x for x in case['assistants']}
        for i,u in enumerate(case['users'],1):
            md += [f'## 用户提问 {i}',u['text'],f"来源：{u['id']}\n"]
            for aid in u['replies']:
                if aid in seen:
                    md.append(f'同一AI正文也对应此提问，已在前文展示：{aid}。\n'); continue
                seen.add(aid); md += ['### AI回复',amap[aid]['text'],f'来源：{aid}\n']
            if not u['replies']: md.append('当前关联中没有对应AI回复；不生成或补造。\n')
        for a in case['assistants']:
            if a['id'] not in seen: md += ['## 尚无对应用户提问的AI正文',a['text'],f"来源：{a['id']}\n"]
        (OUT/'conversations'/f"{case['id']}.md").write_text('\n\n'.join(md)+'\n',encoding='utf-8')
    payload=json.dumps(data,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    template=(ROOT/'review_template.html').read_text(encoding='utf-8')
    (OUT/'index.html').write_text(template.replace('/*__DATA__*/',payload),encoding='utf-8')
    assert hashes=={str(p.relative_to(BASE)):sha(p) for p in [source_path,label_path,annotation_path]}
    dump(ROOT/'manifest.json',{'source_hashes':hashes,'fingerprint':fingerprint,'sessions':41,'unclear':32,'platform':9,'user_groups':185,'assistant_groups':263,'source_files_unmodified':True,'all_texts_untruncated':True,'reply_overlay':'071 labels replace incident 066 links; remaining 066 links retained','outputs':{str(p.relative_to(ROOT)):sha(p) for p in [OUT/'index.html',OUT/'review_cases.json',OUT/'会话清单.csv']}})
    print(json.dumps({'sessions':41,'users':185,'assistants':263,'source_files_unmodified':True},ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
