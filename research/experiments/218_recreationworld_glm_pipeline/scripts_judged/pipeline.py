"""Independent RecreationWorld preparation and official execution adapter.

No agent loop or scoring implementation. Run with the existing WSL Python.
Credentials stay in the existing model relay; only its local placeholder is used.
"""
import argparse
import base64
import concurrent.futures
import hashlib
import io
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / 'vendor/RecreationWorld'
REPORTS = ROOT / 'reports/judged_v3'
REPO = 'Qwen/RecreationBench'
REV = '284341f8fc3d6680dd57ca5414fed92a0fe33b95'
COMMIT = 'b5cda868f44932dc84ea68e3b3053bc418621aa3'
IMAGE = 'skillloop-rw-web:218-v2'
DATA = Path('/var/tmp/skillloop_rw218/datasets') if sys.platform=='linux' else ROOT/'datasets'
MODEL_RESOURCE = ROOT.parent / '115_cogym_spagent_full/reports/model_resource.json'
BASE = 'http://172.28.64.1:8129/218_recreationworld/probe/v1'

def save(name, value):
    REPORTS.mkdir(parents=True, exist_ok=True)
    p = REPORTS / name
    tmp = p.with_suffix(p.suffix + '.tmp')
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    tmp.replace(p)

def fetch(url):
    with urllib.request.urlopen(url, timeout=90) as r:
        return r.read()

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()

def prepare():
    index = json.loads(fetch(f'https://huggingface.co/api/datasets/{REPO}/revision/{REV}'))
    paths = [s['rfilename'] for s in index['siblings'] if s['rfilename'].startswith('web/')]
    groups = {}
    for path in paths:
        groups.setdefault(path.split('/')[1], []).append(path)
    # Transport canary selected by file count before any task score is observed.
    task = min(groups, key=lambda k: (len(groups[k]), k))
    selected = groups[task]
    target = DATA / 'released'
    def download(name):
        p = target / name
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists():
            from urllib.parse import quote
            data = fetch(f'https://huggingface.co/datasets/{REPO}/resolve/{REV}/{quote(name,safe="/")}')
            tmp = p.with_suffix(p.suffix+'.partial')
            tmp.write_bytes(data)
            tmp.replace(p)
        return {'path':name, 'bytes':p.stat().st_size, 'sha256':sha(p)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        manifest = list(pool.map(download, selected))
    save('dataset_manifest.json', {'repo':REPO, 'revision':REV, 'split':'test',
        'role':'infrastructure_canary_excluded_from_reported_test',
        'task_id':task, 'selection':'minimum file count, lexical tie-break',
        'files':manifest, 'complete':len(manifest)==len(selected)})
    print(json.dumps({'task_id':task,'downloaded_files':len(manifest)}), flush=True)

def materialize():
    # POSIX mirror filenames such as "style.css?v=1" cannot be stored on Windows.
    data=json.loads((REPORTS/'dataset_manifest.json').read_text())
    for item in data['files']:
        source=ROOT/'download_staging'/item['staged_file']
        if sha(source)!=item['sha256']: raise RuntimeError('Staging hash changed')
        relative=Path(item['path'])
        if relative.is_absolute() or '..' in relative.parts: raise RuntimeError('Unsafe dataset path')
        target=DATA/'released'/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source,target)
    data['runtime_root']=str(DATA)
    save('dataset_manifest.json',data)
    print(json.dumps({'materialized':len(data['files']),'task_id':data['task_id']}))

def api(payload):
    req = urllib.request.Request(BASE+'/chat/completions',
        data=json.dumps(payload).encode(), headers={'Content-Type':'application/json',
        'Authorization':'Bearer local'})
    started = time.time()
    try:
        with urllib.request.urlopen(req, timeout=240) as r:
            result=json.load(r)
        return result, {'http_status':200, 'elapsed_s':round(time.time()-started,2)}
    except Exception as exc:
        # Never copy upstream bodies, URLs with query tokens, or model payloads to reports.
        return None, {'error_class':type(exc).__name__, 'http_status':getattr(exc,'code',None),
            'elapsed_s':round(time.time()-started,2)}

