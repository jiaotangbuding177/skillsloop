"""Sanitize trajectory filenames in 268's canonicalize script (Windows/git-safe)."""
from pathlib import Path

p = Path("/mnt/d/skillloop/research/experiments/268_tau2_telecom_autoskill/scripts/canonicalize_trajectory.py")
t = p.read_text(encoding="utf-8")

if "\nimport re\n" not in t:
    t = t.replace("import json\n", "import json\nimport re\n", 1)

old = '        (OUT_DIR / f"task_{task_id}.txt").write_text(text, encoding="utf-8")\n'
new = ('        safe = re.sub(r"[^A-Za-z0-9_.\\-]", "_", str(task_id))[:120]\n'
       '        (OUT_DIR / f"task_{safe}.txt").write_text(text, encoding="utf-8")\n')
assert old in t, "write line not found"
t = t.replace(old, new, 1)

p.write_text(t, encoding="utf-8")
import py_compile
py_compile.compile(str(p), doraise=True)
print("patched + compiles")
