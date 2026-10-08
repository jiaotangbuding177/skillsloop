"""Merge public source-side categorization of all250 targets; no evaluation evidence."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / '279_gui_acquisition'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

if __name__ == '__main__':
    paths = [ROOT/'desktop/desktop_100_domain_audit.json', ROOT/'mac_android/bench_100_application_audit.json', ROOT/'web/web50_capability_hints.json']
    desktop, mobile, web = [read(path) for path in paths]
    records = []
    for row in desktop['records']:
        records.append({'instance_id': row['instance_id'], 'platform': row['platform'], 'public_domain': row['domain_primary'], 'public_source_evidence': row['domain_evidence_basis'], 'source_material_relation': row['material_correspondence_hypothesis'], 'detailed_source_record': row, 'coverage_proven': False})
    for row in mobile['rows']:
        records.append({'instance_id': row['instance_id'], 'platform': row['platform'], 'public_domain': row['primary_class'], 'public_source_evidence': row['public_evidence'], 'source_material_relation': row['shared_coverage_status'], 'detailed_source_record': row, 'coverage_proven': False})
    for row in web['rows']:
        records.append({'instance_id': 'web/'+row['task_id'], 'platform': 'web', 'public_domain': 'web_reference', 'paper_origin': row['paper_origin'], 'public_source_evidence': 'public static reference filenames and identity; feature hints are not observed active behavior', 'source_material_relation': 'Vite docs/navigation; Squoosh/miniPaint imagery; StackEdit editing; ActualBudget form/filter/data state. Capability transfer hypothesis only.', 'detailed_source_record': row, 'coverage_proven': False})
    catalog = read(ORIGINAL/'bench_source_catalog.json')
    catalog_ids = {r['instance_id'].lower() for r in catalog['tasks']}
    record_ids = [r['instance_id'].lower() for r in records]
    platforms = Counter(r['platform'] for r in records)
    assert len(records) == 250 and len(set(record_ids)) == 250
    assert set(record_ids) == catalog_ids
    assert platforms == Counter({'ubuntu':50,'windows':50,'macos':50,'android':50,'web':50})
    evidence = {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'schema': 'skillloop.public250_source_capability_audit.v1', 'benchmark_revision': catalog['revision'], 'task_count': len(records), 'platform_counts': dict(platforms), 'target_id_completeness_passed': True, 'inputs_sha256': {str(p.relative_to(ROOT)):digest(p) for p in paths}, 'scope': 'Public task metadata, repository README or public reference identity/filenames; no hidden tests or gold. Source category correspondence is an inference, not real task coverage.', 'private_tests_accessed': False, 'model_calls': 0, 'actual_transfer_measured': False, 'coverage_percent': None, 'coverage_percent_reason': 'Candidate material/category association does not establish passing any behavioral/visual assertion.', 'records': records}
    (ROOT/'benchmark_250_source_audit.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'task_count':len(records),'platform_counts':dict(platforms),'target_id_completeness_passed':True}))
