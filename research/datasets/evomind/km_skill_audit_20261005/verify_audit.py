from pathlib import Path
import hashlib,json,re,sys
ROOT=Path(__file__).resolve().parent;PROJECT=ROOT.parents[3];P=ROOT/'private'
summary=json.loads((ROOT/'summary.json').read_text(encoding='utf-8'))
events=json.loads((P/'classified_events.json').read_text(encoding='utf-8'))
rows=json.loads((P/'skills_by_evidence.json').read_text(encoding='utf-8'))
source=json.loads((ROOT.parent/'matched_066/private/evomind_conversations.json').read_text(encoding='utf-8'))
checks=[]
def check(name,condition):
    assert condition,name
    checks.append(name)
positive={'successful_read','successful_shell_doc_read','script_execution_attempt'}
known=[e for e in events if e['kind'] in positive and '*' not in e['skill']]
runtime=[e for e in known if e['runtime_skill_path']]
check('all_evidence_sessions_in_1466_scope',all(e['session_id'] in source for e in events))
check('81_known_identifiers_unique',len(rows)==len({r['skill'] for r in rows})==summary['known_consumption_skill_identifiers']==81)
check('74_runtime_identifiers',len({e['skill'] for e in runtime})==summary['known_runtime_skill_identifiers']==74)
check('386_runtime_and399_any_sessions',len({e['session_id'] for e in runtime})==386 and len({e['session_id'] for e in known})==399)
check('masked_names_not_counted',all('*' not in r['skill'] for r in rows))
check('row_session_counts_reconcile',all(r['sessions']==len(set(r['session_ids'])) for r in rows))
check('management_help_failures_not_consumption',all(e['kind'] not in {'path_reference_or_management','script_help','script_management','read_failed_or_unconfirmed'} for e in known))
manifest=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
check('input_hashes_preserved',all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in manifest['inputs'].items()))
old=json.loads((ROOT.parent/'analysis_20261005/manifest.json').read_text(encoding='utf-8'))
check('original_066_hash_unchanged_since_topic_analysis',hashlib.sha256((ROOT.parent/'matched_066/private/evomind_conversations.json').read_bytes()).hexdigest()==old['source_sha256'])
page=(P/'index.html').read_text(encoding='utf-8');report=PROJECT/'research/reports/2026-10-05_evomind_km_skill_usage.md'
paths=[P/link for link in re.findall(r'href="([^"#]+)"',page)]
paths += [report.parent/link for link in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8'))]
check('report_and_all_case_links_exist',all(p.exists() for p in paths))
check('no_claim_of_complete_inventory_or_effect',summary['complete_inventory'] is False and summary['applied_methods_or_task_success_verified'] is False)
(ROOT/'verification.json').write_text(json.dumps({'status':'PASS','checks':checks,'semantic_or_physical_KM_execution_independently_verified':False,'production_or_KM_requests':0,'scope':'source and conservative evidence bookkeeping; not method effectiveness'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8');print(json.dumps({'status':'PASS','checks':len(checks),'runtime_skills':74,'runtime_sessions':386},ensure_ascii=False))