def probe():
    from PIL import Image, ImageDraw, ImageFont
    model = json.loads(MODEL_RESOURCE.read_text(encoding='utf-8-sig'))['model_id']
    results=[]
    # Random visual-only strings prevent a generic "image accepted" answer from passing.
    for i in range(2):
        nonce=''.join(secrets.choice('23456789ABCDEFGHJKLMNPQRSTUVWXYZ') for _ in range(6))
        picture=Image.new('RGB',(480,150),'white')
        draw=ImageDraw.Draw(picture)
        font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',56)
        draw.text((35,40),nonce,fill='black',font=font)
        buf=io.BytesIO(); picture.save(buf,format='PNG')
        data, evidence=api({'model':model,'temperature':0,'max_tokens':128,
            'messages':[{'role':'user','content':[
                {'type':'text','text':'Read the six-character code printed in this image. Reply only with the code.'},
                {'type':'image_url','image_url':{'url':'data:image/png;base64,'+base64.b64encode(buf.getvalue()).decode()}}]}]})
        answer=((data or {}).get('choices') or [{}])[0].get('message',{}).get('content')
        evidence.update({'case':i,'image_sha256':hashlib.sha256(buf.getvalue()).hexdigest(),
            'expected':nonce,'answer':answer,'passed':isinstance(answer,str) and answer.strip()==nonce})
        results.append(evidence)
    tool_data,tool_evidence=api({'model':model,'temperature':0,'max_tokens':256,
        'messages':[{'role':'user','content':'Call report_status with status equal to ready.'}],
        'tools':[{'type':'function','function':{'name':'report_status','description':'Report readiness',
            'parameters':{'type':'object','properties':{'status':{'type':'string','enum':['ready']}},
            'required':['status'],'additionalProperties':False}}}],
        'tool_choice':{'type':'function','function':{'name':'report_status'}}})
    calls=((tool_data or {}).get('choices') or [{}])[0].get('message',{}).get('tool_calls',[])
    try:
        tool_evidence['passed']=len(calls)==1 and calls[0]['function']['name']=='report_status' and json.loads(calls[0]['function']['arguments'])=={'status':'ready'}
    except (ValueError,KeyError,TypeError):
        tool_evidence['passed']=False
    report={'time':time.time(),'model_id':model,'images':results,'tool_protocol':tool_evidence,
        'vision_ready':all(x['passed'] for x in results),'tools_ready':tool_evidence['passed'],
        'scope':'gateway OpenAI input only; native CLI end-to-end requires separate canary'}
    save('model_acceptance.json',report)
    print(json.dumps({'vision_ready':report['vision_ready'],'tools_ready':report['tools_ready']}),flush=True)

