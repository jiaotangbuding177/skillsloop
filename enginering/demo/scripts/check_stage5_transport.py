"""Real installed OpenClaw + local fixed provider + official creator packaging.

No enterprise data or paid requests. This tests transport, receipts and packaging,
not generation quality. Keep separate from the real experiment evidence.
"""
import json
import os
from pathlib import Path
import sys
import threading
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from skilldemo.runtime import OpenClawAgent, HEADINGS, parse_object
from skilldemo.bootstrap import draft_files, package
from skilldemo.creator import verify_files, verify_archive


def main():
    action='先确认本次报告的统计期间，再核对输入数据的期间是否一致。'
    check='检查报告的每个数据项是否与确认的统计期间一致。'
    md='---\nname: period-check-fixture\ndescription: 核对报告数据期间的合成控制技能。\n---\n'
    md+='\n## 核对步骤\n<!-- SKILLSLOOP_METHOD:m1 -->\n'+action+'\n完成检查：'+check+'\n'
    md+='\n## 市场信息\n'+'\n'.join('### '+h+'\n仅供程序控制验证，不是研究产物。' for h in HEADINGS)
    coverage=[dict(methodId='m1',file='SKILL.md',actionQuote=action,conditionQuotes=[],completionCheckQuote=check)]
    calls=[]

    class Provider(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            step=len(calls)
            calls.append({'path':self.path,'model':data.get('model'),'step':step})
            if step<2:
                name='read' if step==0 else 'write'
                args={'path':'.foundation/skill-creator/SKILL.md'} if step==0 else {'path':'draft/SKILL.md','content':md}
                msg={'role':'assistant','content':None,'tool_calls':[{'index':0,'id':'fixture-'+str(step),
                     'type':'function','function':{'name':name,'arguments':json.dumps(args,ensure_ascii=False)}}]}
            else:
                msg={'role':'assistant','content':json.dumps({'decision':'CREATE','title':'合成期间控制',
                     'coverageManifest':coverage},ensure_ascii=False)}
            self.send_response(200)
            if data.get('stream'):
                self.send_header('Content-Type','text/event-stream');self.end_headers()
                for chunk in [dict(id='fixture',object='chat.completion.chunk',created=1,model='fixture-model',
                     choices=[{'index':0,'delta':msg,'finish_reason':None}]),
                     dict(id='fixture',object='chat.completion.chunk',created=1,model='fixture-model',
                     choices=[{'index':0,'delta':{},'finish_reason':'tool_calls' if step<2 else 'stop'}],
                     usage={'prompt_tokens':30,'completion_tokens':10,'total_tokens':40})]:
                    self.wfile.write(('data: '+json.dumps(chunk,ensure_ascii=False)+'\n\n').encode())
                self.wfile.write(b'data: [DONE]\n\n')
            else:
                self.send_header('Content-Type','application/json');self.end_headers()
                self.wfile.write(json.dumps({'id':'fixture','object':'chat.completion','model':'fixture-model',
                    'choices':[{'index':0,'message':msg,'finish_reason':'tool_calls' if step<2 else 'stop'}]}).encode())

    server=ThreadingHTTPServer(('127.0.0.1',0),Provider)
    threading.Thread(target=server.serve_forever,daemon=True).start()
    os.environ.update(DEMO_MODEL='fixture-model',DEMO_API_KEY='local-fixture-not-a-real-key',
        DEMO_MODEL_API='openai-completions',DEMO_BASE_URL=f'http://127.0.0.1:{server.server_port}/v1',
        DEMO_AGENT_TIMEOUT='120',DEMO_NETWORK_MODE='direct',NO_PROXY='127.0.0.1,localhost')
    root=Path(__file__).resolve().parents[1]/'artifacts'/'051-stage5-transport'/uuid.uuid4().hex[:10]
    methods=[{'id':'m1','action':action,'conditions':[],'completionCheck':check}]
    try:
        result=OpenClawAgent().run('workflow_creator',{'algorithm':'workflow-creator-v1',
            'workflow':{'title':'合成控制','includedMethodIds':['m1']},'methods':methods},root/'workspace')
        assert len(calls)==3,calls
        assert result['foundationRead']['status']=='FILE_READ',result['foundationRead']
        output=parse_object(result['text']);files=draft_files(root/'workspace')
        validation=verify_files(files,['m1'],methods=methods,coverageManifest=output['coverageManifest'])
        packaged=package(root/'workspace',files)
        archive=verify_archive(root/'workspace',packaged,files)
        evidence={'ok':True,'kind':'REAL_OPENCLAW_SYNTHETIC_PROVIDER','paidRequests':0,
            'requests':calls,'foundationRead':result['foundationRead'],'validation':validation,
            'package':packaged,'archive':archive,'runtime':result['runtime']}
        (root/'result.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'ok':True,'requests':len(calls),'evidence':str(root/'result.json')},ensure_ascii=False))
    finally:
        server.shutdown();server.server_close()


if __name__=='__main__':main()
