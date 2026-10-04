#!/usr/bin/env bash
set -u
cd /mnt/d/skillloop/research/experiments
PY=148_tau2_retail_autoskill/runtime_py/bin/python
echo "=== vendor copy status ==="
cat /var/tmp/skillsloop267_vendor_copy.log
du -sm 267_tau2_airline_autoskill/vendor 268_tau2_telecom_autoskill/vendor 2>/dev/null
echo "=== telecom id structure ==="
"$PY" - <<'PYEOF'
import json
from collections import Counter
from pathlib import Path
base = Path("148_tau2_retail_autoskill/vendor/tau2-bench/data/tau2/domains/telecom")
tasks = json.loads((base / "tasks.json").read_text())
split = json.loads((base / "split_tasks.json").read_text())
base_ids = set(split["base"])
import re
cat, sub, persona = Counter(), Counter(), Counter()
for i in sorted(base_ids):
    m = re.match(r"\[(?P<c>[^\]]+)\](?P<s>.*?)\[PERSONA:(?P<p>[^\]]+)\]$", i)
    if m:
        cat[m.group("c")] += 1
        sub[m.group("s")] += 1
        persona[m.group("p")] += 1
    else:
        cat["UNPARSED:" + i] += 1
print("categories:", dict(cat))
print("personas:", dict(persona))
print("sub-issue (top 15):", sub.most_common(15))
# per split
for name, ids in [("train", split["train"]), ("test", split["test"])]:
    c = Counter()
    for i in ids:
        m = re.match(r"\[(?P<c>[^\]]+)\]", i)
        c[m.group("c") if m else "UNPARSED"] += 1
    print(name, dict(c))
# shared sub-issue train/test
def sid(i):
    m = re.match(r"\[[^\]]+\](?P<s>.*?)\[PERSONA:[^\]]+\]$", i)
    return m.group("s") if m else None
tr_sub = {sid(i) for i in split["train"]}
te_sub = {sid(i) for i in split["test"]}
print("train sub-issues:", len(tr_sub), "test sub-issues:", len(te_sub), "shared:", len(tr_sub & te_sub))
print("shared sample:", sorted(tr_sub & te_sub)[:10])
PYEOF
