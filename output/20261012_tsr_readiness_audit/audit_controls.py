"""Read-only audit of the frozen validator suite using offline constructed results."""
from pathlib import Path
import collections
import copy
import hashlib
import importlib.util
import json
import sys

OUT = Path(__file__).resolve().parent
BENCH = Path('D:/skillloop/benchmark/enterprise_input_closed_v11_20261012')
SUITE = BENCH / 'evaluation/validator_suite'
sys.dont_write_bytecode = True
sys.path.insert(0, str(SUITE))
import _runtime as runtime
from summarize_scores import summarize


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf-8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    manifest = read(SUITE / 'manifest.json')
    contracts = [read(SUITE / entry['contract']) for entry in manifest['tasks']]
    original_pins = {str(path): sha(path) for path in [BENCH / 'release_freeze_v11.json', BENCH / 'release_manifest_v11.jsonl',
        SUITE / 'manifest.json', *(SUITE / name for name in manifest['implementation_sha256'])]}
    engine = runtime.load_engine()
    collector_path = Path('D:/skillloop/research/pipelines/task_group_pipeline/final_state_evidence.py')
    spec = importlib.util.spec_from_file_location('tsr_audit_collector', collector_path)
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    workspace = OUT / 'controls/empty_attempt_workspace'
    workspace.mkdir(parents=True, exist_ok=True)
    nonempty = {'delivered_body_nonempty', 'text_body_nonempty', 'delivered_text_nonempty', 'delivered_text_or_file_nonempty'}
    structure = {'tasks': len(contracts), 'checks': sum(len(c['checks']) for c in contracts),
        'mandatory': sum(p.get('mandatory', True) for c in contracts for p in c['checks']),
        'observations': sum(not p.get('mandatory', True) for c in contracts for p in c['checks']),
        'nonempty_checkpoints': sum(p['kind'] in nonempty for c in contracts for p in c['checks']),
        'no_required_checks': [], 'delivery_without_required_check': [], 'missing_five_fields': [],
        'unsupported_checks': [], 'bad_pins': [], 'policy_violations': []}
    for entry, contract in zip(manifest['tasks'], contracts):
        if sha(SUITE / entry['contract']) != entry['contract_sha256'] or sha(SUITE / entry['script']) != entry['script_sha256']:
            structure['bad_pins'].append(contract['sid'])
        if not all(contract.get(flag) is False for flag in runtime.POLICY_FLAGS) or contract.get('score_at') != 'conversation_end_only':
            structure['policy_violations'].append(contract['sid'])
        mandatory = [p for p in contract['checks'] if p.get('mandatory', True)]
        if not mandatory:
            structure['no_required_checks'].append(contract['sid'])
        for target in contract['final_deliverables']:
            if not any(p['delivery_id'] == target['id'] for p in mandatory):
                structure['delivery_without_required_check'].append({'session_id': contract['sid'], 'delivery_id': target['id'], 'name': target['name']})
        for point in contract['checks']:
            missing = [key for key in ('display_object', 'passing_condition', 'evidence_method', 'requirement_basis', 'parameters') if key not in point]
            if missing:
                structure['missing_five_fields'].append({'session_id': contract['sid'], 'point_id': point['point_id'], 'missing': missing})
            unsupported = engine.parameter_support(point)
            if point['kind'] not in engine.HANDLERS or unsupported:
                structure['unsupported_checks'].append({'session_id': contract['sid'], 'point_id': point['point_id'], 'parameters': unsupported})
    assert all(sha(SUITE / relative) == expected for relative, expected in manifest['implementation_sha256'].items())
    claim_only = []
    empty_body = []
    blank_outputs = []
    for contract in contracts:
        turn_count = len(contract['user_source_texts'])
        for case, text in [('claim_only', '已完成。'), ('empty_body', ' \n\t')]:
            result = {'answer': text, 'turn_answers': [text] * turn_count}
            bindings = collector.bind_final_deliveries(workspace, contract, result, [], {})
            evidence = {'schema': 'final-state-evidence-v1', 'source_session_id': contract['sid'],
                'workspace': str(workspace), 'conversation_complete': True, 'initial_sha256': {},
                'declared_input_sha256': {}, 'deliveries': bindings,
                'measurement': {'namespace': 'final_state_measurement', 'status': 'collected', 'initial_snapshot_complete': True}}
            request = {'source_session_id': contract['sid'], 'task_id': 'heldout_' + contract['sid'],
                'workspace': str(workspace), 'result': result, 'evidence': evidence}
            scored = runtime.score_task_request(request, contract)
            item = {'session_id': contract['sid'], 'title': contract['title'], 'category': contract['category_name'],
                'case': case, 'all_required_only_nonempty': all(p['kind'] in nonempty for p in contract['checks'] if p.get('mandatory', True)),
                'task_success_status': scored['task_success_status'], 'score': scored['score'],
                'counts': scored['counts'], 'checks': [{k:p.get(k) for k in ('point_id', 'kind', 'mandatory', 'status', 'reason')} for p in scored['checks']],
                'actual_collector_bindings': bindings}
            (claim_only if case == 'claim_only' else empty_body).append(item)
            if case == 'claim_only' and item['all_required_only_nonempty']:
                write(OUT / 'controls/claim_only_actual_scores' / (contract['sid'] + '.json'), scored)
            if case == 'empty_body':
                blank_outputs.append(scored)
    only_tasks = [c for c in contracts if all(p['kind'] in nonempty for p in c['checks'] if p.get('mandatory', True))]
    summary_controls = []
    response_root = OUT / 'controls/summary_responses'
    response_root.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, entry in enumerate(manifest['tasks']):
        status = 'PASS' if i % 2 == 0 else 'FAIL'
        path = response_root / (entry['source_session_id'] + '.json')
        write(path, {'source_session_id': entry['source_session_id'], 'score_at': 'conversation_end_only',
            'quality_scored': False, 'valid': True, 'score': int(status == 'PASS'), 'task_success_status': status})
        paths.append(path)
    complete = summarize(paths, manifest)
    assert complete['fixed_tasks'] == 226 and complete['official_task_success_rate'] == 113 / 226
    summary_controls.append({'case': '226_complete_binary_synthetic_results', 'passed': True, 'official_micro': complete['official_task_success_rate'], 'fixed_N': 226})
    missing = summarize(paths[:-1], manifest)
    assert missing['fixed_tasks'] == 226 and missing['official_task_success_rate'] is None and missing['missing'] == 1
    summary_controls.append({'case': 'one_missing_no_denominator_shrink', 'passed': True, 'fixed_N': 226, 'official_TSR': None})
    unknown_path = response_root / 'unscored_override.json'
    write(unknown_path, {'source_session_id': manifest['tasks'][0]['source_session_id'], 'score_at': 'conversation_end_only',
        'quality_scored': False, 'valid': False, 'score': None, 'task_success_status': 'UNSCORED'})
    unknown = summarize([unknown_path, *paths[1:]], manifest)
    assert unknown['fixed_tasks'] == 226 and unknown['official_task_success_rate'] is None and unknown['unscored'] == 1
    summary_controls.append({'case': 'one_UNSCORED_no_official_TSR', 'passed': True, 'fixed_N': 226, 'official_TSR': None})
    try:
        summarize([*paths, paths[0]], manifest)
    except ValueError as exc:
        assert 'duplicate_source_in_one_attempt' in str(exc)
        summary_controls.append({'case': 'duplicate_source_rejected', 'passed': True})
    else:
        raise AssertionError('duplicate source accepted')
    coexist = [v for v in blank_outputs if any(p['mandatory'] and p['status'] == 'fail' for p in v['checks'])
        and any(p['mandatory'] and p['status'] == 'unknown' for p in v['checks'])]
    write(OUT / 'controls/fail_plus_unknown_actual_tasks.json', coexist)
    only_reproduced = [v for v in claim_only if v['all_required_only_nonempty'] and v['score'] == 1]
    invariance = {path: sha(path) == expected for path, expected in original_pins.items()}
    assert all(invariance.values())
    report = {'schema': 'tsr-readiness-audit-offline-controls-v1', 'scope': 'Constructed artifacts/results only; not business task success rates.',
        'structure': structure, 'only_nonempty_tasks': len(only_tasks),
        'only_nonempty_task_categories': dict(collections.Counter(c['category_name'] for c in only_tasks)),
        'claim_only_actual_collector_probes': len(claim_only), 'empty_actual_collector_probes': len(empty_body),
        'claim_only_task_pass_count': sum(v['score'] == 1 for v in claim_only),
        'only_nonempty_claim_false_positive_count': len(only_reproduced),
        'empty_text_pass_count': sum(v['score'] == 1 for v in empty_body),
        'fail_plus_unknown_task_count': len(coexist), 'summary_controls': summary_controls,
        'suite_and_release_pins_unchanged': invariance, 'collector_sha256': sha(collector_path),
        'business_runs': 0, 'model_calls': 0}
    write(OUT / 'claim_only_probes.json', claim_only)
    write(OUT / 'empty_delivery_probes.json', empty_body)
    write(OUT / 'audit_controls.json', report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('suite_and_release_pins_unchanged',)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
