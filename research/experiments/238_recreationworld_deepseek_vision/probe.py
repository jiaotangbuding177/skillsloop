"""Provider admission probe; synthetic images/tools only, no credential output."""
import base64
import hashlib
import io
import json
from pathlib import Path
import secrets
import re
import time
import urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
CONFIG = json.loads((ROOT / 'model_resource.json').read_text())

def main():
    key = json.loads((ROOT / CONFIG['credential_file']).read_text())['api_key']
    evidence = []
    def call(payload, label):
        started = time.time()
        request = urllib.request.Request(CONFIG['upstream_base_url'] + '/chat/completions',
            data=json.dumps(dict(model=CONFIG['model_id'], **payload)).encode(),
            headers={'Content-Type':'application/json', 'Authorization':'Bearer ' + key})
        try:
            with urllib.request.urlopen(request, timeout=CONFIG['socket_idle_timeout_seconds']) as response:
                result = json.load(response)
            envelope = list(result.keys())
            if isinstance(result.get('data'),dict) and 'choices' in result['data'] and result.get('success') is True:
                result = result['data']
            item = {'case':label,'http_status':200,'elapsed_s':round(time.time()-started,2),
                'model_reported':result.get('model'), 'finish_reason':result.get('choices',[{}])[0].get('finish_reason')}
            item['response_keys'] = list(result.keys())
            item['envelope_keys'] = envelope
            if 'data' in result:
                item['data_type'] = type(result['data']).__name__
                if isinstance(result['data'],dict): item['data_keys'] = list(result['data'].keys())
            if result.get('error'):
                error = result['error']
                item['api_error_type'] = error.get('type') if isinstance(error,dict) else type(error).__name__
                item['api_error_code'] = error.get('code') if isinstance(error,dict) else None
                message = str(error.get('message','')) if isinstance(error,dict) else ''
                item['api_error_message'] = re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',message.replace(key,'[REDACTED]'))[:250]
            evidence.append(item)
            return result, item
        except Exception as exc:
            item = {'case':label,'error_class':type(exc).__name__, 'http_status':getattr(exc,'code',None),
                'elapsed_s':round(time.time()-started,2),'passed':False}
            evidence.append(item)
            return {}, item
    for index in range(2):
        nonce = ''.join(secrets.choice('23456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(6))
        image = Image.new('RGB',(480,150),'white')
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',60)
        ImageDraw.Draw(image).text((35,35),nonce,fill='black',font=font)
        buffer = io.BytesIO(); image.save(buffer,format='PNG')
        result, item = call({'temperature':0,'max_tokens':512,'messages':[{'role':'user','content':[
            {'type':'text','text':'Read the six-character code in the image. Reply only with that code.'},
            {'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode()}}]}]}, 'vision_'+str(index))
        answer = result.get('choices',[{}])[0].get('message',{}).get('content','')
        item.update(expected=nonce,answer=answer if isinstance(answer,str) and len(answer)<100 else None,
            image_sha256=hashlib.sha256(buffer.getvalue()).hexdigest(),passed=isinstance(answer,str) and answer.strip()==nonce)
    result, item = call({'max_tokens':512,'messages':[{'role':'user','content':'Call report_status with status ready.'}],
        'tools':[{'type':'function','function':{'name':'report_status','description':'Report readiness',
            'parameters':{'type':'object','properties':{'status':{'type':'string','enum':['ready']}},'required':['status'],'additionalProperties':False}}}],
        'tool_choice':{'type':'function','function':{'name':'report_status'}}}, 'tool_protocol')
    calls = result.get('choices',[{}])[0].get('message',{}).get('tool_calls',[])
    try:
        item['passed'] = len(calls)==1 and calls[0]['function']['name']=='report_status' and json.loads(calls[0]['function']['arguments'])=={'status':'ready'}
    except (ValueError,KeyError,TypeError): item['passed']=False
    report = {'model_id':CONFIG['model_id'],'scope':'direct OpenAI API admission; not native CLI acceptance',
        'cases':evidence,'vision_ready':all(x['passed'] for x in evidence[:2]),'tools_ready':item['passed']}
    (ROOT/'reports').mkdir(exist_ok=True)
    existing = ROOT/'reports/model_acceptance.json'
    if existing.exists():
        (ROOT/'reports'/('model_acceptance_'+str(time.time_ns())+'.json')).write_bytes(existing.read_bytes())
    existing.write_text(json.dumps(report,indent=2))
    print(json.dumps({'vision_ready':report['vision_ready'],'tools_ready':report['tools_ready'],
        'http_statuses':[x.get('http_status') for x in evidence]}))

if __name__ == '__main__': main()
