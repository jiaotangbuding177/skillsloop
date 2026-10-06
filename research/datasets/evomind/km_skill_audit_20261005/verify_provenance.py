from pathlib import Path
import csv,hashlib,json,re
R=Path(__file__).resolve().parent;P=R/'private'
a=json.loads((P/'skill_provenance.json').read_text(encoding='utf-8'))
b=json.loads((P/'skills_by_evidence.json').read_text(encoding='utf-8'))
t=json.loads((P/'normalized_skill_tools.json').read_text(encoding='utf-8'))
with (R/'skill_provenance.csv').open(encoding='utf-8-sig',newline='') as f:c=list(csv.DictReader(f))
links=re.findall(r'href="([^"]+)"',(P/'provenance.html').read_text(encoding='utf-8'))
original=json.loads((R/'manifest.json').read_text(encoding='utf-8'))
checks={'81_unique':len(a)==len({x['skill'] for x in a})==81,'full_prior_skill_coverage':{x['skill'] for x in a}=={x['skill'] for x in b},'csv_matches_json':len(c)==81 and {x['技能标识'] for x in c}=={x['skill'] for x in a},'all_tool_indices_valid':all(0<=i<len(t) for x in a for i in x['evidence_indices']),'all_local_conversation_links_exist':all((P/z).resolve().is_file() for z in links),'all_input_hashes_unchanged':all(hashlib.sha256(Path(z).read_bytes()).hexdigest()==h for z,h in original['inputs'].items()),'all_have_reason_and_retrieval':all(x['reason'] and x['retrieval'] for x in a),'source_class_total_81':sum(json.loads((R/'provenance_summary.json').read_text(encoding='utf-8'))['source_classes'].values())==81}
out={'pass':all(checks.values()),'checks':checks,'html_links_checked':len(links),'scope':'离线结构与来源完整性，不认证安装成功、历史版本、原创或效果'}
(R/'provenance_verification.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False));assert out['pass']
