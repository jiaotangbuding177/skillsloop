import asyncio,subprocess,sys,json
from pathlib import Path
sys.path[:0]=['/workspace/RecreationBench/scripts/web','/workspace/RecreationBench/scripts']
from evaluation.evaluator import _take_agent_screenshots
from playwright.async_api import async_playwright
async def main():
 out=Path('/evidence/gt');out.mkdir(exist_ok=True)
 s=subprocess.Popen(['python3','-m','http.server','8082','--bind','127.0.0.1','--directory','/reference'],stdout=open(out/'server.log','w'),stderr=subprocess.STDOUT)
 try:
  await asyncio.sleep(.3)
  async with async_playwright() as p:await _take_agent_screenshots(p.chromium,'http://127.0.0.1:8082',[{'id':'homepage','path':'/'}],out/'gt_screenshots',out/'gt_layout',out/'gt_regions',out/'gt_dom')
  files=list((out/'gt_screenshots').rglob('*.png'));print(json.dumps({'reference_screenshots':len(files),'names':[str(f.relative_to(out)) for f in files],'model_called':False}));assert len(files)==2
 finally:s.terminate()
if __name__=='__main__':asyncio.run(main())
