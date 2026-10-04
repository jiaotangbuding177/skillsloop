#!/usr/bin/env python3
"""Inspect airline/telecom task structures to define audit categories."""
import json
import re
from collections import Counter
from pathlib import Path

BASE = Path("/mnt/d/skillloop/research/experiments/148_tau2_retail_autoskill/vendor/tau2-bench/data/tau2/domains")

for dom in ["airline", "telecom"]:
    print("=" * 20, dom)
    tasks = json.loads((BASE / dom / "tasks.json").read_text())
    names = Counter()
    sample_args = {}
    for t in tasks:
        ec = t.get("evaluation_criteria") or {}
        for a in ec.get("actions") or []:
            if not isinstance(a, dict):
                continue
            n = a.get("name")
            names[n] += 1
            if n not in sample_args:
                sample_args[n] = a.get("arguments")
    print("action name counts (top 25):")
    for n, c in names.most_common(25):
        print(f"   {c:5d}  {n}  sample={json.dumps(sample_args.get(n), ensure_ascii=False)[:80]}")
    # collect id-like values
    idvals = Counter()
    for t in tasks:
        ec = t.get("evaluation_criteria") or {}
        for a in ec.get("actions") or []:
            if not isinstance(a, dict):
                continue
            for v in (a.get("arguments") or {}).values():
                if isinstance(v, str) and len(v) <= 40:
                    idvals[v] += 1
    print("top argument string values:", idvals.most_common(12))
    # ticket/description sample (telecom)
    if dom == "telecom":
        t0 = tasks[0]
        print("telecom task0 ticket:", str(t0.get("ticket"))[:150])
        print("telecom task0 desc:", str(t0.get("description"))[:150])
    # reward basis quick
    rb = Counter(str((t.get("evaluation_criteria") or {}).get("reward_basis")) for t in tasks)
    print("reward_basis:", dict(rb))
