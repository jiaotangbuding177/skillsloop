"""Package actual brand content and check supplied claim provenance; no model calls."""
import argparse, hashlib, json, re
from pathlib import Path

STATUS={'user_provided','verified','unverified'}

def bundle(source, destination):
    data=json.loads(Path(source).read_text(encoding='utf-8-sig'))
    for key in ('title','channel','audience','objective','key_message','draft_markdown'):
        if not isinstance(data.get(key),str) or not data[key].strip():
            raise ValueError('Nonempty '+key+' required')
    facts=data.get('facts',[])
    if not isinstance(facts,list): raise ValueError('facts must be a list')
    indexed={}
    for fact in facts:
        if not isinstance(fact,dict): raise ValueError('Each fact must be an object')
        fid=fact.get('id')
        if not isinstance(fid,str) or not re.fullmatch('[A-Za-z0-9_-]+',fid) or fid in indexed:
            raise ValueError('Unique simple fact id required')
        if fact.get('status') not in STATUS: raise ValueError('Unknown fact status')
        if not str(fact.get('statement','')).strip(): raise ValueError('Fact statement required')
        if fact['status']!='unverified' and not str(fact.get('source','')).strip():
            raise ValueError('Source required for provided/verified fact')
        indexed[fid]=fact
    draft=data['draft_markdown']
    references=re.findall(r'\[fact:([A-Za-z0-9_-]+)\]',draft)
    unknown=sorted(set(references)-set(indexed))
    if unknown: raise ValueError('Draft cites unknown fact ids: '+','.join(unknown))
    flags=[]
    for term in ('100%杜绝','绝对安全','零风险','全球第一','唯一'):
        if term in draft: flags.append({'type':'wording_review','text':term,'action':'检查依据、适用范围和用户发布规则'})
    pending=[f for f in facts if f['status']=='unverified']
    out=Path(destination);out.mkdir(parents=True,exist_ok=True)
    brief='\n'.join(f'{label}：{data[key]}' for key,label in [('title','标题'),('channel','渠道'),('audience','受众'),('objective','目的'),('key_message','关键主张')])
    (out/'campaign_brief.md').write_text('# 内容策划\n\n'+brief+'\n',encoding='utf-8')
    clean=re.sub(r'\[fact:([A-Za-z0-9_-]+)\]','',draft)
    (out/'article.md').write_text(clean.rstrip()+'\n',encoding='utf-8')
    (out/'fact_register.json').write_text(json.dumps({'facts':facts,'draft_fact_ids':references,'unused_fact_ids':sorted(set(indexed)-set(references))},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    review=['# 审稿记录','',f'事实条目：{len(facts)}；正文已登记引用：{len(set(references))}；未核实：{len(pending)}。','',
            '脚本检查覆盖事实标记的归属和提供的状态；未标记的数字/断言仍须人工复核。']
    review+=['\n待核：'+f['id']+' '+f['statement'] for f in pending]
    review+=['\n措辞复核：'+f['text']+'；'+f['action'] for f in flags]
    notes=data.get('review_notes',[])
    if not isinstance(notes,list) or any(not isinstance(n,str) for n in notes): raise ValueError('review_notes must be strings')
    review+=['\n执行者审稿：'+n for n in notes]
    (out/'review.md').write_text('\n'.join(review)+'\n',encoding='utf-8')
    files=[]
    for name in ('campaign_brief.md','article.md','fact_register.json','review.md'):
        f=out/name;files.append({'name':name,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    result={'schema':'brand-content-delivery-v1','provenance':'context_reconstruction','files':files,'pending_fact_count':len(pending),'wording_review_count':len(flags),'automatic_full_fact_verification':False}
    (out/'delivery_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output-dir',required=True)
    a=p.parse_args();print(json.dumps(bundle(a.input,a.output_dir),ensure_ascii=False))
