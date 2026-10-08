import hashlib
import json
import struct
import tarfile
from pathlib import Path
import zstandard

OUT = Path('/mnt/d/skillloop/research/reports/233_trajectory_audit')
ROOT = Path('/mnt/d/skillloop/research/experiments/218_recreationworld_glm_pipeline')
procua = json.loads((OUT/'procua_first_trajectory.json').read_text())
prefix = 'part_1/cpu-0047--20260303_074022/0028/'
images = {}
with open(OUT/'procua_shard_prefix.zst', 'rb') as source:
    with zstandard.ZstdDecompressor().stream_reader(source) as decoded:
        with tarfile.open(fileobj=decoded, mode='r|') as archive:
            for member in archive:
                if member.isfile() and member.name.startswith(prefix) and member.name.endswith('.png'):
                    raw = archive.extractfile(member).read()
                    if raw[:8] != b'\x89PNG\r\n\x1a\n':
                        raise ValueError('Invalid PNG signature')
                    name = Path(member.name).name
                    (OUT/'procua_images').mkdir(exist_ok=True)
                    (OUT/'procua_images'/name).write_bytes(raw)
                    images[name] = {'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
                                    'dimensions':struct.unpack('>II',raw[16:24])}
                if len(images) == 8:
                    break
actions = [a for step in procua['steps'] for a in step['actions']]
sample = {'id':procua['trajectory_id'], 'goal':procua['goal'],
          'pipeline':procua['metadata']['pipeline'], 'screen_size':procua['metadata']['screen_size'],
          'vm_image_basename':Path(procua['metadata']['vm_image']).name,
          'setup_id':procua['metadata']['osworld_setup']['id'],
          'setup_instruction':procua['metadata']['osworld_setup']['instruction'],
          'actions':[{'index':i,'type':a['action_type'],'code':a['pyautogui_command'],
                      'image':Path(a['screenshot']).name} for i,a in enumerate(actions)],
          'images':images, 'independent_success_score_present':False,
          'checkpoint_identifier_present':False}
human = json.loads((ROOT/'external/AgentNet/schema_sample.json').read_text())
sample_human = {'id':human['task_id'],'instruction':human['instruction'],
                'task_completed':human['task_completed'],
                'actions':[{'index':a['index'],'image':a['image'],'code':a['value']['code']} for a in human['traj']]}
run = ROOT/'runs/recreation_eval_baseline_1791032747410611525'
records = [json.loads(line) for line in (run/'trajectory.jsonl').read_text().splitlines() if line.strip()]
init = records[0]
tools = []
for r in records:
    for c in r.get('message',{}).get('content',[]) if isinstance(r.get('message',{}).get('content',[]),list) else []:
        if isinstance(c,dict) and c.get('type')=='tool_use':
            tools.append({'name':c.get('name'),'id':c.get('id')})
ledger_path = Path('/mnt/d/skillloop/research/experiments/078_autoskill_cogym/ledger/012255.ledger.json')
ledger = json.loads(ledger_path.read_text())
local = {'records':len(records),'runtime_model_alias':init.get('model'),
         'claude_code_version':init.get('claude_code_version'),'mcp_servers':init.get('mcp_servers'),
         'tool_count':len(tools),'tool_names':sorted({t['name'] for t in tools}),
         'first_12_tools':tools[:12], 'native_metrics':json.loads((run/'metrics.json').read_text()),
         'ledger_proof':{k:ledger.get(k) for k in ('request_number','route','model','model_reported','api_outcome','response_complete')},
         'sha256':hashlib.sha256((run/'trajectory.jsonl').read_bytes()).hexdigest()}
(OUT/'point_by_point_audit.json').write_text(json.dumps({'procua':sample,'agentnet':sample_human,'local_rw_glm':local},indent=2))
print(json.dumps({'procua_actions':len(actions),'downloaded_images':len(images),
                 'local_records':len(records),'local_tools':len(tools),
                 'actual_model':ledger.get('model_reported'),'runtime_alias':init.get('model')}))
