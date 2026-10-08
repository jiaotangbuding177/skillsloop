"""Read-only post-run evidence audit. Never edits native scores or trajectories."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
def audit(label):
    run=ROOT/'runs'/label
    metrics=json.loads((run/'metrics.json').read_text(encoding='utf-8')) if (run/'metrics.json').exists() else {}
    trajectory=run/'trajectory.jsonl'
    rows=[json.loads(line) for line in trajectory.read_text(encoding='utf-8').splitlines()] if trajectory.exists() else []
    results=[r for r in rows if r.get('type')=='result']
    tools=[b['name'] for r in rows for b in r.get('message',{}).get('content',[]) if isinstance(b,dict) and b.get('type')=='tool_use']
    receipts=[json.loads(p.read_text(encoding='utf-8')) for p in (ROOT/'ledger').glob('*.json')]
    receipts=[p for p in receipts if label in p.get('route','')]
    source=run/'recreation/src/App.tsx'
    source_changed=source.exists() and 'Ready to build' not in source.read_text(encoding='utf-8')
    details=run/'recreation/eval_results/test_details.json'
    detail=json.loads(details.read_text(encoding='utf-8')) if details.exists() else {}
    functional=detail.get('test_details',{}).get('functional',[])
    passed=sum(x.get('status')=='passed' for x in functional)
    api_complete=bool(receipts) and all(x.get('response_complete') for x in receipts)
    native_success=metrics.get('stage_recreation')=='succeeded'
    answer={'attempt':label,'metrics':metrics,'requests':len(receipts),'all_api_complete':api_complete,
        'trajectory_records':len(rows),'tool_use_records':len(tools),'tool_names':sorted(set(tools)),
        'terminal_result':[{'subtype':r.get('subtype'),'is_error':r.get('is_error'),'visible_result_characters':len(r.get('result') or ''),'summary_output':'<summary>' in (r.get('result') or '')} for r in results],
        'source_replaced_default':source_changed,'functional_total':len(functional),'functional_passed':passed,
        'trajectory_sha256':hashlib.sha256(trajectory.read_bytes()).hexdigest() if trajectory.exists() else None,
        'usable_verified_trajectory':False, 'delivery_candidate_has_some_functional_passes':bool(api_complete and native_success and source_changed and passed>0), 'acceptance_pending_complete_visual_and_authorship_audit':True,
        'all_functional_assertions_passed':bool(functional and passed==len(functional)),
        'visual_judge_verified':False,'benchmark_headline_accepted':False}
    dest=ROOT/'reports'/('audit_'+label+'.json'); dest.write_text(json.dumps(answer,ensure_ascii=False,indent=2))
    print(json.dumps({k:answer[k] for k in ('attempt','requests','all_api_complete','source_replaced_default','functional_total','functional_passed','usable_verified_trajectory')}))

if __name__=='__main__': audit(sys.argv[1])
