"""Sanitize telecom task id in session directory names (268 adapter).

Real task id stays in index.jsonl / job metadata; only the directory segment is
sanitized so Windows-side tools (git, PowerShell) can handle the paths.
"""
import re
from pathlib import Path

p = Path("/mnt/d/skillloop/research/experiments/268_tau2_telecom_autoskill/scripts/tau2_openclaw_agent.py")
t = p.read_text(encoding="utf-8")

old = (
    '        task_id = getattr(self.task, "id", "unknown_task") if self.task else "unknown_task"\n'
    '        session_dir = self.run_root / self.group / f"task_{task_id}" / session_id\n'
)
new = (
    '        task_id = getattr(self.task, "id", "unknown_task") if self.task else "unknown_task"\n'
    '        # Telecom task ids contain |, [, ], : — invalid in Windows path segments.\n'
    '        safe_task = re.sub(r"[^A-Za-z0-9_.\\-]", "_", str(task_id))[:120]\n'
    '        session_dir = self.run_root / self.group / f"task_{safe_task}" / session_id\n'
)
assert old in t, "session dir block not found"
t = t.replace(old, new, 1)

if "\nimport re\n" not in t:
    t = t.replace("import shutil\n", "import re\nimport shutil\n", 1)

p.write_text(t, encoding="utf-8")
print("patched")
# compile check via subprocess-free: just syntax compile
import py_compile
py_compile.compile(str(p), doraise=True)
print("compiles ok")
