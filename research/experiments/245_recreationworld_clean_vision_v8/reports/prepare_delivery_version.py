import shutil,json
from pathlib import Path
OLD=Path(__file__).resolve().parents[1]; ROOT=OLD.parent/'246_recreationworld_clean_delivery_v9'
ROOT.mkdir(exist_ok=False)
for d in ['reports','private','ledger','runs']: (ROOT/d).mkdir()
for f in ['relay.py','vision_bridge.py','container_entry.py','run_canary.py','model_resource.json']:
 text=(OLD/f).read_text().replace('rw_web_deepseek_clean_vision_v8','rw_web_deepseek_clean_delivery_v9').replace('8164','8165').replace('8794','8795').replace('/245_recreationworld/','/246_recreationworld/')
 if f=='relay.py':
  text=text.replace('    return result\n\ndef receive', "    if not all(c['message'].get('tool_calls') or str(c['message'].get('content') or '').strip() for c in choices):\n        raise ValueError('Empty visible assistant response')\n    return result\n\ndef receive")
 (ROOT/f).write_text(text)
(ROOT/'execution_guidance.txt').write_text('Execution requirements: after one homepage screenshot/accessibility snapshot, inspect the scaffold and immediately write a working React homepage and build it. Do not keep exploring before the first build. Then add the other observed pages incrementally. Observe reference only with screenshots, accessibility snapshots, and ordinary clicks/typing; never browser_evaluate/run_code or scripted reference DOM/HTML/CSS/classes/geometry extraction. Use your own component/class names. Allowed binary media may be downloaded from the loopback origin. Deliver self-contained output/index.html, verify the built file and one internal navigation, then give a nonempty final delivery statement without tools. Do not finish while the template remains or output/index.html is missing. Never inspect evaluation/gold files.\n')
(ROOT/'resume_cli.py').write_text('''import os,sys,tempfile
from pathlib import Path
args=sys.argv[1:]
if '-p' in args:
 original=sys.stdin.buffer.read(); guidance=Path('/results/skill_context.md').read_bytes()
 stream=tempfile.TemporaryFile(); stream.write(original+b"\\n\\n"+guidance); stream.seek(0); os.dup2(stream.fileno(),0)
os.execv('/usr/local/bin/claude-original',['claude',*args])
''')
for f in ['model_acceptance.json','full_image_path_admission.json','stream_vision_admission.json','audit_attempt.py','live_check.py','scorer_progress.py','audit_authorship_actions.py','verify_stream.py','launch.py']:
 text=(OLD/'reports'/f).read_text().replace('rw_web_deepseek_clean_vision_v8','rw_web_deepseek_clean_delivery_v9').replace('8164','8165').replace('8794','8795').replace("'244_recreationworld_vision_bridge_v7'","'245_recreationworld_clean_vision_v8'")
 (ROOT/'reports'/f).write_text(text)
print(str(ROOT))
