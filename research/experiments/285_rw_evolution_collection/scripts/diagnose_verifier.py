import json,subprocess,shutil,os,time
from pathlib import Path
out=Path('/evidence/verifier')
work=Path('/tmp/rw285-diagnose');work.mkdir(exist_ok=True)
shutil.copy2('/research-scripts/functional.spec.ts',work/'functional.spec.ts')
if not (work/'node_modules').exists():os.symlink('/opt/mockweb-bench/batch_run/node_modules',work/'node_modules')
(work/'playwright.config.ts').write_text("import {defineConfig} from '@playwright/test';export default defineConfig({workers:1,retries:0,use:{baseURL:'http://127.0.0.1:8080',headless:true},reporter:[['json',{outputFile:'/evidence/verifier/diagnostic.json'}]]});")
s=subprocess.Popen(['python3','-m','http.server','8080','--bind','127.0.0.1','--directory','/reference'],stdout=open(out/'diagnostic_server.log','w'),stderr=subprocess.STDOUT)
try:
 time.sleep(.3);p=subprocess.run(['npx','playwright','test','--config','playwright.config.ts'],cwd=work,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 (out/'diagnostic.log').write_text(p.stdout)
 data=json.loads((out/'diagnostic.json').read_text())
 def walk(x):
  for spec in x.get('specs',[]):
   for t in spec['tests']:
    for r in t['results']:
     if r.get('errors'):print(json.dumps({'title':spec['title'],'errors':r['errors']}))
  for c in x.get('suites',[]):walk(c)
 walk(data)
finally:s.terminate()
