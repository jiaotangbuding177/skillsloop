import json,shutil,hashlib,time
from pathlib import Path
root=Path(__file__).resolve().parents[1];scripts=root/'scripts_v24';assert not scripts.exists();scripts.mkdir()
for p in (root/'scripts_v23').glob('*.py'):
 s=p.read_text(encoding='utf-8').replace('scripts_v23','scripts_v24').replace('freeze_{task}_v23','freeze_{task}_v24').replace('frozen_{task}_v23','frozen_{task}_v24').replace('family_budget_v23','family_budget_v24')
 if p.name=='worker.py':
  s=s.replace("assert task=='squoosh'","assert task in ('minipaint','squoosh')").replace('>=2560','>=4096').replace("previous=1 if task=='minipaint' else 0","previous=2 if task=='minipaint' else 0").replace("'1280m'","'2048m'").replace("'--cpus','1'","'--cpus','2'").replace("'memory_limit_mib':1280","'memory_limit_mib':2048").replace('checkpoints/minipaint/round1','checkpoints/minipaint/round2')
  a=s.index('  if budgetfile.exists():');b=s.index("  previous=",a)
  s=s[:a]+"  if task=='minipaint':\n   inherited=json.loads((ROOT/'private/minipaint_family_budget_v22.json').read_text());assert inherited['round_allocated']==2\n  assert not (ROOT/'private'/f'{task}_family_budget_v24.json').exists(), 'No duplicate allocation'\n"+s[b:]
 if p.name=='container_entry.py':pass
 if p.name=='round_cli.py':
  s=s.replace('.round2_restored','.round3_restored').replace("'round':2","'round':3")
  start=s.index("prompt+='\\n\\nThis is full execution round 2");end=s.index("\nif '--name'",start)
  s=s[:start]+"prompt+='\\n\\nThis is full execution round 3 of at most 3 for the same application. Your own round2 candidate and full session have been restored. Continue from your code. The current reference URL replaces the old URL. Independent training validation of the previous submission: functional '+str(state['prior_passed'])+'/'+str(state['prior_total'])+', visual SSIM '+str(state['prior_visual_ssim'])+'. Failed behavior checks: '+', '.join(state['failed_behavior_checks'])+'. Check these real failures against the public reference, preserve already working behavior, and submit your final candidate. Hidden verifier source is not provided. This is the final permitted full execution round; no fourth attempt is allowed.'"+s[end:]
 if p.name=='freeze_worker.py':
  s=s.replace("assert task=='squoosh'","assert task in ('minipaint','squoosh')").replace('checkpoints/minipaint/round1','checkpoints/minipaint/round2').replace("'rw_parallel_evolution_v2.3'","'rw_parallel_evolution_v2.4'")
 (scripts/p.name).write_text(s,encoding='utf-8')
dst=root/'datasets_v23/released/web/minipaint.training';assert not dst.exists();shutil.copytree(root/'datasets/released/web/minipaint.training',dst)
launcher=(root/'reports/launch_worker_v23.py').read_text(encoding='utf-8').replace('scripts_v23','scripts_v24').replace('family_budget_v23','family_budget_v24');(root/'reports/launch_worker_v24.py').write_text(launcher,encoding='utf-8')
(root/'reports/runtime_v24.json').write_text(json.dumps({'version':'rw_parallel_evolution_v2.4','max_active_workers':2,'memory_mib':2048,'cpus':2,'memory_swap_mib':2048,'start_gate_available_mib':4096,'reason':'round2 agent completed but original1.25GiB score subprocess was MEMCG OOM; independent original candidate scoring and Squoosh own-reference2GiB/2cpu self-check complete','model_resource_and_vendor_unchanged':True,'minipaint_next_round':3,'squoosh_next_round':1,'max_full_rounds_per_family':3,'created_epoch':time.time()},indent=2))
print(json.dumps({'prepared':'v2.4','max_workers':2,'memory_mib_each':2048,'start_gate_mib':4096}))
