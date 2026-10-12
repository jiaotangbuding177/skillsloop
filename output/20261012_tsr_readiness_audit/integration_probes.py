"""Native scorer CLI and evidence-production probes; no agent or external tools."""
from pathlib import Path
import copy
import importlib.util
import json
import os
import subprocess
import sys
from PIL import Image

OUT = Path(__file__).resolve().parent
SUITE = Path('D:/skillloop/benchmark/enterprise_input_closed_v11_20261012/evaluation/validator_suite')
sys.dont_write_bytecode = True
sys.path.insert(0, str(SUITE))
import _runtime as runtime


def read(path):
    return json.loads(Path(path).read_text('utf-8-sig'))


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', 'utf-8')


def main():
    m = read(SUITE / 'manifest.json')
    entries = {e['source_session_id']: e for e in m['tasks']}
    path = Path('D:/skillloop/research/pipelines/task_group_pipeline/final_state_evidence.py')
    spec = importlib.util.spec_from_file_location('tsr_evidence_integration', path)
    collector = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(collector)
    cli = []
    root = OUT / 'controls/native_entry_probes'
    root.mkdir(parents=True, exist_ok=True)
    for sid in ['conv_1484e8af3800', 'conv_e17789e7b661', 'conv_299aa1b64659']:
        c = read(SUITE / entries[sid]['contract'])
        work = root / sid / 'workspace'
        work.mkdir(parents=True, exist_ok=True)
        cases = [('claim_only', '已完成。')]
        if sid == 'conv_299aa1b64659':
            (work / 'outputs').mkdir(exist_ok=True)
            Image.new('RGB', (96, 64), '#ffffff').save(work / 'outputs/image.png')
            cases = [('actual_readable_new_image', '[下载图片](outputs/image.png)'), ('missing_image_only_link', '[下载图片](outputs/absent.png)')]
        for label, text in cases:
            result = {'answer': text, 'turn_answers': [text] * len(c['user_source_texts'])}
            ev = {'schema': 'final-state-evidence-v1', 'source_session_id': sid, 'workspace': str(work),
                'conversation_complete': True, 'initial_sha256': {}, 'declared_input_sha256': {},
                'deliveries': collector.bind_final_deliveries(work, c, result, [], {}),
                'measurement': {'namespace': 'final_state_measurement', 'status': 'collected', 'initial_snapshot_complete': True}}
            req = {'task_id': 'heldout_' + sid, 'source_session_id': sid, 'workspace': str(work), 'result': result, 'evidence': ev}
            req_path, response = root / sid / (label + '_request.json'), root / sid / (label + '_response.json')
            write(req_path, req)
            run = subprocess.run([sys.executable, str(SUITE / entries[sid]['script']), str(req_path), str(response)],
                capture_output=True, text=True, encoding='utf-8', env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, timeout=30)
            assert run.returncode == 0, run.stderr
            score = read(response)
            assert score['score'] == (0 if label == 'missing_image_only_link' else 1), score
            cli.append({'sid': sid, 'case': label, 'score': score['score'], 'task_status': score['task_success_status'],
                'request': str(req_path.relative_to(OUT)), 'response': str(response.relative_to(OUT)), 'exit_code': run.returncode})
    sid = 'conv_737c4b010b18'
    c = read(SUITE / entries[sid]['contract'])
    work, transport = OUT / 'controls/collector_manifest/workspace', OUT / 'controls/collector_manifest/transport'
    work.mkdir(parents=True, exist_ok=True)
    transport.mkdir(parents=True, exist_ok=True)
    Image.new('RGB', (160, 90), '#ffffff').save(work / 'actual_page.png')
    result = {'answer': '[图片](actual_page.png)', 'turn_answers': ['交付的逐页提示词', '交付的提示词', '交付的提示词', '[图片](actual_page.png)']}
    # Actual production collector with no services in this file/text-only contract.
    req = {'task_id': 'heldout_' + sid, 'source_session_id': sid, 'workspace': str(work), 'resources': [], 'followup_inputs': c['user_source_texts'][1:], 'result': result}
    evidence = collector.collect_final_evidence(work, transport, req, result=result, contract=c,
        initial_inventory={}, conversation_complete=True, events=[], env={}, state_dir=None)
    req['evidence'] = evidence
    scored = runtime.score_task_request(req, c)
    manifest_point = next(p for p in scored['checks'] if p['kind'] == 'manifest_corresponding_artifacts')
    assert 'manifest_snapshots' not in evidence and manifest_point['status'] == 'unknown'
    write(transport / 'actual_evidence.json', evidence)
    write(transport / 'actual_score.json', scored)
    record = {'schema': 'tsr-audit-native-integration-controls-v1', 'scorer_cli_controls': cli,
        'actual_collector_missing_manifest_probe': {'sid': sid, 'status': manifest_point['status'],
            'reason': manifest_point['reason'], 'manifest_snapshots_present': False,
            'scope': 'Collector does not automatically produce the new manifest fields; this is an offline constructed output.'},
        'business_runs': 0, 'external_services': 0, 'model_calls': 0}
    write(OUT / 'integration_probes.json', record)
    print(json.dumps(record, ensure_ascii=False))


if __name__ == '__main__':
    main()
