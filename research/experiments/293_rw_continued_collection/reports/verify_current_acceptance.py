"""Persist one fresh identity/freeze/export check; no model/evaluator calls."""
import hashlib,json,time
from pathlib import Path
from observe_current import snapshot,alive
ROOT=Path(__file__).resolve().parents[1]
freeze=json.loads((ROOT/'reports/freeze_squoosh_round2.json').read_text())
bad=[p for p,d in freeze['files'].items() if not Path(p).is_file() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=d]
assert not bad,bad
live=snapshot();supervisor=json.loads((ROOT/'reports/supervisor_identity.json').read_text());assert alive(supervisor)
assert live['controller_alive'] and live['container']['Status']=='running' and live['api']['complete']>0
assert live['limits']['Memory']==3221225472 and live['actor']['round']==2
assert live['native_activity']['restored_round']['round']==2
exports=json.loads((ROOT/'reports/existing_public_exports.json').read_text())
for family,m in exports['families'].items():
 p=ROOT/'exports'/family/'public_messages.jsonl';assert hashlib.sha256(p.read_bytes()).hexdigest()==m['public_view_sha256']
 assert not m['unmatched_tool_call_ids'] and not m['orphan_tool_result_ids'] and not m['conflicting_uuid_records']
report={'epoch':time.time(),'frozen_files':len(freeze['files']),'freeze_mismatches':bad,'supervisor_alive':True,
        'real_native_resume_and_api_verified':True,'live_snapshot':live,'export_view_hashes_and_tool_pairs_passed':True,
        'new_scoring_or_model_calls_from_verification':0,'final_trajectory_success':'not yet known'}
(ROOT/'reports/start_acceptance.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'freeze_files':len(freeze['files']),'mismatches':len(bad),'api':live['api'],'native_bytes':live['native_activity']['native_session']['bytes'],'source_files':live['native_activity']['candidate_source']['files'],'container':live['container'],'supervisor_alive':True}))