def freeze():
    head=subprocess.check_output(['git','-C',str(VENDOR),'rev-parse','HEAD'],text=True).strip()
    if head!=COMMIT: raise RuntimeError('Official source identity changed')
    tracked=subprocess.check_output(['git','-C',str(VENDOR),'ls-files'],text=True).splitlines()
    files=[{'path':str((VENDOR/p).relative_to(ROOT)), 'sha256':sha(VENDOR/p)} for p in tracked]
    files += [{'path':str(p.relative_to(ROOT)), 'sha256':sha(p)} for p in (ROOT/'scripts').glob('*') if p.is_file()]
    files += [{'path':str(p.relative_to(ROOT)), 'sha256':sha(p)} for p in (VENDOR/'.rw218-proxy').rglob('*') if p.is_file()]
    files.append({'path':'scripts_judged/pipeline.py','sha256':sha(ROOT/'scripts_judged/pipeline.py')})
    files.append({'path':'vendor/RecreationWorld/Dockerfile218','sha256':sha(VENDOR/'Dockerfile218')})
    deps=[ROOT.parent/'196_cogym_212_ecnu_learning/scripts/learn_library_ecnu.py',
        ROOT.parent/'196_cogym_212_ecnu_learning/scripts/resources.py',
        ROOT.parent/'115_cogym_spagent_full/scripts/autoskill_bootstrap.py',
        ROOT.parent/'115_cogym_spagent_full/scripts/model_resource.py']
    deps += list((ROOT.parent/'115_cogym_spagent_full/vendor/AutoSkill').rglob('*.py'))
    files += [{'path':os.path.relpath(p,ROOT),'sha256':sha(p)} for p in deps if '__pycache__' not in p.parts]
    save('phase_manifest.json',{'version':'rw_web_glm_pipeline_v3_glm_judge','commit':head,
        'dataset_revision':REV,'image_tag':IMAGE,'vendor_modified':False,'files':files,
        'evaluation':'official task_score/program_score/vlm_score; no custom scorer',
        'training':'external trajectories only, never released test inputs',
        'skills_experiment':'not yet accepted; default native CLI disables Skill tool',
        'canary_excluded':True})

def check():
    judge=json.loads((ROOT/'reports/judge_acceptance.json').read_text())
    if not judge.get('passed'): raise RuntimeError('Official judge acceptance required')
    packaging=json.loads((ROOT/'reports/reference_packaging.json').read_text())
    if sha(DATA/'released/web/corravale.example/reference/reference.tar.gz')!=packaging['sha256']: raise RuntimeError('Reference archive changed')
    manifest=json.loads((REPORTS/'phase_manifest.json').read_text())
    bad=[x['path'] for x in manifest['files'] if not (ROOT/x['path']).is_file() or sha(ROOT/x['path'])!=x['sha256']]
    if bad: raise RuntimeError('Freeze changed: '+','.join(bad[:3]))
    data=json.loads((REPORTS/'dataset_manifest.json').read_text())
    for x in data['files']:
        if sha(DATA/'released'/x['path'])!=x['sha256']: raise RuntimeError('Dataset changed')
    print(json.dumps({'freeze_verified':len(manifest['files']),'task_id':data['task_id'],'dataset_verified':len(data['files'])}))

