"""Freeze local exploratory outputs and check coverage, source and links."""
from pathlib import Path
import hashlib, json, re, sys

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT / 'private'
PROJECT = ROOT.parents[3]
REPORT = PROJECT / 'research/reports/2026-10-05_evomind_full_data_processing.md'
SUPPLY = PROJECT / 'research/reports/2026-10-05_evomind_data_supplement_request.md'

def dump(path, obj):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def main():
    stats = json.loads((ROOT/'summary.json').read_text(encoding='utf-8'))
    labels = json.loads((PRIVATE/'session_task_categories.json').read_text(encoding='utf-8'))
    distribution = json.loads((ROOT/'task_distribution.json').read_text(encoding='utf-8'))
    assert len(labels) == len({x['session_id'] for x in labels}) == 1466
    assert sum(x['primary_sessions'] for x in distribution) == 1466
    assert sum(bool(x['secondary']) for x in labels) == stats['multi_category_sessions']
    assert sum(stats['confidence'].values()) == 1466
    for x in distribution:
        assert x['primary_sessions'] == sum(y['primary'] == x['code'] for y in labels)
        assert x['all_relevant_sessions'] == sum(x['code'] in [y['primary']]+y['secondary'] for y in labels)
    view = (PRIVATE/'index.html').read_text(encoding='utf-8')
    data = view.split('<script>const rows=', 1)[1].split('; const E=', 1)[0]
    assert {x['id'] for x in json.loads(data)} == {x['session_id'] for x in labels}
    broken = []
    for parent in [REPORT, SUPPLY, ROOT/'README.md']:
        for target in re.findall(r'\]\(([^)]+)\)', parent.read_text(encoding='utf-8')):
            if not target.startswith(('https:', 'http:', '#')) and not (parent.parent / target.split('#')[0]).exists():
                broken.append(str(parent)+': '+target)
    for target in re.findall(r'(?:href|src)="([^"#]+)"', view):
        if "'+encodeURIComponent" in target:
            continue
        if not target.startswith(('https:', 'http:')) and not (PRIVATE/target).exists():
            broken.append('index.html: '+target)
    original_view_missing = [x['session_id'] for x in labels if not (ROOT.parent/'matched_066/private/conversations'/f"{x['session_id']}.html").exists()]
    assert not broken and not original_view_missing, (broken, original_view_missing)
    # Reconstruct actual selections from preserved pre-revision labels.
    source = {x['session_id']: x for x in json.loads((PRIVATE/'conversation_cluster_rows.json').read_text(encoding='utf-8'))}
    reviewed = [x['initial_review'] if x['session_id'] in {'conv_737c4b010b18','conv_1702b763a7ee'} else x for x in labels]
    selected = []
    for code in json.loads((ROOT/'category_definitions.json').read_text(encoding='utf-8')):
        group = sorted((x for x in reviewed if x['primary']==code), key=lambda x:x['session_id'])
        for x in [group[0], group[len(group)//2]]:
            selected.append({**x, 'user_group_ids': source[x['session_id']]['user_groups']})
    dump(PRIVATE/'representative_review_28_pre_revision.json', selected)
    validation = json.loads((ROOT/'delivery_validation.json').read_text(encoding='utf-8'))
    validation.update({'multi_label_counts_reconciled': True, 'html_all_1466_rows_present': True, 'local_delivery_links_resolved': True, 'all_1466_original_view_links_resolved': True, 'plots_visually_reviewed': True, 'semantic_review_notes': 'Exploratory AI labels; 107 boundary and 28 representative qualitative reviews; not measured accuracy'})
    dump(ROOT/'delivery_validation.json', validation)
    artifacts = [REPORT, SUPPLY]
    artifacts += [p for p in ROOT.iterdir() if p.is_file() and p.name!='delivery_manifest.json']
    artifacts += list((ROOT/'figures').glob('*'))
    artifacts += [PRIVATE/n for n in ['session_task_categories.json','session_task_categories.csv','index.html','requested_file_references.csv','artifact_path_lookup.csv','session_ids.csv','semantic_review_overrides.json','identical_clean_user_session_groups.json','representative_review_28_pre_revision.json']]
    artifacts += [PRIVATE/f'semantic_shard_{i}/combined_labels.json' for i in (1,2,3)]
    dump(ROOT/'delivery_manifest.json', {'date': '2026-10-05', 'scope': '1466 original sessions; frozen exploratory topic labels', 'input_sha256': {key: validation[key] for key in ['source_sha256','annotation_sha256']}, 'artifacts': [{'path': str(p.relative_to(PROJECT)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size} for p in sorted(set(artifacts))]})
    print(json.dumps({'verified_sessions': len(labels), 'multi_theme_sessions': stats['multi_category_sessions'], 'original_view_missing': len(original_view_missing), 'broken_links': len(broken), 'frozen_artifacts': len(set(artifacts))}, ensure_ascii=False))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
