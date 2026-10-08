"""Read only own recorded process identities and container metadata."""
import json
import subprocess
import sys
from pathlib import Path

actors = json.loads(sys.stdin.read())
boot = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
out = []
for actor in actors:
    alive = False
    try:
        alive = boot == actor['boot_id'] and Path('/proc/' + str(actor['pid']) + '/stat').read_text().split(') ', 1)[1].split()[19] == str(actor['start_ticks'])
    except FileNotFoundError:
        pass
    item = {'attempt': actor['attempt'], 'controller_alive': alive}
    if actor.get('container'):
        try:
            result = subprocess.run(['docker', 'inspect', actor['container']], capture_output=True, text=True, timeout=20)
            if result.returncode == 0:
                state = json.loads(result.stdout)[0]['State']
                item['container'] = {key: state.get(key) for key in ['Status', 'OOMKilled', 'ExitCode']}
            else:
                item['container_inspection'] = 'not_found_or_unavailable'
        except subprocess.TimeoutExpired:
            item['container_inspection'] = 'timeout'
    out.append(item)
print(json.dumps(out))
