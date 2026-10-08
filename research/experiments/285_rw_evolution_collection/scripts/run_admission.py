"""Launch only this experiment's offline reference inspection container."""
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
NAME = 'rw285-minipaint-admission'
IMAGE = 'skillloop-rw-web:218-v2'

def call(args):
    return subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

def main():
    if sys.platform != 'linux':
        raise RuntimeError('Run through the existing WSL runtime')
    inspected = call(['docker', 'inspect', NAME])
    if inspected.returncode == 0:
        raise RuntimeError('Existing admission container retained; do not double-start')
    image = json.loads(subprocess.check_output(['docker', 'image', 'inspect', IMAGE], text=True))[0]
    cmd = ['docker', 'run', '-d', '--name', NAME, '--network', 'none', '--memory', '2g', '--cpus', '2', '--pids-limit', '512',
           '--mount', f'type=bind,src={ROOT}/admission/minipaint/reference/site,dst=/reference,readonly',
           '--mount', f'type=bind,src={ROOT}/scripts,dst=/research-scripts,readonly',
           '--mount', f'type=bind,src={ROOT}/admission/minipaint,dst=/evidence',
           image['Id'], 'sleep', 'infinity']
    container = subprocess.check_output(cmd, text=True).strip()
    result = call(['docker', 'exec', NAME, 'python3', '/research-scripts/inspect_reference.py'])
    (ROOT/'admission/minipaint/inspection.log').write_text(result.stdout)
    (ROOT/'admission/minipaint/runtime_identity.json').write_text(json.dumps({'container': NAME, 'container_id': container,
        'image_tag': IMAGE, 'image_id': image['Id'], 'network': 'none', 'model_called': False,
        'inspection_exit': result.returncode}, indent=2))
    print(result.stdout)
    raise SystemExit(result.returncode)

if __name__ == '__main__':
    main()
