"""Safe current snapshot; actual API progression, no controller-heartbeat shortcut."""
import json,time,subprocess,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 a=json.loads((ROOT/'reports/active_rollout.json').read_text())
 receipts=[json.loads(p.read_text()) for p in (ROOT/'ledger').glob('*.json')]
 receipts=[r for r in receipts if a['attempt'] in r.get('route','')]
 freeze=json.loads((ROOT/'reports/phase_manifest.json').read_text());errors=[n for n,d in freeze['files'].items() if hashlib.sha256((ROOT/n).read_bytes()).hexdigest()!=d]
 ident=Path(f'/proc/{a["pid"]}/stat');same=ident.exists() and ident.read_text().split(') ',1)[1].split()[19]==a['start_ticks']
 inspected=json.loads(subprocess.check_output(['docker','inspect',a['container']],text=True))[0]
 probe={}
 if inspected['State']['Running']:
  subprocess.run(['docker','cp',str(ROOT/'reports/live_probe.py'),a['container']+':/tmp/rw285_probe.py'],check=True,stdout=subprocess.DEVNULL)
  probe=json.loads(subprocess.check_output(['docker','exec',a['container'],'python3','/tmp/rw285_probe.py'],text=True))
 r={'sampled_epoch':time.time(),'version':'rw_evolution_collection_v1','source_pool_registered':26,'references_admitted':1,'complete_trajectories':0,'active_task':'minipaint.training','round':1,'round_limit':3,'attempt':a['attempt'],'controller_identity_matches':same,'container_running':inspected['State']['Running'],'freeze_files_checked':len(freeze['files']),'freeze_mismatches':errors,'api_requests':len(receipts),'api_completed':sum(r.get('response_complete',False) for r in receipts),'api_in_progress':sum(r.get('api_outcome')=='in_progress' for r in receipts),'api_failed':sum(r.get('api_outcome')=='transport_or_protocol_failure' for r in receipts),'cumulative_recovered_image_blocks':sum(r.get('image_transport',{}).get('recovered_image_blocks',0) for r in receipts),'last_actual_api_started':max([r.get('started_at','') for r in receipts],default=None),'native':probe,'model_requested':'deepseek-v4-flash-vision-exp','models_reported':sorted({r['model_reported'] for r in receipts if r.get('model_reported')}),'physical_backend_checkpoint':'unknown','old_corravale_resumed':False,'learning_or_250_evaluation_started':False}
 (ROOT/'reports/health_monitor_state.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
 status=json.loads((ROOT/'reports/collection_status.json').read_text());status.update(state='first_reference_admitted_first_rollout_running' if inspected['State']['Running'] else 'first_rollout_native_ended_pending_audit',new_reference_accepted=1,active_task='minipaint.training',active_round=1,complete_trajectories=0,latest_health='reports/health_monitor_state.json')
 for t in status['tasks']:
  if 'minipaint' in t['source_family_id'].lower():t.update(state='first_rollout_running' if inspected['State']['Running'] else 'native_ended_pending_audit',rounds_started=1,actual_runtime_task_id='minipaint.training',active_attempt=a['attempt'])
 (ROOT/'reports/collection_status.json').write_text(json.dumps(status,indent=2))
if __name__=='__main__':main()
