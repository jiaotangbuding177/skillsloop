"""Free, synthetic stage-4/5 preflight probes. No model or enterprise input.

Run from any directory with Python. Application source is imported read-only;
SQLite writes are confined to TemporaryDirectory and automatically removed.
"""
import copy
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'enginering/demo'))
from skilldemo.core import Loop
from skilldemo import workflow
from skilldemo.workflow_bridge import discover
from skilldemo.creator import verify_files
from skilldemo.runtime import HEADINGS


def trace():
    return {'id': 't1', 'owner': 'alice', 'org': 'acme',
            'schemaVersion': 'task-trace-v2', 'purposeSplit': 'generation',
            'session': 's1', 'state': 'SEALED', 'revision': 1, 'hash': 'h1',
            'goal': 'synthetic task', 'businessOutcome': 'UNKNOWN',
            'initializationEvidence': [{'status': 'KNOWN_NONE', 'basis': 'synthetic fixture'}],
            'skillUseReceipts': [], 'requirementTimeline': [
                {'version': 1, 'effectiveFromPairId': 'p1', 'requestedText': 'synthetic task action'}],
            'feedbackEdges': [], 'observations': [],
            'attempts': [{'id': 'a1', 'pairId': 'p1'}], 'unresolved': []}


def extraction(payload, method_id='m1'):
    return {'sourceHash': payload['sourceHash'], 'frames': [
        {'id': 'f1', 'traceId': 't1', 'goal': 'synthetic task',
         'inputContract': [], 'outputContract': [], 'processSketch': ['step'],
         'conditions': [], 'parameters': [], 'methodIds': [method_id]}],
        'methods': [{'id': method_id, 'frameId': 'f1', 'action': 'do synthetic action',
                     'inputs': [], 'outputs': [], 'conditions': [], 'evidenceRefs': ['e1'],
                     'decisionHint': 'EXCLUDE', 'evidenceKind': 'VERIFIED_CHECK', 'outcome': 'SUCCESS'}],
        'relations': []}


class StubAgent:
    mode = 'audit-free'

    def __init__(self):
        self.calls = 0

    def run(self, purpose, payload, workspace):
        self.calls += 1
        value = extraction(payload) if purpose == 'workflow_extract' else {
            'sourceHash': payload['sourceHash'], 'workflows': [], 'ledger': []}
        return {'text': json.dumps(value)}


def skill_body(method_id):
    return ('---\nname: synthetic-check\ndescription: synthetic fixture\n---\n'
            f'<!-- SKILLSLOOP_METHOD:{method_id} -->\nNo executable workflow content.\n'
            '## 市场信息\n' + '\n'.join('### ' + h + '\nfixture' for h in HEADINGS))


