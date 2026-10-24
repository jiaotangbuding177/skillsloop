import argparse
import hashlib
import json
import re
import shutil
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


BASE = Path(__file__).resolve().parents[1]
SOURCE = Path('D:/skillloop')
STANDARD = SOURCE / 'output/20261025_modified28_evaluation_standard/release'
MAX_RAW_ARCHIVE_BYTES = 48 * 1024 * 1024
ROOT_LOG_NAMES = [
    'request.json', 'response.json', 'result.json', 'usage.json', 'native_events.jsonl',
    'execution.json', 'delivery_inspection.json', 'delivery_receipt.json',
    'attempt_receipt.json', 'delivery_score.json', 'native_skill_read_evidence.json',
    'stderr.log', 'stdout.log',
]
TRANSPORT_NAMES = [
    'session_events.jsonl', 'response.json', 'native_result.json', 'episode_turns.json',
    'skill_reads.json', 'runtime_observation.json', 'container_receipt.json',
    'host_receipt.json', 'native_skill_read_evidence.json',
]
TEXT_SUFFIXES = {'.json', '.jsonl', '.md', '.txt', '.log', '.csv', '.tsv', '.html', '.xml', '.yaml', '.yml', '.py', '.js', '.mjs', '.css', '.svg', '.ics', '.eml'}
SECRET_PATTERNS = [
    ('credential_field', re.compile(r'''(?i)(["']?(?:api[_-]?key|access[_-]?token|refresh[_-]?token|client[_-]?secret|secret[_-]?key|password)["']?\s*[:=]\s*["'])([^"'\r\n]{6,})(["'])'''), 2),
    ('authorization_bearer', re.compile(r'(?i)(\bBearer\s+)([A-Za-z0-9._~+/=-]{12,})'), 2),
    ('github_token', re.compile(r'\b(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,})\b'), 0),
    ('service_key', re.compile(r'\bsk-[A-Za-z0-9_-]{24,}\b'), 0),
    ('private_key', re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----', re.DOTALL), 0),
    ('url_password', re.compile(r'(https?://[^\s/:@]+:)([^\s/@]+)(@)'), 2),
]
SIMULATED_CREDENTIAL_VALUES = set()


def sha_bytes(content):
    return hashlib.sha256(content).hexdigest()


def sha_file(path):
    checksum = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            checksum.update(block)
    return checksum.hexdigest()


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def save_lines(path, values):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(json.dumps(value, ensure_ascii=False) + '\n' for value in values), encoding='utf-8')


def sanitize_text(content):
    changes = Counter()
    for label, pattern, group in SECRET_PATTERNS:
        def substitute(match):
            if label == 'credential_field' and match.group(group) in SIMULATED_CREDENTIAL_VALUES:
                return match.group(0)
            changes[label] += 1
            if group == 0:
                return '[REDACTED_CREDENTIAL]'
            return match.group(0)[:match.start(group) - match.start()] + '[REDACTED_CREDENTIAL]' + match.group(0)[match.end(group) - match.start():]
        content = pattern.sub(substitute, content)
    return content, dict(changes)


def publish_content(source_path):
    content = source_path.read_bytes()
    original_hash = sha_bytes(content)
    changes = {}
    if source_path.suffix.lower() in TEXT_SUFFIXES:
        try:
            decoded = content.decode('utf-8-sig')
        except UnicodeDecodeError:
            decoded = None
        if decoded is not None:
            sanitized, changes = sanitize_text(decoded)
            if changes:
                content = sanitized.encode('utf-8')
    return content, original_hash, changes


def episode_path(row):
    record = row['record']
    return Path(record.get('episode_dir') or record.get('attempt_ref'))


