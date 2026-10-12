"""Read-only inventory for the authorized basic-delivery design audit."""
from pathlib import Path
import collections
import hashlib
import json
import importlib.util

ROOT = Path('D:/skillloop')
OUT = ROOT / 'output/20261012_task_validator_suite'
CHECKLIST = ROOT / 'output/20261012_evaluation_task_checkpoints/逐任务评测点明细.json'
SOURCE = ROOT / 'benchmark/enterprise_original_inputs_v10_20261011/evaluation/终态交付校验合同.jsonl'
SCORER = ROOT / 'research/pipelines/task_group_pipeline/final_state_scorer.py'

data = json.loads(CHECKLIST.read_text('utf-8'))
contracts = [json.loads(line) for line in SOURCE.read_text('utf-8-sig').splitlines() if line.strip()]
spec = importlib.util.spec_from_file_location('audit_existing_scorer', SCORER)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
inventory = {
    'task_count': len(contracts),
    'source_contract_first_shape': {
        'top_keys': list(contracts[0]),
        'first_delivery': contracts[0]['final_deliverables'][0],
        'first_check': contracts[0]['checks'][0],
    },
    'existing_validator_counts': dict(collections.Counter(p['validator'] for p in data['points'])),
    'existing_parameter_variants': {
        kind: list({json.dumps(p['parameters'], ensure_ascii=False, sort_keys=True): p['parameters']
                    for p in data['points'] if p['validator'] == kind}.values())
        for kind in sorted({p['validator'] for p in data['points']})
    },
    'coverage': module.coverage({c.get('sid', c.get('session_id')): c for c in contracts}),
    'pins': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [CHECKLIST, SOURCE, SCORER]},
    'business_runs': 0,
}
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'audit/source_inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), 'utf-8')
print(json.dumps({k: inventory[k] for k in ['task_count', 'source_contract_first_shape', 'existing_validator_counts']}, ensure_ascii=False))
print(json.dumps({'unsupported_existing_parameters': [r for r in inventory['coverage']['rows'] if r['unsupported_parameters']]}, ensure_ascii=False))
