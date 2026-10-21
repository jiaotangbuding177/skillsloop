"""Specific offline business UI observations. Does not score or alter V3 evidence."""
from __future__ import annotations
import argparse,csv,hashlib,io,json,shutil,subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
RUNTIME=ROOT/'evidence_runtime_v4'
PACKETS=ROOT.parent/'20261017_eval250_rubrics/sources/task_packets.jsonl'
SUPPORTED={'T0082','T0179','T0232'}

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def readj(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def writej(path,data):
 p=Path(path);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')

def prepare_functional(task_rubric,inventory_row,output_dir):
 """Return observations, visual_pages, item_coverage, failures; fresh output only."""
 tid=task_rubric['task_id'];out=Path(output_dir).resolve();target=out/'functional_evidence.json'
 if tid not in SUPPORTED:raise ValueError('Unsupported task '+tid)
 if target.exists():raise FileExistsError('Fresh directory required; existing receipt retained: '+str(target))
 out.mkdir(parents=True,exist_ok=True)
 packet=next(json.loads(x) for x in PACKETS.read_text(encoding='utf-8').splitlines() if json.loads(x)['task_id']==tid)
 envpath=ROOT/'evidence_runtime_v3/environment.json';env=readj(envpath);bundle=out/'bundle';bundle.mkdir(exist_ok=True)
 original_checks=[];input_paths={}
 for source in packet['inputs']:
  p=Path(source['path']);dest=bundle/source['name'];dest.parent.mkdir(parents=True,exist_ok=True);actual=sha(p)
  if actual!=source['sha256']:raise ValueError('Original source drift '+source['name'])
  shutil.copy2(p,dest);original_checks.append((p,actual));input_paths[p.name]=p
 html=None
 for record in inventory_row['all_output_artifacts']:
  p=Path(record['path']);dest=bundle/record['relative_path'];dest.parent.mkdir(parents=True,exist_ok=True);actual=sha(p)
  if actual!=record['sha256']:raise ValueError('Original output drift '+p.name)
  shutil.copy2(p,dest);original_checks.append((p,actual))
  if p.suffix.lower() in {'.html','.htm'}:html=dest
 if html is None:raise ValueError('No delivered HTML; absence needs original scoring rule, not function capture')
 browserdir=out/'browser';browserdir.mkdir(exist_ok=True)
 plan={'task_id':tid,'artifact':html.name,'root':str(bundle),'relative_path':html.relative_to(bundle).as_posix(),'destination':str(browserdir),
       'browser':env['browser_absolute_path'],'playwright_module':env['playwright_module_absolute_path']}
 if tid=='T0179':plan['models']=readj(input_paths['模型目录.json'])
 if tid=='T0232':
  plan['sample']=readj(input_paths['客户样例.json']);catalog=list(csv.DictReader(input_paths['产品目录.csv'].read_text(encoding='utf-8-sig').splitlines()))
  prices={x['sku']:float(x['price_ex_tax_cny']) for x in catalog};lines=[{'sku':x['sku'],'quantity':x['quantity'],'unit_price':prices[x['sku']],'amount':round(prices[x['sku']]*x['quantity'],2)} for x in plan['sample']['lines']];total=sum(x['amount'] for x in lines);tax=round(total*.09,2)
  plan['expected_quote']={'lines':lines,'total_ex_tax':f'{total:.2f}','tax_9_percent':f'{tax:.2f}','total_incl_tax':f'{total+tax:.2f}'}
 writej(out/'plan.private.json',plan)
 script=RUNTIME/'functional_capture.cjs';command=[env['node_absolute_path'],str(script),str(out/'plan.private.json')]
 run=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=600,text=True,encoding='utf-8',errors='replace')
 writej(out/'process_receipt.private.json',{'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'model_calls':0,'actor_runs':0})
 raw=readj(browserdir/'observations.json');observations=[];visual=[];state_by={x['state_id']:x for x in raw['states']};image_by={x['image_id']:x for x in raw['images']}
 for im in raw['images']:
  p=browserdir/im['filename'];assert sha(p)==im['sha256']
  visual.append({'evidence_id':'FUNC:'+tid+':'+im['image_id'],'artifact':html.name,'path':str(p),'sha256':im['sha256'],'locator':'functional-browser/'+im['image_id'],'role':'output','evidence_role':'output',
    'state_ids':im['state_ids'],'view_semantics':im['view_semantics'],'scope':im['scope'],'viewport':raw['viewport']})
 for d in raw['downloads']:
  if d.get('failure'):continue
  p=browserdir/d['filename'];assert sha(p)==d['sha256'];d['utf8_decoding_status']='NOT_ATTEMPTED'
  try:
   d['decoded_text']=p.read_text(encoding='utf-8-sig');d['utf8_decoding_status']='SUCCESS_FULL_NO_REPLACEMENT';d['utf8_bom']=p.read_bytes().startswith(b'\xef\xbb\xbf')
   if p.suffix.lower()=='.csv':d['parsed_csv_rows']=list(csv.reader(io.StringIO(d['decoded_text'])))
  except UnicodeDecodeError as e:d['utf8_decoding_status']='FAILED';d['decode_failure']=str(e)
 for scenario in raw['scenarios']:
  sid=scenario['scenario_id'];states=[s for s in raw['states'] if s['scenario_id']==sid]
  observations.append({'evidence_id':'FUNC:'+tid+':'+sid,'artifact':html.name,'item_ids':scenario['item_ids'],'kind':'ACTUAL_TASK_SPECIFIC_LOCAL_BROWSER_SCENARIO','locator':'functional-browser/'+sid,
    'text':'Actual browser scenario '+scenario['name']+'. '+scenario['measurement_status']+'. Compare the recorded original requirement, UI actions, visible results and saved downloads; no score is prefilled.',
    'scenario':scenario,'actual_states':states,'actual_downloads':[d for d in raw['downloads'] if d.get('scenario_id')==sid],
    'actual_dialogs':[d for d in raw['dialogs'] if d.get('scenario_id')==sid],
    'actual_page_runtime_errors':[d for d in raw['errors'] if d.get('scenario_id')==sid],
    'image_evidence_ids':list(dict.fromkeys('FUNC:'+tid+':'+i['image_id'] for s in states for i in s['image_refs']))})
 coverage={}
 for item in task_rubric['items']:
  scenarios=[s for s in raw['scenarios'] if item['item_id'] in s['item_ids']]
  if not scenarios:continue
  bad=[s for s in scenarios if s['measurement_status']=='TEST_TOOL_ERROR'];unavailable=[s for s in scenarios if s['measurement_status']=='BUSINESS_UI_OPERATION_UNAVAILABLE']
  coverage[item['item_id']]={'status':'PARTIAL' if bad else 'COMPLETE','observation_ids':['FUNC:'+tid+':'+s['scenario_id'] for s in scenarios],
    'scenario_ids':[s['scenario_id'] for s in scenarios],'scenario_count':len(scenarios),'observed_scenarios':sum(s['measurement_status']=='OBSERVED' for s in scenarios),
    'business_ui_operation_unavailable':[s['scenario_id'] for s in unavailable],'tool_errors':[s['scenario_id'] for s in bad],
    'interpretation':'Complete means all specified evidence scenarios produced observations, including reliable absence of a delivered UI operation. It does not mean rubric success; Judge must inspect scope, actual outcome and original anchors.'}
 unchanged=all(sha(p)==s for p,s in original_checks)
 evidence={'schema_version':'eval250-task-functional-evidence-v4','task_id':tid,'blind_case_id':inventory_row['blind_case_id'],'artifact':html.name,'observations':observations,'visual_pages':visual,
  'item_coverage':coverage,'failures':[x for x in raw['errors'] if x['kind']=='CAPTURE_INFRASTRUCTURE_FAILURE']+[{'scenario_id':s['scenario_id'],'failure':s.get('failure')} for s in raw['scenarios'] if s['measurement_status']=='TEST_TOOL_ERROR'],
  'runtime':{'capture_completed':raw.get('capture_completed',False),'returncode':run.returncode,'browser_version':raw.get('browser_version'),'environment_sha256':sha(envpath),'python_module_sha256':sha(__file__),'browser_script_sha256':sha(script)},
  'original_files_unchanged':unchanged,'original_file_count':len(original_checks),'model_calls':0,'actor_runs':0,'source_binding':{'prompt_sha256':packet['prompt_sha256'],'rubric_sha256':hashlib.sha256(json.dumps(task_rubric,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'original_outputs':[{ 'filename':p.name,'sha256':s} for p,s in original_checks if p.parent.name=='outputs']},
  'scenario_catalog':[{'scenario_id':s['scenario_id'],'name':s['name'],'measurement_status':s['measurement_status'],'item_ids':s['item_ids']} for s in raw['scenarios']],
  'browser_requests':raw['requests'],'external_requests_blocked':raw['external_requests_blocked'],'limitations':['1440x1000 specific functional scenarios; general V3 states retain separate 1440/1024 evidence.','No application functions called by test and no application DOM values/options injected. Only delivered UI controls used.','No scoring, no model API, no assertion all possible inputs or services tested. Native dialog text recorded; native modal browser chrome not screenshot.']}
 if not unchanged:raise ValueError('Original bytes changed during read-only evidence preparation')
 writej(target,evidence);return evidence

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--all-nine',action='store_true');args=parser.parse_args()
 if not args.all_nine:parser.error('--all-nine required for fixed offline preparation')
 rubrics={r['task_id']:r for r in [json.loads(x) for x in (ROOT/'rubrics_v3.jsonl').read_text(encoding='utf-8').splitlines()]}
 inventory=[json.loads(x) for x in (ROOT/'execution_v2/private_inventory.frozen.jsonl').read_text(encoding='utf-8').splitlines()];manifest=[]
 for row in inventory:
  if row['task_id'] not in SUPPORTED:continue
  directory=ROOT/'functional_validation_v4/jobs'/row['blind_case_id'];e=prepare_functional(rubrics[row['task_id']],row,directory)
  line={'task_id':row['task_id'],'arm':row['arm'],'blind_case_id':row['blind_case_id'],'evidence_path':str(directory/'functional_evidence.json'),'evidence_sha256':sha(directory/'functional_evidence.json'),'scenarios':len(e['observations']),'images':len(e['visual_pages']),'failures':len(e['failures']),'coverage':e['item_coverage'],'original_files_unchanged':e['original_files_unchanged']};manifest.append(line);writej(ROOT/'functional_validation_v4/manifest.json',manifest);print(json.dumps({k:v for k,v in line.items() if k!='coverage'},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
