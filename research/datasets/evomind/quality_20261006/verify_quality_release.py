"""Research release checks. Does not certify semantic quality or business success."""
from pathlib import Path
from collections import Counter
import json,csv,hashlib,re,html,subprocess,shutil
from urllib.parse import unquote
from PIL import Image
import xml.etree.ElementTree as ET

BASE=Path(__file__).resolve().parent
SOURCE=BASE.parent/'enriched_20261006'
REPORT=BASE.parents[2]/'reports/2026-10-06_evomind_trajectory_quality_assessment.md'
def readj(path):return json.loads(path.read_text(encoding='utf-8'))
def rows(path):return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines() if x.strip()]
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def norm(s):return re.sub(r'\s+','',str(s))

def main():
    candidates={x['candidate_id']:x for x in rows(SOURCE/'private/candidate_contexts_union.jsonl')}
    profiles=rows(BASE/'private/quality_assessments.jsonl')
    semantics=rows(BASE/'private/semantic_audit.jsonl')
    inventory=list(csv.DictReader((SOURCE/'private/session_inventory.csv').open(encoding='utf-8-sig',newline='')))
    checks={};issues=[]
    checks['719_unique_candidates']=len(profiles)==len({p['candidate_id'] for p in profiles})==719 and {p['candidate_id'] for p in profiles}==set(candidates)
    checks['716_keep_sessions']=len({p['session_id'] for p in profiles})==716 and {p['session_id'] for p in profiles}=={s['session_id'] for s in inventory if s['effective_decision']=='KEEP'}
    checks['roles_recomputed_from_actual_text']=all(p['user_text_count']==sum(m['role']=='user' and m.get('learning_active',True) and bool(m.get('content','').strip()) for m in candidates[p['candidate_id']]['messages']) and p['assistant_text_count']==sum(m['role']=='assistant' and m.get('learning_active',True) and bool(m.get('content','').strip()) for m in candidates[p['candidate_id']]['messages']) for p in profiles)
    checks['719_evidence_quotes_found_in_candidate_text']=all(any(norm(c['evidence_quote']) in norm(m.get('content','')) for m in c['messages']) for c in candidates.values())
    em=readj(BASE/'evidence_manifest.json')
    checks['frozen_enriched_sources_unchanged']=all(sha(Path(v['path']))==v['sha256'] for v in em['inputs'].values())
    oldmanifest=readj(SOURCE/'manifest.json')
    checks['upstream_original_inputs_unchanged']=all(sha(Path(v['path']))==v['sha256'] for v in oldmanifest['inputs'].values())
    checks['objective_profiles_unchanged']=all(sha(BASE/rel)==digest for rel,digest in em['outputs'].items())
    checks['material_counts_not_quality_scores']=all(p.get('quality_score') is None and not p.get('semantic_quality_certified',False) for p in profiles)
    checks['existing_outcomes_not_promoted']=all(not c['complete_trace_verified'] and not c['chronology_verified'] and c['task_success']=='unknown' for c in candidates.values())
    case=candidates['conv_00416a23f1c6:learn01'];msg=next(m for m in case['messages'] if m['role']=='assistant')
    paragraph=msg['content'].split('推荐版（199字，含标点）：')[1].split('几点说明：')[0].strip().lstrip('*').strip().lstrip('>').strip()
    count_check={'candidate_id':case['candidate_id'],'source_group_id':msg['group_id'],'scope':'仅推荐版正文，不含标题和说明','paragraph_sha256':hashlib.sha256(paragraph.encode()).hexdigest(),'unicode_chars_including_spaces':len(paragraph),'unicode_chars_without_whitespace':len(norm(paragraph)),'without_whitespace_ascii_letters_digits':len(re.sub(r'[A-Za-z0-9\s]','',paragraph)),'assistant_claim':199,'user_limit':200,'business_counting_rule_known':False,'business_failure_certified':False,'conclusion':'计数口径不同；不能单凭Unicode计数认定历史失败，需明确表单口径'}
    checks['visible_word_count_scope_independently_recomputed']=count_check['unicode_chars_including_spaces']==232 and count_check['unicode_chars_without_whitespace']==230 and count_check['without_whitespace_ascii_letters_digits']==199
    (BASE/'private/visible_text_constraint_check.json').write_text(json.dumps(count_check,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    summary=readj(BASE/'quality_summary.json')
    checks['main_chart_totals_match']=sum(summary['preparation_states'].values())==sum(summary['structure_counts'].values())==719 and sum(summary['effective_screening'].values())==1466
    fixed=readj(BASE/'private/sample_selection.json')
    checks['37_fixed_semantic_samples_exact']=len(semantics)==len({x['candidate_id'] for x in semantics})==37 and {x['candidate_id'] for x in semantics}=={x['candidate_id'] for x in fixed['samples']}
    semissues=[]
    for s in semantics:
        c=candidates[s['candidate_id']]; groups={a:m['content'] for m in c['messages'] for a in set(m.get('source_group_ids',[m['group_id']])+[m['group_id']])}
        for field in ('method_evidence','feedback_or_revision_evidence'):
            evidence=s.get(field,[])
            if isinstance(evidence,dict): evidence=[evidence]
            for e in evidence:
                if not isinstance(e,dict): semissues.append({'candidate_id':s['candidate_id'],'field':field,'issue':'non-structured evidence'});continue
                gid=e.get('group_id');quote=e.get('quote','')
                if gid not in groups or (quote and norm(quote) not in norm(groups.get(gid,''))): semissues.append({'candidate_id':s['candidate_id'],'field':field,'group_id':gid,'issue':'quote/anchor not exact'})
    checks['semantic_quotes_and_anchors_locate']=not semissues
    issues.extend(semissues)
    checks['semantic_review_scope_not_full_certification']=all(not p.get('execution_verified',False) for p in semantics) and summary['semantic_reviewed_count']==37
    pages=list((BASE/'private/cards').glob('*.html'))
    checks['719_readable_quality_cards']=len(pages)==719 and all((BASE/'private'/p['card_url']).exists() and html.escape(candidates[p['candidate_id']]['learning_candidate']) in (BASE/'private'/p['card_url']).read_text(encoding='utf-8') for p in profiles)
    csvrows=list(csv.DictReader((BASE/'private/逐条质量清单.csv').open(encoding='utf-8-sig',newline='')))
    checks['chinese_csv_covers_719_once']=len(csvrows)==719 and {p['候选编号'] for p in csvrows}==set(candidates)
    missing=[];linkcount=0
    for file in [BASE/'private/index.html',*pages,REPORT,BASE/'README.md']:
        text=file.read_text(encoding='utf-8')
        static_text=re.sub(r'<script>.*?</script>','',text,flags=re.S)
        links=re.findall(r'(?:href|src)="([^"<>]+)"',static_text) if file.suffix=='.html' else re.findall(r'\]\(([^)]+)\)',text)
        for target in links:
            target=html.unescape(target).split('#')[0]
            if not target or target.startswith(('http:','https:','data:','mailto:')):continue
            resolved=(file.parent/unquote(target)).resolve();linkcount+=1
            if resolved==BASE/'release_validation.json':continue  # produced by this invocation below
            if not resolved.exists():missing.append({'from':str(file.relative_to(BASE)) if file.is_relative_to(BASE) else str(file),'target':target})
    checks['all_static_page_and_report_links_exist']=not missing
    issues.extend(missing)
    chartok=True
    for name in ('01_topic_distribution','02_quality_preparation','03_evidence_coverage'):
        try:
            with Image.open(BASE/'figures'/f'{name}.png') as im:im.verify()
            ET.parse(BASE/'figures'/f'{name}.svg')
            assert (BASE/'figures'/f'{name}.pdf').read_bytes().startswith(b'%PDF')
        except Exception as e:chartok=False;issues.append({'chart':name,'error':str(e)})
    checks['9_chart_files_readable']=chartok
    index=(BASE/'private/index.html').read_text(encoding='utf-8')
    script=re.search(r'<script>(.*?)</script>',index,re.S).group(1)
    scriptpath=BASE/'private/index_script_for_validation.js';scriptpath.write_text(script,encoding='utf-8')
    node=shutil.which('node')
    if node:
        result=subprocess.run([node,'--check',str(scriptpath)],capture_output=True,text=True,encoding='utf-8')
        checks['page_javascript_syntax_valid']=result.returncode==0
        if result.returncode:issues.append({'javascript_error':result.stderr})
    else:checks['page_javascript_syntax_valid']=False;issues.append({'javascript_error':'Node unavailable; not verified'})
    result={'passed':all(checks.values()),'passed_count':sum(checks.values()),'check_count':len(checks),'checks':checks,'static_links_checked':linkcount,'issues':issues,'meaning':'Research data coverage/source/count/presentation checks, not semantic accuracy or business/skill certification','browser_interaction_verified':False,'visual_chart_inspection':'root viewed all three PNGs; Chinese labels and counts readable'}
    (BASE/'release_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    outputs={str(p.relative_to(BASE)):sha(p) for p in sorted(BASE.rglob('*')) if p.is_file() and p.name!='release_manifest.json' and '__pycache__' not in p.parts}
    manifest={'schema':'evomind-quality-release-v1','inputs':em['inputs'],'upstream_evidence_manifest_sha256':sha(BASE/'evidence_manifest.json'),'outputs':outputs,'report':{'path':str(REPORT),'sha256':sha(REPORT)},'quality_not_semantic_accuracy':True}
    (BASE/'release_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if not result['passed']:raise SystemExit(1)

if __name__=='__main__':main()
