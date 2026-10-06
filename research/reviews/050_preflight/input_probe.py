"""Free, source-preserving stage 1-3 preflight. Never calls a remote model.

Prints and saves metadata only; enterprise message bodies remain in memory.
The invalid-output cache check uses a synthetic fixture in a temporary store.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
import tempfile

PROJECT = Path(__file__).resolve().parents[3]
DEMO = PROJECT / 'enginering/demo'
CASE = PROJECT / 'research/cases/038_contract_multi_review'
sys.path.insert(0, str(DEMO))
sys.path.insert(0, str(DEMO / 'scripts'))
from check_038_stages123 import source_events
from skilldemo import intake, pair_detection
from skilldemo.core import Loop


class InvalidOutputAgent:
    mode = 'audit-free'

    def __init__(self):
        self.calls = 0

    def run(self, purpose, payload, work):
        self.calls += 1
        return {'text': json.dumps({'sourceHash': payload['sourceHash'],
                                   'seeds': [], 'annotations': []})}


def main():
    paths = ('private/raw_messages.jsonl', 'source_index.json',
             'recovered_trajectories.json', 'package_manifest.json')
    refs = json.loads((CASE / 'recovered_trajectories.json').read_text(encoding='utf-8'))
    source_index = json.loads((CASE / 'source_index.json').read_text(encoding='utf-8'))
    by_id = {row['messageId']: row for row in source_index}
    lines = (CASE / 'private/raw_messages.jsonl').read_bytes().splitlines()
    raw = [json.loads(line) for line in lines]
    rows = source_events()
    result = {
        'reviewRound': '050', 'remoteModelCalls': 0,
        'evidenceType': 'FREE_INPUT_PREFLIGHT_AND_SYNTHETIC_FAILURE_REPRODUCTION',
        'sourceFilesSha256': {str(CASE / name): hashlib.sha256((CASE / name).read_bytes()).hexdigest()
                              for name in paths},
        'indexedFileExists': True, 'indexedTopLevelType': type(refs).__name__,
        'indexedRecords': len(refs), 'indexedTopLevelKeys': sorted(refs[0]),
        'indexedTurnKeys': sorted(refs[0]['turns'][0]),
        'indexContainsBody': any(key in turn for ref in refs for turn in ref['turns']
                                for key in ('user', 'assistant', 'content')),
        'rawRows': len(raw), 'roles': dict(Counter(row['role'] for row in raw)),
        'uniqueRawIds': len({row['id'] for row in raw}),
        'rawHashMatch': all(hashlib.sha256(line).hexdigest() == by_id[row['id']]['rawLineSha256']
                            for line, row in zip(lines, raw)),
        'contentHashMatch': all(hashlib.sha256(row['content'].encode('utf-8')).hexdigest()
                                == by_id[row['id']]['contentSha256'] for row in raw),
        'referenceIdsEqualRaw': {row['id'] for row in raw} == {
            mid for ref in refs for turn in ref['turns']
            for mid in [turn['userMessageId'], *turn['assistantMessageIds']]},
        'sessions': [],
    }
    for session in sorted({row['sessionId'] for row in rows}):
        split = 'holdout' if session == 'conv_60925fa3f733' else 'generation'
        events = [intake.event('alice', row, split, i)
                  for i, row in enumerate(rows) if row['sessionId'] == session]
        pairs, unassigned = intake.assemble(events, {
            'status': 'KNOWN_NONE', 'basis': 'User confirmed historical enterprise agent had no skills.'})
        payload, *_ = pair_detection.prepare(pairs)
        result['sessions'].append({
            'session': session, 'split': split, 'events': len(events), 'pairs': len(pairs),
            'assistantIds': sum(len(pair['assistantSegments']) for pair in pairs),
            'unassigned': len(unassigned),
            'readable': all(pair['contentStatus'] == 'READABLE' for pair in pairs),
            'stage2PayloadChars': len(str(payload)), 'stage2MaxChars': pair_detection.MAX_CHARS,
        })
    try:
        intake.event('alice', refs[0], 'generation', 1)
    except ValueError as exc:
        result['directIndexImportError'] = str(exc)
    else:
        result['directIndexImportError'] = None

    with tempfile.TemporaryDirectory(prefix='050-input-cache-probe-') as folder:
        agent = InvalidOutputAgent()
        loop = Loop(Path(folder), agent, stage_pipeline=True, settle_seconds=0, daily_limit=8)
        loop.import_events('alice', [
            {'id': 'audit-u', 'sessionId': 'audit-only', 'role': 'user',
             'content': 'Please write a memo.', 'sourceOrder': 1},
            {'id': 'audit-a', 'sessionId': 'audit-only', 'role': 'assistant',
             'content': 'Memo draft.', 'sourceOrder': 2}],
            initialization={'status': 'KNOWN_NONE', 'basis': 'Synthetic fixture'})
        first = loop.run_stages('alice')
        second = loop.run_stages('alice')
        with loop.store.tx() as db:
            cache = loop.store.rows(db, 'front_analysis', 'alice')
        result['invalidOutputCacheProbe'] = {
            'fixtureType': 'SYNTHETIC_NON_ENTERPRISE', 'remoteModelCalls': 0,
            'fakeAgentRequests': agent.calls,
            'firstStage2': first['sessions'][0]['stage2'],
            'secondStage2': second['sessions'][0]['stage2'],
            'analysisCacheState': cache[0]['state'],
            'errorsEqual': first['sessions'][0]['error'] == second['sessions'][0]['error'],
            'error': first['sessions'][0]['error'],
            'observedInvalidOutputCachedReady': agent.calls == 1
                and first['sessions'][0]['stage2'] == 'DEFERRED_OR_INVALID'
                and second['sessions'][0]['stage2'] == 'DEFERRED_OR_INVALID'
                and cache[0]['state'] == 'READY',
        }
    result['scope'] = ('Input preparation and a synthetic cache failure only; '
                       'does not execute semantic stage 2/3 or skill generation.')
    destination = Path(__file__).with_name('input-result.json')
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'artifact': str(destination), 'rawRows': result['rawRows'],
                      'sourceHashesPass': result['rawHashMatch'] and result['contentHashMatch'],
                      'invalidOutputCacheReproduced': result['invalidOutputCacheProbe']['observedInvalidOutputCachedReady'],
                      'remoteModelCalls': 0}, ensure_ascii=True))


if __name__ == '__main__':
    main()
