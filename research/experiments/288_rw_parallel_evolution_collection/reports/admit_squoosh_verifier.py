import asyncio,json,os,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,'/workspace/RecreationBench/scripts')
sys.path.insert(0,'/workspace/RecreationBench/scripts/web')
from web.evaluation.test_runner import _run_playwright_tests
from playwright.async_api import async_playwright
async def main():
 out=Path('/evidence/verifier');out.mkdir(exist_ok=True)
 servers=[]
 try:
  for port,folder in [(8080,'/reference'),(8081,str(out/'negative'))]:
   Path(folder).mkdir(exist_ok=True) if port==8081 else None
   if port==8081:(Path(folder)/'index.html').write_text('<html><body>Static negative control: no editor or drawing functionality</body></html>')
   servers.append(subprocess.Popen(['python3','-m','http.server',str(port),'--bind','127.0.0.1','--directory',folder],stdout=open(out/f'server{port}.log','w'),stderr=subprocess.STDOUT))
  await asyncio.sleep(.4)
  os.environ['MOCKWEB_NODE_MODULES']='/opt/mockweb-bench/batch_run/node_modules'
  spec=Path('/research-scripts/squoosh_functional.spec.ts')
  ref=await _run_playwright_tests([spec],'http://127.0.0.1:8080',timeout=180)
  neg=await _run_playwright_tests([spec],'http://127.0.0.1:8081',timeout=180)
  result={'reference':ref,'negative':neg,'accepted':ref['total']==6 and ref['passed']==6 and ref['skipped']==0 and neg['total']==6 and neg['passed']==0,'model_called':False}
  (out/f'admission_{time.time_ns()}.json').write_text(json.dumps(result,indent=2))
  (out/'admission.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
  if not result['accepted']:raise RuntimeError('Training verifier admission failed')
 finally:
  for s in servers:s.terminate()
if __name__=='__main__':asyncio.run(main())
