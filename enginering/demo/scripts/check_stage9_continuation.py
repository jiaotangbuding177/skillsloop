"""One explicit, isolated stage-9 continuation; never a fresh full-loop claim.

Inherit a completed real stages-1--8 store into a NEW directory, create a NEW
candidate, and run only its learner/host compiler/package/adoption. Old reports,
responses and databases remain untouched. Use --captured-response for a free
host replay, or --live for one fresh real learner dispatch.
"""
import argparse
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import uuid
from zipfile import ZipFile

DEMO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DEMO))
sys.path.insert(0, str(DEMO / 'scripts'))
from check_heuristic_pipeline import (literal_credential_scan, output_manifest,
    public_provider_config, redact_current_key, request_summary, run_rows,
    sha256_file, snapshot_sources, source_manifest, write_json)
from skilldemo.core import Loop
from skilldemo.live import load_env
from skilldemo.runtime import OpenClawAgent, digest


class CapturedLearner:
    mode = 'openclaw'

    def __init__(self, text):
        self.text = text

    def run(self, purpose, payload, workspace):
        if purpose != 'learn':
            raise ValueError('captured continuation permits stage 9 only')
        return {'text': self.text, 'mode': self.mode, 'modelRequestStarts': 0,
                'fixtureHostProof': True, 'runtime': 'CAPTURED_REAL_RESPONSE_HOST_REPLAY',
                'status': 'ok', 'usage': None, 'costUsd': None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True, help='Stable completed real stages-1--8 run')
    parser.add_argument('--candidate', required=True, help='Existing failed UPDATE candidate')
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--live', action='store_true')
    modes.add_argument('--captured-response', help='Exact raw final string JSON record from that run')
    args = parser.parse_args()
    load_env(DEMO / '.env')
    source = Path(args.source).resolve()
    if not source.is_relative_to(DEMO / 'artifacts/heuristic-acceptance/runs'):
        raise ValueError('source must stay in the declared acceptance-runs directory')
    old_report = json.loads((source / 'acceptance.json').read_text(encoding='utf-8'))
    if (old_report.get('completedThrough') != 'STAGES_1_TO_8'
            or old_report.get('mode') != 'REAL_PROVIDER_SYNTHETIC_INPUT'):
        raise ValueError('source is not completed real stages 1--8')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    name = ('stage9-live-' if args.live else 'stage9-captured-') + stamp + '-' + uuid.uuid4().hex[:8]
    root = DEMO / 'artifacts/heuristic-acceptance/runs' / name
    root.mkdir(parents=True, exist_ok=False)
    before = source_manifest()
    before['scripts/check_stage9_continuation.py'] = sha256_file(Path(__file__).resolve())
    snapshot_sources(root)
    destination = root / 'source_snapshot/scripts/check_stage9_continuation.py'
    destination.write_bytes(Path(__file__).read_bytes())
    write_json(root / 'code-before.json', before)
    source_files = [p for p in (source / 'state').rglob('*') if p.is_file()]
    if any(p.is_symlink() for p in (source / 'state').rglob('*')):
        raise ValueError('symlink in source; no implicit external-file copy')
    inherited = {p.relative_to(source).as_posix(): sha256_file(p) for p in source_files}
    # The source process has ended. Its immutable state is copied, never opened
    # by Loop; all writes and the explicit new candidate belong to the clone.
    shutil.copytree(source / 'state', root / 'state')
    write_json(root / 'inherited-source-manifest.json', inherited)
    baseline_snapshot = json.loads((source / 'snapshot-alice.json').read_text(encoding='utf-8'))
    original = next(c for c in baseline_snapshot['candidates'] if c['id'] == args.candidate)
    if original.get('action') != 'UPDATE' or original.get('status') != 'FAILED':
        raise ValueError('expected one explicitly inspected FAILED UPDATE candidate')
    if args.live:
        agent = OpenClawAgent()
    else:
        response = Path(args.captured_response).resolve()
        expected = (source / 'state/workspaces' / (original['runId'] + '-control') / 'stdout.json').resolve()
        if response != expected:
            raise ValueError('captured response must be the exact candidate native stdout')
        native = json.loads(response.read_text(encoding='utf-8'))
        text = native.get('final') or '\n'.join(p.get('text', '') for p in native.get('payloads', []))
        source_result = next(r['result'] for r in baseline_snapshot['runs'] if r['id'] == original['runId'])
        if text != source_result.get('text'):
            raise ValueError('captured native reply differs from persisted candidate run')
        agent = CapturedLearner(text)
        write_json(root / 'captured-response-source.json', {
            'path': str(response), 'sha256': sha256_file(response),
            'notice': 'Exact recorded native reply, not a new model response.'})
    loop = Loop(root / 'state', agent, daily_limit=30, stage_pipeline=True, learning_algorithm='heuristic')
    previous_runs = {row['id'] for row in run_rows(loop)}
    new = copy.deepcopy(original)
    new.update(id='candidate-continuation-' + uuid.uuid4().hex[:24], status='QUEUED',
               poolId=None, runId=None, notBefore=0,
               continuationSource={'run': str(source), 'candidateId': args.candidate,
                                   'upstream': 'INHERITED_REAL_STAGES_1_TO_8'})
    for key in ('error', 'files', 'hash', 'patchAudit', 'installedSkill', 'package'):
        new.pop(key, None)
    baseline = next(s for s in baseline_snapshot['skills'] if s['id'] == new['target'])
    assert baseline['version'] == 1 and baseline['hash'] == new['baseHash']
    with loop.store.tx() as db:
        loop.store.put(db, 'candidate', new)
    write_json(root / 'input.json', {'source': str(source), 'originalCandidateId': args.candidate,
        'newCandidateId': new['id'], 'inputHash': digest(new['input']),
        'baselineSkillId': baseline['id'], 'baselineHash': baseline['hash'],
        'publicConfig': public_provider_config()})
    result = loop.generate('alice', new['id'])
    report = {'mode': 'INHERITED_REAL_PREFIX_FRESH_STAGE9' if args.live else 'CAPTURED_REAL_RESPONSE_HOST_REPLAY',
        'upstreamNotice': 'Stages 1--8 inherited from source; not a fresh full-loop run.',
        'sourceRun': str(source), 'sourceCompletedThrough': old_report['completedThrough'],
        'candidateStatus': result['status'], 'error': result.get('error'),
        'automaticStageRetries': 0, 'organizationReview': 'NOT_EXERCISED',
        'organizationReuse': 'NOT_EXERCISED', 'organizationFeedback': 'NOT_EXERCISED',
        'status': 'FAILED', 'patchAudit': result.get('patchAudit')}
    if result['status'] == 'READY':
        upgraded = loop.accept('alice', new['id'])
        assert upgraded['id'] == baseline['id'] and upgraded['version'] == 2
        assert upgraded['hash'] != baseline['hash']
        old_version = next(v for v in upgraded['versions'] if v['version'] == 1)
        assert old_version['hash'] == baseline['hash'] and old_version['files'] == baseline['files']
        with loop.store.tx() as db:
            native_result = db.execute('SELECT result FROM runs WHERE id=?', (result['runId'],)).fetchone()
        receipt = json.loads(native_result['result'])['package']
        workspace = loop.store.root / 'workspaces' / result['runId']
        archive = (workspace / receipt['path']).resolve()
        assert archive.is_relative_to(workspace.resolve()) and not archive.is_symlink()
        assert sha256_file(archive) == receipt['sha256'] and archive.stat().st_size == receipt['bytes']
        members = {archive.stem + '/' + f['path']: f['content'].encode('utf-8') for f in upgraded['files']}
        with ZipFile(archive) as packaged:
            assert sorted(packaged.namelist()) == sorted(members)
            assert all(packaged.read(path) == data for path, data in members.items())
        report.update(status='PASS', skillId=upgraded['id'], version=2,
                      baselineHash=baseline['hash'], hash=upgraded['hash'],
                      baselinePreserved=True, package={**receipt, 'archiveMembersMatchAdopted': True})
    elif result['status'] in ('DEFER', 'SUPPORT'):
        report.update(status='DEFERRED', baselinePreserved=True)
    write_json(root / 'snapshot-alice.json', loop.snapshot('alice'))
    report.update(request_summary([r for r in run_rows(loop) if r['id'] not in previous_runs]))
    with loop.store.tx() as db:
        rows = db.execute('SELECT id,result FROM runs').fetchall()
    report['newRunUsage'] = [{'id':r['id'], 'usage':json.loads(r['result'] or '{}').get('usage')}
                            for r in rows if r['id'] not in previous_runs]
    after = source_manifest()
    after['scripts/check_stage9_continuation.py'] = sha256_file(Path(__file__).resolve())
    write_json(root / 'code-after.json', after)
    report['sourceCodeUnchanged'] = before == after
    report['inheritedSourceUnchanged'] = all(sha256_file(source / path) == h for path, h in inherited.items())
    report['credentialScan'] = literal_credential_scan(root, True)
    if (not report['sourceCodeUnchanged'] or not report['inheritedSourceUnchanged']
            or report['credentialScan'].get('status') != 'PASS'):
        report['status'] = 'FAILED'
    write_json(root / 'acceptance.json', redact_current_key(report, True))
    write_json(root / 'output-manifest.json', output_manifest(root))
    print(json.dumps({'status': report['status'], 'mode': report['mode'], 'outputDirectory': str(root),
                      'realModelRequestStarts': report.get('realModelRequestStarts')}, ensure_ascii=False))
    return 0 if report['status'] == 'PASS' else 2 if report['status'] == 'DEFERRED' else 1


if __name__ == '__main__':
    raise SystemExit(main())
