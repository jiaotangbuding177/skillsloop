import json,shutil
from pathlib import Path
OLD=Path(__file__).resolve().parents[1]; ROOT=OLD.parent/'245_recreationworld_clean_vision_v8'
ROOT.mkdir(exist_ok=False)
for d in ['reports','private','ledger','runs']: (ROOT/d).mkdir()
for f in ['relay.py','vision_bridge.py','container_entry.py','run_canary.py','model_resource.json']:
 text=(OLD/f).read_text().replace('rw_web_deepseek_vision_bridge_v7','rw_web_deepseek_clean_vision_v8').replace('8163','8164').replace('8793','8794').replace('/244_recreationworld/','/245_recreationworld/')
 if f=='run_canary.py': text=text.replace("        '--mount',f'type=bind,src={ROOT}/private/recovery,dst=/recovery,readonly',\n",'')
 if f=='model_resource.json':
  cfg=json.loads(text); cfg.update(recovery=False,fresh_clean_scaffold=True,source_checkpoint=None); text=json.dumps(cfg,indent=2)
 (ROOT/f).write_text(text)
(ROOT/'execution_guidance.txt').write_text('Observe the reference only through screenshots, accessibility snapshots, and ordinary clicks/typing. Do not call browser_evaluate or browser_run_code on the reference, or use scripts to extract reference DOM/HTML/CSS/classes/geometry. Author original React components with your own class names. Start by building a working skeleton, then add observed pages incrementally. Downloading allowed reference binary media is permitted. Finish by copying the built self-contained dist/index.html to output/index.html, smoke-test it, and give a text-only final delivery statement to end the session. Never inspect evaluation or gold files.\n')
(ROOT/'resume_cli.py').write_text('''import os,sys,tempfile
from pathlib import Path
args=sys.argv[1:]
if '-p' in args:
 guidance=Path('/results/skill_context.md').read_bytes()+b"\\nThe workspace is the clean official scaffold; no previous source or session is restored.\\n\\n"
 stream=tempfile.TemporaryFile(); stream.write(guidance+sys.stdin.buffer.read()); stream.seek(0); os.dup2(stream.fileno(),0)
os.execv('/usr/local/bin/claude-original',['claude',*args])
''')
for f in ['model_acceptance.json','full_image_path_admission.json','stream_vision_admission.json','audit_attempt.py','live_check.py','scorer_progress.py','audit_authorship_actions.py','verify_stream.py']:
 text=(OLD/'reports'/f).read_text().replace('rw_web_deepseek_vision_bridge_v7','rw_web_deepseek_clean_vision_v8').replace('8163','8164').replace('8793','8794'); (ROOT/'reports'/f).write_text(text)
print(str(ROOT))
