"""Exercise resume restoration and duplicate rejection with a local native stub."""
import hashlib,json,subprocess,tempfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
cp=ROOT/'checkpoints/squoosh/round1';state=json.loads((cp/'feedback.json').read_text())
assert state['round']==2 and len(state['failed_behavior_checks'])==5
with tempfile.TemporaryDirectory(prefix='rw293-checkpoint-') as tmp:
 r=Path(tmp);workspace=r/'workspace';workspace.mkdir();project=r/'projects';stub=r/'native.py'
 stub.write_text('import json,sys\nfrom pathlib import Path\nPath(sys.argv[1]).write_text(json.dumps({"args":sys.argv[2:],"prompt":sys.stdin.read()}))\n')
 out=r/'invocation.json';script=(ROOT/'scripts/round_cli.py').read_text()
 script=script.replace("Path('/previous-round')",'Path('+repr(str(cp))+')').replace("Path('/workspace/recreation')",'Path('+repr(str(workspace))+')').replace("Path('/home/agent/.claude/projects')",'Path('+repr(str(project))+')')
 script=script.replace("['/usr/local/bin/claude-native',*args]", "['python3',"+repr(str(stub))+','+repr(str(out))+',*args]')
 fixture=r/'fixture.py';fixture.write_text(script)
 run=subprocess.run(['python3',str(fixture),'-p','--name','fixture','--output-format','stream-json'],input='Original frozen task prompt and current reference URL.',text=True,capture_output=True)
 assert run.returncode==0,run.stderr
 result=json.loads(out.read_text());assert result['args'][:2]==['--resume',state['session_id']] and '--name' not in result['args']
 assert 'round 2 of at most 3' in result['prompt'] and all(x in result['prompt'] for x in state['failed_behavior_checks'])
 for src in (cp/'sessions').rglob('*'):
  if src.is_file():assert hashlib.sha256(src.read_bytes()).hexdigest()==hashlib.sha256((project/src.relative_to(cp/'sessions')).read_bytes()).hexdigest()
 assert (workspace/'src').is_dir() and not(workspace/'eval_results').exists()
 second=subprocess.run(['python3',str(fixture),'-p'],input='x',text=True,capture_output=True);assert second.returncode!=0 and 'Never invoke another correction' in second.stderr
 result={'own_checkpoint_restore_and_full_tool_results':True,'native_resume_arguments_preserved':True,'real_failure_feedback_only':True,'duplicate_correction_rejected':True,'hidden_verifier_not_copied':True,'model_calls':0,'scope':'offline adapter fixture; actual native model continuation still to verify'}
 (ROOT/'reports/checkpoint_offline_admission.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