def evidence_files(episode):
    entries = {}
    def add(source_path, relative_path):
        if source_path.is_file() and not source_path.is_symlink():
            entries[relative_path] = source_path
    for name in ROOT_LOG_NAMES:
        add(episode / name, 'logs/' + name)
    transport = episode / 'openclaw_transport'
    for name in TRANSPORT_NAMES:
        add(transport / name, 'logs/openclaw_transport/' + name)
    for pattern in ['turn_*.native_result.json', 'turn_*.stdout.log', 'turn_*.stderr.log']:
        for source_path in transport.glob(pattern):
            add(source_path, 'logs/openclaw_transport/' + source_path.name)
    for source_root, destination in [
        (episode / 'workspace/outputs', 'outputs'),
        (episode / 'delivery_texts', 'delivery_texts'),
        (transport / 'evidence', 'logs/openclaw_transport/evidence'),
    ]:
        if source_root.is_dir():
            for source_path in source_root.rglob('*'):
                if source_path.is_file():
                    add(source_path, destination + '/' + source_path.relative_to(source_root).as_posix())
    return sorted(entries.items())


def copy_resource(source_path, destination, provenance, kind):
    content, original_hash, changes = publish_content(source_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    provenance.append({'package_path': destination.relative_to(BASE).as_posix(), 'source_path': str(source_path), 'source_sha256': original_hash, 'published_sha256': sha_bytes(content), 'bytes': len(content), 'redactions': changes, 'kind': kind})


def historical_rows(selected):
    candidates = []
    for row in selected:
        previous = row.get('previous_attempt')
        if isinstance(previous, dict) and previous.get('episode_dir'):
            candidates.append((row['task_id'], row['arm'], previous, 'WRAPPER_PREVIOUS_ATTEMPT'))
    selected_keys = {(row['task_id'], row['arm']) for row in selected}
    for filename in [
        SOURCE / 'output/20261024_wrd250_library_run/actor_results.json',
        SOURCE / 'output/20261025_wrd9_retry/actor_results.json',
        SOURCE / 'output/20261025_T0197_retry2/previous_attempt.json',
    ]:
        if filename.is_file():
            rows = read_json(filename)
            if isinstance(rows, dict):
                rows = [rows]
            for record in rows:
                task_id = record.get('task_id')
                arm = record.get('arm')
                if (task_id, arm) in selected_keys:
                    candidates.append((task_id, arm, record, str(filename)))
    selected_paths = {str(episode_path(row)).lower() for row in selected}
    seen = set()
    result = []
    for task_id, arm, record, origin in candidates:
        directory = record.get('episode_dir') or record.get('attempt_ref')
        if not directory or directory.lower() in selected_paths or directory.lower() in seen:
            continue
        seen.add(directory.lower())
        result.append({'task_id': task_id, 'arm': arm, 'record': record, 'source': origin, 'history_only_not_scoring_queue': True})
    return result


def build():
    selected_file = BASE / 'COORDINATOR/selected_runs.jsonl'
    selected = [json.loads(line) for line in selected_file.read_text(encoding='utf-8').splitlines()]
    assert len(selected) == 355 and len({(row['task_id'], row['arm']) for row in selected}) == 355
    assert Counter(row['arm'] for row in selected) == {'autoskill': 28, 'trace2skill': 28, 'no_skill': 49, 'workflow': 250}
    scope = read_json(BASE / 'COORDINATOR/scope.json')
    modified = set(scope['modified_task_ids'])
    registry_path = SOURCE / 'output/20261024_experiment_adopt35/current_tasks250.json'
    registry = read_json(registry_path)
    task_map = {entry['task_id']: entry for entry in registry}
    simulation_task = task_map['T0039']
    assert '不把测试标记字符串当成有效账号' in simulation_task['task']['prompt']
    for source in simulation_task['task']['inputs']:
        actual = Path(simulation_task['input_root']) / source['path']
        if actual.suffix.lower() in TEXT_SUFFIXES:
            for match in SECRET_PATTERNS[0][1].finditer(actual.read_text(encoding='utf-8-sig')):
                SIMULATED_CREDENTIAL_VALUES.add(match.group(2))
    provenance = []
    for entry in registry:
        task_id = entry['task_id']
        task_destination = BASE / 'DATA/tasks' / task_id
        save_json(task_destination / 'task.json', entry['task'])
        for source in entry['task']['inputs']:
            actual = Path(entry['input_root']) / source['path']
            assert sha_file(actual) == source['sha256'] and actual.stat().st_size == source['bytes']
            copy_resource(actual, task_destination / source['name'], provenance, 'CURRENT_TASK_INPUT')
    rubric_rows = [json.loads(line) for line in (STANDARD / 'rubrics250.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rubric_rows) == 250
    for rubric in rubric_rows:
        assert rubric['prompt'] == task_map[rubric['task_id']]['task']['prompt']
        save_json(BASE / 'RUBRICS/tasks' / (rubric['task_id'] + '.json'), rubric)
    for name in ['rubrics250.jsonl', 'rubrics_modified28.jsonl', 'scoring_policy.json', 'rubric_modified28.schema.json', 'schema_validation.json', 'independent_review.json', 'self_reviews28.jsonl', 'final_verification.json']:
        copy_resource(STANDARD / name, BASE / 'RUBRICS' / name, provenance, 'QUALITY_STANDARD_SOURCE')
    copy_resource(SOURCE / 'output/20261017_eval250_quality_review/review_release.schema.json', BASE / 'RUBRICS/rubric_inherited222.schema.json', provenance, 'INHERITED_SCHEMA')
    copy_resource(SOURCE / 'output/20261024_rescan29/250题增量匹配扫描.json', BASE / 'COORDINATOR/strong_match_source.json', provenance, 'COHORT_SELECTION_PROVENANCE')
    history = historical_rows(selected)
    save_lines(BASE / 'COORDINATOR/historical_attempts.jsonl', history)
    ordered = sorted(selected, key=lambda row: (row['task_id'] not in modified, row['task_id'], hashlib.sha256((row['task_id'] + '|' + row['arm'] + '|q-review-20261025').encode()).hexdigest()))
    jobs = []
    case_key = []
    for number, row in enumerate(ordered, 1):
        case_id = 'CASE-' + str(number).zfill(4)
        jobs.append({'case_id': case_id, 'row': row, 'history': False})
        case_key.append({'case_id': case_id, 'task_id': row['task_id'], 'arm': row['arm'], 'episode_source': str(episode_path(row)), 'record_version': row.get('record_version'), 'source': row.get('source'), 'source_sha256': row.get('source_sha256'), 'current_task_aligned': True, 'modified_task': row['task_id'] in modified})
    for number, row in enumerate(history, 1):
        jobs.append({'case_id': 'HISTORY-' + str(number).zfill(4), 'row': row, 'history': True})
    evidence_root = BASE / 'EVIDENCE'
    evidence_root.mkdir(parents=True, exist_ok=True)
    if list(evidence_root.glob('evidence-*.zip')):
        raise RuntimeError('Evidence archives already exist; preserve prior build and use an explicit new output directory')
    archive_number = 0
    archive = None
    raw_bytes = 0
    queue = []
    run_manifests = []
    all_redactions = []
    for job in jobs:
        row = job['row']
        case_id = job['case_id']
        episode = episode_path(row)
        assert episode.is_dir(), str(episode)
        files = evidence_files(episode)
        assert (episode / 'request.json').is_file() and files
        total_bytes = sum(source.stat().st_size for _, source in files)
        if archive is None or raw_bytes + total_bytes > MAX_RAW_ARCHIVE_BYTES:
            if archive is not None:
                archive.close()
            archive_number += 1
            archive_path = evidence_root / ('evidence-' + str(archive_number).zfill(3) + '.zip')
            archive = zipfile.ZipFile(archive_path, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6)
            raw_bytes = 0
        archive_relative = archive_path.relative_to(BASE).as_posix()
        prefix = 'runs/' + case_id
        file_records = []
        for relative, source_path in files:
            content, original_hash, changes = publish_content(source_path)
            member = prefix + '/' + relative
            archive.writestr(member, content)
            record = {'path': relative, 'bytes': len(content), 'sha256': sha_bytes(content), 'redacted': bool(changes)}
            file_records.append(record)
            provenance.append({'archive': archive_relative, 'member': member, 'source_path': str(source_path), 'source_sha256': original_hash, 'published_sha256': record['sha256'], 'bytes': len(content), 'redactions': changes, 'kind': 'HISTORICAL_ATTEMPT' if job['history'] else 'SELECTED_RUN_EVIDENCE'})
            if changes:
                all_redactions.append({'archive': archive_relative, 'member': member, 'categories': changes, 'source_sha256': original_hash})
        manifest = {'case_id': case_id, 'task_id': row['task_id'], 'required_artifact_roles': task_map[row['task_id']]['task']['deliverables'], 'files': file_records, 'redaction_rule': 'ORIGINAL_BYTES_RETAINED_UNLESS_CREDENTIAL_REDACTED_WITH_PROVENANCE', 'history_only_not_scoring_queue': job['history']}
        archive.writestr(prefix + '/run_manifest.json', json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
        run_manifests.append({'case_id': case_id, 'task_id': row['task_id'], 'evidence_archive': archive_relative, 'evidence_prefix': prefix, 'files': len(file_records), 'bytes': sum(value['bytes'] for value in file_records), 'history_only': job['history']})
        raw_bytes += total_bytes
        if not job['history']:
            queue.append({'case_id': case_id, 'task_id': row['task_id'], 'task_ref': 'DATA/tasks/' + row['task_id'] + '/task.json', 'rubric_ref': 'RUBRICS/tasks/' + row['task_id'] + '.json', 'evidence_archive': archive_relative, 'evidence_prefix': prefix, 'priority': 0 if row['task_id'] in modified else 1, 'score_status': 'NOT_SCORED'})
    if archive is not None:
        archive.close()
    assert len(queue) == 355
    save_lines(BASE / 'JUDGE/queue.jsonl', queue)
    save_lines(BASE / 'COORDINATOR/case_key.jsonl', case_key)
    save_lines(BASE / 'COORDINATOR/run_evidence_inventory.jsonl', run_manifests)
    save_lines(BASE / 'COORDINATOR/file_provenance.jsonl', provenance)
    save_json(BASE / 'COORDINATOR/redaction_report.json', {'status': 'CREDENTIAL_SCAN_COMPLETED', 'redacted_files': len(all_redactions), 'files': all_redactions, 'synthetic_placeholder_exception': {'task_id': 'T0039', 'unique_source_values': len(SIMULATED_CREDENTIAL_VALUES), 'basis': 'Task explicitly identifies its supplied fault-log password as a test placeholder, not a valid account. Matched source placeholder evidence is preserved; values are not printed in this report.'}, 'excluded_by_design': ['environment/config/account/credential files', 'runtime_code', 'host_api_queue raw network requests', 'workspace skills and learned_skills', 'private directories'], 'original_files_modified': False})
    save_json(BASE / 'MANIFEST/build_summary.json', {
        'snapshot_Asia_Shanghai': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'status': 'EVIDENCE_PACKAGED_NOT_QUALITY_SCORED',
        'selected_runs': len(selected), 'cohort_counts': dict(Counter(row['arm'] for row in selected)),
        'priority_modified_cases': sum(value['priority'] == 0 for value in queue),
        'current_tasks': len(registry), 'current_input_bindings': sum(len(entry['task']['inputs']) for entry in registry),
        'rubric_tasks': len(rubric_rows), 'rubric_items': sum(len(row['items']) for row in rubric_rows),
        'history_attempts': len(history), 'evidence_archives': archive_number,
        'evidence_file_bindings': sum(value['files'] for value in run_manifests),
        'evidence_raw_bytes': sum(value['bytes'] for value in run_manifests),
        'evidence_archive_bytes': sum(path.stat().st_size for path in evidence_root.glob('evidence-*.zip')),
        'redacted_files': len(all_redactions), 'tsr_name_policy': 'type_count_nonzero_format_open',
        'new_actor_or_judge_calls': 0, 'q_scores_present': False,
        'source_registry_sha256': sha_file(registry_path), 'selected_runs_sha256': sha_file(selected_file),
        'builder_sha256': sha_file(Path(__file__)),
    })
    print(json.dumps(read_json(BASE / 'MANIFEST/build_summary.json'), ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', action='store_true', required=True)
    parser.parse_args()
    build()
