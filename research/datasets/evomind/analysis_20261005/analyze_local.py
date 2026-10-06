"""Reproducible, offline exploration of existing enterprise conversations.

This script does not recover independent task instances or assert task success.
All raw text and file references stay under private/. No model API is called.
"""
from pathlib import Path
from collections import Counter, defaultdict
import json, re, hashlib, sys
import numpy as np

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
PRIVATE = ROOT / 'private'
PRIVATE.mkdir(parents=True, exist_ok=True)
SOURCE = BASE / 'matched_066/private/evomind_conversations.json'
LABELS = BASE / 'accepted_071/private/accepted_annotations.json'

def dump(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def clean(text):
    # Recognized export wrappers only; never erase short feedback.
    original = text
    for _ in range(3):
        text = re.sub(r'^【个人助手设定】[\s\S]*?设定。\s*', '', text.strip())
        text = re.sub(r'^\[[A-Z][a-z]{2} \d{4}-\d{2}-\d{2} \d{2}:\d{2} GMT\+8\]\s*', '', text)
        text = re.sub(r'^请使用技能「[^」]+」协助当前任务。\s*', '', text)
        text = text.removeprefix('请使用中文回复，除非用户明确使用其他语言。').strip()
    if '响应用户的以下需求：' in text:
        text = text.split('响应用户的以下需求：', 1)[1].split('注意：以上身份信息', 1)[0].strip()
    return text

STOP = set('用户 技能 回复 使用 你好 内容 根据 可以 一个 进行 希望 以下 以上 需要 当前 任务 请问 什么 帮我 完成 这个 继续 中文 输出 请你 帮忙 现在 是否 如果 关于 请使 使用中 中回复 明确 其他语言 AI 人工智能'.split())
def features(text):
    text = re.sub(r'https?://\S+', ' URL ', text.lower())
    text = re.sub(r'\bsk-[a-z0-9_-]{12,}', ' SECRET ', text)
    out = Counter(re.findall(r'[a-z][a-z0-9_.-]{2,}', text))
    for chunk in re.findall(r'[\u4e00-\u9fff]+', text):
        for n in (2, 3, 4):
            out.update(chunk[i:i+n] for i in range(len(chunk)-n+1) if chunk[i:i+n] not in STOP)
    return out

def kmeans(x, k=14, seed=20261005):
    rng = np.random.default_rng(seed)
    best = None
    for restart in range(8):
        centers = [x[rng.integers(len(x))]]
        for _ in range(1, k):
            dist = np.maximum(0, 1 - np.max(x @ np.array(centers).T, axis=1))
            prob = dist**2
            centers.append(x[rng.choice(len(x), p=prob/prob.sum())] if prob.sum() else x[len(centers)])
        centers = np.array(centers)
        for iteration in range(60):
            score = x @ centers.T
            lab = score.argmax(axis=1)
            updated = np.array([x[lab==i].mean(axis=0) if np.any(lab==i) else x[score.max(axis=1).argmin()] for i in range(k)])
            updated /= np.maximum(np.linalg.norm(updated, axis=1, keepdims=True), 1e-9)
            if np.allclose(updated, centers, atol=1e-5): break
            centers = updated
        objective = float(np.sum((x @ centers.T).max(axis=1)))
        if best is None or objective > best[0]: best = (objective, lab, centers)
    return best[1], best[2]

def main():
    data = json.loads(SOURCE.read_text(encoding='utf-8'))
    annotations = json.loads(LABELS.read_text(encoding='utf-8'))
    rows = []; frows = []; documents=[]; df=Counter(); occurrence_counts=Counter()
    for sid, s in data.items():
        texts = [clean(u['content']) for u in s['user_requests']]
        joined='\n'.join(texts)
        fs=features(joined); documents.append(fs); df.update(fs.keys())
        # Freeze final association decisions independently of task categories.
        decisions=annotations['labels'].get(sid,{})
        rows.append({'session_id':sid,'owner_id':s['owner_id'],'user_group_count':len(texts),'assistant_group_count':len(s['assistant_contents']), 'clean_user_texts':texts,'source_order_status':s['source_order_diagnostics']['status'],'final_annotation_items':len(decisions),'user_groups':[u['group_id'] for u in s['user_requests']]})
        for role, groups in [('user',s['user_requests']),('assistant',s['assistant_contents'])]:
            for g in groups:
                for occurrence in g['occurrences']:
                    occurrence_counts[role]+=1
                    payload=occurrence.get('raw_record',{}).get('rawPayload') or {}
                    if isinstance(payload,dict):
                        for f in payload.get('files') or []:
                            frows.append({'session_id':sid,'role':role,'message_id':occurrence['id'],'group_id':g['group_id'],'source_line':occurrence.get('source_line'),'file_metadata':f,'bytes_available_in_export':False})
    # Locally learned representation: character n-gram TF-IDF, randomized SVD, spherical k-means.
    vocab=[w for w,c in df.items() if 3<=c<=len(data)*0.55]
    vocab=sorted(vocab,key=lambda w:(-df[w],w))[:7000]
    index={w:i for i,w in enumerate(vocab)}
    matrix=np.zeros((len(rows),len(vocab)),dtype=np.float32)
    idf=np.array([np.log((1+len(rows))/(1+df[w]))+1 for w in vocab],dtype=np.float32)
    for i,fs in enumerate(documents):
        for w,c in fs.items():
            if w in index: matrix[i,index[w]]=(1+np.log(min(c,20)))*idf[index[w]]
    matrix/=np.maximum(np.linalg.norm(matrix,axis=1,keepdims=True),1e-9)
    rng=np.random.default_rng(20261005)
    omega=rng.normal(size=(matrix.shape[1],72)).astype(np.float32)
    q=matrix@omega
    for _ in range(2): q=matrix@(matrix.T@q)
    q=np.linalg.qr(q)[0]
    ub, sv, vt=np.linalg.svd(q.T@matrix, full_matrices=False)
    latent=(q@ub[:,:64])*sv[:64]
    latent/=np.maximum(np.linalg.norm(latent,axis=1,keepdims=True),1e-9)
    labels,centers=kmeans(latent)
    evidence=[]
    for ci in range(14):
        ix=np.where(labels==ci)[0]
        mean=matrix[ix].mean(axis=0)
        top=[vocab[i] for i in mean.argsort()[-35:][::-1]]
        sims=latent[ix]@centers[ci]
        reps=ix[sims.argsort()[-10:][::-1]]
        evidence.append({'cluster':ci,'count':len(ix),'terms':top,'representatives':[{'session_id':rows[i]['session_id'],'requests':rows[i]['clean_user_texts']} for i in reps]})
    for i,row in enumerate(rows):
        score=latent[i]@centers.T
        order=score.argsort()[::-1]
        row.update({'local_cluster':int(labels[i]),'cluster_score':round(float(score[order[0]]),4),'alternative_cluster':int(order[1]),'score_margin':round(float(score[order[0]]-score[order[1]]),4)})
    dump(PRIVATE/'conversation_cluster_rows.json',rows)
    dump(PRIVATE/'local_cluster_evidence.json',evidence)
    dump(PRIVATE/'file_metadata_inventory.json',frows)
    manifest={'scope':'1466 enterprise-source user conversations; not independently recovered tasks','conversation_count':len(rows),'user_group_count':sum(x['user_group_count'] for x in rows),'assistant_group_count':sum(x['assistant_group_count'] for x in rows),'raw_user_chars':sum(len(u['content']) for s in data.values() for u in s['user_requests']),'clean_user_chars':sum(sum(map(len,x['clean_user_texts'])) for x in rows),'user_truncation':False,'uses_titles':False,'model_api_calls':0,'representation':'Chinese character 2/3/4-gram TF-IDF + 64d randomized SVD + spherical kmeans K14','seed':20261005,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'annotation_sha256':hashlib.sha256(LABELS.read_bytes()).hexdigest(),'file_occurrence_metadata_rows':len(frows),'source_occurrences':dict(occurrence_counts)}
    dump(ROOT/'manifest.json',manifest)
    print(json.dumps(manifest,ensure_ascii=False),flush=True)
    print(json.dumps([{'cluster':c['cluster'],'count':c['count'],'terms':c['terms'][:15]} for c in evidence],ensure_ascii=False),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
