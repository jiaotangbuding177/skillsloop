"""Offline provenance grouping hints, not a train/test split or task labels."""
from pathlib import Path
from collections import defaultdict
import ast
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent
SOURCE = BASE / 'matched_066/private/evomind_conversations.json'
HELPER = BASE / 'analysis_20261005/analyze_local.py'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()).hexdigest()


def main():
    before = sha(SOURCE)
    tree = ast.parse(HELPER.read_text(encoding='utf-8'))
    clean_node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'clean')
    ns = {'re': re}
    exec(compile(ast.Module(body=[clean_node], type_ignores=[]), '<clean_only>', 'exec'), ns)
    source = json.loads(SOURCE.read_text(encoding='utf-8'))
    owners, fingerprints = defaultdict(list), defaultdict(list)
    rows = []
    for sid, session in source.items():
        texts = [re.sub(r'\s+', ' ', ns['clean'](re.sub(r'^\[PromptGuard\][^\n]*\n+', '', x['content'].strip()))).strip()
                 for x in session['user_requests']]
        # Keep multiplicity; order here is the source's group display order, not verified chronology.
        fingerprint = digest(texts)
        char_count = sum(map(len, texts))
        owner = session.get('owner_id')
        owners[owner].append(sid)
        fingerprints[fingerprint].append(sid)
        rows.append({'session_id': sid, 'parent_session_family': sid,
                     'owner_id': owner, 'full_user_input_fingerprint': fingerprint,
                     'normalized_user_chars': char_count,
                     'input_group_count': len(texts),
                     'input_equivalence_only': True,
                     'task_identity_verified': False,
                     'split': 'UNASSIGNED',
                     'exposure': 'previously_available_for_research_and_AI_screening'})
    duplicates = [{'fingerprint': key, 'session_ids': ids, 'session_count': len(ids),
                   'warning': 'Identical normalized full user-group sequences only; not proof of identical tasks, files or outputs.'}
                  for key, ids in sorted(fingerprints.items()) if len(ids) > 1]
    root = ROOT / 'partition'
    private = root / 'private'
    private.mkdir(parents=True, exist_ok=True)
    (private / 'session_families.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows), encoding='utf-8')
    (private / 'identical_input_groups.json').write_text(json.dumps(duplicates, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (private / 'owner_groups.json').write_text(json.dumps(dict(owners), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    assert len(rows) == len(source) == len({r['session_id'] for r in rows})
    assert sum(len(x) for x in owners.values()) == len(source)
    assert sha(SOURCE) == before
    summary = {'session_count': len(rows), 'owners': len(owners),
               'identical_full_input_groups': len(duplicates),
               'sessions_in_identical_input_groups': sum(x['session_count'] for x in duplicates),
               'distinct_normalized_full_inputs': len(fingerprints),
               'cross_owner_identical_input_groups': sum(len({source[s].get('owner_id') for s in x['session_ids']}) > 1 for x in duplicates),
               'formal_train_test_split_created': False,
               'independent_gold_task_labels_created': False,
               'source_sha256': before, 'script_sha256': sha(Path(__file__)), 'clean_source_sha256': sha(HELPER),
               'normalization': 'Existing clean wrapper function + PromptGuard first-line removal + whitespace collapse; source display-order sequence, preserving multiplicity.',
               'checks': {'all_sessions_once': True, 'all_owner_members_once': True, 'source_unchanged': True},
               'artifacts': {str(p.relative_to(ROOT)): sha(p) for p in sorted(private.glob('*'))}}
    (root / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('artifacts', 'normalization')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
