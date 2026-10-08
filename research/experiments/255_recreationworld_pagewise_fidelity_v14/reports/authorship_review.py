"""Read-only review of observable tool actions, not private model reasoning."""
import json,re,subprocess
from pathlib import Path
root=Path(__file__).resolve().parents[1]
s=json.loads((root/'reports/pipeline_status.json').read_text())
raw=subprocess.check_output(['docker','exec','rw238-'+s['attempt'],'cat','/workspace/recreation/trajectory.jsonl'],text=True)
rows=[json.loads(x) for x in raw.splitlines()]
results={b.get('tool_use_id'):b for r in rows for b in r.get('message',{}).get('content',[]) if isinstance(b,dict) and b.get('type')=='tool_result'}
network=[]; scripts=[]; private_reads=[]; scripted_browser=[]
for i,r in enumerate(rows):
 for b in r.get('message',{}).get('content',[]):
  if not isinstance(b,dict) or b.get('type')!='tool_use': continue
  inp=b.get('input',{}); name=b.get('name',''); result=results.get(b.get('id'),{})
  if name=='Bash':
   c=inp.get('command','')
   if re.search(r'https?://|curl|wget|urllib|requests|httpx|fetch\(',c):
    network.append({'record':i,'description':inp.get('description'),'binary_helper': '/opt/rw218/asset_fetch.py' in c,'tool_error':bool(result.get('is_error')),'command':c})
  if name in ('Write','Edit'):
   c=inp.get('content','')+'\n'+inp.get('new_string','')
   if re.search(r'urllib|httpx|requests\.(get|post)|fetch\(|querySelector|outerHTML|innerHTML|dangerouslySetInnerHTML',c):
    scripts.append({'record':i,'file':inp.get('file_path'),'tool_error':bool(result.get('is_error'))})
  if name=='Read' and any(x in inp.get('file_path','') for x in ('/workspace/dataset','/evaluation/','gt_layout','test_details','vlm_assertions')):
   private_reads.append({'record':i,'file':inp.get('file_path'),'tool_error':bool(result.get('is_error'))})
  if name.endswith(('browser_evaluate','browser_run_code')):
   scripted_browser.append({'record':i,'tool':name,'tool_error':bool(result.get('is_error'))})
out={'attempt':s['attempt'],'network_commands':network,'network_non_binary_helper':[x for x in network if not x['binary_helper']], 'written_network_or_dom_scripts':scripts,'private_evaluation_reads':private_reads,'scripted_browser_calls':scripted_browser,'automated_security_proof':False,'manual_source_review_required':True}
(root/'reports/authorship_action_review.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'network_commands':len(network),'non_binary_network':len(out['network_non_binary_helper']),'written_network_or_dom_scripts':scripts,'private_evaluation_reads':private_reads,'scripted_browser_calls':scripted_browser}))
