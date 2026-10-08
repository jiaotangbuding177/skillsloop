"""Dedicated provider relay: release only complete responses, durable safe receipts."""
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from vision_bridge import repair_messages
import threading
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CFG = json.loads((ROOT/'model_resource.json').read_text())
KEY = json.loads((ROOT/CFG['credential_file']).read_text())['api_key']
LOCK = threading.Lock()

def complete(result):
    if isinstance(result,dict) and result.get('success') is True and isinstance(result.get('data'),dict):
        result = result['data']
    if not isinstance(result,dict) or result.get('error'): raise ValueError('Provider error or invalid object')
    choices = result.get('choices')
    if not choices or not all(c.get('finish_reason') in ('stop','tool_calls','function_call') and isinstance(c.get('message'),dict) for c in choices):
        raise ValueError('Response incomplete, truncated or filtered')
    return result

def receive(response, record, label):
    if 'text/event-stream' not in response.headers.get('Content-Type',''):
        record['upstream_protocol']='json'
        return complete(json.load(response))
    record['upstream_protocol']='sse'
    choices={}; model=None; result_id=None; usage=None; done=False; frames=0; pending=[]
    def consume(lines):
        nonlocal model,result_id,usage,done,frames
        payload='\n'.join(lines)
        if payload=='[DONE]': done=True; return
        if not payload: return
        frame=json.loads(payload)
        if frame.get('error'):
            import re
            error=json.dumps(frame['error']).replace(KEY,'[REDACTED]')
            record['provider_error']=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',error)[:350]
            receipt(label,record)
            raise ValueError('Provider stream error')
        frames+=1; model=frame.get('model') or model; result_id=frame.get('id') or result_id
        if frame.get('usage'): usage=frame['usage']
        for part in frame.get('choices',[]):
            index=part.get('index',0)
            current=choices.setdefault(index,{'index':index,'message':{'role':'assistant','content':''},'finish_reason':None,'calls':{}})
            delta=part.get('delta',{})
            for key in ('content','reasoning_content'):
                value=delta.get(key)
                if isinstance(value,str): current['message'][key]=current['message'].get(key,'')+value
            for call in delta.get('tool_calls') or []:
                i=call.get('index',0)
                saved=current['calls'].setdefault(i,{'id':'','type':'function','function':{'name':'','arguments':''}})
                if call.get('id'): saved['id']=call['id']
                if call.get('type'): saved['type']=call['type']
                for key in ('name','arguments'):
                    value=call.get('function',{}).get(key)
                    if isinstance(value,str): saved['function'][key]+=value
            if part.get('finish_reason') is not None: current['finish_reason']=part['finish_reason']
        record.update(upstream_frames=frames,upstream_last_frame_at=datetime.now(timezone.utc).isoformat())
        if frames==1 or frames%20==0: receipt(label,record)
    for raw in response:
        line=raw.decode('utf8').rstrip('\r\n')
        if not line:
            consume(pending); pending=[]
            if done: break
        elif line.startswith('data:'): pending.append(line[5:].lstrip())
    if pending: consume(pending)
    record.update(upstream_frames=frames,upstream_done=done)
    if not done: raise ValueError('Provider SSE ended without DONE')
    output=[]
    for i in sorted(choices):
        current=choices[i]; calls=current.pop('calls')
        if calls: current['message']['tool_calls']=[calls[j] for j in sorted(calls)]
        output.append(current)
    return complete({'id':result_id or label,'object':'chat.completion','model':model,'choices':output,'usage':usage})

