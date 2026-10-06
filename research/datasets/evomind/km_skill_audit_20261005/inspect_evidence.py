"""Local evidence extraction only; does not query KM or trust skill declarations."""
from pathlib import Path
import json,re,sys
ROOT=Path(__file__).resolve().parent; P=ROOT/'private';P.mkdir(exist_ok=True)
source=json.loads((ROOT.parent/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
pattern=re.compile(r'(?:/[\w.\-]+)*/skills/([A-Za-z0-9][A-Za-z0-9_.-]*)(?:/[^\s`"\'<>，。；、)]*)?')
def encoded(x):return json.dumps(x,ensure_ascii=False) if not isinstance(x,str) else x
hits=[]; text=[];samples=[]
for sid,s in source.items():
    for role,key in [('user','user_requests'),('assistant','assistant_contents')]:
        for g in s[key]:
            for m in pattern.finditer(g['content']):text.append({'session_id':sid,'group_id':g['group_id'],'role':role,'name':m.group(1),'path':m.group(0)})
            for o in g['occurrences']:
                rp=o.get('raw_record',{}).get('rawPayload') or {}
                ts=rp.get('toolActivity',[]);ts=ts if isinstance(ts,list) else [ts]
                for t in ts:
                    args=encoded(t.get('args',{})); out=encoded(t.get('output',''))
                    if pattern.search(args):
                        hits.append({'session_id':sid,'message_id':o['id'],'group_id':g['group_id'],'source_line':o['source_line'],'tool':t})
samplepath=Path('C:/Users/39835/Downloads/zkys-raw-export-20260925/raw_payload_sample.jsonl')
sample_text=samplepath.read_text(encoding='utf-8-sig'); decoder=json.JSONDecoder(strict=False);position=0;sample_total=0
while position<len(sample_text):
    while position<len(sample_text) and sample_text[position].isspace():position+=1
    if position>=len(sample_text):break
    x,position=decoder.raw_decode(sample_text,position);sample_total+=1
    if x.get('sessionId') in source:
        samples.append(x)
        if pattern.search(encoded(x.get('content',''))) or pattern.search(encoded(x.get('rawPayload',''))):
            hits.append({'session_id':x['sessionId'],'message_id':x['id'],'origin':'raw_payload_sample','raw_record':x})
(P/'skill_tool_candidates.json').write_text(json.dumps(hits,ensure_ascii=False,indent=2),encoding='utf-8')
(P/'skill_path_text_mentions.json').write_text(json.dumps(text,ensure_ascii=False,indent=2),encoding='utf-8')
summary={'structured_candidate_occurrences':len(hits),'text_path_names':sorted({x['name'] for x in text}),'tool_snapshot_candidates':[{'session':x['session_id'],'name':x['tool'].get('name'),'status':x['tool'].get('status'),'args_skill_paths':[m.group(0) for m in pattern.finditer(encoded(x['tool'].get('args',{})))],'output_type':type(x['tool'].get('output')).__name__} for x in hits if 'tool' in x][:40],'raw_sample_total':sample_total,'raw_sample_records_in_scope':len(samples),'sample_shapes':[{'role':x.get('role'),'keys':list(x),'content_type':type(x.get('content')).__name__,'rawPayload_keys':list(x['rawPayload']) if isinstance(x.get('rawPayload'),dict) else []} for x in samples[:3]]}
(ROOT/'inspection_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps(summary,ensure_ascii=False))
