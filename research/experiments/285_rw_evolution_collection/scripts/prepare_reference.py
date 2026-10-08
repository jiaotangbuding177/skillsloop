"""Prepare a fixed, independent reference; never execute an agent or read a key."""
import hashlib
import json
from pathlib import Path
import shutil
import tarfile

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT.parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    for name in ['reports', 'admission', 'datasets', 'runs', 'ledger', 'private', 'canonical']:
        (ROOT / name).mkdir(parents=True, exist_ok=True)
    pool_path = RESEARCH / 'reports/280_gui_pool_sufficiency/application_pool.json'
    pool = json.loads(pool_path.read_text(encoding='utf-8'))
    registry = json.loads((RESEARCH / 'reports/280_gui_pool_sufficiency/evolution_task_registry.json').read_text(encoding='utf-8'))
    app = next(a for a in pool['applications'] if a.get('id') == 'web_minipaint')
    source = Path(app['source_acquisition']['source_directory'])
    assert sha(Path(app['source_acquisition']['archive'])) == app['source_archive_sha256']
    site = ROOT / 'admission/minipaint/reference/site'
    if site.exists():
        raise RuntimeError('Reference already prepared; preserve it and use its manifest')
    site.mkdir(parents=True)
    for name in ['index.html', 'dist', 'images']:
        p = source / name
        if p.is_dir():
            shutil.copytree(p, site / name)
        else:
            shutil.copy2(p, site / name)
    assert (site / 'dist/bundle.js').is_file()
    files = {str(p.relative_to(site)).replace('\\', '/'): sha(p) for p in sorted(site.rglob('*')) if p.is_file()}
    (ROOT / 'admission/minipaint/source_manifest.json').write_text(json.dumps({
        'application': app['id'], 'repo': app['repo'], 'commit': app['commit'],
        'archive_sha256': app['source_archive_sha256'], 'files': files,
        'prebuilt_reference_from_same_fixed_archive': True, 'source_modified': False,
        'original_source_or_private_tests_supplied_to_actor': False,
        'public_browser_reference_uses_original_local_bundle_and_assets': True,
    }, indent=2), encoding='utf-8')
    tasks = []
    for t in registry['tasks']:
        if t['selection_status'] != 'main_source_candidate_runtime_pending':
            continue
        tasks.append({'task_id': t['evolution_task_id'], 'source_family_id': t['source_family_id'],
                      'platform': t['platform'], 'state': 'reference_admission_pending',
                      'rounds_started': 0, 'maximum_rounds_including_first': 3,
                      'last_outcome': None})
    assert len(tasks) == 26
    (ROOT / 'reports/collection_status.json').write_text(json.dumps({
        'version': 'rw_evolution_collection_v1', 'state': 'preparing_reference',
        'planned_families': 26, 'tasks': tasks, 'completed_families': 0,
        'agent_rounds_started': 0, 'skills_learning_started': False,
        'benchmark_250_evaluation_started': False,
        'main_collection_model': 'deepseek-v4-flash-vision-exp',
        'first_reference': 'miniPaint', 'new_reference_accepted': 0,
        'other_platform_hosts_admitted': False,
    }, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'prepared': True, 'reference_files': len(files), 'task_registry': len(tasks), 'model_called': False}))

if __name__ == '__main__':
    main()
