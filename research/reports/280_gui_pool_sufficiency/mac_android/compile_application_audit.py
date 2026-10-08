"""Bounded public evidence synthesis. Does not run apps/models/tests or access benchmark evaluation files."""
from pathlib import Path
import json, csv, hashlib, collections
from datetime import datetime, timezone
BASE = Path(__file__).resolve().parent
PARENT = BASE.parents[1] / '279_gui_acquisition'
catalog = json.loads((PARENT / 'bench_source_catalog.json').read_text(encoding='utf-8'))
web = json.loads((PARENT / 'web_bench_identity_audit.json').read_text(encoding='utf-8'))
readmes = {x['instance_id']: x for x in json.loads((BASE/'bench_readme_manifest.json').read_text(encoding='utf-8'))['rows']}
supplement = json.loads((BASE/'bench_supplementary_manifest.json').read_text(encoding='utf-8'))['docs']
adds = json.loads((BASE/'selected_additions.json').read_text(encoding='utf-8'))['selected_candidates']
old = json.loads((PARENT/'mac_android'/'selected_candidates.json').read_text(encoding='utf-8'))['selected_candidates']
for candidate in adds:
    assert len(candidate['commit']) == 40 and set(candidate['commit'].lower()) <= set('0123456789abcdef'), candidate['id']
class_candidates = {
    'text_code_knowledge': ['macos_hexfiend','web_stackedit'],
    'structured_records_tasks': ['macos_today','android_activity_diary','android_family_gem'],
    'timing_state': ['android_activity_diary'],
    'games_rules': ['android_shattered_pixel_dungeon'],
    'numeric_transform': ['android_opencalc','macos_hexfiend'],
    'media_artifacts': ['macos_gifski','android_fossify_gallery','web_minipaint'],
    'media_playback': ['android_fossify_gallery'],
    'files_search_archive': ['macos_hexfiend','android_fossify_gallery'],
    'system_permissions_device': ['android_package_manager','macos_today'],
    'sensors_navigation': [],
    'security': [],
}
reasons = {
    'text_code_knowledge': 'Local edit/select/search and independent Markdown editor observation are plausible shared UI material; language/compiler/knowledge backend is not established.',
    'structured_records_tasks': 'Synthetic record CRUD, filtering, tree/list organization and completed-state changes are plausible shared material; schema and business rules differ.',
    'timing_state': 'ActivityDiary supplies activity-history and duration records only; it does not establish countdown, pause/resume, wall-clock/timezone or notification behavior.',
    'games_rules': 'Shattered supplies observation-driven game state and rule probes; it does not implement the benchmark puzzles or prove their specific rules.',
    'numeric_transform': 'OpenCalc supplies controlled numeric input/output contracts; code generation, hashes and graphs are not established from that calculator.',
    'media_artifacts': 'Image/video import, preview, parameter controls and output validation can supply shared material. Recording/3D/PDF/codec backends remain specific.',
    'media_playback': 'Gallery supplies local media selection/browsing only; audio/video seek/pause/resume and background transport remain unverified.',
    'files_search_archive': 'Local open/save/select and browser transitions supply limited shared material; archive, search index and filesystem mutation contracts remain unknown here.',
    'system_permissions_device': 'Package Manager supplies read-only package/permission state and To-Day native menu interaction only; IME, sensor, wallpaper, overlay and live system behavior remain unknown.',
    'sensors_navigation': 'No candidate in this subpool demonstrates the required GPS/step/sensor/map core. Generic lists do not count as sensor coverage.',
    'security': 'MacPass is a conditional reserve because of unresolved KeePass-family risk; no admitted independent crypto/OTP core is claimed in this subpool.',
}
native = {x['instance_id']: x for x in catalog['tasks'] if x['platform'] in ('macos','android')}
result=[]
with (BASE/'manual_application_categories.psv').open(encoding='utf-8', newline='') as fp:
    categories = list(csv.DictReader(fp, delimiter='|'))
assert len(categories)==100 and len({x['instance_id'] for x in categories})==100
assert {x['instance_id'] for x in categories} == set(native), 'Public classification must match official 100 IDs exactly'
for row in categories:
    task=native[row['instance_id']]
    rm=readmes[row['instance_id']]
    docs=[]
    if rm['status']=='readme_acquired':
        docs.append({'url':rm['readme_url'], 'local_path':rm['readme_path'], 'sha256':rm['readme_sha256'], 'status':'fixed_commit_public_readme'})
    docs.extend({'url':x['url'],'local_path':x['local_path'],'sha256':x['sha256'],'status':'fixed_commit_public_supplement'} for x in supplement if x['instance_id']==row['instance_id'] and x['status']=='acquired')
    if row['instance_id']=='android/dsandler-markers':
        docs.append({'url':'https://github.com/dsandler/markers','status':'current_official_repository_about; fixed README absent; pinned-version behavior unverified'})
    if row['instance_id']=='macos/photoflare-photoflare':
        docs.append({'url':'https://photoflare.io/','status':'current_official_CE_product_page; fixed README absent; pinned-version behavior unverified'})
    cls=row['primary_class']
    candidate_ids=class_candidates[cls]
    evidence_kind='fixed_source_public_documentation' if any(d['status'].startswith('fixed_commit') for d in docs) else 'current_public_identity_only'
    result.append({
        **task, 'primary_class':cls,
        'public_documented_behavior':row['public_documented_behavior'],
        'classification_evidence_kind':evidence_kind,
        'public_evidence':docs,
        'shared_candidate_ids':candidate_ids,
        'shared_coverage_status':'partial_shared_ui_hypothesis' if candidate_ids else 'unknown_core_coverage',
        'shared_coverage_rationale':reasons[cls],
        'specific_transfer_unknown':row['specific_transfer_unknown'],
        'runtime_evidence':'none; no apps, agents or evaluators run',
        'transfer_is_hypothesis':True,
        'hidden_tests_read':False,
    })
