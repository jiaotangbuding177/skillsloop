"""Read-only HTTP/artifact audit after accept_live.py; no model calls."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.error
import urllib.parse
import urllib.request
import zipfile

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--data',default='artifacts/a024c');parser.add_argument('--port',type=int,default=8767)
    args=parser.parse_args();root=Path(args.data).resolve()
    proof=json.loads((root/'acceptance.json').read_text(encoding='utf-8'));assert proof['passed']
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def get(route,**params):
        return opener.open(f'http://127.0.0.1:{args.port}/api/'+route+'?'+urllib.parse.urlencode(params),timeout=15).read()
    snapshots={a:json.loads(get('state',actor=a)) for a in ('alice','bob','outsider')}
    records=[];requests=0
    for actor in ('alice','bob'):
        for run in snapshots[actor]['runs']:
            r=run['result'];assert run['status']=='COMPLETED' and r['cliExitCode']==0 and r['raw']['ok']
            work=root/'workspaces'/run['id'];tools=r['skillEvidence']['tools']
            execs=[t for t in tools if t['name']=='exec' and t['status']=='SUCCEEDED']
            assert execs,run['id']+' has no successful exec receipt'
            creator=any(t['name']=='read' and t['status']=='SUCCEEDED' and 'skill-creator' in json.dumps(t['arguments']) for t in tools)
            if run['purpose']=='learn':
                assert creator and r.get('package')
                with zipfile.ZipFile(work/r['package']['path']) as archive:
                    assert any(n.endswith('/SKILL.md') for n in archive.namelist())
                    assert not any('__pycache__' in n for n in archive.namelist())
            for s in run['request'].get('selected_skills',[]):
                for f in s['files']:assert (work/'skills'/s['id']/f['path']).read_text(encoding='utf-8')==f['content']
            for f in r.get('artifacts',[]):
                content=get('artifact',actor=actor,run=run['id'],path=f['path'])
                assert hashlib.sha256(content).hexdigest()==f['sha256']
            logs=(work.parent/(work.name+'-control')/'stderr.log').read_text(encoding='utf-8')
            calls=logs.count('[model-fetch] start');requests+=calls
            records.append({'actor':actor,'runId':run['id'],'purpose':run['purpose'],'status':run['status'],
                'nativeExit':r['cliExitCode'],'modelFetchStarts':calls,'assistantTurns':r['assistantTurns'],
                'usage':r['usage'],'creatorRead':creator,'successfulExecs':len(execs),'artifacts':len(r.get('artifacts',[]))})
    personal=proof['steps']['personal']['id'];shared=proof['steps']['approve']['id']
    archive=get('skill-package',actor='bob',id=shared)
    with zipfile.ZipFile(io.BytesIO(archive)) as z:assert len(z.namelist())==3
    denied=[('skill-package',{'actor':'bob','id':personal}),('skill-package',{'actor':'outsider','id':shared}),
            ('artifact',{'actor':'bob','run':proof['steps']['source']['runId'],'path':'outputs\\summary.json'})]
    for route,params in denied:
        try:get(route,**params)
        except urllib.error.HTTPError as e:assert e.code==403
        else:raise AssertionError('Unauthorized download allowed')
    (root/'approved-v2.skill').write_bytes(archive)
    report={'passed':True,'kind':'post-acceptance-http-and-native-receipt-audit','modelCallsMadeByThisAudit':0,
        'successfulRuns':len(records),'modelFetchStartsInCase':requests,'runs':records,
        'checks':['official creator read and package','real exec receipts','selected files unchanged',
                  'all delivery downloads match SHA256','Bob can download approved skill',
                  'private and cross-organization downloads return 403'],
        'metrics':{a:snapshots[a]['metrics'] for a in ('alice','bob')}}
    (root/'postcheck.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
