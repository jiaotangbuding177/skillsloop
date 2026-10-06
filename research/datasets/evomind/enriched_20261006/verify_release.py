"""Independent offline release checks for the enriched research data."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
P = ROOT / 'private'


def rows(name):
    with (P / name).open(encoding='utf-8') as handle:
        for line in handle:
            if line.strip():
                yield json.loads(line)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    summary = json.loads((ROOT / 'summary.json').read_text(encoding='utf-8'))
    manifest = json.loads((ROOT / 'manifest.json').read_text(encoding='utf-8'))
    inputs = list(rows('source_inputs.jsonl'))
    all_ids = {x['session_id'] for x in inputs}
    checks = {}
    checks['full_input_1466_distinct_sessions'] = len(inputs) == len(all_ids) == 1466
    checks['input_has_no_research_answers'] = all(
        not ({'original_screening', 'effective_screening_decision', 'topic_annotation',
              'accepted_content_correspondences', 'unverified_correspondence_candidates',
              'candidate_ids', 'task', 'learning_candidate', 'lesson', 'annotation_decisions_071'} & set(x))
        and x.get('annotation_labels_included') is False
        and x.get('selected_task_or_lesson_included') is False for x in inputs)
    checks['input_no_claim_of_verified_chronology'] = all(x['chronology_verified'] is False for x in inputs)
    checks['input_nonempty_text_and_no_duplicate_fingerprints'] = all(
        all(g['content'].strip() for g in x['messages']) and
        len({(g['role'], g['cleaned_content_fingerprint']) for g in x['messages']}) == len(x['messages']) for x in inputs)
    checks['input_alias_ids_appear_once_per_session'] = all(
        len([a for g in x['messages'] for a in g['source_group_ids']]) ==
        len({a for g in x['messages'] for a in g['source_group_ids']}) for x in inputs)
    inp = {x['session_id']: x for x in inputs}
    alias_ok = occurrence_ok = source_count_ok = True
    source_group_count = 0
    decisions = Counter()
    for s in rows('enriched_sessions.jsonl'):
        source_group_count += len(s['messages'])
        decisions[s['effective_screening_decision']] += 1
        eligible = [m for m in s['messages'] if not m.get('noise_reason') and m['content'].strip()]
        expected_ids = {m['group_id'] for m in eligible}
        actual_ids = {g for m in inp[s['session_id']]['messages'] for g in m['source_group_ids']}
        alias_ok &= expected_ids == actual_ids
        expected_occ = Counter(o['id'] for m in eligible for o in m['occurrences'])
        actual_occ = Counter()
        for m in inp[s['session_id']]['messages']:
            for o in m['source_occurrences']:
                actual_occ[o['id']] += 1
        occurrence_ok &= expected_occ == actual_occ
    checks['all_eligible_source_group_aliases_preserved'] = alias_ok
    checks['all_eligible_occurrences_preserved'] = occurrence_ok
    checks['27936_original_message_groups_preserved'] = source_group_count == 27936
    checks['effective_decisions_match_summary'] = dict(decisions) == summary['effective_screening']
    cs = list(rows('candidate_contexts_union.jsonl'))
    checks['719_distinct_candidates_and_711_plus_8'] = (
        len(cs) == len({c['candidate_id'] for c in cs}) == 719 and
        Counter(c['pool'] for c in cs) == {'original_711': 711, 'supplemental_review': 8})
    checks['candidate_sessions_in_source_input'] = all(c['session_id'] in all_ids for c in cs)
    checks['sources_unchanged'] = all(sha(Path(x['path'])) == x['sha256'] for x in manifest['inputs'].values())
    checks['all_frozen_outputs_match'] = all(sha(ROOT / name) == digest for name, digest in manifest['outputs'].items())
    checks['builder_script_matches_frozen_hash'] = sha(Path(manifest['script']['path'])) == manifest['script']['sha256']
    checks['tools_and_file_ref_counts'] = sum(1 for _ in rows('tools.jsonl')) == 3578 and sum(1 for _ in rows('file_references.jsonl')) == 1767
    # Confirm credential-bearing Chinese assignment forms are not left in user/AI reading text.
    suspicious = re.compile(r'(?:密码|密钥|授权码)(?:是|为)\s*[:：=]\s*[A-Za-z0-9_+/=.-]{8,}')
    hits = [(x['session_id'], g['group_id']) for x in inputs for g in x['messages'] if suspicious.search(g['content'])]
    checks['no_unmasked_explicit_chinese_credential_assignment_in_input'] = not hits
    result = {'passed': all(checks.values()), 'checks': checks,
              'passed_count': sum(checks.values()), 'check_count': len(checks),
              'credential_hit_ids_only': hits,
              'input_text_groups': sum(len(x['messages']) for x in inputs),
              'root_check_script_sha256': sha(Path(__file__)),
              'meaning': 'Independent source, alias, occurrence, annotation-separation and freeze checks; not semantic accuracy, gold certification or exhaustive privacy audit.'}
    (ROOT / 'release_validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    if not result['passed']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
