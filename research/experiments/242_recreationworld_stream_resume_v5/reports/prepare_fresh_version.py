import json, shutil, hashlib
from pathlib import Path
OLD=Path(__file__).resolve().parents[1]
ROOT=OLD.parent/'243_recreationworld_checkpoint_v6'
ROOT.mkdir(exist_ok=False)
for d in ['reports','private','ledger','runs']: (ROOT/d).mkdir()
for f in ['relay.py','run_canary.py','container_entry.py','execution_guidance.txt','model_resource.json']:
 text=(OLD/f).read_text().replace('rw_web_deepseek_stream_resume_v5','rw_web_deepseek_checkpoint_v6').replace('8161','8162').replace('8791','8792').replace('/242_recreationworld/','/243_recreationworld/')
 if f=='relay.py':
  text=text.replace("if frame.get('error'): raise ValueError('Provider stream error')", "if frame.get('error'):\n            import re\n            error=json.dumps(frame['error']).replace(KEY,'[REDACTED]')\n            record['provider_error']=re.sub(r'sk-[A-Za-z0-9_-]+','[REDACTED]',error)[:350]\n            receipt(label,record)\n            raise ValueError('Provider stream error')")
 (ROOT/f).write_text(text)
shutil.copy2(OLD/'reports/model_acceptance.json',ROOT/'reports/model_acceptance.json')
shutil.copy2(OLD/'reports/stream_vision_admission.json',ROOT/'reports/stream_vision_admission.json')
for f in ['audit_attempt.py','live_check.py','verify_stream.py']:
 text=(OLD/'reports'/f).read_text().replace('rw_web_deepseek_stream_resume_v5','rw_web_deepseek_checkpoint_v6').replace('8161','8162').replace('8791','8792')
 (ROOT/'reports'/f).write_text(text)
prepare=(OLD/'reports/prepare_recovery.py').read_text().replace("'241_recreationworld_infra_resume_v4'","'242_recreationworld_stream_resume_v5'").replace("subprocess.run(['docker','cp',name+':/home/agent/.claude/projects',str(rec/'projects')],check=True)","# Fresh context: source checkpoint only; old sessions remain in prior version.").replace('rw_web_deepseek_stream_resume_v5','rw_web_deepseek_checkpoint_v6').replace('8161','8162')
(ROOT/'reports/prepare_recovery.py').write_text(prepare)
(ROOT/'resume_cli.py').write_text('''"""Restore only agent-produced source; start a declared fresh native context."""
import json, os, shutil, sys, tempfile
from pathlib import Path
args=sys.argv[1:]
if '-p' in args:
 snapshot=Path('/recovery'); meta=json.loads((snapshot/'recovery_manifest.json').read_text())
 for item in meta['workspace_items']:
  source=snapshot/'workspace'/item; dest=Path.cwd()/item
  if source.is_dir(): shutil.copytree(source,dest,dirs_exist_ok=True)
  else: shutil.copy2(source,dest)
 guidance=b"Infrastructure checkpoint recovery: src/public contain your existing implementation from the interrupted run. Preserve it. Inspect the current source, run the build and concise browser checks, fix only actual issues, and deliver the required output/index.html. Do not restart reference exploration or rebuild from scratch. This is a fresh context after recorded provider failures.\\n\\n"
 stream=tempfile.TemporaryFile(); stream.write(guidance+sys.stdin.buffer.read()); stream.seek(0); os.dup2(stream.fileno(),0)
os.execv('/usr/local/bin/claude-original',['claude',*args])
''')
print(str(ROOT))
