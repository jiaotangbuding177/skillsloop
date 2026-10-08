"""Persist the unchanged native VLM result, without changing calls or grading."""
import dataclasses,json,runpy,sys
from pathlib import Path
def observed(original,destination):
 async def capture(self,*args,**kwargs):
  result=await original(self,*args,**kwargs)
  Path(destination).write_text(json.dumps(dataclasses.asdict(result),ensure_ascii=False,indent=2))
  return result
 return capture
if __name__=='__main__':
 sys.path.insert(0,str(Path.cwd()))
 from evaluation.vlm_judge import AssertionVLMJudge
 AssertionVLMJudge.judge=observed(AssertionVLMJudge.judge,'/results/native_vlm_result.json')
 sys.argv=['runner.run_agent',*sys.argv[1:]]
 runpy.run_module('runner.run_agent',run_name='__main__')
