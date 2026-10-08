"""Offline check: same native result identity, one call, same error behavior."""
import asyncio,dataclasses,importlib.util,json,tempfile,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
scripts=root.parent/'218_recreationworld_glm_pipeline/vendor/RecreationWorld/scripts'
sys.path[:0]=[str(scripts/'web'),str(scripts)]
from evaluation.vlm_judge import VLMJudgeResult
spec=importlib.util.spec_from_file_location('observer',root/'observe_runner.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
async def main():
 result=VLMJudgeResult(score=.4,page_scores={'fixture':.4},page_details={'fixture':{'score':.4}})
 calls=[]; principal=object(); argument=object()
 async def original(self,*args,**kwargs):
  calls.append((self,args,kwargs)); return result
 with tempfile.TemporaryDirectory() as folder:
  target=Path(folder)/'result.json'; wrapped=m.observed(original,target)
  actual=await wrapped(principal,argument,mode='fixture')
  assert actual is result and len(calls)==1 and calls[0]==(principal,(argument,),{'mode':'fixture'})
  assert json.loads(target.read_text())==dataclasses.asdict(result)
  async def failed(self,*args,**kwargs): raise ValueError('fixture_error')
  try: await m.observed(failed,Path(folder)/'failed.json')(principal)
  except ValueError as e: assert str(e)=='fixture_error'
  else: raise AssertionError('Error was swallowed')
  assert not (Path(folder)/'failed.json').exists()
 report={'passed':True,'native_result_identity_unchanged':True,'call_count':len(calls),'arguments_unchanged':True,'error_not_swallowed':True,'model_called':False}
 (root/'reports/observer_admission.json').write_text(json.dumps(report,indent=2)); print(json.dumps(report))
asyncio.run(main())
