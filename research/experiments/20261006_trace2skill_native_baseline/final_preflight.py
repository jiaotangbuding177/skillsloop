"""Free frozen-protocol checks: no request, no model and no business rollout."""
import argparse,ast,json,os,subprocess,sys
from pathlib import Path
from audited_runtime import HERE,BASELINE,dump,sha,bootstrap_imports
import native_runner

def main():
    bootstrap_imports()
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=HERE/'private/final_preflight_001')
    output=p.parse_args().output
    if output.exists(): raise RuntimeError('Preserve prior controls')
    output.mkdir(parents=True)
    sources={p.name:sha(p) for p in HERE.glob('*.py')}
    for name in sources: ast.parse((HERE/name).read_text(encoding='utf-8'),filename=name)
    before=native_runner.guard_source();native_runner.checker_ready()
    env=os.environ.copy()
    for key in ('ECNU_API_KEY','OPENAI_API_KEY'): env.pop(key,None)
    attempted=output/'must_not_create_run'
    blocked=subprocess.run([sys.executable,'-X','utf8','-B',str(HERE/'native_runner.py'),
        'full-public','--output',str(attempted)],env=env,capture_output=True,text=True,encoding='utf-8')
    if blocked.returncode==0 or attempted.exists() or 'no model call allowed' not in blocked.stderr:
        raise RuntimeError('Known failed runtime was not blocked before the API')
    after=native_runner.guard_source()
    if before!=after: raise RuntimeError('Author source changed')
    dump(output/'result.json',{'status':'FREE_PROTOCOL_CONTROL_PASS_FORMULA_RUNTIME_STILL_BLOCKED',
        'real_model_calls':0,'http_requests':0,'business_rollouts':0,'local_source_sha256':sources,
        'profiles_sha256':sha(HERE/'profiles.json'),'author_source_unchanged':True,
        'author_commit':before['commit'],'actual_checker_file_exists':True,
        'formula_runtime_gate':{'exit_code':blocked.returncode,'output_not_created':not attempted.exists(),
            'expected_error':'Formula-task runs require --runtime-env with actual cache controls PASS; no model call allowed'},
        'does_not_prove':'Native Agentic repair, public rollout, consumer outcomes or research benefit'})
    print('FREE_PROTOCOL_PASS; FORMULA_RUNS_BLOCKED_BEFORE_MODEL')

if __name__=='__main__':main()
