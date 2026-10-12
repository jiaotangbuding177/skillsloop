"""Produce a provenance-aware company evidence report from real local inputs."""
import argparse, hashlib, json
from pathlib import Path
from urllib.parse import urlparse

def check_company(source, output_dir):
    data=json.loads(Path(source).read_text(encoding='utf-8-sig'))
    name=data.get('company_name')
    if not isinstance(name,str) or not name.strip():raise ValueError('company_name required')
    kind=data.get('source_kind')
    if kind not in ('public_evidence','reconstructed_fixture'):raise ValueError('Explicit source_kind required')
    evidence={}
    for item in data.get('evidence',[]):
        eid=item.get('id')
        if not isinstance(eid,str) or not eid or eid in evidence:raise ValueError('Unique evidence id required')
        for key in ('subject_name','url','captured_at','text'):
            if not isinstance(item.get(key),str) or not item[key].strip():raise ValueError('Evidence '+key+' required')
        if item['subject_name']!=name:raise ValueError('Evidence subject differs from queried company')
        if kind=='public_evidence' and urlparse(item['url']).scheme not in ('http','https'):
            raise ValueError('Public evidence requires actual HTTP(S) source URL')
        evidence[eid]=item
    fields=data.get('fields')
    if not isinstance(fields,list) or not fields:raise ValueError('Nonempty fields required')
    names=set();supported=[];unknown=[]
    for item in fields:
        label=item.get('name')
        if not isinstance(label,str) or not label or label in names:raise ValueError('Unique field name required')
        names.add(label)
        if item.get('status') not in ('supported','unknown'):raise ValueError('Explicit field status required')
        refs=item.get('evidence_ids',[])
        if not isinstance(refs,list):raise ValueError('evidence_ids must be a list')
        if any(ref not in evidence for ref in refs):raise ValueError('Unknown evidence reference')
        if item['status']=='supported':
            if not refs or item.get('value') is None or item.get('value')=='':raise ValueError('Supported field requires value and evidence')
            supported.append(item)
        else:
            if item.get('value') not in (None,'','未知'):raise ValueError('Unknown field cannot carry a factual value')
            unknown.append(item)
    out=Path(output_dir);out.mkdir(parents=True,exist_ok=True)
    result={'schema':'company-evidence-review-v1','company_name':name,'source_kind':kind,'qcc_live_data_restored':False,'fields':fields,'evidence':list(evidence.values()),'supported_field_count':len(supported),'unknown_field_count':len(unknown),'original_company_facts_verified':False,'helper_verification_scope':'schema, entity consistency and declared evidence references; truth checked by executor'}
    (out/'company_report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# 公司资料核查', '', '公司：'+name, '资料条件：'+kind, '', '原企查查付费接口与数据未恢复；以下按输入证据登记，未知不代表没有风险。', '', '## 已提供支持的字段','']
    for field in supported:
        value=field['value'] if isinstance(field['value'],str) else json.dumps(field['value'],ensure_ascii=False)
        lines.append('- '+field['name']+'：'+value+'；来源 '+', '.join(field['evidence_ids']))
    lines+=['', '## 未覆盖或未知', '']+['- '+x['name']+'：未知' for x in unknown]
    lines+=['', '## 证据', '']
    for item in evidence.values():lines+=['- '+item['id']+'：'+item['url']+'；查询/提供时间 '+item['captured_at'],'  '+item['text'].replace('\n',' ')]
    (out/'company_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    receipt={'files':[],'source_kind':kind,'qcc_live_data_restored':False}
    for fn in ('company_report.json','company_report.md'):
        f=out/fn;receipt['files'].append({'name':fn,'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
    (out/'delivery_manifest.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output-dir',required=True)
    a=p.parse_args();print(json.dumps(check_company(a.input,a.output_dir),ensure_ascii=False))
