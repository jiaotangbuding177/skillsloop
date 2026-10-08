"""Evidence only: finding a catalog or mentioning a skill is not a native Read."""
import argparse
import json
from pathlib import Path

def calls(value):
    if isinstance(value,dict):
        if value.get('type')=='tool_use' and value.get('name')=='Read':
            path=value.get('input',{}).get('file_path','')
            if path.startswith('/opt/rw218-skills/') and path.endswith('/SKILL.md'):
                yield {'id':value.get('id'),'path':path}
        for nested in value.values():yield from calls(nested)
    elif isinstance(value,list):
        for nested in value:yield from calls(nested)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('attempt',type=Path);a=p.parse_args()
    found={};bad=0
    for path in a.attempt.rglob('*.jsonl'):
        if 'trajectory' not in str(path) and 'sessions' not in str(path):continue
        for line in path.open():
            try:
                for call in calls(json.loads(line)):found[call['id'] or call['path']]=call
            except json.JSONDecodeError:bad+=1
    report={'native_read_calls':list(found.values()),'malformed_lines':bad,
        'consumption_observed':bool(found),'scope':'read invocation evidence only; tool result success and final complete transcript must also be checked'}
    (a.attempt/'skill_read_audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'native_skill_reads':len(found),'malformed_lines':bad}))
