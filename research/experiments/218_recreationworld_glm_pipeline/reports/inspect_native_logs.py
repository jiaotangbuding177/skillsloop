from pathlib import Path
import json,collections
import hashlib
paths=list(Path('/workspace/recreation').rglob('*.jsonl'))+list(Path('/home/agent/.claude/projects').rglob('*.jsonl'))
names=collections.Counter();completed=events=images=errors=0
seen_calls=set();seen_results=set();seen_images=set()
for p in paths:
    for line in p.read_text(errors='replace').splitlines():
        try:d=json.loads(line)
        except ValueError:continue
        stack=[d]
        while stack:
            x=stack.pop()
            if isinstance(x,dict):
                if x.get('type')=='tool_use' and x.get('id') not in seen_calls:
                    seen_calls.add(x.get('id'));names[x.get('name','unknown')]+=1
                if x.get('type')=='tool_result' and x.get('tool_use_id') not in seen_results:
                    seen_results.add(x.get('tool_use_id'));completed+=1;errors+=int(bool(x.get('is_error')))
                if x.get('type')=='image':
                    h=hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
                    if h not in seen_images:seen_images.add(h);images+=1
                stack.extend(x.values())
            elif isinstance(x,list):stack.extend(x)
        events+=1
result=dict(log_files=len(paths),scanned_events=events,tool_calls=names,tool_results=completed,tool_errors=errors,unique_image_blocks=images,deduplication='native tool IDs and image content SHA')
Path('/results/native_transport_acceptance.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result))
