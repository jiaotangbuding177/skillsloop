"""Local supplementary data inspection; no production/network or source writes."""
from pathlib import Path
from collections import Counter, defaultdict
import csv, hashlib, json

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / 'private'
AUDIT = ROOT.parents[2] / 'reviews' / '2026-10-05_evomind_full_audit'

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def main():
    labels = json.loads((PRIVATE / 'session_task_categories.json').read_text(encoding='utf-8'))
    rows = {x['session_id']: x for x in json.loads((PRIVATE / 'conversation_cluster_rows.json').read_text(encoding='utf-8'))}
    cats = json.loads((ROOT / 'category_definitions.json').read_text(encoding='utf-8'))
    refs = json.loads((AUDIT / 'private/file_metadata_references.json').read_text(encoding='utf-8'))
    paths = defaultdict(set)
    for ref in refs:
        path = ref['file'].get('path')
        if path:
            paths[(ref['owner_id'], path)].add(ref['session_id'])
    with (PRIVATE / 'artifact_path_lookup.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['user_id', 'file_path', 'source_session_ids']); w.writeheader()
        w.writerows({'user_id': uid, 'file_path': path, 'source_session_ids': '|'.join(sorted(ids))} for (uid, path), ids in sorted(paths.items()))
    by_role = {role: {r['session_id'] for r in refs if r['role'] == role} for role in ['user', 'assistant']}
    result = []
    for code, title in cats.items():
        ids = {x['session_id'] for x in labels if x['primary'] == code}
        result.append({'category': title, 'primary_sessions': len(ids), 'sessions_with_input_file_metadata': len(ids & by_role['user']), 'sessions_with_output_file_metadata': len(ids & by_role['assistant'])})
    result.sort(key=lambda x: -x['primary_sessions'])
    assert sum(x['sessions_with_input_file_metadata'] for x in result) == 442
    assert sum(x['sessions_with_output_file_metadata'] for x in result) == 14
    write_json(ROOT / 'category_evidence_gaps.json', result)
    with (ROOT / 'category_evidence_gaps.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(result[0])); w.writeheader(); w.writerows(result)
    # Two deterministic representatives per label for qualitative review only.
    audit = []
    for code in cats:
        group = sorted((x for x in labels if x['primary'] == code), key=lambda x: x['session_id'])
        selected = [group[0], group[len(group)//2]] if len(group) > 1 else group
        for label in selected:
            source = rows[label['session_id']]
            audit.append({**label, 'category': cats[code], 'clean_user_inputs': [{'group_id': gid, 'text': text[:600], 'cut': len(text) > 600} for gid, text in zip(source['user_groups'], source['clean_user_texts'])]})
    write_json(PRIVATE / 'representative_review_28.json', audit)
    print(json.dumps({'category_evidence_gaps': result, 'review_sessions': len(audit)}, ensure_ascii=False))

if __name__ == '__main__':
    import sys
    sys.stdout.reconfigure(encoding='utf-8')
    main()