def receipt(label, obj):
    directory=ROOT/'ledger'; directory.mkdir(exist_ok=True)
    target=directory/(label+'.json'); temporary=target.with_suffix('.tmp')
    temporary.write_text(json.dumps(obj,indent=2)); temporary.replace(target)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def send(self,code,data,mime='application/json'):
        self.send_response(code); self.send_header('Content-Type',mime)
        self.send_header('Content-Length',str(len(data))); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        self.send(200,json.dumps({'status':'ready','model':CFG['model_id']} if self.path=='/health' else
            {'object':'list','data':[{'id':CFG['model_id'],'object':'model'}]}).encode())
    def do_POST(self):
        label=str(time.time_ns()); started=time.time()
        record={'route':self.path,'model':CFG['model_id'],'started_at':datetime.now(timezone.utc).isoformat(),
            'api_outcome':'in_progress','response_complete':False,'total_deadline_seconds':None,
            'socket_idle_timeout_seconds':CFG['socket_idle_timeout_seconds']}
        receipt(label,record)
        try:
            if not self.path.endswith('/chat/completions'): raise ValueError('Unsupported route')
            payload=json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))))
            payload['messages'], image_audit=repair_messages(payload.get('messages',[]))
            record['image_transport']=image_audit
            downstream_stream=bool(payload.get('stream')); payload['stream']=True
            payload.pop('stream_options',None); payload['model']=CFG['model_id']
            request=urllib.request.Request(CFG['upstream_base_url']+'/chat/completions',
                data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','Authorization':'Bearer '+KEY})
            # Retry only transport/temporary service errors; never retry model outcomes
            # such as length, empty choices, refusal, or no-code completion.
            attempts=[]
            for attempt in range(CFG['transport_retries']+1):
                attempt_start=time.time()
                try:
                    with urllib.request.urlopen(request,timeout=CFG['socket_idle_timeout_seconds']) as response:
                        result=receive(response,record,label)
                    attempts.append({'attempt':attempt+1,'outcome':'completed','elapsed_s':round(time.time()-attempt_start,3)})
                    break
                except (urllib.error.URLError,ConnectionError,TimeoutError) as exc:
                    retryable=not isinstance(exc,urllib.error.HTTPError) or exc.code in (408,429,500,502,503,504,524)
                    attempts.append({'attempt':attempt+1,'outcome':'transport_error','error_class':type(exc).__name__,
                        'http_status':getattr(exc,'code',None),'elapsed_s':round(time.time()-attempt_start,3)})
                    record['upstream_attempts']=attempts; receipt(label,record)
                    if not retryable or attempt==CFG['transport_retries']: raise
                    time.sleep(min(2**attempt,8))
            record['upstream_attempts']=attempts
            record.update(api_outcome='completed',response_complete=True,model_reported=result.get('model'),
                finish_reasons=[c['finish_reason'] for c in result['choices']],elapsed_seconds=round(time.time()-started,3),
                usage_reported=result.get('usage'),message_diagnostics=[{'text_characters':len(str(c['message'].get('content') or '')),'tool_calls':len(c['message'].get('tool_calls') or []),'exact_interruption_marker':c['message'].get('content')=='[Tool use interrupted]'} for c in result['choices']])
            receipt(label,record)
            if not downstream_stream:
                self.send(200,json.dumps(result).encode()); return
            # Protocol conversion only; no generated model text or fabricated completion.
            chunks=[]
            for choice in result['choices']:
                message=dict(choice['message'])
                if message.get('tool_calls'):
                    message['tool_calls']=[dict(call,index=i) for i,call in enumerate(message['tool_calls'])]
                chunk={'id':result.get('id',label),'object':'chat.completion.chunk','model':result.get('model',CFG['model_id']),
                    'choices':[{'index':choice.get('index',0),'delta':message,'finish_reason':None}]}
                chunks.append('data: '+json.dumps(chunk)+'\n\n')
                chunk['choices']=[{'index':choice.get('index',0),'delta':{},'finish_reason':choice['finish_reason']}]
                if result.get('usage'): chunk['usage']=result['usage']
                chunks.append('data: '+json.dumps(chunk)+'\n\n')
            self.send(200,(''.join(chunks)+'data: [DONE]\n\n').encode(),'text/event-stream')
        except Exception as exc:
            record.update(api_outcome='transport_or_protocol_failure',response_complete=False,
                error_class=type(exc).__name__,upstream_http_status=getattr(exc,'code',None),elapsed_seconds=round(time.time()-started,3))
            receipt(label,record)
            try: self.send(502,json.dumps({'error':{'type':'upstream_error','message':'Incomplete provider response; inspect safe receipt '+label}}).encode())
            except (BrokenPipeError,ConnectionResetError): pass

if __name__=='__main__':
    server=ThreadingHTTPServer(('127.0.0.1',CFG['local_port']),Handler)
    (ROOT/'reports/relay_identity.json').write_text(json.dumps({'pid':__import__('os').getpid(),'port':CFG['local_port'],'started_epoch':time.time()}))
    server.serve_forever()
