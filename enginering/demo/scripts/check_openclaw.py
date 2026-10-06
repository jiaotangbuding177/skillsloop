"""Real OpenClaw process + local synthetic model endpoint; no paid provider calls.

This verifies the CLI/config/envelope transport, not model reasoning quality.
"""
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skilldemo.runtime import OpenClawAgent, ReplayAgent, RuntimeFailure
from skilldemo.core import Loop

def main():
    requests = []
    class Provider(BaseHTTPRequestHandler):
        def log_message(self, *args): pass
        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            requests.append({'path': self.path, 'model': data.get('model'), 'stream': data.get('stream'), 'tools': [t.get('function',{}).get('name') for t in data.get('tools',[])]})
            message = {'role': 'assistant', 'content': 'OPENCLAW_NATIVE_CONTRACT_OK'}
            user_messages = [m.get('content', '') for m in data.get('messages', []) if m.get('role') == 'user']
            last = user_messages[-1] if user_messages else ''
            if isinstance(last, list): last = '\n'.join(p.get('text','') for p in last)
            if '最后只返回JSON对象' in last:
                suffix = last.split('以下JSON为任务材料：', 1)[1].lstrip()
                payload, _ = json.JSONDecoder().raw_decode(suffix)
                message['content'] = ReplayAgent().run('learn', payload, None)['text']
            elif '以下JSON为任务材料：' in last and not any(m.get('role')=='tool' for m in data.get('messages',[])):
                payload, _ = json.JSONDecoder().raw_decode(last.split('以下JSON为任务材料：',1)[1].lstrip())
                if payload.get('selected_skills'):
                    message = {'role':'assistant', 'content':None, 'tool_calls':[{'index':0,'id':'read-skill-control','type':'function',
                        'function':{'name':'read','arguments':json.dumps({'path':payload['selected_skills'][0]['entry']})}}]}
            self.send_response(200)
            if data.get('stream'):
                self.send_header('Content-Type', 'text/event-stream'); self.end_headers()
                for chunk in [
                    {'id':'fixture','object':'chat.completion.chunk','created':1,'model':'fixture-model','choices':[{'index':0,'delta':message,'finish_reason':None}]},
                    {'id':'fixture','object':'chat.completion.chunk','created':1,'model':'fixture-model','choices':[{'index':0,'delta':{},'finish_reason':'tool_calls' if message.get('tool_calls') else 'stop'}], 'usage':{'prompt_tokens':30,'completion_tokens':6,'total_tokens':36}}]:
                    self.wfile.write(('data: '+json.dumps(chunk)+'\n\n').encode())
                self.wfile.write(b'data: [DONE]\n\n')
            else:
                self.send_header('Content-Type', 'application/json'); self.end_headers()
                self.wfile.write(json.dumps({'id':'fixture','object':'chat.completion','created':1,'model':'fixture-model',
                    'choices':[{'index':0,'message':message,'finish_reason':'stop'}],
                    'usage':{'prompt_tokens':30,'completion_tokens':6,'total_tokens':36}}).encode())
    server = ThreadingHTTPServer(('127.0.0.1',0),Provider)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    os.environ.update(DEMO_MODEL='fixture-model', DEMO_API_KEY='local-fixture-not-a-real-key',
                      DEMO_BASE_URL=f'http://127.0.0.1:{server.server_port}/v1', DEMO_AGENT_TIMEOUT='120')
    os.environ['NO_PROXY'] = '127.0.0.1,localhost'
    root = Path(__file__).resolve().parents[1] / 'artifacts' / 'openclaw-contract' / ('run-'+uuid.uuid4().hex[:10])
    root.mkdir(parents=True)
    try:
        result = OpenClawAgent().run('chat', {'message':'Return the contract marker.', 'history':[], 'selected_skills':[]}, root / 'workspace')
        assert 'OPENCLAW_NATIVE_CONTRACT_OK' in result['text'], result
        assert requests, 'real OpenClaw did not reach the local model fixture'
        names=set(requests[0]['tools'])
        assert {'read','write','exec'} <= names, names
        assert not names & {'sessions_spawn','sessions_send','message','cron','nodes'}, names
        with tempfile.TemporaryDirectory(prefix='native-loop-', dir=root) as directory:
            loop = Loop(Path(directory), OpenClawAgent(), settle_seconds=0)
            loop.chat('alice','native-session','整理报告，必须先核对退款再汇总收入')
            loop.tick(); candidate = loop.discover('alice')[0]
            candidate = loop.generate('alice',candidate['id'])
            assert candidate['status'] == 'READY', candidate.get('error')
            skill = loop.accept('alice',candidate['id'])
            used = loop.chat('alice','native-session','新任务：整理下一期报告',[skill['id']])
            assert used['skillEvidence']['skills'][0]['status'] == 'FILE_READ', used
            loop.tick(); assert loop.discover('alice') == []
            loop.chat('alice','native-session','不对，跨期退款必须单独列出')
            loop.tick(); update = loop.discover('alice')[0]
            update = loop.generate('alice',update['id'])
            assert update['status'] == 'READY', update.get('error')
            assert loop.accept('alice',update['id'])['version'] == 2
            lifecycle = loop.snapshot('alice')
        evidence = {'kind':'real-openclaw-with-synthetic-provider', 'notModelQualityEvidence':True,
                    'health':OpenClawAgent().health(),'requests':requests,'result':result,'lifecycle':lifecycle}
        (root / 'result.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'ok':True,'requests':len(requests),'runtime':result['runtime'],'usage':result['usage'],'evidence':str(root/'result.json')},ensure_ascii=False,indent=2))
    except RuntimeFailure as exc:
        print(json.dumps({'result':getattr(exc, 'result', {}), 'requests': requests}, ensure_ascii=False, indent=2))
        raise
    finally: server.shutdown(); server.server_close()

if __name__ == '__main__': main()
