"""Independent, bounded heuristic pipeline acceptance; never a benchmark run.

Default: disclosed artificial model and lifecycle fixture with real host
validators, local file reads and official skill-creator packaging.
--live: one small synthetic source window through real stages 1--5 and adoption.
--live --exercise-use-and-update: additionally use the selected skill, submit a
synthetic feedback request, recover its trace and attempt exact-version UPDATE.
No failed request is retried automatically. Existing output directories are
rejected, including directories from earlier failed runs.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback
import uuid

DEMO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEMO))
sys.path.insert(0, str(DEMO/'tests'))

from skilldemo.core import Loop
from skilldemo.live import load_env
from skilldemo.runtime import OpenClawAgent, digest, request_config
from test_heuristic_pipeline import (BOB_FEEDBACK_REQUEST, EXPLICIT_INPUT_NOTICE, FIXTURE_NOTICE,
                                     FEEDBACK_REQUEST, HeuristicFixture, LIVE_NOTICE, USE_REQUEST,
                                     run_pipeline, synthetic_experience)


def sha256_file(path):
    digest_value = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024*1024), b''):
            digest_value.update(block)
    return digest_value.hexdigest()


def write_json(path, value):
    """Create only; the run owns a new directory and never updates old reports."""
    with path.open('x', encoding='utf-8', newline='\n') as target:
        json.dump(value, target, ensure_ascii=False, indent=2)
        target.write('\n')


def source_files():
    selected = sorted((DEMO/'skilldemo').glob('*.py'))
    selected.extend([Path(__file__).resolve(), DEMO/'tests/test_heuristic_pipeline.py',
                     DEMO/'HEURISTIC_PIPELINE_SPEC.md'])
    foundation = DEMO/'.runtime/node_modules/openclaw/skills/skill-creator'
    selected.append(DEMO/'.runtime/node_modules/openclaw/package.json')
    selected.extend(foundation/relative for relative in (
        'SKILL.md', 'scripts/quick_validate.py', 'scripts/package_skill.py'))
    return [path for path in selected if path.is_file()]


def source_manifest():
    return {path.relative_to(DEMO).as_posix(): sha256_file(path) for path in source_files()}


def snapshot_sources(run_root):
    """Preserve the exact small, declared source set, never the whole checkout."""
    hashes = {}
    for path in source_files():
        relative = path.relative_to(DEMO)
        destination = run_root/'source_snapshot'/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open('xb') as target:
            target.write(path.read_bytes())
        hashes[relative.as_posix()] = sha256_file(destination)
    return hashes


def public_provider_config():
    # request_config deliberately omits the secret API key.  Do not hash, copy,
    # print or persist .env contents; reproducibility records the public options.
    return {purpose: request_config(purpose) for purpose in (
        'relational_extract', 'workflow_extract', 'workflow_merge', 'workflow_creator', 'learn')}


def unique_run_path(explicit, live):
    if explicit:
        result = Path(explicit).resolve()
    else:
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        name = ('live-' if live else 'fixture-')+stamp+'-'+uuid.uuid4().hex[:8]
        result = DEMO/'artifacts/heuristic-acceptance/runs'/name
    if result.exists():
        raise FileExistsError('output directory already exists; choose a new run directory')
    result.mkdir(parents=True, exist_ok=False)
    return result


def output_manifest(run_root):
    # Hash files already stored in this run, including sqlite, request cache,
    # creator drafts and packages. This does not read the source env file.
    return {path.relative_to(run_root).as_posix(): {
        'sha256': sha256_file(path), 'bytes': path.stat().st_size}
        for path in sorted(run_root.rglob('*')) if path.is_file()
        and path.name not in ('output-manifest.json', 'reproducibility.json')}


def run_rows(loop):
    if loop is None:
        return []
    with loop.store.tx() as db:
        rows = db.execute('SELECT id,purpose,mode,status,result FROM runs ORDER BY started,id').fetchall()
    public = []
    for row in rows:
        result = json.loads(row['result'] or '{}')
        public.append({'id': row['id'], 'purpose': row['purpose'], 'mode': row['mode'],
                       'status': row['status'], 'modelRequestStarts': result.get('modelRequestStarts'),
                       'fixtureHostProof': result.get('fixtureHostProof', False)})
    return public


def acceptance_notice(live, explicit_input=False):
    return EXPLICIT_INPUT_NOTICE if explicit_input else LIVE_NOTICE if live else FIXTURE_NOTICE


def request_summary(calls):
    """Keep host dispatches separate from recorded model rounds and unknowns."""
    known = lambda row: isinstance(row.get('modelRequestStarts'), int) and not isinstance(
        row.get('modelRequestStarts'), bool) and row['modelRequestStarts'] >= 0
    real = [row for row in calls if row.get('mode') == 'openclaw']
    unknown = sum(not known(row) for row in calls)
    real_unknown = sum(not known(row) for row in real)
    recorded = sum(row['modelRequestStarts'] for row in calls if known(row))
    recorded_real = sum(row['modelRequestStarts'] for row in real if known(row))
    return {'requestRuns': calls, 'requestDispatches': len(calls),
            'modelRequestStarts': None if unknown else recorded,
            'realModelRequestStarts': None if real_unknown else recorded_real,
            'knownModelRequestStarts': recorded, 'knownRealModelRequestStarts': recorded_real,
            'modelRequestStartsUnknownDispatches': unknown,
            'realModelRequestStartsUnknownDispatches': real_unknown,
            'modelRequestStartsScope': 'Recorded run-result modelRequestStarts; provider transport retries are not measured.'}


def literal_credential_scan(run_root, live):
    """Inspect only this run for the current key; never return its value/content."""
    if not live:
        return {'status': 'NOT_APPLICABLE_FIXTURE', 'checkedFiles': 0, 'literalFound': None, 'paths': []}
    secret = os.environ.get('DEMO_API_KEY')
    if not secret:
        return {'status': 'KEY_UNAVAILABLE', 'checkedFiles': 0, 'literalFound': None, 'paths': []}
    marker = secret.encode('utf-8')
    checked, paths = 0, []
    for path in sorted(run_root.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        checked += 1
        with path.open('rb') as source:
            tail = b''
            for chunk in iter(lambda: source.read(1024*1024), b''):
                joined = tail+chunk
                if marker in joined:
                    paths.append(path.relative_to(run_root).as_posix().replace(secret, '[REDACTED]'))
                    break
                tail = joined[-max(0, len(marker)-1):] if len(marker)>1 else b''
    return {'status': 'FAIL' if paths else 'PASS', 'checkedFiles': checked,
            'literalFound': bool(paths), 'paths': paths,
            'scope': 'Literal current DEMO_API_KEY bytes in this run; no claim about other credentials.'}


def redact_current_key(value, live):
    secret = os.environ.get('DEMO_API_KEY') if live else None
    if not secret:
        return value
    def scrub(item):
        if isinstance(item, str):
            return item.replace(secret, '[REDACTED]')
        if isinstance(item, list):
            return [scrub(child) for child in item]
        if isinstance(item, dict):
            return {scrub(key): scrub(child) for key, child in item.items()}
        return item
    return scrub(value)


def openclaw_version():
    manifest = DEMO/'.runtime/node_modules/openclaw/package.json'
    return json.loads(manifest.read_text(encoding='utf-8')).get('version') if manifest.is_file() else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true', help='Use the existing real provider; synthetic input remains disclosed.')
    parser.add_argument('--exercise-use-and-update', action='store_true',
                        help='In live mode, add actual skill use, synthetic feedback and one UPDATE attempt.')
    parser.add_argument('--organization', action='store_true',
                        help='Also exercise a synthetic review decision and cross-member use in live mode.')
    parser.add_argument('--output', help='A NEW independent run directory; existing paths are refused.')
    parser.add_argument('--env-file', help='Existing DEMO_* env file for live mode (default: demo/.env). Never copied.')
    parser.add_argument('--input-experience',
                        help='Explicit E/C/V JSON for a single live stage1--5 run; no data is read by default.')
    parser.add_argument('--assert-no-prior-skill', metavar='BASIS',
                        help='For explicit input only: nonempty source basis for the caller declaration that no prior skill was used.')
    args = parser.parse_args(argv)
    if args.organization and args.live and not args.exercise_use_and_update:
        parser.error('--organization in live mode requires --exercise-use-and-update')
    if args.input_experience and (not args.live or args.exercise_use_and_update or args.organization):
        parser.error('--input-experience is supported only for a live stage1--5 run; synthetic use/update applies to the default fixture')
    if args.assert_no_prior_skill is not None and (not args.input_experience or not args.assert_no_prior_skill.strip()):
        parser.error('--assert-no-prior-skill requires --input-experience and a nonempty source basis')
    run_root = unique_run_path(args.output, args.live)
    started = datetime.now(timezone.utc).isoformat()
    experience = (json.loads(Path(args.input_experience).read_text(encoding='utf-8-sig'))
                  if args.input_experience else synthetic_experience())
    if not isinstance(experience, dict) or set(experience)-{'events','context','evaluations'}:
        raise ValueError('input experience must contain only events/context/evaluations')
    initialization = ({'status': 'KNOWN_NONE', 'basis': 'CALLER_DECLARATION: '+args.assert_no_prior_skill.strip()}
                      if args.assert_no_prior_skill else
                      {'status': 'UNKNOWN', 'basis': 'Explicit input does not establish prior skill initialization'}
                      if args.input_experience else
                      {'status': 'KNOWN_NONE', 'basis': 'Disclosed synthetic history explicitly contains no selected skills'})
    input_data = {'experience': experience, 'initialization': initialization, 'useRequest': USE_REQUEST,
                  'feedbackRequest': FEEDBACK_REQUEST, 'bobFeedbackRequest': BOB_FEEDBACK_REQUEST,
                  'synthetic': not bool(args.input_experience),
                  'fixtureNotice': acceptance_notice(args.live, bool(args.input_experience))}
    write_json(run_root/'input.json', input_data)
    before_code = snapshot_sources(run_root)
    write_json(run_root/'code-before.json', before_code)
    loop, report, config = None, {}, {}
    try:
        if args.live:
            env = Path(args.env_file).resolve() if args.env_file else DEMO/'.env'
            if not env.is_file():
                raise FileNotFoundError('live mode requires an existing DEMO_* env file')
            load_env(env)
            config = public_provider_config()
            agent = OpenClawAgent()
        else:
            agent = HeuristicFixture()
        loop = Loop(run_root/'state', agent, settle_seconds=0, idle_seconds=1,
                    daily_limit=30, stage_pipeline=True, learning_algorithm='heuristic')
        report = run_pipeline(loop, exercise_use_and_update=(not args.live or args.exercise_use_and_update),
                              organization=(not args.live or args.organization), experience=experience,
                              initialization=initialization, report=report)
        write_json(run_root/'snapshot-alice.json', loop.snapshot('alice'))
        if not args.live or args.organization:
            write_json(run_root/'snapshot-bob.json', loop.snapshot('bob'))
    except Exception as error:
        # Keep the failed run and all host/provider evidence. A new launch must
        # select a new directory; no automatic retries or historical overwrites.
        report.update(status='FAILED', errorType=type(error).__name__,
                      error=str(error)[:1800], traceback=traceback.format_exc(limit=6),
                      semanticPerformance='NOT_MEASURED')
        if loop is not None and not (run_root/'snapshot-alice.json').exists():
            write_json(run_root/'snapshot-alice.json', loop.snapshot('alice'))
    after_code = source_manifest()
    if before_code != after_code:
        report.update(status='FAILED', sourceChangedDuringRun=True,
                      reproducibilityLimitation='Source hashes changed during execution; repeat in a new directory after edits stop.')
    calls = run_rows(loop)
    mode = ('REAL_PROVIDER_EXPLICIT_INPUT' if args.input_experience else
            'REAL_PROVIDER_SYNTHETIC_INPUT' if args.live else 'SYNTHETIC_FIXTURE')
    report.update(request_summary(calls))
    report.setdefault('organizationReview', 'NOT_EXERCISED')
    report.update(mode=mode, fixtureNotice=input_data['fixtureNotice'],
                  automaticRetries=0, benchmarkGoldInput=False,
                  automaticRetryScope='HOST_STAGE_DISPATCH', providerTransportRetries='NOT_MEASURED',
                  organizationReviewRequested=bool(not args.live or args.organization))
    scan = literal_credential_scan(run_root, args.live)
    if scan['status'] == 'FAIL':
        report.update(status='FAILED', credentialLiteralPaths=scan['paths'])
    report['literalCredentialScan'] = scan
    write_json(run_root/'acceptance.json', redact_current_key(report, args.live))
    write_json(run_root/'code-after.json', after_code)
    outputs = output_manifest(run_root)
    write_json(run_root/'output-manifest.json', redact_current_key(outputs, args.live))
    reproducibility = {'startedAtUtc': started, 'finishedAtUtc': datetime.now(timezone.utc).isoformat(),
                       'mode': report['mode'], 'learningAlgorithm': 'heuristic',
                       'inputSha256': sha256_file(run_root/'input.json'), 'inputCanonicalHash': digest(input_data),
                       'codeHashBefore': digest(before_code), 'codeHashAfter': digest(after_code),
                       'outputsCanonicalHash': digest(outputs), 'publicProviderConfig': redact_current_key(config, args.live),
                       'pythonVersion': sys.version, 'pythonExecutable': sys.executable,
                       'openclawVersion': openclaw_version(),
                       'openclawVersionSource': 'Bundled public package.json; custom launcher overrides are not attested.',
                       'literalCurrentProviderKeyPersisted': scan['literalFound'],
                       'literalCredentialScan': scan,
                       'sourceSnapshot': 'source_snapshot',
                       'sourceSnapshotScope': 'Declared small source set and creator foundation; no full vendor snapshot.',
                       'providerReplayLimitation': 'Provider behavior and text are not guaranteed to reproduce verbatim.',
                       'fixtureHostProofIsProviderEvidence': False,
                       'semanticPerformance': 'NOT_MEASURED', 'businessBenefit': 'NOT_MEASURED'}
    write_json(run_root/'reproducibility.json', redact_current_key(reproducibility, args.live))
    print(json.dumps({'status': report['status'], 'mode': report['mode'], 'outputDirectory': str(run_root),
                      'completedThrough': report.get('completedThrough'), 'requestDispatches': len(calls),
                      'realModelRequestStarts': report['realModelRequestStarts'],
                      'semanticPerformance': 'NOT_MEASURED'}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 2 if report['status'] == 'DEFERRED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
