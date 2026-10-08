import asyncio,json,sys,shutil,time
from pathlib import Path
sys.path[:0]=['/workspace/RecreationBench/scripts/web','/workspace/RecreationBench/scripts']
import evaluation.test_runner as runner
from evaluation.evaluator import evaluate_task
out=Path('/results');out.mkdir(exist_ok=True)
parse=runner._parse_json_results
def capture(p):shutil.copy2(p,out/('playwright_'+str(time.time_ns())+'.json'));return parse(p)
runner._parse_json_results=capture
async def main():
 task=sys.argv[1];is_ref=task=='squoosh'
 result=await evaluate_task(task_dir=Path('/data')/(task+'.training'),agent_output_dir=Path('/data/squoosh.training/site') if is_ref else Path('/workspace/recreation/output'),output_dir=out/'eval_results',reference_candidate=is_ref,vlm_overrides={'enabled':False})
 (out/'official_result.json').write_text(json.dumps(result,indent=2));print(json.dumps({'task':task,'model_called':False,'scores':result.get('scores'),'final_score':result.get('final_score')}))
asyncio.run(main())
