import json, shutil
from pathlib import Path
OLD=Path(__file__).resolve().parents[1]; ROOT=OLD.parent/'244_recreationworld_vision_bridge_v7'
ROOT.mkdir(exist_ok=True)
if (ROOT/'run_canary.py').exists(): raise RuntimeError('Version already prepared')
for d in ['reports','private','ledger','runs']: (ROOT/d).mkdir(exist_ok=True)
for f in ['relay.py','run_canary.py','container_entry.py','resume_cli.py','execution_guidance.txt','model_resource.json']:
 text=(OLD/f).read_text().replace('rw_web_deepseek_checkpoint_v6','rw_web_deepseek_vision_bridge_v7').replace('8162','8163').replace('8792','8793').replace('/243_recreationworld/','/244_recreationworld/')
 if f=='relay.py':
  text=text.replace('import threading','from vision_bridge import repair_messages\nimport threading')
  text=text.replace("downstream_stream=bool(payload.get('stream')); payload['stream']=True", "payload['messages'], image_audit=repair_messages(payload.get('messages',[]))\n            record['image_transport']=image_audit\n            downstream_stream=bool(payload.get('stream')); payload['stream']=True")
 (ROOT/f).write_text(text)
for f in ['model_acceptance.json','stream_vision_admission.json','audit_attempt.py','live_check.py','scorer_progress.py','export_public_trajectory.py','launch.py','verify_stream.py']:
 text=(OLD/'reports'/f).read_text().replace('rw_web_deepseek_checkpoint_v6','rw_web_deepseek_vision_bridge_v7').replace('8162','8163').replace('8792','8793')
 if f=='export_public_trajectory.py': text=text.replace("'243_recreationworld_checkpoint_v6']","'243_recreationworld_checkpoint_v6','244_recreationworld_vision_bridge_v7']")
 if f=='launch.py': text=text.replace("'model_resource.json']","'model_resource.json','vision_bridge.py']")
 (ROOT/'reports'/f).write_text(text)
shutil.copytree(OLD/'reports/proxy_source_audit',ROOT/'reports/proxy_source_audit')
print(str(ROOT))
