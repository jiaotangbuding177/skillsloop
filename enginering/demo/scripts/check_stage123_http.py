"""Local HTTP smoke test with a deterministic model fixture; no paid calls."""
import json
from pathlib import Path
import socket
import sys
import tempfile
import threading
import time
import urllib.request
from unittest.mock import patch

DEMO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(DEMO),str(DEMO/'tests')]
from skilldemo.core import Loop
from skilldemo import server
from test_front_stages import StructuredFixture,messages

def main():
    with socket.socket() as sock:sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    holder={};factory=server.ThreadingHTTPServer
    def capture(*args,**kwargs):
        holder['server']=factory(*args,**kwargs);return holder['server']
    def call(path,data=None):
        req=urllib.request.Request(f'http://127.0.0.1:{port}/'+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(req,timeout=10) as r:return r.read()
    with tempfile.TemporaryDirectory() as root,patch.object(server,'ThreadingHTTPServer',capture):
        loop=Loop(root,StructuredFixture(),settle_seconds=0,stage_pipeline=True)
        loop.tick=lambda:None  # Explicit API stage execution owns this fixture.
        thread=threading.Thread(target=server.serve,args=(loop,port,False),daemon=True);thread.start()
        try:
            for _ in range(100):
                if 'server' in holder:break
                time.sleep(.02)
            assert b'<!' in call('/')
            imported=json.loads(call('api/import-events',{'actor':'alice','entries':messages(),'purposeSplit':'generation'}))
            assert imported['pairCount']==2
            result=json.loads(call('api/stages',{'actor':'alice'}))
            assert result['sessions'][0]['stage3']=='RECOVERED'
            state=json.loads(call('api/state?actor=alice'))
            assert len(state['pairs'])==2 and len(state['traces'])==1
            assert len(state['runs'])==2 and state['traces'][0]['businessOutcome']=='UNKNOWN'
            bob=json.loads(call('api/state?actor=bob'));assert not bob['pairs'] and not bob['traces']
            exported=[json.loads(x) for x in call('api/export?actor=alice').decode().splitlines()]
            assert {'pairs','pairAnnotations','recoveries','traces'}<={x['type'] for x in exported}
            print(json.dumps({'passed':True,'mode':'http-with-structured-fixture','realModelEvidence':False,'modelCalls':0,'checks':['page','raw_import','stage2_stage3','owner_isolation','source_export','unknown_preserved']},indent=2))
        finally:
            if 'server' in holder:holder['server'].shutdown()
            thread.join(timeout=5)

if __name__=='__main__':main()