counts=collections.Counter(x['primary_class'] for x in result)
summary={
    'created_utc':datetime.now(timezone.utc).isoformat(),
    'scope':'All 50 macOS and 50 Android public application identities/domains; does not inspect hidden tests or infer per-test capabilities.',
    'benchmark_revision':catalog['revision'],
    'official_task_count':100,
    'platform_counts':dict(collections.Counter(x['platform'] for x in result)),
    'primary_class_counts':dict(sorted(counts.items())),
    'fixed_public_documentation_count':sum(x['classification_evidence_kind']=='fixed_source_public_documentation' for x in result),
    'current_public_identity_only_count':sum(x['classification_evidence_kind']=='current_public_identity_only' for x in result),
    'runtime_ready_count':0,
    'category_counts_are_not_capability_coverage_or_expected_improvement':True,
    'selected_additions_count':4,
    'macpass_excluded_from_formal_subpool_sufficiency':True,
    'rows':result,
}
(BASE/'bench_100_application_audit.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
cols=['instance_id','platform','repo','commit','primary_class','public_documented_behavior','classification_evidence_kind','shared_candidate_ids','shared_coverage_status','specific_transfer_unknown','runtime_evidence','transfer_is_hypothesis']
with (BASE/'bench_100_application_audit.csv').open('w',encoding='utf-8-sig',newline='') as fp:
    writer=csv.DictWriter(fp, fieldnames=cols)
    writer.writeheader()
    for row in result:
        out={k:row[k] for k in cols}
        out['shared_candidate_ids']=';'.join(out['shared_candidate_ids'])
        writer.writerow(out)
def norm(url):
    if not url: return None
    return url.lower().rstrip('/').removesuffix('.git')
native_repos=collections.defaultdict(list)
for task in catalog['tasks']:
    if task['repo']: native_repos[norm(task['repo'])].append(task['instance_id'])
identity_rows=[]
for cand in adds:
    strings=[cand['repo']]+cand['source_isolation']['aliases']+cand['source_isolation']['known_upstream']
    exact=[{'identity':x,'bench_tasks':native_repos[norm(x)]} for x in strings if norm(x) in native_repos]
    web_matches=[]
    for item in web['identities']:
        links=item.get('github_links',[])+item.get('identity_links',[])
        for identity in strings:
            if any(norm(link)==norm(identity) for link in links): web_matches.append({'task_id':item['task_id'],'identity':identity})
    identity_rows.append({'candidate_id':cand['id'],'candidate_repo':cand['repo'],'checked_aliases_upstream':strings[1:],'exact_native_matches':exact,'exact_web_public_identity_matches':web_matches,'known_provenance':cand['source_isolation']['manual_evidence'],'family_or_library_risk':cand['source_isolation']['family_risk'],'status':'no_declared_source_identity_overlap_found' if not exact and not web_matches else 'source_identity_overlap_requires_exclusion_or_review','full_code_similarity_and_dependency_review_complete':False})
audit={
    'scope':'Compare candidate + declared alias/upstream URL identities against all 200 native source identities and all 50 public web identity records.',
    'native_rows':sum(t['platform']!='web' for t in catalog['tasks']),
    'distinct_native_repositories':len(native_repos),
    'web_identity_rows':len(web['identities']),
    'benchmark_revision':catalog['revision'],
    'hidden_tests_or_private_evaluation_paths_read':False,
    'rows':identity_rows,
    'limitations':['Exact source identity comparison is not absolute contamination proof.', 'Web landing-page identities can miss source ancestry; no web repo metadata is available.', 'Package Manager Credits disclose copied code but link some contributor accounts rather than exact repositories. Declared repository candidates require full provenance resolution.', 'Shattered derives from Pixel Dungeon; both declared upstream names were checked but full assets/code similarity was not assessed.', 'MacPass remains a conditional reserve and is excluded from formal sufficiency here.'],
}
(BASE/'source_identity_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
integrity=[]
for name in ('selected_additions.json','manual_application_categories.psv','bench_100_application_audit.json','bench_100_application_audit.csv','source_identity_audit.json','addition_docs_manifest.json','bench_readme_manifest.json','bench_supplementary_manifest.json'):
    path=BASE/name
    data=path.read_bytes()
    integrity.append({'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
(BASE/'report_integrity.json').write_text(json.dumps({'files':integrity,'rows_verified':100,'platform_counts':summary['platform_counts']},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:summary[k] for k in ('official_task_count','platform_counts','primary_class_counts','fixed_public_documentation_count','current_public_identity_only_count')}))
print(json.dumps({'source_overlap_rows':[x['candidate_id'] for x in identity_rows if x['exact_native_matches'] or x['exact_web_public_identity_matches']], 'native_source_rows':audit['native_rows'], 'web_identity_rows':audit['web_identity_rows']}))
