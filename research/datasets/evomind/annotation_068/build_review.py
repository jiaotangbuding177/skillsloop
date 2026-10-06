"""Build a self-contained offline annotation desk for the frozen 505-session queue."""
from pathlib import Path
import hashlib,json,sys

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'matched_066/private'
OUT=ROOT/'private'

def sha(data): return hashlib.sha256(data).hexdigest()
def compact(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))

def main():
    queue=json.loads((BASE/'association_review_queue.json').read_text(encoding='utf-8'))
    sessions=[];source_hashes={};nissues=0
    for row in queue:
        path=BASE/'conversations'/(row['session_id']+'.json');raw=path.read_bytes();source_hashes[row['session_id']]=sha(raw);s=json.loads(raw)
        def convert(node,i):
            return {'id':node['group_id'],'role':node['role'],'number':i+1,'text':node['content'],
                    'occurrences':[{'id':m['id'],'line':m['source_line'],'number':m['numeric_id'],'scheme':m['numeric_scheme'],'time':m['user_created_at'],'status':m['status']} for m in node['occurrences']]}
        users=[convert(n,i) for i,n in enumerate(s['user_requests'])];ais=[convert(n,i) for i,n in enumerate(s['assistant_contents'])]
        um={u['id']:u for u in users};am={a['id']:a for a in ais};edges={e['assistant_group_id']:e for e in s['associations']}
        issues=[];suggestions={};machine={}
        def distance(n,m):return min(abs(a['line']-b['line']) for a in n['occurrences'] for b in m['occurrences'])
        for a in ais:
            e=edges[a['id']];machine[a['id']]={'users':e['user_group_ids'],'reason':e['explanation'],'method':e['method']}
            if not e['user_group_ids']:issues.append({'role':'assistant','id':a['id']})
            candidates=[]
            for r in e['candidate_ranking']:
                uid=r['user_group_id']
                if uid in um:candidates.append({'id':uid,'reason':'上一轮保留的潜在匹配'+('（模型仍有歧义）' if r.get('source')=='model_ambiguous_candidate' else '')})
            for uid in e['user_group_ids']:
                if not any(c['id']==uid for c in candidates):candidates.insert(0,{'id':uid,'reason':'当前机器对应候选，尚非人工确认'})
            for u in sorted(users,key=lambda u:distance(a,u)):
                if len(candidates)>=6:break
                if not any(c['id']==u['id'] for c in candidates):candidates.append({'id':u['id'],'reason':'原文件位置邻近，仅供扩展查找'})
            suggestions['assistant:'+a['id']]=candidates
        linked={uid for e in edges.values() for uid in e['user_group_ids']}
        for u in users:
            if u['id'] not in linked:issues.append({'role':'user','id':u['id']})
            ranked=[]
            for a in ais:
                e=edges[a['id']];matches=[i for i,r in enumerate(e['candidate_ranking']) if r['user_group_id']==u['id']]
                current=u['id'] in e['user_group_ids'];position=any(u['id'] in (p['raw_preceding_user_group'],p['numeric_preceding_user_group']) for p in e['occurrence_position_evidence'])
                rank=0 if current else 1 if matches else 2 if position else 3
                reason='当前机器已有对应' if current else '该AI的旧候选中包含这条用户输入' if matches else '原位置或数字位置提供弱关联' if position else '原文件位置邻近，仅供扩展查找'
                ranked.append((rank,matches[0] if matches else 99,distance(u,a),{'id':a['id'],'reason':reason}))
            suggestions['user:'+u['id']]=[r[3] for r in sorted(ranked,key=lambda r:r[:3])[:6]]
        nissues+=len(issues)
        sessions.append({'id':s['session_id'],'title':s['session_metadata'].get('title') or '无来源标题','conflict':row['original_order_conflict'],
            'unassignedAI':row['unassigned_ai_groups'],'unassignedUser':row['user_groups_without_ai'],'users':users,'assistants':ais,'issues':issues,
            'suggestions':suggestions,'machine':machine,'isolated':{'retry':len(s['retry_controls']),'emptyAI':len(s['empty_ai_events'])}})
    assert len(sessions)==505 and nissues==2674
    fingerprint=sha(compact(source_hashes).encode('utf-8'))
    payload={'version':'annotation-068','fingerprint':fingerprint,'sessions':sessions,'counts':{'sessions':505,'issues':nissues,'aiIssues':798,'userIssues':1876}}
    text=compact(payload)
    safe=text.replace('&','\\u0026').replace('<','\\u003c').replace('>','\\u003e').replace('\u2028','\\u2028').replace('\u2029','\\u2029')
    template=(ROOT/'review_ui.html').read_text(encoding='utf-8');core=(ROOT/'annotation_core.js').read_text(encoding='utf-8')
    page=template.replace('/*__CORE__*/',core).replace('/*__DATA__*/',safe)
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'index.html').write_text(page,encoding='utf-8')
    (OUT/'review_data.json').write_text(text,encoding='utf-8')
    manifest={'source_version':'matched_066','dataset_fingerprint':fingerprint,'source_session_hashes':source_hashes,
              'counts':payload['counts'],'html_bytes':len(page.encode('utf-8')),'html_sha256':sha(page.encode('utf-8')),
              'new_model_calls':0,'initial_human_annotations':0}
    (ROOT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in manifest.items() if k!='source_session_hashes'},ensure_ascii=False))

if __name__=='__main__':sys.stdout.reconfigure(encoding='utf-8');main()
