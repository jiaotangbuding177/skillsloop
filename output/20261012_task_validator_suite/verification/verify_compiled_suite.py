"""Check every generated entry without business tasks, models or network."""
import collections
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

SUITE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(SUITE))
import _runtime as runtime


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest=runtime.read_json(SUITE/'manifest.json');base=runtime.load_engine(); rows=[]
    required={'检查对象','通过条件','取证方法','用户要求依据','校验参数'}
    assert len(manifest['tasks'])==226
    for path,value in manifest['source_pins'].items():assert sha(Path(path))==value,('source_mutated',path)
    for task in manifest['tasks']:
        sid=task['source_session_id'];script=SUITE/task['script'];contract=runtime.read_json(SUITE/task['contract'])
        assert sha(script)==task['script_sha256'];assert sha(SUITE/task['contract'])==task['contract_sha256']
        for c in contract['checks']:
            assert c['kind'] in base.HANDLERS;assert not base.parameter_support(c)
            assert required<=runtime.frozen_row_fields(c,contract).keys()
        description=subprocess.run([sys.executable,str(script),'--describe'],capture_output=True,text=True,encoding='utf-8',timeout=20)
        assert description.returncode==0,(sid,description.stderr)
        body=json.loads(description.stdout);assert body['source_session_id']==sid;assert len(body['checks'])==len(contract['checks'])
        assert all(required<=c.keys() for c in body['checks'])
        with tempfile.TemporaryDirectory() as folder:
            request=Path(folder)/'request.json';response=Path(folder)/'response.json'
            request.write_text(json.dumps({'task_id':'heldout_'+sid,'source_session_id':sid,'workspace':folder,'result':{}}),'utf-8')
            completed=subprocess.run([sys.executable,str(script),str(request),str(response)],capture_output=True,text=True,encoding='utf-8',timeout=20)
            assert completed.returncode==0,(sid,completed.stderr)
            output=runtime.read_json(response)
            assert output['score'] is None and output['task_success_status']=='UNSCORED',(sid,output)
            assert output['reason']=='independent_final_evidence_missing_or_invalid',(sid,output['reason'])
            assert output['historical_ai_read'] is False and output['quality_scored'] is False
        rows.append({'source_session_id':sid,'describe':'passed','missing_evidence':'UNSCORED','pin_and_parameters':'passed'})
    source_scorer=Path('D:/skillloop/research/pipelines/task_group_pipeline/final_state_scorer.py')
    assert sha(source_scorer)==sha(SUITE/'vendor/final_state_scorer.py')
    result={'tasks_verified':len(rows),'entry_invocations':2*len(rows),'sources_unchanged':True,
            'five_fields_complete':True,'model_calls':0,'business_runs':0,'tasks':rows}
    (SUITE/'verification/全任务入口核验.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='tasks'},ensure_ascii=False))


if __name__=='__main__':main()
