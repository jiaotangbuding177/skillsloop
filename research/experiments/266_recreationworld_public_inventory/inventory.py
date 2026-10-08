"""Public reference filename inventory only; no evaluation files or model calls."""
import json,urllib.request
from pathlib import Path
root=Path(__file__).resolve().parent; (root/'reports').mkdir(parents=True,exist_ok=True)
repo='Qwen/RecreationBench'; revision='284341f8fc3d6680dd57ca5414fed92a0fe33b95'
with urllib.request.urlopen(f'https://huggingface.co/api/datasets/{repo}/revision/{revision}',timeout=90) as r: index=json.load(r)
groups={}
for row in index['siblings']:
 p=row['rfilename']; parts=p.split('/')
 if len(parts)<5 or parts[0]!='web' or parts[2:4]!=['reference','site']: continue
 groups.setdefault(parts[1],[]).append('/'.join(parts[4:]))
rows=[]
for task,files in groups.items():
 html=[p for p in files if p.lower().endswith(('.html','.htm')) and not p.startswith('_api_mocks/') and p!='_404.html']
 rows.append({'task_id':task,'public_html_pages':len(html),'public_reference_files':len(files),'root_index_present':'index.html' in files,'public_page_paths':sorted(html)})
rows.sort(key=lambda r:(r['public_html_pages'],r['public_reference_files'],r['task_id']))
value={'repo':repo,'revision':revision,'scope':'Public reference filenames only; evaluation/gold contents neither fetched nor inspected','model_or_agent_called':False,'current_corravale_preserved':True,'ranking_uses_public_page_counts_no_candidate_scores':True,'tasks':rows}
(root/'reports/public_reference_inventory.json').write_text(json.dumps(value,indent=2))
print(json.dumps({'tasks':len(rows),'smallest_public_page_inventories':[{k:v for k,v in row.items() if k!='public_page_paths'} for row in rows[:8]]}))
