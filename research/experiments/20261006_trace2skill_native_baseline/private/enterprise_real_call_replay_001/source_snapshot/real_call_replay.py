"""Replay three saved real calls through the unchanged native core, offline.

This reconstructs saved output from saved responses. It is not an independent
model sample, quality test, historical wrapper snapshot, or task-benefit result.
The current original SDK serializes each request into an in-memory MockTransport.
Its full JSON body and raw body SHA must match the saved request and old ledger.
The original raw body file was not saved; this verifies a reconstruction against
its retained digest rather than claiming the old wrapper source was preserved.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys
import threading
from types import SimpleNamespace
from unittest.mock import patch

from profiles import (BASELINE, BASELINE_COMMIT, HERE, PROJECT, generation_config_for,
                      load_profile, native_evolver_kwargs)

sys.path[:0] = [str(BASELINE/'.runtime/deps'), str(BASELINE), str(BASELINE/'src')]
sys.dont_write_bytecode = True
ANALYSIS = HERE/'private/enterprise_analysis_001'
EVOLUTION = HERE/'private/enterprise_evolution_001'
CHECKER_ROOT = PROJECT/'enginering/demo/.runtime/node_modules/openclaw'
CHECKER = CHECKER_ROOT/'skills/skill-creator/scripts/quick_validate.py'
LABEL = 'SAVED_REAL_RESPONSE_OFFLINE_REPLAY_NOT_A_NEW_MODEL_RESULT'


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'))


def sha(value):
    data = value.read_bytes() if isinstance(value, Path) else value.encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str)+'\n', encoding='utf-8')


def source_manifest():
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=BASELINE, text=True).strip()
    diff = subprocess.check_output(['git', 'diff', '--name-only'], cwd=BASELINE, text=True).strip()
    assert commit == BASELINE_COMMIT and not diff
    paths = subprocess.check_output(['git', 'ls-files'], cwd=BASELINE, text=True).splitlines()
    return {'commit': commit, 'tracked_diff': diff, 'files': {
        name: sha(BASELINE/name) for name in paths if (BASELINE/name).is_file()
        and (name.endswith('.py') or name.endswith('.txt') or name.startswith('gen_config/'))}}


def sdk_json_body(request):
    """The released config has only timeout as an SDK-only transport option."""
    body = deepcopy(request)
    timeout = body.pop('timeout', None)
    extra = body.pop('extra_body', {})
    assert isinstance(extra, dict)
    body.update(extra)
    return body, timeout


class ReplayMismatch(BaseException):
    """Fail closed past native retry/partial-MAP catches; never sleep or fallback."""


class SavedSDK:
    def __init__(self, source, names):
        import openai
        import httpx
        self.source = source
        self.names = names
        self.ledger = read(source/'requests_ledger.json')['requests']
        assert len(self.ledger) == len(names)
        self.index = 0
        self.lock = threading.RLock()
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))
        self.pending_sdk_request = None
        base_url = self.ledger[0]['url'].removesuffix('/chat/completions')
        self.inner = openai.OpenAI(api_key='OFFLINE_REPLAY_NO_REAL_KEY', base_url=base_url,
            http_client=httpx.Client(transport=httpx.MockTransport(self.handle)))

    def create(self, **kwargs):
        with self.lock:
            self.pending_sdk_request = deepcopy(kwargs)
            # Real SDK serialization and ChatCompletion decoding, in memory only.
            return self.inner.chat.completions.create(**kwargs)

    def handle(self, request):
        import httpx
        with self.lock:
            if self.index >= len(self.names):
                raise ReplayMismatch('Native core requested an additional unsaved response')
            number = self.index + 1
            request_path = self.source/'requests'/f'{number:03d}_request.json'
            response_path = self.source/'requests'/f'{number:03d}_response.json'
            expected = read(request_path)
            normalized, timeout = sdk_json_body(self.pending_sdk_request)
            raw = request.read()
            actual = json.loads(raw)
            if canonical(actual) != canonical(expected) or canonical(normalized) != canonical(expected):
                # No enterprise content or mismatched text is printed in the error.
                raise ReplayMismatch(f'Saved request {number} differs: '
                                     f'actual_canonical_sha={sha(canonical(actual))}; '
                                     f'expected_canonical_sha={sha(canonical(expected))}')
            ledger_row = self.ledger[self.index]
            raw_sha = hashlib.sha256(raw).hexdigest()
            if raw_sha != ledger_row['payload_sha256']:
                raise ReplayMismatch(f'Saved request {number} raw SDK serialization SHA differs')
            if request.method != ledger_row['method'] or str(request.url) != ledger_row['url']:
                raise ReplayMismatch(f'Saved request {number} method or URL differs')
            saved_response = read(response_path)
            self.calls.append({'stage': self.names[self.index], 'request_number': number,
                'json_body_exact': True, 'canonical_request_sha256': sha(canonical(actual)),
                'raw_sdk_request_sha256': raw_sha, 'raw_body_sha_matches_original_ledger': True,
                'original_http_payload_sha256': ledger_row['payload_sha256'],
                'method_and_url_exact': True,
                'saved_request_file_sha256': sha(request_path),
                'saved_response_file_sha256': sha(response_path),
                'sdk_transport_timeout_not_in_json_body': timeout,
                'response_origin': 'Unmodified saved real ChatCompletion JSON',
                'served_model': saved_response.get('model'), 'new_http_calls': 0})
            self.index += 1
            return httpx.Response(200, json=saved_response, request=request)

    def close(self):
        self.inner.close()


def tree_hashes(folder):
    return {path.relative_to(folder).as_posix(): sha(path)
            for path in sorted(folder.rglob('*')) if path.is_file()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=HERE/'private/enterprise_real_call_replay_001')
    args = parser.parse_args()
    if not sys.flags.utf8_mode:
        raise SystemExit('Run Python with -X utf8 to preserve native locale-dependent readers.')
    if args.output.exists():
        raise SystemExit('Preserve prior replay evidence; select a fresh output directory.')
    assert CHECKER.is_file()
    os.environ['PYTHONUTF8'] = '1'
    args.output.mkdir(parents=True)
    original_cwd = Path.cwd()
    analysis_protocol, evolution_protocol = read(ANALYSIS/'protocol.json'), read(EVOLUTION/'protocol.json')
    source_before = source_manifest()
    assert source_before == analysis_protocol['source_before'] == evolution_protocol['source_before']
    assert len(source_before['files']) == 550
    manifest = read(ANALYSIS/'enterprise_input_manifest.json')
    log = Path(manifest['log'])
    system, user = ANALYSIS/'domain_interface/success_system.txt', ANALYSIS/'domain_interface/success_user.txt'
    assert sha(log) == manifest['log_sha256'] and sha(system) == manifest['adapted_system_sha256']
    initialization = read(EVOLUTION/'initialization_manifest.json')
    s0 = EVOLUTION/'initial_skills/xlsx'
    paid_s1 = EVOLUTION/'evolved_skills/xlsx'
    assert tree_hashes(s0) == initialization['copied_files'] == initialization['source_files']
    tracked_inputs = [ANALYSIS/'protocol.json', EVOLUTION/'protocol.json', log, system, user,
                      ANALYSIS/'parsed_success_records.json', EVOLUTION/'input_success_records.json',
                      EVOLUTION/'input_error_records.json', EVOLUTION/'initialization_manifest.json',
                      EVOLUTION/'analysis_input_manifest.json', CHECKER]
    for run, count in ((ANALYSIS, 1), (EVOLUTION, 2)):
        tracked_inputs.append(run/'requests_ledger.json')
        for number in range(1, count+1):
            tracked_inputs.extend([run/'requests'/f'{number:03d}_request.json',
                                   run/'requests'/f'{number:03d}_response.json'])
    input_hashes = {str(path): sha(path) for path in tracked_inputs}
    s0_before, s1_before = tree_hashes(s0), tree_hashes(paid_s1)
    report = {'label': LABEL, 'real_model_calls': 0, 'new_http_calls': 0,
        'official_commit': BASELINE_COMMIT, 'official_paid_manifest_entries': len(source_before['files']),
        'official_current_matches_both_paid_manifests': True,
        'paid_wrapper_hashes': {name: doc['local_code_sha256'].get('native_runner.py')
                               for name, doc in (('analysis', analysis_protocol), ('evolution', evolution_protocol))},
        'current_wrapper_sha256': sha(HERE/'native_runner.py'),
        'historical_wrapper_full_source_available': False,
        'wrapper_limitation': 'Paid stages retained wrapper hashes but not their complete source. This is current unchanged-native-core/request replay, not a recovered old-wrapper snapshot.',
        'comparison_scope': 'Original current SDK through in-memory MockTransport: normalized full JSON body, raw body SHA, method and URL must match the saved request/ledger. This does not recover historical wrapper source.',
        'replay_source_files_sha256': input_hashes,
        'replay_program_sha256': sha(Path(__file__)),
        'profile_source_sha256': {name: sha(HERE/name) for name in ('profiles.py', 'profiles.json')},
        'claims_not_established': ['Independent model replicate', 'Skill quality or task benefit',
                                   'MERGE execution on this one-patch real run',
                                   'Historical orchestration full-source recovery']}
    dump(args.output/'source_manifest.json', source_before)
    (args.output/'source_snapshot').mkdir()
    shutil.copyfile(Path(__file__), args.output/'source_snapshot/real_call_replay.py')
    network_attempts = []
    def no_network(*a, **k):
        network_attempts.append(True)
        raise ReplayMismatch('Offline replay forbids network')
    analysis_sdk, evolution_sdk = SavedSDK(ANALYSIS, ['success_analysis']), SavedSDK(EVOLUTION, ['map', 'translation'])
    client = None
    try:
        with patch.object(socket.socket, 'connect', no_network):
            from analysis import run_success_analysis_llm as success_native
            from analysis.report_parsing import collect_success_records
            from src.react_agent.models import OpenAIClient
            from skill_evolver.parallel_success_evolving_agent import CombinedParallelSkillEvolver, normalize_mixed_records
            import openai
            profile = load_profile('paper_v5')
            model = read(ANALYSIS/'requests/001_request.json')['model']
            messages, text = success_native.analyze_instance(analysis_sdk, model,
                system.read_text(encoding='utf-8'), user.read_text(encoding='utf-8'), log,
                generation_config_for(profile, 'success_analysis'))
            analysis_out = args.output/'success_analysis'
            analysis_out.mkdir()
            report_file = analysis_out/'success_analysis_salary-monthly.md'
            report_file.write_text(text, encoding='utf-8')
            success_native.write_prompt_log(analysis_out/'success_analysis_salary-monthly_prompt.md', messages, text)
            success_records = collect_success_records(str(analysis_out))
            original_records = read(ANALYSIS/'parsed_success_records.json')
            assert canonical(success_records) == canonical(original_records)
            assert canonical(success_records) == canonical(read(EVOLUTION/'input_success_records.json'))
            dump(args.output/'parsed_success_records.json', success_records)
            original_report = ANALYSIS/'success_analysis/success_analysis_salary-monthly.md'
            assert sha(report_file) == sha(original_report)
            error_records = read(EVOLUTION/'input_error_records.json')
            assert error_records == []
            target = args.output/'evolved_skills/xlsx'
            shutil.copytree(s0, target)
            assert tree_hashes(target) == s0_before
            # Original constructor, cache/settings/chat/retry/parser are used. Only SDK is a saved-response stub.
            with patch.object(openai, 'OpenAI', lambda **kwargs: evolution_sdk):
                client = OpenAIClient(model=model, api_key='OFFLINE_REPLAY_NO_REAL_KEY',
                    base_url='https://chat.ecnu.edu.cn/open/api/v1',
                    cache_path=str(args.output/'cache/evolution-seed-41'),
                    generation_config=generation_config_for(profile, 'evolution', 41))
            os.chdir(CHECKER_ROOT)
            evolver = CombinedParallelSkillEvolver(client=client, skill_dir=target, verbose=False,
                output_dir=args.output/'intermediates', parse_failure_dir=args.output/'parse_failures',
                **native_evolver_kwargs(profile))
            result = evolver.run(normalize_mixed_records(error_records, success_records), input_mode='records')
            dump(args.output/'native_evolution_result.json', result)
            assert len(result['patches']) == 1 and result['final_patch'] is not None
            assert analysis_sdk.index == 1 and evolution_sdk.index == 2
            valid, validation_message = evolver._evolver.validate_skill()
            assert valid and 'skipped' not in validation_message.lower()
            replay_files = tree_hashes(target)
            assert replay_files == s1_before and len(replay_files) == 3
            assert tree_hashes(s0) == s0_before and tree_hashes(paid_s1) == s1_before
            assert not network_attempts
            assert source_manifest() == source_before
            assert {str(path): sha(path) for path in tracked_inputs} == input_hashes
            report.update(status='SAVED_REAL_REQUESTS_AND_THREE_OUTPUT_FILES_REPLAY_PASS',
                replayed_calls=analysis_sdk.calls+evolution_sdk.calls,
                full_request_bodies_exact_count=3, native_success_records=len(success_records),
                raw_sdk_body_sha_exact_count=3, request_method_url_exact_count=3,
                native_map_patches=1, native_translation_calls=1, native_merge_calls=0,
                native_single_patch_merge_skip=True, native_apply_executed=True,
                original_checker_passed=valid, checker_message=validation_message,
                parsed_success_records_exact=True, success_report_bytes_exact=True,
                original_paid_input_response_and_outputs_unchanged=True,
                replayed_package_sha256=replay_files, original_paid_package_sha256=s1_before,
                package_files_byte_sha_exact=True, network_attempts=0,
                source_unchanged=True, output_reproduction_only=True)
    except BaseException as exc:
        report.update(status='OFFLINE_REAL_CALL_REPLAY_FAILED_PRESERVED',
                      failure_type=type(exc).__name__, failure=str(exc),
                      replayed_calls=analysis_sdk.calls+evolution_sdk.calls,
                      network_attempts=len(network_attempts))
        raise
    finally:
        os.chdir(original_cwd)
        if client is not None and client._cache is not None:
            client._cache.close()
        analysis_sdk.close()
        evolution_sdk.close()
        dump(args.output/'result.json', report)
        print(json.dumps({key: report.get(key) for key in (
            'status', 'full_request_bodies_exact_count', 'native_success_records', 'native_map_patches',
            'native_translation_calls', 'native_merge_calls', 'package_files_byte_sha_exact',
            'replayed_package_sha256', 'source_unchanged', 'real_model_calls', 'new_http_calls',
            'failure_type', 'failure')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
