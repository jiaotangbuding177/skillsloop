"""Validate complete native scoring evidence; never change scores or source."""
import hashlib,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
current=json.loads((root/'reports/current_run.json').read_text()); out=Path(current['path'])
status=json.loads((out/'evaluation_status.json').read_text())
assert status['state']=='native_finished' and status['returncode']==0,'Scoring not complete'
native=json.loads((out/'run.json').read_text()); scores=native['scores']
vlm=json.loads((out/'native_vlm_result.json').read_text())
before=json.loads((out/'candidate_source_before.json').read_text()); after=json.loads((out/'candidate_source_after.json').read_text())
source=root.parent/'257_recreationworld_route_semantics_v15/runs'/current['source_attempt']/'recreation'
source_mismatches=[name for name,sha in before.items() if not (source/name).is_file() or hashlib.sha256((source/name).read_bytes()).hexdigest()!=sha]
screens=out/'eval_results/agent_screenshots'
expected={(p.parent.name,p.stem) for p in screens.glob('*/*.png') if p.stem in ['desktop','mobile']}
details=vlm['page_details']; seen=set(); problems=[]; zero_weight_abstentions=[]; item_count=0; positive_count=0
def valid(v):
 if isinstance(v.get('pass'),bool): return True
 s=v.get('score'); return isinstance(s,(int,float)) and math.isfinite(s) and 0<=s<=1
for page,detail in details.items():
 for viewport,d in detail.get('per_viewport',{}).items():
  pair=(page,viewport); seen.add(pair); verdicts=d.get('verdicts',[]); total=d.get('total'); item_count+=len(verdicts)
  if d.get('error') or d.get('failed') or d.get('note')=='no agent screenshot': problems.append([page,viewport,'native_judge_error_or_missing_image'])
  if total is None or total!=len(verdicts) or total<=0: problems.append([page,viewport,'verdict_count_mismatch'])
  weights=[v.get('weight',1) for v in verdicts]
  if any(not isinstance(w,(int,float)) or not math.isfinite(w) or w<0 for w in weights): problems.append([page,viewport,'invalid_weights']); continue
  positive=[v for v,w in zip(verdicts,weights) if w>0]; positive_count+=len(positive)
  if positive and (d.get('score') is None or d.get('abstained') or any(not valid(v) for v in positive)): problems.append([page,viewport,'unusable_positive_weight_verdict'])
  if verdicts and not positive and d.get('score') is None and d.get('abstained') and not d.get('error') and not d.get('failed'): zero_weight_abstentions.append([page,viewport])
coverage_ok=bool(expected) and expected==seen and len({x[0] for x in expected})==20 and len(expected)==40 and not problems
snapshot=json.loads((root/'reports/scoring_snapshot.json').read_text())
api_terminal=snapshot['in_progress']==0 and snapshot['complete']>=len(seen)
artifact=json.loads((out/'scored_artifact_sha256.json').read_text())
artifact_ok=hashlib.sha256((out/'scored_index.html').read_bytes()).hexdigest()==artifact['index_html_sha256']
build_status=native.get('build_result',{}).get('status')
threshold_met=scores['final_score']>=0.75
accepted=all([threshold_met,coverage_ok,api_terminal,status['source_unchanged'],before==after,not source_mismatches,artifact_ok,scores.get('vlm_enabled') is True])
report={'version':'rw_complete_trajectory_qualification_v1','source_attempt':current['source_attempt'],'scoring_run':current['run'],'accepted_success_trajectory':accepted,'native_final_score':scores['final_score'],'official_threshold':0.75,'threshold_met':threshold_met,'native_breakdown':scores['breakdown'],'native_vlm_score':vlm['score'],'expected_views':len(expected),'returned_views':len(seen),'covered_pages':len(details),'coverage_ok':coverage_ok,'verdict_items':item_count,'positive_weight_items':positive_count,'zero_weight_expected_abstentions':zero_weight_abstentions,'coverage_problems':problems,'missing_views':sorted(expected-seen),'unexpected_views':sorted(seen-expected),'api_complete':snapshot['complete'],'historical_api_failures_preserved':snapshot['failed'],'api_in_progress':snapshot['in_progress'],'api_terminal_and_native_views_complete':api_terminal,'source_hashes':len(before),'source_unchanged':before==after,'model_source_mismatches':source_mismatches,'scored_artifact_hash_verified':artifact_ok,'scored_artifact_sha256':artifact['index_html_sha256'],'same_provider_self_judge':True,'exact_backend_unverified':True,'corrective_demonstration_not_baseline':True,'canary_excluded_from_headline_results':True,'finite_authorship_audit_not_security_proof':True}
report.update(native_build_status=build_status, official_rebuild_verified=False if build_status=='install_failed' else None, original_artifact_metadata_official_rebuild_claim_corrected=build_status=='install_failed', scoring_scope='Native scoring of preserved model-built artifact; independent rebuild failed offline dependency installation', request_count_start_fallback_correction='Final status omits start epoch; use immutable run-label timestamp, without resetting ledger')
(root/'reports/trajectory_qualification.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))
