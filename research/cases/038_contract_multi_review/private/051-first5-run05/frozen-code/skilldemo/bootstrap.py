"""Per-run foundation skills and reproducible AgentSkills packaging."""
from pathlib import Path
import hashlib
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CREATOR = ROOT / '.runtime/node_modules/openclaw/skills/skill-creator'

def initialize(workspace):
    target = workspace / '.foundation/skill-creator'
    target.mkdir(parents=True, exist_ok=True)
    for name in ('SKILL.md', 'scripts/quick_validate.py', 'scripts/package_skill.py'):
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(CREATOR / name, dest)
    (workspace / 'outputs').mkdir(exist_ok=True)
    (workspace / 'draft').mkdir(exist_ok=True)
    (workspace / 'AGENTS.md').write_text(
        '# SkillsLoop workspace\n'
        'Work only on the requested task in this workspace. Do not inspect credentials or unrelated files.\n'
        'To create or revise a skill, read .foundation/skill-creator/SKILL.md and follow it.\n'
        'The draft/ directory is repository-owned candidate source, not a live installed skill.\n'
        'Write deliverables under outputs/. Do not modify selected skills/.\n'
        'Use Python for deterministic calculation and file generation. Do not invent tool execution.\n'
        'On Windows, exec uses PowerShell. Use the workdir argument; do not use cmd.exe syntax such as cd /d or Unix heredocs.\n'
        f'Python executable: {sys.executable}\n', encoding='utf-8')
    return {'skillCreator': '.foundation/skill-creator/SKILL.md',
            'skillCreatorSha256':hashlib.sha256((target/'SKILL.md').read_bytes()).hexdigest(), 'python':sys.executable}

def package(workspace, files):
    from .runtime import validate_bundle
    files = validate_bundle(files)
    # Materialize only the declared package into a fresh directory, excluding agent extras.
    import uuid
    root = workspace / ('validated-' + uuid.uuid4().hex[:8])
    root.mkdir()
    for item in files:
        path = root / item['path']; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(item['content'].encode('utf-8'))
    result = subprocess.run([sys.executable, str(CREATOR/'scripts/package_skill.py'), str(root), str(workspace/'packages')],
                            capture_output=True, text=True, encoding='utf-8', timeout=30)
    if result.returncode:
        raise ValueError('skill-creator package validation failed: '+result.stdout[-1500:]+result.stderr[-500:])
    archive = workspace/'packages'/(root.name+'.skill')
    if not archive.is_file(): raise ValueError('skill-creator did not produce an archive')
    return {'path': str(archive.relative_to(workspace)), 'bytes':archive.stat().st_size,
            'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
            'validator':'OpenClaw bundled skill-creator', 'log':result.stdout}

def draft_files(workspace):
    root = workspace/'draft'
    files = []
    for p in sorted(root.rglob('*')):
        if p.is_symlink(): raise ValueError('Draft symlinks are not permitted')
        if '__pycache__' in p.relative_to(root).parts or p.suffix in ('.pyc','.pyo'): continue
        if p.is_file():
            if p.stat().st_size > 2_000_000: raise ValueError('Draft file too large')
            files.append({'path':p.relative_to(root).as_posix(),'content':p.read_text(encoding='utf-8')})
    return files
