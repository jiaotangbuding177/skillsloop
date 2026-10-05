"""Install pinned OpenClaw and a private Node runtime; no global config is changed."""
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import tarfile
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NODE = '26.1.0'
OPENCLAW = '2026.9.5'

def main():
    runtime = ROOT / '.runtime'
    runtime.mkdir(exist_ok=True)
    system = {'Windows': 'win', 'Linux': 'linux', 'Darwin': 'darwin'}[platform.system()]
    arch = 'arm64' if platform.machine().lower() in ('arm64', 'aarch64') else 'x64'
    folder = f'node-v{NODE}-{system}-{arch}'
    ext = 'zip' if system == 'win' else 'tar.gz'
    archive = runtime / f'{folder}.{ext}'
    node_dir = runtime / folder
    executable = node_dir / ('node.exe' if system == 'win' else 'bin/node')
    if not executable.exists():
        base = f'https://nodejs.org/dist/v{NODE}/'
        sums = urllib.request.urlopen(base + 'SHASUMS256.txt', timeout=60).read().decode()
        expected = next(line.split()[0] for line in sums.splitlines() if line.split()[-1] == archive.name)
        urllib.request.urlretrieve(base + archive.name, archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise RuntimeError('Node download checksum mismatch')
        if ext == 'zip':
            with zipfile.ZipFile(archive) as z: z.extractall(runtime)
        else:
            with tarfile.open(archive) as t: t.extractall(runtime, filter='data')
    npm = node_dir / ('node_modules/npm/bin/npm-cli.js' if system == 'win' else 'lib/node_modules/npm/bin/npm-cli.js')
    env = dict(os.environ, PATH=str(executable.parent) + os.pathsep + os.environ.get('PATH', ''))
    subprocess.run([str(executable), str(npm), 'install', '--prefix', str(runtime), '--cache', str(runtime / 'npm-cache'),
                    '--no-audit', '--no-fund', '--save-exact', f'openclaw@{OPENCLAW}'], env=env, check=True)
    cli = runtime / 'node_modules/openclaw/openclaw.mjs'
    (runtime / 'launcher.json').write_text(json.dumps({'command': [str(executable), str(cli)], 'version': OPENCLAW}, indent=2), encoding='utf-8')
    if system == 'win':
        from patch_openclaw_windows import apply
        print(apply())
    subprocess.run([str(executable), str(cli), '--version'], env=env, check=True)

if __name__ == '__main__': main()
