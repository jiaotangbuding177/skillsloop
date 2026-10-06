"""Independent source-to-delivery conservation checks; no model requests."""
from pathlib import Path
from collections import Counter
from itertools import zip_longest
import hashlib, json, sys

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT.parent / 'full_063' / 'private'
OUT = ROOT / 'private'

def norm(text):
    return text.replace('\r\n', '\n').strip()

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    totals = Counter()
    sessions = set()
    with (SOURCE / 'evomind_conversations.jsonl').open(encoding='utf-8') as raw, (OUT / 'evomind_conversations.jsonl').open(encoding='utf-8') as final:
        for source_line, delivery_line in zip_longest(raw, final):
            assert source_line is not None and delivery_line is not None
            before, after = json.loads(source_line), json.loads(delivery_line)
            sid = before['session_id']
            assert sid == after['session_id'] and sid not in sessions
            sessions.add(sid)
            assert before['session_metadata'] == after['session_metadata']
            assert before['order_diagnostics'] == after['source_order_diagnostics']
            nodes = after['user_requests'] + after['assistant_contents']
            retained = [event for node in nodes for event in node['occurrences']]
            side = after['retry_controls'] + after['empty_ai_events'] + after['other_events']
            original = {event['id']: event for event in before['messages']}
            assert len(original) == len(before['messages'])
            assert Counter(event['id'] for event in retained + side) == Counter(original.keys())
            assert all(event == original[event['id']] for event in retained + side)
            assert after['source_order_ids'] == [event['id'] for event in before['messages']]
            assert len({norm(node['content']) for node in after['assistant_contents']}) == len(after['assistant_contents'])
            assert all(norm(node['content']) for node in after['assistant_contents'])
            user_keys = []
            for node in after['user_requests']:
                event = node['occurrences'][0]
                payload = event['raw_record'].get('rawPayload')
                files = payload.get('files') if isinstance(payload, dict) else None
                user_keys.append((norm(node['content']), json.dumps(files or [], ensure_ascii=False, sort_keys=True)))
            assert len(set(user_keys)) == len(user_keys)
            users = {node['group_id'] for node in after['user_requests']}
            ais = {node['group_id'] for node in after['assistant_contents']}
            assert Counter(edge['assistant_group_id'] for edge in after['associations']) == Counter(ais)
            for edge in after['associations']:
                assert set(edge['user_group_ids']) <= users
                assert edge['verified_reply_link'] is False
                if edge['method'] == 'MODEL_SEMANTIC_CANDIDATE':
                    assert edge['semantic_review']['quote_validation_passed']
                    assert edge['semantic_review']['status'] == 'matched'
                    assert edge['semantic_review']['confidence_label'] in ('high', 'medium')
                    totals['selected_model_associations'] += 1
            for suffix in ('.json', '.md', '.html'):
                assert (OUT / 'conversations' / (sid + suffix)).is_file()
            assert json.loads((OUT / 'conversations' / (sid + '.json')).read_text(encoding='utf-8')) == after
            totals['sessions'] += 1
            totals['original_records'] += len(original)
            totals['retained_occurrences'] += len(retained)
            totals['isolated_occurrences'] += len(side)
    assert totals['sessions'] == 1466 and totals['original_records'] == 46224
    assert totals['retained_occurrences'] + totals['isolated_occurrences'] == totals['original_records']
    internal = json.loads((OUT / 'internal_sessions.json').read_text(encoding='utf-8'))
    metadata = json.loads((OUT / 'sessions_without_exported_messages.json').read_text(encoding='utf-8'))
    assert len(internal) == 19 and len(metadata) == 39
    case = json.loads((OUT / 'conversations/conv_e09b70c51b19.json').read_text(encoding='utf-8'))
    assert len(case['user_requests']) == 6 and len(case['assistant_contents']) == 13
    assert sum(bool(e['user_group_ids']) for e in case['associations']) == 11
    assert len(case['retry_controls']) == 4
    frozen = json.loads((ROOT.parent / 'aligned_066/manifest.json').read_text(encoding='utf-8'))
    for path, expected in frozen['source_hashes'].items():
        assert sha(Path(path)) == expected
    result = {'status': 'PASS', 'counts': dict(totals), 'internal_sessions': 19, 'metadata_only_sessions': 39,
              'source_records_exactly_preserved': True, 'source_metadata_and_order_flags_preserved': True,
              'no_duplicate_active_bodies_under_declared_key': True, 'all_candidate_targets_exist': True,
              'all_selected_model_quotes_validated': True, 'all_detail_files_exist': True,
              'frozen_source_hashes_unchanged': True, 'specified_case_partition_passed': True,
              'does_not_validate_semantic_accuracy_or_true_chronology': True}
    (ROOT / 'independent_delivery_verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
