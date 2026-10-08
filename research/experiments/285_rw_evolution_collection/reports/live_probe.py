"""Read-only statistics inside this task's own sandbox, never model text."""
import json,hashlib
from pathlib import Path
p=Path('/workspace/recreation/trajectory.jsonl')
events=[];bad=0;tools={};images=0
if p.exists():
 for line in p.read_text(errors='replace').splitlines():
  try:
   x=json.loads(line);events.append(x)
   msg=x.get('message',{})
   for c in msg.get('content',[]) if isinstance(msg.get('content'),list) else []:
    if c.get('type')=='tool_use':tools[c.get('name','unknown')]=tools.get(c.get('name','unknown'),0)+1
    if c.get('type')=='image':images+=1
  except Exception:bad+=1
print(json.dumps({'native_event_count':len(events),'partial_lines':bad,'trajectory_bytes':p.stat().st_size if p.exists() else 0,'tool_calls_by_name':tools,'embedded_image_blocks':images,'current_source_file_count':sum(1 for f in Path('/workspace/recreation/src').rglob('*') if f.is_file()),'originality_and_source_access_audit':'pending; counters alone do not prove compliance'}))
