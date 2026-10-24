import argparse
import hashlib
import json
import re
import stat
import sys
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath


BASE = Path(__file__).resolve().parents[1]
SEAL_PATH = 'MANIFEST/file_sha256.jsonl'
REPORT_PATH = 'MANIFEST/verification.json'
DIMENSION_WEIGHTS = {'D1': 0.30, 'D2': 0.20, 'D3': 0.20, 'D4': 0.20, 'D5': 0.10}
HASH_PATTERN = re.compile(r'^[0-9a-f]{64}$')
LFS_HEADER = b'version https://git-lfs.github.com/spec/v1'


class VerificationError(Exception):
    pass


def require(condition, code):
    if not condition:
        raise VerificationError(code)


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def read_json_lines(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def relative_parts(value):
    require(isinstance(value, str) and bool(value), 'EMPTY_OR_INVALID_RELATIVE_PATH')
    require('\\' not in value and '\x00' not in value, 'UNSAFE_RELATIVE_PATH')
    require(not value.startswith('/') and not PureWindowsPath(value).drive, 'ABSOLUTE_PATH_IN_PACKAGE_REFERENCE')
    parts = PurePosixPath(value).parts
    require(bool(parts) and all(part not in ('', '.', '..') for part in parts), 'UNSAFE_RELATIVE_PATH')
    require(PurePosixPath(value).as_posix() == value.rstrip('/'), 'NONCANONICAL_RELATIVE_PATH')
    return parts


def package_path(value):
    parts = relative_parts(value)
    candidate = BASE.joinpath(*parts)
    try:
        candidate.resolve().relative_to(BASE.resolve())
    except ValueError:
        raise VerificationError('PACKAGE_REFERENCE_ESCAPES_HANDOFF')
    require(not candidate.is_symlink(), 'SYMLINK_PACKAGE_REFERENCE')
    return candidate


def required_file(value):
    candidate = package_path(value)
    require(candidate.is_file(), 'PACKAGE_REFERENCE_NOT_FOUND')
    return candidate


def sha_stream(handle):
    checksum = hashlib.sha256()
    byte_count = 0
    for block in iter(lambda: handle.read(1024 * 1024), b''):
        byte_count += len(block)
        checksum.update(block)
    return checksum.hexdigest(), byte_count


def sha_file(path):
    before = path.stat()
    with path.open('rb') as handle:
        checksum, byte_count = sha_stream(handle)
    after = path.stat()
    require(before.st_size == after.st_size == byte_count and before.st_mtime_ns == after.st_mtime_ns, 'FILE_CHANGED_DURING_VERIFICATION')
    return checksum, byte_count


def inventory_paths():
    paths = []
    for candidate in BASE.rglob('*'):
        if not candidate.is_file():
            continue
        relative = candidate.relative_to(BASE).as_posix()
        if relative in (SEAL_PATH, REPORT_PATH):
            continue
        if '__pycache__' in candidate.relative_to(BASE).parts or candidate.suffix.lower() in ('.pyc', '.pyo'):
            continue
        require(not candidate.is_symlink(), 'SYMLINK_IN_PACKAGE_INVENTORY')
        paths.append(relative)
    return sorted(paths)


def validate_structure():
    summary = read_json(required_file('MANIFEST/build_summary.json'))
    require(summary['selected_runs'] == 355 and summary['current_tasks'] == 250, 'BUILD_RUN_OR_TASK_COUNTS_INVALID')
    require(summary['rubric_tasks'] == 250 and summary['rubric_items'] == 2631, 'BUILD_RUBRIC_COUNTS_INVALID')
    require(summary['q_scores_present'] is False, 'BUILD_UNEXPECTED_QUALITY_SCORES')
    queue = read_json_lines(required_file('JUDGE/queue.jsonl'))
    rubric_rows = read_json_lines(required_file('RUBRICS/rubrics250.jsonl'))
    require(len(queue) == 355, 'QUEUE_CASE_COUNT_INVALID')
    require(len({entry['case_id'] for entry in queue}) == 355, 'QUEUE_CASE_IDS_NOT_UNIQUE')
    require(len(rubric_rows) == 250 and len({row['task_id'] for row in rubric_rows}) == 250, 'RUBRIC_TASK_IDS_INVALID')
    rubric_map = {row['task_id']: row for row in rubric_rows}
    require(set(rubric_map) == {'T' + str(number).zfill(4) for number in range(1, 251)}, 'EXPECTED_TASK_ID_SET_INVALID')
    require({entry['task_id'] for entry in queue} == set(rubric_map), 'QUEUE_AND_RUBRIC_TASK_COVERAGE_DIFFER')
    item_ids = set()
    item_count = 0
    for rubric in rubric_rows:
        task_id = rubric['task_id']
        require(rubric['dimension_weights'] == DIMENSION_WEIGHTS, 'RUBRIC_DIMENSION_WEIGHTS_INVALID')
        dimensions = Counter()
        for item in rubric['items']:
            item_id = item['item_id']
            require(item_id not in item_ids and item_id.startswith(task_id + '-'), 'RUBRIC_ITEM_IDS_INVALID')
            item_ids.add(item_id)
            item_count += 1
            dimensions[item['dimension']] += 1
            require(item['dimension'] in DIMENSION_WEIGHTS and item['weight'] == 1, 'RUBRIC_ITEM_DIMENSION_OR_WEIGHT_INVALID')
            require(item.get('score', 'MISSING') is None, 'RUBRIC_ITEM_ALREADY_SCORED')
            require(set(item['anchors']) == {'0', '0.5', '1'}, 'RUBRIC_ITEM_ANCHORS_INVALID')
            require(all(isinstance(value, str) and bool(value.strip()) for value in item['anchors'].values()), 'RUBRIC_ITEM_ANCHOR_TEXT_INVALID')
            for source in item['sources']:
                if source['source'] != 'prompt':
                    required_file('DATA/tasks/' + task_id + '/' + source['source'])
        require(set(dimensions) == set(DIMENSION_WEIGHTS), 'RUBRIC_FIVE_DIMENSIONS_NOT_PRESENT')
        task_ref = 'DATA/tasks/' + task_id + '/task.json'
        task = read_json(required_file(task_ref))
        require(task['task_id'] == task_id and task['prompt'] == rubric['prompt'], 'TASK_AND_RUBRIC_PROMPT_DIFFER')
        task_directory = PurePosixPath(task_ref).parent
        input_names = set()
        for source in task['inputs']:
            relative_parts(source['name'])
            require(source['name'] not in input_names, 'TASK_INPUT_NAMES_NOT_UNIQUE')
            input_names.add(source['name'])
            required_file((task_directory / source['name']).as_posix())
        require(read_json(required_file('RUBRICS/tasks/' + task_id + '.json')) == rubric, 'PER_TASK_RUBRIC_AND_AGGREGATE_DIFFER')
    require(item_count == 2631, 'RUBRIC_ITEM_COUNT_INVALID')
    expected_task_files = {package_path('DATA/tasks/' + task_id + '/task.json').resolve() for task_id in rubric_map}
    actual_task_files = {path.resolve() for path in package_path('DATA/tasks').glob('*/task.json')}
    require(expected_task_files == actual_task_files, 'TASK_DIRECTORY_COVERAGE_INVALID')
    required_archive_paths = set()
    expected_prefixes = {}
    for entry in queue:
        require(entry['score_status'] == 'NOT_SCORED', 'QUEUE_ALREADY_SCORED')
        task = read_json(required_file(entry['task_ref']))
        rubric = read_json(required_file(entry['rubric_ref']))
        require(task['task_id'] == rubric['task_id'] == entry['task_id'], 'QUEUE_RELATIVE_REFERENCE_TASK_MISMATCH')
        archive_path = required_file(entry['evidence_archive'])
        require(archive_path.suffix.lower() == '.zip', 'QUEUE_ARCHIVE_REFERENCE_INVALID')
        require(entry['evidence_prefix'] == 'runs/' + entry['case_id'], 'QUEUE_EVIDENCE_PREFIX_INVALID')
        relative_parts(entry['evidence_prefix'])
        required_archive_paths.add(entry['evidence_archive'])
        expected_prefixes[entry['case_id']] = (entry['evidence_archive'], entry['evidence_prefix'], entry['task_id'])
    actual_archives = {path.relative_to(BASE).as_posix() for path in package_path('EVIDENCE').glob('evidence-*.zip') if path.is_file()}
    require(required_archive_paths <= actual_archives, 'QUEUE_ARCHIVE_NOT_FOUND')
    require(len(actual_archives) == summary['evidence_archives'], 'EVIDENCE_ARCHIVE_COUNT_INVALID')
    return summary, expected_prefixes, set(rubric_map), sorted(actual_archives)


def write_seal():
    records = []
    for relative in inventory_paths():
        checksum, byte_count = sha_file(required_file(relative))
        records.append({'path': relative, 'sha256': checksum, 'bytes': byte_count})
    destination = package_path(SEAL_PATH)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(''.join(json.dumps(record, ensure_ascii=False) + '\n' for record in records), encoding='utf-8')
    return records


def validate_seal():
    require(package_path(SEAL_PATH).is_file(), 'PACKAGE_SEAL_MISSING_RUN_COORDINATOR_SEAL')
    records = read_json_lines(required_file(SEAL_PATH))
    require(bool(records) and len(records) == len({record['path'] for record in records}), 'SEAL_FILE_RECORDS_INVALID')
    require({record['path'] for record in records} == set(inventory_paths()), 'SEALED_AND_ACTUAL_FILE_INVENTORY_DIFFER')
    total_bytes = 0
    for record in records:
        require(isinstance(record.get('bytes'), int) and record['bytes'] >= 0, 'SEAL_BYTE_SIZE_INVALID')
        require(isinstance(record.get('sha256'), str) and HASH_PATTERN.fullmatch(record['sha256']), 'SEAL_SHA256_INVALID')
        path = required_file(record['path'])
        if path.stat().st_size < 1024:
            with path.open('rb') as handle:
                require(not handle.read(len(LFS_HEADER)).startswith(LFS_HEADER), 'GIT_LFS_OBJECT_NOT_DOWNLOADED')
        checksum, byte_count = sha_file(path)
        require(checksum == record['sha256'] and byte_count == record['bytes'], 'SEALED_FILE_HASH_OR_SIZE_MISMATCH')
        total_bytes += byte_count
    return len(records), total_bytes


def validate_archives(summary, queue_prefixes, task_ids, archive_paths):
    seen_cases = set()
    selected_cases = set()
    history_count = 0
    member_count = 0
    member_bytes = 0
    for archive_relative in archive_paths:
        archive_path = required_file(archive_relative)
        with zipfile.ZipFile(archive_path) as archive:
            infos = archive.infolist()
            names = [info.filename for info in infos]
            require(len(names) == len(set(names)), 'DUPLICATE_ZIP_MEMBERS')
            require(all(not info.is_dir() for info in infos), 'UNEXPECTED_ZIP_DIRECTORY_ENTRY')
            for info in infos:
                relative_parts(info.filename)
                require(not stat.S_ISLNK(info.external_attr >> 16), 'SYMLINK_ZIP_MEMBER')
            manifest_names = [name for name in names if len(PurePosixPath(name).parts) == 3 and PurePosixPath(name).parts[0] == 'runs' and PurePosixPath(name).name == 'run_manifest.json']
            require(bool(manifest_names), 'ARCHIVE_HAS_NO_RUN_MANIFEST')
            described_members = set(manifest_names)
            for manifest_name in manifest_names:
                manifest = json.loads(archive.read(manifest_name).decode('utf-8-sig'))
                case_id = manifest['case_id']
                prefix = 'runs/' + case_id
                require(manifest_name == prefix + '/run_manifest.json', 'RUN_MANIFEST_CASE_PREFIX_MISMATCH')
                require(case_id not in seen_cases, 'RUN_MANIFEST_CASE_DUPLICATED')
                seen_cases.add(case_id)
                require(manifest['task_id'] in task_ids, 'RUN_MANIFEST_UNKNOWN_TASK')
                history_only = manifest['history_only_not_scoring_queue']
                require(isinstance(history_only, bool), 'RUN_MANIFEST_HISTORY_FLAG_INVALID')
                if case_id in queue_prefixes:
                    require(not history_only, 'SELECTED_CASE_MARKED_AS_HISTORY')
                    require(queue_prefixes[case_id] == (archive_relative, prefix, manifest['task_id']), 'QUEUE_AND_ARCHIVE_RUN_BINDING_DIFFER')
                    selected_cases.add(case_id)
                else:
                    require(history_only and case_id.startswith('HISTORY-'), 'UNQUEUED_SELECTED_RUN_IN_ARCHIVE')
                    history_count += 1
                files = manifest['files']
                require(len(files) == len({record['path'] for record in files}), 'RUN_MANIFEST_MEMBER_PATHS_DUPLICATED')
                for record in files:
                    relative_parts(record['path'])
                    member = prefix + '/' + record['path']
                    require(member not in described_members, 'RUN_MANIFEST_MEMBER_DESCRIBED_MULTIPLE_TIMES')
                    require(member in names, 'RUN_MANIFEST_DESCRIBED_MEMBER_MISSING')
                    require(isinstance(record.get('bytes'), int) and record['bytes'] >= 0, 'RUN_MANIFEST_BYTE_SIZE_INVALID')
                    require(isinstance(record.get('sha256'), str) and HASH_PATTERN.fullmatch(record['sha256']), 'RUN_MANIFEST_MEMBER_HASH_INVALID')
                    with archive.open(member) as handle:
                        checksum, byte_count = sha_stream(handle)
                    require(checksum == record['sha256'] and byte_count == record['bytes'], 'ARCHIVE_MEMBER_HASH_OR_SIZE_MISMATCH')
                    require(archive.getinfo(member).file_size == byte_count, 'ZIP_MEMBER_DECLARED_SIZE_MISMATCH')
                    described_members.add(member)
                    member_count += 1
                    member_bytes += byte_count
            require(described_members == set(names), 'ARCHIVE_CONTAINS_UNMANIFESTED_MEMBERS')
    require(selected_cases == set(queue_prefixes) and len(selected_cases) == 355, 'DEEP_SELECTED_CASE_COVERAGE_INVALID')
    require(history_count == summary['history_attempts'], 'DEEP_HISTORY_CASE_COUNT_INVALID')
    require(member_count == summary['evidence_file_bindings'], 'DEEP_EVIDENCE_MEMBER_COUNT_INVALID')
    require(member_bytes == summary['evidence_raw_bytes'], 'DEEP_EVIDENCE_BYTE_COUNT_INVALID')
    return {'archives_verified': len(archive_paths), 'selected_run_manifests_verified': len(selected_cases), 'history_run_manifests_verified': history_count, 'archive_members_verified': member_count, 'archive_member_bytes_verified': member_bytes}


def main():
    parser = argparse.ArgumentParser(description='Verify portable Q handoff integrity without scoring or networking.')
    parser.add_argument('--seal', action='store_true', help='Coordinator only: write the complete package file hash inventory, then verify it.')
    parser.add_argument('--deep', action='store_true', help='Also verify every selected and historical ZIP member against its run manifest.')
    parser.add_argument('--write-report', action='store_true', help='Write MANIFEST/verification.json, which is excluded from the package seal.')
    arguments = parser.parse_args()
    report = {'verified_at_UTC': datetime.now(timezone.utc).isoformat(), 'status': 'FAIL', 'scoring_performed': False, 'network_access_performed': False, 'seal_written': False, 'deep_verification': arguments.deep}
    exit_code = 0
    try:
        summary, queue_prefixes, task_ids, archive_paths = validate_structure()
        if arguments.seal:
            write_seal()
            report['seal_written'] = True
        files_verified, bytes_verified = validate_seal()
        report.update({'status': 'PASS_INTEGRITY_ONLY_NOT_QUALITY_SCORE', 'selected_cases_verified': 355, 'current_tasks_verified': 250, 'rubric_items_verified': 2631, 'five_dimension_weights_verified': True, 'rubric_scores_all_null': True, 'relative_references_verified': True, 'sealed_files_verified': files_verified, 'sealed_bytes_verified': bytes_verified})
        if arguments.deep:
            report.update(validate_archives(summary, queue_prefixes, task_ids, archive_paths))
    except VerificationError as error:
        report['status'] = 'FAIL'
        report['error_code'] = str(error)
        exit_code = 1
    except Exception as error:
        report['status'] = 'FAIL'
        report['error_code'] = 'PACKAGE_READ_PARSE_OR_STRUCTURE_ERROR'
        report['error_type'] = type(error).__name__
        exit_code = 1
    if arguments.write_report:
        try:
            destination = package_path(REPORT_PATH)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        except Exception as error:
            report['status'] = 'FAIL'
            report['error_code'] = 'VERIFICATION_REPORT_WRITE_ERROR'
            report['error_type'] = type(error).__name__
            exit_code = 1
    print(json.dumps(report, ensure_ascii=False))
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
