from pathlib import Path
import json,hashlib,time,zipfile,ast
root=Path(__file__).resolve().parents[1];dst=root/'scripts_v27';assert not dst.exists();dst.mkdir()
for p in (root/'scripts_v24').glob('*.py'):
    s=p.read_text().replace('scripts_v24','scripts_v27').replace('freeze_{task}_v24','freeze_{task}_v27').replace('frozen_{task}_v24','frozen_{task}_v27').replace('family_budget_v24','family_budget_v27').replace('rw_parallel_evolution_v2.4','rw_parallel_evolution_v2.7')
    if p.name=='container_entry.py':
        s=s.replace('env.update(UPSTREAM_BASE_URL=',"port=int(env.get('RW_MODEL_PROXY_PORT','8792'));assert port in (8792,8793)\nimport socket\nif stage=='recreation_eval':\n with socket.socket() as sock:sock.bind(('127.0.0.1',port))\nenv.update(UPSTREAM_BASE_URL=")
        s=s.replace("PORT='8788'","PORT=str(port)").replace("RB_AGENT_BASE_URL='http://127.0.0.1:8788'","RB_AGENT_BASE_URL=f'http://127.0.0.1:{port}'")
        old="with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8788/v1/models',headers={'Authorization':'Bearer local'}),timeout=1):break"
        assert old in s
        s=s.replace(old,"with urllib.request.urlopen(urllib.request.Request(f'http://127.0.0.1:{port}/v1/models',headers={'Authorization':'Bearer local'}),timeout=1):\n     if proxy.poll() is not None:raise RuntimeError('Own proxy exited; another listener is not readiness')\n     break")
    if p.name=='worker.py':
        a=s.index("  budgetfile=ROOT/'private'/f'{task}_family_budget.json'");b=s.index("  (ROOT/'private'/f'{task}_family_budget_v27.json').write_text",a)
        s=s[:a]+"  budgets=[json.loads(p.read_text()).get('round_allocated',0) for p in (ROOT/'private').glob(f'{task}_family_budget*.json')]\n  previous=max(budgets,default=0);assert previous<3,'Canonical family exhausted; no reset by version'\n  assert previous==0,'Previous-round continuation checkpoint requires independent admission; do not replay cold'\n  round_no=previous+1\n"+s[b:]
        s=s.replace("'-e','USE_VLM_JUDGE=false'","'-e','USE_VLM_JUDGE=false','-e','RW_MODEL_PROXY_PORT='+str(8792 if task=='minipaint' else 8793)")
    ast.parse(s);(dst/p.name).write_text(s)
for task in ('minipaint','squoosh'):
    selected=[p for folder in (dst,root/'datasets_v23/released/web'/f'{task}.training') for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
    selected.extend(root/n for n in ['parallel_config.json','model_resource.json'])
    files={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in selected}
    (root/'reports'/f'freeze_{task}_v27.json').write_text(json.dumps({'version':'rw_parallel_evolution_v2.7','activated':False,'files':files,'maximum_workers':2,'max_full_rounds_per_family':3},indent=2))
    with zipfile.ZipFile(root/'reports'/f'frozen_{task}_v27.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in selected:z.write(p,str(p.relative_to(root)))
(root/'reports/concurrency_v27_prepared.json').write_text(json.dumps({'epoch':time.time(),'version':'rw_parallel_evolution_v2.7','activated':False,'no_model_calls':True,'ports':{'minipaint':8792,'squoosh':8793},'correction_checkpoint_admission_required':True,'strict_canonical_maximum_rounds':3,'syntax_checked':True,'old_active_v24_files_untouched':True,'scope':'Future launch safety only; current Squoosh remains original v24 actor with explicit v261 external resource repair'},indent=2))
print(json.dumps({'future_version':'v2.7','activated':False,'old_actor_untouched':True,'no_model_calls':True}))
