"""Assemble source-side research evidence and unexecuted evolution task proposals."""
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT.parent / '279_gui_acquisition'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def save(name, document):
    (ROOT / name).write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def canonical(repo):
    return repo.removesuffix('.git').rstrip('/').lower()

if __name__ == '__main__':
    acquisition = read(ROOT / 'source_acquisition_manifest.json')
    integrity = read(ROOT / 'source_integrity_verification.json')
    assert integrity['passed'] and integrity['additional_applications'] == len(acquisition['applications'])
    assert integrity['source_manifest_sha256'] == digest(ROOT / 'source_acquisition_manifest.json')
    old = read(ORIGINAL / 'application_pool.json')
    catalog = read(ORIGINAL / 'bench_source_catalog.json')
    catalog_ids = {r['instance_id'].lower() for r in catalog['tasks']}
    detail_docs = [ROOT / 'desktop/selected_candidates.json', ROOT / 'mac_android/selected_additions.json']
    additions = [r for path in detail_docs for r in read(path)['selected_candidates']]
    additions.append(read(ROOT / 'web/supplemental_candidate.json'))
    details = {(canonical(r['repo']),r['commit']):r for r in additions}
    applications = []
    for original in old['applications']:
        app = dict(original)
        app['origin_report'] = str(ORIGINAL / 'application_pool.json')
        app['selection_status'] = 'conditional_reserve_family_risk' if canonical(app['repo']) == 'https://github.com/macpass/macpass' else 'main_source_candidate_runtime_pending'
        app['source_phase_correction'] = 'Web44 synthetic/6 public-site-derived; full family/near-duplicate audit still pending.'
        for correspondence in app.get('bench_correspondence',[]):
            if isinstance(correspondence,dict) and 'patzly-doodle-android' in json.dumps(correspondence):
                correspondence['correction_280'] = 'Doodle is a dynamic wallpaper/theme app, not drawing/touch canvas; this old mapping is not evidence of drawing transfer.'
                correspondence['mapping_withdrawn_from_sufficiency'] = True
        applications.append(app)
    for acquired in acquisition['applications']:
        key = (canonical(acquired['repo']), acquired['commit'])
        assert key in details, f'missing detailed source evidence: {key}'
        app = dict(details[key])
        assert app.get('license') and len(app.get('workflows',[])) >= 2
        app.update({'source_acquisition': acquired, 'selection_status': 'main_source_candidate_runtime_pending', 'runtime_accepted': False, 'trajectory_count': 0, 'verified_skill_count': 0})
        applications.append(app)
    assert len(applications) == 27
    assert len({canonical(a['repo']) for a in applications}) == 27
    referenced = sorted({task.lower() for a in applications for task in re.findall(r'(?:ubuntu|windows|macos|android|web)/[A-Za-z0-9_.-]+', json.dumps(a.get('bench_correspondence',{}), ensure_ascii=False))})
    invalid = sorted(set(referenced) - catalog_ids)
    assert not invalid, f'invalid public task IDs: {invalid}'
    tasks = []
    for app in applications:
        source_id = app['source_acquisition']['application_id']
        task = {'evolution_task_id': 'evolution/' + source_id, 'source_family_id': canonical(app['repo']), 'platform': app['platform'], 'name': app.get('name', app['repo'].split('/')[-1]), 'repo': app['repo'], 'commit': app['commit'], 'selection_status': app['selection_status'], 'runtime_status': 'reference_admission_pending', 'task_form': 'Observe the running reference, independently implement its GUI and behavior, build and run the implementation, and verify behavior and visual states.', 'public_observation_workflows': app['workflows'], 'workflow_count_is_not_task_count': True, 'private_reference_source_visible_to_actor': False, 'benchmark_private_tests_or_gold_visible': False, 'native_reference_interaction': 'official GUI/control observation boundary; actor sees its own implementation only', 'web_reference_interaction': 'served public HTML/styles/scripts/assets under official protocol; no bulk replay or reference implementation cloning', 'verifier': {'status': 'independent_training_verifier_pending', 'reference_grounded': True, 'reuse_250_test_assertions': False, 'expected_features_are_not_verified_results': True}, 'max_corrective_rounds_including_first': 3, 'counter_scope': 'canonical application family across versions and ports; workflows do not reset the counter', 'attempts_executed': 0, 'trajectory_count': 0, 'verified_skill_count': 0, 'model_started': False}
        tasks.append(task)
    main = [t for t in tasks if t['selection_status'].startswith('main_')]
    reserve = [t for t in tasks if t['selection_status'].startswith('conditional_')]
    assert len(main) == 26 and len(reserve) == 1
    proposed_flows = sum(len(a['workflows']) for a in applications)
    bytes_total = sum(a['source_acquisition']['archive_bytes'] for a in applications)
    files_total = sum(a['source_acquisition']['regular_files'] for a in applications)
    common = {'created_at_utc': datetime.now(timezone.utc).isoformat(), 'official_training_set': False, 'source_sufficiency': 'Enough independent candidate material for a first controlled skills-evolution study targeting all250 benchmark tasks; runtime readiness, skill yield and effect remain unproven.', 'stop_source_expansion': True, 'runtime_accepted_count': 0, 'model_calls': 0, 'trajectory_count': 0, 'verified_skill_count': 0, 'legacy_RW_STOP_preserved': True, 'other_chat_services_modified': False, 'all250_unseen_clean_test_claimed': False, 'historic_corravale_exposure_requires_evaluation_audit': True}
    pool = {**common, 'schema': 'skillloop.gui_evolution_source_pool.v2', 'application_count': len(applications), 'main_candidate_count': len(main), 'conditional_reserve_count': len(reserve), 'platform_counts_all_sources': dict(Counter(a['platform'] for a in applications)), 'platform_counts_main': dict(Counter(t['platform'] for t in main)), 'archive_bytes': bytes_total, 'regular_files': files_total, 'proposed_workflow_count_including_reserve': proposed_flows, 'exact_native_benchmark_repo_overlap': integrity['exact_native_repository_overlap'], 'family_deduplication_proven': False, 'bench_correspondence_id_audit': {'referenced_unique_ids': len(referenced), 'invalid_ids': invalid, 'is_task_coverage_rate': False, 'transfer_measured': False}, 'applications': applications}
    registry = {**common, 'schema': 'skillloop.unexecuted_gui_evolution_task_registry.v1', 'benchmark_target_count': 250, 'benchmark_target_platform_counts': {'ubuntu':50,'windows':50,'macos':50,'android':50,'web':50}, 'main_task_count': 26, 'reserve_task_count': 1, 'planned_round_upper_bound_if_all_main_tasks_admitted': 78, 'round_upper_bound_is_not_successful_trajectory_count': True, 'acquisition_or_evaluation_started': False, 'tasks': tasks}
    save('application_pool.json',pool)
    save('evolution_task_registry.json',registry)
    save('assembly_verification.json', {'passed': True, 'public_task_id_existence_checked': len(referenced), 'invalid_ids': invalid, 'source_sha_evidence': 'source_integrity_verification.json', 'input_sha256': {str(p.relative_to(ROOT)):digest(p) for p in detail_docs + [ROOT/'web/supplemental_candidate.json',ROOT/'source_acquisition_manifest.json',ROOT/'source_integrity_verification.json']}, 'pool_sha256': digest(ROOT/'application_pool.json'), 'task_registry_sha256': digest(ROOT/'evolution_task_registry.json'), 'source_only_no_application_execution': True})
    print(json.dumps({'source_count': len(applications), 'main_tasks': len(main), 'reserve': len(reserve), 'proposed_workflows': proposed_flows, 'archive_bytes': bytes_total, 'regular_files': files_total, 'main_platforms': pool['platform_counts_main'], 'invalid_ids':invalid}))
