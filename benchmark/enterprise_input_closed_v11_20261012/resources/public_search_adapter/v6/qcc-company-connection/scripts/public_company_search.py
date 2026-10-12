"""Actual anonymous public web search; no QCC credentials or historical answers."""
import argparse, datetime, json, urllib.request, uuid
from pathlib import Path

ENDPOINT='https://search.parallel.ai/mcp'

def envelopes(text):
    body=text.strip()
    if body.startswith(('{','[')):
        value=json.loads(body);return value if isinstance(value,list) else [value]
    result=[]; parts=[]
    for line in body.split('\n')+['']:
        if line.startswith('data:'):parts.append(line[5:].lstrip())
        elif not line.strip() and parts:
            result.append(json.loads('\n'.join(parts)));parts=[]
    return result

def search(company, output):
    headers={'Content-Type':'application/json','Accept':'application/json, text/event-stream','User-Agent':'openclaw-parallel/2026.9.5 (linux)'}
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def call(method,params=None, notification=False):
        request_id=str(uuid.uuid4()); body={'jsonrpc':'2.0','method':method}
        if not notification:body['id']=request_id
        if params is not None:body['params']=params
        request=urllib.request.Request(ENDPOINT,data=json.dumps(body).encode(),headers=headers,method='POST')
        with opener.open(request,timeout=45) as response:
            text=response.read().decode('utf-8')
            if response.headers.get('Mcp-Session-Id'):headers['Mcp-Session-Id']=response.headers['Mcp-Session-Id']
        if notification:return None
        candidates=envelopes(text); reply=next((x for x in candidates if x.get('id')==request_id),candidates[-1] if candidates else {})
        if reply.get('error'):raise RuntimeError('Public Search MCP error: '+json.dumps(reply['error']))
        return reply['result']
    initialized=call('initialize',{'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'skillloop-public-company-search','version':'1.0'}})
    headers['MCP-Protocol-Version']=initialized.get('protocolVersion','2025-06-18')
    call('notifications/initialized',notification=True)
    result=call('tools/call',{'name':'web_search','arguments':{
        'objective':'查验公司全称匹配的公开工商、股权、官网、法院、监管披露；只返回可追溯公开网页，勿据未命中推断无风险。公司：'+company,
        'search_queries':['"'+company+'"',company+' 工商 股权 诉讼'], 'session_id':str(uuid.uuid4())}})
    if result.get('isError'):raise RuntimeError('Public Search tool returned an error')
    payload=result.get('structuredContent')
    if payload is None:
        for block in result.get('content',[]):
            if block.get('type')=='text':
                try:payload=json.loads(block['text']);break
                except ValueError:pass
    if not isinstance(payload,dict):raise RuntimeError('Public Search omitted a structured result')
    import re
    normalize=lambda text:re.sub(r'[\s（）()【】\[\]"“”]','',text)
    exact_results=[r for r in payload.get('results',[]) if normalize(company) in normalize(json.dumps(r,ensure_ascii=False))]
    receipt={'schema':'public-company-lookup-v1','company_name':company,'captured_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'public_provider':'parallel-free-native-compatible-mcp','endpoint':ENDPOINT,'QCC_API_used':False,
        'historical_AI_answer_used':False,'raw_search_result':payload,
        'field_verification_required':True,'no_results_does_not_mean_no_risk':True,
        'exact_name_result_candidates':exact_results,'company_facts_verified':False}
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return receipt

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--company',required=True);p.add_argument('--output',required=True);a=p.parse_args()
    result=search(a.company,a.output)
    print(json.dumps({'public_search_completed':True,'result_count':len(result['raw_search_result'].get('results',[])),'output':a.output},ensure_ascii=False))
