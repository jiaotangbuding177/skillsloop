import json,hashlib,zipfile,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
task=sys.argv[1];assert task in ('minipaint','squoosh')
target=ROOT/'reports'/f'freeze_{task}_v22.json'
if target.exists():raise RuntimeError('Keep prior freeze')
selected=[]
for folder in [ROOT/'scripts_v22',ROOT/'datasets/released/web'/f'{task}.training']:
 selected.extend(p for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
if task=='minipaint':selected.extend(p for p in (ROOT/'checkpoints/minipaint/round1').rglob('*') if p.is_file())
selected.extend(ROOT/n for n in ['parallel_config.json','model_resource.json'])
files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in selected}
target.write_text(json.dumps({'version':'rw_parallel_evolution_v2','task':task,'files':files,'max_workers':2,'per_family_rounds_max':3,'created_epoch':__import__('time').time()},indent=2))
with zipfile.ZipFile(ROOT/'reports'/f'frozen_{task}_v22.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in selected:z.write(p,str(p.relative_to(ROOT)))
print(json.dumps({'task':task,'frozen_files':len(files)}))