def main():
    results = {'usesEnterpriseData': False, 'paidModelCalls': 0,
               'applicationSourceModified': False, 'findings': {}}
    found = results['findings']
    with tempfile.TemporaryDirectory() as root:
        agent = StubAgent()
        loop = Loop(root, agent, stage_pipeline=True, task_detection=False, daily_limit=0)
        with loop.store.tx() as db:
            loop.store.put(db, 'trace', trace())
        discover(loop, 'alice')
        loop.daily_limit = 100
        retried = discover(loop, 'alice')
        with loop.store.tx() as db:
            source = loop.store.get(db, 'trace', 't1')
        found['budgetExhaustionBecomesPermanentDecision'] = {
            'reproduced': source['decision']['reason'] == 'STAGE4_FAILED' and agent.calls == 0,
            'callsAfterBudgetIncrease': agent.calls, 'newCandidateCount': len(retried),
            'decision': source['decision']}
    with tempfile.TemporaryDirectory() as root:
        agent = StubAgent()
        loop = Loop(root, agent, stage_pipeline=True, task_detection=False, daily_limit=100)
        with loop.store.tx() as db:
            loop.store.put(db, 'trace', trace())
        discover(loop, 'alice')
        with loop.store.tx() as db:
            analyses = loop.store.rows(db, 'workflow_analysis', 'alice')
            source = loop.store.get(db, 'trace', 't1')
        found['invalidMergeCachedReady'] = {
            'reproduced': any(row['purpose'] == 'workflow_merge' and row['status'] == 'READY'
                              for row in analyses) and source['decision']['reason'] == 'STAGE4_FAILED',
            'stubCalls': agent.calls,
            'analysisStatuses': [{'purpose': row['purpose'], 'status': row['status']} for row in analyses],
            'decision': source['decision']}
    source = trace()
    payload, catalog = workflow.prepare([source])
    extracted = workflow.validate_extract(extraction(payload), payload, catalog)
    groups, routes = workflow.clusters(extracted, [source], catalog)
    view = workflow.merge_input(extracted, groups, routes, payload)
    merged = {'sourceHash': view['sourceHash'], 'workflows': [
        {'frameIds': ['f1'], 'title': 'synthetic', 'trigger': 'use', 'inputs': [],
         'steps': [{'id': 's1', 'methodIds': ['m1'], 'action': 'do', 'completionCheck': 'check'}],
         'outputs': [], 'limitations': [], 'includedMethodIds': ['m1']}],
        'ledger': [{'methodId': 'm1', 'disposition': 'INCLUDED', 'reason': 'include despite exclusion'}]}
    workflow.validate_merge(merged, view, extracted)
    found['underconstrainedStructuredOutputAccepted'] = {
        'reproduced': True, 'emptyInputsOutputsLimitationsAccepted': True,
        'excludeHintCanBeIncludedWithoutReassessment': True,
        'verifiedCheckSuccessClaimAcceptedFromUserRequirementEvidence': True,
        'scope': 'validator behavior; not evidence that a model will emit this output'}
    dotted = extraction(payload, 'm1.1')
    workflow.validate_extract(dotted, payload, catalog)
    try:
        verify_files([{'path': 'SKILL.md', 'content': skill_body('m1.1')}], ['m1.1'])
    except ValueError as exc:
        found['methodIdStage4Stage5Mismatch'] = {'reproduced': True, 'acceptedAtStage4': True,
                                                'rejectedAtStage5': str(exc)}
    files = [{'path': 'SKILL.md', 'content': skill_body('m1')}]
    found['methodMarkerOnlyPassesCoverage'] = {
        'reproduced': verify_files(files, ['m1'])['status'] == 'PASS',
        'scope': 'does not establish semantic content coverage; no actual model generation'}
    files.append({'path': 'references/note.md', 'content': '[Return](../SKILL.md)'})
    try:
        verify_files(files, ['m1'])
    except ValueError as exc:
        found['validRelativeBacklinkRejected'] = {'reproduced': True, 'error': str(exc)}
    long_source = copy.deepcopy(source)
    long_source['requirementTimeline'][0]['requestedText'] = 'x' * 1200
    long_source['attempts'][0]['executionRefs'] = {
        'runId': 'run1', 'checks': [{'status': 'PASS'}],
        'toolEventIds': ['tool1'], 'artifacts': [{'path': 'out.txt'}]}
    prepared, _ = workflow.prepare([long_source])
    evidence_chars = len(prepared['traces'][0]['evidence'][0]['text'])
    attempt = prepared['traces'][0]['attempts'][0]
    found['stage4EvidenceProjectionLoss'] = {
        'reproduced': evidence_chars == 900 and 'executionRefs' not in attempt,
        'sourceEvidenceChars': 1200, 'modelEvidenceChars': evidence_chars,
        'truncationFlagPresent': any('truncat' in key.lower() for key in prepared['traces'][0]['evidence'][0]),
        'executionRefsInModelAttempt': 'executionRefs' in attempt,
        'scope': 'source remains in trace; model view loses suffix and execution evidence'}
    result_path = Path(__file__).with_name('stage45-result.json')
    result_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'resultPath': str(result_path),
                      'reproducedFindings': [key for key, value in found.items() if value['reproduced']]},
                     ensure_ascii=False))


if __name__ == '__main__':
    main()
