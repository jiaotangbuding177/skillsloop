import asyncio,json,os,sys,subprocess,time,shutil
from pathlib import Path
sys.path[:0]=['/workspace/RecreationBench/scripts/web','/workspace/RecreationBench/scripts']
import web.evaluation.test_runner as runner
async def main():
 out=Path('/evidence/native_diagnostic');out.mkdir(exist_ok=True)
 original=runner._parse_json_results
 def capture(path):
  shutil.copy2(path,out/'actual_playwright_report.json');return original(path)
 runner._parse_json_results=capture
 server=subprocess.Popen(['python3','-m','http.server','8080','--bind','127.0.0.1','--directory','/reference'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  await asyncio.sleep(.3);os.environ['MOCKWEB_NODE_MODULES']='/opt/mockweb-bench/batch_run/node_modules'
  result=await runner._run_playwright_tests([Path('/research-scripts/squoosh_functional.spec.ts')],'http://127.0.0.1:8080',timeout=180);print(json.dumps(result))
  j=json.loads((out/'actual_playwright_report.json').read_text())
  def walk(x):
   if isinstance(x,dict):
    if 'errors' in x and x['errors']:print(json.dumps(x['errors']))
    for v in x.values():walk(v)
   elif isinstance(x,list):
    for v in x:walk(v)
  walk(j)
 finally:server.terminate()
asyncio.run(main())
