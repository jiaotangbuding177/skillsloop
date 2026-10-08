"""Observe first rollout completion; no model calls, retries, or frozen edits."""
import json,time,subprocess,hashlib,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def main():
 identity={'pid':os.getpid(),'start_ticks':Path(f'/proc/{os.getpid()}/stat').read_text().split(') ',1)[1].split()[19],'scope':'read-only first rollout completion observer','does_not_start_agent':True}
 (ROOT/'reports/completion_observer_identity.json').write_text(json.dumps(identity,indent=2))
 while True:
  subprocess.run(['python3',str(ROOT/'reports/monitor.py')],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
  a=json.loads((ROOT/'reports/active_rollout.json').read_text())
  if a['state']!='running':break
  time.sleep(30)
 out=Path(a['output']);scores=out/'eval_results/scores.json';raw=out/'private_raw_sessions/copy_manifest.json'
 actual=json.loads(scores.read_text()) if scores.exists() else None
 report={'attempt':a['attempt'],'round':1,'max_rounds':3,'native_returncode':a.get('returncode'),'actual_score_artifact':str(scores) if scores.exists() else None,'actual_scores_sha256':hashlib.sha256(scores.read_bytes()).hexdigest() if scores.exists() else None,'functional_visual_scores':actual.get('scores') if actual else None,'raw_full_session_copy_manifest':str(raw) if raw.exists() else None,'first_trace_admission':'pending completeness/image/tool/source originality audit','verified_success':None,'not_auto_accepted_from_native_passed':True,'correction_or_other_apps_not_started_by_this_observer':True,'completed_epoch':time.time()}
 (ROOT/'reports/first_completion.json').write_text(json.dumps(report,indent=2))
 status=json.loads((ROOT/'reports/collection_status.json').read_text());status.update(state='first_native_execution_ended_pending_trajectory_audit',native_executions_ended=1,accepted_complete_trajectories=0);(ROOT/'reports/collection_status.json').write_text(json.dumps(status,indent=2))
if __name__=='__main__':main()
