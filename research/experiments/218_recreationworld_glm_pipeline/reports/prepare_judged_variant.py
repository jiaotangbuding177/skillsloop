"""Create an isolated adapter variant; never edit v2 or its active attempt."""
from pathlib import Path
import shutil,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
source=ROOT/'scripts/pipeline.py'
old=source.read_text()
new=old
changes={
    "REPORTS = ROOT / 'reports'":"REPORTS = ROOT / 'reports/judged_v3'",
    "'rw_web_glm_pipeline_v2_lf'":"'rw_web_glm_pipeline_v3_glm_judge'",
    "label=f'{stage}_{arm}_{time.time_ns()}'":"label=f'judged_v3_{stage}_{arm}_{time.time_ns()}'",
    "'-e','USE_VLM_JUDGE=false'":"'-e','USE_VLM_JUDGE=true'",
    "if stage=='eval': cmd+=['--eval-target','reference']":"cmd+=['--vlm-key','local','--vlm-model',model,'--vlm-base-url',BASE.replace('/probe/',f'/{label}_judge/') ]\n    if stage=='eval': cmd+=['--eval-target','reference']",
    "'judge':'disabled; no paper-comparable VLM headline'":"'judge':'official assertion judge using GLM-5.3-Flash; differs from paper judge'",
    "files.append({'path':'vendor/RecreationWorld/Dockerfile218'":"files.append({'path':'scripts_judged/pipeline.py','sha256':sha(ROOT/'scripts_judged/pipeline.py')})\n    files.append({'path':'vendor/RecreationWorld/Dockerfile218'",
    "manifest=json.loads((REPORTS/'phase_manifest.json').read_text())":"judge=json.loads((ROOT/'reports/judge_acceptance.json').read_text())\n    if not judge.get('passed'): raise RuntimeError('Official judge acceptance required')\n    packaging=json.loads((ROOT/'reports/reference_packaging.json').read_text())\n    if sha(DATA/'released/web/corravale.example/reference/reference.tar.gz')!=packaging['sha256']: raise RuntimeError('Reference archive changed')\n    manifest=json.loads((REPORTS/'phase_manifest.json').read_text())",
}
for before,after in changes.items():
    assert new.count(before)==1, 'Ambiguous adapter transformation: '+before[:40]
    new=new.replace(before,after)
target=ROOT/'scripts_judged/pipeline.py'
assert not target.exists(), 'Version already exists; refuse overwrite'
target.parent.mkdir(exist_ok=True)
compile(new,str(target),'exec')
target.write_text(new)
reports=ROOT/'reports/judged_v3';reports.mkdir(exist_ok=True)
for name in ['dataset_manifest.json','model_acceptance.json']:
    shutil.copyfile(ROOT/'reports'/name,reports/name)
audit=dict(version='rw_web_glm_pipeline_v3_glm_judge',parent_version='rw_web_glm_pipeline_v2_lf',
    v2_unchanged=source.read_text()==old,parent_sha256=hashlib.sha256(old.encode()).hexdigest(),
    variant_sha256=hashlib.sha256(new.encode()).hexdigest(),changes='official VLM enabled, GLM judge separately routed; archive and judge acceptance gates; distinct reports and labels',
    judge_limit='GLM agent and judge share model; not paper judge or independent judge validation',
    inputs='same frozen public canary; no score-dependent replacement')
(reports/'variant_manifest.json').write_text(json.dumps(audit,indent=2))
print(json.dumps(audit))
