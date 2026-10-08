"""Exactly one counted native resume with own checkpoint and real feedback."""
import sys,os,json,shutil,hashlib,subprocess
from pathlib import Path
args=sys.argv[1:]
if '-p' not in args:os.execv('/usr/local/bin/claude-native',['claude-native',*args])
cp=Path('/previous-round');state=json.loads((cp/'feedback.json').read_text());round_no=state['round']
assert round_no in (2,3) and state['maximum_full_rounds']==3
manifest=json.loads((cp/'checkpoint_manifest.json').read_text())
for name,d in manifest['files'].items():assert hashlib.sha256((cp/name).read_bytes()).hexdigest()==d,name
workspace=Path('/workspace/recreation');marker=workspace/'.counted_correction_restored'
assert not marker.exists(),'Never invoke another correction within this round'
for src in (cp/'candidate').iterdir():
 dst=workspace/src.name
 if src.is_dir():shutil.copytree(src,dst,dirs_exist_ok=True)
 else:shutil.copy2(src,dst)
project=Path('/home/agent/.claude/projects')
for src in (cp/'sessions').rglob('*'):
 if not src.is_file():continue
 dst=project/src.relative_to(cp/'sessions');dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
marker.write_text(json.dumps({'round':round_no,'parent_attempt':state['parent_attempt'],'session_id':state['session_id']}))
prompt=sys.stdin.read()
prompt+='\n\nThis is full execution round '+str(round_no)+' of at most 3 for the same application. Your own previous candidate and complete session have been restored. Continue from your own code. Use the current reference URL in this task instead of the previous reference URL. Independent training validation of your last submission: functional '+str(state['prior_passed'])+'/'+str(state['prior_total'])+', visual SSIM '+str(state['prior_visual_ssim'])+'. Failed behavior checks: '+', '.join(state['failed_behavior_checks'])+'. Investigate these actual failures against the public reference, preserve working behavior, and submit your candidate. Hidden verifier source is not provided. '
prompt+=('This is the final permitted full execution round; no fourth attempt is allowed.' if round_no==3 else 'There is at most one further full correction round after this submission.')
if '--name' in args:
 i=args.index('--name');del args[i:i+2]
args=['--resume',state['session_id'],*args]
p=subprocess.Popen(['/usr/local/bin/claude-native',*args],stdin=subprocess.PIPE);p.communicate(prompt.encode());sys.exit(p.returncode)
