"""One explicitly counted correction call using native Claude --resume."""
import sys,os,json,shutil,hashlib,subprocess
from pathlib import Path
args=sys.argv[1:]
if '-p' not in args:os.execv('/usr/local/bin/claude-native',['claude-native',*args])
checkpoint=Path('/previous-round');state=json.loads((checkpoint/'feedback.json').read_text())
manifest=json.loads((checkpoint/'checkpoint_manifest.json').read_text())
for name,d in manifest['files'].items():assert hashlib.sha256((checkpoint/name.replace('\\','/')).read_bytes()).hexdigest()==d,name
marker=Path('/workspace/recreation/.round2_restored')
if marker.exists():raise RuntimeError('Do not repeat correction invocation in same round')
workspace=Path('/workspace/recreation')
for src in (checkpoint/'candidate').iterdir():
 dst=workspace/src.name
 if src.is_dir():shutil.copytree(src,dst,dirs_exist_ok=True)
 else:shutil.copy2(src,dst)
project=Path('/home/agent/.claude/projects')
for src in (checkpoint/'sessions').rglob('*.jsonl'):
 dst=project/src.relative_to(checkpoint/'sessions');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
marker.write_text(json.dumps({'round':2,'parent_attempt':state['parent_attempt'],'session_id':state['session_id']}))
prompt=sys.stdin.read()
prompt+='\n\nThis is full execution round 2 of at most 3 for the same application. Your own previous candidate and session have been restored. Continue from your code, rather than creating a new application. The reference URL supplied in the current task replaces the previous round URL. Independent training validation of the previous submission: functional 3/6, visual SSIM '+str(state['prior_visual_ssim'])+'. Failed behavior checks: '+', '.join(state['failed_behavior_checks'])+'. Preserve the passing drawing, undo/redo and new-document behavior while investigating these real failures against the public reference. Hidden verifier source is not provided. Complete the task and submit your final candidate in this round.'
if '--name' in args:
 i=args.index('--name');del args[i:i+2]
args=['--resume',state['session_id'],*args]
p=subprocess.Popen(['/usr/local/bin/claude-native',*args],stdin=subprocess.PIPE)
p.communicate(prompt.encode());sys.exit(p.returncode)
