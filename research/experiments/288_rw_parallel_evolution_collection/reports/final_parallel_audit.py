import json,hashlib,time,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
records=[json.loads(p.read_text()) for p in (root/'reports/active').glob('*.json')]
mini=next(x for x in records if x['task']=='minipaint')
assert mini['state']=='native_finished' and mini['round']==3
out=Path(mini['output']);copy=json.loads((out/'private_raw_sessions/copy_manifest.json').read_text())
for x in copy['files']:
    p=out/'private_raw_sessions'/x['file'];assert p.stat().st_size==x['bytes'];assert hashlib.sha256(p.read_bytes()).hexdigest()==x['source_sha256']==x['copied_sha256']
checks={}
for p in (root/'reports').glob('freeze*.json'):
    j=json.loads(p.read_text());bad=[n for n,h in j['files'].items() if not (root/n).is_file() or hashlib.sha256((root/n).read_bytes()).hexdigest()!=h]
    checks[p.name]={'files':len(j['files']),'mismatches':bad};assert not bad
sq=next(x for x in records if x['task']=='squoosh')
code="import json,time;from pathlib import Path;p=Path('/workspace/recreation/trajectory.jsonl');print(json.dumps({'trajectory_bytes':p.stat().st_size if p.exists() else None,'trajectory_mtime':p.stat().st_mtime if p.exists() else None,'lines':sum(1 for _ in p.open()) if p.exists() else None,'sample_epoch':time.time()}))"
r=subprocess.run(['docker','exec',sq['container'],'python3','-c',code],capture_output=True,text=True)
trace=json.loads(r.stdout) if r.returncode==0 else {'read_error':r.stderr[-300:]}
mx=(root/'runs/score_only_minipaint_1791129424129760714/score.json')
report={'epoch':time.time(),'phase':'rw_parallel_v2.4_with_external_transport_v2.5_and_resource_v2.6.1','max_workers':2,'source_pool':26,'admitted_apps':2,'pending_admission_apps':24,'full_round_cap':3,'minipaint_finished_round3':mini,'minipaint_raw_complete':copy,'squoosh_real_trace_sample':trace,'freeze_checks':checks,'external_resource_manifest':'external_resource_v261_manifest.json','transport_manifest':'live_transport_v25_manifest.json','transport_correction':'ss -K did not close old socket. GET-only new-connection NAT was verified; miniPaint finished naturally before actual model migration. Combined Squoosh route during overlap cannot be attributed by route alone. reset_exact_connection_v251 asserted old socket absent and applied no filter rule.','overlap_seconds':mini['ended_epoch']-max(mini['started_epoch'],sq['started_epoch']),'current_phase_not_same_runtime_resource_as_original_v24':True,'success_or_high_quality_accepted_apps':0,'final_canonical_and_originality_audit':'pending','skills_learning_started':False,'benchmark_250_evaluation_started':False}
(root/'reports/current_phase_v261_manifest.json').write_text(json.dumps(report,indent=2));print(json.dumps({'overlap_seconds':report['overlap_seconds'],'minipaint_score':mini['scores']['final_score'],'complete_raw_bytes':sum(x['bytes'] for x in copy['files']),'squoosh_trace':trace,'all_prior_freezes_valid':True}))