def run(stage, arm='baseline', library=None):
    if sys.platform!='linux': raise RuntimeError('Execute inside WSL, never user Windows desktop')
    check()
    if (ROOT/'private/STOP').exists(): raise RuntimeError('User STOP present')
    if stage=='recreation_eval':
        acceptance=json.loads((REPORTS/'model_acceptance.json').read_text())
        if not acceptance['vision_ready'] or not acceptance['tools_ready']:
            raise RuntimeError('Vision/tool acceptance failed; refusing misleading visual benchmark')
    import fcntl
    lock=(ROOT/'pipeline.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    task=json.loads((REPORTS/'dataset_manifest.json').read_text())['task_id']
    model=json.loads(MODEL_RESOURCE.read_text(encoding='utf-8-sig'))['model_id']
    if arm=='skills' and (stage!='recreation_eval' or library is None):
        raise RuntimeError('Skills arm requires an accepted library and recreation_eval')
    label=f'judged_v3_{stage}_{arm}_{time.time_ns()}'
    out=ROOT/'runs'/label; out.mkdir(parents=True)
    cmd=['docker','run','--name','rw218-'+label,'--network','bridge',
        '--cap-add','SYS_ADMIN','--cap-add','NET_ADMIN','--security-opt','seccomp=unconfined',
        '--mount',f'type=bind,src={DATA},dst=/var/lib/mockweb-scorer/download,readonly',
        '--mount',f'type=bind,src={ROOT}/scripts/container_entry.py,dst=/opt/rw218/container_entry.py,readonly',
        '--mount',f'type=bind,src={out},dst=/results',
        '-e','RB_ARTIFACT_ROOT=/var/lib/mockweb-scorer/download','-e','RB_ARTIFACT_BACKEND=filesystem',
        '-e','RB_UNIFIED_PREFIX=released','-e','RB_SCRIPTS_DIR=/workspace/RecreationBench/scripts',
        '-e','RB_MODEL_API_KEY','-e','USE_VLM_JUDGE=true',IMAGE,
        'python3','/opt/rw218/container_entry.py',
        '--platform','web','--task-id',task,'--stage',stage,'--agent-cli','claude',
        '--api-mode','openai','--model',model,'--model-base-url',BASE.replace('/probe/',f'/{label}/'),
        '--capture-tool-use-screenshots','true','--output-dir','/results']
    cmd+=['--vlm-key','local','--vlm-model',model,'--vlm-base-url',BASE.replace('/probe/',f'/{label}_judge/') ]
    if stage=='eval': cmd+=['--eval-target','reference']
    # Native Read consumes exported SKILL.md on demand via the CLI's own context.
    # Skill tool stays disabled by the official harness; this treatment is explicit.
    if stage=='recreation_eval':
        text='Consult relevant installed workflow skills when applicable; use the native Read tool to inspect the named SKILL.md before applying it. Treat skills as fallible guidance and verify against the observed app.\n\nInstalled skill catalog:\n'
        if arm=='skills':
            library=library.resolve()
            if not library.is_relative_to((ROOT/'libraries').resolve()):
                raise RuntimeError('Library must be a new 218 native export, not a borrowed live Co-Gym bank')
            accepted=ROOT/'autoskill_state'/library.name/'accepted_library.json'
            catalog=json.loads(accepted.read_text())
            if catalog['embedding_errors'] or catalog['empty_library']: raise RuntimeError('No accepted semantic skills')
            import yaml
            for relative,expected in catalog['hashes'].items():
                p=(library/relative).resolve()
                if not p.is_relative_to(library) or sha(p)!=expected:raise RuntimeError('Library changed')
                if p.name=='SKILL.md':
                    content=p.read_text()
                    header=yaml.safe_load(content.split('---',2)[1]) if content.startswith('---') else {}
                    text+=json.dumps({'name':header.get('name',p.parent.name),
                        'description':header.get('description',''), 'path':'/opt/rw218-skills/'+relative},ensure_ascii=False)+'\n'
            pos=cmd.index(IMAGE)
            cmd[pos:pos]=['--mount',f'type=bind,src={library},dst=/opt/rw218-skills,readonly']
        else: text+='None.\n'
        (out/'skill_context.md').write_text(text,encoding='utf-8')
    # Local relay placeholder is not an external credential. No provider keys mounted.
    env=os.environ.copy(); env['RB_MODEL_API_KEY']='local'
    with (out/'controller.log').open('w') as log:
        rc=subprocess.call(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)
    metrics=out/'metrics.json'
    save('pipeline_status.json',{'attempt':label,'stage':stage,'returncode':rc,
        'native_metrics':str(metrics.relative_to(ROOT)) if metrics.exists() else None,
        'classification':'read native outcome_class; missing metrics is infrastructure failure, not zero',
        'judge':'official assertion judge using GLM-5.3-Flash; differs from paper judge', 'skills':arm,
        'skills_library':str(library) if library else None,
        'skills_consumption':'native CLI context catalog plus on-demand native Read; acceptance requires actual Read evidence'})
    print(json.dumps({'attempt':label,'returncode':rc,'has_native_metrics':metrics.exists()}))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('command',choices=['prepare','materialize','probe','freeze','check','setup','reference','canary'])
    p.add_argument('--arm',choices=['baseline','skills'],default='baseline')
    p.add_argument('--library',type=Path)
    a=p.parse_args()
    if a.command=='prepare': prepare()
    elif a.command=='materialize': materialize()
    elif a.command=='probe': probe()
    elif a.command=='freeze': freeze()
    elif a.command=='check': check()
    else: run({'setup':'setup','reference':'eval','canary':'recreation_eval'}[a.command],a.arm,a.library)
