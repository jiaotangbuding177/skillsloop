"""Functional acceptance of unchanged official VLM judge; not a task score."""
from pathlib import Path
import json,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'vendor/RecreationWorld/scripts'))
from common.vlm_judge import resolve,judge_assertions
source=json.loads((ROOT/'reports/public_vlm_assertions.json').read_text())
selected=source['assertions'][:4]
view=selected[0]['screenshot']
assert all(x['screenshot']==view for x in selected)
image=ROOT/'runs/eval_baseline_1791032188424599820/reference_eval/agent_screenshots'/view
cfg=resolve(model='GLM-5.3-Flash',base_url='http://172.28.64.1:8129/218_recreationworld/judge_probe/v1',api_key='local')
started=time.time()
verdicts=judge_assertions(str(image),[x['assertion'] for x in selected],cfg=cfg)
result=dict(role='official VLM transport/parser acceptance, not RecreationBench score',model=cfg['model'],
    different_from_paper_judge=True,assertion_ids=[x['id'] for x in selected],verdicts=verdicts,
    passed=len(verdicts)==4 and all(x.get('pass') is not None and not x.get('error') for x in verdicts),
    elapsed_seconds=time.time()-started)
(ROOT/'reports/judge_acceptance.json').write_text(json.dumps(result,indent=2))
print(json.dumps({k:result[k] for k in ['role','model','passed','elapsed_seconds']}))
