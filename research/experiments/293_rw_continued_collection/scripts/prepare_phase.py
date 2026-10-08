"""Freeze continuation scripts and unchanged reference before each round."""
import ast,hashlib,json,sys,time,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'288_rw_parallel_evolution_collection'
round_no=int(sys.argv[1]);assert round_no in (2,3)
target=ROOT/'reports'/f'freeze_squoosh_round{round_no}.json';assert not target.exists(),'Keep prior freeze'
for p in (ROOT/'scripts').glob('*.py'):ast.parse(p.read_text())
paths=[p for folder in (ROOT/'scripts',ROOT/'checkpoints/squoosh'/f'round{round_no-1}',OLD/'datasets_v23/released/web/squoosh.training') for p in folder.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
paths += [OLD/'parallel_config.json',OLD/'model_resource.json']
files={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
target.write_text(json.dumps({'version':'rw_continued_collection_v3','round':round_no,'created_epoch':time.time(),'files':files,'maximum_rounds':3,'max_workers':2,'proxy_port':8793,'memory_mib':3072,'cpus':2,'no_skill_learning':True,'no_benchmark_evaluation':True,'official_vendor_unchanged':True,'model_resource_unchanged':True},indent=2))
with zipfile.ZipFile(ROOT/'reports'/f'frozen_squoosh_round{round_no}.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in paths:z.write(p,str(p.relative_to(ROOT.parent)))
print(json.dumps({'freeze_written':True,'round':round_no,'files':len(files)}))
