"""Validate and copy only prior own code and full session; no model calls."""
import hashlib, json, shutil, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT.parent/'288_rw_parallel_evolution_collection'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 prior=Path(sys.argv[1]).resolve();round_no=int(sys.argv[2]);assert round_no in (2,3)
 assert prior.is_relative_to(OLD/'runs') or prior.is_relative_to(ROOT/'runs')
 state=json.loads((prior/'run_agent_only.json').read_text())
 assert state['submitted'] and state['build_result']['status']=='success' and state['rollout']['native_returncode']==0
 score=json.loads((prior/'recreation/eval_results/scores.json').read_text());assert score['task_id']=='squoosh.training'
 s=score['scores'];details=json.loads((prior/'recreation/eval_results/test_details.json').read_text())['test_details']['functional']
 assert len(details)==6 and all(d['status'] in ('passed','failed') for d in details)
 assert not(s['dimension_details']['functional']['passed']==6 and s['visual_ssim_score']>=.85),'Successful: stop'
 cp=ROOT/'checkpoints/squoosh'/f'round{round_no-1}';assert not cp.exists();cp.mkdir(parents=True)
 for name in ('src','public','index.html','package.json','package-lock.json','vite.config.ts','tsconfig.json'):
  src=prior/'recreation'/name;dst=cp/'candidate'/name
  if not src.exists():continue
  dst.parent.mkdir(parents=True,exist_ok=True)
  if src.is_dir():shutil.copytree(src,dst)
  else:shutil.copy2(src,dst)
 raw=prior/'private_raw_sessions';manifest=json.loads((raw/'copy_manifest.json').read_text());sessions=[]
 for f in manifest['files']:
  rel=Path(f['file']);assert not rel.is_absolute() and '..' not in rel.parts
  src=raw/rel;assert src.stat().st_size==f['bytes'] and sha(src)==f['source_sha256']==f['copied_sha256']
  dst=cp/'sessions'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
  if src.suffix=='.jsonl' and len(rel.parts)==2:sessions.append(src.stem)
 assert len(sessions)==1
 feedback={'round':round_no,'maximum_full_rounds':3,'parent_attempt':prior.name,'session_id':sessions[0],
 'prior_passed':s['dimension_details']['functional']['passed'],'prior_total':6,'prior_visual_ssim':s['visual_ssim_score'],
 'failed_behavior_checks':[d['title'] for d in details if d['status']=='failed']}
 (cp/'feedback.json').write_text(json.dumps(feedback,indent=2))
 files={str(p.relative_to(cp)):sha(p) for p in cp.rglob('*') if p.is_file()}
 (cp/'checkpoint_manifest.json').write_text(json.dumps({'files':files,'source_raw_hash_verified':True,
 'only_own_candidate_and_session':True,'no_evaluator_or_reference_source':True},indent=2))
 (ROOT/'reports'/f'checkpoint_round{round_no}_admission.json').write_text(json.dumps({'epoch':time.time(),
 'parent_attempt':str(prior),'checkpoint':str(cp),'target_round':round_no,'session_id':sessions[0],
 'verified_files':len(files),'raw_source_manifest_sha256':sha(raw/'copy_manifest.json'),
 'prior_score_sha256':sha(prior/'recreation/eval_results/scores.json'),'no_model_calls':True,
 'feedback_only_actual_behavior_titles':True},indent=2))
 print(json.dumps({'checkpoint_admitted':True,'round':round_no,'files':len(files)}))
if __name__=='__main__':main()
